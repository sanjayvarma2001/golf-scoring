from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import get_current_user, require_admin
from app.database.db import get_db
from app.models.draw import Draw, DrawTicket, Winner
from app.models.score import Score
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.draw import DrawCreate, DrawPublic, DrawSimulationResult, SimulationTierResult
from app.services import draw_engine

router = APIRouter(prefix="/draws", tags=["Draws"])


async def _active_subscriber_ids(db: AsyncSession) -> List[str]:
    result = await db.execute(select(Subscription.user_id).where(Subscription.status == "active"))
    return [row[0] for row in result.all()]


async def _avg_score_by_user(db: AsyncSession, user_ids: List[str]) -> dict:
    """Average of each user's currently-retained scores (up to their last 5), defaulting to 0."""
    if not user_ids:
        return {}
    result = await db.execute(
        select(Score.user_id, func.avg(Score.score)).where(Score.user_id.in_(user_ids)).group_by(Score.user_id)
    )
    return {user_id: float(avg) for user_id, avg in result.all()}


async def _ensure_tickets(db: AsyncSession, draw: Draw, subscriber_ids: List[str]) -> List[DrawTicket]:
    existing = await db.execute(select(DrawTicket).where(DrawTicket.draw_id == draw.id))
    existing_tickets = {t.user_id: t for t in existing.scalars().all()}

    for user_id in subscriber_ids:
        if user_id not in existing_tickets:
            ticket = DrawTicket(draw_id=draw.id, user_id=user_id, numbers=draw_engine.generate_ticket_numbers())
            db.add(ticket)
            existing_tickets[user_id] = ticket
    await db.flush()
    return list(existing_tickets.values())


async def _jackpot_rollover_for_new_draw(db: AsyncSession) -> float:
    """If the most recent published draw's 5-match tier had no winners, its pool carries forward."""
    result = await db.execute(
        select(Draw).where(Draw.status == "published").order_by(Draw.published_at.desc()).limit(1)
    )
    last_draw = result.scalar_one_or_none()
    if last_draw is None:
        return 0.0
    winners_5 = await db.execute(
        select(func.count()).select_from(Winner).where(Winner.draw_id == last_draw.id, Winner.match_tier == 5)
    )
    if winners_5.scalar_one() == 0:
        return last_draw.pool_5_match
    return 0.0


@router.post("", response_model=DrawPublic, status_code=status.HTTP_201_CREATED)
async def create_draw(payload: DrawCreate, db: AsyncSession = Depends(get_db), _admin: User = Depends(require_admin)):
    existing = await db.execute(select(Draw).where(Draw.month == payload.month, Draw.year == payload.year))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A draw for this month/year already exists")

    rollover = await _jackpot_rollover_for_new_draw(db)
    draw = Draw(month=payload.month, year=payload.year, draw_type=payload.draw_type, jackpot_rollover_in=rollover)
    db.add(draw)
    await db.flush()

    subscriber_ids = await _active_subscriber_ids(db)
    await _ensure_tickets(db, draw, subscriber_ids)

    await db.commit()
    await db.refresh(draw)
    return draw


async def _run_matching(db: AsyncSession, draw: Draw):
    tickets_result = await db.execute(select(DrawTicket).where(DrawTicket.draw_id == draw.id))
    tickets = tickets_result.scalars().all()
    if not tickets:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active subscribers hold tickets for this draw")

    avg_scores = await _avg_score_by_user(db, [t.user_id for t in tickets])
    avg_score_list = [avg_scores.get(t.user_id, 0.0) for t in tickets]

    winning_numbers = draw_engine.pick_winning_numbers(
        draw.draw_type, [t.numbers for t in tickets], avg_score_list
    )

    matches_by_user = {t.user_id: draw_engine.match_tier(t.numbers, winning_numbers) for t in tickets}

    active_count = len(tickets)
    subs_result = await db.execute(select(Subscription.amount).where(Subscription.status == "active"))
    amounts = [row[0] for row in subs_result.all()] or [0.0]
    average_fee = sum(amounts) / len(amounts)

    settings = get_settings()
    pools = draw_engine.compute_prize_pools(
        active_subscriber_count=active_count,
        average_subscription_fee=average_fee,
        share_5=settings.POOL_SHARE_5_MATCH,
        share_4=settings.POOL_SHARE_4_MATCH,
        share_3=settings.POOL_SHARE_3_MATCH,
        jackpot_rollover_in=draw.jackpot_rollover_in,
    )
    tier_results = draw_engine.resolve_tiers(matches_by_user=matches_by_user, pools=pools)
    return winning_numbers, tier_results, pools, active_count


@router.post("/{draw_id}/simulate", response_model=DrawSimulationResult)
async def simulate_draw(draw_id: str, db: AsyncSession = Depends(get_db), _admin: User = Depends(require_admin)):
    """Preview a draw's outcome without persisting winners or changing its status (PRD: 'simulation before publish')."""
    draw = await db.get(Draw, draw_id)
    if draw is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draw not found")
    if draw.status == "published":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This draw has already been published")

    winning_numbers, tier_results, pools, active_count = await _run_matching(db, draw)
    # Simulation intentionally does NOT commit any state change to draw/winners.

    return DrawSimulationResult(
        draw_id=draw.id,
        draw_type=draw.draw_type,
        winning_numbers=winning_numbers,
        total_participants=active_count,
        tiers=[
            SimulationTierResult(
                match_tier=t.match_tier,
                winner_count=len(t.winner_user_ids),
                prize_per_winner=t.prize_per_winner,
                pool_amount=t.pool_amount,
            )
            for t in tier_results
        ],
        jackpot_rolled_over=(len(tier_results[0].winner_user_ids) == 0),  # tier_results[0] is always tier 5
    )


@router.post("/{draw_id}/publish", response_model=DrawPublic)
async def publish_draw(draw_id: str, db: AsyncSession = Depends(get_db), _admin: User = Depends(require_admin)):
    draw = await db.get(Draw, draw_id)
    if draw is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draw not found")
    if draw.status == "published":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This draw has already been published")

    winning_numbers, tier_results, pools, _active_count = await _run_matching(db, draw)

    draw.winning_numbers = winning_numbers
    draw.pool_5_match = pools.pool_5_match
    draw.pool_4_match = pools.pool_4_match
    draw.pool_3_match = pools.pool_3_match
    draw.published_at = datetime.now(timezone.utc)
    draw.status = "published"

    for tier in tier_results:
        for user_id in tier.winner_user_ids:
            db.add(
                Winner(
                    draw_id=draw.id,
                    user_id=user_id,
                    match_tier=tier.match_tier,
                    prize_amount=tier.prize_per_winner,
                )
            )

    await db.commit()
    await db.refresh(draw)
    return draw


@router.get("", response_model=List[DrawPublic])
async def list_draws(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = select(Draw).order_by(Draw.year.desc(), Draw.month.desc())
    if current_user.role != "admin":
        stmt = stmt.where(Draw.status == "published")
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{draw_id}", response_model=DrawPublic)
async def get_draw(draw_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    draw = await db.get(Draw, draw_id)
    if draw is None or (draw.status != "published" and current_user.role != "admin"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draw not found")
    return draw


@router.get("/{draw_id}/my-ticket")
async def my_ticket(draw_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DrawTicket).where(DrawTicket.draw_id == draw_id, DrawTicket.user_id == current_user.id)
    )
    ticket = result.scalar_one_or_none()
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You don't hold a ticket for this draw")
    return {"draw_id": draw_id, "numbers": ticket.numbers}

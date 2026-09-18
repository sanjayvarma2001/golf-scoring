import calendar

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user
from app.database.db import get_db
from app.models.charity import Charity
from app.models.draw import Draw, DrawTicket, Winner
from app.models.score import Score
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.auth import UserPublic
from app.schemas.dashboard import ParticipationSummary, UserDashboard, WinningsSummary
from app.schemas.score import ScorePublic
from app.schemas.subscription import SubscriptionPublic

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserPublic)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/me/dashboard", response_model=UserDashboard)
async def get_my_dashboard(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    Everything PRD section 10 requires on one screen: subscription status,
    scores, charity + contribution %, participation summary, and winnings.
    """
    sub_result = await db.execute(select(Subscription).where(Subscription.user_id == current_user.id))
    subscription = sub_result.scalar_one_or_none() or Subscription(user_id=current_user.id, status="inactive")

    charity = None
    if current_user.charity_id:
        charity_result = await db.execute(
            select(Charity).options(selectinload(Charity.events)).where(Charity.id == current_user.charity_id)
        )
        charity = charity_result.scalar_one_or_none()

    scores_result = await db.execute(
        select(Score).where(Score.user_id == current_user.id).order_by(Score.date_played.desc())
    )
    scores = scores_result.scalars().all()

    draws_entered_result = await db.execute(
        select(func.count()).select_from(DrawTicket).where(DrawTicket.user_id == current_user.id)
    )
    draws_entered = draws_entered_result.scalar_one()

    upcoming_result = await db.execute(
        select(Draw)
        .join(DrawTicket, DrawTicket.draw_id == Draw.id)
        .where(DrawTicket.user_id == current_user.id, Draw.status != "published")
        .order_by(Draw.year.desc(), Draw.month.desc())
        .limit(1)
    )
    upcoming_draw = upcoming_result.scalar_one_or_none()
    upcoming_label = f"{calendar.month_name[upcoming_draw.month]} {upcoming_draw.year}" if upcoming_draw else None

    winners_result = await db.execute(
        select(Winner).where(Winner.user_id == current_user.id).order_by(Winner.created_at.desc())
    )
    winners = winners_result.scalars().all()
    total_won = sum(w.prize_amount for w in winners)
    total_paid = sum(w.prize_amount for w in winners if w.payment_status == "paid")
    total_pending = total_won - total_paid

    return UserDashboard(
        subscription=SubscriptionPublic.model_validate(subscription),
        charity=charity,
        charity_percentage=current_user.charity_percentage,
        scores=[ScorePublic.model_validate(s) for s in scores],
        participation=ParticipationSummary(draws_entered=draws_entered, upcoming_draw=upcoming_label),
        winnings=WinningsSummary(total_won=total_won, total_paid=total_paid, total_pending=total_pending, winners=winners),
    )

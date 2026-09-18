from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_admin
from app.database.db import get_db
from app.models.draw import Draw, Winner
from app.models.score import Score
from app.models.subscription import Payment, Subscription
from app.models.user import User
from app.schemas.admin import AdminUserPublic, AdminUserUpdate, ReportsSummary
from app.schemas.score import ScoreUpdate

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=List[AdminUserPublic])
async def list_users(db: AsyncSession = Depends(get_db), _admin: User = Depends(require_admin)):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return result.scalars().all()


@router.put("/users/{user_id}", response_model=AdminUserPublic)
async def update_user(
    user_id: str, payload: AdminUserUpdate, db: AsyncSession = Depends(get_db), _admin: User = Depends(require_admin)
):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    if user_id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete your own admin account")
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await db.delete(user)
    await db.commit()


@router.put("/scores/{score_id}")
async def admin_edit_score(
    score_id: str, payload: ScoreUpdate, db: AsyncSession = Depends(get_db), _admin: User = Depends(require_admin)
):
    """Admin edit of any subscriber's score (PRD 11: 'Edit golf scores' under user management)."""
    score = await db.get(Score, score_id)
    if score is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Score not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(score, field, value)
    await db.commit()
    await db.refresh(score)
    return score


@router.get("/reports", response_model=ReportsSummary)
async def reports_summary(db: AsyncSession = Depends(get_db), _admin: User = Depends(require_admin)):
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    active_subscribers = (
        await db.execute(select(func.count()).select_from(Subscription).where(Subscription.status == "active"))
    ).scalar_one()

    paid = (
        await db.execute(select(func.coalesce(func.sum(Winner.prize_amount), 0.0)).where(Winner.payment_status == "paid"))
    ).scalar_one()
    pending = (
        await db.execute(select(func.coalesce(func.sum(Winner.prize_amount), 0.0)).where(Winner.payment_status == "pending"))
    ).scalar_one()

    charity_total = (
        await db.execute(select(func.coalesce(func.sum(Payment.amount), 0.0)).where(Payment.kind == "donation"))
    ).scalar_one()
    # Add the charity-earmarked share of every successful subscription payment.
    sub_payments = (await db.execute(select(Payment).where(Payment.kind == "subscription"))).scalars().all()
    for p in sub_payments:
        user = await db.get(User, p.user_id)
        if user:
            charity_total += p.amount * (user.charity_percentage / 100)

    total_draws_published = (
        await db.execute(select(func.count()).select_from(Draw).where(Draw.status == "published"))
    ).scalar_one()
    total_winners = (await db.execute(select(func.count()).select_from(Winner))).scalar_one()

    return ReportsSummary(
        total_users=total_users,
        active_subscribers=active_subscribers,
        total_prize_pool_paid=round(paid, 2),
        total_prize_pool_pending=round(pending, 2),
        charity_contribution_total=round(charity_total, 2),
        total_draws_published=total_draws_published,
        total_winners=total_winners,
    )

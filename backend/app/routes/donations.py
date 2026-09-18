from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database.db import get_db
from app.models.charity import Charity
from app.models.donation import Donation
from app.models.subscription import Payment
from app.models.user import User
from app.schemas.donation import DonationCreate, DonationPublic

router = APIRouter(prefix="/donations", tags=["Donations"])


@router.post("", response_model=DonationPublic, status_code=status.HTTP_201_CREATED)
async def make_donation(
    payload: DonationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """An independent donation, separate from the gameplay/subscription charity split (PRD 8.1)."""
    charity = await db.get(Charity, payload.charity_id)
    if charity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charity not found")

    donation = Donation(user_id=current_user.id, charity_id=payload.charity_id, amount=payload.amount)
    db.add(donation)
    db.add(Payment(user_id=current_user.id, kind="donation", amount=payload.amount, status="succeeded"))
    await db.commit()
    await db.refresh(donation)
    return donation


@router.get("/me", response_model=List[DonationPublic])
async def my_donations(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Donation).where(Donation.user_id == current_user.id).order_by(Donation.created_at.desc())
    )
    return result.scalars().all()

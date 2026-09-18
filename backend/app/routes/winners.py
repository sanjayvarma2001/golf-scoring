from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_admin
from app.database.db import get_db
from app.models.user import User
from app.models.draw import Winner
from app.schemas.draw import WinnerProofSubmit, WinnerPublic, WinnerVerifyRequest

router = APIRouter(prefix="/winners", tags=["Winners"])


@router.get("/me", response_model=List[WinnerPublic])
async def my_wins(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Winner).where(Winner.user_id == current_user.id).order_by(Winner.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{winner_id}/proof", response_model=WinnerPublic)
async def submit_proof(
    winner_id: str,
    payload: WinnerProofSubmit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Winner uploads a screenshot of their scores for admin review (PRD section 9)."""
    winner = await db.get(Winner, winner_id)
    if winner is None or winner.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Winner record not found")
    winner.proof_image_url = payload.proof_image_url
    winner.verification_status = "pending"
    await db.commit()
    await db.refresh(winner)
    return winner


@router.get("", response_model=List[WinnerPublic])
async def list_all_winners(db: AsyncSession = Depends(get_db), _admin: User = Depends(require_admin)):
    result = await db.execute(select(Winner).order_by(Winner.created_at.desc()))
    return result.scalars().all()


@router.post("/{winner_id}/verify", response_model=WinnerPublic)
async def verify_winner(
    winner_id: str,
    payload: WinnerVerifyRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    winner = await db.get(Winner, winner_id)
    if winner is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Winner record not found")
    winner.verification_status = "approved" if payload.approve else "rejected"
    winner.verified_by = current_user.id
    await db.commit()
    await db.refresh(winner)
    return winner


@router.post("/{winner_id}/pay", response_model=WinnerPublic)
async def mark_paid(winner_id: str, db: AsyncSession = Depends(get_db), _admin: User = Depends(require_admin)):
    winner = await db.get(Winner, winner_id)
    if winner is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Winner record not found")
    if winner.verification_status != "approved":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Winner must be verified before payout")
    winner.payment_status = "paid"
    await db.commit()
    await db.refresh(winner)
    return winner

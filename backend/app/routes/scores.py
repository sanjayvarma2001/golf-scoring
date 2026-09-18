from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database.db import get_db
from app.models.score import Score
from app.models.user import User
from app.schemas.score import ScoreCreate, ScorePublic, ScoreUpdate

router = APIRouter(prefix="/scores", tags=["Scores"])

MAX_SCORES_RETAINED = 5


@router.get("", response_model=List[ScorePublic])
async def list_my_scores(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Score).where(Score.user_id == current_user.id).order_by(Score.date_played.desc())
    )
    return result.scalars().all()


@router.post("", response_model=ScorePublic, status_code=status.HTTP_201_CREATED)
async def add_score(
    payload: ScoreCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing_for_date = await db.execute(
        select(Score).where(Score.user_id == current_user.id, Score.date_played == payload.date_played)
    )
    if existing_for_date.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A score already exists for this date - edit or delete it instead of adding a duplicate",
        )

    score = Score(
        user_id=current_user.id,
        course=payload.course,
        score=payload.score,
        date_played=payload.date_played,
    )
    db.add(score)
    await db.flush()

    all_scores = await db.execute(
        select(Score).where(Score.user_id == current_user.id).order_by(Score.date_played.desc())
    )
    all_scores = all_scores.scalars().all()
    if len(all_scores) > MAX_SCORES_RETAINED:
        for stale in all_scores[MAX_SCORES_RETAINED:]:
            await db.delete(stale)

    await db.commit()
    await db.refresh(score)
    return score


@router.put("/{score_id}", response_model=ScorePublic)
async def update_score(
    score_id: str,
    payload: ScoreUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    score = await db.get(Score, score_id)
    if score is None or score.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Score not found")

    new_date = payload.date_played or score.date_played
    if payload.date_played is not None and payload.date_played != score.date_played:
        clash = await db.execute(
            select(Score).where(
                Score.user_id == current_user.id, Score.date_played == new_date, Score.id != score.id
            )
        )
        if clash.scalar_one_or_none() is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Another score already exists for that date")

    if payload.course is not None:
        score.course = payload.course
    if payload.score is not None:
        score.score = payload.score
    score.date_played = new_date

    await db.commit()
    await db.refresh(score)
    return score


@router.delete("/{score_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_score(
    score_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    score = await db.get(Score, score_id)
    if score is None or score.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Score not found")
    await db.delete(score)
    await db.commit()

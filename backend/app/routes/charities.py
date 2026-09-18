from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import require_admin
from app.database.db import get_db
from app.models.charity import Charity, CharityEvent
from app.models.user import User
from app.schemas.charity import CharityCreate, CharityEventCreate, CharityEventPublic, CharityPublic, CharityUpdate

router = APIRouter(prefix="/charities", tags=["Charities"])


@router.get("", response_model=List[CharityPublic])
async def list_charities(
    search: Optional[str] = Query(default=None, description="Filter by name or description"),
    featured_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    """Public charity directory with search/filter, per PRD section 8.2."""
    stmt = select(Charity).options(selectinload(Charity.events))
    if search:
        like = f"%{search.lower()}%"
        stmt = stmt.where(Charity.name.ilike(like) if hasattr(Charity.name, "ilike") else Charity.name.like(like))
    if featured_only:
        stmt = stmt.where(Charity.is_featured.is_(True))
    result = await db.execute(stmt)
    return result.scalars().unique().all()


@router.get("/{charity_id}", response_model=CharityPublic)
async def get_charity(charity_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Charity).options(selectinload(Charity.events)).where(Charity.id == charity_id)
    )
    charity = result.scalar_one_or_none()
    if charity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charity not found")
    return charity


@router.post("", response_model=CharityPublic, status_code=status.HTTP_201_CREATED)
async def create_charity(
    payload: CharityCreate, db: AsyncSession = Depends(get_db), _admin: User = Depends(require_admin)
):
    charity = Charity(**payload.model_dump())
    db.add(charity)
    await db.commit()
    await db.refresh(charity)
    return charity


@router.put("/{charity_id}", response_model=CharityPublic)
async def update_charity(
    charity_id: str, payload: CharityUpdate, db: AsyncSession = Depends(get_db), _admin: User = Depends(require_admin)
):
    charity = await db.get(Charity, charity_id)
    if charity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charity not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(charity, field, value)
    await db.commit()
    await db.refresh(charity)
    return charity


@router.delete("/{charity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_charity(charity_id: str, db: AsyncSession = Depends(get_db), _admin: User = Depends(require_admin)):
    charity = await db.get(Charity, charity_id)
    if charity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charity not found")
    await db.delete(charity)
    await db.commit()


@router.post("/{charity_id}/events", response_model=CharityEventPublic, status_code=status.HTTP_201_CREATED)
async def add_charity_event(
    charity_id: str, payload: CharityEventCreate, db: AsyncSession = Depends(get_db), _admin: User = Depends(require_admin)
):
    charity = await db.get(Charity, charity_id)
    if charity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charity not found")
    event = CharityEvent(charity_id=charity_id, **payload.model_dump())
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event

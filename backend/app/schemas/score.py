from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class ScoreCreate(BaseModel):
    course: Optional[str] = Field(default=None, max_length=150)
    score: int = Field(..., ge=1, le=45, description="Stableford score, 1-45")
    date_played: date


class ScoreUpdate(BaseModel):
    course: Optional[str] = Field(default=None, max_length=150)
    score: Optional[int] = Field(default=None, ge=1, le=45)
    date_played: Optional[date] = None


class ScorePublic(BaseModel):
    id: str
    course: Optional[str] = None
    score: int
    date_played: date
    created_at: datetime

    class Config:
        from_attributes = True

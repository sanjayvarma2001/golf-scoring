from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CharityEventPublic(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    event_date: date
    location: Optional[str] = None

    class Config:
        from_attributes = True


class CharityEventCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    event_date: date
    location: Optional[str] = None


class CharityCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=150)
    description: str = Field(..., min_length=10)
    website_url: Optional[str] = None
    image_url: Optional[str] = None
    is_featured: bool = False


class CharityUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    website_url: Optional[str] = None
    image_url: Optional[str] = None
    is_featured: Optional[bool] = None


class CharityPublic(BaseModel):
    id: str
    name: str
    description: str
    website_url: Optional[str] = None
    image_url: Optional[str] = None
    is_featured: bool
    created_at: datetime
    events: List[CharityEventPublic] = []

    class Config:
        from_attributes = True

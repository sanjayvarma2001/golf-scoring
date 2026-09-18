from datetime import datetime

from pydantic import BaseModel, Field


class DonationCreate(BaseModel):
    charity_id: str
    amount: float = Field(..., gt=0)


class DonationPublic(BaseModel):
    id: str
    charity_id: str
    amount: float
    created_at: datetime

    class Config:
        from_attributes = True

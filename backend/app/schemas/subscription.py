from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class CheckoutRequest(BaseModel):
    plan: str = Field(..., pattern="^(monthly|yearly)$")


class SubscriptionPublic(BaseModel):
    plan: Optional[str] = None
    status: str
    amount: float
    start_date: Optional[date] = None
    renewal_date: Optional[date] = None

    class Config:
        from_attributes = True


class CheckoutResponse(BaseModel):
    checkout_url: Optional[str] = None
    message: str


class PaymentPublic(BaseModel):
    id: str
    kind: str
    amount: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

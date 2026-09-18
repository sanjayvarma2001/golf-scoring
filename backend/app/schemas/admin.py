from typing import Optional

from pydantic import BaseModel


class AdminUserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    charity_percentage: Optional[int] = None


class AdminUserPublic(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    charity_percentage: int

    class Config:
        from_attributes = True


class ReportsSummary(BaseModel):
    total_users: int
    active_subscribers: int
    total_prize_pool_paid: float
    total_prize_pool_pending: float
    charity_contribution_total: float
    total_draws_published: float
    total_winners: int

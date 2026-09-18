from typing import List, Optional

from pydantic import BaseModel

from app.schemas.charity import CharityPublic
from app.schemas.draw import WinnerPublic
from app.schemas.score import ScorePublic
from app.schemas.subscription import SubscriptionPublic


class ParticipationSummary(BaseModel):
    draws_entered: int
    upcoming_draw: Optional[str] = None  # "March 2026" style label for the next open draw, if any


class WinningsSummary(BaseModel):
    total_won: float
    total_paid: float
    total_pending: float
    winners: List[WinnerPublic]


class UserDashboard(BaseModel):
    subscription: SubscriptionPublic
    charity: Optional[CharityPublic] = None
    charity_percentage: int
    scores: List[ScorePublic]
    participation: ParticipationSummary
    winnings: WinningsSummary

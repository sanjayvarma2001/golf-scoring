from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class DrawCreate(BaseModel):
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2020, le=2100)
    draw_type: str = Field(..., pattern="^(random|algorithmic)$")


class DrawPublic(BaseModel):
    id: str
    month: int
    year: int
    draw_type: str
    status: str
    winning_numbers: Optional[List[int]] = None
    pool_5_match: float
    pool_4_match: float
    pool_3_match: float
    jackpot_rollover_in: float
    created_at: datetime
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WinnerPublic(BaseModel):
    id: str
    draw_id: str
    user_id: str
    match_tier: int
    prize_amount: float
    proof_image_url: Optional[str] = None
    verification_status: str
    payment_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class WinnerProofSubmit(BaseModel):
    proof_image_url: str = Field(..., min_length=3)


class WinnerVerifyRequest(BaseModel):
    approve: bool


class SimulationTierResult(BaseModel):
    match_tier: int
    winner_count: int
    prize_per_winner: float
    pool_amount: float


class DrawSimulationResult(BaseModel):
    draw_id: str
    draw_type: str
    winning_numbers: List[int]
    total_participants: int
    tiers: List[SimulationTierResult]
    jackpot_rolled_over: bool

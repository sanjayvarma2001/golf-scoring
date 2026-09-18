import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Draw(Base):
    """
    One monthly draw cycle. See app/services/draw_engine.py for the actual
    number-generation and matching logic and for the documented assumptions
    behind it - the PRD specifies match tiers and pool shares but leaves the
    concrete ticket/matching mechanism undefined, so this is our interpretation.

    status: "draft" (tickets exist, no winning numbers yet) ->
            "simulated" (admin previewed results, nothing persisted as final) ->
            "published" (winners finalized and visible to subscribers)
    """

    __tablename__ = "draws"
    __table_args__ = (UniqueConstraint("month", "year", name="uq_draw_month_year"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    draw_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "random" | "algorithmic"
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)

    winning_numbers: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    pool_5_match: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    pool_4_match: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    pool_3_match: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    jackpot_rollover_in: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # carried from a prior unclaimed 5-match

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    tickets = relationship("DrawTicket", back_populates="draw", cascade="all, delete-orphan")
    winners = relationship("Winner", back_populates="draw", cascade="all, delete-orphan")


class DrawTicket(Base):
    """
    A subscriber's 5 assigned numbers for one draw. Generated when a draw is
    created (or on-demand for a newly active subscriber) so every active
    subscriber automatically participates - the PRD doesn't describe a
    separate "buy a ticket" action, only that subscribers "participate in
    monthly draw-based prize pools" by virtue of subscribing.
    """

    __tablename__ = "draw_tickets"
    __table_args__ = (UniqueConstraint("draw_id", "user_id", name="uq_ticket_draw_user"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    draw_id: Mapped[str] = mapped_column(ForeignKey("draws.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    numbers: Mapped[list] = mapped_column(JSON, nullable=False)  # 5 unique ints, 1-49
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    draw = relationship("Draw", back_populates="tickets")


class Winner(Base):
    """
    A subscriber who matched 3, 4, or 5 numbers in a published draw.

    verification_status tracks the proof-upload / admin-review step (PRD 9);
    payment_status tracks payout separately, since a winner can be verified
    but not yet paid.
    """

    __tablename__ = "winners"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    draw_id: Mapped[str] = mapped_column(ForeignKey("draws.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    match_tier: Mapped[int] = mapped_column(Integer, nullable=False)  # 3, 4, or 5
    prize_amount: Mapped[float] = mapped_column(Float, nullable=False)

    proof_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    verification_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)  # pending|approved|rejected
    payment_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)  # pending|paid

    verified_by: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    draw = relationship("Draw", back_populates="winners")
    user = relationship("User", back_populates="winners", foreign_keys=[user_id])

import uuid
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Subscription(Base):
    """
    One row per user, tracking their plan and lifecycle state.

    Kept separate from User (rather than columns bolted onto it) so
    "who is a subscriber" and "is their plan currently active" can evolve
    independently - e.g. renewal/cancellation logic never has to touch the
    identity/auth model.
    """

    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    plan: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # "monthly" | "yearly"
    status: Mapped[str] = mapped_column(String(20), default="inactive", nullable=False)
    # inactive -> never subscribed | active | cancelled (active until renewal_date) | lapsed (payment failed/expired)

    amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # fee charged for current plan
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    renewal_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    user = relationship("User", back_populates="subscription")


class Payment(Base):
    """
    An append-only log of money movement (subscription charges and
    independent donations), used by the admin reports/analytics screen.
    Kept separate from Subscription/Donation so those tables stay about
    *current state* while this stays a *history*.
    """

    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)  # "subscription" | "donation"
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="succeeded", nullable=False)
    stripe_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

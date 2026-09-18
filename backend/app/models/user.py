import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    """
    A registered subscriber or administrator.

    Role is intentionally limited to {"subscriber", "admin"}: an account row
    only exists for people who have registered, so it can never represent
    the PRD's third role, "public visitor" - that role has no account at
    all and is simply the unauthenticated state of the API.

    Subscription status lives on the separate Subscription table, not here,
    so "does this user have an active plan" and "what can this user do"
    (role) stay independent questions.
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="subscriber", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    charity_id: Mapped[Optional[str]] = mapped_column(ForeignKey("charities.id"), nullable=True)
    charity_percentage: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    charity = relationship("Charity", back_populates="subscribers")
    scores = relationship("Score", back_populates="user", cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan")
    donations = relationship("Donation", back_populates="user", cascade="all, delete-orphan")
    winners = relationship("Winner", back_populates="user", foreign_keys="Winner.user_id", cascade="all, delete-orphan")

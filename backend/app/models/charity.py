import uuid
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Charity(Base):
    """
    A cause subscribers can direct part of their subscription fee to.

    image_url and the related CharityEvent rows exist specifically to cover
    PRD section 8.2 ("Profiles: description, images, and upcoming events
    such as golf days") - the original Mongo model only had name/
    description/website_url, which wasn't enough to render that page.
    """

    __tablename__ = "charities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    website_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    subscribers = relationship("User", back_populates="charity")
    events = relationship("CharityEvent", back_populates="charity", cascade="all, delete-orphan")
    donations = relationship("Donation", back_populates="charity", cascade="all, delete-orphan")


class CharityEvent(Base):
    """An upcoming event (e.g. a golf day) shown on a charity's profile page."""

    __tablename__ = "charity_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    charity_id: Mapped[str] = mapped_column(ForeignKey("charities.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    charity = relationship("Charity", back_populates="events")

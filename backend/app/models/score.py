import uuid
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Score(Base):
    """
    A single Stableford round for a user.

    Two constraints are enforced at the database level, not just in route
    code, per PRD section 5: the 1-45 Stableford range (CheckConstraint) and
    "only one score entry per date" (UniqueConstraint on user_id+date_played).
    Route code still validates both up front for a clean 400/409 error
    message, but the database is the actual guarantee against races.

    The "only the latest 5 scores are retained" rule is a query-time /
    write-time policy (delete the oldest once a user has more than 5),
    implemented in the scores route/service rather than the schema, since
    it's a business rule about retention, not a structural constraint.
    """

    __tablename__ = "scores"
    __table_args__ = (
        CheckConstraint("score >= 1 AND score <= 45", name="ck_score_stableford_range"),
        UniqueConstraint("user_id", "date_played", name="uq_score_user_date"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    date_played: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="scores")

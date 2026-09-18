"""
Database connection lifecycle: async engine, session factory, declarative
base, and the FastAPI dependency routes use to get a request-scoped session.

Works against SQLite (local dev/tests, zero external setup) or Postgres /
Supabase (production) purely by swapping DATABASE_URL - no code changes,
because the models avoid Postgres-only column types.
"""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.is_sqlite else {}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args=connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Shared declarative base for every SQLAlchemy model in the app."""
    pass


async def init_db() -> None:
    """
    Create tables directly from models.

    Convenient for local dev/tests. Production schema changes should go
    through Alembic migrations (see backend/alembic/) instead of relying on
    this, since create_all() cannot alter existing tables.
    """
    # Import every model so its class registers with the declarative Base
    # before create_all() and before any string-based relationship() (e.g.
    # User.donations = relationship("Donation", ...)) tries to resolve.
    from app.models import charity, donation, draw, score, subscription, user  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding one session per request."""
    async with AsyncSessionLocal() as session:
        yield session

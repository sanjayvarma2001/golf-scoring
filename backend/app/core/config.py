"""
Centralized application configuration.

Every value that differs between local development, testing, and production
(Vercel + Supabase) lives here and is read from environment variables. No
secret or connection string should ever be hardcoded in application code —
see backend/.env.example for the full list of variables this expects.
"""
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    APP_NAME: str = "Digital Heroes Golf Scoring API"
    ENVIRONMENT: str = "development"  # development | test | production
    API_V1_PREFIX: str = "/api/v1"
    FRONTEND_ORIGIN: str = "http://localhost:3000"

    # --- Database ---
    DATABASE_URL: str = "sqlite+aiosqlite:///./golf_scoring.db"

    # --- Auth / JWT ---
    JWT_SECRET_KEY: str = Field(..., min_length=16)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- Seed / bootstrap admin (used only by seed.py) ---
    ADMIN_EMAIL: str = "admin@digitalheroes.local"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = Field(..., min_length=8)

    # --- Stripe (subscription & payment) ---
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_PRICE_ID_MONTHLY: Optional[str] = None
    STRIPE_PRICE_ID_YEARLY: Optional[str] = None

    # --- Prize pool split (must sum to 100) ---
    POOL_SHARE_5_MATCH: float = 0.40
    POOL_SHARE_4_MATCH: float = 0.35
    POOL_SHARE_3_MATCH: float = 0.25

    # --- Charity ---
    MIN_CHARITY_PERCENTAGE: int = 10

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    """Settings are read once per process and cached; env vars only change on restart."""
    return Settings()

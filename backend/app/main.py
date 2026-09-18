from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.database.db import init_db
from app.routes import admin, auth, charities, donations, draws, scores, subscriptions, users, winners

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Local dev / tests: create tables directly from the models.
    # Production (Postgres/Supabase): schema is managed by Alembic migrations
    # instead (see backend/alembic/) - init_db() is skipped there so a
    # forgotten migration doesn't get silently papered over by create_all().
    if settings.is_sqlite:
        await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def health_check():
    """
    API status/health endpoint. The actual marketing landing page (PRD
    section 12: charity-first storytelling, subscribe CTA, etc.) is a
    frontend route, not a JSON API response - see frontend/app/page.tsx.
    """
    return {"status": "ok", "service": settings.APP_NAME}


for router in (
    auth.router,
    users.router,
    scores.router,
    charities.router,
    subscriptions.router,
    draws.router,
    donations.router,
    admin.router,
    winners.router,
):
    app.include_router(router, prefix=settings.API_V1_PREFIX)

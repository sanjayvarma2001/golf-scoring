from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.database.db import get_db
from app.models.charity import Charity
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserPublic

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(User).where((User.username == payload.username) | (User.email == payload.email))
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already registered")

    charity = await db.get(Charity, payload.charity_id)
    if charity is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected charity does not exist")

    if payload.charity_percentage < settings.MIN_CHARITY_PERCENTAGE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Charity contribution must be at least {settings.MIN_CHARITY_PERCENTAGE}%",
        )

    user = User(
        username=payload.username,
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="subscriber",
        charity_id=payload.charity_id,
        charity_percentage=payload.charity_percentage,
    )
    db.add(user)
    await db.flush()  # populate user.id before creating the dependent subscription row

    db.add(Subscription(user_id=user.id, status="inactive"))

    await db.commit()
    await db.refresh(user)

    token = create_access_token(user_id=user.id, username=user.username, role=user.role)
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user))


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == payload.username))
    user = result.scalar_one_or_none()

    # Same generic error for "no such user" and "wrong password" so a
    # failed login can't be used to enumerate valid usernames.
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been deactivated")

    token = create_access_token(user_id=user.id, username=user.username, role=user.role)
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user))

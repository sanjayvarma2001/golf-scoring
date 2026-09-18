from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)

    charity_id: str = Field(..., description="Charity selected at signup")
    charity_percentage: int = Field(default=10, ge=10, le=100, description="Minimum 10%, can be increased voluntarily")


class LoginRequest(BaseModel):
    username: str
    password: str


class UserPublic(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    role: str
    charity_id: Optional[str] = None
    charity_percentage: int

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic

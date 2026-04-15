# backend/app/models/auth_model.py
from pydantic import BaseModel, Field
from typing import Optional


class LoginRequest(BaseModel):
    """
    Request model for user login.
    """
    user_name: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """
    Response model returned after login attempt.
    """
    ok: bool
    token: Optional[str] = None
    role: Optional[str] = None
    user_name: Optional[str] = None
    error: Optional[str] = None


class MeResponse(BaseModel):
    """
    Response model for current user info (/me endpoint).
    """
    ok: bool
    user_name: Optional[str] = None
    role: Optional[str] = None
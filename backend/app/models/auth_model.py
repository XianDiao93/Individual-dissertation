# backend/app/models/auth_model.py
from pydantic import BaseModel, Field
from typing import Optional


class LoginRequest(BaseModel):
    user_name: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    ok: bool
    token: Optional[str] = None
    role: Optional[str] = None
    user_name: Optional[str] = None
    error: Optional[str] = None


class MeResponse(BaseModel):
    ok: bool
    user_name: Optional[str] = None
    role: Optional[str] = None
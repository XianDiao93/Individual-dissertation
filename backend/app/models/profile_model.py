from pydantic import BaseModel, Field
from typing import Optional


class UserProfile(BaseModel):
    uid: str = Field(..., min_length=1, max_length=50)
    user_name: Optional[str] = None
    role: Optional[str] = None

    phone: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    region: Optional[str] = None


class ProfileResponse(BaseModel):
    ok: bool
    profile: Optional[UserProfile] = None
    error: Optional[str] = None


class ProfileUpdateRequest(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    region: Optional[str] = None
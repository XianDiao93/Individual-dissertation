# backend/app/models/profile_model.py

from pydantic import BaseModel, Field
from typing import Optional


class UserProfile(BaseModel):
    """
    Stored at: user_data/user_data/<uid>/<uid>_profile.json

    Demo-friendly: keep it simple.
    """
    uid: str = Field(..., min_length=1, max_length=50)
    user_name: Optional[str] = None
    role: Optional[str] = None

    phone: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None


class ProfileResponse(BaseModel):
    ok: bool
    profile: Optional[UserProfile] = None
    error: Optional[str] = None


class ProfileUpdateRequest(BaseModel):
    """
    Only allow updating "profile" fields.
    Do NOT allow updating uid/role here (auth-managed).
    """
    phone: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
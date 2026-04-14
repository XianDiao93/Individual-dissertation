# backend/app/routers/profile_router.py

from fastapi import APIRouter, Header
from typing import Optional

from app.models.profile_model import ProfileResponse, UserProfile, ProfileUpdateRequest
from app.services.profile import ProfileService

from app.routers.auth_router import auth_service


router = APIRouter(prefix="/profile", tags=["profile"])
profile_service = ProfileService()


def _get_bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    if not authorization.startswith("Bearer "):
        return None
    return authorization.replace("Bearer ", "", 1).strip() or None


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    authorization: Optional[str] = Header(default=None),
) -> ProfileResponse:
    token = _get_bearer_token(authorization)
    if not token:
        return ProfileResponse(ok=False, error="missing_token")

    user = auth_service.get_current_user(token)
    if not user:
        return ProfileResponse(ok=False, error="invalid_token")

    profile_obj = profile_service.get_profile(
        user.uid,
        fallback_user_name=user.user_name,
        fallback_role=user.role,
    )
    return ProfileResponse(ok=True, profile=UserProfile(**profile_obj))


@router.put("/me", response_model=ProfileResponse)
async def update_my_profile(
    req: ProfileUpdateRequest,
    authorization: Optional[str] = Header(default=None),
) -> ProfileResponse:
    token = _get_bearer_token(authorization)
    if not token:
        return ProfileResponse(ok=False, error="missing_token")

    user = auth_service.get_current_user(token)
    if not user:
        return ProfileResponse(ok=False, error="invalid_token")

    profile_obj = profile_service.update_profile_fields(
        user.uid,
        phone=req.phone,
        email=req.email,
        name=req.name,
        company_name=req.company_name,
        region=req.region,
        fallback_user_name=user.user_name,
        fallback_role=user.role,
    )
    return ProfileResponse(ok=True, profile=UserProfile(**profile_obj))
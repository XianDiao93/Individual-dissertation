# backend/app/routers/auth_router.py

from fastapi import APIRouter, Header
from typing import Optional

from app.models.auth_model import LoginRequest, LoginResponse, MeResponse
from app.services.auth_instance import auth_service

router = APIRouter()

@router.post("/login", response_model=LoginResponse)
async def login_endpoint(req: LoginRequest) -> LoginResponse:
    result = auth_service.login(
        user_name=req.user_name,
        password=req.password
    )
    return LoginResponse(**result)


@router.get("/me", response_model=MeResponse)
async def me_endpoint(
    authorization: Optional[str] = Header(default=None)
) -> MeResponse:
    if not authorization or not authorization.startswith("Bearer "):
        return MeResponse(ok=False)

    token = authorization.replace("Bearer ", "")
    user = auth_service.get_current_user(token)

    if not user:
        return MeResponse(ok=False)

    return MeResponse(
        ok=True,
        user_name=user.user_name,
        role=user.role
    )


@router.post("/logout")
async def logout_endpoint(authorization: str = Header(default=None)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        auth_service.logout(token)
    return {"ok": True}
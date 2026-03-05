# backend/app/routers/email_router.py

from __future__ import annotations

from fastapi import APIRouter, Header, Query
from typing import Optional

from app.models.email_model import (
    EmailDetailResponse,
    EmailItem,
    EmailListResponse,
    EmailSummary,
    EmailUpdateRequest,
    EmailUpdateResponse,
    EmailDeleteResponse,   # NEW
)
from app.services.email import EmailService
from app.routers.auth_router import auth_service  # share same session store


router = APIRouter(prefix="/emails", tags=["emails"])
email_service = EmailService()


def _get_bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    if not authorization.startswith("Bearer "):
        return None
    token = authorization.replace("Bearer ", "", 1).strip()
    return token or None


@router.get("", response_model=EmailListResponse)
async def list_emails(
    archived: Optional[bool] = Query(default=None),
    authorization: Optional[str] = Header(default=None),
) -> EmailListResponse:
    try:
        token = _get_bearer_token(authorization)
        if not token:
            return EmailListResponse(ok=False, emails=[], error="missing_token")

        user = auth_service.get_current_user(token)
        if not user:
            return EmailListResponse(ok=False, emails=[], error="invalid_token")

        items = email_service.list_emails(user.uid, archived=archived)

        summaries = [EmailSummary(**x) for x in items]
        return EmailListResponse(ok=True, emails=summaries)

    except Exception as e:
        # IMPORTANT: return error instead of raising -> avoids 500 black box
        return EmailListResponse(ok=False, emails=[], error=str(e))


@router.get("/{email_id}", response_model=EmailDetailResponse)
async def get_email_detail(
    email_id: str,
    authorization: Optional[str] = Header(default=None),
) -> EmailDetailResponse:
    try:
        token = _get_bearer_token(authorization)
        if not token:
            return EmailDetailResponse(ok=False, error="missing_token")

        user = auth_service.get_current_user(token)
        if not user:
            return EmailDetailResponse(ok=False, error="invalid_token")

        e = email_service.get_email(user.uid, email_id)
        return EmailDetailResponse(ok=True, email=EmailItem(**e))

    except Exception as e:
        return EmailDetailResponse(ok=False, error=str(e))


@router.patch("/{email_id}", response_model=EmailUpdateResponse)
async def patch_email(
    email_id: str,
    req: EmailUpdateRequest,
    authorization: Optional[str] = Header(default=None),
) -> EmailUpdateResponse:
    try:
        token = _get_bearer_token(authorization)
        if not token:
            return EmailUpdateResponse(ok=False, error="missing_token")

        user = auth_service.get_current_user(token)
        if not user:
            return EmailUpdateResponse(ok=False, error="invalid_token")

        patch = req.model_dump(by_alias=True, exclude_unset=True)
        e = email_service.update_email(user.uid, email_id, patch)
        return EmailUpdateResponse(ok=True, email=EmailItem(**e))

    except Exception as e:
        return EmailUpdateResponse(ok=False, error=str(e))
    
@router.delete("/{email_id}", response_model=EmailDeleteResponse)
async def delete_email(
    email_id: str,
    authorization: Optional[str] = Header(default=None),
) -> EmailDeleteResponse:
    try:
        token = _get_bearer_token(authorization)
        if not token:
            return EmailDeleteResponse(ok=False, error="missing_token")

        user = auth_service.get_current_user(token)
        if not user:
            return EmailDeleteResponse(ok=False, error="invalid_token")

        email_service.delete_email(user.uid, email_id)
        return EmailDeleteResponse(ok=True)

    except Exception as e:
        return EmailDeleteResponse(ok=False, error=str(e))
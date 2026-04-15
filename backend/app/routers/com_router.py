from typing import Optional

from fastapi import APIRouter, Header

from app.config import PROJECT_ROOT
from app.models.com_model import ComRequest, ComResponse
from app.services.communication import generate_reply
from app.services.extraction import extract_trade_facts
from app.services.profile import ProfileService
from app.services.user_data_store import UserDataStore
from app.services.auth_instance import auth_service

try:
    from app.services.risk import analyze_risks
except Exception:
    analyze_risks = None

# Data store for saving generated emails
store = UserDataStore(str(PROJECT_ROOT))

router = APIRouter()

# Service for retrieving user profile data
profile_service = ProfileService()


def _get_bearer_token(authorization: Optional[str]) -> Optional[str]:
    """
    Extract Bearer token from Authorization header.
    """
    if not authorization:
        return None
    prefix = "Bearer "
    if authorization.startswith(prefix):
        return authorization[len(prefix):].strip()
    return None


def _default_risk_result() -> dict:
    """
    Return default risk result when risk analysis is unavailable or fails.
    """
    return {
        "decision": "CLEAR",
        "risk_tags": [],
        "risk": {
            "level": "unknown",
            "flags": [],
            "summary": None,
        },
    }


@router.post("/chat", response_model=ComResponse)
async def chat_endpoint(
    req: ComRequest,
    authorization: Optional[str] = Header(default=None),
) -> ComResponse:
    """
    Main chat endpoint:
    - Extract user profile (if authenticated)
    - Perform fact extraction
    - Run risk analysis (if available)
    - Generate reply using LLM
    - Store email record (if user is logged in)
    """
    user = None
    profile = {}

    # Resolve user from token
    token = _get_bearer_token(authorization)
    if token:
        user = auth_service.get_current_user(token)
        if user:
            profile = profile_service.get_profile(
                user.uid,
                fallback_user_name=user.user_name,
                fallback_role=user.role,
            )

    # Determine region (fallback to GB)
    profile_region = profile.get("region") or "GB"

    # Extract structured trade facts from message
    facts = extract_trade_facts(
        message=req.message,
        user_region=profile_region,
        preferred_language=None,
    )

    # Determine source region for reply generation
    detected_source_region = (
        facts.get("origin_country_code")
        or profile_region
    )

    # Run risk analysis if module is available
    if analyze_risks is not None:
        try:
            risk_result = analyze_risks(
                normalized_facts=facts,
                raw_message=req.message,
            )
        except Exception:
            risk_result = _default_risk_result()
    else:
        risk_result = _default_risk_result()

    # Generate business reply
    reply = generate_reply(
        message=req.message,
        language="auto",
        region=detected_source_region,
        tone="formal",
        reply_form="email",
        user_name=profile.get("user_name"),
        name=profile.get("name"),
        company_name=profile.get("company_name"),
        email=profile.get("email"),
        phone=profile.get("phone"),
        normalized_facts=facts,
        risk_result=risk_result,
    )

    # Save email record if user is authenticated
    if user:
        email_obj = {
            "source_region": detected_source_region,
            "language": facts.get("language") or "auto",
            "subject": None,
            "body": req.message,
            "reply": reply,
            "group_id": None,
            "from": None,
            "status": "replied",
            "risk": {
                "level": risk_result.get("risk", {}).get("level", "unknown"),
                "tags": risk_result.get("risk", {}).get("tags", []),
                "summary": risk_result.get("risk", {}).get("summary"),
            },
        }

        try:
            store.create_email(user.uid, email_obj)
        except Exception as e:
            print(f"[ERROR] Failed to save generated email for user {user.uid}: {repr(e)}")

    return ComResponse(reply=reply)
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

store = UserDataStore(str(PROJECT_ROOT))

router = APIRouter()

profile_service = ProfileService()


def _get_bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    prefix = "Bearer "
    if authorization.startswith(prefix):
        return authorization[len(prefix):].strip()
    return None


def _default_risk_result() -> dict:
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
    user = None
    profile = {}

    token = _get_bearer_token(authorization)
    if token:
        user = auth_service.get_current_user(token)
        if user:
            profile = profile_service.get_profile(
                user.uid,
                fallback_user_name=user.user_name,
                fallback_role=user.role,
            )

    region = profile.get("region") or req.region or "GB"

    facts = extract_trade_facts(
        message=req.message,
        user_region=region,
        preferred_language=req.language,
    )

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

    reply = generate_reply(
        message=req.message,
        language=req.language,
        region=region,
        tone=req.tone,
        reply_form=req.reply_form,
        user_name=profile.get("user_name"),
        name=profile.get("name"),
        email=profile.get("email"),
        phone=profile.get("phone"),
        normalized_facts=facts,
        risk_result=risk_result,
    )
    
    if user:
        email_obj = {
            "source_region": region,
            "language": req.language,
            "subject": None,
            "body": req.message,
            "reply": reply,
            "group_id": None,
            "from": profile.get("email"),
            "status": "draft",
            "risk": {
                "level": risk_result.get("risk", {}).get("level", "unknown"),
                "flags": risk_result.get("risk", {}).get("flags", []),
                "summary": risk_result.get("risk", {}).get("summary"),
            },
        }

        try:
            store.create_email(user.uid, email_obj)
        except Exception as e:
            print(f"[ERROR] Failed to save generated email for user {user.uid}: {repr(e)}")

    return ComResponse(reply=reply)
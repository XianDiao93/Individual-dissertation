# backend/app/services/communication.py
from typing import Any, Optional

from app.services.llm_client import generate_business_reply


def generate_reply(
    message: str,
    language: str = "auto",
    region: str = "GB",
    tone: str = "formal",
    reply_form: str = "email",
    user_name: Optional[str] = None,
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    normalized_facts: Optional[dict[str, Any]] = None,
    risk_result: Optional[dict[str, Any]] = None,
) -> str:
    """
    Business layer for communication.

    Parameters
    ----------
    message:
        Raw incoming message from user / customer.
    language:
        Preferred output language ("auto", "en", "zh", etc.)
    region:
        Sender/business region (ISO alpha-2, e.g. GB / US / CN)
    tone:
        Writing style ("formal", "neutral", "friendly")
    reply_form:
        Reply format ("email" or "chat")
    user_name / name / email / phone:
        Optional sender profile info
    normalized_facts:
        Structured facts extracted from the incoming message.
    risk_result:
        Risk analysis result produced by risk.py, e.g.
        {
            "decision": "WARN",
            "risk_tags": [...],
            "risk": {
                "level": "medium",
                "flags": [...],
                "summary": "..."
            }
        }
    """
    return generate_business_reply(
        message=message,
        language=language,
        region=region,
        tone=tone,
        reply_form=reply_form,
        user_name=user_name,
        name=name,
        email=email,
        phone=phone,
        normalized_facts=normalized_facts or {},
        risk_result=risk_result or {
            "decision": "CLEAR",
            "risk_tags": [],
            "risk": {
                "level": "unknown",
                "flags": [],
                "summary": None,
            },
        },
    )
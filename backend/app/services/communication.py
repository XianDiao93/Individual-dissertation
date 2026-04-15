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
    company_name: Optional[str] = None,
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
    user_name / name / company_name / email / phone:
        Optional sender profile info
    normalized_facts:
        Structured facts extracted from the incoming message.
        May include:
        - origin_country_name
        - origin_country_code
        - destination_country_name
        - destination_country_code
        - ambiguity_flags: list[str]
    risk_result:
        Risk analysis result produced by risk.py
    """
    # Make a safe copy of normalized facts
    safe_facts = dict(normalized_facts or {})
    ambiguity_flags = safe_facts.get("ambiguity_flags")

    # Ensure ambiguity_flags is always a list
    if not isinstance(ambiguity_flags, list):
        safe_facts["ambiguity_flags"] = []

    # Use default risk structure if no risk result is provided
    safe_risk = risk_result or {
        "decision": "CLEAR",
        "risk_tags": [],
        "risk": {
            "level": "unknown",
            "flags": [],
            "summary": None,
        },
        "by_category": {},
    }

    # Delegate reply generation to the LLM client layer
    return generate_business_reply(
        message=message,
        language=language,
        region=region,
        tone=tone,
        reply_form=reply_form,
        user_name=user_name,
        name=name,
        company_name=company_name,
        email=email,
        phone=phone,
        normalized_facts=safe_facts,
        risk_result=safe_risk,
    )
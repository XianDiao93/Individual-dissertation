# backend/app/services/communication.py
from app.services.llm_client import generate_business_reply


def generate_reply(
    message: str,
    language: str = "auto",
    region: str = "EU",
    tone: str = "formal",
    reply_form: str = "email",
) -> str:
    """
    Business layer for communication.

    - language: preferred output language ("auto", "en", "zh", etc.).
    - region: target business/cultural region (EU / US / ME / ASIA).
    - tone: writing style ("formal", "neutral", "friendly").
    - reply_form: reply format ("email" or "chat").
    """
    return generate_business_reply(
        message=message,
        language=language,
        region=region,
        tone=tone,
        reply_form=reply_form,
    )

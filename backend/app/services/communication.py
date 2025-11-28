from app.services.llm_client import generate_business_reply

def generate_email_reply(message, language="en", region="EU", tone="formal"):
    return generate_business_reply(
        message=message,
        language=language,
        region=region,
        tone=tone,
    )

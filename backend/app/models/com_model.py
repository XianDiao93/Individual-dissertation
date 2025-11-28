# backend/app/models/com_model.py
from pydantic import BaseModel


class ComRequest(BaseModel):
    message: str
    # Preferred output language
    language: str = "auto"
    # Target business/cultural region (EU/US/ME/ASIA, etc.)
    region: str = "EU"
    # Writing tone (formal / neutral / friendly)
    tone: str = "formal"
    # Reply form: "email" for full email, "chat" for short conversational reply
    reply_form: str = "email"


class ComResponse(BaseModel):
    reply: str

# backend/app/models/com_model.py
from pydantic import BaseModel


class ComRequest(BaseModel):
    message: str
    language: str = "auto"
    region: str = "EU"
    tone: str = "formal"
    reply_form: str = "email"


class ComResponse(BaseModel):
    reply: str
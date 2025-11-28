from pydantic import BaseModel

class ComRequest(BaseModel):
    message: str
    language: str = "en"
    region: str = "EU"
    tone: str = "formal"

class ComResponse(BaseModel):
    reply: str

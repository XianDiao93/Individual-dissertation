from fastapi import APIRouter

from app.models.com_model import ComRequest, ComResponse
from app.services.communication import generate_email_reply

router = APIRouter()

@router.post("/chat", response_model=ComResponse)
async def chat_endpoint(req: ComRequest):
    reply = generate_email_reply(
        message=req.message,
        language=req.language,
        region=req.region,
        tone=req.tone,
    )
    return ComResponse(reply=reply)

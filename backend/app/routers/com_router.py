from fastapi import APIRouter

from app.models.com_model import ComRequest, ComResponse
from app.services.communication import generate_reply

router = APIRouter()

# ⭐ 这里是 "/chat"，不要写 "/api/chat"
@router.post("/chat", response_model=ComResponse)
async def chat_endpoint(req: ComRequest) -> ComResponse:
    reply = generate_reply(
        message=req.message,
        language=req.language,
        region=req.region,
        tone=req.tone,
        reply_form=req.reply_form,
    )
    return ComResponse(reply=reply)

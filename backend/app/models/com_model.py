from pydantic import BaseModel

class ComRequest(BaseModel):
    message: str

class ComResponse(BaseModel):
    reply: str
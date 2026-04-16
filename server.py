from fastapi import FastAPI
from pydantic import BaseModel
from agent import kora

app = FastAPI()


class MessageRequest(BaseModel):
    message: str
    org_id: str
    user_id: str


class MessageResponse(BaseModel):
    reply: str


@app.post("/chat", response_model=MessageResponse)
async def chat(req: MessageRequest):
    """
    Your Next.js dashboard sends a POST request here.
    Kora processes it and returns a reply.
    """
    result = kora.invoke({
        "input": req.message,
        "org_id": req.org_id,
        "user_id": req.user_id,
    })
    return MessageResponse(reply=result["output"])


@app.get("/health")
def health():
    return {"status": "Kora is running"}
from pydantic import BaseModel, Field
from typing import Optional, List, Any


class KoraMessage(BaseModel):
    role: str       # "user" | "assistant"
    content: str


class KoraChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_history: List[KoraMessage] = Field(default_factory=list)
    session_id: Optional[str] = None


class ActionCard(BaseModel):
    label: str
    action: str
    payload: dict[str, Any]


class KoraChatResponse(BaseModel):
    message: str
    action_cards: Optional[List[ActionCard]] = None
    tools_used: Optional[List[str]] = None
    session_id: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user, CurrentUser
from app.services.agent_service import KoraAgentService
from app.schemas.schemas import KoraChatRequest, KoraChatResponse

router = APIRouter(prefix="/assistant", tags=["Kora Assistant"])

agent_service = KoraAgentService()


@router.post("/chat", response_model=KoraChatResponse)
async def chat(
    payload: KoraChatRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Send a message to Kora. The agent will:
    1. Understand your intent
    2. Call the appropriate backend API tool(s)
    3. Return a natural language response with optional action cards

    Example queries:
    - "How many appointments do I have today?"
    - "Show me all appointments for tomorrow"
    - "Which customers have an appointment this week?"
    - "What's my schedule for today?"
    - "Cancel the 3pm appointment with Jane"
    - "What time slots are available for a haircut tomorrow?"

    org_id is always taken from the JWT — users cannot access other orgs.
    """
    return await agent_service.chat(
        org_id=current_user.org_id,
        user_id=current_user.user_id,
        role=current_user.role,
        request=payload,
    )
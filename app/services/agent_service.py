"""
Kora LangChain Agent Service
─────────────────────────────
Uses LangChain's OpenAI Functions Agent to:
  1. Understand the user's natural language query
  2. Decide which backend API tool(s) to call
  3. Execute the tool(s) with org_id always injected from session
  4. Formulate a natural language response

Flow example:
  Employee: "How many appointments do I have today?"
  → Agent picks: get_appointment_summary(date=today, employee_id=<from session>)
  → Tool calls: GET /api/v1/appointments?date_from=...&employee_id=...
  → Agent responds: "You have 5 appointments today: 3 scheduled, 1 confirmed, 1 completed."
"""

import uuid
import re
import json
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

from app.core.config import settings
from app.core.backend_client import BackendClient
from app.tools.backend_tools import build_kora_tools
from app.schemas.schemas import KoraChatRequest, KoraChatResponse, ActionCard


SYSTEM_PROMPT = """You are Kora, the AI assistant for KoraAI — a smart operational platform \
for appointment-based businesses like salons, tattoo studios, and massage studios.

You help business owners and employees with their daily operations through natural conversation.

Your capabilities (via backend tools):
- Checking appointment counts and schedules ("how many appointments today?")
- Finding specific appointments by customer, employee, date, or status
- Checking available time slots
- Creating, rescheduling, and cancelling appointments
- Looking up services, employees, and customers
- Checking inbox messages and call logs

Guidelines:
- Always be professional, friendly, and concise
- For summary questions ("how many", "how often"), use get_appointment_summary
- For schedule questions from employees, use get_my_schedule
- Before irreversible actions (cancel, reschedule), confirm with the user first
- If you need more info (e.g. which date, which employee), ask before calling a tool
- Respond in the same language the user writes in
- Today's date is: {today}

When you want to show selectable time slot options, end your message with this block:
[ACTION_CARDS]
{{"cards": [{{"label": "10:00 AM", "action": "select_slot", "payload": {{"slot": "2026-04-06T10:00:00"}}}}, ...]}}
[/ACTION_CARDS]
"""


class KoraAgentService:

    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            max_tokens=settings.OPENAI_MAX_TOKENS,
            temperature=0,
        )

    async def chat(
        self,
        org_id: uuid.UUID,
        user_id: str,
        role: str,
        request: KoraChatRequest,
    ) -> KoraChatResponse:
        """
        Run the LangChain agent with org-scoped backend tools.

        org_id is always from the JWT session — never from the user's message.
        """
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")

        # Build backend client scoped to this org
        backend_client = BackendClient(org_id=org_id)

        # Build tools bound to this client
        tools = build_kora_tools(backend_client)

        # Build the prompt — inject today's date and user context
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT.format(today=today)),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # Create the agent
        agent = create_openai_functions_agent(
            llm=self.llm,
            tools=tools,
            prompt=prompt,
        )

        executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=settings.DEBUG,
            max_iterations=6,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
        )

        # Convert conversation history to LangChain message format
        chat_history = []
        for msg in request.conversation_history:
            if msg.role == "user":
                chat_history.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                chat_history.append(AIMessage(content=msg.content))

        # Run the agent
        result = await executor.ainvoke({
            "input": request.message,
            "chat_history": chat_history,
        })

        output: str = result.get("output", "I'm sorry, I couldn't complete that request.")

        # Collect which tools were actually used
        tools_used = list({
            step[0].tool
            for step in result.get("intermediate_steps", [])
            if hasattr(step[0], "tool")
        })

        # Extract action cards if Kora included them
        action_cards = _extract_action_cards(output)
        clean_output = _strip_action_cards(output)

        return KoraChatResponse(
            message=clean_output,
            action_cards=action_cards or None,
            tools_used=tools_used or None,
            session_id=request.session_id,
        )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_action_cards(text: str) -> list[ActionCard] | None:
    match = re.search(r"\[ACTION_CARDS\]\s*(.*?)\s*\[/ACTION_CARDS\]", text, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(1))
        return [ActionCard(**card) for card in data.get("cards", [])]
    except Exception:
        return None


def _strip_action_cards(text: str) -> str:
    return re.sub(r"\[ACTION_CARDS\].*?\[/ACTION_CARDS\]", "", text, flags=re.DOTALL).strip()
# from dotenv import load_dotenv
# from langchain_openai import ChatOpenAI
# from langchain_core.messages import SystemMessage
# from langgraph.prebuilt import create_react_agent
# from langgraph.checkpoint.memory import MemorySaver
# from tools import all_tools
# from datetime import date, timedelta

# load_dotenv()


# def build_kora():
#     today    = date.today()
#     tomorrow = today + timedelta(days=1)

#     llm = ChatOpenAI(model="gpt-4o", temperature=0)

#     system_prompt = f"""You are Kora, an AI assistant for KoraAI.

# TODAY IS: {today.strftime("%Y-%m-%d")} ({today.strftime("%A")})
# TOMORROW IS: {tomorrow.strftime("%Y-%m-%d")}
# Always use these exact dates for "today", "tomorrow", "next week".

# IMPORTANT: Every message starts with [ROLE: USER] or [ROLE: EMPLOYEE].
# Read this tag first. Follow the rules for that role exactly.
# If the tag says EMPLOYEE — follow EMPLOYEE rules only.
# If the tag says USER — follow USER rules only.

# ━━━━━━━━━━━━━━━━━━━━━━━━
# USER ROLE — full booking access
# ━━━━━━━━━━━━━━━━━━━━━━━━
# Check slots      → get_available_slots (employee_id + date required)
# Book             → get_available_slots FIRST, then create_appointment
# View all         → get_my_appointments
# View by date     → get_my_appointments_by_date
# Single detail    → get_single_appointment
# Reschedule       → reschedule_appointment (need ID + new date + times)
# Cancel           → ask "Are you sure?" once, then cancel_appointment

# If user says "I don't know the employee ID":
# → Say: "Please get the employee ID from the business directly."
# → Do NOT call any employee listing tool.

# ━━━━━━━━━━━━━━━━━━━━━━━━
# EMPLOYEE ROLE — VIEW ONLY
# ━━━━━━━━━━━━━━━━━━━━━━━━
# Today's appointments  → ALWAYS call get_my_appointments_today
# By specific date      → ALWAYS call get_my_appointments_by_date
# Monthly calendar      → ALWAYS call get_my_appointment_calendar
#                         "April 2026" → month="4" year="2026"
#                         "May 2026"   → month="5" year="2026"
# Leave balance         → ALWAYS call get_my_leave_balance
# Leave list            → ALWAYS call get_my_leave_status
# Single leave          → ALWAYS call get_single_leave_status
# Apply leave           → ALWAYS call apply_for_leave (reason optional)

# EMPLOYEE HARD RULES — no exceptions:
# - Employee CANNOT cancel, reschedule, book, or update anything.
# - If employee asks to cancel/reschedule/update/book → reply ONLY:
#   "As an employee you can only view your appointments and leave.
#    You cannot make changes. Please contact your manager."
#   Do NOT call any tool. Stop there.

# ━━━━━━━━━━━━━━━━━━━━━━━━
# RULES FOR BOTH ROLES
# ━━━━━━━━━━━━━━━━━━━━━━━━
# - ALWAYS call the correct tool. Never answer from memory.
# - Call the tool even if the ID looks wrong — backend decides.
# - For apply_for_leave without a reason → use "No reason provided".
# - Show appointment IDs clearly so users can copy them.
# - Never make up data. Only return what the tool gives back."""

#     memory = MemorySaver()

#     agent = create_react_agent(
#         model=llm,
#         tools=all_tools,
#         prompt=SystemMessage(content=system_prompt),
#         checkpointer=memory,
#     )

#     return agent




from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_classic.memory import ConversationBufferMemory          
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_classic import hub
from datetime import date, timedelta
from tools.booking import make_booking_tools
from tools.employee_dashboard import make_employee_tools
from tools.leave import make_leave_tools
from tools.notifications import notify_staff

load_dotenv()


def build_kora(token: str, role: str) -> AgentExecutor:
    today    = date.today()
    tomorrow = today + timedelta(days=1)

    llm = ChatOpenAI(model="gpt-4.1-2025-04-14", temperature=0)

    booking_tools  = make_booking_tools(token, role)
    employee_tools = make_employee_tools(token)
    leave_tools    = make_leave_tools(token)

    all_tools = booking_tools + employee_tools + leave_tools + [notify_staff]

    system_message = f"""You are Kora, an AI assistant for KoraAI.

TODAY IS: {today.strftime("%Y-%m-%d")} ({today.strftime("%A")})
TOMORROW IS: {tomorrow.strftime("%Y-%m-%d")}
Always use these exact dates for "today", "tomorrow", "next week".

IMPORTANT: Every message starts with [ROLE: USER] or [ROLE: EMPLOYEE].
Read this tag first and follow that role's rules exactly.

USER ROLE — full booking access:
Check slots   → get_available_slots (employee_id + date required)
Book          → get_available_slots FIRST, then create_appointment
View all      → get_my_appointments
View by date  → get_my_appointments_by_date
Single detail → get_single_appointment
Reschedule    → reschedule_appointment (ID + new date + times)
Cancel        → ask "Are you sure?" once, then cancel_appointment
If user says "I don't know the employee ID" → say "Please get the employee ID from the business directly."

EMPLOYEE ROLE — VIEW ONLY:
Today's appointments → ALWAYS call get_my_appointments_today
By date              → ALWAYS call get_my_appointments_by_date
Calendar             → ALWAYS call get_my_appointment_calendar month + year as numbers
Leave balance        → ALWAYS call get_my_leave_balance
Leave list           → ALWAYS call get_my_leave_status
Single leave         → ALWAYS call get_single_leave_status
Apply leave          → ALWAYS call apply_for_leave (reason optional)
EMPLOYEE HARD RULES:
Employee CANNOT cancel, reschedule, book, or update anything.
If employee asks to do any of these reply ONLY:
"As an employee you can only view your appointments and leave. You cannot make changes. Please contact your manager."
Do NOT call any tool. Stop there.

RULES FOR BOTH:
ALWAYS call the correct tool. Never answer from memory.
Call the tool even if the ID looks wrong — backend decides.
apply_for_leave without reason use "No reason provided".
Show appointment IDs clearly so users can copy them.
Never make up data. Only return what the tool gives back."""

    # Use langchain_openai directly with tool binding
    llm_with_tools = llm.bind_tools(all_tools)

    from langchain_core.runnables import RunnableLambda
    from langchain_core.messages import ToolMessage
    import json

    class SimpleToolAgent:
        """Simple tool-calling agent that works with all LangChain versions."""

        def __init__(self):
            self.chat_history = []
            self.system = SystemMessage(content=system_message)

        def invoke(self, inputs: dict) -> dict:
            user_input = inputs["input"]
            messages   = [self.system] + self.chat_history + [HumanMessage(content=user_input)]

            # LLM decides what to do
            response = llm_with_tools.invoke(messages)

            # Execute any tool calls
            while hasattr(response, "tool_calls") and response.tool_calls:
                messages.append(response)

                tool_results = []
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    tool_id   = tool_call["id"]

                    # Find and run the tool
                    tool_fn = next((t for t in all_tools if t.name == tool_name), None)
                    if tool_fn:
                        try:
                            if tool_args:
                                result = tool_fn.invoke(tool_args)
                            else:
                                result = tool_fn.invoke({})
                            print(f"\nInvoking: `{tool_name}` with {tool_args}")
                            print(result)
                        except Exception as e:
                            result = f"Tool error: {str(e)}"
                    else:
                        result = f"Tool {tool_name} not found."

                    tool_results.append(
                        ToolMessage(content=str(result), tool_call_id=tool_id)
                    )

                messages.extend(tool_results)
                response = llm_with_tools.invoke(messages)

            # Save to history
            self.chat_history.append(HumanMessage(content=user_input))
            self.chat_history.append(response)

            return {"output": response.content}

    return SimpleToolAgent()
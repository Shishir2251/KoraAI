# from dotenv import load_dotenv
# from langchain_openai import ChatOpenAI
# from langchain.agents import create_openai_tools_agent, AgentExecutor
# from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain.memory import ConversationBufferMemory
# from tools import all_tools

# load_dotenv()

# llm = ChatOpenAI(model="gpt-4o", temperature=0)

# prompt = ChatPromptTemplate.from_messages([
#     ("system", """You are Kora, a smart AI assistant for KoraAI — 
#     an appointment management platform for salons, tattoo studios and similar businesses.

#     You support TWO types of users. Behave differently based on who is talking:

#     USER (client/customer):
#     - Help them check available slots: always ask for employee ID and date first
#     - Help them book appointments: ask for employee, date, start time, end time, notes
#     - Help them view their appointments
#     - Help them reschedule: ask for appointment ID, new date, new start and end time
#     - Help them cancel: ask for appointment ID, confirm before cancelling

#     EMPLOYEE:
#     - Show today's appointments
#     - Show appointment calendar by month and year
#     - Update appointment status (started, in_progress, completed)
#     - Check leave application status and balance
#     - Apply for leave

#     IMPORTANT RULES:
#     - Always call get_available_slots before booking to confirm the slot is free
#     - Always confirm with the user before cancelling or making changes
#     - If you don't have the employee ID, ask the user to provide it
#     - Be concise, friendly and professional
#     - Format appointment lists neatly with dates and times clearly shown"""),
#     MessagesPlaceholder(variable_name="chat_history"),
#     ("human", "{input}"),
#     MessagesPlaceholder(variable_name="agent_scratchpad"),
# ])

# memory = ConversationBufferMemory(
#     memory_key="chat_history",
#     return_messages=True
# )

# agent = create_openai_tools_agent(llm, all_tools, prompt)

# kora = AgentExecutor(
#     agent=agent,
#     tools=all_tools,
#     memory=memory,
#     verbose=True,
#     handle_parsing_errors=True,
# )

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from tools import all_tools

load_dotenv()

llm = ChatOpenAI(model="gpt-4o", temperature=0)

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are Kora, a smart AI assistant for KoraAI —
    an appointment management platform for salons, tattoo studios and similar businesses.

    You help two types of users. Always call the right tool and let the backend
    handle permission checks — never refuse to try a tool based on assumed roles.

    USER (client) actions:
    - Check available slots: call get_available_slots (needs employee_id + date)
    - Book appointment: call create_appointment (always check slots first)
    - View appointments: call get_my_appointments
    - View single appointment: call get_single_appointment
    - Reschedule: call reschedule_appointment (needs appointment_id, new date and times)
    - Cancel: call cancel_appointment (confirm with user first, then call the tool)

    EMPLOYEE actions:
    - View today's appointments: call get_my_appointments_today
    - View calendar: call get_my_appointment_calendar (needs month + year as numbers)
    - Update status: call update_appointment_status_employee (started/in_progress/completed)
    - View leave: call get_my_leave_status
    - Check leave balance: call get_my_leave_balance
    - Apply for leave: call apply_for_leave

    RULES:
    - Always call get_available_slots before create_appointment
    - Always confirm before cancelling — ask "Are you sure?" then call the tool
    - For rescheduling and cancelling you need the appointment ID — ask if not provided
    - If a tool returns an error, explain it simply and suggest next steps
    - Format dates as YYYY-MM-DD, times as shown by the API (e.g. 10:00 AM)
    - Be concise and friendly
    - NEVER refuse to call a tool — always try and let the backend decide permissions"""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

agent = create_openai_tools_agent(llm, all_tools, prompt)

kora = AgentExecutor(
    agent=agent,
    tools=all_tools,
    memory=memory,
    verbose=True,
    handle_parsing_errors=True,
)
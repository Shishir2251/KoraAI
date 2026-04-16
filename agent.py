from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from tools import all_tools

load_dotenv()

llm = ChatOpenAI(model="gpt-4o", temperature=0)

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are Kora, a smart and friendly AI assistant
    for an appointment-based business management platform called KoraAI.
    You help business owners and employees with:
    - Checking today's appointments
    - Managing leave applications and checking their status
    - Booking, rescheduling and cancelling appointments
    - Managing employee information
    Always confirm with the user before making any changes.
    Be concise, clear and professional.
    When showing appointments or leave data, format it neatly."""),
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
    verbose=True
)
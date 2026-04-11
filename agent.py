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
    for an appointment-based business management platform.
    You help business owners and employees manage appointments,
    check schedules, apply for leave, and handle daily operations.
    Always confirm before making any changes.
    Be concise, clear and professional."""),
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
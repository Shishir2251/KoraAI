import sys
import uvicorn
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date, timedelta
import api_client
from agent import build_kora

app = FastAPI(title="KoraAI Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single global agent instance (MemorySaver handles per-thread memory)
kora = build_kora()
session_locks: dict = {}


def get_lock(session_id: str) -> asyncio.Lock:
    if session_id not in session_locks:
        session_locks[session_id] = asyncio.Lock()
    return session_locks[session_id]


class MessageRequest(BaseModel):
    message:    str
    role:       str = "user"
    session_id: str = "default"


class MessageResponse(BaseModel):
    reply:      str
    session_id: str


@app.post("/chat", response_model=MessageResponse)
async def chat(req: MessageRequest):
    role_label = "EMPLOYEE" if req.role == "employee" else "USER"
    full_input = f"[ROLE: {role_label}]\n{req.message}"

    lock = get_lock(req.session_id)

    async with lock:
        api_client.set_role(req.role)
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: kora.invoke(
                {"messages": [{"role": "user", "content": full_input}]},
                config={"configurable": {"thread_id": req.session_id}}
            )
        )

    reply = result["messages"][-1].content

    return MessageResponse(
        reply=reply,
        session_id=req.session_id
    )


@app.delete("/session/{session_id}")
def clear_session(session_id: str):
    if session_id in session_locks:
        del session_locks[session_id]
        return {"cleared": session_id}
    return {"message": "Session not found"}


@app.get("/health")
def health():
    today    = date.today().strftime("%Y-%m-%d")
    tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    return {
        "status":   "Kora is running",
        "today":    today,
        "tomorrow": tomorrow,
        "sessions": len(session_locks),
    }


def run_terminal():
    print("\nKora is ready.")
    print("Commands: 'role user', 'role employee', 'quit'\n")

    current_role = "user"
    api_client.set_role(current_role)

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye.")
            break

        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("Goodbye.")
            break
        if user_input.lower().startswith("role "):
            role = user_input.split(" ", 1)[1].strip().lower()
            if role in ["user", "employee"]:
                current_role = role
                api_client.set_role(role)
                print(f"[Switched to {role} mode]\n")
            else:
                print("Unknown role. Use 'role user' or 'role employee'\n")
            continue

        role_label = "EMPLOYEE" if current_role == "employee" else "USER"
        full_input = f"[ROLE: {role_label}]\n{user_input}"

        result = kora.invoke(
            {"messages": [{"role": "user", "content": full_input}]},
            config={"configurable": {"thread_id": "terminal"}}
        )
        print(f"\nKora: {result['messages'][-1].content}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        print("Starting Kora API server on http://localhost:8000")
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
    else:
        run_terminal()
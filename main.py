import sys
import os
import uvicorn
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date, timedelta
import api_client
from agent import build_kora


load_dotenv()
app = FastAPI(title="KoraAI Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions: dict     = {}
session_locks: dict = {}


def get_or_create_session(session_id: str):
    if session_id not in sessions:
        sessions[session_id]       = build_kora()
        session_locks[session_id]  = asyncio.Lock()
    return sessions[session_id], session_locks[session_id]


class MessageRequest(BaseModel):
    message:    str
    role:       str = "user"
    session_id: str = "default"


class MessageResponse(BaseModel):
    reply:      str
    session_id: str


MONGO_URI = os.getenv("MONGO_URI", "").strip()
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "test")
MONGO_USER_COLLECTION = os.getenv("MONGO_USER_COLLECTION", "users")
_mongo_client: MongoClient | None = None


def _get_users_collection():
    global _mongo_client
    if not MONGO_URI:
        return None
    if _mongo_client is None:
        _mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=4000)
    return _mongo_client[MONGO_DB_NAME][MONGO_USER_COLLECTION]


def _refresh_and_validate_user(refresh_token: str, expected_user_id: str) -> bool:
    users_collection = _get_users_collection()
    if users_collection is None:
        return False

    try:
        user_object_id = ObjectId(expected_user_id)
    except (InvalidId, TypeError):
        return False

    try:
        user_doc = users_collection.find_one(
            {"_id": user_object_id},
            {"_id": 1},
        )
        print(user_doc)
    except PyMongoError:
        return False

    return user_doc is not None


async def require_chat_auth(
    refresh_token: str = Header(..., alias="x-refresh-token"),
    user_id: str = Header(..., alias="x-user-id"),
) -> str:
    if not _refresh_and_validate_user(refresh_token, user_id):
        raise HTTPException(status_code=401, detail="Invalid refresh token or user_id")
    return user_id


@app.post("/chat", response_model=MessageResponse)
async def chat(req: MessageRequest):
    kora, lock = get_or_create_session(req.session_id)

    # Prepend role clearly so GPT-4o always knows who is speaking
    role_label = "EMPLOYEE" if req.role == "employee" else "USER"
    full_input = f"[ROLE: {role_label}]\n{req.message}"

    async with lock:
        api_client.set_role(req.role)
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: kora.invoke({"input": full_input})
        )

    return MessageResponse(
        reply=result["output"],
        session_id=req.session_id
    )


@app.delete("/session/{session_id}")
def clear_session(session_id: str):
    if session_id in sessions:
        del sessions[session_id]
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
        "sessions": len(sessions),
    }


def run_terminal():
    print("\nKora is ready.")
    print("Commands: 'role user', 'role employee', 'quit'\n")

    kora = build_kora()
    api_client.set_role("user")

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
                api_client.set_role(role)
                print(f"[Switched to {role} mode]\n")
            else:
                print("Unknown role. Use 'role user' or 'role employee'\n")
            continue

        response = kora.invoke({"input": user_input})
        print(f"\nKora: {response['output']}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        print("Starting Kora API server on http://localhost:8000")
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
    else:
        run_terminal()

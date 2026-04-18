# import sys
# import uvicorn
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from agent import kora

# # ── FastAPI app ──────────────────────────────────────────

# app = FastAPI(title="KoraAI Agent API")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],   # tighten this in production
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# class MessageRequest(BaseModel):
#     message: str
#     org_id: str = "default-org"
#     user_id: str = "default-user"


# class MessageResponse(BaseModel):
#     reply: str


# @app.post("/chat", response_model=MessageResponse)
# async def chat(req: MessageRequest):
#     """
#     Your Next.js dashboard sends POST requests here.
#     Body: { "message": "...", "org_id": "...", "user_id": "..." }
#     """
#     result = kora.invoke({"input": req.message})
#     return MessageResponse(reply=result["output"])


# @app.get("/health")
# def health():
#     return {"status": "Kora is running"}


# # ── Terminal chat mode ───────────────────────────────────

# def run_terminal():
#     print("\nKora is ready. Type your message or 'quit' to exit.\n")
#     while True:
#         user_input = input("You: ").strip()
#         if not user_input:
#             continue
#         if user_input.lower() == "quit":
#             print("Goodbye.")
#             break
#         response = kora.invoke({"input": user_input})
#         print(f"\nKora: {response['output']}\n")


# # ── Entry point ──────────────────────────────────────────

# if __name__ == "__main__":
#     if len(sys.argv) > 1 and sys.argv[1] == "server":
#         # Run as API server:  python main.py server
#         print("Starting Kora API server on http://localhost:8000")
#         uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
#     else:
#         # Run as terminal chat:  python main.py
#         run_terminal()

import sys
import os
import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv
from agent import kora
import api_client


load_dotenv()
app = FastAPI(title="KoraAI Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class MessageRequest(BaseModel):
    message: str
    role:    str = "user"   # "user" or "employee"


class MessageResponse(BaseModel):
    reply: str


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
async def chat(req: MessageRequest, _: str = Depends(require_chat_auth)):
    api_client.set_role(req.role)
    result = kora.invoke({"input": req.message})
    return MessageResponse(reply=result["output"])


@app.get("/health")
def health():
    return {"status": "Kora is running"}


def run_terminal():
    print("\nKora is ready.")
    print("Commands:")
    print("  'role user'     — switch to user (client) mode")
    print("  'role employee' — switch to employee mode")
    print("  'quit'          — exit\n")

    api_client.set_role("user")   # default start as user

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

        # Role switching command
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
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    else:
        run_terminal()

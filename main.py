import sys
import uvicorn
import asyncio
import time
import jwt
import os
from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date, timedelta
from dotenv import load_dotenv
from agent import build_kora

load_dotenv()

JWT_ACCESS_SECRET  = os.getenv("JWT_ACCESS_SECRET")
SESSION_TTL_SECONDS = 86400  # 24 hours — matches token expiry

app = FastAPI(title="KoraAI Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions: dict = {}


# ── Token validation ───────────────────────────────────────

def validate_and_decode(token: str) -> dict:
    """
    Decode and validate the accessToken using JWT_ACCESS_SECRET.
    Returns payload if valid.
    Raises 401 if expired or invalid.
    """
    try:
        payload = jwt.decode(
            token,
            JWT_ACCESS_SECRET,
            algorithms=["HS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expired. Please login again from the app to get a new token."
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {str(e)}"
        )


def extract_role(payload: dict) -> str:
    role = payload.get("role", "user")
    return "employee" if role == "employee" else "user"


def extract_user_id(payload: dict) -> str:
    return payload.get("_id", payload.get("id", "unknown"))


# ── Session management ─────────────────────────────────────

def get_or_create_session(session_id: str, token: str, role: str):
    if session_id not in sessions:
        sessions[session_id] = {
            "kora":      build_kora(token, role),
            "lock":      asyncio.Lock(),
            "last_used": time.time(),
            "role":      role,
        }
    else:
        sessions[session_id]["last_used"] = time.time()
    return sessions[session_id]["kora"], sessions[session_id]["lock"]


async def cleanup_expired_sessions():
    while True:
        await asyncio.sleep(300)  # every 5 minutes
        now     = time.time()
        expired = [
            sid for sid, data in sessions.items()
            if now - data["last_used"] > SESSION_TTL_SECONDS
        ]
        for sid in expired:
            del sessions[sid]
            print(f"[SESSION EXPIRED] {sid}")
        if expired:
            print(f"[CLEANUP] Removed {len(expired)} session(s). Active: {len(sessions)}")


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_expired_sessions())


# ── Response model ─────────────────────────────────────────

class MessageResponse(BaseModel):
    reply:      str
    session_id: str
    role:       str
    user_id:    str


# ── Main chat endpoint — 3 fields only ────────────────────

@app.post("/chat", response_model=MessageResponse)
async def chat(
    token:      str = Form(..., description="accessToken from your app login"),
    message:    str = Form(..., description="Your message to Kora"),
    session_id: str = Form("default", description="Conversation ID — keep same to maintain memory"),
):
    """
    3 fields:
    - token      → your accessToken
    - message    → what you want to say
    - session_id → any string, keep same across conversation
    """

    # Step 1 — Validate token locally. Raises 401 if invalid or expired.
    payload = validate_and_decode(token)

    # Step 2 — Extract role and user_id from token
    role    = extract_role(payload)
    user_id = extract_user_id(payload)

    print(f"[AUTH] user_id={user_id} role={role} session={session_id}")

    # Step 3 — Get or create session
    kora, lock = get_or_create_session(session_id, token, role)

    # Step 4 — Prepend role so agent knows who is talking
    role_label = "EMPLOYEE" if role == "employee" else "USER"
    full_input = f"[ROLE: {role_label}]\n{message}"

    # Step 5 — Run agent
    async with lock:
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: kora.invoke({"input": full_input})
        )

    return MessageResponse(
        reply=result["output"],
        session_id=session_id,
        role=role,
        user_id=user_id
    )


# ── Session clear ──────────────────────────────────────────

@app.delete("/session/{session_id}")
def clear_session(session_id: str):
    """Clear conversation memory for a session."""
    if session_id in sessions:
        del sessions[session_id]
        return {"cleared": session_id}
    return {"message": "Session not found"}


# ── Health check ───────────────────────────────────────────

@app.get("/health")
def health():
    today    = date.today().strftime("%Y-%m-%d")
    tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    return {
        "status":          "Kora is running",
        "today":           today,
        "tomorrow":        tomorrow,
        "active_sessions": len(sessions),
        "session_ttl_min": SESSION_TTL_SECONDS // 60,
    }


# ── Debug — see what is inside a token ────────────────────

@app.get("/validate-token")
async def validate_token(token: str):
    """
    Paste any token here to see if it is valid and what it contains.
    Useful for debugging before using /chat.
    """
    payload = validate_and_decode(token)
    return {
        "valid":   True,
        "user_id": extract_user_id(payload),
        "role":    payload.get("role"),
        "email":   payload.get("email"),
        "expires": payload.get("exp"),
    }


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        print("Starting Kora API server on http://localhost:8000")
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
    else:
        print("Run: python main.py server")
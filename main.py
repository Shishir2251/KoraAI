import sys
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import kora

# ── FastAPI app ──────────────────────────────────────────

app = FastAPI(title="KoraAI Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten this in production
    allow_methods=["*"],
    allow_headers=["*"],
)


class MessageRequest(BaseModel):
    message: str
    org_id: str = "default-org"
    user_id: str = "default-user"


class MessageResponse(BaseModel):
    reply: str


@app.post("/chat", response_model=MessageResponse)
async def chat(req: MessageRequest):
    """
    Your Next.js dashboard sends POST requests here.
    Body: { "message": "...", "org_id": "...", "user_id": "..." }
    """
    result = kora.invoke({"input": req.message})
    return MessageResponse(reply=result["output"])


@app.get("/health")
def health():
    return {"status": "Kora is running"}


# ── Terminal chat mode ───────────────────────────────────

def run_terminal():
    print("\nKora is ready. Type your message or 'quit' to exit.\n")
    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("Goodbye.")
            break
        response = kora.invoke({"input": user_input})
        print(f"\nKora: {response['output']}\n")


# ── Entry point ──────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        # Run as API server:  python main.py server
        print("Starting Kora API server on http://localhost:8000")
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    else:
        # Run as terminal chat:  python main.py
        run_terminal()
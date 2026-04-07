# KoraAI Agent

A LangChain-powered AI assistant that connects to your existing backend API and answers natural language queries from employees and business owners.

---

## What This Does

When an employee asks **"How many appointments do I have today?"**, this service:

1. Receives the message via `POST /api/v1/assistant/chat`
2. The LangChain agent decides to call the `get_appointment_summary` tool
3. The tool calls your backend: `GET /api/v1/appointments?date_from=...&employee_id=...`
4. Your backend returns the data
5. The agent formulates: *"You have 5 appointments today: 3 scheduled, 1 confirmed, 1 completed."*

**Your backend never changes.** This service sits in front of it and adds AI.

---

## Architecture

```
Frontend / Dashboard
        │
        ▼
┌───────────────────┐
│  KoraAI Agent     │  ← This service (FastAPI)
│  POST /chat       │
│                   │
│  LangChain Agent  │
│  + 12 Tools       │
└────────┬──────────┘
         │  HTTP calls with
         │  X-Org-ID + X-API-Secret
         ▼
┌───────────────────┐
│  Your Backend API │  ← Existing system (unchanged)
│  /appointments    │
│  /services        │
│  /customers       │
│  /users           │
│  /inbox           │
│  /calls           │
└───────────────────┘
         │
         ▼
    Your Database
```

---

## Setup

### 1. Clone and install

```bash
git clone <your-repo>
cd koraai_agent
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in:

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | Your OpenAI API key from platform.openai.com |
| `BACKEND_API_URL` | Base URL of your existing backend (e.g. `https://api.yourdomain.com`) |
| `BACKEND_API_SECRET` | A shared secret — set the same value on your backend under `X-API-Secret` header validation |
| `SECRET_KEY` | JWT secret for this service — run `openssl rand -hex 32` |

### 3. Run

```bash
uvicorn app.main:app --reload
```

API docs (DEBUG=true only): http://localhost:8000/docs

### 4. Run tests

```bash
pytest tests/ -v
```

Tests mock the backend API with `respx` — no real backend needed to run tests.

---

## What Your Backend Must Do

This service sends every request with two headers:

```
X-API-Secret: <your shared secret>
X-Org-ID: <uuid of the organization>
```

Your backend must:
1. Validate `X-API-Secret` matches what you configured
2. Use `X-Org-ID` to scope all queries — never trust user-provided org values

### Required Backend Endpoints

| Method | Path | Used by tool |
|---|---|---|
| `GET` | `/api/v1/appointments` | `get_appointments`, `get_appointment_summary`, `get_my_schedule` |
| `GET` | `/api/v1/appointments/availability` | `get_available_slots` |
| `POST` | `/api/v1/appointments` | `create_appointment` |
| `PATCH` | `/api/v1/appointments/{id}/reschedule` | `reschedule_appointment` |
| `PATCH` | `/api/v1/appointments/{id}/cancel` | `cancel_appointment` |
| `GET` | `/api/v1/services` | `get_services` |
| `GET` | `/api/v1/users` | `get_employees` |
| `GET` | `/api/v1/customers` | `get_customers` |
| `GET` | `/api/v1/inbox` | `get_inbox_messages` |
| `GET` | `/api/v1/calls` | `get_call_logs` |

---

## API Reference

### `POST /api/v1/assistant/chat`

Send a message to Kora. Requires a valid JWT in the `Authorization: Bearer <token>` header.

**Request:**
```json
{
  "message": "How many appointments do I have today?",
  "conversation_history": [
    { "role": "user", "content": "previous message" },
    { "role": "assistant", "content": "previous response" }
  ],
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "message": "You have 5 appointments today: 3 scheduled, 1 confirmed, 1 completed.",
  "action_cards": null,
  "tools_used": ["get_appointment_summary"],
  "session_id": "optional-session-id"
}
```

**Response with action cards** (when Kora shows selectable slots):
```json
{
  "message": "Here are available slots for tomorrow:",
  "action_cards": [
    { "label": "10:00 AM", "action": "select_slot", "payload": { "slot": "2026-04-08T10:00:00" } },
    { "label": "14:00 PM", "action": "select_slot", "payload": { "slot": "2026-04-08T14:00:00" } }
  ],
  "tools_used": ["get_available_slots"],
  "session_id": null
}
```

### `GET /health`

Returns service health status. No auth required.

---

## Example Queries

| Query | Tool Called | Backend Endpoint |
|---|---|---|
| "How many appointments today?" | `get_appointment_summary` | `GET /appointments` |
| "What's my schedule for tomorrow?" | `get_my_schedule` | `GET /appointments?employee_id=...` |
| "Show appointments for Jane Doe" | `get_appointments` | `GET /appointments` |
| "What services do we offer?" | `get_services` | `GET /services` |
| "Who are our employees?" | `get_employees` | `GET /users` |
| "Check availability for haircut tomorrow" | `get_available_slots` | `GET /appointments/availability` |
| "Cancel the 3pm appointment" | `cancel_appointment` | `PATCH /appointments/{id}/cancel` |
| "Reschedule Jane to 4pm" | `reschedule_appointment` | `PATCH /appointments/{id}/reschedule` |
| "How many missed calls today?" | `get_call_logs` | `GET /calls` |
| "Any unread messages?" | `get_inbox_messages` | `GET /inbox` |

---

## Available LangChain Tools

| Tool | Description |
|---|---|
| `get_appointments` | Fetch appointments with flexible filters |
| `get_appointment_summary` | Count and status breakdown for a date |
| `get_my_schedule` | Employee's own schedule |
| `get_available_slots` | Open time slots for service + employee + date |
| `create_appointment` | Book a new appointment |
| `reschedule_appointment` | Move appointment to new time |
| `cancel_appointment` | Cancel an appointment |
| `get_services` | List all services |
| `get_employees` | List all staff |
| `get_customers` | Search customers |
| `get_inbox_messages` | Read inbox |
| `get_call_logs` | Read call history |

---

## Security

- **org_id** is always extracted from the JWT — the LLM never controls it
- **X-API-Secret** is sent on every backend request — your backend validates it
- **X-Org-ID** is sent on every request — your backend scopes all queries to it
- The LLM only decides *which* tool to call and *what parameters* to pass — it never bypasses auth

---

## Project Structure

```
koraai_agent/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── pytest.ini
├── app/
│   ├── main.py                          # FastAPI app
│   ├── core/
│   │   ├── config.py                    # Settings from .env
│   │   ├── security.py                  # JWT helpers
│   │   ├── dependencies.py             # Auth middleware
│   │   └── backend_client.py           # HTTP client for backend API
│   ├── schemas/
│   │   └── schemas.py                   # Pydantic models
│   ├── tools/
│   │   └── backend_tools.py            # 12 LangChain tools
│   ├── services/
│   │   └── agent_service.py            # LangChain agent orchestration
│   └── api/v1/
│       ├── router.py
│       └── endpoints/
│           └── assistant.py            # POST /chat endpoint
└── tests/
    └── test_agent.py                    # Tests with mocked backend
```
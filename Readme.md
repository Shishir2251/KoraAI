# KoraAI — AI Agent


## Project Structure

```
koraai/
│
├── main.py                        # FastAPI server + terminal chat
├── agent.py                       # LangChain agent builder (build_kora)
├── api_client.py                  # Shared HTTP helper for backend API calls
├── .env                           # Environment variables (never commit this)
├── requirements.txt               # Python dependencies
│
├── tools/
│   ├── __init__.py                # Exports factory functions
│   ├── booking.py                 # User booking tools (make_booking_tools)
│   ├── employee_dashboard.py      # Employee view-only tools (make_employee_tools)
│   ├── leave.py                   # Leave management tools (make_leave_tools)
│   └── notifications.py           # Notification placeholder
```

---

## Requirements

- Python 3.11+
- OpenAI API key
- Backend: `https://backendkoraai.onrender.com`
- JWT secrets from the backend team

---

## Installation

```bash
# Clone the repo and enter the directory
cd koraai

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-your-openai-key-here
BASE_URL=https://backendkoraai.onrender.com
JWT_ACCESS_SECRET=your-jwt-access-secret-from-backend
```

> `JWT_ACCESS_SECRET` is used to decode and validate access tokens locally without calling the backend. Get this from your backend team.

---

## Running the Server

```bash
# FastAPI server (recommended)
python main.py server
```

Server runs at: `http://localhost:8000`
                'https://koraai-1.onrender.com'

Swagger UI: `http://localhost:8000/docs`
            'https://koraai-1.onrender.com/docs'

---

## Authentication

This system uses **JWT access tokens** issued by the backend. You do **not** need to log in through Kora. Instead:

1. Login via the backend directly to get your `accessToken`
2. Send the `accessToken` with every request to Kora
3. Kora decodes the token locally — no extra API call needed
4. Role (`user` or `employee`) and `user_id` are extracted automatically from the token

### How to get a token

```bash
curl -X POST https://backendkoraai.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "yourmail@gmail.com", "password": "yourpassword"}'
```

Response:
```json
{
  "data": {
    "accessToken": "eyJhbGci...",
    "refreshToken": "eyJhbGci..."
  }
}
```

Save both tokens. Use `accessToken` with every Kora request.

### When the token expires (after 1 day)

```bash
curl -X POST https://backendkoraai.onrender.com/api/v1/auth/refresh-token \
  -H "Content-Type: application/json" \
  -d '{"refreshToken": "eyJhbGci...your refresh token..."}'
```

Or use the helper script:

```bash
python refresh_tokens.py
```

---

## API Endpoints

### POST `/chat`

Send a message to Kora.

**Form fields:**

| Field   | Required | Description                        |
|---------|----------|------------------------------------|
| token   | Yes      | Your `accessToken` from login      |
| message | Yes      | What you want to ask Kora          |

`session_id` is automatically set to your `user_id` extracted from the token. Every user gets a unique session automatically.

**Example:**

```bash
curl -X POST http://localhost:8000/chat \
  -F "token=eyJhbGci...your accessToken..." \
  -F "message=What appointments do I have today?"
```

**Response:**

```json
{
  "reply": "You have 2 appointments today...",
  "session_id": "69e998e4728842c8afa2a1e3",
  "role": "user",
  "user_id": "69e998e4728842c8afa2a1e3"
}
```

---

### GET `/validate-token`

Check if a token is valid and see its contents.

```
GET /validate-token?token=eyJhbGci...
```

**Response:**

```json
{
  "valid": true,
  "user_id": "69e998e4728842c8afa2a1e3",
  "session_id": "69e998e4728842c8afa2a1e3",
  "role": "user",
  "email": "user@gmail.com",
  "expires": 1745889600
}
```

---

### DELETE `/session/{session_id}`

Clear conversation memory for a session.

```bash
curl -X DELETE http://localhost:8000/session/69e998e4728842c8afa2a1e3
```

---

### GET `/health`

Check server status.

```bash
curl http://localhost:8000/health
```

**Response:**

```json
{
  "status": "Kora is running",
  "today": "2026-04-26",
  "tomorrow": "2026-04-27",
  "active_sessions": 3,
  "session_ttl_min": 1440
}
```

---

## Session Memory

- Each user's `session_id` = their `user_id` from the JWT token
- Sessions are stored in RAM
- Sessions auto-expire after **24 hours** of inactivity
- Cleanup runs every 5 minutes in the background
- If you return within 24 hours with the same token, Kora remembers the full previous conversation
- Memory is lost only on server restart or after 24 hours idle

---

## Roles and Permissions

### User (client)

| Action | Tool |
|--------|------|
| Check available slots | `get_available_slots` |
| Book appointment | `create_appointment` |
| View all appointments | `get_my_appointments` |
| View by date | `get_my_appointments_by_date` |
| View single appointment | `get_single_appointment` |
| Reschedule | `reschedule_appointment` |
| Cancel | `cancel_appointment` |

### Employee (read-only)

| Action | Tool |
|--------|------|
| Today's appointments | `get_my_appointments_today` |
| Appointments by date | `get_my_appointments_by_date` |
| Monthly calendar | `get_my_appointment_calendar` |
| Leave balance | `get_my_leave_balance` |
| Leave applications | `get_my_leave_status` |
| Single leave status | `get_single_leave_status` |
| Apply for leave | `apply_for_leave` |

> Employees **cannot** cancel, reschedule, book, or update anything. All write actions are blocked at the tool level.

---

## Backend API Reference

All tools call these backend endpoints:

| Action | Method | Endpoint |
|--------|--------|----------|
| Available slots | GET | `/api/v1/appointment/available-slots?employee=ID&date=YYYY-MM-DD` |
| Create appointment | POST | `/api/v1/appointment/` |
| Get appointments | GET | `/api/v1/appointment?status=all` |
| Single appointment | GET | `/api/v1/appointment/{id}` |
| Reschedule | PUT | `/api/v1/appointment/{id}` |
| Cancel | PUT | `/api/v1/appointment/{id}` |
| Employee calendar | GET | `/api/v1/appointment/employee/calendar?month=4&year=2026` |
| Leave list | GET | `/api/v1/work/leave` |
| Leave balance | GET | `/api/v1/work/leave-balance` |
| Single leave | GET | `/api/v1/work/leave/{id}` |
| Apply leave | POST | `/api/v1/work/leave` |

---

## Example Conversations

### User — full booking flow

```
message: What slots are available with employee 69e8400fd0becfb24e0cc89f on 2026-05-01?
→ Kora lists free 1-hour slots

message: Book the 11:00 to 12:00 slot with notes Haircut
→ Kora books and returns appointment ID

message: Show all my appointments
→ Kora lists all appointments

message: Cancel appointment 69ec7b16cb13f12890b43e70
→ Kora asks "Are you sure?"

message: yes
→ Appointment cancelled
```

### Employee — view only

```
message: How many appointments do I have today?
→ Kora calls get_my_appointments_today

message: Show my calendar for April 2026
→ Kora calls get_my_appointment_calendar month=4 year=2026

message: What is my leave balance?
→ Casual Leave 10, Sick Leave 10, Leave Without Pay 0

message: Apply for sick leave from 2026-05-05 to 2026-05-07 reason fever
→ Leave submitted, returns leave ID

message: Cancel my appointment
→ "As an employee you can only view appointments..."
```

---

## Architecture

```
User/Employee
     │
     │  token + message
     ▼
FastAPI /chat endpoint (main.py)
     │
     │  validates JWT locally
     │  extracts role + user_id
     │  session_id = user_id
     ▼
LangChain Agent (agent.py)
     │
     │  GPT-4o decides which tool to call
     ▼
Tools (bound to user token + role)
     │
     │  HTTP calls with user's token
     ▼
Backend API (backendkoraai.onrender.com)
     │
     │  token scopes data to that user
     ▼
MongoDB Database
```

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| AI Agent | LangChain + OpenAI GPT-4o |
| API Server | FastAPI + Uvicorn |
| Auth | JWT (PyJWT) — local decode |
| HTTP Client | requests |
| Backend | Node.js REST API on Render |
| Database | MongoDB (managed by backend) |

---

## Known Behaviours

**JWT key length warning** — the backend JWT secret is 27 bytes (below the 32-byte recommendation). This is a warning only, tokens work correctly. Ask the backend team to use a longer secret in production.

**Render.com cold starts** — the backend runs on Render free tier which sleeps after inactivity. First request after idle may timeout. The HTTP client retries automatically up to 2 times.

**Memory on server restart** — session memory lives in RAM. Server restart clears all sessions. Users start fresh conversations automatically. MongoDB data is never affected.

---

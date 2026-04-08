"""
KoraAI Agent Test Suite
Tests use respx to mock the backend API — no real backend needed.
"""
import pytest
import respx
import httpx
import json
from httpx import AsyncClient, ASGITransport
from datetime import datetime

from app.main import app
from app.core.security import create_access_token
import uuid

ORG_ID = str(uuid.uuid4())
USER_ID = str(uuid.uuid4())
BACKEND_URL = "http://test-backend"


def auth_headers() -> dict:
    token = create_access_token(USER_ID, ORG_ID, "owner")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    monkeypatch.setenv("BACKEND_API_URL", BACKEND_URL)
    monkeypatch.setenv("BACKEND_API_SECRET", "test-secret")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-that-is-long-enough-32chars")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


class TestHealth:
    async def test_health_ok(self, client):
        r = await client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"


class TestBackendClient:
    """Test that BackendClient correctly injects org_id and secret into requests."""

    @respx.mock
    async def test_get_injects_org_header(self):
        from app.core.backend_client import BackendClient
        org = uuid.UUID(ORG_ID)
        client = BackendClient(org_id=org)

        route = respx.get(f"{BACKEND_URL}/api/v1/appointments").mock(
            return_value=httpx.Response(200, json={"appointments": [], "total": 0})
        )

        result = await client.get("/api/v1/appointments")
        assert route.called
        request = route.calls.last.request
        assert request.headers["X-Org-ID"] == ORG_ID
        assert request.headers["X-API-Secret"] == "test-secret"
        assert result["total"] == 0

    @respx.mock
    async def test_get_raises_on_error(self):
        from app.core.backend_client import BackendClient, BackendAPIError
        client = BackendClient(org_id=uuid.UUID(ORG_ID))

        respx.get(f"{BACKEND_URL}/api/v1/appointments").mock(
            return_value=httpx.Response(404, json={"detail": "Not found"})
        )

        with pytest.raises(BackendAPIError) as exc_info:
            await client.get("/api/v1/appointments")
        assert exc_info.value.status_code == 404


class TestBackendTools:
    """Test individual LangChain tools."""

    @respx.mock
    async def test_get_appointment_summary_today(self):
        from app.core.backend_client import BackendClient
        from app.tools.Backend_tools import build_kora_tools

        today = datetime.now().strftime("%Y-%m-%d")
        org = uuid.UUID(ORG_ID)

        respx.get(f"{BACKEND_URL}/api/v1/appointments").mock(
            return_value=httpx.Response(200, json={
                "appointments": [
                    {"status": "scheduled", "customer_name": "Jane", "employee_name": "Alice",
                     "service_name": "Haircut", "start_time": f"{today}T10:00:00", "id": str(uuid.uuid4())},
                    {"status": "scheduled", "customer_name": "Bob", "employee_name": "Alice",
                     "service_name": "Haircut", "start_time": f"{today}T11:00:00", "id": str(uuid.uuid4())},
                    {"status": "completed", "customer_name": "Eve", "employee_name": "Alice",
                     "service_name": "Color", "start_time": f"{today}T09:00:00", "id": str(uuid.uuid4())},
                ],
                "total": 3,
            })
        )

        client = BackendClient(org_id=org)
        tools = build_kora_tools(client)
        summary_tool = next(t for t in tools if t.name == "get_appointment_summary")

        result = await summary_tool.coroutine()
        assert "3 total" in result
        assert "Scheduled: 2" in result or "scheduled" in result.lower()
        assert "Completed: 1" in result or "completed" in result.lower()

    @respx.mock
    async def test_get_appointments_filters(self):
        from app.core.backend_client import BackendClient
        from app.tools.Backend_tools import build_kora_tools

        org = uuid.UUID(ORG_ID)

        respx.get(f"{BACKEND_URL}/api/v1/appointments").mock(
            return_value=httpx.Response(200, json={
                "appointments": [
                    {"status": "scheduled", "customer_name": "Jane Doe",
                     "employee_name": "Alice", "service_name": "Massage",
                     "start_time": "2026-04-10T14:00:00", "id": str(uuid.uuid4())},
                ],
                "total": 1,
            })
        )

        client = BackendClient(org_id=org)
        tools = build_kora_tools(client)
        appt_tool = next(t for t in tools if t.name == "get_appointments")

        result = await appt_tool.coroutine(date_from="2026-04-10", date_to="2026-04-10")
        assert "Jane Doe" in result
        assert "Massage" in result

    @respx.mock
    async def test_get_available_slots(self):
        from app.core.backend_client import BackendClient
        from app.tools.Backend_tools import build_kora_tools

        org = uuid.UUID(ORG_ID)
        svc_id = str(uuid.uuid4())
        emp_id = str(uuid.uuid4())

        respx.get(f"{BACKEND_URL}/api/v1/appointments/availability").mock(
            return_value=httpx.Response(200, json={
                "date": "2026-04-10",
                "slots": [
                    {"start_time": "2026-04-10T10:00:00", "end_time": "2026-04-10T11:00:00", "available": True},
                    {"start_time": "2026-04-10T11:00:00", "end_time": "2026-04-10T12:00:00", "available": False},
                    {"start_time": "2026-04-10T14:00:00", "end_time": "2026-04-10T15:00:00", "available": True},
                ]
            })
        )

        client = BackendClient(org_id=org)
        tools = build_kora_tools(client)
        slots_tool = next(t for t in tools if t.name == "get_available_slots")

        result = await slots_tool.coroutine(service_id=svc_id, employee_id=emp_id, date="2026-04-10")
        assert "10:00" in result
        assert "14:00" in result
        assert "11:00" not in result  # Not available

    @respx.mock
    async def test_get_services(self):
        from app.core.backend_client import BackendClient
        from app.tools.Backend_tools import build_kora_tools

        org = uuid.UUID(ORG_ID)
        respx.get(f"{BACKEND_URL}/api/v1/services").mock(
            return_value=httpx.Response(200, json=[
                {"id": str(uuid.uuid4()), "name": "Haircut", "duration_minutes": 60, "price": "45.00"},
                {"id": str(uuid.uuid4()), "name": "Color", "duration_minutes": 120, "price": "90.00"},
            ])
        )

        client = BackendClient(org_id=org)
        tools = build_kora_tools(client)
        svc_tool = next(t for t in tools if t.name == "get_services")

        result = await svc_tool.coroutine()
        assert "Haircut" in result
        assert "Color" in result
        assert "60 min" in result

    @respx.mock
    async def test_cancel_appointment(self):
        from app.core.backend_client import BackendClient
        from app.tools.Backend_tools import build_kora_tools

        org = uuid.UUID(ORG_ID)
        appt_id = str(uuid.uuid4())

        respx.patch(f"{BACKEND_URL}/api/v1/appointments/{appt_id}/cancel").mock(
            return_value=httpx.Response(200, json={"id": appt_id, "status": "cancelled"})
        )

        client = BackendClient(org_id=org)
        tools = build_kora_tools(client)
        cancel_tool = next(t for t in tools if t.name == "cancel_appointment")

        result = await cancel_tool.coroutine(appointment_id=appt_id, reason="Customer request")
        assert "cancelled" in result.lower()

    @respx.mock
    async def test_backend_error_handled_gracefully(self):
        from app.core.backend_client import BackendClient
        from app.tools.Backend_tools import build_kora_tools

        org = uuid.UUID(ORG_ID)
        respx.get(f"{BACKEND_URL}/api/v1/appointments").mock(
            return_value=httpx.Response(503, json={"detail": "Service unavailable"})
        )

        client = BackendClient(org_id=org)
        tools = build_kora_tools(client)
        appt_tool = next(t for t in tools if t.name == "get_appointments")

        # Tools should return error string, not raise — so agent can handle gracefully
        result = await appt_tool.coroutine()
        assert "error" in result.lower() or "Error" in result
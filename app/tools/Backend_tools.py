"""
LangChain Tools — Backend API Wrappers
───────────────────────────────────────
Each tool here maps to a real endpoint on your backend.

When an employee asks "How many appointments do I have today?"
→ LangChain agent picks get_appointments_tool
→ Tool calls your backend API with org_id from session
→ Returns data to the agent
→ Agent formulates a natural language response

SECURITY: org_id is injected from the authenticated session.
          The LLM never controls which org's data is fetched.
"""

from langchain.tools import StructuredTool
from pydantic import BaseModel, Field
from typing import Optional
from app.core.backend_client import BackendClient, BackendAPIError
from datetime import datetime, date
import uuid


# ── Input Schemas (LangChain uses these for validation) ───────────────────────

class GetAppointmentsInput(BaseModel):
    date_from: Optional[str] = Field(None, description="Start date in YYYY-MM-DD format. Use today's date for 'today' queries.")
    date_to: Optional[str] = Field(None, description="End date in YYYY-MM-DD format.")
    employee_id: Optional[str] = Field(None, description="UUID of employee to filter by.")
    customer_name: Optional[str] = Field(None, description="Filter by customer name (partial match).")
    status: Optional[str] = Field(None, description="Filter by status: scheduled, confirmed, completed, cancelled.")
    page: int = Field(1, description="Page number.")
    page_size: int = Field(20, description="Number of results per page.")


class GetAvailableSlotsInput(BaseModel):
    service_id: str = Field(..., description="UUID of the service.")
    employee_id: str = Field(..., description="UUID of the employee.")
    date: str = Field(..., description="Date to check in YYYY-MM-DD format.")


class CreateAppointmentInput(BaseModel):
    service_id: str = Field(..., description="UUID of the service.")
    employee_id: str = Field(..., description="UUID of the employee.")
    customer_id: str = Field(..., description="UUID of the customer.")
    start_time: str = Field(..., description="Start time in ISO 8601 format.")
    notes: Optional[str] = Field(None, description="Optional notes.")


class RescheduleAppointmentInput(BaseModel):
    appointment_id: str = Field(..., description="UUID of the appointment to reschedule.")
    new_start_time: str = Field(..., description="New start time in ISO 8601 format.")


class CancelAppointmentInput(BaseModel):
    appointment_id: str = Field(..., description="UUID of the appointment to cancel.")
    reason: Optional[str] = Field(None, description="Reason for cancellation.")


class GetServicesInput(BaseModel):
    active_only: bool = Field(True, description="Return only active services.")


class GetEmployeesInput(BaseModel):
    role: Optional[str] = Field(None, description="Filter by role: owner, employee.")


class GetCustomersInput(BaseModel):
    search: Optional[str] = Field(None, description="Search term for name, email, or phone.")
    page: int = Field(1, description="Page number.")
    page_size: int = Field(20, description="Results per page.")


class GetAppointmentSummaryInput(BaseModel):
    date: Optional[str] = Field(None, description="Date in YYYY-MM-DD format. Defaults to today.")
    employee_id: Optional[str] = Field(None, description="UUID of employee. If not provided, returns org-wide summary.")


# ── Tool Factory ──────────────────────────────────────────────────────────────

def build_kora_tools(client: BackendClient) -> list:
    """
    Build all LangChain tools bound to a specific org's BackendClient.
    Called once per request — client already has org_id injected.
    """

    # ── 1. Get Appointments ───────────────────────────────────────────────────
    async def get_appointments(
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        employee_id: Optional[str] = None,
        customer_name: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> str:
        """
        Fetch appointments from the backend. Supports date filters, employee filter,
        customer name search, and status filter. Use date_from=date_to=today for 'today' queries.
        """
        params = {"page": page, "page_size": page_size}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        if employee_id:
            params["employee_id"] = employee_id
        if status:
            params["status"] = status

        try:
            data = await client.get("/api/v1/appointments", params=params)
            appointments = data.get("appointments", [])

            # Apply client-side name filter if provided
            if customer_name:
                appointments = [
                    a for a in appointments
                    if customer_name.lower() in (a.get("customer_name") or "").lower()
                ]

            if not appointments:
                return "No appointments found matching the given criteria."

            lines = [f"Found {len(appointments)} appointment(s):"]
            for a in appointments:
                lines.append(
                    f"- [{a.get('status', '?').upper()}] {a.get('customer_name', 'Unknown')} "
                    f"with {a.get('employee_name', 'Unknown')} for {a.get('service_name', 'Unknown')} "
                    f"at {a.get('start_time', '?')} (ID: {a.get('id', '?')})"
                )
            if data.get("total", 0) > len(appointments):
                lines.append(f"(Showing {len(appointments)} of {data['total']} total)")
            return "\n".join(lines)

        except BackendAPIError as e:
            return f"Error fetching appointments: {e.detail}"

    # ── 2. Get Appointment Summary (count/stats for today etc.) ───────────────
    async def get_appointment_summary(
        date: Optional[str] = None,
        employee_id: Optional[str] = None,
    ) -> str:
        """
        Get a summary count of appointments for a specific date (default today).
        Useful for questions like 'how many appointments do I have today?'
        """
        target_date = date or datetime.now().strftime("%Y-%m-%d")
        params = {
            "date_from": f"{target_date}T00:00:00",
            "date_to": f"{target_date}T23:59:59",
            "page_size": 200,
        }
        if employee_id:
            params["employee_id"] = employee_id

        try:
            data = await client.get("/api/v1/appointments", params=params)
            appointments = data.get("appointments", [])
            total = data.get("total", len(appointments))

            # Group by status
            by_status: dict[str, int] = {}
            for a in appointments:
                s = a.get("status", "unknown")
                by_status[s] = by_status.get(s, 0) + 1

            label = "today" if target_date == datetime.now().strftime("%Y-%m-%d") else target_date
            lines = [f"Appointment summary for {label}: {total} total"]
            for status, count in sorted(by_status.items()):
                lines.append(f"  • {status.capitalize()}: {count}")
            return "\n".join(lines)

        except BackendAPIError as e:
            return f"Error fetching summary: {e.detail}"

    # ── 3. Get Available Slots ────────────────────────────────────────────────
    async def get_available_slots(
        service_id: str,
        employee_id: str,
        date: str,
    ) -> str:
        """Check open time slots for a service + employee on a given date."""
        try:
            data = await client.get("/api/v1/appointments/availability", params={
                "service_id": service_id,
                "employee_id": employee_id,
                "date": date,
            })
            slots = [s for s in data.get("slots", []) if s.get("available")]
            if not slots:
                return f"No available slots found on {date}."
            times = [s["start_time"][11:16] for s in slots]  # Extract HH:MM
            return f"Available slots on {date}: {', '.join(times)}"

        except BackendAPIError as e:
            return f"Error checking availability: {e.detail}"

    # ── 4. Create Appointment ─────────────────────────────────────────────────
    async def create_appointment(
        service_id: str,
        employee_id: str,
        customer_id: str,
        start_time: str,
        notes: Optional[str] = None,
    ) -> str:
        """Create a new appointment. Confirm all details with user before calling."""
        try:
            body = {
                "service_id": service_id,
                "employee_id": employee_id,
                "customer_id": customer_id,
                "start_time": start_time,
            }
            if notes:
                body["notes"] = notes

            data = await client.post("/api/v1/appointments", body=body)
            return (
                f"Appointment created successfully! "
                f"ID: {data['id']} | "
                f"{data.get('customer_name', 'Customer')} with {data.get('employee_name', 'Employee')} "
                f"for {data.get('service_name', 'service')} at {data.get('start_time', start_time)}"
            )
        except BackendAPIError as e:
            return f"Failed to create appointment: {e.detail}"

    # ── 5. Reschedule Appointment ─────────────────────────────────────────────
    async def reschedule_appointment(
        appointment_id: str,
        new_start_time: str,
    ) -> str:
        """Reschedule an appointment. Confirm with user before calling."""
        try:
            data = await client.patch(
                f"/api/v1/appointments/{appointment_id}/reschedule",
                body={"new_start_time": new_start_time},
            )
            return (
                f"Appointment rescheduled! "
                f"New time: {data.get('start_time', new_start_time)} | "
                f"Status: {data.get('status', 'scheduled')}"
            )
        except BackendAPIError as e:
            return f"Failed to reschedule: {e.detail}"

    # ── 6. Cancel Appointment ─────────────────────────────────────────────────
    async def cancel_appointment(
        appointment_id: str,
        reason: Optional[str] = None,
    ) -> str:
        """Cancel an appointment. Always confirm with user before calling."""
        try:
            params = {}
            if reason:
                params["reason"] = reason
            data = await client.patch(
                f"/api/v1/appointments/{appointment_id}/cancel",
                body=params,
            )
            return f"Appointment cancelled. ID: {data.get('id', appointment_id)}"
        except BackendAPIError as e:
            return f"Failed to cancel: {e.detail}"

    # ── 7. Get Services ───────────────────────────────────────────────────────
    async def get_services(active_only: bool = True) -> str:
        """Get the list of services offered by this business."""
        try:
            data = await client.get("/api/v1/services", params={"active_only": active_only})
            if not data:
                return "No services found."
            lines = ["Available services:"]
            for s in data:
                price = f"€{s['price']}" if s.get("price") else "no price set"
                lines.append(f"  • {s['name']} — {s['duration_minutes']} min, {price} (ID: {s['id']})")
            return "\n".join(lines)
        except BackendAPIError as e:
            return f"Error fetching services: {e.detail}"

    # ── 8. Get Employees ──────────────────────────────────────────────────────
    async def get_employees(role: Optional[str] = None) -> str:
        """Get the list of employees/staff at this business."""
        try:
            params = {}
            if role:
                params["role"] = role
            data = await client.get("/api/v1/users", params=params)
            users = data.get("users", [])
            if not users:
                return "No employees found."
            lines = ["Employees:"]
            for e in users:
                lines.append(f"  • {e['full_name']} — {e['role']} (ID: {e['id']})")
            return "\n".join(lines)
        except BackendAPIError as e:
            return f"Error fetching employees: {e.detail}"

    # ── 9. Get Customers ──────────────────────────────────────────────────────
    async def get_customers(
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> str:
        """Search customers by name, email, or phone."""
        try:
            params: dict = {"page": page, "page_size": page_size}
            if search:
                params["search"] = search
            data = await client.get("/api/v1/customers", params=params)
            customers = data.get("customers", [])
            if not customers:
                return "No customers found."
            lines = [f"Found {data.get('total', len(customers))} customer(s):"]
            for c in customers:
                contact = c.get("email") or c.get("phone") or "no contact"
                lines.append(f"  • {c['full_name']} — {contact} (ID: {c['id']})")
            return "\n".join(lines)
        except BackendAPIError as e:
            return f"Error fetching customers: {e.detail}"

    # ── 10. Get My Schedule (employee self-service) ───────────────────────────
    async def get_my_schedule(
        employee_id: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> str:
        """
        Get the schedule for a specific employee.
        Used when an employee asks 'what's my schedule?' or 'what appointments do I have?'
        """
        today = datetime.now().strftime("%Y-%m-%d")
        params = {
            "employee_id": employee_id,
            "date_from": f"{date_from or today}T00:00:00",
            "date_to": f"{date_to or today}T23:59:59",
            "page_size": 50,
        }
        try:
            data = await client.get("/api/v1/appointments", params=params)
            appointments = data.get("appointments", [])
            if not appointments:
                label = "today" if not date_from else date_from
                return f"No appointments scheduled for {label}."

            lines = [f"Schedule ({len(appointments)} appointment(s)):"]
            for a in appointments:
                time = (a.get("start_time") or "")[:16].replace("T", " ")
                lines.append(
                    f"  • {time} — {a.get('customer_name', 'Unknown')} "
                    f"({a.get('service_name', 'Unknown')}) [{a.get('status', '?')}]"
                )
            return "\n".join(lines)
        except BackendAPIError as e:
            return f"Error fetching schedule: {e.detail}"

    # ── 11. Get Inbox Messages ────────────────────────────────────────────────
    async def get_inbox_messages(
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> str:
        """Get inbox messages. Filter by status: unread, read, replied, archived."""
        try:
            params: dict = {"page": page, "page_size": page_size}
            if status:
                params["status"] = status
            data = await client.get("/api/v1/inbox", params=params)
            messages = data.get("messages", [])
            unread = data.get("unread_count", 0)

            if not messages:
                return "No messages in inbox."
            lines = [f"Inbox — {data.get('total', 0)} total, {unread} unread:"]
            for m in messages:
                received = (m.get("received_at") or "")[:10]
                lines.append(
                    f"  • [{m.get('status', '?').upper()}] {m.get('sender_name', 'Unknown')} "
                    f"via {m.get('channel', '?')} on {received}: {(m.get('body') or '')[:60]}..."
                )
            return "\n".join(lines)
        except BackendAPIError as e:
            return f"Error fetching inbox: {e.detail}"

    # ── 12. Get Call Logs ─────────────────────────────────────────────────────
    async def get_call_logs(
        outcome: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> str:
        """Get call logs. Filter by outcome: answered, missed, voicemail, rejected."""
        try:
            params: dict = {"page": page, "page_size": page_size}
            if outcome:
                params["outcome"] = outcome
            data = await client.get("/api/v1/calls", params=params)
            calls = data.get("calls", [])
            missed = data.get("missed_count", 0)

            if not calls:
                return "No call logs found."
            lines = [f"Call logs — {data.get('total', 0)} total, {missed} missed:"]
            for c in calls:
                started = (c.get("started_at") or "")[:16].replace("T", " ")
                dur = c.get("duration_seconds", 0)
                lines.append(
                    f"  • [{c.get('outcome', '?').upper()}] {c.get('caller_name') or c.get('caller_number', 'Unknown')} "
                    f"at {started} ({dur}s)"
                )
            return "\n".join(lines)
        except BackendAPIError as e:
            return f"Error fetching calls: {e.detail}"

    # ── Assemble all tools ────────────────────────────────────────────────────
    return [
        StructuredTool.from_function(
            coroutine=get_appointments,
            name="get_appointments",
            description=(
                "Fetch appointments from the backend. Can filter by date range, employee, "
                "customer name, or status. For 'today' queries set date_from and date_to to today's date."
            ),
            args_schema=GetAppointmentsInput,
        ),
        StructuredTool.from_function(
            coroutine=get_appointment_summary,
            name="get_appointment_summary",
            description=(
                "Get a count and status breakdown of appointments for a given date (default today). "
                "Use this when someone asks 'how many appointments today?' or similar summary questions."
            ),
            args_schema=GetAppointmentSummaryInput,
        ),
        StructuredTool.from_function(
            coroutine=get_available_slots,
            name="get_available_slots",
            description="Check available time slots for a service + employee on a given date.",
            args_schema=GetAvailableSlotsInput,
        ),
        StructuredTool.from_function(
            coroutine=create_appointment,
            name="create_appointment",
            description="Create a new appointment. Always confirm all details with the user first.",
            args_schema=CreateAppointmentInput,
        ),
        StructuredTool.from_function(
            coroutine=reschedule_appointment,
            name="reschedule_appointment",
            description="Reschedule an existing appointment to a new time. Confirm with user first.",
            args_schema=RescheduleAppointmentInput,
        ),
        StructuredTool.from_function(
            coroutine=cancel_appointment,
            name="cancel_appointment",
            description="Cancel an appointment. Always confirm with user before calling this.",
            args_schema=CancelAppointmentInput,
        ),
        StructuredTool.from_function(
            coroutine=get_services,
            name="get_services",
            description="Get all services offered by this business with their duration and price.",
            args_schema=GetServicesInput,
        ),
        StructuredTool.from_function(
            coroutine=get_employees,
            name="get_employees",
            description="Get all employees/staff of this business.",
            args_schema=GetEmployeesInput,
        ),
        StructuredTool.from_function(
            coroutine=get_customers,
            name="get_customers",
            description="Search customers by name, email, or phone number.",
            args_schema=GetCustomersInput,
        ),
        StructuredTool.from_function(
            coroutine=get_my_schedule,
            name="get_my_schedule",
            description=(
                "Get the appointment schedule for a specific employee. "
                "Use this when an employee asks about their own schedule or appointments."
            ),
            args_schema=GetAppointmentsInput,
        ),
        StructuredTool.from_function(
            coroutine=get_inbox_messages,
            name="get_inbox_messages",
            description="Get inbox messages. Can filter by status (unread, read, replied, archived).",
            args_schema=GetCustomersInput,
        ),
        StructuredTool.from_function(
            coroutine=get_call_logs,
            name="get_call_logs",
            description="Get call logs. Can filter by outcome (answered, missed, voicemail, rejected).",
            args_schema=GetCustomersInput,
        ),
    ]
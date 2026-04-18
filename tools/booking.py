from langchain.tools import tool
from api_client import api_get, api_post, api_patch
from datetime import datetime


def _format_date(raw: str) -> str:
    """Convert 2026-04-19T18:00:00.000Z to 2026-04-19"""
    if not raw:
        return "N/A"
    return raw[:10]


@tool
def get_available_slots(employee_id: str, date: str) -> str:
    """
    Check available time slots for a specific employee on a specific date.
    Always call this FIRST before booking an appointment.
    Inputs:
      employee_id — MongoDB _id of the employee
      date        — YYYY-MM-DD e.g. '2026-04-20'
    """
    result = api_get(
        "/api/v1/appointment/available-slots",
        params={"employee": employee_id, "date": date}
    )

    if "error" in result:
        return f"Could not fetch slots: {result['error']}"

    data = result.get("data", result)
    slots = []

    # Handle both shapes: list of dicts or nested under "slots"
    if isinstance(data, dict):
        slots = data.get("slots", data.get("availableSlots", []))
    elif isinstance(data, list):
        slots = data

    if not slots:
        return f"No available slots for employee {employee_id} on {date}."

    available = [s for s in slots if s.get("isAvailable", True) and not s.get("isBooked", False)]

    if not available:
        return f"All slots are booked for employee {employee_id} on {date}."

    lines = [
        f"  - {s.get('startTime','?')} to {s.get('endTime','?')}"
        for s in available
    ]

    return (
        f"Available slots for employee {employee_id} on {date}:\n"
        + "\n".join(lines)
        + f"\n\nTo book say: 'Book appointment on {date} from [time] to [time]'"
    )


@tool
def create_appointment(
    employee_id: str,
    appointment_date: str,
    start_time: str,
    end_time: str,
    booking_notes: str = "",
) -> str:
    """
    Book a new appointment. Only a USER (client) can book.
    Make sure get_available_slots was called first.
    Inputs:
      employee_id      — _id of the employee to book with
      appointment_date — YYYY-MM-DD e.g. '2026-04-20'
      start_time       — e.g. '10:00 AM'
      end_time         — e.g. '11:00 AM'
      booking_notes    — optional e.g. 'Haircut, short sides'
    """
    body = {
        "employee":        employee_id,
        "appointmentDate": appointment_date,
        "startTime":       start_time,
        "endTime":         end_time,
        "bookingNotes":    booking_notes,
    }

    result = api_post("/api/v1/appointment/", body)

    if "error" in result:
        # Surface friendly message if role is wrong
        err_str = str(result["error"])
        if "Only user" in err_str or "403" in err_str:
            return (
                "Booking failed: This action requires a USER account token.\n"
                "Your current token may be an employee or owner account.\n"
                "Please make sure USER_TOKEN in your .env is from a 'user' role account."
            )
        return f"Booking failed: {result['error']}"

    data   = result.get("data", result)
    appt_id = data.get("_id", "N/A") if isinstance(data, dict) else "N/A"

    return (
        f"Appointment booked!\n"
        f"Date          : {appointment_date}\n"
        f"Time          : {start_time} - {end_time}\n"
        f"Employee      : {employee_id}\n"
        f"Notes         : {booking_notes or 'None'}\n"
        f"Appointment ID: {appt_id}\n"
        f"Save this ID to reschedule or cancel later."
    )


@tool
def get_my_appointments(status: str = "all") -> str:
    """
    Get appointments for the logged-in user or employee.
    Input:
      status — 'all', 'upcoming', 'completed', 'cancelled' (default: 'all')
    """
    result = api_get("/api/v1/appointment/", params={"status": status})

    if "error" in result:
        return f"Could not fetch appointments: {result['error']}"

    appointments = result.get("data") or result.get("appointments") or []
    if isinstance(appointments, dict):
        appointments = appointments.get("data") or appointments.get("appointments") or []

    if not appointments:
        return f"No appointments found with status '{status}'."

    lines = []
    for i, a in enumerate(appointments, 1):
        lines.append(
            f"{i}. ID     : {a.get('_id','N/A')}\n"
            f"   Date   : {_format_date(a.get('appointmentDate', a.get('date','')))}\n"
            f"   Time   : {a.get('startTime','N/A')} - {a.get('endTime','N/A')}\n"
            f"   Status : {a.get('status','N/A').upper()}\n"
            f"   Notes  : {a.get('bookingNotes', a.get('notes','None'))}"
        )

    return f"Your appointments ({len(lines)} found):\n\n" + "\n\n".join(lines)


@tool
def get_single_appointment(appointment_id: str) -> str:
    """
    Get full details of one appointment by ID.
    Works for both user and employee tokens.
    Input: appointment_id — MongoDB _id
    """
    result = api_get(f"/api/v1/appointment/{appointment_id}")

    if "error" in result:
        return f"Could not fetch appointment: {result['error']}"

    a = result.get("data", result)
    if isinstance(a, list):
        a = a[0] if a else {}

    employee = a.get("employee", {})
    emp_name = employee.get("name", str(employee)) if isinstance(employee, dict) else str(employee)

    client = a.get("client", a.get("user", {}))
    client_name = client.get("name", str(client)) if isinstance(client, dict) else str(client)

    return (
        f"Appointment Details:\n"
        f"ID       : {a.get('_id','N/A')}\n"
        f"Date     : {_format_date(a.get('appointmentDate', a.get('date','')))}\n"
        f"Time     : {a.get('startTime','N/A')} - {a.get('endTime','N/A')}\n"
        f"Status   : {a.get('status','N/A').upper()}\n"
        f"Employee : {emp_name}\n"
        f"Client   : {client_name}\n"
        f"Notes    : {a.get('bookingNotes', a.get('notes','None'))}"
    )


@tool
def reschedule_appointment(
    appointment_id: str,
    new_date: str,
    new_start_time: str,
    new_end_time: str,
) -> str:
    """
    Reschedule an appointment to a new date and time.
    Only the user/client who booked can reschedule.
    Inputs:
      appointment_id — _id of the appointment
      new_date       — YYYY-MM-DD e.g. '2026-04-22'
      new_start_time — e.g. '12:00 PM'
      new_end_time   — e.g. '1:00 PM'
    """
    body = {
        "appointmentDate": new_date,
        "startTime":       new_start_time,
        "endTime":         new_end_time,
    }

    result = api_patch(f"/api/v1/appointment/{appointment_id}", body)

    if "error" in result:
        err_str = str(result["error"])
        if "timeout" in err_str.lower() or "timed out" in err_str.lower():
            return (
                "Request timed out — the server may be slow (Render free tier).\n"
                "Please try again in 30 seconds."
            )
        return f"Reschedule failed: {result['error']}"

    return (
        f"Appointment rescheduled!\n"
        f"Appointment ID : {appointment_id}\n"
        f"New Date       : {new_date}\n"
        f"New Time       : {new_start_time} - {new_end_time}"
    )


@tool
def cancel_appointment(appointment_id: str) -> str:
    """
    Cancel an appointment. Only the user/client who booked can cancel.
    Cannot cancel an appointment that is already completed or started.
    Input: appointment_id — MongoDB _id. Always confirm with user before calling.
    """
    # Pre-check status before attempting cancel
    check = api_get(f"/api/v1/appointment/{appointment_id}")
    if "error" not in check:
        appt = check.get("data", check)
        if isinstance(appt, list):
            appt = appt[0] if appt else {}
        current_status = appt.get("status", "").lower()
        if current_status in ["completed", "started", "in_progress"]:
            return (
                f"Cannot cancel this appointment.\n"
                f"Current status is: {current_status.upper()}\n"
                f"Only upcoming appointments can be cancelled."
            )

    result = api_patch(f"/api/v1/appointment/{appointment_id}", {"status": "cancelled"})

    if "error" in result:
        err_str = str(result["error"])
        if "completed" in err_str.lower():
            return "Cannot cancel — this appointment is already completed."
        if "timeout" in err_str.lower():
            return "Request timed out. Please try again in 30 seconds."
        return f"Cancellation failed: {result['error']}"

    return (
        f"Appointment cancelled.\n"
        f"ID: {appointment_id}\n"
        f"Status: CANCELLED"
    )


@tool
def update_appointment_status_employee(
    appointment_id: str,
    status: str,
) -> str:
    """
    Update appointment status as an employee.
    Use this to mark progress on an appointment.
    Inputs:
      appointment_id — _id of the appointment
      status         — one of: 'started', 'in_progress', 'completed'
    """
    allowed = ["started", "in_progress", "completed"]
    if status.lower() not in allowed:
        return f"Invalid status '{status}'. Allowed: {', '.join(allowed)}"

    result = api_patch(
        f"/api/v1/appointment/{appointment_id}",
        {"status": status.lower()}
    )

    if "error" in result:
        if "timeout" in str(result["error"]).lower():
            return "Request timed out. Please try again."
        return f"Status update failed: {result['error']}"

    return f"Appointment {appointment_id} is now marked as: {status.upper()}"
@tool
def get_my_appointments_by_date(date: str) -> str:
    """
    Get all appointments for a specific date (not just today).
    Use this when the user asks about appointments on a particular date.
    Input: date — YYYY-MM-DD e.g. '2026-04-19'
    """
    result = api_get("/api/v1/appointment/", params={"status": "all"})

    if "error" in result:
        return f"Could not fetch appointments: {result['error']}"

    all_appts = result.get("data") or result.get("appointments") or []
    if isinstance(all_appts, dict):
        all_appts = all_appts.get("data") or all_appts.get("appointments") or []

    # Filter by requested date
    filtered = [
        a for a in all_appts
        if _format_date(a.get("appointmentDate", a.get("date", ""))) == date
    ]

    if not filtered:
        return f"No appointments found on {date}."

    lines = []
    for a in filtered:
        lines.append(
            f"  - {a.get('startTime','N/A')} to {a.get('endTime','N/A')} "
            f"| Status: {a.get('status','N/A').upper()} "
            f"| Notes: {a.get('bookingNotes', a.get('notes','None'))} "
            f"| ID: {a.get('_id','N/A')}"
        )

    return (
        f"Appointments on {date} ({len(lines)} found):\n"
        + "\n".join(lines)
    )
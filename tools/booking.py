from langchain.tools import tool
from api_client import api_get, api_post, api_patch


@tool
def get_available_slots(employee_id: str, date: str) -> str:
    """
    Check available time slots for a specific employee on a specific date.
    This is STEP 1 — always call this before booking.
    Inputs:
      employee_id — the MongoDB _id of the employee (required)
      date        — date in YYYY-MM-DD format e.g. '2026-04-20'
    """
    result = api_get(
        "/api/v1/appointment/available-slots",
        params={"employee": employee_id, "date": date}
    )

    if "error" in result:
        return (
            f"Could not fetch available slots.\n"
            f"Error: {result['error']}\n"
            f"Make sure employee_id and date are correct."
        )

    data = result.get("data", result.get("slots", result.get("availableSlots", [])))

    if not data:
        return f"No available slots found for employee {employee_id} on {date}. They may be fully booked."

    # Handle list of slot strings or dicts
    if isinstance(data, list) and len(data) > 0:
        if isinstance(data[0], str):
            slots_display = "\n".join([f"  - {s}" for s in data])
        else:
            slots_display = "\n".join([
                f"  - {s.get('startTime','?')} to {s.get('endTime','?')}"
                for s in data
            ])
    else:
        slots_display = str(data)

    return (
        f"Available slots for employee {employee_id} on {date}:\n"
        f"{slots_display}\n\n"
        f"To book, say: 'Book appointment on {date} from [startTime] to [endTime]'"
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
    Book a new appointment with an employee.
    IMPORTANT: Always call get_available_slots first to confirm the slot is free.
    Inputs:
      employee_id      — MongoDB _id of the employee e.g. '69df23bd857943bd90be03fb'
      appointment_date — date in YYYY-MM-DD format e.g. '2026-04-20'
      start_time       — e.g. '10:00 AM'
      end_time         — e.g. '11:00 AM'
      booking_notes    — optional notes e.g. 'Haircut, short on sides'
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
        return (
            f"Booking failed.\n"
            f"Error: {result['error']}\n"
            f"Please check the employee ID, date and time are correct."
        )

    data = result.get("data", result)
    appt_id = data.get("_id", "N/A") if isinstance(data, dict) else "N/A"

    return (
        f"Appointment booked successfully!\n"
        f"Date          : {appointment_date}\n"
        f"Time          : {start_time} - {end_time}\n"
        f"Employee ID   : {employee_id}\n"
        f"Notes         : {booking_notes or 'None'}\n"
        f"Appointment ID: {appt_id}\n\n"
        f"Save your Appointment ID — you will need it to reschedule or cancel."
    )


@tool
def get_my_appointments(status: str = "all") -> str:
    """
    Get all appointments for the currently logged-in user or employee.
    The token automatically determines whose appointments are shown.
    Input:
      status — 'all', 'upcoming', 'completed', 'cancelled' (default: 'all')
    """
    result = api_get(
        "/api/v1/appointment/",
        params={"status": status}
    )

    if "error" in result:
        return f"Could not fetch appointments: {result['error']}"

    appointments = (
        result.get("data")
        or result.get("appointments")
        or []
    )

    if isinstance(appointments, dict):
        appointments = appointments.get("data") or appointments.get("appointments") or []

    if not appointments:
        return f"No appointments found with status '{status}'."

    lines = []
    for a in appointments:
        lines.append(
            f"- ID: {a.get('_id','N/A')}\n"
            f"  Date    : {a.get('appointmentDate', a.get('date','N/A'))}\n"
            f"  Time    : {a.get('startTime','N/A')} - {a.get('endTime','N/A')}\n"
            f"  Status  : {a.get('status','N/A').upper()}\n"
            f"  Notes   : {a.get('bookingNotes', a.get('notes','None'))}"
        )

    return (
        f"Your appointments (status={status}) — {len(lines)} found:\n\n"
        + "\n\n".join(lines)
    )


@tool
def get_single_appointment(appointment_id: str) -> str:
    """
    Get full details of one specific appointment.
    Input: appointment_id — the MongoDB _id of the appointment.
    Works for both employee and client tokens.
    """
    result = api_get(f"/api/v1/appointment/{appointment_id}")

    if "error" in result:
        return f"Could not fetch appointment: {result['error']}"

    a = result.get("data", result)

    if isinstance(a, list):
        a = a[0] if a else {}

    employee = a.get("employee", {})
    emp_name = (
        employee.get("name", "N/A")
        if isinstance(employee, dict)
        else str(employee)
    )

    client = a.get("client", a.get("user", {}))
    client_name = (
        client.get("name", "N/A")
        if isinstance(client, dict)
        else str(client)
    )

    return (
        f"Appointment Details:\n"
        f"ID       : {a.get('_id','N/A')}\n"
        f"Date     : {a.get('appointmentDate', a.get('date','N/A'))}\n"
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
    Reschedule an existing appointment to a new date and time.
    Only the user/client who booked can reschedule.
    Inputs:
      appointment_id — the _id of the appointment to change
      new_date       — new date YYYY-MM-DD e.g. '2026-04-22'
      new_start_time — new start time e.g. '12:00 PM'
      new_end_time   — new end time e.g. '1:00 PM'
    """
    body = {
        "appointmentDate": new_date,
        "startTime":       new_start_time,
        "endTime":         new_end_time,
    }

    result = api_patch(f"/api/v1/appointment/{appointment_id}", body)

    if "error" in result:
        return (
            f"Reschedule failed.\n"
            f"Error: {result['error']}\n"
            f"Check that the appointment ID is correct and the new slot is available."
        )

    return (
        f"Appointment rescheduled successfully!\n"
        f"Appointment ID : {appointment_id}\n"
        f"New Date       : {new_date}\n"
        f"New Time       : {new_start_time} - {new_end_time}"
    )


@tool
def cancel_appointment(appointment_id: str) -> str:
    """
    Cancel an appointment. Only the user/client who booked can cancel.
    Input: appointment_id — the MongoDB _id of the appointment.
    Always confirm with the user before calling this.
    """
    body = {"status": "cancelled"}

    result = api_patch(f"/api/v1/appointment/{appointment_id}", body)

    if "error" in result:
        return (
            f"Cancellation failed.\n"
            f"Error: {result['error']}\n"
            f"Check that the appointment ID is correct."
        )

    return (
        f"Appointment cancelled successfully.\n"
        f"Appointment ID: {appointment_id}\n"
        f"Status is now: CANCELLED"
    )


@tool
def update_appointment_status_employee(
    appointment_id: str,
    status: str,
) -> str:
    """
    Update appointment status as an employee.
    Use this to mark appointments as started, in progress, or completed.
    Inputs:
      appointment_id — the _id of the appointment
      status         — one of: 'started', 'in_progress', 'completed'
    """
    allowed = ["started", "in_progress", "completed"]
    if status not in allowed:
        return (
            f"Invalid status '{status}'. "
            f"Allowed values: {', '.join(allowed)}"
        )

    body = {"status": status}
    result = api_patch(f"/api/v1/appointment/{appointment_id}", body)

    if "error" in result:
        return f"Status update failed: {result['error']}"

    return (
        f"Appointment {appointment_id} status updated to: {status.upper()}"
    )
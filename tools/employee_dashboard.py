from langchain.tools import tool
from api_client import api_get
from datetime import date


@tool
def get_my_appointments_today() -> str:
    """
    Get the logged-in employee's appointments for today.
    No input needed — the bearer token identifies the employee.
    """
    today = date.today().strftime("%Y-%m-%d")

    result = api_get(
        "/api/v1/appointment/",
        params={"status": "all"}
    )

    if "error" in result:
        return f"Could not fetch appointments: {result['error']}"

    all_appointments = (
        result.get("data")
        or result.get("appointments")
        or []
    )

    if isinstance(all_appointments, dict):
        all_appointments = (
            all_appointments.get("data")
            or all_appointments.get("appointments")
            or []
        )

    # Filter for today
    todays = [
        a for a in all_appointments
        if a.get("appointmentDate", a.get("date", "")).startswith(today)
    ]

    if not todays:
        return f"You have no appointments today ({today})."

    lines = []
    for a in todays:
        lines.append(
            f"  - {a.get('startTime','N/A')} to {a.get('endTime','N/A')} "
            f"| Status: {a.get('status','N/A').upper()} "
            f"| Notes: {a.get('bookingNotes', a.get('notes','None'))} "
            f"| ID: {a.get('_id','N/A')}"
        )

    return (
        f"You have {len(lines)} appointment(s) today ({today}):\n"
        + "\n".join(lines)
    )


@tool
def get_my_appointment_calendar(month: str, year: str) -> str:
    """
    Get the employee's appointment calendar for a given month and year.
    Inputs:
      month — number e.g. '4' for April
      year  — full year e.g. '2026'
    """
    result = api_get(
        "/api/v1/appointment/employee/calendar",
        params={"month": month, "year": year}
    )

    if "error" in result:
        return f"Could not fetch calendar: {result['error']}"

    data = result.get("data", result.get("calendar", []))

    if not data:
        return f"No calendar data found for {month}/{year}."

    if isinstance(data, list):
        lines = []
        for day in data:
            date_str   = day.get("date", "N/A")
            appts      = day.get("appointments", day.get("slots", []))
            count      = len(appts)
            if count > 0:
                lines.append(f"  {date_str}: {count} appointment(s)")
        if not lines:
            return f"No appointments in {month}/{year}."
        return f"Your calendar for {month}/{year}:\n" + "\n".join(lines)

    return f"Calendar data: {str(data)[:500]}"


@tool
def get_my_leave_status() -> str:
    """
    Get all leave applications for the logged-in employee.
    No input needed.
    """
    result = api_get("/api/v1/work/leave")

    if "error" in result:
        return f"Could not fetch leave: {result['error']}"

    leaves = result.get("data") or result.get("leaves") or []

    if not leaves:
        return "You have no leave applications on record."

    lines = []
    for l in leaves:
        lines.append(
            f"- {l.get('startDate','N/A')} to {l.get('endDate','N/A')} "
            f"| Type: {l.get('leaveType','N/A')} "
            f"| Status: {l.get('status','N/A').upper()} "
            f"| ID: {l.get('_id','N/A')}"
        )

    return "Your leave applications:\n" + "\n".join(lines)


@tool
def get_my_leave_balance() -> str:
    """
    Get remaining leave balance for the logged-in employee.
    No input needed.
    """
    result = api_get("/api/v1/work/leave-balance")

    if "error" in result:
        return f"Could not fetch leave balance: {result['error']}"

    data = result.get("data", result)

    return (
        f"Your leave balance:\n"
        f"Annual leave  : {data.get('annualLeave','N/A')} days\n"
        f"Sick leave    : {data.get('sickLeave','N/A')} days\n"
        f"Total used    : {data.get('totalUsed','N/A')} days"
    )


@tool
def get_single_leave_status(leave_id: str) -> str:
    """
    Get status of one specific leave application.
    Input: leave_id — MongoDB _id of the leave request.
    """
    result = api_get(f"/api/v1/work/leave/{leave_id}")

    if "error" in result:
        return f"Could not fetch leave: {result['error']}"

    l = result.get("data", result)

    return (
        f"Leave Request:\n"
        f"ID      : {l.get('_id','N/A')}\n"
        f"Dates   : {l.get('startDate','N/A')} to {l.get('endDate','N/A')}\n"
        f"Type    : {l.get('leaveType','N/A')}\n"
        f"Reason  : {l.get('reason','N/A')}\n"
        f"Status  : {l.get('status','N/A').upper()}\n"
        f"Applied : {l.get('createdAt','N/A')}"
    )
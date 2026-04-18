from langchain.tools import tool
from api_client import api_get
from datetime import date as date_lib


def _fmt(raw: str) -> str:
    """Clean ISO date string to YYYY-MM-DD."""
    return raw[:10] if raw else "N/A"


@tool
def get_my_appointments_today() -> str:
    """
    View the logged-in employee's appointments for today.
    No input needed. Read-only.
    """
    today = date_lib.today().strftime("%Y-%m-%d")

    result = api_get("/api/v1/appointment/", params={"status": "all"})

    if "error" in result:
        return f"Could not fetch appointments: {result['error']}"

    all_appts = result.get("data") or []
    if isinstance(all_appts, dict):
        all_appts = all_appts.get("data") or []

    todays = [
        a for a in all_appts
        if _fmt(a.get("appointmentDate", a.get("date", ""))) == today
    ]

    if not todays:
        return f"You have no appointments today ({today})."

    lines = []
    for a in todays:
        lines.append(
            f"  - {a.get('startTime','N/A')} to {a.get('endTime','N/A')}"
            f" | Status: {a.get('status','N/A').upper()}"
            f" | Notes: {a.get('bookingNotes', a.get('notes','None'))}"
            f" | ID: {a.get('_id','N/A')}"
        )

    return (
        f"Your appointments today ({today}) — {len(lines)} found:\n"
        + "\n".join(lines)
    )


@tool
def get_my_appointment_calendar(month: str, year: str) -> str:
    """
    View the employee's appointment calendar for a given month and year.
    Inputs:
      month — number e.g. '4' for April
      year  — full year e.g. '2026'
    Read-only.
    """
    result = api_get(
        "/api/v1/appointment/employee/calendar",
        params={"month": month, "year": year}
    )

    if "error" in result:
        return f"Could not fetch calendar: {result['error']}"

    data = result.get("data", [])

    if not data:
        return (
            f"No appointments found in your calendar for {month}/{year}.\n"
            f"This means no appointments have been assigned to your account yet."
        )

    lines = []
    if isinstance(data, list):
        for day in data:
            day_date = day.get("date", "N/A")
            appts    = day.get("appointments", day.get("slots", []))
            count    = len(appts) if appts else day.get("count", 0)
            if count > 0:
                lines.append(f"  {day_date}: {count} appointment(s)")
    elif isinstance(data, dict):
        appts = data.get("appointments", data.get("data", []))
        for a in appts:
            lines.append(
                f"  {_fmt(a.get('appointmentDate',''))} "
                f"| {a.get('startTime','?')} - {a.get('endTime','?')} "
                f"| {a.get('status','?').upper()}"
            )

    if not lines:
        return f"No appointments with bookings in {month}/{year}."

    return f"Your calendar for {month}/{year}:\n" + "\n".join(lines)


@tool
def get_my_leave_status() -> str:
    """
    View all leave applications for the logged-in employee.
    No input needed. Read-only.
    """
    result = api_get("/api/v1/work/leave")

    if "error" in result:
        return f"Could not fetch leave: {result['error']}"

    leaves = result.get("data") or []

    if not leaves:
        return "You have no leave applications on record."

    lines = []
    for l in leaves:
        lines.append(
            f"- {l.get('startDate','N/A')} to {l.get('endDate','N/A')}"
            f" | Type: {l.get('leaveType','N/A')}"
            f" | Status: {l.get('status','N/A').upper()}"
            f" | ID: {l.get('_id','N/A')}"
        )

    return "Your leave applications:\n" + "\n".join(lines)


@tool
def get_my_leave_balance() -> str:
    """
    View remaining leave balance for the logged-in employee.
    No input needed. Read-only.
    """
    result = api_get("/api/v1/work/leave-balance")

    if "error" in result:
        return f"Could not fetch leave balance: {result['error']}"

    data     = result.get("data", {})
    balances = data.get("balances", {})

    if not balances:
        return "No leave balance data found for your account."

    lines = []
    for leave_type, values in balances.items():
        total     = values.get("total", 0)
        used      = values.get("used", 0)
        remaining = values.get("remaining", 0)
        lines.append(
            f"  {leave_type:<22}"
            f" Total: {total}  |  Used: {used}  |  Remaining: {remaining}"
        )

    return "Your leave balance:\n" + "\n".join(lines)


@tool
def get_single_leave_status(leave_id: str) -> str:
    """
    View the status of one specific leave application.
    Input: leave_id — MongoDB _id of the leave request. Read-only.
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
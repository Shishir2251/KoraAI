from langchain.tools import tool
from api_client import api_get
from datetime import date


@tool
def get_my_appointments_today() -> str:
    """
    Get the logged-in employee's appointments for today.
    No input needed.
    """
    today = date.today().strftime("%Y-%m-%d")

    result = api_get(
        "/api/v1/schedule/",
        params={"date": today, "status": "all"}
    )

    if "error" in result:
        return f"Could not fetch appointments: {result['error']}"

    schedules = (
        result.get("data")
        or result.get("schedules")
        or []
    )

    if not schedules:
        return f"You have no appointments today ({today})."

    lines = []
    for s in schedules:
        for slot in s.get("slots", []):
            lines.append(
                f"  {slot.get('startTime','N/A')} - {slot.get('endTime','N/A')} "
                f"| {slot.get('summary','Appointment')} "
                f"| Status: {slot.get('status','N/A')}"
            )

    count = len(lines)
    return (
        f"You have {count} appointment(s) today ({today}):\n"
        + "\n".join(lines)
    )


@tool
def get_my_leave_status() -> str:
    """
    Get all leave applications for the logged-in employee.
    No input needed.
    """
    result = api_get("/api/v1/work/leave")

    if "error" in result:
        return f"Could not fetch leave: {result['error']}"

    leaves = (
        result.get("data")
        or result.get("leaves")
        or []
    )

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
    Get remaining leave days for the logged-in employee.
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
    Get the status of one specific leave application.
    Input: leave_id — the MongoDB _id of the leave request.
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
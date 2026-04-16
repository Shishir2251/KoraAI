from langchain.tools import tool
from api_client import api_get, api_post


@tool
def apply_for_leave(
    start_date: str,
    end_date: str,
    leave_type: str,
    reason: str,
) -> str:
    """
    Submit a leave application for the logged-in employee.
    Inputs:
      start_date  — YYYY-MM-DD
      end_date    — YYYY-MM-DD
      leave_type  — e.g. 'sick', 'annual', 'casual'
      reason      — short description of the reason
    """
    body = {
        "startDate":  start_date,
        "endDate":    end_date,
        "leaveType":  leave_type,
        "reason":     reason,
    }
    result = api_post("/api/v1/work/leave", body)

    if "error" in result:
        return f"Failed to submit leave: {result['error']}"

    data = result.get("data", result)
    return (
        f"Leave application submitted.\n"
        f"Dates  : {start_date} to {end_date}\n"
        f"Type   : {leave_type}\n"
        f"Reason : {reason}\n"
        f"ID     : {data.get('_id','N/A')}\n"
        f"Status : PENDING"
    )


@tool
def check_leave_status(leave_id: str = "") -> str:
    """
    Check leave application status.
    Input: leave_id (optional). If blank, returns all leave applications.
    """
    if leave_id:
        result = api_get(f"/api/v1/work/leave/{leave_id}")
        if "error" in result:
            return f"Could not fetch leave: {result['error']}"
        l = result.get("data", result)
        return (
            f"Leave ID {leave_id}:\n"
            f"Dates  : {l.get('startDate','N/A')} to {l.get('endDate','N/A')}\n"
            f"Type   : {l.get('leaveType','N/A')}\n"
            f"Status : {l.get('status','N/A').upper()}"
        )
    else:
        result = api_get("/api/v1/work/leave")
        if "error" in result:
            return f"Could not fetch leave list: {result['error']}"
        leaves = result.get("data", [])
        if not leaves:
            return "No leave applications found."
        lines = [
            f"- {l.get('startDate','N/A')} to {l.get('endDate','N/A')} "
            f"| {l.get('leaveType','N/A')} "
            f"| {l.get('status','N/A').upper()} "
            f"| ID: {l.get('_id','N/A')}"
            for l in leaves
        ]
        return "Your leave applications:\n" + "\n".join(lines)
from langchain.tools import tool

@tool
def apply_for_leave(employee_id: str, start_date: str, end_date: str, reason: str) -> str:
    """Submit a leave application. Inputs: employee_id, start_date (YYYY-MM-DD), end_date (YYYY-MM-DD), reason."""
    return (
        f"Leave request submitted for employee {employee_id}. "
        f"Dates: {start_date} to {end_date}. "
        f"Reason: {reason}. "
        f"Request ID: LV-204. Status: Pending approval."
    )

@tool
def check_leave_status(employee_id: str) -> str:
    """Check leave application status for an employee. Input: employee_id."""
    return (
        f"Leave requests for employee {employee_id}:\n"
        f"LV-204: Apr 15 to Apr 18 — Status: PENDING — Reason: Family event\n"
        f"LV-198: Mar 01 to Mar 02 — Status: APPROVED"
    )
from langchain.tools import tool
from database import get_db
from models import LeaveRequest
from datetime import datetime

@tool
def apply_for_leave(employee_id: str, start_date: str, end_date: str, reason: str) -> str:
    """
    Submit a leave application for an employee.
    Inputs: employee_id, start_date (YYYY-MM-DD), end_date (YYYY-MM-DD), reason.
    """
    db = next(get_db())

    leave = LeaveRequest(
        employee_id=employee_id,
        start_date=datetime.strptime(start_date, "%Y-%m-%d").date(),
        end_date=datetime.strptime(end_date, "%Y-%m-%d").date(),
        reason=reason,
        status="pending",
        created_at=datetime.utcnow(),
    )
    db.add(leave)
    db.commit()
    db.refresh(leave)

    return (
        f"Leave request submitted successfully. "
        f"Request ID: LV-{leave.id}. "
        f"Dates: {start_date} to {end_date}. "
        f"Status: Pending approval."
    )


@tool
def check_leave_status(employee_id: str) -> str:
    """
    Check the status of all leave requests for an employee.
    Input: employee_id as a string.
    """
    db = next(get_db())

    requests = db.query(LeaveRequest).filter(
        LeaveRequest.employee_id == employee_id
    ).order_by(LeaveRequest.created_at.desc()).all()

    if not requests:
        return f"No leave requests found for employee {employee_id}."

    lines = []
    for r in requests:
        lines.append(
            f"LV-{r.id}: {r.start_date} to {r.end_date} — "
            f"Status: {r.status.upper()} — Reason: {r.reason}"
        )

    return "\n".join(lines)
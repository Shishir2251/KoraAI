from langchain.tools import tool
from database import get_db
from models import Employee

@tool
def get_employee_info(employee_id: str) -> str:
    """
    Get details about a specific employee by their ID.
    Input: employee_id as a string.
    """
    db = next(get_db())
    emp = db.query(Employee).filter(Employee.id == employee_id).first()

    if not emp:
        return f"No employee found with ID {employee_id}."

    return (
        f"Name: {emp.name} | "
        f"Role: {emp.role} | "
        f"Email: {emp.email} | "
        f"Status: {emp.status}"
    )


@tool
def list_employees(org_id: str) -> str:
    """
    List all active employees in the organisation.
    Input: org_id as a string.
    """
    db = next(get_db())
    employees = db.query(Employee).filter(
        Employee.org_id == org_id,
        Employee.status == "active"
    ).all()

    if not employees:
        return "No active employees found."

    lines = [f"- {e.name} ({e.role})" for e in employees]
    return f"Active employees:\n" + "\n".join(lines)
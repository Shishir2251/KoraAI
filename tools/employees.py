from langchain.tools import tool

@tool
def get_employee_info(employee_id: str) -> str:
    """Get details about a specific employee. Input: employee_id."""
    return (
        f"Employee {employee_id} — "
        f"Name: Sara Ahmed | Role: Senior Stylist | "
        f"Email: sara@salon.com | Status: Active"
    )

@tool
def list_employees(org_id: str) -> str:
    """List all active employees in the organisation. Input: org_id."""
    return (
        f"Active employees in org {org_id}:\n"
        f"- Sara Ahmed (Senior Stylist)\n"
        f"- John Malik (Barber)\n"
        f"- Nadia Khan (Colorist)"
    )
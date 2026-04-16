from langchain.tools import tool
from api_client import api_get, api_post, api_put, api_patch, api_delete


@tool
def invite_employee(name: str, email: str, phone: str, role: str) -> str:
    """
    Invite a new employee to the organisation.
    Inputs: name, email, phone number, role e.g. 'stylist'.
    """
    body = {"name": name, "email": email, "phoneNumber": phone, "role": role}
    result = api_post("/api/v1/employee/invite", body)

    if "error" in result:
        return f"Failed to invite employee: {result['error']}"

    return (
        f"Employee invited successfully.\n"
        f"Name: {name} | Email: {email} | Role: {role}\n"
        f"An invitation email has been sent to {email}."
    )


@tool
def get_all_employees(page: str = "1", limit: str = "10") -> str:
    """
    List all employees in the organisation.
    Optional: page number and limit per page.
    """
    result = api_get("/api/v1/employee", params={"page": page, "limit": limit})

    if "error" in result:
        return f"Failed to fetch employees: {result['error']}"

    employees = result.get("data", result.get("employees", []))

    if not employees:
        return "No employees found."

    lines = [
        f"- {e.get('name','N/A')} | Role: {e.get('role','N/A')} "
        f"| Email: {e.get('email','N/A')} "
        f"| Status: {e.get('status','N/A')} "
        f"| ID: {e.get('_id','N/A')}"
        for e in employees
    ]

    return f"Employees ({len(lines)} found):\n" + "\n".join(lines)


@tool
def get_employee_by_id(employee_id: str) -> str:
    """
    Get full details of one employee.
    Input: employee_id — the MongoDB _id string.
    """
    result = api_get(f"/api/v1/employee/{employee_id}")

    if "error" in result:
        return f"Failed to fetch employee: {result['error']}"

    e = result.get("data", result)

    return (
        f"Employee Details:\n"
        f"Name   : {e.get('name','N/A')}\n"
        f"Email  : {e.get('email','N/A')}\n"
        f"Phone  : {e.get('phoneNumber','N/A')}\n"
        f"Role   : {e.get('role','N/A')}\n"
        f"Status : {e.get('status','N/A')}\n"
        f"ID     : {e.get('_id','N/A')}"
    )


@tool
def update_employee(
    employee_id: str,
    name: str = "",
    email: str = "",
    role: str = "",
    phone: str = "",
) -> str:
    """
    Update an employee's details.
    Input: employee_id (required). Then any of: name, email, role, phone.
    Only provide the fields you want to change.
    """
    body: dict = {}
    if name:  body["name"]        = name
    if email: body["email"]       = email
    if role:  body["role"]        = role
    if phone: body["phoneNumber"] = phone

    if not body:
        return "Please provide at least one field to update."

    result = api_put(f"/api/v1/employee/{employee_id}", body)

    if "error" in result:
        return f"Failed to update employee: {result['error']}"

    return (
        f"Employee {employee_id} updated.\n"
        f"Fields changed: {', '.join(body.keys())}"
    )


@tool
def delete_employee(employee_id: str) -> str:
    """
    Permanently delete an employee from the organisation.
    Input: employee_id. Always confirm with the user before calling this.
    """
    result = api_delete(f"/api/v1/employee/{employee_id}")

    if "error" in result:
        return f"Failed to delete employee: {result['error']}"

    return f"Employee {employee_id} has been permanently deleted."


@tool
def toggle_employee_status(employee_id: str) -> str:
    """
    Toggle an employee's active/inactive status.
    Use to deactivate without deleting.
    Input: employee_id.
    """
    result = api_patch(f"/api/v1/employee/{employee_id}/status", {})

    if "error" in result:
        return f"Failed to toggle status: {result['error']}"

    new_status = result.get("data", {}).get("status", "toggled")
    return f"Employee {employee_id} status is now: {new_status.upper()}"
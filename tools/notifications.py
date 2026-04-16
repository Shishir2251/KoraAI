from langchain.tools import tool


@tool
def notify_staff(employee_id: str, message: str) -> str:
    """
    Send a notification to a staff member.
    Inputs: employee_id, message text.
    Currently logs to console — connect to WhatsApp or email in future.
    """
    print(f"[NOTIFY] → Employee {employee_id}: {message}")
    return f"Notification sent to employee {employee_id}: '{message}'"
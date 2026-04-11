from langchain.tools import tool

@tool
def notify_staff(employee_id: str, message: str) -> str:
    """
    Send a notification message to a staff member.
    Input: employee_id and the message text to send.
    In future this will connect to WhatsApp or email.
    """
    # For now, just log it — wire up Twilio or email later
    print(f"[NOTIFY] → Employee {employee_id}: {message}")
    return f"Notification sent to employee {employee_id}: '{message}'"
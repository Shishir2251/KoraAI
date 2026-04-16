from langchain.tools import tool


@tool
def get_appointments(date: str) -> str:
    """Get appointments for a given date (offline test mode). Input: YYYY-MM-DD."""
    return f"[TEST] Appointments on {date}: 10:00 Haircut (Ahmed), 14:00 Color (Sara)"


@tool
def create_appointment(customer: str, date: str, time: str, service: str) -> str:
    """Create an appointment (offline test mode)."""
    return f"[TEST] Appointment created: {customer} | {date} | {time} | {service}"
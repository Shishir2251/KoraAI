from langchain.tools import tool

@tool
def get_appointments(date: str) -> str:
    """Get all appointments for a given date. Input should be a date like 2024-04-11."""
    # Later this will query your real PostgreSQL database
    # For now, return fake data so you can test
    return f"Appointments on {date}: 3pm - Haircut (John), 5pm - Color (Sara)"

@tool
def get_available_slots(date: str) -> str:
    """Get available time slots for a given date."""
    return f"Available slots on {date}: 10am, 2pm, 4pm, 6pm"

@tool
def reschedule_appointment(appointment_id: str, new_time: str) -> str:
    """Reschedule an appointment to a new time."""
    return f"Appointment {appointment_id} has been moved to {new_time}. Confirmation sent."

@tool
def cancel_appointment(appointment_id: str) -> str:
    """Cancel an appointment by its ID."""
    return f"Appointment {appointment_id} has been cancelled."
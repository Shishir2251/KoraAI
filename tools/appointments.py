from langchain.tools import tool

@tool
def get_appointments(date: str) -> str:
    """Get all appointments for a given date. Input: date as YYYY-MM-DD."""
    return f"Appointments on {date}: 10:00 - Haircut (Ahmed), 14:00 - Color (Sara), 16:00 - Trim (John)"

@tool
def create_appointment(customer: str, date: str, time: str, service: str) -> str:
    """Create a new appointment. Inputs: customer name, date (YYYY-MM-DD), time (HH:MM), service name."""
    return f"Appointment created. Customer: {customer} | Date: {date} | Time: {time} | Service: {service}"

@tool
def reschedule_appointment(appointment_id: str, new_date: str, new_time: str) -> str:
    """Reschedule an existing appointment. Inputs: appointment_id, new_date (YYYY-MM-DD), new_time (HH:MM)."""
    return f"Appointment {appointment_id} rescheduled to {new_date} at {new_time}. Customer notified."

@tool
def cancel_appointment(appointment_id: str) -> str:
    """Cancel an appointment by its ID."""
    return f"Appointment {appointment_id} has been cancelled successfully."
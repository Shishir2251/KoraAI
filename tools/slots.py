from langchain.tools import tool


@tool
def get_available_slots(date: str) -> str:
    """Get available slots for a date (offline test mode). Input: YYYY-MM-DD."""
    return f"[TEST] Available slots on {date}: 09:00, 11:00, 13:00, 15:00, 17:00"
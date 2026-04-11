from langchain.tools import tool

@tool
def get_available_slots(date: str) -> str:
    """Get available booking time slots for a given date. Input: date as YYYY-MM-DD."""
    all_slots = ["09:00", "10:00", "11:00", "13:00", "14:00", "15:00", "16:00", "17:00"]
    booked = ["10:00", "14:00"]
    free = [s for s in all_slots if s not in booked]
    return f"Available slots on {date}: {', '.join(free)}"
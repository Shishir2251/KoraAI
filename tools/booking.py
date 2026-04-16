from langchain.tools import tool
from api_client import api_get, api_post, api_patch
from datetime import date as date_lib


@tool
def check_availability(date: str) -> str:
    """
    Check available appointment slots for a specific date or whole month.
    Input examples:
      - specific date : '2026-04-15'
      - whole month   : '2026-04' 
    Returns booked and available slots.
    """
    # Decide if input is a full date or just a month
    if len(date.strip()) == 7:
        # Month format — use calendar endpoint
        result = api_get(
            "/api/v1/schedule/calendar",
            params={"month": date.strip()}
        )
        if "error" in result:
            return f"Could not fetch calendar: {result['error']}"

        data = (
            result.get("data")
            or result.get("calendar")
            or []
        )
        if not data:
            return f"No schedule data found for {date}."

        lines = []
        for day in data:
            day_date = day.get("date", "")
            slots    = day.get("slots", [])
            booked   = [s for s in slots if s.get("status") in ["booked","in_progress","completed"]]
            free     = len(slots) - len(booked)
            if free > 0:
                times = [
                    f"{s.get('startTime','?')}-{s.get('endTime','?')}"
                    for s in slots
                    if s.get("status") not in ["booked","in_progress","completed"]
                ]
                lines.append(f"  {day_date}: {', '.join(times)}")

        if not lines:
            return f"No free slots found in {date}. Fully booked."

        return f"Available slots in {date}:\n" + "\n".join(lines)

    else:
        # Specific date — use schedule list with date filter
        result = api_get(
            "/api/v1/schedule/",
            params={"date": date.strip(), "status": "all"}
        )
        if "error" in result:
            return f"Could not fetch schedule: {result['error']}"

        schedules = (
            result.get("data")
            or result.get("schedules")
            or []
        )

        if not schedules:
            return f"No appointments found on {date}. The day looks fully open!"

        booked_times = []
        for s in schedules:
            for slot in s.get("slots", []):
                status = slot.get("status", "")
                if status in ["booked", "in_progress"]:
                    booked_times.append(
                        f"  {slot.get('startTime','?')} - {slot.get('endTime','?')} "
                        f"[{status}]"
                    )

        if not booked_times:
            return f"No booked slots on {date}. Fully available!"

        return (
            f"Schedule for {date}:\n"
            f"Booked slots:\n" + "\n".join(booked_times) + "\n\n"
            f"Ask your business owner what times are open for new bookings."
        )


@tool
def get_all_schedules() -> str:
    """
    Get all scheduled appointments.
    No input needed.
    """
    result = api_get("/api/v1/schedule/")

    if "error" in result:
        return f"Could not fetch schedules: {result['error']}"

    schedules = (
        result.get("data")
        or result.get("schedules")
        or []
    )

    if not schedules:
        return "No schedules found."

    lines = []
    for s in schedules:
        slots = s.get("slots", [])
        slot_times = [
            f"{sl.get('startTime','?')}-{sl.get('endTime','?')} ({sl.get('status','?')})"
            for sl in slots
        ]
        lines.append(
            f"- Date: {s.get('date','N/A')} "
            f"| ID: {s.get('_id','N/A')} "
            f"| Slots: {', '.join(slot_times)}"
        )

    return f"All schedules ({len(lines)}):\n" + "\n".join(lines)


@tool
def get_appointments_by_date(date: str, status: str = "all") -> str:
    """
    Get appointments for a specific date.
    Inputs:
      date   — YYYY-MM-DD e.g. '2026-04-15'
      status — 'all', 'upcoming', or 'completed' (default: 'all')
    """
    result = api_get(
        "/api/v1/schedule/",
        params={"date": date, "status": status}
    )

    if "error" in result:
        return f"Could not fetch appointments: {result['error']}"

    schedules = (
        result.get("data")
        or result.get("schedules")
        or []
    )

    if not schedules:
        return f"No appointments found on {date}."

    lines = []
    for s in schedules:
        for slot in s.get("slots", []):
            lines.append(
                f"  {slot.get('startTime','?')} - {slot.get('endTime','?')} "
                f"| {slot.get('summary','Appointment')} "
                f"| Status: {slot.get('status','?')} "
                f"| Slot ID: {slot.get('_id','?')}"
            )

    return (
        f"Appointments on {date} (status={status}):\n"
        + "\n".join(lines)
    )


@tool
def book_appointment(
    date: str,
    start_time: str,
    end_time: str,
    client_id: str,
    summary: str = "",
) -> str:
    """
    Book a new appointment slot.
    Inputs:
      date       — YYYY-MM-DD e.g. '2026-04-15'
      start_time — e.g. '10:00 AM'
      end_time   — e.g. '11:30 AM'
      client_id  — the MongoDB _id of the client/customer
      summary    — optional note e.g. 'Haircut for Ahmed'
    """
    body = {
        "date": date,
        "slots": [
            {
                "startTime": start_time,
                "endTime":   end_time,
                "client":    client_id,
                "summary":   summary,
            }
        ],
    }

    result = api_post("/api/v1/schedule/", body)

    if "error" in result:
        return f"Booking failed: {result['error']}"

    data = result.get("data", result)
    return (
        f"Appointment booked successfully!\n"
        f"Date      : {date}\n"
        f"Time      : {start_time} - {end_time}\n"
        f"Summary   : {summary or 'N/A'}\n"
        f"Schedule ID: {data.get('_id','N/A')}"
    )


@tool
def reschedule_appointment(
    schedule_id: str,
    new_date: str = "",
    slot_id: str = "",
    new_start_time: str = "",
    new_end_time: str = "",
) -> str:
    """
    Reschedule an existing appointment.
    Inputs:
      schedule_id    — ID of the schedule (required)
      new_date       — new date YYYY-MM-DD (optional)
      slot_id        — the specific slot _id to change (optional)
      new_start_time — new start time e.g. '02:00 PM' (optional)
      new_end_time   — new end time e.g. '03:00 PM' (optional)
    """
    body: dict = {}
    if new_date:       body["date"]      = new_date
    if slot_id:        body["slotId"]    = slot_id
    if new_start_time: body["startTime"] = new_start_time
    if new_end_time:   body["endTime"]   = new_end_time

    if not body:
        return "Please provide at least a new date or new time to reschedule."

    result = api_patch(f"/api/v1/schedule/{schedule_id}", body)

    if "error" in result:
        return f"Reschedule failed: {result['error']}"

    return (
        f"Appointment rescheduled successfully.\n"
        f"Schedule ID  : {schedule_id}\n"
        f"Changes made : {', '.join(body.keys())}"
    )


@tool
def cancel_appointment(schedule_id: str, slot_id: str) -> str:
    """
    Cancel a specific appointment slot.
    Inputs:
      schedule_id — the schedule document _id
      slot_id     — the slot _id inside that schedule
    """
    body = {
        "scheduleId": schedule_id,
        "slotId":     slot_id,
        "action":     "cancel",
    }
    result = api_patch("/api/v1/schedule/session-action", body)

    if "error" in result:
        return f"Cancellation failed: {result['error']}"

    return (
        f"Appointment cancelled.\n"
        f"Schedule : {schedule_id}\n"
        f"Slot     : {slot_id}"
    )
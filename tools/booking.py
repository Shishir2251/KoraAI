# from langchain.tools import tool
# from api_client import api_get, api_post, api_patch
# from datetime import datetime
# import api_client


# def _format_date(raw: str) -> str:
#     """Convert ISO date to YYYY-MM-DD."""
#     return raw[:10] if raw else "N/A"


# def _generate_hour_slots(start: str, end: str) -> list:
#     """
#     Convert a range like 09:00-18:00 into individual 1-hour slots.
#     Returns list of dicts: [{startTime, endTime}, ...]
#     """
#     slots = []
#     try:
#         current = datetime.strptime(start, "%H:%M")
#         end_dt  = datetime.strptime(end,   "%H:%M")
#         while current < end_dt:
#             next_slot = current.replace(minute=0, second=0)
#             next_slot = next_slot.replace(hour=current.hour + 1)
#             if next_slot > end_dt:
#                 next_slot = end_dt
#             slots.append({
#                 "startTime": current.strftime("%H:%M"),
#                 "endTime":   next_slot.strftime("%H:%M"),
#             })
#             current = next_slot
#     except Exception:
#         pass
#     return slots


# @tool
# def get_available_slots(employee_id: str, date: str) -> str:
#     """
#     Check available time slots for a specific employee on a specific date.
#     Always call this FIRST before booking an appointment.
#     Inputs:
#       employee_id — MongoDB _id of the employee
#       date        — YYYY-MM-DD e.g. '2026-04-25'
#     """
#     result = api_get(
#         "/api/v1/appointment/available-slots",
#         params={"employee": employee_id, "date": date}
#     )

#     if "error" in result:
#         return f"Could not fetch slots: {result['error']}"

#     data = result.get("data", {})

#     if not data:
#         return f"No slot data returned for employee {employee_id} on {date}."

#     # Extract booked appointment times
#     booked = data.get("bookedAppointments", [])
#     booked_times = set()
#     for b in booked:
#         booked_times.add(b.get("startTime", ""))

#     # Build available slots from availableRanges
#     available_ranges = data.get("availableRanges", [])
#     working_hours    = data.get("workingHours", {})

#     all_slots = []

#     if available_ranges:
#         # Generate 1-hour blocks from each free range
#         for r in available_ranges:
#             blocks = _generate_hour_slots(
#                 r.get("startTime", "09:00"),
#                 r.get("endTime",   "18:00")
#             )
#             all_slots.extend(blocks)

#     elif working_hours:
#         # Fallback: generate from working hours and exclude booked
#         all_slots = _generate_hour_slots(
#             working_hours.get("startTime", "09:00"),
#             working_hours.get("endTime",   "18:00")
#         )

#     # Remove any slots that are booked
#     free_slots = [
#         s for s in all_slots
#         if s["startTime"] not in booked_times
#     ]

#     if not free_slots:
#         return (
#             f"No available slots for employee {employee_id} on {date}.\n"
#             f"All time slots are fully booked."
#         )

#     lines = [
#         f"  - {s['startTime']} to {s['endTime']}"
#         for s in free_slots
#     ]

#     booked_summary = ""
#     if booked:
#         booked_lines = [
#             f"  - {b.get('startTime','?')} to {b.get('endTime','?')}"
#             for b in booked
#         ]
#         booked_summary = (
#             f"\nAlready booked ({len(booked)}):\n"
#             + "\n".join(booked_lines)
#         )

#     return (
#         f"Available slots for employee {employee_id} on {date} "
#         f"({len(free_slots)} free):\n"
#         + "\n".join(lines)
#         + booked_summary
#         + f"\n\nTo book say: 'Book appointment on {date} from [startTime] to [endTime]'"
#     )


# @tool
# def create_appointment(
#     employee_id: str,
#     appointment_date: str,
#     start_time: str,
#     end_time: str,
#     booking_notes: str = "",
# ) -> str:
#     """
#     Book a new appointment. Only a USER (client) can book.
#     Always call get_available_slots first to confirm the slot is free.
#     Inputs:
#       employee_id      — _id of the employee e.g. '69e2e76c87b441f121dbe929'
#       appointment_date — YYYY-MM-DD e.g. '2026-04-25'
#       start_time       — e.g. '10:00 AM' or '10:00'
#       end_time         — e.g. '11:00 AM' or '11:00'
#       booking_notes    — optional e.g. 'Haircut, short sides'
#     """
#     body = {
#         "employee":        employee_id,
#         "appointmentDate": appointment_date,
#         "startTime":       start_time,
#         "endTime":         end_time,
#         "bookingNotes":    booking_notes,
#     }

#     result = api_post("/api/v1/appointment/", body)

#     if "error" in result:
#         err_str = str(result["error"])
#         if "Only user" in err_str or "403" in err_str:
#             return (
#                 "Booking failed: your current token is not a user role account.\n"
#                 "Make sure USER_TOKEN in .env is from an account registered with role 'user'."
#             )
#         return f"Booking failed: {result['error']}"

#     data    = result.get("data", result)
#     appt_id = data.get("_id", "N/A") if isinstance(data, dict) else "N/A"

#     return (
#         f"Appointment booked!\n"
#         f"Date          : {appointment_date}\n"
#         f"Time          : {start_time} - {end_time}\n"
#         f"Employee      : {employee_id}\n"
#         f"Notes         : {booking_notes or 'None'}\n"
#         f"Appointment ID: {appt_id}\n"
#         f"Save this ID to reschedule or cancel later."
#     )


# @tool
# def get_my_appointments(status: str = "all") -> str:
#     """
#     Get appointments for the logged-in user or employee.
#     Input:
#       status — 'all', 'upcoming', 'completed', 'cancelled' (default: 'all')
#     """
#     result = api_get("/api/v1/appointment/", params={"status": status})

#     if "error" in result:
#         return f"Could not fetch appointments: {result['error']}"

#     appointments = result.get("data") or []
#     if isinstance(appointments, dict):
#         appointments = appointments.get("data") or appointments.get("appointments") or []

#     if not appointments:
#         return f"No appointments found with status '{status}'."

#     lines = []
#     for i, a in enumerate(appointments, 1):
#         lines.append(
#             f"{i}. ID     : {a.get('_id','N/A')}\n"
#             f"   Date   : {_format_date(a.get('appointmentDate', a.get('date','')))}\n"
#             f"   Time   : {a.get('startTime','N/A')} - {a.get('endTime','N/A')}\n"
#             f"   Status : {a.get('status','N/A').upper()}\n"
#             f"   Notes  : {a.get('bookingNotes', a.get('notes','None'))}"
#         )

#     return f"Your appointments ({len(lines)} found):\n\n" + "\n\n".join(lines)


# @tool
# def get_my_appointments_by_date(date: str) -> str:
#     """
#     Get all appointments for a specific date.
#     Input: date — YYYY-MM-DD e.g. '2026-04-25'
#     """
#     result = api_get("/api/v1/appointment/", params={"status": "all"})

#     if "error" in result:
#         return f"Could not fetch appointments: {result['error']}"

#     all_appts = result.get("data") or []
#     if isinstance(all_appts, dict):
#         all_appts = all_appts.get("data") or all_appts.get("appointments") or []

#     filtered = [
#         a for a in all_appts
#         if _format_date(a.get("appointmentDate", a.get("date", ""))) == date
#     ]

#     if not filtered:
#         return f"No appointments found on {date}."

#     lines = []
#     for a in filtered:
#         lines.append(
#             f"  - {a.get('startTime','N/A')} to {a.get('endTime','N/A')}"
#             f" | Status: {a.get('status','N/A').upper()}"
#             f" | Notes: {a.get('bookingNotes', a.get('notes','None'))}"
#             f" | ID: {a.get('_id','N/A')}"
#         )

#     return (
#         f"Appointments on {date} ({len(lines)} found):\n"
#         + "\n".join(lines)
#     )


# @tool
# def get_single_appointment(appointment_id: str) -> str:
#     """
#     Get full details of one appointment by ID.
#     Works for both user and employee tokens.
#     Input: appointment_id — MongoDB _id
#     """
#     result = api_get(f"/api/v1/appointment/{appointment_id}")

#     if "error" in result:
#         return f"Could not fetch appointment: {result['error']}"

#     a = result.get("data", result)
#     if isinstance(a, list):
#         a = a[0] if a else {}

#     employee    = a.get("employee", {})
#     emp_name    = employee.get("name", str(employee)) if isinstance(employee, dict) else str(employee)
#     client      = a.get("client", a.get("user", {}))
#     client_name = client.get("name", str(client)) if isinstance(client, dict) else str(client)

#     return (
#         f"Appointment Details:\n"
#         f"ID       : {a.get('_id','N/A')}\n"
#         f"Date     : {_format_date(a.get('appointmentDate', a.get('date','')))}\n"
#         f"Time     : {a.get('startTime','N/A')} - {a.get('endTime','N/A')}\n"
#         f"Status   : {a.get('status','N/A').upper()}\n"
#         f"Employee : {emp_name}\n"
#         f"Client   : {client_name}\n"
#         f"Notes    : {a.get('bookingNotes', a.get('notes','None'))}"
#     )


# @tool
# def cancel_appointment(appointment_id: str) -> str:
#     """
#     Cancel an appointment. Only a USER (client) can cancel.
#     Employees cannot cancel appointments.
#     Input: appointment_id — MongoDB _id. Always confirm with user first.
#     """
#     # Hard block — employee cannot cancel
#     if api_client._active_role == "employee":
#         return (
#             "As an employee you can only view appointments. "
#             "You cannot cancel appointments. "
#             "Please ask the client to cancel their own booking."
#         )

#     # Pre-check status
#     check = api_get(f"/api/v1/appointment/{appointment_id}")
#     if "error" not in check:
#         appt   = check.get("data", {})
#         if isinstance(appt, list):
#             appt = appt[0] if appt else {}
#         status = appt.get("status", "").lower()
#         if status == "cancelled":
#             return "This appointment is already cancelled."
#         if status in ["completed", "started", "in_progress"]:
#             return (
#                 f"Cannot cancel — appointment is {status.upper()}.\n"
#                 f"Only upcoming appointments can be cancelled."
#             )

#     result = api_patch(
#         f"/api/v1/appointment/{appointment_id}",
#         {"status": "cancelled"}
#     )

#     if "error" in result:
#         err = str(result["error"])
#         if "timed out" in err.lower():
#             return "Request timed out. Please try again."
#         if "completed" in err.lower():
#             return "Cannot cancel — this appointment is already completed."
#         return f"Cancellation failed: {result['error']}"

#     return (
#         f"Appointment cancelled.\n"
#         f"ID: {appointment_id}\n"
#         f"Status: CANCELLED"
#     )


# @tool
# def reschedule_appointment(
#     appointment_id: str,
#     new_date: str,
#     new_start_time: str,
#     new_end_time: str,
# ) -> str:
#     """
#     Reschedule an appointment. Only a USER (client) can reschedule.
#     Employees cannot reschedule appointments.
#     Inputs:
#       appointment_id — _id of the appointment
#       new_date       — YYYY-MM-DD
#       new_start_time — e.g. '11:00 AM'
#       new_end_time   — e.g. '12:00 PM'
#     """
#     # Hard block — employee cannot reschedule
#     if api_client._active_role == "employee":
#         return (
#             "As an employee you can only view appointments. "
#             "You cannot reschedule appointments. "
#             "Please ask the client to update their own booking."
#         )

#     # Pre-check: do not reschedule cancelled or completed
#     check = api_get(f"/api/v1/appointment/{appointment_id}")
#     if "error" not in check:
#         appt = check.get("data", {})
#         if isinstance(appt, list):
#             appt = appt[0] if appt else {}
#         status = appt.get("status", "").lower()
#         if status in ["cancelled", "completed"]:
#             return (
#                 f"Cannot reschedule — appointment is already {status.upper()}.\n"
#                 f"Only upcoming appointments can be rescheduled."
#             )

#     body = {
#         "appointmentDate": new_date,
#         "startTime":       new_start_time,
#         "endTime":         new_end_time,
#     }

#     result = api_patch(f"/api/v1/appointment/{appointment_id}", body)

#     if "error" in result:
#         err = str(result["error"])
#         if "timed out" in err.lower():
#             return "Request timed out. Please try again."
#         return f"Reschedule failed: {result['error']}"

#     return (
#         f"Appointment rescheduled!\n"
#         f"Appointment ID : {appointment_id}\n"
#         f"New Date       : {new_date}\n"
#         f"New Time       : {new_start_time} - {new_end_time}"
#     )



from langchain_core.tools import tool
from langchain_core.tools import StructuredTool
from pydantic import BaseModel
from typing import Optional
import api_client
from datetime import datetime


def _format_date(raw: str) -> str:
    return raw[:10] if raw else "N/A"


def _generate_hour_slots(start: str, end: str) -> list:
    slots = []
    try:
        current = datetime.strptime(start, "%H:%M")
        end_dt  = datetime.strptime(end,   "%H:%M")
        while current < end_dt:
            next_slot = current.replace(hour=current.hour + 1, minute=0, second=0)
            if next_slot > end_dt:
                next_slot = end_dt
            slots.append({
                "startTime": current.strftime("%H:%M"),
                "endTime":   next_slot.strftime("%H:%M"),
            })
            current = next_slot
    except Exception:
        pass
    return slots


def make_booking_tools(token: str, role: str):
    """
    Build booking tools bound to a specific user token and role.
    Called once per session so each user gets their own tool instances.
    """

    @tool
    def get_available_slots(employee_id: str, date: str) -> str:
        """
        Check available time slots for a specific employee on a specific date.
        Always call this FIRST before booking.
        Inputs: employee_id, date (YYYY-MM-DD)
        """
        result = api_client.api_get(
            "/api/v1/appointment/available-slots",
            token,
            params={"employee": employee_id, "date": date}
        )

        if "error" in result:
            return f"Could not fetch slots: {result['error']}"

        data   = result.get("data", {})
        booked = data.get("bookedAppointments", [])
        booked_times = {b.get("startTime", "") for b in booked}

        available_ranges = data.get("availableRanges", [])
        working_hours    = data.get("workingHours", {})

        all_slots = []
        if available_ranges:
            for r in available_ranges:
                all_slots.extend(_generate_hour_slots(
                    r.get("startTime", "09:00"),
                    r.get("endTime",   "18:00")
                ))
        elif working_hours:
            all_slots = _generate_hour_slots(
                working_hours.get("startTime", "09:00"),
                working_hours.get("endTime",   "18:00")
            )

        free = [s for s in all_slots if s["startTime"] not in booked_times]

        if not free:
            return f"No available slots for employee {employee_id} on {date}."

        lines = [f"  - {s['startTime']} to {s['endTime']}" for s in free]
        return (
            f"Available slots for employee {employee_id} on {date} ({len(free)} free):\n"
            + "\n".join(lines)
            + f"\n\nTo book: 'Book appointment on {date} from [time] to [time]'"
        )

    @tool
    def create_appointment(
        employee_id: str,
        appointment_date: str,
        start_time: str,
        end_time: str,
        booking_notes: str = "",
    ) -> str:
        """
        Book a new appointment. Only users (clients) can book.
        Inputs: employee_id, appointment_date (YYYY-MM-DD), start_time, end_time, booking_notes (optional)
        """
        if role == "employee":
            return (
                "As an employee you can only view appointments. "
                "You cannot book appointments."
            )

        body = {
            "employee":        employee_id,
            "appointmentDate": appointment_date,
            "startTime":       start_time,
            "endTime":         end_time,
            "bookingNotes":    booking_notes,
        }
        result = api_client.api_post("/api/v1/appointment/", token, body)

        if "error" in result:
            return f"Booking failed: {result['error']}"

        data    = result.get("data", result)
        appt_id = data.get("_id", "N/A") if isinstance(data, dict) else "N/A"
        return (
            f"Appointment booked!\n"
            f"Date          : {appointment_date}\n"
            f"Time          : {start_time} - {end_time}\n"
            f"Notes         : {booking_notes or 'None'}\n"
            f"Appointment ID: {appt_id}\n"
            f"Save this ID to reschedule or cancel later."
        )

    @tool
    def get_my_appointments(status: str = "all") -> str:
        """
        Get appointments for the logged-in user.
        Input: status — all, upcoming, completed, cancelled
        """
        result = api_client.api_get(
            "/api/v1/appointment/",
            token,
            params={"status": status}
        )

        if "error" in result:
            return f"Could not fetch appointments: {result['error']}"

        appointments = result.get("data") or []
        if isinstance(appointments, dict):
            appointments = appointments.get("data") or appointments.get("appointments") or []

        if not appointments:
            return f"No appointments found with status '{status}'."

        lines = []
        for i, a in enumerate(appointments, 1):
            lines.append(
                f"{i}. ID     : {a.get('_id','N/A')}\n"
                f"   Date   : {_format_date(a.get('appointmentDate', a.get('date','')))}\n"
                f"   Time   : {a.get('startTime','N/A')} - {a.get('endTime','N/A')}\n"
                f"   Status : {a.get('status','N/A').upper()}\n"
                f"   Notes  : {a.get('bookingNotes', a.get('notes','None'))}"
            )
        return f"Your appointments ({len(lines)} found):\n\n" + "\n\n".join(lines)

    @tool
    def get_my_appointments_by_date(date: str) -> str:
        """
        Get appointments for a specific date.
        Input: date — YYYY-MM-DD
        """
        result = api_client.api_get(
            "/api/v1/appointment/",
            token,
            params={"status": "all"}
        )

        if "error" in result:
            return f"Could not fetch appointments: {result['error']}"

        all_appts = result.get("data") or []
        if isinstance(all_appts, dict):
            all_appts = all_appts.get("data") or all_appts.get("appointments") or []

        filtered = [
            a for a in all_appts
            if _format_date(a.get("appointmentDate", a.get("date", ""))) == date
        ]

        if not filtered:
            return f"No appointments found on {date}."

        lines = [
            f"  - {a.get('startTime','N/A')} to {a.get('endTime','N/A')}"
            f" | Status: {a.get('status','N/A').upper()}"
            f" | Notes: {a.get('bookingNotes', a.get('notes','None'))}"
            f" | ID: {a.get('_id','N/A')}"
            for a in filtered
        ]
        return f"Appointments on {date} ({len(lines)} found):\n" + "\n".join(lines)

    @tool
    def get_single_appointment(appointment_id: str) -> str:
        """
        Get full details of one appointment.
        Input: appointment_id — MongoDB _id
        """
        result = api_client.api_get(
            f"/api/v1/appointment/{appointment_id}",
            token
        )

        if "error" in result:
            return f"Could not fetch appointment: {result['error']}"

        a = result.get("data", result)
        if isinstance(a, list):
            a = a[0] if a else {}

        employee    = a.get("employee", {})
        emp_name    = employee.get("name", str(employee)) if isinstance(employee, dict) else str(employee)
        client      = a.get("client", a.get("user", {}))
        client_name = client.get("name", str(client)) if isinstance(client, dict) else str(client)

        return (
            f"Appointment Details:\n"
            f"ID       : {a.get('_id','N/A')}\n"
            f"Date     : {_format_date(a.get('appointmentDate', a.get('date','')))}\n"
            f"Time     : {a.get('startTime','N/A')} - {a.get('endTime','N/A')}\n"
            f"Status   : {a.get('status','N/A').upper()}\n"
            f"Employee : {emp_name}\n"
            f"Client   : {client_name}\n"
            f"Notes    : {a.get('bookingNotes', a.get('notes','None'))}"
        )

    @tool
    def reschedule_appointment(
        appointment_id: str,
        new_date: str,
        new_start_time: str,
        new_end_time: str,
    ) -> str:
        """
        Reschedule an appointment. Only users can reschedule.
        Inputs: appointment_id, new_date (YYYY-MM-DD), new_start_time, new_end_time
        """
        if role == "employee":
            return (
                "As an employee you can only view appointments. "
                "You cannot reschedule. Please ask the client to update their booking."
            )

        check = api_client.api_get(f"/api/v1/appointment/{appointment_id}", token)
        if "error" not in check:
            appt   = check.get("data", {})
            if isinstance(appt, list):
                appt = appt[0] if appt else {}
            status = appt.get("status", "").lower()
            if status in ["cancelled", "completed"]:
                return f"Cannot reschedule — appointment is already {status.upper()}."

        result = api_client.api_patch(
            f"/api/v1/appointment/{appointment_id}",
            token,
            {
                "appointmentDate": new_date,
                "startTime":       new_start_time,
                "endTime":         new_end_time,
            }
        )

        if "error" in result:
            return f"Reschedule failed: {result['error']}"

        return (
            f"Appointment rescheduled!\n"
            f"ID       : {appointment_id}\n"
            f"New Date : {new_date}\n"
            f"New Time : {new_start_time} - {new_end_time}"
        )

    @tool
    def cancel_appointment(appointment_id: str) -> str:
        """
        Cancel an appointment. Only users can cancel.
        Input: appointment_id — MongoDB _id. Always confirm before calling.
        """
        if role == "employee":
            return (
                "As an employee you can only view appointments. "
                "You cannot cancel. Please ask the client to cancel their booking."
            )

        check = api_client.api_get(f"/api/v1/appointment/{appointment_id}", token)
        if "error" not in check:
            appt = check.get("data", {})
            if isinstance(appt, list):
                appt = appt[0] if appt else {}
            status = appt.get("status", "").lower()
            if status == "cancelled":
                return "This appointment is already cancelled."
            if status in ["completed", "started", "in_progress"]:
                return f"Cannot cancel — appointment is {status.upper()}."

        result = api_client.api_patch(
            f"/api/v1/appointment/{appointment_id}",
            token,
            {"status": "cancelled"}
        )

        if "error" in result:
            return f"Cancellation failed: {result['error']}"

        return (
            f"Appointment cancelled.\n"
            f"ID: {appointment_id}\n"
            f"Status: CANCELLED"
        )

    return [
        get_available_slots,
        create_appointment,
        get_my_appointments,
        get_my_appointments_by_date,
        get_single_appointment,
        reschedule_appointment,
        cancel_appointment,
    ]
from langchain_core.tools import tool
import api_client
import requests
import os
from datetime import date as date_lib


def _fmt(raw: str) -> str:
    """Clean ISO date to YYYY-MM-DD."""
    return raw[:10] if raw else "N/A"


def make_summary_tools(token: str):
    """Build summary and dashboard tools bound to user token."""

    def _get_todays_appointments() -> list:
        """
        Internal helper — reuses the exact same logic as employee_dashboard.
        Returns list of today's appointment dicts or empty list.
        """
        today  = date_lib.today().strftime("%Y-%m-%d")
        result = api_client.api_get(
            "/api/v1/appointments",
            token,
            params={"status": "all"}
        )
        if "error" in result:
            return []
        all_appts = result.get("data") or []
        if isinstance(all_appts, dict):
            all_appts = all_appts.get("data") or []
        return [
            a for a in all_appts
            if _fmt(a.get("appointmentDate", a.get("date", ""))) == today
        ]

    def _get_upcoming_appointments() -> list:
        """
        Internal helper — gets upcoming appointments.
        Returns list or empty list.
        """
        result = api_client.api_get(
            "/api/v1/appointments",
            token,
            params={"status": "upcoming"}
        )
        if "error" in result:
            return []
        appts = result.get("data") or []
        if isinstance(appts, dict):
            appts = appts.get("data") or []
        return appts

    # ── Tools ──────────────────────────────────────────────

    @tool
    def get_daily_summary() -> str:
        """
        Get a complete daily summary — appointments today, attendance,
        and leave balance. Use for the Daily Summary quick action.
        No input needed.
        """
        today   = date_lib.today().strftime("%Y-%m-%d")
        summary = []

        # Appointments today — uses same path as employee_dashboard
        todays = _get_todays_appointments()
        if todays:
            upcoming_count = sum(
                1 for a in todays
                if a.get("status", "").lower() == "upcoming"
            )
            summary.append(
                f"Appointments today: {len(todays)} total, "
                f"{upcoming_count} upcoming"
            )
        else:
            summary.append("Appointments today: None")

        # Attendance status
        attend_result = api_client.api_get("/api/v1/work/attendance", token)
        if "error" not in attend_result:
            data      = attend_result.get("data", {})
            status    = data.get("status", data.get("action", "Not recorded"))
            check_in  = data.get("checkIn", data.get("startTime", "N/A"))
            summary.append(f"Attendance: {status} | Check-in: {check_in}")
        else:
            summary.append("Attendance: could not load")

        # Leave balance
        leave_result = api_client.api_get("/api/v1/work/leave-balance", token)
        if "error" not in leave_result:
            balances = leave_result.get("data", {}).get("balances", {})
            if balances:
                parts = [
                    f"{lt}: {v.get('remaining', 0)} days left"
                    for lt, v in balances.items()
                ]
                summary.append("Leave: " + " | ".join(parts))

        return (
            f"Daily Summary — {today}:\n"
            + "\n".join(f"• {s}" for s in summary)
        )

    @tool
    def get_upcoming_schedule() -> str:
        """
        Get upcoming appointments.
        Use for the Upcoming Schedule quick action.
        No input needed.
        """
        appts = _get_upcoming_appointments()

        if not appts:
            return "No upcoming appointments scheduled."

        lines = []
        for a in appts[:10]:
            appt_date = _fmt(a.get("appointmentDate", a.get("date", "")))
            lines.append(
                f"  • {appt_date} | "
                f"{a.get('startTime','N/A')} - {a.get('endTime','N/A')} | "
                f"{a.get('bookingNotes', a.get('notes', 'No notes'))} | "
                f"ID: {a.get('_id','N/A')}"
            )

        return (
            f"Upcoming Schedule ({len(lines)} appointment(s)):\n"
            + "\n".join(lines)
        )

    @tool
    def get_todays_agenda() -> str:
        """
        Get full agenda for today — appointments and attendance.
        Use for the Today's Agenda quick action.
        No input needed.
        """
        today  = date_lib.today().strftime("%Y-%m-%d")
        output = [f"Today's Agenda — {today}"]

        # Appointments — uses same logic as employee_dashboard
        todays = _get_todays_appointments()
        if todays:
            output.append(f"\nAppointments ({len(todays)}):")
            for a in todays:
                output.append(
                    f"  • {a.get('startTime','N/A')} - {a.get('endTime','N/A')}"
                    f" | {a.get('status','N/A').upper()}"
                    f" | {a.get('bookingNotes', a.get('notes', 'No notes'))}"
                )
        else:
            output.append("\nNo appointments today.")

        # Attendance
        attend_result = api_client.api_get("/api/v1/work/attendance", token)
        if "error" not in attend_result:
            data      = attend_result.get("data", {})
            status    = data.get("status", "Not recorded")
            check_in  = data.get("checkIn", "N/A")
            check_out = data.get("checkOut", "Not yet")
            output.append(
                f"\nAttendance: {status} | "
                f"In: {check_in} | Out: {check_out}"
            )

        return "\n".join(output)

    @tool
    def get_team_performance() -> str:
        """
        Get team performance and earnings overview.
        Use for the Team Performance quick action.
        No input needed.
        """
        result = api_client.api_get("/api/v1/earnings/dashboard", token)

        if "error" in result:
            return f"Could not fetch team performance: {result['error']}"

        data = result.get("data", result)

        if not data:
            return "No performance data available."

        lines = []
        if isinstance(data, dict):
            for key, value in data.items():
                label = key.replace("_", " ").replace("-", " ").title()
                if isinstance(value, (int, float, str)):
                    lines.append(f"  • {label}: {value}")
                elif isinstance(value, dict):
                    lines.append(f"  {label}:")
                    for k2, v2 in value.items():
                        lines.append(f"    - {k2}: {v2}")

        if not lines:
            return (
                f"Performance data received but could not be formatted.\n"
                f"Raw: {str(data)[:300]}"
            )

        return "Team Performance:\n" + "\n".join(lines)

    @tool
    def check_in_attendance() -> str:
        """
        Check in for today. No input needed.
        """
        BASE_URL = os.getenv("BASE_URL", "")
        try:
            res = requests.post(
                f"{BASE_URL}/api/v1/work/attendance",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type":  "application/json",
                },
                json={"action": "check-in"},
                timeout=30,
            )
            data = res.json()
            if not res.ok:
                return f"Check-in failed: {data.get('message', 'Unknown error')}"
            return "You have successfully checked in for today."
        except Exception as e:
            return f"Check-in error: {str(e)}"

    @tool
    def check_out_attendance() -> str:
        """
        Check out for today. No input needed.
        """
        BASE_URL = os.getenv("BASE_URL", "")
        try:
            res = requests.post(
                f"{BASE_URL}/api/v1/work/attendance",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type":  "application/json",
                },
                json={"action": "check-out"},
                timeout=30,
            )
            data = res.json()
            if not res.ok:
                return f"Check-out failed: {data.get('message', 'Unknown error')}"
            return "You have successfully checked out for today."
        except Exception as e:
            return f"Check-out error: {str(e)}"

    return [
        get_daily_summary,
        get_upcoming_schedule,
        get_todays_agenda,
        get_team_performance,
        check_in_attendance,
        check_out_attendance,
    ]

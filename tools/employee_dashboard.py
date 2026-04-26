from langchain.tools import tool
import api_client
from datetime import date as date_lib
from collections import defaultdict
import requests
import os


def _fmt(raw: str) -> str:
    return raw[:10] if raw else "N/A"


def make_employee_tools(token: str):
    """Build employee view-only tools bound to a specific token."""

    @tool
    def get_my_appointments_today() -> str:
        """View today's appointments for the logged-in employee. No input needed."""
        today  = date_lib.today().strftime("%Y-%m-%d")
        result = api_client.api_get(
            "/api/v1/appointment/",
            token,
            params={"status": "all"}
        )

        if "error" in result:
            return f"Could not fetch appointments: {result['error']}"

        all_appts = result.get("data") or []
        if isinstance(all_appts, dict):
            all_appts = all_appts.get("data") or []

        todays = [
            a for a in all_appts
            if _fmt(a.get("appointmentDate", a.get("date", ""))) == today
        ]

        if not todays:
            return f"You have no appointments today ({today})."

        lines = [
            f"  - {a.get('startTime','N/A')} to {a.get('endTime','N/A')}"
            f" | Status: {a.get('status','N/A').upper()}"
            f" | Notes: {a.get('bookingNotes', a.get('notes','None'))}"
            f" | ID: {a.get('_id','N/A')}"
            for a in todays
        ]
        return f"Your appointments today ({today}) — {len(lines)} found:\n" + "\n".join(lines)

    @tool
    def get_my_appointment_calendar(month: str, year: str) -> str:
        """
        View appointment calendar for a given month and year.
        Inputs: month (number e.g. '4'), year (e.g. '2026')
        """
        result = api_client.api_get(
            "/api/v1/appointment/employee/calendar",
            token,
            params={"month": month, "year": year}
        )

        if "error" in result:
            return f"Could not fetch calendar: {result['error']}"

        data = result.get("data", [])

        if not data:
            return f"No appointments found in your calendar for {month}/{year}."

        grouped = defaultdict(list)
        for item in data:
            full_date = item.get("fullDate", "N/A")
            status    = item.get("status", "unknown")
            grouped[full_date].append(status)

        lines = []
        for full_date in sorted(grouped.keys()):
            statuses = grouped[full_date]
            summary  = ", ".join(statuses)
            lines.append(f"  {full_date} — {len(statuses)} appointment(s) — {summary}")

        return (
            f"Your calendar for {month}/{year} ({len(grouped)} day(s)):\n"
            + "\n".join(lines)
        )

    @tool
    def get_my_leave_status() -> str:
        """View all leave applications for the logged-in employee."""
        result = api_client.api_get("/api/v1/work/leave", token)

        if "error" in result:
            return f"Could not fetch leave: {result['error']}"

        leaves = result.get("data") or []
        if not leaves:
            return "You have no leave applications on record."

        lines = [
            f"- {l.get('startDate','N/A')} to {l.get('endDate','N/A')}"
            f" | Type: {l.get('leaveType','N/A')}"
            f" | Status: {l.get('status','N/A').upper()}"
            f" | ID: {l.get('_id','N/A')}"
            for l in leaves
        ]
        return "Your leave applications:\n" + "\n".join(lines)

    @tool
    def get_my_leave_balance() -> str:
        """View remaining leave balance for the logged-in employee."""
        result = api_client.api_get("/api/v1/work/leave-balance", token)

        if "error" in result:
            return f"Could not fetch leave balance: {result['error']}"

        data     = result.get("data", {})
        balances = data.get("balances", {})

        if not balances:
            return "No leave balance data found."

        lines = [
            f"  {leave_type:<22} Total: {v.get('total',0)}"
            f"  |  Used: {v.get('used',0)}"
            f"  |  Remaining: {v.get('remaining',0)}"
            for leave_type, v in balances.items()
        ]
        return "Your leave balance:\n" + "\n".join(lines)

    @tool
    def get_single_leave_status(leave_id: str) -> str:
        """
        View status of one specific leave application.
        Input: leave_id — MongoDB _id
        """
        result = api_client.api_get(f"/api/v1/work/leave/{leave_id}", token)

        if "error" in result:
            return f"Could not fetch leave: {result['error']}"

        l = result.get("data", result)
        return (
            f"Leave Request:\n"
            f"ID      : {l.get('_id','N/A')}\n"
            f"Dates   : {l.get('startDate','N/A')} to {l.get('endDate','N/A')}\n"
            f"Type    : {l.get('leaveType','N/A')}\n"
            f"Reason  : {l.get('reason','N/A')}\n"
            f"Status  : {l.get('status','N/A').upper()}"
        )

    return [
        get_my_appointments_today,
        get_my_appointment_calendar,
        get_my_leave_status,
        get_my_leave_balance,
        get_single_leave_status,
    ]
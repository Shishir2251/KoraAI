# from langchain.tools import tool
# from api_client import api_get, api_post
# import requests
# import os
# from dotenv import load_dotenv

# load_dotenv()

# BASE_URL       = os.getenv("BASE_URL")
# EMPLOYEE_TOKEN = os.getenv("EMPLOYEE_TOKEN", "")


# @tool
# def apply_for_leave(
#     start_date: str,
#     end_date: str,
#     leave_type: str,
#     reason: str = "No reason provided",
# ) -> str:
#     """
#     Submit a leave application for the logged-in employee.
#     Inputs:
#       start_date  — YYYY-MM-DD e.g. '2026-05-01'
#       end_date    — YYYY-MM-DD e.g. '2026-05-03'
#       leave_type  — 'Sick Leave', 'Casual Leave', or 'Leave Without Pay'
#       reason      — optional short description (default: No reason provided)

#     Use multipart/form-data because backend expects formdata not JSON.
#     """
#     try:
#         res = requests.post(
#             f"{BASE_URL}/api/v1/work/leave",
#             headers={"Authorization": f"Bearer {EMPLOYEE_TOKEN}"},
#             data={
#                 "startDate": start_date,
#                 "endDate":   end_date,
#                 "leaveType": leave_type,
#                 "reason":    reason,
#             },
#             timeout=30,
#         )
#         data = res.json()

#         if not res.ok:
#             return (
#                 f"Failed to submit leave.\n"
#                 f"Error: {data.get('message', 'Unknown error')}"
#             )

#         result = data.get("data", {})
#         return (
#             f"Leave application submitted!\n"
#             f"Dates     : {start_date} to {end_date}\n"
#             f"Type      : {leave_type}\n"
#             f"Reason    : {reason}\n"
#             f"Status    : PENDING\n"
#             f"ID        : {result.get('_id', 'N/A')}"
#         )
#     except Exception as e:
#         return f"Could not submit leave: {str(e)}"


# @tool
# def check_leave_status(leave_id: str = "") -> str:
#     """
#     Check leave application status.
#     Input: leave_id — optional. If blank returns all applications.
#     """
#     if leave_id:
#         result = api_get(f"/api/v1/work/leave/{leave_id}")
#         if "error" in result:
#             return f"Could not fetch leave: {result['error']}"
#         l = result.get("data", result)
#         return (
#             f"Leave ID {leave_id}:\n"
#             f"Dates  : {l.get('startDate','N/A')} to {l.get('endDate','N/A')}\n"
#             f"Type   : {l.get('leaveType','N/A')}\n"
#             f"Status : {l.get('status','N/A').upper()}"
#         )
#     else:
#         result = api_get("/api/v1/work/leave")
#         if "error" in result:
#             return f"Could not fetch leave list: {result['error']}"
#         leaves = result.get("data", [])
#         if not leaves:
#             return "No leave applications found."
#         lines = [
#             f"- {l.get('startDate','N/A')} to {l.get('endDate','N/A')} "
#             f"| {l.get('leaveType','N/A')} "
#             f"| {l.get('status','N/A').upper()} "
#             f"| ID: {l.get('_id','N/A')}"
#             for l in leaves
#         ]
#         return "Your leave applications:\n" + "\n".join(lines)



import os
import requests
from langchain.tools import tool
from dotenv import load_dotenv
import api_client

load_dotenv()

BASE_URL = os.getenv("BASE_URL")


def make_leave_tools(token: str):
    """Build leave tools bound to a specific user token."""

    @tool
    def apply_for_leave(
        start_date: str,
        end_date: str,
        leave_type: str,
        reason: str = "No reason provided",
    ) -> str:
        """
        Submit a leave application for the logged-in employee.
        Inputs:
          start_date  — YYYY-MM-DD e.g. '2026-05-01'
          end_date    — YYYY-MM-DD e.g. '2026-05-03'
          leave_type  — 'Sick Leave', 'Casual Leave', or 'Leave Without Pay'
          reason      — optional short description
        """
        try:
            res = requests.post(
                f"{BASE_URL}/api/v1/work/leave",
                headers={"Authorization": f"Bearer {token}"},
                data={
                    "startDate": start_date,
                    "endDate":   end_date,
                    "leaveType": leave_type,
                    "reason":    reason,
                },
                timeout=30,
            )
            data = res.json()
            if not res.ok:
                return f"Failed to submit leave: {data.get('message', 'Unknown error')}"

            result = data.get("data", {})
            return (
                f"Leave application submitted!\n"
                f"Dates  : {start_date} to {end_date}\n"
                f"Type   : {leave_type}\n"
                f"Reason : {reason}\n"
                f"Status : PENDING\n"
                f"ID     : {result.get('_id', 'N/A')}"
            )
        except Exception as e:
            return f"Could not submit leave: {str(e)}"

    @tool
    def check_leave_status(leave_id: str = "") -> str:
        """
        Check leave application status.
        Input: leave_id — optional MongoDB _id.
        If blank, returns all leave applications.
        """
        if leave_id:
            result = api_client.api_get(f"/api/v1/work/leave/{leave_id}", token)
            if "error" in result:
                return f"Could not fetch leave: {result['error']}"
            l = result.get("data", result)
            return (
                f"Leave ID {leave_id}:\n"
                f"Dates  : {l.get('startDate','N/A')} to {l.get('endDate','N/A')}\n"
                f"Type   : {l.get('leaveType','N/A')}\n"
                f"Status : {l.get('status','N/A').upper()}"
            )
        else:
            result = api_client.api_get("/api/v1/work/leave", token)
            if "error" in result:
                return f"Could not fetch leave list: {result['error']}"
            leaves = result.get("data", [])
            if not leaves:
                return "No leave applications found."
            lines = [
                f"- {l.get('startDate','N/A')} to {l.get('endDate','N/A')}"
                f" | {l.get('leaveType','N/A')}"
                f" | {l.get('status','N/A').upper()}"
                f" | ID: {l.get('_id','N/A')}"
                for l in leaves
            ]
            return "Your leave applications:\n" + "\n".join(lines)

    return [apply_for_leave, check_leave_status]
# seed_employee_appointment.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL       = os.getenv("BASE_URL")
USER_TOKEN     = os.getenv("USER_TOKEN")
EMPLOYEE_TOKEN = os.getenv("EMPLOYEE_TOKEN")

# Get the real employee user ID from their token
profile = requests.get(
    f"{BASE_URL}/api/v1/user/profile",
    headers={"Authorization": f"Bearer {EMPLOYEE_TOKEN}"},
    timeout=15
).json()

employee_id = profile.get("data", {}).get("_id")
if not employee_id:
    print("Could not get employee ID from token. Check EMPLOYEE_TOKEN in .env")
    exit(1)

print(f"Employee ID from token: {employee_id}")

# Book appointments using USER token, employee ID from above
headers = {
    "Authorization": f"Bearer {USER_TOKEN}",
    "Content-Type":  "application/json"
}

appointments = [
    {"appointmentDate": "2026-04-25", "startTime": "11:00 AM", "endTime": "12:00 PM", "bookingNotes": "Haircut"},
    {"appointmentDate": "2026-04-26", "startTime": "10:00 AM", "endTime": "11:00 AM", "bookingNotes": "Color"},
    {"appointmentDate": "2026-04-27", "startTime": "02:00 PM", "endTime": "03:00 PM", "bookingNotes": "Trim"},
]

for a in appointments:
    body = {
        "employee":        employee_id,
        "appointmentDate": a["appointmentDate"],
        "startTime":       a["startTime"],
        "endTime":         a["endTime"],
        "bookingNotes":    a["bookingNotes"],
    }
    res = requests.post(
        f"{BASE_URL}/api/v1/appointment/",
        headers=headers,
        json=body,
        timeout=30
    )
    d = res.json()
    if res.ok:
        appt_id = d.get("data", {}).get("_id", "N/A")
        print(f"Booked: {a['appointmentDate']} {a['startTime']} — ID: {appt_id}")
    else:
        print(f"Failed: {d.get('message','unknown')}")
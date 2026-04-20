import requests
import os
from dotenv import load_dotenv
from datetime import date, timedelta

load_dotenv()

BASE_URL    = os.getenv("BASE_URL")
USER_TOKEN  = os.getenv("USER_TOKEN")
EMPLOYEE_ID = os.getenv("EMPLOYEE_ID")

headers = {
    "Authorization": f"Bearer {USER_TOKEN}",
    "Content-Type":  "application/json"
}

# Verify employee ID is correct
profile = requests.get(
    f"{BASE_URL}/api/v1/user/profile",
    headers={"Authorization": f"Bearer {os.getenv('EMPLOYEE_TOKEN')}"},
    timeout=15
).json()
real_emp_id = profile.get("data", {}).get("_id", "")

print(f"EMPLOYEE_ID in .env : {EMPLOYEE_ID}")
print(f"Real ID from token  : {real_emp_id}")

if EMPLOYEE_ID != real_emp_id:
    print(f"\nMISMATCH — using real ID: {real_emp_id}")
    EMPLOYEE_ID = real_emp_id
else:
    print("MATCH — IDs are correct\n")

# Book appointments on future dates
today = date.today()
appointments = [
    {
        "appointmentDate": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
        "startTime": "10:00 AM",
        "endTime":   "11:00 AM",
        "bookingNotes": "Haircut"
    },
    {
        "appointmentDate": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
        "startTime": "02:00 PM",
        "endTime":   "03:00 PM",
        "bookingNotes": "Color treatment"
    },
    {
        "appointmentDate": (today + timedelta(days=3)).strftime("%Y-%m-%d"),
        "startTime": "11:00 AM",
        "endTime":   "12:00 PM",
        "bookingNotes": "Trim"
    },
    {
        "appointmentDate": (today + timedelta(days=5)).strftime("%Y-%m-%d"),
        "startTime": "03:00 PM",
        "endTime":   "04:00 PM",
        "bookingNotes": "Beard styling"
    },
]

print("Booking appointments...\n")
booked_ids = []
for a in appointments:
    res = requests.post(
        f"{BASE_URL}/api/v1/appointment/",
        headers=headers,
        json={
            "employee":        EMPLOYEE_ID,
            "appointmentDate": a["appointmentDate"],
            "startTime":       a["startTime"],
            "endTime":         a["endTime"],
            "bookingNotes":    a["bookingNotes"],
        },
        timeout=30
    )
    d = res.json()
    if res.ok:
        appt_id = d.get("data", {}).get("_id", "N/A")
        booked_ids.append(appt_id)
        print(f"Booked: {a['appointmentDate']} {a['startTime']} — {a['bookingNotes']} | ID: {appt_id}")
    else:
        print(f"Failed: {a['appointmentDate']} {a['startTime']} — {d.get('message','unknown')}")

print(f"\nTotal booked: {len(booked_ids)}")
print("\nAppointment IDs (save these for testing):")
for i, id in enumerate(booked_ids, 1):
    print(f"  {i}. {id}")
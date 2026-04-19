# find_free_slots.py
import requests
import os
from dotenv import load_dotenv
from datetime import date, timedelta
from datetime import datetime as dt

load_dotenv()

BASE_URL    = os.getenv("BASE_URL")
USER_TOKEN  = os.getenv("USER_TOKEN")
EMPLOYEE_ID = os.getenv("EMPLOYEE_ID")

headers = {"Authorization": f"Bearer {USER_TOKEN}"}
print(f"Finding free slots for employee {EMPLOYEE_ID}\n")

today = date.today()
for i in range(1, 15):
    check_date = (today + timedelta(days=i)).strftime("%Y-%m-%d")
    res = requests.get(
        f"{BASE_URL}/api/v1/appointment/available-slots",
        headers=headers,
        params={"employee": EMPLOYEE_ID, "date": check_date},
        timeout=15
    )
    if not res.ok:
        print(f"  {check_date}: error {res.status_code}")
        continue

    data   = res.json().get("data", {})
    ranges = data.get("availableRanges", [])
    booked = data.get("bookedAppointments", [])

    if ranges:
        range_str = ", ".join([f"{r['startTime']}-{r['endTime']}" for r in ranges])
        print(f"  {check_date}: FREE — {range_str}  ({len(booked)} booked)")
    else:
        print(f"  {check_date}: fully booked ({len(booked)} appointments)")
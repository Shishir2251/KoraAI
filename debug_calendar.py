# debug_calendar.py
import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

BASE_URL       = os.getenv("BASE_URL")
EMPLOYEE_TOKEN = os.getenv("EMPLOYEE_TOKEN")

headers = {"Authorization": f"Bearer {EMPLOYEE_TOKEN}"}

print("=== Calendar endpoint raw response ===")
res = requests.get(
    f"{BASE_URL}/api/v1/appointment/employee/calendar",
    headers=headers,
    params={"month": "4", "year": "2026"},
    timeout=30
)
print(f"Status: {res.status_code}")
print(json.dumps(res.json(), indent=2))
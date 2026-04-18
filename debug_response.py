# debug_responses.py
import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

BASE_URL       = os.getenv("BASE_URL")
EMPLOYEE_TOKEN = os.getenv("EMPLOYEE_TOKEN")

headers = {"Authorization": f"Bearer {EMPLOYEE_TOKEN}"}

print("=" * 60)
print("TEST 1: Calendar endpoint")
print("=" * 60)
res = requests.get(
    f"{BASE_URL}/api/v1/appointment/employee/calendar",
    headers=headers,
    params={"month": "4", "year": "2026"},
    timeout=30
)
print(f"Status: {res.status_code}")
print(json.dumps(res.json(), indent=2))

print("\n" + "=" * 60)
print("TEST 2: Leave balance endpoint")
print("=" * 60)
res2 = requests.get(
    f"{BASE_URL}/api/v1/work/leave-balance",
    headers=headers,
    timeout=30
)
print(f"Status: {res2.status_code}")
print(json.dumps(res2.json(), indent=2))

print("\n" + "=" * 60)
print("TEST 3: My appointments (employee token)")
print("=" * 60)
res3 = requests.get(
    f"{BASE_URL}/api/v1/appointment/",
    headers=headers,
    params={"status": "all"},
    timeout=30
)
print(f"Status: {res3.status_code}")
print(json.dumps(res3.json(), indent=2)[:1000])
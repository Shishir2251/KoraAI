# check_employee_id.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL       = os.getenv("BASE_URL")
EMPLOYEE_TOKEN = os.getenv("EMPLOYEE_TOKEN")
EMPLOYEE_ID    = os.getenv("EMPLOYEE_ID")

res = requests.get(
    f"{BASE_URL}/api/v1/user/profile",
    headers={"Authorization": f"Bearer {EMPLOYEE_TOKEN}"},
    timeout=60
)



data = res.json()
real_id = data.get("data", {}).get("_id", "NOT FOUND")

print(f"EMPLOYEE_TOKEN belongs to user ID : {real_id}")
print(f"EMPLOYEE_ID in your .env          : {EMPLOYEE_ID}")
print()

if real_id == EMPLOYEE_ID:
    print("MATCH — calendar will show appointments correctly.")
else:
    print("MISMATCH — this is why calendar is empty.")
    print(f"Fix: update your .env EMPLOYEE_ID to: {real_id}")
    print(f"Also re-run seed script using this corrected ID.")
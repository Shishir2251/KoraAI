import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL     = os.getenv("BASE_URL")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
EMPLOYEE_ID  = os.getenv("EMPLOYEE_ID", "69df23bd857943bd90be03fb")

headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

tests = [
    ("GET",  "/api/v1/user/profile",                                                  None),
    ("GET",  "/api/v1/appointment/?status=all",                                       None),
    ("GET",  f"/api/v1/appointment/available-slots?employee={EMPLOYEE_ID}&date=2026-04-20", None),
    ("GET",  "/api/v1/appointment/employee/calendar?month=4&year=2026",               None),
    ("GET",  "/api/v1/work/leave",                                                    None),
    ("GET",  "/api/v1/work/leave-balance",                                            None),
    ("GET",  "/api/v1/employee",                                                      None),
]

print(f"Backend : {BASE_URL}\n")
print(f"{'Endpoint':<65} {'Status':<8} Result")
print("-" * 100)

for method, path, body in tests:
    try:
        url = f"{BASE_URL}{path}"
        res = requests.get(url, headers=headers, timeout=10)

        try:
            data    = res.json()
            preview = str(data.get("message", data.get("success", str(data))))[:50]
        except Exception:
            preview = res.text[:50]

        icon = "OK  " if res.ok else "FAIL"
        print(f"{path:<65} {res.status_code:<8} [{icon}] {preview}")

    except Exception as e:
        print(f"{path:<65} ERROR    {str(e)[:50]}")

# Also add EMPLOYEE_ID to .env reminder
print(f"\nNOTE: Add this to your .env:")
print(f"EMPLOYEE_ID={EMPLOYEE_ID}")
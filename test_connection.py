import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL     = os.getenv("BASE_URL")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

tests = [
    ("GET", "/api/v1/user/profile",                          None),
    ("GET", "/api/v1/schedule/",                             None),
    ("GET", "/api/v1/schedule/?date=2026-04-15&status=all",  None),
    ("GET", "/api/v1/schedule/?type=next",                   None),
    ("GET", "/api/v1/schedule/calendar?month=2026-04",       None),
    ("GET", "/api/v1/work/leave",                            None),
    ("GET", "/api/v1/work/leave-balance",                    None),
    ("GET", "/api/v1/employee",                              None),
]

print(f"Backend: {BASE_URL}\n")
print(f"{'Endpoint':<50} {'Status':<8} Result")
print("-" * 80)

for method, path, body in tests:
    try:
        url = f"{BASE_URL}{path}"
        if method == "GET":
            res = requests.get(url, headers=headers, timeout=10)
        else:
            res = requests.post(url, headers=headers, json=body, timeout=10)

        # Short preview of response
        try:
            data    = res.json()
            preview = str(data.get("message", data.get("success", "")))[:40]
        except Exception:
            preview = res.text[:40]

        status_icon = "OK" if res.ok else "FAIL"
        print(f"{path:<50} {res.status_code:<8} [{status_icon}] {preview}")

    except Exception as e:
        print(f"{path:<50} ERROR    {str(e)[:40]}")
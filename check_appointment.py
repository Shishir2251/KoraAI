# check_appointment.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
TOKEN    = "paste your user accessToken here"

res = requests.get(
    f"{BASE_URL}/api/v1/appointment/69ec7b16cb13f12890b43e70",
    headers={"Authorization": f"Bearer {TOKEN}"},
    timeout=15
)
import json
print(f"Status: {res.status_code}")
print(json.dumps(res.json(), indent=2))
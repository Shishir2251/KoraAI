import requests
import json

BASE_URL = "https://backendkoraai.onrender.com"   # replace with your real backend URL

response = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    headers={"Content-Type": "application/json"},
    json={
        "email":    "arefin001@gmail.com",   # your registered email
        "password": "1234567"               # your password
    }
)

data = response.json()
print(json.dumps(data, indent=2))
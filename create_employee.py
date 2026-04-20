import requests
import json

BASE_URL = "https://backendkoraai.onrender.com"

print("=== Creating new EMPLOYEE account ===\n")

# Step 1 — Register
reg = requests.post(
    f"{BASE_URL}/api/v1/auth/register",
    json={
        "name":            "Test Employee",
        "email":           "testemployee001@gmail.com",
        "phoneNumber":     "01722222222",
        "password":        "123456",
        "confirmPassword": "123456",
        "role":            "employee"
    },
    timeout=30
)
print(f"Register status : {reg.status_code}")
print(f"Register message: {reg.json().get('message','')}")

# Step 2 — Login
login = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    json={
        "email":    "testemployee001@gmail.com",
        "password": "123456"
    },
    timeout=30
)
data = login.json()
print(f"Login status    : {login.status_code}")

if login.ok:
    token       = data.get("data", {}).get("accessToken", "")
    employee_id = data.get("data", {}).get("user", {}).get("_id", "")
    role        = data.get("data", {}).get("user", {}).get("role", "")

    print(f"\nName        : Test Employee")
    print(f"Email       : testemployee001@gmail.com")
    print(f"Role        : {role}")
    print(f"Employee ID : {employee_id}")
    print(f"Token       : {token[:50]}...")

    print("\n=== COPY THIS INTO YOUR .env ===")
    print(f"EMPLOYEE_TOKEN={token}")
    print(f"EMPLOYEE_ID={employee_id}")
else:
    print(f"Login failed: {data.get('message', 'unknown error')}")
# refresh_tokens.py
import requests
import json

BASE_URL = "https://backendkoraai.onrender.com"

def login(email, password, label):
    print(f"\nLogging in as {label}...")
    res = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": email, "password": password},
        timeout=30
    )
    data = res.json()
    if res.ok:
        token   = data.get("data", {}).get("accessToken", "")
        user_id = data.get("data", {}).get("user", {}).get("_id", "")
        print(f"  Token  : {token[:40]}...")
        print(f"  User ID: {user_id}")
        return token, user_id
    else:
        print(f"  Failed : {data.get('message', 'unknown error')}")
        return None, None

# Use your registered emails and passwords
user_token,     user_id     = login("korauser001@gmail.com",     "123456", "USER")
employee_token, employee_id = login("koraemployee001@gmail.com", "123456", "EMPLOYEE")

print("\n\n=== COPY THIS INTO YOUR .env ===")
print(f"USER_TOKEN={user_token}")
print(f"EMPLOYEE_TOKEN={employee_token}")
print(f"USER_ID={user_id}")
print(f"EMPLOYEE_ID={employee_id}")
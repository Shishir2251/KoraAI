# setup_accounts.py
import requests
import json

BASE_URL = "https://backendkoraai.onrender.com"

def register_and_login(name, email, password, role):
    print(f"\n--- Setting up {role} account ---")

    # Register
    reg = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={
            "name":            name,
            "email":           email,
            "phoneNumber":     "01700000000",
            "password":        password,
            "confirmPassword": password,
            "role":            role,
        }
    )
    print(f"Register: {reg.status_code} — {reg.json().get('message','')}")

    # Login
    login = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": email, "password": password}
    )
    data = login.json()
    print(f"Login:    {login.status_code}")

    if login.ok:
        token   = data.get("data", {}).get("accessToken", "")
        user_id = data.get("data", {}).get("user", {}).get("_id", "")
        print(f"Token:    {token[:40]}...")
        print(f"User ID:  {user_id}")
        return token, user_id
    else:
        print(f"Login failed: {data}")
        return None, None


user_token,     user_id     = register_and_login("Kora User",     "korauser001@gmail.com",     "123456", "user")
employee_token, employee_id = register_and_login("Kora Employee", "koraemployee001@gmail.com", "123456", "employee")

print("\n\n=== COPY THIS INTO YOUR .env ===")
print(f"USER_TOKEN={user_token}")
print(f"EMPLOYEE_TOKEN={employee_token}")
print(f"USER_ID={user_id}")
print(f"EMPLOYEE_ID={employee_id}")
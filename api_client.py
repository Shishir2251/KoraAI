# import os
# import time
# import requests
# from dotenv import load_dotenv

# load_dotenv()

# BASE_URL       = os.getenv("BASE_URL", "http://localhost:5000")
# USER_TOKEN     = os.getenv("USER_TOKEN", "")
# EMPLOYEE_TOKEN = os.getenv("EMPLOYEE_TOKEN", "")

# # Which token is active for this session
# # Switch by calling set_role("user") or set_role("employee")
# _active_role = "user"

# def set_role(role: str):
#     """Switch the active token between 'user' and 'employee'."""
#     global _active_role
#     _active_role = role
#     print(f"[TOKEN] Switched to role: {role}")


# def get_headers():
#     token = EMPLOYEE_TOKEN if _active_role == "employee" else USER_TOKEN
#     return {
#         "Authorization": f"Bearer {token}",
#         "Content-Type":  "application/json",
#     }


# def _handle_response(res, path):
#     try:
#         data = res.json()
#     except Exception:
#         data = {"raw": res.text}

#     if not res.ok:
#         print(f"\n[API ERROR] {res.request.method} {path}")
#         print(f"  Status : {res.status_code}")
#         print(f"  Body   : {data}\n")
#         return {"error": f"HTTP {res.status_code} — {data}"}

#     return data


# def _request_with_retry(method, path, params=None, body=None, timeout=30, retries=2):
#     """Make an HTTP request with automatic retry on timeout."""
#     url = f"{BASE_URL}{path}"
#     for attempt in range(retries + 1):
#         try:
#             if method == "GET":
#                 res = requests.get(url, headers=get_headers(), params=params, timeout=timeout)
#             elif method == "POST":
#                 res = requests.post(url, headers=get_headers(), json=body, timeout=timeout)
#             elif method == "PUT":
#                 res = requests.put(url, headers=get_headers(), json=body, timeout=timeout)
#             elif method == "PATCH":
#                 res = requests.patch(url, headers=get_headers(), json=body, timeout=timeout)
#             elif method == "DELETE":
#                 res = requests.delete(url, headers=get_headers(), timeout=timeout)
#             else:
#                 return {"error": f"Unknown method {method}"}
#             return _handle_response(res, path)

#         except requests.exceptions.Timeout:
#             if attempt < retries:
#                 print(f"\n[TIMEOUT] {method} {path} — retrying ({attempt + 1}/{retries})...")
#                 time.sleep(3)
#             else:
#                 print(f"\n[TIMEOUT] {method} {path} — all retries exhausted")
#                 return {"error": f"Request timed out after {retries + 1} attempts. Backend may be slow — try again."}

#         except requests.exceptions.RequestException as e:
#             print(f"\n[API EXCEPTION] {method} {path} — {e}\n")
#             return {"error": str(e)}


# def api_get(path: str, params: dict = None) -> dict:
#     return _request_with_retry("GET", path, params=params)


# def api_post(path: str, body: dict) -> dict:
#     return _request_with_retry("POST", path, body=body)


# def api_put(path: str, body: dict) -> dict:
#     return _request_with_retry("PUT", path, body=body)


# def api_patch(path: str, body: dict) -> dict:
#     return _request_with_retry("PATCH", path, body=body)


# def api_delete(path: str) -> dict:
#     return _request_with_retry("DELETE", path)



import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")

# No more hardcoded USER_TOKEN or EMPLOYEE_TOKEN
# Token is now passed per request


def get_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
    }


def _handle_response(res, path):
    try:
        data = res.json()
    except Exception:
        data = {"raw": res.text}

    if not res.ok:
        print(f"\n[API ERROR] {res.request.method} {path}")
        print(f"  Status : {res.status_code}")
        print(f"  Body   : {data}\n")
        return {"error": f"HTTP {res.status_code} — {data}"}

    return data


def _request_with_retry(method, path, token, params=None, body=None, timeout=30, retries=2):
    url = f"{BASE_URL}{path}"
    for attempt in range(retries + 1):
        try:
            headers = get_headers(token)
            if method == "GET":
                res = requests.get(url, headers=headers, params=params, timeout=timeout)
            elif method == "POST":
                res = requests.post(url, headers=headers, json=body, timeout=timeout)
            elif method == "PUT":
                res = requests.put(url, headers=headers, json=body, timeout=timeout)
            elif method == "PATCH":
                res = requests.patch(url, headers=headers, json=body, timeout=timeout)
            elif method == "DELETE":
                res = requests.delete(url, headers=headers, timeout=timeout)
            else:
                return {"error": f"Unknown method {method}"}
            return _handle_response(res, path)

        except requests.exceptions.Timeout:
            if attempt < retries:
                print(f"\n[TIMEOUT] {method} {path} — retrying ({attempt+1}/{retries})...")
                time.sleep(3)
            else:
                return {"error": "Request timed out. Backend may be slow — try again."}
        except requests.exceptions.RequestException as e:
            print(f"\n[API EXCEPTION] {method} {path} — {e}\n")
            return {"error": str(e)}


def api_get(path: str, token: str, params: dict = None) -> dict:
    return _request_with_retry("GET", path, token, params=params)


def api_post(path: str, token: str, body: dict) -> dict:
    return _request_with_retry("POST", path, token, body=body)


def api_put(path: str, token: str, body: dict) -> dict:
    return _request_with_retry("PUT", path, token, body=body)


def api_patch(path: str, token: str, body: dict) -> dict:
    return _request_with_retry("PATCH", path, token, body=body)


def api_delete(path: str, token: str) -> dict:
    return _request_with_retry("DELETE", path, token)
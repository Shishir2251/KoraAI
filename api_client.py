import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL     = os.getenv("BASE_URL", "http://localhost:5000")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", "")


def get_headers():
    return {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type":  "application/json",
    }


def _handle_response(res, path):
    """Parse response and print debug info on failure."""
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


def api_get(path: str, params: dict = None) -> dict:
    try:
        res = requests.get(
            f"{BASE_URL}{path}",
            headers=get_headers(),
            params=params,
            timeout=10,
        )
        return _handle_response(res, path)
    except requests.exceptions.RequestException as e:
        print(f"\n[API EXCEPTION] GET {path} — {e}\n")
        return {"error": str(e)}


def api_post(path: str, body: dict) -> dict:
    try:
        res = requests.post(
            f"{BASE_URL}{path}",
            headers=get_headers(),
            json=body,
            timeout=10,
        )
        return _handle_response(res, path)
    except requests.exceptions.RequestException as e:
        print(f"\n[API EXCEPTION] POST {path} — {e}\n")
        return {"error": str(e)}


def api_put(path: str, body: dict) -> dict:
    try:
        res = requests.put(
            f"{BASE_URL}{path}",
            headers=get_headers(),
            json=body,
            timeout=10,
        )
        return _handle_response(res, path)
    except requests.exceptions.RequestException as e:
        print(f"\n[API EXCEPTION] PUT {path} — {e}\n")
        return {"error": str(e)}


def api_patch(path: str, body: dict) -> dict:
    try:
        res = requests.patch(
            f"{BASE_URL}{path}",
            headers=get_headers(),
            json=body,
            timeout=10,
        )
        return _handle_response(res, path)
    except requests.exceptions.RequestException as e:
        print(f"\n[API EXCEPTION] PATCH {path} — {e}\n")
        return {"error": str(e)}


def api_delete(path: str) -> dict:
    try:
        res = requests.delete(
            f"{BASE_URL}{path}",
            headers=get_headers(),
            timeout=10,
        )
        return _handle_response(res, path)
    except requests.exceptions.RequestException as e:
        print(f"\n[API EXCEPTION] DELETE {path} — {e}\n")
        return {"error": str(e)}
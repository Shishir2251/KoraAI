"""
Backend API Client
──────────────────
All calls to your existing backend go through this client.
Every request automatically includes the org_id and API secret.

This is the bridge between the AI agent and your real data.
"""

import httpx
from app.core.config import settings
from typing import Any, Optional
import uuid


class BackendAPIError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Backend API error {status_code}: {detail}")


class BackendClient:
    """
    HTTP client for your backend scheduler/appointment API.
    org_id is always injected — the LLM never sets it.
    """

    def __init__(self, org_id: uuid.UUID):
        self.org_id = org_id
        self.base_url = settings.BACKEND_API_URL.rstrip("/")
        self._headers = {
            "X-API-Secret": settings.BACKEND_API_SECRET,
            "X-Org-ID": str(org_id),       # Always from session, never from LLM
            "Content-Type": "application/json",
        }

    async def get(self, path: str, params: Optional[dict] = None) -> Any:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{self.base_url}{path}",
                headers=self._headers,
                params=params or {},
            )
            return self._handle(response)

    async def post(self, path: str, body: dict) -> Any:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{self.base_url}{path}",
                headers=self._headers,
                json=body,
            )
            return self._handle(response)

    async def patch(self, path: str, body: dict) -> Any:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.patch(
                f"{self.base_url}{path}",
                headers=self._headers,
                json=body,
            )
            return self._handle(response)

    def _handle(self, response: httpx.Response) -> Any:
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            raise BackendAPIError(response.status_code, detail)
        return response.json()
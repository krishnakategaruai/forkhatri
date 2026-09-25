"""Thin HTTP client for the Vyapar public REST API.

The MCP server talks to Vyapar ONLY through this client: HTTP plus a personal
access token. It never touches the database and never imports vyapar-service
code, so it can run on any machine that can reach the API.
"""
from __future__ import annotations

import os
import uuid
from typing import Any

import httpx


class VyaparError(Exception):
    """An API error, carrying Vyapar's stable error code and localized message."""

    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(f"{status} {code}: {message}")
        self.status = status
        self.code = code
        self.message = message


class VyaparClient:
    def __init__(self, base_url: str | None = None, token: str | None = None, language: str | None = None,
                 timeout: float = 20.0) -> None:
        self.base_url = (base_url or os.environ.get("VYAPAR_API_URL") or "http://localhost:8011").rstrip("/")
        self.token = token or os.environ.get("VYAPAR_TOKEN") or ""
        self.language = language or os.environ.get("VYAPAR_LANGUAGE") or "en"
        self._http = httpx.AsyncClient(base_url=self.base_url, timeout=timeout)

    def _headers(self, idempotency_key: str | None = None) -> dict[str, str]:
        if not self.token:
            raise VyaparError(401, "token_missing", "Set VYAPAR_TOKEN to a personal access token created in Vyapar.")
        headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Vyapar-Language": self.language,
            "Accept": "application/json",
            "User-Agent": "vyapar-mcp/0.1",
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    async def request(self, method: str, path: str, *, params: dict[str, Any] | None = None,
                      json: Any = None, idempotent: bool = False, idempotency_key: str | None = None) -> Any:
        key = idempotency_key or (str(uuid.uuid4()) if idempotent else None)
        clean = {k: v for k, v in (params or {}).items() if v is not None and v != ""}
        response = await self._http.request(method, path, params=clean, json=json, headers=self._headers(key))
        if response.status_code >= 400:
            try:
                body = response.json()
            except ValueError:
                body = {}
            err = body.get("error") if isinstance(body, dict) else None
            code = (err or {}).get("code") or response.headers.get("X-Vyapar-Error-Code") or f"http_{response.status_code}"
            message = (err or {}).get("message") or (body.get("detail") if isinstance(body, dict) and isinstance(body.get("detail"), str) else "") or response.reason_phrase
            raise VyaparError(response.status_code, code, message)
        if not response.content:
            return {"ok": True}
        return response.json()

    async def get(self, path: str, **params: Any) -> Any:
        return await self.request("GET", path, params=params)

    async def post(self, path: str, body: Any = None, *, idempotency_key: str | None = None) -> Any:
        return await self.request("POST", path, json=body, idempotent=True, idempotency_key=idempotency_key)

    async def patch(self, path: str, body: Any) -> Any:
        return await self.request("PATCH", path, json=body)

    async def delete(self, path: str) -> Any:
        return await self.request("DELETE", path)

    async def aclose(self) -> None:
        await self._http.aclose()

# [IMP37] Errors raised by the integration edges. Built on workstream A's
# ApiError (app/errors.py), so they carry the shared envelope
# {"detail": "<translated>", "error": {"code", "message", "details"}}.
# The code is derived from the translation key
# (`integrations.error.tokenInvalid` -> `token_invalid`), and also rides in
# the `X-Vyapar-Error-Code` header for clients that only read headers.
from __future__ import annotations

from fastapi import Request

from app.errors import ApiError
from app.i18n import resolve_language


class IntegrationError(ApiError):
    pass


def request_language(request: Request | None) -> str:
    if request is None:
        return "en"
    return resolve_language(request.headers.get("X-Vyapar-Language") or request.headers.get("Accept-Language"))


def fail(status_code: int, code: str, lang: str, headers: dict[str, str] | None = None, **params: object) -> IntegrationError:
    """Builds (does not raise) the error for `integrations.error.<camelCode>`."""
    parts = code.split("_")
    key = "integrations.error." + parts[0] + "".join(p.capitalize() for p in parts[1:])
    return IntegrationError(status_code, key, lang, headers={"X-Vyapar-Error-Code": code, **(headers or {})}, **params)

# [IMP-ADMIN, 2026-09-29] Service-to-service authentication for Vyapar's
# /internal/v1 bridges (today: the MOD05 dashboard summary).
#
# Same scheme the other ForKhatri modules use for their internal routes
# (Milavn/Mangaly `/internal/v1/insights/members`): the caller presents the
# shared service key in `X-ForKhatri-Service-Key` — the very key Vyapar
# presents to the platform (IDENTITY_SERVICE_KEY) — and a request that came
# through the public edge (a reverse proxy always adds X-Forwarded-For) is
# answered as if the route did not exist. Fails closed: while the key is
# still the bare "CHANGE_ME" placeholder, or empty, nobody gets in.
# A host other than ForKhatri can replace this dependency with its own.
from __future__ import annotations

import hmac

from fastapi import Header, HTTPException, Request

from app.config import get_settings
from app.integrations.errors import fail, request_language

SERVICE_KEY_HEADER = "X-ForKhatri-Service-Key"
_UNSET = {"", "CHANGE_ME"}


def require_platform_service(
    request: Request,
    x_forkhatri_service_key: str | None = Header(default=None, alias=SERVICE_KEY_HEADER),
) -> None:
    if request.headers.get("x-forwarded-for") is not None:
        raise HTTPException(status_code=404)
    expected = get_settings().identity_service_key or ""
    presented = x_forkhatri_service_key or ""
    if expected in _UNSET or not hmac.compare_digest(expected.encode("utf-8"), presented.encode("utf-8")):
        raise fail(401, "service_unauthorized", request_language(request))

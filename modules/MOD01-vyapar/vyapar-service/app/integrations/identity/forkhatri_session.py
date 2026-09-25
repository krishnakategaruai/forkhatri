# [TR050] ForKhatri host adapter — the platform session resolve path, moved
# here from app/identity.py by IMP37 with its behaviour unchanged. This is the
# ONLY place in the service that knows the ForKhatri `fk_session` cookie and
# the Identity & Trust `/internal/v1/sessions/resolve` contract.
# Behaviour kept exactly:
#   * no fk_session cookie -> not this provider's credential (the chain then
#     answers 401, as before);
#   * resolve against IDENTITY_SERVICE_INTERNAL_URL with X-Service-Key and a
#     2-second timeout; fail CLOSED (503) on any network failure/timeout —
#     never a default-member fallback (TR050's structural-absence rule);
#   * non-200 -> 401 and a short negative cache; 200 -> positive cache;
#   * <=30s positive / <=5s negative in-process cache (config);
#   * the member-link row is upserted through ensure_member() on success.
# A different host writes its own provider with the same shape (see
# INTEGRATION-GUIDE.md) and lists it in IDENTITY_PROVIDERS.
# Traces to: FR50, TR050, SP050 (IdentityBridge-CC)
from __future__ import annotations

import asyncio
import json
import time
import urllib.error
import urllib.request

from fastapi import Request

from app.config import get_settings
from app.integrations.errors import fail, request_language
from app.integrations.identity.base import AUTH_MEMBER_SESSION, ResolvedIdentity, ensure_member_row

# [TR050] cookie -> (cached_at, member_id | None)
_resolve_cache: dict[str, tuple[float, str | None]] = {}


class ForKhatriSessionProvider:
    name = "forkhatri"

    async def resolve(self, request: Request) -> ResolvedIdentity | None:
        settings = get_settings()
        cookie = request.cookies.get("fk_session")
        if not cookie:
            return None
        lang = request_language(request)

        now = time.time()
        cached = _resolve_cache.get(cookie)
        if cached is not None:
            cached_at, cached_member_id = cached
            window = (
                settings.identity_resolve_cache_seconds
                if cached_member_id
                else settings.identity_resolve_negative_cache_seconds
            )
            if now - cached_at < window:
                if cached_member_id is None:
                    raise fail(401, "session_invalid", lang)
                return ResolvedIdentity(member_id=cached_member_id, auth_method=AUTH_MEMBER_SESSION)

        def _do_request() -> tuple[int, dict]:
            # Stdlib-only (urllib): no extra HTTP-client dependency for a path
            # that is inert until a real IDENTITY_SERVICE_INTERNAL_URL is set.
            req = urllib.request.Request(
                f"{settings.identity_service_internal_url}/internal/v1/sessions/resolve",
                data=json.dumps({"session_cookie": cookie}).encode(),
                headers={"X-Service-Key": settings.identity_service_key, "Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                return resp.status, json.loads(resp.read())

        try:
            status, body = await asyncio.wait_for(asyncio.to_thread(_do_request), timeout=2.0)
        except urllib.error.HTTPError as e:
            # The identity service ANSWERED with a non-2xx (for example a
            # rejected or expired session). urllib raises HTTPError for that,
            # and it is a URLError subclass, so it used to fall into the
            # "unavailable" branch and return 503 for what is really a 401.
            # Fixed after IMP37 flagged it; it still fails closed.
            if e.code >= 500:
                raise fail(503, "identity_unavailable", lang)
            status, body = e.code, {}
        except (urllib.error.URLError, asyncio.TimeoutError, TimeoutError, ValueError):
            # [TR050] Fail CLOSED — never a default/local member fallback.
            raise fail(503, "identity_unavailable", lang)

        if status != 200:
            _resolve_cache[cookie] = (now, None)
            raise fail(401, "session_invalid", lang)

        member_id = body["member_id"]
        _resolve_cache[cookie] = (now, member_id)
        await ensure_member_row(
            member_id, body.get("display_name", member_id), body.get("phone"), body.get("language", "en")
        )
        return ResolvedIdentity(member_id=member_id, auth_method=AUTH_MEMBER_SESSION)

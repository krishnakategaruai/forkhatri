# [TR050] ForKhatri host adapter — the platform session resolve path, moved
# here from app/identity.py by IMP37 with its behaviour unchanged. This is the
# ONLY place in the service that knows the ForKhatri `fk_session` cookie and
# the Identity & Trust `/internal/v1/sessions/resolve` contract.
# Behaviour kept exactly:
#   * no fk_session cookie -> not this provider's credential (the chain then
#     answers 401, as before);
#   * resolve against IDENTITY_SERVICE_INTERNAL_URL with a 2-second timeout;
#     fail CLOSED (503) on any network failure/timeout —
#     never a default-member fallback (TR050's structural-absence rule);
#   * non-200 -> 401 and a short negative cache; 200 -> positive cache;
#   * <=30s positive / <=5s negative in-process cache (config);
#   * the member-link row is upserted through ensure_member() on success.
# A different host writes its own provider with the same shape (see
# INTEGRATION-GUIDE.md) and lists it in IDENTITY_PROVIDERS.
#
# [IMP-ADMIN, 2026-09-29] Contract corrected against the identity service's
# own handler (platform/identity-service/app/api/routes/internal.py):
#   request  headers X-ForKhatri-Service: <IDENTITY_SERVICE_NAME> and
#            X-ForKhatri-Service-Key: <IDENTITY_SERVICE_KEY>,
#            body {"session_token": "<fk_session value>"}
#            (it used to send X-Service-Key and {"session_cookie": ...}, which
#            the identity service rejects as service_unauthorized / 422);
#   response member_id, display_name, preferred_language, identity_level,
#            status, session_expires_at, admin_scopes — plus phone_e164/email
#            only for services allowed to receive identifiers.
# A rejected SERVICE credential is a configuration fault, not a bad session:
# it answers 503 (fail closed) and is logged, and is never negative-cached.
# Traces to: FR50, TR050, SP050 (IdentityBridge-CC)
from __future__ import annotations

import asyncio
import json
import logging
import time
import urllib.error
import urllib.request

from fastapi import Request

from app.config import get_settings
from app.integrations.errors import fail, request_language
from app.integrations.identity.admin_scopes import permissions_for_scopes
from app.integrations.identity.base import AUTH_MEMBER_SESSION, ResolvedIdentity, ensure_member_row

# [IMP-ADMIN — ADR-012] The resolve response also carries
# `"admin_scopes": ["vyapar.moderate", "vyapar.verify", ...]`. They are mapped
# here (admin_scopes.py) onto Vyapar's operator permissions and ride on the
# ResolvedIdentity. This response is the ONLY place session scopes are ever
# read from in production — never a request header, cookie or body. They are
# cached with the member id for the same <=30 s window, so a revoked scope
# stops working within that window.

logger = logging.getLogger(__name__)

# [TR050] cookie -> (cached_at, member_id | None, operator permissions)
_resolve_cache: dict[str, tuple[float, str | None, frozenset[str]]] = {}


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
            cached_at, cached_member_id, cached_permissions = cached
            window = (
                settings.identity_resolve_cache_seconds
                if cached_member_id
                else settings.identity_resolve_negative_cache_seconds
            )
            if now - cached_at < window:
                if cached_member_id is None:
                    raise fail(401, "session_invalid", lang)
                return ResolvedIdentity(
                    member_id=cached_member_id, auth_method=AUTH_MEMBER_SESSION, operator_permissions=cached_permissions
                )

        def _do_request() -> tuple[int, dict]:
            # Stdlib-only (urllib): no extra HTTP-client dependency for a path
            # that is inert until a real IDENTITY_SERVICE_INTERNAL_URL is set.
            req = urllib.request.Request(
                f"{settings.identity_service_internal_url}/internal/v1/sessions/resolve",
                data=json.dumps({"session_token": cookie}).encode(),
                headers={
                    "X-ForKhatri-Service": settings.identity_service_name,
                    "X-ForKhatri-Service-Key": settings.identity_service_key,
                    "Content-Type": "application/json",
                },
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
            try:
                error_text = e.read().decode("utf-8", "replace")
            except Exception:
                error_text = ""
            if "service_unauthorized" in error_text or e.code == 422:
                logger.error("identity service refused Vyapar's service credentials or request (%s): %s", e.code, error_text[:300])
                raise fail(503, "identity_unavailable", lang)
            status, body = e.code, {}
        except (urllib.error.URLError, asyncio.TimeoutError, TimeoutError, ValueError):
            # [TR050] Fail CLOSED — never a default/local member fallback.
            raise fail(503, "identity_unavailable", lang)

        if status != 200:
            _resolve_cache[cookie] = (now, None, frozenset())
            raise fail(401, "session_invalid", lang)

        member_id = body["member_id"]
        raw_scopes = body.get("admin_scopes")
        permissions = permissions_for_scopes(raw_scopes if isinstance(raw_scopes, list) else None)
        _resolve_cache[cookie] = (now, member_id, permissions)
        await ensure_member_row(
            member_id,
            body.get("display_name") or member_id,
            body.get("phone_e164") or body.get("phone"),
            body.get("preferred_language") or body.get("language") or "en",
        )
        return ResolvedIdentity(member_id=member_id, auth_method=AUTH_MEMBER_SESSION, operator_permissions=permissions)

# [TR050] Identity Bridge: platform session resolve, fail-closed, member-link
# (FR50). Vyapar never signs a member up, logs them in, or issues a session —
# authentication is 100% owned by the parent ForKhatri platform. This module
# only resolves "who is calling" from whatever the platform already
# authenticated, then upserts the thin member-link row every other schema's
# owner_id/member_id column points at.
# Approach: two code paths behind one function, selected by DEV_MODE — (1)
# dev stub: trust the X-Dev-Member-Id header (clearly dev-only; a future
# integrator replaces this branch with the real fk_session-cookie read), (2)
# real path: resolve against IDENTITY_SERVICE_INTERNAL_URL and fail CLOSED
# (503) on any non-2xx/timeout — never a default-member fallback, per
# TR050's structural-absence requirement. Both paths converge on the same
# ensure_member() SECURITY DEFINER upsert (idempotent, closes IA050's
# duplicate-row risk) before returning, so downstream code never has to
# special-case which path resolved the caller.
# Traces to: FR50, TR050, SP050 (IdentityBridge-CC)
from __future__ import annotations

import asyncio
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

from fastapi import Header, HTTPException, Request

from app.config import get_settings

# [TR050] ≤30s positive / ≤5s negative in-process cache for the real resolve
# path — avoids hammering Identity & Trust on every request without risking
# a stale-forever session.
_resolve_cache: dict[str, tuple[float, str | None]] = {}


@dataclass(frozen=True)
class AuthzContext:
    member_id: str
    is_operator: bool = False


async def _ensure_member_row(member_id: str, display_name: str, phone: str | None, language: str) -> None:
    """[TR050/IA050] Runs BEFORE vyapar.authz_context is meaningful for a
    brand-new member — calls the SECURITY DEFINER pre-authorization escape
    hatch documented in 07a-db-implementation/README.md, never a plain
    INSERT from this service (which would be blocked by RLS for a new row
    with no context set yet)."""
    from app.db import get_pool

    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "SELECT vyapar_identity.ensure_member($1, $2, $3, $4)",
            member_id,
            display_name,
            phone,
            language,
        )


async def _resolve_dev_stub(request: Request, x_dev_member_id: str | None) -> str:
    """[Dev-only stand-in for the platform's real fk_session cookie/session.
    NOT authentication — selects which already-seeded member the request
    acts as, for local development and manual QA only. A future integrator
    replaces this whole branch with a real fk_session cookie read + the
    resolve() call in _resolve_real below.]"""
    settings = get_settings()
    member_id = x_dev_member_id or request.cookies.get("vyapar_dev_member_id") or settings.dev_default_member_id
    await _ensure_member_row(member_id, member_id, None, "en")
    return member_id


async def _resolve_real(request: Request) -> str:
    """[TR050] Real platform resolve path — reads fk_session cookie, calls
    POST /internal/v1/sessions/resolve, fails closed on any failure."""
    settings = get_settings()
    cookie = request.cookies.get("fk_session")
    if not cookie:
        raise HTTPException(status_code=401, detail="No ForKhatri session — redirect to entrance")

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
                raise HTTPException(status_code=401, detail="Session invalid (cached negative)")
            return cached_member_id

    def _do_request() -> tuple[int, dict]:
        # Stdlib-only (urllib), not a third-party HTTP client — this path is
        # inert until a real IDENTITY_SERVICE_INTERNAL_URL replaces the
        # CHANGE_ME placeholder, and avoids adding a new pip dependency
        # (e.g. httpx) that would otherwise need its own Step 8 supplementary
        # security pass for a code path nothing in dev exercises.
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
    except (urllib.error.URLError, asyncio.TimeoutError, TimeoutError, ValueError):
        # [TR050] Fail CLOSED — never a default/local member fallback.
        raise HTTPException(status_code=503, detail="Identity & Trust unavailable")

    if status != 200:
        _resolve_cache[cookie] = (now, None)
        raise HTTPException(status_code=401, detail="Session invalid")

    member_id = body["member_id"]
    _resolve_cache[cookie] = (now, member_id)
    await _ensure_member_row(
        member_id, body.get("display_name", member_id), body.get("phone"), body.get("language", "en")
    )
    return member_id


async def resolve_authz_context(
    request: Request,
    x_dev_member_id: str | None = Header(default=None, alias="X-Dev-Member-Id"),
) -> AuthzContext:
    settings = get_settings()
    if settings.dev_mode:
        member_id = await _resolve_dev_stub(request, x_dev_member_id)
    else:
        member_id = await _resolve_real(request)

    from app.db import get_pool

    pool = get_pool()
    async with pool.acquire() as conn:
        # set_config(..., true) is transaction-scoped (SET LOCAL-equivalent)
        # — it must be set AND read inside the same transaction, or asyncpg's
        # implicit per-statement auto-transaction resets it before the next
        # bare statement runs. Wrapping both in one conn.transaction() here
        # is what actually makes the RLS-scoped read below see this row.
        async with conn.transaction():
            await conn.execute("SELECT set_config('vyapar.authz_context', $1, true)", member_id)
            row = await conn.fetchrow(
                "SELECT is_operator FROM vyapar_identity.members WHERE id = $1", member_id
            )
    return AuthzContext(member_id=member_id, is_operator=bool(row["is_operator"]) if row else False)

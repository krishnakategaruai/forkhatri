"""Identity Bridge — thin, schema-less (architecture.md §2.1).

# [FR076-FR080, FR088, TR46, TR47, ADR-004; ParentApp 07-tech-reqs TR10-TR17]
# Authentication is owned by the ForKhatri platform's Identity & Trust
# Service. This module never stores credentials, sessions, OTPs or identity
# data — it holds a `member_id` reference and resolves who a request acts as
# through this bridge, and nowhere else (ParentApp TR15).
# Approach:
#   * `resolve_session(token)` sends the browser's `fk_session` cookie value to
#     `POST /internal/v1/sessions/resolve` (service-to-service, TR14). Results
#     are cached in-process keyed by SHA-256 of the token (never the token):
#     positive for 30 s (so a platform sign-out reaches Milavn within 30 s),
#     negative for 5 s. The platform being unreachable raises
#     `IdentityServiceUnavailable`; callers fail closed (503), never guess.
#   * `display_names_for(ids)` uses `POST /internal/v1/members/lookup` in
#     batches of 200 with a 60 s cache; an unknown id or an outage degrades to
#     "Community member" — names are presentation, not authorization.
#   * Module roles (the `milavn.moderate` scope) are Milavn-owned data and are
#     never read from the platform. Until Milavn has a role table they come
#     from `config/dev_identities.json`, keyed by `member_id` (the platform
#     imported the same ids, TR23). The same file supplies the seeded
#     development avatar/handle for those members.
#   * The legacy development stand-in (`X-Milavn-Member-Id` / `milavn_member`
#     resolved against that JSON) is available only when
#     `dev_identity_enabled` is explicitly true, for automated tests.
# Traces to: TR46, TR47, ParentApp TR14/TR15/TR23, architecture.md §1.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from functools import cache
from uuid import UUID

import httpx

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
# httpx logs every request at INFO; one line per session resolve would drown the service log.
logging.getLogger("httpx").setLevel(logging.WARNING)

FALLBACK_DISPLAY_NAME = "Community member"
MODERATE_SCOPE = "milavn.moderate"

SESSION_TTL_SECONDS = 30.0
NEGATIVE_SESSION_TTL_SECONDS = 5.0
LOOKUP_TTL_SECONDS = 60.0
LOOKUP_BATCH_MAX = 200
# After a failed lookup, skip the platform for this long so a page of cards
# does not pay one timeout per call while the service is down.
LOOKUP_OUTAGE_BACKOFF_SECONDS = 5.0
_CACHE_MAX_ENTRIES = 10_000


class IdentityServiceUnavailable(RuntimeError):
    """The platform Identity & Trust Service could not answer. Fail closed."""


@dataclass(frozen=True, slots=True)
class MemberIdentity:
    member_id: UUID
    display_name: str
    handle: str
    avatar: str | None
    identity_level: int
    scopes: tuple[str, ...]

    @property
    def is_moderator(self) -> bool:
        return MODERATE_SCOPE in self.scopes


# --- Milavn-owned role source ------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _ModuleMember:
    display_name: str
    handle: str
    avatar: str | None
    identity_level: int
    scopes: tuple[str, ...]


@cache
def _module_members() -> dict[UUID, _ModuleMember]:
    """Milavn's own per-member role/seed data, keyed by platform member_id.

    Always loaded (roles are needed in every environment); only the dev
    header path below is gated by `dev_identity_enabled`."""
    path = get_settings().dev_identities_path
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    return {
        UUID(m["member_id"]): _ModuleMember(
            display_name=m["display_name"],
            handle=m["handle"],
            avatar=m.get("avatar"),
            identity_level=int(m.get("identity_level", 0)),
            scopes=tuple(m.get("scopes", [])),
        )
        for m in data["members"]
    }


def scopes_for(member_id: UUID) -> tuple[str, ...]:
    m = _module_members().get(member_id)
    return m.scopes if m else ()


def _derive_handle(display_name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", ".", display_name.lower()).strip(".")
    return slug[:30] or "member"


def _compose(member_id: UUID, display_name: str, identity_level: int) -> MemberIdentity:
    local = _module_members().get(member_id)
    return MemberIdentity(
        member_id=member_id,
        display_name=display_name,
        handle=local.handle if local else _derive_handle(display_name),
        avatar=local.avatar if local else None,
        identity_level=identity_level,
        scopes=local.scopes if local else (),
    )


# --- Platform client ---------------------------------------------------------------

_client: httpx.AsyncClient | None = None
_client_loop: asyncio.AbstractEventLoop | None = None
# Tests inject an `httpx.MockTransport` here; production leaves it None.
_transport_factory: Callable[[], httpx.AsyncBaseTransport] | None = None


def _get_client() -> httpx.AsyncClient:
    global _client, _client_loop
    loop = asyncio.get_running_loop()
    if _client is None or _client.is_closed or _client_loop is not loop:
        settings = get_settings()
        _client = httpx.AsyncClient(
            base_url=settings.platform_identity_url.rstrip("/"),
            timeout=httpx.Timeout(2.0, connect=2.0),
            headers={
                "X-ForKhatri-Service": settings.platform_service_name,
                "X-ForKhatri-Service-Key": settings.platform_service_key,
            },
            transport=_transport_factory() if _transport_factory else None,
        )
        _client_loop = loop
    return _client


async def aclose() -> None:
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None


def reset_caches() -> None:
    """Drop every cached resolution (tests; never needed at runtime)."""
    global _lookup_down_until
    _sessions.clear()
    _names.clear()
    _lookup_down_until = 0.0
    _module_members.cache_clear()


def _prune(store: dict, now: float) -> None:
    if len(store) < _CACHE_MAX_ENTRIES:
        return
    for key in [k for k, (expires, _) in store.items() if expires <= now]:
        store.pop(key, None)
    if len(store) >= _CACHE_MAX_ENTRIES:
        store.clear()


# --- Session resolution (TR15) -------------------------------------------------------

_sessions: dict[str, tuple[float, MemberIdentity | None]] = {}


async def resolve_session(session_token: str) -> MemberIdentity | None:
    """`fk_session` value -> acting member, or None when the session is not valid.

    Raises `IdentityServiceUnavailable` when the platform cannot answer."""
    if not session_token:
        return None
    key = hashlib.sha256(session_token.encode("utf-8")).hexdigest()
    now = time.monotonic()
    hit = _sessions.get(key)
    if hit and hit[0] > now:
        return hit[1]
    try:
        res = await _get_client().post("/internal/v1/sessions/resolve", json={"session_token": session_token})
    except httpx.HTTPError as exc:
        logger.warning("identity service unreachable on session resolve: %s", type(exc).__name__)
        raise IdentityServiceUnavailable() from exc
    if res.status_code in (400, 401, 404, 422):
        _prune(_sessions, now)
        _sessions[key] = (now + NEGATIVE_SESSION_TTL_SECONDS, None)
        return None
    if res.status_code != 200:
        # 403 = this service's key was refused; 5xx = platform fault. Neither
        # is "signed out", so neither may be cached as such.
        logger.error("identity service answered %s on session resolve", res.status_code)
        raise IdentityServiceUnavailable()
    claims = res.json()
    if claims.get("status", "active") != "active":
        _sessions[key] = (now + NEGATIVE_SESSION_TTL_SECONDS, None)
        return None
    member_id = UUID(claims["member_id"])
    ident = _compose(member_id, claims.get("display_name") or FALLBACK_DISPLAY_NAME, int(claims.get("identity_level") or 0))
    ttl = SESSION_TTL_SECONDS
    expires_at = claims.get("session_expires_at")
    if expires_at:
        try:
            remaining = datetime.fromisoformat(expires_at).timestamp() - time.time()
            ttl = max(0.0, min(ttl, remaining))
        except ValueError:
            pass
    _prune(_sessions, now)
    _sessions[key] = (now + ttl, ident)
    _names[member_id] = (now + LOOKUP_TTL_SECONDS, ident)
    return ident


# --- Display lookups -----------------------------------------------------------------

_names: dict[UUID, tuple[float, MemberIdentity]] = {}
_lookup_down_until = 0.0


def _fallback(member_id: UUID) -> MemberIdentity:
    return _compose(member_id, FALLBACK_DISPLAY_NAME, 0)


async def _fetch_names(ids: list[UUID]) -> dict[UUID, MemberIdentity] | None:
    """One batch from the platform; None when it cannot answer."""
    global _lookup_down_until
    try:
        res = await _get_client().post("/internal/v1/members/lookup", json={"member_ids": [str(i) for i in ids]})
        res.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("identity lookup failed (%s); showing fallback names", type(exc).__name__)
        _lookup_down_until = time.monotonic() + LOOKUP_OUTAGE_BACKOFF_SECONDS
        return None
    return {UUID(r["member_id"]): _compose(UUID(r["member_id"]), r.get("display_name") or FALLBACK_DISPLAY_NAME, int(r.get("identity_level") or 0)) for r in res.json()}


async def display_names_for(member_ids: list[UUID]) -> dict[UUID, MemberIdentity]:
    """Presentation facts for other members (host names, attendees, chat).

    Never raises for an outage: unknown or unresolvable ids read "Community member"."""
    now = time.monotonic()
    result: dict[UUID, MemberIdentity] = {}
    missing: list[UUID] = []
    for mid in dict.fromkeys(member_ids):
        hit = _names.get(mid)
        if hit and hit[0] > now:
            result[mid] = hit[1]
        else:
            missing.append(mid)
    if missing and _lookup_down_until <= now:
        for start in range(0, len(missing), LOOKUP_BATCH_MAX):
            batch = missing[start : start + LOOKUP_BATCH_MAX]
            fetched = await _fetch_names(batch)
            if fetched is None:
                break
            _prune(_names, now)
            for mid in batch:
                # Unknown ids are cached too, so a deleted member is not re-asked every call.
                ident = fetched.get(mid) or _fallback(mid)
                _names[mid] = (now + LOOKUP_TTL_SECONDS, ident)
                result[mid] = ident
    for mid in missing:
        result.setdefault(mid, _fallback(mid))
    return result


# --- Development stand-in (explicit opt-in only) ----------------------------------------


def resolve_dev(member_id: UUID) -> MemberIdentity | None:
    """Legacy `X-Milavn-Member-Id` path. None unless `dev_identity_enabled` is true."""
    if not get_settings().dev_identity_enabled:
        return None
    local = _module_members().get(member_id)
    if local is None:
        return None
    return MemberIdentity(member_id, local.display_name, local.handle, local.avatar, local.identity_level, local.scopes)


def list_dev_members() -> list[MemberIdentity]:
    if not get_settings().dev_identity_enabled:
        return []
    return [MemberIdentity(mid, m.display_name, m.handle, m.avatar, m.identity_level, m.scopes) for mid, m in _module_members().items()]

"""ForKhatri platform identity client — internal to Identity Bridge.

# [ForKhatri TR14/TR15] Resolve the browser's `fk_session` token to platform
# session claims, and nothing else.
# Approach: one shared `httpx.AsyncClient` (connection reuse; ~2 s timeouts so a
# slow identity service cannot pin request workers) calling
# `POST /internal/v1/sessions/resolve` with this service's name and key.
# Results are cached in-process per token for at most 30 s (positive) or 5 s
# (negative), exactly the bound TR15 sets — so a sign-out reaches Mangaly within
# 30 s while ordinary page loads (several parallel API calls) cost one
# round-trip. The cache key is the SHA-256 digest of the token: the raw bearer
# credential is never held as a dict key where a heap dump or debug print could
# surface it.
#
# Failure semantics are deliberately asymmetric:
#   * `401 session_invalid`      → `PlatformSessionInvalid` (cached 5 s)
#   * anything else — timeout, connection refused, 5xx, our own service key
#     rejected (`401 service_unauthorized`), malformed body
#                                → `PlatformIdentityUnavailable` (never cached)
# The second group must never look like "signed out": that would bounce the
# member to the entrance, which would find them signed in and send them straight
# back — and it must never look like "signed in as someone" either (TR15 step 3,
# fail closed).
#
# Not imported outside this component: callers use `interface.py`.
# Traces to: ForKhatri TR12, TR14, TR15, TR24.
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Final
from uuid import UUID

import httpx

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

POSITIVE_TTL_SECONDS: Final[float] = 30.0
NEGATIVE_TTL_SECONDS: Final[float] = 5.0
_MAX_CACHE_ENTRIES: Final[int] = 10_000
_MAX_TOKEN_LENGTH: Final[int] = 128  # identity service's own request limit


class PlatformSessionInvalid(Exception):
    """The identity service says this token is not a live session."""


class PlatformIdentityUnavailable(Exception):
    """The identity service could not give an answer. Fail closed with 503."""


@dataclass(frozen=True, slots=True)
class PlatformClaims:
    """The subset of TR14 `SessionClaims` Mangaly uses."""

    member_id: UUID
    status: str
    preferred_language: str | None
    phone_e164: str | None
    email: str | None
    # TR14 `session_expires_at` (ISO 8601). None only if the platform omits it.
    session_expires_at: datetime | None = None
    # The member's ForKhatri name, shown to the candidate whose circle they join.
    display_name: str | None = None


_cache: dict[str, tuple[float, PlatformClaims | None]] = {}
# Indirection so tests can move time without patching `time.monotonic` itself,
# which the asyncio event loop also reads.
_clock = time.monotonic
_client: httpx.AsyncClient | None = None


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def clear_cache() -> None:
    """Drop every cached resolution (tests; also safe to call operationally)."""
    _cache.clear()


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        settings = get_settings()
        _client = httpx.AsyncClient(
            base_url=settings.platform_identity_url,
            timeout=httpx.Timeout(settings.platform_identity_timeout_seconds),
            headers={
                "X-ForKhatri-Service": settings.platform_service_name,
                "X-ForKhatri-Service-Key": settings.platform_service_key,
            },
        )
    return _client


async def aclose_client() -> None:
    """Close the shared client (application shutdown)."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def _remember(key: str, claims: PlatformClaims | None) -> None:
    now = _clock()
    if len(_cache) >= _MAX_CACHE_ENTRIES:
        for stale in [k for k, (expires, _) in _cache.items() if expires <= now]:
            del _cache[stale]
        if len(_cache) >= _MAX_CACHE_ENTRIES:
            _cache.clear()
    ttl = POSITIVE_TTL_SECONDS if claims is not None else NEGATIVE_TTL_SECONDS
    _cache[key] = (now + ttl, claims)


def _parse_claims(body: object) -> PlatformClaims:
    if not isinstance(body, dict):
        raise ValueError("claims body is not an object")
    member_id = UUID(str(body["member_id"]))
    status = str(body.get("status") or "")
    if not status:
        raise ValueError("claims carry no status")

    def _optional(name: str) -> str | None:
        value = body.get(name)
        return str(value) if value else None

    raw_expiry = _optional("session_expires_at")
    return PlatformClaims(
        member_id=member_id,
        status=status,
        preferred_language=_optional("preferred_language"),
        phone_e164=_optional("phone_e164"),
        email=_optional("email"),
        display_name=_optional("display_name"),
        # An unparseable timestamp raises ValueError → treated as malformed.
        session_expires_at=datetime.fromisoformat(raw_expiry) if raw_expiry else None,
    )


async def resolve_token(token: str) -> PlatformClaims:
    """Resolve an `fk_session` token, using the bounded per-token cache.

    Raises `PlatformSessionInvalid` or `PlatformIdentityUnavailable`.
    """
    if not token or len(token) > _MAX_TOKEN_LENGTH:
        raise PlatformSessionInvalid

    key = token_digest(token)
    cached = _cache.get(key)
    if cached is not None:
        expires, claims = cached
        if expires > _clock():
            if claims is None:
                raise PlatformSessionInvalid
            return claims
        del _cache[key]

    try:
        response = await _get_client().post(
            "/internal/v1/sessions/resolve", json={"session_token": token}
        )
    except httpx.HTTPError as exc:
        logger.warning("ForKhatri identity service unreachable: %s", type(exc).__name__)
        raise PlatformIdentityUnavailable from exc

    if response.status_code == 401:
        code = _error_code(response)
        if code == "session_invalid":
            _remember(key, None)
            raise PlatformSessionInvalid
        # Our own service credentials were rejected: a deployment fault, not a
        # signed-out member. Loud log, fail closed, never cached.
        logger.error("ForKhatri identity service rejected Mangaly's service credentials (%s)", code)
        raise PlatformIdentityUnavailable

    if response.status_code != 200:
        logger.warning("ForKhatri identity service answered HTTP %s", response.status_code)
        raise PlatformIdentityUnavailable

    try:
        claims = _parse_claims(response.json())
    except (ValueError, KeyError, TypeError) as exc:
        logger.error("ForKhatri identity service returned malformed session claims")
        raise PlatformIdentityUnavailable from exc

    _remember(key, claims)
    return claims


def _error_code(response: httpx.Response) -> str | None:
    try:
        detail = response.json().get("detail")
    except ValueError:
        return None
    if isinstance(detail, dict):
        code = detail.get("code")
        return str(code) if code else None
    return None

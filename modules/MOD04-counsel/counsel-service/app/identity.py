"""Identity bridge. Authentication is owned by the ForKhatri platform's
Identity & Trust Service: the browser holds one HttpOnly `fk_session`
cookie; Counsel resolves it server-to-server with its own service key and
caches the answer briefly (30 s positive / 5 s negative, keyed by the
token's SHA-256). Counsel never stores credentials or sessions.

Admin access: the platform's `counsel.admin` governance scope, or a member
listed in ADMIN_MEMBER_IDS for local development."""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass
from uuid import UUID

import httpx
from fastapi import Depends, Request, WebSocket

from app import db
from app.errors import DomainError
from app.settings import get_settings

log = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

ADMIN_SCOPE = "counsel.admin"
POSITIVE_TTL = 30.0
NEGATIVE_TTL = 5.0
LOOKUP_TTL = 300.0


@dataclass(frozen=True)
class Actor:
    member_id: UUID
    display_name: str
    language: str
    is_admin: bool

    @property
    def id(self) -> str:
        return str(self.member_id)


class IdentityUnavailable(DomainError):
    def __init__(self):
        super().__init__("identity_unavailable", "ForKhatri sign-in service is unavailable. Try again.", 503)


_client: httpx.AsyncClient | None = None
_sessions: dict[str, tuple[float, Actor | None]] = {}
_names: dict[str, tuple[float, str]] = {}


def _http() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        s = get_settings()
        _client = httpx.AsyncClient(
            base_url=s.platform_identity_url.rstrip("/"),
            timeout=httpx.Timeout(3.0, connect=2.0),
            headers={"X-ForKhatri-Service": s.platform_service_name, "X-ForKhatri-Service-Key": s.platform_service_key},
        )
    return _client


async def aclose() -> None:
    if _client and not _client.is_closed:
        await _client.aclose()


async def resolve(token: str | None) -> Actor | None:
    if not token:
        return None
    key = hashlib.sha256(token.encode()).hexdigest()
    now = time.monotonic()
    hit = _sessions.get(key)
    if hit and hit[0] > now:
        return hit[1]
    try:
        res = await _http().post("/internal/v1/sessions/resolve", json={"session_token": token})
    except httpx.HTTPError as exc:
        log.warning("identity service unreachable: %s", type(exc).__name__)
        raise IdentityUnavailable() from exc
    if res.status_code in (400, 401, 404, 422):
        _sessions[key] = (now + NEGATIVE_TTL, None)
        return None
    if res.status_code != 200:
        log.error("identity resolve answered %s", res.status_code)
        raise IdentityUnavailable()
    c = res.json()
    scopes = set(c.get("admin_scopes") or [])
    member_id = UUID(c["member_id"])
    actor = Actor(
        member_id=member_id,
        display_name=c.get("display_name") or "ForKhatri member",
        language=c.get("preferred_language") or "en",
        is_admin=ADMIN_SCOPE in scopes or str(member_id) in get_settings().admin_ids,
    )
    if len(_sessions) > 5000:
        _sessions.clear()
    _sessions[key] = (now + POSITIVE_TTL, actor)
    # Keep Counsel's member cache fresh (display names for lists; never identifiers).
    # A member who deleted their Counsel data keeps the "Deleted member" name.
    if await db.fetchval("SELECT 1 FROM erased_member WHERE member_id=$1", member_id):
        await db.execute("DELETE FROM erased_member WHERE member_id=$1 AND erased_at < now() - interval '1 minute'", member_id)
    await db.execute(
        "INSERT INTO member (member_id, display_name, language) VALUES ($1,$2,$3) "
        "ON CONFLICT (member_id) DO UPDATE SET display_name = EXCLUDED.display_name, language = EXCLUDED.language, last_seen = now()",
        member_id, actor.display_name, actor.language,
    )
    return actor


def forget(member_id: UUID) -> None:
    """Drop everything cached about a member (sessions, names, room tickets) after their data is erased."""
    for k, (_, actor) in list(_sessions.items()):
        if actor is not None and actor.member_id == member_id:
            _sessions.pop(k, None)
    _names.pop(str(member_id), None)
    for k, (_, actor) in list(_tickets.items()):
        if actor.member_id == member_id:
            _tickets.pop(k, None)


async def display_names(ids: list[UUID | str]) -> dict[str, str]:
    """Names for a set of members: Counsel's cache first, the platform for the rest."""
    wanted = list({str(i) for i in ids})
    out: dict[str, str] = {}
    if not wanted:
        return out
    for r in await db.fetch("SELECT member_id, display_name FROM member WHERE member_id = ANY($1::uuid[])", wanted):
        out[str(r["member_id"])] = r["display_name"]
    missing = [i for i in wanted if i not in out]
    now = time.monotonic()
    for i in list(missing):
        hit = _names.get(i)
        if hit and hit[0] > now:
            out[i] = hit[1]
            missing.remove(i)
    if missing:
        try:
            res = await _http().post("/internal/v1/members/lookup", json={"member_ids": missing})
            if res.status_code == 200:
                for m in res.json():
                    name = m.get("display_name") or "ForKhatri member"
                    out[m["member_id"]] = name
                    _names[m["member_id"]] = (now + LOOKUP_TTL, name)
        except httpx.HTTPError:
            pass
    for i in wanted:
        out.setdefault(i, "ForKhatri member")
    return out


async def current_actor(request: Request) -> Actor:
    token = request.cookies.get(get_settings().platform_session_cookie)
    actor = await resolve(token)
    if actor is None:
        raise DomainError("unauthenticated", "Sign in to ForKhatri to continue.", 401)
    return actor


async def optional_actor(request: Request) -> Actor | None:
    token = request.cookies.get(get_settings().platform_session_cookie)
    try:
        return await resolve(token)
    except IdentityUnavailable:
        return None


# Short-lived tickets let the room WebSocket authenticate when the browser
# cannot send the session cookie cross-site (tunnelled development). A ticket
# is minted by an authenticated REST call and is single-use, 60 s.
_tickets: dict[str, tuple[float, Actor]] = {}


def mint_ticket(actor: Actor) -> str:
    import secrets

    now = time.monotonic()
    for k, (exp, _) in list(_tickets.items()):
        if exp < now:
            _tickets.pop(k, None)
    token = secrets.token_urlsafe(24)
    _tickets[token] = (now + 60.0, actor)
    return token


async def ws_actor(ws: WebSocket) -> Actor | None:
    ticket = ws.query_params.get("ticket")
    if ticket:
        hit = _tickets.pop(ticket, None)
        if hit and hit[0] > time.monotonic():
            return hit[1]
        return None
    return await resolve(ws.cookies.get(get_settings().platform_session_cookie))


async def admin_actor(actor: Actor = Depends(current_actor)) -> Actor:
    if not actor.is_admin:
        raise DomainError("forbidden", "Administrators only.", 403)
    return actor

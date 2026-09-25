# [IMP37 — Refactor B] HTTP middleware for the integration edges.
#
# IdempotencyMiddleware — `Idempotency-Key` on any POST.
#   An agent retrying after a timeout must not post the same opportunity or
#   enquiry twice. For a POST carrying the header, the first response is
#   stored for IDEMPOTENCY_TTL_HOURS and replayed byte-for-byte on a repeat
#   (with `Idempotent-Replayed: true`).
#   * Scoped per caller: the member AND the credential (each access token,
#     or the member's session), plus method and path — one caller's key can
#     never return another caller's response.
#   * The request body is fingerprinted (sha256). The same key with a
#     different body is refused (422 idempotency_key_reused), never replayed.
#   * A first request still running when the repeat arrives gets
#     409 idempotency_in_progress, instead of a second concurrent write.
#   * Only 2xx responses are kept. A 4xx/5xx releases the key so the caller
#     can correct the request and retry with the same key.
#   * Stored in the existing vyapar_platform.idempotency_key table (member-
#     scoped RLS), in its own "mw:" endpoint namespace, so it never collides
#     with the per-route handling some routes already do.
#
# TokenAuditMiddleware — every write made with an access token is recorded
#   through the existing audit writer (app/audit.py) with the token id,
#   method, route and outcome — including refused writes. Member-session
#   writes are unaffected (their routes already audit what FR49 requires).
from __future__ import annotations

import hashlib
import json
import logging

from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.config import get_settings
from app.integrations.errors import IntegrationError, fail, request_language

logger = logging.getLogger(__name__)

WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
MAX_KEY_LENGTH = 200
MAX_STORED_BODY = 1_000_000


def _header(scope: Scope, name: bytes) -> str | None:
    for k, v in scope.get("headers") or []:
        if k.lower() == name:
            return v.decode("latin-1")
    return None


async def _send_json(send: Send, status: int, payload: dict, extra: list[tuple[bytes, bytes]] | None = None) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())] + (extra or [])
    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": body})


async def _send_error(send: Send, err: IntegrationError) -> None:
    extra = [(k.lower().encode(), v.encode()) for k, v in (err.headers or {}).items()]
    await _send_json(send, err.status_code, {"detail": err.detail, "error": {"code": err.code, "message": err.detail, "details": {}}}, extra)


class IdempotencyMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope.get("method") != "POST":
            await self.app(scope, receive, send)
            return
        key = _header(scope, b"idempotency-key")
        if key is None:
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        lang = request_language(request)
        key = key.strip()
        if not key or len(key) > MAX_KEY_LENGTH or not key.isprintable():
            await _send_error(send, fail(400, "idempotency_key_invalid", lang))
            return

        # Buffer the body so it can be fingerprinted and then replayed to the app.
        chunks: list[bytes] = []
        more = True
        while more:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunks.append(message.get("body", b""))
            more = message.get("more_body", False)
        body = b"".join(chunks)
        replayed = False

        async def replay_receive() -> Message:
            nonlocal replayed
            if not replayed:
                replayed = True
                return {"type": "http.request", "body": body, "more_body": False}
            return await receive()

        # Who is calling. If no credential resolves, let the app answer
        # (it produces the proper 401); nothing is stored.
        from app.integrations.identity import authenticate

        try:
            identity = await authenticate(request)
        except Exception:
            await self.app(scope, replay_receive, send)
            return

        path = scope.get("path", "")
        query = scope.get("query_string", b"").decode("latin-1")
        endpoint = f"mw:{identity.credential_id or 'session'}:POST {path}"[:500]
        fingerprint = hashlib.sha256(b"POST " + path.encode() + b"?" + query.encode() + b"\n" + body).hexdigest()
        ttl_hours = get_settings().idempotency_ttl_hours

        from app.db import get_pool

        pool = get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("SELECT set_config('vyapar.authz_context', $1, true)", identity.member_id)
                await conn.execute(
                    """DELETE FROM vyapar_platform.idempotency_key
                        WHERE member_id = $1 AND idempotency_key = $2 AND endpoint = $3 AND expires_at < now()""",
                    identity.member_id, key, endpoint,
                )
                claimed = await conn.fetchval(
                    """INSERT INTO vyapar_platform.idempotency_key
                         (idempotency_key, endpoint, member_id, request_hash, expires_at)
                       VALUES ($1, $2, $3, $4, now() + make_interval(hours => $5))
                       ON CONFLICT (member_id, idempotency_key, endpoint) DO NOTHING RETURNING id""",
                    key, endpoint, identity.member_id, fingerprint, ttl_hours,
                )
                existing = None
                if claimed is None:
                    existing = await conn.fetchrow(
                        """SELECT request_hash, status_code, response_snapshot FROM vyapar_platform.idempotency_key
                            WHERE member_id = $1 AND idempotency_key = $2 AND endpoint = $3""",
                        identity.member_id, key, endpoint,
                    )

        if claimed is None:
            if existing is None:  # expired and purged between statements — just run
                await self.app(scope, replay_receive, send)
                return
            if existing["request_hash"] != fingerprint:
                await _send_error(send, fail(422, "idempotency_key_reused", lang))
                return
            if existing["status_code"] is None:
                await _send_error(send, fail(409, "idempotency_in_progress", lang, headers={"Retry-After": "2"}))
                return
            snap = existing["response_snapshot"]
            snap = json.loads(snap) if isinstance(snap, str) else snap
            stored = snap.get("body", "").encode("utf-8")
            headers = [
                (b"content-type", snap.get("content_type", "application/json").encode("latin-1")),
                (b"content-length", str(len(stored)).encode()),
                (b"idempotent-replayed", b"true"),
            ]
            await send({"type": "http.response.start", "status": existing["status_code"], "headers": headers})
            await send({"type": "http.response.body", "body": stored})
            return

        status_holder: dict = {}
        captured: list[bytes] = []

        async def capture_send(message: Message) -> None:
            if message["type"] == "http.response.start":
                status_holder["status"] = message["status"]
                for k, v in message.get("headers") or []:
                    if k.lower() == b"content-type":
                        status_holder["content_type"] = v.decode("latin-1")
            elif message["type"] == "http.response.body":
                captured.append(message.get("body", b""))
            await send(message)

        async def release() -> None:
            async with pool.acquire() as c:
                async with c.transaction():
                    await c.execute("SELECT set_config('vyapar.authz_context', $1, true)", identity.member_id)
                    await c.execute(
                        "DELETE FROM vyapar_platform.idempotency_key WHERE id = $1", claimed
                    )

        try:
            await self.app(scope, replay_receive, capture_send)
        except BaseException:
            await release()
            raise

        status = status_holder.get("status", 500)
        response_body = b"".join(captured)
        try:
            text = response_body.decode("utf-8")
        except UnicodeDecodeError:
            text = None
        if not (200 <= status < 300) or text is None or len(response_body) > MAX_STORED_BODY:
            await release()
            return
        async with pool.acquire() as c:
            async with c.transaction():
                await c.execute("SELECT set_config('vyapar.authz_context', $1, true)", identity.member_id)
                await c.execute(
                    """UPDATE vyapar_platform.idempotency_key SET status_code = $2, response_snapshot = $3::jsonb
                        WHERE id = $1""",
                    claimed, status,
                    json.dumps({"body": text, "content_type": status_holder.get("content_type", "application/json")}),
                )


class TokenAuditMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope.get("method") not in WRITE_METHODS:
            await self.app(scope, receive, send)
            return
        scope.setdefault("state", {})
        status_holder: dict = {}

        async def capture_send(message: Message) -> None:
            if message["type"] == "http.response.start":
                status_holder["status"] = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, capture_send)
        finally:
            ctx = (scope.get("state") or {}).get("vyapar_authz")
            if ctx is not None and getattr(ctx, "is_token", False):
                await self._record(scope, ctx, status_holder.get("status", 500))

    @staticmethod
    async def _record(scope: Scope, ctx, status: int) -> None:
        from app.audit import audit
        from app.db import get_pool

        route = scope.get("route")
        route_path = getattr(route, "path", None) or scope.get("path", "")
        try:
            async with get_pool().acquire() as conn:
                async with conn.transaction():
                    await conn.execute("SELECT set_config('vyapar.authz_context', $1, true)", ctx.member_id)
                    await audit(
                        conn,
                        actor_id=ctx.member_id,
                        action=f"api_token.{scope['method'].lower()}",
                        object_kind="api_request",
                        object_id=scope.get("path", "")[:300],
                        outcome="ok" if status < 400 else "rejected",
                        reason_code=None if status < 400 else f"http_{status}",
                        details={
                            "access_token_id": ctx.credential_id,
                            "method": scope["method"],
                            "route": route_path,
                            "status": status,
                            "scopes": sorted(ctx.scopes or []),
                        },
                    )
        except Exception:
            logger.exception("token write audit failed")


def install(app) -> None:
    """Called from main.py BEFORE CORSMiddleware is added, so CORS stays the
    outermost layer (replayed and refused responses still get CORS headers).
    Order inside: TokenAudit wraps Idempotency wraps the routes."""
    app.add_middleware(IdempotencyMiddleware)
    app.add_middleware(TokenAuditMiddleware)

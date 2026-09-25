# [IMP37 — Refactor B] Personal access tokens: `Authorization: Bearer vyp_...`.
# The token is hashed and looked up through the narrow SECURITY DEFINER
# function resolve_access_token() (migration 015), which returns a row only
# for an unrevoked, unexpired token of a live member. Any presented vyp_
# token that does not resolve is a 401 — it never falls through to another
# provider. A Bearer credential of some other shape is left for a later
# provider (for example a host's own JWT adapter).
from __future__ import annotations

from fastapi import Request

from app.integrations import tokens
from app.integrations.errors import fail, request_language
from app.integrations.identity.base import AUTH_ACCESS_TOKEN, ResolvedIdentity


def bearer_value(request: Request) -> str | None:
    header = request.headers.get("Authorization") or ""
    scheme, _, value = header.partition(" ")
    if scheme.lower() != "bearer" or not value.strip():
        return None
    return value.strip()


class BearerTokenProvider:
    name = "bearer"

    async def resolve(self, request: Request) -> ResolvedIdentity | None:
        value = bearer_value(request)
        if value is None or not value.startswith(tokens.TOKEN_PREFIX):
            return None
        lang = request_language(request)
        challenge = {"WWW-Authenticate": 'Bearer realm="vyapar", error="invalid_token"'}
        if not tokens.looks_like_token(value):
            raise fail(401, "token_invalid", lang, headers=challenge)

        from app.db import get_pool

        async with get_pool().acquire() as conn:
            row = await tokens.lookup(conn, value)
        if row is None:
            raise fail(401, "token_invalid", lang, headers=challenge)
        return ResolvedIdentity(
            member_id=row["member_id"],
            auth_method=AUTH_ACCESS_TOKEN,
            scopes=frozenset(row["scopes"]),
            credential_id=str(row["token_id"]),
        )

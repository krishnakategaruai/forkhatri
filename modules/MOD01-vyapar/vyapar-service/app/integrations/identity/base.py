# [IMP37 — Refactor B] The IdentityProvider interface.
#
# A provider answers one question for one request: "is there a credential of
# MY kind here, and whose is it?" It returns:
#   * a ResolvedIdentity when it recognises and accepts the credential;
#   * None when no credential of its kind is present, so the next configured
#     provider gets a turn;
#   * raises (an IntegrationError / HTTPException) when a credential of its
#     kind IS present but invalid — never falls through to a weaker provider,
#     so a bad or revoked token cannot silently become some default member.
#
# Providers only establish identity. What that identity may do is decided
# afterwards, in one place: app/identity.py (scope policy) and, underneath,
# Postgres RLS keyed on vyapar.authz_context.
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from fastapi import Request

# How the caller authenticated. A member session is a person using the web
# app through their host platform; a token is an agent or API client acting
# on that member's behalf with limited scopes.
AUTH_MEMBER_SESSION = "member_session"
AUTH_DEV_HEADER = "dev_header"
AUTH_ACCESS_TOKEN = "access_token"


@dataclass(frozen=True)
class ResolvedIdentity:
    member_id: str
    auth_method: str
    scopes: frozenset[str] | None = None  # None = a member session: every scope
    credential_id: str | None = None      # access token id, for audit attribution


class IdentityProvider(Protocol):
    name: str

    async def resolve(self, request: Request) -> ResolvedIdentity | None: ...


async def ensure_member_row(member_id: str, display_name: str, phone: str | None, language: str) -> None:
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

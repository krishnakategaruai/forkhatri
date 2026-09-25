# [TR050] Identity Bridge — the single choke point that turns "whatever the
# caller presented" into an AuthzContext (FR50). Vyapar never signs a member
# up, logs them in, or issues a session: authentication belongs to the host
# platform (or, for agents, to a personal access token the member created).
#
# [IMP37 — Refactor B] How the caller is recognised is no longer written
# here. It is delegated to the IdentityProvider adapters in
# app/integrations/identity/ (dev header, ForKhatri session, bearer token),
# chosen by IDENTITY_PROVIDERS. What stays here, unchanged for every router:
#   * the signature of resolve_authz_context(request, X-Dev-Member-Id);
#   * AuthzContext(member_id, is_operator) — now also recording HOW the
#     caller authenticated (auth_method), the token's scopes and its id;
#   * the operator lookup under the resolved member's RLS context.
# New here:
#   * the default-deny scope policy for access tokens (scopes.py) — applied
#     before any route code runs, so no route can forget it;
#   * a token never carries operator powers, even a token an operator made;
#   * require_scope("...") for routes/services that want an explicit check.
# Traces to: FR50, TR050, SP050 (IdentityBridge-CC), REFACTOR-PLAN.md §B
from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header, Request

from app.integrations.errors import fail, request_language
from app.integrations.identity import AUTH_ACCESS_TOKEN, AUTH_MEMBER_SESSION, authenticate
from app.integrations.identity.scopes import DENY, required_scopes


@dataclass(frozen=True)
class AuthzContext:
    member_id: str
    is_operator: bool = False
    # How the caller authenticated: "member_session", "dev_header" or
    # "access_token". Defaults keep every existing AuthzContext(...) call valid.
    auth_method: str = AUTH_MEMBER_SESSION
    # None for member sessions (they implicitly hold every scope).
    scopes: frozenset[str] | None = None
    # The access token's id when auth_method == "access_token" — the audit
    # trail records it for every write the token makes.
    credential_id: str | None = None

    @property
    def is_token(self) -> bool:
        return self.auth_method == AUTH_ACCESS_TOKEN

    def has_scope(self, scope: str) -> bool:
        return self.scopes is None or scope in self.scopes


def _enforce_token_policy(request: Request, ctx: AuthzContext) -> None:
    lang = request_language(request)
    needed = required_scopes(request.method, request.url.path)
    if needed == DENY:
        raise fail(403, "not_available_to_tokens", lang)
    if not any(ctx.has_scope(s) for s in needed):
        raise fail(403, "scope_required", lang, scope=" | ".join(needed))


async def resolve_authz_context(
    request: Request,
    x_dev_member_id: str | None = Header(default=None, alias="X-Dev-Member-Id"),
) -> AuthzContext:
    # x_dev_member_id stays in the signature so the header keeps appearing in
    # the OpenAPI document; DevHeaderProvider reads it from the request.
    identity = await authenticate(request)

    if identity.auth_method == AUTH_ACCESS_TOKEN:
        ctx = AuthzContext(
            member_id=identity.member_id,
            is_operator=False,
            auth_method=identity.auth_method,
            scopes=identity.scopes,
            credential_id=identity.credential_id,
        )
        # Set before the policy check so a refused write is audited too.
        request.state.vyapar_authz = ctx
        _enforce_token_policy(request, ctx)
    else:
        from app.db import get_pool

        async with get_pool().acquire() as conn:
            # set_config(..., true) is transaction-scoped (SET LOCAL-equivalent)
            # — set AND read inside one transaction, or the RLS-scoped read
            # below would not see this member's row.
            async with conn.transaction():
                await conn.execute("SELECT set_config('vyapar.authz_context', $1, true)", identity.member_id)
                row = await conn.fetchrow(
                    "SELECT is_operator FROM vyapar_identity.members WHERE id = $1", identity.member_id
                )
        ctx = AuthzContext(
            member_id=identity.member_id,
            is_operator=bool(row["is_operator"]) if row else False,
            auth_method=identity.auth_method,
        )

    # Read by the integration middleware (per-token write audit).
    request.state.vyapar_authz = ctx
    return ctx


def require_scope(scope: str):
    """FastAPI dependency: `ctx: AuthzContext = Depends(require_scope("listings:write"))`.
    Member sessions pass; access tokens must hold the scope."""

    async def _dependency(request: Request, ctx: AuthzContext = Depends(resolve_authz_context)) -> AuthzContext:
        if not ctx.has_scope(scope):
            raise fail(403, "scope_required", request_language(request), scope=scope)
        return ctx

    return _dependency


def require_member_session(request: Request, ctx: AuthzContext) -> None:
    """Refuses access tokens outright (credential management, for example)."""
    if ctx.is_token:
        raise fail(403, "member_session_required", request_language(request))

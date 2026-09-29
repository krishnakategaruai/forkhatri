# [TR050 dev stub, moved here unchanged by IMP37] Dev-only stand-in for a host
# platform's real session. NOT authentication — selects which already-seeded
# member the request acts as, for local development and manual QA only:
# X-Dev-Member-Id header, else the vyapar_dev_member_id cookie, else
# DEV_DEFAULT_MEMBER_ID. Enabled only when "dev" is in IDENTITY_PROVIDERS (by
# default: when DEV_MODE is on).
#
# One deliberate refinement: when the request carries an Authorization
# header, this provider steps aside. A caller presenting a credential must
# be judged on that credential, never quietly handed the default member.
#
# [IMP-ADMIN — ADR-012] Development-only stand-in for the platform's
# `admin_scopes`: an `X-Dev-Admin-Scopes: vyapar.moderate,vyapar.verify`
# header is mapped exactly as the ForKhatri adapter maps the resolve
# response, so the Admin Console can be exercised without the identity
# service. Honoured only while DEV_MODE is on (the existing dev flag) AND this
# provider is configured; in any other setup the header is ignored.
from __future__ import annotations

from fastapi import Request

from app.config import get_settings
from app.integrations.identity.admin_scopes import parse_scope_list, permissions_for_scopes
from app.integrations.identity.base import AUTH_DEV_HEADER, ResolvedIdentity, ensure_member_row

DEV_ADMIN_SCOPES_HEADER = "X-Dev-Admin-Scopes"


class DevHeaderProvider:
    name = "dev"

    async def resolve(self, request: Request) -> ResolvedIdentity | None:
        if request.headers.get("Authorization"):
            return None
        settings = get_settings()
        member_id = (
            request.headers.get("X-Dev-Member-Id")
            or request.cookies.get("vyapar_dev_member_id")
            or settings.dev_default_member_id
        )
        await ensure_member_row(member_id, member_id, None, "en")
        permissions: frozenset[str] = frozenset()
        if settings.dev_mode:
            permissions = permissions_for_scopes(parse_scope_list(request.headers.get(DEV_ADMIN_SCOPES_HEADER)))
        return ResolvedIdentity(member_id=member_id, auth_method=AUTH_DEV_HEADER, operator_permissions=permissions)

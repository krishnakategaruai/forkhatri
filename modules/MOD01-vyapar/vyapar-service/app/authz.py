# [TR033/TR034] The Authorization Engine — the SINGLE chokepoint for workspace
# capability and role decisions (FR33, FR34).
# Approach: one function resolves, per request, the caller's role for a listing
# (owner / admin / operator / none) and whether the listing's entitlement is
# active, by calling migration 007's `workspace_context()`. Every workspace
# capability check goes through `require()` here — no feature re-checks
# `entitlements.state` on its own, which is exactly the drift SP033 names as a
# High threat. Nothing is cached: each request re-resolves from
# `workspace_members.state`, so a revoked role is denied on the very next
# request with no cache to invalidate (SP034's 100% revocation rule).
# The role matrix is the FR34 split, stated once:
#   owner    — everything, including delete/transfer and billing
#   admin    — everything except delete/transfer
#   operator — opportunities, enquiries and reports; never billing or team
# `entitlement_required` marks the capabilities the plan unlocks (FR33), so a
# Paused plan locks them while the data stays untouched. The DB enforces the
# same rule underneath: `is_workspace_collaborator()` (migration 007) requires
# an active entitlement, and the listings/opportunities/enquiries policies call
# it — so a route-layer mistake still cannot hand a lapsed workspace access.
# Traces to: FR33, FR34, TR033, TR034, SP033, SP034
from __future__ import annotations

from dataclasses import dataclass

import asyncpg
from fastapi import HTTPException

from app.i18n import translate

ROLE_CAPABILITIES: dict[str, set[str]] = {
    "owner": {"billing", "team", "campaigns", "reports", "opportunities", "enquiries", "delete_transfer"},
    "admin": {"billing", "team", "campaigns", "reports", "opportunities", "enquiries"},
    "operator": {"campaigns", "reports", "opportunities", "enquiries"},
    "none": set(),
}

# [FR33] capabilities the Business Workspace plan unlocks. Billing itself is
# never gated (an owner must be able to buy or fix a lapsed plan), and neither
# is a member's own single-listing activity — the plan sells team, campaigns
# and workspace-level reporting, never verification, reputation or ranking.
ENTITLEMENT_REQUIRED = {"team", "campaigns"}


@dataclass
class WorkspaceContext:
    listing_id: str
    listing_name: str | None
    role: str
    owner_id: str | None
    entitlement_state: str | None
    entitlement_active: bool
    entitlement_id: str | None
    renews_at: str | None
    grace_until: str | None
    cancel_at_period_end: bool
    product_id: str | None
    product_version: int | None

    def can(self, capability: str) -> bool:
        if capability not in ROLE_CAPABILITIES.get(self.role, set()):
            return False
        if capability in ENTITLEMENT_REQUIRED and not self.entitlement_active:
            return False
        return True


async def workspace_context(conn: asyncpg.Connection, listing_id: str) -> WorkspaceContext | None:
    try:
        row = await conn.fetchrow("SELECT * FROM vyapar_commercial.workspace_context($1)", listing_id)
    except asyncpg.DataError:
        return None
    if row is None:
        return None
    return WorkspaceContext(
        listing_id=str(listing_id),
        listing_name=row["listing_name"],
        role=row["role"],
        owner_id=row["owner_id"],
        entitlement_state=row["entitlement_state"],
        entitlement_active=row["entitlement_active"],
        entitlement_id=str(row["entitlement_id"]) if row["entitlement_id"] else None,
        renews_at=row["renews_at"].isoformat() if row["renews_at"] else None,
        grace_until=row["grace_until"].isoformat() if row["grace_until"] else None,
        cancel_at_period_end=row["cancel_at_period_end"],
        product_id=row["product_id"],
        product_version=row["product_version"],
    )


async def require(conn: asyncpg.Connection, listing_id: str, capability: str, lang: str) -> WorkspaceContext:
    """Resolves the context and authorises one capability, or raises. Every
    workspace route starts with this call — it is the only place that decides."""
    ctx = await workspace_context(conn, listing_id)
    if ctx is None or ctx.role == "none":
        raise HTTPException(status_code=404, detail=translate("workspace.error.notFound", lang))
    if capability in ENTITLEMENT_REQUIRED and not ctx.entitlement_active:
        raise HTTPException(status_code=403, detail=translate("workspace.error.planRequired", lang))
    if not ctx.can(capability):
        raise HTTPException(status_code=403, detail=translate("workspace.error.roleNotAllowed", lang))
    return ctx

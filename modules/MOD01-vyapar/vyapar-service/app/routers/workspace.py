# [TR033] Business Workspace entitlement, renewal and grace (FR33).
# [TR034] Multi-user workspace roles (FR34).
# Approach:
#  - Every route begins with the Authorization Engine (`app/authz.py`), which
#    is the single place that reads role + entitlement state (TR033/SP033). No
#    route re-checks `entitlements.state` itself, and the database enforces the
#    same rule underneath through `is_workspace_collaborator()`.
#  - Purchase follows FR54's two steps exactly as boosts do: creating the
#    entitlement charges nothing, and `confirm-purchase` (with an explicit
#    `confirmed: true`) is the only route that can start a payment. The plan's
#    own disclosure — price, tax, renewal date, what is included and the
#    explicit "never included" list — is returned for the one screen to show.
#  - The plan NEVER grants verification, reputation, ranking, eligibility or
#    private member data: it unlocks exactly `team` and `campaigns` in
#    `ENTITLEMENT_REQUIRED`, and nothing in this module reads entitlement state
#    when ranking, verifying or moderating.
#  - Renewal (FR33/FR54): the scheduled pass reminds 3 days ahead and will not
#    let a renewal proceed unless that reminder was actually delivered; then a
#    7-day grace, then Paused with all data retained (no delete anywhere).
#  - Roles (FR34): invite by phone resolves a member id through the Identity
#    Bridge's own lookup, the invitee must accept, an invite expires after 30
#    days, and revocation takes effect on the very next request because nothing
#    is cached. Revoking a Vyapar role never touches the platform session —
#    this module owns no sessions at all.
#  - Every team action is audited against the acting individual (FR34/FR49).
# Reference (Upwork + WorkIndia lens): Upwork's Agency/company model and
# WorkIndia's employer accounts both let several people act for one business
# with distinct roles, and both make the invited person accept before they can
# act — followed here. Neither sells verification with the plan, and neither
# does Vyapar.
# Traces to: FR33, FR34, FR54, TR033, TR034, SP033, SP034
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app import authz
from app.audit import audit
from app.db import get_conn
from app.deps import Locale
from app.i18n import LAUNCH_LANGUAGES, translate
from app.identity import AuthzContext, resolve_authz_context
from app.routers.commercial import _history, products_for_kind
from app.routers.payments import GatewayUnavailable, create_payment_order

router = APIRouter(tags=["workspace"])

INVITE_ROLES = ("admin", "operator")


async def _notify_workspace(
    conn: asyncpg.Connection,
    *,
    listing_id: str,
    recipient: str,
    template: str,
    link: str,
    idempotency_key: str,
    params: dict[str, str] | None = None,
    key_params: dict[str, str] | None = None,
) -> bool:
    import json

    texts = {}
    for lang in LAUNCH_LANGUAGES:
        values = dict(params or {})
        for name, key in (key_params or {}).items():
            values[name] = translate(key, lang)
        texts[lang] = {
            "title": translate(f"notifications.{template}.title", lang, **values),
            "body": translate(f"notifications.{template}.body", lang, **values),
        }
    return await conn.fetchval(
        "SELECT vyapar_commercial.notify_workspace_member($1, $2, $3, $4::jsonb, $5, $6)",
        listing_id, recipient, template, json.dumps(texts, ensure_ascii=False), link, idempotency_key,
    )


def _plan_out(product: dict) -> dict:
    return {
        "id": product["id"], "version": product["version"], "billing": product["billing"],
        "duration_days": product["duration_days"], "price_paise": product["price_paise"],
        "tax_paise": product["tax_paise"], "total_paise": product["total_paise"],
        "capabilities": product["capabilities"],
    }


@router.get("/v1/workspace/{listing_id}")
async def get_workspace(
    listing_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    wctx = await authz.workspace_context(conn, listing_id)
    if wctx is None or wctx.role == "none":
        raise HTTPException(status_code=404, detail=translate("workspace.error.notFound", lang))
    members: list[dict] = []
    if wctx.can("team"):
        rows = await conn.fetch("SELECT * FROM vyapar_commercial.workspace_members_for($1)", listing_id)
        members = [
            {
                "id": str(r["id"]), "member_id": r["member_id"], "display_name": r["display_name"],
                "phone_masked": r["phone_masked"], "role": r["role"], "state": r["state"],
                "invited_at": r["invited_at"].isoformat(), "expires_at": r["expires_at"].isoformat() if r["expires_at"] else None,
            }
            for r in rows
        ]
    campaigns = await conn.fetch(
        "SELECT id, name, state, starts_at, ends_at FROM vyapar_commercial.campaigns WHERE listing_id = $1 ORDER BY created_at DESC",
        listing_id,
    )
    return {
        "listing_id": listing_id, "listing_name": wctx.listing_name, "role": wctx.role,
        "is_owner": wctx.role == "owner",
        "entitlement": None if wctx.entitlement_id is None else {
            "id": wctx.entitlement_id, "state": wctx.entitlement_state, "active": wctx.entitlement_active,
            "renews_at": wctx.renews_at, "grace_until": wctx.grace_until,
            "cancel_at_period_end": wctx.cancel_at_period_end,
            "product_id": wctx.product_id, "product_version": wctx.product_version,
        },
        "capabilities": sorted(c for c in authz.ROLE_CAPABILITIES[wctx.role] if wctx.can(c)),
        "plans": [_plan_out(p) for p in await products_for_kind(conn, "workspace")],
        "members": members,
        "campaigns": [
            {"id": str(c["id"]), "name": c["name"], "state": c["state"],
             "starts_at": c["starts_at"].isoformat() if c["starts_at"] else None,
             "ends_at": c["ends_at"].isoformat() if c["ends_at"] else None}
            for c in campaigns
        ],
    }


class EntitlementIn(BaseModel):
    listing_id: str
    product_id: str


@router.post("/v1/entitlements", status_code=201)
async def create_entitlement(
    body: EntitlementIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    wctx = await authz.require(conn, body.listing_id, "billing", lang)
    # [Declared RLS constraint] `entitlements` WITH CHECK admits only
    # `owner_id = self`, so buying the plan is the listing owner's action even
    # though FR34 gives an Admin "everything except delete/transfer". Recorded
    # as a gap for Step 7a rather than worked around.
    if wctx.role != "owner":
        raise HTTPException(status_code=403, detail=translate("workspace.error.ownerOnly", lang))
    if wctx.entitlement_state in ("active", "awaiting_payment"):
        raise HTTPException(status_code=409, detail=translate("workspace.error.planExists", lang))
    product = next((p for p in await products_for_kind(conn, "workspace") if p["id"] == body.product_id), None)
    if product is None:
        raise HTTPException(status_code=422, detail=translate("workspace.error.productNotFound", lang))
    row = await conn.fetchrow(
        """INSERT INTO vyapar_commercial.entitlements
             (listing_id, owner_id, product_id, product_version, price_paise, tax_paise, state)
           VALUES ($1, $2, $3, $4, $5, $6, 'awaiting_payment') RETURNING id""",
        body.listing_id, ctx.member_id, product["id"], product["version"], product["price_paise"], product["tax_paise"],
    )
    await conn.execute(
        "INSERT INTO vyapar_commercial.commercial_order_history (order_kind, order_id, from_state, to_state, reason) VALUES ('entitlement', $1, NULL, 'awaiting_payment', 'created')",
        row["id"],
    )
    await audit(conn, actor_id=ctx.member_id, action="entitlement_created", object_kind="entitlement", object_id=row["id"],
                details={"listing_id": body.listing_id, "product_id": product["id"], "product_version": product["version"]})
    return {"id": str(row["id"]), "state": "awaiting_payment", "plan": _plan_out(product)}


class ConfirmIn(BaseModel):
    confirmed: Literal[True]  # [TR054] explicit confirmation of the disclosure screen


async def _own_entitlement(conn: asyncpg.Connection, entitlement_id: str, member_id: str, lang: str) -> asyncpg.Record:
    try:
        row = await conn.fetchrow(
            "SELECT * FROM vyapar_commercial.entitlements WHERE id = $1 AND owner_id = $2", entitlement_id, member_id
        )
    except asyncpg.DataError:
        row = None
    if row is None:
        raise HTTPException(status_code=404, detail=translate("workspace.error.entitlementNotFound", lang))
    return row


@router.post("/v1/entitlements/{entitlement_id}/confirm-purchase")
async def confirm_entitlement_purchase(
    entitlement_id: str,
    body: ConfirmIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    ent = await _own_entitlement(conn, entitlement_id, ctx.member_id, lang)
    if ent["state"] not in ("awaiting_payment", "paused"):
        raise HTTPException(status_code=400, detail=translate("workspace.error.invalidTransition", lang))
    try:
        order = await create_payment_order(
            conn, kind="entitlement", ref_id=ent["id"], member_id=ctx.member_id,
            amount_paise=ent["price_paise"], tax_paise=ent["tax_paise"],
            description=f"Vyapar Business Workspace {ent['product_id']} v{ent['product_version']}",
            return_path=f"/workspace/{ent['listing_id']}",
        )
    except GatewayUnavailable:
        return {"state": ent["state"], "checkout_url": None, "notice": "gatewayUnavailable"}
    await audit(conn, actor_id=ctx.member_id, action="entitlement_purchase_confirmed", object_kind="entitlement",
                object_id=ent["id"], details={"payment_order_id": order["id"]})
    return {"state": ent["state"], "checkout_url": order["checkout_url"], "payment_order_id": order["id"], "notice": None}


class RenewalIn(BaseModel):
    cancel_at_period_end: bool


@router.post("/v1/entitlements/{entitlement_id}/renewal")
async def set_renewal(
    entitlement_id: str,
    body: RenewalIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    """[FR33] Cancelling stops the renewal at period end — access continues to
    the paid-through date and nothing is deleted. There is no hidden
    auto-renewal: the member can turn it back on from the same control."""
    ent = await _own_entitlement(conn, entitlement_id, ctx.member_id, lang)
    await conn.execute(
        "UPDATE vyapar_commercial.entitlements SET cancel_at_period_end = $2, updated_at = now() WHERE id = $1",
        ent["id"], body.cancel_at_period_end,
    )
    await _history(conn, ent["id"], ent["state"], ent["state"],
                   "renewal_cancelled" if body.cancel_at_period_end else "renewal_resumed", order_kind="entitlement")
    await audit(conn, actor_id=ctx.member_id, action="entitlement_renewal_set", object_kind="entitlement",
                object_id=ent["id"], details={"cancel_at_period_end": body.cancel_at_period_end})
    return {"cancel_at_period_end": body.cancel_at_period_end, "renews_at": ent["renews_at"].isoformat() if ent["renews_at"] else None}


@router.get("/v1/entitlements/mine")
async def list_my_entitlements(
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[dict]:
    rows = await conn.fetch(
        """SELECT e.*, l.name AS listing_name FROM vyapar_commercial.entitlements e
           LEFT JOIN vyapar_listings.listings l ON l.id = e.listing_id::uuid
           WHERE e.owner_id = $1 ORDER BY e.created_at DESC""",
        ctx.member_id,
    )
    return [
        {
            "id": str(r["id"]), "listing_id": r["listing_id"], "listing_name": r["listing_name"], "state": r["state"],
            "product_id": r["product_id"], "product_version": r["product_version"],
            "price_paise": r["price_paise"], "tax_paise": r["tax_paise"],
            "renews_at": r["renews_at"].isoformat() if r["renews_at"] else None,
            "grace_until": r["grace_until"].isoformat() if r["grace_until"] else None,
            "cancel_at_period_end": r["cancel_at_period_end"],
        }
        for r in rows
    ]


class InviteIn(BaseModel):
    phone: str = Field(min_length=8, max_length=20)
    role: Literal["admin", "operator"]


@router.post("/v1/workspace/{listing_id}/invite", status_code=201)
async def invite_member(
    listing_id: str,
    body: InviteIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    await authz.require(conn, listing_id, "team", lang)
    phone = body.phone.strip()
    # [TR034/SP034] resolved through the Identity Bridge's own lookup, never a
    # locally guessed mapping. An unknown phone still gets an invite, held for
    # 30 days until that person joins ForKhatri (FR34).
    member_id = await conn.fetchval("SELECT vyapar_identity.member_id_for_phone($1)", phone)
    if member_id == ctx.member_id:
        raise HTTPException(status_code=400, detail=translate("workspace.error.cannotInviteSelf", lang))
    owner_id = await conn.fetchval("SELECT owner_id FROM vyapar_listings.listings WHERE id = $1", listing_id)
    if member_id and member_id == owner_id:
        raise HTTPException(status_code=400, detail=translate("workspace.error.cannotInviteOwner", lang))
    existing = await conn.fetchval(
        """SELECT count(*) FROM vyapar_commercial.workspace_members
           WHERE listing_id = $1 AND state IN ('pending','active') AND (phone = $2 OR ($3::text IS NOT NULL AND member_id = $3))""",
        listing_id, phone, member_id,
    )
    if existing:
        raise HTTPException(status_code=409, detail=translate("workspace.error.alreadyInvited", lang))
    row = await conn.fetchrow(
        """INSERT INTO vyapar_commercial.workspace_members (listing_id, member_id, phone, role, state, invited_by)
           VALUES ($1, $2, $3, $4, 'pending', $5) RETURNING id, expires_at""",
        listing_id, member_id, phone, body.role, ctx.member_id,
    )
    if member_id:
        await _notify_workspace(
            conn, listing_id=listing_id, recipient=member_id, template="workspaceInvite",
            link="/profile", idempotency_key=f"workspace_invite:{row['id']}",
            params={"business": await conn.fetchval("SELECT name FROM vyapar_listings.listings WHERE id = $1", listing_id) or ""},
            key_params={"role": f"workspace.role.{body.role}"},
        )
    await audit(conn, actor_id=ctx.member_id, action="workspace_invited", object_kind="workspace_member", object_id=row["id"],
                details={"listing_id": listing_id, "role": body.role, "member_id": member_id, "pending_join": member_id is None})
    return {
        "id": str(row["id"]), "state": "pending", "role": body.role,
        "member_known": member_id is not None, "expires_at": row["expires_at"].isoformat(),
    }


@router.get("/v1/workspace/invites/mine")
async def my_invites(
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[dict]:
    rows = await conn.fetch("SELECT * FROM vyapar_commercial.pending_invites_for_me()")
    return [
        {
            "id": str(r["id"]), "listing_id": r["listing_id"], "listing_name": r["listing_name"], "role": r["role"],
            "invited_at": r["invited_at"].isoformat(), "expires_at": r["expires_at"].isoformat(),
        }
        for r in rows
    ]


class AnswerIn(BaseModel):
    accept: bool


@router.post("/v1/workspace/invites/{invite_id}/answer")
async def answer_invite(
    invite_id: str,
    body: AnswerIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    try:
        async with conn.transaction():
            state = await conn.fetchval("SELECT vyapar_commercial.answer_invite($1, $2)", invite_id, body.accept)
    except asyncpg.DataError:
        raise HTTPException(status_code=404, detail=translate("workspace.error.inviteNotFound", lang))
    except asyncpg.RaiseError as exc:
        if "invite_expired" in str(exc):
            raise HTTPException(status_code=400, detail=translate("workspace.error.inviteExpired", lang))
        raise HTTPException(status_code=404, detail=translate("workspace.error.inviteNotFound", lang))
    await audit(conn, actor_id=ctx.member_id, action="workspace_invite_answered", object_kind="workspace_member",
                object_id=invite_id, details={"accepted": body.accept, "state": state})
    return {"state": state}


class RoleChangeIn(BaseModel):
    state: Literal["active", "revoked"]
    role: Literal["admin", "operator"] | None = None


@router.post("/v1/workspace/members/{member_row_id}/role")
async def change_member_role(
    member_row_id: str,
    body: RoleChangeIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    """[FR34] Revocation is effective immediately: nothing caches the role, so
    the member's very next request is denied. The member's ForKhatri platform
    session is untouched — Vyapar owns no sessions."""
    try:
        async with conn.transaction():
            row = await conn.fetchrow(
                "SELECT * FROM vyapar_commercial.set_member_role_state($1, $2, $3)", member_row_id, body.state, body.role
            )
    except asyncpg.DataError:
        raise HTTPException(status_code=404, detail=translate("workspace.error.memberNotFound", lang))
    except asyncpg.RaiseError as exc:
        message = str(exc)
        if "plan_required" in message:
            raise HTTPException(status_code=403, detail=translate("workspace.error.planRequired", lang))
        if "role_not_allowed" in message:
            raise HTTPException(status_code=403, detail=translate("workspace.error.roleNotAllowed", lang))
        raise HTTPException(status_code=404, detail=translate("workspace.error.memberNotFound", lang))
    if row["member_id"]:
        await _notify_workspace(
            conn, listing_id=row["listing_id"], recipient=row["member_id"],
            template="workspaceRoleRevoked" if body.state == "revoked" else "workspaceRoleChanged",
            link="/profile", idempotency_key=f"workspace_role:{member_row_id}:{body.state}:{body.role or ''}",
            params={"business": await conn.fetchval("SELECT name FROM vyapar_listings.listings WHERE id = $1::uuid", row["listing_id"]) or ""},
            key_params={"role": f"workspace.role.{row['role']}"},
        )
    await audit(conn, actor_id=ctx.member_id, action="workspace_role_changed", object_kind="workspace_member",
                object_id=member_row_id, details={"state": body.state, "role": row["role"], "listing_id": row["listing_id"]})
    return {"state": row["state"], "role": row["role"]}


@router.get("/v1/workspace/mine")
async def my_workspaces(
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[dict]:
    """Listings the member can open a workspace for: their own, plus any where
    they hold an active role."""
    rows = await conn.fetch(
        """SELECT l.id, l.name, 'owner' AS role FROM vyapar_listings.listings l WHERE l.owner_id = $1
           UNION
           SELECT l.id, l.name, wm.role FROM vyapar_commercial.workspace_members wm
             JOIN vyapar_listings.listings l ON l.id = wm.listing_id::uuid
            WHERE wm.member_id = $1 AND wm.state = 'active'""",
        ctx.member_id,
    )
    return [{"listing_id": str(r["id"]), "listing_name": r["name"], "role": r["role"]} for r in rows]

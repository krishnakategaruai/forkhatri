# [TR033/TR034] Business Workspace plans and multi-user roles — HTTP front
# door only. Authorization (app/authz.py), purchase, renewal, invites and
# role changes live in app/services/workspace.py.
# Traces to: FR33, FR34, FR54, TR033, TR034, SP033, SP034
from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends

from app.db import get_conn
from app.deps import Locale
from app.errors import ERROR_RESPONSES
from app.identity import AuthzContext, resolve_authz_context
from app.services import workspace as svc
from app.services.workspace import (  # noqa: F401  schemas used below; background passes re-exported for main.py
    AnswerIn,
    ConfirmIn,
    EntitlementCreatedOut,
    EntitlementIn,
    EntitlementOut,
    EntitlementPurchaseOut,
    InviteAnswerOut,
    InviteCreatedOut,
    InviteIn,
    RenewalIn,
    RenewalOut,
    RoleChangeIn,
    RoleChangeOut,
    WorkspaceInviteOut,
    WorkspaceOut,
    WorkspaceSummaryOut,
)

router = APIRouter(tags=["workspace"], responses=ERROR_RESPONSES)


@router.get("/v1/workspace/mine", response_model=list[WorkspaceSummaryOut], operation_id="listMyWorkspaces", summary="List workspaces the member belongs to")
async def my_workspaces(
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[WorkspaceSummaryOut]:
    return await svc.list_my_workspaces(conn, ctx)


@router.get("/v1/workspace/{listing_id}", response_model=WorkspaceOut, operation_id="getWorkspace", summary="Get a listing's workspace")
async def get_workspace(
    listing_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> WorkspaceOut:
    return await svc.get_workspace(conn, ctx, lang, listing_id=listing_id)


@router.post("/v1/entitlements", status_code=201, response_model=EntitlementCreatedOut, operation_id="createEntitlement", summary="Start a workspace plan purchase")
async def create_entitlement(
    body: EntitlementIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> EntitlementCreatedOut:
    return await svc.create_entitlement(conn, ctx, lang, body=body)


@router.post("/v1/entitlements/{entitlement_id}/confirm-purchase", response_model=EntitlementPurchaseOut, response_model_exclude_unset=True, operation_id="confirmEntitlementPurchase", summary="Confirm a workspace plan purchase")
async def confirm_entitlement_purchase(
    entitlement_id: str,
    body: ConfirmIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> EntitlementPurchaseOut:
    return await svc.confirm_entitlement_purchase(conn, ctx, lang, entitlement_id=entitlement_id, body=body)


@router.post("/v1/entitlements/{entitlement_id}/renewal", response_model=RenewalOut, operation_id="setEntitlementRenewal", summary="Turn auto-renewal on or off for a plan")
async def set_renewal(
    entitlement_id: str,
    body: RenewalIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> RenewalOut:
    return await svc.set_entitlement_renewal(conn, ctx, lang, entitlement_id=entitlement_id, body=body)


@router.get("/v1/entitlements/mine", response_model=list[EntitlementOut], operation_id="listMyEntitlements", summary="List the member's workspace plans")
async def list_my_entitlements(
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[EntitlementOut]:
    return await svc.list_my_entitlements(conn, ctx)


@router.post("/v1/workspace/{listing_id}/invite", status_code=201, response_model=InviteCreatedOut, operation_id="inviteWorkspaceMember", summary="Invite a member to a workspace")
async def invite_member(
    listing_id: str,
    body: InviteIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> InviteCreatedOut:
    return await svc.invite_workspace_member(conn, ctx, lang, listing_id=listing_id, body=body)


@router.get("/v1/workspace/invites/mine", response_model=list[WorkspaceInviteOut], operation_id="listMyWorkspaceInvites", summary="List workspace invitations for the member")
async def my_invites(
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[WorkspaceInviteOut]:
    return await svc.list_my_workspace_invites(conn, ctx)


@router.post("/v1/workspace/invites/{invite_id}/answer", response_model=InviteAnswerOut, operation_id="answerWorkspaceInvite", summary="Accept or decline a workspace invitation")
async def answer_invite(
    invite_id: str,
    body: AnswerIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> InviteAnswerOut:
    return await svc.answer_workspace_invite(conn, ctx, lang, invite_id=invite_id, body=body)


@router.post("/v1/workspace/members/{member_row_id}/role", response_model=RoleChangeOut, operation_id="changeWorkspaceMemberRole", summary="Change a workspace member's role")
async def change_member_role(
    member_row_id: str,
    body: RoleChangeIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> RoleChangeOut:
    return await svc.change_workspace_member_role(conn, ctx, lang, member_row_id=member_row_id, body=body)

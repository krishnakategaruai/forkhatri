# [IMP-ADMIN] Admin & Governance Console (ADR-012, TR-PLAT-01) — HTTP front
# door for Vyapar's federated admin views. Every route here is a member-
# session route: personal access tokens are refused before any code runs
# (integrations/identity/scopes.py lists "/vyapar/admin" as token-forbidden).
# Access comes from the member row's operator permissions OR the host
# session's admin scopes; the rules, queue membership and decisions all live
# in app/services/admin_console.py and the services it calls.
#
#   GET  /vyapar/admin/manifest
#   GET  /vyapar/admin/{view}                                 AdminQueueItem[]
#   GET  /vyapar/admin/{view}/{item_id}                       detail + available actions
#   POST /vyapar/admin/{view}/{item_id}/actions/{action_id}   {notes, reason_code?} -> AdminQueueItem
#   GET  /vyapar/admin/members/{member_id}/summary            plan, facts, flags for the person page
#
# Each view gets its own three routes (not one /{view} route) so every
# operation has a distinct, stable operation_id for SDK and agent generators.
# Traces to: TR-PLAT-01, ADR-012, TR040, TR041, TR047, TR048, TR029
from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends

from app.db import get_conn
from app.deps import Locale
from app.errors import ERROR_RESPONSES
from app.identity import AuthzContext, resolve_authz_context
from app.services import admin_console as svc
from app.services.admin_console import AdminActionIn, AdminItemDetailOut, AdminManifestOut, AdminQueueItem, MemberSummaryOut

router = APIRouter(prefix=svc.BASE_PATH, tags=["admin-console"], responses=ERROR_RESPONSES)


@router.get("/manifest", response_model=AdminManifestOut, operation_id="getVyaparAdminManifest",
            summary="Admin Console views this operator may open (TR-PLAT-01 manifest)")
async def get_manifest(
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> AdminManifestOut:
    return await svc.get_manifest(conn, ctx, lang)


@router.get("/members/{member_id}/summary", response_model=MemberSummaryOut, operation_id="getVyaparAdminMemberSummary",
            summary="What this person has in Vyapar: plan, facts and flags (404 without a Vyapar account)")
async def get_member_summary(
    member_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> MemberSummaryOut:
    return await svc.get_member_summary(conn, ctx, lang, member_id)


def _camel(view_id: str) -> str:
    return "".join(part.capitalize() for part in view_id.split("_"))


def _register(view: svc.ViewSpec) -> None:
    name = _camel(view.view_id)

    @router.get(f"/{view.view_id}", response_model=list[AdminQueueItem], operation_id=f"listVyaparAdmin{name}Items",
                summary=f"List the '{view.view_id}' Admin Console queue")
    async def list_items(
        lang: Locale,
        ctx: AuthzContext = Depends(resolve_authz_context),
        conn: asyncpg.Connection = Depends(get_conn, scope="function"),
    ) -> list[AdminQueueItem]:
        return await svc.list_items(conn, ctx, lang, view.view_id)

    @router.get(f"/{view.view_id}/{{item_id}}", response_model=AdminItemDetailOut, operation_id=f"getVyaparAdmin{name}Item",
                summary=f"Get one '{view.view_id}' item with its history and available actions")
    async def get_item(
        item_id: str,
        lang: Locale,
        ctx: AuthzContext = Depends(resolve_authz_context),
        conn: asyncpg.Connection = Depends(get_conn, scope="function"),
    ) -> AdminItemDetailOut:
        return await svc.get_item(conn, ctx, lang, view.view_id, item_id)

    @router.post(f"/{view.view_id}/{{item_id}}/actions/{{action_id}}", response_model=AdminQueueItem,
                 operation_id=f"actOnVyaparAdmin{name}Item",
                 summary=f"Take an action on a '{view.view_id}' item; returns the updated item")
    async def act(
        item_id: str,
        action_id: str,
        body: AdminActionIn,
        lang: Locale,
        ctx: AuthzContext = Depends(resolve_authz_context),
        conn: asyncpg.Connection = Depends(get_conn, scope="function"),
    ) -> AdminQueueItem:
        return await svc.act_on_item(conn, ctx, lang, view.view_id, item_id, action_id, body)


for _view in svc.VIEWS:
    _register(_view)

# [TR039/TR040/TR041] Reports, the moderation queue and graduated actions,
# appeals — HTTP front door only. Rules, SECURITY DEFINER calls and the
# 'moderation' permission chokepoint live in app/services/trust_safety.py.
# Traces to: FR39, FR40, FR41, FR53, TR039, TR040, TR041, SP039, SP040, SP041
from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends, Header

from app.db import get_conn
from app.deps import Locale
from app.errors import ERROR_RESPONSES
from app.identity import AuthzContext, resolve_authz_context
from app.services import trust_safety as svc
from app.services.trust_safety import (  # noqa: F401  schemas used below; background passes re-exported for main.py
    AppealCreatedOut,
    AppealDecisionIn,
    AppealDecisionOut,
    AppealIn,
    AppealQueueItemOut,
    CaseDecisionOut,
    DecideIn,
    ModerationCaseOut,
    ModerationOutcomeOut,
    ReportIn,
    ReportReceivedOut,
    run_moderation_escalation_pass,
)

router = APIRouter(tags=["trust-safety"], responses=ERROR_RESPONSES)
admin_router = APIRouter(prefix="/v1/admin", tags=["admin-moderation"], responses=ERROR_RESPONSES)


@router.post("/v1/reports", status_code=201, response_model=ReportReceivedOut, operation_id="createReport", summary="Report content or a member")
async def file_report(
    body: ReportIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> ReportReceivedOut:
    return await svc.create_report(conn, ctx, lang, body=body, idempotency_key=idempotency_key)


@router.get("/v1/moderation/outcomes", response_model=list[ModerationOutcomeOut], operation_id="listMyModerationOutcomes", summary="List moderation outcomes affecting the member")
async def list_my_outcomes(
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[ModerationOutcomeOut]:
    return await svc.list_my_moderation_outcomes(conn, ctx)


@router.post("/v1/appeals", status_code=201, response_model=AppealCreatedOut, operation_id="createAppeal", summary="Appeal a moderation outcome")
async def file_appeal(
    body: AppealIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> AppealCreatedOut:
    return await svc.create_appeal(conn, ctx, lang, body=body)


@admin_router.get("/moderation-queue", response_model=list[ModerationCaseOut], operation_id="listModerationQueue", summary="List the admin moderation queue")
async def moderation_queue(
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[ModerationCaseOut]:
    return await svc.list_moderation_queue(conn, ctx, lang)


@admin_router.post("/moderation-cases/{case_id}/decide", response_model=CaseDecisionOut, operation_id="decideModerationCase", summary="Decide a moderation case (admin)")
async def decide_case(
    case_id: str,
    body: DecideIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> CaseDecisionOut:
    return await svc.decide_moderation_case(conn, ctx, lang, case_id=case_id, body=body)


@admin_router.get("/appeals", response_model=list[AppealQueueItemOut], operation_id="listAppeals", summary="List appeals (admin)")
async def list_appeals(
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[AppealQueueItemOut]:
    return await svc.list_appeals(conn, ctx, lang)


@admin_router.post("/appeals/{appeal_id}/decide", response_model=AppealDecisionOut, operation_id="decideAppeal", summary="Decide an appeal (admin)")
async def decide_appeal(
    appeal_id: str,
    body: AppealDecisionIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> AppealDecisionOut:
    return await svc.decide_appeal(conn, ctx, lang, appeal_id=appeal_id, body=body)

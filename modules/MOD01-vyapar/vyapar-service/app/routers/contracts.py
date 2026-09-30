# [Backend workstream D, 2026-09-28] Contracts & milestone payments — HTTP
# front door only. Every rule, query and notification lives in
# app/services/contracts.py; this file parses, calls and returns.
#
# Route order: the static `/v1/contracts/jobs/auto-release` and the operator
# list are registered before any `/{contract_id}` route (Starlette matches in
# registration order — the same static-before-dynamic rule main.py applies).
# Traces to: FR23, FR27, FR51/TR051, FR52/TR052, REFACTOR-PLAN.md §A
from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends, Query

from app.config import get_settings
from app.db import get_conn, get_pool
from app.deps import Locale
from app.errors import ApiError, ERROR_RESPONSES
from app.identity import AuthzContext, resolve_authz_context
from app.services import contracts as svc
from app.services.contracts import (  # noqa: F401  schemas used below; the pass is re-exported for a scheduler
    AdminDisputeOut,
    AutoReleaseOut,
    CancelIn,
    ContractCreateIn,
    ContractOut,
    ContractRole,
    ContractRolesOut,
    ContractState,
    ContractSummaryOut,
    DisputeIn,
    DisputeResolveIn,
    DisputeState,
    FundingOut,
    MilestoneIn,
    MilestoneUpdateIn,
    RejectIn,
    SubmitIn,
    TimesheetIn,
    run_contract_auto_release_pass,
)
from app.services.pagination import DEFAULT_LIMIT, MAX_LIMIT, Page

router = APIRouter(prefix="/v1/contracts", tags=["contracts"], responses=ERROR_RESPONSES)


# --- static paths first -------------------------------------------------------
@router.post("/jobs/auto-release", response_model=AutoReleaseOut, operation_id="runContractAutoRelease", summary="Release overdue submitted milestones now (dev only)")
async def run_auto_release(lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context)) -> AutoReleaseOut:
    if not get_settings().dev_mode:
        raise ApiError(404, "contracts.error.devOnly", lang)
    return AutoReleaseOut(**await run_contract_auto_release_pass(get_pool()))


@router.get("/disputes", response_model=list[AdminDisputeOut], operation_id="listContractDisputes", summary="List contract disputes (moderation operators)")
async def list_disputes(
    lang: Locale,
    state: DisputeState | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> list[AdminDisputeOut]:
    return await svc.list_disputes_for_operators(conn, ctx, lang, state=state, limit=limit)


@router.get("/roles", response_model=ContractRolesOut, operation_id="getContractRoles", summary="Who pays and who works if this enquiry becomes a contract, and whether I can start it")
async def get_contract_roles(
    lang: Locale,
    enquiry_id: str = Query(description="The enquiry to check"),
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> ContractRolesOut:
    return await svc.get_contract_roles(conn, ctx, lang, enquiry_id=enquiry_id)


# --- contracts ----------------------------------------------------------------
@router.post("", status_code=201, response_model=ContractOut, operation_id="createContract", summary="Create a contract from an accepted enquiry (client)")
async def create_contract(
    body: ContractCreateIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> ContractOut:
    return await svc.create_contract(conn, ctx, lang, body=body)


@router.get("", response_model=Page[ContractSummaryOut], operation_id="listMyContracts", summary="List my contracts as client, provider or both")
async def list_my_contracts(
    lang: Locale,
    role: ContractRole = "all",
    state: ContractState | None = None,
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    cursor: str | None = None,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> Page[ContractSummaryOut]:
    return await svc.list_my_contracts(conn, ctx, lang, role=role, state=state, limit=limit, cursor=cursor)


@router.get("/{contract_id}", response_model=ContractOut, operation_id="getContract", summary="Get one contract with milestones, ledger, timesheets, disputes and timeline")
async def get_contract(
    contract_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> ContractOut:
    return await svc.get_contract(conn, ctx, lang, contract_id=contract_id)


@router.post("/{contract_id}/propose", response_model=ContractOut, operation_id="proposeContract", summary="Send a draft contract to the provider (client)")
async def propose_contract(
    contract_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> ContractOut:
    return await svc.propose_contract(conn, ctx, lang, contract_id=contract_id)


@router.post("/{contract_id}/accept", response_model=ContractOut, operation_id="acceptContract", summary="Accept a proposed contract (provider)")
async def accept_contract(
    contract_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> ContractOut:
    return await svc.accept_contract(conn, ctx, lang, contract_id=contract_id)


@router.post("/{contract_id}/cancel", response_model=ContractOut, operation_id="cancelContract", summary="Cancel a contract; held milestones are refunded to the client")
async def cancel_contract(
    contract_id: str,
    lang: Locale,
    body: CancelIn | None = None,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> ContractOut:
    return await svc.cancel_contract(conn, ctx, lang, contract_id=contract_id, body=body or CancelIn())


@router.post("/{contract_id}/complete", response_model=ContractOut, operation_id="completeContract", summary="Complete an active contract with nothing held (client; hourly contracts end this way)")
async def complete_contract(
    contract_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> ContractOut:
    return await svc.complete_contract(conn, ctx, lang, contract_id=contract_id)


# --- milestones ---------------------------------------------------------------
@router.post("/{contract_id}/milestones", status_code=201, response_model=ContractOut, operation_id="addMilestone", summary="Add a milestone to a draft fixed-price contract (client)")
async def add_milestone(
    contract_id: str,
    body: MilestoneIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> ContractOut:
    return await svc.add_milestone(conn, ctx, lang, contract_id=contract_id, body=body)


@router.patch("/{contract_id}/milestones/{milestone_id}", response_model=ContractOut, operation_id="updateMilestone", summary="Edit a milestone of a draft contract (client)")
async def update_milestone(
    contract_id: str,
    milestone_id: str,
    body: MilestoneUpdateIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> ContractOut:
    return await svc.update_milestone(conn, ctx, lang, contract_id=contract_id, milestone_id=milestone_id, body=body)


@router.delete("/{contract_id}/milestones/{milestone_id}", response_model=ContractOut, operation_id="deleteMilestone", summary="Remove a milestone from a draft contract (client)")
async def delete_milestone(
    contract_id: str,
    milestone_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> ContractOut:
    return await svc.delete_milestone(conn, ctx, lang, contract_id=contract_id, milestone_id=milestone_id)


@router.post("/{contract_id}/milestones/{milestone_id}/fund", response_model=FundingOut, operation_id="fundMilestone", summary="Open the checkout that funds a milestone (client)")
async def fund_milestone(
    contract_id: str,
    milestone_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> FundingOut:
    return await svc.fund_milestone(conn, ctx, lang, contract_id=contract_id, milestone_id=milestone_id)


@router.post("/{contract_id}/milestones/{milestone_id}/submit", response_model=ContractOut, operation_id="submitMilestone", summary="Submit a funded milestone for approval (provider)")
async def submit_milestone(
    contract_id: str,
    milestone_id: str,
    lang: Locale,
    body: SubmitIn | None = None,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> ContractOut:
    return await svc.submit_milestone(conn, ctx, lang, contract_id=contract_id, milestone_id=milestone_id, body=body or SubmitIn())


@router.post("/{contract_id}/milestones/{milestone_id}/approve", response_model=ContractOut, operation_id="approveMilestone", summary="Approve a submitted milestone and release it (client)")
async def approve_milestone(
    contract_id: str,
    milestone_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> ContractOut:
    return await svc.approve_milestone(conn, ctx, lang, contract_id=contract_id, milestone_id=milestone_id)


@router.post("/{contract_id}/milestones/{milestone_id}/reject", response_model=ContractOut, operation_id="rejectMilestone", summary="Send a submitted milestone back with a note (client)")
async def reject_milestone(
    contract_id: str,
    milestone_id: str,
    body: RejectIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> ContractOut:
    return await svc.reject_milestone(conn, ctx, lang, contract_id=contract_id, milestone_id=milestone_id, body=body)


# --- disputes -----------------------------------------------------------------
@router.post("/{contract_id}/disputes", status_code=201, response_model=ContractOut, operation_id="openDispute", summary="Open a dispute on an active contract (either party)")
async def open_dispute(
    contract_id: str,
    body: DisputeIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> ContractOut:
    return await svc.open_dispute(conn, ctx, lang, contract_id=contract_id, body=body)


@router.post("/{contract_id}/disputes/{dispute_id}/resolve", response_model=ContractOut, operation_id="resolveContractDispute", summary="Record a dispute outcome (moderation operators)")
async def resolve_dispute(
    contract_id: str,
    dispute_id: str,
    body: DisputeResolveIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> ContractOut:
    return await svc.resolve_dispute(conn, ctx, lang, contract_id=contract_id, dispute_id=dispute_id, body=body)


# --- timesheets (hourly contracts) -------------------------------------------
@router.post("/{contract_id}/timesheets", status_code=201, response_model=ContractOut, operation_id="submitTimesheet", summary="Submit a week's hours on an hourly contract (provider)")
async def submit_timesheet(
    contract_id: str,
    body: TimesheetIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> ContractOut:
    return await svc.submit_timesheet(conn, ctx, lang, contract_id=contract_id, body=body)


@router.post("/{contract_id}/timesheets/{timesheet_id}/approve", response_model=FundingOut, operation_id="approveTimesheet", summary="Approve a timesheet and open the checkout that pays it (client)")
async def approve_timesheet(
    contract_id: str,
    timesheet_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> FundingOut:
    return await svc.approve_timesheet(conn, ctx, lang, contract_id=contract_id, timesheet_id=timesheet_id)


@router.post("/{contract_id}/timesheets/{timesheet_id}/reject", response_model=ContractOut, operation_id="rejectTimesheet", summary="Send a timesheet back with a note (client)")
async def reject_timesheet(
    contract_id: str,
    timesheet_id: str,
    body: RejectIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> ContractOut:
    return await svc.reject_timesheet(conn, ctx, lang, contract_id=contract_id, timesheet_id=timesheet_id, body=body)

"""Operations endpoints — the moderator review queue (DEC-V1-007/DEC-V1-028).

`GET /operations/me` answers for ANY signed-in member (roles may be empty);
everything else requires the `moderator` role via `OperatorAccount`, which
binds `mangaly.operator_role` for the request. A non-operator gets 404.

Every action is audited in the same transaction (components/audit_bridge).
"""

from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.deps import AuthenticatedSession, DbSession, Locale
from app.api.operator_deps import Moderator
from app.components.operations import interface as operations
from app.components.profile import interface as profile
from app.components.safety import interface as safety
from app.i18n import translate

router = APIRouter(prefix="/operations", tags=["operations"])


class OperatorMeResponse(BaseModel):
    is_operator: bool
    roles: list[str]


@router.get("/me", response_model=OperatorMeResponse)
async def operator_me(caller: AuthenticatedSession, session: DbSession) -> OperatorMeResponse:
    roles = await operations.operator_roles(session, caller.account_id)
    return OperatorMeResponse(is_operator=bool(roles), roles=roles)


class PersonOut(BaseModel):
    account_id: str | None
    name: str | None
    photo_url: str | None = None
    suspended: bool = False


class CaseOut(BaseModel):
    case_id: str
    state: Literal["open", "acknowledged", "resolved"]
    status: str
    tier: int
    category: str
    source: str
    description: str | None
    has_evidence: bool
    signal_type: str | None
    created_at: str
    acknowledge_by: str | None
    resolve_by: str | None
    acknowledged_at: str | None
    resolved_at: str | None
    outcome: str | None
    reopened_count: int
    sla_breached: bool
    sla_deadline: str | None
    paged: bool
    reporter: PersonOut
    reported: PersonOut


class ActionOut(BaseModel):
    action: str
    operator_account_id: str
    at: str
    note: str | None


class CaseDetailOut(CaseOut):
    evidence: list[dict[str, Any]]
    resolution_note: str | None
    rationale: str | None
    taxonomy_version: str | None
    signal_metadata: dict[str, Any] | None
    paging_events: list[dict[str, Any]]
    csam_packet_status: str | None
    decisions: list[ActionOut]


def _iso(value: Any) -> str | None:
    return value.isoformat() if value is not None else None


def _case(summary: operations.CaseSummary) -> CaseOut:
    system = summary.reporter_account_id == safety.SYSTEM_REPORTER_ID
    return CaseOut(
        case_id=str(summary.case_id),
        state=summary.state,  # type: ignore[arg-type]
        status=summary.status,
        tier=summary.tier,
        category=summary.category,
        source=summary.source,
        description=summary.description,
        has_evidence=summary.has_evidence,
        signal_type=summary.signal_type,
        created_at=summary.created_at.isoformat(),
        acknowledge_by=_iso(summary.acknowledge_by),
        resolve_by=_iso(summary.resolve_by),
        acknowledged_at=_iso(summary.acknowledged_at),
        resolved_at=_iso(summary.resolved_at),
        outcome=summary.outcome,
        reopened_count=summary.reopened_count,
        sla_breached=summary.sla_breached,
        sla_deadline=_iso(summary.sla_deadline),
        paged=summary.paged,
        reporter=PersonOut(
            account_id=None if system else str(summary.reporter_account_id),
            name=None if system else summary.reporter_name,
        ),
        reported=PersonOut(
            account_id=str(summary.reported_account_id) if summary.reported_account_id else None,
            name=summary.reported_name,
            photo_url=(
                profile.resolve_photo_url(summary.reported_photo_ref) if summary.reported_photo_ref else None
            ),
            suspended=summary.reported_suspended,
        ),
    )


@router.get("/cases", response_model=list[CaseOut])
async def list_cases(
    session: DbSession,
    operator: Moderator,
    state: Literal["open", "acknowledged", "resolved"] | None = Query(default=None),
    tier: int | None = Query(default=None, ge=1, le=4),
) -> list[CaseOut]:
    """[SP063] The queue. Never filters on the absence of a detection signal."""
    return [_case(c) for c in await operations.list_cases(session, state=state, tier=tier)]


@router.get("/cases/{case_id}", response_model=CaseDetailOut)
async def get_case(case_id: UUID, session: DbSession, operator: Moderator) -> CaseDetailOut:
    return await _detail(session, case_id)


class NoteBody(BaseModel):
    note: str | None = Field(default=None, max_length=4000)


class ResolveBody(NoteBody):
    outcome: str = Field(min_length=1, max_length=64)


def _not_changed(lang: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT, detail=translate("safety.ops.error.notChanged", lang)
    )


async def _detail(session: DbSession, case_id: UUID) -> CaseDetailOut:
    detail = await operations.get_case(session, case_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return _to_detail(detail)


def _to_detail(detail: operations.CaseDetail) -> CaseDetailOut:
    base = _case(detail.summary)
    return CaseDetailOut(
        **base.model_dump(),
        evidence=detail.evidence,
        resolution_note=detail.resolution_note,
        rationale=detail.rationale,
        taxonomy_version=detail.taxonomy_version,
        signal_metadata=detail.signal_metadata,
        paging_events=detail.paging_events,
        csam_packet_status=detail.csam_packet_status,
        decisions=[
            ActionOut(
                action=d.action,
                operator_account_id=str(d.operator_account_id),
                at=d.at.isoformat(),
                note=d.note,
            )
            for d in detail.decisions
        ],
    )


@router.post("/cases/{case_id}/acknowledge", response_model=CaseDetailOut)
async def acknowledge(
    case_id: UUID, session: DbSession, operator: Moderator, lang: Locale
) -> CaseDetailOut:
    try:
        await operations.acknowledge(session, case_id=case_id, operator_account_id=operator.account_id)
    except operations.NotChanged as exc:
        raise _not_changed(lang) from exc
    return await _detail(session, case_id)


@router.post("/cases/{case_id}/resolve", response_model=CaseDetailOut)
async def resolve(
    case_id: UUID, body: ResolveBody, session: DbSession, operator: Moderator, lang: Locale
) -> CaseDetailOut:
    if body.outcome == "account_suspended":
        detail = await operations.get_case(session, case_id)
        if detail is None or detail.summary.reported_account_id is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        try:
            await operations.suspend_reported_account(
                session,
                case_id=case_id,
                reported_account_id=detail.summary.reported_account_id,
                operator_account_id=operator.account_id,
                reason=body.note,
            )
        except operations.NotChanged as exc:
            raise _not_changed(lang) from exc
        return await _detail(session, case_id)
    try:
        await operations.resolve(
            session,
            case_id=case_id,
            operator_account_id=operator.account_id,
            outcome=body.outcome,
            note=body.note,
        )
    except operations.InvalidOutcome as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=translate("safety.ops.error.invalidOutcome", lang),
        ) from exc
    except operations.NotChanged as exc:
        raise _not_changed(lang) from exc
    return await _detail(session, case_id)


@router.post("/cases/{case_id}/reopen", response_model=CaseDetailOut)
async def reopen(
    case_id: UUID, body: NoteBody, session: DbSession, operator: Moderator, lang: Locale
) -> CaseDetailOut:
    try:
        await operations.reopen(
            session, case_id=case_id, operator_account_id=operator.account_id, note=body.note
        )
    except operations.NotChanged as exc:
        raise _not_changed(lang) from exc
    return await _detail(session, case_id)


@router.post("/cases/{case_id}/suspend", response_model=CaseDetailOut)
async def suspend(
    case_id: UUID, body: NoteBody, session: DbSession, operator: Moderator, lang: Locale
) -> CaseDetailOut:
    """Suspend the reported account and resolve the case as `account_suspended`."""
    detail = await operations.get_case(session, case_id)
    if detail is None or detail.summary.reported_account_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    try:
        await operations.suspend_reported_account(
            session,
            case_id=case_id,
            reported_account_id=detail.summary.reported_account_id,
            operator_account_id=operator.account_id,
            reason=body.note,
        )
    except operations.NotChanged as exc:
        raise _not_changed(lang) from exc
    return await _detail(session, case_id)


@router.post("/cases/{case_id}/lift-suspension", response_model=CaseDetailOut)
async def lift_suspension(
    case_id: UUID, session: DbSession, operator: Moderator, lang: Locale
) -> CaseDetailOut:
    detail = await operations.get_case(session, case_id)
    if detail is None or detail.summary.reported_account_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    try:
        await operations.lift_suspension(
            session,
            case_id=case_id,
            account_id=detail.summary.reported_account_id,
            operator_account_id=operator.account_id,
        )
    except operations.NotChanged as exc:
        raise _not_changed(lang) from exc
    return await _detail(session, case_id)


class SweepOut(BaseModel):
    opened: int


@router.post("/sweeps/minor-profiles", response_model=SweepOut)
async def sweep_minor_profiles(session: DbSession, operator: Moderator) -> SweepOut:
    """[Minor safety] Flag every profile whose date of birth is under 18 (Tier 4)."""
    opened = await safety.sweep_underage_profiles(session)
    return SweepOut(opened=len(opened))

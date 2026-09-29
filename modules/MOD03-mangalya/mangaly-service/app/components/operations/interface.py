"""Operations — public interface (the moderator review queue).

[BR16/DEC-V1-007/DEC-V1-028] Intake → triage → investigation → decision →
resolution on `mangaly_operations.case`, driven by the SECURITY DEFINER
functions migration 048 added. Every function here that changes a case
audits it through the Audit Bridge in the same transaction.

Callers are operator requests: `api/operator_deps.py` has already bound
`mangaly.operator_role`, which the SQL functions check again themselves.

[SP063] `list_cases()` never filters on the absence of a detection signal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Final
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.audit_bridge import interface as audit

__all__ = [
    "CASE_OUTCOMES",
    "CaseAction",
    "CaseDetail",
    "CaseSummary",
    "InvalidOutcome",
    "NotChanged",
    "acknowledge",
    "get_case",
    "is_suspended",
    "lift_suspension",
    "list_cases",
    "operator_roles",
    "reopen",
    "resolve",
    "suspend_reported_account",
]

CASE_OUTCOMES: Final[tuple[str, ...]] = (
    "no_action",
    "warned",
    "content_removed",
    "account_suspended",
    "escalated_to_investigation",
)

# Application role → the `mangaly.operator_role` value the RLS policies read.
ROLE_TO_DB_ROLE: Final[dict[str, str]] = {
    "moderator": "operations",
    "operations": "operations",
    "safety_investigator": "safety_case_investigation",
}


class InvalidOutcome(Exception):
    """Outcome is not one of `CASE_OUTCOMES`."""


class NotChanged(Exception):
    """The case was not in a state that allows this action (or does not exist)."""


@dataclass(frozen=True, slots=True)
class CaseSummary:
    case_id: UUID
    status: str  # raw DB status
    state: str  # open | acknowledged | resolved
    tier: int
    created_at: datetime
    acknowledge_by: datetime | None
    resolve_by: datetime | None
    acknowledged_at: datetime | None
    resolved_at: datetime | None
    outcome: str | None
    reopened_count: int
    report_id: UUID
    category: str
    source: str
    description: str | None
    has_evidence: bool
    signal_type: str | None
    reporter_account_id: UUID
    reporter_name: str | None
    reported_account_id: UUID | None
    reported_name: str | None
    reported_photo_ref: str | None
    reported_suspended: bool
    paged: bool
    sla_breached: bool
    sla_deadline: datetime | None


@dataclass(frozen=True, slots=True)
class CaseAction:
    action: str
    operator_account_id: UUID
    at: datetime
    note: str | None


@dataclass(frozen=True, slots=True)
class CaseDetail:
    summary: CaseSummary
    evidence: list[dict[str, Any]] = field(default_factory=list)
    resolution_note: str | None = None
    rationale: str | None = None
    taxonomy_version: str | None = None
    signal_metadata: dict[str, Any] | None = None
    paging_events: list[dict[str, Any]] = field(default_factory=list)
    csam_packet_status: str | None = None
    decisions: list[CaseAction] = field(default_factory=list)


_OPEN_STATUSES = {"intake", "triage"}
_RESOLVED_STATUSES = {"resolved"}


def _state(status: str) -> str:
    if status in _OPEN_STATUSES:
        return "open"
    if status in _RESOLVED_STATUSES:
        return "resolved"
    return "acknowledged"


def _sla(row: Any, now: datetime) -> tuple[bool, datetime | None]:
    """[SP065] Breach is judged against the deadline still outstanding: the
    acknowledge deadline until acknowledged, then the resolve deadline until
    resolved. A resolved case is breached only if it was resolved late."""
    if row.status in _RESOLVED_STATUSES:
        late = bool(row.resolve_by and row.resolved_at and row.resolved_at > row.resolve_by)
        return late, row.resolve_by
    if row.acknowledged_at is None:
        deadline = row.acknowledge_by or row.resolve_by
    else:
        deadline = row.resolve_by
    return bool(deadline and now > deadline), deadline


def _summary(row: Any, now: datetime) -> CaseSummary:
    breached, deadline = _sla(row, now)
    return CaseSummary(
        case_id=row.case_id,
        status=row.status,
        state=_state(row.status),
        tier=int(row.tier or 2),
        created_at=row.created_at,
        acknowledge_by=row.acknowledge_by,
        resolve_by=row.resolve_by,
        acknowledged_at=row.acknowledged_at,
        resolved_at=row.resolved_at,
        outcome=row.outcome,
        reopened_count=int(row.reopened_count or 0),
        report_id=row.report_id,
        category=row.category,
        source=row.source,
        description=row.description,
        has_evidence=bool(row.has_evidence),
        signal_type=row.signal_type,
        reporter_account_id=row.reporter_account_id,
        reporter_name=row.reporter_name,
        reported_account_id=row.reported_account_id,
        reported_name=row.reported_name,
        reported_photo_ref=row.reported_photo_ref,
        reported_suspended=bool(row.reported_suspended),
        paged=bool(row.paged),
        sla_breached=breached,
        sla_deadline=deadline,
    )


async def operator_roles(session: AsyncSession, account_id: UUID) -> list[str]:
    rows = (
        await session.execute(
            text("SELECT mangaly_operations.operator_roles(:id)"), {"id": account_id}
        )
    ).scalar_one()
    return list(rows or [])


async def is_suspended(session: AsyncSession, account_id: UUID) -> bool:
    return bool(
        (
            await session.execute(
                text("SELECT mangaly_operations.is_suspended(:id)"), {"id": account_id}
            )
        ).scalar_one()
    )


async def list_cases(
    session: AsyncSession, *, state: str | None = None, tier: int | None = None
) -> list[CaseSummary]:
    """The queue, most urgent first. `state` ∈ open | acknowledged | resolved."""
    rows = await session.execute(
        text("SELECT * FROM mangaly_operations.safety_queue(:state, :tier)"),
        {"state": state, "tier": tier},
    )
    now = datetime.now(UTC)
    return [_summary(r, now) for r in rows]


async def get_case(session: AsyncSession, case_id: UUID) -> CaseDetail | None:
    row = (
        await session.execute(
            text(
                "SELECT * FROM mangaly_operations.safety_queue(NULL, NULL) q WHERE q.case_id = :id"
            ),
            {"id": case_id},
        )
    ).first()
    if row is None:
        return None
    now = datetime.now(UTC)
    summary = _summary(row, now)

    extra = (
        await session.execute(
            text(
                """
                SELECT r.evidence, c.resolution_note, sc.rationale, sc.taxonomy_version
                  FROM mangaly_operations.case c
                  JOIN mangaly_safety.report r ON r.id = c.source_reference_id
                  LEFT JOIN mangaly_safety.severity_classification sc ON sc.case_id = c.id
                 WHERE c.id = :id
                """
            ),
            {"id": case_id},
        )
    ).first()
    signal_meta = (
        await session.execute(
            text(
                """
                SELECT ds.metadata FROM mangaly_safety.detection_signal ds
                  JOIN mangaly_safety.report r
                    ON (ds.metadata ->> 'message_id')::uuid = r.reported_message_id
                    OR (r.reported_message_id IS NULL AND ds.conversation_id IS NULL
                        AND (ds.metadata ->> 'account_id')::uuid = r.reported_profile_id)
                 WHERE r.id = :rid AND r.source = 'automated'
                 ORDER BY ds.detected_at DESC LIMIT 1
                """
            ),
            {"rid": summary.report_id},
        )
    ).scalar_one_or_none()
    pages = (
        await session.execute(
            text(
                "SELECT id, tier, vendor, dispatch_status, paged_at, acknowledged_at "
                "FROM mangaly_operations.paging_event WHERE case_id = :id ORDER BY paged_at"
            ),
            {"id": case_id},
        )
    ).mappings().all()
    packet = (
        await session.execute(
            text(
                "SELECT dispatch_status FROM mangaly_operations.csam_report_packet "
                "WHERE case_id = :id ORDER BY submitted_at DESC LIMIT 1"
            ),
            {"id": case_id},
        )
    ).scalar_one_or_none()
    decisions = (
        await session.execute(
            text(
                "SELECT decision_type, decided_by_operator_id, rationale_text, decided_at "
                "FROM mangaly_operations.case_decision WHERE case_id = :id ORDER BY decided_at"
            ),
            {"id": case_id},
        )
    ).all()

    evidence_raw = extra.evidence if extra is not None else None
    evidence: list[dict[str, Any]] = list(evidence_raw) if isinstance(evidence_raw, list) else []
    return CaseDetail(
        summary=summary,
        evidence=evidence,
        resolution_note=extra.resolution_note if extra is not None else None,
        rationale=extra.rationale if extra is not None else None,
        taxonomy_version=extra.taxonomy_version if extra is not None else None,
        signal_metadata=dict(signal_meta) if isinstance(signal_meta, dict) else None,
        paging_events=[
            {
                "id": str(p["id"]),
                "tier": int(p["tier"]),
                "vendor": p["vendor"],
                "dispatch_status": p["dispatch_status"],
                "paged_at": p["paged_at"].isoformat(),
            }
            for p in pages
        ],
        csam_packet_status=packet,
        decisions=[
            CaseAction(
                action=str(d.decision_type),
                operator_account_id=d.decided_by_operator_id,
                at=d.decided_at,
                note=d.rationale_text,
            )
            for d in decisions
        ],
    )


async def acknowledge(session: AsyncSession, *, case_id: UUID, operator_account_id: UUID) -> None:
    changed = (
        await session.execute(
            text("SELECT mangaly_operations.acknowledge_case(:c, :o)"),
            {"c": case_id, "o": operator_account_id},
        )
    ).scalar_one()
    if not changed:
        raise NotChanged
    await audit.record_operator_action(
        session, operator_account_id=operator_account_id, action="acknowledge", case_id=case_id
    )


async def resolve(
    session: AsyncSession,
    *,
    case_id: UUID,
    operator_account_id: UUID,
    outcome: str,
    note: str | None,
) -> None:
    if outcome not in CASE_OUTCOMES:
        raise InvalidOutcome
    changed = (
        await session.execute(
            text("SELECT mangaly_operations.resolve_case(:c, :o, :outcome, :note)"),
            {"c": case_id, "o": operator_account_id, "outcome": outcome, "note": note},
        )
    ).scalar_one()
    if not changed:
        raise NotChanged
    await audit.record_operator_action(
        session,
        operator_account_id=operator_account_id,
        action="resolve",
        case_id=case_id,
        details={"outcome": outcome, "has_note": bool(note)},
    )


async def reopen(
    session: AsyncSession, *, case_id: UUID, operator_account_id: UUID, note: str | None
) -> None:
    changed = (
        await session.execute(
            text("SELECT mangaly_operations.reopen_case(:c, :o, :note)"),
            {"c": case_id, "o": operator_account_id, "note": note},
        )
    ).scalar_one()
    if not changed:
        raise NotChanged
    await audit.record_operator_action(
        session, operator_account_id=operator_account_id, action="reopen", case_id=case_id
    )


async def suspend_reported_account(
    session: AsyncSession,
    *,
    case_id: UUID,
    reported_account_id: UUID,
    operator_account_id: UUID,
    reason: str | None,
) -> UUID:
    """Suspend the reported account (idempotent) and, in the same transaction,
    resolve the case with outcome `account_suspended`."""
    suspension_id = (
        await session.execute(
            text("SELECT mangaly_operations.suspend_account(:a, :c, :o, :r)"),
            {"a": reported_account_id, "c": case_id, "o": operator_account_id, "r": reason},
        )
    ).scalar_one_or_none()
    if suspension_id is None:
        raise NotChanged
    await session.execute(
        text("SELECT mangaly_operations.resolve_case(:c, :o, 'account_suspended', :note)"),
        {"c": case_id, "o": operator_account_id, "note": reason},
    )
    await audit.record_operator_action(
        session,
        operator_account_id=operator_account_id,
        action="suspend_account",
        case_id=case_id,
        details={"suspended_account_id": str(reported_account_id), "suspension_id": str(suspension_id)},
    )
    return suspension_id


async def lift_suspension(
    session: AsyncSession, *, case_id: UUID, account_id: UUID, operator_account_id: UUID
) -> None:
    changed = (
        await session.execute(
            text("SELECT mangaly_operations.lift_suspension(:a, :o)"),
            {"a": account_id, "o": operator_account_id},
        )
    ).scalar_one()
    if not changed:
        raise NotChanged
    await audit.record_operator_action(
        session,
        operator_account_id=operator_account_id,
        action="lift_suspension",
        case_id=case_id,
        details={"account_id": str(account_id)},
    )

"""Safety — public interface (block and report).

`/MODULE-ARCHITECTURE-STANDARD.md` §3: this is the only way other components
reach `mangaly_safety` state.

[Rework contract §3, 2026-09-17] `POST/DELETE /safety/block/{id}` and
`POST /safety/report`. A block is private to the blocker (RLS) but its
EFFECT is read from both sides through two narrow SECURITY DEFINER functions
(migration 033): Discovery, every list and the connection-request gate call
`blocked_ids()` / `is_blocked_between()` so a blocked person vanishes from
both sides. `report()` writes the existing `mangaly_safety.report` row
(TR063's universal entry point); `reported_profile_id` holds the reported
person's ACCOUNT id, like every other people column in this module.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.safety import detection
from app.config import safety_taxonomy
from app.events import bus

__all__ = [
    "REPORT_REASONS",
    "BlockSummary",
    "CannotBlockSelf",
    "InvalidReason",
    "block",
    "blocked_ids",
    "classify_and_escalate",
    "is_blocked_between",
    "list_blocks",
    "report",
    "scan_message",
    "unblock",
]

# DEC-V1-006's user-facing taxonomy, kept small and plain.
REPORT_REASONS: Final[tuple[str, ...]] = (
    "harassment",
    "fake_profile",
    "inappropriate_content",
    "scam_or_money",
    "already_married",
    "underage",
    "other",
)


class CannotBlockSelf(Exception):
    """An account cannot block itself."""


class InvalidReason(Exception):
    """The report reason is not one of `REPORT_REASONS`."""


@dataclass(frozen=True, slots=True)
class BlockSummary:
    blocked_account_id: UUID
    created_at: datetime


async def block(session: AsyncSession, *, blocker_account_id: UUID, blocked_account_id: UUID) -> None:
    if blocker_account_id == blocked_account_id:
        raise CannotBlockSelf
    await session.execute(
        text(
            "INSERT INTO mangaly_safety.block (id, blocker_account_id, blocked_account_id) "
            "VALUES (:id, :blocker, :blocked) "
            "ON CONFLICT (blocker_account_id, blocked_account_id) DO NOTHING"
        ),
        {"id": uuid4(), "blocker": blocker_account_id, "blocked": blocked_account_id},
    )
    # A pending request in either direction is withdrawn/declined implicitly:
    # nothing between the two may remain actionable.
    await session.execute(
        text(
            """
            UPDATE mangaly_connection.connection_request
               SET status = CASE WHEN subject_account_id = :blocker THEN 'withdrawn'
                                 ELSE 'declined' END::mangaly_connection.connection_status,
                   decided_at = now(), decided_by_account_id = :blocker, updated_at = now()
             WHERE status = 'pending'
               AND ((subject_account_id = :blocker AND target_profile_id = :blocked)
                    OR (subject_account_id = :blocked AND target_profile_id = :blocker))
            """
        ),
        {"blocker": blocker_account_id, "blocked": blocked_account_id},
    )
    await bus.publish(
        session,
        schema="mangaly_safety",
        aggregate_id=blocker_account_id,
        event_type="MemberBlocked",
        payload={"blocker_account_id": str(blocker_account_id), "blocked_account_id": str(blocked_account_id)},
    )


async def unblock(session: AsyncSession, *, blocker_account_id: UUID, blocked_account_id: UUID) -> bool:
    result = await session.execute(
        text(
            "DELETE FROM mangaly_safety.block "
            "WHERE blocker_account_id = :blocker AND blocked_account_id = :blocked"
        ),
        {"blocker": blocker_account_id, "blocked": blocked_account_id},
    )
    removed = bool(result.rowcount)
    if removed:
        await bus.publish(
            session,
            schema="mangaly_safety",
            aggregate_id=blocker_account_id,
            event_type="MemberUnblocked",
            payload={
                "blocker_account_id": str(blocker_account_id),
                "blocked_account_id": str(blocked_account_id),
            },
        )
    return removed


async def list_blocks(session: AsyncSession, *, blocker_account_id: UUID) -> list[BlockSummary]:
    rows = await session.execute(
        text(
            "SELECT blocked_account_id, created_at FROM mangaly_safety.block "
            "WHERE blocker_account_id = :blocker ORDER BY created_at DESC"
        ),
        {"blocker": blocker_account_id},
    )
    return [BlockSummary(blocked_account_id=r.blocked_account_id, created_at=r.created_at) for r in rows]


async def blocked_ids(session: AsyncSession, *, account_id: UUID) -> set[UUID]:
    """Everyone blocked by, or blocking, `account_id` — readable by that
    account and by a circle acting for it (`mangaly.authz_context` must be
    bound by `authz.resolve()` for the family case)."""
    rows = await session.execute(
        text("SELECT * FROM mangaly_safety.blocked_account_ids(:account_id)"),
        {"account_id": account_id},
    )
    return {r[0] for r in rows}


async def is_blocked_between(session: AsyncSession, a: UUID, b: UUID) -> bool:
    return bool(
        (
            await session.execute(
                text("SELECT mangaly_safety.is_blocked_between(:a, :b)"), {"a": a, "b": b}
            )
        ).scalar_one()
    )


async def report(
    session: AsyncSession,
    *,
    reporter_account_id: UUID,
    reported_account_id: UUID,
    reason: str,
    details: str | None,
) -> UUID:
    if reason not in REPORT_REASONS:
        raise InvalidReason
    report_id = uuid4()
    await session.execute(
        text(
            "INSERT INTO mangaly_safety.report "
            "(id, reporter_account_id, reported_profile_id, category, description, source) "
            "VALUES (:id, :reporter, :reported, :category, :description, 'user_reported')"
        ),
        {
            "id": report_id,
            "reporter": reporter_account_id,
            "reported": reported_account_id,
            "category": reason,
            "description": (details or "").strip()[:2000] or None,
        },
    )
    await bus.publish(
        session,
        schema="mangaly_safety",
        aggregate_id=report_id,
        event_type="ReportSubmitted",
        payload={
            "report_id": str(report_id),
            "reporter_account_id": str(reporter_account_id),
            "reported_account_id": str(reported_account_id),
            "category": reason,
        },
    )
    await classify_and_escalate(
        session,
        report_id=report_id,
        classification=safety_taxonomy.classify_report_reason(reason),
        category=reason,
        reported_account_id=reported_account_id,
    )
    return report_id


async def classify_and_escalate(
    session: AsyncSession,
    *,
    report_id: UUID,
    classification: safety_taxonomy.Classification,
    category: str,
    reported_account_id: UUID,
    conversation_id: UUID | None = None,
    message_id: UUID | None = None,
    signal_id: UUID | None = None,
) -> UUID | None:
    """[TR068/DEC-V1-006/DEC-V1-028] Classify a report the moment it exists
    (the SLA clock starts now, never at human pickup) and open its case in the
    moderator queue; Tier 3/4 pages on-call, a CSAM-channel Tier 4 also stores
    its packet. Every report — filed, thread or automated — goes through here,
    so none can sit unclassified outside the queue. Returns the case id."""
    from app.components.operations import escalation

    now = datetime.now(UTC)
    acknowledge_by = now + classification.acknowledge_within if classification.acknowledge_within is not None else None
    resolve_by = now + classification.resolve_within if classification.resolve_within is not None else None
    case_id = (
        await session.execute(
            text("SELECT mangaly_safety.classify_report(:r, :tier, :ack, :res, :ver, :why)"),
            {
                "r": report_id,
                "tier": int(classification.tier),
                "ack": acknowledge_by,
                "res": resolve_by,
                "ver": safety_taxonomy.TAXONOMY_VERSION,
                "why": classification.rationale,
            },
        )
    ).scalar_one_or_none()
    if case_id is None:
        return None
    if classification.pages_on_call:
        await escalation.page_for_case(
            session, case_id=case_id, tier=classification.tier, reference=category
        )
    if classification.csam_channel:
        await escalation.assemble_csam_packet(
            session,
            case_id=case_id,
            report_id=report_id,
            reported_account_id=reported_account_id,
            conversation_id=conversation_id,
            message_id=message_id,
            detection_signal_id=signal_id,
            detection_category=category,
            classified_at=now,
        )
    return case_id


async def scan_message(
    session: AsyncSession,
    *,
    message_id: UUID,
    conversation_id: UUID,
    sender_account_id: UUID,
    content: str,
) -> UUID | None:
    """[SP064/DEC-V1-028] Bounded text detection at send time, in the send's
    own transaction. Nothing matched: nothing is written. A match opens ONE
    automated report for the most severe signal (the others ride along in its
    metadata, so one message never floods the queue), classified at once.
    The signal records only its type and pattern class, never the text; the
    report's evidence keeps the thread for the human reviewer (migration 048).
    Returns the report id, or None when the message is clean."""
    signals = detection.scan_text(content)
    if not signals:
        return None
    top = signals[0]
    rule = safety_taxonomy.classify_signal(top.signal_type)
    row = (
        await session.execute(
            text(
                "SELECT report_id, signal_id FROM mangaly_safety.open_automated_report("
                ":conversation, :message, :sender, :signal_type, :category, CAST(:metadata AS jsonb))"
            ),
            {
                "conversation": conversation_id,
                "message": message_id,
                "sender": sender_account_id,
                "signal_type": top.signal_type,
                "category": rule.report_category,
                "metadata": json.dumps(
                    {
                        "pattern_class": top.pattern_class,
                        "also": [s.signal_type for s in signals[1:]],
                    }
                ),
            },
        )
    ).one()
    await classify_and_escalate(
        session,
        report_id=row.report_id,
        classification=rule.classification,
        category=rule.report_category,
        reported_account_id=sender_account_id,
        conversation_id=conversation_id,
        message_id=message_id,
        signal_id=row.signal_id,
    )
    await bus.publish(
        session,
        schema="mangaly_safety",
        aggregate_id=row.report_id,
        event_type="DetectionSignalRaised",
        payload={
            "report_id": str(row.report_id),
            "signal_id": str(row.signal_id),
            "signal_type": top.signal_type,
            "tier": int(rule.classification.tier),
        },
    )
    return row.report_id

"""Safety & Moderation — public interface (`milavn_safety`).

# [FR061, FR062, FR064, FR065, FR087, TR41, TR42, TR43, TR-PLAT-01] Report
# an activity/user/organization/content (audited, rate-limited, idempotent);
# block a member (enforced everywhere through the shared `is_blocked`
# helper); and the module-side moderation queue that consumes the shared
# Admin & Governance Console contract (manifest + list/detail/action
# endpoints) — never a standalone bespoke admin.
# Approach: every report publishes an audit event in the same transaction
# (outbox). Every moderation action is a human decision recorded in
# `moderation_action` with its own audit event; no code path here is
# reachable from a reputation signal or feedback (TR15/FR069).
# Traces to: TR41, TR42, TR43, TR-PLAT-01, TR15.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.events import bus

REPORT_SUBJECTS = ("activity", "occurrence", "user", "organization", "content")
REASONS = ("spam", "unsafe", "harassment", "misleading", "other")
ACTIONS = ("dismiss", "warn", "escalate", "restrict")
ACTION_TO_STATUS = {"dismiss": "dismissed", "warn": "actioned", "escalate": "in_review", "restrict": "actioned"}

ADMIN_VIEW_DESCRIPTOR = {
    "module_id": "milavn",
    "view_id": "moderation_queue",
    "title": "Milavn moderation",
    "nav_group": "moderation",
    "required_permission_scope": "milavn.moderate",
    "list_endpoint": "/milavn/admin/moderation",
    "detail_endpoint": "/milavn/admin/moderation/{item_id}",
    "action_endpoints": ["/milavn/admin/moderation/{item_id}/actions/{action_id}"],
}


class InvalidReport(Exception):
    def __init__(self, fields: list[str]) -> None:
        super().__init__(str(fields))
        self.fields = fields


class ReportNotFound(Exception):
    pass


@dataclass(frozen=True, slots=True)
class Report:
    id: UUID
    reporter_member_id: UUID
    subject_type: str
    subject_id: UUID
    reason_category: str
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime


_COLS = "id, reporter_member_id, subject_type::text, subject_id, reason_category, description, status::text, created_at, updated_at"


async def submit_report(session: AsyncSession, *, reporter_member_id: UUID, subject_type: str, subject_id: UUID, reason: str, description: str | None) -> Report:
    fields = []
    if subject_type not in REPORT_SUBJECTS:
        fields.append("subject_type")
    if reason not in REASONS:
        fields.append("reason_category")
    if fields:
        raise InvalidReport(fields)
    report_id = uuid4()
    await session.execute(
        text(
            "INSERT INTO milavn_safety.report (id, reporter_member_id, subject_type, subject_id, reason_category, description) "
            "VALUES (:id, :r, CAST(:st AS milavn_safety.report_subject_type), :sid, :reason, NULLIF(:d, ''))"
        ),
        {"id": str(report_id), "r": str(reporter_member_id), "st": subject_type, "sid": str(subject_id), "reason": reason, "d": (description or "").strip()},
    )
    # [TR41/IA061] Audit event in the same transaction — a dropped audit for a safety report is a compliance gap.
    await bus.publish(
        session,
        schema="milavn_safety",
        event_type="report.submitted",
        aggregate_id=report_id,
        payload={"report_id": report_id, "reporter_member_id": reporter_member_id, "subject_type": subject_type, "subject_id": subject_id},
    )
    return await get_report(session, report_id=report_id)


async def get_report(session: AsyncSession, *, report_id: UUID) -> Report:
    row = (await session.execute(text(f"SELECT {_COLS} FROM milavn_safety.report WHERE id = :id"), {"id": str(report_id)})).first()
    if row is None:
        raise ReportNotFound
    return Report(*row)


async def my_reports(session: AsyncSession, *, member_id: UUID) -> list[Report]:
    rows = (
        await session.execute(
            text(f"SELECT {_COLS} FROM milavn_safety.report WHERE reporter_member_id = :m ORDER BY created_at DESC"),
            {"m": str(member_id)},
        )
    ).all()
    return [Report(*r) for r in rows]


# --- Block (FR062) -------------------------------------------------------------


async def block(session: AsyncSession, *, blocking_member_id: UUID, blocked_member_id: UUID) -> None:
    if blocking_member_id == blocked_member_id:
        raise InvalidReport(["blocked_member_id"])
    await session.execute(
        text("INSERT INTO milavn_safety.block (blocking_member_id, blocked_member_id) VALUES (:a, :b) ON CONFLICT DO NOTHING"),
        {"a": str(blocking_member_id), "b": str(blocked_member_id)},
    )
    await bus.publish(
        session,
        schema="milavn_safety",
        event_type="member.blocked",
        aggregate_id=blocking_member_id,
        payload={"blocking_member_id": blocking_member_id, "blocked_member_id": blocked_member_id},
    )


async def unblock(session: AsyncSession, *, blocking_member_id: UUID, blocked_member_id: UUID) -> None:
    await session.execute(
        text("DELETE FROM milavn_safety.block WHERE blocking_member_id = :a AND blocked_member_id = :b"),
        {"a": str(blocking_member_id), "b": str(blocked_member_id)},
    )


async def my_blocks(session: AsyncSession, *, member_id: UUID) -> list[UUID]:
    rows = (await session.execute(text("SELECT blocked_member_id FROM milavn_safety.block WHERE blocking_member_id = :m"), {"m": str(member_id)})).all()
    return [r[0] for r in rows]


# --- Moderation queue (FR065, TR43, TR-PLAT-01 module side) ------------------


async def queue(session: AsyncSession, *, status: str | None) -> list[Report]:
    clause = "WHERE status = CAST(:s AS milavn_safety.report_status)" if status else ""
    rows = (await session.execute(text(f"SELECT {_COLS} FROM milavn_safety.report {clause} ORDER BY created_at DESC LIMIT 200"), {"s": status} if status else {})).all()
    return [Report(*r) for r in rows]


async def actions_for(session: AsyncSession, *, report_id: UUID) -> list[dict]:
    rows = (
        await session.execute(
            text("SELECT id, moderator_member_id, action_type::text, notes, created_at FROM milavn_safety.moderation_action WHERE report_id = :r ORDER BY created_at"),
            {"r": str(report_id)},
        )
    ).all()
    return [dict(r._mapping) for r in rows]


async def act(session: AsyncSession, *, report_id: UUID, moderator_member_id: UUID, action: str, notes: str | None) -> Report:
    """[TR43 §3] Every action is a human decision; audited from the owning module (TR-PLAT-01 §4)."""
    if action not in ACTIONS:
        raise InvalidReport(["action"])
    report = await get_report(session, report_id=report_id)
    await session.execute(
        text(
            "INSERT INTO milavn_safety.moderation_action (report_id, moderator_member_id, action_type, notes) "
            "VALUES (:r, :m, CAST(:a AS milavn_safety.moderation_action_type), NULLIF(:n, ''))"
        ),
        {"r": str(report_id), "m": str(moderator_member_id), "a": action, "n": (notes or "").strip()},
    )
    await session.execute(
        text("UPDATE milavn_safety.report SET status = CAST(:s AS milavn_safety.report_status), updated_at = now() WHERE id = :id"),
        {"s": ACTION_TO_STATUS[action], "id": str(report_id)},
    )
    await bus.publish(
        session,
        schema="milavn_safety",
        event_type="admin_action.milavn.moderation_queue",
        aggregate_id=report_id,
        payload={
            "report_id": report_id,
            "moderator_member_id": moderator_member_id,
            "action": action,
            "subject_type": report.subject_type,
            "subject_id": report.subject_id,
        },
    )
    return await get_report(session, report_id=report_id)

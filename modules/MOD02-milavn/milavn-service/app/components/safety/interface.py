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

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.events import bus

REPORT_SUBJECTS = ("activity", "occurrence", "user", "organization", "content")
REASONS = ("spam", "unsafe", "harassment", "misleading", "other", "women_only_misuse")  # [050] women_only_misuse: someone in a women-only circle who should not be
ACTIONS = ("dismiss", "warn", "escalate", "restrict")
REASON_CODE = re.compile(r"^[a-z0-9_.-]{1,64}$")  # mirrors moderation_action_reason_code_shape (045)
# [045] How long a report may wait for a human: safety reports within a day, the rest within three.
# No Milavn requirement fixes an SLA; these are the console's defaults until one does.
SLA_HOURS_SAFETY = 24
SLA_HOURS_DEFAULT = 72
SAFETY_REASONS = ("unsafe", "harassment")
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
    # [047] One open report per person per reported thing: a repeat returns the existing report.
    existing = (
        await session.execute(
            text(
                f"SELECT {_COLS} FROM milavn_safety.report WHERE reporter_member_id = :r AND subject_type = CAST(:st AS milavn_safety.report_subject_type) "
                "AND subject_id = :sid AND status IN ('open', 'in_review') AND duplicate_of IS NULL ORDER BY created_at LIMIT 1"
            ),
            {"r": str(reporter_member_id), "st": subject_type, "sid": str(subject_id)},
        )
    ).first()
    if existing is not None:
        return Report(*existing)
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


def due_at(report: Report) -> datetime:
    return report.created_at + timedelta(hours=SLA_HOURS_SAFETY if report.reason_category in SAFETY_REASONS else SLA_HOURS_DEFAULT)


@dataclass(frozen=True, slots=True)
class ReportGroup:
    """[047] One queue item per reported thing (and status): every report about it, from anyone."""

    lead: Report  # the earliest report; its id is the queue item id
    reports: tuple[Report, ...]

    @property
    def reporter_count(self) -> int:
        return len({r.reporter_member_id for r in self.reports})

    @property
    def report_count(self) -> int:
        return len(self.reports)

    @property
    def reasons(self) -> list[str]:
        return sorted({r.reason_category for r in self.reports})

    @property
    def is_safety(self) -> bool:
        return any(r.reason_category in SAFETY_REASONS for r in self.reports)

    @property
    def lead_reason(self) -> str:
        """The most serious reason: a safety reason when there is one, else the earliest report's."""
        safety_first = sorted((r for r in self.reports if r.reason_category in SAFETY_REASONS), key=lambda r: r.created_at)
        return safety_first[0].reason_category if safety_first else self.lead.reason_category

    @property
    def due_at(self) -> datetime:
        return min(due_at(r) for r in self.reports)


def group_reports(reports: list[Report]) -> list[ReportGroup]:
    buckets: dict[tuple, list[Report]] = {}
    for r in reports:
        buckets.setdefault((r.subject_type, r.subject_id, r.status), []).append(r)
    groups = []
    for items in buckets.values():
        items.sort(key=lambda r: (r.created_at, str(r.id)))
        groups.append(ReportGroup(lead=items[0], reports=tuple(items)))
    groups.sort(key=lambda g: max(r.created_at for r in g.reports), reverse=True)
    return groups


async def subject_title(session: AsyncSession, *, subject_type: str, subject_id: UUID) -> str | None:
    """A moderator-only human name for a reported activity, circle, post or organization (045)."""
    return (
        await session.execute(text("SELECT milavn_safety.moderation_subject_title(:t, :i)"), {"t": subject_type, "i": str(subject_id)})
    ).scalar_one_or_none()


async def member_summary(session: AsyncSession, *, member_id: UUID) -> dict | None:
    """Moderator-only facts about one person in Milavn (045); None when they never opened Milavn."""
    raw = (await session.execute(text("SELECT milavn_safety.member_admin_summary(:m)"), {"m": str(member_id)})).scalar_one_or_none()
    if isinstance(raw, str):
        import json

        raw = json.loads(raw)
    return raw


async def my_blocks(session: AsyncSession, *, member_id: UUID) -> list[UUID]:
    rows = (await session.execute(text("SELECT blocked_member_id FROM milavn_safety.block WHERE blocking_member_id = :m"), {"m": str(member_id)})).all()
    return [r[0] for r in rows]


# --- Moderation queue (FR065, TR43, TR-PLAT-01 module side) ------------------


async def queue(session: AsyncSession, *, status: str | None) -> list[Report]:
    clause = "WHERE status = CAST(:s AS milavn_safety.report_status)" if status else ""
    rows = (await session.execute(text(f"SELECT {_COLS} FROM milavn_safety.report {clause} ORDER BY created_at DESC LIMIT 1000"), {"s": status} if status else {})).all()
    return [Report(*r) for r in rows]


async def actions_for(session: AsyncSession, *, report_id: UUID) -> list[dict]:
    rows = (
        await session.execute(
            text("SELECT id, moderator_member_id, action_type::text, notes, created_at, reason_code FROM milavn_safety.moderation_action WHERE report_id = :r ORDER BY created_at"),
            {"r": str(report_id)},
        )
    ).all()
    return [dict(r._mapping) for r in rows]


async def act(
    session: AsyncSession, *, report_id: UUID, moderator_member_id: UUID, action: str, notes: str | None, reason_code: str | None = None
) -> Report:
    """[TR43 §3] Every action is a human decision; audited from the owning module (TR-PLAT-01 §4).
    `reason_code` (045) is the console's machine-readable why, e.g. 'spam.repeat' — kept with the action."""
    if action not in ACTIONS:
        raise InvalidReport(["action"])
    if reason_code is not None and not REASON_CODE.match(reason_code):
        raise InvalidReport(["reason_code"])
    report = await get_report(session, report_id=report_id)
    await session.execute(
        text(
            "INSERT INTO milavn_safety.moderation_action (report_id, moderator_member_id, action_type, notes, reason_code) "
            "VALUES (:r, :m, CAST(:a AS milavn_safety.moderation_action_type), NULLIF(:n, ''), :rc)"
        ),
        {"r": str(report_id), "m": str(moderator_member_id), "a": action, "n": (notes or "").strip(), "rc": reason_code},
    )
    # [047] Acting on a queue item settles every still-open report about the same thing.
    await session.execute(
        text(
            "UPDATE milavn_safety.report SET status = CAST(:s AS milavn_safety.report_status), updated_at = now() "
            "WHERE id = :id OR (subject_type = CAST(:st AS milavn_safety.report_subject_type) AND subject_id = :sid "
            "AND status = CAST(:cur AS milavn_safety.report_status) AND :cur IN ('open', 'in_review'))"
        ),
        {"s": ACTION_TO_STATUS[action], "id": str(report_id), "st": report.subject_type, "sid": str(report.subject_id), "cur": report.status},
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
            "reason_code": reason_code,
        },
    )
    return await get_report(session, report_id=report_id)

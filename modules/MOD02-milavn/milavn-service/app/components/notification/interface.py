"""Notification Dispatch (incl. inbox) — public interface (`milavn_notification`).

# [FR051-FR057, FR086, TR13, TR37] Milavn governs WHAT and WHEN to notify,
# classed Important / Useful / Social / Opportunity; delivery infrastructure
# is the platform's (ADR-006). Important is never suppressible.
# Approach: subscribers to the in-process bus react after each request's
# transaction commits; each delivery writes the member's inbox row AND a
# `notification_outbox` row (the transactional hand-off to the platform
# Notification & Communication Service) through the definer-owned
# `milavn_notification.deliver()` function, which also honours per-class
# preferences for every class except Important (FR051).
# Traces to: TR13, TR37, TR55, FR086.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.identity_bridge import interface as identity
from app.db.engine import get_process_session_factory
from app.events import bus
from app.events.bus import DomainEvent

CLASSES = ("important", "useful", "social", "opportunity")


@dataclass(frozen=True, slots=True)
class InboxEntry:
    id: UUID
    notification_class: str
    title: str
    body: str
    deep_link: str | None
    source_occurrence_id: UUID | None
    read_at: datetime | None
    created_at: datetime


async def deliver(
    session: AsyncSession,
    *,
    member_id: UUID,
    notification_class: str,
    title: str,
    body: str,
    deep_link: str | None,
    occurrence_id: UUID | None,
) -> None:
    await session.execute(
        text("SELECT milavn_notification.deliver(:m, :c, :t, :b, :d, :o)"),
        {
            "m": str(member_id),
            "c": notification_class,
            "t": title,
            "b": body,
            "d": deep_link,
            "o": str(occurrence_id) if occurrence_id else None,
        },
    )


async def inbox(session: AsyncSession, *, member_id: UUID, limit: int = 100) -> list[InboxEntry]:
    rows = (
        await session.execute(
            text(
                "SELECT id, notification_class::text, title, body, deep_link, source_occurrence_id, read_at, created_at "
                "FROM milavn_notification.notification_inbox_entry WHERE member_id = :m ORDER BY created_at DESC LIMIT :l"
            ),
            {"m": str(member_id), "l": limit},
        )
    ).all()
    return [InboxEntry(*r) for r in rows]


async def unread_count(session: AsyncSession, *, member_id: UUID) -> int:
    return int(
        (
            await session.execute(
                text("SELECT count(*) FROM milavn_notification.notification_inbox_entry WHERE member_id = :m AND read_at IS NULL"),
                {"m": str(member_id)},
            )
        ).scalar_one()
    )


async def mark_read(session: AsyncSession, *, member_id: UUID, entry_id: UUID | None) -> None:
    if entry_id is None:
        await session.execute(
            text("UPDATE milavn_notification.notification_inbox_entry SET read_at = now() WHERE member_id = :m AND read_at IS NULL"),
            {"m": str(member_id)},
        )
    else:
        await session.execute(
            text("UPDATE milavn_notification.notification_inbox_entry SET read_at = now() WHERE member_id = :m AND id = :id"),
            {"m": str(member_id), "id": str(entry_id)},
        )


async def dismiss(session: AsyncSession, *, member_id: UUID, entry_id: UUID) -> None:
    await session.execute(
        text("DELETE FROM milavn_notification.notification_inbox_entry WHERE member_id = :m AND id = :id"),
        {"m": str(member_id), "id": str(entry_id)},
    )


async def preferences(session: AsyncSession, *, member_id: UUID) -> dict[str, dict]:
    rows = (
        await session.execute(
            text("SELECT notification_class::text, muted, frequency_setting FROM milavn_notification.notification_preference WHERE member_id = :m"),
            {"m": str(member_id)},
        )
    ).all()
    prefs = {c: {"muted": False, "frequency": "immediate"} for c in CLASSES}
    for r in rows:
        prefs[r[0]] = {"muted": bool(r[1]), "frequency": r[2] or "immediate"}
    prefs["important"] = {"muted": False, "frequency": "immediate", "locked": True}
    return prefs


async def set_preference(session: AsyncSession, *, member_id: UUID, notification_class: str, muted: bool, frequency: str | None) -> None:
    if notification_class not in CLASSES or notification_class == "important":
        raise ValueError(notification_class)  # [FR051] Important is never mutable.
    await session.execute(
        text(
            """
            INSERT INTO milavn_notification.notification_preference (member_id, notification_class, muted, frequency_setting)
            VALUES (:m, CAST(:c AS milavn_notification.notification_class), :muted, :freq)
            ON CONFLICT (member_id, notification_class) DO UPDATE
              SET muted = EXCLUDED.muted, frequency_setting = EXCLUDED.frequency_setting, updated_at = now()
            """
        ),
        {"m": str(member_id), "c": notification_class, "muted": muted, "freq": frequency},
    )


# --- Subscribers (in-process bus, run after commit) --------------------------


async def _occurrence_brief(session: AsyncSession, occurrence_id: UUID) -> tuple[str, str, list[UUID], UUID] | None:
    # Dispatcher transactions have no acting member; read through the
    # definer-owned brief (migration 004) rather than widening any policy.
    row = (
        await session.execute(
            text("SELECT title, canonical_url_slug, creator_member_id FROM milavn_activity.occurrence_brief(:o)"),
            {"o": str(occurrence_id)},
        )
    ).first()
    if row is None:
        return None
    ids = (await session.execute(text("SELECT milavn_activity.participant_member_ids(:o)"), {"o": str(occurrence_id)})).scalar_one()
    return row[0], row[1], list(ids or []), row[2]


async def _on_cancelled(event: DomainEvent) -> None:
    factory = get_process_session_factory()
    async with factory() as s, s.begin():
        brief = await _occurrence_brief(s, event.aggregate_id)
        if brief is None:
            return
        title, slug, members, _creator = brief
        for m in members:
            await deliver(
                s,
                member_id=m,
                notification_class="important",
                title=f"Cancelled: {title}",
                body="The organizer cancelled this activity. Sorry about that — we'll show you alternatives nearby.",
                deep_link=f"/a/{slug}",
                occurrence_id=event.aggregate_id,
            )


async def _on_updated(event: DomainEvent) -> None:
    if not event.payload.get("material"):
        return
    factory = get_process_session_factory()
    async with factory() as s, s.begin():
        brief = await _occurrence_brief(s, event.aggregate_id)
        if brief is None:
            return
        title, slug, members, _creator = brief
        for m in members:
            await deliver(
                s,
                member_id=m,
                notification_class="important",
                title=f"Time or place changed: {title}",
                body="Check the new details before you head out.",
                deep_link=f"/a/{slug}",
                occurrence_id=event.aggregate_id,
            )


async def _on_announcement(event: DomainEvent) -> None:
    factory = get_process_session_factory()
    async with factory() as s, s.begin():
        brief = await _occurrence_brief(s, event.aggregate_id)
        if brief is None:
            return
        title, slug, members, _creator = brief
        msg = (
            await s.execute(
                text("SELECT milavn_activity.occurrence_update_message(:id)"),
                {"id": str(event.payload.get("update_id"))},
            )
        ).scalar_one_or_none() or ""
        for m in members:
            await deliver(
                s,
                member_id=m,
                notification_class="important",
                title=f"Update from the organizer: {title}",
                body=msg[:280],
                deep_link=f"/a/{slug}",
                occurrence_id=event.aggregate_id,
            )


async def _on_participation_changed(event: DomainEvent) -> None:
    payload = event.payload
    factory = get_process_session_factory()
    async with factory() as s, s.begin():
        brief = await _occurrence_brief(s, event.aggregate_id)
        if brief is None:
            return
        title, slug, _members, creator = brief
        promoted = payload.get("promoted_member_id")
        if promoted:
            await deliver(
                s,
                member_id=UUID(str(promoted)),
                notification_class="important",
                title=f"You're in: {title}",
                body="A spot opened up and you've moved off the waitlist.",
                deep_link=f"/a/{slug}",
                occurrence_id=event.aggregate_id,
            )
        member_id = UUID(str(payload["member_id"]))
        if payload.get("new_status") == "going" and member_id != creator:
            name = identity.display_names_for([member_id])[member_id].display_name
            await deliver(
                s,
                member_id=creator,
                notification_class="social",
                title=f"{name} is going",
                body=f"{name} joined {title}.",
                deep_link=f"/a/{slug}",
                occurrence_id=event.aggregate_id,
            )


async def _on_circle_suggestion(event: DomainEvent) -> None:
    factory = get_process_session_factory()
    async with factory() as s, s.begin():
        for m in event.payload.get("member_ids", []):
            await deliver(
                s,
                member_id=UUID(str(m)),
                notification_class="opportunity",
                title="You keep showing up together",
                body=f"Start a circle: {event.payload.get('name', '')}?",
                deep_link="/circles?suggestions=1",
                occurrence_id=None,
            )


async def _on_created(event: DomainEvent) -> None:
    """[FR054] Opportunity-class: new activity for circle members (circle-scoped) — kept to circle members only."""
    circle_id = event.payload.get("circle_id")
    if not circle_id:
        return
    factory = get_process_session_factory()
    async with factory() as s, s.begin():
        brief = await _occurrence_brief(s, event.aggregate_id)
        if brief is None:
            return
        title, slug, _members, creator = brief
        ids = (await s.execute(text("SELECT milavn_circle.active_member_ids(:c)"), {"c": str(circle_id)})).scalar_one()
        for m in list(ids or []):
            if m == creator:
                continue
            await deliver(
                s,
                member_id=m,
                notification_class="opportunity",
                title=f"New in your circle: {title}",
                body="Something new was planned in one of your circles.",
                deep_link=f"/a/{slug}",
                occurrence_id=event.aggregate_id,
            )


def register_subscribers() -> None:
    bus.subscribe("occurrence.cancelled", _on_cancelled)
    bus.subscribe("occurrence.updated", _on_updated)
    bus.subscribe("occurrence.announcement", _on_announcement)
    bus.subscribe("participation.changed", _on_participation_changed)
    bus.subscribe("circle.suggestion", _on_circle_suggestion)
    bus.subscribe("occurrence.created", _on_created)


async def send_reminders() -> int:
    """[FR052] Useful-class reminders ~24h before a member's Going occurrences (scheduled job)."""
    factory = get_process_session_factory()
    sent = 0
    async with factory() as s, s.begin():
        # No acting member in a scheduled job: candidates come from the
        # definer-owned reader (migration 009), ids and titles only.
        rows = (await s.execute(text("SELECT member_id, occurrence_id, title, canonical_url_slug FROM milavn_notification.reminder_candidates()"))).all()
        for member_id, occ_id, title, slug in rows:
            await deliver(
                s,
                member_id=member_id,
                notification_class="useful",
                title=f"Tomorrow: {title}",
                body="A reminder for something you're going to.",
                deep_link=f"/a/{slug}",
                occurrence_id=occ_id,
            )
            sent += 1
    return sent

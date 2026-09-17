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
from zoneinfo import ZoneInfo

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
            name = (await identity.display_names_for([member_id]))[member_id].display_name
            # [FR108] Tell the host when someone is coming for the first time: a hello on arrival is what keeps newcomers.
            first = (
                await s.execute(
                    text("SELECT milavn_activity.is_first_timer(:m, (SELECT time_start FROM milavn_ticketing.offer_context(:o)))"),
                    {"m": str(member_id), "o": str(event.aggregate_id)},
                )
            ).scalar_one()
            await deliver(
                s,
                member_id=creator,
                notification_class="social",
                title=f"{name} is going · first time" if first else f"{name} is going",
                body=f"{name} is coming to their first Milavn activity. A hello when they arrive goes a long way." if first else f"{name} joined {title}.",
                deep_link=f"/a/{slug}",
                occurrence_id=event.aggregate_id,
            )


async def _on_series_date_added(event: DomainEvent) -> None:
    """[FR112] A new date in a series: regulars get their spot kept (or a waitlist place) and are told how to free it."""
    if not event.payload.get("activity_id"):
        return
    factory = get_process_session_factory()
    async with factory() as s, s.begin():
        kept = (await s.execute(text("SELECT kept_member_id, kept_status FROM milavn_activity.keep_regular_spots(:o)"), {"o": str(event.aggregate_id)})).all()
        if not kept:
            return
        brief = await _occurrence_brief(s, event.aggregate_id)
        if brief is None:
            return
        title, slug, _members, _creator = brief
        for member_id, status in kept:
            await deliver(
                s,
                member_id=member_id,
                notification_class="important",
                title=f"Your spot is kept: {title}" if status == "going" else f"You're on the waitlist: {title}",
                body="You're a regular, so we kept your spot for the new date. Can't make it? Free it in one tap."
                if status == "going"
                else "It was already full, so you're on the waitlist as a regular. You'll move up if a spot opens.",
                deep_link=f"/a/{slug}",
                occurrence_id=event.aggregate_id,
            )


async def _on_circle_join_requested(event: DomainEvent) -> None:
    """[FR115] Someone is waiting to be let into a circle: its organizers are told, once each."""
    member_id = event.payload.get("member_id")
    if not member_id:
        return
    factory = get_process_session_factory()
    async with factory() as s, s.begin():
        name = (await s.execute(text("SELECT milavn_circle.circle_name(:c)"), {"c": str(event.aggregate_id)})).scalar_one_or_none()
        organizers = (await s.execute(text("SELECT milavn_circle.circle_organizer_ids(:c)"), {"c": str(event.aggregate_id)})).scalar_one()
        if not name or not organizers:
            return
        who = (await identity.display_names_for([UUID(str(member_id))]))[UUID(str(member_id))].display_name
        for organizer in organizers:
            if str(organizer) == str(member_id):
                continue
            await deliver(
                s,
                member_id=organizer,
                notification_class="important",
                title=f"{who} would like to join {name}",
                body="They answered your questions. Let them in, or not — either way they are told nothing about who decided.",
                deep_link=f"/circles/{event.aggregate_id}",
                occurrence_id=None,
            )


async def _on_circle_join_decided(event: DomainEvent) -> None:
    """[FR115] Being let in is worth saying. A "no" is deliberately NOT announced: the person sees it
    on the circle page if they look, and a push that says "you were turned down" helps nobody."""
    if not event.payload.get("approved"):
        return
    member_id = event.payload.get("member_id")
    if not member_id:
        return
    factory = get_process_session_factory()
    async with factory() as s, s.begin():
        # The join_request row is readable only by the person who wrote it, so the circle comes from
        # the event payload rather than from a read this dispatcher cannot make.
        circle_id = event.payload.get("circle_id")
        if circle_id is None:
            return
        name = (await s.execute(text("SELECT milavn_circle.circle_name(:c)"), {"c": str(circle_id)})).scalar_one_or_none()
        if not name:
            return
        await deliver(
            s,
            member_id=UUID(str(member_id)),
            notification_class="social",
            title=f"You are in: {name}",
            body="Say hello on the circle board, and see what they have planned.",
            deep_link=f"/circles/{circle_id}",
            occurrence_id=None,
        )


async def _on_group_update_posted(event: DomainEvent) -> None:
    """[FR126] One admin message, fanned out to every distinct member across every chapter — the same
    "class useful" (suppressible) treatment as everything else that is genuinely useful but not
    urgent, so an umbrella-wide broadcast to many people can never become the notification fatigue
    the research on WhatsApp family groups already warns this module against."""
    print(f"DEBUG_FR126 payload={event.payload!r} types={ {k: type(v).__name__ for k, v in event.payload.items()} }", flush=True)
    group_id = event.payload.get("group_id")
    poster = event.payload.get("created_by_member_id")
    if group_id is None:
        return
    factory = get_process_session_factory()
    async with factory() as s, s.begin():
        name = (await s.execute(text("SELECT milavn_circle.group_name(:g)"), {"g": str(group_id)})).scalar_one_or_none()
        if not name:
            return
        member_ids = (await s.execute(text("SELECT milavn_circle.group_member_ids(:g)"), {"g": str(group_id)})).scalar_one()
        msg = (
            await s.execute(
                text("SELECT message FROM milavn_circle.circle_group_update WHERE id = :u"),
                {"u": str(event.payload.get("update_id"))},
            )
        ).scalar_one_or_none() or ""
        for m in member_ids or []:
            if str(m) == str(poster):
                continue
            await deliver(
                s,
                member_id=m,
                notification_class="useful",
                title=f"Update from {name}",
                body=msg[:280],
                deep_link=f"/circles/groups/{group_id}",
                occurrence_id=None,
            )


async def _on_connection_formed(event: DomainEvent) -> None:
    """[FR106] Both picked each other: each is told once, by name. A one-sided pick is never announced."""
    ids = [UUID(str(m)) for m in event.payload.get("member_ids", [])]
    if len(ids) != 2:
        return
    names = await identity.display_names_for(ids)
    factory = get_process_session_factory()
    async with factory() as s, s.begin():
        brief = await _occurrence_brief(s, event.aggregate_id)
        title = brief[0] if brief else "your activity"
        for me, other in ((ids[0], ids[1]), (ids[1], ids[0])):
            first = names[other].display_name.split(" ")[0]
            await deliver(
                s,
                member_id=me,
                notification_class="social",
                title=f"You and {first} would both meet again",
                body=f"You both picked each other after {title}. Say hello, or look out for their next activity.",
                deep_link=f"/p/{other}",
                occurrence_id=event.aggregate_id,
            )


async def _on_photo_removed(event: DomainEvent) -> None:
    """[FR113] The person who shared a photo learns it was taken down (never who asked)."""
    uploader = event.payload.get("uploader_member_id")
    if not uploader:
        return
    factory = get_process_session_factory()
    async with factory() as s, s.begin():
        brief = await _occurrence_brief(s, event.aggregate_id)
        if brief is None:
            return
        title, slug, _members, _creator = brief
        await deliver(
            s,
            member_id=UUID(str(uploader)),
            notification_class="useful",
            title=f"A photo you shared was taken down: {title}",
            body="Someone in it asked for it to be removed. Thank you for respecting people's privacy.",
            deep_link=f"/a/{slug}",
            occurrence_id=event.aggregate_id,
        )


async def _on_thanks(event: DomainEvent) -> None:
    """[FR107] The host hears the thank-you in the attendee's own words."""
    p = event.payload
    sender, host = UUID(str(p["from_member_id"])), UUID(str(p["to_member_id"]))
    factory = get_process_session_factory()
    async with factory() as s, s.begin():
        brief = await _occurrence_brief(s, event.aggregate_id)
        if brief is None:
            return
        title, slug, _members, _creator = brief
        msg = (await s.execute(text("SELECT milavn_trust.thanks_message(:o, :f)"), {"o": str(event.aggregate_id), "f": str(sender)})).scalar_one_or_none() or ""
        name = (await identity.display_names_for([sender]))[sender].display_name
        await deliver(
            s,
            member_id=host,
            notification_class="social",
            title=f"{name} thanked you",
            body=f"For {title}: “{msg[:140]}”",
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


def _rupees(paise: int) -> str:
    return f"₹{paise // 100:,}" if paise % 100 == 0 else f"₹{paise / 100:,.2f}"


async def _on_ticket(event: DomainEvent) -> None:
    """[FR102] Money moments are always Important: the member must never wonder whether they are in or refunded."""
    p = event.payload
    member = UUID(str(p["member_id"]))
    amount = _rupees(int(p.get("amount_paise") or 0))
    factory = get_process_session_factory()
    async with factory() as s, s.begin():
        brief = await _occurrence_brief(s, event.aggregate_id)
        if brief is None:
            return
        title, slug, _members, creator = brief
        if event.event_type == "ticket.paid":
            head, body = f"You're in: {title}", f"{amount} paid. Your spot is confirmed."
        elif event.event_type == "ticket.offered":
            until = datetime.fromisoformat(str(p["hold_until"])).astimezone(ZoneInfo("Asia/Kolkata"))
            head = f"A spot opened: {title}"
            body = f"Pay {amount} by {until:%d %b}, {until:%I:%M %p}".replace(" 0", " ") + " to take it. After that it goes to the next person."
        elif event.event_type == "ticket.refund_started":
            head, body = f"Refund started: {title}", f"{amount} is on its way back to you."
        else:
            head, body = f"Refunded: {title}", f"{amount} has been returned to you."
        await deliver(s, member_id=member, notification_class="important", title=head, body=body, deep_link=f"/a/{slug}", occurrence_id=event.aggregate_id)
        if event.event_type == "ticket.paid" and member != creator:
            name = (await identity.display_names_for([member]))[member].display_name
            await deliver(
                s,
                member_id=creator,
                notification_class="social",
                title=f"{name} is going",
                body=f"{name} joined {title}.",
                deep_link=f"/a/{slug}",
                occurrence_id=event.aggregate_id,
            )


def register_subscribers() -> None:
    for kind in ("ticket.paid", "ticket.offered", "ticket.refund_started", "ticket.refunded"):
        bus.subscribe(kind, _on_ticket)
    bus.subscribe("thanks.given", _on_thanks)
    bus.subscribe("occurrence.created", _on_series_date_added)
    bus.subscribe("photo.removed", _on_photo_removed)
    bus.subscribe("connection.formed", _on_connection_formed)
    bus.subscribe("circle.join_requested", _on_circle_join_requested)
    bus.subscribe("circle.join_decided", _on_circle_join_decided)
    bus.subscribe("occurrence.cancelled", _on_cancelled)
    bus.subscribe("occurrence.updated", _on_updated)
    bus.subscribe("occurrence.announcement", _on_announcement)
    bus.subscribe("participation.changed", _on_participation_changed)
    bus.subscribe("circle.suggestion", _on_circle_suggestion)
    bus.subscribe("circle_group.update_posted", _on_group_update_posted)
    bus.subscribe("occurrence.created", _on_created)


REMINDER_KINDS = ("three_days", "still_coming", "two_hours")
TRAVEL_PHRASE = {"walk": "on foot", "two_wheeler": "by two-wheeler", "car": "by car", "cab_auto": "by cab or auto", "metro_bus": "by metro or bus"}


def reminder_copy(
    kind: str,
    *,
    title: str,
    time_start: datetime,
    locality: str,
    plan_travel: str | None,
    plan_with: str | None,
    waitlisted: int,
    paid: bool,
    missed_last: bool = False,
) -> tuple[str, str]:
    """[FR103/FR104] What each reminder says. Kind, factual, and about other people rather than guilt:
    a missed spot is framed as someone on the waitlist who could have come (Berliner Senderey et al. 2020),
    and the member's own plan is repeated back (Nickerson & Rogers 2010). No penalties are ever mentioned."""
    local = time_start.astimezone(ZoneInfo("Asia/Kolkata"))
    clock = f"{local:%I:%M %p}".lstrip("0")
    day = f"{local:%a} {local.day} {local:%b}"
    if kind == "three_days":
        # [FR112] After a missed date in a series, welcome back warmly (Milkman et al. 2021) — never a broken streak.
        welcome = "We missed you last time; glad you're coming. " if missed_last else ""
        return f"In 3 days: {title}", f"{welcome}{day}, {clock} in {locality}. Put it in your calendar so the day stays free."
    if kind == "still_coming":
        if waitlisted == 1:
            ask = "If you can't make it, free your spot so the person on the waitlist can join."
        elif waitlisted > 1:
            ask = f"If you can't make it, free your spot so one of the {waitlisted} people waiting can join."
        else:
            ask = "If you can't make it, freeing your spot helps the host plan."
        refund = " Your refund rule is on the activity page." if paid else ""
        return f"Still coming tomorrow? {title}", f"{day}, {clock} in {locality}. {ask}{refund}"
    if kind == "two_hours":
        plan = f" You planned to come {TRAVEL_PHRASE[plan_travel]}." if plan_travel in TRAVEL_PHRASE else ""
        alone = " Coming on your own? Say hello to the host when you arrive; they'll introduce you." if plan_with == "alone" else ""
        return f"Starts at {clock}: {title}", f"In {locality}.{plan}{alone}"
    raise ValueError(kind)


async def send_reminders() -> int:
    """[FR052/FR103/FR104] Scheduled every 10 minutes.
    Interested: one nudge the day before. Going: "in 3 days", "still coming?" the day before (with the choice to
    free the spot), and "starts in 2 hours" with the member's own plan. Each is claimed in the database before it
    is sent, so overlapping runs never send twice (migration 018)."""
    factory = get_process_session_factory()
    sent = 0
    async with factory() as s, s.begin():
        # No acting member in a scheduled job: candidates come from definer-owned readers (migrations 009, 018).
        rows = (await s.execute(text("SELECT member_id, occurrence_id, title, canonical_url_slug FROM milavn_notification.reminder_candidates()"))).all()
        for member_id, occ_id, title, slug in rows:
            await deliver(
                s,
                member_id=member_id,
                notification_class="useful",
                title=f"Tomorrow: {title}",
                body="You marked this as interested. Tap Going if you'll be there.",
                deep_link=f"/a/{slug}",
                occurrence_id=occ_id,
            )
            sent += 1
        for kind in REMINDER_KINDS:
            due = (
                await s.execute(
                    text(
                        "SELECT member_id, occurrence_id, title, slug, time_start, locality, plan_travel, plan_with, waitlisted, paid, missed_last "
                        "FROM milavn_notification.claim_reminders(:k)"
                    ),
                    {"k": kind},
                )
            ).all()
            for r in due:
                head, body = reminder_copy(
                    kind, title=r[2], time_start=r[4], locality=r[5], plan_travel=r[6], plan_with=r[7], waitlisted=r[8], paid=r[9], missed_last=bool(r[10])
                )
                await deliver(
                    s,
                    member_id=r[0],
                    notification_class="useful",
                    title=head,
                    body=body,
                    deep_link=f"/a/{r[3]}?confirm=1" if kind == "still_coming" else f"/a/{r[3]}",
                    occurrence_id=r[1],
                )
                sent += 1
    return sent

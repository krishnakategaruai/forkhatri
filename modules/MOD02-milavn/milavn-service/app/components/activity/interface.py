"""Activity & Occurrence — public interface (`milavn_activity`).

# [FR010-FR019, FR056-FR059, TR07-TR15, TR38, TR39] The concrete, dated,
# participable Occurrence is the unit everything resolves to; an Activity is
# an optional recurring-series umbrella (TR08 non-forced wrapper). One-tap
# Interested/Going with a full status lifecycle, organizer edit/cancel/
# announce, co-organizer delegation, capacity + concurrency-safe waitlist
# promotion, QR/manual check-in, and non-punitive no-show marking.
# Approach: every write goes through the Authorization Engine's resolved
# role, publishes a domain event in the same transaction (outbox) for
# Notification Dispatch / Audit, and the participation toggle takes a
# `FOR UPDATE` lock on the occurrence row before any capacity arithmetic so
# two concurrent withdrawals cannot double-promote (TR39).
# Traces to: TR07, TR08, TR09, TR10, TR11, TR12, TR13, TR14, TR15, TR38, TR39.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.authorization import interface as authz
from app.components.trust import interface as trust
from app.db.session import set_internal_service_context
from app.events import bus

INTENT_CATEGORIES = ("play", "meet", "eat", "learn", "work", "explore", "celebrate", "help")
VISIBILITY_SCOPES = ("public", "community", "circle", "organization", "personal")
ACTIVE_STATUSES = ("interested", "going", "waitlisted", "checked_in", "attended")


class OccurrenceNotFound(Exception):
    pass


class OccurrenceCancelled(Exception):
    pass


class InvalidInput(Exception):
    def __init__(self, fields: list[str]) -> None:
        super().__init__(str(fields))
        self.fields = fields


class DuplicateAnnouncement(Exception):
    """[FR057, thesis §84 "need over noise"] The same update was already sent to everyone going within the last hour."""


@dataclass(slots=True)
class Occurrence:
    id: UUID
    activity_id: UUID | None
    creator_member_id: UUID
    title: str
    description: str | None
    intent_category: str
    time_start: datetime
    time_end: datetime | None
    locality_city: str
    locality_zone: str | None
    locality_locality: str | None
    capacity: int | None
    cover_image_ref: str | None
    high_risk: bool
    visibility_scope: str
    circle_id: UUID | None
    organization_scope_id: UUID | None
    canonical_url_slug: str
    status: str
    cancelled_at: datetime | None
    created_at: datetime
    recurrence_rule: dict | None


_OCC_COLS = """
    o.id, o.activity_id, o.creator_member_id, o.title, o.description, o.intent_category::text,
    o.time_start, o.time_end, o.locality_city, o.locality_zone, o.locality_locality, o.capacity,
    o.cover_image_media_id, o.high_risk, o.visibility_scope::text, o.circle_id, o.organization_scope_id,
    o.canonical_url_slug, o.status::text, o.cancelled_at, o.created_at, a.recurrence_rule
"""
_FROM = "FROM milavn_activity.occurrence o LEFT JOIN milavn_activity.activity a ON a.id = o.activity_id"


def _row_to_occurrence(r) -> Occurrence:  # noqa: ANN001
    return Occurrence(
        id=r[0],
        activity_id=r[1],
        creator_member_id=r[2],
        title=r[3],
        description=r[4],
        intent_category=r[5],
        time_start=r[6],
        time_end=r[7],
        locality_city=r[8],
        locality_zone=r[9],
        locality_locality=r[10],
        capacity=r[11],
        cover_image_ref=_cover_ref(r[12]),
        high_risk=r[13],
        visibility_scope=r[14],
        circle_id=r[15],
        organization_scope_id=r[16],
        canonical_url_slug=r[17],
        status=r[18],
        cancelled_at=r[19],
        created_at=r[20],
        recurrence_rule=r[21],
    )


def _cover_ref(media_id: UUID | None) -> str | None:
    # Cover images are stored under .local-media/covers/<media_id>.<ext>; the
    # API resolves the actual file name at read time (see get_cover_url).
    return str(media_id) if media_id else None


async def get(session: AsyncSession, *, occurrence_id: UUID) -> Occurrence:
    row = (await session.execute(text(f"SELECT {_OCC_COLS} {_FROM} WHERE o.id = :id"), {"id": str(occurrence_id)})).first()
    if row is None:
        raise OccurrenceNotFound
    return _row_to_occurrence(row)


async def get_by_slug(session: AsyncSession, *, slug: str) -> Occurrence:
    row = (await session.execute(text(f"SELECT {_OCC_COLS} {_FROM} WHERE o.canonical_url_slug = :slug"), {"slug": slug})).first()
    if row is None:
        raise OccurrenceNotFound
    return _row_to_occurrence(row)


async def list_visible(
    session: AsyncSession,
    *,
    city: str | None,
    start: datetime | None,
    end: datetime | None,
    category: str | None = None,
    scope: str | None = None,
    query: str | None = None,
    circle_id: UUID | None = None,
    organization_scope_id: UUID | None = None,
    creator_member_id: UUID | None = None,
    include_cancelled: bool = False,
    limit: int = 200,
) -> list[Occurrence]:
    clauses = ["1=1"]
    params: dict = {"limit": limit}
    if not include_cancelled:
        clauses.append("o.status = 'active'")
    if city:
        clauses.append("lower(o.locality_city) = lower(:city)")
        params["city"] = city
    if start:
        clauses.append("o.time_start >= :start")
        params["start"] = start
    if end:
        clauses.append("o.time_start < :end")
        params["end"] = end
    if category:
        clauses.append("o.intent_category = CAST(:cat AS milavn_activity.intent_category)")
        params["cat"] = category
    if scope:
        clauses.append("o.visibility_scope = CAST(:scope AS milavn_activity.visibility_scope)")
        params["scope"] = scope
    if circle_id:
        clauses.append("o.circle_id = :circle")
        params["circle"] = str(circle_id)
    if organization_scope_id:
        clauses.append("o.organization_scope_id = :org")
        params["org"] = str(organization_scope_id)
    if creator_member_id:
        clauses.append("o.creator_member_id = :creator")
        params["creator"] = str(creator_member_id)
    if query:
        clauses.append("(o.title ILIKE '%' || :q || '%' OR coalesce(o.description,'') ILIKE '%' || :q || '%' OR o.locality_locality ILIKE '%' || :q || '%')")
        params["q"] = query.strip()
    sql = f"SELECT {_OCC_COLS} {_FROM} WHERE {' AND '.join(clauses)} ORDER BY o.time_start ASC LIMIT :limit"
    rows = (await session.execute(text(sql), params)).all()
    return [_row_to_occurrence(r) for r in rows]


# --- Counts (definer-owned aggregate helpers, migration 002) -----------------


async def going_count(session: AsyncSession, occurrence_id: UUID) -> int:
    return int((await session.execute(text("SELECT milavn_activity.going_count(:o)"), {"o": str(occurrence_id)})).scalar_one())


async def interested_count(session: AsyncSession, occurrence_id: UUID) -> int:
    return int((await session.execute(text("SELECT milavn_activity.interested_count(:o)"), {"o": str(occurrence_id)})).scalar_one())


async def circle_peers_going(session: AsyncSession, occurrence_id: UUID, member_id: UUID) -> int:
    return int((await session.execute(text("SELECT milavn_activity.circle_peers_going(:o, :m)"), {"o": str(occurrence_id), "m": str(member_id)})).scalar_one())


async def viewer_status(session: AsyncSession, occurrence_id: UUID, member_id: UUID) -> str | None:
    row = (
        await session.execute(
            text("SELECT status::text FROM milavn_activity.participation WHERE occurrence_id = :o AND member_id = :m"),
            {"o": str(occurrence_id), "m": str(member_id)},
        )
    ).first()
    return row[0] if row else None


async def viewer_statuses(session: AsyncSession, occurrence_ids: list[UUID], member_id: UUID) -> dict[UUID, str]:
    if not occurrence_ids:
        return {}
    rows = (
        await session.execute(
            text("SELECT occurrence_id, status::text FROM milavn_activity.participation WHERE member_id = :m AND occurrence_id = ANY(:ids)"),
            {"m": str(member_id), "ids": [str(i) for i in occurrence_ids]},
        )
    ).all()
    return {r[0]: r[1] for r in rows}


# --- Create / edit / cancel (FR010-FR014, FR017) -----------------------------


def _slug(occurrence_id: UUID) -> str:
    return f"occ-{occurrence_id.hex[:12]}"


async def create(
    session: AsyncSession,
    *,
    creator_member_id: UUID,
    creator_identity_level: int,
    title: str,
    intent_category: str,
    time_start: datetime,
    time_end: datetime | None,
    locality_city: str,
    locality_zone: str | None,
    locality_locality: str | None,
    description: str | None = None,
    capacity: int | None = None,
    visibility_scope: str = "public",
    circle_id: UUID | None = None,
    organization_scope_id: UUID | None = None,
    high_risk: bool = False,
    cover_image_media_id: UUID | None = None,
    recurrence_rule: dict | None = None,
    activity_id: UUID | None = None,
) -> Occurrence:
    missing = [
        f
        for f, v in (("title", title.strip() if title else ""), ("intent_category", intent_category), ("time_start", time_start), ("locality_city", locality_city))
        if not v
    ]
    if intent_category and intent_category not in INTENT_CATEGORIES:
        missing.append("intent_category")
    if visibility_scope not in VISIBILITY_SCOPES:
        missing.append("visibility_scope")
    if visibility_scope == "circle" and circle_id is None:
        missing.append("circle_id")
    if capacity is not None and capacity < 1:
        missing.append("capacity")
    if missing:
        raise InvalidInput(sorted(set(missing)))

    # [TR08] Only create the umbrella when the creator marked it recurring.
    if recurrence_rule and activity_id is None:
        activity_id = uuid4()
        await session.execute(
            text(
                """
                INSERT INTO milavn_activity.activity (id, creator_member_id, title, intent_category, recurrence_rule)
                VALUES (:id, :creator, :title, CAST(:cat AS milavn_activity.intent_category), CAST(:rule AS jsonb))
                """
            ),
            {
                "id": str(activity_id),
                "creator": str(creator_member_id),
                "title": title.strip(),
                "cat": intent_category,
                "rule": __import__("json").dumps(recurrence_rule),
            },
        )

    occurrence_id = uuid4()
    await session.execute(
        text(
            """
            INSERT INTO milavn_activity.occurrence
              (id, activity_id, creator_member_id, title, description, intent_category, time_start, time_end,
               locality_city, locality_zone, locality_locality, capacity, cover_image_media_id, high_risk,
               visibility_scope, circle_id, organization_scope_id, canonical_url_slug)
            VALUES
              (:id, :activity_id, :creator, :title, NULLIF(:description, ''), CAST(:cat AS milavn_activity.intent_category),
               :time_start, :time_end, :city, :zone, :locality, :capacity, :cover, :high_risk,
               CAST(:scope AS milavn_activity.visibility_scope), :circle_id, :org_id, :slug)
            """
        ),
        {
            "id": str(occurrence_id),
            "activity_id": str(activity_id) if activity_id else None,
            "creator": str(creator_member_id),
            "title": title.strip(),
            "description": (description or "").strip(),
            "cat": intent_category,
            "time_start": time_start,
            "time_end": time_end,
            "city": locality_city.strip(),
            "zone": locality_zone,
            "locality": locality_locality,
            "capacity": capacity,
            "cover": str(cover_image_media_id) if cover_image_media_id else None,
            "high_risk": high_risk,
            "scope": visibility_scope,
            "circle_id": str(circle_id) if circle_id else None,
            "org_id": str(organization_scope_id) if organization_scope_id else None,
            "slug": _slug(occurrence_id),
        },
    )
    # [FR030] Every item resolves to exactly one trust level from the moment it exists.
    level = await trust.resolve_organizer_level(session, member_id=creator_member_id, identity_level=creator_identity_level)
    await trust.ensure_trust(session, subject_type="occurrence", subject_id=occurrence_id, level=level)
    await trust.ensure_trust(session, subject_type="organizer", subject_id=creator_member_id, level=level)
    await bus.publish(
        session,
        schema="milavn_activity",
        event_type="occurrence.created",
        aggregate_id=occurrence_id,
        payload={"occurrence_id": occurrence_id, "creator_member_id": creator_member_id, "circle_id": circle_id},
    )
    return await get(session, occurrence_id=occurrence_id)


async def update(session: AsyncSession, *, occurrence_id: UUID, actor_member_id: UUID, changes: dict) -> tuple[Occurrence, bool]:
    await authz.require_organizer(session, occurrence_id=occurrence_id, member_id=actor_member_id)
    before = await get(session, occurrence_id=occurrence_id)
    if before.status == "cancelled":
        raise OccurrenceCancelled
    allowed = {
        "title",
        "description",
        "intent_category",
        "time_start",
        "time_end",
        "locality_city",
        "locality_zone",
        "locality_locality",
        "capacity",
        "high_risk",
        "visibility_scope",
        "circle_id",
        "cover_image_media_id",
    }
    sets: list[str] = []
    params: dict = {"id": str(occurrence_id)}
    for key, value in changes.items():
        if key not in allowed or value is None and key in ("title", "time_start", "locality_city"):
            continue
        enum_type = {"intent_category": "milavn_activity.intent_category", "visibility_scope": "milavn_activity.visibility_scope"}.get(key)
        if key in ("circle_id", "cover_image_media_id") and value is not None:
            value = str(value)
        # CAST(), never `:p::type` — SQLAlchemy does not parse a bind followed by `::`.
        sets.append(f"{key} = CAST(:{key} AS {enum_type})" if enum_type else f"{key} = :{key}")
        params[key] = value
    if not sets:
        return before, False
    sets.append("updated_at = now()")
    await session.execute(text(f"UPDATE milavn_activity.occurrence SET {', '.join(sets)} WHERE id = :id"), params)
    after = await get(session, occurrence_id=occurrence_id)
    material = before.time_start != after.time_start or before.locality_locality != after.locality_locality or before.locality_city != after.locality_city
    await bus.publish(
        session,
        schema="milavn_activity",
        event_type="occurrence.updated",
        aggregate_id=occurrence_id,
        payload={"occurrence_id": occurrence_id, "actor_member_id": actor_member_id, "material": material},
    )
    return after, material


async def cancel(session: AsyncSession, *, occurrence_id: UUID, actor_member_id: UUID, reason: str | None) -> Occurrence:
    await authz.require_organizer(session, occurrence_id=occurrence_id, member_id=actor_member_id)
    await session.execute(
        text("UPDATE milavn_activity.occurrence SET status = 'cancelled', cancelled_at = now(), updated_at = now() WHERE id = :id AND status = 'active'"),
        {"id": str(occurrence_id)},
    )
    # [FR034] Cancellation is a named behaviour for the organizer — a signal, not a penalty.
    await trust.record_signal(session, member_id=actor_member_id, signal="cancellation", occurrence_id=occurrence_id, weight=-0.5)
    await bus.publish(
        session,
        schema="milavn_activity",
        event_type="occurrence.cancelled",
        aggregate_id=occurrence_id,
        payload={"occurrence_id": occurrence_id, "actor_member_id": actor_member_id, "reason": reason or ""},
    )
    return await get(session, occurrence_id=occurrence_id)


async def announce(session: AsyncSession, *, occurrence_id: UUID, actor_member_id: UUID, message: str) -> UUID:
    """[FR057] Organizer update reaches every current participant."""
    await authz.require_organizer(session, occurrence_id=occurrence_id, member_id=actor_member_id)
    if not message.strip():
        raise InvalidInput(["message"])
    # Need over noise: an identical message inside an hour is almost always a double tap or a retry.
    dup = await session.scalar(
        text("SELECT 1 FROM milavn_activity.occurrence_update WHERE occurrence_id = :o AND message = :msg AND created_at > now() - interval '1 hour' LIMIT 1"),
        {"o": str(occurrence_id), "msg": message.strip()},
    )
    if dup:
        raise DuplicateAnnouncement()
    update_id = uuid4()
    await session.execute(
        text("INSERT INTO milavn_activity.occurrence_update (id, occurrence_id, organizer_member_id, message) VALUES (:id, :o, :m, :msg)"),
        {"id": str(update_id), "o": str(occurrence_id), "m": str(actor_member_id), "msg": message.strip()},
    )
    await bus.publish(
        session,
        schema="milavn_activity",
        event_type="occurrence.announcement",
        aggregate_id=occurrence_id,
        payload={"occurrence_id": occurrence_id, "update_id": update_id, "actor_member_id": actor_member_id},
    )
    return update_id


async def list_announcements(session: AsyncSession, *, occurrence_id: UUID) -> list[dict]:
    rows = (
        await session.execute(
            text("SELECT id, organizer_member_id, message, created_at FROM milavn_activity.occurrence_update WHERE occurrence_id = :o ORDER BY created_at DESC"),
            {"o": str(occurrence_id)},
        )
    ).all()
    return [dict(r._mapping) for r in rows]


# --- Participation (FR015, FR016, FR058) ------------------------------------


@dataclass(frozen=True, slots=True)
class ParticipationResult:
    status: str
    waitlist_position: int | None
    going_count: int
    spots_left: int | None
    promoted_member_id: UUID | None


async def _history(session: AsyncSession, participation_id: UUID, old: str | None, new: str, actor: UUID) -> None:
    await session.execute(
        text(
            """
            INSERT INTO milavn_activity.participation_status_history
              (participation_id, old_status, new_status, changed_by_member_id)
            VALUES (:p, CAST(:old AS milavn_activity.participation_status), CAST(:new AS milavn_activity.participation_status), :actor)
            """
        ),
        {"p": str(participation_id), "old": old, "new": new, "actor": str(actor)},
    )


async def set_participation(session: AsyncSession, *, occurrence_id: UUID, member_id: UUID, desired: str) -> ParticipationResult:
    """[FR015/FR016/FR058] One-tap toggle with a concurrency-safe capacity path."""
    if desired not in ("interested", "going", "cancelled"):
        raise InvalidInput(["status"])
    # [TR39] Serialise the whole capacity decision per occurrence. A row lock
    # (`FOR UPDATE`) would have to pass the UPDATE policy, which a participant
    # correctly cannot — so the transaction-scoped advisory lock keyed on the
    # occurrence id gives the same one-writer-at-a-time guarantee (migration 003).
    await session.execute(text("SELECT pg_advisory_xact_lock(hashtext(:id))"), {"id": str(occurrence_id)})
    occ_row = (
        await session.execute(
            text("SELECT id, capacity, status::text, creator_member_id FROM milavn_activity.occurrence WHERE id = :id"),
            {"id": str(occurrence_id)},
        )
    ).first()
    if occ_row is None:
        raise OccurrenceNotFound
    if occ_row[2] == "cancelled" and desired != "cancelled":
        raise OccurrenceCancelled
    capacity: int | None = occ_row[1]

    existing = (
        await session.execute(
            text("SELECT id, status::text, waitlist_position FROM milavn_activity.participation WHERE occurrence_id = :o AND member_id = :m"),
            {"o": str(occurrence_id), "m": str(member_id)},
        )
    ).first()
    old_status = existing[1] if existing else None
    promoted: UUID | None = None

    new_status = desired
    waitlist_position: int | None = None
    if desired == "going":
        if old_status in ("going", "checked_in", "attended"):
            new_status = old_status
        elif capacity is not None:
            going = await going_count(session, occurrence_id)
            if going >= capacity:
                new_status = "waitlisted"
                waitlist_position = int(
                    (
                        await session.execute(
                            text("SELECT coalesce(max(waitlist_position), 0) + 1 FROM milavn_activity.participation WHERE occurrence_id = :o AND status = 'waitlisted'"),
                            {"o": str(occurrence_id)},
                        )
                    ).scalar_one()
                )

    if existing is None:
        participation_id = uuid4()
        await session.execute(
            text(
                """
                INSERT INTO milavn_activity.participation (id, occurrence_id, member_id, status, waitlist_position)
                VALUES (:id, :o, :m, CAST(:s AS milavn_activity.participation_status), :wp)
                """
            ),
            {"id": str(participation_id), "o": str(occurrence_id), "m": str(member_id), "s": new_status, "wp": waitlist_position},
        )
    else:
        participation_id = existing[0]
        if old_status != new_status:
            await session.execute(
                text(
                    "UPDATE milavn_activity.participation SET status = CAST(:s AS milavn_activity.participation_status), "
                    "waitlist_position = :wp, updated_at = now() WHERE id = :id"
                ),
                {"s": new_status, "wp": waitlist_position, "id": str(participation_id)},
            )
    if old_status != new_status:
        await _history(session, participation_id, old_status, new_status, member_id)

    # [TR39] A freed Going slot promotes the lowest waitlist position, under the lock held above.
    if old_status == "going" and new_status in ("cancelled", "interested") and capacity is not None:
        promoted = await _promote_next(session, occurrence_id, member_id)

    if old_status != new_status:
        await bus.publish(
            session,
            schema="milavn_activity",
            event_type="participation.changed",
            aggregate_id=occurrence_id,
            payload={
                "occurrence_id": occurrence_id,
                "member_id": member_id,
                "old_status": old_status or "",
                "new_status": new_status,
                "promoted_member_id": promoted,
                "organizer_member_id": occ_row[3],
            },
        )
    going_now = await going_count(session, occurrence_id)
    spots_left = (capacity - going_now) if capacity is not None else None
    return ParticipationResult(new_status, waitlist_position, going_now, spots_left, promoted)


async def _promote_next(session: AsyncSession, occurrence_id: UUID, actor_member_id: UUID) -> UUID | None:
    # The waitlisted row belongs to another member, whom RLS correctly hides
    # from the withdrawing member — promotion runs through the definer-owned
    # `promote_next_waitlisted` (migration 003), which also writes the history row.
    row = (
        await session.execute(
            text("SELECT participation_id, member_id FROM milavn_activity.promote_next_waitlisted(:o, :a)"),
            {"o": str(occurrence_id), "a": str(actor_member_id)},
        )
    ).first()
    return row[1] if row else None


# --- Organizer tools (FR056, FR059, FR018, FR019) ----------------------------


@dataclass(frozen=True, slots=True)
class Attendee:
    member_id: UUID
    status: str
    waitlist_position: int | None
    checked_in_at: datetime | None
    updated_at: datetime


async def attendees(session: AsyncSession, *, occurrence_id: UUID, actor_member_id: UUID) -> list[Attendee]:
    """[FR056] Organizer/co-organizer only — enforced here and by RLS."""
    await authz.require_organizer(session, occurrence_id=occurrence_id, member_id=actor_member_id)
    rows = (
        await session.execute(
            text(
                "SELECT member_id, status::text, waitlist_position, checked_in_at, updated_at "
                "FROM milavn_activity.participation WHERE occurrence_id = :o "
                "ORDER BY CASE status WHEN 'going' THEN 0 WHEN 'checked_in' THEN 0 WHEN 'attended' THEN 0 WHEN 'waitlisted' THEN 1 WHEN 'interested' THEN 2 ELSE 3 END, waitlist_position NULLS FIRST, updated_at"
            ),
            {"o": str(occurrence_id)},
        )
    ).all()
    return [Attendee(r[0], r[1], r[2], r[3], r[4]) for r in rows]


async def co_organizers(session: AsyncSession, *, occurrence_id: UUID) -> list[UUID]:
    rows = (
        await session.execute(
            text("SELECT member_id FROM milavn_activity.occurrence_co_organizer WHERE occurrence_id = :o AND revoked_at IS NULL"),
            {"o": str(occurrence_id)},
        )
    ).all()
    return [r[0] for r in rows]


async def grant_co_organizer(session: AsyncSession, *, occurrence_id: UUID, actor_member_id: UUID, member_id: UUID) -> None:
    """[FR059] Creator delegates; revocable."""
    await authz.require_creator(session, occurrence_id=occurrence_id, member_id=actor_member_id)
    await session.execute(
        text(
            """
            INSERT INTO milavn_activity.occurrence_co_organizer (occurrence_id, member_id, granted_by_member_id)
            VALUES (:o, :m, :g)
            ON CONFLICT (occurrence_id, member_id) DO UPDATE SET revoked_at = NULL, granted_at = now(), granted_by_member_id = EXCLUDED.granted_by_member_id
            """
        ),
        {"o": str(occurrence_id), "m": str(member_id), "g": str(actor_member_id)},
    )


async def revoke_co_organizer(session: AsyncSession, *, occurrence_id: UUID, actor_member_id: UUID, member_id: UUID) -> None:
    await authz.require_creator(session, occurrence_id=occurrence_id, member_id=actor_member_id)
    await session.execute(
        text("UPDATE milavn_activity.occurrence_co_organizer SET revoked_at = now() WHERE occurrence_id = :o AND member_id = :m AND revoked_at IS NULL"),
        {"o": str(occurrence_id), "m": str(member_id)},
    )


async def mark_attendance(session: AsyncSession, *, occurrence_id: UUID, actor_member_id: UUID, member_id: UUID, outcome: str) -> str:
    """[FR018 manual check-in, FR019 non-punitive no-show] Organizer marks a participant."""
    if outcome not in ("checked_in", "attended", "no_show"):
        raise InvalidInput(["outcome"])
    await authz.require_organizer(session, occurrence_id=occurrence_id, member_id=actor_member_id)
    # The participant's row is theirs (RLS WITH CHECK member_id = self); the
    # organizer-side write goes through the definer-owned `organizer_set_status`
    # (migration 003), which re-checks the organizer relationship itself.
    previous = (
        await session.execute(
            text("SELECT milavn_activity.organizer_set_status(:o, :m, :s, :a)"),
            {"o": str(occurrence_id), "m": str(member_id), "s": outcome, "a": str(actor_member_id)},
        )
    ).scalar_one()
    if previous is None:
        raise OccurrenceNotFound
    # [FR034/FR019] Named behaviours only; a single no-show is a small signal, never a penalty.
    if outcome in ("checked_in", "attended"):
        await trust.record_signal(session, member_id=member_id, signal="attendance_reliable", occurrence_id=occurrence_id, weight=1.0)
    else:
        await trust.record_signal(session, member_id=member_id, signal="no_show", occurrence_id=occurrence_id, weight=-0.25)
    return outcome


async def complete(session: AsyncSession, *, occurrence_id: UUID, actor_member_id: UUID) -> None:
    """[FR034] Organizer closes a held occurrence: event_completed signal for the organizer."""
    await authz.require_organizer(session, occurrence_id=occurrence_id, member_id=actor_member_id)
    occ = await get(session, occurrence_id=occurrence_id)
    await trust.record_signal(session, member_id=occ.creator_member_id, signal="event_completed", occurrence_id=occurrence_id, weight=1.0)
    level = await trust.resolve_organizer_level(session, member_id=occ.creator_member_id, identity_level=0)
    current = await trust.trust_for(session, subject_type="organizer", subject_id=occ.creator_member_id)
    if current.level == "community_submitted" and level == "community_verified":
        await trust.set_trust(session, subject_type="organizer", subject_id=occ.creator_member_id, level=level)
    await bus.publish(
        session,
        schema="milavn_activity",
        event_type="occurrence.completed",
        aggregate_id=occurrence_id,
        payload={"occurrence_id": occurrence_id, "organizer_member_id": occ.creator_member_id},
    )


async def issue_checkin_token(session: AsyncSession, *, occurrence_id: UUID, actor_member_id: UUID) -> tuple[str, datetime]:
    """[FR018] Scale-gated optional QR token, short-lived."""
    await authz.require_organizer(session, occurrence_id=occurrence_id, member_id=actor_member_id)
    token = secrets.token_urlsafe(16)
    expires = datetime.now(UTC) + timedelta(hours=12)
    await session.execute(
        text("INSERT INTO milavn_activity.qr_checkin_token (occurrence_id, token, expires_at) VALUES (:o, :t, :e)"),
        {"o": str(occurrence_id), "t": token, "e": expires},
    )
    return token, expires


async def redeem_checkin_token(session: AsyncSession, *, occurrence_id: UUID, member_id: UUID, token: str) -> str:
    """[FR018] Participant scans; validated on the internal scan path."""
    await set_internal_service_context(session)
    row = (
        await session.execute(
            text("SELECT id FROM milavn_activity.qr_checkin_token WHERE occurrence_id = :o AND token = :t AND expires_at > now()"),
            {"o": str(occurrence_id), "t": token},
        )
    ).first()
    if row is None:
        raise InvalidInput(["token"])
    p = (
        await session.execute(
            text("SELECT id, status::text FROM milavn_activity.participation WHERE occurrence_id = :o AND member_id = :m"),
            {"o": str(occurrence_id), "m": str(member_id)},
        )
    ).first()
    if p is None:
        await set_participation(session, occurrence_id=occurrence_id, member_id=member_id, desired="going")
        p = (
            await session.execute(
                text("SELECT id, status::text FROM milavn_activity.participation WHERE occurrence_id = :o AND member_id = :m"),
                {"o": str(occurrence_id), "m": str(member_id)},
            )
        ).first()
    await session.execute(
        text(
            "UPDATE milavn_activity.participation SET status = 'checked_in', waitlist_position = NULL, "
            "checked_in_at = coalesce(checked_in_at, now()), updated_at = now() WHERE id = :id"
        ),
        {"id": str(p[0])},
    )
    await _history(session, p[0], p[1], "checked_in", member_id)
    await trust.record_signal(session, member_id=member_id, signal="attendance_reliable", occurrence_id=occurrence_id, weight=1.0)
    return "checked_in"


async def my_participations(session: AsyncSession, *, member_id: UUID) -> dict[UUID, str]:
    rows = (
        await session.execute(
            text("SELECT occurrence_id, status::text FROM milavn_activity.participation WHERE member_id = :m"),
            {"m": str(member_id)},
        )
    ).all()
    return {r[0]: r[1] for r in rows}


async def participant_member_ids(session: AsyncSession, occurrence_id: UUID) -> list[UUID]:
    row = (await session.execute(text("SELECT milavn_activity.participant_member_ids(:o)"), {"o": str(occurrence_id)})).scalar_one()
    return list(row or [])


async def series_summary(session: AsyncSession, *, activity_id: UUID) -> dict:
    """[FR011] Activity-level history is a read-time aggregate over its occurrences."""
    row = (
        await session.execute(
            text(
                """
                SELECT count(*) FILTER (WHERE status='active' AND time_start < now()) AS held,
                       count(*) FILTER (WHERE status='active' AND time_start >= now()) AS upcoming,
                       min(time_start) AS first_at
                FROM milavn_activity.occurrence WHERE activity_id = :a
                """
            ),
            {"a": str(activity_id)},
        )
    ).first()
    return {"held": int(row[0] or 0), "upcoming": int(row[1] or 0), "first_at": row[2]}


async def upcoming_in_series(session: AsyncSession, *, activity_id: UUID, exclude: UUID) -> list[Occurrence]:
    rows = (
        await session.execute(
            text(f"SELECT {_OCC_COLS} {_FROM} WHERE o.activity_id = :a AND o.id <> :x AND o.status = 'active' AND o.time_start >= now() ORDER BY o.time_start LIMIT 6"),
            {"a": str(activity_id), "x": str(exclude)},
        )
    ).all()
    return [_row_to_occurrence(r) for r in rows]

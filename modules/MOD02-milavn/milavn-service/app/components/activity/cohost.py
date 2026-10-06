"""Circles co-hosting an event (Phase 2, Step 6; migration 053).

The event's host (its creator or a co-organizer) invites another circle; that circle's organizer
accepts or declines. Once accepted, the event shows on both circles' pages, both circles' members
can see it (occurrence RLS reads `milavn_activity.cohost_can_see`), and both circles' members are
told. An organizer inviting their own circle needs no second step. At most three circles per event.
Every write is a definer function in 053, which re-checks who is acting.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.events import bus


class NotFound(Exception):
    pass


class NotAllowed(Exception):
    pass


class Refused(Exception):
    """An invitation that cannot be sent: reason 'already' | 'declined_before' | 'limit' | 'own_circle' | 'ended'."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


async def _visible(session: AsyncSession, occurrence_id: UUID) -> bool:
    # Through the occurrence's own RLS: only someone who may see the event learns who hosts it.
    return (await session.execute(text("SELECT 1 FROM milavn_activity.occurrence WHERE id = :o"), {"o": str(occurrence_id)})).first() is not None


async def is_manager(session: AsyncSession, *, occurrence_id: UUID, member_id: UUID) -> bool:
    return bool(
        (await session.execute(text("SELECT milavn_activity.is_event_manager(:o, :m)"), {"o": str(occurrence_id), "m": str(member_id)})).scalar_one()
    )


async def cohosts(session: AsyncSession, *, occurrence_id: UUID, viewer_member_id: UUID) -> list[dict]:
    if not await _visible(session, occurrence_id):
        raise NotFound
    rows = (
        await session.execute(
            text("SELECT circle_id, name, status, cover_ref FROM milavn_activity.occurrence_cohosts(:o, :v)"),
            {"o": str(occurrence_id), "v": str(viewer_member_id)},
        )
    ).all()
    return [{"circle_id": str(r[0]), "name": r[1], "status": r[2], "cover_url": f"/media/{r[3]}" if r[3] else None} for r in rows]


async def invite(session: AsyncSession, *, occurrence_id: UUID, circle_id: UUID, actor_member_id: UUID) -> str:
    """'invited' (the circle's organizer decides) or 'accepted' (the actor organizes that circle)."""
    outcome = (
        await session.execute(
            text("SELECT milavn_activity.invite_cohost_circle(:o, :c, :m)"),
            {"o": str(occurrence_id), "c": str(circle_id), "m": str(actor_member_id)},
        )
    ).scalar_one()
    if outcome == "not_found":
        raise NotFound
    if outcome == "not_allowed":
        raise NotAllowed
    if outcome not in ("invited", "accepted"):
        raise Refused(outcome)
    await bus.publish(
        session,
        schema="milavn_activity",
        event_type="cohost.invited" if outcome == "invited" else "cohost.accepted",
        aggregate_id=occurrence_id,
        payload={"occurrence_id": occurrence_id, "circle_id": circle_id, "member_id": actor_member_id},
    )
    return outcome


async def respond(session: AsyncSession, *, occurrence_id: UUID, circle_id: UUID, actor_member_id: UUID, accept: bool) -> str:
    outcome = (
        await session.execute(
            text("SELECT milavn_activity.respond_cohost_invite(:o, :c, :m, :a)"),
            {"o": str(occurrence_id), "c": str(circle_id), "m": str(actor_member_id), "a": accept},
        )
    ).scalar_one()
    if outcome == "not_found":
        raise NotFound
    if outcome not in ("accepted", "declined"):
        raise NotAllowed
    if outcome == "accepted":
        await bus.publish(
            session,
            schema="milavn_activity",
            event_type="cohost.accepted",
            aggregate_id=occurrence_id,
            payload={"occurrence_id": occurrence_id, "circle_id": circle_id, "member_id": actor_member_id},
        )
    return outcome


async def remove(session: AsyncSession, *, occurrence_id: UUID, circle_id: UUID, actor_member_id: UUID) -> None:
    outcome = (
        await session.execute(
            text("SELECT milavn_activity.remove_cohost(:o, :c, :m)"),
            {"o": str(occurrence_id), "c": str(circle_id), "m": str(actor_member_id)},
        )
    ).scalar_one()
    if outcome == "not_found":
        raise NotFound
    if outcome != "removed":
        raise NotAllowed


async def invites_for_circle(session: AsyncSession, *, circle_id: UUID, viewer_member_id: UUID) -> list[dict]:
    """Pending invitations to co-host, for the circle's organizer (empty for anyone else)."""
    from app.components.identity_bridge import interface as identity

    rows = (
        await session.execute(
            text(
                "SELECT occurrence_id, title, slug, time_start, invited_by, host_circle_name, created_at "
                "FROM milavn_activity.cohost_invites_for_circle(:c, :v)"
            ),
            {"c": str(circle_id), "v": str(viewer_member_id)},
        )
    ).all()
    names = await identity.display_names_for([r[4] for r in rows])
    return [
        {
            "occurrence_id": str(r[0]),
            "title": r[1],
            "slug": r[2],
            "time_start": r[3].isoformat(),
            "invited_by": names[r[4]].display_name,
            "host_circle_name": r[5],
            "created_at": r[6].isoformat(),
        }
        for r in rows
    ]


async def cohosted_occurrence_ids(session: AsyncSession, *, circle_id: UUID) -> list[UUID]:
    ids = (await session.execute(text("SELECT milavn_activity.cohosted_occurrence_ids(:c)"), {"c": str(circle_id)})).scalar_one()
    return list(ids or [])

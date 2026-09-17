"""Connect (People Discovery) — public interface (`milavn_connect`, stateless).

# [FR042-FR045, TR31, TR32] Every suggested person carries a real reason
# (shared circle, attended together); a reason-less "people nearby" list is
# impossible to construct from this interface (it returns (person, reason)
# tuples only); there is no Match/Like model anywhere (FR044); copy is
# activity-framed, never romantic (FR045). Blocked pairs never appear (FR062).
# Approach: read-model over Circle membership and Activity participation via
# definer-owned helpers (identities of co-attendees are only revealed for
# occurrences the viewer themself attended — a fact the viewer already knows
# from being there).
# Traces to: TR31, TR32, TR41.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.authorization import interface as authz
from app.components.identity_bridge import interface as identity
from app.components.locationprivacy import interface as locpriv
from app.components.trust import interface as trust


@dataclass(frozen=True, slots=True)
class Suggestion:
    member_id: UUID
    display_name: str
    avatar: str | None
    reason: str
    reason_kind: str
    location_label: str | None
    reputation: list[str]


async def suggestions(session: AsyncSession, *, viewer_member_id: UUID) -> list[Suggestion]:
    reasons: dict[UUID, tuple[str, str]] = {}
    # Shared circles (visible to the viewer as a member).
    rows = (
        await session.execute(
            text(
                """
                SELECT b.member_id, c.name
                FROM milavn_circle.circle_membership a
                JOIN milavn_circle.circle_membership b ON a.circle_id = b.circle_id AND b.member_id <> a.member_id AND b.left_at IS NULL
                JOIN milavn_circle.circle c ON c.id = a.circle_id
                WHERE a.member_id = :m AND a.left_at IS NULL
                """
            ),
            {"m": str(viewer_member_id)},
        )
    ).all()
    for member_id, circle_name in rows:
        reasons.setdefault(member_id, (f"In {circle_name} with you", "circle"))
    # Attended together (the viewer's own attended occurrences; co-attendee ids via definer helper).
    mine = (
        await session.execute(
            text(
                "SELECT p.occurrence_id, o.title FROM milavn_activity.participation p JOIN milavn_activity.occurrence o ON o.id = p.occurrence_id "
                "WHERE p.member_id = :m AND p.status IN ('attended','checked_in','going')"
            ),
            {"m": str(viewer_member_id)},
        )
    ).all()
    for occ_id, title in mine:
        ids = (await session.execute(text("SELECT milavn_activity.participant_member_ids(:o)"), {"o": str(occ_id)})).scalar_one()
        for other in list(ids or []):
            if other != viewer_member_id:
                reasons.setdefault(other, (f"Went to {title} with you", "attended"))

    out: list[Suggestion] = []
    names = await identity.display_names_for(list(reasons))
    for member_id, (reason, kind) in reasons.items():
        if await authz.is_blocked_either_way(session, viewer_member_id, member_id):
            continue
        location = await _public_location(session, member_id)
        out.append(
            Suggestion(
                member_id=member_id,
                display_name=names[member_id].display_name,
                avatar=names[member_id].avatar,
                reason=reason,
                reason_kind=kind,
                location_label=location,
                reputation=trust.label_text(await trust.reputation_labels(session, member_id=member_id)),
            )
        )
    out.sort(key=lambda s: (s.reason_kind != "attended", s.display_name))
    return out


# --- Free right now (FR119) ------------------------------------------------------

FREE_NOW_MAX_MINUTES = 240


async def set_free_now(session: AsyncSession, *, member_id: UUID, minutes: int, locality: str | None, note: str | None) -> dict:
    """[FR119] "I am free for the next couple of hours." Replaces any earlier one, expires by itself."""
    minutes = max(15, min(int(minutes), FREE_NOW_MAX_MINUTES))
    await session.execute(
        text(
            "INSERT INTO milavn_connect.free_now (member_id, until, locality, note) "
            "VALUES (:m, now() + make_interval(mins => :mins), NULLIF(:loc, ''), NULLIF(:note, '')) "
            "ON CONFLICT (member_id) DO UPDATE SET until = EXCLUDED.until, locality = EXCLUDED.locality, "
            "note = EXCLUDED.note, created_at = now()"
        ),
        {"m": str(member_id), "mins": minutes, "loc": (locality or "").strip(), "note": (note or "").strip()[:80]},
    )
    return {"minutes": minutes}


async def clear_free_now(session: AsyncSession, *, member_id: UUID) -> None:
    await session.execute(text("DELETE FROM milavn_connect.free_now WHERE member_id = :m"), {"m": str(member_id)})


async def my_free_now(session: AsyncSession, *, member_id: UUID) -> dict | None:
    row = (
        await session.execute(
            text("SELECT until, locality, note FROM milavn_connect.free_now WHERE member_id = :m AND until > now()"),
            {"m": str(member_id)},
        )
    ).first()
    return {"until": row[0].isoformat(), "locality": row[1], "note": row[2]} if row else None


async def free_now_nearby(session: AsyncSession, *, viewer_member_id: UUID) -> list[dict]:
    """[FR119] Who from the viewer's circles is free at the moment — never anyone else."""
    rows = (await session.execute(text("SELECT member_id, until, locality, note FROM milavn_connect.free_now_nearby(:v)"), {"v": str(viewer_member_id)})).all()
    names = await identity.display_names_for([r[0] for r in rows])
    return [
        {
            "member_id": str(r[0]),
            "display_name": names[r[0]].display_name,
            "avatar": names[r[0]].avatar,
            "until": r[1].isoformat(),
            "locality": r[2],
            "note": r[3],
        }
        for r in rows
    ]


# --- Would meet again (FR106) ----------------------------------------------------


class NotThere(Exception):
    """The chooser (or the person chosen) was not at this activity, or it has not started."""


async def meet_again_candidates(session: AsyncSession, *, occurrence_id: UUID, viewer_member_id: UUID) -> list[dict]:
    """People who were there, for someone who was there. `picked` is only ever the viewer's own choice."""
    rows = (
        await session.execute(text("SELECT member_id, picked FROM milavn_connect.meet_again_candidates(:o, :v)"), {"o": str(occurrence_id), "v": str(viewer_member_id)})
    ).all()
    names = await identity.display_names_for([r[0] for r in rows])
    people = [{"member_id": str(r[0]), "display_name": names[r[0]].display_name, "avatar": names[r[0]].avatar, "picked": bool(r[1])} for r in rows]
    return sorted(people, key=lambda p: p["display_name"])


async def pick_meet_again(session: AsyncSession, *, occurrence_id: UUID, chooser_member_id: UUID, chosen_member_id: UUID, pick: bool) -> bool:
    """Private pick (or un-pick). Returns True only when both have picked each other; the pair is told once."""
    if not pick:
        await session.execute(
            text("DELETE FROM milavn_connect.meet_again WHERE chooser_member_id = :c AND chosen_member_id = :d"),
            {"c": str(chooser_member_id), "d": str(chosen_member_id)},
        )
        return False
    result = (
        await session.execute(
            text("SELECT milavn_connect.pick_meet_again(:o, :c, :d)"), {"o": str(occurrence_id), "c": str(chooser_member_id), "d": str(chosen_member_id)}
        )
    ).scalar_one_or_none()
    if result is None:
        raise NotThere
    if result == "new_mutual":
        from app.events import bus

        await bus.publish(
            session,
            schema="milavn_trust",
            event_type="connection.formed",
            aggregate_id=occurrence_id,
            payload={"occurrence_id": occurrence_id, "member_ids": [chooser_member_id, chosen_member_id]},
        )
    return result in ("mutual", "new_mutual")


async def connections(session: AsyncSession, *, viewer_member_id: UUID) -> list[dict]:
    """People the viewer and they both said they would meet again — shown only to the two of them."""
    rows = (await session.execute(text("SELECT member_id, occurrence_title, formed_at FROM milavn_connect.my_connections(:v)"), {"v": str(viewer_member_id)})).all()
    names = await identity.display_names_for([r[0] for r in rows])
    return [{"member_id": str(r[0]), "display_name": names[r[0]].display_name, "avatar": names[r[0]].avatar, "title": r[1], "formed_at": r[2].isoformat()} for r in rows]


async def _public_location(session: AsyncSession, member_id: UUID) -> str | None:
    """[FR041] Another member's place, never more precise than THEY chose (definer read, migration 014; precision via 005)."""
    row = (await session.execute(text("SELECT locality_city, locality_zone, locality_locality FROM milavn_profile.public_locality(:m)"), {"m": str(member_id)})).first()
    if row is None or row[0] is None:
        return None
    city, zone, loc = locpriv.apply_precision(row[0], row[1], row[2], await _precision_of(session, member_id))
    return loc or zone or city


async def _precision_of(session: AsyncSession, member_id: UUID) -> str:
    row = (await session.execute(text("SELECT milavn_locationprivacy.precision_of(:m)"), {"m": str(member_id)})).first()
    return row[0] if row and row[0] else "locality"


async def _following(session: AsyncSession, viewer_member_id: UUID, host_member_id: UUID) -> bool:
    from app.components.activity import interface as activity

    return await activity.is_following(session, member_id=viewer_member_id, host_member_id=host_member_id)


async def public_profile(session: AsyncSession, *, viewer_member_id: UUID, member_id: UUID) -> dict | None:
    """The person page. Everything here is either what the person chose to show (bio, photo, interests,
    locality at their own precision) or what the community already knows (reputation labels, circles the
    viewer shares with them). Attendance history is never listed (FR040)."""
    if member_id != viewer_member_id and await authz.is_blocked_either_way(session, viewer_member_id, member_id):
        return None
    ident = (await identity.display_names_for([member_id]))[member_id]
    card = (await session.execute(text("SELECT bio, photo_ref, interest_tags FROM milavn_profile.public_card(:m)"), {"m": str(member_id)})).first()
    location = await _public_location(session, member_id)
    shared = (
        await session.execute(
            text(
                """
                SELECT c.id, c.name FROM milavn_circle.circle_membership a
                JOIN milavn_circle.circle_membership b ON a.circle_id = b.circle_id AND b.member_id = :other AND b.left_at IS NULL
                JOIN milavn_circle.circle c ON c.id = a.circle_id
                WHERE a.member_id = :m AND a.left_at IS NULL
                """
            ),
            {"m": str(viewer_member_id), "other": str(member_id)},
        )
    ).all()
    hosted = [r[0] for r in (await session.execute(text("SELECT milavn_activity.hosted_public_ids(:m)"), {"m": str(member_id)})).all()]
    from app.config.interests import TAG_LABELS

    tags = list(card[2] or []) if card else []
    return {
        "member_id": str(member_id),
        "display_name": ident.display_name,
        "handle": ident.handle,
        "avatar": (f"/media/{card[1]}" if card and card[1] else ident.avatar),
        "bio": card[0] if card else None,
        "interests": [TAG_LABELS.get(t, t) for t in tags],
        "location_label": location,
        "reputation": trust.label_text(await trust.reputation_labels(session, member_id=member_id)),
        # [FR116] "You have both been to N activities" — counted only for the viewer, only from
        # activities they were both actually at (migration 027).
        "familiar_count": int(
            (
                await session.execute(
                    text("SELECT milavn_activity.familiar_count(:v, :o)"),
                    {"v": str(viewer_member_id), "o": str(member_id)},
                )
            ).scalar_one()
        )
        if member_id != viewer_member_id
        else 0,
        # [FR122] Whether the viewer follows this host's calendar (private to the viewer).
        "following": await _following(session, viewer_member_id, member_id) if member_id != viewer_member_id else False,
        "shared_circles": [{"id": str(r[0]), "name": r[1]} for r in shared],
        "hosted_ids": hosted,
        "is_me": member_id == viewer_member_id,
        "can_message": member_id != viewer_member_id
        and bool((await session.execute(text("SELECT milavn_connect.can_message(:a, :b)"), {"a": str(viewer_member_id), "b": str(member_id)})).scalar_one()),
    }

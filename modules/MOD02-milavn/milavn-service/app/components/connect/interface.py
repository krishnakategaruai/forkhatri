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
    names = identity.display_names_for(list(reasons))
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


async def public_profile(session: AsyncSession, *, viewer_member_id: UUID, member_id: UUID) -> dict | None:
    """The person page. Everything here is either what the person chose to show (bio, photo, interests,
    locality at their own precision) or what the community already knows (reputation labels, circles the
    viewer shares with them). Attendance history is never listed (FR040)."""
    if member_id != viewer_member_id and await authz.is_blocked_either_way(session, viewer_member_id, member_id):
        return None
    ident = identity.display_names_for([member_id])[member_id]
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
        "shared_circles": [{"id": str(r[0]), "name": r[1]} for r in shared],
        "hosted_ids": hosted,
        "is_me": member_id == viewer_member_id,
    }

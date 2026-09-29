"""People to add to a circle — the "add people" picker (owner, 2026-09-29).

# "A big missing piece is adding people into our circle." Like adding people to a WhatsApp group
# or inviting friends to a Facebook group, the picker offers the people you already know first
# (`milavn_circle.people_i_know`, migration 044: shared circles, activities you were both at,
# mutual "meet again" connections, and chats), then anyone in Milavn whose name or handle matches.
# Blocked people (either way) and the viewer never appear. Each person's place is shown no more
# precisely than THEY chose (FR041), exactly as on their person page.
# Names live on the ForKhatri platform, not in Milavn, so a name search matches over the Milavn
# member pool with the platform's (cached) display names. Follow-up: a platform-side name search
# endpoint once Milavn has more members than a lookup batch comfortably covers.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.identity_bridge import interface as identity

MIN_QUERY = 2
LIMIT = 20


async def people_i_know(session: AsyncSession, *, viewer_member_id: UUID) -> dict[UUID, tuple[str, int]]:
    """member_id -> (strongest known_via, strength), strongest first."""
    rows = (await session.execute(text("SELECT member_id, known_via, strength FROM milavn_circle.people_i_know(:v)"), {"v": str(viewer_member_id)})).all()
    return {r[0]: (r[1], int(r[2])) for r in rows}


def _matches(q: str, ident: identity.MemberIdentity) -> int | None:
    """0 = name or handle starts with q, 1 = a later word starts with q, 2 = contains; None = no match."""
    name, handle = ident.display_name.lower(), ident.handle.lower()
    if name.startswith(q) or handle.startswith(q) or handle.lstrip("@").startswith(q):
        return 0
    if any(w.startswith(q) for w in name.split()):
        return 1
    if q in name or q in handle:
        return 2
    return None


async def search(session: AsyncSession, *, viewer_member_id: UUID, q: str | None, circle_id: UUID | None) -> list[dict]:
    from app.components.connect.interface import _public_location

    known = await people_i_know(session, viewer_member_id=viewer_member_id)
    query = (q or "").strip().lower()
    if not query:
        # No text yet: the people you know, as suggestions.
        picked = list(known)[:LIMIT]
        names = await identity.display_names_for(picked)
    elif len(query) < MIN_QUERY:
        return []
    else:
        pool = [r[0] for r in (await session.execute(text("SELECT milavn_circle.searchable_member_ids(:v)"), {"v": str(viewer_member_id)})).all()]
        names = await identity.display_names_for(pool)
        scored = []
        for mid in pool:
            rank = _matches(query, names[mid])
            if rank is None or names[mid].display_name == identity.FALLBACK_DISPLAY_NAME:
                continue
            k = known.get(mid)
            # People you know first (strongest bond first), then the closest name match, then A-Z.
            scored.append(((0 if k else 1, -(k[1] if k else 0), rank, names[mid].display_name.lower()), mid))
        picked = [mid for _key, mid in sorted(scored)[:LIMIT]]
    state: dict[UUID, tuple[bool, bool]] = {}
    if circle_id is not None and picked:
        rows = (
            await session.execute(
                text("SELECT member_id, already_member, invited FROM milavn_circle.invite_state(:c, :v, CAST(:ids AS uuid[]))"),
                {"c": str(circle_id), "v": str(viewer_member_id), "ids": [str(m) for m in picked]},
            )
        ).all()
        state = {r[0]: (bool(r[1]), bool(r[2])) for r in rows}
    photos = {
        mid: (await session.execute(text("SELECT photo_ref FROM milavn_profile.public_card(:m)"), {"m": str(mid)})).scalar_one_or_none() for mid in picked
    }
    out = []
    for mid in picked:
        ident = names[mid]
        member, invited = state.get(mid, (False, False))
        out.append(
            {
                "member_id": str(mid),
                "display_name": ident.display_name,
                "handle": ident.handle,
                "avatar": f"/media/{photos[mid]}" if photos.get(mid) else ident.avatar,
                "locality_label": await _public_location(session, mid),
                "known_via": known[mid][0] if mid in known else None,
                "already_member": member,
                "invited": invited,
            }
        )
    return out

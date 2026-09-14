"""Circle (incl. the minimal OrganizationScope) — public interface (`milavn_circle`).

# [FR020-FR029, TR16-TR24] Create/join/leave with enum-enforced types, organic
# circle-formation suggestions from a scheduled co-participation job (never
# auto-created), membership never a precondition elsewhere (TR18 — nothing
# outside this package reads `circle_membership`), community memory as an
# aggregate, and Organization as a deliberately minimal calendar-scope tag
# (TR23 DEC-001: `{organization_scope_id, display_name, created_by_member_id}`
# only).
# Approach: RLS (migration 001) already restricts non-open circles to members;
# this interface adds the write rules (creator seeds the organizer membership;
# join is immediate for open types; leave is a soft-delete via `left_at`).
# Traces to: TR16, TR17, TR18, TR19, TR20, TR21, TR22, TR23, TR24.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.events import bus

CIRCLE_TYPES = ("public", "community", "private", "organization", "interest", "local", "recurring_activity")
OPEN_TYPES = ("public", "community", "interest", "local", "recurring_activity")
TYPE_LABELS = {
    "public": "Public",
    "community": "Community",
    "private": "Private",
    "organization": "Organization",
    "interest": "Interest",
    "local": "Local",
    "recurring_activity": "Recurring activity",
}


def type_label(circle_type: str) -> str:
    """[FR002/FR021] The enum's label in the request language; English is the fallback."""
    from app.i18n import current_language, translate

    key = f"circle.type.{circle_type}"
    txt = translate(key, current_language.get())
    return TYPE_LABELS.get(circle_type, circle_type) if txt == key else txt


class CircleNotFound(Exception):
    pass


class NotMember(Exception):
    pass


class InvalidCircle(Exception):
    def __init__(self, fields: list[str]) -> None:
        super().__init__(str(fields))
        self.fields = fields


@dataclass(slots=True)
class Circle:
    id: UUID
    name: str
    circle_type: str
    description: str | None
    created_by_member_id: UUID
    created_at: datetime
    member_count: int
    viewer_role: str | None  # organizer | member | None
    locality_city: str | None = None  # [FR038] approximate home place of the circle; None = anywhere
    locality_locality: str | None = None
    near_you: bool = False  # in the viewer's own locality (or city-wide in their city)


_COLS = "c.id, c.name, c.circle_type::text, c.description, c.created_by_member_id, c.created_at, c.locality_city, c.locality_locality"


def _row(r, member_count: int, viewer_role: str | None) -> Circle:  # noqa: ANN001
    return Circle(r[0], r[1], r[2], r[3], r[4], r[5], member_count, viewer_role, r[6], r[7])


async def _count(session: AsyncSession, circle_id: UUID) -> int:
    return int((await session.execute(text("SELECT member_count FROM milavn_circle.community_memory(:c)"), {"c": str(circle_id)})).scalar_one() or 0)


async def _role(session: AsyncSession, circle_id: UUID, member_id: UUID) -> str | None:
    row = (
        await session.execute(
            text("SELECT member_role::text FROM milavn_circle.circle_membership WHERE circle_id = :c AND member_id = :m AND left_at IS NULL"),
            {"c": str(circle_id), "m": str(member_id)},
        )
    ).first()
    return row[0] if row else None


async def get(session: AsyncSession, *, circle_id: UUID, viewer_member_id: UUID) -> Circle:
    r = (await session.execute(text(f"SELECT {_COLS} FROM milavn_circle.circle c WHERE c.id = :id"), {"id": str(circle_id)})).first()
    if r is None:
        raise CircleNotFound
    return _row(r, await _count(session, circle_id), await _role(session, circle_id, viewer_member_id))


async def create(
    session: AsyncSession,
    *,
    creator_member_id: UUID,
    name: str,
    circle_type: str,
    description: str | None,
    locality_city: str | None = None,
    locality_locality: str | None = None,
) -> Circle:
    fields = []
    if not name or not name.strip():
        fields.append("name")
    if circle_type not in CIRCLE_TYPES:  # [FR021] enum, never free text
        fields.append("circle_type")
    if fields:
        raise InvalidCircle(fields)
    circle_id = uuid4()
    await session.execute(
        text(
            "INSERT INTO milavn_circle.circle (id, name, circle_type, description, created_by_member_id, locality_city, locality_locality) "
            "VALUES (:id, :name, CAST(:t AS milavn_circle.circle_type), NULLIF(:d, ''), :creator, NULLIF(:city, ''), NULLIF(:loc, ''))"
        ),
        {
            "id": str(circle_id),
            "name": name.strip(),
            "t": circle_type,
            "d": (description or "").strip(),
            "creator": str(creator_member_id),
            "city": (locality_city or "").strip(),
            "loc": (locality_locality or "").strip(),
        },
    )
    await session.execute(
        text("INSERT INTO milavn_circle.circle_membership (circle_id, member_id, member_role) VALUES (:c, :m, 'organizer')"),
        {"c": str(circle_id), "m": str(creator_member_id)},
    )
    await bus.publish(
        session, schema="milavn_circle", event_type="circle.created", aggregate_id=circle_id, payload={"circle_id": circle_id, "creator_member_id": creator_member_id}
    )
    return await get(session, circle_id=circle_id, viewer_member_id=creator_member_id)


async def join(session: AsyncSession, *, circle_id: UUID, member_id: UUID) -> Circle:
    r = (await session.execute(text("SELECT circle_type::text FROM milavn_circle.circle WHERE id = :id"), {"id": str(circle_id)})).first()
    if r is None:
        raise CircleNotFound
    if r[0] not in OPEN_TYPES:
        # [FR021] Private/organization circles are join-by-invite; the creator adds members.
        raise NotMember
    await session.execute(
        text(
            """
            INSERT INTO milavn_circle.circle_membership (circle_id, member_id, member_role) VALUES (:c, :m, 'member')
            ON CONFLICT DO NOTHING
            """
        ),
        {"c": str(circle_id), "m": str(member_id)},
    )
    await bus.publish(session, schema="milavn_circle", event_type="circle.joined", aggregate_id=circle_id, payload={"circle_id": circle_id, "member_id": member_id})
    return await get(session, circle_id=circle_id, viewer_member_id=member_id)


async def add_member(session: AsyncSession, *, circle_id: UUID, actor_member_id: UUID, member_id: UUID) -> None:
    r = (await session.execute(text("SELECT created_by_member_id FROM milavn_circle.circle WHERE id = :id"), {"id": str(circle_id)})).first()
    if r is None:
        raise CircleNotFound
    if r[0] != actor_member_id:
        raise NotMember
    await session.execute(
        text("INSERT INTO milavn_circle.circle_membership (circle_id, member_id, member_role) VALUES (:c, :m, 'member') ON CONFLICT DO NOTHING"),
        {"c": str(circle_id), "m": str(member_id)},
    )


async def leave(session: AsyncSession, *, circle_id: UUID, member_id: UUID) -> None:
    """[FR020] Immediate, no approval — the acting member's own row only."""
    await session.execute(
        text("UPDATE milavn_circle.circle_membership SET left_at = now() WHERE circle_id = :c AND member_id = :m AND left_at IS NULL"),
        {"c": str(circle_id), "m": str(member_id)},
    )
    await bus.publish(session, schema="milavn_circle", event_type="circle.left", aggregate_id=circle_id, payload={"circle_id": circle_id, "member_id": member_id})


async def my_circle_ids(session: AsyncSession, *, member_id: UUID) -> list[UUID]:
    rows = (
        await session.execute(
            text("SELECT circle_id FROM milavn_circle.circle_membership WHERE member_id = :m AND left_at IS NULL"),
            {"m": str(member_id)},
        )
    ).all()
    return [r[0] for r in rows]


async def mine(session: AsyncSession, *, member_id: UUID) -> list[Circle]:
    rows = (
        await session.execute(
            text(
                f"SELECT {_COLS}, m.member_role::text FROM milavn_circle.circle c "
                "JOIN milavn_circle.circle_membership m ON m.circle_id = c.id AND m.member_id = :m AND m.left_at IS NULL "
                "ORDER BY c.created_at DESC"
            ),
            {"m": str(member_id)},
        )
    ).all()
    return [_row(r, await _count(session, r[0]), r[6]) for r in rows]


async def discover(
    session: AsyncSession,
    *,
    viewer_member_id: UUID,
    query: str | None = None,
    viewer_city: str | None = None,
    viewer_locality: str | None = None,
    near_only: bool = False,
) -> list[Circle]:
    """[FR025] Open circles are visible per their type; RLS hides the rest. The viewer's own
    locality comes first, then the rest of their city, then everywhere (local relevance, thesis §84)."""
    params: dict = {"m": str(viewer_member_id), "city": viewer_city or "", "loc": viewer_locality or ""}
    where = "WHERE c.circle_type IN ('public','community','interest','local','recurring_activity')"
    if query:
        where += " AND (c.name ILIKE '%' || :q || '%' OR coalesce(c.description,'') ILIKE '%' || :q || '%')"
        params["q"] = query.strip()
    if near_only and viewer_city:
        where += " AND c.locality_city = :city AND (c.locality_locality IS NULL OR c.locality_locality = :loc)"
    order = "ORDER BY (c.locality_city = :city AND c.locality_locality = :loc) DESC NULLS LAST, (c.locality_city = :city) DESC NULLS LAST, c.created_at DESC"
    rows = (await session.execute(text(f"SELECT {_COLS} FROM milavn_circle.circle c {where} {order} LIMIT 100"), params)).all()
    out: list[Circle] = []
    for r in rows:
        c = _row(r, await _count(session, r[0]), await _role(session, r[0], viewer_member_id))
        c.near_you = bool(viewer_city) and c.locality_city == viewer_city and (c.locality_locality is None or c.locality_locality == viewer_locality)
        out.append(c)
    return out


async def members(session: AsyncSession, *, circle_id: UUID, viewer_member_id: UUID) -> list[tuple[UUID, str, datetime]]:
    rows = (
        await session.execute(
            text(
                "SELECT member_id, member_role::text, joined_at FROM milavn_circle.circle_membership "
                "WHERE circle_id = :c AND left_at IS NULL ORDER BY member_role DESC, joined_at"
            ),
            {"c": str(circle_id)},
        )
    ).all()
    return [(r[0], r[1], r[2]) for r in rows]


async def community_memory(session: AsyncSession, *, circle_id: UUID, viewer_member_id: UUID) -> dict:
    """[FR024] Aggregate only, members-only (non-members of a non-open circle can't even see the circle)."""
    role = await _role(session, circle_id, viewer_member_id)
    r = (await session.execute(text("SELECT circle_type::text FROM milavn_circle.circle WHERE id = :id"), {"id": str(circle_id)})).first()
    if r is None:
        raise CircleNotFound
    if role is None and r[0] not in OPEN_TYPES:
        raise NotMember
    row = (await session.execute(text("SELECT * FROM milavn_circle.community_memory(:c)"), {"c": str(circle_id)})).first()
    return {"member_count": row[0], "activities_held": row[1], "upcoming_count": row[2], "first_activity_at": row[3]}


# --- Organization scope (FR028, TR23) ------------------------------------------


async def create_organization_scope(session: AsyncSession, *, creator_member_id: UUID, display_name: str) -> dict:
    if not display_name.strip():
        raise InvalidCircle(["display_name"])
    scope_id = uuid4()
    await session.execute(
        text("INSERT INTO milavn_circle.organization_scope (organization_scope_id, display_name, created_by_member_id) VALUES (:id, :n, :c)"),
        {"id": str(scope_id), "n": display_name.strip(), "c": str(creator_member_id)},
    )
    return {"organization_scope_id": scope_id, "display_name": display_name.strip(), "created_by_member_id": creator_member_id}


async def list_organization_scopes(session: AsyncSession) -> list[dict]:
    rows = (
        await session.execute(text("SELECT organization_scope_id, display_name, created_by_member_id FROM milavn_circle.organization_scope ORDER BY display_name"))
    ).all()
    return [dict(r._mapping) for r in rows]


# --- Circle-formation suggestions (FR022, TR17) ---------------------------------


async def pending_suggestions(session: AsyncSession, *, member_id: UUID) -> list[dict]:
    rows = (
        await session.execute(
            text(
                """
                SELECT s.id, s.suggested_circle_name, s.status::text, s.created_at,
                       milavn_circle.suggestion_member_ids(s.id) AS members
                FROM milavn_circle.circle_formation_suggestion s
                JOIN milavn_circle.circle_formation_suggestion_member sm ON sm.suggestion_id = s.id AND sm.member_id = :m
                WHERE s.status = 'pending' AND sm.responded_at IS NULL
                ORDER BY s.created_at DESC
                """
            ),
            {"m": str(member_id)},
        )
    ).all()
    return [{"id": r[0], "name": r[1], "status": r[2], "created_at": r[3], "member_ids": list(r[4] or [])} for r in rows]


async def respond_suggestion(session: AsyncSession, *, suggestion_id: UUID, member_id: UUID, accept: bool) -> Circle | None:
    await session.execute(
        text("UPDATE milavn_circle.circle_formation_suggestion_member SET responded_at = now() WHERE suggestion_id = :s AND member_id = :m"),
        {"s": str(suggestion_id), "m": str(member_id)},
    )
    if not accept:
        return None
    r = (await session.execute(text("SELECT suggested_circle_name FROM milavn_circle.circle_formation_suggestion WHERE id = :s"), {"s": str(suggestion_id)})).first()
    if r is None:
        return None
    # [FR022] A human accepts -> a real circle is created by that human, others may join.
    circle = await create(
        session, creator_member_id=member_id, name=r[0], circle_type="recurring_activity", description="Started from people who kept showing up together."
    )
    await session.execute(
        text("UPDATE milavn_circle.circle_formation_suggestion SET status = 'accepted', responded_at = now() WHERE id = :s"),
        {"s": str(suggestion_id)},
    )
    return circle


async def run_suggestion_job(session: AsyncSession, *, min_shared: int = 2) -> int:
    """[TR17] Scheduled: co-participation pairs -> one pending suggestion per pair (idempotent)."""
    from app.components.identity_bridge import interface as identity

    rows = (await session.execute(text("SELECT * FROM milavn_circle.co_participation_pairs(:n)"), {"n": min_shared})).all()
    created = 0
    for a, b, _shared in rows:
        exists = (await session.execute(text("SELECT milavn_circle.suggestion_exists_for_pair(:a, :b)"), {"a": str(a), "b": str(b)})).scalar_one()
        if exists:
            continue
        names = identity.display_names_for([a, b])
        name = f"{names[a].display_name.split()[0]} & {names[b].display_name.split()[0]}'s circle"
        # The job writes rows for other members; that goes through the definer-owned
        # function (migration 008) rather than widening the member-self policy.
        sid = (
            await session.execute(
                text("SELECT milavn_circle.create_formation_suggestion(:n, :ids)"),
                {"n": name, "ids": [str(a), str(b)]},
            )
        ).scalar_one()
        await bus.publish(
            session, schema="milavn_circle", event_type="circle.suggestion", aggregate_id=sid, payload={"suggestion_id": sid, "member_ids": [a, b], "name": name}
        )
        created += 1
    return created


# touch

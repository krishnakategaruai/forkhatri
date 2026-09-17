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

CIRCLE_TYPES = ("public", "community", "private", "organization", "interest", "local", "recurring_activity", "temple", "travel")
# [FR125] temple/travel are open like interest/local — a yatra or a trip is something you join, not something you are invited into.
OPEN_TYPES = ("public", "community", "interest", "local", "recurring_activity", "temple", "travel")
DATE_BOUND_TYPES = ("temple", "travel")  # [FR125] the two types that carry a date
TYPE_LABELS = {
    "public": "Public",
    "community": "Community",
    "private": "Private",
    "organization": "Organization",
    "interest": "Interest",
    "local": "Local",
    "recurring_activity": "Recurring activity",
    "temple": "Temple visit",  # [FR125]
    "travel": "Travel",  # [FR125]
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
    join_policy: str = "open"  # [FR115] 'open' or 'approval'
    join_questions: tuple[str, ...] = ()  # [FR115] what the organizer asks before letting someone in
    starts_on: str | None = None  # [FR125] ISO date — a temple visit's day, or a trip's first day
    ends_on: str | None = None  # [FR125] a trip's last day; None for a single day
    group_id: UUID | None = None  # [FR123] the umbrella this circle sits under, if any


_COLS = (
    "c.id, c.name, c.circle_type::text, c.description, c.created_by_member_id, c.created_at, "
    "c.locality_city, c.locality_locality, c.join_policy, c.join_questions, c.starts_on, c.ends_on, c.group_id"
)


def _row(r, member_count: int, viewer_role: str | None) -> Circle:  # noqa: ANN001
    circle = Circle(r[0], r[1], r[2], r[3], r[4], r[5], member_count, viewer_role, r[6], r[7])
    circle.join_policy = r[8] or "open"
    circle.join_questions = tuple(r[9] or ())
    circle.starts_on = r[10].isoformat() if r[10] else None
    circle.ends_on = r[11].isoformat() if r[11] else None
    circle.group_id = r[12]
    return circle


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
    join_policy: str = "open",
    join_questions: list[str] | None = None,
    starts_on: str | None = None,
    ends_on: str | None = None,
) -> Circle:
    fields = invalid_join_setup(join_policy, join_questions)
    if not name or not name.strip():
        fields.append("name")
    if circle_type not in CIRCLE_TYPES:  # [FR021] enum, never free text
        fields.append("circle_type")
    # [FR125] A temple visit or a trip is nothing without its date; a date on any other circle type
    # is nonsensical (an ordinary interest circle is not "about" a day) so it is refused there too.
    if circle_type in DATE_BOUND_TYPES and not starts_on:
        fields.append("starts_on")
    if circle_type not in DATE_BOUND_TYPES and (starts_on or ends_on):
        fields.append("starts_on")
    if starts_on and ends_on and ends_on < starts_on:
        fields.append("ends_on")
    if fields:
        raise InvalidCircle(fields)
    circle_id = uuid4()
    await session.execute(
        text(
            "INSERT INTO milavn_circle.circle (id, name, circle_type, description, created_by_member_id, locality_city, locality_locality, "
            "join_policy, join_questions, starts_on, ends_on) "
            "VALUES (:id, :name, CAST(:t AS milavn_circle.circle_type), NULLIF(:d, ''), :creator, NULLIF(:city, ''), NULLIF(:loc, ''), "
            ":policy, CAST(:questions AS text[]), CAST(NULLIF(:starts, '') AS date), CAST(NULLIF(:ends, '') AS date))"
        ),
        {
            "id": str(circle_id),
            "name": name.strip(),
            "t": circle_type,
            "d": (description or "").strip(),
            "creator": str(creator_member_id),
            "city": (locality_city or "").strip(),
            "loc": (locality_locality or "").strip(),
            "policy": join_policy,
            "questions": [q.strip() for q in (join_questions or []) if q and q.strip()],
            "starts": starts_on or "",
            "ends": ends_on or "",
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


# --- Joining: questions and the organizer's yes (FR115) ---------------------------

MAX_JOIN_QUESTIONS = 3
JOIN_POLICIES = ("open", "approval")


def invalid_join_setup(join_policy: str, join_questions: list[str] | None) -> list[str]:
    """[FR115] Known policy, at most three short questions, nothing blank."""
    bad: list[str] = []
    if join_policy not in JOIN_POLICIES:
        bad.append("join_policy")
    questions = [q.strip() for q in (join_questions or []) if q and q.strip()]
    if len(questions) > MAX_JOIN_QUESTIONS or any(len(q) > 120 for q in questions):
        bad.append("join_questions")
    return bad


async def request_join(session: AsyncSession, *, circle_id: UUID, member_id: UUID, answers: list[str] | None = None) -> str:
    """[FR115] Ask to join. An open circle admits straight away ("joined"); a circle that asks first
    records the request with the answers ("pending") for its organizer to decide."""
    result = (
        await session.execute(
            text("SELECT milavn_circle.request_to_join(:c, :m, CAST(:a AS text[]))"),
            {"c": str(circle_id), "m": str(member_id), "a": [a.strip()[:500] for a in (answers or []) if a is not None]},
        )
    ).scalar_one_or_none()
    if result is None:
        raise CircleNotFound
    if result == "joined":
        await bus.publish(
            session,
            schema="milavn_circle",
            event_type="circle.joined",
            aggregate_id=circle_id,
            payload={"circle_id": circle_id, "member_id": member_id},
        )
    elif result == "pending":
        await bus.publish(
            session,
            schema="milavn_circle",
            event_type="circle.join_requested",
            aggregate_id=circle_id,
            payload={"circle_id": circle_id, "member_id": member_id},
        )
    return result


async def join_prompt(session: AsyncSession, *, circle_id: UUID, member_id: UUID) -> dict | None:
    """[FR115] What someone outside the circle may see before asking: its name, whether it screens,
    and the questions they will be asked. Nothing else about the circle is exposed (migration 026)."""
    row = (await session.execute(text("SELECT circle_name, join_policy, join_questions FROM milavn_circle.join_prompt(:c)"), {"c": str(circle_id)})).first()
    if row is None:
        return None
    return {
        "circle_name": row[0],
        "join_policy": row[1] or "open",
        "join_questions": list(row[2] or []),
        "my_request_status": await my_request_status(session, circle_id=circle_id, member_id=member_id),
    }


async def my_request_status(session: AsyncSession, *, circle_id: UUID, member_id: UUID) -> str | None:
    return (await session.execute(text("SELECT milavn_circle.my_join_request_status(:c, :m)"), {"c": str(circle_id), "m": str(member_id)})).scalar_one_or_none()


async def set_role(session: AsyncSession, *, circle_id: UUID, actor_member_id: UUID, member_id: UUID, role: str) -> bool:
    """[FR121] The organizer asks someone to help run the circle, or steps them back down.
    Nobody can give themselves a role, and the creator's own role is not editable."""
    return bool(
        (
            await session.execute(
                text("SELECT milavn_circle.set_circle_role(:c, :a, :m, :r)"),
                {"c": str(circle_id), "a": str(actor_member_id), "m": str(member_id), "r": role},
            )
        ).scalar_one()
    )


async def pending_requests(session: AsyncSession, *, circle_id: UUID, viewer_member_id: UUID) -> list[dict]:
    """[FR115] What the organizer sees: who is waiting, what they answered, and since when."""
    rows = (
        await session.execute(
            text("SELECT request_id, member_id, answers, created_at FROM milavn_circle.pending_join_requests(:c, :v)"),
            {"c": str(circle_id), "v": str(viewer_member_id)},
        )
    ).all()
    from app.components.identity_bridge import interface as identity

    names = await identity.display_names_for([r[1] for r in rows])
    return [
        {
            "request_id": str(r[0]),
            "member_id": str(r[1]),
            "display_name": names[r[1]].display_name,
            "avatar": names[r[1]].avatar,
            "answers": list(r[2] or []),
            "created_at": r[3].isoformat(),
        }
        for r in rows
    ]


async def decide_request(session: AsyncSession, *, circle_id: UUID, request_id: UUID, actor_member_id: UUID, approve: bool) -> UUID:
    """[FR115] The organizer's yes or no, once. Returns the member it was about."""
    member_id = (
        await session.execute(
            text("SELECT milavn_circle.decide_join_request(:r, :a, :ok)"),
            {"r": str(request_id), "a": str(actor_member_id), "ok": approve},
        )
    ).scalar_one_or_none()
    if member_id is None:
        raise NotMember
    await bus.publish(
        session,
        schema="milavn_circle",
        event_type="circle.join_decided",
        aggregate_id=request_id,
        payload={"request_id": request_id, "circle_id": circle_id, "member_id": member_id, "approved": approve},
    )
    return member_id


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
    # [Found live, 2026-09-18] `m.member_role::text` is appended AFTER `_COLS`, so its index moves
    # every time `_COLS` grows — a fixed `r[6]` here (accidentally the locality_city column instead)
    # silently reported the wrong "role" as soon as FR115 added two more columns to `_COLS`. `r[-1]`
    # is the correct, always-last appended column, and stays correct no matter how `_COLS` grows.
    return [_row(r, await _count(session, r[0]), r[-1]) for r in rows]


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
    # [FR125] Once a temple visit or trip's date has passed there is nothing left to plan or join —
    # it drops out of discovery (it still shows in the member's own `mine()` list, like a past activity).
    where = (
        "WHERE c.circle_type IN ('public','community','interest','local','recurring_activity','temple','travel') "
        "AND NOT (c.circle_type IN ('temple','travel') AND coalesce(c.ends_on, c.starts_on) < CURRENT_DATE)"
    )
    if query:
        where += " AND (c.name ILIKE '%' || :q || '%' OR coalesce(c.description,'') ILIKE '%' || :q || '%')"
        params["q"] = query.strip()
    if near_only and viewer_city:
        where += " AND c.locality_city = :city AND (c.locality_locality IS NULL OR c.locality_locality = :loc)"
    order = (
        "ORDER BY (c.locality_city = :city AND c.locality_locality = :loc) DESC NULLS LAST, (c.locality_city = :city) DESC NULLS LAST, "
        "c.starts_on ASC NULLS LAST, c.created_at DESC"
    )
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


# --- Asking the circle (FR120) ----------------------------------------------------

POLL_KINDS = ("date", "activity")
MAX_OPTIONS = 6


class InvalidPoll(Exception):
    def __init__(self, fields: list[str]) -> None:
        super().__init__(str(fields))
        self.fields = fields


async def create_poll(session: AsyncSession, *, circle_id: UUID, member_id: UUID, question: str, kind: str, options: list[dict]) -> UUID:
    """[FR120] One question, up to six answers. A date poll's options are times; an activity poll's
    options point at activities already posted. Only a member of the circle can ask (RLS)."""
    clean = [o for o in options if (o.get("label") or "").strip()]
    bad: list[str] = []
    if not question.strip() or len(question.strip()) > 160:
        bad.append("question")
    if kind not in POLL_KINDS:
        bad.append("kind")
    if not 2 <= len(clean) <= MAX_OPTIONS:
        bad.append("options")
    if bad:
        raise InvalidPoll(bad)
    poll_id = uuid4()
    await session.execute(
        text("INSERT INTO milavn_circle.poll (id, circle_id, created_by_member_id, question, kind) VALUES (:id, :c, :m, :q, :k)"),
        {"id": str(poll_id), "c": str(circle_id), "m": str(member_id), "q": question.strip(), "k": kind},
    )
    for i, option in enumerate(clean):
        await session.execute(
            text("INSERT INTO milavn_circle.poll_option (poll_id, label, option_time, occurrence_id, position) VALUES (:p, :l, :t, :o, :i)"),
            {
                "p": str(poll_id),
                "l": str(option["label"]).strip()[:120],
                "t": option.get("option_time"),
                "o": str(option["occurrence_id"]) if option.get("occurrence_id") else None,
                "i": i,
            },
        )
    await bus.publish(
        session,
        schema="milavn_circle",
        event_type="poll.created",
        aggregate_id=circle_id,
        payload={"circle_id": circle_id, "poll_id": poll_id, "created_by_member_id": member_id},
    )
    return poll_id


async def polls(session: AsyncSession, *, circle_id: UUID, member_id: UUID) -> list[dict]:
    """[FR120] The circle's open questions, newest first, with who picked what — inside a circle the
    names are the useful part ("Meera and Ravi can do Sunday"), exactly as a group chat poll shows."""
    rows = (
        await session.execute(
            text("SELECT id, question, kind, created_by_member_id, created_at, closed_at FROM milavn_circle.poll WHERE circle_id = :c ORDER BY created_at DESC LIMIT 10"),
            {"c": str(circle_id)},
        )
    ).all()
    if not rows:
        return []
    poll_ids = [r[0] for r in rows]
    options = (
        await session.execute(
            text("SELECT id, poll_id, label, option_time, occurrence_id, position FROM milavn_circle.poll_option WHERE poll_id = ANY(:ids) ORDER BY position"),
            {"ids": poll_ids},
        )
    ).all()
    votes = (await session.execute(text("SELECT option_id, member_id FROM milavn_circle.poll_vote WHERE poll_id = ANY(:ids)"), {"ids": poll_ids})).all()
    from app.components.identity_bridge import interface as identity

    names = await identity.display_names_for([v[1] for v in votes] + [r[3] for r in rows])
    by_option: dict[UUID, list[UUID]] = {}
    for option_id, voter in votes:
        by_option.setdefault(option_id, []).append(voter)
    out = []
    for r in rows:
        out.append(
            {
                "id": str(r[0]),
                "question": r[1],
                "kind": r[2],
                "asked_by": names[r[3]].display_name if r[3] in names else "",
                "mine": r[3] == member_id,
                "created_at": r[4].isoformat(),
                "closed": r[5] is not None,
                "options": [
                    {
                        "id": str(o[0]),
                        "label": o[2],
                        "option_time": o[3].isoformat() if o[3] else None,
                        "occurrence_id": str(o[4]) if o[4] else None,
                        "voters": [names[v].display_name for v in by_option.get(o[0], []) if v in names],
                        "voted": member_id in by_option.get(o[0], []),
                    }
                    for o in options
                    if o[1] == r[0]
                ],
            }
        )
    return out


async def vote(session: AsyncSession, *, poll_id: UUID, option_id: UUID, member_id: UUID, picked: bool) -> None:
    """[FR120] Pick an option, or take the pick back. Several options may be picked — most people
    can do more than one day, and pretending otherwise produces a worse answer."""
    if picked:
        await session.execute(
            text("INSERT INTO milavn_circle.poll_vote (option_id, member_id, poll_id) VALUES (:o, :m, :p) ON CONFLICT DO NOTHING"),
            {"o": str(option_id), "m": str(member_id), "p": str(poll_id)},
        )
    else:
        await session.execute(
            text("DELETE FROM milavn_circle.poll_vote WHERE option_id = :o AND member_id = :m"),
            {"o": str(option_id), "m": str(member_id)},
        )


async def close_poll(session: AsyncSession, *, poll_id: UUID, member_id: UUID) -> None:
    """[FR120] The person who asked decides when it is settled (RLS allows nobody else)."""
    await session.execute(
        text("UPDATE milavn_circle.poll SET closed_at = now() WHERE id = :p AND created_by_member_id = :m AND closed_at IS NULL"),
        {"p": str(poll_id), "m": str(member_id)},
    )


# --- Chapters under one umbrella (FR123) ------------------------------------------


async def create_group(session: AsyncSession, *, name: str, description: str | None, member_id: UUID) -> UUID:
    """[FR123] Start an umbrella (a samaj, an alumni body) that chapters can sit under."""
    if not name.strip() or len(name.strip()) > 80:
        raise InvalidCircle(["name"])
    group_id = uuid4()
    await session.execute(
        text("INSERT INTO milavn_circle.circle_group (id, name, description, created_by_member_id) VALUES (:id, :n, NULLIF(:d, ''), :m)"),
        {"id": str(group_id), "n": name.strip(), "d": (description or "").strip(), "m": str(member_id)},
    )
    return group_id


async def set_group(session: AsyncSession, *, circle_id: UUID, actor_member_id: UUID, group_id: UUID | None) -> bool:
    """[FR123] Put this circle under an umbrella, or take it out. Its organizer decides."""
    return bool(
        (
            await session.execute(
                text("SELECT milavn_circle.set_circle_group(:c, :a, :g)"),
                {"c": str(circle_id), "a": str(actor_member_id), "g": str(group_id) if group_id else None},
            )
        ).scalar_one()
    )


async def groups(session: AsyncSession) -> list[dict]:
    rows = (await session.execute(text("SELECT id, name, description FROM milavn_circle.circle_group ORDER BY name LIMIT 100"))).all()
    return [{"id": str(r[0]), "name": r[1], "description": r[2]} for r in rows]


async def chapters(session: AsyncSession, *, group_id: UUID) -> list[dict]:
    """[FR123] The chapters under one umbrella: name, place, size, and whether they ask first —
    enough for someone who has moved city to find their people and knock on the right door."""
    rows = (
        await session.execute(
            text("SELECT circle_id, name, locality, member_count, join_policy FROM milavn_circle.group_chapters(:g)"),
            {"g": str(group_id)},
        )
    ).all()
    return [{"circle_id": str(r[0]), "name": r[1], "locality": r[2], "member_count": r[3], "join_policy": r[4]} for r in rows]


async def group_of(session: AsyncSession, *, circle_id: UUID) -> dict | None:
    row = (
        await session.execute(
            text("SELECT g.id, g.name FROM milavn_circle.circle c JOIN milavn_circle.circle_group g ON g.id = c.group_id WHERE c.id = :c"),
            {"c": str(circle_id)},
        )
    ).first()
    return {"id": str(row[0]), "name": row[1]} if row else None


# --- A drive for something the community needs (FR124) ----------------------------


class InvalidFundraiser(Exception):
    def __init__(self, fields: list[str]) -> None:
        super().__init__(str(fields))
        self.fields = fields


async def create_fundraiser(
    session: AsyncSession, *, circle_id: UUID, member_id: UUID, title: str, purpose: str | None, target_paise: int | None, closes_on: str | None
) -> UUID:
    """[FR124] Start a drive. Money does not move in Milavn yet (blocker B1) — this records what the
    community has promised, which is what the hand-kept list in a WhatsApp group does today."""
    bad: list[str] = []
    if not title.strip() or len(title.strip()) > 120:
        bad.append("title")
    if target_paise is not None and not 10_000 <= int(target_paise) <= 1_000_000_000:
        bad.append("target_paise")
    if bad:
        raise InvalidFundraiser(bad)
    fundraiser_id = uuid4()
    await session.execute(
        text(
            "INSERT INTO milavn_circle.fundraiser (id, circle_id, created_by_member_id, title, purpose, target_paise, closes_on) "
            "VALUES (:id, :c, :m, :t, NULLIF(:p, ''), :target, CAST(NULLIF(:closes, '') AS date))"
        ),
        {
            "id": str(fundraiser_id),
            "c": str(circle_id),
            "m": str(member_id),
            "t": title.strip(),
            "p": (purpose or "").strip(),
            "target": target_paise,
            "closes": closes_on or "",
        },
    )
    await bus.publish(
        session,
        schema="milavn_circle",
        event_type="fundraiser.started",
        aggregate_id=circle_id,
        payload={"circle_id": circle_id, "fundraiser_id": fundraiser_id, "created_by_member_id": member_id},
    )
    return fundraiser_id


async def fundraisers(session: AsyncSession, *, circle_id: UUID, member_id: UUID) -> list[dict]:
    """[FR124] The circle's drives with their totals. Individual amounts are never in this list —
    only the organizers see who promised what, through `pledge_list`."""
    rows = (
        await session.execute(
            text(
                "SELECT id, title, purpose, target_paise, closes_on, closed_at, created_by_member_id "
                "FROM milavn_circle.fundraiser WHERE circle_id = :c ORDER BY created_at DESC LIMIT 10"
            ),
            {"c": str(circle_id)},
        )
    ).all()
    out = []
    for r in rows:
        totals = (await session.execute(text("SELECT promised_paise, people, paid_paise FROM milavn_circle.fundraiser_totals(:f)"), {"f": str(r[0])})).first()
        mine = (
            await session.execute(
                text("SELECT amount_paise, note, paid_at FROM milavn_circle.fundraiser_pledge WHERE fundraiser_id = :f AND member_id = :m"),
                {"f": str(r[0]), "m": str(member_id)},
            )
        ).first()
        out.append(
            {
                "id": str(r[0]),
                "title": r[1],
                "purpose": r[2],
                "target_paise": int(r[3]) if r[3] is not None else None,
                "closes_on": r[4].isoformat() if r[4] else None,
                "closed": r[5] is not None,
                "mine": r[6] == member_id,
                "promised_paise": int(totals[0]) if totals else 0,
                "people": int(totals[1]) if totals else 0,
                "paid_paise": int(totals[2]) if totals else 0,
                "my_pledge": {"amount_paise": int(mine[0]), "note": mine[1], "paid": mine[2] is not None} if mine else None,
            }
        )
    return out


async def pledge(session: AsyncSession, *, fundraiser_id: UUID, member_id: UUID, amount_paise: int | None, note: str | None) -> None:
    """[FR124] Promise an amount, change it, or take the promise back (amount None)."""
    if amount_paise is None:
        await session.execute(
            text("DELETE FROM milavn_circle.fundraiser_pledge WHERE fundraiser_id = :f AND member_id = :m"),
            {"f": str(fundraiser_id), "m": str(member_id)},
        )
        return
    if not 10_000 <= int(amount_paise) <= 100_000_000:
        raise InvalidFundraiser(["amount_paise"])
    await session.execute(
        text(
            "INSERT INTO milavn_circle.fundraiser_pledge (fundraiser_id, member_id, amount_paise, note) "
            "VALUES (:f, :m, :a, NULLIF(:n, '')) "
            "ON CONFLICT (fundraiser_id, member_id) DO UPDATE SET amount_paise = EXCLUDED.amount_paise, note = EXCLUDED.note"
        ),
        {"f": str(fundraiser_id), "m": str(member_id), "a": int(amount_paise), "n": (note or "").strip()[:140]},
    )


async def pledge_list(session: AsyncSession, *, fundraiser_id: UUID, viewer_member_id: UUID) -> list[dict]:
    """[FR124] The organizer's reconciliation list — who promised what, and what has arrived."""
    rows = (
        await session.execute(
            text("SELECT member_id, amount_paise, note, created_at, paid_at FROM milavn_circle.fundraiser_pledges(:f, :v)"),
            {"f": str(fundraiser_id), "v": str(viewer_member_id)},
        )
    ).all()
    from app.components.identity_bridge import interface as identity

    names = await identity.display_names_for([r[0] for r in rows])
    return [
        {
            "member_id": str(r[0]),
            "display_name": names[r[0]].display_name,
            "amount_paise": int(r[1]),
            "note": r[2],
            "created_at": r[3].isoformat(),
            "paid": r[4] is not None,
        }
        for r in rows
    ]


async def mark_pledge_paid(session: AsyncSession, *, fundraiser_id: UUID, member_id: UUID, actor_member_id: UUID, paid: bool) -> bool:
    """[FR124] Until Payment Services exists (blocker B1), the organizer ticks off what has actually
    arrived — by hand, exactly as they do today, but in one place everyone can see the totals of."""
    allowed = (
        await session.execute(
            text("SELECT milavn_circle.can_moderate_circle(f.circle_id, :a) FROM milavn_circle.fundraiser f WHERE f.id = :f"),
            {"f": str(fundraiser_id), "a": str(actor_member_id)},
        )
    ).scalar_one_or_none()
    if not allowed:
        return False
    await session.execute(
        text("UPDATE milavn_circle.fundraiser_pledge SET paid_at = CASE WHEN :paid THEN now() ELSE NULL END WHERE fundraiser_id = :f AND member_id = :m"),
        {"f": str(fundraiser_id), "m": str(member_id), "paid": paid},
    )
    return True


async def close_fundraiser(session: AsyncSession, *, fundraiser_id: UUID, actor_member_id: UUID) -> None:
    await session.execute(
        text("UPDATE milavn_circle.fundraiser SET closed_at = now() WHERE id = :f AND closed_at IS NULL AND milavn_circle.can_moderate_circle(circle_id, :a)"),
        {"f": str(fundraiser_id), "a": str(actor_member_id)},
    )


# --- Samaj updates: one announcement, every chapter (FR126) ------------------------

MAX_GROUP_UPDATE_LEN = 1000
MAX_GROUP_UPDATES_PER_DAY = 5  # [thesis §84 "need over noise"] an umbrella-wide broadcast is rare by nature


class NotGroupAdmin(Exception):
    """Only the umbrella's own creator may post to every chapter at once."""


class InvalidGroupUpdate(Exception):
    pass


async def is_group_admin(session: AsyncSession, *, group_id: UUID, member_id: UUID) -> bool:
    return bool((await session.execute(text("SELECT milavn_circle.is_group_admin(:g, :m)"), {"g": str(group_id), "m": str(member_id)})).scalar_one())


async def post_group_update(session: AsyncSession, *, group_id: UUID, member_id: UUID, message: str) -> UUID:
    """[FR126] One message from the umbrella's admin, reaching every chapter's members. Rate-limited
    per day so an umbrella-wide channel stays for real news, not noise (thesis §84)."""
    if not await is_group_admin(session, group_id=group_id, member_id=member_id):
        raise NotGroupAdmin
    text_value = (message or "").strip()
    if not text_value or len(text_value) > MAX_GROUP_UPDATE_LEN:
        raise InvalidGroupUpdate
    today_count = (
        await session.execute(
            text("SELECT count(*) FROM milavn_circle.circle_group_update WHERE group_id = :g AND created_by_member_id = :m AND created_at > now() - interval '24 hours'"),
            {"g": str(group_id), "m": str(member_id)},
        )
    ).scalar_one()
    if today_count >= MAX_GROUP_UPDATES_PER_DAY:
        raise InvalidGroupUpdate
    update_id = uuid4()
    await session.execute(
        text("INSERT INTO milavn_circle.circle_group_update (id, group_id, created_by_member_id, message) VALUES (:id, :g, :m, :msg)"),
        {"id": str(update_id), "g": str(group_id), "m": str(member_id), "msg": text_value},
    )
    await bus.publish(
        session,
        schema="milavn_circle",
        event_type="circle_group.update_posted",
        aggregate_id=group_id,
        payload={"group_id": group_id, "update_id": update_id, "created_by_member_id": member_id, "message": text_value},
    )
    return update_id


async def group_updates(session: AsyncSession, *, group_id: UUID, limit: int = 20) -> list[dict]:
    """[FR126] The umbrella's own feed. RLS decides who may read it (any chapter's active member, or
    the admin) — this reader carries no further check of its own."""
    rows = (
        await session.execute(
            text("SELECT id, created_by_member_id, message, created_at FROM milavn_circle.circle_group_update WHERE group_id = :g ORDER BY created_at DESC LIMIT :l"),
            {"g": str(group_id), "l": limit},
        )
    ).all()
    from app.components.identity_bridge import interface as identity

    names = await identity.display_names_for([r[1] for r in rows])
    return [
        {
            "id": str(r[0]),
            "display_name": names[r[1]].display_name if r[1] in names else "",
            "message": r[2],
            "created_at": r[3].isoformat(),
        }
        for r in rows
    ]


async def group_member_ids(session: AsyncSession, *, group_id: UUID) -> list[UUID]:
    ids = (await session.execute(text("SELECT milavn_circle.group_member_ids(:g)"), {"g": str(group_id)})).scalar_one()
    return list(ids or [])


async def group_detail(session: AsyncSession, *, group_id: UUID, viewer_member_id: UUID) -> dict | None:
    """[FR123/FR126] The umbrella's own page: name, chapters, and its update feed (empty for a viewer
    RLS excludes — no chapter, not the admin — rather than an error)."""
    row = (
        await session.execute(
            text("SELECT id, name, description, created_by_member_id FROM milavn_circle.circle_group WHERE id = :g"),
            {"g": str(group_id)},
        )
    ).first()
    if row is None:
        return None
    return {
        "id": str(row[0]),
        "name": row[1],
        "description": row[2],
        "is_admin": row[3] == viewer_member_id,
        "chapters": await chapters(session, group_id=group_id),
        "updates": await group_updates(session, group_id=group_id),
    }


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
        names = await identity.display_names_for([a, b])
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

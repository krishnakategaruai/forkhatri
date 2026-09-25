"""Assisted Matching — public interface (DEC-V1-032).

A relationship manager (RM) is a named, real person a family can see and
message. The RM searches FOR the member (ranked the member's own way, never
re-ranked), puts profiles forward with a note in the member's language, and
logs every call and meeting where the member and their Home Circle can read
it. The RM never sells visibility and never touches ranking (DEC-V1-002).

Two seats, two contexts:
  * the member (or a circle member acting for them, `family_info`) reads the
    assignment, the suggestions and the interaction log, and answers a
    suggestion — under the ordinary account context;
  * the RM reads and writes their own assignments under
    `mangaly.operator_role = 'relationship_manager'` (`api/rm_deps.RmAccount`).

The RM's search runs AS the member: the request's RLS variables are rebound
to the member for the search and put back afterwards, so the existing
`discovery.search()` — with the member's own "looking for", blocks and
preferences — is what answers, not a copy of it.

Entitlement: an assignment may exist only for a member with the
`assisted_matching` entitlement. Billing is another stream's component; it is
called when present and allowed through (with a warning) when absent.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

__all__ = [
    "AlreadyAssigned",
    "Assignment",
    "FamilyMember",
    "Interaction",
    "MemberSummary",
    "NotEntitled",
    "NotFound",
    "RmSummary",
    "Suggestion",
    "active_assignment_for_member",
    "add_interaction",
    "assign",
    "decide_suggestion",
    "end_assignment",
    "get_assignment",
    "is_rm",
    "list_assignments",
    "list_interactions",
    "list_suggestions",
    "member_summary",
    "rm_summary",
    "search_for_member",
    "suggest",
]

ENTITLEMENT_FLAG = "assisted_matching"
NOTE_MAX_LENGTH = 1000


class NotFound(Exception):
    """No such assignment or suggestion visible to the caller."""


class NotEntitled(Exception):
    """The member does not hold the `assisted_matching` entitlement."""


class AlreadyAssigned(Exception):
    """The member already has an active relationship manager."""


@dataclass(frozen=True, slots=True)
class RmSummary:
    account_id: UUID
    display_name: str
    languages: list[str]
    region: str | None
    photo_url: str | None


@dataclass(frozen=True, slots=True)
class Assignment:
    id: UUID
    rm_account_id: UUID
    member_account_id: UUID
    status: str
    assigned_at: datetime
    ended_at: datetime | None
    note: str | None
    member_name: str | None = None
    member_photo_url: str | None = None


@dataclass(frozen=True, slots=True)
class Suggestion:
    id: UUID
    assignment_id: UUID
    suggested_account_id: UUID
    note: str | None
    created_at: datetime
    member_decision: str | None
    decided_at: datetime | None


@dataclass(frozen=True, slots=True)
class Interaction:
    id: UUID
    assignment_id: UUID
    kind: str
    scheduled_at: datetime | None
    summary: str | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class FamilyMember:
    account_id: UUID
    display_name: str | None
    relationship_type: str
    relation: str | None


@dataclass(frozen=True, slots=True)
class MemberSummary:
    """What an RM may know about the member they help. Never contact details."""

    name: str
    age: int | None
    city: str | None
    gender: str | None
    looking_for: str | None
    mother_tongue: str | None
    education_level: str | None
    profession: str | None
    partner_preference: dict[str, Any]
    family_involvement: dict[str, Any]
    language_preference: str
    family: list[FamilyMember] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Row mapping
# ---------------------------------------------------------------------------

_ASSIGNMENT_COLUMNS = "id, rm_account_id, member_account_id, status, assigned_at, ended_at, note"
_SUGGESTION_COLUMNS = (
    "id, assignment_id, suggested_account_id, note, created_at, member_decision, decided_at"
)
_INTERACTION_COLUMNS = "id, assignment_id, kind, scheduled_at, summary, created_at"


def _assignment(row: Any, *, member_name: str | None = None, photo: str | None = None) -> Assignment:
    return Assignment(
        id=row["id"],
        rm_account_id=row["rm_account_id"],
        member_account_id=row["member_account_id"],
        status=row["status"],
        assigned_at=row["assigned_at"],
        ended_at=row["ended_at"],
        note=row["note"],
        member_name=member_name,
        member_photo_url=photo,
    )


def _suggestion(row: Any) -> Suggestion:
    return Suggestion(
        id=row["id"],
        assignment_id=row["assignment_id"],
        suggested_account_id=row["suggested_account_id"],
        note=row["note"],
        created_at=row["created_at"],
        member_decision=row["member_decision"],
        decided_at=row["decided_at"],
    )


def _interaction(row: Any) -> Interaction:
    return Interaction(
        id=row["id"],
        assignment_id=row["assignment_id"],
        kind=row["kind"],
        scheduled_at=row["scheduled_at"],
        summary=row["summary"],
        created_at=row["created_at"],
    )


def _photo_url(ref: str | None) -> str | None:
    if not ref:
        return None
    from app.components.profile import interface as profile_module

    return profile_module.resolve_photo_url(ref)


async def _names(session: AsyncSession, ids: list[UUID]) -> dict[UUID, tuple[str | None, str | None]]:
    """Display names (and main photo) of RMs, or of the members an RM helps."""
    if not ids:
        return {}
    rows = await session.execute(
        text("SELECT * FROM mangaly_operations.rm_people_names(CAST(:ids AS uuid[]))"),
        {"ids": [str(i) for i in ids]},
    )
    return {r["account_id"]: (r["display_name"], r["photo_ref"]) for r in rows.mappings()}


# ---------------------------------------------------------------------------
# Who is an RM
# ---------------------------------------------------------------------------


async def is_rm(session: AsyncSession, *, account_id: UUID) -> bool:
    return bool(
        (
            await session.execute(
                text(
                    "SELECT EXISTS (SELECT 1 FROM mangaly_operations.relationship_manager "
                    "WHERE account_id = :a AND active)"
                ),
                {"a": account_id},
            )
        ).scalar_one()
    )


async def rm_summary(session: AsyncSession, *, rm_account_id: UUID) -> RmSummary | None:
    row = (
        await session.execute(
            text(
                "SELECT account_id, display_name, languages, region, photo_ref "
                "FROM mangaly_operations.relationship_manager WHERE account_id = :a AND active"
            ),
            {"a": rm_account_id},
        )
    ).mappings().first()
    if row is None:
        return None
    photo = row["photo_ref"]
    if not photo:
        # An RM with no photo of their own on the RM row falls back to their
        # member photo (047) — visible to the people who may message them.
        from app.components.profile import interface as profile_module

        photo = (await profile_module.member_photo_refs(session, account_ids=[rm_account_id])).get(
            rm_account_id
        )
    return RmSummary(
        account_id=row["account_id"],
        display_name=row["display_name"],
        languages=list(row["languages"] or []),
        region=row["region"],
        photo_url=_photo_url(photo),
    )


# ---------------------------------------------------------------------------
# Member seat
# ---------------------------------------------------------------------------


async def active_assignment_for_member(
    session: AsyncSession, *, member_account_id: UUID
) -> Assignment | None:
    """The member's active assignment (RLS: the member, their circle, or the RM)."""
    row = (
        await session.execute(
            text(
                f"SELECT {_ASSIGNMENT_COLUMNS} FROM mangaly_operations.rm_assignment "
                "WHERE member_account_id = :m AND status = 'active'"
            ),
            {"m": member_account_id},
        )
    ).mappings().first()
    return _assignment(row) if row else None


async def list_suggestions(session: AsyncSession, *, assignment_id: UUID) -> list[Suggestion]:
    rows = await session.execute(
        text(
            f"SELECT {_SUGGESTION_COLUMNS} FROM mangaly_operations.rm_suggestion "
            "WHERE assignment_id = :a ORDER BY created_at DESC"
        ),
        {"a": assignment_id},
    )
    return [_suggestion(r) for r in rows.mappings()]


async def list_interactions(session: AsyncSession, *, assignment_id: UUID) -> list[Interaction]:
    rows = await session.execute(
        text(
            f"SELECT {_INTERACTION_COLUMNS} FROM mangaly_operations.rm_interaction "
            "WHERE assignment_id = :a ORDER BY COALESCE(scheduled_at, created_at) DESC"
        ),
        {"a": assignment_id},
    )
    return [_interaction(r) for r in rows.mappings()]


async def decide_suggestion(
    session: AsyncSession, *, suggestion_id: UUID, decision: str, member_account_id: UUID
) -> Suggestion:
    """The member (or a parent acting for them) answers a suggestion: liked or
    passed. Nothing is sent to the suggested person — a like is a signal to
    the RM, who may then set up a call; a request still goes through the
    normal path. The RM is told."""
    if decision not in ("liked", "passed"):
        raise ValueError("decision must be liked or passed")
    row = (
        await session.execute(
            text(
                "UPDATE mangaly_operations.rm_suggestion "
                "SET member_decision = :d, decided_at = now() "
                f"WHERE id = :id RETURNING {_SUGGESTION_COLUMNS}"
            ),
            {"d": decision, "id": suggestion_id},
        )
    ).mappings().first()
    if row is None:
        raise NotFound
    suggestion = _suggestion(row)
    assignment = (
        await session.execute(
            text(
                f"SELECT {_ASSIGNMENT_COLUMNS} FROM mangaly_operations.rm_assignment WHERE id = :a"
            ),
            {"a": suggestion.assignment_id},
        )
    ).mappings().first()
    if assignment is not None:
        member_name = (
            await session.execute(
                text(
                    "SELECT COALESCE(p.name, a.display_name) FROM mangaly_identity.account a "
                    "LEFT JOIN mangaly_profile.profile p ON p.account_id = a.id WHERE a.id = :m"
                ),
                {"m": member_account_id},
            )
        ).scalar_one_or_none()
        from app.components.notification_bridge import interface as notifications

        await notifications.notify(
            session,
            recipients=[assignment["rm_account_id"]],
            subject_account_id=assignment["rm_account_id"],
            kind="rm_suggestion_decided",
            payload={
                "assignment_id": assignment["id"],
                "suggestion_id": suggestion.id,
                "member_name": member_name,
                "decision": decision,
            },
            link=f"/rm/console/{assignment['id']}",
        )
    return suggestion


# ---------------------------------------------------------------------------
# RM seat (caller bound as an RM by `api/rm_deps.RmAccount`)
# ---------------------------------------------------------------------------


async def list_assignments(session: AsyncSession, *, rm_account_id: UUID) -> list[Assignment]:
    rows = (
        await session.execute(
            text(
                f"SELECT {_ASSIGNMENT_COLUMNS} FROM mangaly_operations.rm_assignment "
                "WHERE rm_account_id = :rm ORDER BY (status = 'active') DESC, assigned_at DESC"
            ),
            {"rm": rm_account_id},
        )
    ).mappings().all()
    names = await _names(session, [r["member_account_id"] for r in rows])
    return [
        _assignment(
            r,
            member_name=names.get(r["member_account_id"], (None, None))[0],
            photo=_photo_url(names.get(r["member_account_id"], (None, None))[1]),
        )
        for r in rows
    ]


async def get_assignment(
    session: AsyncSession, *, rm_account_id: UUID, assignment_id: UUID
) -> Assignment | None:
    row = (
        await session.execute(
            text(
                f"SELECT {_ASSIGNMENT_COLUMNS} FROM mangaly_operations.rm_assignment "
                "WHERE id = :id AND rm_account_id = :rm"
            ),
            {"id": assignment_id, "rm": rm_account_id},
        )
    ).mappings().first()
    if row is None:
        return None
    names = await _names(session, [row["member_account_id"]])
    name, photo = names.get(row["member_account_id"], (None, None))
    return _assignment(row, member_name=name, photo=_photo_url(photo))


async def member_summary(session: AsyncSession, *, member_account_id: UUID) -> MemberSummary | None:
    """The narrow window an RM has on the member (migration 052's
    `rm_member_summary`): opens only for the member's own active RM."""
    row = (
        await session.execute(
            text("SELECT * FROM mangaly_operations.rm_member_summary(:m)"), {"m": member_account_id}
        )
    ).mappings().first()
    if row is None:
        return None
    family_rows = await session.execute(
        text("SELECT * FROM mangaly_operations.rm_member_family(:m)"), {"m": member_account_id}
    )
    return MemberSummary(
        name=row["name"],
        age=row["age"],
        city=row["city"],
        gender=row["gender"],
        looking_for=row["looking_for"],
        mother_tongue=row["mother_tongue"],
        education_level=row["education_level"],
        profession=row["profession"],
        partner_preference=dict(row["partner_preference"] or {}),
        family_involvement=dict(row["family_involvement"] or {}),
        language_preference=row["language_preference"] or "en",
        family=[
            FamilyMember(
                account_id=f["member_account_id"],
                display_name=f["display_name"],
                relationship_type=f["relationship_type"],
                relation=f["relation"],
            )
            for f in family_rows.mappings()
        ],
    )


async def search_for_member(
    session: AsyncSession,
    *,
    rm_account_id: UUID,
    member_account_id: UUID,
    filters: Any,
    page: int,
    page_size: int,
    sort: str,
) -> tuple[Any, dict[UUID, Any], dict[UUID, Any]]:
    """Run Discover AS the member. The transaction's RLS variables are rebound
    to the member around the existing `discovery.search()` — same ranking,
    same "looking for" rule, same blocks the member would get — then put back
    to the RM. Returns the page plus the cards (photo/age) and what each
    person shows openly, exactly as `/discovery/search` does."""
    from app.components.discovery import interface as discovery
    from app.db.session import set_account_context, set_authz_context

    await set_account_context(session, member_account_id)
    await set_authz_context(session, member_account_id)
    try:
        page_result = await discovery.search(
            session,
            viewer_account_id=member_account_id,
            filters=filters,
            page=page,
            page_size=page_size,
            sort=sort,
        )
        ids = [r.candidate_account_id for r in page_result.results]
        cards = await discovery.cards_for(session, account_ids=ids)
        opened = await discovery.open_cards_for(session, account_ids=ids)
    finally:
        await set_account_context(session, rm_account_id)
        await set_authz_context(session, rm_account_id)
    return page_result, cards, opened


async def suggest(
    session: AsyncSession,
    *,
    rm_account_id: UUID,
    assignment: Assignment,
    suggested_account_id: UUID,
    note: str | None,
) -> Suggestion:
    """Put one profile forward to the member, with the RM's note. A suggestion
    is never a request (the same rule the Home Circle's suggestions follow).
    The member and their whole circle are told."""
    if suggested_account_id == assignment.member_account_id:
        raise ValueError("cannot suggest the member to themselves")
    suggestion_id = uuid4()
    row = (
        await session.execute(
            text(
                "INSERT INTO mangaly_operations.rm_suggestion (id, assignment_id, suggested_account_id, note) "
                "VALUES (:id, :a, :s, :note) "
                "ON CONFLICT (assignment_id, suggested_account_id) DO UPDATE SET note = EXCLUDED.note "
                f"RETURNING {_SUGGESTION_COLUMNS}"
            ),
            {"id": suggestion_id, "a": assignment.id, "s": suggested_account_id, "note": note},
        )
    ).mappings().one()
    rm = await rm_summary(session, rm_account_id=rm_account_id)
    from app.components.notification_bridge import interface as notifications

    await notifications.notify_circle(
        session,
        candidate_account_id=assignment.member_account_id,
        kind="rm_suggested",
        payload={
            "suggestion_id": row["id"],
            "suggested_account_id": suggested_account_id,
            "rm_name": rm.display_name if rm else None,
            "member_name": assignment.member_name,
        },
        link="/rm",
    )
    return _suggestion(row)


async def add_interaction(
    session: AsyncSession,
    *,
    rm_account_id: UUID,
    assignment: Assignment,
    kind: str,
    scheduled_at: datetime | None,
    summary: str | None,
) -> Interaction:
    """Log a call, a meeting or a note on the assignment — the family reads
    every entry. A scheduled call or meeting is announced to the circle."""
    if kind not in ("call", "meeting", "note"):
        raise ValueError("kind must be call, meeting or note")
    row = (
        await session.execute(
            text(
                "INSERT INTO mangaly_operations.rm_interaction (id, assignment_id, kind, scheduled_at, summary) "
                f"VALUES (:id, :a, :k, :at, :s) RETURNING {_INTERACTION_COLUMNS}"
            ),
            {"id": uuid4(), "a": assignment.id, "k": kind, "at": scheduled_at, "s": summary},
        )
    ).mappings().one()
    if scheduled_at is not None and kind in ("call", "meeting"):
        rm = await rm_summary(session, rm_account_id=rm_account_id)
        from app.components.notification_bridge import interface as notifications

        await notifications.notify_circle(
            session,
            candidate_account_id=assignment.member_account_id,
            kind="rm_interaction_scheduled",
            payload={
                "interaction_id": row["id"],
                "rm_name": rm.display_name if rm else None,
                "kind": kind,
                "when": scheduled_at.isoformat(),
            },
            link="/rm",
        )
    return _interaction(row)


async def end_assignment(session: AsyncSession, *, rm_account_id: UUID, assignment_id: UUID) -> None:
    result = await session.execute(
        text(
            "UPDATE mangaly_operations.rm_assignment SET status = 'ended', ended_at = now() "
            "WHERE id = :id AND rm_account_id = :rm AND status = 'active'"
        ),
        {"id": assignment_id, "rm": rm_account_id},
    )
    if not result.rowcount:
        raise NotFound


async def _require_entitlement(session: AsyncSession, member_account_id: UUID) -> None:
    """Billing is another stream's component. When it is there, it decides;
    when it is not, development is allowed through with a warning."""
    try:
        from app.components.billing import interface as billing  # type: ignore[import-not-found]
    except ImportError:
        logger.warning(
            "billing component not present: allowing assisted_matching assignment for %s "
            "without an entitlement check (development only)",
            member_account_id,
        )
        return
    check = getattr(billing, "has_entitlement", None)
    if check is None:
        logger.warning("billing.interface has no has_entitlement(); allowing assignment")
        return
    if not await check(session, member_account_id, ENTITLEMENT_FLAG):
        raise NotEntitled


async def assign(
    session: AsyncSession, *, rm_account_id: UUID, member_account_id: UUID, note: str | None
) -> Assignment:
    """v1: an RM takes on a member themselves. Real allocation (a queue,
    supervision by operations, regional language routing) is backlog."""
    await _require_entitlement(session, member_account_id)
    exists = (
        await session.execute(
            text("SELECT mangaly_operations.rm_of(:m)"), {"m": member_account_id}
        )
    ).scalar_one_or_none()
    if exists is not None:
        raise AlreadyAssigned
    row = (
        await session.execute(
            text(
                "INSERT INTO mangaly_operations.rm_assignment (id, rm_account_id, member_account_id, note) "
                f"VALUES (:id, :rm, :m, :note) RETURNING {_ASSIGNMENT_COLUMNS}"
            ),
            {"id": uuid4(), "rm": rm_account_id, "m": member_account_id, "note": note},
        )
    ).mappings().one()
    names = await _names(session, [member_account_id])
    name, photo = names.get(member_account_id, (None, None))
    rm = await rm_summary(session, rm_account_id=rm_account_id)
    from app.components.notification_bridge import interface as notifications

    await notifications.notify_circle(
        session,
        candidate_account_id=member_account_id,
        kind="rm_assigned",
        payload={"assignment_id": row["id"], "rm_name": rm.display_name if rm else None},
        link="/rm",
    )
    return _assignment(row, member_name=name, photo=_photo_url(photo))

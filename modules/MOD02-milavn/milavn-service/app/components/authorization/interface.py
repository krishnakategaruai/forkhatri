"""Authorization Engine — the structural chokepoint (architecture.md §2.1, §3).

# [TR-CROSSCUT-03, FR021, FR023, FR040, FR050, FR056, FR059, FR062] Every
# consequential read/write resolves who the actor is *relative to the thing*
# here, once; components receive the resolved role, never a bare id to judge.
# Approach: `occurrence_role()` returns organizer / co_organizer / participant /
# viewer for one occurrence, reading only what the actor's own RLS context
# already permits. Circle membership is deliberately NOT consulted for any
# non-Circle capability (FR023/TR18) — there is no helper here that takes a
# circle id, by construction.
# Traces to: TR-CROSSCUT-03, TR38, TR18, TR41.
"""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class OccurrenceRole(StrEnum):
    ORGANIZER = "organizer"
    CO_ORGANIZER = "co_organizer"
    PARTICIPANT = "participant"
    VIEWER = "viewer"


class NotAuthorized(Exception):
    pass


class NotFound(Exception):
    pass


_ROLE_SQL = text(
    """
    SELECT
      o.creator_member_id = :member AS is_creator,
      EXISTS (SELECT 1 FROM milavn_activity.occurrence_co_organizer c
              WHERE c.occurrence_id = o.id AND c.member_id = :member AND c.revoked_at IS NULL) AS is_co,
      EXISTS (SELECT 1 FROM milavn_activity.participation p
              WHERE p.occurrence_id = o.id AND p.member_id = :member
                AND p.status IN ('interested','going','waitlisted','checked_in','attended')) AS is_participant
    FROM milavn_activity.occurrence o WHERE o.id = :occ
    """
)


async def occurrence_role(session: AsyncSession, *, occurrence_id: UUID, member_id: UUID) -> OccurrenceRole:
    row = (await session.execute(_ROLE_SQL, {"member": str(member_id), "occ": str(occurrence_id)})).first()
    if row is None:
        # Invisible under RLS == does not exist for this actor (TR36: 404, never 403).
        raise NotFound
    if row.is_creator:
        return OccurrenceRole.ORGANIZER
    if row.is_co:
        return OccurrenceRole.CO_ORGANIZER
    if row.is_participant:
        return OccurrenceRole.PARTICIPANT
    return OccurrenceRole.VIEWER


async def require_organizer(session: AsyncSession, *, occurrence_id: UUID, member_id: UUID) -> OccurrenceRole:
    role = await occurrence_role(session, occurrence_id=occurrence_id, member_id=member_id)
    if role not in (OccurrenceRole.ORGANIZER, OccurrenceRole.CO_ORGANIZER):
        raise NotAuthorized
    return role


async def require_creator(session: AsyncSession, *, occurrence_id: UUID, member_id: UUID) -> None:
    role = await occurrence_role(session, occurrence_id=occurrence_id, member_id=member_id)
    if role is not OccurrenceRole.ORGANIZER:
        raise NotAuthorized


async def is_blocked_either_way(session: AsyncSession, a: UUID, b: UUID) -> bool:
    """[FR062] The one shared block check every contact/appearance surface calls."""
    return bool((await session.execute(text("SELECT milavn_safety.is_blocked_either_way(:a, :b)"), {"a": str(a), "b": str(b)})).scalar_one())

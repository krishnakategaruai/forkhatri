"""Shortlist — public interface.

Every function takes the CONTEXT account (`candidate_account_id`: the caller's
own account in the self context — with or without a profile — or the candidate
a circle member acts for) already resolved by
`authorization.interface.resolve_context_account()`, which also binds
`mangaly.authz_context` so the table's `has_scope` policy can see the circle
membership.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.events import bus

__all__ = ["ShortlistEntry", "add", "list_entries", "remove", "saved_ids"]


@dataclass(frozen=True, slots=True)
class ShortlistEntry:
    saved_account_id: UUID
    saved_by_account_id: UUID
    note: str | None
    created_at: datetime


async def add(
    session: AsyncSession,
    *,
    acting_account_id: UUID,
    candidate_account_id: UUID,
    saved_account_id: UUID,
    note: str | None = None,
) -> None:
    if saved_account_id in (acting_account_id, candidate_account_id):
        return
    await session.execute(
        text(
            "INSERT INTO mangaly_discovery.shortlist "
            "(id, candidate_account_id, saved_by_account_id, saved_account_id, note) "
            "VALUES (:id, :candidate, :by, :saved, :note) "
            "ON CONFLICT (candidate_account_id, saved_account_id) DO NOTHING"
        ),
        {
            "id": uuid4(),
            "candidate": candidate_account_id,
            "by": acting_account_id,
            "saved": saved_account_id,
            "note": (note or "").strip()[:500] or None,
        },
    )
    await bus.publish(
        session,
        schema="mangaly_discovery",
        aggregate_id=candidate_account_id,
        event_type="ProfileShortlisted",
        payload={
            "candidate_account_id": str(candidate_account_id),
            "saved_by_account_id": str(acting_account_id),
            "saved_account_id": str(saved_account_id),
        },
    )


async def remove(
    session: AsyncSession, *, candidate_account_id: UUID, saved_account_id: UUID
) -> bool:
    result = await session.execute(
        text(
            "DELETE FROM mangaly_discovery.shortlist "
            "WHERE candidate_account_id = :candidate AND saved_account_id = :saved"
        ),
        {"candidate": candidate_account_id, "saved": saved_account_id},
    )
    return bool(result.rowcount)


async def list_entries(
    session: AsyncSession, *, candidate_account_id: UUID, exclude: set[UUID] | None = None
) -> list[ShortlistEntry]:
    rows = await session.execute(
        text(
            "SELECT saved_account_id, saved_by_account_id, note, created_at "
            "FROM mangaly_discovery.shortlist WHERE candidate_account_id = :candidate "
            "ORDER BY created_at DESC"
        ),
        {"candidate": candidate_account_id},
    )
    hidden = exclude or set()
    return [
        ShortlistEntry(
            saved_account_id=r.saved_account_id,
            saved_by_account_id=r.saved_by_account_id,
            note=r.note,
            created_at=r.created_at,
        )
        for r in rows
        if r.saved_account_id not in hidden
    ]


async def saved_ids(session: AsyncSession, *, candidate_account_id: UUID) -> set[UUID]:
    rows = await session.execute(
        text("SELECT saved_account_id FROM mangaly_discovery.shortlist WHERE candidate_account_id = :c"),
        {"c": candidate_account_id},
    )
    return {r[0] for r in rows}

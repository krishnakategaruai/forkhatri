"""Notification Bridge — public interface (in-app inbox).

`/MODULE-ARCHITECTURE-STANDARD.md` §3: this is the only way other components
reach `mangaly_notification`.

[Rework contract §3, 2026-09-17] Six kinds — `request_received`,
`request_accepted`, `invitation_received`, `suggestion_received`,
`family_conversation_opened`, `note_forwarded` — written by the flows that
cause them, one row PER READER (migration 034), so read state is per person.
A row belongs to a context (`subject_account_id`: the candidate whose matter
it is); `list_for()` reads one context, which is how `?for_candidate=` works.

[SP098] Payloads carry ids and non-identifying params only. Titles and bodies
are NOT stored: the API renders them from `notifications.<kind>.*` i18n keys
in the reader's own language at read time.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Final
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

__all__ = [
    "KINDS",
    "Notification",
    "list_for",
    "mark_read",
    "notify",
    "notify_circle",
    "unread_count",
]

KINDS: Final[frozenset[str]] = frozenset(
    {
        "request_received",
        "request_accepted",
        "invitation_received",
        # The inviter hears back when their Home Circle invitation is accepted.
        "invitation_accepted",
        "suggestion_received",
        "family_conversation_opened",
        "note_forwarded",
        # [DEC-V1-019] A profile someone made for a person: removed by that
        # person ("this isn't me"), or about to be removed unused.
        "profile_disowned",
        "profile_removal_notice",
        # [DEC-V1-032] Assisted matching: a relationship manager was assigned,
        # suggested someone, scheduled a call; the member answered a suggestion.
        "rm_assigned",
        "rm_suggested",
        "rm_interaction_scheduled",
        "rm_suggestion_decided",
        # [DEC-V1-033/034] Marriage agents: a family chose this agent; the
        # agent's access to other families' contacts was paused after
        # reports; the agent was suspended. These were sent by the agent
        # code but never registered here, so choosing an agent crashed.
        "agent_chosen",
        "agent_contact_suspended",
        "agent_suspended",
    }
)


@dataclass(frozen=True, slots=True)
class Notification:
    id: UUID
    kind: str
    payload: dict[str, Any]
    link: str | None
    subject_account_id: UUID | None
    created_at: datetime
    read_at: datetime | None


def _json(payload: dict[str, Any]) -> str:
    import json

    return json.dumps(
        {k: (str(v) if isinstance(v, UUID) else v) for k, v in payload.items() if v is not None}
    )


async def notify(
    session: AsyncSession,
    *,
    recipients: list[UUID],
    subject_account_id: UUID | None,
    kind: str,
    payload: dict[str, Any],
    link: str | None,
) -> int:
    """One inbox row per recipient, through `mangaly_notification.notify()`."""
    if kind not in KINDS:
        raise ValueError(f"unknown notification kind {kind!r}")
    if not recipients:
        return 0
    return (
        await session.execute(
            text(
                "SELECT mangaly_notification.notify(CAST(:recipients AS uuid[]), :subject, "
                ":kind, CAST(:payload AS jsonb), :link)"
            ),
            {
                "recipients": [str(r) for r in recipients],
                "subject": subject_account_id,
                "kind": kind,
                "payload": _json(payload),
                "link": link,
            },
        )
    ).scalar_one()


async def notify_circle(
    session: AsyncSession,
    *,
    candidate_account_id: UUID,
    kind: str,
    payload: dict[str, Any],
    link: str | None,
    exclude: UUID | None = None,
) -> int:
    """The candidate plus every active member of their circle, each their own row."""
    if kind not in KINDS:
        raise ValueError(f"unknown notification kind {kind!r}")
    return (
        await session.execute(
            text(
                "SELECT mangaly_notification.notify_circle(:candidate, :kind, "
                "CAST(:payload AS jsonb), :link, :exclude)"
            ),
            {
                "candidate": candidate_account_id,
                "kind": kind,
                "payload": _json(payload),
                "link": link,
                "exclude": exclude,
            },
        )
    ).scalar_one()


async def list_for(
    session: AsyncSession, *, account_id: UUID, subject_account_id: UUID, limit: int = 100
) -> list[Notification]:
    """The reader's rows in one context, newest first (RLS: recipient only)."""
    rows = await session.execute(
        text(
            """
            SELECT id, kind, payload, link, subject_account_id, created_at, read_at
              FROM mangaly_notification.inbox_entry
             WHERE recipient_account_id = :account_id
               AND subject_account_id = :subject
             ORDER BY created_at DESC
             LIMIT :limit
            """
        ),
        {"account_id": account_id, "subject": subject_account_id, "limit": limit},
    )
    return [
        Notification(
            id=r.id,
            kind=r.kind,
            payload=dict(r.payload or {}),
            link=r.link,
            subject_account_id=r.subject_account_id,
            created_at=r.created_at,
            read_at=r.read_at,
        )
        for r in rows
    ]


async def mark_read(
    session: AsyncSession,
    *,
    account_id: UUID,
    ids: list[UUID] | None,
    subject_account_id: UUID | None,
) -> int:
    """Mark the given rows read — or, with no ids, every unread row in the
    context (every context when no subject is given either)."""
    clauses = ["recipient_account_id = :account_id", "read_at IS NULL"]
    params: dict[str, Any] = {"account_id": account_id}
    if ids:
        clauses.append("id = ANY(CAST(:ids AS uuid[]))")
        params["ids"] = [str(i) for i in ids]
    elif subject_account_id is not None:
        clauses.append("subject_account_id = :subject")
        params["subject"] = subject_account_id
    result = await session.execute(
        text(
            "UPDATE mangaly_notification.inbox_entry SET read_at = now() WHERE "
            + " AND ".join(clauses)
        ),
        params,
    )
    return result.rowcount or 0


async def unread_count(session: AsyncSession, *, account_id: UUID) -> int:
    return (
        await session.execute(
            text(
                "SELECT count(*) FROM mangaly_notification.inbox_entry "
                "WHERE recipient_account_id = :account_id AND read_at IS NULL"
            ),
            {"account_id": account_id},
        )
    ).scalar_one()

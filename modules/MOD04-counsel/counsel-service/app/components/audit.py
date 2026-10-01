"""Append-only audit trail for money, identity-evidence and status decisions."""

from __future__ import annotations

from uuid import UUID


async def record(conn, actor_id: UUID | str | None, action: str, target_kind: str, target_id, detail: dict | None = None) -> None:
    await conn.execute(
        "INSERT INTO audit_log (actor_id, action, target_kind, target_id, detail) VALUES ($1,$2,$3,$4,$5)",
        UUID(str(actor_id)) if actor_id else None, action, target_kind, str(target_id), detail or {},
    )

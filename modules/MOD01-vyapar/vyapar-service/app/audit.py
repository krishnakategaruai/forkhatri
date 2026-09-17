# [TR049/FR49] Audit trail for commercial and administrative actions, and the
# attribution FR34 requires ("every action is attributed to the individual
# member", not to the business).
# Approach: one writer every operator/workspace action calls.
# `vyapar_integration.audit_events` is insert-any / operator-read-only at the
# RLS layer, so any actor can record their own action but only an operator can
# search the log (FR49's audit search). `details` never carries payment
# credentials or member PII — only ids, states and reason codes.
# Traces to: FR49, FR34, TR049, SP049, FR52(c)
from __future__ import annotations

import json

import asyncpg


async def audit(
    conn: asyncpg.Connection,
    *,
    actor_id: str | None,
    action: str,
    object_kind: str,
    object_id: str,
    reason_code: str | None = None,
    outcome: str = "ok",
    details: dict | None = None,
) -> None:
    await conn.execute(
        """INSERT INTO vyapar_integration.audit_events (actor_id, object_kind, object_id, action, reason_code, outcome, details)
           VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb)""",
        actor_id, object_kind, str(object_id), action, reason_code, outcome, json.dumps(details or {}),
    )


async def audit_out_of_band(
    *,
    actor_id: str | None,
    action: str,
    object_kind: str,
    object_id: str,
    reason_code: str | None = None,
    outcome: str = "rejected",
    details: dict | None = None,
) -> None:
    """[FR49] Audit a REFUSED action. The refusal raises, which rolls back the
    request transaction and would take the audit row with it — so this writes
    on its own connection. Found live: a rejected over-value refund left no
    audit trail at all."""
    from app.db import get_pool

    async with get_pool().acquire() as conn:
        async with conn.transaction():
            await audit(conn, actor_id=actor_id, action=action, object_kind=object_kind, object_id=object_id,
                        reason_code=reason_code, outcome=outcome, details=details)

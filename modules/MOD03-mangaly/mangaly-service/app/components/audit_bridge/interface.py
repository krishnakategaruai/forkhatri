"""Audit Bridge — public interface.

[BR15/TR076] Every operator action on a case is audited: the record rides the
same transaction as the action, through the transactional outbox
(`mangaly_operations.outbox_event`), which the platform Audit Log Store
consumes (ADR-011). This component keeps no table of its own; it exists so
every operator mutation calls ONE function with ONE payload shape, and a
missing audit write is a missing call — greppable — rather than a payload
that quietly differs from the next one.

Payloads carry identifiers and the decision, never row contents (SP069).
"""

from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.events import bus

__all__ = ["record_operator_action"]


async def record_operator_action(
    session: AsyncSession,
    *,
    operator_account_id: UUID,
    action: str,
    case_id: UUID,
    details: Mapping[str, str | int | float | bool | None] | None = None,
) -> UUID:
    """Audit one operator action on one case, atomically with the action."""
    payload: dict[str, str | int | float | bool | None] = {
        "operator_account_id": str(operator_account_id),
        "action": action,
        "case_id": str(case_id),
    }
    for key, value in (details or {}).items():
        payload[f"detail_{key}"] = value
    return await bus.publish(
        session,
        schema="mangaly_operations",
        aggregate_id=case_id,
        event_type="OperatorActionRecorded",
        payload=payload,
    )

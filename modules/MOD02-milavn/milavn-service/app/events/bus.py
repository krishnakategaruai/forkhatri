"""Transactional-outbox domain event bus.

# [TR-CROSSCUT-04, TR09, TR13, TR41] Every cross-component side effect is
# published in the SAME transaction as the state change that caused it.
# Approach: `publish()` INSERTs into the owning component's own
# `<schema>.outbox_event` table using the caller's already-open session and
# never commits — a crash between "state changed" and "event queued" is
# impossible because there is no between. In-process subscribers
# (Notification Dispatch, Audit Bridge) react by reading the same row through
# `subscribe()` handlers invoked after commit by the request layer.
# Payloads carry identifiers only — never row contents.
# Traces to: TR-CROSSCUT-04, MODULE-ARCHITECTURE-STANDARD §6.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable, Mapping
from typing import Any, Final
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

OUTBOX_SCHEMAS: Final[frozenset[str]] = frozenset({"milavn_activity", "milavn_circle", "milavn_trust", "milavn_safety"})

_ALLOWED_TYPES = (str, int, float, bool, type(None), UUID)


class OutboxPublishError(RuntimeError):
    pass


Handler = Callable[["DomainEvent"], Awaitable[None]]


class DomainEvent:
    __slots__ = ("event_id", "schema", "event_type", "aggregate_id", "payload")

    def __init__(self, event_id: UUID, schema: str, event_type: str, aggregate_id: UUID, payload: dict) -> None:
        self.event_id = event_id
        self.schema = schema
        self.event_type = event_type
        self.aggregate_id = aggregate_id
        self.payload = payload


_subscribers: dict[str, list[Handler]] = {}


def subscribe(event_type: str, handler: Handler) -> None:
    _subscribers.setdefault(event_type, []).append(handler)


def _validate(payload: Mapping[str, Any]) -> None:
    for key, value in payload.items():
        if isinstance(value, (list, tuple)):
            if not all(isinstance(v, _ALLOWED_TYPES) for v in value):
                raise OutboxPublishError(f"payload {key!r} contains a non-identifier value")
        elif not isinstance(value, _ALLOWED_TYPES):
            raise OutboxPublishError(f"payload {key!r} is a {type(value).__name__}; identifiers only")


def _jsonify(payload: Mapping[str, Any]) -> str:
    def conv(v: Any) -> Any:
        if isinstance(v, UUID):
            return str(v)
        if isinstance(v, (list, tuple)):
            return [conv(i) for i in v]
        return v

    return json.dumps({k: conv(v) for k, v in payload.items()}, separators=(",", ":"), sort_keys=True)


_INSERT = "INSERT INTO {schema}.outbox_event (id, event_type, aggregate_id, payload) VALUES (:id, :event_type, :aggregate_id, CAST(:payload AS jsonb))"


async def publish(
    session: AsyncSession,
    *,
    schema: str,
    event_type: str,
    aggregate_id: UUID,
    payload: Mapping[str, Any],
) -> DomainEvent:
    if schema not in OUTBOX_SCHEMAS:
        raise OutboxPublishError(f"{schema!r} owns no outbox_event table")
    if not session.in_transaction():
        raise OutboxPublishError(f"Refusing to publish {event_type!r}: no open transaction")
    _validate(payload)
    event_id = uuid4()
    await session.execute(
        text(_INSERT.format(schema=schema)),
        {
            "id": str(event_id),
            "event_type": event_type,
            "aggregate_id": str(aggregate_id),
            "payload": _jsonify(payload),
        },
    )
    event = DomainEvent(event_id, schema, event_type, aggregate_id, dict(payload))
    pending: list[DomainEvent] = session.info.setdefault("pending_events", [])
    pending.append(event)
    logger.debug("published %s -> %s.outbox_event", event_type, schema)
    return event


async def dispatch_pending(session: AsyncSession) -> None:
    """Invoke in-process subscribers for the events this transaction published.

    Called by the request layer after the transaction commits, so a subscriber
    only ever sees state that is durably stored. Each subscriber opens its own
    transaction (Notification Dispatch writes the inbox/outbox rows).
    """
    pending: list[DomainEvent] = session.info.pop("pending_events", [])
    for event in pending:
        for handler in _subscribers.get(event.event_type, []):
            try:
                await handler(event)
            except Exception:  # noqa: BLE001 — one failing subscriber never blocks the others
                logger.exception("subscriber failed for %s", event.event_type)
        await _mark_dispatched(event)


async def _mark_dispatched(event: DomainEvent) -> None:
    from app.db.engine import get_process_session_factory

    factory = get_process_session_factory()
    async with factory() as s, s.begin():
        await s.execute(
            text(
                f"UPDATE {event.schema}.outbox_event SET dispatched_at = now() WHERE id = :id"  # noqa: S608 — schema from closed set
            ),
            {"id": str(event.event_id)},
        )

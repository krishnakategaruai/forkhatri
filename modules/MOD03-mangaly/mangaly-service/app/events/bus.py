"""Transactional-outbox domain event bus.

# [TR069/SP069] Every consequential action publishes a domain event in the SAME
# transaction as the state change that caused it.
# Approach: outbox pattern. `publish()` takes the caller's already-open
# `AsyncSession` and INSERTs into the owning component's own
# `<schema>.outbox_event` table. It deliberately does NOT commit, open its own
# session, or fire a network call: SP069's caution is that "an event published
# after commit, or from a different session, reintroduces exactly the
# lost-audit-record failure the pattern exists to prevent". Because the insert
# rides the caller's transaction, a crash between the state change and the
# publish is impossible — there is no between.
#
# Two further structural properties:
#   * `publish()` refuses to run outside an open transaction, rather than
#     opening one. An implicit transaction here would be a *different* unit of
#     work from the state change, which is the exact failure mode above.
#   * [SP069 information-disclosure row] Payloads are minimised by contract:
#     `publish()` accepts a `payload` of identifiers and authorization basis
#     only, and every caller builds that payload by hand (see `events/dto.py`)
#     rather than serialising a domain object. An event payload that carried row
#     contents would leak, through the audit path, data the source row's own RLS
#     would have withheld.
#
# Reads of these tables are restricted at the database layer to
# `mangaly.service_role = 'dispatcher'` (the split RLS policy added during Step
# 7a's live-verification pass); INSERT is unconditional because publishing an
# event is a normal part of any business mutation.
# Traces to: TR069, TR052, SP069, MODULE-ARCHITECTURE-STANDARD §6,
#            CODING-GUIDE.md §4.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from typing import Any, Final
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class OutboxPublishError(RuntimeError):
    """Raised when an event cannot be published atomically with its state change."""


# The eleven schema-owning business components plus the Authorization Engine,
# each with its own `outbox_event` table. Listed explicitly rather than derived
# from a string format, so publishing into a schema that does not own an outbox
# is a KeyError at the call site instead of a runtime SQL error in production.
OUTBOX_SCHEMAS: Final[frozenset[str]] = frozenset(
    {
        "mangaly_authz",
        "mangaly_profile",
        "mangaly_home_circle",
        "mangaly_discovery",
        "mangaly_compatibility",
        "mangaly_trust",
        "mangaly_connection",
        "mangaly_communication",
        "mangaly_safety",
        "mangaly_lifecycle",
        "mangaly_operations",
    }
)

# Values a payload is allowed to contain. Anything else (a dataclass, an ORM
# object, a nested domain model) is rejected — that is the enforcement behind
# "payloads carry identifiers and the resolved authorization basis, not row
# contents", and behind SP081's "no serializer reflection over the domain model".
_ALLOWED_PAYLOAD_TYPES = (str, int, float, bool, type(None))


def _validate_payload(payload: Mapping[str, Any]) -> None:
    for key, value in payload.items():
        if not isinstance(key, str):
            raise OutboxPublishError(f"Event payload key {key!r} must be a string.")
        if isinstance(value, UUID):
            continue
        if isinstance(value, (list, tuple)):
            for item in value:
                if not isinstance(item, (*_ALLOWED_PAYLOAD_TYPES, UUID)):
                    raise OutboxPublishError(
                        f"Event payload {key!r} contains {type(item).__name__}. "
                        "Payloads carry identifiers and authorization basis only "
                        "(SP069) — build a hand-written DTO instead."
                    )
            continue
        if not isinstance(value, _ALLOWED_PAYLOAD_TYPES):
            raise OutboxPublishError(
                f"Event payload {key!r} is a {type(value).__name__}. Payloads carry "
                "identifiers and authorization basis only (SP069) — never a "
                "serialised domain object."
            )


def _jsonify(payload: Mapping[str, Any]) -> str:
    return json.dumps(
        {k: (str(v) if isinstance(v, UUID) else v) for k, v in payload.items()},
        separators=(",", ":"),
        sort_keys=True,
    )


# NOTE — deliberately NO `RETURNING id`, and the id is generated application-side.
# Found by running this against the real database: every `outbox_event` table's
# SELECT policy restricts reads to `mangaly.service_role = 'dispatcher'`, and
# Postgres applies the SELECT policy to the rows an `INSERT ... RETURNING`
# hands back. So `RETURNING id` inside a normal business transaction fails with
# "new row violates row-level security policy" even though the INSERT itself is
# permitted. The correct fix is here rather than in the policy: the dispatcher-
# only read restriction is exactly what SP069's tampering row asks for, and
# relaxing it so the writer can read its own event id back would trade a real
# security control for a value the writer does not need.
_INSERT_SQL_TEMPLATE = (
    "INSERT INTO {schema}.outbox_event (id, aggregate_id, event_type, payload) "
    "VALUES (:id, :aggregate_id, :event_type, CAST(:payload AS jsonb))"
)


async def publish(
    session: AsyncSession,
    *,
    schema: str,
    aggregate_id: UUID,
    event_type: str,
    payload: Mapping[str, Any],
) -> UUID:
    """Insert one outbox row inside the caller's already-open transaction.

    Returns the new event id. Never commits — the caller's transaction owns the
    commit, which is what makes the state change and the event atomic.
    """
    if schema not in OUTBOX_SCHEMAS:
        raise OutboxPublishError(
            f"{schema!r} owns no outbox_event table. Known: {sorted(OUTBOX_SCHEMAS)}"
        )
    if not session.in_transaction():
        raise OutboxPublishError(
            f"Refusing to publish {event_type!r}: no open transaction. An event "
            "published outside the transaction of the state change it describes "
            "can be lost independently of that state change (TR069/SP069)."
        )
    _validate_payload(payload)

    # The schema name is interpolated from the closed `OUTBOX_SCHEMAS` set above,
    # never from request data; every value is bound.
    event_id = uuid4()
    await session.execute(
        text(_INSERT_SQL_TEMPLATE.format(schema=schema)),
        {
            "id": str(event_id),
            "aggregate_id": str(aggregate_id),
            "event_type": event_type,
            "payload": _jsonify(payload),
        },
    )
    logger.debug("published %s to %s.outbox_event (%s)", event_type, schema, event_id)
    return event_id

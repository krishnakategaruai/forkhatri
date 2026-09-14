"""The one shared idempotency guard for every client-queueable mutation.

# [TR-CROSSCUT-01, TR07, TR12, TR41, TR44] A repeated `Idempotency-Key`
# returns the original result WITHOUT re-executing the mutation.
# Approach: an async context manager used inside the handler, after
# authentication and inside the request's single transaction, keyed on
# (endpoint, actor_member_id, idempotency_key) in
# `milavn_platform.idempotency_key`. The request body is fingerprinted, so
# the same key with a different payload is a 409, not a stale replay. The
# snapshot write rides the caller's transaction, so "mutation committed but
# snapshot didn't" is unreachable.
# Traces to: TR-CROSSCUT-01, MODULE-ARCHITECTURE-STANDARD §4b.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class IdempotencyConflict(Exception):
    """Same key, different payload."""


@dataclass
class IdempotentOutcome:
    replayed: bool
    status_code: int = 200
    response: dict[str, Any] = field(default_factory=dict)

    def set_result(self, status_code: int, response: dict[str, Any]) -> None:
        self.status_code = status_code
        self.response = response


def request_fingerprint(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


_LOOKUP = text(
    """
    SELECT request_hash, response_status, response_snapshot
    FROM milavn_platform.idempotency_key
    WHERE endpoint = :endpoint AND actor_member_id = :actor AND idempotency_key = :key
    """
)
_CLAIM = text(
    """
    INSERT INTO milavn_platform.idempotency_key
        (endpoint, actor_member_id, idempotency_key, request_hash, response_status, response_snapshot)
    VALUES (:endpoint, :actor, :key, :hash, 0, '{}'::jsonb)
    """
)
_COMPLETE = text(
    """
    UPDATE milavn_platform.idempotency_key
    SET response_status = :status, response_snapshot = CAST(:snapshot AS jsonb)
    WHERE endpoint = :endpoint AND actor_member_id = :actor AND idempotency_key = :key
    """
)


@asynccontextmanager
async def idempotent(
    session: AsyncSession,
    *,
    actor_member_id: UUID,
    idempotency_key: str | None,
    endpoint: str,
    request_payload: Any,
) -> AsyncIterator[IdempotentOutcome]:
    if idempotency_key is None:
        yield IdempotentOutcome(replayed=False)
        return

    fingerprint = request_fingerprint(request_payload)
    params = {"endpoint": endpoint, "actor": str(actor_member_id), "key": idempotency_key}
    row = (await session.execute(_LOOKUP, params)).first()
    if row is not None:
        if row.request_hash != fingerprint:
            raise IdempotencyConflict(idempotency_key)
        if row.response_status != 0:
            yield IdempotentOutcome(True, row.response_status, dict(row.response_snapshot))
            return
        # A claimed-but-incomplete row (crashed mid-request): fall through and redo.
        outcome = IdempotentOutcome(replayed=False)
        yield outcome
    else:
        await session.execute(_CLAIM, {**params, "hash": fingerprint})
        outcome = IdempotentOutcome(replayed=False)
        yield outcome

    await session.execute(
        _COMPLETE,
        {
            **params,
            "status": outcome.status_code,
            "snapshot": json.dumps(outcome.response, default=str),
        },
    )

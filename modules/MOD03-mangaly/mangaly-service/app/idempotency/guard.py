"""The shared idempotency guard every client-queueable mutation endpoint wraps in.

# [TR102/SP102] A repeated idempotency key returns the original result WITHOUT
# re-executing the mutation.
# Approach: implemented as an async context manager used inside the handler,
# not as ASGI middleware — a deliberate choice with a concrete reason. SP102
# requires `account_id` in every lookup, and `account_id` only exists after
# authentication and after the request's transaction is open (the RLS policy on
# `mangaly_platform.idempotency_key` keys on `mangaly.account_id`, which is
# transaction-local). True ASGI middleware runs before both, so it would have to
# either open a second transaction — losing the atomicity between the snapshot
# and the mutation — or fall back to a key-only lookup, which is precisely the
# cross-account defect SP102 found. This is still ONE shared implementation
# every endpoint calls; it just sits one layer in from the socket.
#
# The snapshot write happens in the caller's transaction, so "the mutation
# committed but its snapshot did not" is not a reachable state.
# Traces to: TR102, TR002, TR042, TR043, TR046, TR047, TR049, TR057, TR058,
#            SP102, MODULE-ARCHITECTURE-STANDARD §4b.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.idempotency import store
from app.idempotency.store import IdempotencyConflict, request_fingerprint

__all__ = ["IdempotencyConflict", "IdempotentOutcome", "idempotent", "request_fingerprint"]


@dataclass
class IdempotentOutcome:
    """Handed to the handler body; carries the replay, or receives the fresh result."""

    replayed: bool
    status_code: int = 200
    response: dict[str, Any] = field(default_factory=dict)

    def set_result(self, status_code: int, response: dict[str, Any]) -> None:
        """Record the fresh result so it is snapshotted for future replays."""
        self.status_code = status_code
        self.response = response


@asynccontextmanager
async def idempotent(
    session: AsyncSession,
    *,
    account_id: UUID,
    idempotency_key: str | None,
    endpoint: str,
    request_payload: Any,
) -> AsyncIterator[IdempotentOutcome]:
    """Wrap one mutation.

    Usage::

        async with idempotent(session, account_id=..., idempotency_key=key,
                              endpoint="POST /profile", request_payload=body) as outcome:
            if not outcome.replayed:
                result = await do_the_mutation(...)
                outcome.set_result(201, result)
        return JSONResponse(outcome.response, status_code=outcome.status_code)

    When `idempotency_key` is None the guard is a pass-through: TR102 names the
    endpoints that must send one, and a missing key is enforced at the router
    (a required header) rather than silently here — a guard that quietly
    tolerates a missing key is a guard that is not actually applied.
    """
    if idempotency_key is None:
        yield IdempotentOutcome(replayed=False)
        return

    settings = get_settings()
    fingerprint = request_fingerprint(request_payload)

    existing = await store.lookup(
        session,
        account_id=account_id,
        idempotency_key=idempotency_key,
        endpoint=endpoint,
        request_hash=fingerprint,
    )
    if existing is not None:
        # Replay. The handler body is skipped entirely — SP102's threshold is
        # "returns the original result and NEVER re-executes the mutation".
        yield IdempotentOutcome(
            replayed=True,
            status_code=existing.status_code,
            response=existing.response_snapshot,
        )
        return

    await store.claim(
        session,
        account_id=account_id,
        idempotency_key=idempotency_key,
        endpoint=endpoint,
        request_hash=fingerprint,
        ttl_days=settings.idempotency_key_ttl_days,
    )

    outcome = IdempotentOutcome(replayed=False)
    yield outcome

    await store.complete(
        session,
        account_id=account_id,
        idempotency_key=idempotency_key,
        endpoint=endpoint,
        status_code=outcome.status_code,
        response_snapshot=outcome.response,
    )

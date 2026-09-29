"""Account-scoped idempotency-key store.

# [TR102/SP102] One shared idempotency implementation every client-queueable
# mutation endpoint honors, with `account_id` in EVERY lookup.
# Approach: SP102 found a real cross-account defect in the Sealed schema — the
# key is client-generated, yet uniqueness was global — and fixed it in migration
# `002-idempotency-account-scope.sql` (`UNIQUE (account_id, idempotency_key,
# endpoint)` plus an RLS policy). SP102 is explicit that "the middleware must
# also include `account_id` in every lookup — the RLS policy is the second
# layer, not the first", so this module takes `account_id` as a required, non-
# defaulted parameter on every function, and every SQL statement below names it
# in the WHERE clause. There is no lookup-by-key-alone function to call by
# mistake.
#
# `request_hash` is stored and compared: a repeated key with a DIFFERENT payload
# is rejected as a client error rather than silently returning a stale success
# (SP102 tampering row).
# Traces to: TR102, SP102, MODULE-ARCHITECTURE-STANDARD §4b,
#            07a-db-implementation/migrations/002-idempotency-account-scope.sql.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class IdempotencyConflict(Exception):
    """Same key, different payload — a client bug, surfaced rather than absorbed."""


@dataclass(frozen=True, slots=True)
class StoredResponse:
    status_code: int
    response_snapshot: dict[str, Any]


def request_fingerprint(payload: Any) -> str:
    """Stable hash of the request body, used to detect key reuse with a changed payload."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# account_id is in the WHERE clause. This is the first layer; the RLS policy
# added by migration 002 is the second.
_LOOKUP_SQL = text(
    """
    SELECT request_hash, status_code, response_snapshot
    FROM mangaly_platform.idempotency_key
    WHERE account_id = :account_id
      AND idempotency_key = :idempotency_key
      AND endpoint = :endpoint
      AND expires_at > now()
    """
)

_CLAIM_SQL = text(
    """
    INSERT INTO mangaly_platform.idempotency_key
        (idempotency_key, endpoint, account_id, request_hash, expires_at)
    VALUES (:idempotency_key, :endpoint, :account_id, :request_hash, :expires_at)
    ON CONFLICT (account_id, idempotency_key, endpoint) DO NOTHING
    RETURNING id
    """
)

_COMPLETE_SQL = text(
    """
    UPDATE mangaly_platform.idempotency_key
    SET status_code = :status_code,
        response_snapshot = CAST(:response_snapshot AS jsonb)
    WHERE account_id = :account_id
      AND idempotency_key = :idempotency_key
      AND endpoint = :endpoint
    """
)


async def lookup(
    session: AsyncSession,
    *,
    account_id: UUID,
    idempotency_key: str,
    endpoint: str,
    request_hash: str,
) -> StoredResponse | None:
    """Return the original response for a repeated key, or None on first use.

    Raises `IdempotencyConflict` if the key was used with a different payload.
    Returns None (not a stored response) when the row exists but has no
    `status_code` yet — an in-flight first attempt whose transaction has not
    committed; the caller treats that as "proceed", and the unique constraint
    is what actually prevents the duplicate write.
    """
    row = (
        await session.execute(
            _LOOKUP_SQL,
            {
                "account_id": str(account_id),
                "idempotency_key": idempotency_key,
                "endpoint": endpoint,
            },
        )
    ).mappings().one_or_none()

    if row is None:
        return None
    if row["request_hash"] != request_hash:
        raise IdempotencyConflict(
            f"idempotency key reused on {endpoint} with a different request payload"
        )
    if row["status_code"] is None:
        return None
    return StoredResponse(
        status_code=int(row["status_code"]),
        response_snapshot=dict(row["response_snapshot"] or {}),
    )


async def claim(
    session: AsyncSession,
    *,
    account_id: UUID,
    idempotency_key: str,
    endpoint: str,
    request_hash: str,
    ttl_days: int,
) -> bool:
    """Reserve the (account, key, endpoint) triple. False means another attempt owns it."""
    expires_at = datetime.now(UTC) + timedelta(days=ttl_days)
    result = await session.execute(
        _CLAIM_SQL,
        {
            "idempotency_key": idempotency_key,
            "endpoint": endpoint,
            "account_id": str(account_id),
            "request_hash": request_hash,
            "expires_at": expires_at,
        },
    )
    return result.scalar_one_or_none() is not None


async def complete(
    session: AsyncSession,
    *,
    account_id: UUID,
    idempotency_key: str,
    endpoint: str,
    status_code: int,
    response_snapshot: dict[str, Any],
) -> None:
    """Record the result, in the SAME transaction as the mutation it describes.

    Snapshot and state change commit or roll back together, so a repeated key can
    never return a snapshot for a write that was rolled back.
    """
    await session.execute(
        _COMPLETE_SQL,
        {
            "account_id": str(account_id),
            "idempotency_key": idempotency_key,
            "endpoint": endpoint,
            "status_code": status_code,
            "response_snapshot": json.dumps(response_snapshot, default=str),
        },
    )

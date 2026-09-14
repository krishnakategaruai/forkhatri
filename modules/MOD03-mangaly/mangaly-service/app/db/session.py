"""The `SET LOCAL`-only RLS session-variable discipline.

# [TR017/SP017] Every RLS session variable is set transaction-locally, never
# session-globally — a plain `SET` under transaction-mode pooling leaks one
# request's authorization context onto a different pooled connection's next
# transaction.
# Approach: three deliberate structural choices, because SP017 calls this "the
# single highest-impact finding in this entire file" and a convention would not
# survive it.
#   1. `SELECT set_config(name, value, is_local => true)` is used instead of a
#      literal `SET LOCAL name = value`. `set_config(..., true)` IS `SET LOCAL`
#      — same transaction-local semantics — but it takes bind parameters, so the
#      authz context (a value derived from request data) is never string-
#      interpolated into SQL. A literal `SET LOCAL` cannot be parameterised in
#      Postgres, which is precisely how "just interpolate the uuid" becomes an
#      injection point.
#   2. Setting a variable REQUIRES an already-open transaction. `set_config`
#      with is_local=true outside a transaction block silently does nothing and
#      the RLS predicate then reads an empty string — a fail-open shape. This
#      module raises instead of silently no-op'ing.
#   3. There is no `set_session_variable` function that takes `is_local` as a
#      parameter. It is not configurable, so no call site can pass `False`.
# Traces to: TR017, SP017, SP102, SP104, CODING-GUIDE.md §7,
#            07a-db-implementation/README.md "RLS".
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Final
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# The exact variable names every RLS policy in `schema.sql` reads. Listed here
# so a typo is a lookup failure in one place rather than a silently-unset
# variable (and therefore a silently empty result set) at a call site.
VAR_ACCOUNT_ID: Final[str] = "mangaly.account_id"
VAR_AUTHZ_CONTEXT: Final[str] = "mangaly.authz_context"
VAR_OPERATOR_ROLE: Final[str] = "mangaly.operator_role"
VAR_SERVICE_ROLE: Final[str] = "mangaly.service_role"

_ALLOWED_VARS: Final[frozenset[str]] = frozenset(
    {VAR_ACCOUNT_ID, VAR_AUTHZ_CONTEXT, VAR_OPERATOR_ROLE, VAR_SERVICE_ROLE}
)

# `is_local => true` is hardcoded. See choice 3 in the block above.
_SET_LOCAL_SQL = text("SELECT set_config(:name, :value, true)")


class SessionVariableError(RuntimeError):
    """Raised when an RLS session variable cannot be set safely."""


async def set_local(session: AsyncSession, name: str, value: str) -> None:
    """Set one RLS session variable transaction-locally.

    Raises rather than no-op'ing when there is no open transaction, because a
    silently-unset RLS variable is a fail-open condition.
    """
    if name not in _ALLOWED_VARS:
        raise SessionVariableError(
            f"{name!r} is not one of this module's RLS session variables "
            f"({sorted(_ALLOWED_VARS)}). Add it to schema.sql's policies first."
        )
    if not session.in_transaction():
        raise SessionVariableError(
            f"Refusing to set {name!r}: no open transaction. `SET LOCAL` outside a "
            "transaction block is a no-op, which would leave the RLS predicate "
            "reading an empty value (TR017/SP017)."
        )
    await session.execute(_SET_LOCAL_SQL, {"name": name, "value": value})


async def set_account_context(session: AsyncSession, account_id: UUID) -> None:
    """[TR017/SP104] Identity Bridge sets this after validating a session token.

    This is the pre-authorization trust root `mangaly_identity.*` and
    `mangaly_platform.idempotency_key` RLS policies key on.
    """
    await set_local(session, VAR_ACCOUNT_ID, str(account_id))


async def set_authz_context(session: AsyncSession, subject_id: UUID) -> None:
    """[TR017] Authorization Engine sets this on `resolve()`, and nothing else does.

    Every business schema's RLS predicate resolves through
    `mangaly_authz.has_scope()` / `is_self()`, both of which read this variable.
    """
    await set_local(session, VAR_AUTHZ_CONTEXT, str(subject_id))


async def set_dispatcher_context(session: AsyncSession) -> None:
    """[SP069] The outbox dispatcher's read role.

    Every `outbox_event` table's split RLS policy allows INSERT unconditionally
    but restricts SELECT to `mangaly.service_role = 'dispatcher'`, so only the
    dispatcher can read event payloads back out.
    """
    await set_local(session, VAR_SERVICE_ROLE, "dispatcher")


async def read_session_variable(session: AsyncSession, name: str) -> str:
    """Read a session variable back — used by the pooling-safety integration test."""
    result = await session.execute(
        text("SELECT current_setting(:name, true)"), {"name": name}
    )
    return result.scalar_one() or ""


@asynccontextmanager
async def request_transaction(
    session: AsyncSession, account_id: UUID | None = None
) -> AsyncIterator[AsyncSession]:
    """Open the one transaction a request's whole unit of work runs inside.

    [TR017] Because every session variable is transaction-local, the transaction
    boundary IS the authorization boundary: opening a second transaction for the
    same request would silently drop the context. Handlers therefore take an
    already-open session rather than opening their own.
    """
    async with session.begin():
        if account_id is not None:
            await set_account_context(session, account_id)
        yield session

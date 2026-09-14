"""The `SET LOCAL`-only RLS session-variable discipline.

# [TR16, TR30, TR-CROSSCUT-03] Every RLS session variable is set
# transaction-locally, never session-globally — a plain `SET` under
# transaction-mode pooling leaks one request's member context onto another
# pooled connection's next transaction (MODULE-ARCHITECTURE-STANDARD §4,
# second named failure mode).
# Approach: `SELECT set_config(name, value, true)` (bind-parameterised, and
# `true` = transaction-local, hardcoded — no call site can pass `false`).
# Setting a variable outside an open transaction raises instead of silently
# no-op'ing, because a silently empty RLS variable is a fail-open shape.
# Traces to: TR16, TR30, 07a-db-implementation/README.md "RLS session variables".
"""

from __future__ import annotations

from typing import Final
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

VAR_MEMBER_ID: Final = "milavn.member_id"
VAR_PERMISSION_SCOPE: Final = "milavn.permission_scope"
VAR_INTERNAL_SERVICE: Final = "milavn.internal_service"

_ALLOWED: Final[frozenset[str]] = frozenset({VAR_MEMBER_ID, VAR_PERMISSION_SCOPE, VAR_INTERNAL_SERVICE})
_SET_LOCAL_SQL = text("SELECT set_config(:name, :value, true)")


class SessionVariableError(RuntimeError):
    pass


async def set_local(session: AsyncSession, name: str, value: str) -> None:
    if name not in _ALLOWED:
        raise SessionVariableError(f"{name!r} is not a Milavn RLS session variable")
    if not session.in_transaction():
        raise SessionVariableError(f"Refusing to set {name!r}: no open transaction (SET LOCAL would be a no-op)")
    await session.execute(_SET_LOCAL_SQL, {"name": name, "value": value})


async def set_member_context(session: AsyncSession, member_id: UUID, scopes: list[str]) -> None:
    await set_local(session, VAR_MEMBER_ID, str(member_id))
    if scopes:
        await set_local(session, VAR_PERMISSION_SCOPE, ",".join(scopes))


async def set_internal_service_context(session: AsyncSession) -> None:
    """[TR27] Only the reputation engine / scan-validation paths — never a request."""
    await set_local(session, VAR_INTERNAL_SERVICE, "true")


async def read_session_variable(session: AsyncSession, name: str) -> str:
    result = await session.execute(text("SELECT current_setting(:name, true)"), {"name": name})
    return result.scalar_one() or ""

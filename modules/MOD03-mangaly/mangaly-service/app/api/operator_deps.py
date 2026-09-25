"""Operator dependencies — who may open the review queue.

# [DEC-V1-007/DEC-V1-028] An operator is an ordinary signed-in member who
# additionally holds a role in `mangaly_operations.operator`. `OperatorAccount(
# role)` resolves the session like any member request, checks the role, and
# then binds `mangaly.operator_role` for THIS transaction (SET LOCAL, per
# TR017/SP017) to the DB-level value the existing RLS policies read —
# 'operations' for moderator/operations, 'safety_case_investigation' for a
# safety investigator. Without that binding every operations table is empty
# under RLS, which is the correct fail-closed shape for a non-operator.
#
# A non-operator gets 404, not 403: the console does not exist for them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status

from app.api.deps import AuthenticatedSession, DbSession
from app.components.operations import interface as operations
from app.db.session import VAR_OPERATOR_ROLE, set_local

__all__ = ["OperatorAccount", "OperatorInfo", "Moderator"]


@dataclass(frozen=True, slots=True)
class OperatorInfo:
    account_id: UUID
    roles: tuple[str, ...]
    display_name: str | None


def OperatorAccount(role: str):  # noqa: N802 — reads as a type at the call site
    db_role = operations.ROLE_TO_DB_ROLE[role]

    async def dependency(caller: AuthenticatedSession, session: DbSession) -> OperatorInfo:
        roles = await operations.operator_roles(session, caller.account_id)
        if role not in roles:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        await set_local(session, VAR_OPERATOR_ROLE, db_role)
        return OperatorInfo(caller.account_id, tuple(roles), caller.display_name)

    return Depends(dependency)


Moderator = Annotated[OperatorInfo, OperatorAccount("moderator")]

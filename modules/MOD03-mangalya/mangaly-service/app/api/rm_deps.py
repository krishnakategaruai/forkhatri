"""The relationship-manager seat (DEC-V1-032).

`RmAccount` resolves the signed-in account as a relationship manager: the
account must be an active row of `mangaly_operations.relationship_manager`,
and the transaction is then bound with
`mangaly.operator_role = 'relationship_manager'` (SET LOCAL, like every RLS
variable — `app/db/session.py`). Migration 052's policies and helpers read
that variable, so an RM acting on an assignment is an RM *for this request*,
never by virtue of the account alone.

NOTE: another stream is building a general operator concept
(`mangaly_operations.operator`, roles text[], an `OperatorAccount(role)`
dependency; migration 048). This dependency and its table should merge into
that once both have landed (backlog).
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status

from app.api.deps import AuthenticatedAccount, DbSession, Locale
from app.db.session import VAR_OPERATOR_ROLE, set_local
from app.i18n import translate

RM_OPERATOR_ROLE = "relationship_manager"


async def get_rm_account(session: DbSession, account_id: AuthenticatedAccount, lang: Locale) -> UUID:
    from app.components.assisted_matching import interface as assisted

    if not await assisted.is_rm(session, account_id=account_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "not_relationship_manager", "message": translate("rm.error.notRm", lang)},
        )
    await set_local(session, VAR_OPERATOR_ROLE, RM_OPERATOR_ROLE)
    return account_id


RmAccount = Annotated[UUID, Depends(get_rm_account)]

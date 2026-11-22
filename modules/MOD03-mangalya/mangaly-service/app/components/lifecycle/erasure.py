"""Account deletion: erase everything Mangalya holds about a member.

[Owner requirement 2026-11-22; contract docs/ParentApp/ACCOUNT-DELETION.md;
inventory modules/MOD03-mangalya/ACCOUNT-DELETION.md.] The work is one
SECURITY DEFINER function per entry point (migration 067); this module only
calls it and removes the files it names after the commit.
"""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.profile import storage

__all__ = ["ErasureRefused", "erase_member", "erase_me", "to_contract", "remove_files"]

_RETAINED_REASONS = {
    "safety_reports": "A report about or by this member is kept without name or text, so someone removed for harm cannot simply return.",
    "contact_reports": "A report about a marriage agent is kept without name or text for the safety of other families.",
    "suspensions": "A moderation suspension is kept as a bare record so it cannot be dodged by deleting the account.",
    "case_appeals": "A moderation appeal is kept as a bare record.",
    "home_circle_reports": "A report made inside a Home Circle is kept without name or text.",
    "paid_orders": "A paid order is kept for tax and legal records, with amount and date only.",
}


class ErasureRefused(Exception):
    """The member holds a moderator role; it must be removed first."""


async def _run(session: AsyncSession, sql: str, params: dict[str, Any]) -> dict[str, Any]:
    try:
        raw = (await session.execute(text(sql), params)).scalar_one()
    except DBAPIError as exc:
        if getattr(getattr(exc, "orig", None), "sqlstate", None) == "MGL11" or "MGL11" in str(exc):
            raise ErasureRefused from exc
        raise
    return raw if isinstance(raw, dict) else json.loads(raw)


async def erase_me(session: AsyncSession) -> dict[str, Any]:
    """Erase the signed-in account (its id is bound in this transaction)."""
    return await _run(session, "SELECT mangaly_identity.erase_my_data()", {})


async def erase_member(session: AsyncSession, member_id: UUID) -> dict[str, Any]:
    """Erase a ForKhatri member's Mangalya data (service-to-service call)."""
    return await _run(session, "SELECT mangaly_identity.erase_member_data(:m)", {"m": member_id})


def remove_files(result: dict[str, Any]) -> int:
    return storage.remove_member_files(result.get("file_refs") or [], result.get("dirs") or [])


def to_contract(result: dict[str, Any], files_removed: int) -> dict[str, Any]:
    """The contract's response shape (docs/ParentApp/ACCOUNT-DELETION.md)."""
    retained = [
        {"kind": kind, "reason": _RETAINED_REASONS.get(kind, "Kept without identifying details.")}
        for kind in (result.get("retained") or {})
    ]
    return {
        "module": "mangalya",
        "status": result.get("status", "done"),
        "deleted": result.get("deleted") or {},
        "retained": retained,
        "files_removed": files_removed,
    }

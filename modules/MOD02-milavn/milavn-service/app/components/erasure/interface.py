"""Erase one member's data from Milavn (docs/ParentApp/ACCOUNT-DELETION.md, kinds A and B).

# [056] One routine for both callers: the platform (deleting a ForKhatri account, internal endpoint) and the member
# (Delete my data in Milavn). Steps, all in one database transaction:
#   1. hosted events that are still upcoming are cancelled the normal way (attendees told, paid spots refunded);
#   2. paid or held tickets on other people's upcoming events are withdrawn the normal way (refund, next person offered);
#   3. `milavn_platform.erase_member()` deletes or pseudonymises every other store (see ACCOUNT-DELETION.md);
# After commit the uploaded files it listed are removed from disk. If a refund cannot be requested the whole
# transaction rolls back and the answer is "partial": nothing is half deleted, the caller retries later.
"""

from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

from sqlalchemy import text

from app import media_files
from app.components.activity import interface as activity
from app.components.identity_bridge import interface as identity
from app.components.payments import interface as payments
from app.components.ticketing import interface as ticketing
from app.db.engine import get_process_session_factory
from app.db.session import set_internal_service_context, set_member_context
from app.events import bus

logger = logging.getLogger(__name__)


class ErasePartial(Exception):
    """Something outside the database (a refund) could not be done now. Nothing was deleted."""


async def erase_member(member_id: UUID) -> dict[str, Any]:
    names: list[str] = []
    try:
        ident = (await identity.display_names_for([member_id])).get(member_id)
        if ident and ident.display_name not in (identity.FALLBACK_DISPLAY_NAME, identity.DELETED_DISPLAY_NAME):
            names = [ident.display_name]
    except Exception:  # noqa: BLE001 - a name lookup must never block a deletion
        logger.warning("erase: could not look the member's name up; names inside other people's notices are left")
    factory = get_process_session_factory()
    upcoming: list = []
    paid: list = []
    try:
        async with factory() as s:
            async with s.begin():
                await set_member_context(s, member_id, [])
                await set_internal_service_context(s)
                upcoming = (
                    await s.execute(
                        text(
                            "SELECT id FROM milavn_activity.occurrence WHERE creator_member_id = :m AND status = 'active' "
                            "AND coalesce(time_end, time_start) > now()"
                        ),
                        {"m": str(member_id)},
                    )
                ).scalars().all()
                for occurrence_id in upcoming:
                    await activity.cancel(s, occurrence_id=occurrence_id, actor_member_id=member_id, reason="The host closed their account.")
                paid = (
                    await s.execute(
                        text(
                            "SELECT DISTINCT t.occurrence_id FROM milavn_ticketing.ticket t JOIN milavn_activity.occurrence o ON o.id = t.occurrence_id "
                            "WHERE t.member_id = :m AND t.status IN ('paid', 'awaiting_payment') AND o.status = 'active' "
                            "AND coalesce(o.time_end, o.time_start) > now()"
                        ),
                        {"m": str(member_id)},
                    )
                ).scalars().all()
                for occurrence_id in paid:
                    await ticketing.withdraw(s, occurrence_id=occurrence_id, member_id=member_id)
                raw = (await s.execute(text("SELECT milavn_platform.erase_member(:m, CAST(:n AS text[]))"), {"m": str(member_id), "n": names})).scalar_one()
                result: dict[str, Any] = json.loads(raw) if isinstance(raw, str) else raw
            await bus.dispatch_pending(s)
    except payments.PaymentsError as exc:
        logger.warning("erase: a refund could not be requested (%s); nothing deleted", type(exc).__name__)
        raise ErasePartial from exc
    refs = [r for r in result.get("files", []) if r]
    media_files.remove(*refs)
    deleted: dict[str, int] = result.get("deleted", {})
    if upcoming:
        deleted["events_cancelled"] = deleted.get("events_cancelled", 0) + len(upcoming)
    if paid:
        deleted["paid_spots_withdrawn_and_refunded"] = len(paid)
    pseudonymised: dict[str, int] = result.get("pseudonymised", {})
    seen: set[str] = set()
    retained = []
    for item in result.get("retained", []):
        if item["kind"] not in seen:
            seen.add(item["kind"])
            retained.append(item)
    return {
        "module": "milavn",
        "status": "done" if (deleted or pseudonymised) else "nothing_to_delete",
        "deleted": deleted,
        "pseudonymised": pseudonymised,
        "retained": retained,
        "files_removed": len(refs),
    }

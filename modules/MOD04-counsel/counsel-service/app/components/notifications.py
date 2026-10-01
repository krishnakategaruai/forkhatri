"""Notifications are domain events. `notify()` writes the in-app record and
fans out to every configured channel adapter (NOTIFICATION_CHANNELS). The
`log` adapter prints; email/sms/whatsapp/push adapters are swap seams that
queue a `delivery` row for an external provider connected later."""

from __future__ import annotations

import logging
from uuid import UUID

from app.settings import get_settings

log = logging.getLogger("counsel.notify")

# Channels that need an external provider queue a delivery for later dispatch.
QUEUED_CHANNELS = {"email", "sms", "whatsapp", "push"}


async def notify(conn, member_id: UUID | str, kind: str, params: dict | None = None, booking_id: UUID | str | None = None) -> None:
    params = params or {}
    mid = UUID(str(member_id))
    bid = UUID(str(booking_id)) if booking_id else None
    channels = [c.strip() for c in get_settings().notification_channels.split(",") if c.strip()]
    for ch in channels:
        if ch == "inapp":
            await conn.execute(
                "INSERT INTO notification (member_id, kind, params, booking_id) VALUES ($1,$2,$3,$4)", mid, kind, params, bid
            )
        elif ch == "log":
            log.info("notify %s -> %s %s", kind, mid, params)
        elif ch in QUEUED_CHANNELS:
            await conn.execute(
                "INSERT INTO delivery (member_id, channel, kind, payload) VALUES ($1,$2,$3,$4)",
                mid, ch, kind, {"params": params, "booking_id": str(bid) if bid else None},
            )

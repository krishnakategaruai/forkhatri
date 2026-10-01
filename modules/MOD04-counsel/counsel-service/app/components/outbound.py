"""Sends Counsel's queued deliveries (the `delivery` table written by
notifications.notify for email/sms/whatsapp/push) through ForKhatri's shared
delivery dispatcher and messaging senders (shared/forkhatri-integrations).

Counsel does not hold phone numbers or email addresses: the platform keeps
contact details. Until the platform offers a contact lookup (or its planned
notification service takes over delivery), `resolve` finds no destination and
rows are marked skipped rather than pretending they were sent."""

from __future__ import annotations

import logging

from app import db
from app.components import money
from app.settings import get_settings

log = logging.getLogger("counsel.outbound")


class CounselDeliveryStore:
    async def claim(self, limit):
        from forkhatri_integrations import delivery

        rows = await db.fetch(
            "UPDATE delivery SET status='sending' WHERE id IN (SELECT id FROM delivery WHERE status IN ('queued','retry') "
            "AND next_attempt_at <= now() ORDER BY id LIMIT $1 FOR UPDATE SKIP LOCKED) RETURNING *", limit)
        return [delivery.OutboxItem(id=r["id"], channel=r["channel"], recipient_id=str(r["member_id"]), kind=r["kind"],
                                    payload=r["payload"], attempts=r["attempts"]) for r in rows]

    async def resolve(self, item):
        return None   # no contact lookup yet (see module docstring and the shared BACKLOG)

    async def mark_sent(self, item, result):
        await db.execute("UPDATE delivery SET status='sent', sent_at=now(), attempts=attempts+1, provider=$2, provider_ref=$3 WHERE id=$1",
                         item.id, result.provider, result.reference)

    async def mark_failed(self, item, error, retry_at):
        await db.execute("UPDATE delivery SET status=$2, attempts=attempts+1, last_error=$3, next_attempt_at=COALESCE($4, next_attempt_at) WHERE id=$1",
                         item.id, "retry" if retry_at else "failed", error[:500], retry_at)

    async def mark_skipped(self, item, reason):
        await db.execute("UPDATE delivery SET status='skipped', last_error=$2 WHERE id=$1", item.id, reason[:500])


def dispatcher():
    from forkhatri_integrations import delivery, messaging

    s = get_settings()
    local = money.running_locally()
    senders = {ch: messaging.get_sender(ch, getattr(s, f"{ch}_provider"), allow_console=local) for ch in messaging.CHANNELS}
    return delivery.Dispatcher(CounselDeliveryStore(), senders)


async def dispatch_once() -> None:
    stats = await dispatcher().run_once()
    if stats.sent or stats.failed or stats.retrying:
        log.info("deliveries: %s", stats)

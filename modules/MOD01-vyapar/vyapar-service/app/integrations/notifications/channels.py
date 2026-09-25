# [TR021 swap seam, moved here from app/notifications.py by IMP37]
# NotificationChannel is the adapter interface a host's notification service
# plugs into. The in-app inbox is the one always-on channel (written by
# app/notifications.py's send_notification(), which also carries kind,
# template and idempotency key). WebPushChannel is a structural stub behind
# placeholder VAPID keys. A third channel exists for machines rather than
# people: outbound webhooks (app/integrations/webhooks/), fed by the outbox.
# A host wiring its own notification service (SMS, WhatsApp, email, a
# platform push service) implements NotificationChannel.deliver().
from __future__ import annotations

from typing import Protocol

import asyncpg

from app.config import get_settings


class NotificationChannel(Protocol):
    async def deliver(self, conn: asyncpg.Connection, member_id: str, title: str, body: str | None, link: str | None) -> None: ...


class InAppChannel:
    """[TR021] The one real, always-available channel — writes the inbox
    row every /v1/notifications read serves. `idempotency_key` is UNIQUE at
    the DB level (already modeled), so a retried send is a no-op, never a
    duplicate — TR052's own delivery contract, enforced structurally."""

    async def deliver(self, conn: asyncpg.Connection, member_id: str, title: str, body: str | None, link: str | None) -> None:
        pass  # writing happens in send_notification() itself (needs kind/template/idempotency_key too)


class WebPushChannel:
    """[Decision] Structural stub behind placeholder VAPID keys — no
    push-subscription table/flow exists yet, so this is never actually
    invoked by `send_notification()`'s default channel list. Exists so a
    future real Web Push integration is a channel addition, not a redesign
    of every call site that sends a notification today."""

    async def deliver(self, conn: asyncpg.Connection, member_id: str, title: str, body: str | None, link: str | None) -> None:
        settings = get_settings()
        if settings.vapid_public_key.startswith("CHANGE_ME"):
            return  # no real subscription/push infra wired yet — honest no-op

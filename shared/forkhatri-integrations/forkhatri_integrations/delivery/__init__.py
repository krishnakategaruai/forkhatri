"""Delivery: send what a module queued in its outbox, with retries.

A module keeps its own outbox table (written in the same transaction as the
change that caused it) and implements `OutboxStore` for that table. The
`Dispatcher` claims due rows, asks the module to turn each into a message
(recipient lookup, language, wording), sends it through the channel's
`Sender`, and records the result:

    dispatcher = delivery.Dispatcher(MyStore(pool), senders={"sms": sms_sender, "email": email_sender})
    await dispatcher.run_once()           # from the module's housekeeping loop

Failures retry with exponential backoff (30 s, 1 min, 2 min ... capped at 1 h)
up to `max_attempts`, then the row is marked failed for good.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

from ..messaging.types import OutboundMessage, SendResult, Sender

__all__ = ["OutboxItem", "OutboxStore", "Dispatcher", "DispatchStats", "backoff"]

log = logging.getLogger("forkhatri.delivery")


@dataclass(frozen=True, slots=True)
class OutboxItem:
    id: Any
    channel: str
    recipient_id: str
    kind: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    attempts: int = 0


class OutboxStore(Protocol):
    async def claim(self, limit: int) -> list[OutboxItem]:
        """Due rows, locked so two dispatchers never send the same one (e.g. FOR UPDATE SKIP LOCKED)."""
        ...

    async def resolve(self, item: OutboxItem) -> OutboundMessage | None:
        """The message to send, or None to skip (no phone on file, opted out, channel muted)."""
        ...

    async def mark_sent(self, item: OutboxItem, result: SendResult) -> None: ...

    async def mark_failed(self, item: OutboxItem, error: str, retry_at: datetime | None) -> None:
        """retry_at None means give up on this row."""
        ...

    async def mark_skipped(self, item: OutboxItem, reason: str) -> None: ...


def backoff(attempt: int, base_seconds: int = 30, cap_seconds: int = 3600) -> timedelta:
    return timedelta(seconds=min(cap_seconds, base_seconds * 2 ** max(0, attempt - 1)))


@dataclass
class DispatchStats:
    sent: int = 0
    retrying: int = 0
    failed: int = 0
    skipped: int = 0


class Dispatcher:
    def __init__(self, store: OutboxStore, senders: Mapping[str, Sender], *, batch_size: int = 50, max_attempts: int = 6) -> None:
        self.store = store
        self.senders = senders
        self.batch_size = batch_size
        self.max_attempts = max_attempts

    async def run_once(self) -> DispatchStats:
        stats = DispatchStats()
        for item in await self.store.claim(self.batch_size):
            sender = self.senders.get(item.channel)
            if sender is None or not sender.available:
                await self.store.mark_skipped(item, f"{item.channel} is not switched on")
                stats.skipped += 1
                continue
            try:
                message = await self.store.resolve(item)
            except Exception as exc:  # a module bug must not stop the whole batch
                log.exception("outbox %s could not be prepared", item.id)
                await self.store.mark_failed(item, f"prepare: {type(exc).__name__}", None)
                stats.failed += 1
                continue
            if message is None:
                await self.store.mark_skipped(item, "no destination")
                stats.skipped += 1
                continue
            try:
                result = await sender.send(message)
            except Exception as exc:
                result = SendResult(ok=False, provider=sender.name, error=type(exc).__name__, retryable=True)
            attempt = item.attempts + 1
            if result.ok:
                await self.store.mark_sent(item, result)
                stats.sent += 1
            elif result.retryable and attempt < self.max_attempts:
                await self.store.mark_failed(item, result.error, datetime.now(timezone.utc) + backoff(attempt))
                stats.retrying += 1
            else:
                await self.store.mark_failed(item, result.error, None)
                stats.failed += 1
        return stats

    async def run_forever(self, interval_seconds: float, stop: asyncio.Event) -> None:
        while not stop.is_set():
            try:
                await self.run_once()
            except Exception:
                log.exception("delivery pass failed")
            try:
                await asyncio.wait_for(stop.wait(), timeout=interval_seconds)
            except asyncio.TimeoutError:
                pass

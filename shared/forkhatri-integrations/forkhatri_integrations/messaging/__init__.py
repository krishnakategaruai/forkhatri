"""Messaging: SMS, WhatsApp, email and push behind one interface.

    from forkhatri_integrations import messaging
    sender = messaging.get_sender("sms", settings.sms_provider, allow_console=running_locally)
    result = await sender.send(messaging.OutboundMessage(channel="sms", to="+9198...", body=text, idempotency_key=key))

Adapters available now: "console" (logs; local development only) and
"disabled" (the channel is not offered). Vendors (MSG91, Gupshup, Meta
WhatsApp Cloud API, Resend, Amazon SES, Web Push, ...) are added later with
`register_sender(channel, name, factory)`; the candidates are in BACKLOG.md.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from typing import Any

from .._common import mask
from .types import CHANNELS, Channel, OutboundMessage, SendResult, Sender

__all__ = ["CHANNELS", "Channel", "OutboundMessage", "SendResult", "Sender", "ConsoleSender", "DisabledSender",
           "get_sender", "register_sender", "available_senders", "render"]

log = logging.getLogger("forkhatri.messaging")


class ConsoleSender:
    """Development only: writes the message to the log instead of sending it."""

    live = False
    available = True

    def __init__(self, channel: Channel) -> None:
        self.channel = channel
        self.name = "console"

    async def send(self, message: OutboundMessage) -> SendResult:
        log.warning("DEVELOPMENT %s to %s: %s", message.channel, mask(message.to), message.subject or message.body)
        return SendResult(ok=True, provider=self.name, reference=f"console:{message.idempotency_key}")


class DisabledSender:
    """The channel is switched off here. Nothing is sent and the caller is told plainly."""

    live = False
    available = False

    def __init__(self, channel: Channel) -> None:
        self.channel = channel
        self.name = "disabled"

    async def send(self, message: OutboundMessage) -> SendResult:
        return SendResult(ok=False, provider=self.name, error=f"{message.channel} is not switched on", retryable=False)


# (channel, name) -> factory(channel=..., **options)
_FACTORIES: dict[tuple[str, str], Callable[..., Sender]] = {}
for _ch in CHANNELS:
    _FACTORIES[(_ch, "console")] = lambda channel, **_: ConsoleSender(channel)
    _FACTORIES[(_ch, "disabled")] = lambda channel, **_: DisabledSender(channel)
_DEV_ONLY = {"console"}


def register_sender(channel: Channel, name: str, factory: Callable[..., Sender], *, dev_only: bool = False) -> None:
    """Adds a vendor adapter for one channel. `factory(channel=..., **options)` builds it."""
    _FACTORIES[(channel, name)] = factory
    if dev_only:
        _DEV_ONLY.add(name)


def available_senders(channel: Channel) -> list[str]:
    return sorted(n for c, n in _FACTORIES if c == channel)


def get_sender(channel: Channel, name: str | None, *, allow_console: bool = False, **options: Any) -> Sender:
    """The adapter `name` for `channel`. A development-only adapter outside local
    development, or an unknown name, gives the disabled sender instead."""
    name = (name or "disabled").strip().lower()
    if (channel, name) not in _FACTORIES or (name in _DEV_ONLY and not allow_console):
        name = "disabled"
    return _FACTORIES[(channel, name)](channel=channel, **options)


def render(templates: Mapping[str, Mapping[str, str]], key: str, language: str, params: Mapping[str, object] | None = None) -> str:
    """Text for `key` in `language` (falling back to English), with {name} placeholders filled.
    Modules keep their own wording; this only picks and fills it."""
    by_lang = templates.get(key) or {}
    text = by_lang.get(language) or by_lang.get("en") or key
    try:
        return text.format(**(params or {}))
    except (KeyError, IndexError, ValueError):
        return text

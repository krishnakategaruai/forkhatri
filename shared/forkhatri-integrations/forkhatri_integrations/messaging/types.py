"""The contract for sending a message to a person outside the app."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Literal, Protocol

Channel = Literal["sms", "whatsapp", "email", "push"]
CHANNELS: tuple[Channel, ...] = ("sms", "whatsapp", "email", "push")


@dataclass(frozen=True, slots=True)
class OutboundMessage:
    channel: Channel
    to: str                        # phone in E.164 (+91...), email address, or push subscription/device token
    body: str                      # plain text, already in the person's language
    idempotency_key: str           # the same key must never deliver twice
    subject: str = ""              # email only
    html: str = ""                 # email only
    language: str = "en"
    # Pre-registered provider templates: India's DLT template id for SMS, the approved
    # WhatsApp template name. Vendors that need them refuse a message without one.
    template_id: str = ""
    template_params: Sequence[str] = ()
    link: str = ""                 # deep link for push and WhatsApp buttons
    metadata: Mapping[str, str] = field(default_factory=dict)
    sensitive: bool = False        # a one-time code: never log the body outside development


@dataclass(frozen=True, slots=True)
class SendResult:
    ok: bool
    provider: str
    reference: str = ""            # the vendor's message id
    error: str = ""
    retryable: bool = False        # True for timeouts and 5xx; False for a bad number or a refused template


class Sender(Protocol):
    name: str
    channel: Channel
    available: bool                # False means the channel is not offered here
    live: bool                     # True only when a real message leaves the system

    async def send(self, message: OutboundMessage) -> SendResult: ...

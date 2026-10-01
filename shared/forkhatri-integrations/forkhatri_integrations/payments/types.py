"""The payment contract every module codes against, whatever moves the money.

Amounts are integers in the currency's minor unit (paise for INR). A module
stores only the references returned here, never card, bank or UPI details.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal, Protocol

ChargeStatus = Literal["pending", "succeeded", "failed", "cancelled"]
EventType = Literal["payment.succeeded", "payment.failed", "refund.succeeded", "refund.failed", "payout.succeeded", "payout.failed"]


class PaymentsError(Exception):
    """Base class for every payment failure."""


class PaymentsNotConfigured(PaymentsError):
    """No payment provider is connected yet. Say so plainly; never pretend a payment worked."""


class PaymentsUnavailable(PaymentsError):
    """The provider refused or could not be reached. The module keeps its order and retries later."""


class EventRejected(PaymentsError):
    """A webhook with a bad signature or an unreadable body. Answer 400 and never apply it."""


@dataclass(frozen=True, slots=True)
class ChargeRequest:
    idempotency_key: str          # the same key returns the same charge
    payer_id: str                 # ForKhatri member id
    amount_minor: int
    currency: str = "INR"
    purpose: str = ""             # e.g. "counsel.booking", "milavn.activity_spot"
    description: str = ""
    return_url: str = ""          # where the payer lands after a hosted checkout
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Charge:
    reference: str                # the provider's id for this charge; store it
    status: ChargeStatus = "pending"
    checkout_url: str | None = None           # hosted page to send the payer to, if any
    client_payload: Mapping[str, object] = field(default_factory=dict)  # what an in-page checkout needs (public key, order id)


@dataclass(frozen=True, slots=True)
class RefundRequest:
    charge_reference: str
    amount_minor: int
    idempotency_key: str
    reason: str = ""


@dataclass(frozen=True, slots=True)
class Refund:
    reference: str
    settled: bool                 # True when confirmed now; otherwise a refund event follows


@dataclass(frozen=True, slots=True)
class PayoutRequest:
    idempotency_key: str
    payee_id: str                 # ForKhatri member id being paid
    amount_minor: int
    currency: str = "INR"
    # The destination as the module holds it (decrypted only for this call), e.g.
    # {"method": "upi", "upi_id": "..."} or {"method": "bank", "account": "...", "ifsc": "..."}.
    destination: Mapping[str, str] = field(default_factory=dict)
    narration: str = ""


@dataclass(frozen=True, slots=True)
class Payout:
    reference: str
    settled: bool


@dataclass(frozen=True, slots=True)
class PaymentEvent:
    event_id: str                 # dedupe on this
    type: EventType
    reference: str                # charge, refund or payout reference
    charge_reference: str | None = None
    amount_minor: int | None = None
    raw: Mapping[str, object] = field(default_factory=dict)


class PaymentGateway(Protocol):
    """What a module may ask of any payment provider."""

    name: str
    configured: bool   # False means every call raises PaymentsNotConfigured
    live: bool         # True only when real money moves

    async def create_charge(self, request: ChargeRequest) -> Charge: ...

    async def get_charge_status(self, reference: str) -> ChargeStatus | None: ...

    def verify_return(self, reference: str, proof: Mapping[str, str]) -> bool:
        """Checks what the browser brings back from an in-page checkout (for example a signed
        payment id). A webhook remains the source of truth; this only speeds up the happy path."""
        ...

    async def cancel_charge(self, reference: str) -> None: ...

    async def refund(self, request: RefundRequest) -> Refund: ...

    async def create_payout(self, request: PayoutRequest) -> Payout: ...

    def parse_event(self, raw_body: bytes, headers: Mapping[str, str]) -> PaymentEvent | None:
        """Verifies and reads a provider webhook. Raises EventRejected on a bad signature;
        returns None for event types the modules do not need."""
        ...

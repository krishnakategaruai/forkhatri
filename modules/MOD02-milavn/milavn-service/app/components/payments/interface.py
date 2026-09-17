"""Payment Services port — how Milavn asks for money to move (FR102).

# [FR102, FR075 boundary, ARCHITECTURE.md MOD06 row, ADR-008] Milavn never
# captures, holds or refunds money itself and never sees card or UPI data. It
# asks Payment Services (MOD06) to create a charge, cancel it, or refund it,
# and stores only the returned reference. The provider behind MOD06 (gateway,
# UPI rails) is an external dependency owned by the product owner.
# Approach: one small provider-agnostic protocol with three adapters chosen by
# configuration:
#   none              — the default. Every call raises PaymentsNotConfigured, so a
#                       paid activity says plainly that payments are not switched
#                       on yet instead of pretending.
#   sandbox           — development only (refused unless the API and web run on
#                       localhost): a test checkout inside Milavn where the payer
#                       presses "Pay" or "Fail". No money moves. It exists so the
#                       whole product flow can be exercised end to end before
#                       MOD06 exists.
#   payment_services  — the HTTP client for MOD06's Payment Services App, using the
#                       contract proposed below. MOD06 is not built yet, so this
#                       adapter is the integration point, recorded as a blocker.
# Traces to: FR102, FR036 (payments never feed trust), 09-implementation.md IMP27.
#
# Proposed contract (for MOD06 to confirm):
#   POST {base}/v1/charges            {idempotency_key, payer_member_id, amount_paise, currency, purpose,
#                                       description, return_url, metadata} -> {reference, checkout_url}
#   POST {base}/v1/charges/{ref}/cancel                                  -> 204
#   POST {base}/v1/refunds            {charge_reference, amount_paise, reason, idempotency_key}
#                                                                          -> {reference, status: pending|succeeded}
#   Events to Milavn: POST {milavn}/payments/events with X-ForKhatri-Service: payments and
#   X-ForKhatri-Service-Key, body {event_id, type: payment.succeeded|payment.failed|refund.succeeded, reference}
"""

from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass
from typing import Protocol
from uuid import NAMESPACE_URL, UUID, uuid5

import httpx

from app.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)

CURRENCY = "INR"
PURPOSE = "milavn.activity_spot"


class PaymentsError(Exception):
    pass


class PaymentsNotConfigured(PaymentsError):
    """No payment provider is connected (the external dependency is still open)."""


class PaymentsUnavailable(PaymentsError):
    """The provider was reachable in principle but refused or failed this call."""


@dataclass(frozen=True, slots=True)
class Charge:
    reference: str
    checkout_url: str | None


@dataclass(frozen=True, slots=True)
class Refund:
    reference: str
    settled: bool  # True when the provider confirms the refund immediately (sandbox); otherwise an event follows


class PaymentServices(Protocol):
    name: str
    configured: bool

    async def create_charge(
        self, *, idempotency_key: str, payer_member_id: UUID, amount_paise: int, description: str, return_url: str, metadata: dict[str, str]
    ) -> Charge: ...

    async def cancel_charge(self, *, reference: str) -> None: ...

    async def refund(self, *, charge_reference: str, amount_paise: int, reason: str, idempotency_key: str) -> Refund: ...


class NotConfiguredPaymentServices:
    name = "none"
    configured = False

    async def create_charge(self, **_: object) -> Charge:
        raise PaymentsNotConfigured

    async def cancel_charge(self, **_: object) -> None:
        raise PaymentsNotConfigured

    async def refund(self, **_: object) -> Refund:
        raise PaymentsNotConfigured


class SandboxPaymentServices:
    """Development test double. References are derived from the idempotency key, so a retry returns the same charge."""

    name = "sandbox"
    configured = True

    def __init__(self, web_base_url: str) -> None:
        self._web = web_base_url.rstrip("/")

    async def create_charge(
        self, *, idempotency_key: str, payer_member_id: UUID, amount_paise: int, description: str, return_url: str, metadata: dict[str, str]
    ) -> Charge:
        reference = f"sbx_{uuid5(NAMESPACE_URL, idempotency_key).hex}"
        return Charge(reference, f"{self._web}/pay/sandbox?ref={reference}")

    async def cancel_charge(self, *, reference: str) -> None:
        return None

    async def refund(self, *, charge_reference: str, amount_paise: int, reason: str, idempotency_key: str) -> Refund:
        return Refund(f"sbxrf_{uuid5(NAMESPACE_URL, idempotency_key).hex}", settled=True)


class HttpPaymentServices:
    """Client for MOD06 Payment Services App (contract in the module docstring)."""

    name = "payment_services"

    def __init__(self, base_url: str, service_name: str, service_key: str) -> None:
        self._base = base_url.rstrip("/")
        self._headers = {"X-ForKhatri-Service": service_name, "X-ForKhatri-Service-Key": service_key}
        self.configured = bool(self._base) and bool(service_key) and not service_key.startswith("CHANGE_ME")

    async def _post(self, path: str, body: dict, idempotency_key: str | None = None) -> dict:
        if not self.configured:
            raise PaymentsNotConfigured
        headers = dict(self._headers)
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=2.0)) as client:
                res = await client.post(f"{self._base}{path}", json=body, headers=headers)
        except httpx.HTTPError as exc:
            raise PaymentsUnavailable(str(exc)) from exc
        if res.status_code >= 400:
            raise PaymentsUnavailable(f"{path} -> {res.status_code}")
        return res.json() if res.content else {}

    async def create_charge(
        self, *, idempotency_key: str, payer_member_id: UUID, amount_paise: int, description: str, return_url: str, metadata: dict[str, str]
    ) -> Charge:
        data = await self._post(
            "/v1/charges",
            {
                "idempotency_key": idempotency_key,
                "payer_member_id": str(payer_member_id),
                "amount_paise": amount_paise,
                "currency": CURRENCY,
                "purpose": PURPOSE,
                "description": description[:140],
                "return_url": return_url,
                "metadata": metadata,
            },
            idempotency_key,
        )
        return Charge(str(data["reference"]), data.get("checkout_url"))

    async def cancel_charge(self, *, reference: str) -> None:
        await self._post(f"/v1/charges/{reference}/cancel", {})

    async def refund(self, *, charge_reference: str, amount_paise: int, reason: str, idempotency_key: str) -> Refund:
        data = await self._post(
            "/v1/refunds", {"charge_reference": charge_reference, "amount_paise": amount_paise, "reason": reason, "idempotency_key": idempotency_key}, idempotency_key
        )
        return Refund(str(data["reference"]), data.get("status") == "succeeded")


def get_payment_services(settings: Settings | None = None) -> PaymentServices:
    s = settings or get_settings()
    if s.payments_provider == "sandbox":
        if s.payments_sandbox_allowed:
            return SandboxPaymentServices(s.web_base_url)
        logger.warning("payments_provider=sandbox refused outside localhost; payments are off")
        return NotConfiguredPaymentServices()
    if s.payments_provider == "payment_services":
        return HttpPaymentServices(s.payment_services_url, s.platform_service_name, s.payment_services_key)
    return NotConfiguredPaymentServices()


def verify_event_caller(settings: Settings, service: str | None, key: str | None) -> bool:
    """Payment Services events are accepted only with the shared key; a placeholder key accepts nothing."""
    expected = settings.payment_services_webhook_key
    if not expected or expected.startswith("CHANGE_ME") or service != "payments" or not key:
        return False
    return secrets.compare_digest(key, expected)

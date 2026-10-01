"""Payments: the one interface modules import.

    from forkhatri_integrations import payments
    gw = payments.get_gateway(settings.payments_provider, allow_sandbox=running_locally,
                              webhook_secret=settings.payments_webhook_secret)
    charge = await gw.create_charge(payments.ChargeRequest(idempotency_key=..., payer_id=..., amount_minor=...))

Adapters available now: "none", "sandbox" (local development only) and
"payment_services" (the future MOD06 service). A real gateway (Razorpay,
Cashfree, ...) is added later with `register_gateway(name, factory)`; the
candidates are listed in BACKLOG.md.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .adapters import EVENT_ID_HEADER, SIGNATURE_HEADER, NotConfiguredGateway, PaymentServicesGateway, SandboxGateway
from .types import (
    Charge,
    ChargeRequest,
    ChargeStatus,
    EventRejected,
    PaymentEvent,
    PaymentGateway,
    PaymentsError,
    PaymentsNotConfigured,
    PaymentsUnavailable,
    Payout,
    PayoutRequest,
    Refund,
    RefundRequest,
)

__all__ = [
    "Charge", "ChargeRequest", "ChargeStatus", "EventRejected", "PaymentEvent", "PaymentGateway", "PaymentsError",
    "PaymentsNotConfigured", "PaymentsUnavailable", "Payout", "PayoutRequest", "Refund", "RefundRequest",
    "SIGNATURE_HEADER", "EVENT_ID_HEADER", "SandboxGateway", "get_gateway", "register_gateway", "available_gateways",
]

_FACTORIES: dict[str, Callable[..., PaymentGateway]] = {
    "none": lambda **_: NotConfiguredGateway(),
    "sandbox": lambda webhook_secret="forkhatri-sandbox", checkout_base_url="", **_: SandboxGateway(webhook_secret, checkout_base_url),
    "payment_services": lambda base_url="", service_name="", service_key="", webhook_secret="", **_: PaymentServicesGateway(
        base_url, service_name, service_key, webhook_secret),
}
_DEV_ONLY = {"sandbox"}
_cache: dict[tuple, PaymentGateway] = {}


def register_gateway(name: str, factory: Callable[..., PaymentGateway], *, dev_only: bool = False) -> None:
    """Adds a vendor adapter. `factory(**options)` receives the options the module passes to get_gateway."""
    _FACTORIES[name] = factory
    if dev_only:
        _DEV_ONLY.add(name)
    for key in [k for k in _cache if k[0] == name]:
        del _cache[key]


def available_gateways() -> list[str]:
    return sorted(_FACTORIES)


def get_gateway(name: str | None, *, allow_sandbox: bool = False, **options: Any) -> PaymentGateway:
    """Returns the adapter called `name`, built once per set of options.

    A development-only adapter is refused (payments switched off) unless the
    module confirms it runs locally, so a mis-set production config can never
    fake a payment. An unknown name also switches payments off."""
    name = (name or "none").strip().lower()
    if name not in _FACTORIES or (name in _DEV_ONLY and not allow_sandbox):
        name = "none"
    key = (name, tuple(sorted((k, str(v)) for k, v in options.items())))
    if key not in _cache:
        _cache[key] = _FACTORIES[name](**options)
    return _cache[key]

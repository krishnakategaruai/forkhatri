"""Payment gateway — behind an interface (DEC-V1-031; external-vendor rule).

# Razorpay is the Indian standard (UPI, cards, netbanking). Everything on our
# side is built; the vendor keys are the one blocker, documented in
# `mangaly-service/.env.example` as RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET /
# RAZORPAY_WEBHOOK_SECRET. With no keys the DevSandboxGateway is used: it
# creates an order and lets a developer "pay" it through a dev-only endpoint
# that refuses to exist once real keys are present.
#
# Shapes follow Razorpay's documented contract:
#   POST https://api.razorpay.com/v1/orders  (basic auth key_id:key_secret)
#     {amount: <paise>, currency: "INR", receipt: "<our order id>", notes: {...}}
#     -> {id: "order_...", amount, currency, receipt, status: "created", ...}
#   Checkout success handler returns
#     {razorpay_order_id, razorpay_payment_id, razorpay_signature}
#     signature = HMAC_SHA256(key_secret, order_id + "|" + payment_id)
#   Webhook: header X-Razorpay-Signature = HMAC_SHA256(webhook_secret, raw body);
#     body {event: "payment.captured" | "order.paid" | "payment.failed",
#           payload: {payment: {entity: {id, order_id, status, ...}}, order?: {...}}}
#     header X-Razorpay-Event-Id is the idempotency key.
#
# Moving this to MOD06-payment-services as a shared platform capability is
# on the backlog; the Protocol below is the seam that move will keep.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import secrets
from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

import httpx

from app.config.settings import Settings

logger = logging.getLogger(__name__)

RAZORPAY_API = "https://api.razorpay.com/v1"


@dataclass(frozen=True, slots=True)
class GatewayOrder:
    """What the client needs to open checkout."""

    gateway: str
    gateway_order_id: str
    amount_paise: int
    currency: str
    # Razorpay's public key id, sent to the browser; None for the sandbox.
    key_id: str | None


@dataclass(frozen=True, slots=True)
class WebhookEvent:
    event_id: str
    event_type: str
    gateway_order_id: str | None
    gateway_payment_id: str | None
    payload: dict[str, Any]


class WebhookRejected(Exception):
    """Bad signature or malformed body — answer 400, never process."""


class PaymentGateway(Protocol):
    name: str

    async def create_order(
        self, *, order_id: UUID, amount_paise: int, currency: str, notes: dict[str, str]
    ) -> GatewayOrder: ...

    def verify_payment_signature(
        self, *, gateway_order_id: str, gateway_payment_id: str, signature: str
    ) -> bool: ...

    def parse_webhook(self, *, raw_body: bytes, headers: dict[str, str]) -> WebhookEvent: ...


def _hmac_sha256_hex(secret: str, message: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


class RazorpayGateway:
    """Real request/response shapes; the network call is the only vendor touch."""

    name = "razorpay"

    def __init__(self, *, key_id: str, key_secret: str, webhook_secret: str) -> None:
        self._key_id = key_id
        self._key_secret = key_secret
        self._webhook_secret = webhook_secret

    async def create_order(
        self, *, order_id: UUID, amount_paise: int, currency: str, notes: dict[str, str]
    ) -> GatewayOrder:
        body = {
            "amount": amount_paise,
            "currency": currency,
            # Razorpay's receipt is our order id, ≤ 40 chars.
            "receipt": str(order_id),
            "notes": notes,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                f"{RAZORPAY_API}/orders", json=body, auth=(self._key_id, self._key_secret)
            )
        if res.status_code >= 400:
            logger.error("razorpay order create failed: %s %s", res.status_code, res.text[:200])
            raise RuntimeError("gateway_order_failed")
        data = res.json()
        return GatewayOrder(
            gateway=self.name,
            gateway_order_id=str(data["id"]),
            amount_paise=int(data["amount"]),
            currency=str(data["currency"]),
            key_id=self._key_id,
        )

    def verify_payment_signature(
        self, *, gateway_order_id: str, gateway_payment_id: str, signature: str
    ) -> bool:
        expected = _hmac_sha256_hex(
            self._key_secret, f"{gateway_order_id}|{gateway_payment_id}".encode()
        )
        return hmac.compare_digest(expected, signature.strip().lower())

    def parse_webhook(self, *, raw_body: bytes, headers: dict[str, str]) -> WebhookEvent:
        lower = {k.lower(): v for k, v in headers.items()}
        signature = lower.get("x-razorpay-signature", "")
        if not signature or not hmac.compare_digest(
            _hmac_sha256_hex(self._webhook_secret, raw_body), signature.strip().lower()
        ):
            raise WebhookRejected("bad signature")
        try:
            body = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise WebhookRejected("malformed body") from exc
        event_type = str(body.get("event", ""))
        payload = body.get("payload") or {}
        payment = (payload.get("payment") or {}).get("entity") or {}
        order = (payload.get("order") or {}).get("entity") or {}
        gateway_order_id = payment.get("order_id") or order.get("id")
        event_id = lower.get("x-razorpay-event-id") or hashlib.sha256(raw_body).hexdigest()
        return WebhookEvent(
            event_id=str(event_id),
            event_type=event_type,
            gateway_order_id=str(gateway_order_id) if gateway_order_id else None,
            gateway_payment_id=str(payment["id"]) if payment.get("id") else None,
            payload=body,
        )


class DevSandboxGateway:
    """DEVELOPMENT ONLY. No money moves. Used when no RAZORPAY_* key is set.

    A sandbox order gets a local id; `POST /billing/dev/pay/{order_id}` marks
    it paid. `verify_payment_signature` accepts the sandbox's own signature
    scheme so the confirm path can be exercised end to end; webhooks are
    signed with a fixed dev secret."""

    name = "dev-sandbox"
    _DEV_SECRET = "mangaly-dev-sandbox"

    async def create_order(
        self, *, order_id: UUID, amount_paise: int, currency: str, notes: dict[str, str]
    ) -> GatewayOrder:
        return GatewayOrder(
            gateway=self.name,
            gateway_order_id=f"sandbox_{secrets.token_hex(8)}",
            amount_paise=amount_paise,
            currency=currency,
            key_id=None,
        )

    def sign(self, gateway_order_id: str, gateway_payment_id: str) -> str:
        return _hmac_sha256_hex(self._DEV_SECRET, f"{gateway_order_id}|{gateway_payment_id}".encode())

    def verify_payment_signature(
        self, *, gateway_order_id: str, gateway_payment_id: str, signature: str
    ) -> bool:
        return hmac.compare_digest(self.sign(gateway_order_id, gateway_payment_id), signature)

    def parse_webhook(self, *, raw_body: bytes, headers: dict[str, str]) -> WebhookEvent:
        lower = {k.lower(): v for k, v in headers.items()}
        expected = _hmac_sha256_hex(self._DEV_SECRET, raw_body)
        if not hmac.compare_digest(expected, lower.get("x-razorpay-signature", "")):
            raise WebhookRejected("bad signature")
        body = json.loads(raw_body)
        payment = ((body.get("payload") or {}).get("payment") or {}).get("entity") or {}
        return WebhookEvent(
            event_id=str(lower.get("x-razorpay-event-id") or hashlib.sha256(raw_body).hexdigest()),
            event_type=str(body.get("event", "")),
            gateway_order_id=payment.get("order_id"),
            gateway_payment_id=payment.get("id"),
            payload=body,
        )


def razorpay_configured(settings: Settings) -> bool:
    return bool(
        settings.razorpay_key_id
        and settings.razorpay_key_id != "CHANGE_ME"
        and settings.razorpay_key_secret
        and settings.razorpay_key_secret != "CHANGE_ME"
    )


class SharedLibraryGateway:
    """PAYMENT_GATEWAY=shared:<adapter>: billing through ForKhatri's shared payments
    library (shared/forkhatri-integrations), which every module uses, so one vendor
    adapter (or MOD06) serves all of them. Opt-in; the gateways above are unchanged."""

    def __init__(self, settings: Settings, adapter: str) -> None:
        from forkhatri_integrations import payments

        self._p = payments
        self.gw = payments.get_gateway(
            adapter, allow_sandbox=settings.payments_allow_sandbox, webhook_secret=settings.payments_webhook_secret,
            base_url=settings.payment_services_url, service_name="mangaly", service_key=settings.payment_services_key,
        )
        self.name = f"shared:{self.gw.name}"

    async def create_order(
        self, *, order_id: UUID, amount_paise: int, currency: str, notes: dict[str, str]
    ) -> GatewayOrder:
        charge = await self.gw.create_charge(self._p.ChargeRequest(
            idempotency_key=f"mangaly-order-{order_id}", payer_id="", amount_minor=amount_paise, currency=currency,
            purpose="mangaly.plan", metadata=notes))
        key_id = charge.client_payload.get("key_id")
        return GatewayOrder(gateway=self.name, gateway_order_id=charge.reference, amount_paise=amount_paise,
                            currency=currency, key_id=str(key_id) if key_id else None)

    def verify_payment_signature(
        self, *, gateway_order_id: str, gateway_payment_id: str, signature: str
    ) -> bool:
        return self.gw.verify_return(gateway_order_id, {"result": "success", "payment_id": gateway_payment_id, "signature": signature})

    def parse_webhook(self, *, raw_body: bytes, headers: dict[str, str]) -> WebhookEvent:
        try:
            ev = self.gw.parse_event(raw_body, headers)
        except self._p.EventRejected as exc:
            raise WebhookRejected(str(exc)) from exc
        if ev is None:
            return WebhookEvent(event_id=hashlib.sha256(raw_body).hexdigest(), event_type="ignored",
                                gateway_order_id=None, gateway_payment_id=None, payload={})
        # Mapped onto the event names billing already acts on.
        kind = {"payment.succeeded": "payment.captured", "payment.failed": "payment.failed"}.get(ev.type, ev.type)
        return WebhookEvent(event_id=ev.event_id, event_type=kind, gateway_order_id=ev.charge_reference or ev.reference,
                            gateway_payment_id=ev.reference, payload=dict(ev.raw))


def gateway_for(settings: Settings) -> PaymentGateway:
    if settings.payment_gateway.startswith("shared:"):
        return SharedLibraryGateway(settings, settings.payment_gateway.removeprefix("shared:"))
    if razorpay_configured(settings):
        return RazorpayGateway(
            key_id=settings.razorpay_key_id,
            key_secret=settings.razorpay_key_secret,
            webhook_secret=settings.razorpay_webhook_secret,
        )
    return DevSandboxGateway()

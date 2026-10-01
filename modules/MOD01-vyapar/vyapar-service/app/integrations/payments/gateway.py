# [IMP37] Moved here from app/payment_gateway.py (which is now an import shim).
# [TR051] PaymentGateway — the one swap seam every payment call goes through
# (CCR13: a future MOD06 consolidation replaces an adapter, not Commercial).
# Approach: a Protocol with exactly three gateway capabilities TR051 names —
# create a hosted checkout, verify a webhook, issue a refund — plus parsing
# the gateway's event shape. Two adapters:
#  - RazorpayGateway: real REST calls with the standard library (no SDK, no
#    new dependency). Checkout is a Razorpay-hosted Payment Link
#    (POST /v1/payment_links -> short_url, callback_url/callback_method=get),
#    so card/bank details are only ever typed on Razorpay's page (FR51).
#    Webhooks: HMAC-SHA256 hex over the RAW body with the webhook secret,
#    compared in constant time, header X-Razorpay-Signature; dedupe key is
#    the per-event x-razorpay-event-id header (SP051). Refunds:
#    POST /v1/payments/{id}/refund. Placeholder keys => GatewayUnavailable,
#    which is exactly FR51's outage path ("order remains Awaiting Payment").
#  - DevSandboxGateway: DEV STAND-IN, clearly labelled wherever it shows. It
#    emits Razorpay-shaped events signed with the same webhook secret, so the
#    real verify -> parse -> record -> apply chain runs end to end in dev.
#    Its checkout page collects no card data and moves no money.
# Traces to: FR51, TR051, SP051, CCR13
from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from typing import Protocol

from app.config import get_settings


class GatewayUnavailable(Exception):
    """Gateway unreachable or not configured — the order stays saved."""


@dataclass
class CheckoutSession:
    gateway_order_ref: str
    checkout_url: str


@dataclass
class GatewayEvent:
    event_id: str
    type: str
    gateway_order_ref: str | None
    payment_ref: str | None
    outcome: str  # succeeded | failed | refunded


class PaymentGateway(Protocol):
    name: str

    async def create_checkout(self, *, order_id: str, amount_paise: int, description: str, callback_url: str) -> CheckoutSession: ...

    def verify_webhook(self, raw_body: bytes, signature: str) -> bool: ...

    def parse_webhook(self, payload: dict, event_id: str | None) -> GatewayEvent | None: ...

    async def refund(self, payment_ref: str, amount_paise: int) -> str: ...

    async def fetch_outcome(self, gateway_order_ref: str) -> str | None: ...


def _signature_ok(secret: str, raw_body: bytes, signature: str) -> bool:
    if not secret or secret.startswith("CHANGE_ME") and get_settings().payment_gateway == "razorpay":
        return False
    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def parse_razorpay_event(payload: dict, event_id: str | None) -> GatewayEvent | None:
    event_type = payload.get("event") or ""
    body = payload.get("payload") or {}
    link = (body.get("payment_link") or {}).get("entity") or {}
    payment = (body.get("payment") or {}).get("entity") or {}
    refund = (body.get("refund") or {}).get("entity") or {}
    eid = event_id or f"{event_type}:{link.get('id') or payment.get('id') or refund.get('id')}"
    if event_type == "payment_link.paid":
        return GatewayEvent(eid, event_type, link.get("id"), payment.get("id"), "succeeded")
    if event_type in ("payment_link.expired", "payment_link.cancelled"):
        return GatewayEvent(eid, event_type, link.get("id"), None, "failed")
    if event_type == "refund.processed":
        return GatewayEvent(eid, event_type, None, refund.get("payment_id"), "refunded")
    return None  # every other event type is acknowledged and ignored


class RazorpayGateway:
    name = "razorpay"
    base_url = "https://api.razorpay.com/v1"

    def _configured(self) -> bool:
        s = get_settings()
        return not (s.razorpay_key_id.startswith("CHANGE_ME") or s.razorpay_key_secret.startswith("CHANGE_ME"))

    def _request(self, method: str, path: str, body: dict | None = None) -> dict:
        s = get_settings()
        token = base64.b64encode(f"{s.razorpay_key_id}:{s.razorpay_key_secret}".encode()).decode()
        req = urllib.request.Request(
            self.base_url + path, method=method, data=json.dumps(body).encode() if body is not None else None,
            headers={"Authorization": f"Basic {token}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read())
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            raise GatewayUnavailable(str(exc)) from exc

    async def create_checkout(self, *, order_id: str, amount_paise: int, description: str, callback_url: str) -> CheckoutSession:
        if not self._configured():
            raise GatewayUnavailable("payment gateway keys are placeholders")
        data = await asyncio.to_thread(self._request, "POST", "/payment_links", {
            "amount": amount_paise, "currency": "INR", "reference_id": order_id, "description": description[:2048],
            "callback_url": callback_url, "callback_method": "get", "reminder_enable": False,
        })
        return CheckoutSession(gateway_order_ref=data["id"], checkout_url=data["short_url"])

    def verify_webhook(self, raw_body: bytes, signature: str) -> bool:
        return _signature_ok(get_settings().payment_webhook_secret, raw_body, signature)

    def parse_webhook(self, payload: dict, event_id: str | None) -> GatewayEvent | None:
        return parse_razorpay_event(payload, event_id)

    async def refund(self, payment_ref: str, amount_paise: int) -> str:
        if not self._configured():
            raise GatewayUnavailable("payment gateway keys are placeholders")
        data = await asyncio.to_thread(self._request, "POST", f"/payments/{payment_ref}/refund", {"amount": amount_paise})
        return data["id"]

    async def fetch_outcome(self, gateway_order_ref: str) -> str | None:
        """Status-poll fallback (FR51) for a webhook that hasn't arrived."""
        if not self._configured():
            return None
        data = await asyncio.to_thread(self._request, "GET", f"/payment_links/{gateway_order_ref}")
        return {"paid": "succeeded", "expired": "failed", "cancelled": "failed"}.get(data.get("status"))


class DevSandboxGateway:
    """[Dev stand-in] Never used when PAYMENT_GATEWAY=razorpay."""

    name = "dev_sandbox"

    async def create_checkout(self, *, order_id: str, amount_paise: int, description: str, callback_url: str) -> CheckoutSession:
        return CheckoutSession(
            gateway_order_ref=f"plink_sandbox_{order_id}",
            checkout_url=f"{get_settings().web_origin}/payments/checkout/{order_id}",
        )

    def verify_webhook(self, raw_body: bytes, signature: str) -> bool:
        return _signature_ok(get_settings().payment_webhook_secret, raw_body, signature)

    def parse_webhook(self, payload: dict, event_id: str | None) -> GatewayEvent | None:
        return parse_razorpay_event(payload, event_id)

    async def refund(self, payment_ref: str, amount_paise: int) -> str:
        return f"rfnd_sandbox_{uuid.uuid4().hex[:14]}"

    async def fetch_outcome(self, gateway_order_ref: str) -> str | None:
        return None

    def build_signed_event(self, *, event_type: str, gateway_order_ref: str, amount_paise: int) -> tuple[bytes, str, str]:
        """A Razorpay-shaped event, signed exactly as the real gateway signs."""
        payment_id = f"pay_sandbox_{uuid.uuid4().hex[:14]}"
        payload = {
            "event": event_type,
            "payload": {
                "payment_link": {"entity": {"id": gateway_order_ref, "amount": amount_paise, "status": "paid" if event_type.endswith("paid") else "expired"}},
                "payment": {"entity": {"id": payment_id, "amount": amount_paise, "status": "captured"}},
            },
        }
        raw = json.dumps(payload).encode("utf-8")
        signature = hmac.new(get_settings().payment_webhook_secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()
        return raw, signature, f"evt_sandbox_{uuid.uuid4().hex[:16]}"


class SharedLibraryGateway:
    """PAYMENT_GATEWAY=shared:<adapter> — Vyapar's gateway calls mapped onto ForKhatri's
    shared payments library (shared/forkhatri-integrations), the seam every module
    shares so one vendor adapter (or MOD06) serves all of them. Opt-in; the default
    dev_sandbox / razorpay paths above are unchanged."""

    def __init__(self, adapter: str) -> None:
        from forkhatri_integrations import payments

        s = get_settings()
        self._p = payments
        self.gw = payments.get_gateway(
            adapter, allow_sandbox=s.dev_mode,
            webhook_secret=s.payment_webhook_secret, base_url=s.payment_services_url,
            service_name=s.identity_service_name, service_key=s.payment_services_key,
        )
        self.name = f"shared:{self.gw.name}"

    async def create_checkout(self, *, order_id: str, amount_paise: int, description: str, callback_url: str) -> CheckoutSession:
        try:
            charge = await self.gw.create_charge(self._p.ChargeRequest(
                idempotency_key=f"vyapar-order-{order_id}", payer_id="", amount_minor=amount_paise, purpose="vyapar.order",
                description=description, return_url=callback_url, metadata={"order_id": order_id}))
        except self._p.PaymentsError as exc:
            raise GatewayUnavailable(str(exc) or type(exc).__name__) from exc
        return CheckoutSession(gateway_order_ref=charge.reference,
                               checkout_url=charge.checkout_url or f"{get_settings().web_origin}/payments/checkout/{order_id}")

    def verify_webhook(self, raw_body: bytes, signature: str) -> bool:
        try:
            self.gw.parse_event(raw_body, {self._p.SIGNATURE_HEADER: signature})
        except self._p.EventRejected:
            return False
        return True

    def parse_webhook(self, payload: dict, event_id: str | None) -> GatewayEvent | None:
        kind, ref = payload.get("type"), payload.get("reference")
        eid = str(payload.get("event_id") or event_id or f"{kind}:{ref}")
        if kind == "payment.succeeded":
            return GatewayEvent(eid, kind, ref, ref, "succeeded")
        if kind == "payment.failed":
            return GatewayEvent(eid, kind, ref, None, "failed")
        if kind == "refund.succeeded":
            return GatewayEvent(eid, kind, None, payload.get("charge_reference"), "refunded")
        return None

    async def refund(self, payment_ref: str, amount_paise: int) -> str:
        try:
            r = await self.gw.refund(self._p.RefundRequest(charge_reference=payment_ref, amount_minor=amount_paise,
                                                           idempotency_key=f"vyapar-refund-{payment_ref}-{uuid.uuid4().hex[:8]}"))
        except self._p.PaymentsError as exc:
            raise GatewayUnavailable(str(exc) or type(exc).__name__) from exc
        return r.reference

    async def fetch_outcome(self, gateway_order_ref: str) -> str | None:
        status = await self.gw.get_charge_status(gateway_order_ref)
        return {"succeeded": "succeeded", "failed": "failed", "cancelled": "failed"}.get(status or "")


def get_gateway() -> RazorpayGateway | DevSandboxGateway | SharedLibraryGateway:
    name = get_settings().payment_gateway
    if name.startswith("shared:"):
        return SharedLibraryGateway(name.removeprefix("shared:"))
    return RazorpayGateway() if name == "razorpay" else DevSandboxGateway()

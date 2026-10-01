"""The payment adapters that need no outside account.

- `NotConfiguredGateway` ("none"): every call raises PaymentsNotConfigured.
- `SandboxGateway` ("sandbox"): development only. No money moves. References are
  derived from the idempotency key, so a retry returns the same charge. It signs
  its own webhook events with the webhook secret, so a module's real
  verify -> parse -> apply chain runs end to end before any vendor exists.
- `PaymentServicesGateway` ("payment_services"): the HTTP client for the planned
  ForKhatri Payment Services module (MOD06), using the contract below. When
  MOD06 exists, every module switches to it by configuration alone.

Proposed MOD06 contract (first written by Milavn; extended here with status and payouts):
  POST {base}/v1/charges              ChargeRequest fields              -> {reference, status, checkout_url, client_payload}
  GET  {base}/v1/charges/{ref}                                           -> {status}
  POST {base}/v1/charges/{ref}/cancel                                    -> 204
  POST {base}/v1/refunds              {charge_reference, amount_minor, reason, idempotency_key} -> {reference, status}
  POST {base}/v1/payouts              PayoutRequest fields              -> {reference, status}
  Events to the module: POST with X-ForKhatri-Signature = HMAC-SHA256 hex of the raw body and
  X-ForKhatri-Event-Id; body {event_id, type, reference, charge_reference?, amount_minor?}.
  Calls carry X-ForKhatri-Service, X-ForKhatri-Service-Key and Idempotency-Key.
"""

from __future__ import annotations

import asyncio
import json
import urllib.error
import urllib.request
import uuid
from collections.abc import Mapping
from dataclasses import asdict

from .._common import is_placeholder, lower_headers, sign, signature_ok
from .types import (
    Charge,
    ChargeRequest,
    ChargeStatus,
    EventRejected,
    PaymentEvent,
    PaymentsNotConfigured,
    PaymentsUnavailable,
    Payout,
    PayoutRequest,
    Refund,
    RefundRequest,
)

SIGNATURE_HEADER = "X-ForKhatri-Signature"
EVENT_ID_HEADER = "X-ForKhatri-Event-Id"
_EVENT_TYPES = {"payment.succeeded", "payment.failed", "refund.succeeded", "refund.failed", "payout.succeeded", "payout.failed"}


def _read_event(secret: str, raw_body: bytes, headers: Mapping[str, str]) -> PaymentEvent | None:
    h = lower_headers(headers)
    if not signature_ok(secret, raw_body, h.get(SIGNATURE_HEADER.lower())):
        raise EventRejected("bad signature")
    try:
        body = json.loads(raw_body)
    except ValueError as exc:
        raise EventRejected("unreadable body") from exc
    if body.get("type") not in _EVENT_TYPES:
        return None
    return PaymentEvent(
        event_id=str(body.get("event_id") or h.get(EVENT_ID_HEADER.lower()) or sign(secret, raw_body)),
        type=body["type"],
        reference=str(body["reference"]),
        charge_reference=body.get("charge_reference"),
        amount_minor=body.get("amount_minor"),
        raw=body,
    )


class NotConfiguredGateway:
    name = "none"
    configured = False
    live = False

    async def create_charge(self, request: ChargeRequest) -> Charge:
        raise PaymentsNotConfigured

    async def get_charge_status(self, reference: str) -> ChargeStatus | None:
        return None

    def verify_return(self, reference: str, proof: Mapping[str, str]) -> bool:
        return False

    async def cancel_charge(self, reference: str) -> None:
        raise PaymentsNotConfigured

    async def refund(self, request: RefundRequest) -> Refund:
        raise PaymentsNotConfigured

    async def create_payout(self, request: PayoutRequest) -> Payout:
        raise PaymentsNotConfigured

    def parse_event(self, raw_body: bytes, headers: Mapping[str, str]) -> PaymentEvent | None:
        raise EventRejected("payments are not configured")


class SandboxGateway:
    """Development stand-in. The registry refuses it unless the module says it runs locally."""

    name = "sandbox"
    configured = True
    live = False

    def __init__(self, webhook_secret: str = "forkhatri-sandbox", checkout_base_url: str = "") -> None:
        self._secret = webhook_secret
        self._checkout_base = checkout_base_url.rstrip("/")
        self._status: dict[str, ChargeStatus] = {}

    @staticmethod
    def _ref(prefix: str, key: str) -> str:
        return f"{prefix}_{uuid.uuid5(uuid.NAMESPACE_URL, key).hex[:20]}"

    async def create_charge(self, request: ChargeRequest) -> Charge:
        ref = self._ref("sbx_ch", request.idempotency_key)
        self._status.setdefault(ref, "pending")
        url = f"{self._checkout_base}?ref={ref}" if self._checkout_base else None
        return Charge(reference=ref, status=self._status[ref], checkout_url=url, client_payload={"mode": "sandbox"})

    async def get_charge_status(self, reference: str) -> ChargeStatus | None:
        return self._status.get(reference)

    def return_proof(self, reference: str, succeeded: bool = True) -> dict[str, str]:
        """What a sandbox checkout page hands back to the module after "Pay" or "Fail"."""
        result = "success" if succeeded else "failed"
        return {"result": result, "signature": sign(self._secret, f"{reference}|{result}".encode())}

    def verify_return(self, reference: str, proof: Mapping[str, str]) -> bool:
        result = proof.get("result", "")
        ok = result == "success" and signature_ok(self._secret, f"{reference}|{result}".encode(), proof.get("signature"))
        if ok:
            self._status[reference] = "succeeded"
        return ok

    async def cancel_charge(self, reference: str) -> None:
        if self._status.get(reference) == "pending":
            self._status[reference] = "cancelled"

    async def refund(self, request: RefundRequest) -> Refund:
        return Refund(reference=self._ref("sbx_rf", request.idempotency_key), settled=True)

    async def create_payout(self, request: PayoutRequest) -> Payout:
        return Payout(reference=self._ref("sbx_po", request.idempotency_key), settled=True)

    def signed_event(self, type: str, reference: str, *, charge_reference: str | None = None, amount_minor: int | None = None) -> tuple[bytes, dict[str, str]]:
        """A webhook exactly as the sandbox would send it: feed it to the module's webhook route."""
        event_id = f"evt_sbx_{uuid.uuid4().hex[:16]}"
        body = json.dumps({"event_id": event_id, "type": type, "reference": reference,
                           "charge_reference": charge_reference, "amount_minor": amount_minor}).encode()
        if type == "payment.succeeded":
            self._status[reference] = "succeeded"
        elif type == "payment.failed":
            self._status[reference] = "failed"
        return body, {SIGNATURE_HEADER: sign(self._secret, body), EVENT_ID_HEADER: event_id}

    def parse_event(self, raw_body: bytes, headers: Mapping[str, str]) -> PaymentEvent | None:
        return _read_event(self._secret, raw_body, headers)


class PaymentServicesGateway:
    """HTTP client for ForKhatri Payment Services (MOD06). Standard library only."""

    name = "payment_services"
    live = True

    def __init__(self, base_url: str, service_name: str, service_key: str, webhook_secret: str, timeout_seconds: float = 8.0) -> None:
        self._base = (base_url or "").rstrip("/")
        self._headers = {"X-ForKhatri-Service": service_name, "X-ForKhatri-Service-Key": service_key, "Content-Type": "application/json"}
        self._secret = webhook_secret
        self._timeout = timeout_seconds
        self.configured = bool(self._base) and not is_placeholder(service_key)

    def _call(self, method: str, path: str, body: dict | None, idempotency_key: str | None) -> dict:
        headers = dict(self._headers)
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        req = urllib.request.Request(self._base + path, method=method, headers=headers,
                                     data=json.dumps(body).encode() if body is not None else None)
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                raw = resp.read()
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise PaymentsUnavailable(f"{method} {path}: {exc}") from exc
        return json.loads(raw) if raw else {}

    async def _request(self, method: str, path: str, body: dict | None = None, idempotency_key: str | None = None) -> dict:
        if not self.configured:
            raise PaymentsNotConfigured
        return await asyncio.to_thread(self._call, method, path, body, idempotency_key)

    async def create_charge(self, request: ChargeRequest) -> Charge:
        body = asdict(request)
        body["metadata"] = dict(request.metadata)
        data = await self._request("POST", "/v1/charges", body, request.idempotency_key)
        return Charge(reference=str(data["reference"]), status=data.get("status", "pending"),
                      checkout_url=data.get("checkout_url"), client_payload=data.get("client_payload") or {})

    async def get_charge_status(self, reference: str) -> ChargeStatus | None:
        return (await self._request("GET", f"/v1/charges/{reference}")).get("status")

    def verify_return(self, reference: str, proof: Mapping[str, str]) -> bool:
        # MOD06 confirms by event; a browser return is never trusted on its own.
        return False

    async def cancel_charge(self, reference: str) -> None:
        await self._request("POST", f"/v1/charges/{reference}/cancel", {})

    async def refund(self, request: RefundRequest) -> Refund:
        data = await self._request("POST", "/v1/refunds", asdict(request), request.idempotency_key)
        return Refund(reference=str(data["reference"]), settled=data.get("status") == "succeeded")

    async def create_payout(self, request: PayoutRequest) -> Payout:
        body = asdict(request)
        body["destination"] = dict(request.destination)
        data = await self._request("POST", "/v1/payouts", body, request.idempotency_key)
        return Payout(reference=str(data["reference"]), settled=data.get("status") == "succeeded")

    def parse_event(self, raw_body: bytes, headers: Mapping[str, str]) -> PaymentEvent | None:
        return _read_event(self._secret, raw_body, headers)

"""Money. Explicit amounts (gross, platform fee, processing fee, tax, payable,
refund) — never `price - 2%` as the whole model. The platform fee percent and
the cancellation policy are platform settings (data), read per booking and
snapshotted onto it.

PaymentProvider is the integration boundary. `MockPaymentProvider` succeeds
locally with no money moving (PAYMENT_PROVIDER=mock, the default). Any other
PAYMENT_PROVIDER goes through `SharedPaymentProvider`, which wraps ForKhatri's
shared payments library (shared/forkhatri-integrations): the same gateway,
sandbox and future MOD06 client every module uses. The rest of Counsel does
not change."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from app.settings import get_settings


async def setting(conn, key: str, default=None):
    v = await conn.fetchval("SELECT value FROM platform_setting WHERE key = $1", key)
    return default if v is None else v


@dataclass(frozen=True)
class Quote:
    gross_minor: int
    platform_fee_minor: int
    processing_fee_minor: int
    tax_minor: int
    provider_payable_minor: int
    currency: str
    platform_fee_percent: float

    def as_dict(self) -> dict:
        return self.__dict__.copy()


async def quote(conn, price_minor: int, currency: str) -> Quote:
    pct = float(await setting(conn, "platform_fee_percent", 2))
    fee = round(price_minor * pct / 100)
    processing = 0  # the gateway adapter reports its own fee once one is connected
    tax = 0         # tax treatment is represented separately, configured per deployment
    return Quote(price_minor, fee, processing, tax, price_minor - fee - processing - tax, currency, pct)


async def cancellation_policy(conn) -> dict:
    return await setting(conn, "cancellation_policy", {})


def refund_percent_for_seeker_cancel(policy: dict, starts_at: datetime, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    hours = (starts_at - now).total_seconds() / 3600
    tiers = sorted(policy.get("seeker", []), key=lambda t: -t["min_hours_before"])
    for tier in tiers:
        if hours >= tier["min_hours_before"]:
            return int(tier["refund_percent"])
    return 0


# --- Payment provider boundary ---------------------------------------------------

@dataclass
class PaymentIntent:
    external_ref: str
    status: str            # created | succeeded | failed
    checkout: dict         # what the client needs to complete (mock: nothing)


class PaymentProvider:
    name = "abstract"

    async def create_payment(self, booking_id: UUID, amount_minor: int, currency: str) -> PaymentIntent: ...
    async def verify_payment(self, external_ref: str, proof: dict) -> bool: ...
    async def refund(self, external_ref: str, amount_minor: int) -> str: ...
    async def create_payout(self, provider_id: UUID, amount_minor: int, currency: str) -> str: ...


class MockPaymentProvider(PaymentProvider):
    """Development only: every payment succeeds when the client confirms, no
    money moves. Refused outside localhost by settings validation in main."""

    name = "mock"

    async def create_payment(self, booking_id, amount_minor, currency):
        return PaymentIntent(external_ref=f"mock_{secrets.token_hex(8)}", status="created", checkout={"mode": "mock"})

    async def verify_payment(self, external_ref, proof):
        return proof.get("mock_result", "success") == "success"

    async def refund(self, external_ref, amount_minor):
        return f"mockrf_{secrets.token_hex(6)}"

    async def create_payout(self, provider_id, amount_minor, currency):
        return f"mockpo_{secrets.token_hex(6)}"


class SharedPaymentProvider(PaymentProvider):
    """Counsel's four calls mapped onto the shared ForKhatri payments library."""

    def __init__(self, gateway) -> None:
        self.gw = gateway
        self.name = gateway.name

    async def create_payment(self, booking_id, amount_minor, currency):
        from forkhatri_integrations import payments

        charge = await self.gw.create_charge(payments.ChargeRequest(
            idempotency_key=f"counsel-charge-{booking_id}", payer_id="", amount_minor=amount_minor, currency=currency,
            purpose="counsel.consultation", description="Counsel consultation", metadata={"counsel_ref": str(booking_id)}))
        return PaymentIntent(external_ref=charge.reference, status="created",
                             checkout={"mode": self.gw.name, "checkout_url": charge.checkout_url, **dict(charge.client_payload)})

    async def verify_payment(self, external_ref, proof):
        # A provider event (webhook) or a status check is the source of truth; a signed browser return is the fast path.
        if await self.gw.get_charge_status(external_ref) == "succeeded":
            return True
        if self.gw.name == "sandbox" and proof.get("mock_result", "success") == "success":
            proof = self.gw.return_proof(external_ref)   # the sandbox checkout's own "Pay" button
        return self.gw.verify_return(external_ref, {k: str(v) for k, v in proof.items()})

    async def refund(self, external_ref, amount_minor):
        from forkhatri_integrations import payments

        r = await self.gw.refund(payments.RefundRequest(charge_reference=external_ref, amount_minor=amount_minor,
                                                        idempotency_key=f"counsel-refund-{external_ref}-{secrets.token_hex(4)}"))
        return r.reference

    async def create_payout(self, provider_id, amount_minor, currency):
        from forkhatri_integrations import payments

        p = await self.gw.create_payout(payments.PayoutRequest(idempotency_key=f"counsel-payout-{provider_id}-{secrets.token_hex(6)}",
                                                               payee_id=str(provider_id), amount_minor=amount_minor, currency=currency))
        return p.reference


def running_locally() -> bool:
    return get_settings().api_host in ("127.0.0.1", "localhost")


def shared_gateway():
    """The shared-library gateway named by PAYMENT_PROVIDER (none when mock is chosen)."""
    from forkhatri_integrations import payments

    s = get_settings()
    return payments.get_gateway(
        s.payment_provider.removeprefix("shared:") if s.payment_provider != "mock" else "none", allow_sandbox=running_locally(),
        webhook_secret=s.payments_webhook_secret, base_url=s.payment_services_url,
        service_name=s.platform_service_name, service_key=s.payment_services_key)


def provider() -> PaymentProvider:
    if get_settings().payment_provider == "mock":
        return MockPaymentProvider()
    gw = shared_gateway()
    if not gw.configured:
        raise RuntimeError(f"payment provider {get_settings().payment_provider!r} is not connected; set PAYMENT_PROVIDER=mock for local development")
    return SharedPaymentProvider(gw)


async def ledger(conn, booking_id: UUID, kind: str, amount_minor: int, currency: str, note: str | None = None) -> None:
    await conn.execute(
        "INSERT INTO ledger_entry (booking_id, kind, amount_minor, currency, note) VALUES ($1,$2,$3,$4,$5)",
        booking_id, kind, amount_minor, currency, note,
    )

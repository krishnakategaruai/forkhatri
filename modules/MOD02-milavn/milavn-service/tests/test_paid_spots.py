"""FR102 — paid spots: the rules a member reads before paying, the provider boundary, and FR036 isolation.

No database: these are the pure decisions every flow relies on.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from app.components.payments import interface as payments
from app.components.ticketing import interface as ticketing
from app.config.settings import Settings

START = datetime(2026, 9, 20, 7, 0, tzinfo=UTC)


def test_full_refund_up_to_the_cutoff_and_none_after() -> None:
    kw = {"amount_paise": 25_000, "time_start": START, "cutoff_hours": 24}
    assert ticketing.refund_for_withdrawal(**kw, now=START - timedelta(hours=30)) == 25_000
    assert ticketing.refund_for_withdrawal(**kw, now=START - timedelta(hours=24)) == 25_000
    assert ticketing.refund_for_withdrawal(**kw, now=START - timedelta(hours=23, minutes=59)) == 0


def test_cutoff_zero_means_refundable_until_the_start() -> None:
    kw = {"amount_paise": 10_000, "time_start": START, "cutoff_hours": 0}
    assert ticketing.refund_for_withdrawal(**kw, now=START - timedelta(minutes=1)) == 10_000
    assert ticketing.refund_for_withdrawal(**kw, now=START + timedelta(minutes=1)) == 0


def test_waitlist_offer_window() -> None:
    now = START - timedelta(days=3)
    assert ticketing.offer_hold_until(time_start=START, now=now) == now + timedelta(hours=12)
    now = START - timedelta(hours=5)
    assert ticketing.offer_hold_until(time_start=START, now=now) == START - timedelta(hours=1)
    now = START - timedelta(minutes=40)
    assert ticketing.offer_hold_until(time_start=START, now=now) == now + timedelta(minutes=30)


def _settings(**over: object) -> Settings:
    base = {"api_host": "127.0.0.1", "web_base_url": "http://localhost:3001", "payments_provider": "none", "payment_services_webhook_key": "CHANGE_ME"}
    return Settings(**{**base, **over})


def test_payments_are_off_by_default() -> None:
    provider = payments.get_payment_services(_settings())
    assert provider.configured is False
    try:
        asyncio.run(provider.refund(charge_reference="x", amount_paise=100, reason="member_withdrew", idempotency_key="k"))
    except payments.PaymentsNotConfigured:
        pass
    else:
        raise AssertionError("an unconfigured provider must refuse")


def test_sandbox_only_on_localhost() -> None:
    assert payments.get_payment_services(_settings(payments_provider="sandbox")).name == "sandbox"
    assert payments.get_payment_services(_settings(payments_provider="sandbox", web_base_url="https://milavn.forkhatri.in")).configured is False
    assert payments.get_payment_services(_settings(payments_provider="sandbox", api_host="0.0.0.0")).configured is False


def test_sandbox_charge_is_idempotent_per_key() -> None:
    provider = payments.SandboxPaymentServices("http://localhost:3001")
    member = uuid4()
    a = asyncio.run(provider.create_charge(idempotency_key="milavn-ticket-1", payer_member_id=member, amount_paise=100, description="x", return_url="r", metadata={}))
    b = asyncio.run(provider.create_charge(idempotency_key="milavn-ticket-1", payer_member_id=member, amount_paise=100, description="x", return_url="r", metadata={}))
    c = asyncio.run(provider.create_charge(idempotency_key="milavn-ticket-2", payer_member_id=member, amount_paise=100, description="x", return_url="r", metadata={}))
    assert a.reference == b.reference != c.reference
    assert a.checkout_url == f"http://localhost:3001/pay/sandbox?ref={a.reference}"


def test_http_adapter_is_not_configured_with_a_placeholder_key() -> None:
    assert payments.get_payment_services(_settings(payments_provider="payment_services")).configured is False
    assert payments.get_payment_services(_settings(payments_provider="payment_services", payment_services_key="real-key")).configured is True


def test_payment_events_need_the_shared_key() -> None:
    placeholder = _settings()
    assert payments.verify_event_caller(placeholder, "payments", "CHANGE_ME") is False
    real = _settings(payment_services_webhook_key="s3cret-key")
    assert payments.verify_event_caller(real, "payments", "s3cret-key") is True
    assert payments.verify_event_caller(real, "payments", "wrong") is False
    assert payments.verify_event_caller(real, "someone-else", "s3cret-key") is False
    assert payments.verify_event_caller(real, "payments", None) is False


def test_trust_and_ranking_never_read_payment_data() -> None:
    """[FR036] Reputation and discovery ranking must not take money as an input."""
    app = Path(__file__).resolve().parents[1] / "app" / "components"
    for component in ("trust", "discovery"):
        for source in (app / component).rglob("*.py"):
            code = source.read_text(encoding="utf-8")
            assert "ticketing" not in code and "components.payments" not in code, f"{source} reads payment data"

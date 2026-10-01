"""Run: python -m unittest discover -s shared/forkhatri-integrations/tests"""

from __future__ import annotations

import asyncio
import json
import unittest
from datetime import datetime

from forkhatri_integrations import delivery, messaging, payments


class PaymentsTest(unittest.IsolatedAsyncioTestCase):
    async def test_sandbox_refused_unless_local(self):
        self.assertEqual(payments.get_gateway("sandbox").name, "none")
        self.assertEqual(payments.get_gateway("sandbox", allow_sandbox=True).name, "sandbox")
        self.assertEqual(payments.get_gateway("no-such-vendor", allow_sandbox=True).name, "none")

    async def test_not_configured_never_pretends(self):
        gw = payments.get_gateway("none")
        with self.assertRaises(payments.PaymentsNotConfigured):
            await gw.create_charge(payments.ChargeRequest(idempotency_key="k", payer_id="m", amount_minor=100))

    async def test_sandbox_charge_return_refund_payout(self):
        gw = payments.get_gateway("sandbox", allow_sandbox=True, webhook_secret="s1")
        req = payments.ChargeRequest(idempotency_key="order-1", payer_id="m1", amount_minor=120000, purpose="test")
        c1, c2 = await gw.create_charge(req), await gw.create_charge(req)
        self.assertEqual(c1.reference, c2.reference)  # idempotent
        self.assertEqual(await gw.get_charge_status(c1.reference), "pending")
        self.assertFalse(gw.verify_return(c1.reference, {"result": "success", "signature": "forged"}))
        self.assertTrue(gw.verify_return(c1.reference, gw.return_proof(c1.reference)))
        self.assertEqual(await gw.get_charge_status(c1.reference), "succeeded")
        rf = await gw.refund(payments.RefundRequest(charge_reference=c1.reference, amount_minor=500, idempotency_key="rf-1"))
        self.assertTrue(rf.settled)
        po = await gw.create_payout(payments.PayoutRequest(idempotency_key="po-1", payee_id="p1", amount_minor=9000))
        self.assertTrue(po.reference.startswith("sbx_po_"))

    async def test_sandbox_events_signed(self):
        gw = payments.get_gateway("sandbox", allow_sandbox=True, webhook_secret="s2")
        body, headers = gw.signed_event("payment.succeeded", "sbx_ch_x", amount_minor=100)
        ev = gw.parse_event(body, headers)
        self.assertEqual((ev.type, ev.reference), ("payment.succeeded", "sbx_ch_x"))
        with self.assertRaises(payments.EventRejected):
            gw.parse_event(body.replace(b"100", b"999"), headers)
        ignored, h2 = gw.signed_event("something.else", "r")
        self.assertIsNone(gw.parse_event(ignored, h2))

    async def test_payment_services_needs_real_key(self):
        gw = payments.get_gateway("payment_services", base_url="http://127.0.0.1:9", service_name="x", service_key="CHANGE_ME")
        self.assertFalse(gw.configured)
        with self.assertRaises(payments.PaymentsNotConfigured):
            await gw.cancel_charge("r")
        gw2 = payments.get_gateway("payment_services", base_url="http://127.0.0.1:9", service_name="x", service_key="real-key-123")
        with self.assertRaises(payments.PaymentsUnavailable):  # nothing listens on port 9
            await gw2.cancel_charge("r")

    async def test_register_vendor(self):
        class Fake(payments.SandboxGateway):
            name = "fakepay"
        payments.register_gateway("fakepay", lambda **o: Fake(o.get("webhook_secret", "x")))
        self.assertEqual(payments.get_gateway("fakepay").name, "fakepay")


class MessagingTest(unittest.IsolatedAsyncioTestCase):
    async def test_console_only_locally(self):
        self.assertEqual(messaging.get_sender("sms", "console").name, "disabled")
        s = messaging.get_sender("sms", "console", allow_console=True)
        r = await s.send(messaging.OutboundMessage(channel="sms", to="+919800000001", body="hi", idempotency_key="k"))
        self.assertTrue(r.ok)

    async def test_disabled(self):
        s = messaging.get_sender("whatsapp", "disabled")
        self.assertFalse(s.available)
        r = await s.send(messaging.OutboundMessage(channel="whatsapp", to="+91", body="x", idempotency_key="k"))
        self.assertFalse(r.ok)

    def test_render(self):
        t = {"booking.new": {"en": "New booking: {title}", "hi": "नई बुकिंग: {title}"}}
        self.assertEqual(messaging.render(t, "booking.new", "hi", {"title": "GST"}), "नई बुकिंग: GST")
        self.assertEqual(messaging.render(t, "booking.new", "te", {"title": "GST"}), "New booking: GST")


class MemoryStore:
    def __init__(self, items):
        self.items = {i.id: i for i in items}
        self.log = []

    async def claim(self, limit):
        return list(self.items.values())[:limit]

    async def resolve(self, item):
        if item.payload.get("to") is None:
            return None
        return messaging.OutboundMessage(channel=item.channel, to=item.payload["to"], body="x", idempotency_key=str(item.id))

    async def mark_sent(self, item, result):
        self.log.append((item.id, "sent")); self.items.pop(item.id)

    async def mark_failed(self, item, error, retry_at):
        self.log.append((item.id, "retry" if isinstance(retry_at, datetime) else "failed")); self.items.pop(item.id)

    async def mark_skipped(self, item, reason):
        self.log.append((item.id, "skipped")); self.items.pop(item.id)


class Flaky:
    name, channel, available, live = "flaky", "sms", True, False

    async def send(self, message):
        return messaging.SendResult(ok=False, provider="flaky", error="timeout", retryable=True)


class DeliveryTest(unittest.IsolatedAsyncioTestCase):
    async def test_dispatch(self):
        store = MemoryStore([
            delivery.OutboxItem(1, "email", "m", "k", {"to": "a@b.in"}),
            delivery.OutboxItem(2, "email", "m", "k", {}),
            delivery.OutboxItem(3, "sms", "m", "k", {"to": "+91"}),
            delivery.OutboxItem(4, "sms", "m", "k", {"to": "+91"}, attempts=5),
            delivery.OutboxItem(5, "push", "m", "k", {"to": "t"}),
        ])
        senders = {"email": messaging.get_sender("email", "console", allow_console=True), "sms": Flaky(),
                   "push": messaging.get_sender("push", "disabled")}
        stats = await delivery.Dispatcher(store, senders).run_once()
        self.assertEqual(dict(store.log), {1: "sent", 2: "skipped", 3: "retry", 4: "failed", 5: "skipped"})
        self.assertEqual((stats.sent, stats.retrying, stats.failed, stats.skipped), (1, 1, 1, 2))

    def test_backoff(self):
        self.assertEqual(delivery.backoff(1).total_seconds(), 30)
        self.assertEqual(delivery.backoff(3).total_seconds(), 120)
        self.assertEqual(delivery.backoff(20).total_seconds(), 3600)


if __name__ == "__main__":
    unittest.main()

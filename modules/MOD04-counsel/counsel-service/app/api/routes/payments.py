"""Payment events from the provider behind the shared ForKhatri payments library
(a vendor webhook, or MOD06 Payment Services). Verified by signature, then the
same confirm path as the in-app "Pay" is used, so a paid booking or purchase is
confirmed even when the payer closes the checkout before returning."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request

from app import db
from app.components import bookings, money, purchases
from app.errors import DomainError

router = APIRouter(tags=["payments"])
log = logging.getLogger("counsel.payments")


@router.post("/payments/events")
async def payment_event(request: Request):
    from forkhatri_integrations import payments

    gw = money.shared_gateway()
    try:
        ev = gw.parse_event(await request.body(), dict(request.headers))
    except payments.EventRejected:
        raise DomainError("bad_event", "Event rejected.", 400) from None
    if ev is None or ev.type != "payment.succeeded":
        return {"ok": True, "applied": False}
    async with db.tx() as conn:
        p = await conn.fetchrow("SELECT b.id, b.seeker_id FROM payment p JOIN booking b ON b.id = p.booking_id WHERE p.external_ref=$1", ev.reference)
        if p:
            await bookings.confirm_payment(conn, booking_id=p["id"], actor_id=p["seeker_id"], proof={})
            return {"ok": True, "applied": True}
        pu = await conn.fetchrow("SELECT id, buyer_id, status FROM purchase WHERE external_ref=$1", ev.reference)
        if pu and pu["status"] == "pending_payment":
            await purchases.pay(conn, purchase_id=pu["id"], actor_id=pu["buyer_id"], proof={})
            return {"ok": True, "applied": True}
    log.info("payment event %s for unknown reference", ev.event_id)
    return {"ok": True, "applied": False}

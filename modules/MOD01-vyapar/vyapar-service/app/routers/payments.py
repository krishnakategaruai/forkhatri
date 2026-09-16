# [TR051] Payment Bridge: idempotent orders, verified webhooks, isolated
# adapter (FR51).
# Approach:
#  - `create_payment_order()` / `refund_payment_order()` are the ONLY entry
#    points Commercial uses; Commercial never touches `payment_gateway.py`.
#    Every order has a UNIQUE idempotency key (a retried create with the same
#    key returns the original row). Only references, amount, tax, currency
#    and state are stored — no column can hold card or bank data.
#  - POST /v1/payments/webhook reads the RAW body and verifies the signature
#    BEFORE parsing or writing anything; a bad signature is rejected and
#    logged. It has no member session (the gateway calls it), so it runs in
#    its own transaction with `vyapar.service_role='payment_webhook'` and
#    records the event through migration 006's `record_gateway_event()`
#    (dedupe on the gateway's event id, out-of-order reconciliation). The
#    promotion itself is moved by Commercial's own `apply_payment_result()`,
#    never by this handler (TR030).
#  - Status-poll fallback: reading an order that's still pending asks the
#    gateway directly (FR51 "signed webhook ... and a status poll fallback").
#  - Dev sandbox: POST /v1/payments/orders/{id}/simulate builds a signed,
#    Razorpay-shaped event and pushes it through the exact same
#    `process_webhook()` path — available only with DEV_MODE and the sandbox
#    gateway selected.
# Traces to: FR51, FR30, FR31, TR051, SP051
from __future__ import annotations

import json
import logging
import uuid
from typing import Literal

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import get_settings
from app.db import get_conn, get_pool
from app.deps import Locale
from app.i18n import translate
from app.identity import AuthzContext, resolve_authz_context
from app.notifications import notify_member
from app.payment_gateway import DevSandboxGateway, GatewayEvent, GatewayUnavailable, get_gateway

router = APIRouter(prefix="/v1/payments", tags=["payments"])
logger = logging.getLogger(__name__)

__all__ = ["GatewayUnavailable", "create_payment_order", "refund_payment_order", "process_webhook"]


async def create_payment_order(
    conn: asyncpg.Connection,
    *,
    kind: str,
    ref_id,
    member_id: str,
    amount_paise: int,
    tax_paise: int,
    description: str,
    return_path: str,
    idempotency_key: str | None = None,
) -> dict:
    """Creates the order row, then the hosted checkout. Raises
    GatewayUnavailable AFTER the row is saved, so a retry can reuse it."""
    gateway = get_gateway()
    key = idempotency_key or f"{kind}:{ref_id}:{uuid.uuid4().hex}"
    row = await conn.fetchrow(
        """INSERT INTO vyapar_payments.payment_orders (kind, ref_id, member_id, amount_paise, tax_paise, gateway, idempotency_key)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (idempotency_key) DO NOTHING RETURNING *""",
        kind, ref_id, member_id, amount_paise, tax_paise, gateway.name, key,
    )
    if row is None:
        row = await conn.fetchrow("SELECT * FROM vyapar_payments.payment_orders WHERE idempotency_key = $1", key)
    session = await gateway.create_checkout(
        order_id=str(row["id"]), amount_paise=amount_paise + tax_paise, description=description,
        callback_url=f"{get_settings().web_origin}{return_path}?order={row['id']}",
    )
    await conn.execute(
        "UPDATE vyapar_payments.payment_orders SET gateway_order_ref = $2, updated_at = now() WHERE id = $1",
        row["id"], session.gateway_order_ref,
    )
    return {"id": str(row["id"]), "checkout_url": session.checkout_url}


async def refund_payment_order(conn: asyncpg.Connection, order: asyncpg.Record, amount_paise: int) -> str | None:
    """Refund through the same gateway with the original payment reference.
    Returns the refund reference, or None if the gateway couldn't do it (the
    caller leaves the order visible for the FR49 queue)."""
    if not order["gateway_payment_ref"] or amount_paise <= 0:
        return None
    try:
        refund_ref = await get_gateway().refund(order["gateway_payment_ref"], amount_paise)
    except GatewayUnavailable:
        logger.warning("refund failed for payment order %s", order["id"])
        return None
    await conn.execute(
        """UPDATE vyapar_payments.payment_orders
           SET state = 'refunded', refund_paise = refund_paise + $2, refund_ref = $3, updated_at = now() WHERE id = $1""",
        order["id"], amount_paise, refund_ref,
    )
    return refund_ref


async def _apply_event(conn: asyncpg.Connection, event: GatewayEvent) -> dict:
    rows = await conn.fetch(
        "SELECT * FROM vyapar_payments.record_gateway_event($1, $2, $3, $4, $5)",
        event.gateway_order_ref, event.payment_ref, event.event_id, event.type, event.outcome,
    )
    if not rows:
        return {"matched": False}
    order = rows[0]
    if not order["applied"]:
        return {"matched": True, "applied": False, "state": order["state"]}
    outcomes = [event.outcome]
    if event.outcome == "succeeded" and order["state"] == "refunded":
        outcomes.append("refunded")  # an earlier-stored refund just reconciled
    for outcome in outcomes:
        results = await conn.fetch(
            "SELECT * FROM vyapar_commercial.apply_payment_result($1, $2, $3, $4)",
            order["kind"], order["ref_id"], order["order_id"], outcome,
        )
        for res in results:
            link = f"/promotions/{order['ref_id']}"
            if res["to_state"] == "active":
                await notify_member(
                    conn, member_id=res["owner_id"], template="promotionActive", link=link,
                    idempotency_key=f"promotion_active:{order['ref_id']}",
                    params={"date": res["ends_at"].date().isoformat() if res["ends_at"] else ""},
                )
            elif outcome == "failed":
                await notify_member(
                    conn, member_id=res["owner_id"], template="paymentFailed", link=link,
                    idempotency_key=f"payment_failed:{order['order_id']}",
                )
    return {"matched": True, "applied": True, "state": order["state"]}


async def process_webhook(raw_body: bytes, signature: str | None, event_id: str | None) -> tuple[int, dict]:
    gateway = get_gateway()
    if not signature or not gateway.verify_webhook(raw_body, signature):
        logger.warning("payment webhook rejected: signature missing or invalid")
        return 400, {"error": "invalid_signature"}
    try:
        payload = json.loads(raw_body)
    except ValueError:
        return 400, {"error": "invalid_body"}
    event = gateway.parse_webhook(payload, event_id)
    if event is None:
        return 200, {"ignored": True}
    settings = get_settings()
    async with get_pool().acquire() as conn:
        async with conn.transaction():
            await conn.execute("SELECT set_config('vyapar.service_role', 'payment_webhook', true)")
            # notifications + owner language reads need an operator context
            await conn.execute("SELECT set_config('vyapar.authz_context', $1, true)", settings.dispatcher_operator_member_id)
            result = await _apply_event(conn, event)
    return 200, result


@router.post("/webhook")
async def payment_webhook(request: Request) -> JSONResponse:
    raw_body = await request.body()  # raw bytes — the signature is over these, not re-serialised JSON
    status, result = await process_webhook(
        raw_body, request.headers.get("X-Razorpay-Signature"), request.headers.get("x-razorpay-event-id")
    )
    return JSONResponse(status_code=status, content=result)


@router.get("/orders/{order_id}")
async def get_payment_order(
    order_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    try:
        row = await conn.fetchrow("SELECT * FROM vyapar_payments.payment_orders WHERE id = $1 AND member_id = $2", order_id, ctx.member_id)
    except asyncpg.DataError:
        row = None
    if row is None:
        raise HTTPException(status_code=404, detail=translate("commercial.error.orderNotFound", lang))
    state = row["state"]
    if state == "pending" and row["gateway_order_ref"]:
        try:
            outcome = await get_gateway().fetch_outcome(row["gateway_order_ref"])
        except GatewayUnavailable:
            outcome = None
        if outcome:
            async with get_pool().acquire() as sys_conn:
                async with sys_conn.transaction():
                    await sys_conn.execute("SELECT set_config('vyapar.service_role', 'payment_webhook', true)")
                    await sys_conn.execute("SELECT set_config('vyapar.authz_context', $1, true)", get_settings().dispatcher_operator_member_id)
                    applied = await _apply_event(sys_conn, GatewayEvent(
                        f"poll:{row['gateway_order_ref']}:{outcome}", "status_poll", row["gateway_order_ref"], None, outcome))
            state = applied.get("state", state)
    return {
        "id": str(row["id"]), "kind": row["kind"], "ref_id": str(row["ref_id"]), "amount_paise": row["amount_paise"],
        "tax_paise": row["tax_paise"], "state": state, "gateway": row["gateway"],
        "sandbox": row["gateway"] == "dev_sandbox",
    }


class SimulateIn(BaseModel):
    outcome: Literal["succeeded", "failed"]


@router.post("/orders/{order_id}/simulate")
async def simulate_sandbox_payment(
    order_id: str,
    body: SimulateIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    settings = get_settings()
    if not settings.dev_mode or settings.payment_gateway != "dev_sandbox":
        raise HTTPException(status_code=404, detail=translate("commercial.error.orderNotFound", lang))
    try:
        row = await conn.fetchrow("SELECT * FROM vyapar_payments.payment_orders WHERE id = $1 AND member_id = $2", order_id, ctx.member_id)
    except asyncpg.DataError:
        row = None
    if row is None or not row["gateway_order_ref"]:
        raise HTTPException(status_code=404, detail=translate("commercial.error.orderNotFound", lang))
    raw, signature, event_id = DevSandboxGateway().build_signed_event(
        event_type="payment_link.paid" if body.outcome == "succeeded" else "payment_link.expired",
        gateway_order_ref=row["gateway_order_ref"], amount_paise=row["amount_paise"] + row["tax_paise"],
    )
    status, result = await process_webhook(raw, signature, event_id)
    return {"status": status, "result": result, "redirect": f"/promotions/{row['ref_id']}?result={body.outcome}"}

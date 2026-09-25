# [TR051] Payment Bridge — HTTP front door only. Orders, refunds, webhook
# verification and reconciliation live in app/services/payments.py. The
# webhook route stays here because it must read the raw request body.
# Traces to: FR51, FR30, FR31, TR051, SP051
from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from app.db import get_conn
from app.deps import Locale
from app.errors import ERROR_RESPONSES
from app.identity import AuthzContext, resolve_authz_context
from app.services import payments as svc
from app.services.payments import (  # noqa: F401  schemas used below; background passes re-exported for main.py
    PaymentOrderOut,
    PaymentWebhookAck,
    SimulatedPaymentOut,
    SimulateIn,
)

router = APIRouter(prefix="/v1/payments", tags=["payments"], responses=ERROR_RESPONSES)


@router.post("/webhook", response_model=None, responses={200: {"model": PaymentWebhookAck}, 400: {"model": PaymentWebhookAck}}, operation_id="receivePaymentWebhook", summary="Receive a payment gateway webhook")
async def payment_webhook(request: Request) -> JSONResponse:
    raw_body = await request.body()  # raw bytes — the signature is over these, not re-serialised JSON
    status, result = await svc.process_webhook(
        raw_body, request.headers.get("X-Razorpay-Signature"), request.headers.get("x-razorpay-event-id")
    )
    return JSONResponse(status_code=status, content=result)


@router.get("/orders/{order_id}", response_model=PaymentOrderOut, operation_id="getPaymentOrder", summary="Get one payment order")
async def get_payment_order(
    order_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> PaymentOrderOut:
    return await svc.get_payment_order(conn, ctx, lang, order_id=order_id)


@router.post("/orders/{order_id}/simulate", response_model=SimulatedPaymentOut, operation_id="simulatePaymentOrder", summary="Simulate a sandbox payment for an order")
async def simulate_sandbox_payment(
    order_id: str,
    body: SimulateIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> SimulatedPaymentOut:
    return await svc.simulate_payment_order(conn, ctx, lang, order_id=order_id, body=body)

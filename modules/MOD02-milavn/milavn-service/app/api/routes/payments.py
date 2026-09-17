"""Paid spots endpoints (FR102): join by paying, withdraw with the stated refund rule, organizer totals,
the member's payment history, the Payment Services event receiver, and the development sandbox checkout.

Money never moves here; see `components/payments/interface.py` for the provider boundary.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Header, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.api.deps import AppSettings, CurrentMember, DbSession, IdempotencyKeyHeader, Locale
from app.components.activity import interface as activity
from app.components.authorization import interface as authz
from app.components.payments import interface as payments
from app.components.ticketing import interface as ticketing
from app.db.session import set_internal_service_context
from app.i18n import translate
from app.idempotency import idempotent
from app.rate_limiting import RateLimitScope, enforce

router = APIRouter(tags=["payments"])


class PaymentEvent(BaseModel):
    event_id: str = Field(min_length=1, max_length=200)
    type: str
    reference: str = Field(min_length=1, max_length=200)


class SandboxOutcome(BaseModel):
    outcome: str  # paid | failed


def _ticket(t: ticketing.Ticket | None) -> dict | None:
    if t is None:
        return None
    return {
        "id": str(t.id),
        "kind": t.kind,
        "status": t.status,
        "amount_paise": t.amount_paise,
        "checkout_url": t.checkout_url if t.status == "awaiting_payment" else None,
        "hold_active": t.status == "awaiting_payment" and t.hold_expires_at is not None and t.hold_expires_at > datetime.now(UTC),
        "hold_expires_at": t.hold_expires_at.isoformat() if t.hold_expires_at else None,
        "paid_at": t.paid_at.isoformat() if t.paid_at else None,
        "refund_amount_paise": t.refund_amount_paise,
        "refunded_at": t.refunded_at.isoformat() if t.refunded_at else None,
    }


def _unavailable(exc: payments.PaymentsError, lang: str) -> HTTPException:
    key = "payments.notConfigured" if isinstance(exc, payments.PaymentsNotConfigured) else "payments.unavailable"
    return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=translate(key, lang))


@router.get("/occurrences/{occurrence_id}/ticket")
async def my_ticket(occurrence_id: UUID, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    ctx = await ticketing.context(session, occurrence_id)
    if ctx is None:
        raise HTTPException(status_code=404, detail=translate("occurrence.notFound", lang))
    t = await ticketing.my_latest_ticket(session, occurrence_id=occurrence_id, member_id=member.member_id)
    now = datetime.now(UTC)
    deadline = ticketing.refund_deadline(time_start=ctx.time_start, cutoff_hours=ctx.refund_cutoff_hours)
    refund_now = (
        ticketing.refund_for_withdrawal(amount_paise=t.amount_paise, time_start=ctx.time_start, cutoff_hours=ctx.refund_cutoff_hours, now=now)
        if t is not None and t.status == "paid"
        else 0
    )
    return {
        "price_paise": ctx.price_paise,
        "refund_cutoff_hours": ctx.refund_cutoff_hours,
        "refund_deadline": deadline.isoformat(),
        "refund_if_withdraw_now_paise": refund_now,
        "payments_available": payments.get_payment_services().configured,
        "ticket": _ticket(t),
    }


@router.post("/occurrences/{occurrence_id}/ticket")
async def join_paid(occurrence_id: UUID, session: DbSession, member: CurrentMember, lang: Locale, settings: AppSettings, idem: IdempotencyKeyHeader) -> JSONResponse:
    """[FR102] Join a paid activity: hold a spot and hand back the checkout, or take a free waitlist place when full."""
    await enforce(
        session,
        scope=RateLimitScope.PARTICIPATION_TOGGLE,
        subject=str(member.member_id),
        limit_max=settings.rate_limit_participation_max,
        window_seconds=settings.rate_limit_participation_window_seconds,
    )
    async with idempotent(
        session, actor_member_id=member.member_id, idempotency_key=idem, endpoint=f"POST /occurrences/{occurrence_id}/ticket", request_payload={}
    ) as outcome:
        if not outcome.replayed:
            try:
                res = await ticketing.start_join(session, occurrence_id=occurrence_id, member_id=member.member_id)
            except activity.OccurrenceNotFound as exc:
                raise HTTPException(status_code=404, detail=translate("occurrence.notFound", lang)) from exc
            except ticketing.NotPaidActivity as exc:
                raise HTTPException(status_code=409, detail=translate("payments.notPaid", lang)) from exc
            except ticketing.ActivityClosed as exc:
                raise HTTPException(status_code=409, detail=translate("payments.closed", lang)) from exc
            except payments.PaymentsError as exc:
                raise _unavailable(exc, lang) from exc
            outcome.set_result(
                200,
                {
                    "status": res.status,
                    "waitlist_position": res.waitlist_position,
                    "ticket": _ticket(res.ticket),
                    "checkout_url": res.ticket.checkout_url if res.ticket and res.status == "awaiting_payment" else None,
                },
            )
    return JSONResponse(outcome.response, status_code=outcome.status_code)


@router.post("/occurrences/{occurrence_id}/ticket/withdraw")
async def withdraw_paid(occurrence_id: UUID, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """[FR102] Give the spot back. The refund follows the rule the member saw before paying."""
    try:
        res = await ticketing.withdraw(session, occurrence_id=occurrence_id, member_id=member.member_id)
    except activity.OccurrenceNotFound as exc:
        raise HTTPException(status_code=404, detail=translate("occurrence.notFound", lang)) from exc
    except payments.PaymentsError as exc:
        raise _unavailable(exc, lang) from exc
    return {"refund_paise": res.refund_paise, "refund_status": res.refund_status}


@router.get("/occurrences/{occurrence_id}/money")
async def organizer_money(occurrence_id: UUID, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """[FR102] Organizer totals only — never who paid or who did not."""
    try:
        await authz.require_organizer(session, occurrence_id=occurrence_id, member_id=member.member_id)
    except authz.NotFound as exc:
        raise HTTPException(status_code=404, detail=translate("occurrence.notFound", lang)) from exc
    except authz.NotAuthorized as exc:
        raise HTTPException(status_code=403, detail=translate("occurrence.notOrganizer", lang)) from exc
    ctx = await ticketing.context(session, occurrence_id)
    return {
        **(await ticketing.money_summary(session, occurrence_id)),
        "price_paise": ctx.price_paise if ctx else None,
        "payments_available": payments.get_payment_services().configured,
        "payouts_connected": False,  # organizer payouts belong to Payment Services (MOD06), not connected yet
    }


@router.get("/tickets/mine")
async def tickets_mine(session: DbSession, member: CurrentMember) -> list[dict]:
    return [
        {**(_ticket(t) or {}), "occurrence_id": str(t.occurrence_id), "title": c.title, "slug": c.slug, "time_start": c.time_start.isoformat()}
        for t, c in await ticketing.my_tickets(session, member_id=member.member_id)
    ]


@router.post("/payments/events", status_code=200)
async def payment_events(
    body: PaymentEvent,
    session: DbSession,
    settings: AppSettings,
    x_forkhatri_service: Annotated[str | None, Header()] = None,
    x_forkhatri_service_key: Annotated[str | None, Header()] = None,
) -> dict:
    """Service-to-service: Payment Services reports payment and refund outcomes (never called by a browser)."""
    if not payments.verify_event_caller(settings, x_forkhatri_service, x_forkhatri_service_key):
        raise HTTPException(status_code=401, detail="unknown caller")
    if body.type not in ("payment.succeeded", "payment.failed", "refund.succeeded"):
        return {"result": "ignored"}
    await set_internal_service_context(session)
    return {"result": await ticketing.handle_payment_event(session, event_id=body.event_id, event_type=body.type, reference=body.reference)}


def _require_sandbox() -> None:
    if payments.get_payment_services().name != "sandbox":
        raise HTTPException(status_code=404, detail="not found")


@router.get("/payments/sandbox/{reference}")
async def sandbox_checkout(reference: str, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """Development only: what the test checkout shows. The ticket must be the signed-in member's own (RLS)."""
    _require_sandbox()
    from sqlalchemy import text

    row = (
        await session.execute(
            text("SELECT id, occurrence_id, amount_paise, status, hold_expires_at FROM milavn_ticketing.ticket WHERE payment_reference = :r"), {"r": reference}
        )
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail=translate("common.notFound", lang))
    ctx = await ticketing.context(session, row[1])
    return {
        "reference": reference,
        "amount_paise": row[2],
        "status": row[3],
        "hold_expires_at": row[4].isoformat() if row[4] else None,
        "title": ctx.title if ctx else "",
        "slug": ctx.slug if ctx else "",
    }


@router.post("/payments/sandbox/{reference}/complete")
async def sandbox_complete(reference: str, body: SandboxOutcome, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """Development only: stands in for the provider's event after the payer presses Pay or Fail in the test checkout."""
    _require_sandbox()
    from sqlalchemy import text

    owned = await session.scalar(text("SELECT 1 FROM milavn_ticketing.ticket WHERE payment_reference = :r"), {"r": reference})
    if not owned:
        raise HTTPException(status_code=404, detail=translate("common.notFound", lang))
    event_type = "payment.succeeded" if body.outcome == "paid" else "payment.failed"
    result = await ticketing.handle_payment_event(session, event_id=f"sbx-{uuid4()}", event_type=event_type, reference=reference)
    return {"result": result}

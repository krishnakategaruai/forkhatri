"""Paid spots — Milavn's side of paid activities (`milavn_ticketing`, FR102).

# [FR102; thesis §38 no-shows, §53–§55 revenue values; FR036] An organizer may
# charge for a spot (a court booking, a food crawl). Milavn owns the product
# behaviour around the money; Payment Services owns the money.
# Approach, and why:
#   - Free is the default and nothing here changes a free activity.
#   - Joining a paid activity holds a spot for 15 minutes while the member pays,
#     so two people can never pay for one spot (holds count against capacity).
#   - A full paid activity takes a waitlist place for free; when a spot frees up
#     it is OFFERED to the next person with a payment window (12 h, never past
#     one hour before the start) instead of charging them silently.
#   - One refund rule the member reads before paying: a full refund up to the
#     organizer's cutoff before the start, none after; always a full refund when
#     the organizer cancels or a lapsed payment finds the activity full.
#   - Nobody sees who has or has not paid; organizers see totals only.
#   - Every cross-member write runs through definer functions (migration 017).
# Traces to: FR102, FR015/FR058 (capacity + waitlist), FR036, IMP27.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.activity import interface as activity
from app.components.payments import interface as payments
from app.config.settings import get_settings
from app.db.engine import get_process_session_factory
from app.db.session import set_internal_service_context
from app.events import bus
from app.events.bus import DomainEvent

logger = logging.getLogger(__name__)

HOLD = timedelta(minutes=15)
OFFER_HOLD = timedelta(hours=12)
OFFER_MIN = timedelta(minutes=30)


class NotPaidActivity(Exception):
    pass


class ActivityClosed(Exception):
    """Cancelled, or already started: no new paid spots."""


@dataclass(frozen=True, slots=True)
class Ticket:
    id: UUID
    occurrence_id: UUID
    member_id: UUID
    kind: str
    amount_paise: int
    status: str
    checkout_url: str | None
    hold_expires_at: datetime | None
    paid_at: datetime | None
    refund_amount_paise: int | None
    refund_reason: str | None
    refunded_at: datetime | None
    created_at: datetime
    payment_reference: str | None


@dataclass(frozen=True, slots=True)
class Context:
    title: str
    slug: str
    time_start: datetime
    price_paise: int | None
    refund_cutoff_hours: int
    status: str
    capacity: int | None


@dataclass(frozen=True, slots=True)
class JoinOutcome:
    status: str  # awaiting_payment | waitlisted | going
    ticket: Ticket | None
    waitlist_position: int | None


@dataclass(frozen=True, slots=True)
class WithdrawOutcome:
    refund_paise: int
    refund_status: str | None  # refund_pending | refunded | None


_COLS = (
    "id, occurrence_id, member_id, kind, amount_paise, status, checkout_url, hold_expires_at, paid_at, "
    "refund_amount_paise, refund_reason, refunded_at, created_at, payment_reference"
)


# --- pure rules (unit-tested) ------------------------------------------------------


def refund_deadline(*, time_start: datetime, cutoff_hours: int) -> datetime:
    return time_start - timedelta(hours=cutoff_hours)


def refund_for_withdrawal(*, amount_paise: int, time_start: datetime, cutoff_hours: int, now: datetime) -> int:
    """Full refund up to the cutoff, nothing after. One rule, no partial percentages to decode."""
    return amount_paise if now <= refund_deadline(time_start=time_start, cutoff_hours=cutoff_hours) else 0


def offer_hold_until(*, time_start: datetime, now: datetime) -> datetime:
    """A waitlist offer stays open 12 hours but never past one hour before the start; if the start is closer, 30 minutes."""
    until = min(now + OFFER_HOLD, time_start - timedelta(hours=1))
    return until if until >= now + OFFER_MIN else now + OFFER_MIN


# --- reads -----------------------------------------------------------------------------


async def context(session: AsyncSession, occurrence_id: UUID) -> Context | None:
    row = (
        await session.execute(
            text("SELECT title, slug, time_start, price_paise, refund_cutoff_hours, status, capacity FROM milavn_ticketing.offer_context(:o)"),
            {"o": str(occurrence_id)},
        )
    ).first()
    return Context(*row) if row else None


async def my_latest_ticket(session: AsyncSession, *, occurrence_id: UUID, member_id: UUID) -> Ticket | None:
    """The member's most recent ticket for this activity (RLS: their own rows only)."""
    row = (
        await session.execute(
            text(f"SELECT {_COLS} FROM milavn_ticketing.ticket WHERE occurrence_id = :o AND member_id = :m ORDER BY created_at DESC LIMIT 1"),
            {"o": str(occurrence_id), "m": str(member_id)},
        )
    ).first()
    return Ticket(*row) if row else None


async def has_paid_spot(session: AsyncSession, *, occurrence_id: UUID, member_id: UUID) -> bool:
    t = await my_latest_ticket(session, occurrence_id=occurrence_id, member_id=member_id)
    return t is not None and t.status == "paid"


async def open_ticket_count(session: AsyncSession, occurrence_id: UUID) -> int:
    return int((await session.execute(text("SELECT milavn_ticketing.open_ticket_count(:o)"), {"o": str(occurrence_id)})).scalar_one())


async def my_tickets(session: AsyncSession, *, member_id: UUID, limit: int = 50) -> list[tuple[Ticket, Context]]:
    rows = (
        await session.execute(
            text(
                f"SELECT {', '.join('t.' + c.strip() for c in _COLS.split(','))}, c.title, c.slug, c.time_start, c.price_paise, c.refund_cutoff_hours, c.status, c.capacity "
                "FROM milavn_ticketing.ticket t CROSS JOIN LATERAL milavn_ticketing.offer_context(t.occurrence_id) c "
                "WHERE t.member_id = :m AND (t.status IN ('paid', 'refund_pending', 'refunded') "
                "  OR (t.status = 'awaiting_payment' AND t.hold_expires_at > now()) OR (t.status = 'void' AND t.paid_at IS NOT NULL)) "
                "ORDER BY t.created_at DESC LIMIT :l"
            ),
            {"m": str(member_id), "l": limit},
        )
    ).all()
    return [(Ticket(*r[:14]), Context(*r[14:])) for r in rows]


async def money_summary(session: AsyncSession, occurrence_id: UUID) -> dict:
    row = (
        await session.execute(
            text("SELECT paid_spots, collected_paise, refunds_paise, refunds_pending, holds_active FROM milavn_ticketing.money_summary(:o)"),
            {"o": str(occurrence_id)},
        )
    ).one()
    return {"paid_spots": row[0], "collected_paise": int(row[1]), "refunds_paise": int(row[2]), "refunds_pending": row[3], "holds_active": row[4]}


# --- flows -----------------------------------------------------------------------------


async def _lock(session: AsyncSession, occurrence_id: UUID) -> None:
    await session.execute(text("SELECT pg_advisory_xact_lock(hashtext(:id))"), {"id": str(occurrence_id)})


async def _charge(session: AsyncSession, provider: payments.PaymentServices, *, ticket_id: UUID, member_id: UUID, ctx: Context, occurrence_id: UUID) -> None:
    settings = get_settings()
    charge = await provider.create_charge(
        idempotency_key=f"milavn-ticket-{ticket_id}",
        payer_member_id=member_id,
        amount_paise=int(ctx.price_paise or 0),
        description=ctx.title,
        return_url=f"{settings.web_base_url}/a/{ctx.slug}?payment=return",
        metadata={"occurrence_id": str(occurrence_id), "ticket_id": str(ticket_id)},
    )
    await session.execute(text("SELECT milavn_ticketing.attach_charge(:t, :ref, :url)"), {"t": str(ticket_id), "ref": charge.reference, "url": charge.checkout_url})


async def _cancel_quietly(provider: payments.PaymentServices, reference: str | None) -> None:
    if not reference:
        return
    try:
        await provider.cancel_charge(reference=reference)
    except payments.PaymentsError:
        logger.warning("could not cancel charge %s; the provider expires unpaid charges on its own", reference)


async def start_join(session: AsyncSession, *, occurrence_id: UUID, member_id: UUID) -> JoinOutcome:
    ctx = await context(session, occurrence_id)
    if ctx is None:
        raise activity.OccurrenceNotFound
    if ctx.price_paise is None:
        raise NotPaidActivity
    now = datetime.now(UTC)
    if ctx.status != "active" or ctx.time_start <= now:
        raise ActivityClosed
    await _lock(session, occurrence_id)
    current = await my_latest_ticket(session, occurrence_id=occurrence_id, member_id=member_id)
    provider = payments.get_payment_services()
    if current is not None and current.status in ("paid", "refund_pending"):
        return JoinOutcome("going" if current.status == "paid" else current.status, current, None)
    if current is not None and current.status == "awaiting_payment":
        if current.hold_expires_at and current.hold_expires_at > now:
            if not current.checkout_url:  # an offer whose charge could not be created earlier
                await _charge(session, provider, ticket_id=current.id, member_id=member_id, ctx=ctx, occurrence_id=occurrence_id)
            return JoinOutcome("awaiting_payment", await my_latest_ticket(session, occurrence_id=occurrence_id, member_id=member_id), None)
        await _cancel_quietly(provider, current.payment_reference)
        await session.execute(text("SELECT milavn_ticketing.mark_void(:t)"), {"t": str(current.id)})
    if ctx.capacity is not None:
        taken = await activity.spots_taken(session, occurrence_id) + await activity.held_spot_count(session, occurrence_id)
        if taken >= ctx.capacity:
            position = await activity.join_waitlist(session, occurrence_id=occurrence_id, member_id=member_id)
            return JoinOutcome("waitlisted", None, position)
    if not provider.configured:
        raise payments.PaymentsNotConfigured
    ticket_id = uuid4()
    await session.execute(
        text(
            "INSERT INTO milavn_ticketing.ticket (id, occurrence_id, member_id, kind, amount_paise, status, hold_expires_at) "
            "VALUES (:id, :o, :m, 'join', :amount, 'awaiting_payment', :hold)"
        ),
        {"id": str(ticket_id), "o": str(occurrence_id), "m": str(member_id), "amount": ctx.price_paise, "hold": now + HOLD},
    )
    await _charge(session, provider, ticket_id=ticket_id, member_id=member_id, ctx=ctx, occurrence_id=occurrence_id)
    return JoinOutcome("awaiting_payment", await my_latest_ticket(session, occurrence_id=occurrence_id, member_id=member_id), None)


async def _refund(
    session: AsyncSession, provider: payments.PaymentServices, *, ticket_id: UUID, occurrence_id: UUID, member_id: UUID, reference: str | None, amount: int, reason: str
) -> str:
    if not reference:
        raise payments.PaymentsUnavailable("paid ticket without a charge reference")
    refund = await provider.refund(charge_reference=reference, amount_paise=amount, reason=reason, idempotency_key=f"milavn-refund-{ticket_id}")
    await session.execute(text("SELECT milavn_ticketing.mark_refund_pending(:t, :a, :r, :ref)"), {"t": str(ticket_id), "a": amount, "r": reason, "ref": refund.reference})
    payload = {"occurrence_id": occurrence_id, "member_id": member_id, "amount_paise": amount}
    if refund.settled:
        await session.execute(text("SELECT milavn_ticketing.mark_refunded(:t)"), {"t": str(ticket_id)})
        await bus.publish(session, schema="milavn_activity", event_type="ticket.refunded", aggregate_id=occurrence_id, payload=payload)
        return "refunded"
    await bus.publish(session, schema="milavn_activity", event_type="ticket.refund_started", aggregate_id=occurrence_id, payload=payload)
    return "refund_pending"


async def withdraw(session: AsyncSession, *, occurrence_id: UUID, member_id: UUID) -> WithdrawOutcome:
    ctx = await context(session, occurrence_id)
    if ctx is None:
        raise activity.OccurrenceNotFound
    await _lock(session, occurrence_id)
    current = await my_latest_ticket(session, occurrence_id=occurrence_id, member_id=member_id)
    provider = payments.get_payment_services()
    if current is None or current.status not in ("paid", "awaiting_payment"):
        await activity.set_participation(session, occurrence_id=occurrence_id, member_id=member_id, desired="cancelled", via_ticket=True)
        return WithdrawOutcome(0, None)
    if current.status == "awaiting_payment":
        await _cancel_quietly(provider, current.payment_reference)
        await session.execute(text("SELECT milavn_ticketing.mark_void(:t)"), {"t": str(current.id)})
        if current.kind == "waitlist_offer":
            await activity.set_participation(session, occurrence_id=occurrence_id, member_id=member_id, desired="cancelled", via_ticket=True)
        await offer_next(session, occurrence_id)
        return WithdrawOutcome(0, None)
    now = datetime.now(UTC)
    amount = (
        current.amount_paise
        if ctx.status != "active"
        else refund_for_withdrawal(amount_paise=current.amount_paise, time_start=ctx.time_start, cutoff_hours=ctx.refund_cutoff_hours, now=now)
    )
    status: str | None = None
    if amount > 0:
        # Refund first: if Payment Services cannot take the request, nothing changes and the member keeps their spot.
        status = await _refund(
            session,
            provider,
            ticket_id=current.id,
            occurrence_id=occurrence_id,
            member_id=member_id,
            reference=current.payment_reference,
            amount=amount,
            reason="member_withdrew",
        )
    else:
        await session.execute(text("SELECT milavn_ticketing.mark_void(:t)"), {"t": str(current.id)})
    await activity.set_participation(session, occurrence_id=occurrence_id, member_id=member_id, desired="cancelled", via_ticket=True)
    await offer_next(session, occurrence_id)
    return WithdrawOutcome(amount, status)


async def offer_next(session: AsyncSession, occurrence_id: UUID) -> UUID | None:
    """A paid spot came free: offer it to the next waitlisted member, who must pay within the window to take it."""
    ctx = await context(session, occurrence_id)
    now = datetime.now(UTC)
    if ctx is None or ctx.price_paise is None or ctx.status != "active" or ctx.time_start <= now:
        return None
    provider = payments.get_payment_services()
    if not provider.configured:
        return None
    hold_until = offer_hold_until(time_start=ctx.time_start, now=now)
    row = (
        await session.execute(
            text("SELECT ticket_id, member_id, amount_paise FROM milavn_ticketing.create_waitlist_offer(:o, :until)"),
            {"o": str(occurrence_id), "until": hold_until},
        )
    ).first()
    if row is None:
        return None
    try:
        await _charge(session, provider, ticket_id=row[0], member_id=row[1], ctx=ctx, occurrence_id=occurrence_id)
    except payments.PaymentsError:
        logger.warning("offer created without a charge for ticket %s; the member's Pay button retries", row[0])
    await bus.publish(
        session,
        schema="milavn_activity",
        event_type="ticket.offered",
        aggregate_id=occurrence_id,
        payload={"occurrence_id": occurrence_id, "member_id": row[1], "amount_paise": row[2], "hold_until": hold_until.isoformat()},
    )
    return row[1]


async def handle_payment_event(session: AsyncSession, *, event_id: str, event_type: str, reference: str) -> str:
    """Payment Services told us something happened. Idempotent per event id; unknown references are ignored."""
    fresh = (await session.execute(text("SELECT milavn_ticketing.record_payment_event(:e, :t, :r)"), {"e": event_id, "t": event_type, "r": reference})).scalar_one()
    if not fresh:
        return "duplicate"
    row = (
        await session.execute(text("SELECT id, occurrence_id, member_id, kind, status, amount_paise FROM milavn_ticketing.ticket_by_reference(:r)"), {"r": reference})
    ).first()
    if row is None:
        return "unknown_reference"
    ticket_id, occurrence_id, member_id, _kind, _status, amount = row
    provider = payments.get_payment_services()
    if event_type == "payment.succeeded":
        outcome = (await session.execute(text("SELECT milavn_ticketing.mark_paid(:t)"), {"t": str(ticket_id)})).scalar_one()
        if outcome == "going":
            await bus.publish(
                session,
                schema="milavn_activity",
                event_type="ticket.paid",
                aggregate_id=occurrence_id,
                payload={"occurrence_id": occurrence_id, "member_id": member_id, "amount_paise": amount},
            )
        elif outcome in ("refund_no_spot", "refund_cancelled"):
            await _refund(
                session,
                provider,
                ticket_id=ticket_id,
                occurrence_id=occurrence_id,
                member_id=member_id,
                reference=reference,
                amount=amount,
                reason="no_spot" if outcome == "refund_no_spot" else "organizer_cancelled",
            )
        return str(outcome)
    if event_type == "payment.failed":
        kind = (await session.execute(text("SELECT milavn_ticketing.mark_failed(:t)"), {"t": str(ticket_id)})).scalar_one()
        if kind:
            await offer_next(session, occurrence_id)
        return "failed"
    if event_type == "refund.succeeded":
        if (await session.execute(text("SELECT milavn_ticketing.mark_refunded(:t)"), {"t": str(ticket_id)})).scalar_one():
            refunded = (await session.execute(text("SELECT refund_amount_paise FROM milavn_ticketing.ticket WHERE id = :t"), {"t": str(ticket_id)})).scalar_one_or_none()
            await bus.publish(
                session,
                schema="milavn_activity",
                event_type="ticket.refunded",
                aggregate_id=occurrence_id,
                payload={"occurrence_id": occurrence_id, "member_id": member_id, "amount_paise": int(refunded or amount)},
            )
        return "refunded"
    return "ignored"


async def settle_cancelled(session: AsyncSession, occurrence_id: UUID) -> int:
    """The organizer cancelled: every paid spot is refunded in full, every open hold is released."""
    rows = (
        await session.execute(
            text("SELECT ticket_id, member_id, status, amount_paise, payment_reference FROM milavn_ticketing.tickets_to_settle(:o)"), {"o": str(occurrence_id)}
        )
    ).all()
    provider = payments.get_payment_services()
    settled = 0
    for ticket_id, member_id, status, amount, reference in rows:
        if status == "awaiting_payment":
            await _cancel_quietly(provider, reference)
            await session.execute(text("SELECT milavn_ticketing.mark_void(:t)"), {"t": str(ticket_id)})
            continue
        try:
            await _refund(
                session, provider, ticket_id=ticket_id, occurrence_id=occurrence_id, member_id=member_id, reference=reference, amount=amount, reason="organizer_cancelled"
            )
            settled += 1
        except payments.PaymentsError:
            # Left as 'paid' on purpose: the refund is retried on the next cancellation sweep once payments are reachable.
            logger.exception("refund for cancelled activity could not be requested (ticket %s)", ticket_id)
    return settled


async def run_hold_expiry() -> int:
    """Scheduled every minute: lapsed holds give their spot back and the next person on the waitlist is offered it."""
    factory = get_process_session_factory()
    async with factory() as s:
        async with s.begin():
            await set_internal_service_context(s)
            rows = (await s.execute(text("SELECT ticket_id, occurrence_id, member_id, kind, payment_reference FROM milavn_ticketing.expire_holds()"))).all()
            provider = payments.get_payment_services()
            for r in rows:
                await _cancel_quietly(provider, r[4])
            for occurrence_id in {r[1] for r in rows}:
                await offer_next(s, occurrence_id)
        await bus.dispatch_pending(s)
    return len(rows)


async def _on_occurrence_cancelled(event: DomainEvent) -> None:
    factory = get_process_session_factory()
    async with factory() as s:
        async with s.begin():
            await set_internal_service_context(s)
            await settle_cancelled(s, event.aggregate_id)
        await bus.dispatch_pending(s)


def register_subscribers() -> None:
    bus.subscribe("occurrence.cancelled", _on_occurrence_cancelled)

"""Billing — public interface (DEC-V1-031).

Plans, entitlements, orders, the gateway seam, and the two "who is
interested in you" lists that Gold unlocks.

Every entitlement is resolved for the CANDIDATE account (`account_id` is the
context account already resolved by `authz.resolve_context_account()`, so a
parent acting for the candidate reads the candidate's plan).

Nothing here is ever read by discovery: a plan buys capability in one's own
search, never a place in someone else's results.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import plans as catalogue
from app.config.plans import Entitlements, Plan
from app.config.settings import Settings, get_settings
from app.components.billing import gateway as gw

logger = logging.getLogger(__name__)

__all__ = [
    "ContactRequest",
    "ContactRequestNotAllowed",
    "ContactRequestNotFound",
    "InterestedPerson",
    "OrderNotFound",
    "OrderSummary",
    "PaymentNotVerified",
    "PlanState",
    "SandboxUnavailable",
    "UnknownPlanOrTerm",
    "UpgradeRequired",
    "cancel_auto_renew",
    "check_daily_requests",
    "confirm_order",
    "contact_request_state",
    "create_order",
    "decide_contact_request",
    "entitlements_for",
    "has_entitlement",
    "process_webhook",
    "record_profile_view",
    "request_contact",
    "requests_sent_today",
    "resolve_plan",
    "sandbox_pay",
    "who_shortlisted",
    "who_viewed",
]


# --------------------------------------------------------------------------
# Errors
# --------------------------------------------------------------------------


class UpgradeRequired(Exception):
    """The action needs a plan the candidate does not hold."""

    def __init__(self, flag: str, plan_needed: str, *, used: int | None = None, limit: int | None = None):
        super().__init__(f"{flag} needs {plan_needed}")
        self.flag = flag
        self.plan_needed = plan_needed
        self.used = used
        self.limit = limit


class UnknownPlanOrTerm(Exception):
    pass


class OrderNotFound(Exception):
    pass


class PaymentNotVerified(Exception):
    pass


class SandboxUnavailable(Exception):
    """Real gateway keys are configured; the sandbox refuses to run."""


class ContactRequestNotFound(Exception):
    pass


class ContactRequestNotAllowed(Exception):
    """Not an accepted connection of this context, or deciding one's own request."""


# --------------------------------------------------------------------------
# Plan state and entitlements
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PlanState:
    account_id: UUID
    plan: Plan
    subscription_id: UUID | None
    term_months: int | None
    started_at: datetime | None
    ends_at: datetime | None
    auto_renew: bool
    cancelled_at: datetime | None

    @property
    def code(self) -> str:
        return self.plan.code

    @property
    def entitlements(self) -> Entitlements:
        return self.plan.entitlements


async def resolve_plan(session: AsyncSession, *, account_id: UUID) -> PlanState:
    """The plan `account_id` holds right now: the highest-ranked active
    subscription, else FREE. Readable by the holder and their circle."""
    rows = (
        await session.execute(
            text("SELECT * FROM mangaly_billing.active_subscriptions(:account)"),
            {"account": account_id},
        )
    ).mappings().all()
    best = None
    for row in rows:
        rank = catalogue.PLAN_ORDER.index(row["plan_code"]) if row["plan_code"] in catalogue.PLAN_ORDER else -1
        if best is None or rank > best[0]:
            best = (rank, row)
    if best is None:
        return PlanState(account_id, catalogue.plan_for("FREE"), None, None, None, None, False, None)
    row = best[1]
    return PlanState(
        account_id=account_id,
        plan=catalogue.plan_for(row["plan_code"]),
        subscription_id=row["id"],
        term_months=row["term_months"],
        started_at=row["started_at"],
        ends_at=row["ends_at"],
        auto_renew=bool(row["auto_renew"]),
        cancelled_at=row["cancelled_at"],
    )


async def entitlements_for(session: AsyncSession, *, account_id: UUID) -> Entitlements:
    return (await resolve_plan(session, account_id=account_id)).entitlements


async def has_entitlement(session: AsyncSession, account_id: UUID, flag: str) -> bool:
    """`True` when the candidate's plan carries `flag` (e.g. `kundli_full_report`).
    Other components call exactly this; the plan itself stays private here."""
    return (await entitlements_for(session, account_id=account_id)).flag(flag)


async def requests_sent_today(session: AsyncSession, *, account_id: UUID) -> int:
    return int(
        (
            await session.execute(
                text("SELECT mangaly_billing.requests_sent_today(:account)"), {"account": account_id}
            )
        ).scalar_one()
    )


async def check_daily_requests(session: AsyncSession, *, candidate_account_id: UUID) -> None:
    """Free members send a few requests a day; Gold lifts the limit. Raises
    `UpgradeRequired` when today's allowance is used up."""
    ents = await entitlements_for(session, account_id=candidate_account_id)
    if ents.daily_requests is catalogue.UNLIMITED:
        return
    used = await requests_sent_today(session, account_id=candidate_account_id)
    if used >= ents.daily_requests:
        raise UpgradeRequired(
            catalogue.DAILY_REQUESTS,
            catalogue.plan_needed_for(catalogue.DAILY_REQUESTS) or "GOLD",
            used=used,
            limit=ents.daily_requests,
        )


# --------------------------------------------------------------------------
# Orders and payments
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class OrderSummary:
    id: UUID
    account_id: UUID
    plan_code: str
    term_months: int
    amount_paise: int
    gst_paise: int
    currency: str
    status: str
    gateway: str
    gateway_order_id: str | None
    gateway_payment_id: str | None
    created_at: datetime
    paid_at: datetime | None

    @property
    def total_paise(self) -> int:
        return self.amount_paise + self.gst_paise


def _order_from_row(row: Any) -> OrderSummary:
    return OrderSummary(
        id=row["id"],
        account_id=row["account_id"],
        plan_code=row["plan_code"],
        term_months=row["term_months"],
        amount_paise=int(row["amount_paise"]),
        gst_paise=int(row["gst_paise"]),
        currency=row["currency"],
        status=str(row["status"]),
        gateway=row["gateway"],
        gateway_order_id=row["gateway_order_id"],
        gateway_payment_id=row["gateway_payment_id"],
        created_at=row["created_at"],
        paid_at=row["paid_at"],
    )


async def _get_order(session: AsyncSession, *, order_id: UUID) -> OrderSummary:
    row = (
        await session.execute(
            text('SELECT * FROM mangaly_billing."order" WHERE id = :id'), {"id": order_id}
        )
    ).mappings().first()
    if row is None:
        raise OrderNotFound
    return _order_from_row(row)


async def create_order(
    session: AsyncSession,
    *,
    account_id: UUID,
    plan_code: str,
    term_months: int,
    settings: Settings | None = None,
) -> tuple[OrderSummary, gw.GatewayOrder]:
    """Price the plan from the catalogue (never from the client), write the
    order, and ask the gateway for its order. The gateway id is attached to
    our row so a webhook can find it later."""
    settings = settings or get_settings()
    plan = catalogue.PLANS.get(plan_code)
    if plan is None or not plan.terms:
        raise UnknownPlanOrTerm
    term = plan.term(term_months)
    if term is None:
        raise UnknownPlanOrTerm

    gateway = gw.gateway_for(settings)
    order_id = uuid4()
    await session.execute(
        text(
            'INSERT INTO mangaly_billing."order" '
            "(id, account_id, plan_code, term_months, amount_paise, gst_paise, currency, "
            " status, gateway, catalogue_version) "
            "VALUES (:id, :account, :plan, :months, :amount, :gst, :currency, "
            " 'created', :gateway, :version)"
        ),
        {
            "id": order_id,
            "account": account_id,
            "plan": plan.code,
            "months": term.months,
            "amount": term.amount_paise,
            "gst": term.gst_paise,
            "currency": catalogue.CURRENCY,
            "gateway": gateway.name,
            "version": catalogue.CATALOGUE_VERSION,
        },
    )
    gateway_order = await gateway.create_order(
        order_id=order_id,
        amount_paise=term.total_paise,
        currency=catalogue.CURRENCY,
        notes={"plan": plan.code, "term_months": str(term.months), "mangaly_order_id": str(order_id)},
    )
    attached = (
        await session.execute(
            text("SELECT mangaly_billing.attach_gateway_order(:id, :gid)"),
            {"id": order_id, "gid": gateway_order.gateway_order_id},
        )
    ).scalar_one()
    if not attached:
        raise OrderNotFound
    return await _get_order(session, order_id=order_id), gateway_order


async def confirm_order(
    session: AsyncSession,
    *,
    account_id: UUID,
    order_id: UUID,
    gateway_payment_id: str,
    signature: str,
    settings: Settings | None = None,
) -> tuple[OrderSummary, PlanState]:
    """The checkout success handler's `{payment_id, signature}`: verify the
    HMAC against our stored gateway order id, then activate."""
    settings = settings or get_settings()
    order = await _get_order(session, order_id=order_id)  # RLS: owner only
    if order.account_id != account_id or not order.gateway_order_id:
        raise OrderNotFound
    gateway = gw.gateway_for(settings)
    if gateway.name != order.gateway or not gateway.verify_payment_signature(
        gateway_order_id=order.gateway_order_id,
        gateway_payment_id=gateway_payment_id,
        signature=signature,
    ):
        raise PaymentNotVerified
    await session.execute(
        text("SELECT mangaly_billing.mark_order_paid(:id, :pid)"),
        {"id": order_id, "pid": gateway_payment_id},
    )
    return await _get_order(session, order_id=order_id), await resolve_plan(
        session, account_id=account_id
    )


async def sandbox_pay(
    session: AsyncSession, *, account_id: UUID, order_id: UUID, settings: Settings | None = None
) -> tuple[OrderSummary, PlanState]:
    """DEVELOPMENT ONLY: marks the caller's own sandbox order paid. Refuses
    outright when Razorpay keys are configured."""
    settings = settings or get_settings()
    if gw.razorpay_configured(settings):
        raise SandboxUnavailable
    order = await _get_order(session, order_id=order_id)
    if order.account_id != account_id or order.gateway != gw.DevSandboxGateway.name:
        raise OrderNotFound
    payment_id = f"sandbox_pay_{uuid4().hex[:12]}"
    await session.execute(
        text("SELECT mangaly_billing.mark_order_paid(:id, :pid)"),
        {"id": order_id, "pid": payment_id},
    )
    return await _get_order(session, order_id=order_id), await resolve_plan(
        session, account_id=account_id
    )


async def process_webhook(
    session: AsyncSession, *, raw_body: bytes, headers: dict[str, str], settings: Settings | None = None
) -> str:
    """Signature-verified, idempotent. Returns 'processed', 'duplicate' or 'ignored'.
    Raises `gw.WebhookRejected` for a bad signature (answer 400)."""
    settings = settings or get_settings()
    gateway = gw.gateway_for(settings)
    event = gateway.parse_webhook(raw_body=raw_body, headers=headers)

    inserted = (
        await session.execute(
            text(
                "INSERT INTO mangaly_billing.webhook_event (gateway, event_id, event_type, payload) "
                "VALUES (:gateway, :event_id, :event_type, CAST(:payload AS jsonb)) "
                "ON CONFLICT (gateway, event_id) DO NOTHING RETURNING id"
            ),
            {
                "gateway": gateway.name,
                "event_id": event.event_id,
                "event_type": event.event_type,
                "payload": _json(event.payload),
            },
        )
    ).scalar_one_or_none()
    if inserted is None:
        return "duplicate"

    outcome = "ignored"
    if event.gateway_order_id:
        order_id = (
            await session.execute(
                text("SELECT mangaly_billing.order_id_for_gateway(:g, :gid)"),
                {"g": gateway.name, "gid": event.gateway_order_id},
            )
        ).scalar_one_or_none()
        if order_id is not None:
            if event.event_type in ("payment.captured", "order.paid") and event.gateway_payment_id:
                await session.execute(
                    text("SELECT mangaly_billing.mark_order_paid(:id, :pid)"),
                    {"id": order_id, "pid": event.gateway_payment_id},
                )
                outcome = "processed"
            elif event.event_type == "payment.failed":
                await session.execute(
                    text("SELECT mangaly_billing.mark_order_failed(:id)"), {"id": order_id}
                )
                outcome = "processed"
    await session.execute(
        text("UPDATE mangaly_billing.webhook_event SET processed_at = now() WHERE id = :id"),
        {"id": inserted},
    )
    return outcome


def _json(value: dict[str, Any]) -> str:
    import json

    return json.dumps(value, separators=(",", ":"), default=str)


async def cancel_auto_renew(session: AsyncSession, *, account_id: UUID) -> PlanState:
    """Auto-renew off; the plan runs to its end date. No refund logic here."""
    await session.execute(
        text(
            "UPDATE mangaly_billing.plan_subscription "
            "SET auto_renew = false, cancelled_at = COALESCE(cancelled_at, now()) "
            "WHERE account_id = :account AND status = 'active' AND ends_at > now()"
        ),
        {"account": account_id},
    )
    return await resolve_plan(session, account_id=account_id)


# --------------------------------------------------------------------------
# Who is interested in you
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class InterestedPerson:
    account_id: UUID
    at: datetime


async def who_shortlisted(session: AsyncSession, *, account_id: UUID) -> list[InterestedPerson]:
    rows = await session.execute(
        text("SELECT account_id, at FROM mangaly_billing.who_shortlisted(:account)"),
        {"account": account_id},
    )
    return [InterestedPerson(r.account_id, r.at) for r in rows]


async def who_viewed(session: AsyncSession, *, account_id: UUID) -> list[InterestedPerson]:
    rows = await session.execute(
        text("SELECT account_id, at FROM mangaly_billing.who_viewed(:account)"),
        {"account": account_id},
    )
    return [InterestedPerson(r.account_id, r.at) for r in rows]


async def record_profile_view(session: AsyncSession, *, viewer_account_id: UUID, viewed_account_id: UUID) -> None:
    """For the viewed person's "who viewed you" only. Never feeds ranking."""
    try:
        await session.execute(
            text("SELECT mangaly_profile.record_profile_view(:viewer, :viewed)"),
            {"viewer": viewer_account_id, "viewed": viewed_account_id},
        )
    except DBAPIError:
        # A view log must never break a profile view.
        logger.warning("profile view not recorded", exc_info=True)
        raise


# --------------------------------------------------------------------------
# Contact exchange (phone/email) — asking is Gold; the person asked decides.
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ContactRequest:
    id: UUID
    connection_id: UUID
    requester_account_id: UUID
    status: str
    requested_at: datetime
    decided_at: datetime | None
    phone_disclosed_at: datetime | None
    email_disclosed_at: datetime | None


def _contact_from_row(row: Any) -> ContactRequest:
    return ContactRequest(
        id=row["id"],
        connection_id=row["connection_id"],
        requester_account_id=row["requester_account_id"],
        status=str(row["status"]),
        requested_at=row["requested_at"],
        decided_at=row["decided_at"],
        phone_disclosed_at=row["phone_disclosed_at"],
        email_disclosed_at=row["email_disclosed_at"],
    )


async def _accepted_pair(session: AsyncSession, *, connection_id: UUID) -> tuple[UUID, UUID] | None:
    row = (
        await session.execute(
            text(
                "SELECT subject_account_id, target_profile_id FROM mangaly_connection.connection_request "
                "WHERE id = :id AND status = 'accepted'"
            ),
            {"id": connection_id},
        )
    ).first()
    return (row[0], row[1]) if row else None


async def contact_request_state(
    session: AsyncSession, *, connection_id: UUID, context_account_id: UUID
) -> tuple[ContactRequest | None, ContactRequest | None]:
    """(mine, theirs) for this accepted connection, from the context's side."""
    pair = await _accepted_pair(session, connection_id=connection_id)
    if pair is None or context_account_id not in pair:
        raise ContactRequestNotAllowed
    rows = (
        await session.execute(
            text(
                "SELECT * FROM mangaly_communication.contact_exchange_request "
                "WHERE connection_id = :id ORDER BY requested_at DESC"
            ),
            {"id": connection_id},
        )
    ).mappings().all()
    other = pair[1] if pair[0] == context_account_id else pair[0]
    mine = next((_contact_from_row(r) for r in rows if r["requester_account_id"] != other), None)
    theirs = next((_contact_from_row(r) for r in rows if r["requester_account_id"] == other), None)
    return mine, theirs


async def request_contact(
    session: AsyncSession, *, connection_id: UUID, acting_account_id: UUID, context_account_id: UUID
) -> ContactRequest:
    """Ask the other side of an accepted connection for their phone and email.
    Gated on the CONTEXT account's plan (`contact_unlock`)."""
    pair = await _accepted_pair(session, connection_id=connection_id)
    if pair is None or context_account_id not in pair:
        raise ContactRequestNotAllowed
    if not await has_entitlement(session, context_account_id, catalogue.CONTACT_UNLOCK):
        raise UpgradeRequired(
            catalogue.CONTACT_UNLOCK, catalogue.plan_needed_for(catalogue.CONTACT_UNLOCK) or "GOLD"
        )
    row = (
        await session.execute(
            text(
                "INSERT INTO mangaly_communication.contact_exchange_request "
                "(connection_id, requester_account_id) VALUES (:cid, :who) "
                "ON CONFLICT (connection_id, requester_account_id) DO UPDATE SET "
                " status = CASE WHEN contact_exchange_request.status = 'accepted' "
                "               THEN contact_exchange_request.status ELSE 'pending' END, "
                " requested_at = CASE WHEN contact_exchange_request.status = 'accepted' "
                "               THEN contact_exchange_request.requested_at ELSE now() END, "
                " decided_at = CASE WHEN contact_exchange_request.status = 'accepted' "
                "               THEN contact_exchange_request.decided_at ELSE NULL END "
                "RETURNING *"
            ),
            {"cid": connection_id, "who": acting_account_id},
        )
    ).mappings().one()
    return _contact_from_row(row)


async def decide_contact_request(
    session: AsyncSession, *, connection_id: UUID, account_id: UUID, accept: bool
) -> ContactRequest:
    """The person whose contact it is decides, in their own session: accepting
    shares their phone and email with this connection through the ordinary
    sharing grants (what exists of them), so the result is visible where every
    other shared detail is."""
    pair = await _accepted_pair(session, connection_id=connection_id)
    if pair is None or account_id not in pair:
        raise ContactRequestNotAllowed
    other = pair[1] if pair[0] == account_id else pair[0]
    row = (
        await session.execute(
            text(
                "SELECT * FROM mangaly_communication.contact_exchange_request "
                "WHERE connection_id = :cid AND requester_account_id <> :me AND status = 'pending' "
                "ORDER BY requested_at DESC LIMIT 1"
            ),
            {"cid": connection_id, "me": account_id},
        )
    ).mappings().first()
    if row is None:
        raise ContactRequestNotFound
    if row["requester_account_id"] == account_id:
        raise ContactRequestNotAllowed

    phone_at = email_at = None
    if accept:
        from datetime import UTC

        from app.components.connection import interface as connection

        for category in ("phone", "email"):
            try:
                state = await connection.set_share(
                    session,
                    connection_id=connection_id,
                    account_id=account_id,
                    category=category,
                    shared=True,
                )
            except connection.ShareUnavailable:
                continue
            if category == "phone":
                phone_at = state.shared_at or datetime.now(UTC)
            else:
                email_at = state.shared_at or datetime.now(UTC)
        _ = other
    updated = (
        await session.execute(
            text(
                "UPDATE mangaly_communication.contact_exchange_request SET "
                " status = :status, decided_at = now(), decided_by_account_id = :me, "
                " phone_disclosed_at = :phone_at, email_disclosed_at = :email_at "
                "WHERE id = :id RETURNING *"
            ),
            {
                "status": "accepted" if accept else "declined",
                "me": account_id,
                "phone_at": phone_at,
                "email_at": email_at,
                "id": row["id"],
            },
        )
    ).mappings().one()
    return _contact_from_row(updated)

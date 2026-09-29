# [Backend workstream D, 2026-09-28] Contracts & milestone payments.
#
# What this is: a client (who pays) and a provider (who does the work) turn an
# accepted enquiry — a listing enquiry the provider accepted, or a hired
# applicant on an opportunity — into a contract. Fixed-price contracts are
# paid milestone by milestone; hourly contracts are paid from weekly
# timesheets the client approves (each approved week becomes one auto-
# released milestone). Every rupee moves through the existing Payment Bridge
# (services/payments.py, TR051): funding a milestone creates a payment order
# of kind `contract_milestone`, and migration 021's trigger on
# `payment_orders` marks the milestone funded when the gateway says so —
# webhook, status poll or the dev sandbox, this service never guesses.
#
# HONEST GAP (09-implementation.md BLOCKER-01, no merchant account):
# "held" and "released" are ledger facts in `contract_ledger`, not escrow or
# payouts. Nothing here moves money to a provider; a payout adapter belongs
# behind the same ledger once a merchant account exists.
#
# Platform fee: CONTRACT_PLATFORM_FEE_BPS (default 0 — Vyapar takes no cut
# from workers). A `fee` ledger entry is written only when the rate is > 0.
#
# Roles: the client is the side that pays. For an `apply` enquiry (a hired
# applicant) that is the opportunity poster (`enquiries.provider_id`); for
# every other enquiry it is the sender. Only the two parties (and moderation
# operators) can read a contract — RLS in migration 021 enforces it, this
# service re-checks the role for each action.
#
# Domain events (contract.proposed, contract.accepted, milestone.funded,
# milestone.submitted, milestone.approved, contract.completed, plus
# contract.cancelled / contract.disputed) go through the existing outbox
# (`vyapar_enquiries.outbox_event`, which the webhook fan-out already reads):
# a contract is the continuation of an enquiry between the same two members.
# Traces to: FR23, FR27, FR51/TR051, FR52/TR052, REFACTOR-PLAN.md §A
from __future__ import annotations

import json
import logging
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from functools import lru_cache
from typing import Any, Literal

import asyncpg
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.audit import audit
from app.config import get_settings
from app.errors import ApiError
from app.i18n import LAUNCH_LANGUAGES, translate
from app.identity import AuthzContext
from app.outbox import publish_with_outbox
from app.services.pagination import Page, keyset_after, keyset_cursor
from app.services.payments import GatewayUnavailable, create_payment_order, refund_payment_order
from app.services.reviews import issue_review_invites

logger = logging.getLogger(__name__)

ORDER_KIND = "contract_milestone"
HELD_STATES = ("funded", "rejected")            # money recorded as held, work not yet approved
OPEN_MILESTONE_STATES = ("pending", "funded", "submitted", "rejected")


class ContractSettings(BaseSettings):
    """Contract-specific configuration, read from the same .env as app.config
    (kept here so workstream D adds no line to config.py)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Basis points of each released milestone kept by the platform. 0 = no cut.
    contract_platform_fee_bps: int = 0
    # Days after a submission before a silent client's milestone releases itself.
    contract_auto_release_days: int = 14
    # A still-pending checkout younger than this is handed back instead of a new order.
    contract_checkout_reuse_hours: int = 24


@lru_cache
def contract_settings() -> ContractSettings:
    return ContractSettings()


# ---------------------------------------------------------------------------
# API models
# ---------------------------------------------------------------------------
ContractKind = Literal["fixed", "hourly"]
ContractState = Literal["draft", "proposed", "active", "completed", "cancelled", "disputed"]
MilestoneState = Literal["pending", "funded", "submitted", "approved", "released", "rejected", "refunded"]
TimesheetState = Literal["submitted", "approved", "paid", "rejected"]
DisputeState = Literal["open", "resolved_client", "resolved_provider", "closed"]
DisputeOutcome = Literal["resolved_client", "resolved_provider", "closed"]
ContractRole = Literal["client", "provider", "all"]


class MilestoneIn(BaseModel):
    title: str = Field(min_length=2, max_length=140)
    description: str | None = Field(default=None, max_length=2000)
    amount_paise: int = Field(gt=0)
    due_date: date | None = None


class MilestoneUpdateIn(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=140)
    description: str | None = Field(default=None, max_length=2000)
    amount_paise: int | None = Field(default=None, gt=0)
    due_date: date | None = None
    sort: int | None = Field(default=None, ge=0)


class ContractCreateIn(BaseModel):
    enquiry_id: str
    title: str = Field(min_length=3, max_length=140)
    description: str | None = Field(default=None, max_length=2000)
    kind: ContractKind = "fixed"
    total_paise: int = Field(gt=0, description="Fixed: the sum of the milestones. Hourly: the budget ceiling.")
    hourly_rate_paise: int | None = Field(default=None, gt=0)
    weekly_hours_cap: float | None = Field(default=None, gt=0, le=168)
    provider_listing_id: str | None = None
    milestones: list[MilestoneIn] = Field(default_factory=list)
    propose: bool = Field(default=False, description="Send to the provider straight away (draft -> proposed).")


class CancelIn(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class SubmitIn(BaseModel):
    note: str | None = Field(default=None, max_length=1000)


class RejectIn(BaseModel):
    note: str = Field(min_length=1, max_length=1000)


class DisputeIn(BaseModel):
    reason: str = Field(min_length=10, max_length=2000)
    milestone_id: str | None = None


class DisputeResolveIn(BaseModel):
    outcome: DisputeOutcome
    notes: str | None = Field(default=None, max_length=2000)


class TimesheetIn(BaseModel):
    week_start: date = Field(description="The Monday of the week")
    hours: float = Field(gt=0, le=168)
    note: str | None = Field(default=None, max_length=1000)


class MilestoneOut(BaseModel):
    id: str
    title: str
    description: str | None
    amount_paise: int
    due_date: date | None
    sort: int
    state: MilestoneState
    funded_order_id: str | None
    checkout_url: str | None = Field(description="The open checkout while a funding order is pending; null otherwise")
    funded_at: datetime | None
    submitted_at: datetime | None
    submission_note: str | None
    approved_at: datetime | None
    released_at: datetime | None
    rejected_at: datetime | None
    reject_note: str | None
    auto_release_at: datetime | None
    auto_approve: bool


class LedgerSummaryOut(BaseModel):
    held_paise: int = Field(description="Paid by the client and not yet released or refunded")
    released_paise: int = Field(description="Released to the provider (net of any fee)")
    refunded_paise: int
    fee_paise: int


class LedgerEntryOut(BaseModel):
    id: int
    milestone_id: str | None
    entry: Literal["held", "released", "refunded", "fee"]
    amount_paise: int
    payment_order_id: str | None
    note: str | None
    created_at: datetime


class TimesheetOut(BaseModel):
    id: str
    week_start: date
    hours: float
    note: str | None
    state: TimesheetState
    reject_note: str | None
    amount_paise: int
    milestone_id: str | None
    submitted_at: datetime
    approved_at: datetime | None
    paid_at: datetime | None


class DisputeOut(BaseModel):
    id: str
    contract_id: str
    milestone_id: str | None
    opened_by: str
    reason: str
    state: DisputeState
    notes: str | None
    resolved_by: str | None
    resolved_at: datetime | None
    created_at: datetime


class EventOut(BaseModel):
    id: int
    milestone_id: str | None
    actor_member_id: str | None
    type: str
    data: dict[str, Any]
    created_at: datetime


class ContractSummaryOut(BaseModel):
    id: str
    enquiry_id: str
    opportunity_id: str | None
    client_member_id: str
    provider_member_id: str
    provider_listing_id: str | None
    title: str
    kind: ContractKind
    currency: str
    total_paise: int
    state: ContractState
    my_role: Literal["client", "provider", "operator"]
    counterpart_name: str | None
    created_at: datetime
    updated_at: datetime


class ContractOut(ContractSummaryOut):
    description: str | None
    hourly_rate_paise: int | None
    weekly_hours_cap: float | None
    platform_fee_bps: int
    sandbox: bool = Field(description="True when the configured gateway is the dev sandbox (no real money moves). Same value for both parties.")
    payment_notice: str = Field(description="Localized explanation of how money on this contract is handled, shown to both parties")
    proposed_at: datetime | None
    accepted_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None
    cancelled_by: str | None
    cancel_reason: str | None
    client_name: str | None
    provider_name: str | None
    milestones: list[MilestoneOut]
    ledger: LedgerSummaryOut
    ledger_entries: list[LedgerEntryOut]
    timesheets: list[TimesheetOut]
    disputes: list[DisputeOut]
    events: list[EventOut]


class FundingOut(BaseModel):
    """Same shape as a boost purchase: the checkout to open, or a notice."""

    milestone_id: str
    state: MilestoneState
    amount_paise: int
    payment_order_id: str | None
    checkout_url: str | None
    sandbox: bool
    notice: str | None = Field(default=None, description="gatewayUnavailable when no checkout could be created")


class AdminDisputeOut(DisputeOut):
    contract_title: str
    contract_state: ContractState
    client_member_id: str
    provider_member_id: str


class AutoReleaseOut(BaseModel):
    released: int
    completed: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _inr(paise: int) -> str:
    """₹ with Indian digit grouping (₹1,23,456.50); whole rupees drop the paise."""
    rupees, rest = divmod(abs(int(paise)), 100)
    s = str(rupees)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    text = f"₹{s}" if rest == 0 else f"₹{s}.{rest:02d}"
    return f"-{text}" if paise < 0 else text


def _amount_for_hours(hours: Decimal | float, rate_paise: int) -> int:
    return int((Decimal(str(hours)) * Decimal(rate_paise)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _sandbox_mode() -> bool:
    """From the configured gateway, never from a payment order: the provider
    cannot read the client's orders (RLS), and both parties must see the same."""
    return get_settings().payment_gateway == "dev_sandbox"


def _s(value: Any) -> str | None:
    return None if value is None else str(value)


async def _load(conn: asyncpg.Connection, contract_id: str, lang: str, *, for_update: bool = False) -> asyncpg.Record:
    try:
        row = await conn.fetchrow(
            f"SELECT * FROM vyapar_contracts.contracts WHERE id = $1{' FOR UPDATE' if for_update else ''}", contract_id
        )
    except asyncpg.DataError:
        row = None
    if row is None:
        raise ApiError(404, "contracts.error.contractNotFound", lang)
    return row


async def _load_milestone(conn: asyncpg.Connection, contract_id: str, milestone_id: str, lang: str) -> asyncpg.Record:
    try:
        row = await conn.fetchrow(
            "SELECT * FROM vyapar_contracts.contract_milestones WHERE id = $1 AND contract_id = $2 FOR UPDATE",
            milestone_id, contract_id,
        )
    except asyncpg.DataError:
        row = None
    if row is None:
        raise ApiError(404, "contracts.error.milestoneNotFound", lang)
    return row


def _role(ctx: AuthzContext, contract: asyncpg.Record) -> str:
    if ctx.member_id == contract["client_member_id"]:
        return "client"
    if ctx.member_id == contract["provider_member_id"]:
        return "provider"
    return "operator"


def _require_client(ctx: AuthzContext, contract: asyncpg.Record, lang: str) -> None:
    if ctx.member_id != contract["client_member_id"]:
        raise ApiError(403, "contracts.error.notClient", lang)


def _require_provider(ctx: AuthzContext, contract: asyncpg.Record, lang: str) -> None:
    if ctx.member_id != contract["provider_member_id"]:
        raise ApiError(403, "contracts.error.notProvider", lang)


def _require_party(ctx: AuthzContext, contract: asyncpg.Record, lang: str) -> None:
    if ctx.member_id not in (contract["client_member_id"], contract["provider_member_id"]):
        raise ApiError(403, "contracts.error.notParty", lang)


def _require_state(contract: asyncpg.Record, lang: str, *states: str) -> None:
    if contract["state"] not in states:
        raise ApiError(400, "contracts.error.invalidTransition", lang)


def _other(contract: asyncpg.Record, member_id: str) -> str:
    return contract["provider_member_id"] if member_id == contract["client_member_id"] else contract["client_member_id"]


async def _names(conn: asyncpg.Connection, ids: list[str]) -> dict[str, str]:
    rows = await conn.fetch("SELECT id, display_name FROM vyapar_identity.public_names($1::text[])", ids)
    return {r["id"]: r["display_name"] for r in rows}


async def _event(conn: asyncpg.Connection, contract_id, type_: str, *, actor: str | None, milestone_id=None, data: dict | None = None) -> None:
    await conn.execute(
        "INSERT INTO vyapar_contracts.contract_events (contract_id, milestone_id, actor_member_id, type, data) VALUES ($1, $2, $3, $4, $5::jsonb)",
        contract_id, milestone_id, actor, type_, json.dumps(data or {}, default=str),
    )


async def _emit(conn: asyncpg.Connection, contract: asyncpg.Record, event_type: str, **extra: Any) -> None:
    payload = {
        "contract_id": str(contract["id"]), "enquiry_id": str(contract["enquiry_id"]),
        "client_member_id": contract["client_member_id"], "provider_member_id": contract["provider_member_id"],
        "kind": contract["kind"], "total_paise": contract["total_paise"],
        "audience": [contract["client_member_id"], contract["provider_member_id"]],
    }
    payload.update({k: (str(v) if isinstance(v, uuid.UUID) else v) for k, v in extra.items()})
    await publish_with_outbox(conn, schema="enquiry", event_type=event_type, payload=payload)


def _texts(template: str, params: dict[str, Any], key_params: dict[str, str] | None = None) -> dict:
    out = {}
    for lang in LAUNCH_LANGUAGES:
        values = {k: str(v) for k, v in params.items()}
        for name, key in (key_params or {}).items():
            values[name] = translate(key, lang)
        out[lang] = {
            "title": translate(f"notifications.{template}.title", lang, **values),
            "body": translate(f"notifications.{template}.body", lang, **values),
        }
    return out


async def _notify(
    conn: asyncpg.Connection, contract: asyncpg.Record, recipient: str, template: str, idem: str,
    params: dict[str, Any] | None = None, key_params: dict[str, str] | None = None,
) -> None:
    """One party notifies the other (or an operator notifies either). The
    texts are rendered in every launch language; migration 021's
    notify_party() picks the recipient's own and honours blocks."""
    values = dict(params or {})
    keys = dict(key_params or {})
    if "name" not in values and "name" not in keys:
        names = await _names(conn, [_other(contract, recipient)])
        name = names.get(_other(contract, recipient))
        if name:
            values["name"] = name
        else:
            keys["name"] = "contracts.label.otherParty"
    values.setdefault("title", contract["title"])
    await conn.fetchval(
        "SELECT vyapar_contracts.notify_party($1, $2, $3, $4::jsonb, $5, $6)",
        contract["id"], recipient, template, json.dumps(_texts(template, values, keys), ensure_ascii=False),
        f"/contracts/{contract['id']}", idem,
    )


def _milestone_out(m: asyncpg.Record) -> MilestoneOut:
    return MilestoneOut(
        id=str(m["id"]), title=m["title"], description=m["description"], amount_paise=m["amount_paise"], due_date=m["due_date"],
        sort=m["sort"], state=m["state"], funded_order_id=_s(m["funded_order_id"]), checkout_url=m["checkout_url"],
        funded_at=m["funded_at"], submitted_at=m["submitted_at"], submission_note=m["submission_note"], approved_at=m["approved_at"],
        released_at=m["released_at"], rejected_at=m["rejected_at"], reject_note=m["reject_note"], auto_release_at=m["auto_release_at"],
        auto_approve=m["auto_approve"],
    )


def _timesheet_out(t: asyncpg.Record, rate_paise: int | None) -> TimesheetOut:
    return TimesheetOut(
        id=str(t["id"]), week_start=t["week_start"], hours=float(t["hours"]), note=t["note"], state=t["state"], reject_note=t["reject_note"],
        amount_paise=_amount_for_hours(t["hours"], rate_paise or 0), milestone_id=_s(t["milestone_id"]),
        submitted_at=t["submitted_at"], approved_at=t["approved_at"], paid_at=t["paid_at"],
    )


def _dispute_out(d: asyncpg.Record) -> DisputeOut:
    return DisputeOut(
        id=str(d["id"]), contract_id=str(d["contract_id"]), milestone_id=_s(d["milestone_id"]), opened_by=d["opened_by"], reason=d["reason"],
        state=d["state"], notes=d["notes"], resolved_by=d["resolved_by"], resolved_at=d["resolved_at"], created_at=d["created_at"],
    )


def _summary(row: asyncpg.Record, ctx: AuthzContext, names: dict[str, str]) -> dict:
    role = _role(ctx, row)
    counterpart = row["provider_member_id"] if role == "client" else row["client_member_id"]
    return dict(
        id=str(row["id"]), enquiry_id=str(row["enquiry_id"]), opportunity_id=_s(row["opportunity_id"]),
        client_member_id=row["client_member_id"], provider_member_id=row["provider_member_id"], provider_listing_id=_s(row["provider_listing_id"]),
        title=row["title"], kind=row["kind"], currency=row["currency"], total_paise=row["total_paise"], state=row["state"],
        my_role=role, counterpart_name=names.get(counterpart), created_at=row["created_at"], updated_at=row["updated_at"],
    )


async def _detail(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, contract_id) -> ContractOut:
    row = await conn.fetchrow("SELECT * FROM vyapar_contracts.contracts WHERE id = $1", contract_id)
    names = await _names(conn, [row["client_member_id"], row["provider_member_id"]])
    milestones = await conn.fetch("SELECT * FROM vyapar_contracts.contract_milestones WHERE contract_id = $1 ORDER BY sort, created_at", contract_id)
    ledger = await conn.fetch("SELECT * FROM vyapar_contracts.contract_ledger WHERE contract_id = $1 ORDER BY id", contract_id)
    timesheets = await conn.fetch("SELECT * FROM vyapar_contracts.timesheets WHERE contract_id = $1 ORDER BY week_start", contract_id)
    disputes = await conn.fetch("SELECT * FROM vyapar_contracts.contract_disputes WHERE contract_id = $1 ORDER BY created_at DESC", contract_id)
    events = await conn.fetch("SELECT * FROM vyapar_contracts.contract_events WHERE contract_id = $1 ORDER BY id DESC LIMIT 100", contract_id)
    totals = {"held": 0, "released": 0, "refunded": 0, "fee": 0}
    for e in ledger:
        totals[e["entry"]] += e["amount_paise"]
    # held = paid in, minus what has since left the hold (released + fee + refunded)
    held = totals["held"] - totals["released"] - totals["fee"] - totals["refunded"]
    return ContractOut(
        **_summary(row, ctx, names),
        description=row["description"], hourly_rate_paise=row["hourly_rate_paise"],
        weekly_hours_cap=float(row["weekly_hours_cap"]) if row["weekly_hours_cap"] is not None else None,
        platform_fee_bps=row["platform_fee_bps"], sandbox=_sandbox_mode(),
        payment_notice=translate(f"contracts.label.paymentNotice.{'sandbox' if _sandbox_mode() else 'live'}", lang),
        proposed_at=row["proposed_at"], accepted_at=row["accepted_at"], completed_at=row["completed_at"],
        cancelled_at=row["cancelled_at"], cancelled_by=row["cancelled_by"], cancel_reason=row["cancel_reason"],
        client_name=names.get(row["client_member_id"]), provider_name=names.get(row["provider_member_id"]),
        milestones=[_milestone_out(m) for m in milestones],
        ledger=LedgerSummaryOut(held_paise=max(held, 0), released_paise=totals["released"], refunded_paise=totals["refunded"], fee_paise=totals["fee"]),
        ledger_entries=[LedgerEntryOut(id=e["id"], milestone_id=_s(e["milestone_id"]), entry=e["entry"], amount_paise=e["amount_paise"],
                                       payment_order_id=_s(e["payment_order_id"]), note=e["note"], created_at=e["created_at"]) for e in ledger],
        timesheets=[_timesheet_out(t, row["hourly_rate_paise"]) for t in timesheets],
        disputes=[_dispute_out(d) for d in disputes],
        events=[EventOut(id=e["id"], milestone_id=_s(e["milestone_id"]), actor_member_id=e["actor_member_id"], type=e["type"],
                         data=json.loads(e["data"]) if isinstance(e["data"], str) else dict(e["data"] or {}), created_at=e["created_at"]) for e in events],
    )


# ---------------------------------------------------------------------------
# Contract lifecycle
# ---------------------------------------------------------------------------
async def create_contract(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, body: ContractCreateIn) -> ContractOut:
    try:
        enq = await conn.fetchrow("SELECT * FROM vyapar_enquiries.enquiries WHERE id = $1", body.enquiry_id)
    except asyncpg.DataError:
        enq = None
    if enq is None:
        raise ApiError(404, "contracts.error.enquiryNotFound", lang)
    if enq["state"] != "in_progress":
        raise ApiError(400, "contracts.error.enquiryNotAccepted", lang)
    # Who pays: the poster for a hired applicant, otherwise the enquiry's sender.
    if enq["action_type"] == "apply":
        client, provider = enq["provider_id"], enq["sender_id"]
    else:
        client, provider = enq["sender_id"], enq["provider_id"]
    if ctx.member_id != client:
        raise ApiError(403, "contracts.error.notClient", lang)
    if body.kind == "hourly" and (body.hourly_rate_paise is None or body.weekly_hours_cap is None):
        raise ApiError(422, "contracts.error.hourlyRateRequired", lang)
    if body.kind == "hourly" and body.milestones:
        raise ApiError(422, "contracts.error.hourlyNoManualMilestones", lang)

    listing_id = body.provider_listing_id or _s(enq["listing_id"])
    if listing_id is None:
        listing_id = _s(await conn.fetchval(
            """SELECT id FROM vyapar_listings.listings WHERE owner_id = $1 AND state IN ('active_unverified','active_verified')
               ORDER BY created_at DESC LIMIT 1""", provider))
    fee_bps = max(0, min(10000, contract_settings().contract_platform_fee_bps))
    try:
        row = await conn.fetchrow(
            """INSERT INTO vyapar_contracts.contracts
                 (opportunity_id, enquiry_id, client_member_id, provider_member_id, provider_listing_id, title, description, kind,
                  total_paise, hourly_rate_paise, weekly_hours_cap, platform_fee_bps)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12) RETURNING *""",
            enq["opportunity_id"], enq["id"], client, provider, listing_id, body.title.strip(), body.description, body.kind,
            body.total_paise, body.hourly_rate_paise, body.weekly_hours_cap, fee_bps,
        )
    except asyncpg.UniqueViolationError:
        raise ApiError(409, "contracts.error.duplicateContract", lang)
    except asyncpg.DataError:
        raise ApiError(404, "contracts.error.enquiryNotFound", lang)
    for i, m in enumerate(body.milestones):
        await conn.execute(
            "INSERT INTO vyapar_contracts.contract_milestones (contract_id, title, description, amount_paise, due_date, sort) VALUES ($1, $2, $3, $4, $5, $6)",
            row["id"], m.title.strip(), m.description, m.amount_paise, m.due_date, i,
        )
    await _event(conn, row["id"], "contract.created", actor=ctx.member_id, data={"kind": body.kind, "total_paise": body.total_paise})
    if body.propose:
        await _propose(conn, ctx, lang, row)
    return await _detail(conn, ctx, lang, row["id"])


async def _check_milestones_for_proposal(conn: asyncpg.Connection, contract: asyncpg.Record, lang: str) -> None:
    if contract["kind"] == "hourly":
        return
    agg = await conn.fetchrow(
        "SELECT count(*) AS n, coalesce(sum(amount_paise), 0) AS total FROM vyapar_contracts.contract_milestones WHERE contract_id = $1", contract["id"])
    if agg["n"] == 0:
        raise ApiError(422, "contracts.error.milestonesRequired", lang)
    if agg["total"] != contract["total_paise"]:
        raise ApiError(422, "contracts.error.milestonesMustSumToTotal", lang, total=_inr(contract["total_paise"]),
                       extra={"milestones_paise": int(agg["total"]), "total_paise": contract["total_paise"]})


async def _propose(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, contract: asyncpg.Record) -> None:
    await _check_milestones_for_proposal(conn, contract, lang)
    await conn.execute("UPDATE vyapar_contracts.contracts SET state = 'proposed', proposed_at = now(), updated_at = now() WHERE id = $1", contract["id"])
    await _event(conn, contract["id"], "contract.proposed", actor=ctx.member_id)
    await _emit(conn, contract, "contract.proposed", state="proposed")
    await _notify(conn, contract, contract["provider_member_id"], "contractProposed", f"contract_proposed:{contract['id']}",
                  params={"amount": _inr(contract["total_paise"])})


async def propose_contract(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, contract_id: str) -> ContractOut:
    contract = await _load(conn, contract_id, lang, for_update=True)
    _require_client(ctx, contract, lang)
    _require_state(contract, lang, "draft")
    await _propose(conn, ctx, lang, contract)
    return await _detail(conn, ctx, lang, contract["id"])


async def accept_contract(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, contract_id: str) -> ContractOut:
    contract = await _load(conn, contract_id, lang, for_update=True)
    _require_provider(ctx, contract, lang)
    _require_state(contract, lang, "proposed")
    await conn.execute("UPDATE vyapar_contracts.contracts SET state = 'active', accepted_at = now(), updated_at = now() WHERE id = $1", contract["id"])
    await _event(conn, contract["id"], "contract.accepted", actor=ctx.member_id)
    await _emit(conn, contract, "contract.accepted", state="active")
    await _notify(conn, contract, contract["client_member_id"], "contractAccepted", f"contract_accepted:{contract['id']}")
    return await _detail(conn, ctx, lang, contract["id"])


async def _refund_held(conn: asyncpg.Connection, contract: asyncpg.Record, milestone: asyncpg.Record, *, actor: str | None, note: str) -> None:
    """Records the refund in the ledger, then asks the gateway. The order row
    is readable to its payer (and commercial operators); when it is not, the
    order stays visible in the FR49 refund queue exactly as boosts do."""
    await conn.execute("UPDATE vyapar_contracts.contract_milestones SET state = 'refunded', updated_at = now() WHERE id = $1", milestone["id"])
    await conn.execute(
        "INSERT INTO vyapar_contracts.contract_ledger (contract_id, milestone_id, entry, amount_paise, payment_order_id, note) VALUES ($1, $2, 'refunded', $3, $4, $5)",
        contract["id"], milestone["id"], milestone["amount_paise"], milestone["funded_order_id"], note,
    )
    await _event(conn, contract["id"], "milestone.refunded", actor=actor, milestone_id=milestone["id"], data={"reason": note})
    refund_ref = None
    if milestone["funded_order_id"]:
        order = await conn.fetchrow("SELECT * FROM vyapar_payments.payment_orders WHERE id = $1", milestone["funded_order_id"])
        if order is not None and order["state"] == "succeeded":
            refund_ref = await refund_payment_order(conn, order, milestone["amount_paise"])
    if refund_ref is None:
        logger.info("contract %s milestone %s: refund left for the refund queue", contract["id"], milestone["id"])


async def cancel_contract(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, contract_id: str, body: CancelIn) -> ContractOut:
    contract = await _load(conn, contract_id, lang, for_update=True)
    _require_party(ctx, contract, lang)
    _require_state(contract, lang, "draft", "proposed", "active")
    if contract["state"] == "draft":
        _require_client(ctx, contract, lang)
    if contract["state"] == "active":
        milestones = await conn.fetch("SELECT * FROM vyapar_contracts.contract_milestones WHERE contract_id = $1 FOR UPDATE", contract["id"])
        if any(m["state"] == "submitted" for m in milestones):
            raise ApiError(400, "contracts.error.submittedBlocksCancel", lang)
        held = [m for m in milestones if m["state"] in HELD_STATES]
        if held and ctx.member_id != contract["client_member_id"]:
            raise ApiError(400, "contracts.error.heldFundsClientOnly", lang)
        for m in held:
            await _refund_held(conn, contract, m, actor=ctx.member_id, note="contract_cancelled")
    await conn.execute(
        "UPDATE vyapar_contracts.contracts SET state = 'cancelled', cancelled_at = now(), cancelled_by = $2, cancel_reason = $3, updated_at = now() WHERE id = $1",
        contract["id"], ctx.member_id, body.reason,
    )
    await _event(conn, contract["id"], "contract.cancelled", actor=ctx.member_id, data={"from_state": contract["state"], "reason": body.reason})
    await _emit(conn, contract, "contract.cancelled", state="cancelled", previous_state=contract["state"])
    if contract["state"] != "draft":
        await _notify(conn, contract, _other(contract, ctx.member_id), "contractCancelled", f"contract_cancelled:{contract['id']}")
    return await _detail(conn, ctx, lang, contract["id"])


async def _complete(conn: asyncpg.Connection, contract: asyncpg.Record, *, actor: str | None) -> None:
    await conn.execute("UPDATE vyapar_contracts.contracts SET state = 'completed', completed_at = now(), updated_at = now() WHERE id = $1", contract["id"])
    await _event(conn, contract["id"], "contract.completed", actor=actor)
    await _emit(conn, contract, "contract.completed", state="completed")
    for member in (contract["client_member_id"], contract["provider_member_id"]):
        await _notify(conn, contract, member, "contractCompleted", f"contract_completed:{contract['id']}:{member}")
    # The enquiry this contract came from has reached its outcome.
    await conn.execute(
        "UPDATE vyapar_enquiries.enquiries SET state = 'resolved', state_reason = 'contract_completed', last_activity_at = now(), updated_at = now() WHERE id = $1 AND state = 'in_progress'",
        contract["enquiry_id"],
    )
    # [FR27] Review invites for both sides, through the existing reviews
    # service; migration 021 taught issue_invites() that a completed contract
    # qualifies the enquiry.
    await issue_review_invites(conn, "enquiry", contract["enquiry_id"])


async def _maybe_complete(conn: asyncpg.Connection, contract: asyncpg.Record, *, actor: str | None) -> bool:
    """A fixed-price contract completes itself when every milestone is
    released. Hourly contracts (open-ended) complete on the client's word."""
    if contract["kind"] != "fixed":
        return False
    agg = await conn.fetchrow(
        """SELECT count(*) FILTER (WHERE state <> 'released') AS open, count(*) AS n
             FROM vyapar_contracts.contract_milestones WHERE contract_id = $1""", contract["id"])
    if agg["n"] == 0 or agg["open"] != 0:
        return False
    await _complete(conn, contract, actor=actor)
    return True


async def complete_contract(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, contract_id: str) -> ContractOut:
    contract = await _load(conn, contract_id, lang, for_update=True)
    _require_client(ctx, contract, lang)
    _require_state(contract, lang, "active")
    agg = await conn.fetchrow(
        """SELECT count(*) FILTER (WHERE state IN ('funded','submitted','rejected')) AS held,
                  count(*) FILTER (WHERE state = 'released') AS released
             FROM vyapar_contracts.contract_milestones WHERE contract_id = $1""", contract["id"])
    if agg["held"] != 0 or agg["released"] == 0:
        raise ApiError(400, "contracts.error.notCompletable", lang)
    await _complete(conn, contract, actor=ctx.member_id)
    return await _detail(conn, ctx, lang, contract["id"])


async def get_contract(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, contract_id: str) -> ContractOut:
    contract = await _load(conn, contract_id, lang)
    return await _detail(conn, ctx, lang, contract["id"])


async def list_my_contracts(
    conn: asyncpg.Connection, ctx: AuthzContext, lang: str, *, role: str, state: str | None, limit: int, cursor: str | None,
) -> Page[ContractSummaryOut]:
    after_t, after_id = keyset_after(cursor, lang)
    clauses, params = [], [ctx.member_id]
    if role == "client":
        clauses.append("client_member_id = $1")
    elif role == "provider":
        clauses.append("provider_member_id = $1")
    else:
        clauses.append("(client_member_id = $1 OR provider_member_id = $1)")
    if state:
        params.append(state)
        clauses.append(f"state = ${len(params)}")
    if after_t is not None:
        params.extend([after_t, after_id])
        clauses.append(f"(created_at, id::text) < (${len(params) - 1}, ${len(params)})")
    params.append(limit + 1)
    rows = await conn.fetch(
        f"SELECT * FROM vyapar_contracts.contracts WHERE {' AND '.join(clauses)} ORDER BY created_at DESC, id::text DESC LIMIT ${len(params)}", *params)
    more = len(rows) > limit
    rows = rows[:limit]
    ids = {r["client_member_id"] for r in rows} | {r["provider_member_id"] for r in rows}
    names = await _names(conn, list(ids)) if ids else {}
    items = [ContractSummaryOut(**_summary(r, ctx, names)) for r in rows]
    return Page[ContractSummaryOut](items=items, next_cursor=keyset_cursor(rows[-1]["created_at"], rows[-1]["id"]) if more and rows else None)


# ---------------------------------------------------------------------------
# Milestones
# ---------------------------------------------------------------------------
async def _draft_for_edit(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, contract_id: str) -> asyncpg.Record:
    contract = await _load(conn, contract_id, lang, for_update=True)
    _require_client(ctx, contract, lang)
    if contract["state"] != "draft":
        raise ApiError(400, "contracts.error.draftOnly", lang)
    if contract["kind"] == "hourly":
        raise ApiError(400, "contracts.error.hourlyNoManualMilestones", lang)
    return contract


async def add_milestone(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, contract_id: str, body: MilestoneIn) -> ContractOut:
    contract = await _draft_for_edit(conn, ctx, lang, contract_id)
    sort = await conn.fetchval("SELECT coalesce(max(sort), -1) + 1 FROM vyapar_contracts.contract_milestones WHERE contract_id = $1", contract["id"])
    await conn.execute(
        "INSERT INTO vyapar_contracts.contract_milestones (contract_id, title, description, amount_paise, due_date, sort) VALUES ($1, $2, $3, $4, $5, $6)",
        contract["id"], body.title.strip(), body.description, body.amount_paise, body.due_date, sort,
    )
    await conn.execute("UPDATE vyapar_contracts.contracts SET updated_at = now() WHERE id = $1", contract["id"])
    return await _detail(conn, ctx, lang, contract["id"])


async def update_milestone(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, contract_id: str, milestone_id: str, body: MilestoneUpdateIn) -> ContractOut:
    contract = await _draft_for_edit(conn, ctx, lang, contract_id)
    m = await _load_milestone(conn, contract["id"], milestone_id, lang)
    fields = body.model_dump(exclude_unset=True)
    await conn.execute(
        """UPDATE vyapar_contracts.contract_milestones
              SET title = $2, description = $3, amount_paise = $4, due_date = $5, sort = $6, updated_at = now() WHERE id = $1""",
        m["id"], (fields.get("title") or m["title"]).strip(), fields.get("description", m["description"]),
        fields.get("amount_paise") or m["amount_paise"], fields.get("due_date", m["due_date"]),
        fields["sort"] if fields.get("sort") is not None else m["sort"],
    )
    await conn.execute("UPDATE vyapar_contracts.contracts SET updated_at = now() WHERE id = $1", contract["id"])
    return await _detail(conn, ctx, lang, contract["id"])


async def delete_milestone(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, contract_id: str, milestone_id: str) -> ContractOut:
    contract = await _draft_for_edit(conn, ctx, lang, contract_id)
    m = await _load_milestone(conn, contract["id"], milestone_id, lang)
    await conn.execute("DELETE FROM vyapar_contracts.contract_milestones WHERE id = $1", m["id"])
    await conn.execute("UPDATE vyapar_contracts.contracts SET updated_at = now() WHERE id = $1", contract["id"])
    return await _detail(conn, ctx, lang, contract["id"])


async def _fund(
    conn: asyncpg.Connection, ctx: AuthzContext, lang: str, contract: asyncpg.Record, m: asyncpg.Record, *, notice_template: str, notice_params: dict[str, Any],
) -> FundingOut:
    """Creates (or hands back) the checkout that funds one pending milestone.
    The milestone becomes `funded` only when the Payment Bridge records the
    gateway's success (migration 021 trigger) — never here."""
    sandbox = _sandbox_mode()
    if m["funded_order_id"] and m["checkout_url"]:
        order = await conn.fetchrow("SELECT * FROM vyapar_payments.payment_orders WHERE id = $1", m["funded_order_id"])
        if order is not None and order["state"] == "pending" and \
                order["created_at"] > datetime.now(order["created_at"].tzinfo) - timedelta(hours=contract_settings().contract_checkout_reuse_hours):
            return FundingOut(milestone_id=str(m["id"]), state=m["state"], amount_paise=m["amount_paise"], payment_order_id=str(order["id"]),
                              checkout_url=m["checkout_url"], sandbox=sandbox)
    # Pre-render the provider's "funded" notification in every language: the
    # payment trigger has no translator, it only picks the recipient's language.
    notice = {"template": notice_template, "texts": _texts(notice_template, {**notice_params, "title": contract["title"]})}
    await conn.execute("UPDATE vyapar_contracts.contract_milestones SET pending_notice = $2::jsonb, updated_at = now() WHERE id = $1",
                       m["id"], json.dumps(notice, ensure_ascii=False))
    try:
        order = await create_payment_order(
            conn, kind=ORDER_KIND, ref_id=m["id"], member_id=ctx.member_id, amount_paise=m["amount_paise"], tax_paise=0,
            description=f"Vyapar contract milestone: {m['title']}"[:200], return_path=f"/contracts/{contract['id']}",
            idempotency_key=f"{ORDER_KIND}:{m['id']}:{uuid.uuid4().hex[:12]}",
        )
    except GatewayUnavailable:
        return FundingOut(milestone_id=str(m["id"]), state=m["state"], amount_paise=m["amount_paise"], payment_order_id=None,
                          checkout_url=None, sandbox=sandbox, notice="gatewayUnavailable")
    await conn.execute(
        "UPDATE vyapar_contracts.contract_milestones SET funded_order_id = $2, checkout_url = $3, updated_at = now() WHERE id = $1",
        m["id"], order["id"], order["checkout_url"],
    )
    await _event(conn, contract["id"], "milestone.funding_started", actor=ctx.member_id, milestone_id=m["id"],
                 data={"payment_order_id": order["id"], "amount_paise": m["amount_paise"]})
    return FundingOut(milestone_id=str(m["id"]), state=m["state"], amount_paise=m["amount_paise"], payment_order_id=order["id"],
                      checkout_url=order["checkout_url"], sandbox=sandbox)


async def fund_milestone(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, contract_id: str, milestone_id: str) -> FundingOut:
    contract = await _load(conn, contract_id, lang, for_update=True)
    _require_client(ctx, contract, lang)
    _require_state(contract, lang, "active")
    m = await _load_milestone(conn, contract["id"], milestone_id, lang)
    if m["state"] != "pending":
        raise ApiError(400, "contracts.error.milestoneNotFundable", lang)
    return await _fund(conn, ctx, lang, contract, m, notice_template="milestoneFunded",
                       notice_params={"milestone": m["title"], "amount": _inr(m["amount_paise"])})


async def submit_milestone(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, contract_id: str, milestone_id: str, body: SubmitIn) -> ContractOut:
    contract = await _load(conn, contract_id, lang, for_update=True)
    _require_provider(ctx, contract, lang)
    _require_state(contract, lang, "active")
    m = await _load_milestone(conn, contract["id"], milestone_id, lang)
    if m["state"] not in HELD_STATES:
        raise ApiError(400, "contracts.error.milestoneNotFunded", lang)
    days = contract_settings().contract_auto_release_days
    await conn.execute(
        """UPDATE vyapar_contracts.contract_milestones
              SET state = 'submitted', submitted_at = now(), submission_note = $2, auto_release_at = now() + make_interval(days => $3), updated_at = now()
            WHERE id = $1""", m["id"], body.note, days)
    await _event(conn, contract["id"], "milestone.submitted", actor=ctx.member_id, milestone_id=m["id"], data={"note": body.note, "auto_release_days": days})
    await _emit(conn, contract, "milestone.submitted", milestone_id=m["id"], amount_paise=m["amount_paise"])
    await _notify(conn, contract, contract["client_member_id"], "milestoneSubmitted", f"milestone_submitted:{m['id']}:{uuid.uuid4().hex[:8]}",
                  params={"milestone": m["title"]})
    return await _detail(conn, ctx, lang, contract["id"])


async def _release(conn: asyncpg.Connection, contract: asyncpg.Record, m: asyncpg.Record, *, actor: str | None, reason: str) -> None:
    fee = (m["amount_paise"] * contract["platform_fee_bps"]) // 10000
    await conn.execute(
        "UPDATE vyapar_contracts.contract_milestones SET state = 'released', approved_at = now(), released_at = now(), auto_release_at = NULL, updated_at = now() WHERE id = $1",
        m["id"])
    await conn.execute(
        "INSERT INTO vyapar_contracts.contract_ledger (contract_id, milestone_id, entry, amount_paise, payment_order_id, note) VALUES ($1, $2, 'released', $3, $4, $5)",
        contract["id"], m["id"], m["amount_paise"] - fee, m["funded_order_id"], reason)
    if fee > 0:
        await conn.execute(
            "INSERT INTO vyapar_contracts.contract_ledger (contract_id, milestone_id, entry, amount_paise, payment_order_id, note) VALUES ($1, $2, 'fee', $3, $4, 'platform_fee')",
            contract["id"], m["id"], fee, m["funded_order_id"])
    await _event(conn, contract["id"], "milestone.released", actor=actor, milestone_id=m["id"],
                 data={"amount_paise": m["amount_paise"], "fee_paise": fee, "reason": reason})
    await _emit(conn, contract, "milestone.approved", milestone_id=m["id"], amount_paise=m["amount_paise"], fee_paise=fee, reason=reason)
    await _notify(conn, contract, contract["provider_member_id"], "milestoneReleased", f"milestone_released:{m['id']}",
                  params={"milestone": m["title"], "amount": _inr(m["amount_paise"] - fee)})


async def approve_milestone(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, contract_id: str, milestone_id: str) -> ContractOut:
    contract = await _load(conn, contract_id, lang, for_update=True)
    _require_client(ctx, contract, lang)
    _require_state(contract, lang, "active")
    m = await _load_milestone(conn, contract["id"], milestone_id, lang)
    if m["state"] != "submitted":
        raise ApiError(400, "contracts.error.milestoneNotSubmitted", lang)
    await _release(conn, contract, m, actor=ctx.member_id, reason="client_approved")
    await _maybe_complete(conn, contract, actor=ctx.member_id)
    return await _detail(conn, ctx, lang, contract["id"])


async def reject_milestone(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, contract_id: str, milestone_id: str, body: RejectIn) -> ContractOut:
    contract = await _load(conn, contract_id, lang, for_update=True)
    _require_client(ctx, contract, lang)
    _require_state(contract, lang, "active")
    m = await _load_milestone(conn, contract["id"], milestone_id, lang)
    if m["state"] != "submitted":
        raise ApiError(400, "contracts.error.milestoneNotSubmitted", lang)
    await conn.execute(
        "UPDATE vyapar_contracts.contract_milestones SET state = 'rejected', rejected_at = now(), reject_note = $2, auto_release_at = NULL, updated_at = now() WHERE id = $1",
        m["id"], body.note)
    await _event(conn, contract["id"], "milestone.rejected", actor=ctx.member_id, milestone_id=m["id"], data={"note": body.note})
    await _notify(conn, contract, contract["provider_member_id"], "milestoneRejected", f"milestone_rejected:{m['id']}:{uuid.uuid4().hex[:8]}",
                  params={"milestone": m["title"], "note": body.note})
    return await _detail(conn, ctx, lang, contract["id"])


# ---------------------------------------------------------------------------
# Disputes (in-product mediation; a moderation operator records the outcome)
# ---------------------------------------------------------------------------
async def open_dispute(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, contract_id: str, body: DisputeIn) -> ContractOut:
    contract = await _load(conn, contract_id, lang, for_update=True)
    _require_party(ctx, contract, lang)
    _require_state(contract, lang, "active")
    if await conn.fetchval("SELECT EXISTS (SELECT 1 FROM vyapar_contracts.contract_disputes WHERE contract_id = $1 AND state = 'open')", contract["id"]):
        raise ApiError(409, "contracts.error.disputeAlreadyOpen", lang)
    milestone_id = None
    if body.milestone_id:
        milestone_id = (await _load_milestone(conn, contract["id"], body.milestone_id, lang))["id"]
    dispute = await conn.fetchrow(
        "INSERT INTO vyapar_contracts.contract_disputes (contract_id, milestone_id, opened_by, reason) VALUES ($1, $2, $3, $4) RETURNING *",
        contract["id"], milestone_id, ctx.member_id, body.reason.strip())
    await conn.execute("UPDATE vyapar_contracts.contracts SET state = 'disputed', updated_at = now() WHERE id = $1", contract["id"])
    await _event(conn, contract["id"], "contract.disputed", actor=ctx.member_id, milestone_id=milestone_id, data={"dispute_id": dispute["id"]})
    await _emit(conn, contract, "contract.disputed", state="disputed", dispute_id=dispute["id"], milestone_id=milestone_id)
    await _notify(conn, contract, _other(contract, ctx.member_id), "contractDisputed", f"contract_disputed:{dispute['id']}")
    return await _detail(conn, ctx, lang, contract["id"])


async def _require_moderator(conn: asyncpg.Connection, lang: str) -> None:
    if not await conn.fetchval("SELECT vyapar_identity.is_operator('moderation')"):
        raise ApiError(403, "contracts.error.moderationPermissionRequired", lang)


async def resolve_dispute(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, contract_id: str, dispute_id: str, body: DisputeResolveIn) -> ContractOut:
    await _require_moderator(conn, lang)
    contract = await _load(conn, contract_id, lang, for_update=True)
    _require_state(contract, lang, "disputed")
    try:
        dispute = await conn.fetchrow("SELECT * FROM vyapar_contracts.contract_disputes WHERE id = $1 AND contract_id = $2 FOR UPDATE", dispute_id, contract["id"])
    except asyncpg.DataError:
        dispute = None
    if dispute is None:
        raise ApiError(404, "contracts.error.disputeNotFound", lang)
    if dispute["state"] != "open":
        raise ApiError(400, "contracts.error.invalidTransition", lang)
    await conn.execute(
        "UPDATE vyapar_contracts.contract_disputes SET state = $2, notes = $3, resolved_by = $4, resolved_at = now(), updated_at = now() WHERE id = $1",
        dispute["id"], body.outcome, body.notes, ctx.member_id)
    held = await conn.fetch(
        "SELECT * FROM vyapar_contracts.contract_milestones WHERE contract_id = $1 AND state IN ('funded','submitted','rejected') FOR UPDATE", contract["id"])
    if body.outcome == "resolved_client":
        for m in held:
            await _refund_held(conn, contract, m, actor=ctx.member_id, note="dispute_resolved_client")
        await conn.execute(
            "UPDATE vyapar_contracts.contracts SET state = 'cancelled', cancelled_at = now(), cancelled_by = $2, cancel_reason = 'dispute_resolved_client', updated_at = now() WHERE id = $1",
            contract["id"], ctx.member_id)
        await _emit(conn, contract, "contract.cancelled", state="cancelled", previous_state="disputed", dispute_id=dispute["id"])
    else:
        await conn.execute("UPDATE vyapar_contracts.contracts SET state = 'active', updated_at = now() WHERE id = $1", contract["id"])
        if body.outcome == "resolved_provider":
            for m in held:
                await _release(conn, contract, m, actor=ctx.member_id, reason="dispute_resolved_provider")
    await _event(conn, contract["id"], "dispute.resolved", actor=ctx.member_id, data={"dispute_id": dispute["id"], "outcome": body.outcome, "notes": body.notes})
    await audit(conn, actor_id=ctx.member_id, action="contract_dispute_resolved", object_kind="contract_dispute", object_id=str(dispute["id"]),
                reason_code=body.outcome, details={"contract_id": str(contract["id"]), "milestones": len(held)})
    for member in (contract["client_member_id"], contract["provider_member_id"]):
        await _notify(conn, contract, member, "disputeResolved", f"dispute_resolved:{dispute['id']}:{member}",
                      key_params={"outcome": f"contracts.label.outcome.{body.outcome}"})
    if body.outcome == "resolved_provider":
        # Completion resolves the parties' enquiry and issues their review
        # invites; both are party-only paths (enquiry RLS WITH CHECK,
        # issue_invites()). Run that step as the client — the same context
        # the auto-release pass uses — then return to the operator's.
        fresh = await conn.fetchrow("SELECT * FROM vyapar_contracts.contracts WHERE id = $1", contract["id"])
        await conn.execute("SELECT set_config('vyapar.authz_context', $1, true)", contract["client_member_id"])
        try:
            await _maybe_complete(conn, fresh, actor=ctx.member_id)
        finally:
            await conn.execute("SELECT set_config('vyapar.authz_context', $1, true)", ctx.member_id)
    return await _detail(conn, ctx, lang, contract["id"])


async def list_disputes_for_operators(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, *, state: str | None, limit: int) -> list[AdminDisputeOut]:
    await _require_moderator(conn, lang)
    rows = await conn.fetch(
        """SELECT d.*, c.title AS contract_title, c.state AS contract_state, c.client_member_id, c.provider_member_id
             FROM vyapar_contracts.contract_disputes d JOIN vyapar_contracts.contracts c ON c.id = d.contract_id
            WHERE ($1::text IS NULL OR d.state = $1) ORDER BY d.created_at DESC LIMIT $2""", state, limit)
    return [AdminDisputeOut(**_dispute_out(r).model_dump(), contract_title=r["contract_title"], contract_state=r["contract_state"],
                            client_member_id=r["client_member_id"], provider_member_id=r["provider_member_id"]) for r in rows]


# ---------------------------------------------------------------------------
# Hourly contracts: weekly timesheets
# ---------------------------------------------------------------------------
async def submit_timesheet(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, contract_id: str, body: TimesheetIn) -> ContractOut:
    contract = await _load(conn, contract_id, lang, for_update=True)
    _require_provider(ctx, contract, lang)
    _require_state(contract, lang, "active")
    if contract["kind"] != "hourly":
        raise ApiError(400, "contracts.error.hourlyOnly", lang)
    if body.week_start.isoweekday() != 1:
        raise ApiError(422, "contracts.error.weekStartNotMonday", lang)
    today = date.today()
    if body.week_start > today - timedelta(days=today.isoweekday() - 1):
        raise ApiError(422, "contracts.error.weekInFuture", lang)
    hours = Decimal(str(body.hours)).quantize(Decimal("0.01"))
    if hours > contract["weekly_hours_cap"]:
        raise ApiError(422, "contracts.error.weeklyCapExceeded", lang, cap=f"{float(contract['weekly_hours_cap']):g}")
    amount = _amount_for_hours(hours, contract["hourly_rate_paise"])
    committed = await conn.fetchval(
        "SELECT coalesce(sum(amount_paise), 0) FROM vyapar_contracts.contract_milestones WHERE contract_id = $1 AND state <> 'refunded'", contract["id"])
    pending_hours = await conn.fetchval(
        "SELECT coalesce(sum(hours), 0) FROM vyapar_contracts.timesheets WHERE contract_id = $1 AND state = 'submitted'", contract["id"])
    if committed + _amount_for_hours(pending_hours, contract["hourly_rate_paise"]) + amount > contract["total_paise"]:
        raise ApiError(422, "contracts.error.budgetExceeded", lang, total=_inr(contract["total_paise"]))
    try:
        ts = await conn.fetchrow(
            "INSERT INTO vyapar_contracts.timesheets (contract_id, week_start, hours, note) VALUES ($1, $2, $3, $4) RETURNING *",
            contract["id"], body.week_start, hours, body.note)
    except asyncpg.UniqueViolationError:
        raise ApiError(409, "contracts.error.timesheetDuplicateWeek", lang)
    await _event(conn, contract["id"], "timesheet.submitted", actor=ctx.member_id, data={"timesheet_id": ts["id"], "week_start": body.week_start, "hours": str(hours)})
    await _notify(conn, contract, contract["client_member_id"], "timesheetSubmitted", f"timesheet_submitted:{ts['id']}",
                  params={"week": body.week_start.isoformat(), "hours": f"{float(hours):g}", "amount": _inr(amount)})
    return await _detail(conn, ctx, lang, contract["id"])


async def _load_timesheet(conn: asyncpg.Connection, contract_id, timesheet_id: str, lang: str) -> asyncpg.Record:
    try:
        ts = await conn.fetchrow("SELECT * FROM vyapar_contracts.timesheets WHERE id = $1 AND contract_id = $2 FOR UPDATE", timesheet_id, contract_id)
    except asyncpg.DataError:
        ts = None
    if ts is None:
        raise ApiError(404, "contracts.error.timesheetNotFound", lang)
    if ts["state"] != "submitted":
        raise ApiError(400, "contracts.error.timesheetNotSubmitted", lang)
    return ts


async def approve_timesheet(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, contract_id: str, timesheet_id: str) -> FundingOut:
    """Approving a week turns it into one auto-released milestone and opens
    its checkout: once paid, the trigger funds and releases it in one go and
    marks the timesheet paid."""
    contract = await _load(conn, contract_id, lang, for_update=True)
    _require_client(ctx, contract, lang)
    _require_state(contract, lang, "active")
    ts = await _load_timesheet(conn, contract["id"], timesheet_id, lang)
    amount = _amount_for_hours(ts["hours"], contract["hourly_rate_paise"])
    sort = await conn.fetchval("SELECT coalesce(max(sort), -1) + 1 FROM vyapar_contracts.contract_milestones WHERE contract_id = $1", contract["id"])
    m = await conn.fetchrow(
        """INSERT INTO vyapar_contracts.contract_milestones (contract_id, title, description, amount_paise, due_date, sort, auto_approve)
           VALUES ($1, $2, $3, $4, $5, $6, true) RETURNING *""",
        contract["id"], translate("contracts.label.weekOf", lang, week=ts["week_start"].isoformat()), ts["note"], amount, ts["week_start"] + timedelta(days=6), sort)
    await conn.execute("UPDATE vyapar_contracts.timesheets SET state = 'approved', approved_at = now(), milestone_id = $2, updated_at = now() WHERE id = $1", ts["id"], m["id"])
    await _event(conn, contract["id"], "timesheet.approved", actor=ctx.member_id, milestone_id=m["id"], data={"timesheet_id": ts["id"], "amount_paise": amount})
    week = ts["week_start"].isoformat()
    return await _fund(conn, ctx, lang, contract, m, notice_template="timesheetPaid",
                       notice_params={"week": week, "hours": f"{float(ts['hours']):g}", "amount": _inr(amount - (amount * contract["platform_fee_bps"]) // 10000)})


async def reject_timesheet(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, contract_id: str, timesheet_id: str, body: RejectIn) -> ContractOut:
    contract = await _load(conn, contract_id, lang, for_update=True)
    _require_client(ctx, contract, lang)
    _require_state(contract, lang, "active")
    ts = await _load_timesheet(conn, contract["id"], timesheet_id, lang)
    await conn.execute("UPDATE vyapar_contracts.timesheets SET state = 'rejected', reject_note = $2, updated_at = now() WHERE id = $1", ts["id"], body.note)
    await _event(conn, contract["id"], "timesheet.rejected", actor=ctx.member_id, data={"timesheet_id": ts["id"], "note": body.note})
    await _notify(conn, contract, contract["provider_member_id"], "timesheetRejected", f"timesheet_rejected:{ts['id']}",
                  params={"week": ts["week_start"].isoformat(), "note": body.note})
    return await _detail(conn, ctx, lang, contract["id"])


# ---------------------------------------------------------------------------
# Scheduled pass: auto-release after 14 days of client silence
# ---------------------------------------------------------------------------
async def run_contract_auto_release_pass(pool: asyncpg.Pool) -> dict:
    """Releases every submitted milestone whose auto_release_at has passed on
    an active contract. Callable from the hourly scheduler loop in main.py
    (not wired by workstream D — main.py gains one include_router line only)
    and from POST /v1/contracts/jobs/auto-release in development. Each
    milestone is processed in its own transaction with the client's context
    set, so RLS, notifications and review invites behave exactly as if the
    client had approved it."""
    counts = {"released": 0, "completed": 0}
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("SELECT set_config('vyapar.service_role', 'dispatcher', true)")
            due = await conn.fetch(
                """SELECT m.id AS milestone_id, c.id AS contract_id, c.client_member_id
                     FROM vyapar_contracts.contract_milestones m JOIN vyapar_contracts.contracts c ON c.id = m.contract_id
                    WHERE m.state = 'submitted' AND m.auto_release_at <= now() AND c.state = 'active'
                    ORDER BY m.auto_release_at LIMIT 200""")
    for item in due:
        try:
            async with pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute("SELECT set_config('vyapar.service_role', 'dispatcher', true)")
                    await conn.execute("SELECT set_config('vyapar.authz_context', $1, true)", item["client_member_id"])
                    contract = await conn.fetchrow("SELECT * FROM vyapar_contracts.contracts WHERE id = $1 AND state = 'active' FOR UPDATE", item["contract_id"])
                    m = await conn.fetchrow(
                        "SELECT * FROM vyapar_contracts.contract_milestones WHERE id = $1 AND state = 'submitted' AND auto_release_at <= now() FOR UPDATE",
                        item["milestone_id"])
                    if contract is None or m is None:
                        continue
                    await _release(conn, contract, m, actor=None, reason="auto_release")
                    counts["released"] += 1
                    if await _maybe_complete(conn, contract, actor=None):
                        counts["completed"] += 1
        except Exception:
            logger.exception("contract auto-release failed for milestone %s", item["milestone_id"])
    return counts

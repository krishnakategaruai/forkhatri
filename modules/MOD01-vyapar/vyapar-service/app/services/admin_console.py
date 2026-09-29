# [IMP-ADMIN] Vyapar's side of the shared Admin & Governance Console
# (ADR-012, contract TR-PLAT-01 in modules/MOD02-milavn/07-tech-reqs.md).
#
# What this is: a thin, generic adapter over Vyapar's EXISTING operator
# queues, so the platform console can render every module's queues with one
# shared list/detail/action component. It owns no tables and no business
# rules:
#   * membership of each queue comes from the existing list functions
#     (trust_safety.list_moderation_queue / list_appeals,
#     verification.list_verification_queue, admin_ops.list_opportunity_review_queue
#     / list_stale_queue, contracts.list_disputes_for_operators) — they also
#     run the existing permission chokepoints;
#   * every action is dispatched to the existing decision function
#     (decide_moderation_case, decide_appeal, approve/reject/
#     request_clearer_verification_copy, decide_opportunity_review,
#     bulk_stale_action, resolve_dispute), which keeps its own notifications,
#     outbox events and audit rows exactly as the /v1/admin routes produce them;
#   * on top of that each console action records one audit event tagged
#     `admin_action.vyapar.<view_id>` (TR-PLAT-01 §4), carrying the operator's
#     free-text notes, which the older endpoints have no field for.
#
# The five views and who sees them (manifest):
#   moderation    reported content (moderation cases, except review disputes)   vyapar.moderate -> moderation
#   verification  business/credential documents waiting for a decision         vyapar.verify   -> verification
#   opportunities opportunity review queue + stale queue                        vyapar.moderate -> content
#   appeals       appeals against moderation decisions                          vyapar.moderate -> moderation
#   disputes      contract disputes + review disputes                           vyapar.moderate -> moderation
#   commercial    boost, Business Workspace and campaign orders, their payments   vyapar.commercial -> commercial
#                 and refunds (admin_commercial.list_commercial_orders,
#                 process_refund; commercial.reject_promotion)
#
# Plus a per-member summary for the console's person page
# (GET /vyapar/admin/members/{member_id}/summary): plan, facts, flags.
#
# Item ids are opaque to the console: "<item_type>:<uuid>". Summaries and
# reasons are human words in the caller's language (en/hi/te), never ids.
# Priority: urgent (critical severity, or a job seeker asked for money),
# high (high severity, escalated or past its target time, money held in a
# disputed contract), otherwise normal. due_at comes from the existing timers:
# moderation target_due_at, appeal due_at, and the verification queue's
# "3 business days" highlight (TR047).
# Traces to: TR-PLAT-01, ADR-012, FR39-FR41, FR47, FR48, FR29, TR040, TR041, TR047, TR048
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import asyncpg
from pydantic import BaseModel, ConfigDict, Field

from app.audit import audit
from app.errors import ApiError
from app.i18n import translate
from app.identity import AuthzContext, operator_permissions
from app.integrations.identity.admin_scopes import SCOPE_COMMERCIAL, SCOPE_MODERATE, SCOPE_VERIFY
from app.services import admin_commercial, admin_ops, commercial, contracts, trust_safety, verification

MODULE_ID = "vyapar"
BASE_PATH = "/vyapar/admin"
NS = "admin_console"

Priority = Literal["urgent", "high", "normal"]
PRIORITY_RANK = {"urgent": 0, "high": 1, "normal": 2}
VERIFICATION_TARGET_BUSINESS_DAYS = 3  # TR047: "highlighting rows where now() - created_at > 3 business days"
SUSPEND_DEFAULT_DAYS = 30  # the existing moderation screen's default suspension length


# ---------------------------------------------------------------------------
# Contract models (TR-PLAT-01 §1-§3)
# ---------------------------------------------------------------------------
class AdminViewDescriptor(BaseModel):
    view_id: str
    title: str = Field(description="Localized view title")
    nav_group: Literal["moderation", "disputes", "policy", "commercial"]
    required_permission_scope: str = Field(description="The host admin scope that opens this view, e.g. vyapar.moderate")
    list_endpoint: str = Field(description="Relative to the API base URL")
    detail_endpoint: str = Field(description="Relative to the API base URL; {item_id} is filled by the console")
    action_endpoints: list[str] = Field(description="Relative to the API base URL; {item_id} and {action_id} are filled by the console")


class AdminManifestOut(BaseModel):
    module_id: Literal["vyapar"] = MODULE_ID
    views: list[AdminViewDescriptor]


class AdminQueueItem(BaseModel):
    item_id: str = Field(description="Opaque id: <item_type>:<uuid>")
    module_id: Literal["vyapar"] = MODULE_ID
    item_type: Literal[
        "moderation_case", "verification_record", "opportunity_review", "stale_opportunity",
        "appeal", "contract_dispute", "review_dispute", "promotion_order", "plan_order", "campaign_order",
    ]
    item_type_label: str
    submitted_at: datetime
    priority: Priority
    status: str = Field(description="Stable state code, e.g. open, escalated, pending")
    status_label: str
    summary_text: str = Field(description="One sentence in the caller's language; never raw ids")
    subject_title: str
    reason: str | None = Field(default=None, description="Why the item is in the queue, in words")
    due_at: datetime | None = None
    overdue: bool = False
    deep_link: str | None = Field(default=None, description="Web-app path of the thing under review, when it has one")


class AdminHistoryEntry(BaseModel):
    action: str = Field(description="Stable code of what happened")
    label: str = Field(description="What happened, in the caller's language")
    by: str = Field(description="Who did it, by name (a reporter is never named)")
    notes: str | None = None
    at: datetime


class AdminCaseDetail(BaseModel):
    """Module-defined, opaque to the console, except `history`."""

    model_config = ConfigDict(extra="allow")
    history: list[AdminHistoryEntry]


class AdminAvailableAction(BaseModel):
    action_id: str
    label: str
    requires_reason: bool
    reason_codes: list[str] | None = None
    reason_labels: dict[str, str] | None = Field(default=None, description="reason_code -> label in the caller's language")


class AdminItemDetailOut(BaseModel):
    item_id: str
    item: AdminQueueItem
    case_detail: AdminCaseDetail
    available_actions: list[AdminAvailableAction]


class AdminActionIn(BaseModel):
    notes: str | None = Field(default=None, max_length=2000)
    reason_code: str | None = Field(default=None, max_length=60)
    duration_days: int | None = Field(default=None, ge=1, le=365, description="Only for the moderation 'suspend' action; default 30")
    amount_paise: int | None = Field(default=None, gt=0, description="Only for the commercial 'refund' action; default = everything not yet refunded")


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ViewSpec:
    view_id: str
    nav_group: str
    scope: str        # host scope, shown in the manifest
    permission: str   # Vyapar operator permission the scope maps to
    item_types: tuple[str, ...]


VIEWS: tuple[ViewSpec, ...] = (
    ViewSpec("moderation", "moderation", SCOPE_MODERATE, "moderation", ("moderation_case",)),
    ViewSpec("verification", "moderation", SCOPE_VERIFY, "verification", ("verification_record",)),
    ViewSpec("opportunities", "moderation", SCOPE_MODERATE, "content", ("opportunity_review", "stale_opportunity")),
    ViewSpec("appeals", "moderation", SCOPE_MODERATE, "moderation", ("appeal",)),
    ViewSpec("disputes", "disputes", SCOPE_MODERATE, "moderation", ("contract_dispute", "review_dispute")),
    ViewSpec("commercial", "commercial", SCOPE_COMMERCIAL, "commercial", ("promotion_order", "plan_order", "campaign_order")),
)
VIEW_BY_ID = {v.view_id: v for v in VIEWS}

# Reason codes offered per action. Moderation/appeal/review codes are the
# trust_safety.reasonCode catalogue the affected member's notification is
# written from; verification codes are the ones the listing's rejected state
# reads back; opportunity codes are stored as the post's state_reason.
VIOLATION_REASONS = [
    "scam_confirmed", "asked_for_money", "fake_listing", "impersonation", "harassment", "discrimination",
    "spam", "stale_info", "privacy_violation", "policy_other",
]
REVIEW_VIOLATION_REASONS = ["harassment", "discrimination", "privacy_violation", "spam", "policy_other"]
VERIFICATION_REASONS = ["document_illegible", "document_expired", "name_mismatch", "document_type_mismatch", "suspected_fraud", "other"]
OPPORTUNITY_RETURN_REASONS = ["missing_details", "unclear_pay", "source_unreachable", "other"]
OPPORTUNITY_REMOVE_REASONS = ["seeker_charge", "prohibited_content", "duplicate", "source_unreachable", "other"]
# The existing commercial screen's refund reasons (trust_safety.reasonCode catalogue).
REFUND_REASONS = ["scam_confirmed", "policy_other", "no_violation", "appeal_evidence_accepted"]
ORDER_TABLE = {"promotion_order": "promotions", "plan_order": "entitlements", "campaign_order": "campaigns"}
ORDER_KIND = {"promotion_order": "promotion", "plan_order": "entitlement", "campaign_order": "campaign"}
REJECTABLE_PROMOTION_STATES = ("awaiting_payment", "scheduled", "active", "paused")  # migration 006 reject_promotion()

OBJECT_LINK = {"listing": "/listings/{id}", "opportunity": "/opportunities/{id}", "enquiry": "/enquiries/{id}", "partnership": "/partnerships/{id}"}
OPEN_CASE_STATES = ("open", "in_review", "escalated")


# ---------------------------------------------------------------------------
# Request-scoped helpers
# ---------------------------------------------------------------------------
class _Req:
    def __init__(self, conn: asyncpg.Connection, ctx: AuthzContext, lang: str) -> None:
        self.conn, self.ctx, self.lang = conn, ctx, lang
        self._names: dict[str, str] = {}

    def t(self, key: str, **params: Any) -> str:
        return translate(f"{NS}.{key}", self.lang, **params)

    def label(self, group: str, code: str | None) -> str:
        if not code:
            return self.t("label.none")
        key = f"{NS}.{group}.{code}"
        text = translate(key, self.lang)
        return code.replace("_", " ") if text == key else text

    async def names(self, *ids: str | None) -> None:
        missing = [i for i in {i for i in ids if i} if i not in self._names]
        if missing:
            # Operators read member rows through the members_self_or_operator
            # RLS policy (is_operator(NULL)); nobody else reaches this code.
            rows = await self.conn.fetch("SELECT id, display_name FROM vyapar_identity.members WHERE id = ANY($1::text[])", missing)
            self._names.update({r["id"]: r["display_name"] for r in rows})

    def name(self, member_id: str | None) -> str:
        if not member_id:
            return self.t("actor.system")
        return self._names.get(member_id) or self.t("actor.unknown")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _add_business_days(start: datetime, days: int) -> datetime:
    current, added = start, 0
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5:
            added += 1
    return current


def _excerpt(text: str | None, limit: int = 140) -> str | None:
    if not text:
        return None
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _make_id(item_type: str, raw_id: Any) -> str:
    return f"{item_type}:{raw_id}"


def _parse_id(view: ViewSpec, item_id: str, lang: str) -> tuple[str, str]:
    item_type, _, raw = item_id.partition(":")
    try:
        if item_type not in view.item_types:
            raise ValueError
        return item_type, str(uuid.UUID(raw))
    except ValueError:
        raise ApiError(404, f"{NS}.error.itemNotFound", lang)


async def _require_view(r: _Req, view: ViewSpec) -> None:
    if view.permission not in await operator_permissions(r.conn, r.ctx):
        raise ApiError(403, f"{NS}.error.permissionRequired", r.lang)


def _view(view_id: str, lang: str) -> ViewSpec:
    view = VIEW_BY_ID.get(view_id)
    if view is None:
        raise ApiError(404, f"{NS}.error.itemNotFound", lang)
    return view


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------
def view_descriptor(view: ViewSpec, lang: str) -> AdminViewDescriptor:
    base = f"{BASE_PATH}/{view.view_id}"
    return AdminViewDescriptor(
        view_id=view.view_id,
        title=translate(f"{NS}.view.{view.view_id}", lang),
        nav_group=view.nav_group,  # type: ignore[arg-type]
        required_permission_scope=view.scope,
        list_endpoint=base,
        detail_endpoint=f"{base}/{{item_id}}",
        action_endpoints=[f"{base}/{{item_id}}/actions/{{action_id}}"],
    )


async def get_manifest(conn: asyncpg.Connection, ctx: AuthzContext, lang: str) -> AdminManifestOut:
    granted = await operator_permissions(conn, ctx)
    views = [view_descriptor(v, lang) for v in VIEWS if v.permission in granted]
    if not views:
        raise ApiError(403, f"{NS}.error.permissionRequired", lang)
    return AdminManifestOut(views=views)


# ---------------------------------------------------------------------------
# Row loaders (by id, any state — the queue functions decide membership)
# ---------------------------------------------------------------------------
async def _case_rows(conn: asyncpg.Connection, ids: list[str]) -> dict[str, asyncpg.Record]:
    rows = await conn.fetch("SELECT * FROM vyapar_trust_safety.moderation_cases WHERE id = ANY($1::uuid[])", ids)
    return {str(r["id"]): r for r in rows}


async def _verification_rows(conn: asyncpg.Connection, ids: list[str]) -> dict[str, asyncpg.Record]:
    rows = await conn.fetch(
        """SELECT v.*, l.name AS listing_name, l.owner_id AS listing_owner
             FROM vyapar_listings.verification_records v LEFT JOIN vyapar_listings.listings l ON l.id = v.listing_id
            WHERE v.id = ANY($1::uuid[])""",
        ids,
    )
    return {str(r["id"]): r for r in rows}


async def _opportunity_rows(conn: asyncpg.Connection, ids: list[str]) -> dict[str, asyncpg.Record]:
    rows = await conn.fetch("SELECT * FROM vyapar_opportunities.opportunities WHERE id = ANY($1::uuid[])", ids)
    return {str(r["id"]): r for r in rows}


async def _appeal_rows(conn: asyncpg.Connection, ids: list[str]) -> dict[str, asyncpg.Record]:
    rows = await conn.fetch(
        """SELECT a.*, c.object_kind, c.object_id, c.subject_member_id, c.action AS case_action,
                  c.reason_code AS case_reason_code, c.primary_reason AS case_primary_reason,
                  c.operator_id AS case_operator_id, c.decided_at AS case_decided_at
             FROM vyapar_trust_safety.appeals a JOIN vyapar_trust_safety.moderation_cases c ON c.id = a.case_id
            WHERE a.id = ANY($1::uuid[])""",
        ids,
    )
    return {str(r["id"]): r for r in rows}


async def _dispute_rows(conn: asyncpg.Connection, ids: list[str]) -> dict[str, asyncpg.Record]:
    rows = await conn.fetch(
        """SELECT d.*, c.title AS contract_title, c.state AS contract_state, c.client_member_id, c.provider_member_id,
                  c.total_paise, c.currency,
                  (SELECT coalesce(sum(CASE WHEN l.entry = 'held' THEN l.amount_paise ELSE -l.amount_paise END), 0)
                     FROM vyapar_contracts.contract_ledger l WHERE l.contract_id = c.id) AS held_paise
             FROM vyapar_contracts.contract_disputes d JOIN vyapar_contracts.contracts c ON c.id = d.contract_id
            WHERE d.id = ANY($1::uuid[])""",
        ids,
    )
    return {str(r["id"]): r for r in rows}


async def _order_rows(conn: asyncpg.Connection, item_type: str, ids: list[str]) -> dict[str, asyncpg.Record]:
    table = ORDER_TABLE[item_type]
    rows = await conn.fetch(
        f"""SELECT o.*, p.name AS product_name,
                   po.id AS po_id, po.state AS payment_state, po.amount_paise AS po_amount, po.tax_paise AS po_tax,
                   po.refund_paise AS po_refund,
                   (SELECT a.action FROM vyapar_integration.audit_events a
                     WHERE a.object_kind = 'payment_order' AND a.object_id = po.id::text AND a.action LIKE 'refund%'
                     ORDER BY a.at DESC, a.id DESC LIMIT 1) AS last_refund_action
              FROM vyapar_commercial.{table} o
              LEFT JOIN vyapar_commercial.products p ON p.id = o.product_id AND p.version = o.product_version
              LEFT JOIN vyapar_payments.payment_orders po ON po.id = o.payment_order_id
             WHERE o.id = ANY($1::uuid[])""",
        ids,
    )
    return {str(r["id"]): r for r in rows}


# ---------------------------------------------------------------------------
# Item builders
# ---------------------------------------------------------------------------
def _case_priority(case: asyncpg.Record, report_reasons: list[str]) -> Priority:
    if case["severity"] == "critical" or case["primary_reason"] == "asked_for_money" or "asked_for_money" in report_reasons:
        return "urgent"
    if case["severity"] == "high" or case["state"] == "escalated" or case["target_due_at"] < _now():
        return "high"
    return "normal"


async def _case_item(r: _Req, case: asyncpg.Record) -> AdminQueueItem:
    kind, object_id = case["object_kind"], case["object_id"]
    is_review_dispute = case["source"] == "review_dispute"
    item_type = "review_dispute" if is_review_dispute else "moderation_case"
    report_reasons = [x["reason"] for x in await r.conn.fetch("SELECT reason FROM vyapar_trust_safety.reports WHERE case_id = $1", case["id"])]
    title = await trust_safety._object_title(r.conn, kind, object_id)
    kind_label = r.label("objectKind", kind)
    reason = r.label("primaryReason", case["primary_reason"])
    link_tpl = OBJECT_LINK.get(kind)
    deep_link = link_tpl.format(id=object_id) if link_tpl else None

    if is_review_dispute:
        review = await r.conn.fetchrow(
            "SELECT author_id, subject_member_id, subject_listing_id, comment FROM vyapar_reviews.reviews WHERE id = $1", object_id
        )
        author = review["author_id"] if review else case["subject_member_id"]
        disputer = review["subject_member_id"] if review else None
        await r.names(author, disputer)
        subject_title = _excerpt(review["comment"] if review else None, 80) or r.t("subject.untitled", kind=kind_label, name=r.name(author))
        summary = r.t("summary.reviewDispute", subject=r.name(disputer), author=r.name(author), reason=reason)
        if review and review["subject_listing_id"]:
            deep_link = f"/listings/{review['subject_listing_id']}"
    else:
        await r.names(case["subject_member_id"])
        subject_title = title or r.t("subject.untitled", kind=kind_label, name=r.name(case["subject_member_id"]))
        if case["source"] == "auto_flag":
            summary = r.t("summary.autoFlagged", kind=kind_label, title=subject_title, reason=reason)
        else:
            summary = r.t("summary.reported", kind=kind_label, title=subject_title, count=max(case["reporter_count"], len(report_reasons), 1), reason=reason)

    return AdminQueueItem(
        item_id=_make_id(item_type, case["id"]), item_type=item_type, item_type_label=r.label("itemType", item_type),
        submitted_at=case["created_at"], priority=_case_priority(case, report_reasons),
        status=case["state"], status_label=r.label("status", case["state"]),
        summary_text=summary, subject_title=subject_title, reason=reason,
        due_at=case["target_due_at"], overdue=case["state"] in OPEN_CASE_STATES and case["target_due_at"] < _now(),
        deep_link=deep_link,
    )


def _document_label(r: _Req, row: asyncpg.Record) -> str:
    if row["document_type"] == "credential":
        return r.t("document.credential", name=row["credential_name"] or "", issuer=row["issuer"] or "")
    return r.label("document", row["document_type"])


async def _verification_item(r: _Req, row: asyncpg.Record) -> AdminQueueItem:
    await r.names(row["member_id"])
    due = _add_business_days(row["created_at"], VERIFICATION_TARGET_BUSINESS_DAYS) if row["state"] == "pending" else None
    overdue = bool(due and due < _now())
    listing = row["listing_name"] or r.label("objectKind", "listing")
    document = _document_label(r, row)
    return AdminQueueItem(
        item_id=_make_id("verification_record", row["id"]), item_type="verification_record",
        item_type_label=r.label("itemType", "verification_record"),
        submitted_at=row["created_at"], priority="high" if overdue else "normal",
        status=row["state"], status_label=r.label("status", row["state"]),
        summary_text=r.t("summary.verification", owner=r.name(row["member_id"]), document=document, listing=listing),
        subject_title=listing,
        reason=r.label("reasonCode", row["reason_code"]) if row["reason_code"] else document,
        due_at=due, overdue=overdue, deep_link=f"/listings/{row['listing_id']}",
    )


def _opportunity_flags(row: asyncpg.Record) -> list[str]:
    return [f for f, on in (("source_unreachable", row["source_unreachable"]), ("unconfirmed_fields", bool(row["unconfirmed_fields"]))) if on]


async def _opportunity_item(r: _Req, row: asyncpg.Record, item_type: str) -> AdminQueueItem:
    await r.names(row["poster_id"])
    poster, title = r.name(row["poster_id"]), row["title"]
    if item_type == "stale_opportunity":
        if row["published_at"]:
            days = (_now() - row["published_at"]).days
            summary = r.t("summary.stale", title=title, poster=poster, days=days)
        else:
            summary = r.t("summary.staleNeverPublished", title=title, poster=poster)
        reason = r.label("status", "stale")
    else:
        flags = _opportunity_flags(row)
        if flags:
            joined = "; ".join(r.label("flag", f) for f in flags)
            summary = r.t("summary.opportunityFlagged", title=title, poster=poster, flags=joined)
            reason = joined
        else:
            summary = r.t("summary.opportunityReview", title=title, poster=poster)
            reason = r.label("status", "pending_review")
    return AdminQueueItem(
        item_id=_make_id(item_type, row["id"]), item_type=item_type, item_type_label=r.label("itemType", item_type),
        submitted_at=row["created_at"], priority="normal",
        status=row["state"], status_label=r.label("status", row["state"]),
        summary_text=summary, subject_title=title, reason=reason, due_at=None, overdue=False,
        deep_link=f"/opportunities/{row['id']}",
    )


async def _appeal_item(r: _Req, row: asyncpg.Record) -> AdminQueueItem:
    await r.names(row["member_id"], row["subject_member_id"])
    kind_label = r.label("objectKind", row["object_kind"])
    title = await trust_safety._object_title(r.conn, row["object_kind"], row["object_id"])
    title = title or r.t("subject.untitled", kind=kind_label, name=r.name(row["subject_member_id"]))
    decision = translate(f"trust_safety.action.{row['case_action']}", r.lang) if row["case_action"] else r.t("label.none")
    open_state = row["state"] in ("open", "delayed")
    overdue = open_state and row["due_at"] < _now()
    link_tpl = OBJECT_LINK.get(row["object_kind"])
    return AdminQueueItem(
        item_id=_make_id("appeal", row["id"]), item_type="appeal", item_type_label=r.label("itemType", "appeal"),
        submitted_at=row["created_at"], priority="high" if (overdue or row["state"] == "delayed") else "normal",
        status=row["state"], status_label=r.label("status", row["state"]),
        summary_text=r.t("summary.appeal", member=r.name(row["member_id"]), action=decision, kind=kind_label.lower() if r.lang == "en" else kind_label, title=title),
        subject_title=title,
        reason=r.label("reasonCode", row["case_reason_code"]) if row["case_reason_code"] else r.label("primaryReason", row["case_primary_reason"]),
        due_at=row["due_at"], overdue=overdue,
        deep_link=link_tpl.format(id=row["object_id"]) if link_tpl else None,
    )


async def _dispute_item(r: _Req, row: asyncpg.Record) -> AdminQueueItem:
    await r.names(row["client_member_id"], row["provider_member_id"], row["opened_by"])
    other = row["provider_member_id"] if row["opened_by"] == row["client_member_id"] else row["client_member_id"]
    held = max(int(row["held_paise"] or 0), 0)
    return AdminQueueItem(
        item_id=_make_id("contract_dispute", row["id"]), item_type="contract_dispute",
        item_type_label=r.label("itemType", "contract_dispute"),
        submitted_at=row["created_at"],
        # Money held in the contract is frozen for the worker until this is decided.
        priority="high" if (row["state"] == "open" and held > 0) else "normal",
        status=row["state"], status_label=r.label("status", row["state"]),
        summary_text=r.t("summary.contractDispute", opener=r.name(row["opened_by"]), title=row["contract_title"], other=r.name(other)),
        subject_title=r.t("subject.contract", title=row["contract_title"]),
        reason=_excerpt(row["reason"]), due_at=None, overdue=False,
        deep_link=f"/contracts/{row['contract_id']}",
    )


def _order_amounts(row: asyncpg.Record) -> tuple[int, int, int]:
    """(charged, refunded, remaining) in paise; before payment, the order's price."""
    if row["po_amount"] is not None:
        charged = int(row["po_amount"]) + int(row["po_tax"])
    else:
        base = row["budget_paise"] if "budget_paise" in row.keys() else row["price_paise"]
        charged = int(base or 0) + int(row["tax_paise"] or 0)
    refunded = int(row["po_refund"] or 0)
    return charged, refunded, max(charged - refunded, 0)


def _order_status_label(r: _Req, state: str) -> str:
    """An order's 'draft' is not an opportunity's 'returned to the poster'."""
    key = f"{NS}.orderStatus.{state}"
    text = translate(key, r.lang)
    return r.label("status", state) if text == key else text


def _product_label(r: _Req, row: asyncpg.Record) -> str:
    key = f"{NS}.product.{row['product_id']}"
    text = translate(key, r.lang)
    if text == key:
        return row["product_name"] or row["product_id"]
    return text


async def _order_item(r: _Req, row: asyncpg.Record, item_type: str) -> AdminQueueItem:
    await r.names(row["owner_id"])
    owner, product = r.name(row["owner_id"]), _product_label(r, row)
    charged, refunded, _ = _order_amounts(row)
    amount = contracts._inr(charged)
    paid = row["payment_state"] in ("succeeded", "refunded")
    if item_type == "promotion_order":
        target = await trust_safety._object_title(r.conn, row["target_kind"], row["target_id"]) or r.label("objectKind", row["target_kind"])
        subject = target
        summary = r.t("summary.promotionOrder", owner=owner, product=product, target=target, amount=amount)
        deep_link = f"/promotions/{row['id']}"
    elif item_type == "plan_order":
        listing = await r.conn.fetchval("SELECT name FROM vyapar_listings.listings WHERE id::text = $1", row["listing_id"])
        listing = listing or r.label("objectKind", "listing")
        subject = listing
        summary = r.t("summary.planOrder", owner=owner, product=product, listing=listing, amount=amount)
        deep_link = f"/workspace/{row['listing_id']}"
    else:
        subject = row["name"]
        summary = r.t("summary.campaignOrder", owner=owner, product=product, name=row["name"], amount=amount)
        deep_link = f"/campaigns/{row['id']}"
    if not paid:
        summary = r.t("summary.unpaidOrder", owner=owner, product=product)
    if refunded:
        summary = f"{summary} {r.t('summary.refundedPart', amount=contracts._inr(refunded))}"
    refund_failed = row["last_refund_action"] == "refund_failed"
    reason = r.t("payment.refundFailed") if refund_failed else r.label("payment", row["payment_state"] or "none")
    status = row["state"]
    status_label = _order_status_label(r, status)
    if item_type == "plan_order" and status == "active" and row["cancel_at_period_end"]:
        status_label = r.label("status", "cancelling")
    return AdminQueueItem(
        item_id=_make_id(item_type, row["id"]), item_type=item_type, item_type_label=r.label("itemType", item_type),
        submitted_at=row["created_at"], priority="high" if refund_failed else "normal",
        status=status, status_label=status_label, summary_text=summary, subject_title=subject, reason=reason,
        due_at=None, overdue=False, deep_link=deep_link,
    )


async def _build(r: _Req, item_type: str, raw_id: str) -> tuple[AdminQueueItem, asyncpg.Record] | None:
    if item_type in ("moderation_case", "review_dispute"):
        row = (await _case_rows(r.conn, [raw_id])).get(raw_id)
        if row is None or (row["source"] == "review_dispute") != (item_type == "review_dispute"):
            return None
        return await _case_item(r, row), row
    if item_type == "verification_record":
        row = (await _verification_rows(r.conn, [raw_id])).get(raw_id)
        return None if row is None else (await _verification_item(r, row), row)
    if item_type in ("opportunity_review", "stale_opportunity"):
        row = (await _opportunity_rows(r.conn, [raw_id])).get(raw_id)
        return None if row is None else (await _opportunity_item(r, row, item_type), row)
    if item_type == "appeal":
        row = (await _appeal_rows(r.conn, [raw_id])).get(raw_id)
        return None if row is None else (await _appeal_item(r, row), row)
    if item_type == "contract_dispute":
        row = (await _dispute_rows(r.conn, [raw_id])).get(raw_id)
        return None if row is None else (await _dispute_item(r, row), row)
    if item_type in ORDER_TABLE:
        row = (await _order_rows(r.conn, item_type, [raw_id])).get(raw_id)
        return None if row is None else (await _order_item(r, row, item_type), row)
    return None


def _sorted(items: list[AdminQueueItem], *, newest_first: bool = False) -> list[AdminQueueItem]:
    far = datetime.max.replace(tzinfo=timezone.utc)
    if newest_first:  # a ledger (orders) reads newest first; work queues oldest first
        return sorted(items, key=lambda i: (PRIORITY_RANK[i.priority], -i.submitted_at.timestamp()))
    return sorted(items, key=lambda i: (PRIORITY_RANK[i.priority], i.due_at or far, i.submitted_at))


# ---------------------------------------------------------------------------
# Lists — membership from the existing queue functions
# ---------------------------------------------------------------------------
async def list_items(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, view_id: str) -> list[AdminQueueItem]:
    r = _Req(conn, ctx, lang)
    view = _view(view_id, lang)
    await _require_view(r, view)
    items: list[AdminQueueItem] = []

    if view.view_id == "moderation":
        cases = [c for c in await trust_safety.list_moderation_queue(conn, ctx, lang) if c.source != "review_dispute"]
        rows = await _case_rows(conn, [c.id for c in cases])
        items = [await _case_item(r, rows[c.id]) for c in cases if c.id in rows]
    elif view.view_id == "verification":
        queue = await verification.list_verification_queue(conn, ctx, lang)
        rows = await _verification_rows(conn, [v.id for v in queue])
        items = [await _verification_item(r, rows[v.id]) for v in queue if v.id in rows]
    elif view.view_id == "opportunities":
        review = await admin_ops.list_opportunity_review_queue(conn, ctx, lang)
        stale = await admin_ops.list_stale_queue(conn, ctx, lang)
        rows = await _opportunity_rows(conn, [o.id for o in review] + [o.id for o in stale])
        items = [await _opportunity_item(r, rows[o.id], "opportunity_review") for o in review if o.id in rows]
        items += [await _opportunity_item(r, rows[o.id], "stale_opportunity") for o in stale if o.id in rows]
    elif view.view_id == "appeals":
        appeals = await trust_safety.list_appeals(conn, ctx, lang)
        rows = await _appeal_rows(conn, [a.id for a in appeals])
        items = [await _appeal_item(r, rows[a.id]) for a in appeals if a.id in rows]
    elif view.view_id == "disputes":
        disputes = await contracts.list_disputes_for_operators(conn, ctx, lang, state="open", limit=200)
        rows = await _dispute_rows(conn, [d.id for d in disputes])
        items = [await _dispute_item(r, rows[d.id]) for d in disputes if d.id in rows]
        cases = [c for c in await trust_safety.list_moderation_queue(conn, ctx, lang) if c.source == "review_dispute"]
        case_rows = await _case_rows(conn, [c.id for c in cases])
        items += [await _case_item(r, case_rows[c.id]) for c in cases if c.id in case_rows]
    elif view.view_id == "commercial":
        for item_type, kind in ORDER_KIND.items():
            orders = await admin_commercial.list_commercial_orders(conn, ctx, lang, kind=kind, limit=50)
            rows = await _order_rows(conn, item_type, [o.id for o in orders])
            items += [await _order_item(r, rows[o.id], item_type) for o in orders if o.id in rows]
        return _sorted(items, newest_first=True)
    return _sorted(items)


# ---------------------------------------------------------------------------
# Available actions (state-dependent; an empty list means "already decided")
# ---------------------------------------------------------------------------
def _act(r: _Req, group: str, action_id: str, reasons: list[str] | None) -> AdminAvailableAction:
    return AdminAvailableAction(
        action_id=action_id, label=r.t(f"action.{group}.{action_id}"), requires_reason=bool(reasons),
        reason_codes=list(reasons) if reasons else None,
        reason_labels={c: r.label("reasonCode", c) for c in reasons} if reasons else None,
    )


def _actions(r: _Req, item_type: str, row: asyncpg.Record) -> list[AdminAvailableAction]:
    if item_type == "moderation_case":
        if row["state"] not in OPEN_CASE_STATES:
            return []
        kind = row["object_kind"]
        out = [_act(r, "moderation", "dismiss", ["no_violation"])]
        if kind in ("listing", "opportunity"):
            out.append(_act(r, "moderation", "limit", VIOLATION_REASONS))
        out.append(_act(r, "moderation", "remove", VIOLATION_REASONS))
        if kind == "listing":
            out.append(_act(r, "moderation", "request_verification", VIOLATION_REASONS))
        if row["subject_member_id"]:
            out.append(_act(r, "moderation", "suspend", VIOLATION_REASONS))
        return out
    if item_type == "review_dispute":
        if row["state"] not in OPEN_CASE_STATES:
            return []
        return [
            _act(r, "review", "keep", ["no_violation"]),
            _act(r, "review", "hide", REVIEW_VIOLATION_REASONS),
            _act(r, "review", "remove", REVIEW_VIOLATION_REASONS),
        ]
    if item_type == "verification_record":
        if row["state"] != "pending":
            return []
        return [
            _act(r, "verification", "verify", None),
            _act(r, "verification", "reject", VERIFICATION_REASONS),
            _act(r, "verification", "needs_clearer_copy", VERIFICATION_REASONS),
        ]
    if item_type == "opportunity_review":
        # In the queue = the review queue's own rule (admin_ops): pending review,
        # or flagged (source unreachable / details the poster has not confirmed).
        state = row["state"]
        if state in ("removed", "expired", "closed") or not (state == "pending_review" or _opportunity_flags(row)):
            return []
        out = []
        if state in ("pending_review", "draft"):  # the transitions decide_opportunity_review allows for approve
            out.append(_act(r, "opportunity", "approve", None))
        out += [
            _act(r, "opportunity", "return", OPPORTUNITY_RETURN_REASONS),
            _act(r, "opportunity", "remove", OPPORTUNITY_REMOVE_REASONS),
        ]
        return out
    if item_type == "stale_opportunity":
        old = row["published_at"] is None or row["published_at"] < _now() - timedelta(days=21)
        if row["state"] in ("stale", "active") and old:
            return [_act(r, "stale", "remind", None), _act(r, "stale", "expire", None)]
        return []
    if item_type == "appeal":
        if row["state"] not in ("open", "delayed"):
            return []
        return [
            _act(r, "appeal", "upheld", VIOLATION_REASONS),
            _act(r, "appeal", "overturned", ["appeal_evidence_accepted", "no_violation"]),
        ]
    if item_type == "contract_dispute":
        if row["state"] != "open" or row["contract_state"] != "disputed":
            return []
        return [_act(r, "contract", a, None) for a in ("resolved_client", "resolved_provider", "closed")]
    if item_type in ORDER_TABLE:
        out = []
        if item_type == "promotion_order" and row["state"] in REJECTABLE_PROMOTION_STATES:
            out.append(_act(r, "commercial", "reject", VIOLATION_REASONS))
        if row["payment_state"] in ("succeeded", "refunded") and _order_amounts(row)[2] > 0:
            out.append(_act(r, "commercial", "refund", REFUND_REASONS))
        return out
    return []


# ---------------------------------------------------------------------------
# History and case detail
# ---------------------------------------------------------------------------
async def _console_history(r: _Req, item_type: str, raw_id: str, *, extra_kinds: tuple[tuple[str, str], ...] = ()) -> list[AdminHistoryEntry]:
    """Console actions (admin_action.vyapar.*) on this item, plus the audit
    rows the older admin endpoints write for the same object. A service row
    written in the same transaction as a console row is the same decision,
    so it is shown once."""
    targets = [(item_type, raw_id), *extra_kinds]
    rows = await r.conn.fetch(
        """SELECT actor_id, object_kind, action, reason_code, details, at FROM vyapar_integration.audit_events
            WHERE (object_kind, object_id) IN (SELECT * FROM unnest($1::text[], $2::text[])) ORDER BY at, id""",
        [k for k, _ in targets], [i for _, i in targets],
    )
    await r.names(*[x["actor_id"] for x in rows])
    console_at = {x["at"] for x in rows if x["action"].startswith("admin_action.")}
    out: list[AdminHistoryEntry] = []
    for x in rows:
        details = x["details"] if isinstance(x["details"], dict) else _json(x["details"])
        if x["action"].startswith("admin_action."):
            group = ACTION_GROUP.get(x["object_kind"])
            action_label = r.t(f"action.{group}.{details.get('action_id')}") if group and details.get("action_id") else ""
            label = r.t("history.consoleAction", action=action_label)
            if x["reason_code"]:
                label = f"{label} — {r.label('reasonCode', x['reason_code'])}"
            out.append(AdminHistoryEntry(action=x["action"], label=label, by=r.name(x["actor_id"]), notes=details.get("notes"), at=x["at"]))
        elif x["action"] in ("refund_processed", "refund_failed", "refund_rejected"):
            if x["action"] == "refund_processed":
                label = r.t("history.refundProcessed", amount=contracts._inr(int(details.get("amount_paise") or 0)))
            else:
                label = r.t("history.refundFailed" if x["action"] == "refund_failed" else "history.refundRejected")
            out.append(AdminHistoryEntry(action=x["action"], label=label, by=r.name(x["actor_id"]),
                                         notes=r.label("reasonCode", x["reason_code"]) if x["reason_code"] else None, at=x["at"]))
        elif x["action"].startswith("opportunity_queue_") and x["at"] not in console_at:
            code = x["action"].removeprefix("opportunity_queue_")
            out.append(AdminHistoryEntry(
                action=x["action"], label=r.t("history.auditAction", action=r.t(f"action.opportunity.{code}")),
                by=r.name(x["actor_id"]), notes=r.label("reasonCode", x["reason_code"]) if x["reason_code"] else None, at=x["at"],
            ))
    return out


def _json(value: Any) -> dict:
    import json

    try:
        parsed = json.loads(value) if isinstance(value, str) else dict(value or {})
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _by_time(entries: list[AdminHistoryEntry]) -> list[AdminHistoryEntry]:
    return sorted(entries, key=lambda e: e.at)


async def _case_detail(r: _Req, item_type: str, row: asyncpg.Record) -> AdminCaseDetail:
    conn = r.conn
    history: list[AdminHistoryEntry] = []
    evidence = await conn.fetch(
        "SELECT reason, evidence_text, evidence_urls, created_at FROM vyapar_trust_safety.reports WHERE case_id = $1 ORDER BY created_at", row["id"]
    )
    history.append(AdminHistoryEntry(action="case_opened", label=r.t("history.caseOpened"), by=r.t("actor.system"), at=row["created_at"]))
    if row["source"] == "auto_flag":
        history.append(AdminHistoryEntry(
            action="auto_flagged", label=r.t("history.autoFlagged", reason=r.label("primaryReason", row["primary_reason"])),
            by=r.t("actor.system"), at=row["created_at"],
        ))
    for e in evidence:
        history.append(AdminHistoryEntry(
            action="reported", label=r.t("history.reported", reason=r.label("primaryReason", e["reason"])),
            by=r.t("actor.reporter"), notes=e["evidence_text"], at=e["created_at"],
        ))
    review = None
    if row["source"] == "review_dispute":
        review = await conn.fetchrow("SELECT * FROM vyapar_reviews.reviews WHERE id = $1", row["object_id"])
        dispute = await conn.fetchrow("SELECT * FROM vyapar_reviews.review_disputes WHERE case_id = $1", row["id"])
        if review:
            await r.names(review["author_id"], review["subject_member_id"])
            history.append(AdminHistoryEntry(action="review_written", label=r.t("history.reviewWritten"), by=r.name(review["author_id"]),
                                             notes=review["comment"], at=review["created_at"]))
        if dispute:
            await r.names(dispute["disputer_id"])
            history.append(AdminHistoryEntry(action="dispute_opened", label=r.t("history.disputeOpened"), by=r.name(dispute["disputer_id"]),
                                             notes=r.label("primaryReason", dispute["reason"]), at=dispute["created_at"]))
    if row["decided_at"]:
        await r.names(row["operator_id"])
        history.append(AdminHistoryEntry(
            action=f"decided_{row['action']}", label=r.t("history.decided", action=translate(f"trust_safety.action.{row['action']}", r.lang)),
            by=r.name(row["operator_id"]), notes=r.label("reasonCode", row["reason_code"]) if row["reason_code"] else None, at=row["decided_at"],
        ))
    history += await _console_history(r, item_type, str(row["id"]))

    prior = await conn.fetch(
        """SELECT action, reason_code, primary_reason, state, decided_at, created_at FROM vyapar_trust_safety.moderation_cases
            WHERE object_id = $1 AND id <> $2 ORDER BY created_at DESC""",
        row["object_id"], row["id"],
    )
    await r.names(row["subject_member_id"])
    extra: dict[str, Any] = {
        "object_kind": row["object_kind"],
        "object_kind_label": r.label("objectKind", row["object_kind"]),
        "object_title": await trust_safety._object_title(conn, row["object_kind"], row["object_id"]),
        "about_member": r.name(row["subject_member_id"]),
        "severity": row["severity"],
        "source": row["source"],
        "reporter_count": row["reporter_count"],
        "distribution_limited": row["distribution_limited"],
        "evidence": [
            {"reason": e["reason"], "reason_label": r.label("primaryReason", e["reason"]), "text": e["evidence_text"],
             "attachments": list(e["evidence_urls"] or []), "at": e["created_at"]}
            for e in evidence
        ],
        "prior_cases": [
            {"decision": translate(f"trust_safety.action.{p['action']}", r.lang) if p["action"] else r.label("status", p["state"]),
             "reason": r.label("reasonCode", p["reason_code"]) if p["reason_code"] else r.label("primaryReason", p["primary_reason"]),
             "at": p["decided_at"] or p["created_at"]}
            for p in prior
        ],
    }
    if review is not None:
        extra["review"] = {
            "recommend": review["recommend"], "tags": list(review["tags"] or []), "comment": review["comment"],
            "author": r.name(review["author_id"]), "about": r.name(review["subject_member_id"]), "state": review["state"],
        }
    return AdminCaseDetail(history=_by_time(history), **extra)


async def _verification_detail(r: _Req, row: asyncpg.Record) -> AdminCaseDetail:
    await r.names(row["member_id"], row["verifier_id"])
    history = [AdminHistoryEntry(action="submitted", label=r.t("history.submitted"), by=r.name(row["member_id"]),
                                 notes=_document_label(r, row), at=row["created_at"])]
    if row["decided_at"]:
        history.append(AdminHistoryEntry(
            action=f"verification_{row['state']}", label=r.t("history.verificationDecided", state=r.label("status", row["state"])),
            by=r.name(row["verifier_id"]), notes=r.label("reasonCode", row["reason_code"]) if row["reason_code"] else None, at=row["decided_at"],
        ))
    history += await _console_history(r, "verification_record", str(row["id"]))
    return AdminCaseDetail(
        history=_by_time(history),
        listing_name=row["listing_name"],
        owner=r.name(row["member_id"]),
        kind=row["kind"],
        document_type=row["document_type"],
        document_label=_document_label(r, row),
        identifier_masked=row["identifier_masked"],  # the encrypted identifier is never returned
        image_url=row["image_url"],
        credential_name=row["credential_name"],
        issuer=row["issuer"],
        days_pending=(_now() - row["created_at"]).days if row["state"] == "pending" else 0,
    )


async def _opportunity_detail(r: _Req, item_type: str, row: asyncpg.Record) -> AdminCaseDetail:
    await r.names(row["poster_id"])
    history = [AdminHistoryEntry(action="posted", label=r.t("history.posted"), by=r.name(row["poster_id"]), at=row["created_at"])]
    if row["published_at"]:
        history.append(AdminHistoryEntry(action="published", label=r.t("history.published"), by=r.name(row["poster_id"]), at=row["published_at"]))
    history += await _console_history(r, item_type, str(row["id"]), extra_kinds=(("opportunity", str(row["id"])),))
    return AdminCaseDetail(
        history=_by_time(history),
        title=row["title"],
        type=row["type"],
        description=_excerpt(row["description"], 600),
        poster=r.name(row["poster_id"]),
        location=row["location"],
        flags=[{"code": f, "label": r.label("flag", f)} for f in _opportunity_flags(row)],
        published_at=row["published_at"],
        days_since_published=(_now() - row["published_at"]).days if row["published_at"] else None,
    )


async def _appeal_detail(r: _Req, row: asyncpg.Record) -> AdminCaseDetail:
    await r.names(row["member_id"], row["case_operator_id"], row["reviewer_id"])
    history: list[AdminHistoryEntry] = []
    if row["case_decided_at"]:
        history.append(AdminHistoryEntry(
            action=f"decided_{row['case_action']}",
            label=r.t("history.decided", action=translate(f"trust_safety.action.{row['case_action']}", r.lang)),
            by=r.name(row["case_operator_id"]), notes=r.label("reasonCode", row["case_reason_code"]) if row["case_reason_code"] else None,
            at=row["case_decided_at"],
        ))
    history.append(AdminHistoryEntry(action="appeal_filed", label=r.t("history.appealFiled"), by=r.name(row["member_id"]), notes=row["text"], at=row["created_at"]))
    if row["decided_at"]:
        history.append(AdminHistoryEntry(
            action=f"appeal_{row['state']}", label=r.t("history.appealDecided", state=r.label("status", row["state"])),
            by=r.name(row["reviewer_id"]), notes=r.label("reasonCode", row["reason_code"]) if row["reason_code"] else None, at=row["decided_at"],
        ))
    history += await _console_history(r, "appeal", str(row["id"]))
    title = await trust_safety._object_title(r.conn, row["object_kind"], row["object_id"])
    return AdminCaseDetail(
        history=_by_time(history),
        appeal_text=row["text"],
        attachments=list(row["evidence_urls"] or []),
        appellant=r.name(row["member_id"]),
        object_kind=row["object_kind"],
        object_kind_label=r.label("objectKind", row["object_kind"]),
        object_title=title,
        original_decision=translate(f"trust_safety.action.{row['case_action']}", r.lang) if row["case_action"] else None,
        original_reason=r.label("reasonCode", row["case_reason_code"]) if row["case_reason_code"] else None,
    )


async def _dispute_detail(r: _Req, row: asyncpg.Record) -> AdminCaseDetail:
    await r.names(row["opened_by"], row["resolved_by"], row["client_member_id"], row["provider_member_id"])
    history = [AdminHistoryEntry(action="dispute_opened", label=r.t("history.disputeOpened"), by=r.name(row["opened_by"]), notes=row["reason"], at=row["created_at"])]
    if row["resolved_at"]:
        history.append(AdminHistoryEntry(
            action=f"dispute_{row['state']}", label=r.t("history.disputeResolved", state=r.label("status", row["state"])),
            by=r.name(row["resolved_by"]), notes=row["notes"], at=row["resolved_at"],
        ))
    history += await _console_history(r, "contract_dispute", str(row["id"]))
    milestone = None
    if row["milestone_id"]:
        milestone = await r.conn.fetchval("SELECT title FROM vyapar_contracts.contract_milestones WHERE id = $1", row["milestone_id"])
    held = max(int(row["held_paise"] or 0), 0)
    return AdminCaseDetail(
        history=_by_time(history),
        contract_title=row["contract_title"],
        contract_state=row["contract_state"],
        client=r.name(row["client_member_id"]),
        provider=r.name(row["provider_member_id"]),
        opened_by=r.name(row["opened_by"]),
        dispute_reason=row["reason"],
        milestone_title=milestone,
        contract_total=contracts._inr(int(row["total_paise"] or 0)),
        held_amount=contracts._inr(held),
        held_paise=held,
    )


async def _order_detail(r: _Req, item_type: str, row: asyncpg.Record) -> AdminCaseDetail:
    await r.names(row["owner_id"])
    history = [AdminHistoryEntry(action="order_placed", label=r.t("history.orderPlaced"), by=r.name(row["owner_id"]), at=row["created_at"])]
    if item_type in ("promotion_order", "plan_order"):
        changes = await r.conn.fetch(
            "SELECT from_state, to_state, reason, at FROM vyapar_commercial.commercial_order_history WHERE order_kind = $1 AND order_id = $2 ORDER BY at, id",
            ORDER_KIND[item_type], row["id"],
        )
        for c in changes:
            history.append(AdminHistoryEntry(
                action=f"state_{c['to_state']}", label=r.t("history.orderState", state=_order_status_label(r, c["to_state"])),
                by=r.t("actor.system"), at=c["at"],
            ))
    extra = (("payment_order", str(row["po_id"])),) if row["po_id"] else ()
    history += await _console_history(r, item_type, str(row["id"]), extra_kinds=extra)
    charged, refunded, remaining = _order_amounts(row)
    detail: dict[str, Any] = {
        "product": _product_label(r, row),
        "owner": r.name(row["owner_id"]),
        "state": row["state"],
        "payment": r.label("payment", row["payment_state"] or "none"),
        "charged": contracts._inr(charged), "refunded": contracts._inr(refunded), "refundable": contracts._inr(remaining),
        "charged_paise": charged, "refunded_paise": refunded, "refundable_paise": remaining,
        "starts_at": row["starts_at"],
        "ends_at": row["ends_at"] if "ends_at" in row.keys() else row["renews_at"],
    }
    if item_type == "promotion_order":
        detail["boosted"] = await trust_safety._object_title(r.conn, row["target_kind"], row["target_id"])
        detail["reject_reason"] = r.label("reasonCode", row["reject_reason"]) if row["reject_reason"] else None
    return AdminCaseDetail(history=_by_time(history), **detail)


async def _detail_for(r: _Req, item_type: str, row: asyncpg.Record) -> AdminCaseDetail:
    if item_type in ("moderation_case", "review_dispute"):
        return await _case_detail(r, item_type, row)
    if item_type == "verification_record":
        return await _verification_detail(r, row)
    if item_type in ("opportunity_review", "stale_opportunity"):
        return await _opportunity_detail(r, item_type, row)
    if item_type == "appeal":
        return await _appeal_detail(r, row)
    if item_type in ORDER_TABLE:
        return await _order_detail(r, item_type, row)
    return await _dispute_detail(r, row)


async def get_item(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, view_id: str, item_id: str) -> AdminItemDetailOut:
    r = _Req(conn, ctx, lang)
    view = _view(view_id, lang)
    await _require_view(r, view)
    item_type, raw_id = _parse_id(view, item_id, lang)
    built = await _build(r, item_type, raw_id)
    if built is None:
        raise ApiError(404, f"{NS}.error.itemNotFound", lang)
    item, row = built
    return AdminItemDetailOut(
        item_id=item.item_id, item=item, case_detail=await _detail_for(r, item_type, row), available_actions=_actions(r, item_type, row),
    )


# ---------------------------------------------------------------------------
# Actions — each one dispatched to the existing decision function
# ---------------------------------------------------------------------------
ACTION_GROUP = {
    "moderation_case": "moderation", "review_dispute": "review", "verification_record": "verification",
    "opportunity_review": "opportunity", "stale_opportunity": "stale", "appeal": "appeal", "contract_dispute": "contract",
    "promotion_order": "commercial", "plan_order": "commercial", "campaign_order": "commercial",
}
REVIEW_ACTION_TO_MODERATION = {"keep": "dismiss", "hide": "limit", "remove": "remove"}


async def _dispatch(r: _Req, item_type: str, raw_id: str, row: asyncpg.Record, action_id: str, body: AdminActionIn) -> None:
    conn, ctx, lang = r.conn, r.ctx, r.lang
    if item_type in ("moderation_case", "review_dispute"):
        action = REVIEW_ACTION_TO_MODERATION[action_id] if item_type == "review_dispute" else action_id
        duration = (body.duration_days or SUSPEND_DEFAULT_DAYS) if action == "suspend" else None
        await trust_safety.decide_moderation_case(
            conn, ctx, lang, case_id=raw_id,
            body=trust_safety.DecideIn(action=action, reason_code=body.reason_code, duration_days=duration),
        )
    elif item_type == "verification_record":
        decision = verification.DecisionIn(reason_code=body.reason_code)
        fn = {
            "verify": verification.approve_verification,
            "reject": verification.reject_verification,
            "needs_clearer_copy": verification.request_clearer_verification_copy,
        }[action_id]
        await fn(conn, ctx, lang, record_id=raw_id, body=decision)
    elif item_type == "opportunity_review":
        await admin_ops.decide_opportunity_review(
            conn, ctx, lang, opportunity_id=raw_id, body=admin_ops.QueueDecisionIn(action=action_id, reason=body.reason_code),
        )
    elif item_type == "stale_opportunity":
        await admin_ops.bulk_stale_action(conn, ctx, lang, body=admin_ops.BulkStaleIn(action=action_id, ids=[raw_id], confirm_count=1))
    elif item_type == "appeal":
        await trust_safety.decide_appeal(
            conn, ctx, lang, appeal_id=raw_id, body=trust_safety.AppealDecisionIn(decision=action_id, reason_code=body.reason_code),
        )
    elif item_type == "contract_dispute":
        await contracts.resolve_dispute(
            conn, ctx, lang, contract_id=str(row["contract_id"]), dispute_id=raw_id,
            body=contracts.DisputeResolveIn(outcome=action_id, notes=body.notes),
        )
    elif item_type in ORDER_TABLE and action_id == "reject":
        await commercial.reject_promotion(conn, ctx, lang, promotion_id=raw_id, body=commercial.RejectIn(reason_code=body.reason_code))
    elif item_type in ORDER_TABLE and action_id == "refund":
        await admin_commercial.process_refund(
            conn, ctx, lang,
            body=admin_commercial.RefundIn(
                payment_order_id=str(row["po_id"]), amount_paise=body.amount_paise or _order_amounts(row)[2], reason_code=body.reason_code,
            ),
        )


async def act_on_item(
    conn: asyncpg.Connection, ctx: AuthzContext, lang: str, view_id: str, item_id: str, action_id: str, body: AdminActionIn,
) -> AdminQueueItem:
    r = _Req(conn, ctx, lang)
    view = _view(view_id, lang)
    await _require_view(r, view)
    item_type, raw_id = _parse_id(view, item_id, lang)
    built = await _build(r, item_type, raw_id)
    if built is None:
        raise ApiError(404, f"{NS}.error.itemNotFound", lang)
    _, row = built
    available = {a.action_id: a for a in _actions(r, item_type, row)}
    chosen = available.get(action_id)
    if chosen is None:
        raise ApiError(409, f"{NS}.error.actionNotAvailable", lang)
    if chosen.requires_reason and not body.reason_code:
        raise ApiError(422, f"{NS}.error.reasonRequired", lang)
    if body.reason_code and chosen.reason_codes is not None and body.reason_code not in chosen.reason_codes:
        raise ApiError(422, f"{NS}.error.reasonNotAllowed", lang)
    if chosen.reason_codes is None:
        body = body.model_copy(update={"reason_code": None})

    await _dispatch(r, item_type, raw_id, row, action_id, body)
    # TR-PLAT-01 §4: one audit event per console action, from the owning module.
    await audit(
        conn, actor_id=ctx.member_id, action=f"admin_action.{MODULE_ID}.{view.view_id}", object_kind=item_type, object_id=raw_id,
        reason_code=body.reason_code,
        details={
            "action_id": action_id, "notes": body.notes, "via": "admin_console", "auth_method": ctx.auth_method,
            "permission_source": "session" if view.permission in ctx.session_permissions else "member",
        },
    )
    rebuilt = await _build(_Req(conn, ctx, lang), item_type, raw_id)
    if rebuilt is None:  # e.g. the record was removed as part of the decision
        raise ApiError(404, f"{NS}.error.itemNotFound", lang)
    return rebuilt[0]



# ---------------------------------------------------------------------------
# Member summary — the console's person page asks every module "what does
# this person have with you?". Facts respect the caller's permissions (RLS):
# an operator with only `verification` sees the counts that permission reaches.
# ---------------------------------------------------------------------------
class MemberPlanOut(BaseModel):
    tier: str = Field(description="Product id of the Business Workspace plan, e.g. workspace_monthly")
    name: str
    status: str = Field(description="active | paused | cancelling")
    renews_at: datetime | None = None


class MemberFactOut(BaseModel):
    label: str
    value: str


class MemberFlagOut(BaseModel):
    code: str
    label: str


class MemberSummaryOut(BaseModel):
    module_id: Literal["vyapar"] = MODULE_ID
    plan: MemberPlanOut | None
    facts: list[MemberFactOut]
    flags: list[MemberFlagOut]
    deep_link: str | None = None


def _date(value: datetime) -> str:
    return value.strftime("%d/%m/%Y")  # Indian day/month/year order


MEMBER_STATS_SQL = """
SELECT
  (SELECT count(*) FROM vyapar_listings.listings WHERE owner_id = $1 AND state IN ('active_unverified','active_verified')) AS listings,
  (SELECT count(*) FROM vyapar_listings.listings WHERE owner_id = $1 AND verification_state IN ('verified','expiring')) AS verified,
  (SELECT count(*) FROM vyapar_listings.listings WHERE owner_id = $1 AND verification_state = 'pending') AS pending,
  (SELECT count(*) FROM vyapar_listings.listings WHERE owner_id = $1 AND verification_state = 'rejected') AS rejected,
  (SELECT count(*) FROM vyapar_opportunities.opportunities WHERE poster_id = $1 AND state = 'active') AS open_opportunities,
  (SELECT count(*) FROM vyapar_commercial.promotions WHERE owner_id = $1 AND state IN ('active','scheduled')) AS boosts,
  (SELECT count(*) FROM vyapar_commercial.campaigns WHERE owner_id = $1 AND state = 'active') AS campaigns,
  (SELECT count(*) FROM vyapar_contracts.contracts
    WHERE (client_member_id = $1 OR provider_member_id = $1) AND state IN ('active','disputed')) AS contracts,
  (SELECT count(*) FROM vyapar_contracts.contracts
    WHERE (client_member_id = $1 OR provider_member_id = $1) AND state = 'disputed') AS disputed,
  (SELECT count(*) FROM vyapar_trust_safety.moderation_cases
    WHERE subject_member_id = $1 AND state IN ('open','in_review','escalated')) AS open_reports,
  (SELECT count(*) FROM vyapar_trust_safety.appeals WHERE member_id = $1 AND state IN ('open','delayed')) AS appeals,
  (SELECT count(*) FROM vyapar_listings.listings WHERE owner_id = $1 AND state = 'suspended')
    + (SELECT count(*) FROM vyapar_opportunities.opportunities
        WHERE poster_id = $1 AND state_reason LIKE 'account_suspended:%') AS suspended,
  (SELECT coalesce(sum(amount_paise + tax_paise - refund_paise), 0) FROM vyapar_payments.payment_orders
    WHERE member_id = $1 AND state IN ('succeeded','refunded')) AS paid,
  (SELECT count(*) FROM vyapar_payments.payment_orders
    WHERE member_id = $1 AND state = 'failed' AND created_at > now() - interval '30 days') AS failed_payments
"""


async def get_member_summary(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, member_id: str) -> MemberSummaryOut:
    r = _Req(conn, ctx, lang)
    granted = await operator_permissions(conn, ctx)
    if not granted:
        raise ApiError(403, f"{NS}.error.permissionRequired", lang)
    member = await conn.fetchrow(
        "SELECT id, created_at, is_operator FROM vyapar_identity.members WHERE id = $1 AND deleted_at IS NULL", member_id
    )
    if member is None:
        raise ApiError(404, f"{NS}.error.itemNotFound", lang)

    plan_row = await conn.fetchrow(
        """SELECT e.*, p.name AS product_name FROM vyapar_commercial.entitlements e
             LEFT JOIN vyapar_commercial.products p ON p.id = e.product_id AND p.version = e.product_version
            WHERE e.owner_id = $1 AND e.state IN ('active','paused') ORDER BY e.created_at DESC LIMIT 1""",
        member_id,
    )
    plan = None
    if plan_row is not None:
        status = "cancelling" if plan_row["state"] == "active" and plan_row["cancel_at_period_end"] else plan_row["state"]
        plan = MemberPlanOut(tier=plan_row["product_id"], name=_product_label(r, plan_row), status=status, renews_at=plan_row["renews_at"])

    stats = await conn.fetchrow(MEMBER_STATS_SQL, member_id)

    def fact(key: str, value: Any) -> MemberFactOut:
        return MemberFactOut(label=r.t(f"member.fact.{key}"), value=str(value))

    facts = [fact("memberSince", _date(member["created_at"]))]
    facts.append(fact("listings", stats["listings"] if stats["listings"] else r.t("member.value.noListing")))
    if stats["listings"] or stats["pending"] or stats["verified"]:
        facts.append(fact("verification", r.t("member.value.verification", verified=stats["verified"], pending=stats["pending"])))
    facts += [
        fact("openOpportunities", stats["open_opportunities"]),
        fact("activeBoosts", stats["boosts"]),
        fact("campaigns", stats["campaigns"]),
        fact("contracts", stats["contracts"]),
    ]
    if "moderation" in granted:
        facts.append(fact("openReports", stats["open_reports"]))
    if "commercial" in granted:
        facts.append(fact("totalPaid", contracts._inr(int(stats["paid"] or 0))))

    flags: list[MemberFlagOut] = []

    def flag(code: str) -> None:
        flags.append(MemberFlagOut(code=code, label=r.t(f"member.flag.{code}")))

    if stats["open_reports"]:
        flag("open_reports")
    if stats["suspended"]:
        flag("content_suspended")
    if stats["appeals"]:
        flag("appeal_open")
    if stats["pending"]:
        flag("verification_pending")
    if stats["rejected"]:
        flag("verification_rejected")
    if plan is not None and plan.status == "paused":
        flag("plan_paused")
    if plan is not None and plan.status == "cancelling":
        flag("plan_ending")
    if stats["failed_payments"]:
        flag("payment_failed")
    if stats["disputed"]:
        flag("contract_disputed")
    if member["is_operator"]:
        flag("operator")
    return MemberSummaryOut(plan=plan, facts=facts, flags=flags, deep_link=None)

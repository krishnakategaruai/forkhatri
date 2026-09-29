"""ForKhatri shared Admin & Governance Console adapter (ADR-012, TR-PLAT-01).

The platform console (entrance /admin, gateway in identity-service) reads
every module through the same three shapes: a manifest of views, a queue of
items, and item detail with actions. For Mangaly the one view is the
moderation case queue. These routes are thin wrappers over the existing
`/operations/cases` logic: no new tables, the same `Moderator` chokepoint
(which also admits the platform's `mangaly.moderate` admin scope), and every
action still audited in the same transaction by `operations`.
"""

from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.api.deps import DbSession, Locale
from app.api.operator_deps import Moderator
from app.api.routes import operations as ops_routes
from app.components.operations import interface as operations
from app.i18n import translate

router = APIRouter(prefix="/mangaly/admin", tags=["admin"])

MODULE_ID = "mangaly"
ACTIONS: tuple[str, ...] = ("acknowledge", "resolve", "suspend", "lift_suspension", "reopen")


class AdminView(BaseModel):
    view_id: str
    title: str
    nav_group: str
    required_permission_scope: str
    list_endpoint: str
    detail_endpoint: str
    action_endpoints: list[str]


class AdminManifest(BaseModel):
    module_id: str
    views: list[AdminView]


class AdminQueueItem(BaseModel):
    item_id: str
    module_id: str
    item_type: str
    submitted_at: str
    priority: Literal["urgent", "high", "normal"]
    status: str
    summary_text: str
    subject_title: str
    reason: str
    due_at: str | None = None


class AdminItemDetail(BaseModel):
    item_id: str
    case_detail: dict[str, Any]
    available_actions: list[str]


class ActionBody(BaseModel):
    notes: str | None = Field(default=None, max_length=4000)
    reason_code: str | None = Field(default=None, max_length=64)


@router.get("/manifest", response_model=AdminManifest)
async def manifest(lang: Locale) -> AdminManifest:
    """Public shape only; the list/detail/action routes enforce access."""
    return AdminManifest(
        module_id=MODULE_ID,
        views=[
            AdminView(
                view_id="cases",
                title=translate("safety.admin.casesTitle", lang),
                nav_group="moderation",
                required_permission_scope="mangaly.moderate",
                list_endpoint="/mangaly/admin/moderation",
                detail_endpoint="/mangaly/admin/moderation/{item_id}",
                action_endpoints=["/mangaly/admin/moderation/{item_id}/actions/{action_id}"],
            )
        ],
    )


def _category(summary: operations.CaseSummary, lang: str) -> str:
    key = f"safety.admin.category.{summary.category}"
    text_ = translate(key, lang)
    return summary.category.replace("_", " ").capitalize() if text_ == key else text_


def _priority(summary: operations.CaseSummary) -> Literal["urgent", "high", "normal"]:
    # Tier 4 is the child-safety tier; a missed deadline is urgent too.
    if summary.tier >= 4 or summary.sla_breached:
        return "urgent"
    if summary.tier == 3:
        return "high"
    return "normal"


def _item(summary: operations.CaseSummary, lang: str) -> AdminQueueItem:
    who = summary.reported_name or translate("safety.admin.someone", lang)
    category = _category(summary, lang)
    due = summary.acknowledge_by if summary.state == "open" else summary.resolve_by
    return AdminQueueItem(
        item_id=str(summary.case_id),
        module_id=MODULE_ID,
        item_type="moderation_case",
        submitted_at=summary.created_at.isoformat(),
        priority=_priority(summary),
        status=summary.state,
        summary_text=translate("safety.admin.summary", lang, category=category, name=who),
        subject_title=who,
        reason=category,
        due_at=due.isoformat() if due and summary.state != "resolved" else None,
    )


def _available(summary: operations.CaseSummary) -> list[str]:
    if summary.state == "open":
        out = ["acknowledge", "resolve"]
    elif summary.state == "acknowledged":
        out = ["resolve"]
    else:
        out = ["reopen"]
    if summary.reported_account_id and summary.state != "resolved":
        out.append("lift_suspension" if summary.reported_suspended else "suspend")
    elif summary.reported_account_id and summary.reported_suspended:
        out.append("lift_suspension")
    return out


@router.get("/moderation", response_model=list[AdminQueueItem])
async def queue(session: DbSession, operator: Moderator, lang: Locale) -> list[AdminQueueItem]:
    cases = await operations.list_cases(session, state=None, tier=None)
    order = {"urgent": 0, "high": 1, "normal": 2}
    items = [_item(c, lang) for c in cases]
    items.sort(key=lambda i: (i.status == "resolved", order[i.priority], i.submitted_at))
    return items


async def _load(session: DbSession, item_id: UUID) -> operations.CaseDetail:
    detail = await operations.get_case(session, item_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return detail


@router.get("/moderation/{item_id}", response_model=AdminItemDetail)
async def detail(item_id: UUID, session: DbSession, operator: Moderator, lang: Locale) -> AdminItemDetail:
    loaded = await _load(session, item_id)
    full = ops_routes._to_detail(loaded).model_dump()
    full["history"] = [
        {"action": d.action, "by": str(d.operator_account_id), "notes": d.note, "at": d.at.isoformat()}
        for d in loaded.decisions
    ]
    full["summary_text"] = _item(loaded.summary, lang).summary_text
    sm = loaded.summary

    def f(key: str) -> str:
        return translate(f"safety.admin.field.{key}", lang)

    fields = [
        {"label": f("reason"), "value": _category(sm, lang)},
        {"label": f("about"), "value": sm.reported_name or translate("safety.admin.someone", lang)},
        {"label": f("state"), "value": translate(f"safety.admin.state.{sm.state}", lang)},
        {"label": f("priority"), "value": translate(f"safety.admin.priority.{_priority(sm)}", lang)},
        {"label": f("reported"), "value": _day(sm.created_at)},
    ]
    if sm.description:
        fields.append({"label": f("description"), "value": sm.description})
    due = sm.acknowledge_by if sm.state == "open" else sm.resolve_by
    if due and sm.state != "resolved":
        fields.append({"label": f("due"), "value": _day(due)})
    if sm.outcome:
        fields.append({"label": f("outcome"), "value": translate(f"safety.admin.outcome.{sm.outcome}", lang)})
    if sm.reported_suspended:
        fields.append({"label": f("account"), "value": translate("safety.admin.suspended", lang)})
    full["fields"] = fields
    return AdminItemDetail(item_id=str(item_id), case_detail=full, available_actions=_available(loaded.summary))


@router.post("/moderation/{item_id}/actions/{action_id}", response_model=AdminQueueItem)
async def act(
    item_id: UUID, action_id: str, body: ActionBody, session: DbSession, operator: Moderator, lang: Locale
) -> AdminQueueItem:
    if action_id not in ACTIONS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown action")
    loaded = await _load(session, item_id)
    if action_id not in _available(loaded.summary):
        raise ops_routes._not_changed(lang)
    note = body.notes
    try:
        if action_id == "acknowledge":
            await operations.acknowledge(session, case_id=item_id, operator_account_id=operator.account_id)
        elif action_id == "resolve":
            outcome = body.reason_code or "no_action"
            if outcome == "account_suspended":
                action_id = "suspend"
            else:
                await operations.resolve(
                    session, case_id=item_id, operator_account_id=operator.account_id, outcome=outcome, note=note
                )
        if action_id == "suspend":
            if loaded.summary.reported_account_id is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
            await operations.suspend_reported_account(
                session,
                case_id=item_id,
                reported_account_id=loaded.summary.reported_account_id,
                operator_account_id=operator.account_id,
                reason=note,
            )
        elif action_id == "lift_suspension":
            if loaded.summary.reported_account_id is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
            await operations.lift_suspension(
                session,
                case_id=item_id,
                account_id=loaded.summary.reported_account_id,
                operator_account_id=operator.account_id,
            )
        elif action_id == "reopen":
            await operations.reopen(session, case_id=item_id, operator_account_id=operator.account_id, note=note)
    except operations.InvalidOutcome as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=translate("safety.ops.error.invalidOutcome", lang),
        ) from exc
    except operations.NotChanged as exc:
        raise ops_routes._not_changed(lang) from exc
    return _item((await _load(session, item_id)).summary, lang)


# ---------------------------------------------------------------------------
# [ADR-012] One member's Mangaly facts for the console's member page. Mangaly's
# own plan tier sits beside other modules' tiers there, never merged.
# ---------------------------------------------------------------------------


class MemberPlan(BaseModel):
    tier: str
    name: str
    status: str
    status_label: str
    renews_at: str | None


def _day(value) -> str:
    """Indian day-month order, language-neutral digits: 28/09/2026."""
    return value.strftime("%d/%m/%Y")


class MemberFact(BaseModel):
    label: str
    value: str


class MemberSummary(BaseModel):
    plan: MemberPlan | None
    facts: list[MemberFact]
    flags: list[str]
    deep_link: str | None = None


@router.get("/members/{member_id}/summary", response_model=MemberSummary)
async def member_summary(member_id: UUID, session: DbSession, operator: Moderator, lang: Locale) -> MemberSummary:
    """`member_id` is the platform member id, which equals Mangaly's account id
    by construction (TR10/TR23). 404 when they have no Mangaly account."""
    row = (
        await session.execute(
            text("SELECT * FROM mangaly_operations.admin_member_summary(:id)"), {"id": member_id}
        )
    ).mappings().one_or_none()
    if row is None or not row["has_account"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    def tr(key: str, **params: object) -> str:
        return translate(f"safety.admin.member.{key}", lang, **params)

    cases = [c for c in await operations.list_cases(session, state=None, tier=None) if c.reported_account_id == member_id]
    open_cases = sum(1 for c in cases if c.state != "resolved")

    code = row["plan_code"] or "FREE"
    plan = MemberPlan(
        tier=code.lower(),
        name=translate(f"billing.plan.{code}.name", lang),
        status="cancelled" if row["plan_cancelled_at"] else "active",
        status_label=tr("planCancelled") if row["plan_cancelled_at"] else tr("planActive"),
        renews_at=row["plan_ends_at"].isoformat() if row["plan_ends_at"] and row["plan_auto_renew"] else None,
    )
    facts = [
        MemberFact(label=tr("profile"), value=tr("searchable") if row["searchable"] else tr("notSearchable")),
        MemberFact(label=tr("reports"), value=tr("reportsValue", open=open_cases, total=len(cases))),
        MemberFact(label=tr("blocks"), value=tr("blocksValue", made=row["blocks_made"], by=row["blocked_by"])),
    ]
    if row["plan_ends_at"]:
        facts.append(MemberFact(label=tr("planEnds"), value=_day(row["plan_ends_at"])))
    if row["rm_name"]:
        facts.append(MemberFact(label=tr("rm"), value=row["rm_name"]))
    if row["last_order_status"]:
        facts.append(
            MemberFact(
                label=tr("lastOrder"),
                value=tr(
                    "lastOrderValue",
                    plan=translate(f"billing.plan.{row['last_order_plan']}.name", lang),
                    total=f"₹{row['last_order_total'] / 100:,.2f}",
                    status=tr(f"order.{row['last_order_status']}"),
                    date=_day(row["last_order_at"]),
                ),
            )
        )
    flags = []
    if row["suspended"]:
        flags.append("suspended_in_module")
    if open_cases:
        flags.append("open_reports")
    return MemberSummary(plan=plan, facts=facts, flags=flags)

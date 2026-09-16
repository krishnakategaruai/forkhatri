# [TR039] Report and block intake (FR39). [TR040] Moderation queue and
# graduated actions (FR40). [TR041] Appeals and outcome communication (FR41).
# Approach: every member-side write goes through migration 004's narrow
# SECURITY DEFINER functions (the live RLS makes moderation_cases operator-
# only, so a plain INSERT from a member session is structurally impossible —
# see that migration's header). The reported party (`subject_member_id`) is
# always resolved server-side from the object itself, never from the client.
# Reporter identity never appears in anything the reported party can read:
# `my_outcomes()` has no reporter column at all. Operator routes check the
# 'moderation' permission first (this router is the chokepoint for these
# paths), every action needs a reason code, evidence has no edit route, and
# every decision notifies the affected party with the appeal path and the
# grievance contact (FR53). Reference check (Upwork + WorkIndia lens): Upwork
# flags in place from the profile/job/message with a reason list and reviews
# reports confidentially ("the person you flag will not be notified") —
# followed here; WorkIndia routes reports to an email inbox — Vyapar does it
# in-app in one sheet instead.
# Traces to: FR39, FR40, FR41, FR53, TR039, TR040, TR041, SP039, SP040, SP041
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Literal

import asyncpg
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from app.db import get_conn
from app.deps import Locale
from app.i18n import translate
from app.identity import AuthzContext, resolve_authz_context
from app.notifications import send_notification
from app.routers.verification import revoke_verification

router = APIRouter(tags=["trust-safety"])
admin_router = APIRouter(prefix="/v1/admin", tags=["admin-moderation"])

REPORTS_PER_DAY = 10  # [TR039] RateLimit-CC
GRIEVANCE_CONTACT = "grievance@forkhatri.example"  # the seeded FR53 privacy notice's own grievance channel
SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
# [FR29] moderation action -> the review's resulting state, as told to both parties
REVIEW_OUTCOME = {"limit": "hidden", "remove": "removed", "dismiss": "published", "restore": "published"}

ObjectKind = Literal["listing", "opportunity", "enquiry", "partnership", "review"]
ReportReason = Literal["scam", "fake", "impersonation", "harassment", "discrimination", "spam", "stale", "privacy", "other"]
Action = Literal["limit", "remove", "restore", "request_verification", "suspend", "dismiss"]


async def _subject_of(conn: asyncpg.Connection, kind: str, object_id: str, caller: str) -> str | None:
    """The reported party, resolved from the object itself (never client input)."""
    if kind == "listing":
        return await conn.fetchval("SELECT owner_id FROM vyapar_listings.listings WHERE id = $1", object_id)
    if kind == "opportunity":
        return await conn.fetchval("SELECT poster_id FROM vyapar_opportunities.opportunities WHERE id = $1", object_id)
    if kind == "enquiry":
        row = await conn.fetchrow("SELECT sender_id, provider_id FROM vyapar_enquiries.enquiries WHERE id = $1", object_id)
        return None if row is None else (row["provider_id"] if row["sender_id"] == caller else row["sender_id"])
    if kind == "partnership":
        row = await conn.fetchrow("SELECT sender_id, recipient_id FROM vyapar_enquiries.partnership_requests WHERE id = $1", object_id)
        return None if row is None else (row["recipient_id"] if row["sender_id"] == caller else row["sender_id"])
    if kind == "review":
        return await conn.fetchval("SELECT author_id FROM vyapar_reviews.reviews WHERE id = $1", object_id)
    return None


class ReportIn(BaseModel):
    object_kind: ObjectKind
    object_id: str
    reason: ReportReason
    evidence_text: str | None = Field(default=None, max_length=1000)


@router.post("/v1/reports", status_code=201)
async def file_report(
    body: ReportIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict:
    if idempotency_key:
        cached = await conn.fetchval(
            "SELECT response_snapshot FROM vyapar_platform.idempotency_key WHERE member_id = $1 AND idempotency_key = $2 AND endpoint = 'POST /v1/reports'",
            ctx.member_id, idempotency_key,
        )
        if cached:
            return json.loads(cached) if isinstance(cached, str) else cached

    subject = await _subject_of(conn, body.object_kind, body.object_id, ctx.member_id)
    if subject is None:
        raise HTTPException(status_code=404, detail=translate("trust_safety.error.objectNotFound", lang))
    if subject == ctx.member_id:
        raise HTTPException(status_code=400, detail=translate("trust_safety.error.cannotReportOwn", lang))

    allowed = await conn.fetchval(
        "SELECT vyapar_platform.check_and_increment($1, 86400, $2)", f"report:{ctx.member_id}:day", REPORTS_PER_DAY
    )
    if not allowed:
        raise HTTPException(status_code=429, detail=translate("trust_safety.error.dailyCapReached", lang, cap=REPORTS_PER_DAY))

    await conn.fetchrow(
        "SELECT * FROM vyapar_trust_safety.file_report($1, $2, $3, $4, $5)",
        body.object_kind, body.object_id, subject, body.reason, body.evidence_text,
    )
    # FR39 offers Block in the same flow — the reporter gets the id they can
    # block (they are already a party to / viewer of this object). Never for
    # reviews, where the author may not otherwise be shown.
    result = {"received": True, "block_member_id": None if body.object_kind == "review" else subject}

    if idempotency_key:
        await conn.execute(
            """INSERT INTO vyapar_platform.idempotency_key (idempotency_key, endpoint, member_id, request_hash, status_code, response_snapshot)
               VALUES ($1, 'POST /v1/reports', $2, '', 201, $3::jsonb)
               ON CONFLICT (member_id, idempotency_key, endpoint) DO NOTHING""",
            idempotency_key, ctx.member_id, json.dumps(result),
        )
    return result


@router.get("/v1/moderation/outcomes")
async def list_my_outcomes(
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[dict]:
    rows = await conn.fetch("SELECT * FROM vyapar_trust_safety.my_outcomes()")
    now = datetime.now(timezone.utc)
    return [
        {
            "case_id": str(r["case_id"]), "object_kind": r["object_kind"], "object_id": str(r["object_id"]),
            "action": r["action"], "reason_code": r["reason_code"], "action_duration_days": r["action_duration_days"],
            "decided_at": r["decided_at"].isoformat(), "appeal_deadline": r["appeal_deadline"].isoformat(),
            "appeal_state": r["appeal_state"],
            "can_appeal": r["appeal_state"] is None and r["action"] != "restore" and now < r["appeal_deadline"],
        }
        for r in rows
    ]


class AppealIn(BaseModel):
    case_id: str
    text: str = Field(min_length=1, max_length=1000)


@router.post("/v1/appeals", status_code=201)
async def file_appeal(
    body: AppealIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    try:
        async with conn.transaction():  # savepoint — see IMP19's transaction-abort fix
            appeal_id = await conn.fetchval("SELECT vyapar_trust_safety.file_appeal($1, $2)", body.case_id, body.text)
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=409, detail=translate("trust_safety.error.alreadyAppealed", lang))
    except asyncpg.RaiseError as exc:
        message = str(exc)
        if "window_closed" in message:
            raise HTTPException(status_code=400, detail=translate("trust_safety.error.windowClosed", lang))
        if "not_appealable" in message:
            raise HTTPException(status_code=400, detail=translate("trust_safety.error.notAppealable", lang))
        raise HTTPException(status_code=404, detail=translate("trust_safety.error.caseNotFound", lang))
    return {"appeal_id": str(appeal_id), "state": "open"}


# ---------------------------------------------------------------------------
# Operator side
# ---------------------------------------------------------------------------
async def _require_moderation(conn: asyncpg.Connection, ctx: AuthzContext, lang: str) -> None:
    perms = await conn.fetchval("SELECT operator_permissions FROM vyapar_identity.members WHERE id = $1", ctx.member_id)
    if not perms or "moderation" not in perms:
        raise HTTPException(status_code=403, detail=translate("trust_safety.error.permissionRequired", lang))


async def _object_title(conn: asyncpg.Connection, kind: str, object_id) -> str | None:
    if kind == "listing":
        return await conn.fetchval("SELECT name FROM vyapar_listings.listings WHERE id = $1", object_id)
    if kind == "opportunity":
        return await conn.fetchval("SELECT title FROM vyapar_opportunities.opportunities WHERE id = $1", object_id)
    if kind == "partnership":
        return await conn.fetchval("SELECT left(need, 80) FROM vyapar_enquiries.partnership_requests WHERE id = $1", object_id)
    if kind == "review":
        return await conn.fetchval("SELECT left(comment, 80) FROM vyapar_reviews.reviews WHERE id = $1", object_id)
    return None


async def _set_limited(conn: asyncpg.Connection, kind: str, object_id, value: bool) -> None:
    if kind == "listing":
        await conn.execute("UPDATE vyapar_listings.listings SET distribution_limited = $2, updated_at = now() WHERE id = $1", object_id, value)
    elif kind == "opportunity":
        await conn.execute("UPDATE vyapar_opportunities.opportunities SET distribution_limited = $2, updated_at = now() WHERE id = $1", object_id, value)


async def _lift_suspension(conn: asyncpg.Connection, case_id) -> int:
    """Reverses exactly what `suspend` did for this one case — only rows it
    tagged, so an unrelated suspension is never lifted by accident."""
    tag = f"account_suspended:{case_id}"
    a = await conn.execute(
        """UPDATE vyapar_listings.listings SET
             state = CASE WHEN verification_state IN ('verified','expiring') THEN 'active_verified' ELSE 'active_unverified' END,
             state_reason = NULL, updated_at = now()
           WHERE state = 'suspended' AND state_reason = $1""",
        tag,
    )
    b = await conn.execute(
        "UPDATE vyapar_opportunities.opportunities SET state = 'active', state_reason = NULL, updated_at = now() WHERE state = 'paused' AND state_reason = $1",
        tag,
    )
    return int(a.split()[-1]) + int(b.split()[-1])


async def _apply_action(conn: asyncpg.Connection, case: asyncpg.Record, action: str, reason_code: str) -> None:
    """[FR40] Six graduated actions. Restore reverses every one of the others."""
    kind, object_id, subject, case_id = case["object_kind"], case["object_id"], case["subject_member_id"], case["id"]
    if action == "limit":
        if kind == "review":
            # [FR29] "Hidden (visible to author only)"
            await conn.execute("SELECT vyapar_trust_safety.set_object_state('review', $1, 'limit')", object_id)
        else:
            await _set_limited(conn, kind, object_id, True)
    elif action == "dismiss":
        if kind == "review":
            # [FR29] dispute not upheld — the review returns to Published
            await conn.execute("SELECT vyapar_trust_safety.set_object_state('review', $1, 'restore')", object_id)
        else:
            # No violation found — the pending-review auto-limit is lifted.
            await _set_limited(conn, kind, object_id, False)
    elif action == "remove":
        if kind == "listing":
            await conn.execute("UPDATE vyapar_listings.listings SET state = 'suspended', state_reason = $2, updated_at = now() WHERE id = $1", object_id, reason_code)
        elif kind == "opportunity":
            await conn.execute("UPDATE vyapar_opportunities.opportunities SET state = 'removed', state_reason = $2, updated_at = now() WHERE id = $1", object_id, reason_code)
        else:
            if kind in ("enquiry", "partnership"):
                # [FR27] reviews tied to a removed thread are hidden with it
                # (migration 005's set_object_state cascade); authors are told why.
                authors = await conn.fetch(
                    "SELECT DISTINCT author_id FROM vyapar_reviews.reviews WHERE interaction_kind = $1 AND interaction_id = $2 AND state IN ('published','disputed')",
                    kind, object_id,
                )
                for a in authors:
                    await _notify(conn, a["author_id"], "reviewAutoHidden", f"review_auto_hidden:{kind}:{object_id}:{a['author_id']}", "/activity")
            await conn.execute("SELECT vyapar_trust_safety.set_object_state($1, $2, 'hide')", kind, object_id)
    elif action == "request_verification":
        if kind == "listing":
            # [SP010] the one shared revert call site — label shows "Under review".
            await revoke_verification(conn, object_id, reason_code, "disputed")
    elif action == "suspend" and subject:
        # [ER-model gap, recorded in IMP21] no member-level suspension column
        # exists; suspension is applied to the member's live content, tagged
        # with this case so it can be lifted exactly.
        tag = f"account_suspended:{case_id}"
        await conn.execute(
            "UPDATE vyapar_listings.listings SET state = 'suspended', state_reason = $2, updated_at = now() WHERE owner_id = $1 AND state IN ('active_unverified','active_verified')",
            subject, tag,
        )
        await conn.execute(
            "UPDATE vyapar_opportunities.opportunities SET state = 'paused', state_reason = $2, updated_at = now() WHERE poster_id = $1 AND state = 'active'",
            subject, tag,
        )
    elif action == "restore":
        await _set_limited(conn, kind, object_id, False)
        await _lift_suspension(conn, case_id)
        if kind == "listing":
            await conn.execute(
                """UPDATE vyapar_listings.listings SET
                     state = CASE WHEN state = 'suspended'
                                  THEN CASE WHEN verification_state IN ('verified','expiring') THEN 'active_verified' ELSE 'active_unverified' END
                                  ELSE state END,
                     verification_state = CASE WHEN verification_state = 'disputed'
                                  THEN CASE WHEN verified_at > now() - interval '12 months' THEN 'verified' ELSE 'not_started' END
                                  ELSE verification_state END,
                     state_reason = NULL, updated_at = now()
                   WHERE id = $1""",
                object_id,
            )
        elif kind == "opportunity":
            await conn.execute(
                "UPDATE vyapar_opportunities.opportunities SET state = 'active', state_reason = NULL, updated_at = now() WHERE id = $1 AND state = 'removed'",
                object_id,
            )
        else:
            await conn.execute("SELECT vyapar_trust_safety.set_object_state($1, $2, 'restore')", kind, object_id)


async def _notify(conn: asyncpg.Connection, member_id: str, template: str, idem: str, link: str, **params) -> None:
    member_lang = await conn.fetchval("SELECT language FROM vyapar_identity.members WHERE id = $1", member_id)
    translated = {}
    if "action" in params:
        translated["action"] = translate(f"trust_safety.action.{params['action']}", member_lang)
    if "reason" in params:
        translated["reason"] = translate(f"trust_safety.reasonCode.{params['reason']}", member_lang)
    if "outcome" in params:
        translated["outcome"] = translate(f"reviews.outcome.{params['outcome']}", member_lang)
    if "decision" in params:
        translated["decision"] = translate(f"trust_safety.appealDecision.{params['decision']}", member_lang)
    await send_notification(
        conn, member_id=member_id, kind=template, template_id=template,
        title=translate(f"notifications.{template}.title", member_lang),
        body=translate(f"notifications.{template}.body", member_lang, contact=GRIEVANCE_CONTACT, **translated),
        link=link, params={k: str(v) for k, v in params.items()}, idempotency_key=idem,
    )


@admin_router.get("/moderation-queue")
async def moderation_queue(
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[dict]:
    await _require_moderation(conn, ctx, lang)
    now = datetime.now(timezone.utc)
    cases = await conn.fetch(
        "SELECT * FROM vyapar_trust_safety.moderation_cases WHERE state IN ('open','in_review','escalated')"
    )
    out = []
    for c in cases:
        evidence = await conn.fetch(
            "SELECT reason, evidence_text, created_at FROM vyapar_trust_safety.reports WHERE case_id = $1 ORDER BY created_at", c["id"]
        )
        prior = await conn.fetchval(
            "SELECT count(*) FROM vyapar_trust_safety.moderation_cases WHERE object_id = $1 AND id <> $2", c["object_id"], c["id"]
        )
        out.append({
            "id": str(c["id"]), "object_kind": c["object_kind"], "object_id": str(c["object_id"]),
            "object_title": await _object_title(conn, c["object_kind"], c["object_id"]),
            "source": c["source"], "severity": c["severity"], "state": c["state"],
            "reporter_count": c["reporter_count"], "primary_reason": c["primary_reason"],
            "distribution_limited": c["distribution_limited"], "target_due_at": c["target_due_at"].isoformat(),
            "overdue": c["target_due_at"] < now, "prior_cases": prior,
            "evidence": [{"reason": e["reason"], "evidence_text": e["evidence_text"], "created_at": e["created_at"].isoformat()} for e in evidence],
        })
    out.sort(key=lambda x: (SEVERITY_RANK[x["severity"]], x["target_due_at"]))
    return out


class DecideIn(BaseModel):
    action: Action
    reason_code: str = Field(min_length=2, max_length=60)
    duration_days: int | None = Field(default=None, ge=1, le=365)


@admin_router.post("/moderation-cases/{case_id}/decide")
async def decide_case(
    case_id: str,
    body: DecideIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    await _require_moderation(conn, ctx, lang)
    case = await conn.fetchrow("SELECT * FROM vyapar_trust_safety.moderation_cases WHERE id = $1", case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=translate("trust_safety.error.caseNotFound", lang))
    await _apply_action(conn, case, body.action, body.reason_code)
    limited = body.action == "limit" or (case["distribution_limited"] and body.action not in ("dismiss", "restore"))
    state = "dismissed" if body.action == "dismiss" else "actioned"
    await conn.execute(
        """UPDATE vyapar_trust_safety.moderation_cases SET action = $2, reason_code = $3, action_duration_days = $4,
             operator_id = $5, decided_at = now(), state = $6, distribution_limited = $7, updated_at = now()
           WHERE id = $1""",
        case_id, body.action, body.reason_code, body.duration_days if body.action == "suspend" else None,
        ctx.member_id, state, limited,
    )
    if body.action != "dismiss" and case["subject_member_id"]:
        await _notify(
            conn, case["subject_member_id"], "moderationOutcome", f"moderation_outcome:{case_id}:{body.action}",
            "/moderation/outcomes", action=body.action, reason=body.reason_code, case_id=case_id,
        )
    if case["object_kind"] == "review":
        # [FR29] "Author and subject both notified of the outcome with reason code"
        outcome = REVIEW_OUTCOME.get(body.action, "published")
        review_subject = await conn.fetchval("SELECT subject_member_id FROM vyapar_reviews.reviews WHERE id = $1", case["object_id"])
        for member in {review_subject, case["subject_member_id"]} - {None}:
            await _notify(
                conn, member, "reviewDisputeOutcome", f"review_dispute_outcome:{case_id}:{body.action}:{member}",
                "/activity", outcome=outcome, reason=body.reason_code,
            )
    return {"state": state, "action": body.action}


@admin_router.get("/appeals")
async def list_appeals(
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[dict]:
    await _require_moderation(conn, ctx, lang)
    now = datetime.now(timezone.utc)
    rows = await conn.fetch(
        """SELECT a.id, a.case_id, a.text, a.state, a.due_at, a.created_at,
                  c.object_kind, c.object_id, c.action, c.reason_code
           FROM vyapar_trust_safety.appeals a JOIN vyapar_trust_safety.moderation_cases c ON c.id = a.case_id
           WHERE a.state IN ('open','delayed') ORDER BY a.due_at"""
    )
    return [
        {
            "id": str(r["id"]), "case_id": str(r["case_id"]), "text": r["text"], "state": r["state"],
            "due_at": r["due_at"].isoformat(), "overdue": r["due_at"] < now,
            "object_kind": r["object_kind"], "object_id": str(r["object_id"]),
            "object_title": await _object_title(conn, r["object_kind"], r["object_id"]),
            "action": r["action"], "reason_code": r["reason_code"],
        }
        for r in rows
    ]


class AppealDecisionIn(BaseModel):
    decision: Literal["upheld", "overturned"]
    reason_code: str = Field(min_length=2, max_length=60)


@admin_router.post("/appeals/{appeal_id}/decide")
async def decide_appeal(
    appeal_id: str,
    body: AppealDecisionIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    await _require_moderation(conn, ctx, lang)
    appeal = await conn.fetchrow("SELECT * FROM vyapar_trust_safety.appeals WHERE id = $1", appeal_id)
    if appeal is None:
        raise HTTPException(status_code=404, detail=translate("trust_safety.error.appealNotFound", lang))
    if body.decision == "overturned":
        case = await conn.fetchrow("SELECT * FROM vyapar_trust_safety.moderation_cases WHERE id = $1", appeal["case_id"])
        await _apply_action(conn, case, "restore", body.reason_code)
        await conn.execute(
            """UPDATE vyapar_trust_safety.moderation_cases SET action = 'restore', reason_code = $2, operator_id = $3,
                 decided_at = now(), distribution_limited = false, updated_at = now() WHERE id = $1""",
            appeal["case_id"], body.reason_code, ctx.member_id,
        )
    await conn.execute(
        "UPDATE vyapar_trust_safety.appeals SET state = $2, reviewer_id = $3, reason_code = $4, decided_at = now() WHERE id = $1",
        appeal_id, body.decision, ctx.member_id, body.reason_code,
    )
    await _notify(
        conn, appeal["member_id"], "appealDecided", f"appeal_decided:{appeal_id}", "/moderation/outcomes",
        decision=body.decision, appeal_id=appeal_id,
    )
    return {"state": body.decision}


async def run_moderation_escalation_pass(pool: asyncpg.Pool) -> dict:
    """[FR40/FR41] Missed targets escalate — never an automatic permanent
    action. Appeals past due become 'delayed' and the member is told.
    Suspensions whose duration has run are lifted exactly (tag-matched)."""
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("SELECT set_config('vyapar.service_role', 'dispatcher', true)")
            await conn.execute("SELECT set_config('vyapar.authz_context', 'm_neha_ops', true)")
            status = await conn.execute(
                "UPDATE vyapar_trust_safety.moderation_cases SET state = 'escalated', updated_at = now() WHERE state IN ('open','in_review') AND target_due_at < now()"
            )
            escalated = int(status.split()[-1])
            delayed = 0
            for a in await conn.fetch("SELECT id, member_id FROM vyapar_trust_safety.appeals WHERE state = 'open' AND due_at < now()"):
                await conn.execute("UPDATE vyapar_trust_safety.appeals SET state = 'delayed' WHERE id = $1", a["id"])
                await _notify(conn, a["member_id"], "appealDelayed", f"appeal_delayed:{a['id']}", "/moderation/outcomes", appeal_id=a["id"])
                delayed += 1
            lifted = 0
            for c in await conn.fetch(
                """SELECT id FROM vyapar_trust_safety.moderation_cases
                   WHERE action = 'suspend' AND action_duration_days IS NOT NULL
                     AND decided_at + make_interval(days => action_duration_days) < now()"""
            ):
                lifted += await _lift_suspension(conn, c["id"])
    return {"escalated": escalated, "appeals_delayed": delayed, "suspension_rows_lifted": lifted}

# [TR022] Submit an Enquiry or Opportunity Response (FR22). [TR023] Provider
# manages the Enquiry lifecycle (FR23). [TR024] Consent-based contact
# disclosure and blocking (FR24).
# Approach: `action_type` is ALWAYS resolved server-side from the target's
# own type — reusing opportunities.py's TYPE_ACTION_LABEL mapping for
# opportunity targets and a fixed 'enquire' for listing targets — never
# accepted as client input (closes the exact Spoofing risk SP022 names:
# "client-supplied action_type claiming a different action than the target
# actually supports"). The DB's own partial unique index
# (`enquiries_one_open_per_target`) is the actual 1-open-enquiry-per-target
# enforcement — this file's own pre-check is a friendlier error message on
# top of it, not the enforcement itself, closing the race condition an
# application-only check could miss. Idempotency-CC: `Idempotency-Key`
# header via the shared `vyapar_platform.idempotency_key` table.
# Traces to: FR22, FR23, FR24, TR022, TR023, TR024, SP022, SP023, SP024
from __future__ import annotations

from typing import Literal

import asyncpg
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from app.db import get_conn
from app.deps import Locale
from app.i18n import translate
from app.identity import AuthzContext, resolve_authz_context
from app.routers.opportunities import TYPE_ACTION_LABEL
from app.routers.reviews import issue_review_invites
from app.impressions import log_events

router = APIRouter(prefix="/v1/enquiries", tags=["enquiries"])

RATE_LIMIT_PER_DAY = 20


class EnquiryCreate(BaseModel):
    listing_id: str | None = None
    opportunity_id: str | None = None
    message: str = Field(min_length=20, max_length=1000)
    attachment_url: str | None = None
    sub_choice: str | None = None


class MessageIn(BaseModel):
    body: str = Field(min_length=1, max_length=1000)
    attachment_url: str | None = None


class EnquiryMessageOut(BaseModel):
    id: str
    sender_id: str
    body: str
    system_note: bool
    created_at: str


class ContactOut(BaseModel):
    channel: str
    value: str


class EnquiryOut(BaseModel):
    id: str
    sender_id: str
    provider_id: str
    is_sender: bool
    listing_id: str | None
    opportunity_id: str | None
    action_type: str
    state: str
    state_reason: str | None
    delivered: bool
    safety_notice_seen: bool
    last_activity_at: str
    created_at: str
    messages: list[EnquiryMessageOut] = []
    disclosed_contacts: list[ContactOut] = []


async def _resolve_action_type(conn: asyncpg.Connection, listing_id: str | None, opportunity_id: str | None) -> tuple[str, str | None, str | None]:
    """[SP022] Server-resolved action_type — the ONE place this mapping
    happens, never trusted from client input. Returns (action_type,
    provider_id, target_kind_error_if_any)."""
    if listing_id:
        row = await conn.fetchrow("SELECT owner_id, state, enquiry_pref FROM vyapar_listings.listings WHERE id = $1", listing_id)
        if row is None or row["state"] not in ("active_unverified", "active_verified"):
            return "", None, "target_not_active"
        if row["enquiry_pref"] == "disabled":
            return "", None, "enquiries_disabled"
        return "enquire", row["owner_id"], None
    if opportunity_id:
        row = await conn.fetchrow("SELECT poster_id, state, type FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
        if row is None or row["state"] != "active":
            return "", None, "target_not_active"
        return TYPE_ACTION_LABEL.get(row["type"], "contact"), row["poster_id"], None
    return "", None, "no_target"


def _row_to_enquiry(row: asyncpg.Record, caller_id: str) -> EnquiryOut:
    return EnquiryOut(
        id=str(row["id"]), sender_id=row["sender_id"], provider_id=row["provider_id"],
        is_sender=row["sender_id"] == caller_id,
        listing_id=str(row["listing_id"]) if row["listing_id"] else None,
        opportunity_id=str(row["opportunity_id"]) if row["opportunity_id"] else None,
        action_type=row["action_type"], state=row["state"], state_reason=row["state_reason"],
        delivered=row["delivered"], safety_notice_seen=row["safety_notice_seen"],
        last_activity_at=row["last_activity_at"].isoformat(), created_at=row["created_at"].isoformat(),
    )


@router.post("", response_model=EnquiryOut, status_code=201)
async def create_enquiry(
    body: EnquiryCreate,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> EnquiryOut:
    if not body.listing_id and not body.opportunity_id:
        raise HTTPException(status_code=422, detail=translate("enquiries.error.noTarget", lang))

    # [Idempotency-CC] repeated key returns the original response.
    if idempotency_key:
        cached = await conn.fetchrow(
            "SELECT response_snapshot FROM vyapar_platform.idempotency_key WHERE member_id = $1 AND idempotency_key = $2 AND endpoint = 'POST /v1/enquiries'",
            ctx.member_id, idempotency_key,
        )
        if cached:
            return EnquiryOut(**cached["response_snapshot"])

    action_type, provider_id, err = await _resolve_action_type(conn, body.listing_id, body.opportunity_id)
    if err == "target_not_active":
        raise HTTPException(status_code=400, detail=translate("enquiries.error.targetNotActive", lang))
    if err == "enquiries_disabled":
        raise HTTPException(status_code=400, detail=translate("enquiries.error.enquiriesDisabled", lang))
    if err or provider_id is None:
        raise HTTPException(status_code=404, detail=translate("common.error.listingNotFound", lang))
    if provider_id == ctx.member_id:
        raise HTTPException(status_code=400, detail=translate("enquiries.error.cannotEnquireOwn", lang))

    # [SP022] Rate limit — 20/day.
    allowed = await conn.fetchval(
        "SELECT vyapar_platform.check_and_increment($1, 86400, $2)", f"enquiry:{ctx.member_id}:day", RATE_LIMIT_PER_DAY
    )
    if not allowed:
        raise HTTPException(status_code=429, detail=translate("enquiries.error.dailyCapReached", lang, cap=RATE_LIMIT_PER_DAY))

    # [FR22 — blocked-sender handling: silently not delivered, no
    # disclosure. Real bug found via curl testing: blocks_blocker_only's
    # RLS means the SENDER's own session can't see a row where they are
    # the blocked_id — a plain query here always returned false. Fixed via
    # the narrow SECURITY DEFINER check added in migration 003.]
    blocked = await conn.fetchval("SELECT vyapar_enquiries.is_blocked($1, $2)", provider_id, ctx.member_id)

    try:
        # [Real bug found and fixed] a plain try/except around this INSERT
        # is not enough — once Postgres raises UniqueViolationError, the
        # whole enclosing transaction is aborted, and the very next query
        # (the existing-row lookup below) failed with
        # InFailedSQLTransactionError instead of returning a clean 409.
        # Wrapping the INSERT in its own nested `conn.transaction()` uses a
        # SAVEPOINT, so only THIS statement rolls back on conflict — the
        # outer request-scoped transaction (get_conn()'s own) stays usable
        # for the lookup query that follows.
        async with conn.transaction():
            row = await conn.fetchrow(
                """INSERT INTO vyapar_enquiries.enquiries
                     (sender_id, provider_id, listing_id, opportunity_id, action_type, sub_choice, delivered)
                   VALUES ($1,$2,$3,$4,$5,$6,$7)
                   RETURNING *""",
                ctx.member_id, provider_id, body.listing_id, body.opportunity_id, action_type, body.sub_choice, not blocked,
            )
    except asyncpg.UniqueViolationError:
        existing = await conn.fetchrow(
            """SELECT id FROM vyapar_enquiries.enquiries WHERE sender_id = $1
               AND COALESCE(listing_id::text, opportunity_id::text) = $2
               AND state NOT IN ('resolved','closed','withdrawn')""",
            ctx.member_id, body.listing_id or body.opportunity_id,
        )
        raise HTTPException(
            status_code=409,
            detail={"message": translate("enquiries.error.alreadyOpen", lang), "existing_enquiry_id": str(existing["id"]) if existing else None},
        )

    await conn.execute(
        "INSERT INTO vyapar_enquiries.enquiry_messages (enquiry_id, sender_id, body, attachment_url) VALUES ($1,$2,$3,$4)",
        row["id"], ctx.member_id, body.message, body.attachment_url,
    )
    # [FR32] enquiry event on the target (sponsored if it is boosted right now)
    if body.listing_id:
        await log_events(conn, "listing", [body.listing_id], "enquiry", "enquiry")
    else:
        await log_events(conn, "opportunity", [body.opportunity_id], "enquiry", "enquiry")
    result = _row_to_enquiry(row, ctx.member_id)

    if idempotency_key:
        await conn.execute(
            """INSERT INTO vyapar_platform.idempotency_key (idempotency_key, endpoint, member_id, request_hash, status_code, response_snapshot)
               VALUES ($1,'POST /v1/enquiries',$2,'',201,$3::jsonb)
               ON CONFLICT (member_id, idempotency_key, endpoint) DO NOTHING""",
            idempotency_key, ctx.member_id, result.model_dump_json(),
        )
    return result


@router.get("/mine", response_model=list[EnquiryOut])
async def list_my_enquiries(
    role: Literal["sent", "received", "all"] = "all",
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[EnquiryOut]:
    if role == "sent":
        rows = await conn.fetch("SELECT * FROM vyapar_enquiries.enquiries WHERE sender_id = $1 ORDER BY last_activity_at DESC", ctx.member_id)
    elif role == "received":
        rows = await conn.fetch("SELECT * FROM vyapar_enquiries.enquiries WHERE provider_id = $1 ORDER BY last_activity_at DESC", ctx.member_id)
    else:
        rows = await conn.fetch(
            "SELECT * FROM vyapar_enquiries.enquiries WHERE sender_id = $1 OR provider_id = $1 ORDER BY last_activity_at DESC", ctx.member_id
        )
    return [_row_to_enquiry(r, ctx.member_id) for r in rows]


async def _get_enquiry_or_404(conn: asyncpg.Connection, enquiry_id: str, member_id: str, lang: str) -> asyncpg.Record:
    row = await conn.fetchrow("SELECT * FROM vyapar_enquiries.enquiries WHERE id = $1", enquiry_id)
    if row is None or (row["sender_id"] != member_id and row["provider_id"] != member_id):
        raise HTTPException(status_code=404, detail=translate("enquiries.error.notFound", lang))
    return row


@router.get("/{enquiry_id}", response_model=EnquiryOut)
async def get_enquiry(
    enquiry_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> EnquiryOut:
    row = await _get_enquiry_or_404(conn, enquiry_id, ctx.member_id, lang)
    messages = await conn.fetch("SELECT * FROM vyapar_enquiries.enquiry_messages WHERE enquiry_id = $1 ORDER BY created_at", enquiry_id)
    out = _row_to_enquiry(row, ctx.member_id)
    out.messages = [
        EnquiryMessageOut(id=str(m["id"]), sender_id=m["sender_id"], body=m["body"], system_note=m["system_note"], created_at=m["created_at"].isoformat())
        for m in messages
    ]
    # [FR24/TR024] Contact disclosure ONLY after In Progress, ONLY for
    # listing-linked enquiries, ONLY via the one shared read function
    # (contacts_for_viewer) — never a second, independently-coded check.
    if row["state"] == "in_progress" and row["listing_id"]:
        disclose = True
        rows = await conn.fetch("SELECT * FROM vyapar_listings.contacts_for_viewer($1, $2)", row["listing_id"], disclose)
        out.disclosed_contacts = [ContactOut(channel=r["channel"], value=r["value"]) for r in rows]
        if not row["safety_notice_seen"]:
            await conn.execute("UPDATE vyapar_enquiries.enquiries SET safety_notice_seen = true WHERE id = $1", enquiry_id)
            out.safety_notice_seen = False  # [FR24] shown once — this response is the one time it's false
    return out


@router.post("/{enquiry_id}/messages", response_model=EnquiryMessageOut, status_code=201)
async def reply_to_enquiry(
    enquiry_id: str,
    body: MessageIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> EnquiryMessageOut:
    row = await _get_enquiry_or_404(conn, enquiry_id, ctx.member_id, lang)
    if row["state"] == "restricted":
        raise HTTPException(status_code=400, detail=translate("enquiries.error.restricted", lang))
    msg = await conn.fetchrow(
        "INSERT INTO vyapar_enquiries.enquiry_messages (enquiry_id, sender_id, body, attachment_url) VALUES ($1,$2,$3,$4) RETURNING *",
        enquiry_id, ctx.member_id, body.body, body.attachment_url,
    )
    new_state = row["state"]
    is_provider = ctx.member_id == row["provider_id"]
    if row["state"] == "open" and is_provider:
        new_state = "awaiting_response"
    # [FR28 "Responds in ~X" — real bug fixed in slice 7] first_reply_at is
    # the PROVIDER's first reply; a sender's follow-up used to set it too,
    # which would have made slow providers look fast.
    await conn.execute(
        """UPDATE vyapar_enquiries.enquiries SET state = $2,
             first_reply_at = CASE WHEN $3 THEN COALESCE(first_reply_at, now()) ELSE first_reply_at END,
             last_activity_at = now(), updated_at = now() WHERE id = $1""",
        enquiry_id, new_state, is_provider,
    )
    return EnquiryMessageOut(id=str(msg["id"]), sender_id=msg["sender_id"], body=msg["body"], system_note=msg["system_note"], created_at=msg["created_at"].isoformat())


async def _transition(conn: asyncpg.Connection, enquiry_id: str, member_id: str, lang: str, *, from_states: set[str], to_state: str, require_provider: bool = False) -> EnquiryOut:
    row = await _get_enquiry_or_404(conn, enquiry_id, member_id, lang)
    if require_provider and member_id != row["provider_id"]:
        raise HTTPException(status_code=403, detail=translate("enquiries.error.providerOnly", lang))
    if row["state"] not in from_states:
        raise HTTPException(status_code=400, detail=translate("enquiries.error.invalidTransition", lang))
    updated = await conn.fetchrow(
        "UPDATE vyapar_enquiries.enquiries SET state = $2, last_activity_at = now(), updated_at = now() WHERE id = $1 RETURNING *",
        enquiry_id, to_state,
    )
    # [FR27] Resolved/Closed is the qualifying moment; issue_invites() itself
    # checks the "a reply from each side" rule and invites each party once.
    if to_state in ("resolved", "closed"):
        await issue_review_invites(conn, "enquiry", enquiry_id)
    if to_state == "resolved":  # [FR32] outcome confirmed by the provider
        if updated["listing_id"]:
            await log_events(conn, "listing", [updated["listing_id"]], "outcome", "enquiry")
        elif updated["opportunity_id"]:
            await log_events(conn, "opportunity", [updated["opportunity_id"]], "outcome", "enquiry")
    return _row_to_enquiry(updated, member_id)


@router.post("/{enquiry_id}/accept", response_model=EnquiryOut)
async def accept_enquiry(enquiry_id: str, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn)) -> EnquiryOut:
    return await _transition(conn, enquiry_id, ctx.member_id, lang, from_states={"open", "awaiting_response"}, to_state="in_progress", require_provider=True)


@router.post("/{enquiry_id}/resolve", response_model=EnquiryOut)
async def resolve_enquiry(enquiry_id: str, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn)) -> EnquiryOut:
    return await _transition(conn, enquiry_id, ctx.member_id, lang, from_states={"in_progress"}, to_state="resolved", require_provider=True)


@router.post("/{enquiry_id}/close", response_model=EnquiryOut)
async def close_enquiry(enquiry_id: str, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn)) -> EnquiryOut:
    return await _transition(conn, enquiry_id, ctx.member_id, lang, from_states={"resolved", "in_progress"}, to_state="closed")


@router.post("/{enquiry_id}/withdraw", response_model=EnquiryOut)
async def withdraw_enquiry(enquiry_id: str, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn)) -> EnquiryOut:
    row = await _get_enquiry_or_404(conn, enquiry_id, ctx.member_id, lang)
    if ctx.member_id != row["sender_id"]:
        raise HTTPException(status_code=403, detail=translate("enquiries.error.senderOnly", lang))
    updated = await conn.fetchrow(
        "UPDATE vyapar_enquiries.enquiries SET state = 'withdrawn', last_activity_at = now(), updated_at = now() WHERE id = $1 RETURNING *", enquiry_id
    )
    return _row_to_enquiry(updated, ctx.member_id)


@router.post("/{enquiry_id}/restrict", response_model=EnquiryOut)
async def restrict_enquiry(enquiry_id: str, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn)) -> EnquiryOut:
    row = await _get_enquiry_or_404(conn, enquiry_id, ctx.member_id, lang)
    updated = await conn.fetchrow(
        "UPDATE vyapar_enquiries.enquiries SET state = 'restricted', last_activity_at = now(), updated_at = now() WHERE id = $1 RETURNING *", enquiry_id
    )
    return _row_to_enquiry(updated, ctx.member_id)


# ---------------------------------------------------------------------------
# [FR24] Blocking — ends the thread, prevents future enquiries both ways,
# hides the blocked party's future content from the blocker (the "future
# content" half is a search/feed-level concern for a later pass; this
# endpoint owns the block relationship + immediate thread-ending itself).
# Traces to: FR24, TR024
# ---------------------------------------------------------------------------
class BlockIn(BaseModel):
    blocked_id: str
    enquiry_id: str | None = None


@router.post("/block")
async def block_member(body: BlockIn, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn)) -> dict:
    await conn.execute(
        "INSERT INTO vyapar_enquiries.blocks (blocker_id, blocked_id) VALUES ($1,$2) ON CONFLICT DO NOTHING",
        ctx.member_id, body.blocked_id,
    )
    if body.enquiry_id:
        await conn.execute(
            """UPDATE vyapar_enquiries.enquiries SET state = 'closed', last_activity_at = now(), updated_at = now()
               WHERE id = $1 AND (sender_id = $2 OR provider_id = $2)""",
            body.enquiry_id, ctx.member_id,
        )
    return {"blocked": True}


# ---------------------------------------------------------------------------
# [FR23] "Refer to Counsel" — explicit, consented referral only, per
# FR52(f)'s minimal-payload contract (member_id, problem_summary, consent
# flag only — no appointment/payment state exchanged).
# Traces to: FR23, FR52(f)
# ---------------------------------------------------------------------------
class ReferToCounselIn(BaseModel):
    problem_summary: str = Field(min_length=10, max_length=500)
    consent: Literal[True]


@router.post("/{enquiry_id}/refer-to-counsel")
async def refer_to_counsel(enquiry_id: str, body: ReferToCounselIn, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn)) -> dict:
    await _get_enquiry_or_404(conn, enquiry_id, ctx.member_id, lang)
    await conn.execute(
        "INSERT INTO vyapar_integration.counsel_referrals (member_id, enquiry_id, problem_summary, consent) VALUES ($1,$2,$3,$4)",
        ctx.member_id, enquiry_id, body.problem_summary, body.consent,
    )
    return {"referred": True}

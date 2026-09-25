# [TR022] Submit an Enquiry or Opportunity Response (FR22). [TR023] Provider
# manages the Enquiry lifecycle (FR23). [TR024] Consent-based contact
# disclosure and blocking (FR24).
# Approach: `action_type` is ALWAYS resolved server-side from the target's
# own type — reusing the opportunities service's TYPE_ACTION_LABEL mapping for
# opportunity targets and a fixed 'enquire' for listing targets — never
# accepted as client input (closes the exact Spoofing risk SP022 names:
# "client-supplied action_type claiming a different action than the target
# actually supports"). The DB's own partial unique index
# (`enquiries_one_open_per_target`) is the actual 1-open-enquiry-per-target
# enforcement — this service's own pre-check is a friendlier error message on
# top of it, not the enforcement itself, closing the race condition an
# application-only check could miss. Idempotency-CC: `Idempotency-Key`
# header via the shared `vyapar_platform.idempotency_key` table.
# Traces to: FR22, FR23, FR24, TR022, TR023, TR024, SP022, SP023, SP024
from __future__ import annotations

from typing import Literal

import asyncpg
from pydantic import BaseModel, Field

from app.services.listings import require_profile
from app.errors import ApiError
from app.identity import AuthzContext
from app.services.opportunities import TYPE_ACTION_LABEL
from app.services.privacy import require_accepted
from app.services.reviews import issue_review_invites
from app.impressions import log_events
from app.services.pagination import DEFAULT_LIMIT, MAX_LIMIT, Page, paginate


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
    # [Critique agent finding, fixed here] attachment_url was stored on
    # every message insert since the very first slice but never returned —
    # UX12's own wireframe names "attachments as file chips" in the thread,
    # which had no data to render.
    attachment_url: str | None = None


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
    # [Real bug found live — coordinator's two-user test] the mine list
    # rendered as literally "enquire · open" with no target, no counterpart,
    # no readable state — every other list in the app (Discover, Businesses,
    # Activity) shows real names. These two are populated only by the list
    # endpoint (a single extra join per row, cheap at list-page scale) so
    # every other caller of `_row_to_enquiry` is unaffected.
    target_name: str | None = None
    counterpart_name: str | None = None


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


async def create_enquiry(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    body: EnquiryCreate,
    idempotency_key: str | None = None,
) -> EnquiryOut:
    if not body.listing_id and not body.opportunity_id:
        raise ApiError(422, "enquiries.error.noTarget", lang)
    # [FR53/TR053] the gate every gated action calls before proceeding.
    await require_accepted(conn, ctx.member_id, "privacy", lang)
    await require_accepted(conn, ctx.member_id, "terms", lang)
    await require_profile(conn, ctx.member_id, lang)

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
        raise ApiError(400, "enquiries.error.targetNotActive", lang)
    if err == "enquiries_disabled":
        raise ApiError(400, "enquiries.error.enquiriesDisabled", lang)
    if err or provider_id is None:
        raise ApiError(404, "common.error.listingNotFound", lang)
    if provider_id == ctx.member_id:
        raise ApiError(400, "enquiries.error.cannotEnquireOwn", lang)

    # [SP022] Rate limit — 20/day.
    allowed = await conn.fetchval(
        "SELECT vyapar_platform.check_and_increment($1, 86400, $2)", f"enquiry:{ctx.member_id}:day", RATE_LIMIT_PER_DAY
    )
    if not allowed:
        raise ApiError(429, "enquiries.error.dailyCapReached", lang, cap=RATE_LIMIT_PER_DAY)

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
            # [Real bug found via curl testing, fixed here] content_language
            # lives on vyapar_enquiries.enquiry_messages (the actual authored
            # text), not on vyapar_enquiries.enquiries (the thread/state
            # container) — the ER model only put the TR042 column on tables
            # holding authored content. An earlier pass wrongly inserted it
            # into the enquiries INSERT, which raised UndefinedColumnError.
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
        raise ApiError(409, "enquiries.error.alreadyOpen", lang, extra={"existing_enquiry_id": str(existing["id"]) if existing else None})

    await conn.execute(
        "INSERT INTO vyapar_enquiries.enquiry_messages (enquiry_id, sender_id, body, attachment_url, content_language) VALUES ($1,$2,$3,$4,$5)",
        row["id"], ctx.member_id, body.message, body.attachment_url, lang,
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


async def list_my_enquiries(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    role: Literal["sent", "received", "all"] = "all",
) -> list[EnquiryOut]:
    if role == "sent":
        rows = await conn.fetch("SELECT * FROM vyapar_enquiries.enquiries WHERE sender_id = $1 ORDER BY last_activity_at DESC", ctx.member_id)
    elif role == "received":
        rows = await conn.fetch("SELECT * FROM vyapar_enquiries.enquiries WHERE provider_id = $1 ORDER BY last_activity_at DESC", ctx.member_id)
    else:
        rows = await conn.fetch(
            "SELECT * FROM vyapar_enquiries.enquiries WHERE sender_id = $1 OR provider_id = $1 ORDER BY last_activity_at DESC", ctx.member_id
        )
    out = [_row_to_enquiry(r, ctx.member_id) for r in rows]
    if not out:
        return out
    listing_ids = {r.listing_id for r in out if r.listing_id}
    opportunity_ids = {r.opportunity_id for r in out if r.opportunity_id}
    counterpart_ids = {(r.provider_id if r.is_sender else r.sender_id) for r in out}
    listing_names: dict[str, str] = {}
    opp_names: dict[str, str] = {}
    member_names: dict[str, str] = {}
    if listing_ids:
        for r in await conn.fetch("SELECT id, name FROM vyapar_listings.listings WHERE id = ANY($1::uuid[])", list(listing_ids)):
            listing_names[str(r["id"])] = r["name"]
    if opportunity_ids:
        for r in await conn.fetch("SELECT id, title FROM vyapar_opportunities.opportunities WHERE id = ANY($1::uuid[])", list(opportunity_ids)):
            opp_names[str(r["id"])] = r["title"]
    if counterpart_ids:
        # [Real bug found live, fixed here] a plain SELECT against
        # vyapar_identity.members is blocked by members_self_or_operator RLS
        # for anyone but the caller — the same gap FR18/feed.py already hit
        # and fixed via this one shared SECURITY DEFINER function; reused
        # here rather than a second, independently-coded lookup.
        for r in await conn.fetch("SELECT id, display_name FROM vyapar_identity.public_names($1::text[])", list(counterpart_ids)):
            member_names[r["id"]] = r["display_name"]
    for item in out:
        item.target_name = listing_names.get(item.listing_id) or opp_names.get(item.opportunity_id)
        item.counterpart_name = member_names.get(item.provider_id if item.is_sender else item.sender_id)
    return out


async def _get_enquiry_or_404(conn: asyncpg.Connection, enquiry_id: str, member_id: str, lang: str) -> asyncpg.Record:
    row = await conn.fetchrow("SELECT * FROM vyapar_enquiries.enquiries WHERE id = $1", enquiry_id)
    if row is None or (row["sender_id"] != member_id and row["provider_id"] != member_id):
        raise ApiError(404, "enquiries.error.notFound", lang)
    return row


async def get_enquiry(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    enquiry_id: str,
) -> EnquiryOut:
    row = await _get_enquiry_or_404(conn, enquiry_id, ctx.member_id, lang)
    messages = await conn.fetch("SELECT * FROM vyapar_enquiries.enquiry_messages WHERE enquiry_id = $1 ORDER BY created_at", enquiry_id)
    out = _row_to_enquiry(row, ctx.member_id)
    out.messages = [
        EnquiryMessageOut(id=str(m["id"]), sender_id=m["sender_id"], body=m["body"], system_note=m["system_note"], created_at=m["created_at"].isoformat(), attachment_url=m["attachment_url"])
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


async def reply_to_enquiry(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    enquiry_id: str,
    body: MessageIn,
) -> EnquiryMessageOut:
    row = await _get_enquiry_or_404(conn, enquiry_id, ctx.member_id, lang)
    if row["state"] == "restricted":
        raise ApiError(400, "enquiries.error.restricted", lang)
    # [TR042] content_language recorded on every authored message, same as
    # the create-enquiry path — reply text is content too.
    msg = await conn.fetchrow(
        "INSERT INTO vyapar_enquiries.enquiry_messages (enquiry_id, sender_id, body, attachment_url, content_language) VALUES ($1,$2,$3,$4,$5) RETURNING *",
        enquiry_id, ctx.member_id, body.body, body.attachment_url, lang,
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
    return EnquiryMessageOut(id=str(msg["id"]), sender_id=msg["sender_id"], body=msg["body"], system_note=msg["system_note"], created_at=msg["created_at"].isoformat(), attachment_url=msg["attachment_url"])


async def _transition(conn: asyncpg.Connection, enquiry_id: str, member_id: str, lang: str, *, from_states: set[str], to_state: str, require_provider: bool = False) -> EnquiryOut:
    row = await _get_enquiry_or_404(conn, enquiry_id, member_id, lang)
    if require_provider and member_id != row["provider_id"]:
        raise ApiError(403, "enquiries.error.providerOnly", lang)
    if row["state"] not in from_states:
        raise ApiError(400, "enquiries.error.invalidTransition", lang)
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


async def accept_enquiry(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    enquiry_id: str,
) -> EnquiryOut:
    return await _transition(conn, enquiry_id, ctx.member_id, lang, from_states={"open", "awaiting_response"}, to_state="in_progress", require_provider=True)


async def resolve_enquiry(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    enquiry_id: str,
) -> EnquiryOut:
    return await _transition(conn, enquiry_id, ctx.member_id, lang, from_states={"in_progress"}, to_state="resolved", require_provider=True)


async def close_enquiry(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    enquiry_id: str,
) -> EnquiryOut:
    return await _transition(conn, enquiry_id, ctx.member_id, lang, from_states={"resolved", "in_progress"}, to_state="closed")


async def withdraw_enquiry(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    enquiry_id: str,
) -> EnquiryOut:
    row = await _get_enquiry_or_404(conn, enquiry_id, ctx.member_id, lang)
    if ctx.member_id != row["sender_id"]:
        raise ApiError(403, "enquiries.error.senderOnly", lang)
    updated = await conn.fetchrow(
        "UPDATE vyapar_enquiries.enquiries SET state = 'withdrawn', last_activity_at = now(), updated_at = now() WHERE id = $1 RETURNING *", enquiry_id
    )
    return _row_to_enquiry(updated, ctx.member_id)


async def restrict_enquiry(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    enquiry_id: str,
) -> EnquiryOut:
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


class BlockedOut(BaseModel):
    blocked: bool


async def block_member(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    body: BlockIn,
) -> BlockedOut:
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
    return BlockedOut(blocked=True)


# ---------------------------------------------------------------------------
# [FR23] "Refer to Counsel" — explicit, consented referral only, per
# FR52(f)'s minimal-payload contract (member_id, problem_summary, consent
# flag only — no appointment/payment state exchanged).
# Traces to: FR23, FR52(f)
# ---------------------------------------------------------------------------
class ReferToCounselIn(BaseModel):
    problem_summary: str = Field(min_length=10, max_length=500)
    consent: Literal[True]


class ReferredOut(BaseModel):
    referred: bool


async def refer_enquiry_to_counsel(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    enquiry_id: str,
    body: ReferToCounselIn,
) -> ReferredOut:
    await _get_enquiry_or_404(conn, enquiry_id, ctx.member_id, lang)
    await conn.execute(
        "INSERT INTO vyapar_integration.counsel_referrals (member_id, enquiry_id, problem_summary, consent) VALUES ($1,$2,$3,$4)",
        ctx.member_id, enquiry_id, body.problem_summary, body.consent,
    )
    return ReferredOut(referred=True)


async def list_my_enquiries_page(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    limit: int = DEFAULT_LIMIT,
    cursor: str | None = None, role: Literal["sent", "received", "all"] = "all",
) -> Page[EnquiryOut]:
    """[Refactor A] Cursor-paged `list_my_enquiries` — same rows, same order."""
    return paginate(await list_my_enquiries(conn, ctx, role=role), limit, cursor, lang)

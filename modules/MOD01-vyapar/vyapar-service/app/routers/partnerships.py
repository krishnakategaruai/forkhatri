# [TR025] Create a Partnership Request (FR25). [TR026] Respond to and manage
# a Partnership Request (FR26).
# Approach:
#  - Both listings must pass Listings' own `is_active()` (never a direct
#    state query from here, SP025). The recipient's opt-out
#    (`partnership_open`), an existing block either way, or an earlier
#    Restrict between the pair all answer with the SAME neutral "not
#    accepting" message, so a sender can't tell a block from an opt-out.
#  - The 10-pending cap is a standing count (Cross-cutting §2(b)), taken under
#    a per-sender advisory lock so the 11th concurrent request can't race past
#    it (SP025's concurrency threshold). 30-day re-send cooldown after Decline
#    between the same pair (SP026). Idempotency-Key honoured.
#  - Every state change goes through migration 005's
#    `partnership_transition()` — the one state machine, which is also what
#    lets the RECIPIENT accept (the table's RLS admits only the sender).
#    Pending never auto-expires (FR26).
#  - Contact appears only after Accept, via the same `contacts_for_viewer()`
#    TR024 uses for enquiries — never a second disclosure implementation.
#  - Accepted -> Closed issues both parties' review invites (FR27).
#  - V1 has no message thread inside a request (UX17 DEC-001): Accept ->
#    contact reveal is the whole workflow.
# Reference (Upwork + WorkIndia lens): neither app has B2B partnership
# requests (UX17 found no directory precedent either); the one borrowed
# pattern is Upwork's "invite, then contact details only inside an accepted
# engagement". Category and locality are prefilled from the recipient's own
# listing, so the sender types only what is genuinely theirs to say.
# Traces to: FR25, FR26, FR27, TR025, TR026, TR024, SP025, SP026
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Literal

import asyncpg
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from app.config import get_settings
from app.db import get_conn
from app.deps import Locale
from app.i18n import translate
from app.identity import AuthzContext, resolve_authz_context
from app.notifications import notify_interaction_party
from app.reputation import reputation_for_listings
from app.routers.listings import is_active
from app.routers.reviews import issue_review_invites

router = APIRouter(prefix="/v1/partnership-requests", tags=["partnerships"])

DECLINE_COOLDOWN = timedelta(days=30)
Action = Literal["accept", "decline", "withdraw", "restrict", "close"]


class PartnershipIn(BaseModel):
    recipient_listing_id: str
    sender_listing_id: str | None = None
    need: str = Field(min_length=10, max_length=500)
    offer: str = Field(min_length=10, max_length=500)
    expectations: str = Field(min_length=10, max_length=500)
    # [Decision] FR25 says every field is 10-500 characters, but UX17 makes
    # category a chip/select and locality a short place name (e.g. "Abids") —
    # a 10-character minimum can't hold for those two structured fields.
    category: str = Field(min_length=2, max_length=120)
    locality: str = Field(min_length=2, max_length=120)
    timing: str = Field(min_length=10, max_length=500)
    next_step: str = Field(min_length=10, max_length=500)


@router.post("", status_code=201)
async def create_partnership_request(
    body: PartnershipIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict:
    endpoint = "POST /v1/partnership-requests"
    if idempotency_key:
        cached = await conn.fetchval(
            "SELECT response_snapshot FROM vyapar_platform.idempotency_key WHERE member_id = $1 AND idempotency_key = $2 AND endpoint = $3",
            ctx.member_id, idempotency_key, endpoint,
        )
        if cached:
            return json.loads(cached) if isinstance(cached, str) else cached

    recipient_listing = await is_active(conn, body.recipient_listing_id)
    if recipient_listing is None:
        raise HTTPException(status_code=400, detail=translate("partnerships.error.targetNotActive", lang))
    if recipient_listing["owner_id"] == ctx.member_id:
        raise HTTPException(status_code=400, detail=translate("partnerships.error.cannotProposeOwn", lang))
    if not recipient_listing["partnership_open"]:
        raise HTTPException(status_code=400, detail=translate("partnerships.error.notAccepting", lang))

    if body.sender_listing_id:
        sender_listing = await is_active(conn, body.sender_listing_id)
        if sender_listing is None or sender_listing["owner_id"] != ctx.member_id:
            raise HTTPException(status_code=422, detail=translate("partnerships.error.senderListingInvalid", lang))
    else:
        sender_listing = await conn.fetchrow(
            """SELECT id, name FROM vyapar_listings.listings
               WHERE owner_id = $1 AND state IN ('active_unverified','active_verified')
               ORDER BY published_at DESC NULLS LAST LIMIT 1""",
            ctx.member_id,
        )
        if sender_listing is None:
            raise HTTPException(
                status_code=422,
                detail={"message": translate("partnerships.error.needActiveListing", lang), "code": "need_active_listing"},
            )

    other = recipient_listing["owner_id"]
    blocked = await conn.fetchval(
        "SELECT vyapar_enquiries.is_blocked($1, $2) OR vyapar_enquiries.is_blocked($2, $1)", other, ctx.member_id
    )
    restricted = await conn.fetchval(
        """SELECT EXISTS (SELECT 1 FROM vyapar_enquiries.partnership_requests WHERE state = 'restricted'
             AND ((sender_id = $1 AND recipient_id = $2) OR (sender_id = $2 AND recipient_id = $1)))""",
        ctx.member_id, other,
    )
    if blocked or restricted:
        raise HTTPException(status_code=400, detail=translate("partnerships.error.notAccepting", lang))

    await conn.execute("SELECT pg_advisory_xact_lock(hashtext($1))", f"partnership_pending:{ctx.member_id}")

    last_decline = await conn.fetchval(
        "SELECT max(decided_at) FROM vyapar_enquiries.partnership_requests WHERE sender_id = $1 AND recipient_id = $2 AND state = 'declined'",
        ctx.member_id, other,
    )
    if last_decline and last_decline + DECLINE_COOLDOWN > datetime.now(timezone.utc):
        raise HTTPException(
            status_code=409,
            detail={
                "message": translate("partnerships.error.cooldown", lang, date=(last_decline + DECLINE_COOLDOWN).date().isoformat()),
                "code": "cooldown",
            },
        )
    duplicate = await conn.fetchval(
        "SELECT id FROM vyapar_enquiries.partnership_requests WHERE sender_id = $1 AND recipient_listing_id = $2 AND state = 'pending'",
        ctx.member_id, recipient_listing["id"],
    )
    if duplicate:
        raise HTTPException(
            status_code=409,
            detail={"message": translate("partnerships.error.alreadyPending", lang), "code": "already_pending", "existing_id": str(duplicate)},
        )
    cap = get_settings().partnership_request_pending_cap
    pending = await conn.fetch(
        """SELECT p.id, l.name FROM vyapar_enquiries.partnership_requests p
           LEFT JOIN vyapar_listings.listings l ON l.id = p.recipient_listing_id
           WHERE p.sender_id = $1 AND p.state = 'pending' ORDER BY p.created_at""",
        ctx.member_id,
    )
    if len(pending) >= cap:
        raise HTTPException(
            status_code=409,
            detail={
                "message": translate("partnerships.error.pendingCap", lang, cap=cap),
                "code": "pending_cap",
                "pending": [{"id": str(p["id"]), "name": p["name"]} for p in pending],
            },
        )

    row = await conn.fetchrow(
        """INSERT INTO vyapar_enquiries.partnership_requests
             (sender_id, recipient_id, sender_listing_id, recipient_listing_id, need, offer, expectations,
              content_language, category, locality, timing, next_step, state)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,'pending') RETURNING id, state""",
        ctx.member_id, other, sender_listing["id"], recipient_listing["id"], body.need.strip(), body.offer.strip(),
        body.expectations.strip(), lang, body.category.strip(), body.locality.strip(), body.timing.strip(), body.next_step.strip(),
    )
    await notify_interaction_party(
        conn, interaction_kind="partnership", interaction_id=row["id"], recipient=other, template="partnershipReceived",
        link=f"/partnerships/{row['id']}", idempotency_key=f"partnership_received:{row['id']}",
        params={"name": sender_listing["name"]},
    )
    result = {"id": str(row["id"]), "state": row["state"]}
    if idempotency_key:
        await conn.execute(
            """INSERT INTO vyapar_platform.idempotency_key (idempotency_key, endpoint, member_id, request_hash, status_code, response_snapshot)
               VALUES ($1, $2, $3, '', 201, $4::jsonb) ON CONFLICT (member_id, idempotency_key, endpoint) DO NOTHING""",
            idempotency_key, endpoint, ctx.member_id, json.dumps(result),
        )
    return result


@router.get("/mine")
async def list_my_partnership_requests(
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[dict]:
    rows = await conn.fetch(
        """SELECT p.id, p.state, p.sender_id, p.created_at, sl.name AS sender_listing_name, rl.name AS recipient_listing_name
           FROM vyapar_enquiries.partnership_requests p
           LEFT JOIN vyapar_listings.listings sl ON sl.id = p.sender_listing_id
           LEFT JOIN vyapar_listings.listings rl ON rl.id = p.recipient_listing_id
           WHERE p.sender_id = $1 OR p.recipient_id = $1 ORDER BY p.updated_at DESC""",
        ctx.member_id,
    )
    return [
        {
            "id": str(r["id"]), "state": r["state"], "is_sender": r["sender_id"] == ctx.member_id,
            "other_listing_name": r["recipient_listing_name"] if r["sender_id"] == ctx.member_id else r["sender_listing_name"],
            "created_at": r["created_at"].isoformat(),
        }
        for r in rows
    ]


async def _listing_summary(conn: asyncpg.Connection, listing_id) -> asyncpg.Record | None:
    return await conn.fetchrow(
        "SELECT id, owner_id, name, kind, verification_state FROM vyapar_listings.listings WHERE id = $1", listing_id
    )


@router.get("/{request_id}")
async def get_partnership_request(
    request_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    try:
        row = await conn.fetchrow("SELECT * FROM vyapar_enquiries.partnership_requests WHERE id = $1", request_id)
    except asyncpg.DataError:
        row = None
    if row is None or ctx.member_id not in (row["sender_id"], row["recipient_id"]):
        raise HTTPException(status_code=404, detail=translate("partnerships.error.notFound", lang))
    is_sender = row["sender_id"] == ctx.member_id
    sender_listing = await _listing_summary(conn, row["sender_listing_id"])
    recipient_listing = await _listing_summary(conn, row["recipient_listing_id"])
    reps = await reputation_for_listings(conn, [r for r in (sender_listing, recipient_listing) if r])

    def summary(listing: asyncpg.Record | None) -> dict | None:
        if listing is None:
            return None
        return {
            "id": str(listing["id"]), "name": listing["name"], "kind": listing["kind"],
            "verification_state": listing["verification_state"], "reputation": reps.get(str(listing["id"])),
        }

    contacts: list[dict] = []
    if row["state"] in ("accepted", "closed"):
        other_listing_id = row["recipient_listing_id"] if is_sender else row["sender_listing_id"]
        contact_rows = await conn.fetch("SELECT channel, value FROM vyapar_listings.contacts_for_viewer($1, true)", other_listing_id)
        contacts = [{"channel": c["channel"], "value": c["value"]} for c in contact_rows]

    return {
        "id": str(row["id"]), "state": row["state"], "is_sender": is_sender,
        "need": row["need"], "offer": row["offer"], "expectations": row["expectations"], "category": row["category"],
        "locality": row["locality"], "timing": row["timing"], "next_step": row["next_step"],
        "created_at": row["created_at"].isoformat(), "decided_at": row["decided_at"].isoformat() if row["decided_at"] else None,
        "sender_listing": summary(sender_listing), "recipient_listing": summary(recipient_listing),
        "disclosed_contacts": contacts,
    }


@router.post("/{request_id}/{action}")
async def transition_partnership_request(
    request_id: str,
    action: Action,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    try:
        async with conn.transaction():
            new_state = await conn.fetchval("SELECT vyapar_enquiries.partnership_transition($1, $2)", request_id, action)
    except asyncpg.DataError:
        raise HTTPException(status_code=404, detail=translate("partnerships.error.notFound", lang))
    except asyncpg.RaiseError as exc:
        message = str(exc)
        for code, (status, key) in {
            "recipient_only": (403, "recipientOnly"), "sender_only": (403, "senderOnly"),
            "invalid_transition": (400, "invalidTransition"), "not_found": (404, "notFound"),
        }.items():
            if code in message:
                raise HTTPException(status_code=status, detail=translate(f"partnerships.error.{key}", lang))
        raise

    row = await conn.fetchrow("SELECT sender_id, recipient_id FROM vyapar_enquiries.partnership_requests WHERE id = $1", request_id)
    other = row["recipient_id"] if row["sender_id"] == ctx.member_id else row["sender_id"]
    if action != "restrict":  # restricting never pings the restricted party
        await notify_interaction_party(
            conn, interaction_kind="partnership", interaction_id=request_id, recipient=other, template="partnershipUpdated",
            link=f"/partnerships/{request_id}", idempotency_key=f"partnership_updated:{request_id}:{new_state}",
            key_params={"state": f"partnerships.stateWord.{new_state}"},
        )
    invites = await issue_review_invites(conn, "partnership", request_id) if new_state == "closed" else 0
    return {"state": new_state, "review_invites": invites}

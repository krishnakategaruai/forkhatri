# [TR027] Submit a Review tied to a qualifying interaction (FR27).
# [TR028] Reputation display (FR28) — review rows for a listing.
# [TR029] Review dispute, hide, and removal via Trust & Safety only (FR29).
# Approach:
#  - Invites are issued by migration 005's `issue_invites()` the moment an
#    enquiry becomes Resolved/Closed with a message from both sides, or a
#    partnership goes Accepted -> Closed; qualification is re-derived from the
#    source rows in the DB, never trusted from the caller. Each party is
#    invited once (UNIQUE) and notified in their own language.
#  - POST /v1/reviews is rejected unless the caller holds an unused,
#    unexpired invite for that exact interaction (SP027: a foreign-row check,
#    not a flag). One review per party per interaction is the DB's UNIQUE,
#    caught in a savepoint so a double submit is a clean 409.
#  - TR003's wordlist check (`listings._content_flags`, reused — not copied)
#    runs before insert; a flagged comment is stored Hidden and raised as an
#    automated moderation case instead of publishing.
#  - Dispute is the ONLY action a review's subject has (StructAbsence,
#    SP029): there is no edit/hide operation for subjects at all. The
#    decision is made in the moderation queue (trust_safety.py).
#  - Anti-retaliation: Upwork's double-blind feedback, adapted — a review is
#    revealed to its subject (and counted publicly) only once the subject has
#    reviewed back or their own 30-day window has closed (`is_revealed()`).
# Reference (Upwork + WorkIndia lens): Upwork invites both parties when a
# contract ends, keeps feedback hidden until both submit or 14 days pass, so
# neither side can retaliate; WorkIndia has no interaction review for
# employers/candidates to copy. Vyapar keeps FR27's recommend + tags (no
# stars, DEC-001) and its 30-day window, adopting only the blind reveal.
# Traces to: FR27, FR28, FR29, TR027, TR028, TR029, SP027, SP028, SP029
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Literal

import asyncpg
from pydantic import BaseModel, Field

from app.config import get_settings
from app.errors import ApiError
from app.identity import AuthzContext
from app.notifications import notify_interaction_party
from app.services.listings import _content_flags
from app.services.pagination import DEFAULT_LIMIT, MAX_LIMIT, Page, paginate


InteractionKind = Literal["enquiry", "partnership"]
DisputeReason = Literal["retaliation", "manipulation", "not_the_interaction", "abusive"]
THREAD_PATH = {"enquiry": "/enquiries/", "partnership": "/partnerships/"}


class ReviewInviteStatusOut(BaseModel):
    can_review: bool
    expires_at: str | None
    already_reviewed: bool
    review_state: str | None
    tags_positive: list[str]
    tags_negative: list[str]


class ReviewCreatedOut(BaseModel):
    id: str
    state: str


class ListingReviewOut(BaseModel):
    id: str
    recommend: bool
    tags: list[str]
    comment: str | None
    created_at: str
    state: str
    author_first_name: str | None
    is_subject: bool
    is_author: bool
    disputed: bool


class DisputeOut(BaseModel):
    state: str


def allowed_tags() -> list[str]:
    settings = get_settings()
    return settings.review_tags_positive + settings.review_tags_negative


async def issue_review_invites(conn: asyncpg.Connection, kind: str, interaction_id) -> int:
    """Called by enquiries.py / partnerships.py on the qualifying transition.
    Returns the number of NEW invites (0 if not qualifying or already issued)."""
    rows = await conn.fetch("SELECT * FROM vyapar_reviews.issue_invites($1, $2)", kind, interaction_id)
    for r in rows:
        await notify_interaction_party(
            conn, interaction_kind=kind, interaction_id=interaction_id, recipient=r["member_id"],
            template="reviewInvite", link=f"{THREAD_PATH[kind]}{interaction_id}",
            idempotency_key=f"review_invite:{kind}:{interaction_id}:{r['member_id']}",
        )
    return len(rows)


async def get_review_invite_status(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    interaction_kind: InteractionKind,
    interaction_id: str,
) -> ReviewInviteStatusOut:
    invite = await conn.fetchrow(
        "SELECT expires_at, used_at FROM vyapar_reviews.review_invites WHERE interaction_kind = $1 AND interaction_id = $2 AND member_id = $3",
        interaction_kind, interaction_id, ctx.member_id,
    )
    review = await conn.fetchrow(
        "SELECT state FROM vyapar_reviews.reviews WHERE interaction_kind = $1 AND interaction_id = $2 AND author_id = $3",
        interaction_kind, interaction_id, ctx.member_id,
    )
    settings = get_settings()
    return ReviewInviteStatusOut(
        can_review=invite is not None and invite["used_at"] is None and invite["expires_at"] > datetime.now(timezone.utc) and review is None,
        expires_at=invite["expires_at"].isoformat() if invite else None,
        already_reviewed=review is not None,
        review_state=review["state"] if review else None,
        tags_positive=settings.review_tags_positive,
        tags_negative=settings.review_tags_negative,
    )


class ReviewIn(BaseModel):
    interaction_kind: InteractionKind
    interaction_id: str
    recommend: bool
    tags: list[str] = Field(default_factory=list, max_length=3)
    comment: str | None = Field(default=None, max_length=500)


async def create_review(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    body: ReviewIn,
    idempotency_key: str | None = None,
) -> ReviewCreatedOut:
    endpoint = "POST /v1/reviews"
    if idempotency_key:
        cached = await conn.fetchval(
            "SELECT response_snapshot FROM vyapar_platform.idempotency_key WHERE member_id = $1 AND idempotency_key = $2 AND endpoint = $3",
            ctx.member_id, idempotency_key, endpoint,
        )
        if cached:
            return ReviewCreatedOut(**(json.loads(cached) if isinstance(cached, str) else cached))

    comment = (body.comment or "").strip() or None
    if comment is not None and len(comment) < 20:
        raise ApiError(422, "reviews.error.commentLength", lang)
    if any(tag not in allowed_tags() for tag in body.tags) or len(set(body.tags)) != len(body.tags):
        raise ApiError(422, "reviews.error.invalidTag", lang)

    invite = await conn.fetchrow(
        """SELECT * FROM vyapar_reviews.review_invites
           WHERE interaction_kind = $1 AND interaction_id = $2 AND member_id = $3""",
        body.interaction_kind, body.interaction_id, ctx.member_id,
    )
    already = await conn.fetchval(
        "SELECT 1 FROM vyapar_reviews.reviews WHERE interaction_kind = $1 AND interaction_id = $2 AND author_id = $3",
        body.interaction_kind, body.interaction_id, ctx.member_id,
    )
    if already:
        raise ApiError(409, "reviews.error.alreadyReviewed", lang)
    if invite is None or invite["used_at"] is not None or invite["expires_at"] <= datetime.now(timezone.utc):
        raise ApiError(403, "reviews.error.noQualifyingInteraction", lang)

    flag = _content_flags(comment or "", None, None) if comment else None
    state = "hidden" if flag else "published"
    try:
        async with conn.transaction():  # savepoint — a concurrent duplicate is a clean 409
            row = await conn.fetchrow(
                """INSERT INTO vyapar_reviews.reviews
                     (interaction_kind, interaction_id, author_id, subject_listing_id, subject_member_id, recommend, tags, comment, content_language, state)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10) RETURNING id, state""",
                body.interaction_kind, body.interaction_id, ctx.member_id, invite["subject_listing_id"], invite["subject_member_id"],
                body.recommend, body.tags, comment, lang, state,
            )
    except asyncpg.UniqueViolationError:
        raise ApiError(409, "reviews.error.alreadyReviewed", lang)
    await conn.execute("UPDATE vyapar_reviews.review_invites SET used_at = now() WHERE id = $1", invite["id"])
    if flag:
        await conn.execute(
            "SELECT vyapar_trust_safety.raise_auto_flag('review', $1, $2, $3, 'medium')", row["id"], ctx.member_id, flag
        )

    result = {"id": str(row["id"]), "state": row["state"]}
    if idempotency_key:
        await conn.execute(
            """INSERT INTO vyapar_platform.idempotency_key (idempotency_key, endpoint, member_id, request_hash, status_code, response_snapshot)
               VALUES ($1, $2, $3, '', 201, $4::jsonb) ON CONFLICT (member_id, idempotency_key, endpoint) DO NOTHING""",
            idempotency_key, endpoint, ctx.member_id, json.dumps(result),
        )
    return ReviewCreatedOut(**result)


async def list_listing_reviews(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    listing_id: str,
) -> list[ListingReviewOut]:
    try:
        rows = await conn.fetch("SELECT * FROM vyapar_reviews.reviews_for_listing($1)", listing_id)
    except asyncpg.DataError:
        return []
    return [
        ListingReviewOut(
            id=str(r["id"]), recommend=r["recommend"], tags=list(r["tags"]), comment=r["comment"],
            created_at=r["created_at"].isoformat(), state=r["state"], author_first_name=r["author_first_name"],
            is_subject=r["is_subject"], is_author=r["is_author"], disputed=r["disputed"],
        )
        for r in rows
    ]


class DisputeIn(BaseModel):
    reason: DisputeReason


async def dispute_review(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    review_id: str,
    body: DisputeIn,
) -> DisputeOut:
    try:
        async with conn.transaction():
            await conn.fetchval("SELECT vyapar_reviews.open_dispute($1, $2)", review_id, body.reason)
    except asyncpg.DataError:
        raise ApiError(404, "reviews.error.reviewNotFound", lang)
    except asyncpg.RaiseError as exc:
        message = str(exc)
        if "already_disputed" in message:
            raise ApiError(409, "reviews.error.alreadyDisputed", lang)
        if "not_disputable" in message:
            raise ApiError(400, "reviews.error.notDisputable", lang)
        raise ApiError(403, "reviews.error.notSubject", lang)
    return DisputeOut(state="disputed")


async def list_listing_reviews_page(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    limit: int = DEFAULT_LIMIT,
    cursor: str | None = None, listing_id: str = "",
) -> Page[ListingReviewOut]:
    """[Refactor A] Cursor-paged `list_listing_reviews` — same rows, same order."""
    return paginate(await list_listing_reviews(conn, ctx, listing_id=listing_id), limit, cursor, lang)

# [TR027/TR028/TR029] Reviews: invite status, submit, list, dispute — HTTP
# front door only. Rules and queries live in app/services/reviews.py.
# Traces to: FR27, FR28, FR29, TR027, TR028, TR029, SP027, SP028, SP029
from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends, Query, Header

from app.db import get_conn
from app.deps import Locale
from app.errors import ERROR_RESPONSES
from app.identity import AuthzContext, resolve_authz_context
from app.services import reviews as svc
from app.services.reviews import (  # noqa: F401  schemas used below; background passes re-exported for main.py
    DisputeIn,
    DisputeOut,
    InteractionKind,
    ListingReviewOut,
    ReviewCreatedOut,
    ReviewIn,
    ReviewInviteStatusOut,
)
from app.services.pagination import DEFAULT_LIMIT, MAX_LIMIT, Page

router = APIRouter(tags=["reviews"], responses=ERROR_RESPONSES)


@router.get("/v1/reviews/invite/{interaction_kind}/{interaction_id}", response_model=ReviewInviteStatusOut, operation_id="getReviewInviteStatus", summary="Get whether the member may review an interaction")
async def get_invite_status(
    interaction_kind: InteractionKind,
    interaction_id: str,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> ReviewInviteStatusOut:
    return await svc.get_review_invite_status(conn, ctx, interaction_kind=interaction_kind, interaction_id=interaction_id)


@router.post("/v1/reviews", status_code=201, response_model=ReviewCreatedOut, operation_id="createReview", summary="Submit a review for an interaction")
async def submit_review(
    body: ReviewIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> ReviewCreatedOut:
    return await svc.create_review(conn, ctx, lang, body=body, idempotency_key=idempotency_key)


@router.get("/v1/listings/{listing_id}/reviews", response_model=list[ListingReviewOut], operation_id="listListingReviews", summary="List published reviews for a listing")
async def list_listing_reviews(
    listing_id: str,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[ListingReviewOut]:
    return await svc.list_listing_reviews(conn, ctx, listing_id=listing_id)


@router.get("/v1/listings/{listing_id}/reviews/page", response_model=Page[ListingReviewOut], operation_id="listListingReviewsPage", summary="List published reviews for a listing, one page at a time")
async def list_listing_reviews_page(
    listing_id: str,
    lang: Locale,
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    cursor: str | None = None,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> Page[ListingReviewOut]:
    return await svc.list_listing_reviews_page(conn, ctx, lang, limit=limit, cursor=cursor, listing_id=listing_id)


@router.post("/v1/reviews/{review_id}/dispute", status_code=201, response_model=DisputeOut, operation_id="disputeReview", summary="Dispute a review (listing owner)")
async def dispute_review(
    review_id: str,
    body: DisputeIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> DisputeOut:
    return await svc.dispute_review(conn, ctx, lang, review_id=review_id, body=body)

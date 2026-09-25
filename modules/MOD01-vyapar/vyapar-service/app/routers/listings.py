# [TR001-TR007] Listings: create/edit, contact disclosure, intent visibility,
# lifecycle, contact OTP and credential reference — HTTP front door only.
# Every rule and query lives in app/services/listings.py (see its header).
# Traces to: FR01, FR02, FR03, FR04, FR05, FR06, FR07, FR16, FR55, TR001, TR002, TR003, TR004, TR005, TR006, TR007
from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends, Query

from app.db import get_conn
from app.deps import Locale
from app.errors import ERROR_RESPONSES
from app.identity import AuthzContext, resolve_authz_context
from app.profile_cards import ProfileCard
from app.services import listings as svc
from app.services.listings import (  # noqa: F401  schemas used below; background passes re-exported for main.py
    ContactsPatch,
    IntentPatch,
    ListingCreate,
    ListingOut,
    ListingPatch,
    OtpRequestIn,
    OtpRequestOut,
    OtpVerifyIn,
    OtpVerifyOut,
    VisibilityPatch,
    sync_credential_refs,
)
from app.services.pagination import DEFAULT_LIMIT, MAX_LIMIT, Page

router = APIRouter(prefix="/v1/listings", tags=["listings"], responses=ERROR_RESPONSES)


@router.post("", response_model=ListingOut, status_code=201, operation_id="createListing", summary="Create a business or professional listing")
async def create_listing(
    body: ListingCreate,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> ListingOut:
    return await svc.create_listing(conn, ctx, lang, body=body)


@router.get("/mine", response_model=list[ListingOut], operation_id="listMyListings", summary="List the signed-in member's own listings")
async def list_my_listings(
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[ListingOut]:
    return await svc.list_my_listings(conn, ctx, lang)


@router.get("/mine/page", response_model=Page[ListingOut], operation_id="listMyListingsPage", summary="List the signed-in member's own listings, one page at a time")
async def list_my_listings_page(
    lang: Locale,
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    cursor: str | None = None,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> Page[ListingOut]:
    return await svc.list_my_listings_page(conn, ctx, lang, limit=limit, cursor=cursor)


@router.get("/{listing_id}", response_model=ListingOut, operation_id="getListing", summary="Get one listing's profile")
async def get_listing(
    listing_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> ListingOut:
    return await svc.get_listing(conn, ctx, lang, listing_id=listing_id)


@router.get("/{listing_id}/similar", response_model=list[ProfileCard], operation_id="listSimilarProfiles", summary="List profiles similar to a listing")
async def similar_profiles(
    listing_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[ProfileCard]:
    return await svc.list_similar_profiles(conn, ctx, lang, listing_id=listing_id)


@router.post("/{listing_id}/save", response_model=ListingOut, operation_id="saveListing", summary="Save a listing")
async def save_listing(
    listing_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> ListingOut:
    return await svc.save_listing(conn, ctx, lang, listing_id=listing_id)


@router.delete("/{listing_id}/save", response_model=ListingOut, operation_id="unsaveListing", summary="Remove a listing from saved")
async def unsave_listing(
    listing_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> ListingOut:
    return await svc.unsave_listing(conn, ctx, lang, listing_id=listing_id)


@router.patch("/{listing_id}", response_model=ListingOut, operation_id="updateListing", summary="Update a listing's details")
async def patch_listing(
    listing_id: str,
    body: ListingPatch,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> ListingOut:
    return await svc.update_listing(conn, ctx, lang, listing_id=listing_id, body=body)


@router.patch("/{listing_id}/contacts", response_model=ListingOut, operation_id="updateListingContacts", summary="Update a listing's contact channels")
async def patch_contacts(
    listing_id: str,
    body: ContactsPatch,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> ListingOut:
    return await svc.update_listing_contacts(conn, ctx, lang, listing_id=listing_id, body=body)


@router.patch("/{listing_id}/visibility", response_model=ListingOut, operation_id="updateListingVisibility", summary="Update a listing's visibility")
async def patch_visibility(
    listing_id: str,
    body: VisibilityPatch,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> ListingOut:
    return await svc.update_listing_visibility(conn, ctx, lang, listing_id=listing_id, body=body)


@router.patch("/{listing_id}/intent", response_model=ListingOut, operation_id="updateListingIntent", summary="Update a listing's intent (what it is looking for)")
async def patch_intent(
    listing_id: str,
    body: IntentPatch,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> ListingOut:
    return await svc.update_listing_intent(conn, ctx, lang, listing_id=listing_id, body=body)


@router.post("/{listing_id}/submit", response_model=ListingOut, operation_id="submitListing", summary="Submit a draft listing for publishing")
async def submit_listing(
    listing_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> ListingOut:
    return await svc.submit_listing(conn, ctx, lang, listing_id=listing_id)


@router.post("/{listing_id}/archive", response_model=ListingOut, operation_id="archiveListing", summary="Archive a listing")
async def archive_listing(
    listing_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> ListingOut:
    return await svc.archive_listing(conn, ctx, lang, listing_id=listing_id)


@router.post("/{listing_id}/suspend", response_model=ListingOut, operation_id="suspendListing", summary="Suspend a listing")
async def suspend_listing(
    listing_id: str,
    reason: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> ListingOut:
    return await svc.suspend_listing(conn, ctx, lang, listing_id=listing_id, reason=reason)


@router.post("/{listing_id}/otp/request", response_model=OtpRequestOut, operation_id="requestListingContactOtp", summary="Request an OTP to verify a listing contact")
async def request_otp(
    listing_id: str,
    body: OtpRequestIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> OtpRequestOut:
    return await svc.request_listing_contact_otp(conn, ctx, lang, listing_id=listing_id, body=body)


@router.post("/{listing_id}/otp/verify", response_model=OtpVerifyOut, operation_id="verifyListingContactOtp", summary="Verify a listing contact with an OTP")
async def verify_otp(
    listing_id: str,
    body: OtpVerifyIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> OtpVerifyOut:
    return await svc.verify_listing_contact_otp(conn, ctx, lang, listing_id=listing_id, body=body)


@router.post("/{listing_id}/credential-ref/attach", response_model=ListingOut, operation_id="attachListingCredentialRef", summary="Attach a platform credential reference to a listing")
async def attach_credential_ref(
    listing_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> ListingOut:
    return await svc.attach_listing_credential_ref(conn, ctx, lang, listing_id=listing_id)

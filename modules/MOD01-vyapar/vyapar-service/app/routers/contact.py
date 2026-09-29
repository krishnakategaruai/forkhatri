# [IMP-B] Contact preferences, contact actions and contact attempts — HTTP
# front door only. Rules live in app/services/contact.py.
#
# Path note: the member-level preferences sit under /v1/listings/ (a static
# path, registered BEFORE listings.router so "/v1/listings/{listing_id}"
# cannot swallow it — the same static-before-dynamic rule main.py already
# applies to /v1/listings/search). They govern how people reach the member
# through any of their listings and opportunities, and the listings:write
# scope is the one an agent holds for "how my profile is presented".
# Traces to: FR02, FR22, FR24, TR002, TR024
from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends

from app.db import get_conn
from app.deps import Locale
from app.errors import ERROR_RESPONSES
from app.identity import AuthzContext, resolve_authz_context
from app.services import contact as svc
from app.services.contact import (  # noqa: F401
    ContactActionsOut,
    ContactAttemptIn,
    ContactAttemptOut,
    ContactPreferencesOut,
    ContactPreferencesPatch,
    ListingContactPreferencesOut,
    PrecallActionsOut,
    PrecallAttemptOut,
)

router = APIRouter(tags=["contact"], responses=ERROR_RESPONSES)


@router.get("/v1/listings/contact-preferences", response_model=ContactPreferencesOut, operation_id="getContactPreferences", summary="Get how the member allows others to call or message them")
async def get_contact_preferences(
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> ContactPreferencesOut:
    return await svc.get_member_contact_preferences(conn, ctx)


@router.patch("/v1/listings/contact-preferences", response_model=ContactPreferencesOut, operation_id="updateContactPreferences", summary="Update the member's call hours, days, daily cap and channels")
async def update_contact_preferences(
    body: ContactPreferencesPatch,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> ContactPreferencesOut:
    return await svc.update_member_contact_preferences(conn, ctx, lang, body=body)


@router.get("/v1/listings/{listing_id}/contact-preferences", response_model=ListingContactPreferencesOut, operation_id="getListingContactPreferences", summary="Get one listing's contact preferences (owner)")
async def get_listing_contact_preferences(
    listing_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> ListingContactPreferencesOut:
    return await svc.get_listing_contact_preferences(conn, ctx, lang, listing_id=listing_id)


@router.patch("/v1/listings/{listing_id}/contact-preferences", response_model=ListingContactPreferencesOut, operation_id="updateListingContactPreferences", summary="Override contact preferences for one listing (owner)")
async def update_listing_contact_preferences(
    listing_id: str,
    body: ContactPreferencesPatch,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> ListingContactPreferencesOut:
    return await svc.update_listing_contact_preferences(conn, ctx, lang, listing_id=listing_id, body=body)


@router.get("/v1/enquiries/{enquiry_id}/contact-actions", response_model=ContactActionsOut, operation_id="getEnquiryContactActions", summary="Call / WhatsApp actions for an accepted enquiry, per the other person's preferences")
async def get_enquiry_contact_actions(
    enquiry_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> ContactActionsOut:
    return await svc.contact_actions_for_enquiry(conn, ctx, lang, enquiry_id=enquiry_id)


@router.get("/v1/enquiries/{enquiry_id}/contact-attempts", response_model=list[ContactAttemptOut], operation_id="listContactAttempts", summary="Who called or messaged whom on this enquiry, and when")
async def list_contact_attempts(
    enquiry_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> list[ContactAttemptOut]:
    return await svc.list_contact_attempts(conn, ctx, lang, enquiry_id=enquiry_id)


@router.post("/v1/enquiries/{enquiry_id}/contact-attempts", response_model=ContactActionsOut, status_code=201, operation_id="recordContactAttempt", summary="Record that the member is calling or messaging the other person now")
async def record_contact_attempt(
    enquiry_id: str,
    body: ContactAttemptIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> ContactActionsOut:
    return await svc.record_contact_attempt(conn, ctx, lang, enquiry_id=enquiry_id, body=body)


# [IMP-B/L1] Pre-accept calling. Registered before opportunities.router (main.py
# includes contact_router first); both paths have a fixed suffix, so they never
# collide with /v1/opportunities/{opportunity_id}.
@router.get("/v1/opportunities/{opportunity_id}/contact-actions", response_model=PrecallActionsOut, operation_id="getOpportunityContactActions", summary="Call / WhatsApp the poster before an application is accepted (when the post allows it)")
async def get_opportunity_contact_actions(
    opportunity_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> PrecallActionsOut:
    return await svc.opportunity_contact_actions(conn, ctx, lang, opportunity_id=opportunity_id)


@router.post("/v1/opportunities/{opportunity_id}/contact-attempts", response_model=PrecallAttemptOut, status_code=201, operation_id="recordOpportunityContactAttempt", summary="Record a pre-accept call or WhatsApp tap on an opportunity")
async def record_opportunity_contact_attempt(
    opportunity_id: str,
    body: ContactAttemptIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> PrecallAttemptOut:
    return await svc.record_opportunity_contact_attempt(conn, ctx, lang, opportunity_id=opportunity_id, body=body)

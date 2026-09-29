# [TR011/TR012/TR013/TR014/TR055] Opportunity Composer, field confirmation,
# lifecycle and save/hide/share — HTTP front door only. Every rule and query
# lives in app/services/opportunities.py (see its header for the approach).
# Traces to: FR11, FR12, FR13, FR14, FR55, TR011, TR012, TR013, TR014, TR055
from __future__ import annotations

from typing import Literal

import asyncpg
from fastapi import APIRouter, Depends, Query

from app.db import get_conn
from app.deps import Locale
from app.errors import ERROR_RESPONSES
from app.identity import AuthzContext, resolve_authz_context
from app.profile_cards import ProfileCard
from app.services import opportunities as svc
from app.services.opportunities import (  # noqa: F401  schemas used below; background passes re-exported for main.py
    ConfirmFieldsIn,
    HiddenOut,
    NotInterestedIn,
    OpenedOut,
    OpportunityCreate,
    OpportunityOut,
    OpportunityPatch,
    SharedOut,
    SuggestionsOut,
)
from app.services import applicants as applicants_svc
from app.services.applicants import ApplicantOut, ApplicantPage, CompareOut, Stage, StageIn
from app.services.contact import ContactAttemptIn
from app.services.pagination import DEFAULT_LIMIT, MAX_LIMIT, Page

router = APIRouter(prefix="/v1/opportunities", tags=["opportunities"], responses=ERROR_RESPONSES)


@router.post("", response_model=OpportunityOut, status_code=201, operation_id="createOpportunity", summary="Create an opportunity draft")
async def create_opportunity(
    body: OpportunityCreate,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> OpportunityOut:
    return await svc.create_opportunity(conn, ctx, lang, body=body)


@router.get("/mine", response_model=list[OpportunityOut], operation_id="listMyOpportunities", summary="List opportunities posted by the signed-in member")
async def list_my_opportunities(
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> list[OpportunityOut]:
    return await svc.list_my_opportunities(conn, ctx)


@router.get("/mine/page", response_model=Page[OpportunityOut], operation_id="listMyOpportunitiesPage", summary="List opportunities posted by the signed-in member, one page at a time")
async def list_my_opportunities_page(
    lang: Locale,
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    cursor: str | None = None,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> Page[OpportunityOut]:
    return await svc.list_my_opportunities_page(conn, ctx, lang, limit=limit, cursor=cursor)


@router.get("/{opportunity_id}", response_model=OpportunityOut, operation_id="getOpportunity", summary="Get one opportunity with decision context")
async def get_opportunity(
    opportunity_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> OpportunityOut:
    return await svc.get_opportunity(conn, ctx, lang, opportunity_id=opportunity_id)


@router.get("/{opportunity_id}/similar", response_model=list[OpportunityOut], operation_id="listSimilarOpportunities", summary="List opportunities similar to one opportunity")
async def similar_opportunities(
    opportunity_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> list[OpportunityOut]:
    return await svc.list_similar_opportunities(conn, ctx, lang, opportunity_id=opportunity_id)


@router.get("/{opportunity_id}/matching-profiles", response_model=list[ProfileCard], operation_id="listMatchingProfiles", summary="List profiles matching an opportunity (poster only)")
async def matching_profiles(
    opportunity_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> list[ProfileCard]:
    return await svc.list_matching_profiles(conn, ctx, lang, opportunity_id=opportunity_id)


@router.patch("/{opportunity_id}", response_model=OpportunityOut, operation_id="updateOpportunity", summary="Update an opportunity")
async def patch_opportunity(
    opportunity_id: str,
    body: OpportunityPatch,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> OpportunityOut:
    return await svc.update_opportunity(conn, ctx, lang, opportunity_id=opportunity_id, body=body)


@router.patch("/{opportunity_id}/confirm", response_model=OpportunityOut, operation_id="confirmOpportunityFields", summary="Confirm inferred opportunity fields")
async def confirm_fields(
    opportunity_id: str,
    body: ConfirmFieldsIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> OpportunityOut:
    return await svc.confirm_opportunity_fields(conn, ctx, lang, opportunity_id=opportunity_id, body=body)


@router.post("/{opportunity_id}/publish", response_model=OpportunityOut, operation_id="publishOpportunity", summary="Publish a draft opportunity")
async def publish_opportunity(
    opportunity_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> OpportunityOut:
    return await svc.publish_opportunity(conn, ctx, lang, opportunity_id=opportunity_id)


@router.post("/{opportunity_id}/pause", response_model=OpportunityOut, operation_id="pauseOpportunity", summary="Pause an opportunity")
async def pause_opportunity(opportunity_id: str, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> OpportunityOut:
    return await svc.pause_opportunity(conn, ctx, lang, opportunity_id=opportunity_id)


@router.post("/{opportunity_id}/resume", response_model=OpportunityOut, operation_id="resumeOpportunity", summary="Resume a paused opportunity")
async def resume_opportunity(opportunity_id: str, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> OpportunityOut:
    return await svc.resume_opportunity(conn, ctx, lang, opportunity_id=opportunity_id)


@router.post("/{opportunity_id}/close", response_model=OpportunityOut, operation_id="closeOpportunity", summary="Close an opportunity")
async def close_opportunity(opportunity_id: str, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> OpportunityOut:
    return await svc.close_opportunity(conn, ctx, lang, opportunity_id=opportunity_id)


@router.post("/{opportunity_id}/renew", response_model=OpportunityOut, operation_id="renewOpportunity", summary="Renew a stale or expired opportunity")
async def renew_opportunity(opportunity_id: str, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> OpportunityOut:
    return await svc.renew_opportunity(conn, ctx, lang, opportunity_id=opportunity_id)


@router.post("/{opportunity_id}/save", response_model=OpportunityOut, operation_id="saveOpportunity", summary="Save an opportunity")
async def save_opportunity(opportunity_id: str, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> OpportunityOut:
    return await svc.save_opportunity(conn, ctx, lang, opportunity_id=opportunity_id)


@router.delete("/{opportunity_id}/save", response_model=OpportunityOut, operation_id="unsaveOpportunity", summary="Remove an opportunity from saved")
async def unsave_opportunity(opportunity_id: str, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> OpportunityOut:
    return await svc.unsave_opportunity(conn, ctx, lang, opportunity_id=opportunity_id)


@router.post("/{opportunity_id}/not-interested", response_model=HiddenOut, operation_id="markOpportunityNotInterested", summary="Hide an opportunity as not interested")
async def not_interested(opportunity_id: str, body: NotInterestedIn, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> HiddenOut:
    return await svc.mark_opportunity_not_interested(conn, ctx, opportunity_id=opportunity_id, body=body)


@router.post("/{opportunity_id}/share", response_model=SharedOut, operation_id="shareOpportunity", summary="Record that the member shared an opportunity")
async def share_opportunity(opportunity_id: str, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> SharedOut:
    return await svc.share_opportunity(conn, ctx, lang, opportunity_id=opportunity_id)


@router.post("/{opportunity_id}/external-open", response_model=OpenedOut, operation_id="recordOpportunityExternalOpen", summary="Record that the member opened an opportunity's external source")
async def external_open(opportunity_id: str, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> OpenedOut:
    return await svc.record_opportunity_external_open(conn, ctx, opportunity_id=opportunity_id)


# ---------------------------------------------------------------------------
# [Backend A, 2026-09-28] Posting suggestions and the poster's applicant
# pipeline. Rules live in app/services/opportunities.py (suggestions) and
# app/services/applicants.py (list, compare, stage).
# ---------------------------------------------------------------------------
@router.get("/{opportunity_id}/suggestions", response_model=SuggestionsOut, operation_id="getOpportunitySuggestions", summary="Tips to get more or better responses (poster only)")
async def opportunity_suggestions(opportunity_id: str, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> SuggestionsOut:
    return await svc.get_opportunity_suggestions(conn, ctx, lang, opportunity_id=opportunity_id)


@router.get("/{opportunity_id}/applicants", response_model=ApplicantPage, operation_id="listOpportunityApplicants", summary="List applicants and proposals on an opportunity (poster only)")
async def list_applicants(
    opportunity_id: str,
    lang: Locale,
    stage: Stage | None = None,
    sort: Literal["newest", "match"] = "newest",
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    cursor: str | None = None,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> ApplicantPage:
    return await applicants_svc.list_opportunity_applicants(
        conn, ctx, lang, opportunity_id=opportunity_id, stage=stage, sort=sort, limit=limit, cursor=cursor
    )


@router.get("/{opportunity_id}/applicants/compare", response_model=CompareOut, operation_id="compareApplicants", summary="Compare 2 to 4 applicants side by side (poster only)")
async def compare_applicants(
    opportunity_id: str,
    lang: Locale,
    ids: str = Query(description="Comma-separated enquiry ids (2 to 4)"),
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> CompareOut:
    return await applicants_svc.compare_applicants(conn, ctx, lang, opportunity_id=opportunity_id, ids=[i.strip() for i in ids.split(",")])


@router.post("/{opportunity_id}/applicants/{enquiry_id}/stage", response_model=ApplicantOut, operation_id="setApplicantStage", summary="Move an applicant to shortlisted, hired or declined (poster only)")
async def set_applicant_stage(
    opportunity_id: str,
    enquiry_id: str,
    body: StageIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> ApplicantOut:
    return await applicants_svc.set_applicant_stage(conn, ctx, lang, opportunity_id=opportunity_id, enquiry_id=enquiry_id, body=body)


@router.post("/{opportunity_id}/applicants/{enquiry_id}/contact-attempts", response_model=ApplicantOut, status_code=201, operation_id="recordApplicantContactAttempt", summary="Record that the poster called or messaged a shortlisted or hired applicant")
async def record_applicant_contact_attempt(
    opportunity_id: str,
    enquiry_id: str,
    body: ContactAttemptIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> ApplicantOut:
    return await applicants_svc.record_applicant_contact_attempt(conn, ctx, lang, opportunity_id=opportunity_id, enquiry_id=enquiry_id, body=body)

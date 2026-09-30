# [Trust pack, 2026-09-30] HTTP front door for VISION-2040 items 1-5: the
# scam-shield pre-check, profession rules, council credentials, "paid on
# time", the member's restrictions with their appeal path, the poster's
# close check, and the dev trigger for the hourly trust pass. Rules live in
# app/services/{scam_shield,profession_rules,credentials,paid_on_time,
# restrictions,close_loop,trust_jobs}.py. Contract: references/imp-trust-pack.md.
from __future__ import annotations

from typing import Literal

import asyncpg
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.config import get_settings
from app.db import get_conn, get_pool
from app.deps import Locale
from app.errors import ERROR_RESPONSES, ApiError
from app.identity import AuthzContext, resolve_authz_context
from app.services import close_loop, credentials, paid_on_time, profession_rules, restrictions, scam_shield, trust_jobs

router = APIRouter(tags=["trust"], responses=ERROR_RESPONSES)


# ---------------------------------------------------------------- scam shield
class ScamCheckIn(BaseModel):
    text: str = Field(default="", max_length=5000)
    surface: Literal["opportunity", "enquiry_reply", "package"] = "opportunity"
    opportunity_type: str | None = Field(default=None, description="For opportunity text and replies: employment | freelance | local_service | ...")


class ScamCheckOut(BaseModel):
    allowed: bool
    code: str | None = None
    message: str | None = None
    explanation: str | None = None
    rule: str | None = None
    matched: str | None = None


@router.post("/v1/trust/scam-check", response_model=ScamCheckOut, operation_id="checkScamShield",
             summary="Check text a poster is about to send for a charge on applicants (never raises; nothing is stored)")
async def check_scam_shield(body: ScamCheckIn, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context)) -> ScamCheckOut:
    from app.services.trust_safety import HIRING_TYPES

    if body.surface == "package":
        tier = "offer"
    else:
        tier = "hiring" if (body.opportunity_type or "employment") in HIRING_TYPES else "offer"
    match = scam_shield.detect(body.text, tier)
    if match is None:
        return ScamCheckOut(allowed=True)
    exc = scam_shield.refuse(match, lang, field="text", opportunity_type=body.opportunity_type, surface=body.surface)
    return ScamCheckOut(allowed=False, code=exc.code, message=exc.message, explanation=exc.extra.get("explanation"),
                        rule=match.rule, matched=match.matched)


# ---------------------------------------------------------------- profession rules
@router.get("/v1/profession-rules", response_model=list[profession_rules.ProfessionRuleOut], operation_id="listProfessionRules",
            summary="What each regulated profession may show and buy on Vyapar (council rules, as configured)")
async def list_profession_rules(lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context)) -> list[profession_rules.ProfessionRuleOut]:
    return profession_rules.list_rules_out(lang)


# ---------------------------------------------------------------- council credentials
@router.get("/v1/credentials/types", response_model=list[credentials.CredentialTypeOut], operation_id="listCredentialTypes",
            summary="Council registers a professional can add, with number formats")
async def list_credential_types(lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context)) -> list[credentials.CredentialTypeOut]:
    return credentials.list_credential_types(lang)


@router.get("/v1/me/profile/credentials", response_model=list[credentials.CredentialOut], operation_id="listMyCredentials",
            summary="My council register entries, with their check status")
async def list_my_credentials(lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context),
                              conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> list[credentials.CredentialOut]:
    return await credentials.list_my_credentials(conn, ctx, lang)


@router.post("/v1/me/profile/credentials", response_model=credentials.CredentialOut, status_code=201, operation_id="addCredential",
             summary="Add a council register entry (ICAI, medical council, NCAHP, Bar Council, CoA, DigiLocker) to my profile")
async def add_credential(body: credentials.CredentialIn, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context),
                         conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> credentials.CredentialOut:
    return await credentials.add_credential(conn, ctx, lang, body)


@router.post("/v1/me/profile/credentials/{credential_id}/recheck", response_model=credentials.CredentialOut, operation_id="recheckCredential",
             summary="Ask for a register entry to be checked again")
async def recheck_credential(credential_id: str, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context),
                             conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> credentials.CredentialOut:
    return await credentials.recheck_credential(conn, ctx, lang, credential_id)


@router.delete("/v1/me/profile/credentials/{credential_id}", response_model=credentials.DeletedOut, operation_id="deleteCredential",
               summary="Remove a register entry from my profile")
async def delete_credential(credential_id: str, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context),
                            conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> credentials.DeletedOut:
    return await credentials.delete_credential(conn, ctx, lang, credential_id)


# ---------------------------------------------------------------- paid on time
@router.get("/v1/paid-on-time/asks", response_model=list[paid_on_time.PaidOnTimeAskOut], operation_id="listMyPaidOnTimeAsks",
            summary='My "Were you paid on time?" questions (open ones by default)')
async def list_my_asks(lang: Locale, state: Literal["open", "all"] = Query(default="open"),
                       ctx: AuthzContext = Depends(resolve_authz_context),
                       conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> list[paid_on_time.PaidOnTimeAskOut]:
    return await paid_on_time.list_my_asks(conn, ctx, lang, state)


@router.post("/v1/paid-on-time/asks/{ask_id}/answer", response_model=paid_on_time.PaidOnTimeAskOut, operation_id="answerPaidOnTime",
             summary='Answer "Were you paid on time?" (Yes or No, once; only the person who was paid)')
async def answer_paid_on_time(ask_id: str, body: paid_on_time.AnswerIn, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context),
                              conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> paid_on_time.PaidOnTimeAskOut:
    return await paid_on_time.answer(conn, ctx, lang, ask_id, body)


@router.get("/v1/members/{member_id}/paid-on-time", response_model=paid_on_time.PaidOnTimeSummary, operation_id="getMemberPaidOnTime",
            summary='A payer\'s "Paid on time: 12 of 13" (shown only after 3 answers)')
async def get_member_paid_on_time(member_id: str, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context),
                                  conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> paid_on_time.PaidOnTimeSummary:
    return await paid_on_time.get_member_summary(conn, ctx, lang, member_id)


# ---------------------------------------------------------------- restrictions and appeals
@router.get("/v1/me/restrictions", response_model=list[restrictions.RestrictionOut], operation_id="listMyRestrictions",
            summary="Everything of mine the platform restricts now, why, and how to appeal to a person")
async def list_my_restrictions(lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context),
                               conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> list[restrictions.RestrictionOut]:
    return await restrictions.list_my_restrictions(conn, ctx, lang)


# ---------------------------------------------------------------- close the loop
@router.get("/v1/opportunities/{opportunity_id}/close-check", response_model=close_loop.CloseCheckOut, operation_id="getOpportunityCloseCheck",
            summary="Before closing: how many applicants are still waiting, and what closing tells them (poster only)")
async def get_close_check(opportunity_id: str, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context),
                          conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> close_loop.CloseCheckOut:
    return await close_loop.get_close_check(conn, ctx, lang, opportunity_id)


# ---------------------------------------------------------------- dev trigger
@router.post("/v1/trust/jobs/run", response_model=trust_jobs.TrustPassOut, operation_id="runTrustPass",
             summary="Run the hourly trust pass now (dev only; runs hourly anyway)")
async def run_trust_pass(lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context)) -> trust_jobs.TrustPassOut:
    if not get_settings().dev_mode:
        raise ApiError(404, "opportunities.error.devOnly", lang)
    return trust_jobs.TrustPassOut(**await trust_jobs.run_trust_pass(get_pool()))

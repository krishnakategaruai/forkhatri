# [IMP42 — Refactor C (AI)] AI assistance — HTTP front door only. Every rule,
# query, validation and audit row lives in app/services/ai.py (see its header).
# Nothing here writes an opportunity or an enquiry: the answers are drafts
# and suggestions the person confirms through the existing endpoints.
# Traces to: FR11, FR12, FR18, FR19, FR22, REFACTOR-PLAN.md (AI workstream C)
from __future__ import annotations

from typing import Literal

import asyncpg
from fastapi import APIRouter, Depends, Query

from app.db import get_conn
from app.deps import Locale
from app.errors import ERROR_RESPONSES
from app.identity import AuthzContext, resolve_authz_context
from app.services import ai as svc
from app.services.ai import DraftOut, DraftRequest, ImageRequest, ProposalOut, ProposalRequest, ShortlistOut, TipsOut, TipsRequest

AI_RESPONSES = {
    **ERROR_RESPONSES,
    429: {**ERROR_RESPONSES[429], "description": "The member's daily AI allowance is used up (code ai_limit_reached)"},
    501: {"model": ERROR_RESPONSES[404]["model"], "description": "Needs the AI provider; the rules engine cannot do this (code unsupported_without_ai)"},
    503: {"model": ERROR_RESPONSES[404]["model"], "description": "The AI provider did not answer and there is no fallback for this operation"},
}

router = APIRouter(prefix="/v1", tags=["ai"], responses=AI_RESPONSES)


@router.post("/ai/draft-opportunity", response_model=DraftOut, operation_id="draftOpportunity", summary="Draft an opportunity from free text (typed or dictated), in English, Hindi, Telugu or Hinglish")
async def draft_opportunity(
    body: DraftRequest,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> DraftOut:
    return await svc.draft_opportunity(conn, ctx, lang, body)


@router.post("/ai/read-opportunity-image", response_model=DraftOut, operation_id="readOpportunityImage", summary="Draft an opportunity from a photo or PDF of a notice (needs the AI provider)")
async def read_opportunity_image(
    body: ImageRequest,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> DraftOut:
    return await svc.read_opportunity_image(conn, ctx, lang, body)


@router.get("/opportunities/{opportunity_id}/ai-shortlist", response_model=ShortlistOut, operation_id="getAiShortlist", summary="Rank the applicants to one opportunity 1–10 with reasons and risks (poster only)")
async def get_ai_shortlist(
    opportunity_id: str,
    lang: Locale,
    language: Literal["en", "hi", "te", "mr", "kn"] | None = Query(default=None, description="Answer language; defaults to the request locale"),
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> ShortlistOut:
    return await svc.get_ai_shortlist(conn, ctx, lang, opportunity_id, language)


@router.post("/ai/posting-tips", response_model=TipsOut, operation_id="getPostingTips", summary="Tips that would get a draft or a posted opportunity more responses")
async def get_posting_tips(
    body: TipsRequest,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> TipsOut:
    return await svc.get_posting_tips(conn, ctx, lang, body)


@router.post("/ai/improve-proposal", response_model=ProposalOut, operation_id="improveProposal", summary="Suggest a better cover text and a bid range for applying to an opportunity")
async def improve_proposal(
    body: ProposalRequest,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> ProposalOut:
    return await svc.improve_proposal(conn, ctx, lang, body)

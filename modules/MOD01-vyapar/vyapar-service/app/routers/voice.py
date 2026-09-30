# [Voice interview, 2026-09-30] HTTP front door only. Rules, readers and
# wording live in app/services/voice_interview.py (see its header). Nothing
# here writes: the interview ends with a draft the person reviews and then
# posts (createOpportunity) or saves (PATCH /v1/me/profile) themselves.
# Access tokens need only the `read` scope (app/integrations/identity/scopes.py).
# Traces to: FR01, FR11, FR12, FR44
from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends

from app.db import get_conn
from app.deps import Locale
from app.errors import ERROR_RESPONSES
from app.identity import AuthzContext, resolve_authz_context
from app.services import voice_interview as svc
from app.services.voice_interview import InterviewInterpretOut, InterviewInterpretRequest, InterviewNextOut, InterviewNextRequest

router = APIRouter(prefix="/v1/voice/interview", tags=["voice"], responses=ERROR_RESPONSES)


@router.post("/next", response_model=InterviewNextOut, operation_id="nextInterviewQuestion",
             summary="The next spoken question for what is still missing, or the finished summary and draft")
async def next_interview_question(
    body: InterviewNextRequest,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> InterviewNextOut:
    return await svc.next_question(conn, ctx, lang, body)


@router.post("/interpret", response_model=InterviewInterpretOut, operation_id="interpretInterviewAnswer",
             summary="Read one spoken answer: its typed value, a read-back to confirm, or what to ask again")
async def interpret_interview_answer(
    body: InterviewInterpretRequest,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> InterviewInterpretOut:
    return await svc.interpret_answer(conn, ctx, lang, body)

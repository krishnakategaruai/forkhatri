# [Backend A, 2026-09-30] The member's one Vyapar profile — HTTP front door
# only. Rules live in app/services/profile.py.
# Traces to: FR01, FR03, FR44, TR050, owner decision 2026-09-30
from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends

from app.db import get_conn
from app.deps import Locale
from app.errors import ERROR_RESPONSES
from app.identity import AuthzContext, resolve_authz_context
from app.services import profile as svc
from app.services.profile import CompletionOut, LocateIn, LocateOut, MyProfileOut, ProfilePatch

router = APIRouter(prefix="/v1/me/profile", tags=["profile"], responses=ERROR_RESPONSES)


@router.get("", response_model=MyProfileOut, operation_id="getMyProfile", summary="The member's one profile, created from the ForKhatri identity on first read")
async def get_my_profile(lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> MyProfileOut:
    return await svc.get_my_profile(conn, ctx, lang)


@router.patch("", response_model=MyProfileOut, operation_id="updateMyProfile", summary="Update the member's profile, including its business section")
async def update_my_profile(body: ProfilePatch, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> MyProfileOut:
    return await svc.update_my_profile(conn, ctx, lang, body)


@router.post("/locate", response_model=LocateOut, operation_id="locateMyProfile", summary="Nearest known locality for the browser's current position, with nearby areas for one-tap chips")
async def locate(body: LocateIn, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> LocateOut:
    return await svc.locate(conn, body, lang)


@router.get("/completion", response_model=CompletionOut, operation_id="getMyProfileCompletion", summary="How complete the profile is, and the one next question to ask (never blocking)")
async def completion(lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> CompletionOut:
    return await svc.profile_completion(conn, ctx, lang)

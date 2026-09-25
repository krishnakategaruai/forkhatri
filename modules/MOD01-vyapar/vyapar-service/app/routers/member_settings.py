# [Product-owner standing i18n rule, 2026-09-15] The member's own basic
# settings and language choice — HTTP front door only; see
# app/services/member_settings.py.
# Traces to: product-owner i18n rule, 2026-09-15 (not a numbered FR)
from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends

from app.db import get_conn
from app.deps import Locale
from app.errors import ERROR_RESPONSES
from app.services import member_settings as svc
from app.services.member_settings import LanguageOut, LanguagePatch, MemberMeOut

router = APIRouter(prefix="/v1/members/me", tags=["member-settings"], responses=ERROR_RESPONSES)


@router.get("", response_model=MemberMeOut, operation_id="getMe", summary="Get the signed-in member's basic settings")
async def get_me(lang: Locale, conn: asyncpg.Connection = Depends(get_conn)) -> MemberMeOut:
    return await svc.get_me(conn, lang)


@router.patch("/language", response_model=LanguageOut, operation_id="setMemberLanguage", summary="Set the signed-in member's preferred language")
async def set_member_language(body: LanguagePatch, conn: asyncpg.Connection = Depends(get_conn)) -> LanguageOut:
    return await svc.set_member_language(conn, body.language)

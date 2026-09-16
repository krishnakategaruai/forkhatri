# [Product-owner standing i18n rule, 2026-09-15] Persists the member's
# language choice server-side (`members.language`, already modeled and
# already read by `resolve_language`'s `X-Vyapar-Language` header override
# on every subsequent request) so the preference survives across devices —
# the frontend's localStorage copy (`vyapar-web/lib/i18n/provider.tsx`) is
# only the same-device fast path, not the source of truth. Its own small
# router rather than folded into `first_run.py` — a post-onboarding
# language change from a settings/language-switcher UI is a different
# concern from the first-run flow, even though both touch the same column.
# Traces to: product-owner i18n rule, 2026-09-15 (not a numbered FR)
from __future__ import annotations

from typing import Literal

import asyncpg
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.db import get_conn

router = APIRouter(prefix="/v1/members/me", tags=["member-settings"])


class LanguagePatch(BaseModel):
    language: Literal["en", "hi", "te"]


@router.get("")
async def get_me(conn: asyncpg.Connection = Depends(get_conn)) -> dict:
    """The caller's own display name, language and operator permissions —
    lets Profile show operator tools (verification/moderation queues) only
    to operators, instead of links everyone would hit a 403 on."""
    row = await conn.fetchrow(
        """SELECT id, display_name, language, is_operator, operator_permissions
           FROM vyapar_identity.members WHERE id = current_setting('vyapar.authz_context', true)"""
    )
    return {
        "id": row["id"], "display_name": row["display_name"], "language": row["language"],
        "is_operator": row["is_operator"], "operator_permissions": list(row["operator_permissions"]),
    }


@router.patch("/language")
async def set_member_language(body: LanguagePatch, conn: asyncpg.Connection = Depends(get_conn)) -> dict:
    await conn.execute(
        "UPDATE vyapar_identity.members SET language = $1, updated_at = now() WHERE id = current_setting('vyapar.authz_context', true)",
        body.language,
    )
    return {"language": body.language}

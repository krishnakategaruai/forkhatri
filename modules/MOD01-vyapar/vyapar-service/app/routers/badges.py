# [IMP-B] Count-based badges (FR28) — one read route; the rules and the
# on-read cache live in app/reputation.py. Badges also ride on listing
# detail/search cards, profile cards and feed cards (poster_badges).
# Traces to: FR28, TR028
from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.db import get_conn
from app.deps import Locale
from app.errors import ERROR_RESPONSES
from app.identity import AuthzContext, resolve_authz_context
from app.reputation import BadgeOut, badges_for_member

router = APIRouter(tags=["reputation"], responses=ERROR_RESPONSES)


class MemberBadgesOut(BaseModel):
    member_id: str
    badges: list[BadgeOut]


@router.get("/v1/members/{member_id}/badges", response_model=MemberBadgesOut, operation_id="getMemberBadges", summary="A member's earned badges (counts-based, no score)")
async def get_member_badges(
    member_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> MemberBadgesOut:
    return MemberBadgesOut(member_id=member_id, badges=await badges_for_member(conn, member_id, lang))

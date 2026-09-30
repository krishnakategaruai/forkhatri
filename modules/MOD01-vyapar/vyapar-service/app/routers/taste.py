# [Recommendations that learn, 2026-09-30] HTTP front door for the member's
# learned taste: see it in their own language, reset it, remove one item,
# and say "More like this" on a post. Rules live in app/services/taste.py
# (and the model in app/taste.py). Contract: references/imp-recommendations.md.
# Only the member themself can reach their taste; there is no operator route.
# Traces to: FR19, FR20, FR36, FR37, FR38, FR55
from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends

from app.db import get_conn
from app.deps import Locale
from app.errors import ERROR_RESPONSES
from app.identity import AuthzContext, resolve_authz_context
from app.services import taste as svc
from app.services.taste import TasteOut, TastePatch

router = APIRouter(tags=["recommendations"], responses=ERROR_RESPONSES)


@router.get("/v1/me/taste", response_model=TasteOut, operation_id="getMyTaste",
            summary="What Vyapar has learned from your own actions, in your language")
async def get_my_taste(lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context),
                       conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> TasteOut:
    return await svc.get_my_taste(conn, ctx, lang)


@router.delete("/v1/me/taste", response_model=TasteOut, operation_id="resetMyTaste",
               summary="Forget everything learned; earlier actions never count again")
async def reset_my_taste(lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context),
                         conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> TasteOut:
    return await svc.reset_my_taste(conn, ctx, lang)


@router.patch("/v1/me/taste", response_model=TasteOut, operation_id="removeMyTasteItem",
              summary="Stop using one learned item (a skill, a kind of post, the distance limit, the pay floor ...)")
async def remove_my_taste_item(body: TastePatch, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context),
                               conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> TasteOut:
    return await svc.remove_taste_item(conn, ctx, lang, body)


@router.post("/v1/opportunities/{opportunity_id}/more-like-this", response_model=TasteOut, operation_id="moreLikeThis",
             summary="Show me more posts like this one (a strong positive for your recommendations)")
async def more_like_this(opportunity_id: str, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context),
                         conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> TasteOut:
    return await svc.more_like_this(conn, ctx, lang, opportunity_id)

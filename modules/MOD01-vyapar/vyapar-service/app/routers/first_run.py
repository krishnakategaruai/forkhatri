# [TR044] Progressive first-run to Discover — HTTP front door only. Steps,
# scoped skill suggestions and category descriptions live in
# app/services/first_run.py. No credential-related route exists here.
# Traces to: FR44, TR044, SP044
from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends

from app.db import get_conn
from app.deps import Locale
from app.errors import ERROR_RESPONSES
from app.identity import AuthzContext, resolve_authz_context
from app.services import first_run as svc
from app.services.first_run import (  # noqa: F401  schemas used below; background passes re-exported for main.py
    CategoryOptionOut,
    FirstRunState,
    FirstRunStepInput,
    StartInput,
    StartOut,
    TaxonomyOptionOut,
    TradeTileOut,
)

router = APIRouter(prefix="/v1/first-run", tags=["first-run"], responses=ERROR_RESPONSES)


@router.get("/state", response_model=FirstRunState, operation_id="getFirstRunState", summary="Get the member's first-run onboarding state")
async def get_first_run_state(conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> FirstRunState:
    return await svc.get_first_run_state(conn)


@router.get("/capability-options", response_model=list[TaxonomyOptionOut], operation_id="listCapabilityOptions", summary="List capability (skill) options for onboarding")
async def capability_options(lang: Locale, conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> list[TaxonomyOptionOut]:
    return await svc.list_capability_options(conn, lang)


@router.get("/category-options", response_model=list[CategoryOptionOut], operation_id="listCategoryOptions", summary="List business category options for onboarding")
async def category_options(lang: Locale, conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> list[CategoryOptionOut]:
    return await svc.list_category_options(conn, lang)


@router.get("/scoped-capability-options", response_model=list[TaxonomyOptionOut], operation_id="listScopedCapabilityOptions", summary="List capability options scoped to chosen categories")
async def scoped_capability_options(lang: Locale, categories: str = "", conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> list[TaxonomyOptionOut]:
    return await svc.list_scoped_capability_options(conn, lang, categories=categories)


@router.post("/step", response_model=FirstRunState, operation_id="saveFirstRunStep", summary="Save one onboarding step")
async def save_first_run_step(
    body: FirstRunStepInput, conn: asyncpg.Connection = Depends(get_conn, scope="function")
) -> FirstRunState:
    return await svc.save_first_run_step(conn, body=body)


# [Start flow 2026-10] The 3-question start (ONBOARDING-REDESIGN-2026-10.md).
@router.get("/trade-tiles", response_model=list[TradeTileOut], operation_id="listTradeTiles", summary="Picture-tile trades for the start, by goal (find_work | get_customers)")
async def trade_tiles(lang: Locale, goal: str = "find_work") -> list[TradeTileOut]:
    return svc.list_trade_tiles(goal, lang)


@router.post("/start", response_model=StartOut, operation_id="completeStart", summary="Save the 3-question start (goal, trades, area) in one call and go live where the rules allow")
async def complete_start(
    body: StartInput, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn, scope="function")
) -> StartOut:
    return await svc.start(conn, ctx, lang, body)

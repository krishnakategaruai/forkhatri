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
from app.services import first_run as svc
from app.services.first_run import (  # noqa: F401  schemas used below; background passes re-exported for main.py
    CategoryOptionOut,
    FirstRunState,
    FirstRunStepInput,
    TaxonomyOptionOut,
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

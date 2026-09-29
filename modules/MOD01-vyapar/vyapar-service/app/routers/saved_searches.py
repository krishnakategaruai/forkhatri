# [IMP-B] Saved opportunity searches — HTTP front door only; rules live in
# app/services/saved_searches.py. Registered BEFORE opportunities.router so
# the static "/v1/opportunities/saved-searches" is never read as an
# opportunity id (main.py's static-before-dynamic rule).
# Traces to: FR18, FR21, TR018, TR021
from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.db import get_conn
from app.deps import Locale
from app.errors import ERROR_RESPONSES
from app.identity import AuthzContext, resolve_authz_context
from app.services import saved_searches as svc
from app.services.saved_searches import SavedSearchIn, SavedSearchOut  # noqa: F401

router = APIRouter(prefix="/v1/opportunities/saved-searches", tags=["saved-searches"], responses=ERROR_RESPONSES)


class DeletedOut(BaseModel):
    deleted: bool


@router.post("", response_model=SavedSearchOut, status_code=201, operation_id="saveSearch", summary="Save the current opportunity search, optionally with alerts")
async def save_search(
    body: SavedSearchIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> SavedSearchOut:
    return await svc.save_search(conn, ctx, lang, body=body)


@router.get("", response_model=list[SavedSearchOut], operation_id="listSavedSearches", summary="List the member's saved searches")
async def list_saved_searches(
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> list[SavedSearchOut]:
    return await svc.list_saved_searches(conn, ctx)


@router.delete("/{search_id}", response_model=DeletedOut, operation_id="deleteSavedSearch", summary="Delete a saved search")
async def delete_saved_search(
    search_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> DeletedOut:
    return DeletedOut(**await svc.delete_saved_search(conn, ctx, lang, search_id=search_id))

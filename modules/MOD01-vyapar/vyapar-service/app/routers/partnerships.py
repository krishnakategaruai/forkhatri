# [TR025/TR026] Partnership requests: create, list, read, transition — HTTP
# front door only. Rules and queries live in app/services/partnerships.py.
# Traces to: FR25, FR26, FR27, TR025, TR026, TR024, SP025, SP026
from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends, Query, Header

from app.db import get_conn
from app.deps import Locale
from app.errors import ERROR_RESPONSES
from app.identity import AuthzContext, resolve_authz_context
from app.services import partnerships as svc
from app.services.partnerships import (  # noqa: F401  schemas used below; background passes re-exported for main.py
    Action,
    PartnershipCreatedOut,
    PartnershipIn,
    PartnershipRequestOut,
    PartnershipSummaryOut,
    PartnershipTransitionOut,
)
from app.services.pagination import DEFAULT_LIMIT, MAX_LIMIT, Page

router = APIRouter(prefix="/v1/partnership-requests", tags=["partnerships"], responses=ERROR_RESPONSES)


@router.post("", status_code=201, response_model=PartnershipCreatedOut, operation_id="createPartnershipRequest", summary="Send a partnership request")
async def create_partnership_request(
    body: PartnershipIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> PartnershipCreatedOut:
    return await svc.create_partnership_request(conn, ctx, lang, body=body, idempotency_key=idempotency_key)


@router.get("/mine", response_model=list[PartnershipSummaryOut], operation_id="listMyPartnershipRequests", summary="List the member's partnership requests")
async def list_my_partnership_requests(
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> list[PartnershipSummaryOut]:
    return await svc.list_my_partnership_requests(conn, ctx)


@router.get("/mine/page", response_model=Page[PartnershipSummaryOut], operation_id="listMyPartnershipRequestsPage", summary="List the member's partnership requests, one page at a time")
async def list_my_partnership_requests_page(
    lang: Locale,
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    cursor: str | None = None,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> Page[PartnershipSummaryOut]:
    return await svc.list_my_partnership_requests_page(conn, ctx, lang, limit=limit, cursor=cursor)


@router.get("/{request_id}", response_model=PartnershipRequestOut, operation_id="getPartnershipRequest", summary="Get one partnership request")
async def get_partnership_request(
    request_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> PartnershipRequestOut:
    return await svc.get_partnership_request(conn, ctx, lang, request_id=request_id)


@router.post("/{request_id}/{action}", response_model=PartnershipTransitionOut, operation_id="transitionPartnershipRequest", summary="Accept, decline or withdraw a partnership request")
async def transition_partnership_request(
    request_id: str,
    action: Action,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> PartnershipTransitionOut:
    return await svc.transition_partnership_request(conn, ctx, lang, request_id=request_id, action=action)

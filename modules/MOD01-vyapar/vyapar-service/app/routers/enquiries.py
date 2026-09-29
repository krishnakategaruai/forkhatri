# [TR022/TR023/TR024] Enquiries and applications: send, thread, lifecycle,
# consent-based contact disclosure, blocking, Counsel referral — HTTP front
# door only. Rules and queries live in app/services/enquiries.py.
# Traces to: FR22, FR23, FR24, FR52, TR022, TR023, TR024, SP022, SP023, SP024
from __future__ import annotations

from typing import Literal

import asyncpg
from fastapi import APIRouter, Depends, Query, Header

from app.db import get_conn
from app.deps import Locale
from app.errors import ERROR_RESPONSES
from app.identity import AuthzContext, resolve_authz_context
from app.services import enquiries as svc
from app.services.enquiries import (  # noqa: F401  schemas used below; background passes re-exported for main.py
    BlockedOut,
    BlockIn,
    EnquiryCreate,
    EnquiryMessageOut,
    EnquiryOut,
    MessageIn,
    ReferredOut,
    ReferToCounselIn,
)
from app.services.pagination import DEFAULT_LIMIT, MAX_LIMIT, Page

router = APIRouter(prefix="/v1/enquiries", tags=["enquiries"], responses=ERROR_RESPONSES)


@router.post("", response_model=EnquiryOut, status_code=201, operation_id="createEnquiry", summary="Send an enquiry or application")
async def create_enquiry(
    body: EnquiryCreate,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> EnquiryOut:
    return await svc.create_enquiry(conn, ctx, lang, body=body, idempotency_key=idempotency_key)


@router.get("/mine", response_model=list[EnquiryOut], operation_id="listMyEnquiries", summary="List the member's sent and received enquiries")
async def list_my_enquiries(
    role: Literal["sent", "received", "all"] = "all",
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> list[EnquiryOut]:
    return await svc.list_my_enquiries(conn, ctx, role=role)


@router.get("/mine/page", response_model=Page[EnquiryOut], operation_id="listMyEnquiriesPage", summary="List the member's sent and received enquiries, one page at a time")
async def list_my_enquiries_page(
    lang: Locale,
    role: Literal["sent", "received", "all"] = "all",
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    cursor: str | None = None,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> Page[EnquiryOut]:
    return await svc.list_my_enquiries_page(conn, ctx, lang, limit=limit, cursor=cursor, role=role)


@router.get("/{enquiry_id}", response_model=EnquiryOut, operation_id="getEnquiry", summary="Get one enquiry thread")
async def get_enquiry(
    enquiry_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> EnquiryOut:
    return await svc.get_enquiry(conn, ctx, lang, enquiry_id=enquiry_id)


@router.post("/{enquiry_id}/messages", response_model=EnquiryMessageOut, status_code=201, operation_id="replyToEnquiry", summary="Post a message in an enquiry thread")
async def reply_to_enquiry(
    enquiry_id: str,
    body: MessageIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> EnquiryMessageOut:
    return await svc.reply_to_enquiry(conn, ctx, lang, enquiry_id=enquiry_id, body=body)


@router.post("/{enquiry_id}/accept", response_model=EnquiryOut, operation_id="acceptEnquiry", summary="Accept an enquiry")
async def accept_enquiry(enquiry_id: str, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> EnquiryOut:
    return await svc.accept_enquiry(conn, ctx, lang, enquiry_id=enquiry_id)


@router.post("/{enquiry_id}/resolve", response_model=EnquiryOut, operation_id="resolveEnquiry", summary="Mark an enquiry resolved")
async def resolve_enquiry(enquiry_id: str, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> EnquiryOut:
    return await svc.resolve_enquiry(conn, ctx, lang, enquiry_id=enquiry_id)


@router.post("/{enquiry_id}/close", response_model=EnquiryOut, operation_id="closeEnquiry", summary="Close an enquiry")
async def close_enquiry(enquiry_id: str, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> EnquiryOut:
    return await svc.close_enquiry(conn, ctx, lang, enquiry_id=enquiry_id)


@router.post("/{enquiry_id}/withdraw", response_model=EnquiryOut, operation_id="withdrawEnquiry", summary="Withdraw a sent enquiry")
async def withdraw_enquiry(enquiry_id: str, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> EnquiryOut:
    return await svc.withdraw_enquiry(conn, ctx, lang, enquiry_id=enquiry_id)


@router.post("/{enquiry_id}/restrict", response_model=EnquiryOut, operation_id="restrictEnquiry", summary="Restrict an enquiry thread")
async def restrict_enquiry(enquiry_id: str, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> EnquiryOut:
    return await svc.restrict_enquiry(conn, ctx, lang, enquiry_id=enquiry_id)


@router.post("/block", response_model=BlockedOut, operation_id="blockMember", summary="Block a member from contacting you")
async def block_member(body: BlockIn, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> BlockedOut:
    return await svc.block_member(conn, ctx, body=body)


@router.post("/{enquiry_id}/refer-to-counsel", response_model=ReferredOut, operation_id="referEnquiryToCounsel", summary="Refer an enquiry to Counsel")
async def refer_to_counsel(enquiry_id: str, body: ReferToCounselIn, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> ReferredOut:
    return await svc.refer_enquiry_to_counsel(conn, ctx, lang, enquiry_id=enquiry_id, body=body)

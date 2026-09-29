# [TR008/TR009/TR010/TR047] Verification: submit and list documents, the
# operator queue and decisions, revocation — HTTP front door only. Rules,
# masking and the permission chokepoint live in app/services/verification.py.
# Traces to: FR08, FR09, FR10, FR47, TR008, TR009, TR010, TR047, SP008, SP009, SP047
from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends

from app.db import get_conn
from app.deps import Locale
from app.errors import ERROR_RESPONSES
from app.identity import AuthzContext, resolve_authz_context
from app.services import verification as svc
from app.services.verification import (  # noqa: F401  schemas used below; background passes re-exported for main.py
    DecisionIn,
    RevokedOut,
    VerificationCreate,
    VerificationOut,
    run_verification_expiry_pass,
    run_verification_image_cleanup,
)

router = APIRouter(prefix="/v1/listings", tags=["verification"], responses=ERROR_RESPONSES)
admin_router = APIRouter(prefix="/v1/admin/verification-queue", tags=["admin-verification"], responses=ERROR_RESPONSES)


@router.post("/{listing_id}/verification", response_model=VerificationOut, status_code=201, operation_id="submitListingVerification", summary="Submit a verification document for a listing")
async def submit_verification(
    listing_id: str,
    body: VerificationCreate,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> VerificationOut:
    return await svc.submit_listing_verification(conn, ctx, lang, listing_id=listing_id, body=body)


@router.get("/{listing_id}/verification", response_model=list[VerificationOut], operation_id="listListingVerifications", summary="List a listing's verification records")
async def list_verification_records(
    listing_id: str,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> list[VerificationOut]:
    return await svc.list_listing_verifications(conn, ctx, listing_id=listing_id)


@admin_router.get("", response_model=list[VerificationOut], operation_id="listVerificationQueue", summary="List the admin verification queue")
async def verification_queue(
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> list[VerificationOut]:
    return await svc.list_verification_queue(conn, ctx, lang)


@admin_router.post("/{record_id}/verify", response_model=VerificationOut, operation_id="approveVerification", summary="Approve a verification record (admin)")
async def decide_verify(record_id: str, body: DecisionIn, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> VerificationOut:
    return await svc.approve_verification(conn, ctx, lang, record_id=record_id, body=body)


@admin_router.post("/{record_id}/reject", response_model=VerificationOut, operation_id="rejectVerification", summary="Reject a verification record (admin)")
async def decide_reject(record_id: str, body: DecisionIn, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> VerificationOut:
    return await svc.reject_verification(conn, ctx, lang, record_id=record_id, body=body)


@admin_router.post("/{record_id}/needs-clearer-copy", response_model=VerificationOut, operation_id="requestClearerVerificationCopy", summary="Ask for a clearer verification copy (admin)")
async def decide_needs_clearer_copy(record_id: str, body: DecisionIn, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn, scope="function")) -> VerificationOut:
    return await svc.request_clearer_verification_copy(conn, ctx, lang, record_id=record_id, body=body)


@admin_router.post("/listings/{listing_id}/revoke", response_model=RevokedOut, operation_id="revokeListingVerification", summary="Revoke a listing's verification (admin)")
async def admin_revoke_verification(
    listing_id: str,
    body: DecisionIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> RevokedOut:
    return await svc.revoke_listing_verification(conn, ctx, lang, listing_id=listing_id, body=body)

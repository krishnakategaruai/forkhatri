# [TR036/TR037/TR038/TR053] Privacy controls, data rights, derived
# preferences and legal acceptance — HTTP front door only. Every rule and
# query lives in app/services/privacy.py (see its header for the approach).
# Traces to: FR36, FR37, FR38, FR53, TR036, TR037, TR038, TR053
from __future__ import annotations

from typing import Literal

import asyncpg
from fastapi import APIRouter, Depends

from app.db import get_conn
from app.deps import Locale
from app.errors import ERROR_RESPONSES
from app.identity import AuthzContext, resolve_authz_context
from app.services import privacy as svc
from app.services.privacy import (  # noqa: F401  schemas used below; background passes re-exported for main.py
    DataExportOut,
    DeletionOut,
    DerivedPreferenceOut,
    LegalAcceptanceOut,
    LegalDocumentOut,
    PreferenceDecisionOut,
    PrivacyPatch,
    PrivacyRequestOut,
    PrivacySettingsOut,
    WithdrawConsentIn,
    WithdrawConsentOut,
    run_preference_detection_pass,
)

router = APIRouter(tags=["privacy"], responses=ERROR_RESPONSES)


@router.get("/v1/privacy", response_model=PrivacySettingsOut, operation_id="getPrivacySettings", summary="Get the member's privacy settings")
async def get_privacy(
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> PrivacySettingsOut:
    return await svc.get_privacy_settings(conn, ctx)


@router.patch("/v1/privacy", response_model=PrivacySettingsOut, operation_id="updatePrivacySettings", summary="Update the member's privacy settings")
async def patch_privacy(
    body: PrivacyPatch,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> PrivacySettingsOut:
    return await svc.update_privacy_settings(conn, ctx, lang, body)


@router.post("/v1/privacy/export", status_code=201, response_model=DataExportOut, operation_id="requestDataExport", summary="Request an export of the member's data")
async def request_export(
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> DataExportOut:
    return await svc.request_data_export(conn, ctx)


@router.post("/v1/privacy/withdraw-consent", response_model=WithdrawConsentOut, operation_id="withdrawConsent", summary="Withdraw a consent")
async def withdraw_consent(
    body: WithdrawConsentIn,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> WithdrawConsentOut:
    return await svc.withdraw_consent(conn, ctx, body.field)


@router.post(
    "/v1/privacy/delete", status_code=201, response_model=DeletionOut, response_model_exclude_none=True,
    operation_id="requestAccountDeletion", summary="Request deletion of the member's Vyapar data",
)
async def request_deletion(
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> DeletionOut:
    return await svc.request_account_deletion(conn, ctx, lang)


@router.get("/v1/privacy/requests", response_model=list[PrivacyRequestOut], operation_id="listMyPrivacyRequests", summary="List the member's privacy requests")
async def list_my_requests(
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[PrivacyRequestOut]:
    return await svc.list_my_privacy_requests(conn, ctx)


@router.get("/v1/preferences/mine", response_model=list[DerivedPreferenceOut], operation_id="listMyPreferences", summary="List the member's derived preferences")
async def list_my_preferences(
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[DerivedPreferenceOut]:
    return await svc.list_my_preferences(conn, ctx)


@router.post("/v1/preferences/{pref_id}/{action}", response_model=PreferenceDecisionOut, operation_id="decidePreference", summary="Accept or reject a derived preference")
async def decide_preference(
    pref_id: str,
    action: Literal["confirm", "decline", "remove"],
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> PreferenceDecisionOut:
    return await svc.decide_preference(conn, ctx, lang, pref_id, action)


@router.get("/v1/legal/{kind}", response_model=LegalDocumentOut, operation_id="getLegalDocument", summary="Get the current legal document of a kind")
async def get_legal_document(
    kind: Literal["privacy", "terms"],
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> LegalDocumentOut:
    return await svc.get_legal_document(conn, ctx, lang, kind)


@router.post("/v1/legal/{kind}/accept", response_model=LegalAcceptanceOut, operation_id="acceptLegalDocument", summary="Accept the current legal document of a kind")
async def accept_legal_document(
    kind: Literal["privacy", "terms"],
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> LegalAcceptanceOut:
    return await svc.accept_legal_document(conn, ctx, kind)

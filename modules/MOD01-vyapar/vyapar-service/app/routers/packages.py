# [IMP-B] Tiered service packages on listings — HTTP front door only.
# Rules live in app/services/packages.py.
# Traces to: FR01, FR04, FR22, TR001, TR022
from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends, Header

from app.db import get_conn
from app.deps import Locale
from app.errors import ERROR_RESPONSES
from app.identity import AuthzContext, resolve_authz_context
from app.services import packages as svc
from app.services.packages import PackageOut, PackageRequestIn, PackageRequestOut, PackagesUpsertIn  # noqa: F401

router = APIRouter(prefix="/v1/listings", tags=["listing-packages"], responses=ERROR_RESPONSES)


@router.get("/{listing_id}/packages", response_model=list[PackageOut], operation_id="listListingPackages", summary="List a listing's service packages (basic / standard / premium)")
async def list_listing_packages(
    listing_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> list[PackageOut]:
    return await svc.list_listing_packages(conn, ctx, lang, listing_id=listing_id)


@router.put("/{listing_id}/packages", response_model=list[PackageOut], operation_id="upsertListingPackages", summary="Create or update up to three package tiers (owner)")
async def upsert_listing_packages(
    listing_id: str,
    body: PackagesUpsertIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> list[PackageOut]:
    return await svc.upsert_listing_packages(conn, ctx, lang, listing_id=listing_id, body=body)


@router.delete("/{listing_id}/packages/{package_id}", response_model=list[PackageOut], operation_id="deleteListingPackage", summary="Delete one package tier (owner)")
async def delete_listing_package(
    listing_id: str,
    package_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
) -> list[PackageOut]:
    return await svc.delete_listing_package(conn, ctx, lang, listing_id=listing_id, package_id=package_id)


@router.post("/{listing_id}/packages/{package_id}/request", response_model=PackageRequestOut, status_code=201, operation_id="requestListingPackage", summary="Request a package: opens an enquiry tagged with it")
async def request_listing_package(
    listing_id: str,
    package_id: str,
    body: PackageRequestIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn, scope="function"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> PackageRequestOut:
    return await svc.request_listing_package(conn, ctx, lang, listing_id=listing_id, package_id=package_id, body=body, idempotency_key=idempotency_key)

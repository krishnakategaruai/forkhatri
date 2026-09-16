# [TR008] Business-existence document verification with masked storage
# (FR08). [TR009] Professional-credential document review (FR09). [TR047]
# Verification queue, Admin Console federated view (FR47).
# Approach: exactly one document type per request (Aadhaar structurally
# absent from the CHECK constraint's fixed value list, never offered as an
# option — TR008's own rule). Server-side format validation for GSTIN(15)/
# PAN(10)/Udyam(pattern) before insert. `identifier_enc` via
# `app.crypto.encrypt_identifier` (SP008's AES-256-GCM Decision);
# `identifier_masked` (last 4 only) is the ONLY form any response ever
# returns — `identifier_enc` is never serialized into a Pydantic response
# model at all (a structural absence, not a runtime redaction step that
# could be forgotten). The operator queue is gated by
# `operator_permissions @> ARRAY['verification']` via
# `ctx.is_operator`/a dedicated permission check — the endpoint performs
# the check itself here since a full Authorization Engine component
# doesn't exist as separate code yet (07-tech-reqs.md's own "logic-only,
# no owned tables" component; this router IS that chokepoint for this
# path).
# Traces to: FR08, FR09, FR10, FR47, TR008, TR009, TR010, TR047, SP008, SP009, SP047
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Literal

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.crypto import encrypt_identifier, mask_identifier
from app.notifications import send_notification
from app.db import get_conn
from app.deps import Locale
from app.i18n import translate
from app.identity import AuthzContext, resolve_authz_context

router = APIRouter(prefix="/v1/listings", tags=["verification"])
admin_router = APIRouter(prefix="/v1/admin/verification-queue", tags=["admin-verification"])

_GSTIN_RE = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z][Z][0-9A-Z]$")
_PAN_RE = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
_UDYAM_RE = re.compile(r"^UDYAM-[A-Z]{2}-[0-9]{2}-[0-9]{7}$")

_FORMAT_CHECKS = {"gst": _GSTIN_RE, "pan": _PAN_RE, "udyam": _UDYAM_RE}


class VerificationCreate(BaseModel):
    document_type: Literal["gst", "udyam", "pan", "shops_est", "credential"]
    identifier: str | None = None
    image_url: str | None = None
    credential_name: str | None = None
    issuer: str | None = None


class VerificationOut(BaseModel):
    id: str
    listing_id: str
    kind: str
    document_type: str
    identifier_masked: str | None
    image_url: str | None
    credential_name: str | None
    issuer: str | None
    state: str
    reason_code: str | None
    created_at: str
    days_pending: int


def _row_out(row: asyncpg.Record) -> VerificationOut:
    days_pending = (datetime.now(timezone.utc) - row["created_at"]).days if row["state"] == "pending" else 0
    return VerificationOut(
        id=str(row["id"]), listing_id=str(row["listing_id"]), kind=row["kind"], document_type=row["document_type"],
        identifier_masked=row["identifier_masked"], image_url=row["image_url"],
        credential_name=row["credential_name"], issuer=row["issuer"], state=row["state"],
        reason_code=row["reason_code"], created_at=row["created_at"].isoformat(), days_pending=days_pending,
    )


@router.post("/{listing_id}/verification", response_model=VerificationOut, status_code=201)
async def submit_verification(
    listing_id: str,
    body: VerificationCreate,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> VerificationOut:
    listing = await conn.fetchrow("SELECT owner_id, kind FROM vyapar_listings.listings WHERE id = $1", listing_id)
    if listing is None or listing["owner_id"] != ctx.member_id:
        raise HTTPException(status_code=404, detail=translate("common.error.listingNotFound", lang))

    kind = "credential" if body.document_type == "credential" else "business"
    # [FR09] a credential claim needs its name and issuer — "Credential
    # reviewed: <name>" is meaningless without them.
    if kind == "credential" and not (body.credential_name and body.issuer):
        raise HTTPException(status_code=422, detail=translate("verification.error.credentialFieldsRequired", lang))

    identifier_masked, identifier_enc = None, None
    if body.document_type in _FORMAT_CHECKS:
        if not body.identifier or not _FORMAT_CHECKS[body.document_type].match(body.identifier.upper()):
            raise HTTPException(status_code=422, detail=translate(f"verification.error.invalidFormat.{body.document_type}", lang))
        identifier_masked = mask_identifier(body.identifier)
        identifier_enc = encrypt_identifier(body.identifier)
    elif body.document_type == "shops_est":
        identifier_masked = mask_identifier(body.identifier) if body.identifier else None
        identifier_enc = encrypt_identifier(body.identifier) if body.identifier else None

    # [TR008] 30-day deletion window for identity-document images, starting
    # from decision — set here as a placeholder; the actual deletion job
    # only fires once `decided_at` is set (see decide_verification below).
    row = await conn.fetchrow(
        """INSERT INTO vyapar_listings.verification_records
             (listing_id, member_id, kind, document_type, identifier_masked, identifier_enc, image_url, credential_name, issuer)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
           RETURNING *""",
        listing_id, ctx.member_id, kind, body.document_type, identifier_masked, identifier_enc,
        body.image_url, body.credential_name, body.issuer,
    )
    # [FR10] Pending Review is one of the eight displayed states. A listing
    # that is still verified-but-expiring keeps its label until decided.
    await conn.execute(
        """UPDATE vyapar_listings.listings SET verification_state = 'pending', updated_at = now()
           WHERE id = $1 AND verification_state IN ('not_started','rejected','expired','revoked')""",
        listing_id,
    )
    return _row_out(row)


@router.get("/{listing_id}/verification", response_model=list[VerificationOut])
async def list_verification_records(
    listing_id: str,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[VerificationOut]:
    rows = await conn.fetch("SELECT * FROM vyapar_listings.verification_records WHERE listing_id = $1 ORDER BY created_at DESC", listing_id)
    return [_row_out(r) for r in rows]


# ---------------------------------------------------------------------------
# [TR047] Operator queue — federated Admin Console view. Gated on
# `operator_permissions @> ARRAY['verification']`, checked here (the
# endpoint IS the chokepoint for this path, per this file's own header note).
# ---------------------------------------------------------------------------
def _require_verification_permission(ctx: AuthzContext, conn_row: asyncpg.Record | None, lang: str) -> None:
    if not conn_row or "verification" not in (conn_row["operator_permissions"] or []):
        raise HTTPException(status_code=403, detail=translate("verification.error.permissionRequired", lang))


@admin_router.get("", response_model=list[VerificationOut])
async def verification_queue(
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[VerificationOut]:
    perm_row = await conn.fetchrow("SELECT operator_permissions FROM vyapar_identity.members WHERE id = $1", ctx.member_id)
    _require_verification_permission(ctx, perm_row, lang)
    rows = await conn.fetch("SELECT * FROM vyapar_listings.verification_records WHERE state = 'pending' ORDER BY created_at ASC")
    return [_row_out(r) for r in rows]


class DecisionIn(BaseModel):
    reason_code: str | None = None
    claim_scope: str | None = None  # e.g. "GST Certificate/GSTIN" — shown on the listing


@admin_router.post("/{record_id}/verify", response_model=VerificationOut)
async def decide_verify(record_id: str, body: DecisionIn, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn)) -> VerificationOut:
    return await _decide(conn, ctx, record_id, "verified", body, lang)


@admin_router.post("/{record_id}/reject", response_model=VerificationOut)
async def decide_reject(record_id: str, body: DecisionIn, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn)) -> VerificationOut:
    return await _decide(conn, ctx, record_id, "rejected", body, lang)


@admin_router.post("/{record_id}/needs-clearer-copy", response_model=VerificationOut)
async def decide_needs_clearer_copy(record_id: str, body: DecisionIn, lang: Locale, ctx: AuthzContext = Depends(resolve_authz_context), conn: asyncpg.Connection = Depends(get_conn)) -> VerificationOut:
    return await _decide(conn, ctx, record_id, "needs_clearer_copy", body, lang)


async def _decide(conn: asyncpg.Connection, ctx: AuthzContext, record_id: str, new_state: str, body: DecisionIn, lang: str) -> VerificationOut:
    perm_row = await conn.fetchrow("SELECT operator_permissions FROM vyapar_identity.members WHERE id = $1", ctx.member_id)
    _require_verification_permission(ctx, perm_row, lang)
    record = await conn.fetchrow("SELECT * FROM vyapar_listings.verification_records WHERE id = $1", record_id)
    if record is None:
        raise HTTPException(status_code=404, detail=translate("verification.error.recordNotFound", lang))

    image_delete_after = datetime.now(timezone.utc) + timedelta(days=30) if record["image_url"] else None
    updated = await conn.fetchrow(
        """UPDATE vyapar_listings.verification_records SET
             state = $2, reason_code = $3, verifier_id = $4, decided_at = now(),
             image_delete_after = $5, updated_at = now()
           WHERE id = $1 RETURNING *""",
        record_id, new_state, body.reason_code, ctx.member_id, image_delete_after,
    )

    # [TR010] Verified -> Listing becomes Active-Verified with the claim scope.
    if new_state == "verified":
        # [FR09] a credential's claim is the credential's own name.
        claim = body.claim_scope or (record["credential_name"] if record["document_type"] == "credential" else record["document_type"])
        await conn.execute(
            """UPDATE vyapar_listings.listings SET
                 verification_state = 'verified', verification_document = $2, verification_claim = $3,
                 verified_at = now(), verification_expires_at = now() + interval '12 months',
                 state = CASE WHEN state = 'active_unverified' THEN 'active_verified' ELSE state END,
                 updated_at = now()
               WHERE id = $1""",
            record["listing_id"], record["document_type"], claim,
        )
    elif new_state == "rejected":
        await conn.execute(
            """UPDATE vyapar_listings.listings SET verification_state = 'rejected', state_reason = $2,
                 state = CASE WHEN state = 'active_verified' THEN 'active_unverified' ELSE state END, updated_at = now()
               WHERE id = $1""",
            record["listing_id"], body.reason_code,
        )
    elif new_state == "needs_clearer_copy":
        # [FR09] no penalty — the listing returns to its pre-request label.
        await conn.execute(
            "UPDATE vyapar_listings.listings SET verification_state = 'not_started', updated_at = now() WHERE id = $1 AND verification_state = 'pending'",
            record["listing_id"],
        )
    return _row_out(updated)


async def run_verification_image_cleanup(pool: asyncpg.Pool) -> int:
    """[TR008 — 30-day deletion compliance control] Clears image_url (and
    the encrypted identifier, since its retention purpose ends with the
    decision review) for any record past its `image_delete_after` —
    logged as a count, not silently assumed to have run."""
    deleted = 0
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("SELECT set_config('vyapar.service_role', 'dispatcher', true)")
            await conn.execute("SELECT set_config('vyapar.authz_context', 'm_neha_ops', true)")
            rows = await conn.fetch(
                "SELECT id FROM vyapar_listings.verification_records WHERE image_delete_after IS NOT NULL AND image_delete_after < now() AND image_url IS NOT NULL"
            )
            for r in rows:
                await conn.execute(
                    "UPDATE vyapar_listings.verification_records SET image_url = NULL, identifier_enc = NULL, updated_at = now() WHERE id = $1",
                    r["id"],
                )
                deleted += 1
    return deleted


# ---------------------------------------------------------------------------
# [TR010] Verification expiry and revert (FR10). `revoke_verification()` is
# the ONE call site that reverts a displayed claim — expiry, operator
# revocation and (later, slice 6) dispute all call it, so the label can
# never drift between surfaces (SP010's own import-boundary rule).
# The expiry pass reads `verified_at` directly: the 12-month expiry fires
# even if the 11-month reminder notification failed (SP010: a failed
# reminder must never silently extend a verification).
# Traces to: FR10, TR010, SP010
# ---------------------------------------------------------------------------
async def revoke_verification(conn: asyncpg.Connection, listing_id, reason: str | None, new_state: str = "revoked") -> None:
    await conn.execute(
        """UPDATE vyapar_listings.listings SET verification_state = $2,
             state_reason = COALESCE($3, state_reason),
             state = CASE WHEN state = 'active_verified' THEN 'active_unverified' ELSE state END,
             updated_at = now()
           WHERE id = $1""",
        listing_id, new_state, reason,
    )
    if new_state in ("revoked", "expired"):
        await conn.execute(
            "UPDATE vyapar_listings.verification_records SET state = $2, updated_at = now() WHERE listing_id = $1 AND state = 'verified'",
            listing_id, new_state,
        )


async def run_verification_expiry_pass(pool: asyncpg.Pool) -> dict:
    reminded = expired = 0
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("SELECT set_config('vyapar.service_role', 'dispatcher', true)")
            await conn.execute("SELECT set_config('vyapar.authz_context', 'm_neha_ops', true)")
            # Expire first, so a 12-month listing is never "reminded".
            for r in await conn.fetch(
                "SELECT id FROM vyapar_listings.listings WHERE verification_state IN ('verified','expiring') AND verified_at < now() - interval '12 months'"
            ):
                await revoke_verification(conn, r["id"], None, "expired")
                expired += 1
            for r in await conn.fetch(
                """SELECT id, owner_id, name, verified_at FROM vyapar_listings.listings
                   WHERE verification_state = 'verified' AND verified_at < now() - interval '11 months'"""
            ):
                await conn.execute("UPDATE vyapar_listings.listings SET verification_state = 'expiring', updated_at = now() WHERE id = $1", r["id"])
                member_lang = await conn.fetchval("SELECT language FROM vyapar_identity.members WHERE id = $1", r["owner_id"])
                if await send_notification(
                    conn, member_id=r["owner_id"], kind="verification_reminder", template_id="verification_reminder",
                    title=translate("notifications.verificationReminder.title", member_lang, name=r["name"]),
                    body=translate("notifications.verificationReminder.body", member_lang),
                    link=f"/listings/{r['id']}", params={"listing_id": str(r["id"])},
                    idempotency_key=f"verification_reminder:{r['id']}:{r['verified_at'].date().isoformat()}",
                ):
                    reminded += 1
    return {"reminded": reminded, "expired": expired}


@admin_router.post("/listings/{listing_id}/revoke")
async def admin_revoke_verification(
    listing_id: str,
    body: DecisionIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    perm_row = await conn.fetchrow("SELECT operator_permissions FROM vyapar_identity.members WHERE id = $1", ctx.member_id)
    _require_verification_permission(ctx, perm_row, lang)
    await revoke_verification(conn, listing_id, body.reason_code, "revoked")
    return {"revoked": True}

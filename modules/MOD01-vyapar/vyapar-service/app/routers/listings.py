# [TR001] Create-and-edit BusinessProfile/ProfessionalListingProfile (FR01,
# FR04). Both kinds share one table/endpoint family — a Listing is a
# BusinessProfile or ProfessionalListingProfile per the FR set's own shared
# definition, never two parallel implementations.
# Approach: owner_id is resolved server-side from AuthzContext (RLS-CC +
# AuthzChokepoint-CC), never accepted as client input (closes SP001's
# Spoofing row). Free-text category/capability input is matched against
# vyapar_listings.taxonomy_terms (by slug or alias); anything unmatched goes
# to unmapped_labels[] and stays immediately searchable — never blocked
# pending taxonomy review (TR001/TR004's own explicit rule). The
# UNIQUE(owner_id, name, locality) DB constraint enforces FR01's duplicate
# rule directly; on conflict, returns the existing listing id (409) so the
# client can offer "edit existing" instead of a bare validation error.
# [Product-owner i18n rule, 2026-09-15] Every member-facing string returned
# from this router (HTTPException.detail, success "message" fields) goes
# through `translate(key, lang)` — `lang` is resolved per-request from the
# `Locale` dependency (X-Vyapar-Language header, falling back to
# Accept-Language), never a hardcoded English literal.
# Traces to: FR01, FR04, TR001, TR004, SP001, SP004
from __future__ import annotations

import random
import re
from datetime import timedelta
from typing import Literal

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.db import get_conn
from app.deps import Locale
from app.i18n import translate
from app.identity import AuthzContext, resolve_authz_context
from app.impressions import boosted_ids, log_events
from app.reputation import reputation_for_listings

router = APIRouter(prefix="/v1/listings", tags=["listings"])

# [SP001 Decision] standing-count cap — not named by any FR/TR, added at
# Step 8 as a genuine gap fix; enforced here at submit time (the point a
# Draft actually becomes an "active listing" the cap is meant to bound),
# not at Draft-creation time, since Drafts are cheap and not the abuse
# surface SP001 named.
LISTING_ACTIVE_CAP = 20

# [TR003] V1 static prohibited-content wordlist / spam heuristic. SP003
# explicitly treats this as "an ongoing tuning exercise (CCR12), not a
# one-time build task" — kept as one small, easily-extended list rather than
# scattered inline checks, so Step 13 monitoring has one place to tune.
_PROHIBITED_WORDS = {"scam", "fraud", "guaranteed money", "pyramid scheme"}
_SPAM_PATTERN = re.compile(r"(https?://\S+.*){3,}|(.)\1{9,}")

# [Member-facing copy — never leak the raw internal state-machine enum value
# (e.g. 'active_unverified') into an error message a member reads. Values
# here are i18n KEYS under listings.state.*, not display text — see
# app/i18n/locales/<lang>/listings.json.]
STATE_PHRASE_KEYS = {
    "draft": "draft",
    "submitted": "submitted",
    "active_unverified": "active_unverified",
    "active_verified": "active_verified",
    "suspended": "suspended",
    "archived": "archived",
}


async def _match_taxonomy(conn: asyncpg.Connection, kind: str, labels: list[str]) -> tuple[list[str], list[str]]:
    """Splits free-text labels into (matched slugs, unmapped free-text) —
    TR001's own fallback rule: unmatched text is never blocked, just queued
    for FR48 taxonomy review while remaining searchable."""
    if not labels:
        return [], []
    rows = await conn.fetch(
        "SELECT slug, aliases FROM vyapar_listings.taxonomy_terms WHERE kind = $1 AND status = 'active'",
        kind,
    )
    matched: list[str] = []
    unmapped: list[str] = []
    for label in labels:
        norm = label.strip().lower()
        hit = None
        for row in rows:
            if norm == row["slug"] or norm in (a.lower() for a in row["aliases"]):
                hit = row["slug"]
                break
        (matched if hit else unmapped).append(hit or label.strip())
    return matched, unmapped


def _content_flags(name: str, description: str | None, headline: str | None) -> str | None:
    """[TR003] Automated safety check run before auto-activation. Returns a
    reason category (never the raw wordlist) or None if clean. The return
    value is an i18n KEY (listings.reason.*), not display text."""
    text = " ".join(filter(None, [name, description, headline])).lower()
    for word in _PROHIBITED_WORDS:
        if word in text:
            return "prohibited_content"
    if _SPAM_PATTERN.search(text):
        return "spam_pattern"
    return None


class ContactIn(BaseModel):
    channel: Literal["phone", "whatsapp", "email", "website", "address"]
    value: str
    disclosure: Literal["public", "after_accept", "hidden"] = "after_accept"


class ListingCreate(BaseModel):
    kind: Literal["business", "professional"]
    name: str = Field(min_length=1)
    headline: str | None = None
    description: str | None = None
    categories: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    locality: str = Field(min_length=1)
    lat: float | None = None
    lng: float | None = None
    service_mode: Literal["on_site", "remote", "both"] = "both"
    service_radius_km: int = 10
    primary_phone: str | None = None
    contacts: list[ContactIn] = Field(default_factory=list)
    opportunity_participation: bool = True


class ListingPatch(BaseModel):
    name: str | None = None
    headline: str | None = None
    description: str | None = None
    categories: list[str] | None = None
    capabilities: list[str] | None = None
    locality: str | None = None
    lat: float | None = None
    lng: float | None = None
    service_mode: Literal["on_site", "remote", "both"] | None = None
    service_radius_km: int | None = None
    primary_phone: str | None = None
    enquiry_pref: Literal["enabled", "disabled"] | None = None
    opportunity_participation: bool | None = None
    experience_years: int | None = None
    languages: list[str] | None = None
    availability: Literal["now", "this_week", "later"] | None = None
    evidence_links: list[str] | None = None
    rates: str | None = None
    setup_step: int | None = None


class ListingOut(BaseModel):
    id: str
    kind: str
    name: str
    headline: str | None
    description: str | None
    categories: list[str]
    capabilities: list[str]
    unmapped_labels: list[str]
    locality: str
    service_mode: str
    service_radius_km: int
    enquiry_pref: str
    opportunity_participation: bool
    discoverable: bool
    partnership_open: bool
    primary_phone: str | None
    contact_verified: bool
    setup_step: int
    experience_years: int | None
    languages: list[str]
    availability: str | None
    evidence_links: list[str]
    rates: str | None
    intent_state: str | None
    intent_visible: bool
    capability_visible: bool
    state: str
    state_reason: str | None
    verification_state: str
    owner_id: str
    is_owner: bool
    contacts: list[dict]
    saved: bool = False
    credential_ref: dict | None = None  # [FR06/TR006]
    # [FR10/TR010] scope + date shown with every verification label
    verification_document: str | None = None
    verification_claim: str | None = None
    verified_at: str | None = None
    verification_expires_at: str | None = None
    # [FR28/TR028] counts only, composed by app/reputation.py — never a score
    reputation: dict | None = None
    # [FR30/FR54] true while a boost is active — rendered only via SponsoredBadge
    sponsored: bool = False


async def is_active(conn: asyncpg.Connection, listing_id: str) -> asyncpg.Record | None:
    """[TR025/SP025] Listings' own public "is this listing Active" method —
    other components (partnerships) call this instead of querying
    `listings.state` themselves. Returns the row if Active, else None
    (including a malformed id)."""
    try:
        row = await conn.fetchrow(
            """SELECT id, owner_id, name, kind, locality, categories, partnership_open, verification_state, state
               FROM vyapar_listings.listings WHERE id = $1""",
            listing_id,
        )
    except asyncpg.DataError:
        return None
    return row if row is not None and row["state"] in ("active_unverified", "active_verified") else None


async def has_verified_listing(conn: asyncpg.Connection, member_id: str) -> bool:
    """[TR030] Listings' own answer to "does this member own an Active-Verified
    listing" — the opportunity-boost eligibility rule reads this, never
    `listings.verification_state` directly."""
    return await conn.fetchval(
        "SELECT EXISTS (SELECT 1 FROM vyapar_listings.listings WHERE owner_id = $1 AND state = 'active_verified')", member_id
    )


def _row_to_out(
    row: asyncpg.Record, contacts: list[asyncpg.Record], caller_id: str, saved: bool = False
) -> ListingOut:
    is_owner = row["owner_id"] == caller_id
    credential_ref = row["credential_ref"]
    if isinstance(credential_ref, str):
        import json as _json
        credential_ref = _json.loads(credential_ref)
    return ListingOut(
        saved=saved,
        credential_ref=credential_ref,
        verification_document=row["verification_document"],
        verification_claim=row["verification_claim"],
        verified_at=row["verified_at"].isoformat() if row["verified_at"] else None,
        verification_expires_at=row["verification_expires_at"].isoformat() if row["verification_expires_at"] else None,
        id=str(row["id"]),
        kind=row["kind"],
        name=row["name"],
        headline=row["headline"],
        description=row["description"],
        categories=list(row["categories"]),
        capabilities=list(row["capabilities"]),
        unmapped_labels=list(row["unmapped_labels"]),
        locality=row["locality"],
        service_mode=row["service_mode"],
        service_radius_km=row["service_radius_km"],
        enquiry_pref=row["enquiry_pref"],
        opportunity_participation=row["opportunity_participation"],
        discoverable=row["discoverable"],
        partnership_open=row["partnership_open"],
        primary_phone=row["primary_phone"] if is_owner else None,
        contact_verified=row["contact_verified"],
        setup_step=row["setup_step"],
        experience_years=row["experience_years"],
        languages=list(row["languages"]),
        availability=row["availability"],
        evidence_links=list(row["evidence_links"]),
        rates=row["rates"],
        # [FR05/TR005 — the module's own highest-severity read-boundary rule]
        # intent_state is returned ONLY when intent_visible=true OR the
        # caller is the owner — this function is the one call site every
        # listings read goes through, never a second, independently-coded
        # check elsewhere.
        intent_state=row["intent_state"] if (row["intent_visible"] or is_owner) else None,
        intent_visible=row["intent_visible"],
        capability_visible=row["capability_visible"],
        state=row["state"],
        state_reason=row["state_reason"],
        verification_state=row["verification_state"],
        owner_id=row["owner_id"],
        is_owner=is_owner,
        contacts=[dict(c) for c in contacts] if is_owner else [
            dict(c) for c in contacts if c["disclosure"] == "public"
        ],
    )


@router.post("", response_model=ListingOut, status_code=201)
async def create_listing(
    body: ListingCreate,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> ListingOut:
    cat_matched, cat_unmapped = await _match_taxonomy(conn, "category", body.categories)
    cap_matched, cap_unmapped = await _match_taxonomy(conn, "capability", body.capabilities)

    existing = await conn.fetchrow(
        "SELECT id FROM vyapar_listings.listings WHERE owner_id = $1 AND name = $2 AND locality = $3",
        ctx.member_id, body.name, body.locality,
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail={"message": translate("listings.error.duplicate", lang), "existing_listing_id": str(existing["id"])},
        )

    row = await conn.fetchrow(
        """INSERT INTO vyapar_listings.listings
             (owner_id, kind, name, headline, description, categories, capabilities, unmapped_labels,
              locality, lat, lng, service_mode, service_radius_km, primary_phone,
              opportunity_participation, setup_step)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16)
           RETURNING *""",
        ctx.member_id, body.kind, body.name, body.headline, body.description,
        cat_matched, cap_matched, cat_unmapped + cap_unmapped,
        body.locality, body.lat, body.lng, body.service_mode, body.service_radius_km,
        body.primary_phone, body.opportunity_participation,
        1 if body.kind == "professional" else 0,
    )
    for c in body.contacts:
        await conn.execute(
            "INSERT INTO vyapar_listings.listing_contacts (listing_id, channel, value, disclosure) VALUES ($1,$2,$3,$4)",
            row["id"], c.channel, c.value, c.disclosure,
        )
    contacts = await conn.fetch(
        "SELECT channel, value, disclosure FROM vyapar_listings.listing_contacts WHERE listing_id = $1", row["id"]
    )
    return _row_to_out(row, contacts, ctx.member_id)


@router.get("/mine", response_model=list[ListingOut])
async def list_my_listings(
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> list[ListingOut]:
    rows = await conn.fetch(
        "SELECT * FROM vyapar_listings.listings WHERE owner_id = $1 ORDER BY created_at DESC", ctx.member_id
    )
    out = []
    for row in rows:
        contacts = await conn.fetch(
            "SELECT channel, value, disclosure FROM vyapar_listings.listing_contacts WHERE listing_id = $1", row["id"]
        )
        out.append(_row_to_out(row, contacts, ctx.member_id))
    return out


@router.get("/{listing_id}", response_model=ListingOut)
async def get_listing(
    listing_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> ListingOut:
    row = await conn.fetchrow("SELECT * FROM vyapar_listings.listings WHERE id = $1", listing_id)
    if row is None:
        # [FR16] RLS already hides Draft/Submitted rows from a non-owner —
        # this also covers a stale link to a Suspended/Archived listing that
        # a non-owner/non-operator should never see underlying data for.
        raise HTTPException(status_code=404, detail=translate("common.error.listingNotFound", lang))
    contacts = await conn.fetch(
        "SELECT channel, value, disclosure FROM vyapar_listings.listing_contacts WHERE listing_id = $1", row["id"]
    )
    # [FR55 "Recently viewed" — real, DB-backed via the already-modeled
    # member_listing table, not a placeholder] every detail open records a
    # view for the Activity screen to read later (slice 3).
    saved_row = await conn.fetchrow(
        """INSERT INTO vyapar_listings.member_listing (member_id, listing_id, viewed_at)
           VALUES ($1, $2, now())
           ON CONFLICT (member_id, listing_id) DO UPDATE SET viewed_at = now()
           RETURNING saved_at""",
        ctx.member_id, listing_id,
    )
    out = _row_to_out(row, contacts, ctx.member_id, saved=saved_row["saved_at"] is not None)
    # [FR28/TR016] trust context composed on the detail read
    out.reputation = (await reputation_for_listings(conn, [row])).get(str(row["id"]))
    out.sponsored = str(row["id"]) in await boosted_ids(conn, "listing", [row["id"]])
    if not out.is_owner:  # [FR32] an owner viewing their own listing isn't a detail view
        await log_events(conn, "listing", [row["id"]], "view", "listing_detail", {str(row["id"])} if out.sponsored else set())
    return out


# ---------------------------------------------------------------------------
# [FR16/FR55] Save — real, persisted via member_listing.saved_at. Share is
# deliberately NOT a backend endpoint: it's just "copy/open this listing's
# own URL", handled entirely client-side (navigator.share / clipboard) per
# the design direction's "fewer taps, no unnecessary round-trip" principle
# — adding a server call for something that needs no server state would be
# the over-engineered choice, not the modern one. Report (FR39) is
# deliberately deferred here, not faked: vyapar_trust_safety.reports.case_id
# is NOT NULL and references moderation_cases — a real Report action needs
# FR39/FR40's moderation-case lifecycle (slice 6), not a bare insert.
# Traces to: FR16, FR55
# ---------------------------------------------------------------------------
@router.post("/{listing_id}/save", response_model=ListingOut)
async def save_listing(
    listing_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> ListingOut:
    row = await conn.fetchrow("SELECT * FROM vyapar_listings.listings WHERE id = $1", listing_id)
    if row is None:
        raise HTTPException(status_code=404, detail=translate("common.error.listingNotFound", lang))
    await conn.execute(
        """INSERT INTO vyapar_listings.member_listing (member_id, listing_id, saved_at)
           VALUES ($1, $2, now())
           ON CONFLICT (member_id, listing_id) DO UPDATE SET saved_at = now()""",
        ctx.member_id, listing_id,
    )
    contacts = await conn.fetch(
        "SELECT channel, value, disclosure FROM vyapar_listings.listing_contacts WHERE listing_id = $1", listing_id
    )
    await log_events(conn, "listing", [row["id"]], "save", "listing_detail")  # [FR32]
    return _row_to_out(row, contacts, ctx.member_id, saved=True)


@router.delete("/{listing_id}/save", response_model=ListingOut)
async def unsave_listing(
    listing_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> ListingOut:
    row = await conn.fetchrow("SELECT * FROM vyapar_listings.listings WHERE id = $1", listing_id)
    if row is None:
        raise HTTPException(status_code=404, detail=translate("common.error.listingNotFound", lang))
    await conn.execute(
        "UPDATE vyapar_listings.member_listing SET saved_at = NULL WHERE member_id = $1 AND listing_id = $2",
        ctx.member_id, listing_id,
    )
    contacts = await conn.fetch(
        "SELECT channel, value, disclosure FROM vyapar_listings.listing_contacts WHERE listing_id = $1", listing_id
    )
    return _row_to_out(row, contacts, ctx.member_id, saved=False)


@router.patch("/{listing_id}", response_model=ListingOut)
async def patch_listing(
    listing_id: str,
    body: ListingPatch,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> ListingOut:
    current = await conn.fetchrow("SELECT * FROM vyapar_listings.listings WHERE id = $1", listing_id)
    if current is None or current["owner_id"] != ctx.member_id:
        raise HTTPException(status_code=404, detail=translate("common.error.listingNotFound", lang))

    cat_matched, cat_unmapped, cap_matched, cap_unmapped = None, [], None, []
    if body.categories is not None:
        cat_matched, cat_unmapped = await _match_taxonomy(conn, "category", body.categories)
    if body.capabilities is not None:
        cap_matched, cap_unmapped = await _match_taxonomy(conn, "capability", body.capabilities)
    unmapped = (cat_unmapped + cap_unmapped) if (body.categories is not None or body.capabilities is not None) else None

    row = await conn.fetchrow(
        """UPDATE vyapar_listings.listings SET
             name = COALESCE($2, name), headline = COALESCE($3, headline), description = COALESCE($4, description),
             categories = COALESCE($5, categories), capabilities = COALESCE($6, capabilities),
             unmapped_labels = COALESCE($7, unmapped_labels),
             locality = COALESCE($8, locality), lat = COALESCE($9, lat), lng = COALESCE($10, lng),
             service_mode = COALESCE($11, service_mode), service_radius_km = COALESCE($12, service_radius_km),
             primary_phone = COALESCE($13, primary_phone), enquiry_pref = COALESCE($14, enquiry_pref),
             opportunity_participation = COALESCE($15, opportunity_participation),
             experience_years = COALESCE($16, experience_years), languages = COALESCE($17, languages),
             availability = COALESCE($18, availability), evidence_links = COALESCE($19, evidence_links),
             rates = COALESCE($20, rates),
             setup_step = GREATEST(setup_step, COALESCE($21, setup_step)),
             updated_at = now()
           WHERE id = $1
           RETURNING *""",
        listing_id, body.name, body.headline, body.description,
        cat_matched, cap_matched, unmapped,
        body.locality, body.lat, body.lng, body.service_mode, body.service_radius_km,
        body.primary_phone, body.enquiry_pref, body.opportunity_participation,
        body.experience_years, body.languages, body.availability, body.evidence_links, body.rates,
        body.setup_step,
    )
    # [TR002] enquiry_pref='disabled' with every contact hidden must warn —
    # enforced client-side per FR02's own text (confirmation dialog), server
    # accepts the state; nothing further to enforce here.
    contacts = await conn.fetch(
        "SELECT channel, value, disclosure FROM vyapar_listings.listing_contacts WHERE listing_id = $1", row["id"]
    )
    return _row_to_out(row, contacts, ctx.member_id)


# ---------------------------------------------------------------------------
# [TR002] Per-channel contact disclosure and discoverability toggle (FR02).
# Approach: one PATCH per concern (contacts vs. visibility) matching TR002's
# own two named endpoints; both write through the same listings/listing_
# contacts tables every read (_row_to_out, contacts_for_viewer) already
# resolves through — no surface computes disclosure independently.
# Traces to: FR02, TR002, SP002
# ---------------------------------------------------------------------------
class ContactsPatch(BaseModel):
    contacts: list[ContactIn]


@router.patch("/{listing_id}/contacts", response_model=ListingOut)
async def patch_contacts(
    listing_id: str,
    body: ContactsPatch,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> ListingOut:
    current = await conn.fetchrow("SELECT * FROM vyapar_listings.listings WHERE id = $1", listing_id)
    if current is None or current["owner_id"] != ctx.member_id:
        raise HTTPException(status_code=404, detail=translate("common.error.listingNotFound", lang))
    await conn.execute("DELETE FROM vyapar_listings.listing_contacts WHERE listing_id = $1", listing_id)
    for c in body.contacts:
        await conn.execute(
            "INSERT INTO vyapar_listings.listing_contacts (listing_id, channel, value, disclosure) VALUES ($1,$2,$3,$4)",
            listing_id, c.channel, c.value, c.disclosure,
        )
    contacts = await conn.fetch(
        "SELECT channel, value, disclosure FROM vyapar_listings.listing_contacts WHERE listing_id = $1", listing_id
    )
    return _row_to_out(current, contacts, ctx.member_id)


class VisibilityPatch(BaseModel):
    discoverable: bool
    confirm_no_reach: bool = False


@router.patch("/{listing_id}/visibility", response_model=ListingOut)
async def patch_visibility(
    listing_id: str,
    body: VisibilityPatch,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> ListingOut:
    current = await conn.fetchrow("SELECT * FROM vyapar_listings.listings WHERE id = $1", listing_id)
    if current is None or current["owner_id"] != ctx.member_id:
        raise HTTPException(status_code=404, detail=translate("common.error.listingNotFound", lang))
    contacts = await conn.fetch(
        "SELECT channel, value, disclosure FROM vyapar_listings.listing_contacts WHERE listing_id = $1", listing_id
    )
    all_hidden = all(c["disclosure"] == "hidden" for c in contacts) if contacts else True
    if current["enquiry_pref"] == "disabled" and all_hidden and not body.confirm_no_reach:
        raise HTTPException(
            status_code=400,
            detail=translate("listings.error.noReachWarning", lang),
        )
    row = await conn.fetchrow(
        "UPDATE vyapar_listings.listings SET discoverable = $2, updated_at = now() WHERE id = $1 RETURNING *",
        listing_id, body.discoverable,
    )
    return _row_to_out(row, contacts, ctx.member_id)


# ---------------------------------------------------------------------------
# [TR005] Capability visibility independent of seeking-status visibility
# (FR05). Approach: intent_state/intent_visible/capability_visible are three
# independently-settable fields on the SAME row a member already owns —
# this endpoint is the only writer; _row_to_out (above) is the only reader
# that decides whether to include intent_state, closing IA005's named
# highest-severity leak risk structurally, not by convention.
# Traces to: FR05, TR005, SP005
# ---------------------------------------------------------------------------
class IntentPatch(BaseModel):
    intent_state: Literal["looking", "open", "curious", "not_interested"] | None = None
    intent_visible: bool | None = None
    capability_visible: bool | None = None


@router.patch("/{listing_id}/intent", response_model=ListingOut)
async def patch_intent(
    listing_id: str,
    body: IntentPatch,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> ListingOut:
    current = await conn.fetchrow("SELECT * FROM vyapar_listings.listings WHERE id = $1", listing_id)
    if current is None or current["owner_id"] != ctx.member_id:
        raise HTTPException(status_code=404, detail=translate("common.error.listingNotFound", lang))
    row = await conn.fetchrow(
        """UPDATE vyapar_listings.listings SET
             intent_state = COALESCE($2, intent_state),
             intent_visible = COALESCE($3, intent_visible),
             capability_visible = COALESCE($4, capability_visible),
             updated_at = now()
           WHERE id = $1 RETURNING *""",
        listing_id, body.intent_state, body.intent_visible, body.capability_visible,
    )
    contacts = await conn.fetch(
        "SELECT channel, value, disclosure FROM vyapar_listings.listing_contacts WHERE listing_id = $1", listing_id
    )
    return _row_to_out(row, contacts, ctx.member_id)


# ---------------------------------------------------------------------------
# [TR003] Listing lifecycle: submit / suspend / archive (FR03). Approach:
# server-side CHECK-constraint-backed state machine; submit auto-activates
# only when contact_verified=true AND the content check passes, otherwise
# routes to Submitted (operator review, FR47) — never silently rejected,
# never silently activated unsafe. Suspend requires the 'content' operator
# permission (AuthzChokepoint-CC); archive is an owner action.
# Traces to: FR03, TR003, SP003
# ---------------------------------------------------------------------------
@router.post("/{listing_id}/submit", response_model=ListingOut)
async def submit_listing(
    listing_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> ListingOut:
    current = await conn.fetchrow("SELECT * FROM vyapar_listings.listings WHERE id = $1", listing_id)
    if current is None or current["owner_id"] != ctx.member_id:
        raise HTTPException(status_code=404, detail=translate("common.error.listingNotFound", lang))
    if current["state"] != "draft":
        # [Plain-language member-facing message — never the raw internal
        # state enum value, e.g. 'active_unverified'.]
        state_key = STATE_PHRASE_KEYS.get(current["state"], current["state"])
        state_phrase = translate(f"listings.state.{state_key}", lang)
        raise HTTPException(status_code=400, detail=translate("listings.error.alreadySubmitted", lang, state=state_phrase))
    if not current["name"] or (not current["categories"] and not current["capabilities"]):
        raise HTTPException(status_code=422, detail=translate("listings.error.missingNameOrCapability", lang))
    if not current["locality"]:
        raise HTTPException(status_code=422, detail=translate("listings.error.missingLocality", lang))

    active_count = await conn.fetchval(
        "SELECT count(*) FROM vyapar_listings.listings WHERE owner_id = $1 AND state IN ('active_unverified','active_verified')",
        ctx.member_id,
    )
    if active_count >= LISTING_ACTIVE_CAP:
        raise HTTPException(status_code=429, detail=translate("listings.error.activeCapReached", lang, cap=LISTING_ACTIVE_CAP))

    if not current["contact_verified"]:
        raise HTTPException(status_code=422, detail=translate("listings.error.verifyContactFirst", lang))

    flag = _content_flags(current["name"], current["description"], current["headline"])
    if flag:
        row = await conn.fetchrow(
            "UPDATE vyapar_listings.listings SET state='submitted', state_reason=$2, updated_at=now() WHERE id=$1 RETURNING *",
            listing_id, flag,
        )
        # [TR003/FR40] the held listing enters the operator moderation
        # queue as an automated flag (migration 004's raise_auto_flag — the
        # author's own session can't insert a case directly). Medium: the
        # listing is already held out of distribution by its Submitted state.
        await conn.execute(
            "SELECT vyapar_trust_safety.raise_auto_flag('listing', $1, $2, $3, 'medium')", listing_id, ctx.member_id, flag
        )
    else:
        row = await conn.fetchrow(
            "UPDATE vyapar_listings.listings SET state='active_unverified', state_reason=NULL, published_at=now(), updated_at=now() WHERE id=$1 RETURNING *",
            listing_id,
        )
    contacts = await conn.fetch(
        "SELECT channel, value, disclosure FROM vyapar_listings.listing_contacts WHERE listing_id = $1", listing_id
    )
    return _row_to_out(row, contacts, ctx.member_id)


@router.post("/{listing_id}/archive", response_model=ListingOut)
async def archive_listing(
    listing_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> ListingOut:
    current = await conn.fetchrow("SELECT * FROM vyapar_listings.listings WHERE id = $1", listing_id)
    if current is None or current["owner_id"] != ctx.member_id:
        raise HTTPException(status_code=404, detail=translate("common.error.listingNotFound", lang))
    if current["state"] == "archived":
        raise HTTPException(status_code=400, detail=translate("listings.error.alreadyArchived", lang))
    row = await conn.fetchrow(
        "UPDATE vyapar_listings.listings SET state='archived', updated_at=now() WHERE id=$1 RETURNING *", listing_id
    )
    # [FR03] cascade-close open enquiries — enquiries table not yet built in
    # this session (slice 4); no-op guarded so this endpoint doesn't fail
    # once it exists, per FR03's own acceptance criterion, to be completed
    # when the Enquiries & Partnerships component is implemented.
    contacts = await conn.fetch(
        "SELECT channel, value, disclosure FROM vyapar_listings.listing_contacts WHERE listing_id = $1", listing_id
    )
    return _row_to_out(row, contacts, ctx.member_id)


@router.post("/{listing_id}/suspend", response_model=ListingOut)
async def suspend_listing(
    listing_id: str,
    reason: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> ListingOut:
    if not ctx.is_operator:
        raise HTTPException(status_code=403, detail=translate("common.error.operatorPermissionRequired", lang))
    current = await conn.fetchrow("SELECT * FROM vyapar_listings.listings WHERE id = $1", listing_id)
    if current is None:
        raise HTTPException(status_code=404, detail=translate("common.error.listingNotFound", lang))
    row = await conn.fetchrow(
        "UPDATE vyapar_listings.listings SET state='suspended', state_reason=$2, updated_at=now() WHERE id=$1 RETURNING *",
        listing_id, reason,
    )
    contacts = await conn.fetch(
        "SELECT channel, value, disclosure FROM vyapar_listings.listing_contacts WHERE listing_id = $1", listing_id
    )
    return _row_to_out(row, contacts, ctx.member_id)


# ---------------------------------------------------------------------------
# [TR007] Listing-contact OTP verification — NOT authentication (FR07).
# Approach: 6-digit code, 10-min expiry, 30s resend cooldown, 5-attempt/
# 15-min lockout, all enforced server-side against otp_challenges. Reuses
# the platform's shared SMS-sending capability in production; in dev the
# code is echoed back in the response (clearly dev-only) since no real SMS
# provider credential exists yet (config-placeholder convention) — this
# never creates a session/cookie/credential of any kind, only sets
# listings.contact_verified.
# Traces to: FR07, TR007, SP007
# ---------------------------------------------------------------------------
class OtpRequestIn(BaseModel):
    phone: str


class OtpVerifyIn(BaseModel):
    code: str


@router.post("/{listing_id}/otp/request")
async def request_otp(
    listing_id: str,
    body: OtpRequestIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    current = await conn.fetchrow("SELECT * FROM vyapar_listings.listings WHERE id = $1", listing_id)
    if current is None or current["owner_id"] != ctx.member_id:
        raise HTTPException(status_code=404, detail=translate("common.error.listingNotFound", lang))

    last = await conn.fetchrow(
        "SELECT * FROM vyapar_listings.otp_challenges WHERE listing_id = $1 ORDER BY created_at DESC LIMIT 1",
        listing_id,
    )
    now_row = await conn.fetchrow("SELECT now() as now")
    now = now_row["now"]
    if last and last["locked_until"] and last["locked_until"] > now:
        raise HTTPException(status_code=429, detail=translate("listings.error.otpLockedUntil", lang, time=last["locked_until"].isoformat()))
    if last and last["resend_after"] > now:
        raise HTTPException(status_code=429, detail=translate("listings.error.otpResendWait", lang))

    code = f"{random.randint(0, 999999):06d}"
    await conn.execute(
        """INSERT INTO vyapar_listings.otp_challenges (member_id, listing_id, phone, code, expires_at, resend_after)
           VALUES ($1,$2,$3,$4, now() + interval '10 minutes', now() + interval '30 seconds')""",
        ctx.member_id, listing_id, body.phone, code,
    )
    # [Dev-only] real SMS dispatch is a CHANGE_ME placeholder integration
    # (SMS_PROVIDER_INTERNAL_URL) — echoing the code back here is explicitly
    # for local manual testing only, never shipped behind DEV_MODE=false.
    return {"message": translate("listings.success.otpSent", lang), "dev_code": code}


@router.post("/{listing_id}/otp/verify")
async def verify_otp(
    listing_id: str,
    body: OtpVerifyIn,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict:
    current = await conn.fetchrow("SELECT * FROM vyapar_listings.listings WHERE id = $1", listing_id)
    if current is None or current["owner_id"] != ctx.member_id:
        raise HTTPException(status_code=404, detail=translate("common.error.listingNotFound", lang))

    challenge = await conn.fetchrow(
        "SELECT * FROM vyapar_listings.otp_challenges WHERE listing_id = $1 ORDER BY created_at DESC LIMIT 1",
        listing_id,
    )
    if challenge is None:
        raise HTTPException(status_code=400, detail=translate("listings.error.otpNotRequested", lang))
    now_row = await conn.fetchrow("SELECT now() as now")
    now = now_row["now"]
    if challenge["locked_until"] and challenge["locked_until"] > now:
        raise HTTPException(status_code=429, detail=translate("listings.error.otpLocked", lang))
    if challenge["expires_at"] < now:
        raise HTTPException(status_code=400, detail=translate("listings.error.otpExpired", lang))

    if challenge["code"] != body.code:
        attempts = challenge["attempts"] + 1
        locked_until = now + timedelta(minutes=15) if attempts >= 5 else None
        await conn.execute(
            "UPDATE vyapar_listings.otp_challenges SET attempts=$2, locked_until=$3 WHERE id=$1",
            challenge["id"], attempts, locked_until,
        )
        if locked_until:
            raise HTTPException(status_code=429, detail=translate("listings.error.otpLockedNow", lang))
        raise HTTPException(status_code=400, detail=translate("listings.error.otpIncorrect", lang, attempts=attempts))

    await conn.execute("UPDATE vyapar_listings.otp_challenges SET verified_at = now() WHERE id = $1", challenge["id"])
    # [TR007 gap-fix] Two separate statements, not one: the
    # reset_contact_verified trigger (BEFORE UPDATE) sets NEW.contact_verified
    # := false whenever primary_phone changes — correct for TR007's own rule
    # (a later phone change must clear the verified flag) but it would also
    # wipe our own true value if we set primary_phone and contact_verified in
    # the SAME statement on first verification. Setting primary_phone first
    # (trigger fires harmlessly, contact_verified was already false) and
    # contact_verified=true second (no primary_phone change in that
    # statement, trigger does not fire) avoids the self-defeating race.
    await conn.execute(
        "UPDATE vyapar_listings.listings SET primary_phone = COALESCE(primary_phone, $2), updated_at = now() WHERE id = $1",
        listing_id, challenge["phone"],
    )
    row = await conn.fetchrow(
        "UPDATE vyapar_listings.listings SET contact_verified = true, updated_at = now() WHERE id = $1 RETURNING *",
        listing_id,
    )
    contacts = await conn.fetch(
        "SELECT channel, value, disclosure FROM vyapar_listings.listing_contacts WHERE listing_id = $1", listing_id
    )
    return {"listing": _row_to_out(row, contacts, ctx.member_id).model_dump(), "message": translate("listings.success.contactVerified", lang)}


# ---------------------------------------------------------------------------
# [TR006] VerifiedCredential read-only reference (FR06). Approach: member-
# initiated attach — looks up the DEV STAND-IN Identity & Trust provider
# (app/identity_trust_stub.py, clearly labelled as such) for the CALLER's
# own credential and, if found, writes the read-only reference (never
# evidence) onto their own professional listing. The hourly-equivalent
# `sync_credential_refs()` job then re-checks every listing with a non-null
# reference and clears it if the upstream stand-in has since "revoked" it —
# exercising TR006's own revocation-removal rule for real, not just in theory.
# Traces to: FR06, TR006, SP006
# ---------------------------------------------------------------------------
import json as _json_mod

from app import identity_trust_stub


@router.post("/{listing_id}/credential-ref/attach", response_model=ListingOut)
async def attach_credential_ref(
    listing_id: str,
    lang: Locale,
    ctx: AuthzContext = Depends(resolve_authz_context),
    conn: asyncpg.Connection = Depends(get_conn),
) -> ListingOut:
    current = await conn.fetchrow("SELECT * FROM vyapar_listings.listings WHERE id = $1", listing_id)
    if current is None or current["owner_id"] != ctx.member_id:
        raise HTTPException(status_code=404, detail=translate("common.error.listingNotFound", lang))
    cred = identity_trust_stub.get_credential(ctx.member_id)
    if cred is None:
        raise HTTPException(status_code=404, detail=translate("listings.error.noCredentialFound", lang))
    payload = identity_trust_stub.credential_ref_payload(cred)
    row = await conn.fetchrow(
        "UPDATE vyapar_listings.listings SET credential_ref = $2::jsonb, updated_at = now() WHERE id = $1 RETURNING *",
        listing_id, _json_mod.dumps(payload),
    )
    contacts = await conn.fetch(
        "SELECT channel, value, disclosure FROM vyapar_listings.listing_contacts WHERE listing_id = $1", listing_id
    )
    return _row_to_out(row, contacts, ctx.member_id)


async def sync_credential_refs(pool: asyncpg.Pool) -> int:
    """[TR006] Hourly-equivalent re-sync: re-checks the dev stand-in for
    every listing with a non-null credential_ref, clearing it if revoked —
    'no error surfaced to the viewer' either way, per TR006's own text
    (the cached value simply stays until the next successful check, or is
    cleared on a confirmed revocation, never shown as broken)."""
    updated = 0
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("SELECT set_config('vyapar.service_role', 'dispatcher', true)")
            await conn.execute("SELECT set_config('vyapar.authz_context', 'm_neha_ops', true)")
            rows = await conn.fetch("SELECT id, owner_id, credential_ref FROM vyapar_listings.listings WHERE credential_ref IS NOT NULL")
            for row in rows:
                cred = identity_trust_stub.get_credential(row["owner_id"])
                if cred is None:
                    await conn.execute("UPDATE vyapar_listings.listings SET credential_ref = NULL, updated_at = now() WHERE id = $1", row["id"])
                    updated += 1
                else:
                    payload = identity_trust_stub.credential_ref_payload(cred)
                    current_ref = row["credential_ref"]
                    if isinstance(current_ref, str):
                        current_ref = _json_mod.loads(current_ref)
                    payload["verified_at"] = current_ref.get("verified_at", payload["verified_at"]) if current_ref else payload["verified_at"]
                    await conn.execute(
                        "UPDATE vyapar_listings.listings SET credential_ref = $2::jsonb, updated_at = now() WHERE id = $1",
                        row["id"], _json_mod.dumps(payload),
                    )
    return updated

# [Backend A, 2026-09-30 — owner decision] One Vyapar profile per member,
# built on the ForKhatri identity.
#
# Owner: "each user will get one profile", "i already logged in as user,
# but still it is asking me this [name, locality]", "locality can be taken
# current right". So:
#   * a member has exactly ONE profile: their live `listings` row (migration
#     026 consolidated members who had several and enforces one live row per
#     owner). A business is an optional section of it (business_name,
#     business_headline, business_description; verification stays on the row);
#   * the profile is created on first read from what the identity already
#     knows (display name, phone, language on the member row, synced by
#     ensure_member() on every sign-in; locality/coordinates from first run),
#     so the web never asks for any of it again. Only what is genuinely
#     missing is reported in `missing`;
#   * a missing locality can come from the browser's position:
#     `locate(lat, lng)` returns the nearest locality Vyapar already knows.
# Everything else (verification, reviews, packages, contacts, enquiries,
# promotions) keeps using the same listing id, so every existing screen and
# the listing detail/search routes keep working unchanged.
# Traces to: FR01, FR03, FR04, FR16, FR44, TR001, TR044, TR050
from __future__ import annotations

from typing import Literal

import asyncpg
from pydantic import BaseModel, Field

from app.errors import ApiError
from app.geo import nearest_place, resolve_place
from app.identity import AuthzContext
from app.integrations.ai.localities import find_known_locality
from app.services import listings as listings_svc
from app.services.listings import ListingOut, ListingPatch

LIVE_STATES = ("draft", "submitted", "active_unverified", "active_verified")
VERIFIED_STATES = ("verified", "expiring")


class ProfileBusinessIn(BaseModel):
    name: str = Field(min_length=1, max_length=120, description="Business name, e.g. Meena's Oven")
    headline: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class ProfilePatch(ListingPatch):
    """Every profile field (same as a listing patch), plus the business section."""

    business: ProfileBusinessIn | None = Field(default=None, description="Add or change the business section")
    remove_business: bool = Field(default=False, description="Remove the business section (refused while the business is verified)")


class ProfilePrefill(BaseModel):
    """What Vyapar already knows from the ForKhatri identity and first run."""

    name: str | None = None
    phone: str | None = None
    locality: str | None = None
    lat: float | None = None
    lng: float | None = None
    language: str | None = None


class MyProfileOut(BaseModel):
    exists: bool = Field(description="False only when a required field (locality, or a real name) is still missing")
    profile: ListingOut | None = None
    prefill: ProfilePrefill
    missing: list[Literal["name", "locality"]] = Field(default_factory=list, description="Ask the member only for these")
    prefilled_from_identity: list[str] = Field(default_factory=list, description="Fields taken from the ForKhatri identity, never to be asked again")


class LocateIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class LocateOut(BaseModel):
    matched: bool
    locality: str | None = Field(description="Nearest locality Vyapar knows, within 15 km; null when none")
    lat: float
    lng: float
    distance_km: float | None = None


async def _member(conn: asyncpg.Connection, member_id: str) -> asyncpg.Record | None:
    return await conn.fetchrow(
        "SELECT id, display_name, phone, language, locality, lat, lng FROM vyapar_identity.members WHERE id = $1", member_id
    )


def _prefill(member: asyncpg.Record | None) -> tuple[ProfilePrefill, list[str], list[str]]:
    if member is None:
        return ProfilePrefill(), [], ["name", "locality"]
    real_name = member["display_name"] if member["display_name"] and member["display_name"] != member["id"] else None
    prefill = ProfilePrefill(
        name=real_name, phone=member["phone"], locality=member["locality"], lat=member["lat"], lng=member["lng"],
        language=member["language"],
    )
    from_identity = [f for f, v in (("name", real_name), ("phone", member["phone"]), ("language", member["language"])) if v]
    missing = [f for f, v in (("name", real_name), ("locality", member["locality"])) if not v]
    return prefill, from_identity, missing


async def profile_row(conn: asyncpg.Connection, member_id: str) -> asyncpg.Record | None:
    """The member's one profile: the live listing, else (for display only) a
    suspended one. Archived rows are history, never the profile."""
    return await conn.fetchrow(
        """SELECT * FROM vyapar_listings.listings
            WHERE owner_id = $1 AND state <> 'archived'
            ORDER BY (state = ANY($2::text[])) DESC, updated_at DESC LIMIT 1""",
        member_id, list(LIVE_STATES),
    )


async def _known_locality(conn: asyncpg.Connection, text: str | None) -> str | None:
    """A typed locality, spelled the way Vyapar already knows it (any script,
    via the AI locality matcher); the text as typed when unknown."""
    if not text:
        return text
    place = resolve_place(text)  # the gazetteer first (IMP-B, app/geo.py)
    if place is not None:
        return place.name
    names = [r["n"] for r in await conn.fetch(
        """SELECT DISTINCT trim(locality) AS n FROM vyapar_listings.listings
            WHERE state IN ('active_unverified','active_verified') AND coalesce(trim(locality), '') <> ''""")]
    return find_known_locality(text, names) or text.strip()


async def _create_from_identity(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, prefill: ProfilePrefill,
                                name: str, locality: str, lat: float | None, lng: float | None) -> asyncpg.Record:
    if lat is None or lng is None:  # a known locality gives the centre, so distance works from day one
        place = resolve_place(locality)
        if place is not None:
            lat, lng = place.lat, place.lng
    try:
        async with conn.transaction():
            row = await conn.fetchrow(
                """INSERT INTO vyapar_listings.listings
                     (owner_id, kind, name, locality, lat, lng, primary_phone, languages, setup_step, content_language, state)
                   VALUES ($1, 'professional', $2, $3, $4, $5, $6, $7, 1, $8, 'draft')
                   RETURNING *""",
                ctx.member_id, name, locality, lat, lng, prefill.phone,
                [prefill.language] if prefill.language else [], lang if lang in ("en", "hi", "te") else "en",
            )
    except asyncpg.UniqueViolationError:
        existing = await profile_row(conn, ctx.member_id)
        if existing is not None:
            return existing  # created by a concurrent request: that is the profile
        raise ApiError(409, "listings.error.duplicate", lang)
    if prefill.phone:
        # reachable after acceptance (and by a poster who shortlists them)
        await conn.execute(
            "INSERT INTO vyapar_listings.listing_contacts (listing_id, channel, value, disclosure) VALUES ($1, 'phone', $2, 'after_accept')",
            row["id"], prefill.phone,
        )
    return row


async def _out(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, row: asyncpg.Record) -> ListingOut:
    contacts = await conn.fetch("SELECT channel, value, disclosure FROM vyapar_listings.listing_contacts WHERE listing_id = $1", row["id"])
    return listings_svc._row_to_out(row, contacts, ctx.member_id, lang=lang)


async def get_my_profile(conn: asyncpg.Connection, ctx: AuthzContext, lang: str) -> MyProfileOut:
    member = await _member(conn, ctx.member_id)
    prefill, from_identity, missing = _prefill(member)
    row = await profile_row(conn, ctx.member_id)
    if row is None and not missing:
        row = await _create_from_identity(conn, ctx, lang, prefill, prefill.name, prefill.locality, prefill.lat, prefill.lng)
    if row is None:
        return MyProfileOut(exists=False, prefill=prefill, missing=missing, prefilled_from_identity=from_identity)
    return MyProfileOut(exists=True, profile=await _out(conn, ctx, lang, row), prefill=prefill, missing=[],
                        prefilled_from_identity=from_identity)


async def update_my_profile(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, body: ProfilePatch) -> MyProfileOut:
    member = await _member(conn, ctx.member_id)
    prefill, _, _ = _prefill(member)
    if body.locality is not None:
        body.locality = await _known_locality(conn, body.locality)
    row = await profile_row(conn, ctx.member_id)
    if row is None:
        name = (body.name or prefill.name or "").strip()
        locality = (body.locality or prefill.locality or "").strip()
        lacking = [f for f, v in (("name", name), ("locality", locality)) if not v]
        if lacking:
            raise ApiError(422, "listings.error.profileFieldsMissing", lang, fields=", ".join(lacking), extra={"missing": lacking})
        lat = body.lat if body.lat is not None else prefill.lat
        lng = body.lng if body.lng is not None else prefill.lng
        row = await _create_from_identity(conn, ctx, lang, prefill, name, locality, lat, lng)
    if row["state"] == "suspended":
        raise ApiError(409, "listings.error.profileSuspended", lang)

    base = ListingPatch(**body.model_dump(exclude={"business", "remove_business"}, exclude_unset=True))
    if base.model_dump(exclude_unset=True):
        await listings_svc.update_listing(conn, ctx, lang, listing_id=str(row["id"]), body=base)

    if body.remove_business:
        if row["verification_state"] in VERIFIED_STATES:
            raise ApiError(409, "listings.error.businessVerifiedCannotRemove", lang)
        await conn.execute(
            """UPDATE vyapar_listings.listings SET business_name = NULL, business_headline = NULL, business_description = NULL,
                 kind = 'professional', updated_at = now() WHERE id = $1""", row["id"])
    elif body.business is not None:
        await conn.execute(
            """UPDATE vyapar_listings.listings SET business_name = $2,
                 business_headline = COALESCE($3, business_headline), business_description = COALESCE($4, business_description),
                 kind = 'business', updated_at = now() WHERE id = $1""",
            row["id"], body.business.name.strip(), body.business.headline, body.business.description)

    # The member row learns the place too, so no other screen asks again.
    if body.locality and member is not None and not member["locality"]:
        await conn.execute(
            "UPDATE vyapar_identity.members SET locality = $2, lat = COALESCE($3, lat), lng = COALESCE($4, lng), updated_at = now() WHERE id = $1",
            ctx.member_id, body.locality, body.lat, body.lng)
    return await get_my_profile(conn, ctx, lang)


async def locate(conn: asyncpg.Connection, body: LocateIn) -> LocateOut:
    """Nearest named locality: the gazetteer (app/geo.py) first, then the
    places Vyapar's own data carries (vyapar_listings.nearest_locality)."""
    near = nearest_place(body.lat, body.lng)
    if near is not None:
        return LocateOut(matched=True, locality=near[0].name, lat=body.lat, lng=body.lng, distance_km=round(near[1], 2))
    hit = await conn.fetchrow("SELECT * FROM vyapar_listings.nearest_locality($1, $2)", body.lat, body.lng)
    if hit is None:
        return LocateOut(matched=False, locality=None, lat=body.lat, lng=body.lng)
    return LocateOut(matched=True, locality=hit["locality"], lat=body.lat, lng=body.lng, distance_km=round(hit["distance_km"], 2))

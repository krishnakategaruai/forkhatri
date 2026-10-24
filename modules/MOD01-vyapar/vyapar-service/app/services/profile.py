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

from app.config import get_settings
from app.errors import ApiError
from app.geo import nearby_places, nearest_place, resolve_place
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
    # [Start flow 2026-10, decision 8] "Save means live": after saving, submit
    # the profile the same way the Submit button does. It goes live as "New on
    # Vyapar" when the contact is verified and the content check passes;
    # otherwise it simply stays a draft (the reason is reported in `publish_blocked`).
    publish: bool = Field(default=False, description="After saving, submit the profile so it goes live when the server rules allow")


class ProfilePrefill(BaseModel):
    """What Vyapar already knows from the ForKhatri identity and first run."""

    name: str | None = None
    phone: str | None = None
    locality: str | None = None
    lat: float | None = None
    lng: float | None = None
    language: str | None = None
    # [Start flow 2026-10, decision 2] the host verified this phone at sign-in
    phone_verified: bool = False
    date_of_birth_known: bool = False


class MyProfileOut(BaseModel):
    exists: bool = Field(description="False only when a required field (locality, or a real name) is still missing")
    profile: ListingOut | None = None
    prefill: ProfilePrefill
    missing: list[Literal["name", "locality"]] = Field(default_factory=list, description="Ask the member only for these")
    prefilled_from_identity: list[str] = Field(default_factory=list, description="Fields taken from the ForKhatri identity, never to be asked again")
    publish_blocked: str | None = Field(default=None, description="When `publish` was asked and the profile stayed a draft: the server's reason (error code)")


class CompletionQuestion(BaseModel):
    """[Start flow 2026-10, decision 12] One question per visit, never blocking."""

    key: Literal["experience_years", "own_assets", "headline", "service_radius_km"]
    kind: Literal["choice", "multi", "text"]
    question: str
    options: list[dict[str, str]] = Field(default_factory=list, description="[{value,label}] for choice/multi")
    placeholder: str | None = None


class CompletionOut(BaseModel):
    percent: int
    done: list[str]
    next: CompletionQuestion | None


class LocateIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class LocateOut(BaseModel):
    matched: bool
    locality: str | None = Field(description="Nearest locality Vyapar knows, within 15 km; null when none")
    lat: float
    lng: float
    distance_km: float | None = None
    # [Start flow 2026-10, decision 6] areas within about 25 km, nearest first,
    # for one-tap chips; empty elsewhere, so no city's list is offered to
    # someone in another city.
    nearby: list[str] = Field(default_factory=list)
    source: Literal["gazetteer", "listings", "places", "none"] = "none"


async def _member(conn: asyncpg.Connection, member_id: str) -> asyncpg.Record | None:
    return await conn.fetchrow(
        "SELECT id, display_name, phone, language, locality, lat, lng, phone_verified, date_of_birth FROM vyapar_identity.members WHERE id = $1",
        member_id,
    )


def _prefill(member: asyncpg.Record | None) -> tuple[ProfilePrefill, list[str], list[str]]:
    if member is None:
        return ProfilePrefill(), [], ["name", "locality"]
    real_name = member["display_name"] if member["display_name"] and member["display_name"] != member["id"] else None
    prefill = ProfilePrefill(
        name=real_name, phone=member["phone"], locality=member["locality"], lat=member["lat"], lng=member["lng"],
        language=member["language"], phone_verified=bool(member["phone_verified"]) and bool(member["phone"]),
        date_of_birth_known=member["date_of_birth"] is not None,
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
            # [Start flow 2026-10, decision 2] a phone the host verified at
            # sign-in is this profile's verified contact; OTP is only for a
            # different number (the FR07 trigger still resets it on change).
            row = await conn.fetchrow(
                """INSERT INTO vyapar_listings.listings
                     (owner_id, kind, name, locality, lat, lng, primary_phone, languages, setup_step, content_language, state, contact_verified)
                   VALUES ($1, 'professional', $2, $3, $4, $5, $6, $7, 1, $8, 'draft', $9)
                   RETURNING *""",
                ctx.member_id, name, locality, lat, lng, prefill.phone,
                [prefill.language] if prefill.language else [], lang if lang in ("en", "hi", "te", "mr", "kn") else "en",
                bool(prefill.phone and prefill.phone_verified),
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
    out = listings_svc._row_to_out(row, contacts, ctx.member_id, lang=lang)
    await listings_svc.enrich_trust(conn, ctx, lang, out, row)  # [Trust pack] badges, paid on time, restriction
    return out


async def _verify_identity_contact(conn: asyncpg.Connection, prefill: ProfilePrefill, row: asyncpg.Record) -> asyncpg.Record:
    """[Start flow 2026-10, decision 2] A profile whose phone is the member's
    host-verified phone counts as contact-verified, also for profiles made
    before migration 032 (e.g. the audit's drafts). Nothing else changes."""
    if row["contact_verified"] or not prefill.phone_verified or not prefill.phone:
        return row
    if (row["primary_phone"] or "") != prefill.phone:
        return row
    updated = await conn.fetchrow(
        "UPDATE vyapar_listings.listings SET contact_verified = true, updated_at = now() WHERE id = $1 RETURNING *", row["id"]
    )
    return updated or row


async def get_my_profile(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, *, publish_blocked: str | None = None) -> MyProfileOut:
    member = await _member(conn, ctx.member_id)
    prefill, from_identity, missing = _prefill(member)
    row = await profile_row(conn, ctx.member_id)
    if row is None and not missing:
        row = await _create_from_identity(conn, ctx, lang, prefill, prefill.name, prefill.locality, prefill.lat, prefill.lng)
    if row is None:
        return MyProfileOut(exists=False, prefill=prefill, missing=missing, prefilled_from_identity=from_identity)
    row = await _verify_identity_contact(conn, prefill, row)
    return MyProfileOut(exists=True, profile=await _out(conn, ctx, lang, row), prefill=prefill, missing=[],
                        prefilled_from_identity=from_identity, publish_blocked=publish_blocked)


async def ensure_profile(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, *, locality: str | None = None,
                         lat: float | None = None, lng: float | None = None) -> asyncpg.Record | None:
    """[Start flow 2026-10, decision 3] The one profile, created from the
    identity when it does not exist yet. `locality` is used only when the
    member has not named their own area (a hirer's first post names the
    shop's area; a worker's start names where they live). Returns the row,
    or None when even a name is missing (the dev stub with no real name)."""
    row = await profile_row(conn, ctx.member_id)
    if row is not None:
        return row
    member = await _member(conn, ctx.member_id)
    prefill, _from_identity, missing = _prefill(member)
    if "name" in missing:
        return None
    place = (prefill.locality or (locality or "").strip()) or None
    if not place:
        return None
    if prefill.locality is None:
        place = await _known_locality(conn, place)
    row = await _create_from_identity(conn, ctx, lang, prefill, prefill.name or "", place,
                                      prefill.lat if prefill.locality else lat, prefill.lng if prefill.locality else lng)
    if member is not None and not member["locality"]:
        await conn.execute(
            "UPDATE vyapar_identity.members SET locality = $2, lat = COALESCE($3, lat), lng = COALESCE($4, lng), updated_at = now() WHERE id = $1",
            ctx.member_id, place, lat, lng)
    return row


async def try_publish(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, listing_id: str) -> str | None:
    """[Decision 8] Submit a draft profile the way the Submit button does; the
    server rules (terms accepted, contact verified, content check) decide
    whether it goes live. Returns None when live or already past draft, else
    the rule that held it (an error code the client can explain)."""
    try:
        await listings_svc.submit_listing(conn, ctx, lang, listing_id=listing_id)
        return None
    except ApiError as e:
        return str(getattr(e, "code", None) or getattr(e, "error_code", None) or getattr(e, "key", None) or "blocked")


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
    blocked: str | None = None
    if body.publish:
        fresh = await profile_row(conn, ctx.member_id)
        if fresh is not None and fresh["state"] == "draft":
            fresh = await _verify_identity_contact(conn, prefill, fresh)
            blocked = await try_publish(conn, ctx, lang, str(fresh["id"]))
    return await get_my_profile(conn, ctx, lang, publish_blocked=blocked)


async def _reverse_via_places(lat: float, lng: float, lang: str) -> str | None:
    """[Decision 6] Outside the gazetteer's cities, the shared places adapter
    (shared/forkhatri-integrations) names the area when a provider is
    configured; off ("none") by default, so this returns None and the screen
    asks the member to type the town."""
    st = get_settings()
    if (st.places_provider or "none").lower() == "none":
        return None
    try:
        from forkhatri_integrations import places

        provider = places.get_provider(st.places_provider, base_url=st.places_base_url, user_agent=st.places_user_agent,
                                       email=st.places_contact_email)
        hit = await provider.reverse(lat, lng, language=lang if lang in ("en", "hi", "te", "mr", "kn") else "en")
    except Exception:  # noqa: BLE001 - an unreachable provider degrades to "please type it"
        return None
    if hit is None:
        return None
    return hit.locality or hit.name or None


async def locate(conn: asyncpg.Connection, body: LocateIn, lang: str = "en") -> LocateOut:
    """Nearest named locality: the gazetteer (app/geo.py) first, then the
    places Vyapar's own data carries (vyapar_listings.nearest_locality), then
    the shared places adapter when one is configured. `nearby` lists areas
    within about 25 km for one-tap chips and is empty anywhere else."""
    nearby = [p.name for p, _d in nearby_places(body.lat, body.lng)]
    near = nearest_place(body.lat, body.lng)
    if near is not None:
        return LocateOut(matched=True, locality=near[0].name, lat=body.lat, lng=body.lng, distance_km=round(near[1], 2),
                         nearby=[n for n in nearby if n != near[0].name], source="gazetteer")
    hit = await conn.fetchrow("SELECT * FROM vyapar_listings.nearest_locality($1, $2)", body.lat, body.lng)
    if hit is not None and (hit["distance_km"] is None or hit["distance_km"] <= 25):
        return LocateOut(matched=True, locality=hit["locality"], lat=body.lat, lng=body.lng, distance_km=round(hit["distance_km"], 2),
                         nearby=[n for n in nearby if n != hit["locality"]], source="listings")
    named = await _reverse_via_places(body.lat, body.lng, lang)
    if named:
        return LocateOut(matched=True, locality=named, lat=body.lat, lng=body.lng, nearby=nearby, source="places")
    return LocateOut(matched=False, locality=None, lat=body.lat, lng=body.lng, nearby=nearby, source="none")


# ---------------------------------------------------------------------------
# [Start flow 2026-10, decision 12] The completion card: a percentage and ONE
# next question, never a wall. Answers are saved through the ordinary
# PATCH /v1/me/profile (experience_years, own_assets, headline,
# service_radius_km), so nothing new is written here.
# ---------------------------------------------------------------------------
_EXPERIENCE_OPTIONS = (("1", "0_2"), ("4", "3_5"), ("8", "6_10"), ("12", "10_plus"))
_ASSET_OPTIONS = ("two_wheeler", "four_wheeler", "driving_licence", "smartphone", "laptop", "own_tools", "none")


def _col(row: asyncpg.Record, name: str):
    try:
        return row[name]
    except (KeyError, IndexError):
        return None


async def profile_completion(conn: asyncpg.Connection, ctx: AuthzContext, lang: str) -> CompletionOut:
    from app.i18n import translate

    row = await profile_row(conn, ctx.member_id)
    if row is None:
        return CompletionOut(percent=0, done=[], next=None)
    business = bool(_col(row, "business_name"))
    own_assets = list(_col(row, "own_assets") or [])
    steps: list[tuple[str, bool]] = [
        ("trade", bool(row["capabilities"]) or bool(row["categories"])),
        ("locality", bool(row["locality"])),
        ("live", row["state"] in ("active_unverified", "active_verified")),
    ]
    if business:
        steps += [("headline", bool(_col(row, "business_headline") or row["headline"]))]
    else:
        steps += [("experience_years", row["experience_years"] is not None), ("own_assets", bool(own_assets)),
                  ("headline", bool(row["headline"]))]
    steps += [("service_radius_km", row["service_radius_km"] is not None),
              ("verified", row["verification_state"] in ("verified", "expiring"))]
    done = [k for k, ok in steps if ok]
    percent = int(round(100 * len(done) / len(steps)))

    def t(k: str, **kw: object) -> str:
        return translate(f"listings.completion.{k}", lang, **kw)

    nxt: CompletionQuestion | None = None
    for key, ok in steps:
        if ok or key in ("trade", "locality", "live", "verified"):
            continue
        if key == "experience_years":
            nxt = CompletionQuestion(key="experience_years", kind="choice", question=t("q.experience_years"),
                                     options=[{"value": v, "label": t(f"experience.{lab}")} for v, lab in _EXPERIENCE_OPTIONS])
        elif key == "own_assets":
            nxt = CompletionQuestion(key="own_assets", kind="multi", question=t("q.own_assets"),
                                     options=[{"value": v, "label": t(f"assets.{v}")} for v in _ASSET_OPTIONS])
        elif key == "headline":
            nxt = CompletionQuestion(key="headline", kind="text", question=t("q.headline_business" if business else "q.headline"),
                                     placeholder=t("placeholder.headline_business" if business else "placeholder.headline"))
        elif key == "service_radius_km":
            nxt = CompletionQuestion(key="service_radius_km", kind="choice", question=t("q.service_radius_km"),
                                     options=[{"value": str(km), "label": t("radius", km=km)} for km in (5, 10, 25, 50)])
        break
    return CompletionOut(percent=percent, done=done, next=nxt)

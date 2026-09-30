# [IMP-B, 2026-09-28] Tiered service packages on listings (FR01/FR04/FR22).
#
# A provider prices their work as up to three tiers (basic / standard /
# premium — the Fiverr / Upwork project-catalog shape) with delivery time,
# revisions and what is included. A viewer "requests this package", which
# is an ordinary enquiry (every existing rule applies: profile required,
# daily cap, one open thread per target, blocks, idempotency) tagged with
# sub_choice = 'request_package' and the package id, so the provider's
# inbox shows exactly which offer was asked for.
#
# Text is stored as given (the provider's own language) with optional
# Hindi/Telugu variants; the read picks the viewer's language when present
# and falls back to the original — no machine translation is pretended.
# Traces to: FR01, FR04, FR22, TR001, TR022
from __future__ import annotations

from typing import Literal

import asyncpg
from pydantic import BaseModel, Field

from app.errors import ApiError
from app.i18n import translate
from app.identity import AuthzContext
from app.services import enquiries as enquiries_svc
from app.services import profession_rules

Tier = Literal["basic", "standard", "premium"]
TIER_ORDER = {"basic": 0, "standard": 1, "premium": 2}
MAX_TIERS = 3


class PackageIn(BaseModel):
    tier: Tier
    name: str = Field(min_length=1, max_length=80)
    name_hi: str | None = Field(default=None, max_length=80)
    name_te: str | None = Field(default=None, max_length=80)
    description: str | None = Field(default=None, max_length=600)
    description_hi: str | None = Field(default=None, max_length=600)
    description_te: str | None = Field(default=None, max_length=600)
    price_paise: int = Field(ge=0)
    delivery_days: int | None = Field(default=None, ge=0, le=365)
    revisions: int | None = Field(default=None, ge=0, le=99)
    includes: list[str] = Field(default_factory=list, max_length=12)
    sort: int | None = None


class PackagesUpsertIn(BaseModel):
    packages: list[PackageIn] = Field(max_length=MAX_TIERS)


class PackageOut(BaseModel):
    id: str
    listing_id: str
    tier: Tier
    tier_label: str
    name: str
    description: str | None
    price_paise: int
    price_label: str
    delivery_days: int | None
    revisions: int | None
    includes: list[str]
    sort: int
    # The stored originals plus the two optional variants, for the owner's editor.
    name_hi: str | None = None
    name_te: str | None = None
    description_hi: str | None = None
    description_te: str | None = None


class PackageRequestIn(BaseModel):
    message: str = Field(min_length=20, max_length=1000)
    attachment_url: str | None = None


class PackageRequestOut(BaseModel):
    enquiry: enquiries_svc.EnquiryOut
    package: PackageOut


def _rupees(paise: int) -> str:
    rupees, rest = divmod(int(paise), 100)
    # Indian digit grouping: 12,34,567
    s = str(rupees)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts + [tail])
    return f"₹{s}" if rest == 0 else f"₹{s}.{rest:02d}"


def _row_to_out(row: asyncpg.Record, lang: str) -> PackageOut:
    name = row["name"]
    description = row["description"]
    if lang in ("hi", "te"):
        name = row[f"name_{lang}"] or name
        description = row[f"description_{lang}"] or description
    return PackageOut(
        id=str(row["id"]), listing_id=str(row["listing_id"]), tier=row["tier"],
        tier_label=translate(f"listings.packageTier.{row['tier']}", lang),
        name=name, description=description, price_paise=int(row["price_paise"]), price_label=_rupees(row["price_paise"]),
        delivery_days=row["delivery_days"], revisions=row["revisions"], includes=list(row["includes"] or []), sort=row["sort"],
        name_hi=row["name_hi"], name_te=row["name_te"], description_hi=row["description_hi"], description_te=row["description_te"],
    )


async def list_listing_packages(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, listing_id: str) -> list[PackageOut]:
    try:
        rows = await conn.fetch(
            "SELECT * FROM vyapar_listings.listing_packages WHERE listing_id = $1 ORDER BY sort, tier", listing_id
        )
    except asyncpg.DataError:
        raise ApiError(404, "common.error.listingNotFound", lang)
    rows = sorted(rows, key=lambda r: (r["sort"], TIER_ORDER[r["tier"]]))
    if rows and not await _prices_public(conn, ctx, listing_id):
        return []  # [Trust pack] a council that forbids advertised fees (advocates, architects)
    return [_row_to_out(r, lang) for r in rows]


async def _prices_public(conn: asyncpg.Connection, ctx: AuthzContext, listing_id: str) -> bool:
    """False when this viewer may not see prices on this profile: the owner
    always may; others not when the profile's profession rule forbids public
    prices and discounts."""
    row = await conn.fetchrow("SELECT owner_id, categories, capabilities FROM vyapar_listings.listings WHERE id = $1", listing_id)
    if row is None or row["owner_id"] == ctx.member_id:
        return True
    return profession_rules.verdict_for_row(row).allow_public_prices


async def _owned_listing(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, listing_id: str) -> asyncpg.Record:
    try:
        row = await conn.fetchrow("SELECT id, owner_id, name, state FROM vyapar_listings.listings WHERE id = $1", listing_id)
    except asyncpg.DataError:
        row = None
    if row is None or row["owner_id"] != ctx.member_id:
        raise ApiError(404, "common.error.listingNotFound", lang)
    return row


async def upsert_listing_packages(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, listing_id: str, body: PackagesUpsertIn) -> list[PackageOut]:
    """Insert-or-update by tier. Tiers not in the body are left as they are
    (delete one explicitly with deleteListingPackage)."""
    owned = await _owned_listing(conn, ctx, lang, listing_id)
    if not (await profession_rules.verdict_for_listing(conn, owned["id"])).allow_public_prices:
        raise ApiError(403, "listings.error.packagesNotPermittedForProfession", lang, error_code="packages_not_permitted_for_profession")
    # [Trust pack — scam shield, "offer" tier] a priced service is fine; a
    # charge for getting a JOB ("placement fee", "pay and get a job") is not.
    from app.services import scam_shield

    await scam_shield.guard(
        ctx.member_id,
        {f"packages[{i}].{name}": value for i, p in enumerate(body.packages)
         for name, value in (("name", p.name), ("description", p.description), ("description_hi", p.description_hi),
                             ("description_te", p.description_te), ("includes", " ".join(p.includes)))},
        lang, tier="offer", surface="package", object_kind="listing", object_id=listing_id,
    )
    tiers = [p.tier for p in body.packages]
    if len(set(tiers)) != len(tiers):
        raise ApiError(422, "listings.error.duplicatePackageTier", lang)
    existing = await conn.fetch("SELECT tier FROM vyapar_listings.listing_packages WHERE listing_id = $1", listing_id)
    if len({r["tier"] for r in existing} | set(tiers)) > MAX_TIERS:
        raise ApiError(422, "listings.error.tooManyPackages", lang, max=MAX_TIERS)
    for p in body.packages:
        await conn.execute(
            """INSERT INTO vyapar_listings.listing_packages
                 (listing_id, tier, name, name_hi, name_te, description, description_hi, description_te,
                  price_paise, delivery_days, revisions, includes, sort)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
               ON CONFLICT (listing_id, tier) DO UPDATE SET
                 name = EXCLUDED.name, name_hi = EXCLUDED.name_hi, name_te = EXCLUDED.name_te,
                 description = EXCLUDED.description, description_hi = EXCLUDED.description_hi, description_te = EXCLUDED.description_te,
                 price_paise = EXCLUDED.price_paise, delivery_days = EXCLUDED.delivery_days, revisions = EXCLUDED.revisions,
                 includes = EXCLUDED.includes, sort = EXCLUDED.sort, updated_at = now()""",
            listing_id, p.tier, p.name, p.name_hi, p.name_te, p.description, p.description_hi, p.description_te,
            p.price_paise, p.delivery_days, p.revisions, [s.strip() for s in p.includes if s.strip()],
            p.sort if p.sort is not None else TIER_ORDER[p.tier],
        )
    return await list_listing_packages(conn, ctx, lang, listing_id)


async def delete_listing_package(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, listing_id: str, package_id: str) -> list[PackageOut]:
    await _owned_listing(conn, ctx, lang, listing_id)
    try:
        status = await conn.execute(
            "DELETE FROM vyapar_listings.listing_packages WHERE id = $1 AND listing_id = $2", package_id, listing_id
        )
    except asyncpg.DataError:
        raise ApiError(404, "listings.error.packageNotFound", lang)
    if status.split()[-1] == "0":
        raise ApiError(404, "listings.error.packageNotFound", lang)
    return await list_listing_packages(conn, ctx, lang, listing_id)


async def request_listing_package(
    conn: asyncpg.Connection, ctx: AuthzContext, lang: str, listing_id: str, package_id: str,
    body: PackageRequestIn, idempotency_key: str | None = None,
) -> PackageRequestOut:
    """Creates the enquiry through the enquiries service — the one place the
    enquiry rules live — then tags it with the package."""
    try:
        pkg = await conn.fetchrow(
            "SELECT * FROM vyapar_listings.listing_packages WHERE id = $1 AND listing_id = $2", package_id, listing_id
        )
    except asyncpg.DataError:
        pkg = None
    if pkg is None or not await _prices_public(conn, ctx, listing_id):
        raise ApiError(404, "listings.error.packageNotFound", lang)
    package = _row_to_out(pkg, lang)
    enquiry = await enquiries_svc.create_enquiry(
        conn, ctx, lang,
        body=enquiries_svc.EnquiryCreate(listing_id=listing_id, message=body.message, attachment_url=body.attachment_url, sub_choice="request_package"),
        idempotency_key=idempotency_key,
    )
    await conn.execute(
        "UPDATE vyapar_enquiries.enquiries SET package_id = $2 WHERE id = $1 AND sender_id = $3 AND package_id IS NULL",
        enquiry.id, package_id, ctx.member_id,
    )
    # A system note in the thread names the offer for both sides (the provider
    # reads it in the language the request was written in, like any message).
    note = translate("listings.packageRequestNote", lang, tier=package.tier_label, name=package.name, price=package.price_label)
    await conn.execute(
        """INSERT INTO vyapar_enquiries.enquiry_messages (enquiry_id, sender_id, body, content_language, system_note)
           SELECT $1, $2, $3, $4, true
            WHERE NOT EXISTS (SELECT 1 FROM vyapar_enquiries.enquiry_messages m WHERE m.enquiry_id = $1 AND m.system_note AND m.body = $3)""",
        enquiry.id, ctx.member_id, note, lang,
    )
    return PackageRequestOut(enquiry=enquiry, package=package)

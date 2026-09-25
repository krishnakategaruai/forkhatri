# [TR044] Progressive first-run to Discover (FR44). Five screens, server-
# verified via members.first_run_step/first_run_done — none of them is a
# sign-up/login/OTP-sign-in screen (a structural absence: neither this
# service nor its router defines any credential-related operation at all), directly honouring the product
# owner's standing correction that authentication belongs to the parent
# platform alone.
# Approach: GET returns the member's current step so the frontend can
# resume mid-flow after a refresh; POST /step is idempotent per step
# (repeating the same step number just re-saves that step's fields, never
# double-advances). Location-permission-denied falls back to a manual
# `locality` text field on the same call, per TR044's own text.
# [Original-Vyapar upgrade, 2026-09-17, product-owner-approved] FR44's own
# acceptance criteria names "capture capabilities via structured choices
# plus free text, capture location/radius and work mode" as required
# first-run steps — genuinely missing before this change (not merely
# "plainer" than a reference app; `members.capabilities`/`radius_km`/
# `work_mode` existed on the table since migration 001 but the first-run
# flow never read or wrote any of them). Added here; `capabilities_other`
# (migration 012) is the "plus free text" half of that same criterion.
# Traces to: FR44, TR044, SP044
from __future__ import annotations

from typing import Literal

import asyncpg
from pydantic import BaseModel

from app.taxonomy_cache import labels_for


TOTAL_STEPS = 5


class FirstRunState(BaseModel):
    step: int
    done: bool
    display_name: str
    language: str
    locality: str | None
    lat: float | None
    lng: float | None
    radius_km: int
    work_mode: str | None
    capabilities: list[str]
    capabilities_other: str | None
    help_with: list[str]


class FirstRunStepInput(BaseModel):
    step: int
    display_name: str | None = None
    language: Literal["en", "hi", "te"] | None = None
    locality: str | None = None
    lat: float | None = None
    lng: float | None = None
    radius_km: int | None = None
    work_mode: Literal["on_site", "remote", "both"] | None = None
    capabilities: list[str] | None = None
    capabilities_other: str | None = None
    help_with: list[str] | None = None


class TaxonomyOptionOut(BaseModel):
    slug: str
    label: str


class CategoryOptionOut(BaseModel):
    slug: str
    label: str
    description: str


def _row_to_state(row: asyncpg.Record) -> FirstRunState:
    return FirstRunState(
        step=row["first_run_step"], done=row["first_run_done"], display_name=row["display_name"],
        language=row["language"], locality=row["locality"], lat=row["lat"], lng=row["lng"],
        radius_km=row["radius_km"], work_mode=row["work_mode"], capabilities=list(row["capabilities"]),
        capabilities_other=row["capabilities_other"], help_with=list(row["help_with"]),
    )


async def get_first_run_state(
    conn: asyncpg.Connection,
) -> FirstRunState:
    row = await conn.fetchrow(
        """SELECT first_run_step, first_run_done, display_name, language, locality, lat, lng,
                  radius_km, work_mode, capabilities, capabilities_other, help_with
           FROM vyapar_identity.members WHERE id = current_setting('vyapar.authz_context', true)"""
    )
    return _row_to_state(row)


async def list_capability_options(
    conn: asyncpg.Connection,
    lang: str,
) -> list[TaxonomyOptionOut]:
    """[FR44 "structured choices" half] the same active capability terms
    every listing already picks from — one shared taxonomy, never a
    second, first-run-only list that could drift out of sync.
    [Real bug found live, fixed here] this hardcoded `labels_for(slugs,
    "en")` — every other taxonomy-label call site in the codebase already
    threads the caller's own language through; this one never did, so
    category/skill names stayed in English even with Hindi/Telugu picked
    everywhere else on the same screen."""
    rows = await conn.fetch("SELECT slug FROM vyapar_listings.taxonomy_terms WHERE kind = 'capability' AND status = 'active' ORDER BY slug")
    slugs = [r["slug"] for r in rows]
    labels = labels_for(slugs, lang)
    return [TaxonomyOptionOut(slug=s, label=l) for s, l in zip(slugs, labels)]


# [Original-Vyapar upgrade, 2026-09-17, product-owner-reaffirmed: "I
# genuinely feel above things also should be available" — a direct
# reaffirmation of the WorkIndia-onboarding research, built as an original
# Vyapar screen, never their layout/chrome] a real DB parent-child link
# between category and capability taxonomy terms doesn't exist (checked
# directly — every capability row's `parent_id` is null), so "scoped
# suggestions per category" needs an explicit mapping; this is that
# mapping, editorially curated once here rather than guessed per-request.
# Categories/capabilities not listed here simply fall back to the full
# unscoped list — never a missing/broken suggestion set.
CATEGORY_CAPABILITY_SCOPE: dict[str, list[str]] = {
    "accounting_tax": ["accounting", "tax", "gst_filing"],
    "automotive": ["car_repair"],
    "design_architecture": ["architecture", "interior_design"],
    "education": ["tutoring", "mathematics", "yoga"],
    "events": ["events", "catering"],
    "food_catering": ["catering", "bakery", "cakes"],
    "handicraft": ["handicraft", "tailoring", "textiles"],
    "health_wellness": ["yoga"],
    "home_repair": ["plumbing", "electrical", "car_repair"],
    "legal": ["legal", "property_law", "gst_filing"],
    "logistics": ["delivery", "wholesale"],
    "marketing": ["social_media", "sales", "content_writing"],
    "media_photo": ["photography", "video_editing", "content_writing"],
    "printing": ["printing"],
    "software_it": ["software", "python", "react", "product_management", "startup"],
    "textiles_retail": ["textiles", "tailoring", "wholesale"],
}

# [Same upgrade] taxonomy_terms has no `description` column (checked
# directly) — a short, honest one-line description per category, written
# once here for each of the 3 launch languages, matching the same
# translated-content standard as every taxonomy display name already gets.
CATEGORY_DESCRIPTIONS: dict[str, dict[str, str]] = {
    "en": {
        "accounting_tax": "Bookkeeping, tax filing, GST and audit help",
        "automotive": "Vehicle repair, servicing and parts",
        "design_architecture": "Architecture, interiors and design services",
        "education": "Tutoring, coaching and skill classes",
        "events": "Event planning, decor and management",
        "food_catering": "Catering, baking and food service",
        "handicraft": "Handmade goods, tailoring and textiles work",
        "health_wellness": "Fitness, yoga and wellness services",
        "home_repair": "Plumbing, electrical and home maintenance",
        "legal": "Legal advice, documentation and compliance",
        "logistics": "Delivery, transport and wholesale supply",
        "marketing": "Marketing, social media and sales support",
        "media_photo": "Photography, video and content creation",
        "printing": "Printing and signage services",
        "software_it": "Software, IT and technology services",
        "textiles_retail": "Textiles, garments and retail",
    },
    "hi": {
        "accounting_tax": "बहीखाता, टैक्स फाइलिंग, GST और ऑडिट सहायता",
        "automotive": "वाहन मरम्मत, सर्विसिंग और पार्ट्स",
        "design_architecture": "आर्किटेक्चर, इंटीरियर और डिज़ाइन सेवाएँ",
        "education": "ट्यूशन, कोचिंग और स्किल क्लासेज़",
        "events": "इवेंट योजना, सजावट और प्रबंधन",
        "food_catering": "कैटरिंग, बेकिंग और फूड सेवा",
        "handicraft": "हस्तनिर्मित सामान, दर्ज़ी और कपड़ा काम",
        "health_wellness": "फिटनेस, योग और वेलनेस सेवाएँ",
        "home_repair": "प्लंबिंग, इलेक्ट्रिकल और घर की मरम्मत",
        "legal": "कानूनी सलाह, दस्तावेज़ीकरण और अनुपालन",
        "logistics": "डिलीवरी, परिवहन और थोक आपूर्ति",
        "marketing": "मार्केटिंग, सोशल मीडिया और सेल्स सहायता",
        "media_photo": "फोटोग्राफी, वीडियो और कंटेंट निर्माण",
        "printing": "प्रिंटिंग और साइनेज सेवाएँ",
        "software_it": "सॉफ़्टवेयर, IT और टेक्नोलॉजी सेवाएँ",
        "textiles_retail": "कपड़े, परिधान और रिटेल",
    },
    "te": {
        "accounting_tax": "బుక్కీపింగ్, టాక్స్ ఫైలింగ్, GST మరియు ఆడిట్ సహాయం",
        "automotive": "వాహన మరమ్మత్తు, సర్వీసింగ్ మరియు పార్ట్స్",
        "design_architecture": "ఆర్కిటెక్చర్, ఇంటీరియర్స్ మరియు డిజైన్ సేవలు",
        "education": "ట్యూషన్, కోచింగ్ మరియు స్కిల్ క్లాసులు",
        "events": "ఈవెంట్ ప్లానింగ్, డెకర్ మరియు మేనేజ్‌మెంట్",
        "food_catering": "క్యాటరింగ్, బేకింగ్ మరియు ఫుడ్ సర్వీస్",
        "handicraft": "హస్తనిర్మిత వస్తువులు, టైలరింగ్ మరియు టెక్స్‌టైల్స్ పని",
        "health_wellness": "ఫిట్‌నెస్, యోగా మరియు వెల్‌నెస్ సేవలు",
        "home_repair": "ప్లంబింగ్, ఎలక్ట్రికల్ మరియు హోమ్ మెయింటెనెన్స్",
        "legal": "న్యాయ సలహా, డాక్యుమెంటేషన్ మరియు కంప్లయన్స్",
        "logistics": "డెలివరీ, రవాణా మరియు హోల్‌సేల్ సరఫరా",
        "marketing": "మార్కెటింగ్, సోషల్ మీడియా మరియు సేల్స్ సహాయం",
        "media_photo": "ఫోటోగ్రఫీ, వీడియో మరియు కంటెంట్ క్రియేషన్",
        "printing": "ప్రింటింగ్ మరియు సైనేజ్ సేవలు",
        "software_it": "సాఫ్ట్‌వేర్, IT మరియు టెక్నాలజీ సేవలు",
        "textiles_retail": "టెక్స్‌టైల్స్, గార్మెంట్స్ మరియు రిటైల్",
    },
}


async def list_category_options(
    conn: asyncpg.Connection,
    lang: str,
) -> list[CategoryOptionOut]:
    """[Same upgrade] categories the member can tap during first-run,
    each with a short description — phase 1 of the two-phase capability
    capture (category, then scoped skills)."""
    rows = await conn.fetch("SELECT slug FROM vyapar_listings.taxonomy_terms WHERE kind = 'category' AND status = 'active' ORDER BY slug")
    slugs = [r["slug"] for r in rows]
    labels = labels_for(slugs, lang)
    descriptions = CATEGORY_DESCRIPTIONS.get(lang, CATEGORY_DESCRIPTIONS["en"])
    return [CategoryOptionOut(slug=s, label=l, description=descriptions.get(s, l)) for s, l in zip(slugs, labels)]


async def list_scoped_capability_options(
    conn: asyncpg.Connection,
    lang: str,
    categories: str = "",
) -> list[TaxonomyOptionOut]:
    """[Same upgrade] phase 2 of the two-phase capture — capability
    suggestions scoped to whichever categories were picked in phase 1.
    Falls back to the full list if no category maps to anything (never an
    empty, dead-end suggestion set)."""
    picked = [c for c in categories.split(",") if c]
    scoped_slugs: list[str] = []
    for c in picked:
        for s in CATEGORY_CAPABILITY_SCOPE.get(c, []):
            if s not in scoped_slugs:
                scoped_slugs.append(s)
    rows = await conn.fetch("SELECT slug FROM vyapar_listings.taxonomy_terms WHERE kind = 'capability' AND status = 'active' ORDER BY slug")
    all_slugs = [r["slug"] for r in rows]
    slugs = [s for s in scoped_slugs if s in all_slugs] or all_slugs
    labels = labels_for(slugs, lang)
    return [TaxonomyOptionOut(slug=s, label=l) for s, l in zip(slugs, labels)]


async def save_first_run_step(
    conn: asyncpg.Connection,
    body: FirstRunStepInput,
) -> FirstRunState:
    # Idempotent: only ever moves first_run_step forward (GREATEST), a
    # repeat POST of an earlier step never regresses progress.
    done = body.step >= TOTAL_STEPS
    # [Real bug found live, fixed here] the query text never referenced
    # `$1` at all (the first positional param was a duplicate of `$2`,
    # `body.step`, left over from an earlier draft) — asyncpg's prepare
    # step requires every bound parameter to be inferable from where it's
    # actually used in the SQL text, and a completely unreferenced $1
    # fails with `IndeterminateDatatypeError` rather than being silently
    # ignored. Removed the stray duplicate positional argument.
    row = await conn.fetchrow(
        """UPDATE vyapar_identity.members SET
             first_run_step = GREATEST(first_run_step, $1),
             first_run_done = first_run_done OR $2,
             display_name = COALESCE($3, display_name),
             language = COALESCE($4, language),
             locality = COALESCE($5, locality),
             lat = COALESCE($6, lat),
             lng = COALESCE($7, lng),
             radius_km = COALESCE($8::smallint, radius_km),
             work_mode = COALESCE($9::text, work_mode),
             capabilities = COALESCE($10::text[], capabilities),
             capabilities_other = COALESCE($11::text, capabilities_other),
             help_with = COALESCE($12::text[], help_with),
             updated_at = now()
           WHERE id = current_setting('vyapar.authz_context', true)
           RETURNING first_run_step, first_run_done, display_name, language, locality, lat, lng,
                     radius_km, work_mode, capabilities, capabilities_other, help_with""",
        body.step,
        done,
        body.display_name,
        body.language,
        body.locality,
        body.lat,
        body.lng,
        body.radius_km,
        body.work_mode,
        body.capabilities,
        body.capabilities_other,
        body.help_with,
    )
    return _row_to_state(row)

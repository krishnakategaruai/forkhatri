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

from datetime import date, datetime, timedelta, timezone
from typing import Literal

import asyncpg
from pydantic import BaseModel, Field

from app.errors import ApiError
from app.identity import AuthzContext
from app.taxonomy_cache import categories as taxonomy_categories, children_of, description_for, labels_for, term_for


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
    # [Start flow 2026-10, decision 1] the 3-question start is shown once, and
    # never to a member who already has a trade or a post. `needs_start` is
    # the one flag a client reads; the rest explain it.
    needs_start: bool = False
    goal: str | None = None
    has_trade: bool = False
    has_post: bool = False
    date_of_birth_known: bool = False
    eligible: bool = True  # 18 and over, or not yet asked


class FirstRunStepInput(BaseModel):
    step: int
    display_name: str | None = None
    language: Literal["en", "hi", "te", "mr", "kn"] | None = None
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


def _col(row: asyncpg.Record, name: str):
    try:
        return row[name]
    except (KeyError, IndexError):
        return None


def _age(dob: date | None, today: date | None = None) -> int | None:
    if dob is None:
        return None
    today = today or (datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)).date()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _row_to_state(row: asyncpg.Record, *, has_trade: bool = False, has_post: bool = False) -> FirstRunState:
    dob = _col(row, "date_of_birth")
    age = _age(dob)
    help_with = list(row["help_with"])
    return FirstRunState(
        step=row["first_run_step"], done=row["first_run_done"], display_name=row["display_name"],
        language=row["language"], locality=row["locality"], lat=row["lat"], lng=row["lng"],
        radius_km=row["radius_km"], work_mode=row["work_mode"], capabilities=list(row["capabilities"]),
        capabilities_other=row["capabilities_other"], help_with=help_with,
        needs_start=not row["first_run_done"] and not has_trade and not has_post,
        goal=next((g for g in help_with if g in GOALS), None),
        has_trade=has_trade, has_post=has_post,
        date_of_birth_known=dob is not None, eligible=age is None or age >= MIN_AGE,
    )


async def _trade_and_post(conn: asyncpg.Connection, member_id: str) -> tuple[bool, bool]:
    """Decision 1: a member with a trade (skills on the member row or on
    their one profile) or a post of their own is never shown the start."""
    row = await conn.fetchrow(
        """SELECT (cardinality(m.capabilities) > 0
                   OR EXISTS (SELECT 1 FROM vyapar_listings.listings l
                               WHERE l.owner_id = m.id AND l.state <> 'archived'
                                 AND (cardinality(l.capabilities) > 0 OR cardinality(l.categories) > 0 OR l.business_name IS NOT NULL))) AS has_trade,
                  EXISTS (SELECT 1 FROM vyapar_opportunities.opportunities o WHERE o.poster_id = m.id) AS has_post
             FROM vyapar_identity.members m WHERE m.id = $1""",
        member_id,
    )
    if row is None:
        return False, False
    return bool(row["has_trade"]), bool(row["has_post"])


async def get_first_run_state(
    conn: asyncpg.Connection,
) -> FirstRunState:
    row = await conn.fetchrow(
        """SELECT id, first_run_step, first_run_done, display_name, language, locality, lat, lng,
                  radius_km, work_mode, capabilities, capabilities_other, help_with, date_of_birth
           FROM vyapar_identity.members WHERE id = current_setting('vyapar.authz_context', true)"""
    )
    has_trade, has_post = await _trade_and_post(conn, row["id"])
    if not row["first_run_done"] and (has_trade or has_post):
        # [Decision 1] a member who already has a trade or a post is never sent
        # to the start again (the audit's Mohan saw step 1 after a live post).
        row = await conn.fetchrow(
            """UPDATE vyapar_identity.members SET first_run_done = true, first_run_step = GREATEST(first_run_step, $2), updated_at = now()
                WHERE id = $1
            RETURNING id, first_run_step, first_run_done, display_name, language, locality, lat, lng,
                      radius_km, work_mode, capabilities, capabilities_other, help_with, date_of_birth""",
            row["id"], TOTAL_STEPS,
        )
    return _row_to_state(row, has_trade=has_trade, has_post=has_post)


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
# Vyapar screen, never their layout/chrome] scoped skill suggestions per
# category. Until migration 018 no capability row had a `parent_id`, so this
# file carried a hard-coded category -> skills map and a hard-coded
# description per category in three languages. [Backend A, 2026-09-28] Both
# now come from the taxonomy tree itself (`taxonomy_terms.parent_id` and
# `description_*`, served by the shared in-process cache), so an operator
# adding a role under a category is enough — nothing to edit here.
# Categories with no children fall back to the full unscoped list — never a
# missing/broken suggestion set.


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
    return [
        CategoryOptionOut(slug=s, label=l, description=description_for("category", s, lang) or l)
        for s, l in zip(slugs, labels)
    ]


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
        for s in children_of(c):
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


# ===========================================================================
# [Start flow 2026-10 — ONBOARDING-REDESIGN-2026-10.md, decisions 1–12]
# The 3-question start: goal, trade(s) or need, area. One call saves it all
# and leaves the member on results. Name, language and phone are never asked
# (they come from the identity); radius and work mode are defaulted from the
# trade and changed later in filters or the profile.
# ===========================================================================

MIN_AGE = 18
GOALS = ("find_work", "hire", "get_customers")
Goal = Literal["find_work", "hire", "get_customers"]

# Decision 6: plain defaults instead of a question. Trades people go out to
# do, and shops/home sellers customers come to, are "in person" (on_site);
# desk professions can work either way.
_IN_PERSON_CATEGORIES = frozenset({
    "home_repair", "logistics", "hospitality_housekeeping", "manufacturing_labour", "automotive", "events",
    "beauty_personal_care", "textiles_retail", "food_catering", "handicraft", "printing", "health_wellness", "healthcare",
})

# Decision 5: the picture tiles. Curated, ordered, filtered to what the
# taxonomy actually holds, so a renamed or retired slug never shows a dead tile.
TRADE_TILES: dict[str, tuple[str, ...]] = {
    "find_work": (
        "plumbing", "electrical", "carpenter", "painter", "mason", "delivery", "driver", "cook",
        "maid", "security_guard", "tailoring", "beautician", "ac_technician", "mechanic", "shop_helper", "borewell_motor",
        "data_entry", "telecaller", "tile_fitter", "welder", "gardener", "packer", "nurse", "teacher",
    ),
    "get_customers": (
        "kirana_store", "home_food", "tailoring", "beautician", "bakery", "catering", "plumbing", "electrical",
        "car_repair", "photography", "tutoring", "accountant", "printing", "interior_design", "textiles", "handicraft",
        "yoga", "legal", "digital_marketer", "software",
    ),
}
TILES_FIRST = 8


class TradeTileOut(BaseModel):
    slug: str
    label: str
    category: str | None


class StartInput(BaseModel):
    goal: Goal
    capabilities: list[str] = Field(default_factory=list, description="Taxonomy slugs the member tapped")
    capabilities_other: list[str] = Field(default_factory=list, description="Trades typed or spoken as written")
    locality: str | None = None
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    date_of_birth: date | None = Field(default=None, description="Asked only when the identity does not know it")
    business_name: str | None = Field(default=None, max_length=120, description="Optional; suggested from the name and trade when empty")
    # Voice can learn these in the same conversation (decision 7); saved, never re-asked.
    experience_years: int | None = Field(default=None, ge=0, le=60)
    own_assets: list[Literal["two_wheeler", "four_wheeler", "driving_licence", "smartphone", "laptop", "own_tools"]] | None = None
    headline: str | None = Field(default=None, max_length=200)


class StartOut(BaseModel):
    state: FirstRunState
    eligible: bool
    profile_id: str | None = None
    live: bool = False
    publish_blocked: str | None = None
    next: Literal["discover", "post", "visible", "under_18"]


def _category_of(slug: str) -> str | None:
    term = term_for("capability", slug)
    return term.parent_slug if term else None


def default_work_mode(goal: str, slugs: list[str]) -> str:
    cats = {c for c in (_category_of(s) for s in slugs) if c}
    if goal == "get_customers":
        return "both" if cats and not (cats & _IN_PERSON_CATEGORIES) else "on_site"
    if not cats:
        return "on_site" if goal == "find_work" else "both"
    return "on_site" if cats & _IN_PERSON_CATEGORIES else "both"


def list_trade_tiles(goal: str, lang: str) -> list[TradeTileOut]:
    slugs = [s for s in TRADE_TILES.get(goal, TRADE_TILES["find_work"]) if term_for("capability", s) is not None]
    labels = labels_for(slugs, lang)
    return [TradeTileOut(slug=s, label=l, category=_category_of(s)) for s, l in zip(slugs, labels)]


def _suggested_business_name(display_name: str, trade_label: str | None, lang: str) -> str:
    from app.i18n import translate

    first = (display_name or "").split(" ")[0]
    if trade_label:
        return translate("listings.start.businessNameSuggested", lang, name=first, trade=trade_label)
    return translate("listings.start.businessNameFallback", lang, name=first)


async def start(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, body: StartInput) -> StartOut:
    """One call for the whole start. Idempotent: calling it again re-saves
    the same answers and never creates a second profile."""
    from app.services import profile as profile_svc

    member = await conn.fetchrow(
        "SELECT id, display_name, phone, locality, lat, lng, date_of_birth, capabilities FROM vyapar_identity.members WHERE id = $1",
        ctx.member_id,
    )
    if member is None:
        raise ApiError(404, "common.error.listingNotFound", lang)

    # Age: asked once when the identity does not know it; under 18 is a kind
    # explanation on the client, recorded here so it is not asked again.
    dob = body.date_of_birth or member["date_of_birth"]
    if dob is None:
        raise ApiError(422, "listings.error.dateOfBirthRequired", lang, error_code="date_of_birth_required")
    if body.date_of_birth is not None and member["date_of_birth"] is None:
        await conn.execute("UPDATE vyapar_identity.members SET date_of_birth = $2, updated_at = now() WHERE id = $1", ctx.member_id, body.date_of_birth)
    if (_age(dob) or 0) < MIN_AGE:
        state = await get_first_run_state(conn)
        return StartOut(state=state, eligible=False, next="under_18")

    slugs = [s for s in dict.fromkeys(body.capabilities) if term_for("capability", s) is not None]
    other = [t.strip() for t in body.capabilities_other if t and t.strip()][:10]
    work_mode = default_work_mode(body.goal, slugs)
    locality = (body.locality or "").strip() or None
    if locality:
        locality = await profile_svc._known_locality(conn, locality)

    # The member row: goal, trades, area, defaults, and the start marked done.
    await conn.execute(
        """UPDATE vyapar_identity.members SET
             help_with = $2::text[],
             capabilities = CASE WHEN cardinality($3::text[]) > 0 THEN $3::text[] ELSE capabilities END,
             capabilities_other = COALESCE($4::text, capabilities_other),
             locality = COALESCE($5::text, locality),
             lat = COALESCE($6::double precision, lat),
             lng = COALESCE($7::double precision, lng),
             work_mode = COALESCE(work_mode, $8::text),
             first_run_step = GREATEST(first_run_step, $9),
             first_run_done = true,
             updated_at = now()
           WHERE id = $1""",
        ctx.member_id, [body.goal], slugs, ", ".join(other) if other else None, locality, body.lat, body.lng, work_mode, TOTAL_STEPS,
    )

    profile_id: str | None = None
    live = False
    blocked: str | None = None
    row = await profile_svc.ensure_profile(conn, ctx, lang, locality=locality, lat=body.lat, lng=body.lng)
    if row is not None:
        profile_id = str(row["id"])
        caps = list(dict.fromkeys([*slugs, *other])) or None
        patch: dict = {}
        if caps:
            existing = list(row["capabilities"] or [])
            patch["capabilities"] = list(dict.fromkeys([*existing, *caps]))[:15]
        if row["service_mode"] in (None, "both") and work_mode != "both":
            patch["service_mode"] = work_mode
        if body.experience_years is not None:
            patch["experience_years"] = body.experience_years
        if body.own_assets is not None:
            patch["own_assets"] = body.own_assets
        if body.headline:
            patch["headline"] = body.headline.strip()
        if body.lat is not None and body.lng is not None and row["lat"] is None:
            patch["lat"], patch["lng"] = body.lat, body.lng
        if body.goal == "get_customers" and not _col(row, "business_name"):
            trade_label = labels_for(slugs[:1], lang)[0] if slugs else (other[0] if other else None)
            name = (body.business_name or "").strip() or _suggested_business_name(member["display_name"], trade_label, lang)
            patch["business"] = {"name": name[:120]}
        # Decision 8: saving makes you live as "New on Vyapar" when the server
        # rules allow (terms accepted on screen 1, host-verified phone).
        patch["publish"] = body.goal in ("find_work", "get_customers")
        out = await profile_svc.update_my_profile(conn, ctx, lang, profile_svc.ProfilePatch(**patch))
        blocked = out.publish_blocked
        live = bool(out.profile and out.profile.state in ("active_unverified", "active_verified"))

    state = await get_first_run_state(conn)
    nxt: Literal["discover", "post", "visible"] = "post" if body.goal == "hire" else ("visible" if body.goal == "get_customers" else "discover")
    return StartOut(state=state, eligible=True, profile_id=profile_id, live=live, publish_blocked=blocked, next=nxt)

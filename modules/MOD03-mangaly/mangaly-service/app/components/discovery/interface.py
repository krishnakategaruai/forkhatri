"""Discovery — public interface.

`/MODULE-ARCHITECTURE-STANDARD.md` §3: this is the only way other components
reach Discovery state.

Implements:
  * FR021 / TR021 — searchable is independent of any viewer's own visibility.
  * FR026 / TR026 — DEC-V1-002's fixed, versioned ranking weights.
  * FR027 / TR027 — the discoverability gate is `profile.is_discoverable()`,
    never re-derived here (the TR003/TR027 non-divergence contract).
  * Rework contract §3/§6 (2026-09-17) — biodata filters (height, gotra,
    sub-community, profession, income band, mother tongue, manglik), free
    text `q` over the tsvector, `sort`, `total`; and BROWSE MODE: a caller
    with no own profile and no `for_candidate` may search by passing
    `looking_for` explicitly. Blocked people (either direction) are excluded.

Filtering is SQL over the index's own columns (migration 031); the ranking
formula and its diversity re-rank stay in Python for the page.

Interim, deliberate deviation from this package's own header comment
("synced via domain events — never a live cross-schema query"): TR069's
outbox dispatcher does not exist yet, so `refresh_index()` is called
SYNCHRONOUSLY from `profile.interface`'s own create/update functions, in the
same transaction. When the dispatcher is built the call site moves; this
function does not change.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.compatibility import interface as compatibility
from app.components.discovery.models import DiscoveryProfileIndex
from app.components.profile.models import FieldState, Profile
from app.config.matching_engine import NEARBY_REASON_KM
from app.config.profile_schema import FACT_SOURCES
from app.config.ranking_weights import (
    DAILY_PICK_MAX_AGE_DAYS,
    MAX_SAME_BRACKET_RUN,
    SCORE_BRACKETS,
)

__all__ = [
    "DailyPick",
    "DiscoverFilters",
    "DiscoveryCard",
    "LookingForMissing",
    "SearchPage",
    "SearchResult",
    "Snippet",
    "authorize_family_viewer",
    "cards_for",
    "daily_picks_for",
    "get_snapshot",
    "get_snippet",
    "reciprocal_reasons",
    "reciprocity",
    "refresh_index",
    "search",
    "shelves",
]


@dataclass(frozen=True, slots=True)
class Snippet:
    """Same deliberately-limited shape as `SearchResult` (no name/photo —
    see its own docstring), for exactly one account rather than a ranked
    list. `None` is "nothing to show", not an error."""

    locality: str | None
    education_level: str | None
    profession: str | None


@dataclass(frozen=True, slots=True)
class SearchResult:
    """The ranked, index-backed fields of one result. The main photo and age
    are added per DEC-V1-016 through `cards_for()`; the name and everything
    else stay consent-gated until a connection is accepted."""

    candidate_account_id: UUID
    score: float
    locality: str | None
    education_level: str | None
    profession: str | None
    height_cm: int | None = None
    marital_status: str | None = None
    mother_tongue: str | None = None
    gotra: str | None = None
    income_band: str | None = None
    # [§13] What has actually been verified about this person, with the date
    # and method. Evidence, never a score — there is no aggregate here and
    # there must not be one.
    verification: list[dict[str, str | None]] = field(default_factory=list)
    # [Migration 039/043] The first prompt answer this person published, if any.
    open_prompt: dict[str, str] | None = None
    # [DEC-V1-031] "strong" / "good" / None — the word a member sees. The
    # engine's 1–10 number stays internal.
    match_label: str | None = None


@dataclass(frozen=True, slots=True)
class SearchPage:
    results: list[SearchResult]
    total: int
    page: int
    page_size: int

    @property
    def has_more(self) -> bool:
        return self.page * self.page_size < self.total


_Attrs = dict[str, dict[str, tuple[FieldState, Any]]]


def _fact(attrs: _Attrs | None, name: str) -> Any:
    """First `value`-state answer for a fact across its known (category, key)
    slots (`config/profile_schema.FACT_SOURCES`). A declined or unset field
    contributes nothing, exactly as it contributes nothing to completeness."""
    if not attrs:
        return None
    for category, key in FACT_SOURCES.get(name, ()):
        entry = (attrs.get(category) or {}).get(key)
        if entry and entry[0] is FieldState.VALUE and entry[1] not in (None, ""):
            return entry[1]
    return None


def _text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        return " ".join(str(v) for v in value if v is not None) or None
    if isinstance(value, dict):
        return " ".join(str(v) for v in value.values() if isinstance(v, str)) or None
    return str(value)


def _int(value: Any) -> int | None:
    try:
        return int(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _geo_of(locality: str | None) -> dict[str, float] | None:
    """[DEC-V1-031] Coordinates of a member's city for the engine's distance
    fall-off, from the GeoNames list — "Hyderabad, Telangana" narrows by the
    state after the comma. None when the place is not in the list."""
    from app.components.places import interface as places

    if not locality or not locality.strip():
        return None
    found = places.search(locality, limit=1) or places.search(locality.split(",")[0], limit=1)
    return {"lat": found[0].latitude, "lon": found[0].longitude} if found else None


def _scales_of(entries: dict[str, tuple[FieldState, Any]]) -> dict[str, int]:
    """A member's own 1–10 ratings (`self_scales`), answered ones only."""
    out: dict[str, int] = {}
    for key, (state, value) in entries.items():
        number = _int(value) if state is FieldState.VALUE else None
        if number is not None and 1 <= number <= 10:
            out[key] = number
    return out


def _partner_value(attrs: _Attrs, key: str) -> Any:
    entry = (attrs.get("partner_preference") or {}).get(key)
    return entry[1] if entry and entry[0] is FieldState.VALUE else None


async def refresh_index(session: AsyncSession, *, account_id: UUID) -> None:
    """[FR021/FR026/FR027] Recompute this candidate's Discovery row from
    their current profile state. Called synchronously by `profile.interface`
    after any write that could change discoverability or ranking input."""
    from app.components.profile import interface as profile_module
    from app.components.trust import interface as trust

    own_profile = await profile_module.get_own_profile(session, account_id=account_id)
    if own_profile is None:
        return
    row = (await session.execute(select(Profile).where(Profile.id == own_profile.id))).scalar_one()

    searchable = await profile_module.is_discoverable(session, profile_id=own_profile.id)
    attrs = await profile_module.get_all_attribute_values(session, account_id=account_id) or {}
    completeness = await profile_module.completeness(session, account_id=account_id)

    education_level = _text(_fact(attrs, "highest_education_level"))
    profession_value = _text(_fact(attrs, "occupation"))
    relocation_willingness = _text(_fact(attrs, "relocation_willingness"))
    looking_for = _text(
        ((attrs.get("partner_preference") or {}).get("looking_for") or (None, None))[1]
    )
    partner_age_range = ((attrs.get("partner_preference") or {}).get("age_range") or (None, None))[1]
    partner_locality = ((attrs.get("partner_preference") or {}).get("locality") or (None, None))[1]
    # [DEC-V1-030] The rest of what a person asked for in a partner, so the
    # REVERSE check ("do I fit what they want?") can read it from their row
    # alone. Keys per `config/profile_schema` `partner_preference`.
    partner_height_range = ((attrs.get("partner_preference") or {}).get("height_range") or (None, None))[1]
    partner_education = ((attrs.get("partner_preference") or {}).get("education") or (None, None))[1]
    partner_diet = ((attrs.get("partner_preference") or {}).get("diet") or (None, None))[1]
    wanted_scales = _partner_value(attrs, "scales")
    brief = _partner_value(attrs, "brief")

    evidence_completeness = (
        completeness.enhanced_filled_categories / completeness.enhanced_total_categories
        if completeness and completeness.enhanced_total_categories
        else 0.0
    )

    snapshot = {
        "locality": own_profile.city_locality,
        "relocation_willingness": relocation_willingness,
        "partner_age_range": partner_age_range,
        "partner_locality": partner_locality,
        "partner_height_range": partner_height_range if isinstance(partner_height_range, dict) else None,
        "partner_education": partner_education,
        "partner_diet": partner_diet,
        "lifestyle_diet": _text(_fact(attrs, "diet")),
        "gender": own_profile.gender,
        "looking_for": looking_for,
        "marital_status": _text(_fact(attrs, "marital_status")),
        "date_of_birth": own_profile.date_of_birth.isoformat(),
        "education_level": education_level,
        "evidence_completeness": evidence_completeness,
        "height_cm": _int(_fact(attrs, "height_cm")),
        "mother_tongue": _text(_fact(attrs, "mother_tongue")),
        "gotra": _text(_fact(attrs, "gotra")),
        # [DEC-V1-022] What the "For you" rows compare. All biodata a searchable
        # profile already shows before a connection — never prompts or the ten
        # choices, which stay candidate-to-candidate (migration 039).
        "sub_community": _text(_fact(attrs, "sub_community")),
        "native_place": _text(_fact(attrs, "native_place")),
        "family_involvement": _text(_fact(attrs, "family_involvement")),
        "hobbies": [
            str(h).strip()
            for h in (_fact(attrs, "hobbies") or [])
            if isinstance(_fact(attrs, "hobbies"), list) and str(h).strip()
        ],
        # Evidence travels with the snapshot because Discovery must be able to
        # show it before a connection exists, and the verification table's own
        # RLS admits only the owner or a `candidate_info` holder. Written here,
        # in the candidate's own context, where reading it is permitted.
        "verification": trust.snapshot_form(
            (await trust.verified_layers_for(session, account_ids=[account_id])).get(
                account_id, []
            )
        ),
        # [DEC-V1-031] What the matching engine reads. The facts are biodata
        # a searchable profile already shows; the brief and both sets of 1–10
        # scales are private and only ever read by the engine — no endpoint
        # returns them for anyone but their owner.
        "geo": _geo_of(own_profile.city_locality),
        "smoking": _text(_fact(attrs, "smoking")),
        "drinking": _text(_fact(attrs, "drinking")),
        "income_band": _text(_fact(attrs, "income_band")),
        "family_type": _text(_fact(attrs, "family_type")),
        "family_values": _text(_fact(attrs, "family_values")),
        "manglik": _text(_fact(attrs, "manglik")),
        "self_scales": _scales_of(attrs.get("self_scales") or {}),
        "partner_scales": wanted_scales if isinstance(wanted_scales, dict) else None,
        "partner_brief": brief.get("items") if isinstance(brief, dict) else None,
    }

    # [Migration 039/043] The first prompt answer the candidate published —
    # shown on their Discover tile. Only answers marked public ever leave here.
    published = [
        {"q": str(v.get("q")), "a": str(v.get("a"))}
        for entry in (attrs.get("in_my_words") or {}).values()
        if entry[0] is FieldState.VALUE
        and isinstance((v := entry[1]), dict)
        and v.get("public") is True
        and v.get("q")
        and v.get("a")
    ]
    snapshot["open_prompt"] = published[0] if published else None

    prompts = [
        _text((entry[1] or {}).get("a")) if isinstance(entry[1], dict) else None
        for entry in (attrs.get("in_my_words") or {}).values()
        if entry[0] is FieldState.VALUE
    ]
    search_fields = (
        own_profile.city_locality,
        education_level,
        profession_value,
        relocation_willingness,
        _text(_fact(attrs, "employer")),
        _text(_fact(attrs, "college")),
        _text(_fact(attrs, "gotra")),
        _text(_fact(attrs, "sub_community")),
        _text(_fact(attrs, "mother_tongue")),
        _text(_fact(attrs, "native_place")),
        _text(_fact(attrs, "hobbies")),
        _text(_fact(attrs, "diet")),
        _text(_fact(attrs, "about_family")),
        *prompts,
    )
    search_text = " ".join(str(v) for v in search_fields if v)

    await session.execute(
        text(
            """
            INSERT INTO mangaly_discovery.discovery_profile_index
                (profile_id, searchable, locality, relocation_willingness,
                 education_level, profession, search_vector, ranking_input_snapshot, updated_at,
                 gender, looking_for, date_of_birth, marital_status, diet, height_cm, gotra,
                 sub_community, mother_tongue, income_band, manglik, profile_created_at,
                 last_active_at)
            VALUES
                (:profile_id, :searchable, :locality, :relocation_willingness,
                 :education_level, :profession, to_tsvector('english', :search_text),
                 CAST(:snapshot AS jsonb), now(),
                 :gender, :looking_for, :date_of_birth, :marital_status, :diet, :height_cm, :gotra,
                 :sub_community, :mother_tongue, :income_band, :manglik, :profile_created_at,
                 :last_active_at)
            ON CONFLICT (profile_id) DO UPDATE SET
                searchable = EXCLUDED.searchable,
                locality = EXCLUDED.locality,
                relocation_willingness = EXCLUDED.relocation_willingness,
                education_level = EXCLUDED.education_level,
                profession = EXCLUDED.profession,
                search_vector = EXCLUDED.search_vector,
                ranking_input_snapshot = EXCLUDED.ranking_input_snapshot,
                updated_at = now(),
                gender = EXCLUDED.gender,
                looking_for = EXCLUDED.looking_for,
                date_of_birth = EXCLUDED.date_of_birth,
                marital_status = EXCLUDED.marital_status,
                diet = EXCLUDED.diet,
                height_cm = EXCLUDED.height_cm,
                gotra = EXCLUDED.gotra,
                sub_community = EXCLUDED.sub_community,
                mother_tongue = EXCLUDED.mother_tongue,
                income_band = EXCLUDED.income_band,
                manglik = EXCLUDED.manglik,
                profile_created_at = EXCLUDED.profile_created_at,
                last_active_at = EXCLUDED.last_active_at
            """
        ),
        {
            "profile_id": account_id,
            "searchable": searchable,
            "locality": own_profile.city_locality,
            "relocation_willingness": relocation_willingness,
            "education_level": education_level,
            "profession": profession_value,
            "search_text": search_text,
            "snapshot": json.dumps(snapshot),
            "gender": own_profile.gender,
            "looking_for": looking_for,
            "date_of_birth": own_profile.date_of_birth,
            "marital_status": snapshot["marital_status"],
            "diet": snapshot["lifestyle_diet"],
            "height_cm": snapshot["height_cm"],
            "gotra": snapshot["gotra"],
            "sub_community": _text(_fact(attrs, "sub_community")),
            "mother_tongue": snapshot["mother_tongue"],
            "income_band": _text(_fact(attrs, "income_band")),
            "manglik": _text(_fact(attrs, "manglik")),
            "profile_created_at": row.created_at,
            "last_active_at": row.updated_at,
        },
    )


def _score(viewer: dict, candidate: dict) -> float:
    """[DEC-V1-031] The AI matching engine's pair score, rescaled from its
    1–10 to 0–1 for the diversity brackets. Both directions, the family's own
    words and importance, both sides' 1–10 scales, diet and distance — see
    `components/compatibility/engine.py`. `POPULARITY_WEIGHT` stays 0.0 by
    construction (DEC-V1-002): the engine reads no engagement or view metric.
    In browse mode the viewer dict is empty and every direction is neutral,
    so profile evidence alone gives a stable, explainable order.
    """
    return (compatibility.pair_score(viewer, candidate) - 1.0) / 9.0


def match_label(score: float) -> str | None:
    """[DEC-V1-031] The word a member sees for a 0–1 `_score`, never the number."""
    return compatibility.label_for(1.0 + 9.0 * score)


# [DEC-V1-030] A side that stated no preference is neither a fit nor a
# misfit. Treating it as 0 would bury everyone who set strict preferences
# behind people whose counterparts said nothing; 0.5 keeps them visible.
NEUTRAL_FIT = 0.5


def fit(checks: list[float]) -> float:
    """Share of one person's stated preferences the other person meets;
    `NEUTRAL_FIT` when nothing was stated (or nothing could be checked)."""
    return sum(checks) / len(checks) if checks else NEUTRAL_FIT


def reciprocity(forward: list[float], reverse: list[float]) -> float:
    """[DEC-V1-030] Harmonic mean of "they fit what I asked" (`forward`) and
    "I fit what they asked" (`reverse`). Hinge's Most Compatible pairs people
    likely to want EACH OTHER (a Gale–Shapley idea); the harmonic mean is the
    arithmetic form of that — 1.0 on one side and 0.0 on the other gives 0,
    not 0.5, so a one-way fit never passes as a mutual one."""
    a, b = fit(forward), fit(reverse)
    return 0.0 if a + b == 0 else 2 * a * b / (a + b)


def _as_set(value: Any) -> set[str]:
    if value in (None, ""):
        return set()
    items = value if isinstance(value, list) else [value]
    return {str(v).strip().lower() for v in items if v not in (None, "")}


def _preference_checks(seeker: dict, other: dict) -> list[float]:
    """One 0/1 per preference the `seeker` stated that `other`'s facts allow
    us to check: locality, age, and — since DEC-V1-030 — height, education
    and diet. A preference the other person has no fact for is skipped (it
    counts neither way), exactly as an unset preference is."""
    checks: list[float] = []
    preferred_locality = seeker.get("partner_locality")
    if preferred_locality and other.get("locality"):
        checks.append(1.0 if _locality_wanted(preferred_locality, other["locality"]) else 0.0)
    age_range = seeker.get("partner_age_range")
    other_age = _age_years(other.get("date_of_birth"))
    if isinstance(age_range, dict) and other_age is not None:
        low, high = age_range.get("min"), age_range.get("max")
        if low or high:
            inside = (low or 0) <= other_age <= (high or 200)
            checks.append(1.0 if inside else 0.0)
    height_range = seeker.get("partner_height_range")
    other_height = _int(other.get("height_cm"))
    if isinstance(height_range, dict) and other_height is not None:
        low, high = _int(height_range.get("min")), _int(height_range.get("max"))
        if low or high:
            checks.append(1.0 if (low or 0) <= other_height <= (high or 300) else 0.0)
    wanted_education = _as_set(seeker.get("partner_education"))
    if wanted_education and other.get("education_level"):
        checks.append(1.0 if str(other["education_level"]).strip().lower() in wanted_education else 0.0)
    wanted_diet = _as_set(seeker.get("partner_diet"))
    if wanted_diet and other.get("lifestyle_diet"):
        checks.append(1.0 if str(other["lifestyle_diet"]).strip().lower() in wanted_diet else 0.0)
    return checks


def _locality_wanted(preferred: Any, locality: Any) -> bool:
    """"Bengaluru or Hyderabad" wants either city; "Hyderabad" wants
    "Hyderabad, Telangana". Free text on both sides, so this is containment
    of each wanted place in the person's locality, not equality."""
    spelled = str(preferred).lower().replace("/", ",").replace(" or ", ",")
    places = [p.strip() for p in spelled.split(",") if p.strip()]
    where = str(locality).strip().lower()
    return any(p in where for p in places)


def reciprocal_reasons(seeker: dict, other: dict) -> list[dict[str, Any]]:
    """[DEC-V1-030] Honest, language-neutral reasons a pair fits EACH OTHER,
    strongest first, as `{"key": ..., **params}` for `discovery.shelf.reason`
    / `reasonFor`. Only stated preferences and checkable biodata — never a
    score, never who looked at whom."""
    forward = _preference_checks(seeker, other)
    reverse = _preference_checks(other, seeker)
    out: list[dict[str, Any]] = []
    if forward and reverse and all(forward) and all(reverse):
        out.append({"key": "mutualFit"})
    my_city = str(seeker.get("locality") or "").split(",")[0].strip()
    if my_city and other.get("partner_locality") and _locality_wanted(other["partner_locality"], seeker.get("locality")):
        out.append({"key": "wantsYourCity", "city": my_city})
    age_range = other.get("partner_age_range")
    my_age = _age_years(seeker.get("date_of_birth"))
    if isinstance(age_range, dict) and my_age is not None and (age_range.get("min") or age_range.get("max")):
        if (age_range.get("min") or 0) <= my_age <= (age_range.get("max") or 200):
            out.append({"key": "wantsYourAge"})
    return out


def _score_bracket(score: float) -> int:
    return min(int(score * SCORE_BRACKETS), SCORE_BRACKETS - 1)


def _diversify[T](ranked: list[T], *, score_of: Callable[[T], float]) -> list[T]:
    """[TR026/DEC-V1-002] No more than `MAX_SAME_BRACKET_RUN` results in a
    row share one score bracket; nothing is dropped, order within a bracket
    never changes."""
    remaining = list(ranked)
    result: list[T] = []
    while remaining:
        run_bracket = _score_bracket(score_of(result[-1])) if result else None
        run_length = 0
        for item in reversed(result):
            if _score_bracket(score_of(item)) != run_bracket:
                break
            run_length += 1
        pick = 0
        if run_length >= MAX_SAME_BRACKET_RUN:
            pick = next(
                (
                    i
                    for i, item in enumerate(remaining)
                    if _score_bracket(score_of(item)) != run_bracket
                ),
                0,
            )
        result.append(remaining.pop(pick))
    return result


async def get_snapshot(session: AsyncSession, *, account_id: UUID) -> dict | None:
    row = await session.get(DiscoveryProfileIndex, account_id)
    return row.ranking_input_snapshot if row else None


async def get_snippet(session: AsyncSession, *, account_id: UUID) -> Snippet | None:
    row = await session.get(DiscoveryProfileIndex, account_id)
    if row is None:
        return None
    return Snippet(
        locality=row.locality, education_level=row.education_level, profession=row.profession
    )


class LookingForMissing(Exception):
    """The person matches are ranked for has not said who they are looking
    for — and, in browse mode, the caller did not say either."""


_GENDER_LOOKED_FOR = {"bride": "female", "groom": "male"}
_WORD_FOR_GENDER = {"female": "bride", "male": "groom"}


async def looking_for_allows(
    session: AsyncSession, *, seeker_account_id: UUID, target_account_id: UUID
) -> bool:
    """[Owner rule: "Looking for" always constrains who you see AND who your
    requests reach] The same two-way test `search()` applies: the target is
    the gender the seeker is looking for, and — when the target has answered —
    is looking for the seeker's. A seeker who has not answered matches nobody,
    exactly as search raises `LookingForMissing` for them."""
    seeker = await session.get(DiscoveryProfileIndex, seeker_account_id)
    target = await session.get(DiscoveryProfileIndex, target_account_id)
    if seeker is None or target is None:
        return False
    wanted_gender = _GENDER_LOOKED_FOR.get(seeker.looking_for or "")
    if wanted_gender is None or target.gender != wanted_gender:
        return False
    seeker_word = _WORD_FOR_GENDER.get(seeker.gender or "")
    return not (seeker_word and target.looking_for and target.looking_for != seeker_word)


@dataclass(frozen=True, slots=True)
class DiscoverFilters:
    """[UX16, contract §3] Filters narrow the engine's matches and never
    change the ranking. Multi-valued filters are case-insensitive exact."""

    nearby: str | None = None  # "city" or "state", relative to the seeker's own locality
    age_min: int | None = None
    age_max: int | None = None
    marital_status: tuple[str, ...] = ()
    education: tuple[str, ...] = ()
    diet: tuple[str, ...] = ()
    open_to_relocate: bool = False
    height_min: int | None = None
    height_max: int | None = None
    gotra: tuple[str, ...] = ()
    sub_community: tuple[str, ...] = ()
    profession: tuple[str, ...] = ()
    income_band: tuple[str, ...] = ()
    mother_tongue: tuple[str, ...] = ()
    manglik: str | None = None
    q: str | None = None
    city: tuple[str, ...] = ()
    # [Owner, 2026-09-27] Optional horoscope filter, switched on by the member:
    # a minimum Guna Milan (out of 36) with the person searched for, and/or
    # Mangal Dosha "match" (same presence) or "none". Needs that person's chart.
    min_guna: float | None = None
    mangal: str | None = None
    # South Indian: at least this many of the 10 poruthams, and/or Rajju and
    # Vedha (the essential two) must agree.
    min_porutham: int | None = None
    porutham_essentials: bool = False


def _place(locality: str | None, part: str) -> str:
    pieces = [p.strip().lower() for p in (locality or "").split(",") if p.strip()]
    if not pieces:
        return ""
    return pieces[0] if part == "city" else pieces[-1]


def _age_years(date_of_birth: str | date | None) -> int | None:
    if not date_of_birth:
        return None
    born = date.fromisoformat(date_of_birth) if isinstance(date_of_birth, str) else date_of_birth
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def _lower(values: tuple[str, ...]) -> list[str]:
    return [v.strip().lower() for v in values if v and v.strip()]


async def authorize_family_viewer(
    session: AsyncSession, *, viewer_account_id: UUID, candidate_account_id: UUID
) -> None:
    """[FR013] A Home Circle member may search for the candidate they help,
    ranked against that candidate's own preferences, only while they hold
    `family_info` on that candidate. Raises `AuthorizationDenied`."""
    from app.components.authorization import interface as authz
    from app.components.authorization.context import Action, Capacity, GrantScope

    ctx = await authz.resolve(
        session,
        subject_id=viewer_account_id,
        account_id=viewer_account_id,
        target_profile_id=candidate_account_id,
        action=Action.READ,
        capacity=Capacity.FAMILY,
    )
    ctx.require_scope(GrantScope.FAMILY_INFO)


async def search(
    session: AsyncSession,
    *,
    viewer_account_id: UUID,
    for_candidate_account_id: UUID | None = None,
    filters: DiscoverFilters | None = None,
    page: int = 1,
    page_size: int = 20,
    looking_for: str | None = None,
    sort: str = "relevance",
) -> SearchPage:
    """[FR021/FR026, contract §3/§6] Every result is `searchable = true`.
    What a caller may then SEE of a found profile is a separate question,
    resolved by the Authorization Engine, not here.

    Ranked for the context candidate (`for_candidate_account_id`, a circle
    member acting for them) or for the viewer. When neither has a "looking
    for" answer — a member with no profile, browsing — the explicit
    `looking_for` parameter is required (browse mode), and the seeker side of
    the two-way gender rule is simply unknown.
    """
    from app.components.authorization import interface as authz
    from app.components.authorization.context import Action
    from app.components.safety import interface as safety

    filters = filters or DiscoverFilters()
    ranking_account_id = viewer_account_id
    if for_candidate_account_id is not None and for_candidate_account_id != viewer_account_id:
        await authorize_family_viewer(
            session,
            viewer_account_id=viewer_account_id,
            candidate_account_id=for_candidate_account_id,
        )
        ranking_account_id = for_candidate_account_id
    else:
        await authz.resolve_self(session, account_id=viewer_account_id, action=Action.READ)

    seeker = await get_snapshot(session, account_id=ranking_account_id) or {}
    seeker_looking_for = str(seeker.get("looking_for") or looking_for or "")
    wanted_gender = _GENDER_LOOKED_FOR.get(seeker_looking_for)
    if wanted_gender is None:
        raise LookingForMissing
    seeker_word = _WORD_FOR_GENDER.get(str(seeker.get("gender") or ""))

    excluded: set[UUID] = {viewer_account_id, ranking_account_id}
    excluded |= await safety.blocked_ids(session, account_id=ranking_account_id)
    if ranking_account_id != viewer_account_id:
        excluded |= await safety.blocked_ids(session, account_id=viewer_account_id)
    # Already connected (accepted, either direction): no longer a "new match".
    # Pending requests stay in, shown with their state.
    from app.components.connection import interface as connection

    excluded |= await connection.connected_ids(session, account_id=ranking_account_id)
    # [Owner, 2026-09-25] Someone who declined this candidate stays out of
    # their Discover for the decline cool-down.
    excluded |= await connection.declined_ids(session, account_id=ranking_account_id)

    clauses = [
        "searchable",
        "NOT (profile_id = ANY(CAST(:excluded AS uuid[])))",
        "gender = :wanted_gender",
    ]
    params: dict[str, Any] = {
        "excluded": [str(e) for e in excluded],
        "wanted_gender": wanted_gender,
    }
    if seeker_word:
        clauses.append("looking_for = :seeker_word")
        params["seeker_word"] = seeker_word
    if filters.age_min is not None:
        clauses.append("date_part('year', age(current_date, date_of_birth)) >= :age_min")
        params["age_min"] = filters.age_min
    if filters.age_max is not None:
        clauses.append("date_part('year', age(current_date, date_of_birth)) <= :age_max")
        params["age_max"] = filters.age_max
    if filters.height_min is not None:
        clauses.append("height_cm >= :height_min")
        params["height_min"] = filters.height_min
    if filters.height_max is not None:
        clauses.append("height_cm <= :height_max")
        params["height_max"] = filters.height_max
    for column, values in (
        ("marital_status", filters.marital_status),
        ("education_level", filters.education),
        ("diet", filters.diet),
        ("gotra", filters.gotra),
        ("sub_community", filters.sub_community),
        ("profession", filters.profession),
        ("income_band", filters.income_band),
        ("mother_tongue", filters.mother_tongue),
    ):
        lowered = _lower(values)
        if lowered:
            clauses.append(f"lower({column}) = ANY(CAST(:{column}_in AS text[]))")
            params[f"{column}_in"] = lowered
    if filters.manglik:
        clauses.append("lower(manglik) = :manglik")
        params["manglik"] = filters.manglik.strip().lower()
    if filters.open_to_relocate:
        clauses.append("relocation_willingness IN ('yes', 'open_to_discussion', 'open_to_relocate')")
    if filters.city:
        clauses.append(
            "lower(split_part(COALESCE(locality, ''), ',', 1)) = ANY(CAST(:city_in AS text[]))"
        )
        params["city_in"] = _lower(filters.city)
    if filters.q and filters.q.strip():
        clauses.append(
            "(search_vector @@ plainto_tsquery('english', :q) OR locality ILIKE :q_like "
            "OR profession ILIKE :q_like OR gotra ILIKE :q_like OR sub_community ILIKE :q_like)"
        )
        params["q"] = filters.q.strip()
        params["q_like"] = f"%{filters.q.strip()}%"

    sql = text(
        "SELECT profile_id, locality, relocation_willingness, education_level, profession, "
        "ranking_input_snapshot, height_cm, marital_status, mother_tongue, gotra, income_band, "
        "profile_created_at, last_active_at, updated_at "
        "FROM mangaly_discovery.discovery_profile_index WHERE " + " AND ".join(clauses)
        # A fixed base order: the sorts below are stable, so people with the
        # same score or date keep this order on every page request and a page
        # boundary never repeats or skips one of them.
        + " ORDER BY profile_id"
    )
    rows = (await session.execute(sql, params)).mappings().all()

    if filters.nearby:
        mine = _place(seeker.get("locality"), filters.nearby)
        rows = [r for r in rows if mine and _place(r["locality"], filters.nearby) == mine]

    if (filters.min_guna is not None or filters.mangal or filters.min_porutham is not None or filters.porutham_essentials) and rows:
        from app.components.horoscope import interface as horoscope

        keep = await horoscope.filter_ids(
            session,
            seeker_account_id=ranking_account_id,
            seeker_gender=str(seeker.get("gender") or ""),
            candidate_ids=[r["profile_id"] for r in rows],
            min_guna=filters.min_guna,
            mangal=filters.mangal,
            min_porutham=filters.min_porutham,
            porutham_essentials=filters.porutham_essentials,
        )
        rows = [r for r in rows if r["profile_id"] in keep]

    # [DEC-V1-031] Must-haves, both ways: anyone whose facts clearly miss an
    # importance-10 wish of the seeker is left out, and so is anyone whose own
    # must-have the seeker clearly misses (they would only decline). A blank
    # fact never removes anyone.
    if seeker:
        rows = [
            r
            for r in rows
            if not compatibility.fails_must(seeker, r["ranking_input_snapshot"] or {})
            and not compatibility.fails_must(r["ranking_input_snapshot"] or {}, seeker)
        ]

    scored = [(r, _score(seeker, r["ranking_input_snapshot"] or {})) for r in rows]
    if sort == "newest":
        scored.sort(key=lambda pair: (pair[0]["profile_created_at"] or pair[0]["updated_at"]), reverse=True)
    elif sort == "recently_active":
        scored.sort(key=lambda pair: (pair[0]["last_active_at"] or pair[0]["updated_at"]), reverse=True)
    else:
        scored.sort(key=lambda pair: pair[1], reverse=True)
        scored = _diversify(scored, score_of=lambda pair: pair[1])

    total = len(scored)
    start = (page - 1) * page_size
    page_slice = scored[start : start + page_size]
    return SearchPage(
        results=[
            SearchResult(
                candidate_account_id=r["profile_id"],
                score=score,
                locality=r["locality"],
                education_level=r["education_level"],
                profession=r["profession"],
                height_cm=r["height_cm"],
                marital_status=r["marital_status"],
                mother_tongue=r["mother_tongue"],
                gotra=r["gotra"],
                income_band=r["income_band"],
                verification=list((r["ranking_input_snapshot"] or {}).get("verification") or []),
                open_prompt=(r["ranking_input_snapshot"] or {}).get("open_prompt"),
                match_label=match_label(score) if seeker else None,
            )
            for r, score in page_slice
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@dataclass(frozen=True, slots=True)
class DiscoveryCard:
    photo_url: str | None
    age: int | None


@dataclass(frozen=True, slots=True)
class OpenCard:
    """[Migration 043] What one candidate chose to show openly."""

    first_name: str | None
    photo_urls: list[str]


async def open_cards_for(session: AsyncSession, *, account_ids: list[UUID]) -> dict[UUID, OpenCard]:
    """First name and photos a searchable candidate opened (both default closed)."""
    if not account_ids:
        return {}
    from app.components.profile import interface as profile_module

    rows = await session.execute(
        text("SELECT * FROM mangaly_profile.open_cards(CAST(:ids AS uuid[]))"),
        {"ids": [str(a) for a in account_ids]},
    )
    return {
        r["account_id"]: OpenCard(
            first_name=r["first_name"],
            photo_urls=[u for ref in (r["photo_refs"] or []) if (u := profile_module.resolve_photo_url(ref))],
        )
        for r in rows.mappings()
    }


async def cards_for(session: AsyncSession, *, account_ids: list[UUID]) -> dict[UUID, DiscoveryCard]:
    """[DEC-V1-016] Main photo and age for searchable candidates only, through
    `discovery_cards()` (migration 020). Anyone not searchable is simply absent."""
    if not account_ids:
        return {}
    from app.components.profile import interface as profile_module

    rows = await session.execute(
        text("SELECT * FROM mangaly_discovery.discovery_cards(CAST(:ids AS uuid[]))"),
        {"ids": [str(a) for a in account_ids]},
    )
    return {
        r["account_id"]: DiscoveryCard(
            photo_url=profile_module.resolve_photo_url(r["photo_ref"]) if r["photo_ref"] else None,
            age=r["age"],
        )
        for r in rows.mappings()
    }



# ---------------------------------------------------------------------------
# [DEC-V1-022] "For you": themed rows, each face with one honest reason
# ---------------------------------------------------------------------------
#
# Netflix's home is titled rows whose title is the explanation ("Because you
# watched…"); Bumble's Discover groups people by shared interests and
# communities; Hinge's Most Compatible leads with mutual preferences. Mangaly
# takes the pattern and keeps its own rules: every row is a fact both people can
# check (same city, same mother tongue, both vegetarian, the family suggested
# them), no row is ranked by popularity or attention (Hinge's Standouts is the
# pattern NOT taken — popularity weight is 0 by construction, DEC-V1-002), and
# nothing is scored. Rows only compare biodata a searchable profile already
# shows before a connection.

@dataclass(frozen=True, slots=True)
class DailyPick:
    """[DEC-V1-030] One row of `mangaly_discovery.daily_pick`: the stable
    partner the daily pass chose for `account_id` (`rank` 1), and the
    fallbacks (`rank` 2..n) for when the first is no longer available."""

    pick_account_id: UUID
    pick_date: date
    rank: int
    reasons: list[dict[str, Any]]


async def daily_picks_for(session: AsyncSession, *, account_id: UUID) -> list[DailyPick]:
    """The most recent day's picks for one person, rank order. Under RLS the
    person and a circle member holding `family_info` may read them. Nothing
    older than `DAILY_PICK_MAX_AGE_DAYS` is returned."""
    rows = (
        await session.execute(
            text(
                "SELECT pick_account_id, pick_date, rank, reasons "
                "FROM mangaly_discovery.daily_pick "
                "WHERE account_id = :me "
                "  AND pick_date = (SELECT max(pick_date) FROM mangaly_discovery.daily_pick WHERE account_id = :me) "
                "  AND pick_date >= current_date - CAST(:max_age AS integer) "
                "ORDER BY rank"
            ),
            {"me": account_id, "max_age": DAILY_PICK_MAX_AGE_DAYS},
        )
    ).mappings().all()
    return [
        DailyPick(
            pick_account_id=r["pick_account_id"],
            pick_date=r["pick_date"],
            rank=int(r["rank"]),
            reasons=list(r["reasons"] or []),
        )
        for r in rows
    ]


async def _most_compatible(
    session: AsyncSession,
    *,
    account_id: UUID,
    seeker: dict,
    by_id: dict[UUID, "SearchResult"],
    snap: dict[UUID, dict],
    translate_reason: Callable[[dict[str, Any]], str],
    reciprocal_reason: Callable[[dict], str | None],
) -> tuple["SearchResult", str | None] | None:
    """[DEC-V1-030] The first stored stable choice still worth showing.

    `by_id` is the ranked search result set, so a pick who is no longer
    searchable, no longer matches the "looking for" rule, or is blocked in
    either direction is skipped without a second query. A pick with a live
    request (pending) or an accepted connection is skipped too: "most
    compatible today" introduces someone new, it does not re-show a person
    the family is already talking to."""
    from app.components.connection import interface as connection
    from app.components.connection.models import ConnectionStatus

    for pick in await daily_picks_for(session, account_id=account_id):
        result = by_id.get(pick.pick_account_id)
        if result is None:
            continue
        try:
            between = await connection.connection_between(
                session, account_id=account_id, other_account_id=pick.pick_account_id
            )
        except Exception:  # noqa: BLE001 — a row, never the page, fails
            between = None
        if between is not None and between.status in (ConnectionStatus.PENDING, ConnectionStatus.ACCEPTED):
            continue
        reasons = pick.reasons or reciprocal_reasons(seeker, snap.get(pick.pick_account_id, {}))
        why = translate_reason(reasons[0]) if reasons else reciprocal_reason(snap.get(pick.pick_account_id, {}))
        return result, why
    return None


@dataclass(frozen=True, slots=True)
class ShelfItem:
    result: SearchResult
    reason: str | None


@dataclass(frozen=True, slots=True)
class Shelf:
    key: str
    items: list[ShelfItem]
    # Filters that reproduce this row on the full wall ("See all").
    see_all: dict[str, object]


SHELF_SIZE = 12
# "Picked for you" is a short lead row so the rows below keep real people
# (each person appears in one row only); a row needs two people to stand.
PICKED_SHELF_SIZE = 6
MIN_SHELF_SIZE = 2


async def shelves(
    session: AsyncSession,
    *,
    viewer_account_id: UUID,
    for_candidate_account_id: UUID | None = None,
    looking_for: str | None = None,
    lang: str = "en",
) -> list[Shelf]:
    from datetime import UTC, datetime

    from app.components.home_circle import interface as home_circle
    from app.i18n import translate

    page = await search(
        session,
        viewer_account_id=viewer_account_id,
        for_candidate_account_id=for_candidate_account_id,
        page=1,
        page_size=200,
        looking_for=looking_for,
    )
    ranked = page.results
    if not ranked:
        return []
    ranking_account = for_candidate_account_id or viewer_account_id
    seeker = await get_snapshot(session, account_id=ranking_account) or {}
    rows = (
        await session.execute(
            text(
                "SELECT profile_id, ranking_input_snapshot, profile_created_at "
                "FROM mangaly_discovery.discovery_profile_index "
                "WHERE profile_id = ANY(CAST(:ids AS uuid[]))"
            ),
            {"ids": [str(r.candidate_account_id) for r in ranked]},
        )
    ).mappings().all()
    snap = {r["profile_id"]: (r["ranking_input_snapshot"] or {}) for r in rows}
    created = {r["profile_id"]: r["profile_created_at"] for r in rows}

    # Whose seat the reasons are written from. A parent searching for Varun
    # reads "In Hyderabad, like Varun", never "like you" — it is Varun's city.
    for_other = ranking_account != viewer_account_id
    candidate_first = ""
    if for_other:
        candidate_first = (
            (
                await session.execute(
                    text("SELECT candidate_name FROM mangaly_home_circle.list_member_contexts(:me) WHERE candidate_account_id = :c"),
                    {"me": viewer_account_id, "c": ranking_account},
                )
            ).scalar_one_or_none()
            or ""
        ).split(" ")[0]

    def t(key: str, **params: object) -> str:
        text_ = ""
        if for_other:
            alt = f"discovery.shelf.reasonFor.{key}"
            text_ = translate(alt, lang, name=candidate_first, **params)
            if text_ == alt:
                text_ = ""
        text_ = text_ or translate(f"discovery.shelf.reason.{key}", lang, **params)
        # A reason is a sentence: it starts with a capital even when it opens
        # on a value ("Eggetarian, like Varun").
        return text_[:1].upper() + text_[1:]

    def val(enum: str, raw: object) -> str:
        key = f"discovery.value.{enum}.{raw}"
        text_ = translate(key, lang)
        return str(raw) if text_ == key else text_

    def city_of(value: object) -> str:
        return str(value or "").split(",")[0].strip()

    def same(a: object, b: object) -> bool:
        return bool(a) and bool(b) and str(a).strip().lower() == str(b).strip().lower()

    my_city = city_of(seeker.get("locality"))
    my_hobbies = {h.lower(): h for h in (seeker.get("hobbies") or [])}

    def shared_hobbies(c: dict) -> list[str]:
        return [h for h in (c.get("hobbies") or []) if h.lower() in my_hobbies]

    def reciprocal_reason(c: dict) -> str | None:
        """[DEC-V1-030] The strongest way this pair fits EACH OTHER, if any."""
        reasons = reciprocal_reasons(seeker, c)
        return translate_reason(reasons[0]) if reasons else None

    def translate_reason(reason: dict[str, Any]) -> str:
        params = {k: v for k, v in reason.items() if k != "key"}
        return t(str(reason["key"]), **params)

    def best_reason(c: dict) -> str | None:
        """The single strongest shared fact, for the "Picked for you" row.
        A specific fact first (it tells the two people apart); the mutual
        preference fit next (the row's own title already says it, so on a
        card it only earns its place when nothing more specific exists);
        the city last."""
        hobbies = shared_hobbies(c)
        if hobbies:
            return t("sharedHobbies", list=", ".join(hobbies[:2]))
        if same(c.get("mother_tongue"), seeker.get("mother_tongue")):
            return t("sameTongue", value=val("mother_tongue", c.get("mother_tongue")))
        if same(c.get("sub_community"), seeker.get("sub_community")):
            return t("sameCommunity", value=val("sub_community", c.get("sub_community")))
        if same(c.get("family_involvement"), seeker.get("family_involvement")):
            return t("sameFamilyView", value=val("family_involvement", c.get("family_involvement")))
        if same(c.get("lifestyle_diet"), seeker.get("lifestyle_diet")):
            return t("sameDiet", value=val("diet", c.get("lifestyle_diet")))
        mutual = reciprocal_reason(c)
        if mutual:
            return mutual
        # The city last: when everyone is local it says the least.
        if my_city and same(city_of(c.get("locality")), my_city):
            return t("sameCity", city=my_city)
        return nearby_reason(c)

    def nearby_reason(c: dict) -> str | None:
        """[DEC-V1-031] A different city close enough to matter ("In
        Secunderabad · about 12 km away") — it used to count as "not
        Hyderabad" at all."""
        here, there = seeker.get("geo"), c.get("geo")
        if not (isinstance(here, dict) and isinstance(there, dict)) or same(city_of(c.get("locality")), my_city):
            return None
        km = compatibility.distance_km((here["lat"], here["lon"]), (there["lat"], there["lon"]))
        if km > NEARBY_REASON_KM:
            return None
        return t("nearby", city=city_of(c.get("locality")), km=max(5, int(round(km / 5.0)) * 5))

    out: list[Shelf] = []

    # Each person sits in ONE row per screen (owner, 2026-09-24: "why am I
    # seeing the same person in multiple baskets?"). A row takes only people
    # no earlier row has claimed; a family suggestion is reserved for the
    # family row before "Picked for you" is filled, since a person the circle
    # chose is best explained by that. "See all" still opens the full wall.
    claimed: set[UUID] = set()
    # One person left for a row does not make a row (lead, 2026-09-24): the
    # card joins the row above it, keeping its own reason; before any row
    # exists it waits and opens the next one.
    waiting: list[ShelfItem] = []

    def shelf(
        key: str,
        picked: list[tuple[SearchResult, str | None]],
        see_all: dict[str, object],
        size: int = SHELF_SIZE,
    ) -> None:
        """A row of people not already shown in a row above it; no row when
        nobody is left for it."""
        items = [ShelfItem(r, why) for r, why in picked if r.candidate_account_id not in claimed][:size]
        if not items:
            return
        claimed.update(i.result.candidate_account_id for i in items)
        # The one-person hero is a row by design, and one person the family
        # chose is still the family's pick: neither folds into another row.
        if key in ("mostCompatible", "family"):
            out.append(Shelf(key=key, items=items, see_all=see_all))
            return
        above = next((s for s in reversed(out) if s.key not in ("mostCompatible", "family")), None)
        if len(items) < MIN_SHELF_SIZE:
            if above is not None:
                above.items.extend(items)
            else:
                waiting.extend(items)
            return
        out.append(Shelf(key=key, items=[*waiting, *items], see_all=see_all))
        waiting.clear()

    # 0. Most compatible today — ONE person from the daily stable-matching
    #    pass (DEC-V1-030), with the reason the pair fits each other. The first
    #    stored choice who is still searchable, still matches, and is not yet
    #    connected, requested or blocked; nothing if the job has no pick.
    by_id = {r.candidate_account_id: r for r in ranked}
    hero = await _most_compatible(
        session,
        account_id=ranking_account,
        seeker=seeker,
        by_id=by_id,
        snap=snap,
        translate_reason=translate_reason,
        reciprocal_reason=reciprocal_reason,
    )
    if hero is not None:
        shelf("mostCompatible", [hero], {})

    # 2 (built first, shown second). Suggested by the family — the circle's
    #    picks, only the ones who match.
    try:
        suggestions = await home_circle.list_suggestions(
            session, caller_account_id=viewer_account_id, candidate_account_id=ranking_account
        )
    except Exception:  # noqa: BLE001 — a row, never the page, fails
        suggestions = []
    fam: list[tuple[SearchResult, str | None]] = []
    for s_ in suggestions:
        r = by_id.get(s_.suggested_profile_id)
        if r is not None and all(r is not x for x, _ in fam):
            if s_.suggested_by_account_id == viewer_account_id:
                why = t("suggestedByYou")
            else:
                who = (
                    val("relation", s_.suggested_by_relation)
                    if s_.suggested_by_relation
                    else val("relationship", s_.suggested_by_relationship_type.value)
                )
                why = t("suggestedBy", relation=who)
            fam.append((r, why))
    family_ids = {r.candidate_account_id for r, _ in fam if r.candidate_account_id not in claimed}

    # 1. Picked for you — the engine's own order (DEC-V1-002), with a reason.
    shelf(
        "picked",
        [
            (r, best_reason(snap.get(r.candidate_account_id, {})))
            for r in ranked
            if r.candidate_account_id not in family_ids
        ],
        {},
        size=PICKED_SHELF_SIZE,
    )
    shelf("family", fam, {})

    # 3. Close to home — the same city.
    if my_city:
        shelf(
            "near",
            [(r, t("sameCity", city=my_city)) for r in ranked
             if same(city_of(snap.get(r.candidate_account_id, {}).get("locality")), my_city)],
            {"nearby": "city"},
        )

    # 4. Would move for the right person — other cities, open to relocating.
    if my_city:
        shelf(
            "moving",
            [
                (r, t("openToMove", city=city_of(c.get("locality"))))
                for r in ranked
                if (c := snap.get(r.candidate_account_id, {}))
                and not same(city_of(c.get("locality")), my_city)
                and c.get("relocation_willingness") in ("yes", "open_to_discussion")
            ],
            {"openToRelocate": True},
        )

    # 5. Same roots — mother tongue, community, native place.
    roots: list[tuple[SearchResult, str | None]] = []
    for r in ranked:
        c = snap.get(r.candidate_account_id, {})
        if same(c.get("mother_tongue"), seeker.get("mother_tongue")):
            roots.append((r, t("sameTongue", value=val("mother_tongue", c.get("mother_tongue")))))
        elif same(c.get("sub_community"), seeker.get("sub_community")):
            roots.append((r, t("sameCommunity", value=val("sub_community", c.get("sub_community")))))
        elif same(c.get("native_place"), seeker.get("native_place")):
            roots.append((r, t("sameNative", place=c.get("native_place"))))
    shelf(
        "roots",
        roots,
        {"motherTongue": [seeker["mother_tongue"]]} if seeker.get("mother_tongue") else {},
    )

    # 6. Shares your way of life — shared interests, or the same food.
    life: list[tuple[SearchResult, str | None]] = []
    for r in ranked:
        c = snap.get(r.candidate_account_id, {})
        hobbies = shared_hobbies(c)
        if hobbies:
            life.append((r, t("sharedHobbies", list=", ".join(hobbies[:2]))))
        elif same(c.get("lifestyle_diet"), seeker.get("lifestyle_diet")):
            life.append((r, t("sameDiet", value=val("diet", c.get("lifestyle_diet")))))
    shelf("life", life, {"diet": [seeker["lifestyle_diet"]]} if seeker.get("lifestyle_diet") else {})

    # 7. Sees family life the way you do — the same family-involvement answer.
    if seeker.get("family_involvement"):
        shelf(
            "familyView",
            [
                (r, t("sameFamilyView", value=val("family_involvement", seeker["family_involvement"])))
                for r in ranked
                if same(snap.get(r.candidate_account_id, {}).get("family_involvement"), seeker["family_involvement"])
            ],
            {},
        )

    # 8. In their own words — people who published an answer openly.
    shelf("words", [(r, None) for r in ranked if r.open_prompt], {})

    # 9. New this month — newest first.
    now = datetime.now(UTC)
    fresh = sorted(
        (r for r in ranked if created.get(r.candidate_account_id) and (now - created[r.candidate_account_id]).days <= 30),
        key=lambda r: created[r.candidate_account_id],
        reverse=True,
    )
    shelf(
        "new",
        [
            (
                r,
                t("joinedToday")
                if (d := (now - created[r.candidate_account_id]).days) <= 0
                else t("joinedYesterday")
                if d == 1
                else t("joined", days=d),
            )
            for r in fresh
        ],
        {"sort": "newest"},
    )
    # 10. Everyone else who matches, in the engine's order. Without it a match
    #     who fits no theme and ranks below "Picked for you" appeared nowhere,
    #     so "Everyone" on For you (14) disagreed with Home's match count (15).
    shelf(
        "more",
        [(r, best_reason(snap.get(r.candidate_account_id, {}))) for r in ranked],
        {},
        size=len(ranked),
    )
    if waiting:  # the whole pool was one person: still show them
        out.append(Shelf(key="picked", items=waiting, see_all={}))
    return out

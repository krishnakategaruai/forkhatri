"""Discovery — public interface.

`/MODULE-ARCHITECTURE-STANDARD.md` §3: this is the only way other components
reach Discovery state.

Implements:
  * FR021 / TR021 — searchable is independent of any viewer's own visibility.
  * FR026 / TR026 — DEC-V1-002's fixed, versioned ranking weights.
  * FR027 / TR027 — the discoverability gate is `profile.is_discoverable()`,
    never re-derived here (the TR003/TR027 non-divergence contract).

Interim, deliberate deviation from this package's own header comment
("synced via domain events — never a live cross-schema query"): TR069's
outbox dispatcher does not exist yet (tracked separately, `FOUNDATIONS`
in `mangaly-web/lib/requirements.ts`), so `refresh_index()` is called
SYNCHRONOUSLY from `profile.interface`'s own create/update functions, in the
same transaction, rather than by an event consumer that cannot run yet. This
is the same interim-real-thing pattern `components/profile/storage.py`
already uses for Object Storage (a real local-disk implementation standing
in for the eventual one, not a mock) — when the dispatcher is built, the
call site moves from `profile.interface` to a consumer, but `refresh_index()`
itself does not change.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.discovery.models import DiscoveryProfileIndex
from app.components.profile.models import FieldState
from app.config.ranking_weights import (
    EVIDENCE_COMPLETENESS_WEIGHT,
    LIFESTYLE_COMPATIBILITY_WEIGHT,
    LOCALITY_RELOCATION_WEIGHT,
    MAX_SAME_BRACKET_RUN,
    PARTNER_PREFERENCE_WEIGHT,
    SCORE_BRACKETS,
)

__all__ = ["SearchResult", "Snippet", "get_snapshot", "get_snippet", "refresh_index", "search"]


@dataclass(frozen=True, slots=True)
class Snippet:
    """Same deliberately-limited shape as `SearchResult` (no name/photo —
    see its own docstring), for exactly one account rather than a ranked
    list. Used wherever a screen needs to identify a candidate who has not
    yet granted `candidate_info` visibility: an incoming connection
    request's sender, or the other party in a conversation list — both
    already have a `searchable` Discovery row (a live connection or
    request cannot exist with someone who was never discoverable... in
    principle; a `None` result is handled as "nothing to show" rather than
    an error either way, since a candidate can toggle discoverability off
    after a connection already exists)."""

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


_CategoryAttrs = dict[str, tuple[FieldState, "dict | list | str | int | float | bool | None"]]


def _attr_value(category: _CategoryAttrs | None, key: str) -> object | None:
    """`category` is a `profile.get_category()` result: `{key: (state, value)}`.
    Only a `value` state's value counts — a declined or unset field
    contributes nothing to the index, exactly as it contributes nothing to
    completeness (`components/profile/interface.py`'s own convention)."""
    if not category or key not in category:
        return None
    state, value = category[key]
    return value if state is FieldState.VALUE else None


async def refresh_index(session: AsyncSession, *, account_id: UUID) -> None:
    """[FR021/FR026/FR027] Recompute this candidate's Discovery row from
    their current profile state. Called synchronously by `profile.interface`
    after any write that could change discoverability or ranking input — see
    this module's docstring for why that is a direct call rather than an
    event-consumer for now.
    """
    # Imported here, not at module load, to avoid a circular import: `profile`
    # does not import `discovery` at module scope either (it calls this
    # function from inside its own already-running request), so the cycle
    # only exists at call time, never at import time.
    from app.components.profile import interface as profile_module

    own_profile = await profile_module.get_own_profile(session, account_id=account_id)
    if own_profile is None:
        return

    searchable = await profile_module.is_discoverable(session, profile_id=own_profile.id)

    education = await profile_module.get_category(
        session, account_id=account_id, category="education"
    )
    profession = await profile_module.get_category(
        session, account_id=account_id, category="profession"
    )
    relocation = await profile_module.get_category(
        session, account_id=account_id, category="relocation"
    )
    partner_pref = await profile_module.get_category(
        session, account_id=account_id, category="partner_preference"
    )
    lifestyle = await profile_module.get_category(
        session, account_id=account_id, category="lifestyle"
    )
    marital = await profile_module.get_category(
        session, account_id=account_id, category="marital_history"
    )
    completeness = await profile_module.completeness(session, account_id=account_id)

    education_level = _attr_value(education, "highest_education_level")
    profession_value = _attr_value(profession, "occupation")
    relocation_willingness = _attr_value(relocation, "relocation_willingness")

    evidence_completeness = (
        completeness.enhanced_filled_categories / completeness.enhanced_total_categories
        if completeness and completeness.enhanced_total_categories
        else 0.0
    )

    snapshot = {
        "locality": own_profile.city_locality,
        "relocation_willingness": relocation_willingness,
        "partner_age_range": _attr_value(partner_pref, "age_range"),
        "partner_locality": _attr_value(partner_pref, "locality"),
        "lifestyle_diet": _attr_value(lifestyle, "diet"),
        "gender": own_profile.gender,
        "looking_for": _attr_value(partner_pref, "looking_for"),
        "marital_status": _attr_value(marital, "marital_status"),
        "date_of_birth": own_profile.date_of_birth.isoformat(),
        "education_level": education_level,
        "evidence_completeness": evidence_completeness,
    }

    search_fields = (
        own_profile.city_locality,
        education_level,
        profession_value,
        relocation_willingness,
    )
    search_text = " ".join(str(v) for v in search_fields if v)

    await session.execute(
        text(
            """
            INSERT INTO mangaly_discovery.discovery_profile_index
                (profile_id, searchable, locality, relocation_willingness,
                 education_level, profession, search_vector, ranking_input_snapshot, updated_at)
            VALUES
                (:profile_id, :searchable, :locality, :relocation_willingness,
                 :education_level, :profession, to_tsvector('english', :search_text),
                 CAST(:snapshot AS jsonb), now())
            ON CONFLICT (profile_id) DO UPDATE SET
                searchable = EXCLUDED.searchable,
                locality = EXCLUDED.locality,
                relocation_willingness = EXCLUDED.relocation_willingness,
                education_level = EXCLUDED.education_level,
                profession = EXCLUDED.profession,
                search_vector = EXCLUDED.search_vector,
                ranking_input_snapshot = EXCLUDED.ranking_input_snapshot,
                updated_at = now()
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
        },
    )


def _score(viewer: dict, candidate: dict) -> float:
    """[TR026/DEC-V1-002] The fixed weighted formula. `POPULARITY_WEIGHT` is
    0.0 by construction (`config/ranking_weights.py`) — no term below reads
    any engagement/view metric, and none exists in `ranking_input_snapshot`
    to read even if a future edit tried.

    Simplified matching rules (documented, not hidden): locality match is
    exact-string-equal OR the candidate has indicated general relocation
    willingness; partner-preference match is two-way — the viewer's stated
    preferred locality and age range checked against the candidate, AND the
    candidate's own stated preferences checked against the viewer, every
    checkable preference counting equally (a "2-way match", `reference.md`;
    BR06's reciprocal-interest framing), so someone who fits you but not what
    they are looking for no longer ranks as highly as someone who fits both
    ways; lifestyle overlap checks
    a single shared attribute (diet) as a representative signal rather than
    a full compatibility model (FR033/034's assessment mechanism, out of
    scope); evidence completeness reuses the same enhanced-tier ratio
    `completeness()` already computes, so this can never diverge from what
    the candidate's own completeness screen shows them.
    """
    locality_score = 0.0
    if viewer.get("locality") and candidate.get("locality") == viewer.get("locality"):
        locality_score = 1.0
    elif candidate.get("relocation_willingness") == "yes":
        locality_score = 0.5

    checks = _preference_checks(viewer, candidate) + _preference_checks(candidate, viewer)
    partner_pref_score = sum(checks) / len(checks) if checks else 0.0

    viewer_diet = viewer.get("lifestyle_diet")
    lifestyle_score = 1.0 if viewer_diet and viewer_diet == candidate.get("lifestyle_diet") else 0.0

    evidence_score = float(candidate.get("evidence_completeness") or 0.0)

    return (
        locality_score * LOCALITY_RELOCATION_WEIGHT
        + partner_pref_score * PARTNER_PREFERENCE_WEIGHT
        + lifestyle_score * LIFESTYLE_COMPATIBILITY_WEIGHT
        + evidence_score * EVIDENCE_COMPLETENESS_WEIGHT
    )


def _preference_checks(seeker: dict, other: dict) -> list[float]:
    """One direction of the partner-preference term: each preference the
    seeker stated that can be checked against the other person scores 1 or 0
    (preferred locality, preferred age range). Unstated preferences add
    nothing, so an empty preference never counts against anyone."""
    checks: list[float] = []
    preferred_locality = seeker.get("partner_locality")
    if preferred_locality and other.get("locality"):
        wanted = str(preferred_locality).strip().lower()
        checks.append(1.0 if wanted in str(other["locality"]).strip().lower() else 0.0)
    age_range = seeker.get("partner_age_range")
    other_age = _age_years(other.get("date_of_birth"))
    if isinstance(age_range, dict) and other_age is not None:
        low, high = age_range.get("min"), age_range.get("max")
        if low or high:
            inside = (low or 0) <= other_age <= (high or 200)
            checks.append(1.0 if inside else 0.0)
    return checks


def _score_bracket(score: float) -> int:
    """Which of `SCORE_BRACKETS` equal bands of the 0–1 score a result falls in."""
    return min(int(score * SCORE_BRACKETS), SCORE_BRACKETS - 1)


def _diversify[T](ranked: list[T], *, score_of: Callable[[T], float]) -> list[T]:
    """[TR026/DEC-V1-002] Diversity re-rank after the weighted sort: no more
    than `MAX_SAME_BRACKET_RUN` results in a row share one score bracket.
    When the next result would make the run too long, the highest-ranked
    result from a different bracket moves up instead, so adjacent-quality
    matches are seen rather than the top band taking every slot. If only one
    bracket is left, the order simply continues — nothing is dropped, and the
    order within each bracket never changes."""
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
    """The caller's own ranking snapshot — used by `search()` to score
    candidates relative to the viewer, and available standalone for a
    `Compatibility` explanation to read the same numbers it shows the
    viewer, rather than re-deriving them."""
    row = await session.get(DiscoveryProfileIndex, account_id)
    return row.ranking_input_snapshot if row else None


async def get_snippet(session: AsyncSession, *, account_id: UUID) -> Snippet | None:
    """[FR021] One candidate's demographic snippet — the same shape
    `search()` already exposes to any viewer, used wherever a screen must
    identify a not-yet-connected candidate (e.g. a pending connection
    request's sender) without a raw account id being the only option. `None`
    when the row is not `searchable` and the caller isn't its owner (RLS),
    which a caller should treat as "nothing to show," not an error.
    """
    row = await session.get(DiscoveryProfileIndex, account_id)
    if row is None:
        return None
    return Snippet(
        locality=row.locality, education_level=row.education_level, profession=row.profession
    )


async def search(
    session: AsyncSession,
    *,
    viewer_account_id: UUID,
    for_candidate_account_id: UUID | None = None,
    filters: DiscoverFilters | None = None,
    page: int = 1,
    page_size: int = 20,
) -> list[SearchResult]:
    """[FR021/FR026] Every result is `searchable = true` — TR021's own
    "visibility ≠ searchability" separation means this function decides who
    is FOUND; what a caller may then SEE of a found profile is a completely
    separate question, resolved later by the Authorization Engine, not here.
    """
    ranking_account_id = viewer_account_id
    if for_candidate_account_id is not None:
        await authorize_family_viewer(
            session,
            viewer_account_id=viewer_account_id,
            candidate_account_id=for_candidate_account_id,
        )
        ranking_account_id = for_candidate_account_id
    viewer_snapshot = await get_snapshot(session, account_id=ranking_account_id) or {}
    if not viewer_snapshot.get("looking_for"):
        raise LookingForMissing

    stmt = select(DiscoveryProfileIndex).where(
        DiscoveryProfileIndex.searchable.is_(True),
        DiscoveryProfileIndex.profile_id.not_in({viewer_account_id, ranking_account_id}),
    )
    rows = [
        row
        for row in (await session.execute(stmt)).scalars().all()
        if _looking_for_each_other(viewer_snapshot, row.ranking_input_snapshot or {})
        and _passes_filters(viewer_snapshot, row, filters)
    ]

    scored = [(row, _score(viewer_snapshot, row.ranking_input_snapshot or {})) for row in rows]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    scored = _diversify(scored, score_of=lambda pair: pair[1])

    start = (page - 1) * page_size
    page_slice = scored[start : start + page_size]
    return [
        SearchResult(
            candidate_account_id=row.profile_id,
            score=score,
            locality=row.locality,
            education_level=row.education_level,
            profession=row.profession,
        )
        for row, score in page_slice
    ]


async def authorize_family_viewer(
    session: AsyncSession, *, viewer_account_id: UUID, candidate_account_id: UUID
) -> None:
    """[FR013] A Home Circle member may search, and read match reasons, for the
    candidate they help, ranked against that candidate's own preferences, only
    while they hold `family_info` on that candidate. Raises `AuthorizationDenied`."""
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


@dataclass(frozen=True, slots=True)
class DiscoveryCard:
    photo_url: str | None
    age: int | None


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


class LookingForMissing(Exception):
    """The person matches are ranked for has not said who they are looking for."""


_GENDER_LOOKED_FOR = {"bride": "female", "groom": "male"}


def _looking_for_each_other(seeker: dict, candidate: dict) -> bool:
    """A match only when the candidate is who the seeker is looking for AND the
    seeker is who the candidate is looking for, both from their own
    "looking for" answers. Anyone who has not answered is not matched."""
    seeker_wants = _GENDER_LOOKED_FOR.get(str(seeker.get("looking_for") or ""))
    candidate_wants = _GENDER_LOOKED_FOR.get(str(candidate.get("looking_for") or ""))
    return bool(
        seeker_wants
        and candidate_wants
        and candidate.get("gender") == seeker_wants
        and seeker.get("gender") == candidate_wants
    )


@dataclass(frozen=True, slots=True)
class DiscoverFilters:
    """[UX16] Filters a member sets on Discover. They narrow the engine's matches
    and never change the ranking."""

    nearby: str | None = None  # "city" or "state", relative to the seeker's own locality
    age_min: int | None = None
    age_max: int | None = None
    marital_status: tuple[str, ...] = ()
    education: tuple[str, ...] = ()
    diet: tuple[str, ...] = ()
    open_to_relocate: bool = False


def _place(locality: str | None, part: str) -> str:
    pieces = [p.strip().lower() for p in (locality or "").split(",") if p.strip()]
    if not pieces:
        return ""
    return pieces[0] if part == "city" else pieces[-1]


def _age_years(date_of_birth: str | None) -> int | None:
    if not date_of_birth:
        return None
    born = date.fromisoformat(date_of_birth)
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def _passes_filters(
    seeker: dict, row: DiscoveryProfileIndex, filters: DiscoverFilters | None
) -> bool:
    if filters is None:
        return True
    candidate = row.ranking_input_snapshot or {}
    if filters.nearby:
        mine = _place(seeker.get("locality"), filters.nearby)
        if not mine or _place(row.locality, filters.nearby) != mine:
            return False
    if filters.age_min is not None or filters.age_max is not None:
        age = _age_years(candidate.get("date_of_birth"))
        if age is None:
            return False
        if filters.age_min is not None and age < filters.age_min:
            return False
        if filters.age_max is not None and age > filters.age_max:
            return False
    if filters.marital_status and candidate.get("marital_status") not in filters.marital_status:
        return False
    if filters.education and row.education_level not in filters.education:
        return False
    if filters.diet and candidate.get("lifestyle_diet") not in filters.diet:
        return False
    return not (
        filters.open_to_relocate and row.relocation_willingness not in ("yes", "open_to_discussion")
    )

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
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.discovery.models import DiscoveryProfileIndex
from app.components.profile.models import FieldState
from app.config.ranking_weights import (
    EVIDENCE_COMPLETENESS_WEIGHT,
    LIFESTYLE_COMPATIBILITY_WEIGHT,
    LOCALITY_RELOCATION_WEIGHT,
    PARTNER_PREFERENCE_WEIGHT,
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
    """Deliberately carries only the fields `discovery_profile_index` itself
    stores (locality/education/profession) — never name or photo. Those live
    in `mangaly_profile.profile`, which is not readable by a stranger who
    has not yet connected (`profile_owner_or_granted`'s RLS), and Discovery
    is documented as never joining live against that table anyway. A search
    result card is therefore a demographic snippet, not a preview of the
    real profile — deliberately, not an oversight: showing name/photo to
    any searcher would itself be the "public teaser profile" the product's
    own vision explicitly rejects."""

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
    willingness; partner-preference match checks the viewer's stated
    preferred locality against the candidate's own locality (age-range
    matching needs a birth date this snapshot does not carry and is a
    reasonable, recorded scope cut for this pass); lifestyle overlap checks
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

    partner_pref_score = 0.0
    preferred_locality = viewer.get("partner_locality")
    if preferred_locality and candidate.get("locality"):
        if str(preferred_locality).strip().lower() in str(candidate["locality"]).strip().lower():
            partner_pref_score = 1.0

    viewer_diet = viewer.get("lifestyle_diet")
    lifestyle_score = 1.0 if viewer_diet and viewer_diet == candidate.get("lifestyle_diet") else 0.0

    evidence_score = float(candidate.get("evidence_completeness") or 0.0)

    return (
        locality_score * LOCALITY_RELOCATION_WEIGHT
        + partner_pref_score * PARTNER_PREFERENCE_WEIGHT
        + lifestyle_score * LIFESTYLE_COMPATIBILITY_WEIGHT
        + evidence_score * EVIDENCE_COMPLETENESS_WEIGHT
    )


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
    locality: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> list[SearchResult]:
    """[FR021/FR026] Every result is `searchable = true` — TR021's own
    "visibility ≠ searchability" separation means this function decides who
    is FOUND; what a caller may then SEE of a found profile is a completely
    separate question, resolved later by the Authorization Engine, not here.
    """
    viewer_snapshot = await get_snapshot(session, account_id=viewer_account_id) or {}

    stmt = select(DiscoveryProfileIndex).where(
        DiscoveryProfileIndex.searchable.is_(True),
        DiscoveryProfileIndex.profile_id != viewer_account_id,
    )
    if locality:
        stmt = stmt.where(DiscoveryProfileIndex.locality.ilike(f"%{locality}%"))
    rows = (await session.execute(stmt)).scalars().all()

    scored = [(row, _score(viewer_snapshot, row.ranking_input_snapshot or {})) for row in rows]
    scored.sort(key=lambda pair: pair[1], reverse=True)

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

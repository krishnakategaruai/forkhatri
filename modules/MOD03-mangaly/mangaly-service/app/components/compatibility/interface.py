"""Compatibility — public interface.

`/MODULE-ARCHITECTURE-STANDARD.md` §3: this is the only way other components
reach Compatibility state.

Implements:
  * FR030 / TR030 — explainable, non-score compatibility reasons: 2-4
    concrete, templated sentences, never a numeric score or percentage.
  * FR031 / TR031 — every reason carries a `source: fact | inference` tag.

Deliberately out of this pass's scope: FR033/FR034's optional compatibility-
assessment questionnaire and horoscope opt-in (`mangaly_compatibility
.assessment_response` / `.horoscope`). FR030's own research finding is that
core compatibility has ZERO dependency on either — this module reads only
already-built `profile_attribute` data, proving that independence rather
than asserting it. No new schema/table is needed for this pass at all.

Templated, not generative (TR030's own mechanism requirement): every
sentence below is a fixed Python string with values interpolated from
structured data — there is no code path that could phrase a claim about
character, honesty, or marriage success (FR031's banned-claim rule is
enforced by this file structurally having no such template, not by a
runtime filter that could miss one).

[Bug found live, 2026-09-14] The original version of this function read the
CANDIDATE's side of every comparison through `profile.interface.get_category()`
/`get_own_profile()` — the same `profile_attribute`/`profile` tables RLS
(`profile_owner_or_granted`) restricts to the owner or an existing
`candidate_info` grant. Discover's whole point is showing "why this match"
to a viewer who has NOT connected yet (FR043: full compatibility context
visible to the RECIPIENT before they decide), so that call was silently
blocked by RLS for every not-yet-connected pair — `explain()` returned an
empty list unconditionally, and the empty-list-is-a-valid-answer design
(FR030's own "never fabricate" outcome) meant this looked like "nothing in
common" for candidates who in fact matched on every field. `discovery.
get_snapshot()` already exists for exactly this — its own docstring says
it is "available standalone for a Compatibility explanation to read the
same numbers it shows the viewer" — and reads `discovery_profile_index`,
the table Discovery deliberately keeps safe to read across accounts before
any connection exists (the same table `search()` already reads for every
other candidate in one query). Switching both sides of every comparison to
snapshot reads fixes the bug without touching RLS at all.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.components.compatibility.engine import breakdown, distance_km, fails_must, label_for, pair_score
from app.components.compatibility.understand import (
    Understood,
    clean_items,
    clean_scales,
    understand,
)
from app.i18n import translate

# [DEC-V1-031] The AI matching engine and the matchmaker's reading of a
# family's own words are part of this component's public surface: Discovery
# ranks with `pair_score`/`fails_must`, the profile routes call `understand`.
__all__ = [
    "Reason",
    "Understood",
    "breakdown",
    "clean_items",
    "fit_for",
    "clean_scales",
    "distance_km",
    "explain",
    "fails_must",
    "label_for",
    "pair_score",
    "understand",
]


@dataclass(frozen=True, slots=True)
class Reason:
    text: str
    source: Literal["fact", "inference"]


async def explain(
    session: AsyncSession,
    *,
    viewer_account_id: UUID,
    candidate_account_id: UUID,
    for_candidate_account_id: UUID | None = None,
    lang: str | None = None,
) -> list[Reason]:
    """[FR030/FR031] 2-4 concrete reasons, or an empty list — never a
    fabricated one when nothing genuinely matches (FR030's own explicit
    failure outcome). Reads both parties' `discovery_profile_index.
    ranking_input_snapshot` — the pre-connection-safe snapshot Discovery
    already maintains for ranking, not the RLS-protected `profile_attribute`
    table directly (see this module's docstring for why that matters: this
    function must work for a viewer who has not connected with the
    candidate yet, and only the snapshot is readable in that state).
    """
    from app.components.discovery import interface as discovery_module

    ranking_account_id = viewer_account_id
    if for_candidate_account_id is not None:
        await discovery_module.authorize_family_viewer(
            session,
            viewer_account_id=viewer_account_id,
            candidate_account_id=for_candidate_account_id,
        )
        ranking_account_id = for_candidate_account_id
    viewer = await discovery_module.get_snapshot(session, account_id=ranking_account_id) or {}
    candidate = await discovery_module.get_snapshot(session, account_id=candidate_account_id) or {}

    reasons: list[Reason] = []

    def label(enum_name: str, raw: object) -> str:
        """A member-readable form of a stored enum. The stored token is the
        fallback, so an enum added without a label degrades to something
        odd-looking rather than to a crash — and is obvious in review."""
        key = f"discovery.value.{enum_name}.{raw}"
        text = translate(key, lang)
        return str(raw) if text == key else text

    def agree(field: str) -> object | None:
        """The shared value when both sides answered the same, else None."""
        mine, theirs = viewer.get(field), candidate.get(field)
        return theirs if mine and theirs and mine == theirs else None

    if (relo := agree("relocation_willingness")) is not None:
        reasons.append(
            Reason(
                text=translate(
                    "discovery.reason.relocation",
                    lang,
                    value=label("relocation_willingness", relo),
                ),
                source="fact",
            )
        )

    if (diet := agree("lifestyle_diet")) is not None:
        reasons.append(
            Reason(
                text=translate("discovery.reason.diet", lang, value=label("diet", diet)),
                source="fact",
            )
        )

    if (edu := agree("education_level")) is not None:
        reasons.append(
            Reason(
                text=translate(
                    "discovery.reason.education", lang, value=label("education_level", edu)
                ),
                source="fact",
            )
        )

    preferred_locality = viewer.get("partner_locality")
    candidate_locality = candidate.get("locality")
    if preferred_locality and candidate_locality:
        if str(preferred_locality).strip().lower() in str(candidate_locality).strip().lower():
            reasons.append(
                Reason(
                    text=translate(
                        "discovery.reason.locality", lang, locality=candidate_locality
                    ),
                    source="inference",
                )
            )

    return reasons[:4]


async def fit_for(
    session: AsyncSession,
    *,
    viewer_account_id: UUID,
    candidate_account_id: UUID,
    for_candidate_account_id: UUID | None = None,
) -> dict:
    """[DEC-V1-031] The profile page's "How you fit each other": the engine's
    word for the pair and `breakdown()`, read from the same pre-connection-safe
    snapshots `explain()` reads. A circle member reading for their candidate
    sees it from the candidate's seat."""
    from app.components.discovery import interface as discovery_module

    seat = viewer_account_id
    if for_candidate_account_id is not None:
        await discovery_module.authorize_family_viewer(
            session,
            viewer_account_id=viewer_account_id,
            candidate_account_id=for_candidate_account_id,
        )
        seat = for_candidate_account_id
    mine = await discovery_module.get_snapshot(session, account_id=seat) or {}
    theirs = await discovery_module.get_snapshot(session, account_id=candidate_account_id) or {}
    if not mine or not theirs:
        return {"label": None, "yours": [], "theirs_met": []}
    return {"label": label_for(pair_score(mine, theirs)), **breakdown(mine, theirs)}

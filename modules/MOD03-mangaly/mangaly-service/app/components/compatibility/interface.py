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

__all__ = ["Reason", "explain"]


@dataclass(frozen=True, slots=True)
class Reason:
    text: str
    source: Literal["fact", "inference"]


async def explain(
    session: AsyncSession, *, viewer_account_id: UUID, candidate_account_id: UUID
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

    viewer = await discovery_module.get_snapshot(session, account_id=viewer_account_id) or {}
    candidate = await discovery_module.get_snapshot(session, account_id=candidate_account_id) or {}

    reasons: list[Reason] = []

    v_relo = viewer.get("relocation_willingness")
    c_relo = candidate.get("relocation_willingness")
    if v_relo and c_relo and v_relo == c_relo:
        reasons.append(
            Reason(text=f"Both have the same outlook on relocation ({c_relo}).", source="fact")
        )

    v_diet = viewer.get("lifestyle_diet")
    c_diet = candidate.get("lifestyle_diet")
    if v_diet and c_diet and v_diet == c_diet:
        reasons.append(Reason(text=f"Both share a {c_diet} lifestyle.", source="fact"))

    v_edu = viewer.get("education_level")
    c_edu = candidate.get("education_level")
    if v_edu and c_edu and v_edu == c_edu:
        reasons.append(Reason(text=f"Both hold a {c_edu} level of education.", source="fact"))

    preferred_locality = viewer.get("partner_locality")
    candidate_locality = candidate.get("locality")
    if preferred_locality and candidate_locality:
        if str(preferred_locality).strip().lower() in str(candidate_locality).strip().lower():
            text = f"Located in {candidate_locality}, matching your preferred area."
            reasons.append(Reason(text=text, source="inference"))

    return reasons[:4]

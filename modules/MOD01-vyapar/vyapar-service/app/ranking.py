# [TR019] Canonical eligibility-then-ranking function with signal allow-list
# (FR19) — the module's single most explicit anti-bias control. Every
# ranked-list endpoint in this codebase (TR015 listings search, TR018
# opportunity feed, TR020 "why this?", TR055 opportunity detail) calls THIS
# module, never a second, independently-coded scorer — closing the exact
# gap `discovery.py`'s IMP09 Decision flagged (an interim listings-only
# scorer used ahead of FR19 existing).
# Approach: `RankingSignals` is a typed struct whose fields are EXACTLY the
# FR19 allow-list (capability/intent/location/timing/value/experience/
# freshness/trust fit) — a structural absence: there is no field for a
# sensitive attribute, community status, account age, paid status,
# popularity, or report signal, so no future change can pass one in without
# first changing this one reviewable type. Hard-constraint exclusion
# (non-Active state, blocks, radius-when-on-site, eligibility mismatch)
# happens in each caller's own repository-layer query/filter BEFORE this
# module ever sees a candidate — this module only scores and diversifies
# what already passed. Weights are a plain dict (a stand-in for the
# `config` table TR019 names — no live config-admin UI exists yet this
# session; see Decisions) with safe defaults on any missing key.
# Traces to: FR19, FR20, TR019, TR020, SP019, SP020
from __future__ import annotations

from pydantic import BaseModel

# [SP019 — this file's own most load-bearing rule] the ONLY allowed scoring
# inputs. Adding a field here for a sensitive attribute, community status,
# account age, paid status, popularity, or report signal is a Critical-
# severity defect at code review, not a style nit — SP019's own text says
# so explicitly.
class RankingSignals(BaseModel):
    capability_fit: float = 0.0
    intent_fit: float = 0.0
    location_fit: float = 0.0
    timing_fit: float = 0.0
    value_fit: float = 0.0
    experience_fit: float = 0.0
    freshness_fit: float = 0.0
    trust_fit: float = 0.0


DEFAULT_WEIGHTS: dict[str, float] = {
    "capability_fit": 3.0,
    "intent_fit": 2.0,
    "location_fit": 2.0,
    "timing_fit": 1.0,
    "value_fit": 1.0,
    "experience_fit": 1.0,
    "freshness_fit": 1.5,
    "trust_fit": 1.5,
}

# [Product-owner i18n rule, 2026-09-15] This module used to hold a
# `SIGNAL_PHRASES` dict of pre-baked English phrases returned directly in
# API responses — a hardcoded-English leak into member-facing JSON.
# `top_signals()` now returns the raw signal KEY (e.g. "capability_fit")
# unchanged; every caller (discovery.py, feed.py) is responsible for
# translating via `translate('ranking.signal.'+key, lang)` before it
# reaches a member. One source of truth for WHICH signals mattered still
# holds — only the language-specific text moved to the i18n catalogs
# (app/i18n/locales/<lang>/ranking.json), so score and explanation can
# never drift (TR020's own anti-drift requirement) in any language.


def score(signals: RankingSignals, weights: dict[str, float] | None = None) -> float:
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    return sum(getattr(signals, field) * w.get(field, DEFAULT_WEIGHTS[field]) for field in RankingSignals.model_fields)


def top_signal_keys(signals: RankingSignals, limit: int = 3) -> list[str]:
    """[FR20] Top-N contributing signal KEYS by (weighted) magnitude — reads
    the exact same signals `score()` used, never a separate explanation
    model. Callers translate each key themselves (see module note above)."""
    weighted = [
        (getattr(signals, f) * DEFAULT_WEIGHTS[f], f) for f in RankingSignals.model_fields if getattr(signals, f) > 0
    ]
    weighted.sort(reverse=True)
    return [f for _, f in weighted[:limit]]


def diversify(items: list, provider_key, type_key, max_consecutive: int = 3) -> list:
    """[FR19] No more than `max_consecutive` results in a row share the
    same provider or type — a stable-ish reordering that keeps overall rank
    order as intact as possible while enforcing the cap."""
    result: list = []
    pending = list(items)
    while pending:
        placed = False
        for i, item in enumerate(pending):
            tail = result[-max_consecutive:]
            same_provider = len(tail) == max_consecutive and all(provider_key(t) == provider_key(item) for t in tail)
            same_type = len(tail) == max_consecutive and all(type_key(t) == type_key(item) for t in tail)
            if not (same_provider or same_type):
                result.append(pending.pop(i))
                placed = True
                break
        if not placed:
            # every remaining item would violate the cap — place the best
            # remaining one anyway rather than drop data.
            result.append(pending.pop(0))
    return result

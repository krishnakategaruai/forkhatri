"""DEC-V1-002's fixed, versioned Discovery ranking weights, as configuration.

# [TR026/TR028/FR028] A named list, not a rule each call site re-derives, and
# never popularity: `POPULARITY` is defined at 0.0 and no code path anywhere
# reads an engagement/view metric into this — the constant exists so a future
# read of this file states that omission explicitly rather than leaving a
# silent gap someone might "helpfully" fill in later.
# Traces to: TR026, TR028, FR026, FR028, DEC-V1-002.
"""

from __future__ import annotations

from typing import Final

LOCALITY_RELOCATION_WEIGHT: Final[float] = 0.30
PARTNER_PREFERENCE_WEIGHT: Final[float] = 0.30
LIFESTYLE_COMPATIBILITY_WEIGHT: Final[float] = 0.20
EVIDENCE_COMPLETENESS_WEIGHT: Final[float] = 0.20
POPULARITY_WEIGHT: Final[float] = 0.0  # by construction — never read from anywhere

assert (
    abs(
        LOCALITY_RELOCATION_WEIGHT
        + PARTNER_PREFERENCE_WEIGHT
        + LIFESTYLE_COMPATIBILITY_WEIGHT
        + EVIDENCE_COMPLETENESS_WEIGHT
        + POPULARITY_WEIGHT
        - 1.0
    )
    < 1e-9
), "DEC-V1-002 weights must sum to 1.0"

RANKING_WEIGHTS_VERSION: Final[str] = "DEC-V1-002.v1"

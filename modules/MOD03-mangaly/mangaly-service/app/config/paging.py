"""On-call paging trigger contract for Tier 3/4 safety cases.

# [TR065/DEC-V1-009/DEC-V1-011] The paging *trigger contract* is fixed
# configuration; only the vendor call itself is pluggable.
# Approach: CODING-GUIDE.md §7 is explicit that "the pipeline exists" is not the
# same as "the pipeline's exits are reachable" — a graduated-response state
# machine with no wired paging exit leaves the most legally consequential path
# unbuilt behind correct-looking code. So the *trigger* (auto-fire on Tier 3/4
# classification, never queued) is declared here as data, independent of whether
# the PagerDuty client is wired yet, which means the Safety component can be
# built and tested against a real contract rather than a TODO.
# NOTE: this file declares the contract only. The Safety/Operations components
# that fire it are NOT implemented in this pass — see 09-implementation.md's
# honest "what remains" list.
# Traces to: TR065, SP065, DEC-V1-009, DEC-V1-011.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.config.thresholds import SafetyTier

# DEC-V1-009: Tier 3 and Tier 4 fire the pager. Tier 1/2 never do — they route
# to the ordinary case queue. This tuple, not an `if tier >= 3` scattered across
# call sites, is the authority.
PAGING_TRIGGER_TIERS: Final[tuple[SafetyTier, ...]] = (SafetyTier.HIGH, SafetyTier.CRITICAL)

# SP-Class E: measured wall-clock from classification event to the mechanism
# firing, independent of human pickup.
PAGING_TRIGGER_FIRE_P99_SECONDS: Final[int] = 60
CSAM_PACKET_DISPATCH_P99_SECONDS: Final[int] = 300


@dataclass(frozen=True, slots=True)
class PagingTrigger:
    """The event a Tier 3/4 classification must produce, vendor-independently."""

    case_id: str
    tier: SafetyTier
    dedup_key: str
    summary: str  # [SP098-adjacent] event type + reference only — never content.

    def __post_init__(self) -> None:
        if self.tier not in PAGING_TRIGGER_TIERS:
            raise ValueError(
                f"Tier {self.tier} does not page per DEC-V1-009; "
                f"only {[t.name for t in PAGING_TRIGGER_TIERS]} do."
            )

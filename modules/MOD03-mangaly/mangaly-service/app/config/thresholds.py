"""Versioned, operator-changeable thresholds.

# [TR041/DEC-V1-005] The marriageable-age gate is a configured, versioned
# setting — never a literal inside business logic.
# Approach: DEC-V1-005 resolved the value (21 for men / 18 for women, the
# Prohibition of Child Marriage Act 2006 figures, unchanged by Uttarakhand's
# 2025 UCC) but explicitly required it be stored as an admin-configurable,
# versioned setting so a pending amendment becomes a config change rather than
# a redeploy. This module is therefore the ONLY place the numbers appear, and
# they are carried with a `version` and `effective_from` so a change is
# auditable rather than silently swapped.
# Traces to: TR041, DEC-V1-005, CODING-GUIDE.md §5.

# [TR068/DEC-V1-006] Safety severity tiers are consumed as fixed configuration,
# not re-derived per component.
# Approach: DEC-V1-006 derived every SLA from the IT Rules 2021 (as amended
# 10 Feb 2026) legal ceilings — 24 h acknowledgment, 36 h resolution, 2 h for
# nudity/impersonation — rather than inventing round numbers. Exposing them as
# one frozen mapping means Safety, Operations, and Notification all read the
# same table; a component that hardcodes "24 hours" has bypassed this file and
# is a defect.
# Traces to: TR065, TR068, SP065, SP068, DEC-V1-006.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from enum import Enum
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class VersionedSetting:
    """A threshold value that carries when it took effect and why."""

    version: int
    effective_from: date
    basis: str


# --- TR041 / DEC-V1-005: marriageable-age gate --------------------------------

MARRIAGEABLE_AGE_SETTING = VersionedSetting(
    version=1,
    effective_from=date(2026, 1, 1),
    basis=(
        "Prohibition of Child Marriage Act, 2006 (21 male / 18 female); "
        "Uttarakhand UCC in force Jan 2025 uses identical figures. The 2021 "
        "amendment bill raising the female threshold to 21 is NOT enacted as of "
        "DEC-V1-005's research date — bump `version` and add a row here if it is."
    ),
)

# Keyed on the same gender vocabulary `mangaly_profile.profile.gender` stores.
# A gender not present here falls back to MARRIAGEABLE_AGE_DEFAULT_YEARS, which
# is the stricter of the two figures — an unrecognised value must never open the
# gate wider than the law does.
MARRIAGEABLE_AGE_YEARS: Mapping[str, int] = MappingProxyType({"male": 21, "female": 18})
MARRIAGEABLE_AGE_DEFAULT_YEARS = 21


# --- TR068 / DEC-V1-006: safety severity taxonomy -----------------------------


class SafetyTier(int, Enum):
    """DEC-V1-006's four tiers. The integer value is the tier number."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass(frozen=True, slots=True)
class SafetySla:
    """Response commitments for one severity tier, in hours (None = no human SLA)."""

    acknowledge_within_hours: float | None
    resolve_within_hours: float | None
    immediate_block: bool
    pages_on_call: bool
    legal_basis: str


SAFETY_SLAS: Mapping[SafetyTier, SafetySla] = MappingProxyType(
    {
        SafetyTier.LOW: SafetySla(
            acknowledge_within_hours=None,
            resolve_within_hours=None,
            immediate_block=False,
            pages_on_call=False,
            legal_basis=(
                "No statutory SLA for an unreported automated nudge; a filed report "
                "reclassifies immediately into the grievance-acknowledgment SLA."
            ),
        ),
        SafetyTier.MEDIUM: SafetySla(
            acknowledge_within_hours=24,
            resolve_within_hours=36,
            immediate_block=False,
            pages_on_call=False,
            legal_basis=(
                "IT Rules 2021 (2026-amended): 24 h acknowledgment, "
                "36 h resolution ceilings."
            ),
        ),
        SafetyTier.HIGH: SafetySla(
            # 2 h applies to the nudity/impersonation subset (the legal ceiling for
            # that category); 12 h to the rest — deliberately faster than the 36 h
            # general ceiling, per DEC-V1-006's TSPA-practice rationale.
            acknowledge_within_hours=2,
            resolve_within_hours=12,
            immediate_block=True,
            pages_on_call=False,
            legal_basis=(
                "IT Rules 2021 2 h nudity/impersonation ceiling + "
                "TSPA severity-tiered practice."
            ),
        ),
        SafetyTier.CRITICAL: SafetySla(
            acknowledge_within_hours=0,
            resolve_within_hours=0,
            immediate_block=True,
            pages_on_call=True,
            legal_basis=(
                "POCSO mandatory reporting; internal response is immediate so the "
                "external reporting deadline is never the binding constraint."
            ),
        ),
    }
)

SAFETY_TAXONOMY_SETTING = VersionedSetting(
    version=1,
    effective_from=date(2026, 2, 10),
    basis="IT (Intermediary Guidelines) Rules 2021 as amended 10 February 2026 — DEC-V1-006.",
)

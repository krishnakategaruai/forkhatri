"""Versioned severity taxonomy — DEC-V1-006 as data.

# [TR068/DEC-V1-006/DEC-V1-028] Every report and every automated detection
# signal is classified into one of four tiers at creation time, and the SLA
# clock starts at that moment (SP065's tampering row: never at human pickup).
# The figures are the document's own, not invented here:
#   Tier 2 — acknowledge within 24 h, resolve within 36 h (IT Rules 2021,
#            2026-amended, grievance ceilings).
#   Tier 3 — human-reviewed within 2 h where the content is nudity- or
#            impersonation-adjacent (the legal ceiling for that subset);
#            otherwise within 12 h.
#   Tier 4 — immediate: paged, never queued; suspected CSAM/underage-sexual is
#            additionally reported without waiting for the internal review.
#   Tier 1 — an automated nudge with no human SLA. A FILED report is never
#            Tier 1: DEC-V1-006 says a filed report "is immediately
#            reclassified into the grievance-acknowledgment SLA".
#
# The version string is stored on every classification row so a later change
# to this table (the IT Rules were already tightened once, in February 2026)
# can be told apart from the rows classified under the earlier one.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Final

from app.config.thresholds import SafetyTier

TAXONOMY_VERSION: Final[str] = "2026-09-22.1"


@dataclass(frozen=True, slots=True)
class TierSla:
    """Deadlines measured from the classification moment. `None` = no human SLA."""

    acknowledge_within: timedelta | None
    resolve_within: timedelta | None
    pages_on_call: bool
    csam_channel: bool = False


IMMEDIATE: Final[timedelta] = timedelta(0)

TIER_SLA: Final[dict[SafetyTier, TierSla]] = {
    SafetyTier.LOW: TierSla(None, None, pages_on_call=False),
    SafetyTier.MEDIUM: TierSla(timedelta(hours=24), timedelta(hours=36), pages_on_call=False),
    # Tier 3's two windows are picked per category below (2 h subset vs 12 h).
    SafetyTier.HIGH: TierSla(timedelta(hours=12), timedelta(hours=12), pages_on_call=True),
    SafetyTier.CRITICAL: TierSla(IMMEDIATE, IMMEDIATE, pages_on_call=True, csam_channel=True),
}

TIER3_LEGAL_SUBSET_WINDOW: Final[timedelta] = timedelta(hours=2)


@dataclass(frozen=True, slots=True)
class Classification:
    tier: SafetyTier
    acknowledge_within: timedelta | None
    resolve_within: timedelta | None
    rationale: str
    pages_on_call: bool
    csam_channel: bool


def _tier3(rationale: str, *, legal_subset: bool) -> Classification:
    window = TIER3_LEGAL_SUBSET_WINDOW if legal_subset else TIER_SLA[SafetyTier.HIGH].resolve_within
    return Classification(SafetyTier.HIGH, window, window, rationale, pages_on_call=True, csam_channel=False)


def _tier2(rationale: str) -> Classification:
    sla = TIER_SLA[SafetyTier.MEDIUM]
    return Classification(
        SafetyTier.MEDIUM, sla.acknowledge_within, sla.resolve_within, rationale, False, False
    )


def _tier4(rationale: str, *, csam: bool) -> Classification:
    return Classification(SafetyTier.CRITICAL, IMMEDIATE, IMMEDIATE, rationale, True, csam)


# --- Filed reports: REPORT_REASONS → tier ------------------------------------
# Keyed by the user-facing reason in `components/safety/interface.py`.
REPORT_REASON_CLASSIFICATION: Final[dict[str, Classification]] = {
    "harassment": _tier2("Repeated harassment / unwanted contact (Tier 2 example)."),
    "fake_profile": _tier3("Impersonation-adjacent: 2 h legal ceiling (IT Rules 2021).", legal_subset=True),
    "inappropriate_content": _tier3(
        "Nudity-adjacent content: 2 h legal ceiling (IT Rules 2021).", legal_subset=True
    ),
    "scam_or_money": _tier3(
        "Financial manipulation / romance-scam indicator (Tier 3 example).", legal_subset=False
    ),
    "already_married": _tier2("Misrepresentation; ordinary grievance ceilings apply."),
    "underage": _tier4("Suspected minor: POCSO mandatory-reporting path.", csam=True),
    "other": _tier2("Any filed complaint enters the 24 h / 36 h grievance SLA."),
}

# --- Automated detection signals: signal_type → tier + report category -------
@dataclass(frozen=True, slots=True)
class SignalRule:
    classification: Classification
    report_category: str


DETECTION_SIGNAL_CLASSIFICATION: Final[dict[str, SignalRule]] = {
    "off_platform_push": SignalRule(_tier2("Off-platform pressure (Tier 2 example)."), "harassment"),
    "contact_phone_number": SignalRule(
        _tier2("Phone number shared in chat: off-platform pressure indicator."), "harassment"
    ),
    "contact_upi_id": SignalRule(
        _tier3("UPI id in chat: financial manipulation indicator.", legal_subset=False), "scam_or_money"
    ),
    "money_ask": SignalRule(
        _tier3("Request for money: romance-scam indicator.", legal_subset=False), "scam_or_money"
    ),
    "sexual_solicitation": SignalRule(
        _tier3("Explicit sexual solicitation: nudity-adjacent, 2 h ceiling.", legal_subset=True),
        "inappropriate_content",
    ),
    "self_declared_minor": SignalRule(
        _tier4("Self-declared minor in a matrimonial chat: Tier 4.", csam=True), "underage"
    ),
    "underage_date_of_birth": SignalRule(
        _tier4("Profile date of birth under 18: Tier 4.", csam=True), "underage"
    ),
}


def classify_report_reason(reason: str) -> Classification:
    """A filed report is never Tier 1 (DEC-V1-006); unknown reasons fall to Tier 2."""
    return REPORT_REASON_CLASSIFICATION.get(reason, REPORT_REASON_CLASSIFICATION["other"])


def classify_signal(signal_type: str) -> SignalRule:
    return DETECTION_SIGNAL_CLASSIFICATION[signal_type]

"""Plans and entitlements — the one catalogue (DEC-V1-031).

# What a plan may and may not buy. Gold and Assisted buy CAPABILITY for the
# member's own search: more requests a day, knowing who shortlisted or viewed
# you, asking a connection for their phone, the full kundli report, a
# relationship manager. No plan ever buys VISIBILITY: nothing here feeds
# "For you", search order, or the photo wall (v1-decisions: evidence not
# score, no engagement metrics, and the product-values line that Mangaly
# does not sell a place in someone else's results).
#
# Versioned: `CATALOGUE_VERSION` is stored on every order so a later price
# change never rewrites what a member actually paid for.
#
# Prices are config placeholders in INR paise (₹2,499 = 249_900). GST (18%)
# is a separate line on every order, never folded into the plan price, so
# the invoice work in the backlog has the two numbers it needs.
#
# Family: an entitlement belongs to the CANDIDATE account. A parent acting for
# the candidate (`for_candidate`) uses the candidate's plan — the search is the
# candidate's, so is the plan.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

CATALOGUE_VERSION: Final = "2026-09"
CURRENCY: Final = "INR"
GST_RATE_BPS: Final = 1800  # 18.00 % as basis points

PlanCode = Literal["FREE", "GOLD", "ASSISTED"]

# Entitlement flags. `daily_requests` is a number; the rest are booleans.
DAILY_REQUESTS: Final = "daily_requests"
SEE_WHO_SHORTLISTED_YOU: Final = "see_who_shortlisted_you"
SEE_WHO_VIEWED_YOU: Final = "see_who_viewed_you"
CONTACT_UNLOCK: Final = "contact_unlock"
KUNDLI_FULL_REPORT: Final = "kundli_full_report"
ASSISTED_MATCHING: Final = "assisted_matching"

BOOLEAN_FLAGS: Final = (
    SEE_WHO_SHORTLISTED_YOU,
    SEE_WHO_VIEWED_YOU,
    CONTACT_UNLOCK,
    KUNDLI_FULL_REPORT,
    ASSISTED_MATCHING,
)

# `None` means unlimited.
UNLIMITED: Final = None
FREE_DAILY_REQUESTS: Final = 3


@dataclass(frozen=True, slots=True)
class Entitlements:
    daily_requests: int | None
    see_who_shortlisted_you: bool
    see_who_viewed_you: bool
    contact_unlock: bool
    kundli_full_report: bool
    assisted_matching: bool

    def flag(self, name: str) -> bool:
        if name == DAILY_REQUESTS:
            return self.daily_requests is UNLIMITED
        if name not in BOOLEAN_FLAGS:
            raise KeyError(name)
        return bool(getattr(self, name))

    def as_dict(self) -> dict[str, bool | int | None]:
        return {
            DAILY_REQUESTS: self.daily_requests,
            SEE_WHO_SHORTLISTED_YOU: self.see_who_shortlisted_you,
            SEE_WHO_VIEWED_YOU: self.see_who_viewed_you,
            CONTACT_UNLOCK: self.contact_unlock,
            KUNDLI_FULL_REPORT: self.kundli_full_report,
            ASSISTED_MATCHING: self.assisted_matching,
        }


@dataclass(frozen=True, slots=True)
class Term:
    months: int
    amount_paise: int  # plan price before GST

    @property
    def gst_paise(self) -> int:
        return (self.amount_paise * GST_RATE_BPS + 5000) // 10000

    @property
    def total_paise(self) -> int:
        return self.amount_paise + self.gst_paise


@dataclass(frozen=True, slots=True)
class Plan:
    code: PlanCode
    entitlements: Entitlements
    terms: tuple[Term, ...]  # empty for FREE
    # The plan this one contains entirely (Assisted includes Gold).
    includes: PlanCode | None = None

    def term(self, months: int) -> Term | None:
        return next((t for t in self.terms if t.months == months), None)


FREE_ENTITLEMENTS: Final = Entitlements(
    daily_requests=FREE_DAILY_REQUESTS,
    see_who_shortlisted_you=False,
    see_who_viewed_you=False,
    contact_unlock=False,
    kundli_full_report=False,
    assisted_matching=False,
)

GOLD_ENTITLEMENTS: Final = Entitlements(
    daily_requests=UNLIMITED,
    see_who_shortlisted_you=True,
    see_who_viewed_you=True,
    contact_unlock=True,
    kundli_full_report=True,
    assisted_matching=False,
)

ASSISTED_ENTITLEMENTS: Final = Entitlements(
    daily_requests=UNLIMITED,
    see_who_shortlisted_you=True,
    see_who_viewed_you=True,
    contact_unlock=True,
    kundli_full_report=True,
    assisted_matching=True,
)

PLANS: Final[dict[str, Plan]] = {
    "FREE": Plan(code="FREE", entitlements=FREE_ENTITLEMENTS, terms=()),
    "GOLD": Plan(
        code="GOLD",
        entitlements=GOLD_ENTITLEMENTS,
        terms=(
            Term(months=3, amount_paise=249_900),
            Term(months=6, amount_paise=399_900),
            Term(months=12, amount_paise=599_900),
        ),
    ),
    "ASSISTED": Plan(
        code="ASSISTED",
        entitlements=ASSISTED_ENTITLEMENTS,
        terms=(
            Term(months=6, amount_paise=1_999_900),
            Term(months=12, amount_paise=2_999_900),
        ),
        includes="GOLD",
    ),
}

# The order plans are shown, and the rank used to answer "which plan do I
# need for this flag?" (the cheapest plan that carries it).
PLAN_ORDER: Final = ("FREE", "GOLD", "ASSISTED")


def plan_for(code: str | None) -> Plan:
    """The plan a code names; anything unknown or absent is FREE."""
    return PLANS.get(code or "FREE", PLANS["FREE"])


def plan_needed_for(flag: str) -> PlanCode | None:
    """The cheapest plan that carries `flag`, or None if no plan does."""
    for code in PLAN_ORDER:
        plan = PLANS[code]
        if code != "FREE" and plan.entitlements.flag(flag):
            return plan.code
    return None


def paid_plan_codes() -> tuple[str, ...]:
    return tuple(code for code in PLAN_ORDER if PLANS[code].terms)

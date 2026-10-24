# [TR011] Opportunity Composer: create, share, or upload (FR11). One
# canonical Opportunity concept shared by every type (FR14) — Employment,
# Freelance/Project, Local Service promoted in V1; Partnership/Training/
# Community under "Other" (TR014). Entry modes create/share/upload never
# duplicate the schema, only how it's first populated.
# Approach: `poster_id` resolved server-side from AuthzContext, never client
# input (same pattern as listings.py's owner_id). `source_segment` is
# mandatory; `public` requires `source_name` or `source_url` (FR11's own
# edge case). Rule-based (not AI) field extraction for share/upload modes:
# a pasted URL/text is scanned for a title-like first line and any known
# capability keyword; an upload just requires manual entry since no OCR
# exists in V1 — both cases mark every inferred field `unconfirmed_fields`,
# never presented as fact, per FR12. Publish is blocked server-side until
# title/type/location/response_method are all in `confirmed_fields`
# (TR012) — this is the ONE gate every publish path (create/share/upload)
# goes through, not three independently-coded checks.
# Traces to: FR11, FR12, FR13, FR14, FR55, TR011, TR012, TR013, TR014, TR055
from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta, timezone
from typing import Any, Literal

import asyncpg
from pydantic import BaseModel, Field

from app.services import hooks
from app.viewer_profile import viewer_capabilities
from app.geo import resolve_place
from app.services.listings import require_profile
from app.errors import ApiError
from app.i18n import translate
from app.identity import AuthzContext
from app.services.privacy import require_accepted
from app.impressions import boosted_ids, log_events
from app.taxonomy_cache import labels_for
from app.profile_cards import ProfileCard, recommend_profiles
from app.services.pagination import DEFAULT_LIMIT, MAX_LIMIT, Page, paginate


V1_TYPES = ["employment", "freelance", "local_service"]
OTHER_TYPES = ["partnership", "training", "community"]
MATERIAL_FIELDS = {"title", "type", "location", "response_method"}

# [FR22 DEC-002 — same fixed vocabulary already verified on real apps and
# used by the (not-yet-built) Enquiries component; reused here read-only so
# the Opportunity detail's primary-action label can never independently
# drift from that one mapping (TR055's own "never a second, independently-
# coded type→label mapping" rule). [Product-owner i18n rule] Values here
# are i18n KEYS under opportunities.actionLabel.*, not display text — the
# frontend translates via `t('opportunities:actionLabel.'+key)`.]
TYPE_ACTION_LABEL = {
    "employment": "apply",
    "freelance": "submitProposal",
    "local_service": "enquireNow",
    "partnership": "contact",
    "training": "register",
    "community": "register",
}

# [FR40] advance-payment / registration-fee wording, in the three launch
# languages — the classic job-scam pattern the Indian job market reports.
ADVANCE_PAYMENT_PATTERNS = (
    "advance payment", "pay in advance", "registration fee", "registration charge", "security deposit",
    "joining fee", "processing fee", "pay to apply",
    "अग्रिम भुगतान", "पंजीकरण शुल्क", "रजिस्ट्रेशन फीस", "जमानत राशि",
    "ముందస్తు చెల్లింపు", "రిజిస్ట్రేషన్ ఫీజు", "సెక్యూరిటీ డిపాజిట్",
)

NOT_INTERESTED_REASONS = {
    "too_far", "wrong_type", "not_my_capability", "value_too_low", "wrong_timing", "already_found", "not_interested",
}

# ---------------------------------------------------------------------------
# [Backend A, 2026-09-28] Typed fields per opportunity type (migration 018).
# WorkIndia asks an employer for salary, shift, timings, qualification and
# openings as fields; Upwork asks a client for budget type, duration,
# experience level and screening questions. Vyapar stores the same as
# nullable columns so ranking, filters, suggestions and one-tap applications
# can read them. The free-text `compensation` column is kept in sync as a
# derived display string, so every screen and client that reads it today
# keeps working. Money is in paise (integers), never floats.
# ---------------------------------------------------------------------------
IncentiveType = Literal["none", "fixed_plus_incentive", "incentive_only"]
Shift = Literal["day", "night", "rotational", "flexible"]
MinQualification = Literal["below_10th", "10th", "12th", "diploma", "iti", "graduate", "postgraduate", "any"]
EnglishLevel = Literal["none", "basic", "good", "fluent"]
BudgetType = Literal["fixed", "hourly"]
Duration = Literal["under_1_week", "1_4_weeks", "1_3_months", "3_6_months", "over_6_months", "ongoing"]
ExperienceLevel = Literal["entry", "intermediate", "expert"]
Urgency = Literal["today", "this_week", "flexible"]

EMPLOYMENT_FIELDS = frozenset({
    "salary_min_paise", "salary_max_paise", "incentive_type", "incentive_max_paise", "openings", "shift",
    "job_timings", "interview_details", "min_qualification", "english_level", "experience_min_months",
    "experience_max_months", "requires_assets",
})
FREELANCE_FIELDS = frozenset({
    "budget_type", "budget_min_paise", "budget_max_paise", "hourly_rate_min_paise", "hourly_rate_max_paise",
    "duration", "experience_level", "screening_questions",
})
LOCAL_SERVICE_FIELDS = frozenset({"preferred_date", "budget_paise", "urgency"})
STRUCTURED_FIELDS_BY_TYPE: dict[str, frozenset[str]] = {
    "employment": EMPLOYMENT_FIELDS,
    "freelance": FREELANCE_FIELDS,
    "local_service": LOCAL_SERVICE_FIELDS,
}
ALL_STRUCTURED_FIELDS = EMPLOYMENT_FIELDS | FREELANCE_FIELDS | LOCAL_SERVICE_FIELDS
_STRUCTURED_COLUMNS = sorted(ALL_STRUCTURED_FIELDS)
MAX_SCREENING_QUESTIONS = 5


class ScreeningQuestion(BaseModel):
    id: str | None = Field(default=None, max_length=40, description="Stable id; assigned (q1, q2, ...) when omitted")
    text: str = Field(min_length=3, max_length=300)


class OpportunityStructured(BaseModel):
    """Type-specific fields. On input, only the fields for the opportunity's
    own type are accepted (a salary on a freelance project is a 422,
    `structured_field_not_for_type`). On output every field is present and
    the ones for other types are null."""

    # employment (monthly, in-hand, paise)
    salary_min_paise: int | None = Field(default=None, ge=0)
    salary_max_paise: int | None = Field(default=None, ge=0)
    incentive_type: IncentiveType | None = None
    incentive_max_paise: int | None = Field(default=None, ge=0)
    openings: int | None = Field(default=None, ge=1, le=1000)
    shift: Shift | None = None
    job_timings: str | None = Field(default=None, max_length=200)
    interview_details: str | None = Field(default=None, max_length=500)
    min_qualification: MinQualification | None = None
    english_level: EnglishLevel | None = None
    experience_min_months: int | None = Field(default=None, ge=0, le=600)
    experience_max_months: int | None = Field(default=None, ge=0, le=600)
    requires_assets: list[str] | None = Field(default=None, max_length=10, description="e.g. bike, smartphone, laptop")
    # freelance
    budget_type: BudgetType | None = None
    budget_min_paise: int | None = Field(default=None, ge=0)
    budget_max_paise: int | None = Field(default=None, ge=0)
    hourly_rate_min_paise: int | None = Field(default=None, ge=0)
    hourly_rate_max_paise: int | None = Field(default=None, ge=0)
    duration: Duration | None = None
    experience_level: ExperienceLevel | None = None
    screening_questions: list[ScreeningQuestion] | None = Field(default=None, max_length=MAX_SCREENING_QUESTIONS)
    # local service
    preferred_date: date | None = None
    budget_paise: int | None = Field(default=None, ge=0)
    urgency: Urgency | None = None


def _col(row: asyncpg.Record, name: str) -> Any:
    """Column value, or None when a narrower SELECT did not include it."""
    try:
        return row[name]
    except (KeyError, IndexError):
        return None


def structured_from_row(row: asyncpg.Record) -> OpportunityStructured:
    values: dict[str, Any] = {}
    for name in ALL_STRUCTURED_FIELDS:
        v = _col(row, name)
        if name == "screening_questions":
            if isinstance(v, str):
                v = json.loads(v)
            v = [ScreeningQuestion(**q) for q in (v or [])]
        elif name == "requires_assets":
            v = list(v) if v else []
        values[name] = v
    return OpportunityStructured(**values)


def _normalize_structured(struct: OpportunityStructured, type_: str, lang: str) -> dict[str, Any]:
    """Validates the fields for `type_` and returns the full column dict
    (fields of other types set to their empty value). One place for every
    per-type rule, shared by create and patch."""
    allowed = STRUCTURED_FIELDS_BY_TYPE.get(type_, frozenset())
    data = struct.model_dump()
    for name in ALL_STRUCTURED_FIELDS - allowed:
        if data.get(name) not in (None, [], {}):
            raise ApiError(
                422, "opportunities.error.fieldNotForType", lang, field=name, type=type_,
                extra={"field": name, "opportunity_type": type_}, error_code="structured_field_not_for_type",
            )
    out: dict[str, Any] = {name: None for name in ALL_STRUCTURED_FIELDS}
    out["requires_assets"] = []
    out["screening_questions"] = []
    if type_ == "employment":
        lo, hi = data["salary_min_paise"], data["salary_max_paise"]
        # [Start flow 2026-10, decision 11] fixed pay is one amount: a single
        # side given means min = max ("₹10,000 a month"), never a refusal.
        if (lo is None) != (hi is None):
            data["salary_min_paise"] = data["salary_max_paise"] = lo if lo is not None else hi
            lo = hi = data["salary_min_paise"]
        if lo is not None and hi is not None and lo > hi:
            raise ApiError(422, "opportunities.error.salaryRangeInvalid", lang)
        elo, ehi = data["experience_min_months"], data["experience_max_months"]
        if elo is not None and ehi is not None and elo > ehi:
            raise ApiError(422, "opportunities.error.experienceRangeInvalid", lang)
        assets: list[str] = []
        for a in data["requires_assets"] or []:
            a = a.strip().lower()[:40]
            if a and a not in assets:
                assets.append(a)
        for name in EMPLOYMENT_FIELDS:
            out[name] = data[name]
        if data["incentive_type"] in (None, "none"):
            out["incentive_max_paise"] = None
        out["requires_assets"] = assets
    elif type_ == "freelance":
        btype = data["budget_type"]
        has_fixed = data["budget_min_paise"] is not None or data["budget_max_paise"] is not None
        has_hourly = data["hourly_rate_min_paise"] is not None or data["hourly_rate_max_paise"] is not None
        if btype is None:
            btype = "hourly" if (has_hourly and not has_fixed) else ("fixed" if has_fixed else None)
        if (btype == "fixed" and has_hourly) or (btype == "hourly" and has_fixed):
            raise ApiError(422, "opportunities.error.budgetFieldsMismatch", lang)
        for lo, hi in ((data["budget_min_paise"], data["budget_max_paise"]), (data["hourly_rate_min_paise"], data["hourly_rate_max_paise"])):
            if lo is not None and hi is not None and lo > hi:
                raise ApiError(422, "opportunities.error.budgetRangeInvalid", lang)
        questions: list[dict[str, str]] = []
        used: set[str] = set()
        for i, q in enumerate(data["screening_questions"] or [], start=1):
            qid = (q.get("id") or "").strip() or f"q{i}"
            while qid in used:
                qid = f"{qid}_{i}"
            used.add(qid)
            questions.append({"id": qid, "text": q["text"].strip()})
        if len(questions) > MAX_SCREENING_QUESTIONS:
            raise ApiError(422, "opportunities.error.tooManyScreeningQuestions", lang, max=MAX_SCREENING_QUESTIONS)
        for name in FREELANCE_FIELDS:
            out[name] = data[name]
        out["budget_type"] = btype
        out["screening_questions"] = questions
    elif type_ == "local_service":
        for name in LOCAL_SERVICE_FIELDS:
            out[name] = data[name]
    return out


def format_inr(paise: int) -> str:
    """Rupee sign with Indian digit grouping (1,50,000); paise only when non-zero."""
    rupees, rest = divmod(int(paise), 100)
    digits = str(rupees)
    if len(digits) > 3:
        head, tail = digits[:-3], digits[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        digits = ",".join(groups) + "," + tail
    return "\u20b9" + digits + (f".{rest:02d}" if rest else "")


def compensation_label(struct: OpportunityStructured, type_: str, lang: str) -> str | None:
    """The derived display string for the money fields, in `lang`. None
    when no money field is set (the caller then falls back to free text)."""

    def t(key: str, **params: Any) -> str:
        return translate(f"opportunities.compensation.{key}", lang, **params)

    if type_ == "employment":
        lo, hi = struct.salary_min_paise, struct.salary_max_paise
        if lo is None and hi is None:
            base = None
        elif lo is not None and hi is not None and lo != hi:
            base = t("monthlyRange", min=format_inr(lo), max=format_inr(hi))
        else:
            base = t("monthly", amount=format_inr(lo if lo is not None else hi))
        if struct.incentive_type == "fixed_plus_incentive":
            extra = t("plusIncentive", amount=format_inr(struct.incentive_max_paise)) if struct.incentive_max_paise else t("plusIncentiveOpen")
            return f"{base} {extra}" if base else extra
        if struct.incentive_type == "incentive_only":
            return t("incentiveOnly", amount=format_inr(struct.incentive_max_paise)) if struct.incentive_max_paise else t("incentiveOnlyOpen")
        return base
    if type_ == "freelance":
        if struct.budget_type == "hourly":
            lo, hi = struct.hourly_rate_min_paise, struct.hourly_rate_max_paise
            if lo is None and hi is None:
                return None
            if lo is not None and hi is not None and lo != hi:
                return t("hourlyRange", min=format_inr(lo), max=format_inr(hi))
            return t("hourly", amount=format_inr(lo if lo is not None else hi))
        lo, hi = struct.budget_min_paise, struct.budget_max_paise
        if lo is None and hi is None:
            return None
        if lo is not None and hi is not None and lo != hi:
            return t("fixedRange", min=format_inr(lo), max=format_inr(hi))
        return t("fixed", amount=format_inr(lo if lo is not None else hi))
    if type_ == "local_service" and struct.budget_paise is not None:
        return t("budget", amount=format_inr(struct.budget_paise))
    return None


_BARE_AMOUNT = re.compile(r"^\s*(?:₹|rs\.?|inr)?\s*([0-9][0-9,]*)(?:\.(\d{1,2}))?\s*(?:/-)?\s*$", re.IGNORECASE)

# [Terminology — GLOSSARY.md "Pay"] "LPA" is recruiter shorthand most members
# don't read. A yearly lakh figure ("₹8–10 LPA", "6 lakh per annum") is shown
# as "₹8–10 lakh a year (₹67,000–₹83,000 a month)" in the viewer's language.
_YEARLY_LAKH = re.compile(
    r"^\s*(?:₹|rs\.?|inr)?\s*([0-9]+(?:\.[0-9]+)?)\s*"
    r"(?:(?:–|-|to)\s*(?:₹|rs\.?)?\s*([0-9]+(?:\.[0-9]+)?))?\s*"
    r"(?:lpa|l\.p\.a\.?|lakhs?\s*(?:per\s+annum|p\.?\s?a\.?|a\s+year|per\s+year|/\s*year|yearly))\s*$",
    re.IGNORECASE,
)


def _yearly_lakh_label(text: str, lang: str) -> str | None:
    m = _YEARLY_LAKH.match(text)
    if not m:
        return None

    def monthly_paise(lakh: str) -> int:
        # to a clean ₹1,000 (a converted figure must not look exact; matches DiscoverCard)
        return round(float(lakh) * 100_000 / 12 / 1000) * 1000 * 100

    def lakh(v: str) -> str:
        return v[:-2] if v.endswith(".0") else v

    lo, hi = m.group(1), m.group(2)
    amount = f"₹{lakh(lo)}–{lakh(hi)}" if hi else f"₹{lakh(lo)}"
    monthly = (
        f"{format_inr(monthly_paise(lo))}–{format_inr(monthly_paise(hi))}" if hi else format_inr(monthly_paise(lo))
    )
    return translate("opportunities.compensation.yearlyLakh", lang, amount=amount, monthly=monthly)


def legacy_compensation_label(text: str | None, type_: str, lang: str) -> str | None:
    """[FE2 — owner review 2026-09-29] Older posts keep money only in the
    free-text `compensation`. A bare number there ("15000", "Rs 800") used to
    reach cards as-is. It is now shown with ₹ and the period the post type
    implies (a month for a job, fixed for a project, a budget for a local
    service). Any other free text is kept exactly as the poster wrote it."""
    if not text:
        return None
    yearly = _yearly_lakh_label(text, lang)
    if yearly:
        return yearly
    m = _BARE_AMOUNT.match(text)
    if not m:
        # [Backend A, 2026-09-29] unit words ("₹250 per visit", "from ₹300
        # per visit", "Pay per visit", "700/day", "negotiable") in the
        # viewer's language (GLOSSARY.md "Pay"); anything else stays as written.
        return _unit_pay_label(text, lang) or text
    paise = int(m.group(1).replace(",", "")) * 100 + int((m.group(2) or "0").ljust(2, "0"))
    key = {"employment": "monthly", "freelance": "fixed", "local_service": "budget"}.get(type_)
    if key is None:
        return format_inr(paise)
    return translate(f"opportunities.compensation.{key}", lang, amount=format_inr(paise))


# ---------------------------------------------------------------------------
# [Backend A, 2026-09-29] Pay units in free text, and pay facts for clients.
# ---------------------------------------------------------------------------
_AMT = r"(?:₹|rs\.?|inr)?\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*(k)?"
_UNIT_WORDS = {
    "visit": "visit", "day": "day", "daily": "day", "hour": "hour", "hr": "hour", "hrs": "hour",
    "week": "week", "month": "month", "mo": "month", "monthly": "month",
}
_UNIT_AMOUNT = re.compile(
    r"^\s*(from\s+|starting\s+(?:at\s+|from\s+)?)?" + _AMT +
    r"(?:\s*(?:–|-|to)\s*" + _AMT + r")?\s*(?:/-)?\s*(?:/|per|a|an|every)\s*"
    r"(visit|day|daily|hour|hrs?|week|month|mo)\s*$",
    re.IGNORECASE,
)
_UNIT_ONLY = re.compile(r"^\s*(?:(?:pay|paid|payment)\s+)?(?:per|by\s+the|a|/)\s*(visit|day|hour|month)\s*(?:basis)?\s*$", re.IGNORECASE)
_NEGOTIABLE = re.compile(r"^\s*(?:pay\s+|salary\s+|price\s+)?negotiable\s*$", re.IGNORECASE)
_UNIT_KEY = {"visit": "perVisit", "day": "daily", "hour": "hourly", "week": "weekly", "month": "monthly"}


def _amount_paise(num: str, k: str | None) -> int:
    value = float(num.replace(",", ""))
    return int(round(value * (1000 if k else 1) * 100))


def _parse_unit_pay(text: str) -> tuple[str, int | None, int | None, bool] | None:
    """(unit, min_paise, max_paise, starting_from) for a unit phrase, else None."""
    m = _UNIT_AMOUNT.match(text or "")
    if m:
        lo = _amount_paise(m.group(2), m.group(3))
        hi = _amount_paise(m.group(4), m.group(5)) if m.group(4) else None
        return _UNIT_WORDS[m.group(6).lower()], lo, hi, bool(m.group(1))
    m = _UNIT_ONLY.match(text or "")
    if m:
        return m.group(1).lower(), None, None, False
    return None


def _unit_pay_label(text: str, lang: str) -> str | None:
    if _NEGOTIABLE.match(text or ""):
        return translate("opportunities.compensation.negotiable", lang)
    parsed = _parse_unit_pay(text)
    if parsed is None:
        return None
    unit, lo, hi, starting = parsed
    if lo is None:
        return translate(f"opportunities.compensation.unitOnly.{unit}", lang)
    amount = f"{format_inr(lo)}–{format_inr(hi)}" if hi and hi != lo else format_inr(lo)
    label = translate(f"opportunities.compensation.{_UNIT_KEY[unit]}", lang, amount=amount)
    return translate("opportunities.compensation.startingFrom", lang, label=label) if starting else label


PayPeriod = Literal["month", "year", "week", "day", "visit", "hour", "fixed", "budget"]


def _round_1000(paise: int) -> int:
    return int(round(paise / 100_000)) * 100_000


def pay_facts(struct: OpportunityStructured, type_: str, compensation: str | None) -> tuple[str | None, int | None, int | None]:
    """(pay_period, pay_monthly_min_paise, pay_monthly_max_paise), so a client
    can show a monthly figure first. Stated monthly salaries are exact;
    figures converted from a yearly amount are rounded to ₹1,000 (a converted
    figure must not look exact, same rule as the yearly label)."""
    if type_ == "employment" and (struct.salary_min_paise is not None or struct.salary_max_paise is not None):
        lo = struct.salary_min_paise if struct.salary_min_paise is not None else struct.salary_max_paise
        hi = struct.salary_max_paise if struct.salary_max_paise is not None else struct.salary_min_paise
        return "month", lo, hi
    if type_ == "employment" and struct.incentive_type == "incentive_only":
        return "month", None, None
    if type_ == "freelance" and has_budget(struct):
        return ("hour" if struct.budget_type == "hourly" else "fixed"), None, None
    if type_ == "local_service" and struct.budget_paise is not None:
        return "budget", None, None
    text = (compensation or "").strip()
    if not text:
        return None, None, None
    y = _YEARLY_LAKH.match(text)
    if y:
        lo = _round_1000(int(round(float(y.group(1)) * 100_000 * 100 / 12)))
        hi = _round_1000(int(round(float(y.group(2)) * 100_000 * 100 / 12))) if y.group(2) else lo
        return "year", lo, hi
    b = _BARE_AMOUNT.match(text)
    if b:
        paise = int(b.group(1).replace(",", "")) * 100
        period = {"employment": "month", "freelance": "fixed", "local_service": "budget"}.get(type_)
        return period, (paise if period == "month" else None), (paise if period == "month" else None)
    u = _parse_unit_pay(text)
    if u:
        unit, lo, hi = u[0], u[1], u[2]
        if unit == "month" and lo is not None:
            return "month", lo, hi or lo
        return unit, None, None
    return None, None, None


def has_budget(struct: OpportunityStructured) -> bool:
    if struct.budget_type == "hourly":
        return struct.hourly_rate_min_paise is not None or struct.hourly_rate_max_paise is not None
    return struct.budget_min_paise is not None or struct.budget_max_paise is not None


def _structured_placeholders(start: int) -> str:
    """`$n, $n+1, ...` (jsonb-cast where needed) for every structured column, in `_STRUCTURED_COLUMNS` order."""
    return ", ".join(f"${start + i}" + ("::jsonb" if c == "screening_questions" else "") for i, c in enumerate(_STRUCTURED_COLUMNS))


def _structured_set_clause(start: int) -> str:
    return ", ".join(f"{c} = ${start + i}" + ("::jsonb" if c == "screening_questions" else "") for i, c in enumerate(_STRUCTURED_COLUMNS))


def _structured_values(columns: dict[str, Any]) -> list[Any]:
    return [json.dumps(columns[c]) if c == "screening_questions" else columns[c] for c in _STRUCTURED_COLUMNS]


def _seeker_charge_check(
    *, lang: str, type_: str, title: str | None, description: str | None, requirements: str | None,
    compensation: str | None, columns: dict[str, Any], candidate_pays: bool | None = None,
) -> None:
    """[Backend A, wiring workstream B's hook] "Nobody charges job seekers":
    every create, patch and publish runs the registered checks over the
    record as it WILL be (free text plus the structured text fields a fee
    could hide in: timings, interview details, screening questions). A
    refusal is B's 422 `seeker_charge_not_allowed`, raised before anything
    is written."""
    questions = " ".join(q["text"] if isinstance(q, dict) else q.text for q in (columns.get("screening_questions") or []))
    text = " ".join(filter(None, [
        title, description, requirements, compensation,
        columns.get("job_timings"), columns.get("interview_details"), questions,
    ]))
    structured = {k: v for k, v in columns.items() if k != "screening_questions"}
    structured.update({"type": type_, "candidate_pays": candidate_pays})
    hooks.run_seeker_charge_checks(text=text, structured=structured, lang=lang)


async def _seeker_charge_guard(ctx: AuthzContext, opportunity_id: str | None, **kwargs: Any) -> None:
    """[Trust pack] `_seeker_charge_check` plus the trust event: a refusal is
    written to the audit log on its own connection (the refusal rolls this
    request back), with the rule and matched words, never the text."""
    try:
        _seeker_charge_check(**kwargs)
    except ApiError as exc:
        if exc.code == "seeker_charge_not_allowed":
            from app.services import scam_shield

            await scam_shield.log_block(ctx.member_id, surface="opportunity", object_kind="opportunity",
                                        object_id=opportunity_id, exc=exc)
        raise


# [IMP-B/L1] Pre-accept calling makes sense where a person rings about a job
# or a local job (Apna's "Call HR", WorkIndia's "Click to call HR"); a
# freelance proposal or a partnership is a written conversation.
PRECALL_TYPES = ("employment", "local_service")


async def _set_position(conn: asyncpg.Connection, row: asyncpg.Record, lat: float | None, lng: float | None,
                        location: str | None, force: bool = False) -> asyncpg.Record:
    """[IMP-B, owner 2026-09-30] A post needs coordinates for distance, radius
    and Near you. Explicit lat/lng win; otherwise a known locality named in the
    location text is used (app/geo.py). `force` re-derives on a location edit."""
    if lat is not None and lng is not None:
        new = (lat, lng)
    else:
        if row["lat"] is not None and not force:
            return row
        place = resolve_place(location or row["location"])
        if place is None:
            return row
        new = (place.lat, place.lng)
    return await conn.fetchrow(
        "UPDATE vyapar_opportunities.opportunities SET lat = $2, lng = $3 WHERE id = $1 RETURNING *", row["id"], *new
    )


def _check_precall(allow: bool | None, type_: str, lang: str) -> None:
    if allow and type_ not in PRECALL_TYPES:
        raise ApiError(422, "opportunities.error.precallNotForType", lang, error_code="precall_not_for_type",
                       extra={"field": "allow_precall", "opportunity_type": type_, "allowed_types": list(PRECALL_TYPES)})


def _extract_fields(raw_input: str | None) -> dict:
    """[TR012] Rule-based extraction only — never an AI hot-path dependency,
    per FR12's own stated assumption. First non-empty line becomes a
    candidate title; a handful of keyword checks infer a type. Both are
    marked unconfirmed by the caller, never inserted as confirmed fact."""
    if not raw_input:
        return {}
    lines = [l.strip() for l in raw_input.splitlines() if l.strip()]
    title = lines[0][:200] if lines else None
    text = raw_input.lower()
    inferred_type = None
    if any(k in text for k in ["hiring", "job opening", "full-time", "full time"]):
        inferred_type = "employment"
    elif any(k in text for k in ["freelance", "project basis", "gig"]):
        inferred_type = "freelance"
    elif any(k in text for k in ["plumber", "electrician", "repair", "service needed"]):
        inferred_type = "local_service"
    return {"title": title, "type": inferred_type}


class OpportunityCreate(BaseModel):
    entry_mode: Literal["create", "share", "upload"] = "create"
    title: str | None = None
    type: str = "employment"
    description: str | None = None
    requirements: str | None = None
    compensation: str | None = None
    value_amount: float | None = None
    location: str | None = None
    work_mode: Literal["on_site", "remote", "both"] | None = None
    timing: str | None = None
    required_capabilities: list[str] = Field(default_factory=list)
    response_method: Literal["in_app", "external"] = "in_app"
    deadline: datetime | None = None
    source_segment: Literal["community", "public"]
    source_name: str | None = None
    source_url: str | None = None
    raw_input: str | None = None
    raw_image_url: str | None = None
    structured: OpportunityStructured | None = None
    # Declared, never stored: an opportunity may not charge the applicant.
    # true is refused with 422 seeker_charge_not_allowed (workstream B's rule).
    candidate_pays: bool | None = Field(default=None, description="Must be false or omitted; true is refused (seeker_charge_not_allowed)")
    # [IMP-B/L1] "Let people call me before I accept" — employment and local_service only.
    allow_precall: bool = Field(default=False, description="Let people call or WhatsApp before an application is accepted (employment, local_service)")
    # [IMP-B/W2] how they may reach the poster before acceptance; WhatsApp only by default.
    precall_channel: Literal["call_and_whatsapp", "whatsapp_only"] = "whatsapp_only"
    # [IMP-B] where the work is; when omitted, a known locality named in `location` is used (app/geo.py)
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)


class OpportunityPatch(BaseModel):
    title: str | None = None
    type: str | None = None
    description: str | None = None
    requirements: str | None = None
    compensation: str | None = None
    value_amount: float | None = None
    location: str | None = None
    work_mode: Literal["on_site", "remote", "both"] | None = None
    timing: str | None = None
    required_capabilities: list[str] | None = None
    response_method: Literal["in_app", "external"] | None = None
    deadline: datetime | None = None
    structured: OpportunityStructured | None = None  # partial: only the fields sent are changed
    candidate_pays: bool | None = Field(default=None, description="Must be false or omitted; true is refused (seeker_charge_not_allowed)")
    allow_precall: bool | None = Field(default=None, description="Let people call or WhatsApp before accepting (employment, local_service)")
    precall_channel: Literal["call_and_whatsapp", "whatsapp_only"] | None = None
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)


class ConfirmFieldsIn(BaseModel):
    fields: list[str]


class OpportunityOut(BaseModel):
    id: str
    poster_id: str
    is_poster: bool
    title: str
    type: str
    type_action_label: str
    description: str | None
    requirements: str | None
    compensation: str | None
    value_amount: float | None
    location: str | None
    work_mode: str | None
    timing: str | None
    required_capabilities: list[str]
    response_method: str | None
    deadline: datetime | None
    source_segment: str
    source_name: str | None
    source_url: str | None
    source_unreachable: bool
    entry_mode: str
    unconfirmed_fields: list[str]
    confirmed_fields: list[str]
    state: str
    state_reason: str | None
    saved: bool = False
    # [Backend A] typed fields per type, and the derived money line in the
    # caller's language (falls back to the free-text `compensation`).
    structured: OpportunityStructured = Field(default_factory=OpportunityStructured)
    compensation_label: str | None = None
    # [Backend A, 2026-09-29] How the pay is counted and, where it is a
    # salary, its monthly figure, so a card can lead with "a month".
    pay_period: PayPeriod | None = None  # month|year|week|day|visit|hour|fixed|budget
    pay_monthly_min_paise: int | None = None
    pay_monthly_max_paise: int | None = None
    # [critique N3] true once the post's last date has passed: show it as
    # Expired (GLOSSARY "Post past its date"); applying is refused.
    deadline_passed: bool = False
    # [Backend A, workstream B's enrichers] set on the detail read only.
    # Shapes are B's: seeker_protection = {applies, title, body, report_reason,
    # report_label} (employment only, else null); poster_badges =
    # [{key, label, description, earned_at}]. See references/imp-backend-b.md.
    seeker_protection: dict[str, Any] | None = None
    poster_badges: list[dict[str, Any]] = []
    # [Trust pack] detail read only: the payee-confirmed "Paid on time: 12 of
    # 13" for the poster (null until 3 answers); for the POSTER, the platform
    # restriction on this post with its appeal path, and how many applicants
    # still wait for an answer. See references/imp-trust-pack.md.
    poster_paid_on_time: dict[str, Any] | None = None
    restriction: dict[str, Any] | None = None
    applicants_waiting: dict[str, Any] | None = None
    # [IMP-B/L1] pre-accept calling: the poster's switch, and (detail read,
    # non-poster viewers) the call/WhatsApp actions — the same shape as
    # GET /v1/opportunities/{id}/contact-actions.
    allow_precall: bool = False
    precall_actions: dict[str, Any] | None = None
    # [IMP-B/W2] whatsapp_only | call_and_whatsapp, and the honest sentence to
    # show next to the switch, in the reader's language ("Anyone who calls or
    # messages you from this post will see your phone number.").
    precall_channel: str = "whatsapp_only"
    precall_disclosure: str | None = None
    # [FR18 card fields — set only by feed.py's card builder, None elsewhere]
    submitter_name: str | None = None
    posted_days_ago: int | None = None
    relevance_reason: str | None = None  # i18n key under ranking.signal.*
    sponsored: bool = False  # [FR30/FR54] rendered only via SponsoredBadge
    # [Opportunity detail rebuild, 2026-09-21] Context a person needs to
    # decide, set only by the detail endpoint. The data always existed on the
    # row; the detail screen simply never showed it (requirements, duration,
    # skills, deadline, source were all returned and all hidden).
    capability_labels: list[str] = []  # localized display names, never raw slugs
    min_experience_years: int | None = None
    days_left: int | None = None
    response_bucket: str | None = None  # none|under_5|5_to_10|10_to_20|20_plus
    poster: PosterSummary | None = None
    # Aligned index-for-index with capability_labels: which required skills
    # the VIEWER already has. None when the viewer has listed no skills (a
    # row of red crosses would read as rejection, not guidance).
    capability_match: list[bool] | None = None
    # On recommendation cards: which of the VIEWER's own skills this
    # opportunity asks for, so the card can say why it is shown.
    viewer_matched_labels: list[str] = []


class PosterSummary(BaseModel):
    """Upwork's "About the client" / WorkIndia's company block, Vyapar-sourced:
    only facts Vyapar itself can vouch for — never a self-reported claim."""

    name: str | None
    member_since: str | None
    active_opportunities: int
    verified_listing_id: str | None
    verified_listing_name: str | None
    # "Will they get back to me?" — coarse buckets from poster_reply_habit(),
    # None until the poster has received enough enquiries to say.
    reply_rate: str | None = None  # most|some|few
    reply_speed: str | None = None  # hours|day|days


OpportunityOut.model_rebuild()


def _row_to_opp(row: asyncpg.Record, caller_id: str, saved: bool = False, lang: str = "en") -> OpportunityOut:
    structured = structured_from_row(row)
    return OpportunityOut(
        id=str(row["id"]),
        poster_id=row["poster_id"],
        is_poster=row["poster_id"] == caller_id,
        title=row["title"],
        type=row["type"],
        type_action_label=TYPE_ACTION_LABEL.get(row["type"], "contact"),
        description=row["description"],
        requirements=row["requirements"],
        compensation=row["compensation"],
        value_amount=float(row["value_amount"]) if row["value_amount"] is not None else None,
        location=row["location"],
        work_mode=row["work_mode"],
        timing=row["timing"],
        required_capabilities=list(row["required_capabilities"]),
        response_method=row["response_method"],
        deadline=row["deadline"],
        source_segment=row["source_segment"],
        source_name=row["source_name"],
        source_url=row["source_url"],
        source_unreachable=row["source_unreachable"],
        entry_mode=row["entry_mode"],
        unconfirmed_fields=list(row["unconfirmed_fields"]),
        confirmed_fields=list(row["confirmed_fields"]),
        state=row["state"],
        state_reason=row["state_reason"],
        saved=saved,
        structured=structured,
        compensation_label=compensation_label(structured, row["type"], lang) or legacy_compensation_label(row["compensation"], row["type"], lang),
        **dict(zip(("pay_period", "pay_monthly_min_paise", "pay_monthly_max_paise"), pay_facts(structured, row["type"], row["compensation"]))),
        deadline_passed=bool(row["deadline"] and row["deadline"] < datetime.now(timezone.utc)),
        allow_precall=bool(_col(row, "allow_precall")),
        precall_channel=_col(row, "precall_channel") or "whatsapp_only",
        precall_disclosure=(
            translate(f"opportunities.precall.disclosure.{_col(row, 'precall_channel') or 'whatsapp_only'}", lang)
            if row["type"] in PRECALL_TYPES else None
        ),
    )


async def create_opportunity(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    body: OpportunityCreate,
) -> OpportunityOut:
    if body.source_segment == "public" and not (body.source_name or body.source_url):
        raise ApiError(422, "opportunities.error.sourceRequired", lang)
    # [Start flow 2026-10, decision 3] the one profile is created from the
    # ForKhatri identity here, with the post's own area when the member has
    # not named theirs yet, so "without a profile nothing moves forward"
    # holds without a "Create your profile first" wall.
    from app.services.profile import ensure_profile

    await ensure_profile(conn, ctx, lang, locality=body.location, lat=body.lat, lng=body.lng)
    await require_profile(conn, ctx.member_id, lang)

    title, type_ = body.title, body.type
    unconfirmed: list[str] = []
    if body.entry_mode in ("share", "upload"):
        extracted = _extract_fields(body.raw_input)
        if not title and extracted.get("title"):
            title = extracted["title"]
            unconfirmed.append("title")
        if extracted.get("type"):
            type_ = extracted["type"]
            unconfirmed.append("type")
    if not title:
        title = translate("opportunities.error.untitled", lang)
        unconfirmed.append("title")
    if not body.location:
        unconfirmed.append("location")

    # [Backend A] typed fields validated for the type; `compensation` is the
    # derived money line (in the content language) whenever money fields are
    # set, else the free text the caller sent.
    columns = _normalize_structured(body.structured or OpportunityStructured(), type_, lang)
    compensation = compensation_label(OpportunityStructured(**columns), type_, lang) or body.compensation
    await _seeker_charge_guard(
        ctx, None,
        lang=lang, type_=type_, title=title, description=body.description,
        # [Trust pack] a pasted WhatsApp forward (share mode) is poster text too
        requirements=" ".join(filter(None, [body.requirements, body.raw_input])) or None,
        compensation=body.compensation or compensation, columns=columns, candidate_pays=body.candidate_pays,
    )
    _check_precall(body.allow_precall, type_, lang)

    row = await conn.fetchrow(
        f"""INSERT INTO vyapar_opportunities.opportunities
             (poster_id, title, type, description, requirements, compensation, value_amount,
              location, work_mode, timing, required_capabilities, response_method, deadline,
              source_segment, source_name, source_url, entry_mode, raw_input, raw_image_url,
              unconfirmed_fields, content_language, {", ".join(_STRUCTURED_COLUMNS)})
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21,
                   {_structured_placeholders(22)})
           RETURNING *""",
        ctx.member_id, title, type_, body.description, body.requirements, compensation, body.value_amount,
        body.location, body.work_mode, body.timing, body.required_capabilities, body.response_method, body.deadline,
        body.source_segment, body.source_name, body.source_url, body.entry_mode, body.raw_input, body.raw_image_url,
        unconfirmed, lang, *_structured_values(columns),
    )
    row = await _set_position(conn, row, body.lat, body.lng, body.location)
    if body.allow_precall or body.precall_channel != "whatsapp_only":
        row = await conn.fetchrow(
            "UPDATE vyapar_opportunities.opportunities SET allow_precall = $2, precall_channel = $3 WHERE id = $1 RETURNING *",
            row["id"], bool(body.allow_precall), body.precall_channel,
        )
    return _row_to_opp(row, ctx.member_id, lang=lang)


async def list_my_opportunities(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str = "en",
) -> list[OpportunityOut]:
    rows = await conn.fetch(
        "SELECT * FROM vyapar_opportunities.opportunities WHERE poster_id = $1 ORDER BY created_at DESC", ctx.member_id
    )
    return [_row_to_opp(r, ctx.member_id, lang=lang) for r in rows]


async def get_opportunity(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    opportunity_id: str,
) -> OpportunityOut:
    row = await conn.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    if row is None:
        raise ApiError(404, "common.error.opportunityNotFound", lang)
    saved_row = await conn.fetchrow(
        """INSERT INTO vyapar_opportunities.member_opportunity (member_id, opportunity_id, viewed_at)
           VALUES ($1, $2, now())
           ON CONFLICT (member_id, opportunity_id) DO UPDATE SET viewed_at = now()
           RETURNING saved_at""",
        ctx.member_id, opportunity_id,
    )
    out = _row_to_opp(row, ctx.member_id, saved=saved_row["saved_at"] is not None, lang=lang)
    # [Real gap found live by the product owner, fixed here] feed cards
    # correctly show "posted by <name>, from your community" (a trust
    # signal research on this audience found matters more than
    # institutional signals) — but the detail screen a member actually
    # acts on never carried it at all, losing that trust signal exactly
    # where it matters most. Same RLS-safe `public_names()` lookup
    # feed.py's own card builder already uses, not a second implementation.
    if not out.is_poster:
        name_rows = await conn.fetch("SELECT display_name FROM vyapar_identity.public_names($1::text[])", [row["poster_id"]])
        out.submitter_name = name_rows[0]["display_name"] if name_rows else None
    out.sponsored = str(row["id"]) in await boosted_ids(conn, "opportunity", [row["id"]])

    # [Opportunity detail rebuild, 2026-09-21] Decision context.
    out.capability_labels = labels_for(out.required_capabilities, lang)
    eligibility = row["eligibility"]
    if isinstance(eligibility, str):
        eligibility = json.loads(eligibility)
    if isinstance(eligibility, dict) and eligibility.get("min_experience_years") is not None:
        out.min_experience_years = int(eligibility["min_experience_years"])
    now = datetime.now(timezone.utc)
    if row["deadline"]:
        out.days_left = max(0, (row["deadline"] - now).days)
    if row["published_at"]:
        out.posted_days_ago = (now - row["published_at"]).days
    # Response activity only means something where people respond through
    # Vyapar — for a Public/External item people apply on the source site.
    if out.response_method != "external":
        out.response_bucket = await conn.fetchval(
            "SELECT vyapar_enquiries.opportunity_response_bucket($1::uuid)", row["id"]
        )
    summary = await conn.fetchrow("SELECT * FROM vyapar_identity.poster_summary($1)", row["poster_id"])
    if summary:
        out.poster = PosterSummary(
            name=out.submitter_name,
            member_since=summary["member_since"].isoformat() if summary["member_since"] else None,
            active_opportunities=summary["active_opportunities"] or 0,
            verified_listing_id=str(summary["verified_listing_id"]) if summary["verified_listing_id"] else None,
            verified_listing_name=summary["verified_listing_name"],
        )
        habit = await conn.fetchrow("SELECT * FROM vyapar_enquiries.poster_reply_habit($1)", row["poster_id"])
        if habit:
            out.poster.reply_rate = habit["reply_rate"]
            out.poster.reply_speed = habit["reply_speed"]
    if not out.is_poster and out.required_capabilities:
        viewer_caps = await viewer_capabilities(conn, ctx.member_id)  # [L14] own + active listings' skills
        if viewer_caps:
            mine = set(viewer_caps)
            out.capability_match = [c in mine for c in out.required_capabilities]
    if not out.is_poster:  # [FR32] detail view event, never with member identity
        await log_events(conn, "opportunity", [row["id"]], "view", "opportunity_detail", {str(row["id"])} if out.sponsored else set())
    # [Backend A] workstream B's enrichers (seeker protection, poster badges).
    extra = await hooks.run_opportunity_enrichers(conn, ctx, lang, out.model_dump(mode="json"))
    out.seeker_protection = extra.get("seeker_protection")
    out.poster_badges = extra.get("poster_badges") or []
    out.precall_actions = extra.get("precall_actions")
    out.poster_paid_on_time = extra.get("poster_paid_on_time")
    out.restriction = extra.get("restriction")
    out.applicants_waiting = extra.get("applicants_waiting")
    return out


async def list_similar_opportunities(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    opportunity_id: str,
) -> list[OpportunityOut]:
    """[Opportunity detail rebuild, 2026-09-21] WorkIndia ends every job page
    with "Similar jobs" so a person who isn't the right fit keeps moving
    instead of dead-ending. Same type or any shared required skill, active
    only, never the member's own posts and never anything they hid."""
    base = await conn.fetchrow(
        "SELECT type, required_capabilities FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id
    )
    if base is None:
        raise ApiError(404, "common.error.opportunityNotFound", lang)
    # [Fix, found reading the screen as a member] "same type OR any shared
    # skill" put catering staff and an accounts assistant under a Python
    # developer job — same type ("employment"), nothing else in common. A
    # person reads "similar" as "I could do this instead", so a shared
    # required skill is mandatory; type alone only counts when the base
    # opportunity lists no skills at all.
    caps = list(base["required_capabilities"])
    # [Owner, 2026-09-21: "prioritize the skills as per the person's
    # profile"] Among similar opportunities, the ones that ask for skills
    # the viewer actually has come first; closeness to this one breaks ties.
    viewer_caps = list(
        await viewer_capabilities(conn, ctx.member_id) or []  # [L14] own + active listings' skills
    )
    rows = await conn.fetch(
        """SELECT o.* FROM vyapar_opportunities.opportunities o
            WHERE o.id <> $1 AND o.state = 'active' AND o.poster_id <> $2
              AND (o.deadline IS NULL OR o.deadline >= now())
              AND (CASE WHEN cardinality($4::text[]) > 0
                        THEN o.required_capabilities && $4::text[]
                        ELSE o.type = $3 END)
              AND NOT EXISTS (
                SELECT 1 FROM vyapar_opportunities.member_opportunity mo
                 WHERE mo.opportunity_id = o.id AND mo.member_id = $2 AND mo.hidden_at IS NOT NULL)
            ORDER BY cardinality(ARRAY(SELECT unnest(o.required_capabilities) INTERSECT SELECT unnest($5::text[]))) DESC,
                     cardinality(ARRAY(SELECT unnest(o.required_capabilities) INTERSECT SELECT unnest($4::text[]))) DESC,
                     o.published_at DESC NULLS LAST
            LIMIT 4""",
        opportunity_id, ctx.member_id, base["type"], caps, viewer_caps,
    )
    mine = set(viewer_caps)
    poster_ids = list({r["poster_id"] for r in rows})
    names = {
        n["id"]: n["display_name"]
        for n in await conn.fetch("SELECT id, display_name FROM vyapar_identity.public_names($1::text[])", poster_ids)
    } if poster_ids else {}
    now = datetime.now(timezone.utc)
    out: list[OpportunityOut] = []
    for r in rows:
        card = _row_to_opp(r, ctx.member_id, lang=lang)
        card.submitter_name = names.get(r["poster_id"])
        card.posted_days_ago = (now - r["published_at"]).days if r["published_at"] else None
        card.viewer_matched_labels = labels_for([c for c in r["required_capabilities"] if c in mine], lang)
        out.append(card)
    return out


async def list_matching_profiles(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    opportunity_id: str,
) -> list[ProfileCard]:
    """[Owner, 2026-09-21: "we will have other profiles for you"] The poster
    of an opportunity sees the professionals and businesses who already
    have the skills it asks for, instead of only waiting for responses.
    Poster-only: to anyone else this list would be noise. Only profiles
    that opted in to opportunities (opportunity_participation) appear."""
    row = await conn.fetchrow(
        "SELECT poster_id, required_capabilities, location, lat, lng, work_mode FROM vyapar_opportunities.opportunities WHERE id = $1",
        opportunity_id,
    )
    if row is None:
        raise ApiError(404, "common.error.opportunityNotFound", lang)
    if row["poster_id"] != ctx.member_id:
        return []
    from app.services.taste import taste_or_empty

    # [Start flow 2026-10, decision 14] matching honours distance: an on-site
    # post in Delhi must not suggest people in Kukatpally. With coordinates,
    # profiles beyond the poster's radius are out; without them, only
    # profiles in the same named area are suggested.
    radius = await conn.fetchval("SELECT radius_km FROM vyapar_identity.members WHERE id = $1", ctx.member_id)
    remote = row["work_mode"] == "remote"
    return await recommend_profiles(
        conn,
        skills=list(row["required_capabilities"]),
        categories=[],
        exclude_owner_ids=[ctx.member_id],
        exclude_listing_id=None,
        viewer_locality=row["location"],
        require_opportunity_participation=True,
        lang=lang,
        taste=await taste_or_empty(conn, ctx.member_id),
        within=None if remote else (row["lat"], row["lng"], float(max(radius or 10, 10))),
    )


async def update_opportunity(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    opportunity_id: str,
    body: OpportunityPatch,
) -> OpportunityOut:
    current = await conn.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    if current is None or current["poster_id"] != ctx.member_id:
        raise ApiError(404, "common.error.opportunityNotFound", lang)
    # [TR014] type change after publish re-validates type-specific mandatory
    # fields (compensation for employment; location for local_service) —
    # rejects the save otherwise rather than silently accepting a half-typed record.
    new_type = body.type or current["type"]
    if body.type and body.type != current["type"] and current["state"] != "draft":
        if new_type == "employment" and not (body.compensation or current["compensation"]):
            raise ApiError(422, "opportunities.error.compensationRequired", lang)
        if new_type == "local_service" and not (body.location or current["location"]):
            raise ApiError(422, "opportunities.error.locationRequired", lang)
    # [Backend A] the structured patch is partial: fields sent replace, the
    # rest stay; a type change drops the old type's fields (a salary makes no
    # sense on a freelance project). The merged set is re-validated whole.
    merged = OpportunityStructured() if (body.type and body.type != current["type"]) else structured_from_row(current)
    if body.structured is not None:
        merged = merged.model_copy(update=body.structured.model_dump(exclude_unset=True))
    columns = _normalize_structured(merged, new_type, lang)
    derived = compensation_label(OpportunityStructured(**columns), new_type, current["content_language"] or lang)
    compensation = derived or body.compensation  # the derived line wins; else the caller's free text, else unchanged
    await _seeker_charge_guard(
        ctx, str(current["id"]),
        lang=lang, type_=new_type,
        title=body.title if body.title is not None else current["title"],
        description=body.description if body.description is not None else current["description"],
        requirements=body.requirements if body.requirements is not None else current["requirements"],
        compensation=body.compensation or compensation or current["compensation"],
        columns=columns, candidate_pays=body.candidate_pays,
    )
    _check_precall(body.allow_precall, new_type, lang)
    # A type change to one where pre-accept calling does not apply switches it
    # off rather than refusing the edit (the switch has no meaning there).
    allow_precall = body.allow_precall if body.allow_precall is not None else current["allow_precall"]
    if new_type not in PRECALL_TYPES:
        allow_precall = False

    row = await conn.fetchrow(
        f"""UPDATE vyapar_opportunities.opportunities SET
             title = COALESCE($2, title), type = COALESCE($3, type), description = COALESCE($4, description),
             requirements = COALESCE($5, requirements), compensation = COALESCE($6, compensation),
             value_amount = COALESCE($7, value_amount), location = COALESCE($8, location),
             work_mode = COALESCE($9, work_mode), timing = COALESCE($10, timing),
             required_capabilities = COALESCE($11, required_capabilities),
             response_method = COALESCE($12, response_method), deadline = COALESCE($13, deadline),
             {_structured_set_clause(14)},
             allow_precall = ${14 + len(_STRUCTURED_COLUMNS)},
             precall_channel = COALESCE(${15 + len(_STRUCTURED_COLUMNS)}, precall_channel),
             last_confirmed_at = now(), updated_at = now()
           WHERE id = $1 RETURNING *""",
        opportunity_id, body.title, body.type, body.description, body.requirements, compensation,
        body.value_amount, body.location, body.work_mode, body.timing, body.required_capabilities,
        body.response_method, body.deadline, *_structured_values(columns), allow_precall, body.precall_channel,
    )
    if body.lat is not None or body.location is not None:
        row = await _set_position(conn, row, body.lat, body.lng, body.location, force=True)
    return _row_to_opp(row, ctx.member_id, lang=lang)


# ---------------------------------------------------------------------------
# [TR012] Structured fields, uncertainty marking, contributor confirmation
# (FR12). Approach: `confirm` accepts the list of field names the
# contributor has reviewed and confirmed correct; removes them from
# `unconfirmed_fields` and adds to `confirmed_fields`. `publish` is blocked
# until all four material fields (title/type/location/response_method) are
# confirmed — one server-side gate, not a client-side checklist a modified
# client could bypass.
# Traces to: FR12, TR012
# ---------------------------------------------------------------------------
async def confirm_opportunity_fields(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    opportunity_id: str,
    body: ConfirmFieldsIn,
) -> OpportunityOut:
    current = await conn.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    if current is None or current["poster_id"] != ctx.member_id:
        raise ApiError(404, "common.error.opportunityNotFound", lang)
    confirmed = sorted(set(current["confirmed_fields"]) | set(body.fields))
    unconfirmed = [f for f in current["unconfirmed_fields"] if f not in body.fields]
    row = await conn.fetchrow(
        """UPDATE vyapar_opportunities.opportunities SET confirmed_fields = $2, unconfirmed_fields = $3, updated_at = now()
           WHERE id = $1 RETURNING *""",
        opportunity_id, confirmed, unconfirmed,
    )
    return _row_to_opp(row, ctx.member_id, lang=lang)


async def publish_opportunity(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    opportunity_id: str,
) -> OpportunityOut:
    current = await conn.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    if current is None or current["poster_id"] != ctx.member_id:
        raise ApiError(404, "common.error.opportunityNotFound", lang)
    # [FR53/TR053] the gate every publish path calls before proceeding.
    await require_accepted(conn, ctx.member_id, "privacy", lang)
    await require_accepted(conn, ctx.member_id, "terms", lang)
    if current["state"] not in ("draft",):
        raise ApiError(400, "opportunities.error.alreadyPublished", lang)
    missing = MATERIAL_FIELDS - set(current["confirmed_fields"])
    # title/type are always present (defaulted at create); only require
    # explicit confirmation for fields that were actually marked unconfirmed.
    missing = {f for f in missing if f in current["unconfirmed_fields"]}
    if missing:
        raise ApiError(422, "opportunities.error.confirmRequired", lang, fields=", ".join(sorted(missing)))
    # [Backend A] a job without a salary or a project without a budget gets
    # few and poor responses (WorkIndia and Upwork both require them), so
    # publish needs them — the same one gate every publish path goes through.
    structured = structured_from_row(current)
    await _seeker_charge_guard(
        ctx, str(current["id"]),
        lang=lang, type_=current["type"], title=current["title"], description=current["description"],
        requirements=current["requirements"], compensation=current["compensation"], columns=structured.model_dump(),
    )
    if current["type"] == "employment" and (structured.salary_min_paise is None) != (structured.salary_max_paise is None):
        # [Decision 11] a post saved before fixed pay was allowed: one side is the fixed amount
        fixed = structured.salary_min_paise if structured.salary_min_paise is not None else structured.salary_max_paise
        await conn.execute(
            "UPDATE vyapar_opportunities.opportunities SET salary_min_paise = $2, salary_max_paise = $2, updated_at = now() WHERE id = $1",
            current["id"], fixed,
        )
        structured.salary_min_paise = structured.salary_max_paise = fixed
    if current["type"] == "employment" and (structured.salary_min_paise is None or structured.salary_max_paise is None):
        raise ApiError(422, "opportunities.error.salaryRequired", lang)
    if current["type"] == "freelance" and not has_budget(structured):
        raise ApiError(422, "opportunities.error.budgetRequired", lang)
    # [Trust pack — honest terms] a local-service post must say what the job
    # pays: a budget, or a stated fee basis ("₹300 a visit", "Pay per visit").
    # Jobs (salary) and projects (budget) were already gated above.
    if current["type"] == "local_service" and structured.budget_paise is None and not (current["compensation"] or "").strip():
        raise ApiError(422, "opportunities.error.payBasisRequired", lang, error_code="pay_basis_required",
                       extra={"field": "structured.budget_paise"})
    row = await conn.fetchrow(
        """UPDATE vyapar_opportunities.opportunities SET state='active', published_at=now(), last_confirmed_at=now(), updated_at=now()
           WHERE id=$1 RETURNING *""",
        opportunity_id,
    )
    # [FR40] "an opportunity mentioning advance payment/registration fees" is
    # an automated High flag: published, but auto-limited from distribution
    # pending operator review (automated flags prioritise, never finalise).
    text_blob = " ".join(filter(None, [row["title"], row["description"], row["requirements"], row["compensation"]])).lower()
    if any(pattern in text_blob for pattern in ADVANCE_PAYMENT_PATTERNS):
        await conn.execute(
            "SELECT vyapar_trust_safety.raise_auto_flag('opportunity', $1, $2, 'advance_payment', 'high')", opportunity_id, ctx.member_id
        )
        row = await conn.fetchrow(
            "UPDATE vyapar_opportunities.opportunities SET distribution_limited = true, updated_at = now() WHERE id = $1 RETURNING *",
            opportunity_id,
        )
    return _row_to_opp(row, ctx.member_id, lang=lang)


# ---------------------------------------------------------------------------
# [TR013] Opportunity lifecycle: pause/resume/close/renew (FR13).
# Traces to: FR13, TR013
# ---------------------------------------------------------------------------
async def pause_opportunity(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    opportunity_id: str,
) -> OpportunityOut:
    return await _lifecycle_action(conn, ctx, opportunity_id, lang, from_states={"active", "stale"}, to_state="paused")


async def resume_opportunity(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    opportunity_id: str,
) -> OpportunityOut:
    return await _lifecycle_action(conn, ctx, opportunity_id, lang, from_states={"paused"}, to_state="active", reset_freshness=True)


async def close_opportunity(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    opportunity_id: str,
) -> OpportunityOut:
    out = await _lifecycle_action(conn, ctx, opportunity_id, lang, from_states={"active", "paused", "stale"}, to_state="closed")
    # [Trust pack — close the loop] everyone still waiting gets a polite final answer
    from app.services.close_loop import close_waiting_applicants

    await close_waiting_applicants(conn, {"id": out.id, "poster_id": ctx.member_id, "title": out.title}, "closed")
    return out


class RenewIn(BaseModel):
    deadline: datetime | None = Field(default=None, description="New last date (must be in the future). When omitted and the old one has passed, the post gets its original window again (7 to 30 days, 14 when unknown).")


RENEW_MIN_DAYS, RENEW_MAX_DAYS, RENEW_DEFAULT_DAYS = 7, 30, 14


async def renew_opportunity(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    opportunity_id: str,
    body: RenewIn | None = None,
) -> OpportunityOut:
    current = await conn.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    if current is None or current["poster_id"] != ctx.member_id:
        raise ApiError(404, "common.error.opportunityNotFound", lang)
    if current["state"] == "expired" and current["updated_at"] < datetime.now(timezone.utc) - timedelta(days=90):
        # [FR13] renewing an Expired record older than 90 days re-requires
        # material-field confirmation rather than a bare state flip.
        raise ApiError(422, "opportunities.error.tooOldToRenew", lang)
    # [Backend A, 2026-09-29] A post that expired because its last date
    # passed needs a new one, or renewing it would bring back a post the feed
    # still hides and that still refuses applications.
    now = datetime.now(timezone.utc)
    deadline = current["deadline"]
    if body is not None and body.deadline is not None:
        new_deadline = body.deadline if body.deadline.tzinfo else body.deadline.replace(tzinfo=timezone.utc)
        if new_deadline <= now:
            raise ApiError(422, "opportunities.error.deadlineInPast", lang)
        deadline = new_deadline
    elif deadline is not None and deadline < now:
        start = current["published_at"] or current["created_at"]
        window = (deadline - start).days if start and deadline > start else RENEW_DEFAULT_DAYS
        deadline = now + timedelta(days=max(RENEW_MIN_DAYS, min(RENEW_MAX_DAYS, window)))
    row = await conn.fetchrow(
        """UPDATE vyapar_opportunities.opportunities SET state='active', state_reason=NULL, deadline=$2,
             last_confirmed_at=now(), updated_at=now() WHERE id=$1 RETURNING *""",
        opportunity_id, deadline,
    )
    return _row_to_opp(row, ctx.member_id, lang=lang)


# ---------------------------------------------------------------------------
# [Backend A, 2026-09-29] Lifecycle: active/paused/stale -> expired when the
# post's last date passes (FR13's Expired state; GLOSSARY "Post past its
# date"). The feed already hides such posts and applying is refused; this
# makes the state say so too, and tells the poster in their language, with a
# link to renew. Runs from the hourly loop in main.py; each post is expired
# in its own transaction AS ITS POSTER (the RLS rule every poster update
# follows), so the opportunity.expired domain event and the notification go
# out exactly as if the poster had closed it. Idempotent: an expired post is
# never picked again, and the notification key includes the deadline.
# ---------------------------------------------------------------------------
EXPIRABLE_STATES = ("active", "paused", "stale")


class ExpiryPassOut(BaseModel):
    expired: int
    notified: int


async def run_opportunity_expiry_pass(pool: asyncpg.Pool) -> dict:
    from app.notifications import notify_member

    counts = {"expired": 0, "notified": 0}
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("SELECT set_config('vyapar.service_role', 'dispatcher', true)")
            due = await conn.fetch(
                """SELECT id, poster_id FROM vyapar_opportunities.opportunities
                    WHERE state = ANY($1::text[]) AND deadline < now() ORDER BY deadline LIMIT 500""",
                list(EXPIRABLE_STATES),
            )
    for item in due:
        try:
            async with pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute("SELECT set_config('vyapar.authz_context', $1, true)", item["poster_id"])
                    row = await conn.fetchrow(
                        """UPDATE vyapar_opportunities.opportunities
                              SET state = 'expired', state_reason = 'deadline_passed', updated_at = now()
                            WHERE id = $1 AND state = ANY($2::text[]) AND deadline < now()
                        RETURNING id, poster_id, title, deadline""",
                        item["id"], list(EXPIRABLE_STATES),
                    )
                    if row is None:
                        continue
                    counts["expired"] += 1
                    # [Trust pack — close the loop] applicants still waiting are told, as the poster
                    from app.services.close_loop import close_waiting_applicants

                    await close_waiting_applicants(conn, row, "expired")
                    if await notify_member(
                        conn, member_id=row["poster_id"], template="opportunityExpired", link=f"/opportunities/{row['id']}",
                        idempotency_key=f"opportunity_expired:{row['id']}:{row['deadline'].date().isoformat()}",
                        params={"title": row["title"]},
                    ):
                        counts["notified"] += 1
        except Exception:  # one bad row never stops the pass
            import logging

            logging.getLogger(__name__).exception("opportunity expiry failed for %s", item["id"])
    return counts


async def _lifecycle_action(conn, ctx, opportunity_id, lang: str, *, from_states: set[str], to_state: str, reset_freshness: bool = False) -> OpportunityOut:
    current = await conn.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    if current is None or current["poster_id"] != ctx.member_id:
        raise ApiError(404, "common.error.opportunityNotFound", lang)
    if current["state"] not in from_states:
        raise ApiError(400, "opportunities.error.invalidTransition", lang)
    if reset_freshness:
        row = await conn.fetchrow(
            "UPDATE vyapar_opportunities.opportunities SET state=$2, last_confirmed_at=now(), updated_at=now() WHERE id=$1 RETURNING *",
            opportunity_id, to_state,
        )
    else:
        row = await conn.fetchrow(
            "UPDATE vyapar_opportunities.opportunities SET state=$2, updated_at=now() WHERE id=$1 RETURNING *",
            opportunity_id, to_state,
        )
    return _row_to_opp(row, ctx.member_id, lang=lang)


# ---------------------------------------------------------------------------
# [TR055] Save / Not interested / Share-block-on-removed (FR55).
# Traces to: FR55, TR055
# ---------------------------------------------------------------------------
async def save_opportunity(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    opportunity_id: str,
) -> OpportunityOut:
    row = await conn.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    if row is None:
        raise ApiError(404, "common.error.opportunityNotFound", lang)
    await conn.execute(
        """INSERT INTO vyapar_opportunities.member_opportunity (member_id, opportunity_id, saved_at) VALUES ($1,$2,now())
           ON CONFLICT (member_id, opportunity_id) DO UPDATE SET saved_at = now()""",
        ctx.member_id, opportunity_id,
    )
    await log_events(conn, "opportunity", [row["id"]], "save", "opportunity_detail")  # [FR32]
    return _row_to_opp(row, ctx.member_id, saved=True, lang=lang)


async def unsave_opportunity(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    opportunity_id: str,
) -> OpportunityOut:
    row = await conn.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    if row is None:
        raise ApiError(404, "common.error.opportunityNotFound", lang)
    await conn.execute(
        "UPDATE vyapar_opportunities.member_opportunity SET saved_at = NULL WHERE member_id = $1 AND opportunity_id = $2",
        ctx.member_id, opportunity_id,
    )
    return _row_to_opp(row, ctx.member_id, saved=False, lang=lang)


class NotInterestedIn(BaseModel):
    reason: Literal["too_far", "wrong_type", "not_my_capability", "value_too_low", "wrong_timing", "already_found", "not_interested"]


class HiddenOut(BaseModel):
    hidden: bool


class SharedOut(BaseModel):
    shared: bool


class OpenedOut(BaseModel):
    opened: bool


async def mark_opportunity_not_interested(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    opportunity_id: str,
    body: NotInterestedIn,
) -> HiddenOut:
    await conn.execute(
        """INSERT INTO vyapar_opportunities.member_opportunity (member_id, opportunity_id, hidden_at, hidden_reason)
           VALUES ($1,$2,now(),$3)
           ON CONFLICT (member_id, opportunity_id) DO UPDATE SET hidden_at = now(), hidden_reason = $3""",
        ctx.member_id, opportunity_id, body.reason,
    )
    return HiddenOut(hidden=True)


async def share_opportunity(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    opportunity_id: str,
) -> SharedOut:
    row = await conn.fetchrow("SELECT state FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    if row is None:
        raise ApiError(404, "common.error.opportunityNotFound", lang)
    if row["state"] == "removed":
        # [FR55] Sharing a Removed item is blocked at the API layer.
        raise ApiError(400, "opportunities.error.removedCannotShare", lang)
    await conn.execute(
        """INSERT INTO vyapar_opportunities.member_opportunity (member_id, opportunity_id, shared_at) VALUES ($1,$2,now())
           ON CONFLICT (member_id, opportunity_id) DO UPDATE SET shared_at = now()""",
        ctx.member_id, opportunity_id,
    )
    return SharedOut(shared=True)


async def record_opportunity_external_open(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    opportunity_id: str,
) -> OpenedOut:
    """[FR55] Records that the member opened a Public/External item's
    source link — a leave-app notice is the frontend's job; this just logs
    the action for TR048's later review use."""
    await conn.execute(
        """INSERT INTO vyapar_opportunities.member_opportunity (member_id, opportunity_id, external_opened_at) VALUES ($1,$2,now())
           ON CONFLICT (member_id, opportunity_id) DO UPDATE SET external_opened_at = now()""",
        ctx.member_id, opportunity_id,
    )
    return OpenedOut(opened=True)


# ---------------------------------------------------------------------------
# [Backend A, 2026-09-28] Suggestions: what to change to get more or better
# responses, computed from what is missing or restrictive on the row.
# WorkIndia shows an employer "Lower min qualification to 12th -> likely
# more responses" while the job is being posted; Upwork nudges for a budget
# and screening questions. Rule-based, poster-only, localized; each item
# names the field so the composer can focus it.
# ---------------------------------------------------------------------------
Impact = Literal["more_responses", "better_fit", "trust"]


class SuggestionOut(BaseModel):
    code: str = Field(description="Stable rule id, e.g. lower_qualification")
    field: str | None = Field(default=None, description="The opportunity or structured field the tip is about")
    impact: Impact
    message: str = Field(description="Localized tip")


class SuggestionsOut(BaseModel):
    opportunity_id: str
    suggestions: list[SuggestionOut]


def compute_suggestions(row: asyncpg.Record, lang: str) -> list[SuggestionOut]:
    s = structured_from_row(row)
    type_ = row["type"]
    tips: list[tuple[str, str | None, str]] = []  # (code, field, impact)

    def add(code: str, field: str | None, impact: str) -> None:
        tips.append((code, field, impact))

    if len((row["description"] or "").strip()) < 80:
        add("expand_description", "description", "better_fit")
    if not row["required_capabilities"]:
        add("add_skills", "required_capabilities", "better_fit")
    elif len(row["required_capabilities"]) > 5:
        add("fewer_skills", "required_capabilities", "more_responses")
    if row["work_mode"] == "on_site" and not row["location"]:
        add("add_location", "location", "more_responses")
    if row["work_mode"] == "on_site" and type_ in ("employment", "freelance"):
        add("consider_remote", "work_mode", "more_responses")

    if type_ == "employment":
        if s.salary_min_paise is None or s.salary_max_paise is None:
            add("add_salary", "salary_min_paise", "more_responses")
        if s.min_qualification in ("graduate", "postgraduate"):
            add("lower_qualification", "min_qualification", "more_responses")
        if s.english_level in ("good", "fluent"):
            add("relax_english", "english_level", "more_responses")
        if (s.experience_min_months or 0) > 24:
            add("lower_experience", "experience_min_months", "more_responses")
        if not s.job_timings:
            add("add_job_timings", "job_timings", "better_fit")
        if not s.interview_details:
            add("add_interview_details", "interview_details", "trust")
        if s.openings is None:
            add("add_openings", "openings", "trust")
        if s.shift is None:
            add("add_shift", "shift", "better_fit")
    elif type_ == "freelance":
        if not has_budget(s):
            add("add_budget", "budget_type", "more_responses")
        if s.duration is None:
            add("add_duration", "duration", "better_fit")
        if not s.screening_questions:
            add("add_screening_question", "screening_questions", "better_fit")
        if s.experience_level == "expert":
            add("relax_experience_level", "experience_level", "more_responses")
        if not row["deadline"]:
            add("add_deadline", "deadline", "more_responses")
    elif type_ == "local_service":
        if s.preferred_date is None:
            add("add_preferred_date", "preferred_date", "better_fit")
        if s.budget_paise is None:
            add("add_local_budget", "budget_paise", "more_responses")
        if s.urgency is None:
            add("add_urgency", "urgency", "better_fit")

    return [
        SuggestionOut(code=code, field=field, impact=impact, message=translate(f"opportunities.suggestion.{code}", lang))
        for code, field, impact in tips
    ]


async def get_opportunity_suggestions(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    opportunity_id: str,
) -> SuggestionsOut:
    row = await conn.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    if row is None or row["poster_id"] != ctx.member_id:
        raise ApiError(404, "common.error.opportunityNotFound", lang)
    return SuggestionsOut(opportunity_id=str(row["id"]), suggestions=compute_suggestions(row, lang))


async def list_my_opportunities_page(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    limit: int = DEFAULT_LIMIT,
    cursor: str | None = None,
) -> Page[OpportunityOut]:
    """[Refactor A] Cursor-paged `list_my_opportunities` — same rows, same order."""
    return paginate(await list_my_opportunities(conn, ctx, lang), limit, cursor, lang)

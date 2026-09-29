# [IMP42 — Refactor C (AI)] Closed vocabularies and the validators that are
# the ONLY way a provider's answer reaches a caller.
#
# Every enum below is a product decision (opportunity types from
# services/opportunities.py, the typed employment/freelance/local_service
# fields workstream A is adding in migration 018, taxonomy capability slugs
# read live from vyapar_listings.taxonomy_terms). A provider — Claude or the
# keyword engine — may only answer inside these sets: an invented type, slug,
# tip code or score is dropped, clamped or ignored, never passed on. That is
# what makes the AI safe to put in front of a person who then confirms.
from __future__ import annotations

import re
from typing import Any

# ---- opportunity model ------------------------------------------------------

OPPORTUNITY_TYPES = ("employment", "freelance", "local_service", "partnership", "training", "community")
WORK_MODES = ("on_site", "remote", "both")

INCENTIVE_TYPES = ("none", "fixed_plus_incentive", "incentive_only")
SHIFTS = ("day", "night", "rotational", "flexible")
MIN_QUALIFICATIONS = ("below_10th", "10th", "12th", "diploma", "iti", "graduate", "postgraduate", "any")
ENGLISH_LEVELS = ("none", "basic", "good", "fluent")
# What a job may ask the worker to bring. Workstream A stores the column as
# text[]; this is the vocabulary both sides agree on.
REQUIRES_ASSETS = ("two_wheeler", "four_wheeler", "driving_licence", "smartphone", "laptop", "own_tools")

BUDGET_TYPES = ("fixed", "hourly")
DURATIONS = ("under_1_week", "1_4_weeks", "1_3_months", "3_6_months", "over_6_months", "ongoing")
EXPERIENCE_LEVELS = ("entry", "intermediate", "expert")

URGENCIES = ("today", "this_week", "flexible")

# Field names used by `confidence`, `missing` and `questions`. Stable codes:
# the web app maps them to its own form controls.
DRAFT_FIELDS = (
    "type", "title", "description", "location", "work_mode", "timing", "required_capabilities",
    "salary", "incentive_type", "openings", "shift", "job_timings", "interview_details",
    "min_qualification", "english_level", "experience", "requires_assets",
    "budget", "budget_type", "hourly_rate", "duration", "experience_level", "screening_questions",
    "preferred_date", "urgency",
)

# What a poster must still tell us before the draft is worth publishing.
ESSENTIAL_FIELDS: dict[str, tuple[str, ...]] = {
    "employment": ("salary", "job_timings", "min_qualification", "experience"),
    "freelance": ("budget", "duration"),
    "local_service": ("preferred_date", "urgency", "budget"),
    "partnership": (),
    "training": ("timing",),
    "community": ("timing",),
}
COMMON_ESSENTIALS = ("title", "type", "description", "location")

# ---- shortlist, tips, proposal ---------------------------------------------

REASON_CODES = (
    "capability_fit", "location_fit", "experience_fit", "trust_fit", "timing_fit", "value_fit",
    "cover_text_specific", "bid_within_budget", "quick_to_apply",
)
RISK_CODES = (
    "no_capability_overlap", "partial_capability_overlap", "far_away", "unverified", "no_cover_text",
    "bid_above_budget", "bid_far_below_budget", "no_experience_listed", "not_available_now", "no_public_profile",
)

TIP_CODES = (
    "add_title", "shorten_title", "add_description", "add_location", "set_remote_or_both", "add_capabilities",
    "fewer_capabilities", "add_salary", "add_job_timings", "add_openings", "lower_min_qualification",
    "relax_english_level", "reduce_experience", "add_interview_details", "add_budget", "add_hourly_rate",
    "add_duration", "add_screening_questions", "add_preferred_date", "set_urgency", "add_timing",
    "add_deadline", "mention_incentives",
)
IMPACTS = ("high", "medium", "low")

PROPOSAL_IMPROVEMENT_CODES = (
    "mention_matching_skills", "mention_experience", "state_availability", "state_price",
    "answer_screening_questions", "keep_it_short", "remove_contact_details", "be_specific_to_this_work",
    "polite_opening", "clear_next_step",
)

MAX_TITLE = 120
MAX_DESCRIPTION = 2000
MAX_SHORT = 200
MAX_COVER = 1200
MAX_CAPABILITIES = 8
MAX_QUESTIONS = 5
MAX_LIST = 6

_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_PHONE = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


# Label words that head a notice without naming the work: "Job opening:",
# "Urgent -", "We are hiring:", "ज़रूरत है:", "ఖాళీలు:".
_TITLE_LABEL = re.compile(
    r"^\s*(?:(?:we\s+are\s+|we're\s+)?hiring(?:\s+now)?|urgent(?:ly)?(?:\s+(?:requirement|required|hiring))?|job\s+(?:opening|alert|vacancy|post)s?|"
    r"(?:new\s+)?openings?|vacanc(?:y|ies)|requirement|required|wanted|notice|announcement|attention|alert|update|job|jobs|"
    r"ज़रूरत\s+है|जरूरत\s+है|आवश्यकता(?:\s+है)?|भर्ती|नौकरी|तुरंत|అవసరం|ఖాళీలు|ఉద్యోగం|ఉద్యోగాలు|అత్యవసరం)\s*[:\-–—|!]+\s*",
    re.I,
)


def strip_title_label(title: str) -> str:
    """"Job opening: Sales executive" -> "Sales executive"; "Urgent:" -> "".
    Only a known label is removed, so "Kukatpally: delivery boys" keeps its
    place name. Shared by the rules reader and Claude's answer validation."""
    stripped = _TITLE_LABEL.sub("", title, count=1).strip(" :-–—|")
    if stripped != title.strip() and stripped[:1].isascii() and stripped[:1].islower():
        stripped = stripped[0].upper() + stripped[1:]  # "Urgent: delivery boys…" -> "Delivery boys…"
    return stripped


def redact_contacts(text: str) -> str:
    """Phone numbers and e-mail addresses never travel to a provider."""
    text = _PHONE.sub("[phone]", text)
    return _EMAIL.sub("[email]", text)


# ---- primitives -------------------------------------------------------------

def _enum(value: Any, allowed: tuple[str, ...]) -> str | None:
    if not isinstance(value, str):
        return None
    v = value.strip().lower()
    return v if v in allowed else None


def _text(value: Any, limit: int) -> str | None:
    if not isinstance(value, str):
        return None
    v = " ".join(value.split()).strip()
    return v[:limit] if v else None


def _int(value: Any, low: int = 0, high: int = 10**12) -> int | None:
    try:
        if value is None or value == "":
            return None
        n = int(round(float(value)))
    except (TypeError, ValueError):
        return None
    if n <= low and low == 0:
        return None  # 0 means "not given" for every money/count field
    return max(low, min(high, n))


def _float01(value: Any) -> float | None:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, min(1.0, round(f, 2)))


def _range(low: Any, high: Any, cap: int) -> tuple[int | None, int | None]:
    lo, hi = _int(low, 0, cap), _int(high, 0, cap)
    if lo is not None and hi is not None and lo > hi:
        lo, hi = hi, lo
    return lo, hi


def _enum_list(values: Any, allowed: tuple[str, ...] | frozenset[str] | set[str], limit: int) -> list[str]:
    if not isinstance(values, list):
        return []
    out: list[str] = []
    for v in values:
        if isinstance(v, str):
            s = v.strip().lower()
            if s in allowed and s not in out:
                out.append(s)
        if len(out) >= limit:
            break
    return out


def rupees_to_paise(rupees: int | None) -> int | None:
    return None if rupees is None else rupees * 100


# ---- draft ------------------------------------------------------------------

def clean_draft(raw: Any, capability_slugs: set[str]) -> dict[str, Any]:
    """Validate a provider's draft. Money arrives in rupees (what people say
    and what the model reads) and leaves in paise (what the schema stores).
    Only the typed block for the resolved type is kept."""
    raw = raw if isinstance(raw, dict) else {}
    type_ = _enum(raw.get("type"), OPPORTUNITY_TYPES) or "employment"
    out: dict[str, Any] = {
        "type": type_,
        "title": _text(strip_title_label(raw["title"]) if isinstance(raw.get("title"), str) else None, MAX_TITLE),
        "description": _text(raw.get("description"), MAX_DESCRIPTION),
        "location": _text(raw.get("location"), 80),
        "work_mode": _enum(raw.get("work_mode"), WORK_MODES),
        "timing": _text(raw.get("timing"), MAX_SHORT),
        "required_capabilities": _enum_list(raw.get("required_capabilities"), capability_slugs, MAX_CAPABILITIES),
        "employment": None,
        "freelance": None,
        "local_service": None,
    }
    if type_ == "employment":
        e = raw.get("employment") if isinstance(raw.get("employment"), dict) else {}
        smin, smax = _range(e.get("salary_min_rupees"), e.get("salary_max_rupees"), 10**8)
        xmin, xmax = _range(e.get("experience_min_months"), e.get("experience_max_months"), 600)
        out["employment"] = {
            "salary_min_paise": rupees_to_paise(smin),
            "salary_max_paise": rupees_to_paise(smax),
            "incentive_type": _enum(e.get("incentive_type"), INCENTIVE_TYPES),
            "openings": _int(e.get("openings"), 0, 500),
            "shift": _enum(e.get("shift"), SHIFTS),
            "job_timings": _text(e.get("job_timings"), MAX_SHORT),
            "interview_details": _text(e.get("interview_details"), MAX_SHORT),
            "min_qualification": _enum(e.get("min_qualification"), MIN_QUALIFICATIONS),
            "english_level": _enum(e.get("english_level"), ENGLISH_LEVELS),
            "experience_min_months": xmin if xmin is not None else (0 if e.get("fresher_ok") is True else None),
            "experience_max_months": xmax,
            "requires_assets": _enum_list(e.get("requires_assets"), REQUIRES_ASSETS, MAX_LIST),
        }
    elif type_ == "freelance":
        f = raw.get("freelance") if isinstance(raw.get("freelance"), dict) else {}
        bmin, bmax = _range(f.get("budget_min_rupees"), f.get("budget_max_rupees"), 10**9)
        hmin, hmax = _range(f.get("hourly_rate_min_rupees"), f.get("hourly_rate_max_rupees"), 10**6)
        questions = [q for q in (_text(x, MAX_SHORT) for x in (f.get("screening_questions") or [])) if q]
        out["freelance"] = {
            "budget_type": _enum(f.get("budget_type"), BUDGET_TYPES) or ("hourly" if (hmin or hmax) and not (bmin or bmax) else ("fixed" if (bmin or bmax) else None)),
            "budget_min_paise": rupees_to_paise(bmin),
            "budget_max_paise": rupees_to_paise(bmax),
            "hourly_rate_min_paise": rupees_to_paise(hmin),
            "hourly_rate_max_paise": rupees_to_paise(hmax),
            "duration": _enum(f.get("duration"), DURATIONS),
            "experience_level": _enum(f.get("experience_level"), EXPERIENCE_LEVELS),
            "screening_questions": [{"text": q} for q in questions[:MAX_QUESTIONS]],
        }
    elif type_ == "local_service":
        s = raw.get("local_service") if isinstance(raw.get("local_service"), dict) else {}
        date = _text(s.get("preferred_date"), 10)
        out["local_service"] = {
            "preferred_date": date if date and _DATE.match(date) else None,
            "budget_paise": rupees_to_paise(_int(s.get("budget_rupees"), 0, 10**8)),
            "urgency": _enum(s.get("urgency"), URGENCIES),
        }

    confidence: dict[str, float] = {}
    conf_raw = raw.get("confidence")
    pairs = conf_raw.items() if isinstance(conf_raw, dict) else (
        (c.get("field"), c.get("value")) for c in conf_raw if isinstance(c, dict)
    ) if isinstance(conf_raw, list) else []
    for name, value in pairs:
        if name in DRAFT_FIELDS and (v := _float01(value)) is not None:
            confidence[name] = v
    out["confidence"] = confidence
    out["missing"] = _enum_list(raw.get("missing"), DRAFT_FIELDS, len(DRAFT_FIELDS))
    return out


def has_value(draft: dict[str, Any], field: str) -> bool:
    """Does the validated draft carry a value for this DRAFT_FIELDS code?"""
    t = draft.get("type")
    e, f, s = draft.get("employment") or {}, draft.get("freelance") or {}, draft.get("local_service") or {}
    match field:
        case "type" | "title" | "description" | "location" | "work_mode" | "timing":
            return bool(draft.get(field))
        case "required_capabilities":
            return bool(draft.get("required_capabilities"))
        case "salary":
            return bool(e.get("salary_min_paise") or e.get("salary_max_paise"))
        case "experience":
            return e.get("experience_min_months") is not None or e.get("experience_max_months") is not None
        case "incentive_type" | "openings" | "shift" | "job_timings" | "interview_details" | "min_qualification" | "english_level":
            return bool(e.get(field))
        case "requires_assets":
            return bool(e.get("requires_assets"))
        case "budget":
            if t == "freelance":
                return bool(f.get("budget_min_paise") or f.get("budget_max_paise") or f.get("hourly_rate_min_paise") or f.get("hourly_rate_max_paise"))
            return bool(s.get("budget_paise"))
        case "hourly_rate":
            return bool(f.get("hourly_rate_min_paise") or f.get("hourly_rate_max_paise"))
        case "budget_type" | "duration" | "experience_level":
            return bool(f.get(field))
        case "screening_questions":
            return bool(f.get("screening_questions"))
        case "preferred_date" | "urgency":
            return bool(s.get(field))
    return False


def compute_missing(draft: dict[str, Any], suggested: list[str]) -> list[str]:
    """What to ask the poster: the essentials for this type that have no
    value, plus anything the provider flagged that is genuinely empty."""
    t = draft.get("type") or "employment"
    wanted = list(COMMON_ESSENTIALS) + list(ESSENTIAL_FIELDS.get(t, ()))
    if draft.get("work_mode") == "remote":
        wanted = [w for w in wanted if w != "location"]
    for s in suggested:
        if s not in wanted:
            wanted.append(s)
    return [w for w in wanted if not has_value(draft, w)]


# ---- shortlist --------------------------------------------------------------

def clean_shortlist(raw: Any, refs: list[str]) -> dict[str, dict[str, Any]]:
    """{ref: {match_score 1-10, reasons[], risks[], summary}} for known refs only."""
    items = raw.get("applicants") if isinstance(raw, dict) else raw
    out: dict[str, dict[str, Any]] = {}
    known = set(refs)
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        ref = item.get("ref")
        if ref not in known or ref in out:
            continue
        score = _int(item.get("match_score"), 1, 10)
        out[ref] = {
            "match_score": score if score is not None else 1,
            "reasons": _enum_list(item.get("reasons"), REASON_CODES, 3),
            "risks": _enum_list(item.get("risks"), RISK_CODES, 3),
            "summary": _text(item.get("summary"), 240),
        }
    return out


# ---- tips -------------------------------------------------------------------

def clean_tips(raw: Any) -> list[dict[str, Any]]:
    items = raw.get("tips") if isinstance(raw, dict) else raw
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        code = _enum(item.get("code"), TIP_CODES)
        if code is None or code in seen:
            continue
        seen.add(code)
        out.append({
            "code": code,
            "impact": _enum(item.get("impact"), IMPACTS) or "medium",
            "text": _text(item.get("text"), MAX_SHORT),
        })
        if len(out) >= 8:
            break
    return out


# ---- proposal ---------------------------------------------------------------

def clean_proposal(raw: Any) -> dict[str, Any]:
    raw = raw if isinstance(raw, dict) else {}
    return {
        "cover_text": _text(raw.get("cover_text"), MAX_COVER),
        "improvements": _enum_list(raw.get("improvements"), PROPOSAL_IMPROVEMENT_CODES, 4),
    }

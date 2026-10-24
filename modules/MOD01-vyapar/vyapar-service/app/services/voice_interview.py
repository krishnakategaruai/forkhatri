# [Voice interview, 2026-09-30 — owner: "Voice should like, we ask questions
# in their perspective and waits until we receive answer!"]
#
# Voice posting and profile setup become a guided conversation: the app asks
# ONE question at a time, in the person's own everyday words, speaks it, waits
# for the answer, reads back what it understood for a yes/no, then asks the
# next one — only for what is still missing — and ends with a summary to
# review. It never publishes or saves anything by itself.
#
# Two operations, both stateless (the client keeps the confirmed answers and
# sends them back on every turn), deterministic and fast (no model is needed
# to choose a question):
#
#   next_question(flow, language, answers, skipped)
#       the next question for what is missing, or {done, summary, draft}.
#       Fields needed to publish come first, optional ones last; anything the
#       app already knows is never asked (profile: name, area, skills,
#       experience, tools from the member's own profile; posts: the area is
#       offered from the saved locality as a yes/no).
#   interpret_answer(flow, field, language, text, answers)
#       reads one spoken answer with the rules readers (money ranges in any
#       script, localities, hours, headcounts, studies, skills against the
#       taxonomy, days like "kal" / "repu"), recognises control words (skip,
#       yes, no, repeat) in en/hi/te, runs the scam shield on what a poster
#       says, and returns a typed value plus a read-back sentence in the
#       glossary's formats ("₹15,000 to ₹18,000 a month", "in Kukatpally",
#       "2 people"). Claude is asked only when AI_PROVIDER=anthropic and the
#       rules could not read the answer; it rewrites the answer into plain
#       words that the SAME rules then read, so its output passes the same
#       validation (and the member's daily AI allowance and audit row apply).
#
# The finished draft is the shape draftOpportunity returns (plus the date and
# pay basis a spoken post can carry), or the body of PATCH /v1/me/profile.
# The person reviews it and posts or saves through the ordinary endpoints.
# Traces to: FR01, FR11, FR12, FR44, REFACTOR-PLAN.md (AI workstream C)
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field as dc_field
from datetime import date, datetime, timedelta, timezone
from typing import Annotated, Any, Literal

import asyncpg
from pydantic import BaseModel, Field

from app.errors import ApiError
from app.geo import _PLACES as GAZETTEER, resolve_place
from app.i18n import _catalog, _lookup, translate, translate_count
from app.identity import AuthzContext
from app.integrations.ai import AiUnavailable, get_ai_provider, get_ai_settings
from app.integrations.ai.localities import _strip_telugu_suffix, find_known_locality, skeleton
from app.integrations.ai.rules_provider import (
    _ASSETS,
    _DAILY,
    _HOURLY,
    _SHIFT,
    draft_from_text,
    find_capabilities,
    find_experience_months,
    find_money,
    find_openings,
    find_qualification,
    find_timings,
    strip_contacts,
)
from app.integrations.ai.spoken import _NUM_WORDS as NUM_WORDS
from app.integrations.ai.spoken import control_intent, first_int, norm, parse_day, parse_hours, parse_name, words_to_digits
from app.integrations.ai.vocab import (
    MIN_QUALIFICATIONS,
    REQUIRES_ASSETS,
    SHIFTS,
    URGENCIES,
    clean_draft,
    compute_missing,
)
from app.services import ai as ai_svc
from app.services import scam_shield
from app.services.ai import DraftOut, EmploymentFields, FreelanceFields, LocalServiceFields
from app.services.opportunities import OpportunityStructured, compensation_label, format_inr, legacy_compensation_label
from app.services.profile import profile_row
from app.taxonomy_cache import labels_for, term_for

Flow = Literal["post_job", "post_local", "post_project", "profile"]
Language = Literal["en", "hi", "te", "mr", "kn"]
Kind = Literal["text", "choice", "number", "yesno"]
Intent = Literal["answer", "skip", "yes", "no", "repeat", "unclear"]

FLOW_TYPE = {"post_job": "employment", "post_local": "local_service", "post_project": "freelance"}

# (field, optional). Fields needed to publish first, optional ones last.
FLOWS: dict[str, tuple[tuple[str, bool], ...]] = {
    "post_job": (("work", False), ("location", False), ("salary", False), ("openings", False), ("job_timings", False),
                 ("min_qualification", True), ("experience", True), ("requires_assets", True)),
    "post_local": (("work", False), ("location", False), ("when", False), ("budget", False)),
    "post_project": (("work", False), ("budget", False), ("deadline", False), ("work_mode", False), ("location", False)),
    "profile": (("name", False), ("work", False), ("locality", False), ("experience_years", True), ("own_assets", True)),
}
KINDS: dict[str, Kind] = {
    "work": "text", "location": "text", "locality": "text", "name": "text", "salary": "number", "openings": "number",
    "job_timings": "text", "min_qualification": "choice", "experience": "number", "requires_assets": "choice",
    "when": "text", "budget": "number", "deadline": "text", "work_mode": "choice", "experience_years": "number",
    "own_assets": "choice",
}
# What "I didn't catch …" names, per field.
_MISSED = {"salary": "amount", "budget": "amount", "location": "area", "locality": "area", "openings": "number",
           "experience_years": "number", "experience": "number", "job_timings": "hours", "when": "day", "deadline": "day",
           "name": "name", "work_mode": "choice", "min_qualification": "choice", "requires_assets": "choice", "own_assets": "choice"}
QUAL_ORDER = ("any", "below_10th", "10th", "12th", "iti", "diploma", "graduate", "postgraduate")
WORK_MODES = ("remote", "on_site", "both")
MAX_TEXT = 1000

# ---- request / response models ----------------------------------------------


class InterviewOption(BaseModel):
    value: Any
    label: str


class InterviewProgress(BaseModel):
    asked: int = Field(description="Position of this question among the questions this interview asks (1-based)")
    total: int = Field(description="How many questions this interview asks; things already known are not counted")


class SummaryItem(BaseModel):
    field: str
    label: str
    value_label: str


class InterviewPostDraft(DraftOut):
    """draftOpportunity's shape, plus what a spoken post can also carry."""

    draft_type: Literal["opportunity"] = "opportunity"
    deadline: str | None = Field(default=None, description="Project: the date it is needed by (YYYY-MM-DD) — createOpportunity.deadline")
    compensation: str | None = Field(default=None, description="Local service: how it is paid when no budget was given (\"₹300 per visit\", \"Pay per visit\", \"negotiable\")")


class InterviewProfileDraft(BaseModel):
    """The body for PATCH /v1/me/profile (only what the interview learned)."""

    draft_type: Literal["profile"] = "profile"
    name: str | None = None
    locality: str | None = None
    capabilities: list[str] | None = None
    headline: str | None = None
    experience_years: int | None = None
    own_assets: list[str] | None = None


class InterviewNextRequest(BaseModel):
    flow: Flow
    language: Language | None = Field(default=None, description="Defaults to the request locale")
    answers: dict[str, Any] = Field(default_factory=dict, description="Confirmed values, keyed by field, exactly as interpretInterviewAnswer returned them")
    skipped: list[str] = Field(default_factory=list, description="Fields the person chose to skip")


class InterviewNextOut(BaseModel):
    done: bool
    field: str | None = None
    question: str | None = None
    hint: str | None = None
    kind: Kind | None = None
    options: list[InterviewOption] | None = None
    optional: bool | None = None
    progress: InterviewProgress | None = None
    summary: list[SummaryItem] | None = None
    draft: Annotated[InterviewPostDraft | InterviewProfileDraft, Field(discriminator="draft_type")] | None = Field(
        default=None, description="draft_type=opportunity: draftOpportunity's shape (+deadline, compensation) for createOpportunity; "
                                  "draft_type=profile: the PATCH /v1/me/profile body")


class InterviewInterpretRequest(BaseModel):
    flow: Flow
    field: str
    language: Language | None = None
    text: str = Field(default="", max_length=4000, description="The transcript of what the person said")
    answers: dict[str, Any] = Field(default_factory=dict)


class InterviewInterpretOut(BaseModel):
    understood: bool
    value: Any = None
    readback: str | None = None
    confidence: float = 0.0
    alternatives: list[Any] = Field(default_factory=list)
    intent: Intent
    reprompt: str | None = None
    needs_confirmation: bool = Field(default=True, description="False when the answer was itself a yes/no (no read-back needed)")
    also: dict[str, Any] = Field(default_factory=dict, description="Other fields the same answer stated (first answer only); merge them once the person says yes")
    source: Literal["rules", "ai"] = "rules"


# ---- context ------------------------------------------------------------------


@dataclass
class Ctx:
    flow: str
    lang: str
    today: date
    saved_locality: str | None = None
    known: dict[str, Any] = dc_field(default_factory=dict)  # profile: what the profile already has
    terms: list[dict[str, Any]] = dc_field(default_factory=list)
    localities: list[str] = dc_field(default_factory=list)


def _today() -> date:
    return (datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)).date()  # India


async def _load(conn: asyncpg.Connection, ctx: AuthzContext, flow: str, lang: str, *, need_terms: bool = False) -> Ctx:
    member = await conn.fetchrow(
        "SELECT id, display_name, locality FROM vyapar_identity.members WHERE id = $1", ctx.member_id
    )
    row = await profile_row(conn, ctx.member_id)
    c = Ctx(flow=flow, lang=lang, today=_today())
    c.saved_locality = (row["locality"] if row is not None and row["locality"] else None) or (member["locality"] if member else None)
    if flow == "profile":
        real_name = member["display_name"] if member and member["display_name"] and member["display_name"] != member["id"] else None
        name = (row["name"] if row is not None else None) or real_name
        if name:
            c.known["name"] = name
        if c.saved_locality:
            c.known["locality"] = c.saved_locality
        if row is not None:
            if list(row["capabilities"] or []):
                c.known["work"] = list(row["capabilities"])
                c.known["headline"] = row["headline"]
            if row["experience_years"] is not None:
                c.known["experience_years"] = row["experience_years"]
            own = _col(row, "own_assets")
            if own:
                c.known["own_assets"] = list(own)
            if row["headline"]:
                c.known["headline"] = row["headline"]
    if need_terms:
        c.terms = await ai_svc._capability_terms(conn)
        c.localities = sorted({p[0] for p in GAZETTEER} | set(await ai_svc._known_localities(conn)))
    return c


def _col(row: asyncpg.Record, name: str) -> Any:
    try:
        return row[name]
    except (KeyError, IndexError):
        return None


# ---- small helpers ------------------------------------------------------------


def _t(key: str, lang: str, **params: Any) -> str:
    return translate(f"voice.{key}", lang, **params)


def _t_opt(key: str, lang: str, **params: Any) -> str | None:
    """The text when the catalog has this key (a flow-specific hint), else None."""
    if _lookup(_catalog("en", "voice"), key) is None:
        return None
    return translate(f"voice.{key}", lang, **params)


def _fields(flow: str) -> tuple[tuple[str, bool], ...]:
    return FLOWS[flow]


def _applies(c: Ctx, name: str, answers: dict[str, Any]) -> bool:
    """A field that does not apply is neither asked nor counted."""
    if c.flow == "profile" and name in c.known:
        return False
    if c.flow == "post_project" and name == "location" and answers.get("work_mode") == "remote":
        return False
    return True


def _question(c: Ctx, name: str) -> str:
    if name in ("location",) and c.flow != "profile" and c.saved_locality:
        return _t(f"q.{c.flow}.location_confirm", c.lang, place=c.saved_locality)
    return _t(f"q.{c.flow}.{name}", c.lang)


def _kind(c: Ctx, name: str) -> Kind:
    if name == "location" and c.flow != "profile" and c.saved_locality:
        return "yesno"
    return KINDS[name]


def _hint(c: Ctx, name: str) -> str | None:
    if name == "location" and c.flow != "profile" and c.saved_locality:
        return _t_opt("hint.location_confirm", c.lang)
    return _t_opt(f"hint.{c.flow}.{name}", c.lang) or _t_opt(f"hint.{name}", c.lang)


def _options(c: Ctx, name: str) -> list[InterviewOption] | None:
    if name == "work_mode":
        return [InterviewOption(value=v, label=_t(f"option.work_mode.{v}", c.lang)) for v in WORK_MODES]
    if name == "min_qualification":
        return [InterviewOption(value=v, label=_t(f"qualification.{v}", c.lang)) for v in QUAL_ORDER]
    if name in ("requires_assets", "own_assets"):
        return [InterviewOption(value=v, label=_cap(_t(f"asset.{v}", c.lang))) for v in (*REQUIRES_ASSETS, "none")]
    return None


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:] if s[:1].isascii() else s


def _lang(requested: str | None, locale: str) -> str:
    return requested or (locale if locale in ("en", "hi", "te", "mr", "kn") else "en")


# ---- validating what the client sends back -----------------------------------


def _pos_int(v: Any, lo: int = 1, hi: int = 10**12) -> int | None:
    if isinstance(v, bool):
        return None
    try:
        n = int(v)
    except (TypeError, ValueError):
        return None
    return n if lo <= n <= hi else None


def _iso(v: Any) -> str | None:
    if not isinstance(v, str):
        return None
    try:
        return date.fromisoformat(v[:10]).isoformat()
    except ValueError:
        return None


def coerce(flow: str, name: str, v: Any) -> Any:
    """A confirmed answer as the client sent it back, validated; None if unusable."""
    if name == "work":
        if not isinstance(v, dict) or not isinstance(v.get("title"), str) or not v["title"].strip():
            return None
        caps = [s for s in (v.get("required_capabilities") or []) if isinstance(s, str) and term_for("capability", s)]
        return {"title": v["title"].strip()[:120], "description": str(v.get("description") or v["title"]).strip()[:2000],
                "required_capabilities": caps[:8]}
    if name in ("location", "locality", "name"):
        return v.strip()[:80] if isinstance(v, str) and len(v.strip()) >= 2 else None
    if name == "salary":
        if not isinstance(v, dict):
            return None
        lo, hi = _pos_int(v.get("min_paise")), _pos_int(v.get("max_paise"))
        lo, hi = lo or hi, hi or lo
        return None if lo is None else {"min_paise": min(lo, hi), "max_paise": max(lo, hi)}
    if name == "openings":
        return _pos_int(v, 1, 1000)
    if name == "job_timings":
        if not isinstance(v, dict):
            return None
        label = v.get("job_timings") if isinstance(v.get("job_timings"), str) and v["job_timings"].strip() else None
        shift = v.get("shift") if v.get("shift") in SHIFTS else None
        return {"job_timings": label.strip()[:200] if label else None, "shift": shift} if (label or shift) else None
    if name == "min_qualification":
        return v if v in MIN_QUALIFICATIONS else None
    if name == "experience":
        if not isinstance(v, dict):
            return None
        lo = _pos_int(v.get("min_months"), 0, 600)
        hi = _pos_int(v.get("max_months"), 0, 600) if v.get("max_months") is not None else None
        return None if lo is None else {"min_months": lo, "max_months": hi if hi is None or hi >= lo else None}
    if name in ("requires_assets", "own_assets"):
        if v == "none" or v == ["none"]:
            return []
        if isinstance(v, str):
            v = [v]
        if not isinstance(v, list):
            return None
        return [a for a in dict.fromkeys(v) if a in REQUIRES_ASSETS]
    if name == "when":
        if not isinstance(v, dict) or v.get("urgency") not in URGENCIES:
            return None
        return {"preferred_date": _iso(v.get("preferred_date")), "urgency": v["urgency"]}
    if name == "budget" and flow == "post_local":
        if not isinstance(v, dict):
            return None
        paise = _pos_int(v.get("budget_paise"))
        comp = v.get("compensation").strip()[:100] if isinstance(v.get("compensation"), str) and v["compensation"].strip() else None
        return {"budget_paise": paise, "compensation": None if paise else comp} if (paise or comp) else None
    if name == "budget":
        if not isinstance(v, dict) or v.get("budget_type") not in ("fixed", "hourly"):
            return None
        lo, hi = _pos_int(v.get("min_paise")), _pos_int(v.get("max_paise"))
        lo, hi = lo or hi, hi or lo
        return None if lo is None else {"budget_type": v["budget_type"], "min_paise": min(lo, hi), "max_paise": max(lo, hi)}
    if name == "deadline":
        if not isinstance(v, dict):
            return None
        duration = v.get("duration") if v.get("duration") in ("under_1_week", "1_4_weeks", "1_3_months", "3_6_months", "over_6_months", "ongoing") else None
        return {"deadline": _iso(v.get("deadline")), "duration": duration}
    if name == "work_mode":
        return v if v in WORK_MODES else None
    if name == "experience_years":
        return _pos_int(v, 0, 60)
    return None


def _clean_answers(c: Ctx, answers: dict[str, Any]) -> dict[str, Any]:
    names = {n for n, _ in _fields(c.flow)}
    out: dict[str, Any] = {}
    for k, v in (answers or {}).items():
        if k in names:
            cv = coerce(c.flow, k, v)
            if cv is not None:
                out[k] = cv
    return out


# ---- labels (read-back and summary) ------------------------------------------


def _date_label(d: date, c: Ctx) -> str:
    base = _t("date.format", c.lang, weekday=_t(f"weekday.{d.weekday()}", c.lang), day=d.day, month=_t(f"month.{d.month}", c.lang))
    delta = (d - c.today).days
    if delta == 0:
        return _t("date.today", c.lang, date=base)
    if delta == 1:
        return _t("date.tomorrow", c.lang, date=base)
    if delta == 2:
        return _t("date.dayAfter", c.lang, date=base)
    return base


def _clock(h: int, m: int, lang: str) -> str:
    part = "morning" if 4 <= h < 12 else "afternoon" if 12 <= h < 16 else "evening" if 16 <= h < 20 else "night"
    h12 = h % 12 or 12
    return _t("time.format", lang, h=h12, mm=f":{m:02d}" if m else "", ampm=_t("time.am" if h < 12 else "time.pm", lang),
              daypart=_t(f"daypart.{part}", lang))


def _assets_label(codes: list[str], lang: str) -> str:
    if not codes:
        return _t("asset.none", lang)
    return _t("readback.list", lang).join(_t(f"asset.{a}", lang) for a in codes)


def _experience_label(v: dict[str, Any], lang: str) -> str:
    months = v["min_months"]
    if months == 0:
        return _t("experience.none", lang)
    if months % 12 == 0:
        return translate_count("voice.experience.years", lang, months // 12)
    return translate_count("voice.experience.months", lang, months)


def value_label(c: Ctx, name: str, v: Any) -> str:
    lang = c.lang
    if name == "work":
        return v["title"]
    if name in ("location", "locality", "name"):
        return v
    if name == "salary":
        return compensation_label(OpportunityStructured(salary_min_paise=v["min_paise"], salary_max_paise=v["max_paise"]), "employment", lang) or ""
    if name == "openings":
        return translate_count("voice.count.people", lang, v)
    if name == "job_timings":
        return v["job_timings"] or _t(f"shift.{v['shift']}", lang)
    if name == "min_qualification":
        return _t(f"qualification.{v}", lang)
    if name == "experience":
        return _experience_label(v, lang)
    if name in ("requires_assets", "own_assets"):
        return _assets_label(v, lang)
    if name == "when":
        if v["preferred_date"]:
            return _date_label(date.fromisoformat(v["preferred_date"]), c)
        return _t(f"urgency.{v['urgency']}", lang)
    if name == "budget" and c.flow == "post_local":
        if v["budget_paise"]:
            return compensation_label(OpportunityStructured(budget_paise=v["budget_paise"]), "local_service", lang) or ""
        return legacy_compensation_label(v["compensation"], "local_service", lang) or v["compensation"]
    if name == "budget":
        s = OpportunityStructured(budget_type=v["budget_type"], **(
            {"hourly_rate_min_paise": v["min_paise"], "hourly_rate_max_paise": v["max_paise"]} if v["budget_type"] == "hourly"
            else {"budget_min_paise": v["min_paise"], "budget_max_paise": v["max_paise"]}))
        return compensation_label(s, "freelance", lang) or ""
    if name == "deadline":
        if v["deadline"]:
            return _t("deadline.by", lang, date=_date_label(date.fromisoformat(v["deadline"]), c))
        return _t("deadline.ongoing" if v["duration"] == "ongoing" else "deadline.flexible", lang)
    if name == "work_mode":
        return _t(f"option.work_mode.{v}", lang)
    if name == "experience_years":
        return translate_count("voice.count.years", lang, v) if v else _t("count.new", lang)
    return str(v)


def _readback_part(c: Ctx, name: str, v: Any) -> str:
    if name in ("location", "locality"):
        return _t("readback.in", c.lang, place=v)
    if name == "work":
        return f"“{v['title']}”"
    return value_label(c, name, v)


# ---- next question -------------------------------------------------------------


async def next_question(conn: asyncpg.Connection, ctx: AuthzContext, locale: str, body: InterviewNextRequest) -> InterviewNextOut:
    lang = _lang(body.language, locale)
    c = await _load(conn, ctx, body.flow, lang)
    answers = _clean_answers(c, body.answers)
    skipped = set(body.skipped or [])
    askable = [(n, opt) for n, opt in _fields(c.flow) if _applies(c, n, answers)]
    pending = [(n, opt) for n, opt in askable if n not in answers]
    order = ([p for p in pending if not p[1] and p[0] not in skipped]
             + [p for p in pending if p[1] and p[0] not in skipped]
             + [p for p in pending if not p[1] and p[0] in skipped])  # a required field skipped is asked again, last
    if order:
        name, optional = order[0]
        question = _question(c, name)
        if not optional and name in skipped:
            question = _t("reprompt.needed", lang, question=question)
        done_count = sum(1 for n, opt in askable if n in answers or (opt and n in skipped))
        return InterviewNextOut(
            done=False, field=name, question=question, hint=_hint(c, name), kind=_kind(c, name), options=_options(c, name),
            optional=optional, progress=InterviewProgress(asked=min(done_count + 1, len(askable)), total=len(askable)),
        )
    summary = [SummaryItem(field=n, label=_t(f"label.{n}", lang), value_label=_cap(value_label(c, n, answers[n])))
               for n, _ in _fields(c.flow) if n in answers]
    draft = _profile_draft(c, answers) if c.flow == "profile" else _post_draft(c, answers)
    return InterviewNextOut(done=True, summary=summary, draft=draft)


def _post_draft(c: Ctx, a: dict[str, Any]) -> InterviewPostDraft:
    type_ = FLOW_TYPE[c.flow]
    work = a.get("work") or {}
    d: dict[str, Any] = {
        "type": type_, "title": work.get("title"), "description": work.get("description"), "location": a.get("location"),
        "work_mode": a.get("work_mode") or "on_site", "timing": None, "required_capabilities": work.get("required_capabilities") or [],
        "employment": None, "freelance": None, "local_service": None,
    }
    if c.flow == "post_project" and a.get("work_mode") == "remote":
        d["location"] = None
    confidence = {k: 1.0 for k in ("type", "title", "description", "required_capabilities") if work}
    deadline = compensation = None
    if type_ == "employment":
        sal, tim, exp = a.get("salary") or {}, a.get("job_timings") or {}, a.get("experience") or {}
        d["employment"] = {
            "salary_min_paise": sal.get("min_paise"), "salary_max_paise": sal.get("max_paise"),
            "incentive_type": "none" if sal else None, "openings": a.get("openings"), "shift": tim.get("shift"),
            "job_timings": tim.get("job_timings"), "interview_details": None, "min_qualification": a.get("min_qualification"),
            "english_level": None, "experience_min_months": exp.get("min_months"), "experience_max_months": exp.get("max_months"),
            "requires_assets": a.get("requires_assets") or [],
        }
    elif type_ == "local_service":
        when, bud = a.get("when") or {}, a.get("budget") or {}
        d["local_service"] = {"preferred_date": when.get("preferred_date"), "budget_paise": bud.get("budget_paise"), "urgency": when.get("urgency")}
        compensation = bud.get("compensation")
    else:
        bud, dl = a.get("budget") or {}, a.get("deadline") or {}
        hourly = bud.get("budget_type") == "hourly"
        d["freelance"] = {
            "budget_type": bud.get("budget_type"),
            "budget_min_paise": None if hourly else bud.get("min_paise"), "budget_max_paise": None if hourly else bud.get("max_paise"),
            "hourly_rate_min_paise": bud.get("min_paise") if hourly else None, "hourly_rate_max_paise": bud.get("max_paise") if hourly else None,
            "duration": dl.get("duration"), "experience_level": None, "screening_questions": [],
        }
        deadline = dl.get("deadline")
    for name, codes in (("location", ("location",)), ("salary", ("salary",)), ("openings", ("openings",)),
                        ("job_timings", ("job_timings", "shift")), ("min_qualification", ("min_qualification",)),
                        ("experience", ("experience",)), ("requires_assets", ("requires_assets",)),
                        ("when", ("preferred_date", "urgency")), ("budget", ("budget", "budget_type")),
                        ("deadline", ("duration",)), ("work_mode", ("work_mode",))):
        if name in a:
            confidence.update({code: 1.0 for code in codes})
    missing = compute_missing(d, [])
    if type_ == "local_service" and compensation:
        missing = [m for m in missing if m != "budget"]  # a stated pay basis answers "what does it pay"
    return InterviewPostDraft(
        type=type_, title=d["title"], description=d["description"], location=d["location"], work_mode=d["work_mode"],
        timing=None, required_capabilities=d["required_capabilities"], capability_labels=labels_for(d["required_capabilities"], c.lang),
        employment=EmploymentFields(**d["employment"]) if d["employment"] else None,
        freelance=FreelanceFields(**d["freelance"]) if d["freelance"] else None,
        local_service=LocalServiceFields(**d["local_service"]) if d["local_service"] else None,
        confidence=confidence, missing=missing, questions=[translate(f"ai.ask.{m}", c.lang) for m in missing],
        source="rules", language=c.lang,  # type: ignore[arg-type]
        deadline=deadline, compensation=compensation,
    )


def _profile_draft(c: Ctx, a: dict[str, Any]) -> InterviewProfileDraft:
    work = a.get("work")
    caps = None
    headline = None
    if work:
        caps = work["required_capabilities"] or [work["title"]]  # an unmatched trade is kept as the person said it
        headline = None if c.known.get("headline") else work["title"]
    return InterviewProfileDraft(
        name=a.get("name"), locality=a.get("locality"), capabilities=caps, headline=headline,
        experience_years=a.get("experience_years"), own_assets=a.get("own_assets"),
    )


# ---- interpreting one answer ------------------------------------------------------


@dataclass
class Parsed:
    value: Any
    confidence: float = 0.9
    alternatives: list[Any] = dc_field(default_factory=list)
    also: dict[str, Any] = dc_field(default_factory=dict)
    readback: str | None = None  # a special read-back (e.g. a day wage shown with its monthly figure)
    reprompt_key: str | None = None  # understood=false with this reprompt (e.g. hourly pay for a monthly salary)


_NEGATIVE = re.compile(
    r"(?<![a-z])(?:no|none|nothing|nope|not needed|no need|not required|doesn t matter|doesnt matter|anything|any|nahi|nahin|"
    r"kuch nahi|kuchh nahi|koi nahi|kuch bhi|koi bhi|zaroorat nahi|jarurat nahi|zaruri nahi|jaruri nahi|ledu|emi ledu|emi vaddu|"
    r"avasaram ledu|parledu)(?![a-z])"
    r"|नहीं|कुछ नहीं|कोई नहीं|कुछ भी|कोई भी|ज़रूरत नहीं|जरूरत नहीं|ज़रूरी नहीं|जरूरी नहीं|లేదు|ఏమీ లేదు|ఏమీ వద్దు|అవసరం లేదు|పర్లేదు|ఏదైనా"
)
_NEW_OK = re.compile(
    r"(?<![a-z])(?:new|fresher|freshers|beginner|no experience|naya|naye|fresh|kotha|kottha|kothavallu)(?![a-z])"
    r"|नया|नए|फ्रेशर|अनुभव नहीं|కొత్త|ఫ్రెషర్|అనుభవం అవసరం లేదు|అనుభవం లేదు"
)
_EXTRA_ASSETS = (
    ("smartphone", re.compile(r"(?<![a-z])(?:phone|mobile|fone)(?![a-z])|फोन|फ़ोन|मोबाइल|ఫోన్|మొబైల్", re.I)),
    ("two_wheeler", re.compile(r"(?<![a-z])(?:bike|motorbike|motorcycle|scooter|scooty|bandi|two wheeler|activa)(?![a-z])|बाइक|स्कूटी|स्कूटर|బైక్|స్కూటీ|బండి|టూ వీలర్", re.I)),
    ("four_wheeler", re.compile(r"(?<![a-z])(?:car|four wheeler)(?![a-z])|कार|కారు", re.I)),
    ("driving_licence", re.compile(r"(?<![a-z])(?:licence|license|dl)(?![a-z])|लाइसेंस|లైసెన్స్", re.I)),
    ("laptop", re.compile(r"(?<![a-z])(?:laptop|computer)(?![a-z])|लैपटॉप|कंप्यूटर|ల్యాప్‌టాప్|ల్యాప్ టాప్|కంప్యూటర్", re.I)),
    ("own_tools", re.compile(r"(?<![a-z])(?:tools?|equipment|kit|auzar|aujar|panimuttu|panimutlu)(?![a-z])|औजार|औज़ार|टूल|పనిముట్లు|పనిముట్టు|టూల్స్|సామాను", re.I)),
)
_VEHICLE = re.compile(r"(?<![a-z])(?:vehicle|gaadi|gadi|vahan)(?![a-z])|गाड़ी|गाडी|वाहन|వాహనం", re.I)
_VISIT = re.compile(r"(?<![a-z])(?:visit|per visit|a visit|each visit|ek visit)(?![a-z])|विजिट|विज़िट|విజిట్", re.I)
_YEARLY = re.compile(r"(?<![a-z])(?:a year|per year|yearly|per annum|annual|lpa|saal ka|salana|saalana)(?![a-z])|सालाना|साल का|సంవత్సరానికి|ఏడాదికి", re.I)
_NEGOTIABLE = re.compile(
    r"(?<![a-z])(?:negotiable|discuss|will discuss|let s discuss|talk|quote|tell me the rate|baat karke|baat kar lenge|"
    r"rate batao|matladukundam|matladudam|after seeing|dekh ke|dekhkar)(?![a-z])"
    r"|बात करके|बात कर लेंगे|रेट बताइए|रेट बताओ|देखकर|మాట్లాడుకుందాం|మాట్లాడదాం|రేటు చెప్పండి|చూసి",
    re.I,
)
_REMOTE = re.compile(
    r"(?<![a-z])(?:remote|online|from home|their place|their own place|own place|anywhere|apni jagah|ghar se|vaalla daggara|valla daggara)(?![a-z])"
    r"|अपनी जगह|घर से|ऑनलाइन|कहीं से भी|వాళ్ళ దగ్గర|వాళ్ల దగ్గర|ఇంటి నుండి|ఆన్‌లైన్|ఆన్ లైన్|ఎక్కడి నుండైనా", re.I)
_ONSITE = re.compile(
    r"(?<![a-z])(?:come to me|my place|my office|my shop|my home|come here|on site|onsite|in person|mere paas|mere yahan|naa daggara)(?![a-z])"
    r"|मेरे पास|मेरे यहाँ|मेरे यहां|ऑफिस|दुकान पर|నా దగ్గరికి|నా దగ్గర|మా ఇంటికి|ఆఫీసుకి|షాప్‌కి", re.I)
_BOTH = re.compile(r"(?<![a-z])(?:either|both|any|dono|anything)(?![a-z])|दोनों|कोई भी|ఏదైనా|రెండూ|ఎలాగైనా", re.I)
_PLACE_FILLER = re.compile(
    r"(?<![a-z])(?:the work is|work is|it is|it s|is in|in|at|near|around|area|side|kaam|mein|me|mei|lo|daggara|hai|undi|ki|ke paas|"
    r"the|locality|colony)(?![a-z])|में|के पास|है|इलाका|इलाके|काम|లో|దగ్గర|ఏరియా|ఉంది|పని",
    re.I,
)
_TITLE_LEAD = re.compile(
    r"^(?:(?:i|we)\s+(?:need|want|require)|need|want|looking for|require|i am an?|i m an?|i am|i m|i work as an?|i work as|i do|"
    r"someone to|someone for|someone who can|a person to|a person for|mujhe|mujhko|hame|hamein|humein|hume|main|mai|naaku|maaku|nenu|"
    r"मुझे|मुझको|हमें|हमको|मैं|నాకు|మాకు|నేను)\s+",
    re.I,
)
_TITLE_TAIL = re.compile(
    r"\s+(?:chahiye|chaiye|chahie|karwana hai|karvana hai|banwana hai|banvana hai|karna hai|ki zarurat hai|ki jarurat hai|"
    r"needed|required|wanted|please|kavali|kaavali|cheyinchukovali|chestanu|pani chestanu|"
    r"चाहिए|चाहिये|करवाना है|बनवाना है|की ज़रूरत है|की जरूरत है|का काम करता हूँ|का काम करता हूं|का काम करती हूँ|करता हूँ|करता हूं|करती हूँ|"
    r"కావాలి|కావాలండి|చేయాలి|చేయించాలి|చేయించుకోవాలి|తయారు చేయించుకోవాలి|పని చేస్తాను|గా పని చేస్తాను|చేస్తాను)$",
    re.I,
)


_TITLE_CUT = re.compile(
    r"\s*(?:,|;|।|\.\s|(?<![a-z])(?:salary|pay|paying|budget|rs|rupees|timings?|from|by|within|urgent|today|tomorrow)(?![a-z])|₹|"
    r"सैलरी|वेतन|बजट|तनख्वाह|టైమింగ్|జీతం|బడ్జెట్)",
    re.I,
)


def _lead_count(text: str, place: str | None) -> int | None:
    """The headcount an opening answer starts with ("iddaru delivery boys")."""
    t = _without_place(text, place)
    for _ in range(2):
        t = _TITLE_LEAD.sub("", t.strip()).strip()
    t = re.sub(r"^(?:(?:mujhe|hame|humein|naaku|maaku|lo|mein|me|in|at|मुझे|हमें|में|నాకు|మాకు|లో)\s+)+", "", t.strip(), flags=re.I)
    m = re.match(r"^(\d{1,3})\s+\S", words_to_digits(t))
    return int(m.group(1)) if m and 1 <= int(m.group(1)) <= 500 else None


def _without_place(text: str, place: str | None) -> str:
    """The text with the place's own words taken out, in any script, so a
    skill is never read inside a place name (कुकटपल्ली is not "कुक")."""
    if not place:
        return text
    key = skeleton(re.sub(r"[^A-Za-z ]", " ", place))
    words = text.split()
    kept = [w for w in words if not (len(key) >= 3 and skeleton(_strip_telugu_suffix(re.sub(r"[^\wऀ-ॿఀ-౿]", "", w))) == key)]
    out = " ".join(kept)
    return re.sub(re.escape(place), " ", out, flags=re.I)


def _title(text: str, place: str | None = None) -> str:
    """The heading a post or a profile shows: the work itself, without the
    request words, the place or the pay ("I need 2 delivery boys in
    Kukatpally, salary 15 to 18 thousand" -> "Delivery boys")."""
    t = re.sub(r"\s+", " ", text).strip(" .,!?।")
    head = _TITLE_CUT.split(t, maxsplit=1)[0].strip()
    if len(head) >= 3:
        t = head
    if place:
        t = re.sub(rf"\s*(?<![a-z])(?:in|at|near|around)\s+{re.escape(place)}(?![a-z])", "", t, flags=re.I)
        t = re.sub(rf"\s*{re.escape(place)}\s*(?:mein|me|lo|में|లో)?(?![a-z])", " ", t, flags=re.I).strip()
    for _ in range(2):
        t = _TITLE_LEAD.sub("", t).strip()
        t = _TITLE_TAIL.sub("", t).strip(" .,!?।")
    t = re.sub(r"^(?:a|an|some)\s+", "", t, flags=re.I).strip()
    first, _, rest_words = t.partition(" ")
    if rest_words and (first.isdigit() or norm(first) in NUM_WORDS):  # "2 delivery boys", "iddaru delivery boys"
        t = rest_words.strip()
    if len(t) < 2:
        t = text.strip()
    if len(t) > 80:
        cut = re.split(r"(?<=[.!?।])\s+|,\s+", t)[0]
        t = cut if len(cut) >= 8 else t[:79].rsplit(" ", 1)[0] + "…"
    return _cap(t)


def _money(text: str) -> tuple[int | None, int | None, str | None]:
    """(min_rupees, max_rupees, period) from a spoken amount; the question is the money context."""
    t = words_to_digits(text)
    lo, hi, period = find_money("pay " + t)
    lo, hi = lo or hi, hi or lo
    if lo is None:
        return None, None, None
    low = norm(text) + " " + t
    if _VISIT.search(low):
        period = "visit"
    elif _HOURLY.search(low):
        period = "hourly"
    elif _DAILY.search(low):
        period = "daily"
    elif _YEARLY.search(low):
        period = "yearly"
    return lo, hi, period


def _place(c: Ctx, text: str) -> tuple[str, float] | None:
    found = find_known_locality(text, c.localities)
    if not found:
        place = resolve_place(text)
        found = place.name if place else None
    if found:
        return found, 0.9
    cleaned = re.sub(r"\s+", " ", _PLACE_FILLER.sub(" ", norm(text))).strip()
    cleaned = re.sub(r"లో$", "", cleaned).strip()
    if 2 <= len(cleaned) <= 40 and len(cleaned.split()) <= 4 and not any(ch.isdigit() for ch in cleaned):
        return " ".join(w[:1].upper() + w[1:] if w.isascii() else w for w in cleaned.split()), 0.5
    return None


def _assets(text: str) -> list[str]:
    low = norm(text)
    found = [code for code, pattern in _ASSETS if pattern.search(low)]
    for code, pattern in _EXTRA_ASSETS:
        if pattern.search(low) and code not in found:
            found.append(code)
    return [a for a in REQUIRES_ASSETS if a in found]


def _months(text: str) -> tuple[int, int | None] | None:
    t = words_to_digits(text)
    if _NEW_OK.search(norm(text)):
        return 0, None
    m = re.search(r"(\d+)\s*(?:months?|mahine|mahina|महीने|महीना|నెలలు|నెలల|నెల)", t)
    if m:
        return int(m.group(1)), None
    lo, hi = find_experience_months("experience " + t)
    if lo is not None:
        return lo, hi
    n = re.fullmatch(r"\s*(\d{1,2}(?:\.\d)?)\s*", t)
    if n and float(n.group(1)) <= 40:
        return int(round(float(n.group(1)) * 12)), None
    return None


def _duration(days: int) -> str:
    return ("under_1_week" if days <= 7 else "1_4_weeks" if days <= 31 else "1_3_months" if days <= 92
            else "3_6_months" if days <= 183 else "over_6_months")


def _hours_value(c: Ctx, text: str) -> dict[str, Any] | None:
    h = parse_hours(text)
    if h and "start" in h:
        label = _t("hours.range", c.lang, start=_clock(*h["start"], c.lang), end=_clock(*h["end"], c.lang))
        return {"job_timings": label, "shift": h["shift"]}
    if h and "hours" in h:
        return {"job_timings": translate_count("voice.hours.perDay", c.lang, h["hours"]), "shift": None}
    low = norm(text)
    for code, pattern in _SHIFT:
        if pattern.search(low):
            return {"job_timings": None, "shift": code}
    stated = find_timings(text)
    if stated:
        return {"job_timings": stated[:200], "shift": None}
    return None


def parse_field(c: Ctx, name: str, text: str) -> Parsed | None:
    """The typed value one answer gives for one field, or None (not understood)."""
    flow = c.flow
    if name == "work":
        t = strip_contacts(text).strip()
        if len(t) < 2:
            return None
        place = find_known_locality(t, c.localities)
        caps = find_capabilities(_without_place(t, place), c.terms)
        also = _also(c, t)
        count = _lead_count(t, place)
        if c.flow == "post_job" and count and "openings" not in also:
            also["openings"] = count
        return Parsed({"title": _title(t, place), "description": t[:2000], "required_capabilities": caps[:8]},
                      confidence=0.9 if caps else 0.7, also=also)
    if name in ("location", "locality"):
        found = _place(c, text)
        return Parsed(found[0], confidence=found[1]) if found else None
    if name == "name":
        n = parse_name(text)
        return Parsed(n, confidence=0.8) if n else None
    if name == "salary":
        lo, hi, period = _money(text)
        if lo is None:
            return None
        if period == "hourly":
            return Parsed(None, reprompt_key="reprompt.monthly")
        said = None
        confidence = 0.9
        if period == "daily" or (period is None and 100 <= hi < 1000):
            said = format_inr(lo * 100) if lo == hi else f"{format_inr(lo * 100)}–{format_inr(hi * 100)}"
            said = translate("opportunities.compensation.daily", c.lang, amount=said)
            lo, hi, confidence = lo * 26, hi * 26, 0.7 if period is None else 0.85
        elif period == "yearly":
            lo, hi = int(round(lo / 1200)) * 100, int(round(hi / 1200)) * 100  # a yearly figure, shown as its month
        elif period is None and hi < 100:
            lo, hi, confidence = lo * 1000, hi * 1000, 0.6  # "fifteen to eighteen" for a monthly salary means thousands
        value = {"min_paise": lo * 100, "max_paise": hi * 100}
        readback = None
        if said:
            readback = _t("readback.approxMonthly", c.lang, said=said, monthly=value_label(c, "salary", value))
        return Parsed(value, confidence=confidence, readback=readback)
    if name == "openings":
        n = first_int(text) or find_openings(text)
        return Parsed(n, confidence=0.9) if n and 1 <= n <= 1000 else None
    if name == "job_timings":
        v = _hours_value(c, text)
        return Parsed(v, confidence=0.85 if v and v.get("shift") else 0.6) if v else None
    if name == "min_qualification":
        q = find_qualification(words_to_digits(text)) or find_qualification(text)
        if q:
            return Parsed(q)
        if _NEGATIVE.search(norm(text)):
            return Parsed("any", confidence=0.8)
        return None
    if name == "experience":
        m = _months(text)
        if m is None and _NEGATIVE.search(norm(text)):
            m = (0, None)
        return Parsed({"min_months": m[0], "max_months": m[1]}) if m is not None else None
    if name == "experience_years":
        m = _months(text)
        if m is None and _NEGATIVE.search(norm(text)):
            m = (0, None)
        return Parsed(int(round(m[0] / 12)), confidence=0.85) if m is not None else None
    if name in ("requires_assets", "own_assets"):
        found = _assets(text)
        if found:
            return Parsed(found)
        if _VEHICLE.search(norm(text)):
            return Parsed(["two_wheeler"], confidence=0.6, alternatives=[["four_wheeler"]])
        if _NEGATIVE.search(norm(text)):
            return Parsed([], confidence=0.9)
        return None
    if name == "when":
        d = parse_day(text, c.today)
        if d is None:
            return None
        if d["date"]:
            days = (d["date"] - c.today).days
            urgency = "today" if days <= 0 else "this_week" if days <= 7 else "flexible"
            return Parsed({"preferred_date": d["date"].isoformat(), "urgency": urgency})
        urgency = "this_week" if d.get("span_days") == 6 else "flexible"
        return Parsed({"preferred_date": None, "urgency": urgency}, confidence=0.85)
    if name == "budget" and flow == "post_local":
        lo, hi, period = _money(text)
        low = norm(text)
        if lo is not None:
            unit = {"visit": "visit", "hourly": "hour", "daily": "day"}.get(period or "")
            if unit:
                amount = format_inr(lo * 100) if lo == hi else f"{format_inr(lo * 100)} to {format_inr(hi * 100)}"
                return Parsed({"budget_paise": None, "compensation": f"{amount} per {unit}"})
            return Parsed({"budget_paise": hi * 100, "compensation": None}, alternatives=[] if lo == hi else [{"budget_paise": lo * 100, "compensation": None}])
        if _VISIT.search(low):
            return Parsed({"budget_paise": None, "compensation": "Pay per visit"}, confidence=0.85)
        if _HOURLY.search(low):
            return Parsed({"budget_paise": None, "compensation": "Pay per hour"}, confidence=0.85)
        if _DAILY.search(low):
            return Parsed({"budget_paise": None, "compensation": "Pay per day"}, confidence=0.85)
        if _NEGOTIABLE.search(low):
            return Parsed({"budget_paise": None, "compensation": "negotiable"}, confidence=0.8)
        return None
    if name == "budget":
        lo, hi, period = _money(text)
        if lo is None:
            return None
        btype = "hourly" if period == "hourly" else "fixed"
        return Parsed({"budget_type": btype, "min_paise": lo * 100, "max_paise": hi * 100})
    if name == "deadline":
        d = parse_day(text, c.today)
        if d is None:
            return None
        if d["ongoing"]:
            return Parsed({"deadline": None, "duration": "ongoing"})
        if d["date"]:
            days = max(1, (d["date"] - c.today).days)
            return Parsed({"deadline": d["date"].isoformat(), "duration": _duration(days)})
        if d.get("span_days") == 6:
            return Parsed({"deadline": (c.today + timedelta(days=6)).isoformat(), "duration": "under_1_week"}, confidence=0.8)
        return Parsed({"deadline": None, "duration": None}, confidence=0.8)
    if name == "work_mode":
        low = norm(text)
        for code, pattern in (("both", _BOTH), ("remote", _REMOTE), ("on_site", _ONSITE)):
            if pattern.search(low):
                return Parsed(code, confidence=0.85)
        return None
    return None


def _also(c: Ctx, text: str) -> dict[str, Any]:
    """Other fields the opening answer already states ("2 delivery boys in
    Kukatpally, 15 to 18 thousand"), so they are not asked again."""
    names = {n for n, _ in _fields(c.flow)}
    out: dict[str, Any] = {}
    place = find_known_locality(text, c.localities) or (resolve_place(text).name if resolve_place(text) else None)
    if place:
        out["locality" if c.flow == "profile" else "location"] = place
    if c.flow == "profile":
        years = re.search(r"(\d{1,2})\s*(?:years?|yrs?|saal|साल|वर्ष|సంవత్సరాలు|సంవత్సరాల|సంవత్సరం|ఏళ్ళు|ఏళ్లు)", words_to_digits(text))
        if years:
            out["experience_years"] = int(years.group(1))
        assets = _assets(text)
        if assets:
            out["own_assets"] = assets
        return {k: v for k, v in out.items() if k in names}
    raw = clean_draft(draft_from_text(text, c.terms, force_type=FLOW_TYPE[c.flow]), {t["slug"] for t in c.terms})
    e, f, s = raw.get("employment") or {}, raw.get("freelance") or {}, raw.get("local_service") or {}
    if c.flow == "post_job":
        if e.get("salary_min_paise") or e.get("salary_max_paise"):
            lo, hi = e.get("salary_min_paise") or e.get("salary_max_paise"), e.get("salary_max_paise") or e.get("salary_min_paise")
            out["salary"] = {"min_paise": lo, "max_paise": hi}
        if e.get("openings"):
            out["openings"] = e["openings"]
        if e.get("job_timings"):
            v = _hours_value(c, e["job_timings"])
            if v:
                out["job_timings"] = v
        if e.get("min_qualification"):
            out["min_qualification"] = e["min_qualification"]
        if e.get("experience_min_months") is not None:
            out["experience"] = {"min_months": e["experience_min_months"], "max_months": e.get("experience_max_months")}
        if e.get("requires_assets"):
            out["requires_assets"] = e["requires_assets"]
    elif c.flow == "post_local":
        if s.get("urgency"):
            out["when"] = {"preferred_date": s.get("preferred_date"), "urgency": s["urgency"]}
        if s.get("budget_paise"):
            out["budget"] = {"budget_paise": s["budget_paise"], "compensation": None}
    elif c.flow == "post_project":
        lo, hi = f.get("budget_min_paise") or f.get("hourly_rate_min_paise"), f.get("budget_max_paise") or f.get("hourly_rate_max_paise")
        if lo or hi:
            out["budget"] = {"budget_type": f.get("budget_type") or "fixed", "min_paise": lo or hi, "max_paise": hi or lo}
        if raw.get("work_mode") in WORK_MODES:
            out["work_mode"] = raw["work_mode"]
    return {k: v for k, v in out.items() if k in names and coerce(c.flow, k, v) is not None}


def _reprompt_unclear(c: Ctx, name: str) -> str:
    sorry = _t(f"reprompt.sorry.{_MISSED.get(name, 'answer')}", c.lang)
    return _t("reprompt.again", c.lang, sorry=sorry, question=_open_question(c, name))


def _open_question(c: Ctx, name: str) -> str:
    """The question without the yes/no offer (after "no", or when unclear)."""
    return _t(f"q.{c.flow}.{name}", c.lang)


_NEEDS_DETAIL_ON_YES = ("requires_assets", "own_assets", "experience", "min_qualification")
_NO_IS_AN_ANSWER = ("requires_assets", "own_assets", "experience", "min_qualification")


async def interpret_answer(conn: asyncpg.Connection, ctx: AuthzContext, locale: str, body: InterviewInterpretRequest) -> InterviewInterpretOut:
    lang = _lang(body.language, locale)
    names = dict(_fields(body.flow))
    if body.field not in names:
        raise ApiError(422, "voice.error.unknownField", lang, field=body.field, error_code="voice_unknown_field",
                       extra={"field": body.field, "flow": body.flow, "fields": list(names)})
    c = await _load(conn, ctx, body.flow, lang, need_terms=body.field in ("work", "location", "locality"))
    name, optional = body.field, names[body.field]
    text = (body.text or "").strip()[:MAX_TEXT]
    answers = _clean_answers(c, body.answers)
    offers_saved = name == "location" and c.flow != "profile" and bool(c.saved_locality)

    def out(**kw: Any) -> InterviewInterpretOut:
        return InterviewInterpretOut(**kw)

    if not text:
        return out(understood=False, intent="unclear", reprompt=_reprompt_unclear(c, name))
    intent, rest = control_intent(text)
    if intent == "repeat":
        return out(understood=False, intent="repeat", reprompt=_question(c, name))
    if intent == "skip":
        return out(understood=False, intent="skip", reprompt=None if optional else _t("reprompt.needed", lang, question=_question(c, name)))
    if intent in ("yes", "no") and not rest:
        if offers_saved:
            if intent == "yes":
                return out(understood=True, value=c.saved_locality, intent="yes", confidence=1.0, needs_confirmation=False,
                           readback=_cap(_t("readback.in", lang, place=c.saved_locality)))
            return out(understood=False, intent="no", reprompt=_t("reprompt.ok", lang, question=_open_question(c, name)))
        if intent == "no" and name in _NO_IS_AN_ANSWER:
            value = {"min_months": 0, "max_months": None} if name == "experience" else ("any" if name == "min_qualification" else [])
            return out(understood=True, value=value, intent="no", confidence=0.9, needs_confirmation=False,
                       readback=value_label(c, name, value))
        if intent == "yes" and name in _NEEDS_DETAIL_ON_YES:
            return out(understood=False, intent="yes", reprompt=_t(f"reprompt.which.{name}", lang))
        # A plain yes/no to any other question is the answer to a read-back
        # (the client reads only `intent` there); asked as an answer, it is unclear.
        return out(understood=False, intent=intent, reprompt=_reprompt_unclear(c, name))
    answer_text = rest if (intent in ("yes", "no") and rest) else text

    # Scam shield on what a poster (or a profile) says in their own words.
    tier = "offer" if c.flow == "profile" else "hiring"
    match = scam_shield.detect(answer_text, tier) if name in ("work", "job_timings", "budget", "when", "deadline", "name") else None
    if match is not None:
        explanation = translate(f"trust_safety.scamShield.rule.{match.rule}", lang)
        return out(understood=False, intent="answer", confidence=0.0, reprompt=f"{explanation} {_t('reprompt.scam', lang)}")

    source = "rules"
    parsed = parse_field(c, name, answer_text)
    if parsed is None and get_ai_settings().provider_name == "anthropic":
        parsed = await _ask_claude(conn, ctx, c, name, answer_text)
        source = "ai" if parsed is not None else "rules"
    if parsed is None:
        return out(understood=False, intent="unclear", reprompt=_reprompt_unclear(c, name))
    if parsed.reprompt_key:
        return out(understood=False, intent="answer", reprompt=_t(parsed.reprompt_key, lang, question=_open_question(c, name)))
    value = coerce(c.flow, name, parsed.value)
    if value is None:
        return out(understood=False, intent="unclear", reprompt=_reprompt_unclear(c, name))
    also = {k: coerce(c.flow, k, v) for k, v in parsed.also.items() if k not in answers and k != name}
    also = {k: v for k, v in also.items() if v is not None}
    parts = [parsed.readback or _readback_part(c, name, value)] + [_readback_part(c, k, v) for k, v in also.items()]
    readback = _t("readback.heard", lang, what=_t("readback.list", lang).join(parts))
    alternatives = [a for a in (coerce(c.flow, name, x) for x in parsed.alternatives) if a is not None]
    return out(understood=True, value=value, readback=readback, confidence=round(parsed.confidence, 2), alternatives=alternatives,
               intent="answer", also=also, source=source)  # type: ignore[arg-type]


async def _ask_claude(conn: asyncpg.Connection, ctx: AuthzContext, c: Ctx, name: str, text: str) -> Parsed | None:
    """Only when AI_PROVIDER=anthropic and the rules could not read the
    answer: Claude rewrites it in plain English words, which the same rules
    then read — so nothing unvalidated reaches the person."""
    await ai_svc._enforce_daily_limit(conn, ctx, c.lang)
    started = time.perf_counter()
    provider = get_ai_provider()
    question = _open_question(c, name)
    interpret = getattr(provider, "interpret_answer", None)
    if interpret is None:
        return None
    input_hash = ai_svc._hash({"field": name, "flow": c.flow, "text": text, "language": c.lang})
    try:
        result = await interpret(name, _t(f"q.{c.flow}.{name}", "en"), question, text, c.lang)
    except AiUnavailable as exc:
        await ai_svc._audit(ctx, "interview", input_hash, None, exc.reason, started)
        return None
    await ai_svc._audit(ctx, "interview", input_hash, result, "ok", started)
    canonical = result.data.get("canonical") if isinstance(result.data, dict) else None
    if not result.data.get("understood") or not isinstance(canonical, str) or not canonical.strip():
        return None
    en = Ctx(flow=c.flow, lang=c.lang, today=c.today, saved_locality=c.saved_locality, known=c.known, terms=c.terms, localities=c.localities)
    parsed = parse_field(en, name, canonical[:300])
    if parsed is not None:
        parsed.confidence = min(parsed.confidence, 0.75)
        parsed.also = {}
    return parsed


__all__ = [
    "InterviewInterpretOut", "InterviewInterpretRequest", "InterviewNextOut", "InterviewNextRequest",
    "interpret_answer", "next_question",
]

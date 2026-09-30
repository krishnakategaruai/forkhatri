# [IMP42 — Refactor C (AI)] AI assistance for posting, shortlisting and
# applying. Five operations, one shape of guarantee for all of them:
#
#   * The provider (Claude, or the rules engine) is asked through the
#     AiProvider seam in app/integrations/ai; its answer is validated against
#     the closed vocabularies in app/integrations/ai/vocab.py before a caller
#     sees it. An invented type, slug, tip or score never leaves this module.
#   * Nothing here writes an opportunity, an enquiry or a proposal. Every
#     answer is a suggestion the person confirms in the UI through the
#     existing endpoints (createOpportunity, createEnquiry ...).
#   * Only the text and structured fields an answer needs are sent. Phone
#     numbers and e-mails are redacted; other members are opaque refs; no
#     third party's name is in any prompt.
#   * Every call — including a rules-only or a refused one — is recorded in
#     vyapar_integration.ai_events (migration 020) with the member, kind, a
#     hash of the input, model, latency, tokens and outcome, so cost and
#     usage can be audited per member without storing the text itself.
#   * A per-member daily cap (AI_DAILY_LIMIT) protects cost; error code
#     `ai_limit_reached`.
#
# Dependency on workstream A (migration 018): the shortlist reads
# `stage`, `bid_*` and `profile_snapshot` from enquiries and the typed
# employment/freelance/local_service columns from opportunities. Both are read
# through `to_jsonb(row)` and `.get()`, so a column that does not exist yet is
# simply None — nothing here breaks before 018 lands, and nothing needs to
# change when it does (provided A keeps the field names of vocab.py).
# Traces to: FR11, FR12, FR18, FR19, FR22, REFACTOR-PLAN.md (AI workstream C)
from __future__ import annotations

import base64
import hashlib
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import asyncpg
from pydantic import BaseModel, Field

from app.db import get_pool
from app.errors import ApiError
from app.i18n import translate
from app.identity import AuthzContext
from app.integrations.ai import AiResult, AiUnavailable, ImageInput, get_ai_provider, get_ai_settings, get_rules_provider
from app.integrations.ai.localities import find_known_locality
from app.integrations.ai.rules_provider import (
    capability_mentioned_only_as_data,
    draft_from_text,
    proposal_improvements,
    rank_applicant,
    rule_tips,
    strip_contacts,
)
from app.integrations.ai.vocab import (
    DRAFT_FIELDS,
    IMPACTS,
    TIP_FIELD,
    clean_draft,
    has_value,
    clean_proposal,
    clean_shortlist,
    clean_tips,
    compute_missing,
    redact_contacts,
)
from app.services.uploads import ALLOWED_EXT, UPLOAD_DIR
from app.taxonomy_cache import labels_for

logger = logging.getLogger(__name__)

Language = Literal["en", "hi", "te"]
DAY_SECONDS = 86_400
_IMAGE_MEDIA = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp", ".pdf": "application/pdf"}
_MAX_IMAGE_BYTES = 5 * 1024 * 1024


# ---- schemas ----------------------------------------------------------------

class EmploymentFields(BaseModel):
    salary_min_paise: int | None = None
    salary_max_paise: int | None = None
    incentive_type: Literal["none", "fixed_plus_incentive", "incentive_only"] | None = None
    openings: int | None = None
    shift: Literal["day", "night", "rotational", "flexible"] | None = None
    job_timings: str | None = None
    interview_details: str | None = None
    min_qualification: Literal["below_10th", "10th", "12th", "diploma", "iti", "graduate", "postgraduate", "any"] | None = None
    english_level: Literal["none", "basic", "good", "fluent"] | None = None
    experience_min_months: int | None = None
    experience_max_months: int | None = None
    requires_assets: list[str] = Field(default_factory=list)


class ScreeningQuestion(BaseModel):
    text: str


class FreelanceFields(BaseModel):
    budget_type: Literal["fixed", "hourly"] | None = None
    budget_min_paise: int | None = None
    budget_max_paise: int | None = None
    hourly_rate_min_paise: int | None = None
    hourly_rate_max_paise: int | None = None
    duration: Literal["under_1_week", "1_4_weeks", "1_3_months", "3_6_months", "over_6_months", "ongoing"] | None = None
    experience_level: Literal["entry", "intermediate", "expert"] | None = None
    screening_questions: list[ScreeningQuestion] = Field(default_factory=list)


class LocalServiceFields(BaseModel):
    preferred_date: str | None = None  # YYYY-MM-DD
    budget_paise: int | None = None
    urgency: Literal["today", "this_week", "flexible"] | None = None


class DraftIn(BaseModel):
    """A draft as the composer holds it (input to posting tips)."""

    type: str | None = None
    title: str | None = None
    description: str | None = None
    location: str | None = None
    work_mode: str | None = None
    timing: str | None = None
    required_capabilities: list[str] = Field(default_factory=list)
    deadline: datetime | None = None
    employment: EmploymentFields | None = None
    freelance: FreelanceFields | None = None
    local_service: LocalServiceFields | None = None


class DraftOut(BaseModel):
    type: str
    title: str | None
    description: str | None
    location: str | None
    work_mode: str | None
    timing: str | None
    required_capabilities: list[str]
    capability_labels: list[str]
    employment: EmploymentFields | None
    freelance: FreelanceFields | None
    local_service: LocalServiceFields | None
    confidence: dict[str, float]
    missing: list[str]
    questions: list[str]  # localized, one per `missing` entry, same order
    source: Literal["ai", "rules"]
    language: Language


class DraftRequest(BaseModel):
    text: str = Field(min_length=1)
    language: Language | None = None
    entry: Literal["text", "voice"] = "text"


class ImageRequest(BaseModel):
    image_url: str | None = None  # http(s) URL, or the /uploads/<name> URL uploadFile returned
    upload_id: str | None = None  # the bare file name uploadFile returned, if the client kept only that
    language: Language | None = None


class LabelledCode(BaseModel):
    code: str
    text: str


class ShortlistItem(BaseModel):
    enquiry_id: str
    sender_id: str
    listing_id: str | None
    name: str | None  # the applicant's own public listing name, as the poster already sees it in Enquiries
    kind: str | None
    verified: bool
    experience_years: int | None
    distance_km: float | None
    availability: str | None
    stage: str | None
    bid_paise: int | None
    match_score: int
    reasons: list[LabelledCode]
    risks: list[LabelledCode]
    summary: str | None


class ShortlistOut(BaseModel):
    opportunity_id: str
    applicant_count: int
    items: list[ShortlistItem]
    source: Literal["ai", "rules"]
    language: Language


class Tip(BaseModel):
    code: str
    impact: Literal["high", "medium", "low"]
    text: str


class TipsRequest(BaseModel):
    draft: DraftIn | None = None
    opportunity_id: str | None = None
    language: Language | None = None


class TipsOut(BaseModel):
    tips: list[Tip]
    source: Literal["ai", "rules"]
    language: Language


class BidRange(BaseModel):
    """The suggested bid. It never goes below the poster's own stated range
    (FE1); when similar work pays outside that range, `note` says so."""

    min_paise: int | None
    median_paise: int | None
    max_paise: int | None
    sample_size: int
    # capability_overlap / same_type: from similar opportunities' value_amount
    # (kept inside the poster's range); poster_budget: the poster's own stated
    # budget only; none: nothing to go on.
    basis: Literal["capability_overlap", "same_type", "poster_budget", "none"]
    poster_min_paise: int | None = None  # what the poster stated
    poster_max_paise: int | None = None
    market_min_paise: int | None = None  # 25th–75th percentile of similar work, before clamping
    market_max_paise: int | None = None
    # code: market | poster_budget | clamped_to_poster_budget | market_above_poster_budget | none
    note: LabelledCode | None = None


class ProposalRequest(BaseModel):
    opportunity_id: str
    text: str = ""
    language: Language | None = None


class ProposalOut(BaseModel):
    cover_text: str
    improvements: list[LabelledCode]
    bid: BidRange
    source: Literal["ai", "rules"]
    language: Language


# ---- shared plumbing --------------------------------------------------------

def _hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()


def _jsonb(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, (str, bytes)):
        try:
            data = json.loads(value)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


async def _enforce_daily_limit(conn: asyncpg.Connection, ctx: AuthzContext, lang: str) -> None:
    settings = get_ai_settings()
    allowed = await conn.fetchval(
        "SELECT vyapar_platform.check_and_increment($1, $2, $3)", f"ai:{ctx.member_id}", DAY_SECONDS, settings.ai_daily_limit
    )
    if not allowed:
        raise ApiError(429, "ai.error.limitReached", lang, error_code="ai_limit_reached", limit=settings.ai_daily_limit)


async def _audit(ctx: AuthzContext, kind: str, input_hash: str, result: AiResult | None, outcome: str, started: float) -> None:
    """Own connection and transaction, so the row survives a request that
    then fails (an unsupported image, a refused answer)."""
    latency_ms = int((time.perf_counter() - started) * 1000)
    try:
        async with get_pool().acquire() as conn:
            async with conn.transaction():
                await conn.execute("SELECT set_config('vyapar.authz_context', $1, true)", ctx.member_id)
                await conn.execute(
                    """INSERT INTO vyapar_integration.ai_events
                         (member_id, kind, provider, model, input_hash, latency_ms, tokens_in, tokens_out, outcome, credential_id)
                       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)""",
                    ctx.member_id, kind,
                    result.provider if result else get_ai_settings().provider_name,
                    result.model if result else None,
                    input_hash, latency_ms,
                    result.tokens_in if result else 0, result.tokens_out if result else 0,
                    outcome, ctx.credential_id,
                )
    except Exception:  # audit must never break the answer
        logger.exception("ai audit row failed (kind=%s)", kind)


async def _capability_terms(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        "SELECT slug, name_en, name_hi, name_te, aliases FROM vyapar_listings.taxonomy_terms WHERE kind = 'capability' AND status <> 'merged' ORDER BY slug"
    )
    return [{"slug": r["slug"], "name_en": r["name_en"], "name_hi": r["name_hi"], "name_te": r["name_te"], "aliases": list(r["aliases"] or [])} for r in rows]


async def _known_localities(conn: asyncpg.Connection) -> list[str]:
    """The localities Vyapar already knows: those of active listings (the
    same set Discover's locality filter offers) and active opportunities.
    Read under the caller's RLS, so only places visible to them."""
    rows = await conn.fetch(
        """SELECT DISTINCT trim(x) AS name FROM (
             SELECT locality AS x FROM vyapar_listings.listings WHERE state IN ('active_unverified', 'active_verified')
             UNION SELECT location FROM vyapar_opportunities.opportunities WHERE state = 'active' AND location IS NOT NULL
           ) s WHERE x <> '' LIMIT 1000"""
    )
    return [r["name"] for r in rows]


def _canonical_location(clean: dict[str, Any], text: str | None, known: list[str]) -> None:
    """N7: a place named in Hindi or Telugu ("हिमायतनगर की बेकरी") is the
    known locality ("Himayatnagar"), stored in Vyapar's own spelling. Applies
    to Claude's answer and the rules reader alike."""
    found = find_known_locality(text, known) if text else None
    if found is None and clean.get("location"):
        found = find_known_locality(clean["location"], known)
    if found:
        clean["location"] = found
        clean.setdefault("confidence", {})["location"] = max(clean.get("confidence", {}).get("location", 0), 0.8)


async def _call(kind: str, ctx: AuthzContext, input_hash: str, primary, fallback) -> tuple[AiResult, str, str]:
    """Run the configured provider; on AiUnavailable use the rules engine.
    Returns (result, source, outcome) and writes the audit row."""
    started = time.perf_counter()
    provider = get_ai_provider()
    try:
        result = await primary(provider)
        source = "ai" if provider.name == "anthropic" else "rules"
        outcome = "ok"
    except AiUnavailable as exc:
        if fallback is None:
            await _audit(ctx, kind, input_hash, None, exc.reason, started)
            raise
        logger.info("ai %s: %s unavailable (%s); rules fallback", kind, provider.name, exc.reason)
        result = await fallback(get_rules_provider())
        result.notes.append(exc.reason)
        source, outcome = "rules", "fallback"
    await _audit(ctx, kind, input_hash, result, outcome, started)
    return result, source, outcome


def _draft_out(clean: dict[str, Any], lang: str, source: str) -> DraftOut:
    missing = compute_missing(clean, clean.get("missing") or [])
    return DraftOut(
        type=clean["type"],
        title=clean["title"],
        description=clean["description"],
        location=clean["location"],
        work_mode=clean["work_mode"],
        timing=clean["timing"],
        required_capabilities=clean["required_capabilities"],
        capability_labels=labels_for(clean["required_capabilities"], lang),
        employment=EmploymentFields(**clean["employment"]) if clean.get("employment") else None,
        freelance=FreelanceFields(**clean["freelance"]) if clean.get("freelance") else None,
        local_service=LocalServiceFields(**clean["local_service"]) if clean.get("local_service") else None,
        confidence=clean["confidence"],
        missing=missing,
        questions=[translate(f"ai.ask.{field}", lang) for field in missing],
        source=source,  # type: ignore[arg-type]
        language=lang,  # type: ignore[arg-type]
    )


# ---- 1. draft from text -----------------------------------------------------

async def draft_opportunity(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, body: DraftRequest) -> DraftOut:
    lang = body.language or lang
    settings = get_ai_settings()
    text = body.text.strip()
    if len(text) > settings.ai_max_input_chars:
        raise ApiError(422, "ai.error.textTooLong", lang, max=settings.ai_max_input_chars)
    await _enforce_daily_limit(conn, ctx, lang)
    terms = await _capability_terms(conn)
    slugs = {t["slug"] for t in terms}
    result, source, _ = await _call(
        "draft", ctx, _hash({"text": text, "language": lang, "entry": body.entry}),
        lambda p: p.draft_opportunity(text, lang, body.entry, terms),
        lambda p: p.draft_opportunity(text, lang, body.entry, terms),
    )
    clean = clean_draft(result.data, slugs)
    if source == "ai":
        # Same context rule as the rules reader: a skill named only as data
        # ("sales charts" on a dashboard) is not a skill the work needs.
        by_slug = {t["slug"]: t for t in terms}
        clean["required_capabilities"] = [
            s for s in clean["required_capabilities"] if not capability_mentioned_only_as_data(text, by_slug[s])
        ]
    _canonical_location(clean, text, await _known_localities(conn))
    return _draft_out(clean, lang, source)


# ---- 2. draft from an image -------------------------------------------------

async def _load_image(body: ImageRequest, lang: str) -> ImageInput:
    ref = (body.image_url or "").strip()
    name: str | None = None
    if body.upload_id:
        name = body.upload_id.strip()
    elif ref.startswith("/uploads/"):
        name = ref[len("/uploads/"):]
    elif "/uploads/" in ref and ref.startswith(("http://", "https://")):
        name = ref.rsplit("/uploads/", 1)[1]
    if name is not None:
        if "/" in name or "\\" in name or name.startswith(".") or not name:
            raise ApiError(422, "ai.error.imageNotFound", lang)
        path = Path(UPLOAD_DIR) / name
        ext = path.suffix.lower()
        if ext not in ALLOWED_EXT or ext not in _IMAGE_MEDIA or not path.is_file():
            raise ApiError(422, "ai.error.imageNotFound", lang)
        data = path.read_bytes()
        if len(data) > _MAX_IMAGE_BYTES:
            raise ApiError(413, "ai.error.imageTooLarge", lang)
        return ImageInput(media_type=_IMAGE_MEDIA[ext], data_base64=base64.standard_b64encode(data).decode("ascii"))
    if ref.startswith(("http://", "https://")):
        if ref.lower().split("?", 1)[0].endswith(".pdf"):
            raise ApiError(422, "ai.error.pdfNeedsUpload", lang)
        return ImageInput(media_type="image/*", url=ref)
    raise ApiError(422, "ai.error.imageRequired", lang)


async def read_opportunity_image(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, body: ImageRequest) -> DraftOut:
    lang = body.language or lang
    image = await _load_image(body, lang)
    await _enforce_daily_limit(conn, ctx, lang)
    terms = await _capability_terms(conn)
    slugs = {t["slug"] for t in terms}
    input_hash = _hash({"image": image.url or hashlib.sha256((image.data_base64 or "").encode()).hexdigest(), "language": lang})
    try:
        result, source, _ = await _call("read_image", ctx, input_hash, lambda p: p.read_opportunity_image(image, lang, terms), None)
    except AiUnavailable as exc:
        if exc.reason == "unsupported_without_ai":
            raise ApiError(501, "ai.error.unsupportedWithoutAi", lang) from exc
        raise ApiError(503, "ai.error.unavailable", lang) from exc
    clean = clean_draft(result.data, slugs)
    _canonical_location(clean, None, await _known_localities(conn))
    return _draft_out(clean, lang, source)


# ---- 3. shortlist -----------------------------------------------------------

def _opportunity_facts(opp: dict[str, Any]) -> dict[str, Any]:
    """What a provider may know about the opportunity — its own public text
    and typed fields, never the poster's identity."""
    facts: dict[str, Any] = {
        "type": opp.get("type"),
        "title": opp.get("title"),
        "description": redact_contacts(opp.get("description") or "")[:1500],
        "requirements": redact_contacts(opp.get("requirements") or "")[:600],
        "required_capabilities": list(opp.get("required_capabilities") or []),
        "location": opp.get("location"),
        "work_mode": opp.get("work_mode"),
        "timing": opp.get("timing"),
        "value_rupees": _budget_rupees(opp),
    }
    for key in ("salary_min_paise", "salary_max_paise", "min_qualification", "english_level", "experience_min_months",
                "experience_max_months", "shift", "job_timings", "openings", "budget_type", "budget_min_paise", "budget_max_paise",
                "hourly_rate_min_paise", "hourly_rate_max_paise", "duration", "experience_level", "screening_questions",
                "preferred_date", "budget_paise", "urgency"):
        if opp.get(key) not in (None, "", [], {}):
            facts[key] = opp[key]
    # 018 stores screening questions as [{id, text}]; providers need the text only.
    if isinstance(facts.get("screening_questions"), list):
        facts["screening_questions"] = [
            str(q.get("text") if isinstance(q, dict) else q)[:200] for q in facts["screening_questions"] if q
        ][:5]
    return facts


def _budget_rupees(opp: dict[str, Any]) -> float | None:
    """The one number a bid is compared with: the typed budget from 018 when
    present (freelance total or hourly, local-service budget, monthly salary),
    else the legacy value_amount."""
    for key in ("budget_max_paise", "budget_min_paise", "hourly_rate_max_paise", "budget_paise", "salary_max_paise"):
        v = opp.get(key)
        if isinstance(v, (int, float)) and v > 0:
            return round(v / 100, 2)
    value = opp.get("value_amount")
    return float(value) if isinstance(value, (int, float)) and value > 0 else None


def _bid_rupees(enquiry: dict[str, Any]) -> tuple[int | None, int | None]:
    """(bid_paise, bid_rupees) from whichever column workstream A adds."""
    for key in ("bid_amount_paise", "bid_paise", "bid_max_paise", "bid_min_paise"):
        v = enquiry.get(key)
        if isinstance(v, (int, float)) and v > 0:
            return int(v), int(round(v / 100))
    for key in ("bid_amount", "bid_value", "bid_rupees"):
        v = enquiry.get(key)
        if isinstance(v, (int, float)) and v > 0:
            return int(round(v * 100)), int(round(v))
    return None, None


async def get_ai_shortlist(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, opportunity_id: str, language: str | None = None) -> ShortlistOut:
    lang = language or lang
    try:
        row = await conn.fetchrow("SELECT to_jsonb(o) AS opp FROM vyapar_opportunities.opportunities o WHERE o.id = $1", opportunity_id)
    except asyncpg.DataError:
        row = None
    if row is None:
        raise ApiError(404, "common.error.opportunityNotFound", lang)
    opp = _jsonb(row["opp"])
    if opp.get("poster_id") != ctx.member_id:
        raise ApiError(403, "ai.error.posterOnly", lang)

    enquiry_rows = await conn.fetch(
        """SELECT to_jsonb(e) AS enquiry FROM vyapar_enquiries.enquiries e
            WHERE e.opportunity_id = $1 AND e.state NOT IN ('withdrawn', 'restricted')
            ORDER BY e.created_at""",
        opportunity_id,
    )
    enquiries = [_jsonb(r["enquiry"]) for r in enquiry_rows]
    if not enquiries:
        return ShortlistOut(opportunity_id=opportunity_id, applicant_count=0, items=[], source="rules", language=lang)  # type: ignore[arg-type]

    await _enforce_daily_limit(conn, ctx, lang)
    enquiry_ids = [e["id"] for e in enquiries]
    sender_ids = list({e["sender_id"] for e in enquiries})
    wanted = list(opp.get("required_capabilities") or [])
    covers = {
        str(r["enquiry_id"]): r["body"]
        for r in await conn.fetch(
            """SELECT DISTINCT ON (enquiry_id) enquiry_id, body FROM vyapar_enquiries.enquiry_messages
                WHERE enquiry_id = ANY($1::uuid[]) AND sender_id <> $2 AND NOT system_note
                ORDER BY enquiry_id, created_at""",
            enquiry_ids, ctx.member_id,
        )
    }
    listings = {
        r["owner_id"]: r
        for r in await conn.fetch(
            """SELECT DISTINCT ON (l.owner_id) l.id, l.owner_id, l.kind, l.name, l.capabilities, l.capability_visible,
                      l.experience_years, l.locality, l.verification_state, l.availability,
                      vyapar_platform.distance_km($3, $4, l.lat, l.lng) AS distance_km
                 FROM vyapar_listings.listings l
                WHERE l.owner_id = ANY($1::text[]) AND l.state IN ('active_unverified', 'active_verified')
                ORDER BY l.owner_id, (l.capabilities && $2::text[]) DESC, (l.state = 'active_verified') DESC, l.updated_at DESC""",
            sender_ids, wanted, opp.get("lat"), opp.get("lng"),
        )
    }

    applicants: list[dict[str, Any]] = []
    meta: dict[str, dict[str, Any]] = {}
    for i, e in enumerate(enquiries, start=1):
        ref = f"a{i}"
        listing = listings.get(e["sender_id"])
        snapshot = _jsonb(e.get("profile_snapshot"))
        caps = list(listing["capabilities"]) if listing is not None and listing["capability_visible"] else list(snapshot.get("capabilities") or [])
        years = listing["experience_years"] if listing is not None else snapshot.get("experience_years")
        bid_paise, bid_rupees = _bid_rupees(e)
        comparable = not (e.get("bid_type") and opp.get("budget_type") and e.get("bid_type") != opp.get("budget_type"))
        verified = listing is not None and listing["verification_state"] in ("verified", "expiring")
        distance = float(listing["distance_km"]) if listing is not None and listing["distance_km"] is not None else None
        applicants.append({
            "ref": ref,
            "capabilities": caps,
            "experience_years": years,
            "distance_km": round(distance, 1) if distance is not None else None,
            "verified": verified,
            "has_profile": listing is not None,
            "availability": listing["availability"] if listing is not None else None,
            "cover_text": (covers.get(str(e["id"])) or "")[:1200],
            "bid_rupees": bid_rupees if comparable else None,
            "bid_type": e.get("bid_type"),
            "stage": e.get("stage"),
        })
        meta[ref] = {
            "enquiry_id": str(e["id"]), "sender_id": e["sender_id"],
            "listing_id": str(listing["id"]) if listing is not None else None,
            "name": listing["name"] if listing is not None else None,
            "kind": listing["kind"] if listing is not None else None,
            "verified": verified, "experience_years": years, "distance_km": round(distance, 1) if distance is not None else None,
            "availability": listing["availability"] if listing is not None else None,
            "stage": e.get("stage"), "bid_paise": bid_paise,
        }

    facts = _opportunity_facts(opp)
    baseline = {a["ref"]: rank_applicant(facts, a) for a in applicants}
    result, source, _ = await _call(
        "shortlist", ctx, _hash({"opportunity": opportunity_id, "enquiries": enquiry_ids, "language": lang}),
        lambda p: p.shortlist(facts, applicants, lang),
        lambda p: p.shortlist(facts, applicants, lang),
    )
    answered = clean_shortlist(result.data, [a["ref"] for a in applicants]) if source == "ai" else {}

    items: list[ShortlistItem] = []
    for a in applicants:
        ref = a["ref"]
        pick = answered.get(ref) or baseline[ref]
        if "no_capability_overlap" in baseline[ref]["risks"]:
            # Same guard for Claude as for the rules: none of the required
            # skills caps the score at 3, and the poster is always told why.
            pick = {**pick, "match_score": min(pick["match_score"], 3),
                    "risks": ["no_capability_overlap"] + [r for r in pick["risks"] if r != "no_capability_overlap"][:2]}
        items.append(ShortlistItem(
            **meta[ref],
            match_score=pick["match_score"],
            reasons=[LabelledCode(code=c, text=translate(f"ai.reason.{c}", lang)) for c in pick["reasons"]],
            risks=[LabelledCode(code=c, text=translate(f"ai.risk.{c}", lang)) for c in pick["risks"]],
            summary=pick.get("summary"),
        ))
    items.sort(key=lambda it: (-it.match_score, it.enquiry_id))
    return ShortlistOut(opportunity_id=opportunity_id, applicant_count=len(items), items=items, source=source, language=lang)  # type: ignore[arg-type]


# ---- 4. posting tips --------------------------------------------------------

def _draft_dict_from_opportunity(opp: dict[str, Any]) -> dict[str, Any]:
    t = opp.get("type") or "employment"
    draft: dict[str, Any] = {
        "type": t, "title": opp.get("title"), "description": opp.get("description"), "location": opp.get("location"),
        "work_mode": opp.get("work_mode"), "timing": opp.get("timing"),
        "required_capabilities": list(opp.get("required_capabilities") or []), "deadline": opp.get("deadline"),
        "employment": None, "freelance": None, "local_service": None,
    }
    block = {k: opp.get(k) for k in EmploymentFields.model_fields} if t == "employment" else \
        {k: opp.get(k) for k in FreelanceFields.model_fields} if t == "freelance" else \
        {k: opp.get(k) for k in LocalServiceFields.model_fields} if t == "local_service" else None
    if block is not None:
        if t == "employment" and not isinstance(block.get("requires_assets"), list):
            block["requires_assets"] = []
        if t == "freelance" and not isinstance(block.get("screening_questions"), list):
            block["screening_questions"] = []
        draft[t] = block
    return draft


def _draft_dict_from_input(draft: DraftIn) -> dict[str, Any]:
    d = draft.model_dump()
    d["type"] = d.get("type") or "employment"
    return d


async def _with_stated_fields(conn: asyncpg.Connection, draft: dict[str, Any], text: str) -> dict[str, Any]:
    """N7: a tip must never ask for what the poster already wrote. Reads the
    title, description and requirements with the same rules reader as
    drafting, and fills every EMPTY field of a copy of the draft with what the
    text states (hours, headcount, qualification, place, pay …). Only used to
    decide which tips apply; nothing is returned or saved from it."""
    merged = {k: (dict(v) if isinstance(v, dict) else v) for k, v in draft.items()}
    if not text.strip():
        return merged
    terms = await _capability_terms(conn)
    stated = clean_draft(draft_from_text(text, terms, force_type=merged.get("type")), {t["slug"] for t in terms})
    _canonical_location(stated, text, await _known_localities(conn))
    for key in ("title", "location", "work_mode", "timing"):
        if not merged.get(key) and stated.get(key):
            merged[key] = stated[key]
    if not merged.get("required_capabilities") and stated.get("required_capabilities"):
        merged["required_capabilities"] = stated["required_capabilities"]
    t = merged.get("type")
    if t in ("employment", "freelance", "local_service") and stated.get(t):
        block = dict(merged.get(t) or {})
        for key, value in stated[t].items():
            if block.get(key) in (None, "", [], {}) and value not in (None, "", [], {}):
                block[key] = value
        merged[t] = block
    return merged


async def get_posting_tips(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, body: TipsRequest) -> TipsOut:
    lang = body.language or lang
    if body.opportunity_id:
        try:
            row = await conn.fetchrow("SELECT to_jsonb(o) AS opp FROM vyapar_opportunities.opportunities o WHERE o.id = $1", body.opportunity_id)
        except asyncpg.DataError:
            row = None
        if row is None:
            raise ApiError(404, "common.error.opportunityNotFound", lang)
        opp = _jsonb(row["opp"])
        if opp.get("poster_id") != ctx.member_id:
            raise ApiError(403, "ai.error.posterOnly", lang)
        draft = _draft_dict_from_opportunity(opp)
    elif body.draft is not None:
        draft = _draft_dict_from_input(body.draft)
    else:
        raise ApiError(422, "ai.error.draftOrOpportunityRequired", lang)

    await _enforce_daily_limit(conn, ctx, lang)
    written = " \n".join(str(draft.get(k) or "") for k in ("title", "description", "requirements") if draft.get(k))
    if body.opportunity_id:
        written += " \n" + str(opp.get("requirements") or "")
    draft = await _with_stated_fields(conn, draft, written)
    base = rule_tips(draft)
    for tip in base:
        tip["text"] = translate(f"ai.tip.{tip['code']}", lang)
    payload = {k: v for k, v in draft.items() if k != "deadline"}
    result, source, _ = await _call(
        "tips", ctx, _hash({"draft": payload, "language": lang}),
        lambda p: p.posting_tips(payload, base, lang),
        lambda p: p.posting_tips(payload, base, lang),
    )
    tips = base
    if source == "ai":
        ai_tips = clean_tips(result.data)
        if ai_tips:
            merged: dict[str, dict[str, Any]] = {t["code"]: t for t in base}
            for t in ai_tips:
                merged[t["code"]] = {"code": t["code"], "impact": t["impact"], "text": t["text"] or translate(f"ai.tip.{t['code']}", lang)}
            tips = list(merged.values())
    # Claude included: a tip asking for a field the draft or its text already states is dropped.
    tips = [t for t in tips if not (TIP_FIELD.get(t["code"]) and has_value(draft, TIP_FIELD[t["code"]]))]
    order = {v: i for i, v in enumerate(IMPACTS)}
    tips.sort(key=lambda t: order.get(t["impact"], 9))
    return TipsOut(tips=[Tip(**t) for t in tips[:8]], source=source, language=lang)  # type: ignore[arg-type]


# ---- 5. improve a proposal --------------------------------------------------

def _inr(paise: int) -> str:
    """₹ with Indian digit grouping: 4800000 paise -> ₹48,000; 12500000 -> ₹1,25,000."""
    rupees = int(round(paise / 100))
    s = str(rupees)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        head = ",".join([head[max(0, i - 2): i] for i in range(len(head), 0, -2)][::-1])
        s = f"{head},{tail}"
    return f"₹{s}"


def _span(lo: int, hi: int) -> str:
    return _inr(lo) if lo == hi else f"{_inr(lo)}–{_inr(hi)}"


def poster_range(opp: dict[str, Any]) -> tuple[int | None, int | None]:
    """What the poster stated, in paise. A single figure is a range of one."""
    if opp.get("budget_type") == "hourly":
        lo, hi = opp.get("hourly_rate_min_paise"), opp.get("hourly_rate_max_paise")
    else:
        lo, hi = opp.get("budget_min_paise"), opp.get("budget_max_paise")
    if not (lo or hi) and opp.get("budget_paise"):
        lo = hi = opp["budget_paise"]
    if not (lo or hi):
        budget = _budget_rupees(opp)
        lo = hi = int(round(budget * 100)) if budget else None
    lo, hi = (int(lo) if lo else None), (int(hi) if hi else None)
    lo, hi = lo or hi, hi or lo
    if lo and hi and lo > hi:
        lo, hi = hi, lo
    return lo, hi


def suggest_bid(market: list[int] | None, sample_size: int, basis: str, poster_lo: int | None, poster_hi: int | None, lang: str) -> BidRange:
    """The one rule for a suggested bid, for the rules engine and Claude alike:
    never below the poster's stated range. Similar work that pays less is
    raised to the poster's floor, and similar work that pays more is held at
    the poster's ceiling — each time with a note saying why."""
    def note(code: str, **params: Any) -> LabelledCode:
        return LabelledCode(code=code, text=translate(f"ai.bid.{code}", lang, **params))

    if market and poster_lo and poster_hi:
        clamp = [min(max(v, poster_lo), poster_hi) for v in market]
        common = dict(sample_size=sample_size, basis=basis, poster_min_paise=poster_lo, poster_max_paise=poster_hi,
                      market_min_paise=market[0], market_max_paise=market[2])
        params = {"n": sample_size, "market": _span(market[0], market[2]), "poster": _span(poster_lo, poster_hi)}
        if clamp == market:
            return BidRange(min_paise=market[0], median_paise=market[1], max_paise=market[2], note=note("market", **params), **common)
        if market[0] >= poster_hi:
            return BidRange(min_paise=poster_hi, median_paise=poster_hi, max_paise=poster_hi, note=note("market_above_poster_budget", **params), **common)
        return BidRange(min_paise=clamp[0], median_paise=clamp[1], max_paise=clamp[2], note=note("clamped_to_poster_budget", **params), **common)
    if market:
        return BidRange(min_paise=market[0], median_paise=market[1], max_paise=market[2], sample_size=sample_size, basis=basis,  # type: ignore[arg-type]
                        market_min_paise=market[0], market_max_paise=market[2],
                        note=note("market", n=sample_size, market=_span(market[0], market[2]), poster=""))
    if poster_lo and poster_hi:
        return BidRange(min_paise=poster_lo, median_paise=(poster_lo + poster_hi) // 2, max_paise=poster_hi, sample_size=0,
                        basis="poster_budget", poster_min_paise=poster_lo, poster_max_paise=poster_hi,
                        note=note("poster_budget", poster=_span(poster_lo, poster_hi)))
    return BidRange(min_paise=None, median_paise=None, max_paise=None, sample_size=0, basis="none", note=note("none"))


async def _bid_range(conn: asyncpg.Connection, opp: dict[str, Any], lang: str) -> BidRange:
    """p25/p50/p75 of value_amount across similar opportunities the caller
    can see (same type with overlapping capabilities first, then same type),
    passed through suggest_bid() with the poster's stated range."""
    plo, phi = poster_range(opp)
    wanted = list(opp.get("required_capabilities") or [])
    for basis, extra in (("capability_overlap", "AND o.required_capabilities && $3::text[]"), ("same_type", "")):
        if basis == "capability_overlap" and not wanted:
            continue
        args: list[Any] = [opp.get("type"), opp.get("id")]
        if basis == "capability_overlap":
            args.append(wanted)
        row = await conn.fetchrow(
            f"""SELECT count(*) AS n,
                       percentile_cont(ARRAY[0.25, 0.5, 0.75]) WITHIN GROUP (ORDER BY o.value_amount) AS q
                  FROM vyapar_opportunities.opportunities o
                 WHERE o.type = $1 AND o.id <> $2::uuid AND o.value_amount > 0 {extra}""",
            *args,
        )
        if row and row["n"] >= 3 and row["q"] is not None:
            q = [int(round(float(x) * 100)) for x in row["q"]]
            return suggest_bid(q, int(row["n"]), basis, plo, phi, lang)
    return suggest_bid(None, 0, "none", plo, phi, lang)


def _rules_cover_text(opp: dict[str, Any], text: str, applicant: dict[str, Any], lang: str) -> str:
    parts: list[str] = []
    cleaned = strip_contacts(text.strip())  # contact details are shared in chat once connected, never in the pitch
    if cleaned:
        # The person's own words come first; a sentence added after them needs a full stop between.
        parts.append(cleaned if cleaned[-1] in ".!?।" else cleaned + ("।" if lang == "hi" else "."))
    else:
        parts.append(translate("ai.proposal.greeting", lang))
        parts.append(translate("ai.proposal.interest", lang, title=opp.get("title") or ""))
    # Only claims the applicant's own profile supports FOR THIS WORK: skills
    # that match what it asks for, and years only when those skills match.
    # (A developer applying to architecture work is never made to claim
    # "8 years of experience in this".)
    wanted = set(opp.get("required_capabilities") or [])
    matched = [c for c in applicant.get("capabilities") or [] if c in wanted] if wanted else list(applicant.get("capabilities") or [])[:3]
    low = cleaned.lower()
    if matched and not any(m.replace("_", " ") in low for m in matched):
        parts.append(translate("ai.proposal.skills", lang, skills=", ".join(labels_for(matched, lang))))
    years = applicant.get("experience_years")
    if years and matched and not any(w in low for w in ("year", "yrs", "साल", "సంవత్సర")):
        parts.append(translate("ai.proposal.experience", lang, years=years))
    availability = applicant.get("availability")
    if availability in ("now", "this_week", "later") and not any(w in low for w in ("available", "start", "join", "अभी", "उपलब्ध", "అందుబాటు")):
        parts.append(translate(f"ai.proposal.availability.{availability}", lang))
    if not cleaned:
        parts.append(translate("ai.proposal.closing", lang))
    return " ".join(p for p in parts if p)


async def improve_proposal(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, body: ProposalRequest) -> ProposalOut:
    lang = body.language or lang
    settings = get_ai_settings()
    text = body.text.strip()
    if len(text) > settings.ai_max_input_chars:
        raise ApiError(422, "ai.error.textTooLong", lang, max=settings.ai_max_input_chars)
    try:
        row = await conn.fetchrow("SELECT to_jsonb(o) AS opp FROM vyapar_opportunities.opportunities o WHERE o.id = $1", body.opportunity_id)
    except asyncpg.DataError:
        row = None
    if row is None:
        raise ApiError(404, "common.error.opportunityNotFound", lang)
    opp = _jsonb(row["opp"])
    await _enforce_daily_limit(conn, ctx, lang)

    wanted = list(opp.get("required_capabilities") or [])
    mine = await conn.fetchrow(
        """SELECT capabilities, capability_visible, experience_years, availability, verification_state, kind
             FROM vyapar_listings.listings
            WHERE owner_id = $1 AND state IN ('active_unverified', 'active_verified')
            ORDER BY (capabilities && $2::text[]) DESC, (state = 'active_verified') DESC, updated_at DESC
            LIMIT 1""",
        ctx.member_id, wanted,
    )
    applicant = {
        "capabilities": list(mine["capabilities"]) if mine is not None else [],
        "experience_years": mine["experience_years"] if mine is not None else None,
        "availability": mine["availability"] if mine is not None else None,
        "verified": mine is not None and mine["verification_state"] in ("verified", "expiring"),
        "kind": mine["kind"] if mine is not None else None,
    }
    facts = _opportunity_facts(opp)
    bid = await _bid_range(conn, opp, lang)
    result, source, _ = await _call(
        "proposal", ctx, _hash({"opportunity": body.opportunity_id, "text": text, "language": lang}),
        lambda p: p.improve_proposal(facts, text, applicant, lang),
        lambda p: p.improve_proposal(facts, text, applicant, lang),
    )
    clean = clean_proposal(result.data)
    cover = clean["cover_text"] if source == "ai" and clean["cover_text"] else _rules_cover_text(opp, text, applicant, lang)
    if source == "ai":
        codes = clean["improvements"]
    else:
        # What the SUGGESTED text still lacks, plus a note when contact
        # details had to be taken out of what the person typed.
        codes = proposal_improvements(facts, cover, applicant)
        if "remove_contact_details" in proposal_improvements(facts, text, applicant) and "remove_contact_details" not in codes:
            codes = ["remove_contact_details"] + codes[:3]
    return ProposalOut(
        cover_text=cover,
        improvements=[LabelledCode(code=c, text=translate(f"ai.improvement.{c}", lang)) for c in codes],
        bid=bid,
        source=source,  # type: ignore[arg-type]
        language=lang,  # type: ignore[arg-type]
    )


__all__ = [
    "DRAFT_FIELDS", "DraftIn", "DraftOut", "DraftRequest", "ImageRequest", "ProposalOut", "ProposalRequest",
    "ShortlistOut", "TipsOut", "TipsRequest", "draft_opportunity", "get_ai_shortlist", "get_posting_tips",
    "improve_proposal", "read_opportunity_image",
]

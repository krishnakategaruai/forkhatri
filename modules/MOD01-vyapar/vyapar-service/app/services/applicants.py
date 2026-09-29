# [Backend A, 2026-09-28] The poster's applicant list and hiring pipeline.
# Why: a person who posted a job or project had only a flat enquiry inbox.
# WorkIndia gives an employer a candidate list with filters and a call
# button; Upwork gives a client proposals it can shortlist, compare, hire or
# decline. Vyapar now does the same over its own enquiries:
#   * every application/proposal on an opportunity is a row, carrying the
#     applicant's profile snapshot, bid and timeline, and a rule-based match
#     score computed from the SAME allow-listed signals app/ranking.py uses
#     everywhere else (capability, location, experience, timing, value) —
#     never a second scorer and never a sensitive attribute;
#   * the poster moves each applicant through `stage`
#     (new -> shortlisted -> hired | declined), separate from the thread
#     `state`. Hiring also accepts the thread through the existing
#     `accept_enquiry` path, so contact disclosure follows the one rule that
#     already governs it. Declining closes the thread and notifies the
#     applicant in their own language; the poster never has to type a
#     rejection. hired and declined are final.
#   * applicant.shortlisted|hired|declined domain events are written to the
#     enquiries outbox by the migration-018 trigger, in the same transaction.
# RLS: enquiries are visible only to their two parties; every query here
# additionally pins `provider_id = caller`, and the opportunity must be the
# caller's own (404 otherwise, never revealing that it has applicants).
# Traces to: FR22, FR23, FR24, FR19 (signal allow-list), TR022, TR023, SP019
from __future__ import annotations

from typing import Literal

import asyncpg
from pydantic import BaseModel, Field

from app.audit import audit
from app.errors import ApiError
from app.i18n import translate
from app.identity import AuthzContext
from app.notifications import notify_interaction_party
from app.ranking import DEFAULT_WEIGHTS, RankingSignals, score, top_signal_keys
from app.services import contact as contact_svc
from app.services import enquiries as enquiries_svc
from app.services.shortlist_contact import shortlist_contact_actions
from app.services.enquiries import Milestone, ProfileSnapshot, _json
from app.services.opportunities import has_budget, structured_from_row
from app.services.pagination import DEFAULT_LIMIT, decode_cursor, encode_cursor
from app.taxonomy_cache import labels_for

Stage = Literal["new", "shortlisted", "hired", "declined"]
STAGES: tuple[str, ...] = ("new", "shortlisted", "hired", "declined")
FINAL_STAGES = frozenset({"hired", "declined"})
MAX_COMPARE = 4
AVAILABILITY_FIT = {"now": 1.0, "this_week": 0.7, "later": 0.3}
# The signals an applicant score uses, and so the maximum it can reach.
_APPLICANT_SIGNALS = ("capability_fit", "location_fit", "experience_fit", "timing_fit", "value_fit")


class ApplicantProfile(ProfileSnapshot):
    capability_labels: list[str] = []  # localized, index-aligned with `capabilities`


class SkillRef(BaseModel):
    slug: str
    label: str


class SkillsMatch(BaseModel):
    """ONE verdict on the required skills, from the actual overlap, so a card
    can never say both "has the skills" and "only some of the skills"."""

    state: Literal["all", "some", "none", "not_required"]
    kind: Literal["reason", "risk"] | None = Field(description="reason for all/some, risk for none, null when nothing is required")
    matched_count: int
    required_count: int
    matched_skills: list[str] = Field(description="Localized labels of the required skills the applicant has")
    missing_skills: list[str] = Field(description="Localized labels of the required skills the applicant lacks")
    text: str | None = Field(description='Localized, e.g. "Has 2 of 3 skills: React, Software development"')
    missing_text: str | None = Field(description='Localized, e.g. "Missing: Startup operations"; null when nothing is missing')


class ScreeningAnswerOut(BaseModel):
    question_id: str
    question: str | None  # the question text as the poster wrote it
    answer: str


class ApplicantOut(BaseModel):
    enquiry_id: str
    sender_id: str
    name: str | None
    profile: ApplicantProfile
    action_type: str  # apply | propose | ...
    applied_via: str
    stage: str
    stage_changed_at: str | None
    thread_state: str
    bid_amount_paise: int | None
    bid_type: str | None
    timeline_days: int | None
    milestones: list[Milestone]
    screening_answers: list[ScreeningAnswerOut]
    message_preview: str | None = Field(description="First message of the thread, up to 200 characters")
    created_at: str
    match_score: int = Field(ge=0, le=100, description="Rule-based fit, 0-100, from the ranking signal allow-list")
    match_signals: list[str] = Field(description="Top contributing signal keys, e.g. capability_fit")
    match_reasons: list[str] = Field(description="Localized, written for the poster; at most one is about skills (skills_match.text)")
    match_risks: list[str] = Field(default_factory=list, description="Localized concerns, e.g. none of the required skills, bid above budget")
    skills_match: SkillsMatch
    missing_skills: list[SkillRef] = Field(default_factory=list, description="Required skills the applicant lacks, slug + label")
    matched_capability_labels: list[str] = []
    missing_capability_labels: list[str] = []  # kept for existing clients; same labels as missing_skills
    # [critique L11] The poster's Call / WhatsApp for this applicant: while
    # shortlisted (no call hours; the applicant consented by applying) and
    # after hiring (workstream B's accepted-enquiry rule). [] otherwise.
    contact_actions: list[dict] = Field(default_factory=list)
    contact_revealed: bool = False


class ApplicantPage(BaseModel):
    items: list[ApplicantOut]
    next_cursor: str | None = None
    total: int = Field(description="Applicants matching the stage filter")
    stage_counts: dict[str, int] = Field(description="Applicants per stage, ignoring the stage filter")


class StageIn(BaseModel):
    stage: Stage


class CompareOut(BaseModel):
    opportunity_id: str
    opportunity_title: str
    required_capabilities: list[str]
    required_capability_labels: list[str]
    items: list[ApplicantOut]


async def _own_opportunity(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, opportunity_id: str) -> asyncpg.Record:
    try:
        row = await conn.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    except asyncpg.DataError:
        row = None
    if row is None or row["poster_id"] != ctx.member_id:
        raise ApiError(404, "common.error.opportunityNotFound", lang)
    return row


def _signals(opp: asyncpg.Record, snap: ProfileSnapshot, bid_paise: int | None) -> RankingSignals:
    required = set(opp["required_capabilities"] or [])
    have = set(snap.capabilities)
    capability_fit = len(required & have) / len(required) if required else 0.5

    if opp["work_mode"] == "remote":
        location_fit = 1.0
    elif opp["location"] and snap.locality:
        a, b = opp["location"].strip().lower(), snap.locality.strip().lower()
        location_fit = 1.0 if (a in b or b in a) else 0.3
    else:
        location_fit = 0.3

    s = structured_from_row(opp)
    min_months = s.experience_min_months
    if min_months is None and s.experience_level:
        min_months = {"entry": 0, "intermediate": 24, "expert": 60}[s.experience_level]
    have_months = snap.experience_years * 12 if snap.experience_years is not None else None
    if not min_months:
        experience_fit = 1.0 if have_months else 0.5
    elif have_months is None:
        experience_fit = 0.0
    else:
        experience_fit = min(1.0, have_months / min_months)

    timing_fit = AVAILABILITY_FIT.get(snap.availability or "", 0.3)

    value_fit = 0.5
    if bid_paise is not None and opp["type"] == "freelance" and has_budget(s):
        cap = (s.hourly_rate_max_paise or s.hourly_rate_min_paise) if s.budget_type == "hourly" else (s.budget_max_paise or s.budget_min_paise)
        if cap:
            value_fit = 1.0 if bid_paise <= cap else max(0.0, 1.0 - (bid_paise - cap) / cap)
    return RankingSignals(
        capability_fit=capability_fit, location_fit=location_fit, experience_fit=experience_fit,
        timing_fit=timing_fit, value_fit=value_fit,
    )


# Signals other than skills, worded for the POSTER (ranking.signal.* speaks
# to the viewer about themselves: "close to you", "matches your experience").
_POSTER_REASON_SIGNALS = ("location_fit", "experience_fit", "timing_fit", "value_fit")


def skills_match(required: list[str], have: set[str], lang: str) -> SkillsMatch:
    matched = [c for c in required if c in have]
    missing = [c for c in required if c not in have]
    m_labels, x_labels = labels_for(matched, lang), labels_for(missing, lang)
    if not required:
        state, kind, text = "not_required", None, None
    elif not missing:
        state, kind = "all", "reason"
        text = (translate("enquiries.applicant.skills.allOne", lang, skills=m_labels[0]) if len(required) == 1
                else translate("enquiries.applicant.skills.all", lang, count=len(required)))
    elif matched:
        state, kind = "some", "reason"
        text = translate("enquiries.applicant.skills.some", lang, matched=len(matched), total=len(required), skills=", ".join(m_labels))
    else:
        state, kind = "none", "risk"
        text = translate("enquiries.applicant.skills.none", lang)
    return SkillsMatch(
        state=state, kind=kind, matched_count=len(matched), required_count=len(required),
        matched_skills=m_labels, missing_skills=x_labels, text=text,
        missing_text=translate("enquiries.applicant.skills.missing", lang, skills=", ".join(x_labels)) if x_labels else None,
    )


def _match_score(signals: RankingSignals) -> int:
    best = sum(DEFAULT_WEIGHTS[k] for k in _APPLICANT_SIGNALS)
    return max(0, min(100, round(100 * score(signals) / best)))


def _to_applicant(opp: asyncpg.Record, row: asyncpg.Record, first_message: str | None, lang: str) -> ApplicantOut:
    snap = ProfileSnapshot(**(_json(row["profile_snapshot"], None) or {}))
    required = list(opp["required_capabilities"] or [])
    have = set(snap.capabilities)
    signals = _signals(opp, snap, row["bid_amount_paise"])
    keys = top_signal_keys(signals)
    questions = {q.id: q.text for q in (structured_from_row(opp).screening_questions or [])}
    skills = skills_match(required, have, lang)
    reasons: list[str] = [skills.text] if skills.kind == "reason" and skills.text else []
    for k in keys:
        if k in _POSTER_REASON_SIGNALS and getattr(signals, k) >= 0.6:
            reasons.append(translate(f"enquiries.applicant.reason.{k}", lang))
    risks: list[str] = [skills.text] if skills.kind == "risk" and skills.text else []
    if row["bid_amount_paise"] is not None and signals.value_fit < 1.0 and opp["type"] == "freelance" and has_budget(structured_from_row(opp)):
        risks.append(translate("enquiries.applicant.risk.bidAboveBudget", lang))
    return ApplicantOut(
        enquiry_id=str(row["id"]),
        sender_id=row["sender_id"],
        name=snap.name,
        profile=ApplicantProfile(**snap.model_dump(), capability_labels=labels_for(snap.capabilities, lang)),
        action_type=row["action_type"],
        applied_via=row["applied_via"],
        stage=row["stage"],
        stage_changed_at=row["stage_changed_at"].isoformat() if row["stage_changed_at"] else None,
        thread_state=row["state"],
        bid_amount_paise=row["bid_amount_paise"],
        bid_type=row["bid_type"],
        timeline_days=row["timeline_days"],
        milestones=[Milestone(**m) for m in _json(row["milestones"], [])],
        screening_answers=[
            ScreeningAnswerOut(question_id=a["question_id"], question=questions.get(a["question_id"]), answer=a["answer"])
            for a in _json(row["screening_answers"], [])
        ],
        message_preview=(first_message[:200] if first_message else None),
        created_at=row["created_at"].isoformat(),
        match_score=_match_score(signals),
        match_signals=keys,
        match_reasons=reasons[:3],
        match_risks=risks,
        skills_match=skills,
        missing_skills=[SkillRef(slug=c, label=label) for c, label in zip([c for c in required if c not in have], skills.missing_skills)],
        matched_capability_labels=skills.matched_skills,
        missing_capability_labels=skills.missing_skills,
    )


async def _with_contacts(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, opp: asyncpg.Record, row: asyncpg.Record) -> ApplicantOut:
    out = _to_applicant(opp, row, row["first_message"], lang)
    if row["stage"] == "shortlisted":
        out.contact_actions = await shortlist_contact_actions(conn, ctx, lang, row, opp["title"])
    elif row["stage"] == "hired" and row["state"] in ("in_progress", "resolved"):
        actions = await contact_svc.contact_actions_for_enquiry(conn, ctx, lang, str(row["id"]))
        out.contact_actions = [a.model_dump() for a in actions.contact_actions]
    out.contact_revealed = bool(out.contact_actions)
    return out


_APPLICANT_ROWS = """
    SELECT e.*,
           (SELECT m.body FROM vyapar_enquiries.enquiry_messages m
             WHERE m.enquiry_id = e.id ORDER BY m.created_at LIMIT 1) AS first_message
      FROM vyapar_enquiries.enquiries e
     WHERE e.opportunity_id = $1 AND e.provider_id = $2
       AND e.delivered AND e.state <> 'withdrawn'
"""


async def list_opportunity_applicants(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    opportunity_id: str,
    stage: Stage | None = None,
    sort: Literal["newest", "match"] = "newest",
    limit: int = DEFAULT_LIMIT,
    cursor: str | None = None,
) -> ApplicantPage:
    opp = await _own_opportunity(conn, ctx, lang, opportunity_id)
    rows = await conn.fetch(_APPLICANT_ROWS + " ORDER BY e.created_at DESC, e.id", opp["id"], ctx.member_id)
    counts = {s: 0 for s in STAGES}
    for r in rows:
        counts[r["stage"]] = counts.get(r["stage"], 0) + 1
    items = [_to_applicant(opp, r, r["first_message"], lang) for r in rows if stage is None or r["stage"] == stage]
    if sort == "match":
        items.sort(key=lambda a: (-a.match_score, a.created_at), reverse=False)
    data = decode_cursor(cursor, lang) or {}
    offset = data.get("o", 0)
    if not isinstance(offset, int) or offset < 0:
        raise ApiError(422, "common.error.invalidCursor", lang)
    window = items[offset:offset + limit]
    rows_by_id = {str(r["id"]): r for r in rows}
    window = [await _with_contacts(conn, ctx, lang, opp, rows_by_id[a.enquiry_id]) for a in window]
    more = offset + limit < len(items)
    return ApplicantPage(
        items=window, next_cursor=encode_cursor({"o": offset + limit}) if more else None,
        total=len(items), stage_counts=counts,
    )


async def compare_applicants(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    opportunity_id: str,
    ids: list[str],
) -> CompareOut:
    opp = await _own_opportunity(conn, ctx, lang, opportunity_id)
    wanted: list[str] = []
    for i in ids:
        if i and i not in wanted:
            wanted.append(i)
    if not 2 <= len(wanted) <= MAX_COMPARE:
        raise ApiError(422, "enquiries.error.compareCount", lang, max=MAX_COMPARE)
    try:
        rows = await conn.fetch(_APPLICANT_ROWS + " AND e.id = ANY($3::uuid[])", opp["id"], ctx.member_id, wanted)
    except asyncpg.DataError:
        rows = []
    by_id = {str(r["id"]): r for r in rows}
    missing = [i for i in wanted if i not in by_id]
    if missing:
        raise ApiError(404, "enquiries.error.applicantNotFound", lang, extra={"enquiry_ids": missing})
    required = list(opp["required_capabilities"] or [])
    return CompareOut(
        opportunity_id=str(opp["id"]), opportunity_title=opp["title"],
        required_capabilities=required, required_capability_labels=labels_for(required, lang),
        items=[await _with_contacts(conn, ctx, lang, opp, by_id[i]) for i in wanted],
    )


async def set_applicant_stage(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    opportunity_id: str,
    enquiry_id: str,
    body: StageIn,
) -> ApplicantOut:
    opp = await _own_opportunity(conn, ctx, lang, opportunity_id)
    try:
        row = await conn.fetchrow(_APPLICANT_ROWS + " AND e.id = $3::uuid", opp["id"], ctx.member_id, enquiry_id)
    except asyncpg.DataError:
        row = None
    if row is None:
        raise ApiError(404, "enquiries.error.applicantNotFound", lang)
    target = body.stage
    if row["stage"] == target:
        return await _with_contacts(conn, ctx, lang, opp, row)  # idempotent repeat
    if row["stage"] in FINAL_STAGES:
        raise ApiError(409, "enquiries.error.stageFinal", lang, extra={"stage": row["stage"]})

    if target == "hired":
        # The existing accept path: provider-only, open/awaiting -> in_progress,
        # after which contact disclosure follows its one rule.
        if row["state"] in ("open", "awaiting_response"):
            await enquiries_svc.accept_enquiry(conn, ctx, lang, enquiry_id=str(row["id"]))
        elif row["state"] != "in_progress":
            raise ApiError(400, "enquiries.error.applicantNotAvailable", lang)
    if target == "declined" and row["state"] in ("open", "awaiting_response"):
        # Nothing to review: the poster never engaged. Closing the thread is
        # what frees the applicant's one-open-enquiry slot everywhere else.
        await conn.execute(
            """UPDATE vyapar_enquiries.enquiries SET state = 'closed', state_reason = 'declined',
                 last_activity_at = now(), updated_at = now() WHERE id = $1""",
            row["id"],
        )

    await conn.execute(
        "UPDATE vyapar_enquiries.enquiries SET stage = $2, stage_changed_at = now(), updated_at = now() WHERE id = $1",
        row["id"], target,
    )
    # [critique L11] shortlisting lets the poster call the applicant; leaving
    # the shortlist for declined or new hides the number again. Both are
    # audited (the grant and the revoke); each tap is a contact_attempts row.
    if target == "shortlisted" and row["state"] in ("open", "awaiting_response"):
        await audit(conn, actor_id=ctx.member_id, action="applicant_contact_revealed", object_kind="enquiry",
                    object_id=str(row["id"]), reason_code="shortlisted",
                    details={"opportunity_id": str(opp["id"]), "applicant_id": row["sender_id"]})
        poster = await conn.fetchval("SELECT display_name FROM vyapar_identity.public_names($1::text[])", [ctx.member_id])
        await notify_interaction_party(
            conn, interaction_kind="enquiry", interaction_id=row["id"], recipient=row["sender_id"],
            template="applicantShortlisted", link=f"/enquiries/{row['id']}", idempotency_key=f"applicant_shortlisted:{row['id']}",
            params={"title": opp["title"], "poster": poster or ""},
        )
    if row["stage"] == "shortlisted" and target in ("declined", "new"):
        await audit(conn, actor_id=ctx.member_id, action="applicant_contact_hidden", object_kind="enquiry",
                    object_id=str(row["id"]), reason_code=target,
                    details={"opportunity_id": str(opp["id"]), "applicant_id": row["sender_id"]})
    if target in FINAL_STAGES:
        template = "applicantHired" if target == "hired" else "applicantDeclined"
        await notify_interaction_party(
            conn, interaction_kind="enquiry", interaction_id=row["id"], recipient=row["sender_id"],
            template=template, link=f"/enquiries/{row['id']}", idempotency_key=f"applicant_{target}:{row['id']}",
            params={"title": opp["title"]},
        )
    fresh = await conn.fetchrow(_APPLICANT_ROWS + " AND e.id = $3::uuid", opp["id"], ctx.member_id, enquiry_id)
    return await _with_contacts(conn, ctx, lang, opp, fresh)


async def record_applicant_contact_attempt(
    conn: asyncpg.Connection,
    ctx: AuthzContext,
    lang: str,
    opportunity_id: str,
    enquiry_id: str,
    body: contact_svc.ContactAttemptIn,
) -> ApplicantOut:
    """[critique L11] The poster tapped Call / WhatsApp on a shortlisted (or
    hired) applicant: recorded in contact_attempts, visible to both sides in
    the thread. Refused when that channel is not offered right now."""
    opp = await _own_opportunity(conn, ctx, lang, opportunity_id)
    try:
        row = await conn.fetchrow(_APPLICANT_ROWS + " AND e.id = $3::uuid", opp["id"], ctx.member_id, enquiry_id)
    except asyncpg.DataError:
        row = None
    if row is None:
        raise ApiError(404, "enquiries.error.applicantNotFound", lang)
    current = await _with_contacts(conn, ctx, lang, opp, row)
    if not current.contact_revealed:
        raise ApiError(400, "contact.error.notRevealed", lang)
    if not any(a["channel"] == body.channel and a.get("href") for a in current.contact_actions):
        raise ApiError(400, "contact.error.channelOff", lang)
    await conn.execute(
        """INSERT INTO vyapar_enquiries.contact_attempts (enquiry_id, opportunity_id, caller_id, callee_id, channel)
           VALUES ($1, $2, $3, $4, $5)""",
        row["id"], opp["id"], ctx.member_id, row["sender_id"], body.channel,
    )
    return current

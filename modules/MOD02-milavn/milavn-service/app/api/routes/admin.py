"""Moderation queue — FR065 via the shared Admin & Governance Console contract (TR-PLAT-01, TR43).

Milavn ships only its manifest and the list/detail/action endpoints; the
console shell renders them. Until the platform console exists, the web
app's /admin/moderation route renders these same endpoints with the same
shapes, so nothing here is Milavn-specific UI logic.

[047] The queue shows ONE item per reported thing (with how many people
reported it), acting on it settles every open report about that thing, and
all human text follows the moderator's language (Accept-Language en/hi/te/mr/kn).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.api.deps import DbSession, Moderator
from app.components.identity_bridge import interface as identity
from app.components.safety import interface as safety
from app.i18n import resolve_language, translate

router = APIRouter(prefix="/milavn/admin", tags=["admin"])

MANY_BLOCKS = 3  # blocked by this many people is worth a moderator's glance


class ActionRequest(BaseModel):
    notes: str | None = None
    # [045] Optional machine-readable why from the shared console (e.g. 'spam.repeat'); stored with the action.
    reason_code: str | None = Field(default=None, max_length=64)


def _lang(request: Request) -> str:
    return resolve_language(request.headers.get("x-milavn-language") or request.headers.get("accept-language"))


def _day(dt: datetime, lang: str) -> str:
    """A date for people: '13 Sep 2026', month names localised."""
    months = translate("admin.months", lang).split(",")
    return f"{dt.day} {months[dt.month - 1]} {dt.year}"


def _reason(reason: str, lang: str) -> str:
    return translate(f"admin.reason.{reason}", lang)


def _summary(reason: str, title: str | None, reporters: int, lang: str) -> str:
    out = translate("admin.summary", lang, reason=_reason(reason, lang), title=title or translate("admin.untitled", lang))
    if reporters > 1:
        out += " · " + translate("admin.summaryMany", lang, n=reporters)
    return out


@router.get("/manifest")
async def manifest(request: Request) -> dict:
    """[TR-PLAT-01 §1] The AdminViewDescriptor this module registers with the console."""
    return {**safety.ADMIN_VIEW_DESCRIPTOR, "title": translate("admin.manifestTitle", _lang(request))}


def _queue_item(g: safety.ReportGroup, subject_title: str | None, lang: str) -> dict:
    """[TR-PLAT-01 §2] AdminQueueItem shape, one per reported thing (047). item_id is the earliest
    report. `summary_text` names the thing for a person; the machine fields sit beside it."""
    r = g.lead
    reason = g.lead_reason
    return {
        "item_id": str(r.id),
        "module_id": "milavn",
        "item_type": f"report.{r.subject_type}",
        "submitted_at": r.created_at.isoformat(),
        "priority": "high" if g.is_safety else "normal",
        "status": r.status,
        "reason": reason,
        "reasons": g.reasons,
        "reporter_count": g.reporter_count,
        "report_count": g.report_count,
        "subject_type": r.subject_type,
        "subject_title": subject_title,
        # [045] When a human should have looked at it: 24 h for safety reports, 72 h otherwise.
        "due_at": g.due_at.isoformat(),
        "summary_text": _summary(reason, subject_title, g.reporter_count, lang),
        "deep_link": f"/admin/moderation/{r.id}",
    }


async def _subject_titles(session: DbSession, reports: list[safety.Report]) -> dict[UUID, str | None]:
    from app.components.activity import interface as activity

    out: dict[UUID, str | None] = {}
    for r in reports:
        if r.subject_id in out:
            continue
        if r.subject_type in ("occurrence", "activity"):
            try:
                out[r.subject_id] = (await activity.get(session, occurrence_id=r.subject_id)).title
            except activity.OccurrenceNotFound:
                # A members-only activity the moderator's RLS cannot read is still named (045).
                out[r.subject_id] = await safety.subject_title(session, subject_type=r.subject_type, subject_id=r.subject_id)
        elif r.subject_type == "user":
            out[r.subject_id] = (await identity.display_names_for([r.subject_id]))[r.subject_id].display_name
        else:
            # [045] 'content' (a circle, a circle post, an activity) and 'organization'.
            out[r.subject_id] = await safety.subject_title(session, subject_type=r.subject_type, subject_id=r.subject_id)
    return out


async def _group_for(session: DbSession, r: safety.Report) -> safety.ReportGroup:
    """Every report in the same queue item as `r` (same thing, same status)."""
    same = [x for x in await safety.queue(session, status=r.status) if x.subject_type == r.subject_type and x.subject_id == r.subject_id]
    if not any(x.id == r.id for x in same):
        same.append(r)
    return safety.group_reports(same)[0]


@router.get("/moderation")
async def list_queue(request: Request, session: DbSession, moderator: Moderator, status: str | None = None) -> list[dict]:
    reports = await safety.queue(session, status=status)
    titles = await _subject_titles(session, reports)
    lang = _lang(request)
    return [_queue_item(g, titles.get(g.lead.subject_id), lang) for g in safety.group_reports(reports)]


@router.get("/moderation/{item_id}")
async def detail(item_id: UUID, request: Request, session: DbSession, moderator: Moderator) -> dict:
    try:
        r = await safety.get_report(session, report_id=item_id)
    except safety.ReportNotFound as exc:
        raise HTTPException(status_code=404) from exc
    lang = _lang(request)
    g = await _group_for(session, r)
    reporter = (await identity.display_names_for([r.reporter_member_id]))[r.reporter_member_id]
    actions = await safety.actions_for(session, report_id=item_id)
    names = await identity.display_names_for([a["moderator_member_id"] for a in actions])
    subject: dict = {"type": r.subject_type, "id": str(r.subject_id)}
    if r.subject_type in ("occurrence", "activity"):
        from app.components.activity import interface as activity

        try:
            occ = await activity.get(session, occurrence_id=r.subject_id)
            subject.update(
                {
                    "title": occ.title,
                    "slug": occ.canonical_url_slug,
                    "organizer": (await identity.display_names_for([occ.creator_member_id]))[occ.creator_member_id].display_name,
                }
            )
        except activity.OccurrenceNotFound:
            pass
    elif r.subject_type == "user":
        subject["display_name"] = (await identity.display_names_for([r.subject_id]))[r.subject_id].display_name
    title = subject.get("title") or subject.get("display_name") or (await _subject_titles(session, [r])).get(r.subject_id)
    reporters = await identity.display_names_for(list({x.reporter_member_id for x in g.reports}))
    t = lambda k, **kw: translate(k, lang, **kw)  # noqa: E731
    fields = [
        {"label": t("admin.field.subject"), "value": title or t("admin.untitled")},
        {"label": t("admin.field.reason"), "value": ", ".join(_reason(x, lang) for x in g.reasons)},
        {"label": t("admin.field.reporters"), "value": ", ".join(sorted(n.display_name for n in reporters.values()))},
        {"label": t("admin.field.reports"), "value": str(g.report_count)},
        {"label": t("admin.field.status"), "value": t(f"admin.status.{r.status}")},
        {"label": t("admin.field.firstReported"), "value": _day(g.lead.created_at, lang)},
    ]
    if subject.get("organizer"):
        fields.append({"label": t("admin.field.organizer"), "value": subject["organizer"]})
    said = [x.description for x in g.reports if x.description]
    if said:
        fields.append({"label": t("admin.field.description"), "value": " / ".join(said)})
    return {
        "item_id": str(r.id),
        "case_detail": {
            "reporter": {"member_id": str(r.reporter_member_id), "display_name": reporter.display_name},  # moderator-only (UX20)
            "subject": subject,
            "reason": r.reason_category,
            "description": r.description,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
            "summary_text": _summary(g.lead_reason, title, g.reporter_count, lang),
            "reasons": g.reasons,
            "reporter_count": g.reporter_count,
            "report_count": g.report_count,
            "due_at": g.due_at.isoformat(),
            "fields": fields,
            "history": [
                {
                    "action": a["action_type"],
                    "by": names[a["moderator_member_id"]].display_name,
                    "notes": a["notes"],
                    "reason_code": a["reason_code"],
                    "at": a["created_at"].isoformat(),
                }
                for a in actions
            ],
        },
        "available_actions": [] if r.status in ("dismissed", "actioned") else list(safety.ACTIONS),
    }


@router.post("/moderation/{item_id}/actions/{action_id}")
async def act(item_id: UUID, action_id: str, body: ActionRequest, request: Request, session: DbSession, moderator: Moderator) -> dict:
    """[TR-PLAT-01 §3/§4] Human decision, enforced by this module's own chokepoint and audited from here.
    [047] safety.act settles every open report about the same thing."""
    try:
        r = await safety.act(
            session, report_id=item_id, moderator_member_id=moderator.member_id, action=action_id, notes=body.notes, reason_code=body.reason_code
        )
    except safety.ReportNotFound as exc:
        raise HTTPException(status_code=404) from exc
    except safety.InvalidReport as exc:
        raise HTTPException(status_code=422, detail={"fields": exc.fields}) from exc
    g = await _group_for(session, r)
    return _queue_item(g, (await _subject_titles(session, [r])).get(r.subject_id), _lang(request))


@router.get("/members/{member_id}/summary")
async def member_summary(member_id: UUID, request: Request, session: DbSession, moderator: Moderator) -> dict:
    """[TR-PLAT-01, shared ForKhatri admin console] What Milavn knows about one person, for the
    console's member page. Milavn has no paid tiers, so `plan` is always null. Labels follow the
    moderator's language (047). 404 when the person has never opened Milavn (no Milavn profile)."""
    from app.components.trust import interface as trust

    s = await safety.member_summary(session, member_id=member_id)
    if s is None:
        raise HTTPException(status_code=404)
    lang = _lang(request)
    t = lambda k, **kw: translate(k, lang, **kw)  # noqa: E731
    badge = await trust.trust_for(session, subject_type="organizer", subject_id=member_id)
    labels = trust.label_text(await trust.reputation_labels(session, member_id=member_id))
    organizes = int(s["organizes_count"])
    names = list(s.get("organizes_names") or [])
    blocks = int(s["blocks_against"])
    since = _day(datetime.fromisoformat(str(s["member_since"])), lang) if s.get("member_since") else ""
    facts = [
        {"label": t("admin.fact.reports"), "value": t("admin.fact.reportsValue", total=s["reports_total"], open=s["reports_open"])},
        {"label": t("admin.fact.blockedBy"), "value": t("admin.fact.person" if blocks == 1 else "admin.fact.people", n=blocks)},
        {"label": t("admin.fact.organises"), "value": f"{organizes}" + (f" — {', '.join(names)}" + (" …" if organizes > len(names) else "") if names else "")},
        {"label": t("admin.fact.memberOf"), "value": str(s["member_of_count"])},
        {"label": t("admin.fact.trust"), "value": badge.label},
        {"label": t("admin.fact.reputation"), "value": ", ".join(labels) if labels else t("admin.fact.noLabels")},
        {"label": t("admin.fact.since"), "value": since},
    ]
    flags = []
    if int(s["reports_open"]) > 0:
        flags.append("open_reports")
    if s.get("restricted"):
        flags.append("restricted")
    if blocks >= MANY_BLOCKS:
        flags.append("many_blocks")
    return {"plan": None, "facts": facts, "flags": flags, "deep_link": None}

"""Moderation queue — FR065 via the shared Admin & Governance Console contract (TR-PLAT-01, TR43).

Milavn ships only its manifest and the list/detail/action endpoints; the
console shell renders them. Until the platform console exists, the web
app's /admin/moderation route renders these same endpoints with the same
shapes, so nothing here is Milavn-specific UI logic.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import DbSession, Moderator
from app.components.identity_bridge import interface as identity
from app.components.safety import interface as safety

router = APIRouter(prefix="/milavn/admin", tags=["admin"])


class ActionRequest(BaseModel):
    notes: str | None = None
    # [045] Optional machine-readable why from the shared console (e.g. 'spam.repeat'); stored with the action.
    reason_code: str | None = Field(default=None, max_length=64)


@router.get("/manifest")
async def manifest() -> dict:
    """[TR-PLAT-01 §1] The AdminViewDescriptor this module registers with the console."""
    return safety.ADMIN_VIEW_DESCRIPTOR


def _queue_item(r: safety.Report, subject_title: str | None) -> dict:
    """[TR-PLAT-01 §2] AdminQueueItem shape. `summary_text` is for a person, so it names the thing
    reported (activity title / member name), never a raw id; the machine fields sit beside it."""
    return {
        "item_id": str(r.id),
        "module_id": "milavn",
        "item_type": f"report.{r.subject_type}",
        "submitted_at": r.created_at.isoformat(),
        "priority": "high" if r.reason_category in ("unsafe", "harassment") else "normal",
        "status": r.status,
        "reason": r.reason_category,
        "subject_type": r.subject_type,
        "subject_title": subject_title,
        # [045] When a human should have looked at it: 24 h for safety reports, 72 h otherwise.
        "due_at": safety.due_at(r).isoformat(),
        "summary_text": f"{r.reason_category} · {r.subject_type} · {subject_title or str(r.subject_id)[:8]}",
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


@router.get("/moderation")
async def list_queue(session: DbSession, moderator: Moderator, status: str | None = None) -> list[dict]:
    reports = await safety.queue(session, status=status)
    titles = await _subject_titles(session, reports)
    return [_queue_item(r, titles.get(r.subject_id)) for r in reports]


@router.get("/moderation/{item_id}")
async def detail(item_id: UUID, session: DbSession, moderator: Moderator) -> dict:
    try:
        r = await safety.get_report(session, report_id=item_id)
    except safety.ReportNotFound as exc:
        raise HTTPException(status_code=404) from exc
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
    return {
        "item_id": str(r.id),
        "case_detail": {
            "reporter": {"member_id": str(r.reporter_member_id), "display_name": reporter.display_name},  # moderator-only (UX20)
            "subject": subject,
            "reason": r.reason_category,
            "description": r.description,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
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
async def act(item_id: UUID, action_id: str, body: ActionRequest, session: DbSession, moderator: Moderator) -> dict:
    """[TR-PLAT-01 §3/§4] Human decision, enforced by this module's own chokepoint and audited from here."""
    try:
        r = await safety.act(
            session, report_id=item_id, moderator_member_id=moderator.member_id, action=action_id, notes=body.notes, reason_code=body.reason_code
        )
    except safety.ReportNotFound as exc:
        raise HTTPException(status_code=404) from exc
    except safety.InvalidReport as exc:
        raise HTTPException(status_code=422, detail={"fields": exc.fields}) from exc
    return _queue_item(r, (await _subject_titles(session, [r])).get(r.subject_id))


@router.get("/members/{member_id}/summary")
async def member_summary(member_id: UUID, session: DbSession, moderator: Moderator) -> dict:
    """[TR-PLAT-01, shared ForKhatri admin console] What Milavn knows about one person, for the
    console's member page. Milavn has no paid tiers, so `plan` is always null. Plain English labels:
    this is an operator API and the other admin responses are not translated either.
    404 when the person has never opened Milavn (no Milavn profile)."""
    from app.components.trust import interface as trust

    s = await safety.member_summary(session, member_id=member_id)
    if s is None:
        raise HTTPException(status_code=404)
    badge = await trust.trust_for(session, subject_type="organizer", subject_id=member_id)
    labels = trust.label_text(await trust.reputation_labels(session, member_id=member_id))
    organizes = int(s["organizes_count"])
    names = list(s.get("organizes_names") or [])
    since = str(s["member_since"])[:10]
    facts = [
        {"label": "Reports about this person", "value": f"{s['reports_total']} ({s['reports_open']} open)"},
        {"label": "Blocked by", "value": f"{s['blocks_against']} {'person' if s['blocks_against'] == 1 else 'people'}"},
        {"label": "Circles they organise", "value": f"{organizes}" + (f" — {', '.join(names)}" + (" …" if organizes > len(names) else "") if names else "")},
        {"label": "Circles they are in", "value": str(s["member_of_count"])},
        {"label": "Trust", "value": badge.label},
        {"label": "Reputation", "value": ", ".join(labels) if labels else "No labels yet"},
        {"label": "In Milavn since", "value": since},
    ]
    flags = []
    if int(s["reports_open"]) > 0:
        flags.append("open_reports")
    if s.get("restricted"):
        flags.append("restricted")
    if int(s["blocks_against"]) >= MANY_BLOCKS:
        flags.append("many_blocks")
    return {"plan": None, "facts": facts, "flags": flags, "deep_link": None}


MANY_BLOCKS = 3  # blocked by this many people is worth a moderator's glance

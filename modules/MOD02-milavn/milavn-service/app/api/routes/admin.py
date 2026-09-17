"""Moderation queue — FR065 via the shared Admin & Governance Console contract (TR-PLAT-01, TR43).

Milavn ships only its manifest and the list/detail/action endpoints; the
console shell renders them. Until the platform console exists, the web
app's /admin/moderation route renders these same endpoints with the same
shapes, so nothing here is Milavn-specific UI logic.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.deps import DbSession, Moderator
from app.components.identity_bridge import interface as identity
from app.components.safety import interface as safety

router = APIRouter(prefix="/milavn/admin", tags=["admin"])


class ActionRequest(BaseModel):
    notes: str | None = None


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
        "summary_text": f"{r.reason_category} · {r.subject_type} · {subject_title or str(r.subject_id)[:8]}",
        "deep_link": f"/admin/moderation/{r.id}",
    }


async def _subject_titles(session: DbSession, reports: list[safety.Report]) -> dict[UUID, str | None]:
    from app.components.activity import interface as activity

    out: dict[UUID, str | None] = {}
    for r in reports:
        if r.subject_type in ("occurrence", "activity"):
            try:
                out[r.subject_id] = (await activity.get(session, occurrence_id=r.subject_id)).title
            except activity.OccurrenceNotFound:
                out[r.subject_id] = None
        elif r.subject_type == "user":
            out[r.subject_id] = (await identity.display_names_for([r.subject_id]))[r.subject_id].display_name
        else:
            out[r.subject_id] = None
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
                {"action": a["action_type"], "by": names[a["moderator_member_id"]].display_name, "notes": a["notes"], "at": a["created_at"].isoformat()} for a in actions
            ],
        },
        "available_actions": [] if r.status in ("dismissed", "actioned") else list(safety.ACTIONS),
    }


@router.post("/moderation/{item_id}/actions/{action_id}")
async def act(item_id: UUID, action_id: str, body: ActionRequest, session: DbSession, moderator: Moderator) -> dict:
    """[TR-PLAT-01 §3/§4] Human decision, enforced by this module's own chokepoint and audited from here."""
    try:
        r = await safety.act(session, report_id=item_id, moderator_member_id=moderator.member_id, action=action_id, notes=body.notes)
    except safety.ReportNotFound as exc:
        raise HTTPException(status_code=404) from exc
    except safety.InvalidReport as exc:
        raise HTTPException(status_code=422, detail={"fields": exc.fields}) from exc
    return _queue_item(r, (await _subject_titles(session, [r])).get(r.subject_id))

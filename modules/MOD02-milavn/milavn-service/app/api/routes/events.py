"""Event programme endpoints: agenda, speakers, expo stalls, tournament teams, online join, recording / notes
(Phase 2, Step 5 of PLAN-places-events-groups.md).

No in-app video (owner decision 2026-10-05): online sessions use the organizer's own meeting link. Every rule is in
the database (migration 054) and repeated here; the web screens only present what these endpoints decided.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import AppSettings, CurrentMember, DbSession, Locale
from app.components.activity import events
from app.components.activity import interface as activity
from app.components.authorization import interface as authz
from app.components.identity_bridge import interface as identity
from app.components.trust import interface as trust
from app.i18n import translate

router = APIRouter(prefix="/occurrences/{occurrence_id}", tags=["events"])


class SpeakerBody(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    bio: str | None = Field(default=None, max_length=300)
    member_id: UUID | None = None


class SessionBody(BaseModel):
    starts_at: datetime
    ends_at: datetime | None = None
    title: str = Field(min_length=1, max_length=140)
    details: str | None = Field(default=None, max_length=400)
    speaker_ids: list[UUID] = Field(default_factory=list, max_length=8)


class StallBody(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    stall_number: str | None = Field(default=None, max_length=20)
    description: str | None = Field(default=None, max_length=300)


class TeamBody(BaseModel):
    name: str = Field(min_length=2, max_length=60)


class FollowupBody(BaseModel):
    recording_url: str | None = Field(default=None, max_length=500)
    notes_url: str | None = Field(default=None, max_length=500)


_STATUS = {"not_allowed": 403, "not_found": 404, "invalid": 422, "session_times": 422, "session_outside": 422, "not_member": 422}


def _refused(exc: events.Refused, lang: str, *, team: bool = False) -> HTTPException:
    if exc.reason == "not_allowed":
        return HTTPException(status_code=403, detail=translate("evt.err.team_not_allowed" if team else "occurrence.notOrganizer", lang))
    if exc.reason == "not_found":
        return HTTPException(status_code=404, detail=translate("evt.err.not_found", lang))
    return HTTPException(status_code=_STATUS.get(exc.reason, 409), detail=translate(f"evt.err.{exc.reason}", lang))


async def _event(session: DbSession, occurrence_id: UUID, lang: str) -> activity.Occurrence:
    try:
        return await activity.get(session, occurrence_id=occurrence_id)
    except activity.OccurrenceNotFound as exc:
        raise HTTPException(status_code=404, detail=translate("occurrence.notFound", lang)) from exc


async def _require_organizer(session: DbSession, occurrence_id: UUID, member: CurrentMember, lang: str) -> None:
    try:
        await authz.require_organizer(session, occurrence_id=occurrence_id, member_id=member.member_id)
    except authz.NotFound as exc:
        raise HTTPException(status_code=404, detail=translate("occurrence.notFound", lang)) from exc
    except authz.NotAuthorized as exc:
        raise HTTPException(status_code=403, detail=translate("occurrence.notOrganizer", lang)) from exc


# --- read ---------------------------------------------------------------------------------------------------------------


@router.get("/program")
async def program(occurrence_id: UUID, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """Agenda (sessions with their speakers), speaker cards, expo stalls, tournament teams and the recording / notes
    links. Agenda, speakers and stalls are as public as the event; who is in which team and the follow-up links are
    for confirmed attendees and organizers only."""
    occ = await _event(session, occurrence_id, lang)
    spk = await events.speakers(session, occurrence_id)
    team_list, my_team = (await events.teams(session, occurrence_id=occurrence_id, viewer=member.member_id)) if occ.team_size_max else ([], None)
    ids = [s["member_id"] for s in spk if s["member_id"]] + [m for t in team_list for m in (t.member_ids or [])]
    names = await identity.display_names_for(ids) if ids else {}
    return {
        "event_format": occ.event_format,
        "speakers": [
            {
                "id": str(s["id"]),
                "name": s["name"],
                "bio": s["bio"],
                "member_id": str(s["member_id"]) if s["member_id"] else None,
                "avatar": names[s["member_id"]].avatar if s["member_id"] in names else None,
            }
            for s in spk
        ],
        "sessions": [
            {
                "id": str(x["id"]),
                "starts_at": x["starts_at"].isoformat(),
                "ends_at": x["ends_at"].isoformat() if x["ends_at"] else None,
                "title": x["title"],
                "details": x["details"],
                "speaker_ids": [str(i) for i in x["speaker_ids"]],
            }
            for x in await events.sessions(session, occurrence_id)
        ],
        "stalls": [
            {"id": str(s["id"]), "stall_number": s["stall_number"], "name": s["name"], "description": s["description"]} for s in await events.stalls(session, occurrence_id)
        ],
        "teams": {
            "team_size_max": occ.team_size_max,
            "my_team_id": str(my_team) if my_team else None,
            "list": [
                {
                    "id": str(t.id),
                    "name": t.name,
                    "size": t.size,
                    "full": t.size >= occ.team_size_max,
                    "captain_member_id": str(t.captain_member_id) if t.captain_member_id else None,
                    "members": [{"member_id": str(m), "display_name": names[m].display_name} for m in t.member_ids] if t.member_ids is not None else None,
                }
                for t in team_list
            ],
        }
        if occ.team_size_max
        else None,
        "followup": await events.followup(session, occurrence_id),
    }


# --- organizer: agenda, speakers, stalls, follow-up ------------------------------------------------------------------


@router.post("/speakers", status_code=201)
async def add_speaker(occurrence_id: UUID, body: SpeakerBody, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    await _require_organizer(session, occurrence_id, member, lang)
    try:
        await events.add_speaker(session, occurrence_id=occurrence_id, name=body.name, bio=body.bio, member_id=body.member_id)
    except events.Refused as exc:
        raise _refused(exc, lang) from exc
    return {"ok": True}


@router.delete("/speakers/{speaker_id}")
async def remove_speaker(occurrence_id: UUID, speaker_id: UUID, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    await _require_organizer(session, occurrence_id, member, lang)
    try:
        await events.remove_speaker(session, occurrence_id=occurrence_id, speaker_id=speaker_id)
    except events.Refused as exc:
        raise _refused(exc, lang) from exc
    return {"ok": True}


@router.post("/sessions", status_code=201)
async def add_session(occurrence_id: UUID, body: SessionBody, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    await _require_organizer(session, occurrence_id, member, lang)
    try:
        await events.add_session(
            session, occurrence_id=occurrence_id, starts_at=body.starts_at, ends_at=body.ends_at, title=body.title, details=body.details, speaker_ids=body.speaker_ids
        )
    except events.Refused as exc:
        raise _refused(exc, lang) from exc
    return {"ok": True}


@router.delete("/sessions/{session_id}")
async def remove_session(occurrence_id: UUID, session_id: UUID, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    await _require_organizer(session, occurrence_id, member, lang)
    try:
        await events.remove_session(session, occurrence_id=occurrence_id, session_id=session_id)
    except events.Refused as exc:
        raise _refused(exc, lang) from exc
    return {"ok": True}


@router.post("/stalls", status_code=201)
async def add_stall(occurrence_id: UUID, body: StallBody, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    await _require_organizer(session, occurrence_id, member, lang)
    try:
        await events.add_stall(session, occurrence_id=occurrence_id, stall_number=body.stall_number, name=body.name, description=body.description)
    except events.Refused as exc:
        raise _refused(exc, lang) from exc
    return {"ok": True}


@router.delete("/stalls/{stall_id}")
async def remove_stall(occurrence_id: UUID, stall_id: UUID, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    await _require_organizer(session, occurrence_id, member, lang)
    try:
        await events.remove_stall(session, occurrence_id=occurrence_id, stall_id=stall_id)
    except events.Refused as exc:
        raise _refused(exc, lang) from exc
    return {"ok": True}


@router.put("/followup")
async def put_followup(occurrence_id: UUID, body: FollowupBody, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """Recording / notes links after the event (from its start onwards), for the people who had a confirmed spot."""
    await _require_organizer(session, occurrence_id, member, lang)
    try:
        await events.set_followup(session, occurrence_id=occurrence_id, actor=member.member_id, recording_url=body.recording_url, notes_url=body.notes_url)
    except events.Refused as exc:
        raise _refused(exc, lang) from exc
    return {"ok": True}


# --- members: teams, online join ---------------------------------------------------------------------------------------


@router.post("/teams", status_code=201)
async def register_team(occurrence_id: UUID, body: TeamBody, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """A person with a confirmed spot registers a team and becomes its captain."""
    await _event(session, occurrence_id, lang)
    try:
        await events.register_team(session, occurrence_id=occurrence_id, actor=member.member_id, name=body.name)
    except events.Refused as exc:
        raise _refused(exc, lang, team=True) from exc
    return {"ok": True}


@router.post("/teams/{team_id}/join")
async def join_team(occurrence_id: UUID, team_id: UUID, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    try:
        await events.join_team(session, occurrence_id=occurrence_id, team_id=team_id, actor=member.member_id)
    except events.Refused as exc:
        raise _refused(exc, lang, team=True) from exc
    return {"ok": True}


@router.delete("/teams/{team_id}/members/{member_id}")
async def leave_or_remove(occurrence_id: UUID, team_id: UUID, member_id: UUID, session: DbSession, member: CurrentMember, lang: Locale) -> dict:
    """The member leaves, or their captain or an organizer takes them off the team."""
    try:
        await events.remove_from_team(session, occurrence_id=occurrence_id, team_id=team_id, actor=member.member_id, member_id=member_id)
    except events.Refused as exc:
        raise _refused(exc, lang, team=True) from exc
    return {"ok": True}


@router.post("/join-online")
async def join_online(occurrence_id: UUID, session: DbSession, member: CurrentMember, lang: Locale, settings: AppSettings) -> dict:
    """Tapping Join: a confirmed attendee inside the join window is marked checked in, and gets the link to open."""
    occ = await _event(session, occurrence_id, lang)
    try:
        result = await events.record_online_join(session, occurrence_id=occurrence_id, member_id=member.member_id, open_minutes=settings.online_join_open_minutes)
    except events.Refused as exc:
        code = {"not_found": 404, "not_allowed": 403, "not_confirmed": 403}.get(exc.reason, 409)
        raise HTTPException(status_code=code, detail=translate(f"evt.err.join_{exc.reason}", lang, minutes=settings.online_join_open_minutes)) from exc
    venue = await activity.get_venue(session, occurrence_id=occurrence_id, member_id=member.member_id)
    if not venue or not venue.get("join_link"):
        raise HTTPException(status_code=409, detail=translate("evt.err.no_link", lang))
    if result == "checked_in":
        await trust.record_signal(session, member_id=member.member_id, signal="attendance_reliable", occurrence_id=occ.id, weight=1.0)
    return {"status": "checked_in", "join_link": venue["join_link"], "provider": events.link_provider(venue["join_link"])}

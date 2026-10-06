"""Event programme: formats, agenda, speakers, expo stalls, tournament teams, online join, recording (Phase 2, Step 5).

# Owner decision 2026-10-05: no in-app video. An online session uses the organizer's own Google Meet / Zoom / Teams /
# YouTube link; this module only recognises which one it is, shows it to confirmed attendees close to the start, and
# marks attendance when they tap Join. Offline events get the exact venue pin (activity.interface.pin_venue).
# Every rule lives in the database (migration 054: RLS for agenda/speakers/stalls, definer functions for teams,
# follow-up and online join); this file translates their answers into Python results and exceptions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

# ---------------------------------------------------------------------------------------------------------------------
# Meeting link provider, recognised from the address only (nothing is fetched).
_PROVIDERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("google_meet", ("meet.google.com",)),
    ("zoom", ("zoom.us", "zoom.com", "zoomgov.com")),
    ("teams", ("teams.microsoft.com", "teams.live.com")),
    ("youtube", ("youtube.com", "youtu.be")),
)


def link_provider(url: str | None) -> str | None:
    """'google_meet' | 'zoom' | 'teams' | 'youtube' | 'other', or None without a link."""
    if not url:
        return None
    host = (urlparse(url.strip()).hostname or "").lower()
    for name, domains in _PROVIDERS:
        if any(host == d or host.endswith("." + d) for d in domains):
            return name
    return "other"


def event_end(time_start: datetime, time_end: datetime | None) -> datetime:
    """Same rule as the rest of the module: the end time, or three hours after the start when none was given."""
    return time_end or time_start + timedelta(hours=3)


def join_window(time_start: datetime, time_end: datetime | None, open_minutes: int, now: datetime | None = None) -> tuple[str, datetime]:
    """('later' | 'open' | 'ended', opens_at) for an online join link."""
    now = now or datetime.now(UTC)
    opens = time_start - timedelta(minutes=max(open_minutes, 0))
    if now < opens:
        return "later", opens
    if now > event_end(time_start, time_end):
        return "ended", opens
    return "open", opens


# ---------------------------------------------------------------------------------------------------------------------
class Refused(Exception):
    """A database rule said no; `reason` is the function's own answer ('not_allowed', 'team_full', ...)."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def _https(url: str | None) -> bool:
    u = (url or "").strip()
    return not u or (u.lower().startswith("https://") and " " not in u and len(u) <= 500)


# --- Speakers ---------------------------------------------------------------------------------------------------------
async def speakers(session: AsyncSession, occurrence_id: UUID) -> list[dict]:
    rows = (
        await session.execute(
            text("SELECT id, name, bio, member_id FROM milavn_activity.event_speaker WHERE occurrence_id = :o ORDER BY position, created_at"),
            {"o": str(occurrence_id)},
        )
    ).all()
    return [{"id": r[0], "name": r[1], "bio": r[2], "member_id": r[3]} for r in rows]


async def add_speaker(session: AsyncSession, *, occurrence_id: UUID, name: str, bio: str | None, member_id: UUID | None) -> None:
    if member_id is not None and not (await session.execute(text("SELECT milavn_activity.is_milavn_member(:m)"), {"m": str(member_id)})).scalar_one():
        raise Refused("not_member")
    n = (await session.execute(text("SELECT count(*) FROM milavn_activity.event_speaker WHERE occurrence_id = :o"), {"o": str(occurrence_id)})).scalar_one()
    if n >= 30:
        raise Refused("too_many")
    await _write(
        session,
        "INSERT INTO milavn_activity.event_speaker (occurrence_id, name, bio, member_id, position) VALUES (:o, :n, NULLIF(:b, ''), :m, :p)",
        {"o": str(occurrence_id), "n": name.strip(), "b": (bio or "").strip(), "m": str(member_id) if member_id else None, "p": n},
    )


async def remove_speaker(session: AsyncSession, *, occurrence_id: UUID, speaker_id: UUID) -> None:
    await _delete(session, "event_speaker", occurrence_id, speaker_id)


# --- Agenda -----------------------------------------------------------------------------------------------------------
async def sessions(session: AsyncSession, occurrence_id: UUID) -> list[dict]:
    rows = (
        await session.execute(
            text("SELECT id, starts_at, ends_at, title, details, speaker_ids FROM milavn_activity.event_session WHERE occurrence_id = :o ORDER BY starts_at, created_at"),
            {"o": str(occurrence_id)},
        )
    ).all()
    return [{"id": r[0], "starts_at": r[1], "ends_at": r[2], "title": r[3], "details": r[4], "speaker_ids": list(r[5] or [])} for r in rows]


async def add_session(
    session: AsyncSession, *, occurrence_id: UUID, starts_at: datetime, ends_at: datetime | None, title: str, details: str | None, speaker_ids: list[UUID]
) -> None:
    if ends_at is not None and ends_at <= starts_at:
        raise Refused("session_times")
    n = (await session.execute(text("SELECT count(*) FROM milavn_activity.event_session WHERE occurrence_id = :o"), {"o": str(occurrence_id)})).scalar_one()
    if n >= 80:
        raise Refused("too_many")
    await _write(
        session,
        "INSERT INTO milavn_activity.event_session (occurrence_id, starts_at, ends_at, title, details, speaker_ids) "
        "VALUES (:o, :s, :e, :t, NULLIF(:d, ''), CAST(:sp AS uuid[]))",
        {"o": str(occurrence_id), "s": starts_at, "e": ends_at, "t": title.strip(), "d": (details or "").strip(), "sp": [str(x) for x in dict.fromkeys(speaker_ids)]},
    )


async def remove_session(session: AsyncSession, *, occurrence_id: UUID, session_id: UUID) -> None:
    await _delete(session, "event_session", occurrence_id, session_id)


# --- Expo stalls ------------------------------------------------------------------------------------------------------
async def stalls(session: AsyncSession, occurrence_id: UUID) -> list[dict]:
    rows = (
        await session.execute(
            text("SELECT id, stall_number, name, description FROM milavn_activity.event_stall WHERE occurrence_id = :o ORDER BY created_at"),
            {"o": str(occurrence_id)},
        )
    ).all()
    return [{"id": r[0], "stall_number": r[1], "name": r[2], "description": r[3]} for r in rows]


async def add_stall(session: AsyncSession, *, occurrence_id: UUID, stall_number: str | None, name: str, description: str | None) -> None:
    n = (await session.execute(text("SELECT count(*) FROM milavn_activity.event_stall WHERE occurrence_id = :o"), {"o": str(occurrence_id)})).scalar_one()
    if n >= 300:
        raise Refused("too_many")
    await _write(
        session,
        "INSERT INTO milavn_activity.event_stall (occurrence_id, stall_number, name, description) VALUES (:o, NULLIF(:sn, ''), :n, NULLIF(:d, ''))",
        {"o": str(occurrence_id), "sn": (stall_number or "").strip(), "n": name.strip(), "d": (description or "").strip()},
    )


async def remove_stall(session: AsyncSession, *, occurrence_id: UUID, stall_id: UUID) -> None:
    await _delete(session, "event_stall", occurrence_id, stall_id)


async def _write(session: AsyncSession, sql: str, params: dict) -> None:
    """Organizer-only writes are decided by row-level security; a refused or invalid row comes back as Refused."""
    try:
        async with session.begin_nested():
            await session.execute(text(sql), params)
    except DBAPIError as exc:
        msg = str(exc.orig).lower()
        if "row-level security" in msg:
            raise Refused("not_allowed") from exc
        if "event_session_inside_event" in msg or "session outside the event" in msg:
            raise Refused("session_outside") from exc
        if "unique" in msg:
            raise Refused("duplicate") from exc
        raise Refused("invalid") from exc


async def _delete(session: AsyncSession, table: str, occurrence_id: UUID, row_id: UUID) -> None:
    res = await session.execute(
        text(f"DELETE FROM milavn_activity.{table} WHERE id = :id AND occurrence_id = :o"),  # noqa: S608 - table is one of three literals above
        {"id": str(row_id), "o": str(occurrence_id)},
    )
    if res.rowcount == 0:
        raise Refused("not_found")


# --- Tournament teams -------------------------------------------------------------------------------------------------
@dataclass(slots=True)
class Team:
    id: UUID
    name: str
    captain_member_id: UUID | None  # None when the viewer may not see who is in which team
    size: int
    member_ids: list[UUID] | None


async def teams(session: AsyncSession, *, occurrence_id: UUID, viewer: UUID) -> tuple[list[Team], UUID | None]:
    rows = (
        await session.execute(
            text("SELECT team_id, name, captain_member_id, size, member_ids FROM milavn_activity.teams_for(:o, :v)"), {"o": str(occurrence_id), "v": str(viewer)}
        )
    ).all()
    mine = (await session.execute(text("SELECT milavn_activity.my_team(:o, :v)"), {"o": str(occurrence_id), "v": str(viewer)})).scalar_one()
    return [Team(r[0], r[1], r[2], int(r[3]), list(r[4]) if r[4] is not None else None) for r in rows], mine


async def _answer(session: AsyncSession, sql: str, params: dict) -> None:
    res = (await session.execute(text(sql), params)).scalar_one()
    if res != "ok":
        raise Refused(res)


async def register_team(session: AsyncSession, *, occurrence_id: UUID, actor: UUID, name: str) -> None:
    await _answer(session, "SELECT milavn_activity.team_register(:o, :a, :n)", {"o": str(occurrence_id), "a": str(actor), "n": name})


async def join_team(session: AsyncSession, *, occurrence_id: UUID, team_id: UUID, actor: UUID) -> None:
    await _team_on_event(session, occurrence_id, team_id)
    await _answer(session, "SELECT milavn_activity.team_join(:t, :a)", {"t": str(team_id), "a": str(actor)})


async def remove_from_team(session: AsyncSession, *, occurrence_id: UUID, team_id: UUID, actor: UUID, member_id: UUID) -> None:
    await _team_on_event(session, occurrence_id, team_id)
    await _answer(session, "SELECT milavn_activity.team_remove(:t, :a, :m)", {"t": str(team_id), "a": str(actor), "m": str(member_id)})


async def _team_on_event(session: AsyncSession, occurrence_id: UUID, team_id: UUID) -> None:
    rows = (await session.execute(text("SELECT team_id FROM milavn_activity.teams_for(:o, milavn_activity.acting_member())"), {"o": str(occurrence_id)})).all()
    if team_id not in {r[0] for r in rows}:
        raise Refused("not_found")


# --- Online join and follow-up ----------------------------------------------------------------------------------------
async def record_online_join(session: AsyncSession, *, occurrence_id: UUID, member_id: UUID, open_minutes: int) -> str:
    """'checked_in' (first tap) | 'already'; anything else raises Refused with the database's reason."""
    res = (
        await session.execute(text("SELECT milavn_activity.record_online_join(:o, :m, :w)"), {"o": str(occurrence_id), "m": str(member_id), "w": int(open_minutes)})
    ).scalar_one()
    if res not in ("checked_in", "already"):
        raise Refused(res)
    return res


async def followup(session: AsyncSession, occurrence_id: UUID) -> dict | None:
    """Recording / notes links, readable only by organizers and confirmed attendees (row-level security)."""
    row = (
        await session.execute(
            text(
                "SELECT recording_url, notes_url FROM milavn_activity.occurrence_followup "
                "WHERE occurrence_id = :o AND milavn_activity.can_see_venue(occurrence_id, milavn_activity.acting_member())"
            ),
            {"o": str(occurrence_id)},
        )
    ).first()
    if row is None or not (row[0] or row[1]):
        return None
    return {"recording_url": row[0], "recording_provider": link_provider(row[0]), "notes_url": row[1]}


async def set_followup(session: AsyncSession, *, occurrence_id: UUID, actor: UUID, recording_url: str | None, notes_url: str | None) -> None:
    if not _https(recording_url) or not _https(notes_url):
        raise Refused("invalid")
    await _answer(
        session, "SELECT milavn_activity.set_event_followup(:o, :a, :r, :n)", {"o": str(occurrence_id), "a": str(actor), "r": recording_url or "", "n": notes_url or ""}
    )

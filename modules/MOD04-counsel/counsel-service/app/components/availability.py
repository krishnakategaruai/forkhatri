"""Slot engine. Weekly rules + date exceptions, in the provider's time zone,
minus existing live bookings (with the service's buffer), respecting the
service's minimum notice and maximum advance window. Slots start on a
15-minute grid. Returned in UTC; the client renders in the viewer's zone."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

GRID_MIN = 15


def _combine(d: date, t: time, tz: ZoneInfo) -> datetime:
    return datetime.combine(d, t, tzinfo=tz)


async def slots(conn, provider_id: UUID, service: dict, from_date: date, days: int, now: datetime | None = None) -> list[datetime]:
    now = now or datetime.now(timezone.utc)
    prov = await conn.fetchrow("SELECT timezone FROM provider WHERE member_id = $1", provider_id)
    tz = ZoneInfo(prov["timezone"] if prov else "Asia/Kolkata")
    rules = await conn.fetch("SELECT weekday, start_time, end_time, kind FROM availability_rule WHERE provider_id = $1", provider_id)
    exceptions = await conn.fetch(
        "SELECT on_date, start_time, end_time, available FROM availability_exception WHERE provider_id = $1 AND on_date BETWEEN $2 AND $3",
        provider_id, from_date, from_date + timedelta(days=days),
    )
    duration = timedelta(minutes=service["duration_min"])
    buffer = timedelta(minutes=service["buffer_min"])
    earliest = now + timedelta(hours=service["min_notice_hours"])
    latest = now + timedelta(days=service["max_advance_days"])
    busy = await conn.fetch(
        "SELECT starts_at, ends_at FROM booking WHERE provider_id = $1 AND status IN ('pending_payment','confirmed','in_progress') AND ends_at > $2",
        provider_id, now,
    )
    busy_ranges = [(b["starts_at"] - buffer, b["ends_at"] + buffer) for b in busy]

    # Windows are cut into 15-minute starts; fixed slots offer exactly one start.
    by_weekday: dict[int, list[tuple[time, time]]] = {}
    fixed_by_weekday: dict[int, list[time]] = {}
    for r in rules:
        if r["kind"] == "slot":
            fixed_by_weekday.setdefault(r["weekday"], []).append(r["start_time"])
        else:
            by_weekday.setdefault(r["weekday"], []).append((r["start_time"], r["end_time"]))
    by_date: dict[date, list] = {}
    for e in exceptions:
        by_date.setdefault(e["on_date"], []).append(e)

    out: list[datetime] = []
    # "Available now" (Practo/Astrotalk-style instant consults): the next 5-minute
    # mark is bookable without the usual notice while the consultant is online.
    avail_until = await conn.fetchval("SELECT available_until FROM provider WHERE member_id=$1", provider_id)
    if service.get("instant_allowed") and avail_until and avail_until > now:
        start = (now + timedelta(minutes=5 - now.minute % 5)).replace(second=0, microsecond=0)
        end = start + duration
        if end <= avail_until + timedelta(minutes=15) and not any(start < b_end and end > b_start for b_start, b_end in busy_ranges):
            out.append(start)
    for i in range(days):
        d = from_date + timedelta(days=i)
        windows = list(by_weekday.get(d.weekday(), []))
        fixed = list(fixed_by_weekday.get(d.weekday(), []))
        for e in by_date.get(d, []):
            if not e["available"]:
                if e["start_time"] is None:
                    windows, fixed = [], []   # whole day off
                else:
                    windows = _subtract(windows, (e["start_time"], e["end_time"]))
                    fixed = [f for f in fixed if not (e["start_time"] <= f < e["end_time"])]
            else:
                windows.append((e["start_time"], e["end_time"]))
        candidates: list[datetime] = [_combine(d, f, tz) for f in fixed]
        for start_t, end_t in windows:
            cursor = _combine(d, start_t, tz)
            if cursor.minute % GRID_MIN:
                cursor += timedelta(minutes=GRID_MIN - cursor.minute % GRID_MIN)
            cursor = cursor.replace(second=0, microsecond=0)
            end = _combine(d, end_t, tz)
            while cursor + duration <= end:
                candidates.append(cursor)
                cursor += timedelta(minutes=GRID_MIN)
        for c in candidates:
            s_utc = c.astimezone(timezone.utc)
            e_utc = s_utc + duration
            if earliest <= s_utc <= latest and not any(s_utc < b_end and e_utc > b_start for b_start, b_end in busy_ranges):
                out.append(s_utc)
    return sorted(set(out))


async def conflicts(conn, provider_id: UUID, starts_at: datetime, duration_min: int, buffer_min: int) -> bool:
    """True when a live booking (with buffer) overlaps the proposed time."""
    buffer = timedelta(minutes=buffer_min)
    ends_at = starts_at + timedelta(minutes=duration_min)
    return bool(await conn.fetchval(
        "SELECT 1 FROM booking WHERE provider_id=$1 AND status IN ('pending_payment','confirmed','in_progress') "
        "AND starts_at < $3 AND ends_at > $2", provider_id, starts_at - buffer, ends_at + buffer))


def _subtract(windows: list[tuple[time, time]], cut: tuple[time, time]) -> list[tuple[time, time]]:
    res = []
    for s, e in windows:
        if cut[1] <= s or cut[0] >= e:
            res.append((s, e))
            continue
        if s < cut[0]:
            res.append((s, cut[0]))
        if cut[1] < e:
            res.append((cut[1], e))
    return res


async def is_free(conn, provider_id: UUID, service: dict, starts_at: datetime) -> bool:
    day = starts_at.astimezone(ZoneInfo((await conn.fetchval("SELECT timezone FROM provider WHERE member_id=$1", provider_id)) or "Asia/Kolkata")).date()
    return any(abs((s - starts_at).total_seconds()) < 1 for s in await slots(conn, provider_id, service, day, 1))

# [IMP-B, 2026-09-28] Contact actions with poster control (FR02/FR24).
#
# What a person gets after an enquiry is accepted is not a bare phone
# number but two actions — Call and WhatsApp — shaped by what the OTHER
# person allowed: call hours and days, a daily call cap, WhatsApp on/off,
# calls on/off, and "only people whose skills match" (calls_from =
# matching_only). Preferences live on the member (defaults) and may be
# overridden per listing (NULL = inherit). Every tap on Call/WhatsApp is
# recorded as a contact attempt so the callee's daily cap is real and both
# sides can see "you called X on ...".
#
# Disclosure is unchanged (TR002/TR024): the number still comes only from
# `vyapar_listings.contacts_for_viewer(listing, true)`, and only once the
# enquiry is past acceptance (in_progress/resolved). Before that the
# response says `revealed: false` and carries no href at all.
#
# The clock is India Standard Time as a fixed offset from configuration
# (CONTACT_TIMEZONE_OFFSET_MINUTES), never the server's local zone.
# `matching_only` reuses the ranking module's capability signal
# (`_opportunity_signals().capability_fit`) so "matching" means exactly what
# the feed means by it — never a second definition.
# Traces to: FR02, FR22, FR24, TR002, TR024, SP024, FR19 (capability signal)
from __future__ import annotations

import json
import re
from datetime import datetime, time, timedelta, timezone
from typing import Literal
from urllib.parse import quote

import asyncpg
from pydantic import BaseModel, Field, field_validator

from app.config import get_settings
from app.errors import ApiError
from app.i18n import translate
from app.identity import AuthzContext
from app.ranking import RankingSignals
from app.services import hooks
from app.viewer_profile import viewer_capabilities

DAYS: tuple[str, ...] = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
REVEALED_STATES = ("in_progress", "resolved")
Channel = Literal["call", "whatsapp"]
CallsFrom = Literal["anyone", "matching_only"]
PREF_FIELDS = ("call_hours_start", "call_hours_end", "call_days", "max_calls_per_day", "calls_from", "whatsapp_ok", "call_ok")


# [IMP-B follow-up] Every time a person reads is India Standard Time
# (Asia/Kolkata = fixed +05:30, no daylight saving; the offset comes from
# CONTACT_TIMEZONE_OFFSET_MINUTES), with day and month names from the
# reader's language catalog, never the host's English locale, and an explicit
# zone label so the text can't be misread as UTC.
_WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def to_local(dt: datetime) -> datetime:
    if dt.tzinfo is None:  # a naive value is UTC by this service's convention, never the host clock
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_tz())


def format_local(dt: datetime, lang: str, *, weekday: bool = False, year: bool = True) -> str:
    local = to_local(dt)
    parts = []
    if weekday:
        parts.append(translate(f"contact.date.weekday.{_WEEKDAYS[local.weekday()]}", lang))
    parts.append(f"{local.day} {translate(f'contact.date.month.m{local.month}', lang)}" + (f" {local.year}" if year else ""))
    return translate("contact.date.pattern", lang, date=" ".join(parts), time=local.strftime("%H:%M"),
                     zone=translate("contact.date.zone", lang))


def _tz() -> timezone:
    return timezone(timedelta(minutes=get_settings().contact_timezone_offset_minutes))


def _tz_label() -> str:
    minutes = get_settings().contact_timezone_offset_minutes
    sign = "+" if minutes >= 0 else "-"
    minutes = abs(minutes)
    return f"UTC{sign}{minutes // 60:02d}:{minutes % 60:02d}"


# ---------------------------------------------------------------------------
# Preferences
# ---------------------------------------------------------------------------
class ContactPreferencesOut(BaseModel):
    call_hours_start: str | None = Field(default=None, description="HH:MM in the member's local time, null = any hour")
    call_hours_end: str | None = None
    call_days: list[str] = Field(default_factory=list, description="mon..sun; empty = every day")
    max_calls_per_day: int | None = Field(default=None, description="null = unlimited")
    calls_from: CallsFrom = "anyone"
    whatsapp_ok: bool = True
    call_ok: bool = True
    timezone: str = Field(default="UTC+05:30", description="Offset the hours are expressed in")


class ContactPreferencesPatch(BaseModel):
    call_hours_start: str | None = None
    call_hours_end: str | None = None
    call_days: list[str] | None = None
    max_calls_per_day: int | None = Field(default=None, ge=1, le=500)
    calls_from: CallsFrom | None = None
    whatsapp_ok: bool | None = None
    call_ok: bool | None = None
    # Fields to reset: on the member, back to the default (any hour, every
    # day, unlimited, anyone, both channels on); on a listing, back to
    # "inherit from the member".
    reset: list[str] = Field(default_factory=list)

    @field_validator("call_days")
    @classmethod
    def _days(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        cleaned = []
        for d in value:
            d = d.strip().lower()[:3]
            if d not in DAYS:
                raise ValueError("call_days must be mon..sun")
            if d not in cleaned:
                cleaned.append(d)
        return cleaned

    @field_validator("call_hours_start", "call_hours_end")
    @classmethod
    def _hhmm(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", value.strip()):
            raise ValueError("hours must be HH:MM")
        return value.strip()

    @field_validator("reset")
    @classmethod
    def _reset(cls, value: list[str]) -> list[str]:
        bad = [f for f in value if f not in PREF_FIELDS]
        if bad:
            raise ValueError(f"unknown preference fields: {', '.join(bad)}")
        return value


class ListingContactPreferencesOut(BaseModel):
    listing_id: str
    effective: ContactPreferencesOut
    # Which fields this listing sets itself (the rest inherit the member's).
    overrides: list[str]


def _fmt_time(value: time | None) -> str | None:
    return value.strftime("%H:%M") if value else None


def _parse_time(value: str | None) -> time | None:
    return time(int(value[:2]), int(value[3:5])) if value else None


def _prefs_out(row: dict) -> ContactPreferencesOut:
    return ContactPreferencesOut(
        call_hours_start=_fmt_time(row.get("call_hours_start")),
        call_hours_end=_fmt_time(row.get("call_hours_end")),
        call_days=list(row.get("call_days") or []),
        max_calls_per_day=row.get("max_calls_per_day"),
        calls_from=row.get("calls_from") or "anyone",
        whatsapp_ok=True if row.get("whatsapp_ok") is None else bool(row["whatsapp_ok"]),
        call_ok=True if row.get("call_ok") is None else bool(row["call_ok"]),
        timezone=_tz_label(),
    )


def _effective(member: dict | None, listing: dict | None) -> dict:
    base = {f: (member or {}).get(f) for f in PREF_FIELDS}
    if listing:
        for f in PREF_FIELDS:
            if listing.get(f) is not None:
                base[f] = listing[f]
    return base


async def get_member_contact_preferences(conn: asyncpg.Connection, ctx: AuthzContext) -> ContactPreferencesOut:
    row = await conn.fetchrow(
        "SELECT call_hours_start, call_hours_end, call_days, max_calls_per_day, calls_from, whatsapp_ok, call_ok FROM vyapar_identity.members WHERE id = $1",
        ctx.member_id,
    )
    return _prefs_out(dict(row) if row else {})


async def update_member_contact_preferences(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, body: ContactPreferencesPatch) -> ContactPreferencesOut:
    _validate_window(body, lang)
    defaults = {"call_hours_start": None, "call_hours_end": None, "call_days": [], "max_calls_per_day": None,
                "calls_from": "anyone", "whatsapp_ok": True, "call_ok": True}
    row = await conn.fetchrow(
        """UPDATE vyapar_identity.members SET
             call_hours_start = CASE WHEN 'call_hours_start' = ANY($8::text[]) THEN NULL ELSE COALESCE($2::time, call_hours_start) END,
             call_hours_end   = CASE WHEN 'call_hours_end' = ANY($8::text[]) THEN NULL ELSE COALESCE($3::time, call_hours_end) END,
             call_days        = CASE WHEN 'call_days' = ANY($8::text[]) THEN '{}'::text[] ELSE COALESCE($4::text[], call_days) END,
             max_calls_per_day = CASE WHEN 'max_calls_per_day' = ANY($8::text[]) THEN NULL ELSE COALESCE($5::int, max_calls_per_day) END,
             calls_from       = CASE WHEN 'calls_from' = ANY($8::text[]) THEN 'anyone' ELSE COALESCE($6::text, calls_from) END,
             whatsapp_ok      = CASE WHEN 'whatsapp_ok' = ANY($8::text[]) THEN true ELSE COALESCE($7::boolean, whatsapp_ok) END,
             call_ok          = CASE WHEN 'call_ok' = ANY($8::text[]) THEN true ELSE COALESCE($9::boolean, call_ok) END,
             updated_at = now()
           WHERE id = $1
           RETURNING call_hours_start, call_hours_end, call_days, max_calls_per_day, calls_from, whatsapp_ok, call_ok""",
        ctx.member_id, _parse_time(body.call_hours_start), _parse_time(body.call_hours_end), body.call_days,
        body.max_calls_per_day, body.calls_from, body.whatsapp_ok, body.reset, body.call_ok,
    )
    return _prefs_out(dict(row) if row else defaults)


async def _owned_listing(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, listing_id: str) -> asyncpg.Record:
    try:
        row = await conn.fetchrow("SELECT * FROM vyapar_listings.listings WHERE id = $1", listing_id)
    except asyncpg.DataError:
        row = None
    if row is None or row["owner_id"] != ctx.member_id:
        raise ApiError(404, "common.error.listingNotFound", lang)
    return row


def _listing_prefs_out(listing: asyncpg.Record, member: dict) -> ListingContactPreferencesOut:
    listing_d = dict(listing)
    return ListingContactPreferencesOut(
        listing_id=str(listing["id"]),
        effective=_prefs_out(_effective(member, listing_d)),
        overrides=[f for f in PREF_FIELDS if listing_d.get(f) is not None],
    )


async def get_listing_contact_preferences(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, listing_id: str) -> ListingContactPreferencesOut:
    listing = await _owned_listing(conn, ctx, lang, listing_id)
    member = await get_member_contact_preferences(conn, ctx)
    return _listing_prefs_out(listing, _member_dict(member))


def _member_dict(prefs: ContactPreferencesOut) -> dict:
    return {
        "call_hours_start": _parse_time(prefs.call_hours_start), "call_hours_end": _parse_time(prefs.call_hours_end),
        "call_days": prefs.call_days, "max_calls_per_day": prefs.max_calls_per_day, "calls_from": prefs.calls_from,
        "whatsapp_ok": prefs.whatsapp_ok, "call_ok": prefs.call_ok,
    }


def _validate_window(body: ContactPreferencesPatch, lang: str) -> None:
    # A missing half of the window means "any hour" on that side; only an
    # empty window (start == end) is meaningless and refused.
    if body.call_hours_start and body.call_hours_end and body.call_hours_start == body.call_hours_end:
        raise ApiError(422, "contact.error.emptyWindow", lang)


async def update_listing_contact_preferences(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, listing_id: str, body: ContactPreferencesPatch) -> ListingContactPreferencesOut:
    await _owned_listing(conn, ctx, lang, listing_id)
    _validate_window(body, lang)
    listing = await conn.fetchrow(
        """UPDATE vyapar_listings.listings SET
             call_hours_start = CASE WHEN 'call_hours_start' = ANY($8::text[]) THEN NULL ELSE COALESCE($2::time, call_hours_start) END,
             call_hours_end   = CASE WHEN 'call_hours_end' = ANY($8::text[]) THEN NULL ELSE COALESCE($3::time, call_hours_end) END,
             call_days        = CASE WHEN 'call_days' = ANY($8::text[]) THEN NULL ELSE COALESCE($4::text[], call_days) END,
             max_calls_per_day = CASE WHEN 'max_calls_per_day' = ANY($8::text[]) THEN NULL ELSE COALESCE($5::int, max_calls_per_day) END,
             calls_from       = CASE WHEN 'calls_from' = ANY($8::text[]) THEN NULL ELSE COALESCE($6::text, calls_from) END,
             whatsapp_ok      = CASE WHEN 'whatsapp_ok' = ANY($8::text[]) THEN NULL ELSE COALESCE($7::boolean, whatsapp_ok) END,
             call_ok          = CASE WHEN 'call_ok' = ANY($8::text[]) THEN NULL ELSE COALESCE($9::boolean, call_ok) END,
             updated_at = now()
           WHERE id = $1 RETURNING *""",
        listing_id, _parse_time(body.call_hours_start), _parse_time(body.call_hours_end), body.call_days,
        body.max_calls_per_day, body.calls_from, body.whatsapp_ok, body.reset, body.call_ok,
    )
    member = await get_member_contact_preferences(conn, ctx)
    return _listing_prefs_out(listing, _member_dict(member))


# ---------------------------------------------------------------------------
# Contact actions on an accepted enquiry
# ---------------------------------------------------------------------------
class ContactAction(BaseModel):
    channel: Channel
    label: str
    href: str | None = Field(default=None, description="tel:+91... or https://wa.me/91...?text=...; null while the callee's rule does not allow this caller")
    available_now: bool
    next_window: str | None = Field(default=None, description="ISO 8601 local time when the next call window opens; null when open now or no window applies")
    reason: Literal["outside_hours", "day_off", "daily_cap_reached", "not_matching", "precall_off", "caller_limit_reached", "whatsapp_only"] | None = None
    reason_label: str | None = None
    window: str | None = Field(default=None, description="Human summary of the callee's window, e.g. 'mon-sat 09:00-18:00'")


class ContactAttemptOut(BaseModel):
    id: str
    enquiry_id: str | None
    caller_id: str
    callee_id: str
    channel: Channel
    at: str = Field(description="UTC, ISO 8601 (machine use)")
    at_local: str = Field(default="", description="The same instant in IST (Asia/Kolkata, +05:30), ISO 8601")
    mine: bool
    summary: str


class ContactActionsOut(BaseModel):
    enquiry_id: str
    revealed: bool
    counterpart_id: str
    counterpart_name: str | None
    contact_actions: list[ContactAction] = []
    attempts: list[ContactAttemptOut] = []
    calls_today: int = 0
    max_calls_per_day: int | None = None


class ContactAttemptIn(BaseModel):
    channel: Channel


def _e164(raw: str) -> str | None:
    cc = get_settings().contact_default_country_code
    digits = re.sub(r"\D", "", raw or "")
    if not digits:
        return None
    if raw.strip().startswith("+") and 8 <= len(digits) <= 15:
        return "+" + digits
    if len(digits) == 10:
        return f"+{cc}{digits}"
    if len(digits) == 11 and digits.startswith("0"):
        return f"+{cc}{digits[1:]}"
    if len(digits) == 12 and digits.startswith(cc):
        return "+" + digits
    if 8 <= len(digits) <= 15:
        return "+" + digits
    return None


def _window_summary(prefs: dict) -> str | None:
    days = list(prefs.get("call_days") or [])
    start, end = prefs.get("call_hours_start"), prefs.get("call_hours_end")
    if not days and not (start or end):
        return None
    ordered = sorted(days, key=DAYS.index)
    consecutive = len(ordered) > 2 and [DAYS.index(d) for d in ordered] == list(range(DAYS.index(ordered[0]), DAYS.index(ordered[-1]) + 1))
    day_part = f"{ordered[0]}-{ordered[-1]}" if consecutive else ",".join(ordered)
    hour_part = f"{_fmt_time(start) or '00:00'}-{_fmt_time(end) or '24:00'}" if (start or end) else ""
    return " ".join(p for p in (day_part, hour_part) if p) or None


def window_state(prefs: dict, now_local: datetime, calls_today: int) -> tuple[bool, str | None, datetime | None]:
    """(available_now, reason, next_window) from the callee's window and cap."""
    days = list(prefs.get("call_days") or []) or list(DAYS)
    start: time = prefs.get("call_hours_start") or time(0, 0)
    end: time = prefs.get("call_hours_end") or time(23, 59, 59)
    cap = prefs.get("max_calls_per_day")

    def in_window(moment: datetime) -> bool:
        if DAYS[moment.weekday()] not in days:
            return False
        t = moment.time()
        return (start <= t < end) if start <= end else (t >= start or t < end)

    def next_open(after: datetime, skip_today: bool) -> datetime | None:
        for d in range(0 if not skip_today else 1, 9):
            day = (after + timedelta(days=d)).date()
            if DAYS[day.weekday()] not in days:
                continue
            candidate = datetime.combine(day, start, tzinfo=after.tzinfo)
            if candidate > after:
                return candidate
        return None

    if cap is not None and calls_today >= cap:
        return False, "daily_cap_reached", next_open(now_local, skip_today=True)
    if in_window(now_local):
        return True, None, None
    reason = "day_off" if DAYS[now_local.weekday()] not in days else "outside_hours"
    return False, reason, next_open(now_local, skip_today=False)


async def _enquiry_or_404(conn: asyncpg.Connection, enquiry_id: str, lang: str) -> asyncpg.Record:
    try:
        row = await conn.fetchrow("SELECT * FROM vyapar_enquiries.enquiries WHERE id = $1", enquiry_id)
    except asyncpg.DataError:
        row = None
    if row is None:
        raise ApiError(404, "enquiries.error.notFound", lang)
    return row


async def _counterpart_listing(conn: asyncpg.Connection, enquiry: asyncpg.Record, counterpart_id: str) -> asyncpg.Record | None:
    """The listing whose disclosed contacts reach the counterpart: the
    enquiry's own listing when they are its owner, else their newest
    active listing (an opportunity poster answering an application)."""
    if enquiry["listing_id"] and counterpart_id == enquiry["provider_id"]:
        row = await conn.fetchrow("SELECT * FROM vyapar_listings.listings WHERE id = $1", enquiry["listing_id"])
        if row is not None:
            return row
    return await conn.fetchrow(
        """SELECT * FROM vyapar_listings.listings WHERE owner_id = $1 AND state IN ('active_unverified','active_verified')
           ORDER BY published_at DESC NULLS LAST LIMIT 1""",
        counterpart_id,
    )


async def _target_capabilities(conn: asyncpg.Connection, enquiry: asyncpg.Record, listing: asyncpg.Record | None) -> list[str]:
    if enquiry["opportunity_id"]:
        caps = await conn.fetchval("SELECT required_capabilities FROM vyapar_opportunities.opportunities WHERE id = $1", enquiry["opportunity_id"])
        return list(caps or [])
    return list(listing["capabilities"] or []) if listing is not None else []


def _matches(caller_caps: list[str], target_caps: list[str]) -> bool:
    """[FR19] The feed's own capability signal decides "matching": overlap
    ratio > 0, and an empty requirement counts as matching (the feed scores
    it 0.3, never 0)."""
    caller, target = set(caller_caps or []), set(target_caps or [])
    fit = len(caller & target) / len(target) if target else 0.3
    return RankingSignals(capability_fit=fit).capability_fit > 0


async def _target_title(conn: asyncpg.Connection, enquiry: asyncpg.Record, listing: asyncpg.Record | None) -> str:
    if enquiry["opportunity_id"]:
        title = await conn.fetchval("SELECT title FROM vyapar_opportunities.opportunities WHERE id = $1", enquiry["opportunity_id"])
        if title:
            return title
    return listing["name"] if listing is not None else ""


def _attempt_out(row: asyncpg.Record, caller_id: str, names: dict[str, str], lang: str) -> ContactAttemptOut:
    mine = row["caller_id"] == caller_id
    other = row["callee_id"] if mine else row["caller_id"]
    at_local = to_local(row["at"])
    channel_label = translate(f"contact.channel.{row['channel']}", lang)
    when = format_local(row["at"], lang)
    key = "contact.attempt.youContacted" if mine else "contact.attempt.theyContacted"
    return ContactAttemptOut(
        id=str(row["id"]), enquiry_id=str(row["enquiry_id"]) if row["enquiry_id"] else None, caller_id=row["caller_id"], callee_id=row["callee_id"],
        channel=row["channel"], at=row["at"].isoformat(), at_local=at_local.isoformat(), mine=mine,
        summary=translate(key, lang, name=names.get(other, ""), channel=channel_label, when=when),
    )


async def contact_actions_for_enquiry(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, enquiry_id: str) -> ContactActionsOut:
    enquiry = await _enquiry_or_404(conn, enquiry_id, lang)
    caller_id = ctx.member_id
    counterpart_id = enquiry["provider_id"] if caller_id == enquiry["sender_id"] else enquiry["sender_id"]
    names = {r["id"]: r["display_name"] for r in await conn.fetch(
        "SELECT id, display_name FROM vyapar_identity.public_names($1::text[])", [counterpart_id, caller_id])}
    out = ContactActionsOut(enquiry_id=str(enquiry["id"]), revealed=enquiry["state"] in REVEALED_STATES,
                            counterpart_id=counterpart_id, counterpart_name=names.get(counterpart_id))
    attempts = await conn.fetch(
        "SELECT * FROM vyapar_enquiries.contact_attempts WHERE enquiry_id = $1 ORDER BY at DESC LIMIT 50", enquiry["id"]
    )
    out.attempts = [_attempt_out(a, caller_id, names, lang) for a in attempts]
    if not out.revealed:
        return out  # [TR024] nothing about the number leaves the server before acceptance

    listing = await _counterpart_listing(conn, enquiry, counterpart_id)
    member_prefs = await conn.fetchrow("SELECT * FROM vyapar_identity.contact_preferences_for($1)", counterpart_id)
    prefs = _effective(dict(member_prefs) if member_prefs else {}, dict(listing) if listing is not None else None)
    contacts = await conn.fetch("SELECT * FROM vyapar_listings.contacts_for_viewer($1, true)", listing["id"]) if listing is not None else []
    phone = next((c["value"] for c in contacts if c["channel"] == "phone"), None)
    whatsapp = next((c["value"] for c in contacts if c["channel"] == "whatsapp"), None) or phone
    phone = phone or whatsapp

    offset = get_settings().contact_timezone_offset_minutes
    calls_today = await conn.fetchval("SELECT vyapar_enquiries.contact_attempts_today($1, 'call', $2)", counterpart_id, offset)
    out.calls_today = int(calls_today or 0)
    out.max_calls_per_day = prefs.get("max_calls_per_day")
    now_local = datetime.now(_tz())
    available, reason, next_at = window_state(prefs, now_local, out.calls_today)

    matching = True
    if (prefs.get("calls_from") or "anyone") == "matching_only":
        caller_caps = await viewer_capabilities(conn, caller_id)
        matching = _matches(list(caller_caps or []), await _target_capabilities(conn, enquiry, listing))

    title = await _target_title(conn, enquiry, listing)
    summary = _window_summary(prefs)
    call_ok = True if prefs.get("call_ok") is None else bool(prefs["call_ok"])
    whatsapp_ok = True if prefs.get("whatsapp_ok") is None else bool(prefs["whatsapp_ok"])

    def action(channel: str, number: str | None) -> ContactAction | None:
        e164 = _e164(number or "")
        if e164 is None:
            return None
        if not matching:
            return ContactAction(channel=channel, label=translate(f"contact.channel.{channel}", lang), href=None,
                                 available_now=False, reason="not_matching",
                                 reason_label=translate("contact.reason.not_matching", lang), window=summary)
        if channel == "call":
            href = f"tel:{e164}"
            avail, why, nxt = available, reason, next_at
        else:
            text = translate("contact.prefill.whatsapp", lang, name=names.get(counterpart_id, ""), subject=title,
                             me=names.get(caller_id) or "")
            href = f"https://wa.me/{e164.lstrip('+')}?text={quote(text)}"
            # A message can be sent any time; only the daily cap is a call cap.
            avail, why, nxt = True, None, None
        return ContactAction(
            channel=channel, label=translate(f"contact.channel.{channel}", lang), href=href, available_now=avail,
            next_window=nxt.isoformat() if nxt else None, reason=why,
            reason_label=translate(f"contact.reason.{why}", lang, when=format_local(nxt, lang, weekday=True, year=False) if nxt else "") if why else None,
            window=summary,
        )

    if call_ok and (a := action("call", phone)):
        out.contact_actions.append(a)
    if whatsapp_ok and (a := action("whatsapp", whatsapp)):
        out.contact_actions.append(a)
    return out


async def record_contact_attempt(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, enquiry_id: str, body: ContactAttemptIn) -> ContactActionsOut:
    current = await contact_actions_for_enquiry(conn, ctx, lang, enquiry_id)
    if not current.revealed:
        raise ApiError(400, "contact.error.notRevealed", lang)
    action = next((a for a in current.contact_actions if a.channel == body.channel), None)
    if action is None:
        raise ApiError(400, "contact.error.channelOff", lang)
    if action.reason == "not_matching":
        raise ApiError(403, "contact.error.notMatching", lang)
    if action.reason == "daily_cap_reached":
        raise ApiError(429, "contact.error.dailyCapReached", lang, error_code="daily_cap_reached",
                       extra={"next_window": action.next_window})
    await conn.execute(
        "INSERT INTO vyapar_enquiries.contact_attempts (enquiry_id, caller_id, callee_id, channel) VALUES ($1, $2, $3, $4)",
        enquiry_id, ctx.member_id, current.counterpart_id, body.channel,
    )
    return await contact_actions_for_enquiry(conn, ctx, lang, enquiry_id)


async def list_contact_attempts(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, enquiry_id: str) -> list[ContactAttemptOut]:
    return (await contact_actions_for_enquiry(conn, ctx, lang, enquiry_id)).attempts


# ---------------------------------------------------------------------------
# [IMP-B/L1, owner-approved 2026-09-28] Pre-accept calling on an opportunity.
# A poster who switched on `allow_precall` (employment / local_service) can be
# called or messaged straight from the post, like Apna's "Call HR" and
# WorkIndia's "Click to call HR". Every protection above applies to every
# caller: the poster's (or their listing's) call hours and days, the daily
# call cap counted across all callers, and calls_from = matching_only against
# the post's required_capabilities. Stricter than the enquiry flow on one
# point: the number is sent ONLY inside `href` and ONLY while the action is
# available now; otherwise href is null and `reason` says why. A caller may
# tap at most PRECALL_CALLER_TAPS_PER_DAY times a day per post. Each tap
# notifies the poster in their language, and a caller with no open
# application gets a lightweight `apply` enquiry (applied_via = 'call', built
# through enquiries.create_enquiry and its profile snapshot) so they appear
# on the applicants board.
# Traces to: FR02, FR22, FR24, TR024, critique L1
# ---------------------------------------------------------------------------
OPEN_ENQUIRY_EXCLUDED = ("resolved", "closed", "withdrawn")


class PrecallActionsOut(BaseModel):
    opportunity_id: str
    allow_precall: bool
    precall_channel: str = Field(default="whatsapp_only", description="whatsapp_only | call_and_whatsapp (critique W2)")
    available: bool = Field(description="True when at least one action can be used right now")
    reason: Literal["precall_off", "own_post", "no_contact"] | None = Field(
        default=None, description="Why there is nothing to tap at all (per-action reasons are on each action)")
    reason_label: str | None = None
    poster_name: str | None = None
    contact_actions: list[ContactAction] = []
    calls_today: int = 0
    max_calls_per_day: int | None = None
    my_taps_today: int = 0
    my_taps_limit: int = 0
    application_enquiry_id: str | None = Field(default=None, description="The caller's open application on this post, if any")
    attempts: list[ContactAttemptOut] = Field(default_factory=list, description="The caller's own taps on this post")


class PrecallAttemptOut(PrecallActionsOut):
    attempt_id: str
    application_created: bool = False
    application_error_code: str | None = Field(
        default=None, description="Why no application could be created for this tap (e.g. profile_required); the tap is still recorded")


def _precall_empty(opp_id: str, allow: bool, reason: str, lang: str, **kw) -> PrecallActionsOut:
    return PrecallActionsOut(opportunity_id=opp_id, allow_precall=allow, available=False, reason=reason,
                             reason_label=translate(f"contact.precall.reason.{reason}", lang), **kw)


_LOCAL_DAY_SQL = "(a.at + make_interval(mins => $3))::date = (now() + make_interval(mins => $3))::date"


async def opportunity_contact_actions(conn: asyncpg.Connection, ctx: AuthzContext | None, lang: str, opportunity_id: str) -> PrecallActionsOut:
    settings = get_settings()
    try:
        opp = await conn.fetchrow(
            """SELECT id, poster_id, state, type, title, allow_precall, precall_channel, required_capabilities, listing_id
                 FROM vyapar_opportunities.opportunities WHERE id = $1""", opportunity_id)
    except asyncpg.DataError:
        opp = None
    if opp is None:
        raise ApiError(404, "common.error.opportunityNotFound", lang)
    opp_id, allow = str(opp["id"]), bool(opp["allow_precall"])
    whatsapp_only = (opp["precall_channel"] or "whatsapp_only") == "whatsapp_only"
    caller_id = ctx.member_id if ctx is not None else None
    if not caller_id:  # anonymous: nothing, not even whether the poster has a number
        return _precall_empty(opp_id, allow, "precall_off", lang)
    if caller_id == opp["poster_id"]:
        return _precall_empty(opp_id, allow, "own_post", lang)

    limit = settings.precall_caller_taps_per_day
    offset = settings.contact_timezone_offset_minutes
    mine = await conn.fetch(
        """SELECT * FROM vyapar_enquiries.contact_attempts a
            WHERE a.opportunity_id = $1 AND a.caller_id = $2 ORDER BY a.at DESC LIMIT 20""",
        opp["id"], caller_id,
    )
    my_today = await conn.fetchval(
        f"""SELECT count(*) FROM vyapar_enquiries.contact_attempts a
             WHERE a.opportunity_id = $1 AND a.caller_id = $2 AND {_LOCAL_DAY_SQL}""",
        opp["id"], caller_id, offset,
    )
    application = await conn.fetchval(
        """SELECT id FROM vyapar_enquiries.enquiries
            WHERE sender_id = $1 AND opportunity_id = $2 AND NOT (state = ANY($3::text[]))
            ORDER BY created_at DESC LIMIT 1""",
        caller_id, opp["id"], list(OPEN_ENQUIRY_EXCLUDED),
    )
    names = {r["id"]: r["display_name"] for r in await conn.fetch(
        "SELECT id, display_name FROM vyapar_identity.public_names($1::text[])", [opp["poster_id"]])}
    my_name = await conn.fetchval("SELECT display_name FROM vyapar_identity.members WHERE id = $1", caller_id) or ""
    names[caller_id] = my_name
    common = dict(
        precall_channel=opp["precall_channel"] or "whatsapp_only",
        poster_name=names.get(opp["poster_id"]), my_taps_today=int(my_today or 0), my_taps_limit=limit,
        application_enquiry_id=str(application) if application else None,
        attempts=[_attempt_out(a, caller_id, names, lang) for a in mine],
    )

    blocked = await conn.fetchval("SELECT vyapar_enquiries.is_blocked($1, $2)", opp["poster_id"], caller_id)
    if not allow or opp["state"] != "active" or blocked:
        # A block reads exactly like "switched off": the caller can't tell them apart.
        out = _precall_empty(opp_id, allow and not blocked, "precall_off", lang, **common)
        out.contact_actions = [
            ContactAction(channel=ch, label=translate(f"contact.channel.{ch}", lang), href=None, available_now=False,
                          reason="precall_off", reason_label=translate("contact.reason.precall_off", lang))
            for ch in ("call", "whatsapp")
        ]
        return out

    listing = None
    if opp["listing_id"]:
        listing = await conn.fetchrow(
            "SELECT * FROM vyapar_listings.listings WHERE id = $1 AND owner_id = $2", opp["listing_id"], opp["poster_id"])
    if listing is None:
        listing = await conn.fetchrow(
            """SELECT * FROM vyapar_listings.listings WHERE owner_id = $1 AND state IN ('active_unverified','active_verified')
               ORDER BY published_at DESC NULLS LAST LIMIT 1""", opp["poster_id"])
    member_prefs = await conn.fetchrow("SELECT * FROM vyapar_identity.contact_preferences_for($1)", opp["poster_id"])
    prefs = _effective(dict(member_prefs) if member_prefs else {}, dict(listing) if listing is not None else None)
    # The poster opted in to pre-accept contact for this post, so after_accept
    # channels count; 'hidden' ones never do (contacts_for_viewer's own rule).
    contacts = await conn.fetch("SELECT * FROM vyapar_listings.contacts_for_viewer($1, true)", listing["id"]) if listing is not None else []
    phone = next((c["value"] for c in contacts if c["channel"] == "phone"), None)
    whatsapp = next((c["value"] for c in contacts if c["channel"] == "whatsapp"), None) or phone
    phone = phone or whatsapp
    call_ok = True if prefs.get("call_ok") is None else bool(prefs["call_ok"])
    whatsapp_ok = True if prefs.get("whatsapp_ok") is None else bool(prefs["whatsapp_ok"])
    channels = [(ch, num) for ch, num, ok in (("call", phone, call_ok), ("whatsapp", whatsapp, whatsapp_ok)) if ok and _e164(num or "")]
    if not channels:
        return _precall_empty(opp_id, allow, "no_contact", lang, **common)

    calls_today = int(await conn.fetchval("SELECT vyapar_enquiries.contact_attempts_today($1, 'call', $2)", opp["poster_id"], offset) or 0)
    now_local = datetime.now(_tz())
    window_ok, window_reason, next_at = window_state(prefs, now_local, calls_today)
    matching = True
    if (prefs.get("calls_from") or "anyone") == "matching_only":
        caller_caps = await viewer_capabilities(conn, caller_id)
        matching = _matches(list(caller_caps or []), list(opp["required_capabilities"] or []))
    caller_limited = common["my_taps_today"] >= limit
    summary = _window_summary(prefs)

    actions: list[ContactAction] = []
    for channel, number in channels:
        e164 = _e164(number)
        reason, nxt = None, None
        if channel == "call" and whatsapp_only:
            reason = "whatsapp_only"
        elif not matching:
            reason = "not_matching"
        elif caller_limited:
            reason = "caller_limit_reached"
        elif channel == "call" and not window_ok:
            reason, nxt = window_reason, next_at
        if reason is None:
            if channel == "call":
                href = f"tel:{e164}"
            else:
                text = translate("contact.prefill.whatsappJob", lang, name=names.get(opp["poster_id"]) or "", job=opp["title"], me=my_name)
                href = f"https://wa.me/{e164.lstrip('+')}?text={quote(text)}"
        else:
            href = None  # the number never leaves the server while it can't be used
        actions.append(ContactAction(
            channel=channel, label=translate(f"contact.channel.{channel}", lang), href=href, available_now=reason is None,
            next_window=nxt.isoformat() if nxt else None, reason=reason,
            reason_label=translate(f"contact.reason.{reason}", lang, when=format_local(nxt, lang, weekday=True, year=False) if nxt else "", limit=limit) if reason else None,
            window=summary,
        ))
    return PrecallActionsOut(
        opportunity_id=opp_id, allow_precall=allow, available=any(a.available_now for a in actions), contact_actions=actions,
        calls_today=calls_today, max_calls_per_day=prefs.get("max_calls_per_day"), **common,
    )


_PRECALL_REFUSALS = {
    "not_matching": (403, "contact.error.notMatching", "not_matching"),
    "caller_limit_reached": (429, "contact.error.precallCallerLimit", "precall_caller_limit"),
    "daily_cap_reached": (429, "contact.error.dailyCapReached", "daily_cap_reached"),
    "outside_hours": (409, "contact.error.outsideHours", "outside_hours"),
    "day_off": (409, "contact.error.outsideHours", "outside_hours"),
    "precall_off": (403, "contact.error.precallOff", "precall_off"),
    "whatsapp_only": (403, "contact.error.precallWhatsappOnly", "precall_whatsapp_only"),
}


async def record_opportunity_contact_attempt(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, opportunity_id: str, body: ContactAttemptIn) -> PrecallAttemptOut:
    from app.i18n import LAUNCH_LANGUAGES
    from app.services import enquiries as enquiries_svc  # local: enquiries imports listings/opportunities

    current = await opportunity_contact_actions(conn, ctx, lang, opportunity_id)
    if current.reason == "own_post":
        raise ApiError(400, "contact.error.ownPost", lang, error_code="own_post")
    if current.reason == "precall_off":
        raise ApiError(403, "contact.error.precallOff", lang, error_code="precall_off")
    action = next((a for a in current.contact_actions if a.channel == body.channel), None)
    if action is None:
        raise ApiError(400, "contact.error.channelOff", lang)
    if action.href is None:
        status, key, code = _PRECALL_REFUSALS.get(action.reason or "precall_off", _PRECALL_REFUSALS["precall_off"])
        raise ApiError(status, key, lang, error_code=code, extra={"next_window": action.next_window}, limit=current.my_taps_limit)

    opp = await conn.fetchrow("SELECT id, poster_id, title FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    # One application per caller: create the lightweight one on the first tap.
    enquiry_id, created, app_error = current.application_enquiry_id, False, None
    if enquiry_id is None:
        snapshot = await enquiries_svc.build_profile_snapshot(conn, ctx.member_id)
        message = (translate("contact.precall.leadIntro", lang, channel=translate(f"contact.channel.{body.channel}", lang))
                   + " " + enquiries_svc._one_tap_message(snapshot, lang))[:1000]
        try:
            async with conn.transaction():  # savepoint: a refused application must not undo the tap
                enquiry = await enquiries_svc.create_enquiry(
                    conn, ctx, lang,
                    body=enquiries_svc.EnquiryCreate(opportunity_id=opportunity_id, message=message, applied_via="call"),
                )
            enquiry_id, created = enquiry.id, True
        except ApiError as exc:
            app_error = exc.code
    attempt = await conn.fetchrow(
        """INSERT INTO vyapar_enquiries.contact_attempts (enquiry_id, opportunity_id, caller_id, callee_id, channel)
           VALUES ($1, $2, $3, $4, $5) RETURNING id""",
        enquiry_id, opp["id"], ctx.member_id, opp["poster_id"], body.channel,
    )
    caller_name = (await conn.fetchval("SELECT display_name FROM vyapar_identity.members WHERE id = $1", ctx.member_id) or "").split(" ")[0]
    texts: dict = {"_i18n": {"title": f"notifications.precallContact.title_{body.channel}", "body": "notifications.precallContact.body",
                             "values": {"name": caller_name, "job": opp["title"]}}}
    texts |= {
        lg: {"title": translate(f"notifications.precallContact.title_{body.channel}", lg, name=caller_name, job=opp["title"]),
             "body": translate("notifications.precallContact.body", lg, name=caller_name)}
        for lg in LAUNCH_LANGUAGES
    }
    await conn.fetchval("SELECT vyapar_integration.notify_precall($1, $2::jsonb)", attempt["id"], json.dumps(texts, ensure_ascii=False))
    after = await opportunity_contact_actions(conn, ctx, lang, opportunity_id)
    return PrecallAttemptOut(**after.model_dump(), attempt_id=str(attempt["id"]), application_created=created,
                             application_error_code=app_error)


@hooks.register_opportunity_enricher
async def enrich_opportunity_with_precall(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, opportunity: dict) -> dict:
    """Detail read: the viewer's call/WhatsApp block when the poster allows it."""
    if not opportunity.get("allow_precall") or opportunity.get("is_poster"):
        return {}
    try:
        out = await opportunity_contact_actions(conn, ctx, lang, str(opportunity.get("id")))
    except ApiError:
        return {}
    return {"precall_actions": out.model_dump(mode="json")}


# ---------------------------------------------------------------------------
# Hook for the enquiry thread read (services/enquiries.py may call
# hooks.run_enquiry_enrichers and merge these keys into its response).
# ---------------------------------------------------------------------------
@hooks.register_enquiry_enricher
async def enrich_enquiry_with_contact_actions(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, enquiry: dict) -> dict:
    try:
        out = await contact_actions_for_enquiry(conn, ctx, lang, str(enquiry.get("id")))
    except ApiError:
        return {}
    return {"contact_actions": [a.model_dump() for a in out.contact_actions],
            "contact_attempts": [a.model_dump() for a in out.attempts]}

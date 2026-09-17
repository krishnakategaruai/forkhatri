"""Discovery & Ranking — public interface (`milavn_discovery`).

# [FR004-FR009, FR033, TR02-TR06] "Around You" groups locally-relevant
# occurrences into Today / Tomorrow / This Weekend (IST); four modes (Feed,
# Calendar, Map, Search) share one card contract (six questions + a real
# "why this?" reason); ranking is deterministic and rules-based with
# popularity never a factor.
# Approach: candidates come from Activity & Occurrence's own interface
# (RLS-scoped to the viewer), then `RankingEngine` scores four typed inputs
# (locality proximity, interest match, trust, freshness) plus circle
# relevance using the versioned weights in `ranking_weight_config`. The
# reason string is generated from the SAME factor that dominated the score —
# an item with no factor-grounded reason is excluded (TR04), never rendered
# with "Recommended for you".
# `MilavnActivityFeedReader` (TR02) is the only surface Dashboard may import.
# Traces to: TR02, TR03, TR04, TR05, TR06, FR038.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.activity import interface as activity
from app.components.activity.interface import Occurrence
from app.components.identity_bridge import interface as identity
from app.components.locationprivacy import interface as locpriv
from app.components.trust import interface as trust
from app.config import localities
from app.config.interests import TAG_LABELS, TAG_TO_CATEGORY
from app.i18n import current_language, translate

IST = ZoneInfo("Asia/Kolkata")
# The web app's static covers (served by Next from milavn-web/public); checked
# for existence so a missing keyword photo falls back to the category one.
_ASSETS_DIR = Path(__file__).resolve().parents[4] / "milavn-web" / "public" / "assets" / "covers"

CATEGORY_LABELS = {
    "play": "Play",
    "meet": "Meet",
    "eat": "Eat",
    "learn": "Learn",
    "work": "Work",
    "explore": "Explore",
    "celebrate": "Celebrate",
    "help": "Help",
}


@dataclass(slots=True)
class Card:
    """[FR006] What / when / where / who / how many / why — all six, always."""

    id: UUID
    slug: str
    title: str
    intent_category: str
    category_label: str
    time_start: datetime
    time_end: datetime | None
    location_label: str
    distance_label: str | None
    host_member_id: UUID
    host_name: str
    host_avatar: str | None
    going_count: int
    interested_count: int
    capacity: int | None
    spots_left: int | None
    trust_level: str
    trust_label: str
    trust_positive: bool
    why_reason: str
    why_factor: str
    viewer_status: str | None
    cover_image_url: str | None
    visibility_scope: str
    circle_id: UUID | None
    high_risk: bool
    status: str
    is_recurring: bool
    lat: float | None
    lng: float | None
    price_paise: int | None = None  # [FR102] None = free
    audience_tags: tuple[str, ...] = ()  # [FR110] family_friendly | elder_friendly | beginner_friendly
    food_tags: tuple[str, ...] = ()  # [FR110] veg | jain_options | non_veg | alcohol_free
    score: float = field(default=0.0, repr=False)


@dataclass(frozen=True, slots=True)
class ViewerProfile:
    member_id: UUID
    city: str
    zone: str | None
    locality: str | None
    interests: list[str]
    circle_ids: list[UUID]


@dataclass(frozen=True, slots=True)
class Weights:
    locality: float = 0.35
    interest: float = 0.30
    trust: float = 0.20
    freshness: float = 0.15
    version: int = 0


async def load_weights(session: AsyncSession) -> Weights:
    row = (
        await session.execute(
            text(
                "SELECT version, locality_weight, interest_weight, trust_weight, freshness_weight "
                "FROM milavn_discovery.ranking_weight_config WHERE effective_to IS NULL ORDER BY version DESC LIMIT 1"
            )
        )
    ).first()
    if row is None:
        return Weights()
    return Weights(float(row[1]), float(row[2]), float(row[3]), float(row[4]), int(row[0]))


async def viewer_profile(session: AsyncSession, member_id: UUID) -> ViewerProfile | None:
    from app.components.circle import interface as circle
    from app.components.profile import interface as profile

    p = await profile.get_own_profile(session, member_id=member_id)
    if p is None:
        return None
    circle_ids = await circle.my_circle_ids(session, member_id=member_id)
    return ViewerProfile(member_id, p.locality_city, p.locality_zone, p.locality_locality, p.interests, circle_ids)


TRUST_SCORE = {
    "forkhatri_verified": 1.0,
    "partner_verified": 0.9,
    "community_verified": 0.8,
    "external_trusted_source": 0.7,
    "community_submitted": 0.3,
}


Reason = tuple[str, dict] | None  # (i18n key, params) — rendered in the viewer's language at the edge


def _locality_factor(occ: Occurrence, viewer: ViewerProfile) -> tuple[float, Reason]:
    if viewer.locality and occ.locality_locality and viewer.locality.lower() == occ.locality_locality.lower():
        return 1.0, ("reason.locality", {"place": occ.locality_locality})
    if viewer.zone and occ.locality_zone and viewer.zone.lower() == occ.locality_zone.lower():
        return 0.65, ("reason.zone", {"place": occ.locality_zone})
    a = localities.find(viewer.city, viewer.locality)
    b = localities.find(occ.locality_city, occ.locality_locality)
    if a and b:
        km = localities.distance_km(a, b)
        if km <= 5:
            return 0.6, ("reason.km", {"km": f"{km:.0f}"})
        if km <= 12:
            return 0.4, ("reason.km", {"km": f"{km:.0f}"})
        return 0.2, None
    if viewer.city.lower() == occ.locality_city.lower():
        return 0.3, ("reason.city", {"place": occ.locality_city})
    return 0.0, None


def _interest_factor(occ: Occurrence, viewer: ViewerProfile) -> tuple[float, Reason]:
    haystack = f"{occ.title} {occ.description or ''}".lower()
    best = 0.0
    reason: Reason = None
    for tag in viewer.interests:
        words = TAG_LABELS.get(tag, tag).lower()
        if tag.replace("-", " ") in haystack or words in haystack or tag in haystack:
            return 1.0, ("reason.interest", {"interest": TAG_LABELS.get(tag, tag).lower()})
        if TAG_TO_CATEGORY.get(tag) == occ.intent_category and best < 0.5:
            best, reason = 0.5, ("reason.interest_category", {"interest": TAG_LABELS.get(tag, tag).lower()})
    return best, reason


def _freshness_factor(occ: Occurrence, now: datetime) -> tuple[float, Reason]:
    age_h = max(0.0, (now - occ.created_at).total_seconds() / 3600)
    if age_h <= 48:
        return 1.0, ("reason.fresh_new", {})
    if age_h <= 24 * 7:
        return 0.6, ("reason.fresh_week", {})
    return 0.2, None


def _time_fit(occ: Occurrence, now: datetime) -> float:
    hours = (occ.time_start - now).total_seconds() / 3600
    if hours < 0:
        return 0.0
    if hours <= 24:
        return 1.0
    if hours <= 72:
        return 0.8
    if hours <= 24 * 7:
        return 0.6
    return 0.3


class RankingEngine:
    """[FR007/TR05] Deterministic; popularity is structurally absent from the inputs."""

    def __init__(self, weights: Weights) -> None:
        self.w = weights

    def score(
        self,
        occ: Occurrence,
        viewer: ViewerProfile,
        *,
        trust_level: str,
        peers: int,
        now: datetime,
        host_times: int = 0,
        host_held: int | None = None,
        host_name: str = "",
    ) -> tuple[float, tuple[str, dict], str] | None:
        loc, loc_reason = _locality_factor(occ, viewer)
        interest, int_reason = _interest_factor(occ, viewer)
        fresh, fresh_reason = _freshness_factor(occ, now)
        tr = TRUST_SCORE.get(trust_level, 0.3)
        circle_hit = occ.circle_id is not None and occ.circle_id in viewer.circle_ids
        social = min(1.0, peers / 3) if peers else 0.0
        # [FR111] For brand-new activities the host matters most (Zhang & Wang 2015): having checked in at a host's
        # activities before is a strong, checkable signal. A host who has never held an activity gets a small, *labelled*
        # fair-start boost when it is nearby, so new hosts are not starved by the ones already known (Abdollahpouri 2019).
        returning = min(1.0, host_times / 2) if host_times else 0.0
        fair_start = host_held == 0 and loc >= 0.6

        base = self.w.locality * loc + self.w.interest * interest + self.w.trust * tr + self.w.freshness * fresh
        score = base + 0.25 * (1.0 if circle_hit else 0.0) + 0.2 * social + 0.1 * _time_fit(occ, now) + 0.15 * returning + (0.08 if fair_start else 0.0)

        # [FR008] The reason names the dominant *real* factor. Priority favours
        # the socially/personally specific over the generic. Reasons are i18n
        # keys + params, rendered in the viewer's language (FR002/ADR-010).
        candidates: list[tuple[float, tuple[str, dict], str]] = []
        if peers:
            candidates.append((0.2 * social + 0.5, ("reason.social_one" if peers == 1 else "reason.social_many", {"n": peers}), "social"))
        if circle_hit:
            candidates.append((0.45, ("reason.circle", {}), "circle"))
        if returning and host_name:
            candidates.append((0.35 + 0.05 * min(host_times, 3), ("reason.host_before", {"host": host_name}), "host"))
        if fair_start:
            candidates.append((0.12, ("reason.new_host", {}), "fair_start"))
        if interest and int_reason:
            candidates.append((self.w.interest * interest + (0.1 if interest == 1.0 else 0), int_reason, "interest"))
        if loc and loc_reason:
            candidates.append((self.w.locality * loc, loc_reason, "locality"))
        if tr >= 0.8:
            candidates.append((self.w.trust * tr, ("reason.trust", {"level": f"@trust.{trust_level}"}), "trust"))
        if fresh_reason:
            candidates.append((self.w.freshness * fresh, fresh_reason, "freshness"))
        if not candidates:
            return None  # [TR04] no factor-grounded reason -> excluded, never "Recommended for you"
        candidates.sort(key=lambda c: c[0], reverse=True)
        _, reason, factor = candidates[0]
        return score, reason, factor


HIDE_REASONS = ("not_my_thing", "too_far", "bad_time", "not_this_host")
HIDE_HOST_DAYS = 60


def cap_per_host(cards: list[Card], *, max_per_host: int = 2, window: int = 10) -> list[Card]:
    """[FR111] Within the first `window` results no host appears more than `max_per_host` times; the rest keep
    their order after the window. Variety without hiding anything (Kaminskas & Bridge 2016)."""
    head: list[Card] = []
    overflow: list[Card] = []
    counts: dict[UUID, int] = {}
    for c in cards:
        if len(head) < window and counts.get(c.host_member_id, 0) < max_per_host:
            head.append(c)
            counts[c.host_member_id] = counts.get(c.host_member_id, 0) + 1
        else:
            overflow.append(c)
    return head + overflow


async def hosts_attended(session: AsyncSession, member_id: UUID) -> dict[UUID, int]:
    rows = (await session.execute(text("SELECT host_member_id, times FROM milavn_activity.hosts_attended(:m)"), {"m": str(member_id)})).all()
    return {r[0]: int(r[1]) for r in rows}


async def host_track_record(session: AsyncSession, host_ids: list[UUID]) -> dict[UUID, int]:
    if not host_ids:
        return {}
    rows = (
        await session.execute(text("SELECT host_member_id, held FROM milavn_activity.host_track_record(CAST(:ids AS uuid[]))"), {"ids": [str(h) for h in host_ids]})
    ).all()
    return {r[0]: int(r[1]) for r in rows}


async def hide(session: AsyncSession, *, member_id: UUID, occurrence_id: UUID, reason: str) -> None:
    """[FR111] "Not interested", with a reason. "Not this host" also hides that host's activities for 60 days."""
    if reason not in HIDE_REASONS:
        raise ValueError(reason)
    host = (await activity.get(session, occurrence_id=occurrence_id)).creator_member_id if reason == "not_this_host" else None
    await session.execute(
        text(
            "INSERT INTO milavn_discovery.hidden_occurrence (member_id, occurrence_id, reason, host_member_id) VALUES (:m, :o, :r, :h) "
            "ON CONFLICT (member_id, occurrence_id) DO UPDATE SET reason = EXCLUDED.reason, host_member_id = EXCLUDED.host_member_id, created_at = now()"
        ),
        {"m": str(member_id), "o": str(occurrence_id), "r": reason, "h": str(host) if host else None},
    )


async def hidden_for(session: AsyncSession, member_id: UUID) -> tuple[set[UUID], set[UUID]]:
    rows = (
        await session.execute(
            text("SELECT occurrence_id, host_member_id, created_at > now() - make_interval(days => :d) FROM milavn_discovery.hidden_occurrence WHERE member_id = :m"),
            {"m": str(member_id), "d": HIDE_HOST_DAYS},
        )
    ).all()
    return {r[0] for r in rows}, {r[1] for r in rows if r[1] is not None and r[2]}


def render_reason(reason: tuple[str, dict], lang: str) -> str:
    """Render an (i18n key, params) reason; a param value starting with '@' is itself a key."""
    key, params = reason
    resolved = {k: translate(v[1:], lang) if isinstance(v, str) and v.startswith("@") else v for k, v in params.items()}
    return translate(key, lang, **resolved)


async def build_cards(
    session: AsyncSession, occurrences: list[Occurrence], viewer: ViewerProfile | None, *, rank: bool = True, lang: str | None = None, exclude_hidden: bool = False
) -> list[Card]:
    if not occurrences:
        return []
    lang = lang or current_language.get()
    now = datetime.now(UTC)
    weights = await load_weights(session)
    engine = RankingEngine(weights)
    ids = [o.id for o in occurrences]
    trust_map = await trust.trust_for_many(session, subject_type="occurrence", subject_ids=ids)
    hosts = await identity.display_names_for(list({o.creator_member_id for o in occurrences}))
    statuses = await activity.viewer_statuses(session, ids, viewer.member_id) if viewer else {}
    returning: dict[UUID, int] = {}
    track_record: dict[UUID, int] = {}  # activities each host has already held (0 = new host)
    hidden_occ: set[UUID] = set()
    hidden_hosts: set[UUID] = set()
    if viewer and rank:
        returning = await hosts_attended(session, viewer.member_id)
        track_record = await host_track_record(session, list({o.creator_member_id for o in occurrences}))
    if viewer and exclude_hidden:
        hidden_occ, hidden_hosts = await hidden_for(session, viewer.member_id)
    cards: list[Card] = []
    for occ in occurrences:
        # Something the member already joined never disappears from their own view, even if they hid the host later.
        if (occ.id in hidden_occ or occ.creator_member_id in hidden_hosts) and not statuses.get(occ.id):
            continue
        badge = trust_map.get(occ.id) or trust.TrustBadge("community_submitted", trust.TRUST_LABELS["community_submitted"], False)
        going = await activity.going_count(session, occ.id)
        # [FR114] Spots left counts guests too, so a card never promises room that is taken.
        taken = await activity.spots_taken(session, occ.id) if occ.capacity is not None else going
        held = await activity.held_spot_count(session, occ.id) if occ.capacity is not None and occ.price_paise is not None else 0
        interested = await activity.interested_count(session, occ.id)
        peers = await activity.circle_peers_going(session, occ.id, viewer.member_id) if viewer else 0
        if viewer and rank:
            scored = engine.score(
                occ,
                viewer,
                trust_level=badge.level,
                peers=peers,
                now=now,
                host_times=returning.get(occ.creator_member_id, 0),
                host_held=track_record.get(occ.creator_member_id),
                host_name=hosts[occ.creator_member_id].display_name.split(" ")[0],
            )
            if scored is None:
                continue
            score, reason, factor = scored
            why = render_reason(reason, lang)
        else:
            score, factor = 0.0, "public"
            why = render_reason(
                (
                    "reason.public",
                    {"level": f"@trust.{badge.level}", "category": f"@category.{occ.intent_category}", "place": occ.locality_locality or occ.locality_city},
                ),
                lang,
            )
        disp = locpriv.display_location(
            city=occ.locality_city,
            zone=occ.locality_zone,
            locality=occ.locality_locality,
            viewer_city=viewer.city if viewer else None,
            viewer_locality=viewer.locality if viewer else None,
        )
        host = hosts[occ.creator_member_id]
        loc = localities.find(occ.locality_city, occ.locality_locality)
        cards.append(
            Card(
                id=occ.id,
                slug=occ.canonical_url_slug,
                title=occ.title,
                intent_category=occ.intent_category,
                category_label=translate(f"category.{occ.intent_category}", lang),
                time_start=occ.time_start,
                time_end=occ.time_end,
                location_label=disp.label,
                distance_label=_distance_label(disp, lang),
                host_member_id=occ.creator_member_id,
                host_name=host.display_name,
                host_avatar=host.avatar,
                going_count=going,
                interested_count=interested,
                capacity=occ.capacity,
                spots_left=max(0, occ.capacity - taken - held) if occ.capacity is not None else None,
                trust_level=badge.level,
                trust_label=translate(f"trust.{badge.level}", lang),
                trust_positive=badge.positive,
                why_reason=why,
                why_factor=factor,
                viewer_status=statuses.get(occ.id),
                cover_image_url=cover_url(occ),
                visibility_scope=occ.visibility_scope,
                circle_id=occ.circle_id,
                high_risk=occ.high_risk,
                status=occ.status,
                is_recurring=occ.activity_id is not None,
                lat=loc.lat if loc else None,
                lng=loc.lng if loc else None,
                price_paise=occ.price_paise,
                audience_tags=tuple(occ.audience_tags),
                food_tags=tuple(occ.food_tags),
                score=score,
            )
        )
    if rank:
        cards.sort(key=lambda c: (-c.score, c.time_start))
        cards = cap_per_host(cards)
    return cards


def _distance_label(disp: locpriv.LocationDisplay, lang: str) -> str | None:
    if disp.distance_km is not None:
        return translate("distance.same", lang) if disp.distance_km < 1.0 else translate("distance.km", lang, km=f"{disp.distance_km:g}")
    if disp.distance_label:
        # Zone/city fallbacks carry the place name; translate the frame only.
        if disp.distance_label.startswith("In "):
            return translate("distance.in", lang, place=disp.distance_label[3:])
        return disp.distance_label
    return None


# Photography-led cards (UI04): when no cover was uploaded, pick the most
# specific stock photo the title/description suggests, then the category one.
# Ordered most-specific first and matched on word boundaries, so "biryani run"
# is food (not running) and "Prism Café" is not a "ride".
_COVER_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("kw-bathukamma", r"bathukamma"),
    ("kw-biryani", r"biryani|street food|food crawl|dinner|lunch|breakfast|dosa|tiffin"),
    ("kw-boardgames", r"board ?games?|catan|chess|carrom|ludo"),
    ("kw-founders", r"startup|founders?|networking|cowork|hackathon"),
    ("kw-yoga", r"yoga|meditation|pranayama"),
    ("kw-cricket", r"cricket"),
    ("kw-badminton", r"badminton|shuttle"),
    ("kw-football", r"football|soccer|futsal"),
    ("kw-cycling", r"cycl\w*|bike ride|ride|bicycle"),
    ("kw-running", r"run|running|marathon|jog\w*|5k|10k"),
    ("kw-trek", r"trek\w*|hik\w*|trail"),
    ("kw-cleanup", r"clean-?up|clean up|plantation|swachh"),
    ("kw-bookclub", r"book|reading|chapters"),
    ("kw-photowalk", r"photo ?walk|photograph\w*|camera"),
    ("kw-coffee", r"coffee|chai|caf[eé]"),
    ("kw-music", r"music|concert|jam|karaoke|gig"),
    ("kw-festival", r"diwali|deepavali|festival|dussehra|holi|sankranti|ganesh"),
)
_COVER_PATTERNS = [(name, re.compile(rf"\b(?:{pattern})\b", re.IGNORECASE)) for name, pattern in _COVER_KEYWORDS]


def cover_url(occ: Occurrence) -> str | None:
    if occ.cover_image_ref:
        return f"/media/covers/{occ.cover_image_ref}.jpg"
    haystack = f"{occ.title} {occ.description or ''}"
    for name, pattern in _COVER_PATTERNS:
        if pattern.search(haystack) and (_ASSETS_DIR / f"{name}.jpg").exists():
            return f"/assets/covers/{name}.jpg"
    return f"/assets/covers/{occ.intent_category}.jpg"


def _day_bounds(now_ist: datetime) -> dict[str, tuple[datetime, datetime]]:
    start_today = now_ist.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = start_today + timedelta(days=1)
    day_after = tomorrow + timedelta(days=1)
    # Weekend = the coming Saturday 00:00 -> Monday 00:00 (IST).
    days_to_sat = (5 - start_today.weekday()) % 7
    sat = start_today + timedelta(days=days_to_sat)
    if start_today.weekday() == 6:  # Sunday: the weekend is today
        sat = start_today
    mon = sat + timedelta(days=(7 - sat.weekday()) % 7 or 7) if sat.weekday() != 0 else sat + timedelta(days=7)
    return {
        "today": (start_today, tomorrow),
        "tomorrow": (tomorrow, day_after),
        "weekend": (sat, mon),
    }


async def around_you(session: AsyncSession, viewer: ViewerProfile) -> dict:
    """[FR004] Today / Tomorrow / This Weekend / Later — empty groups stay explicit."""
    now_ist = datetime.now(IST)
    bounds = _day_bounds(now_ist)
    horizon = bounds["today"][0] + timedelta(days=21)
    occs = await activity.list_visible(session, city=viewer.city, start=now_ist - timedelta(hours=3), end=horizon)
    cards = await build_cards(session, occs, viewer, exclude_hidden=True)
    groups: dict[str, list[Card]] = {"today": [], "tomorrow": [], "weekend": [], "later": []}
    for c in cards:
        t = c.time_start.astimezone(IST)
        if bounds["today"][0] <= t < bounds["today"][1]:
            groups["today"].append(c)
        elif bounds["tomorrow"][0] <= t < bounds["tomorrow"][1]:
            groups["tomorrow"].append(c)
        elif bounds["weekend"][0] <= t < bounds["weekend"][1]:
            groups["weekend"].append(c)
        else:
            groups["later"].append(c)
    return groups


async def calendar_day(session: AsyncSession, viewer: ViewerProfile, day: datetime) -> list[Card]:
    start = day.astimezone(IST).replace(hour=0, minute=0, second=0, microsecond=0)
    occs = await activity.list_visible(session, city=viewer.city, start=start, end=start + timedelta(days=1))
    return await build_cards(session, occs, viewer, exclude_hidden=True)


async def calendar_range(session: AsyncSession, viewer: ViewerProfile, start: datetime, end: datetime) -> list[Card]:
    occs = await activity.list_visible(session, city=viewer.city, start=start, end=end)
    return await build_cards(session, occs, viewer)


async def search(
    session: AsyncSession,
    viewer: ViewerProfile,
    *,
    query: str | None,
    category: str | None,
    scope: str | None,
    when: str | None,
    distance: str | None,
    high_risk: bool | None,
    free: bool | None = None,
    audience: str | None = None,
    food: str | None = None,
) -> list[Card]:
    """[FR005/FR009] Common filters (date, distance, category, scope) + advanced.
    [FR102/FR110] Free only, who it's for (family, elders, beginners) and food (veg, alcohol-free)."""
    now_ist = datetime.now(IST)
    bounds = _day_bounds(now_ist)
    start, end = now_ist - timedelta(hours=3), bounds["today"][0] + timedelta(days=60)
    if when in bounds:
        start, end = bounds[when]
    elif when == "week":
        start, end = bounds["today"][0], bounds["today"][0] + timedelta(days=7)
    occs = await activity.list_visible(session, city=viewer.city, start=start, end=end, category=category, scope=scope, query=query)
    if high_risk is False:
        occs = [o for o in occs if not o.high_risk]
    if free:
        occs = [o for o in occs if o.price_paise is None]
    if audience:
        occs = [o for o in occs if audience in o.audience_tags]
    if food:
        occs = [o for o in occs if food in o.food_tags]
    cards = await build_cards(session, occs, viewer, exclude_hidden=True)
    if distance == "locality" and viewer.locality:
        cards = [c for c in cards if c.location_label.lower() == viewer.locality.lower()]
    elif distance == "zone" and viewer.zone:
        cards = [
            c
            for c in cards
            if (c.distance_label or "").startswith("Same")
            or viewer.zone.lower() in (c.distance_label or "").lower()
            or c.location_label.lower() == (viewer.locality or "").lower()
        ]
    return cards


async def map_pins(session: AsyncSession, viewer: ViewerProfile) -> list[Card]:
    now_ist = datetime.now(IST)
    occs = await activity.list_visible(session, city=viewer.city, start=now_ist - timedelta(hours=3), end=now_ist + timedelta(days=30))
    cards = await build_cards(session, occs, viewer, exclude_hidden=True)
    return [c for c in cards if c.lat is not None]


# --- TR02: the Dashboard-facing read contract -------------------------------


class MilavnActivityFeedReader:
    """The only public surface another module (Dashboard) may import (TR02)."""

    @staticmethod
    async def get_nearby_activities(session: AsyncSession, *, city: str, limit: int = 10) -> list[dict]:
        occs = await activity.list_visible(session, city=city, start=datetime.now(UTC), end=None, limit=limit)
        return [
            {"id": str(o.id), "title": o.title, "time_start": o.time_start.isoformat(), "locality": o.locality_locality or o.locality_city, "slug": o.canonical_url_slug}
            for o in occs
        ]

    @staticmethod
    async def get_upcoming_for_member(session: AsyncSession, *, member_id: UUID) -> list[dict]:
        mine = await activity.my_participations(session, member_id=member_id)
        out: list[dict] = []
        for occ_id, status in mine.items():
            if status not in ("going", "interested", "waitlisted"):
                continue
            try:
                o = await activity.get(session, occurrence_id=occ_id)
            except activity.OccurrenceNotFound:
                continue
            if o.time_start >= datetime.now(UTC):
                out.append({"id": str(o.id), "title": o.title, "time_start": o.time_start.isoformat(), "status": status, "slug": o.canonical_url_slug})
        return sorted(out, key=lambda x: x["time_start"])

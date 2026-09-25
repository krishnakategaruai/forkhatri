"""Horoscope — public interface (DEC-V1-029).

What families in India actually do before a match goes further: the two
kundlis are compared. Two things are computed here and nothing else:

  * A person's own Moon chart from their birth details (`compute_chart`):
    Moon rashi, nakshatra and pada, the Lagna when time and place are known,
    where Mars sits from the Lagna and from the Moon, and so whether the
    person is manglik. Cached per account in `mangaly_horoscope.chart`, keyed
    by a hash of the inputs, so a change to any birth detail recomputes it
    and nothing else ever does.
  * Ashta Koota (Guna Milan) between two charts (`guna_milan`): the eight
    kootas, 36 points, the traditional reading bands, Nadi and Bhakoot dosha
    with their usual cancellations, and whether the two Mangal doshas cancel.

The 36-point total is the one number Mangaly shows on purpose. It is not a
score of the people or of the match in Mangaly's sense (DEC-V1-002: no
popularity, no trust score, no compatibility percentage): it is the
traditional reading a family would otherwise get from a panchang or a
pandit, and it is never used for ranking, gating or ordering anyone.

Privacy (the rule the API and the SQL functions both enforce):
  * A pair report exists only when BOTH have a chart and at least ONE of
    them answered "Horoscope matching: yes" (`horoscope.matching_required`).
  * The other person's birth time and place are never returned: the report
    carries rashi and nakshatra of both, the koota rows, the total and the
    reading. Before a connection is accepted only the total and the band go
    out; after acceptance (the `candidate_info` grant) the breakdown too.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Literal
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.horoscope import astronomy, places
from app.components.horoscope import tables as T

logger = logging.getLogger(__name__)

__all__ = [
    "Chart",
    "GunaReport",
    "KootaRow",
    "MatchReport",
    "OwnChart",
    "compute_chart",
    "guna_milan",
    "match_report",
    "own_chart",
    "recompute",
]

# Every Indian birth place: IST, UTC+5:30, no daylight saving, so a fixed
# offset is exact and needs no tz database (Windows ships none).
IST = timezone(timedelta(hours=5, minutes=30), "IST")

# Bump when the rules or the astronomy change so cached charts are redone.
_ALGORITHM_VERSION = "2026-09-22.1"

Source = Literal["computed", "stated", "mixed"]
Manglik = Literal["no", "partial", "yes", "unknown"]


# ---------------------------------------------------------------------------
# One person's chart
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class Chart:
    """What is kept per account. Never the birth time or place themselves —
    only what was derived, plus flags saying how sure the derivation is."""

    source: Source
    moon_rashi: str | None = None
    moon_nakshatra: str | None = None
    moon_pada: int | None = None
    moon_longitude: float | None = None
    lagna_rashi: str | None = None
    mars_rashi: str | None = None
    mars_house_from_lagna: int | None = None
    mars_house_from_moon: int | None = None
    manglik: Manglik = "unknown"
    manglik_from_lagna: bool | None = None
    manglik_from_moon: bool | None = None
    manglik_cancelled_by: str | None = None  # 'own_sign' | 'exalted' | None
    approximate: bool = False
    notes: list[str] = field(default_factory=list)  # i18n keys under horoscope.note.*
    has_birth_time: bool = False
    place_matched: str | None = None
    ayanamsa: float | None = None
    algorithm: str = _ALGORITHM_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Chart:
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in known})

    @property
    def complete(self) -> bool:
        return self.moon_rashi is not None and self.moon_nakshatra is not None


_TIME_RE = re.compile(
    r"^\s*(?P<h>\d{1,2})\s*[:.\s]?\s*(?P<m>\d{2})?\s*(?P<ampm>am|pm|a\.m\.|p\.m\.)?\s*$",
    re.IGNORECASE,
)


def parse_birth_time(value: object) -> time | None:
    """'07:15', '7.15 pm', '19:15', '0715', '7 AM' -> time; anything else None."""
    if value is None:
        return None
    text_value = str(value).strip().lower().replace("hrs", "").replace("h", ":")
    match = _TIME_RE.match(text_value)
    if not match:
        return None
    hour = int(match.group("h"))
    minute = int(match.group("m") or 0)
    ampm = (match.group("ampm") or "").replace(".", "")
    if ampm == "pm" and hour < 12:
        hour += 12
    if ampm == "am" and hour == 12:
        hour = 0
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    return time(hour, minute)


def _rashi_of(longitude: float) -> str:
    return T.RASHIS[int(longitude // 30) % 12]


def _nakshatra_of(longitude: float) -> tuple[str, int]:
    span = 360.0 / 27.0
    index = int(longitude // span) % 27
    pada = int((longitude % span) // (span / 4)) + 1
    return T.NAKSHATRAS[index], pada


def _house(from_sign: str, planet_sign: str) -> int:
    return (T.RASHIS.index(planet_sign) - T.RASHIS.index(from_sign)) % 12 + 1


def canonical_nakshatra(value: object) -> str | None:
    if value is None:
        return None
    key = re.sub(r"[^a-z]", "", str(value).lower())
    return T.NAKSHATRA_ALIASES.get(key)


def canonical_rashi(value: object) -> str | None:
    if value is None:
        return None
    key = re.sub(r"[^a-z]", "", str(value).lower())
    aliases = {
        "aries": "mesh",
        "mesha": "mesh",
        "taurus": "vrishabh",
        "vrishabha": "vrishabh",
        "vrushabh": "vrishabh",
        "gemini": "mithun",
        "mithuna": "mithun",
        "cancer": "kark",
        "karka": "kark",
        "karkata": "kark",
        "leo": "simha",
        "virgo": "kanya",
        "libra": "tula",
        "thula": "tula",
        "scorpio": "vrishchik",
        "vrishchika": "vrishchik",
        "vrischika": "vrishchik",
        "sagittarius": "dhanu",
        "dhanus": "dhanu",
        "capricorn": "makar",
        "makara": "makar",
        "aquarius": "kumbh",
        "kumbha": "kumbh",
        "pisces": "meen",
        "meena": "meen",
    }
    if key in T.RASHIS:
        return key
    return aliases.get(key)


def compute_chart(
    dob: date,
    birth_time: object | None,
    birth_place: object | None,
    *,
    stated_rashi: object | None = None,
    stated_nakshatra: object | None = None,
    stated_manglik: object | None = None,
) -> Chart:
    """The chart for one person.

    * Birth time known: everything is computed from the sky at that moment
      (IST; every Indian birth place is in one time zone). With a known place
      the Lagna is computed too, and Mars is read from both Lagna and Moon.
    * No birth time but a stated rashi/nakshatra: the person's own values are
      used (`source='stated'`), the Moon-based Mars reading is computed from
      the noon Moon only if it agrees with the stated rashi.
    * Nothing but the date: the Moon at noon IST, flagged approximate - the
      Moon moves about 13 deg a day, so the nakshatra (and, one day in
      thirteen, the rashi) may be the neighbouring one.
    """
    parsed_time = parse_birth_time(birth_time)
    place = places.lookup(str(birth_place)) if birth_place else None
    rashi_stated = canonical_rashi(stated_rashi)
    nakshatra_stated = canonical_nakshatra(stated_nakshatra)
    manglik_stated = str(stated_manglik).strip().lower() if stated_manglik else None

    chart = Chart(source="computed", has_birth_time=parsed_time is not None)
    moment = datetime.combine(dob, parsed_time or time(12, 0), tzinfo=IST)
    try:
        pos = astronomy.positions_at(
            moment,
            place.lat if (place and parsed_time) else None,
            place.lon if (place and parsed_time) else None,
        )
    except astronomy.EphemerisRange:
        pos = None
        chart.notes.append("outside_ephemeris")

    if pos is not None:
        chart.ayanamsa = round(pos.ayanamsa, 6)
        chart.moon_longitude = round(pos.moon, 4)
        chart.mars_rashi = _rashi_of(pos.mars)
        computed_rashi = _rashi_of(pos.moon)
        computed_nakshatra, computed_pada = _nakshatra_of(pos.moon)
        if parsed_time is None and (rashi_stated or nakshatra_stated):
            # The person told us; a noon guess must not overrule them.
            chart.source = "stated"
            chart.moon_rashi = rashi_stated or computed_rashi
            chart.moon_nakshatra = nakshatra_stated
            chart.moon_pada = None
            chart.notes.append("stated_values")
            if chart.moon_nakshatra is None:
                chart.notes.append("nakshatra_missing")
        else:
            chart.moon_rashi = computed_rashi
            chart.moon_nakshatra = computed_nakshatra
            chart.moon_pada = computed_pada
            if parsed_time is None:
                chart.approximate = True
                chart.notes.append("no_birth_time")
        if pos.lagna is not None:
            chart.lagna_rashi = _rashi_of(pos.lagna)
            chart.place_matched = place.name if place else None
        elif parsed_time is not None:
            chart.notes.append("unknown_place" if birth_place else "no_birth_place")
    else:
        chart.source = "stated" if (rashi_stated or nakshatra_stated) else "computed"
        chart.moon_rashi = rashi_stated
        chart.moon_nakshatra = nakshatra_stated

    if parsed_time is None and rashi_stated is None and nakshatra_stated is None:
        pass
    elif parsed_time is not None and (rashi_stated or nakshatra_stated):
        if (rashi_stated and rashi_stated != chart.moon_rashi) or (
            nakshatra_stated and nakshatra_stated != chart.moon_nakshatra
        ):
            chart.source = "mixed"
            chart.notes.append("stated_differs")

    _read_mangal_dosha(chart, manglik_stated)
    return chart


def _read_mangal_dosha(chart: Chart, manglik_stated: str | None) -> None:
    if chart.mars_rashi and chart.moon_rashi and chart.source != "stated":
        chart.mars_house_from_moon = _house(chart.moon_rashi, chart.mars_rashi)
        chart.manglik_from_moon = chart.mars_house_from_moon in T.MANGLIK_HOUSES
    if chart.mars_rashi and chart.lagna_rashi:
        chart.mars_house_from_lagna = _house(chart.lagna_rashi, chart.mars_rashi)
        chart.manglik_from_lagna = chart.mars_house_from_lagna in T.MANGLIK_HOUSES

    if chart.manglik_from_moon is None and chart.manglik_from_lagna is None:
        # Nothing computed: fall back to what the person said, if anything.
        if manglik_stated in ("yes", "no", "partial"):
            chart.manglik = manglik_stated  # type: ignore[assignment]
            chart.notes.append("manglik_stated")
        return

    if chart.mars_rashi in T.MARS_OWN_SIGNS:
        chart.manglik_cancelled_by = "own_sign"
    elif chart.mars_rashi == T.MARS_EXALTED_SIGN:
        chart.manglik_cancelled_by = "exalted"

    flags = [f for f in (chart.manglik_from_lagna, chart.manglik_from_moon) if f is not None]
    if chart.manglik_cancelled_by:
        chart.manglik = "no"
    elif all(flags) and len(flags) == 2:
        chart.manglik = "yes"
    elif any(flags):
        chart.manglik = "partial"
        if len(flags) == 1:
            chart.notes.append("lagna_unavailable")
    else:
        chart.manglik = "no"
        if len(flags) == 1:
            chart.notes.append("lagna_unavailable")


# ---------------------------------------------------------------------------
# Ashta Koota
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class KootaRow:
    key: str  # varna | vashya | tara | yoni | graha_maitri | gana | bhakoot | nadi
    points: float
    max: int
    reason: str  # i18n key under horoscope.reason.*
    reason_params: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class GunaReport:
    rows: list[KootaRow]
    total: float
    band: str  # excellent | very_good | acceptable | not_recommended
    nadi_dosha: bool
    nadi_cancelled: str | None
    bhakoot_dosha: bool
    bhakoot_cancelled: str | None
    manglik_note: str  # i18n key under horoscope.manglik_note.*
    manglik_compatible: bool | None


def _tara_direction(from_nak: str, to_nak: str) -> tuple[int, bool]:
    count = (T.NAKSHATRAS.index(to_nak) - T.NAKSHATRAS.index(from_nak)) % 27 + 1
    tara = count % 9 or 9
    return tara, tara not in T.TARA_BAD


def guna_milan(bride: Chart, groom: Chart) -> GunaReport:
    """The eight kootas between a bride's and a groom's Moon chart. Both
    charts must be `complete` (rashi and nakshatra known)."""
    if not (bride.complete and groom.complete):
        raise ValueError("both charts need a Moon rashi and nakshatra")
    b_r, g_r = bride.moon_rashi, groom.moon_rashi
    b_n, g_n = bride.moon_nakshatra, groom.moon_nakshatra
    assert b_r and g_r and b_n and g_n
    b_i, g_i = T.NAKSHATRAS.index(b_n), T.NAKSHATRAS.index(g_n)
    rows: list[KootaRow] = []

    # 1. Varna (1)
    bv, gv = T.VARNA[b_r], T.VARNA[g_r]
    varna_ok = T.VARNA_RANK[gv] >= T.VARNA_RANK[bv]
    rows.append(
        KootaRow(
            "varna",
            1 if varna_ok else 0,
            1,
            "varna_ok" if varna_ok else "varna_low",
            {"bride": bv, "groom": gv},
        )
    )

    # 2. Vashya (2)
    bva, gva = T.VASHYA[b_r], T.VASHYA[g_r]
    vashya = T.vashya_points(bva, gva)
    rows.append(
        KootaRow(
            "vashya",
            vashya,
            2,
            "vashya_same" if bva == gva else ("vashya_good" if vashya >= 1 else "vashya_poor"),
            {"bride": bva, "groom": gva},
        )
    )

    # 3. Tara (3): 1.5 for each auspicious direction.
    t1, ok1 = _tara_direction(b_n, g_n)
    t2, ok2 = _tara_direction(g_n, b_n)
    tara = (1.5 if ok1 else 0) + (1.5 if ok2 else 0)
    rows.append(
        KootaRow(
            "tara",
            tara,
            3,
            "tara_both" if tara == 3 else ("tara_one" if tara == 1.5 else "tara_none"),
            {"from_bride": T.TARA_NAMES[t1 - 1], "from_groom": T.TARA_NAMES[t2 - 1]},
        )
    )

    # 4. Yoni (4)
    by, gy = T.YONI[b_i], T.YONI[g_i]
    yoni = T.yoni_points(by, gy)
    rows.append(
        KootaRow(
            "yoni",
            yoni,
            4,
            {4: "yoni_same", 3: "yoni_friendly", 2: "yoni_neutral", 1: "yoni_unfriendly"}.get(
                yoni, "yoni_enemy"
            ),
            {"bride": by, "groom": gy},
        )
    )

    # 5. Graha Maitri (5): friendship of the two Moon-sign lords.
    bl, gl = T.RASHI_LORD[b_r], T.RASHI_LORD[g_r]
    r1, r2 = T.relation(bl, gl), T.relation(gl, bl)
    if bl == gl:
        maitri, maitri_reason = 5.0, "maitri_same"
    else:
        pair = {r1, r2}
        if pair == {"friend"}:
            maitri, maitri_reason = 5.0, "maitri_friends"
        elif pair == {"friend", "neutral"}:
            maitri, maitri_reason = 4.0, "maitri_friend_neutral"
        elif pair == {"neutral"}:
            maitri, maitri_reason = 3.0, "maitri_neutral"
        elif pair == {"friend", "enemy"}:
            maitri, maitri_reason = 1.0, "maitri_friend_enemy"
        elif pair == {"neutral", "enemy"}:
            maitri, maitri_reason = 0.5, "maitri_neutral_enemy"
        else:
            maitri, maitri_reason = 0.0, "maitri_enemies"
    rows.append(KootaRow("graha_maitri", maitri, 5, maitri_reason, {"bride": bl, "groom": gl}))

    # 6. Gana (6)
    bg, gg = T.GANA[b_i], T.GANA[g_i]
    gana = T.GANA_POINTS[(bg, gg)]
    rows.append(
        KootaRow(
            "gana",
            gana,
            6,
            "gana_same" if bg == gg else ("gana_ok" if gana >= 5 else "gana_clash"),
            {"bride": bg, "groom": gg},
        )
    )

    # 7. Bhakoot (7): the rashi distance counted both ways.
    d1 = (T.RASHIS.index(g_r) - T.RASHIS.index(b_r)) % 12 + 1
    d2 = (T.RASHIS.index(b_r) - T.RASHIS.index(g_r)) % 12 + 1
    bhakoot_dosha = frozenset({d1, d2}) in T.BHAKOOT_DOSHA_PAIRS
    bhakoot_cancelled: str | None = None
    if bhakoot_dosha:
        if bl == gl:
            bhakoot_cancelled = "same_lord"
        elif T.relation(bl, gl) == "friend" and T.relation(gl, bl) == "friend":
            bhakoot_cancelled = "friendly_lords"
    bhakoot = 7 if (not bhakoot_dosha or bhakoot_cancelled) else 0
    rows.append(
        KootaRow(
            "bhakoot",
            bhakoot,
            7,
            "bhakoot_ok"
            if not bhakoot_dosha
            else ("bhakoot_cancelled" if bhakoot_cancelled else "bhakoot_dosha"),
            {"distance": f"{min(d1, d2)}-{max(d1, d2)}"},
        )
    )

    # 8. Nadi (8)
    bn, gn = T.NADI[b_i], T.NADI[g_i]
    nadi_dosha = bn == gn
    nadi_cancelled: str | None = None
    if nadi_dosha:
        if b_n == g_n and bride.moon_pada and groom.moon_pada and bride.moon_pada != groom.moon_pada:
            nadi_cancelled = "same_nakshatra_different_pada"
        elif b_r == g_r and b_n != g_n:
            nadi_cancelled = "same_rashi_different_nakshatra"
        elif b_n == g_n and b_r != g_r:
            nadi_cancelled = "same_nakshatra_different_rashi"
    nadi = 8 if (not nadi_dosha or nadi_cancelled) else 0
    rows.append(
        KootaRow(
            "nadi",
            nadi,
            8,
            "nadi_ok" if not nadi_dosha else ("nadi_cancelled" if nadi_cancelled else "nadi_dosha"),
            {"bride": bn, "groom": gn},
        )
    )

    total = sum(r.points for r in rows)

    # Mangal dosha compatibility.
    b_m, g_m = bride.manglik, groom.manglik
    if b_m == "unknown" or g_m == "unknown":
        manglik_note, compatible = "unknown", None
    elif b_m == "no" and g_m == "no":
        manglik_note, compatible = "neither", True
    elif b_m != "no" and g_m != "no":
        manglik_note, compatible = "both", True
    elif (b_m == "partial") != (g_m == "partial") and "yes" not in (b_m, g_m):
        manglik_note, compatible = "one_partial", True
    else:
        manglik_note, compatible = "one_only", False

    return GunaReport(
        rows=rows,
        total=total,
        band=T.band_for(total),
        nadi_dosha=nadi_dosha,
        nadi_cancelled=nadi_cancelled,
        bhakoot_dosha=bhakoot_dosha,
        bhakoot_cancelled=bhakoot_cancelled,
        manglik_note=manglik_note,
        manglik_compatible=compatible,
    )


# ---------------------------------------------------------------------------
# Storage: the cached chart per account (migration 049)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _Inputs:
    dob: date
    gender: str
    birth_time: str | None
    birth_place: str | None
    rashi: str | None
    nakshatra: str | None
    manglik: str | None
    matching_required: bool

    @property
    def hash(self) -> str:
        payload = json.dumps(
            [
                _ALGORITHM_VERSION,
                self.dob.isoformat(),
                self.birth_time,
                self.birth_place,
                self.rashi,
                self.nakshatra,
                self.manglik,
            ],
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _json_text(value: object) -> str | None:
    """`profile_attribute.value` is jsonb: a string comes back as a str, but
    anything else (a number, a list) is not a birth detail."""
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, (int, float)):
        return str(value)
    return None


def _matching_required(value: object) -> bool:
    if value is True:
        return True
    return isinstance(value, str) and value.strip().lower() in ("yes", "true", "required")


async def _birth_inputs(session: AsyncSession, account_id: UUID) -> _Inputs | None:
    row = (
        await session.execute(
            text("SELECT * FROM mangaly_horoscope.birth_inputs(:account_id)"),
            {"account_id": account_id},
        )
    ).first()
    if row is None or row.dob is None:
        return None
    return _Inputs(
        dob=row.dob,
        gender=row.gender,
        birth_time=_json_text(row.birth_time),
        birth_place=_json_text(row.birth_place),
        rashi=_json_text(row.rashi),
        nakshatra=_json_text(row.nakshatra),
        manglik=_json_text(row.manglik),
        matching_required=_matching_required(row.matching_required),
    )


@dataclass(frozen=True, slots=True)
class OwnChart:
    chart: Chart
    matching_required: bool
    computed_at: datetime


@dataclass(frozen=True, slots=True)
class _StoredChart:
    account_id: UUID
    chart: Chart
    inputs_hash: str
    matching_required: bool
    gender: str
    connected: bool
    computed_at: datetime


async def _pair_rows(
    session: AsyncSession, viewer_account_id: UUID, other_account_id: UUID
) -> dict[UUID, _StoredChart]:
    rows = await session.execute(
        text("SELECT * FROM mangaly_horoscope.pair_charts(:viewer, :other)"),
        {"viewer": viewer_account_id, "other": other_account_id},
    )
    out: dict[UUID, _StoredChart] = {}
    for row in rows:
        chart_data = row.chart if isinstance(row.chart, dict) else json.loads(row.chart)
        out[row.account_id] = _StoredChart(
            account_id=row.account_id,
            chart=Chart.from_dict(chart_data),
            inputs_hash=row.inputs_hash,
            matching_required=bool(row.matching_required),
            gender=row.gender,
            connected=bool(row.connected),
            computed_at=row.computed_at,
        )
    return out


async def _save(session: AsyncSession, account_id: UUID, inputs: _Inputs, chart: Chart) -> None:
    await session.execute(
        text(
            "SELECT mangaly_horoscope.save_chart(:account_id, :inputs_hash, "
            "CAST(:chart AS jsonb), :matching_required)"
        ),
        {
            "account_id": account_id,
            "inputs_hash": inputs.hash,
            "chart": json.dumps(chart.to_dict()),
            "matching_required": inputs.matching_required,
        },
    )


async def _ensure_fresh(
    session: AsyncSession, account_id: UUID, stored: _StoredChart | None
) -> tuple[Chart, bool] | None:
    """The chart for `account_id`, recomputed if the birth details changed
    since it was stored. None when the person has no profile."""
    inputs = await _birth_inputs(session, account_id)
    if inputs is None:
        return None
    if stored is not None and stored.inputs_hash == inputs.hash:
        return stored.chart, inputs.matching_required
    chart = compute_chart(
        inputs.dob,
        inputs.birth_time,
        inputs.birth_place,
        stated_rashi=inputs.rashi,
        stated_nakshatra=inputs.nakshatra,
        stated_manglik=inputs.manglik,
    )
    await _save(session, account_id, inputs, chart)
    return chart, inputs.matching_required


async def recompute(session: AsyncSession, *, account_id: UUID) -> Chart | None:
    """Recompute and store the account's chart from its current birth
    details. Called after a horoscope-category or profile write; never
    raises into the caller's transaction (a chart is a derived convenience,
    the profile write is the thing that must succeed)."""
    try:
        inputs = await _birth_inputs(session, account_id)
        if inputs is None:
            return None
        chart = compute_chart(
            inputs.dob,
            inputs.birth_time,
            inputs.birth_place,
            stated_rashi=inputs.rashi,
            stated_nakshatra=inputs.nakshatra,
            stated_manglik=inputs.manglik,
        )
        await _save(session, account_id, inputs, chart)
        return chart
    except Exception:  # noqa: BLE001 - see docstring
        logger.exception("horoscope chart recompute failed for %s", account_id)
        return None


async def own_chart(session: AsyncSession, *, account_id: UUID) -> OwnChart | None:
    """The caller's own chart, computed on first read and whenever the birth
    details changed. None when there is no candidate profile."""
    stored = (await _pair_rows(session, account_id, account_id)).get(account_id)
    fresh = await _ensure_fresh(session, account_id, stored)
    if fresh is None:
        return None
    chart, matching_required = fresh
    computed_at = (
        stored.computed_at
        if stored is not None and stored.chart == chart
        else datetime.now(tz=IST)
    )
    return OwnChart(chart=chart, matching_required=matching_required, computed_at=computed_at)


# ---------------------------------------------------------------------------
# A pair
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class MatchReport:
    report: GunaReport
    detailed: bool  # False before the connection is accepted: total + band only
    mine: Chart
    theirs: Chart
    bride_is_me: bool


async def match_report(
    session: AsyncSession, *, viewer_account_id: UUID, other_account_id: UUID
) -> MatchReport | None:
    """The Guna Milan between `viewer_account_id` (the candidate whose match
    this is - a parent passes their child's account after
    `authz.resolve_context_account`) and `other_account_id`. None whenever
    the privacy rule says there is nothing to show: either has no complete
    chart, or neither asked for horoscope matching."""
    if viewer_account_id == other_account_id:
        return None
    rows = await _pair_rows(session, viewer_account_id, other_account_id)
    mine = await _ensure_fresh(session, viewer_account_id, rows.get(viewer_account_id))
    theirs = await _ensure_fresh(session, other_account_id, rows.get(other_account_id))
    if mine is None or theirs is None:
        return None
    my_chart, my_required = mine
    their_chart, their_required = theirs
    if not (my_required or their_required):
        return None
    if not (my_chart.complete and their_chart.complete):
        return None

    my_gender = rows[viewer_account_id].gender if viewer_account_id in rows else None
    their_gender = rows[other_account_id].gender if other_account_id in rows else None
    if my_gender is None or their_gender is None:
        # Genders come with the stored rows; after a first-time save they are
        # not in `rows` yet, so read them back.
        rows = await _pair_rows(session, viewer_account_id, other_account_id)
        my_gender = rows[viewer_account_id].gender
        their_gender = rows[other_account_id].gender
    bride_is_me = my_gender == "female" or their_gender == "male"
    bride, groom = (my_chart, their_chart) if bride_is_me else (their_chart, my_chart)
    report = guna_milan(bride, groom)
    connected = rows[other_account_id].connected if other_account_id in rows else False
    return MatchReport(
        report=report,
        detailed=connected,
        mine=my_chart,
        theirs=their_chart,
        bride_is_me=bride_is_me,
    )

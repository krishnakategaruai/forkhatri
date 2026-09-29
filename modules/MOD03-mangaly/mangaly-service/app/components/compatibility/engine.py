"""The AI matching engine: a 1–10 score for a pair, from both sides' words,
facts and 1–10 scales (DEC-V1-031).

Pure functions over two `ranking_input_snapshot` dicts — no database, no
network — so Discover can score every candidate row in one pass and the
same numbers are testable without a server.

How a pair is scored:
  1. What the seeker wants (`wishes`): the items understood from their own
     words, each with an importance 1–10. People who have not used the
     matchmaker yet still have wishes: their older partner-preference fields
     are read as items of default importance, so nobody's stated preferences
     stop counting.
  2. One direction (`direction_fit`): an importance-weighted average of how
     well the other person meets each wish, how close their self-ratings are
     to the wanted scale values, and two implicit terms (a shared kitchen,
     distance) that matter even unstated. A wish the other person has no
     fact for is skipped, never counted against them.
  3. Both directions, combined by harmonic mean (DEC-V1-030): a one-way fit
     never passes as a mutual one. Profile evidence breaks near-ties.
  4. `fails_must`: any importance-10 wish the other person's facts clearly
     do not meet removes them. A blank fact never removes anyone — unlike a
     Hinge dealbreaker, which also hides everyone who left the field empty.

Nothing here reads who viewed, liked or messaged whom (DEC-V1-002).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from typing import Any

from app.config import matching_engine as cfg

__all__ = [
    "Wish",
    "common_points",
    "priorities",
    "direction_fit",
    "distance_km",
    "fails_must",
    "label_for",
    "pair_score",
    "wishes",
]


@dataclass(frozen=True, slots=True)
class Wish:
    field: str
    importance: int
    values: tuple[str, ...] = ()
    min: float | None = None
    max: float | None = None
    # For "locality" wishes: coordinates of each wanted place, when known.
    geo: tuple[tuple[float, float], ...] = ()


def _lower(value: Any) -> str:
    return str(value or "").strip().lower()


def _int(value: Any) -> int | None:
    try:
        return int(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _age(date_of_birth: Any) -> int | None:
    if not date_of_birth:
        return None
    try:
        born = date.fromisoformat(str(date_of_birth)[:10])
    except ValueError:
        return None
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def _geo(snapshot: dict) -> tuple[float, float] | None:
    g = snapshot.get("geo")
    if isinstance(g, dict) and g.get("lat") is not None and g.get("lon") is not None:
        return float(g["lat"]), float(g["lon"])
    return None


def distance_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Great-circle distance (haversine). A few hundred rows per search, so
    no geohash index is needed at this scale."""
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def _distance_fit(km: float) -> float:
    if km <= cfg.DISTANCE_FULL_KM:
        return 1.0
    return math.exp(-(((km - cfg.DISTANCE_FULL_KM) / cfg.DISTANCE_SCALE_KM) ** 2))


def _would_relocate(snapshot: dict) -> bool:
    return snapshot.get("relocation_willingness") in ("yes", "open_to_discussion")


def _places(value: Any) -> list[str]:
    items = value if isinstance(value, list) else [value]
    out: list[str] = []
    for item in items:
        spelled = str(item or "").lower().replace("/", ",").replace(" or ", ",")
        out += [p.strip() for p in spelled.split(",") if p.strip()]
    return out


def wishes(snapshot: dict) -> list[Wish]:
    """The seeker's wishes: the understood items when they used the
    matchmaker, else their older partner-preference fields — plus a "like
    us" wish for each theme they said matters (`priority_wishes`)."""
    stated = _stated_wishes(snapshot)
    covered = {w.field for w in stated}
    return stated + [w for w in priority_wishes(snapshot) if w.field not in covered]


def priorities(snapshot: dict) -> dict[str, int]:
    """[Owner, 2026-09-28] {theme: 1–10} the family gave at setup; unset
    themes are absent."""
    raw = snapshot.get("priorities")
    if not isinstance(raw, dict):
        return {}
    out: dict[str, int] = {}
    for theme, value in raw.items():
        n = _int(value)
        if theme in cfg.PRIORITY_THEMES and n is not None and n >= cfg.SCALE_MIN:
            out[theme] = min(cfg.SCALE_MAX, n)
    return out


def priority_wishes(snapshot: dict) -> list[Wish]:
    """Each theme that matters, as wishes built from the seeker's own facts:
    "same roots" means their own mother tongue and community. A fact the
    seeker never gave makes no wish (nothing is guessed)."""
    out: list[Wish] = []
    for theme, importance in priorities(snapshot).items():
        for field in cfg.PRIORITY_THEMES[theme]:
            own = _fact(field, snapshot)
            if own in (None, "", []):
                continue
            if field == "locality":
                city = str(own).split(",")[0].strip()
                here = _geo(snapshot)
                out.append(Wish(field, importance, values=(city,), geo=(here,) if here else ()))
            elif field == "hobbies":
                out.append(Wish(field, importance, values=tuple(str(h) for h in own)))
            elif field == "education" and _lower(own) not in cfg.EDUCATION_LEVELS:
                continue  # a level outside the ordered list cannot be a floor
            elif field == "diet" and _lower(own) not in cfg.DIET_COMPAT:
                continue
            else:
                out.append(Wish(field, importance, values=(_lower(own),)))
    return out


def _stated_wishes(snapshot: dict) -> list[Wish]:
    brief = snapshot.get("partner_brief")
    if isinstance(brief, list) and brief:
        out: list[Wish] = []
        for item in brief:
            if not isinstance(item, dict) or item.get("field") not in cfg.ITEM_FIELDS:
                continue
            geo = tuple(
                (float(g["lat"]), float(g["lon"]))
                for g in (item.get("geo") or [])
                if isinstance(g, dict) and g.get("lat") is not None and g.get("lon") is not None
            )
            out.append(
                Wish(
                    field=str(item["field"]),
                    importance=max(1, min(10, _int(item.get("importance")) or cfg.DEFAULT_IMPORTANCE)),
                    values=tuple(str(v) for v in (item.get("values") or []) if str(v).strip()),
                    min=item.get("min"),
                    max=item.get("max"),
                    geo=geo,
                )
            )
        return out

    legacy: list[Wish] = []
    age = snapshot.get("partner_age_range")
    if isinstance(age, dict) and (age.get("min") or age.get("max")):
        legacy.append(Wish("age", cfg.DEFAULT_IMPORTANCE, min=age.get("min"), max=age.get("max")))
    height = snapshot.get("partner_height_range")
    if isinstance(height, dict) and (height.get("min") or height.get("max")):
        legacy.append(Wish("height_cm", cfg.DEFAULT_IMPORTANCE, min=height.get("min"), max=height.get("max")))
    if snapshot.get("partner_locality"):
        legacy.append(Wish("locality", cfg.DEFAULT_IMPORTANCE, values=tuple(_places(snapshot["partner_locality"]))))
    for field, key in (("education", "partner_education"), ("diet", "partner_diet")):
        wanted = snapshot.get(key)
        values = tuple(_lower(v) for v in (wanted if isinstance(wanted, list) else [wanted]) if v)
        if values:
            legacy.append(Wish(field, cfg.DEFAULT_IMPORTANCE, values=values))
    return legacy


def _range_fit(value: float, low: Any, high: Any, per_unit: float) -> float:
    lo = float(low) if low not in (None, "", 0) else -math.inf
    hi = float(high) if high not in (None, "", 0) else math.inf
    if lo <= value <= hi:
        return 1.0
    off = (lo - value) if value < lo else (value - hi)
    return max(0.0, 1.0 - off * per_unit)


def _fact(field: str, other: dict) -> Any:
    return {
        "age": _age(other.get("date_of_birth")),
        "height_cm": _int(other.get("height_cm")),
        "locality": other.get("locality"),
        "relocation": other.get("relocation_willingness"),
        "diet": other.get("lifestyle_diet"),
        "smoking": other.get("smoking"),
        "drinking": other.get("drinking"),
        "education": other.get("education_level"),
        "income_band": other.get("income_band"),
        "mother_tongue": other.get("mother_tongue"),
        "sub_community": other.get("sub_community"),
        "family_type": other.get("family_type"),
        "family_values": other.get("family_values"),
        "manglik": other.get("manglik"),
        "hobbies": other.get("hobbies") or None,
    }.get(field)


def item_fit(wish: Wish, other: dict) -> float | None:
    """0–1 for how well `other` meets one wish; None when they have no fact
    for it (skipped — a blank never counts against anyone)."""
    fact = _fact(wish.field, other)
    if fact in (None, "", []):
        return None
    if wish.field == "age":
        return _range_fit(float(fact), wish.min, wish.max, per_unit=0.25)
    if wish.field == "height_cm":
        return _range_fit(float(fact), wish.min, wish.max, per_unit=0.125)
    if wish.field == "locality":
        where = _lower(fact)
        if any(p and p in where for p in (_lower(v) for v in wish.values)):
            return 1.0
        near = 0.0
        mine = _geo(other)
        if mine and wish.geo:
            near = max(_distance_fit(distance_km(mine, g)) for g in wish.geo)
        if _would_relocate(other):
            near = max(near, cfg.RELOCATION_FLOOR)
        return near
    if wish.field == "hobbies":
        theirs = {_lower(h) for h in fact} if isinstance(fact, list) else {_lower(fact)}
        shared = theirs & {_lower(v) for v in wish.values}
        return min(1.0, 0.5 + 0.25 * len(shared)) if shared else 0.0

    value = _lower(fact)
    wanted = [_lower(v) for v in wish.values]
    if not wanted:
        return None
    if value in wanted:
        return 1.0
    if wish.field in cfg.ORDERED_FLOOR:
        order = cfg.ORDERED_FLOOR[wish.field]
        ranks = [order.index(v) for v in wanted if v in order]
        if value in order and ranks:
            gap = min(ranks) - order.index(value)
            return 1.0 if gap <= 0 else (0.4 if gap == 1 else 0.0)
        return 0.0
    if wish.field in cfg.ORDERED_CEILING:
        order = cfg.ORDERED_CEILING[wish.field]
        ranks = [order.index(v) for v in wanted if v in order]
        if value in order and ranks:
            gap = order.index(value) - max(ranks)
            return 1.0 if gap <= 0 else (0.3 if gap == 1 else 0.0)
        return 0.0
    if wish.field == "diet":
        return max(cfg.DIET_COMPAT.get(w, {}).get(value, 0.0) for w in wanted)
    if wish.field == "family_values":
        return max(
            cfg.FAMILY_VALUES_COMPAT.get((w, value), cfg.FAMILY_VALUES_COMPAT.get((value, w), 0.0))
            for w in wanted
        )
    return 0.0


def _meets_must(wish: Wish, other: dict, fit: float) -> bool:
    """An importance-10 wish is strict: only a full fit keeps someone, with
    one allowance — a person who will relocate meets a "must live in" wish."""
    if fit >= 1.0:
        return True
    return wish.field == "locality" and _would_relocate(other)


def fails_must(seeker: dict, other: dict) -> bool:
    for wish in wishes(seeker):
        if wish.importance < cfg.MUST_HAVE:
            continue
        fit = item_fit(wish, other)
        if fit is not None and not _meets_must(wish, other, fit):
            return True
    return False


def direction_fit(seeker: dict, other: dict) -> float:
    """How well `other` fits what `seeker` wants, 0–1, shrunk toward
    NEUTRAL_FIT by PRIOR_WEIGHT: exactly neutral when nothing could be checked
    (browse mode, or nobody said anything), and closer to the evidence the
    more importance was actually checked."""
    total = weight = 0.0
    fields: set[str] = set()
    for wish in wishes(seeker):
        fit = item_fit(wish, other)
        fields.add(wish.field)
        if fit is None:
            continue
        total += wish.importance * fit
        weight += wish.importance

    wanted_scales = seeker.get("partner_scales") or {}
    their_scales = other.get("self_scales") or {}
    for dim in cfg.SCALES:
        want = wanted_scales.get(dim) if isinstance(wanted_scales, dict) else None
        own = _int(their_scales.get(dim)) if isinstance(their_scales, dict) else None
        if not isinstance(want, dict) or own is None or _int(want.get("want")) is None:
            continue
        importance = max(1, min(10, _int(want.get("importance")) or cfg.DEFAULT_IMPORTANCE))
        closeness = 1.0 - abs(_int(want["want"]) - own) / (cfg.SCALE_MAX - cfg.SCALE_MIN)
        total += importance * closeness
        weight += importance

    my_diet, their_diet = _lower(seeker.get("lifestyle_diet")), _lower(other.get("lifestyle_diet"))
    if "diet" not in fields and my_diet in cfg.DIET_COMPAT and their_diet:
        total += cfg.IMPLICIT_DIET_IMPORTANCE * cfg.DIET_COMPAT[my_diet].get(their_diet, 0.5)
        weight += cfg.IMPLICIT_DIET_IMPORTANCE

    here, there = _geo(seeker), _geo(other)
    if "locality" not in fields and here and there:
        near = _distance_fit(distance_km(here, there))
        if _would_relocate(other) or _would_relocate(seeker):
            near = max(near, cfg.RELOCATION_FLOOR)
        total += cfg.IMPLICIT_DISTANCE_IMPORTANCE * near
        weight += cfg.IMPLICIT_DISTANCE_IMPORTANCE

    return (total + cfg.PRIOR_WEIGHT * cfg.NEUTRAL_FIT) / (weight + cfg.PRIOR_WEIGHT)


def pair_score(seeker: dict, other: dict) -> float:
    """1–10 for the pair. Internal only: it orders Discover and chooses the
    word a member sees; the number itself is never shown (DEC-V1-031)."""
    forward = direction_fit(seeker, other)
    reverse = direction_fit(other, seeker)
    mutual = 0.0 if forward + reverse == 0 else 2 * forward * reverse / (forward + reverse)
    evidence = float(other.get("evidence_completeness") or 0.0)
    blended = cfg.PAIR_WEIGHT * mutual + cfg.EVIDENCE_WEIGHT * evidence
    return round(cfg.SCALE_MIN + (cfg.SCALE_MAX - cfg.SCALE_MIN) * blended, 2)


def label_for(score: float) -> str | None:
    """The word a member sees, or nothing. Never a "weak match": the product
    does not judge a person (baseline §3)."""
    if score >= cfg.LABEL_STRONG:
        return "strong"
    if score >= cfg.LABEL_GOOD:
        return "good"
    return None


def breakdown(seeker: dict, other: dict) -> dict[str, Any]:
    """[DEC-V1-031] "How you fit each other", for the profile page.

    `yours`: each of the seeker's own wishes with how the other person meets
    it — met / close / differs / unknown (they did not say). The seeker's own
    wishes are theirs to see in full. `theirs_met`: only the TOPICS of the
    other person's wishes the seeker meets. Their values, their misses and
    how many wishes they have stay private (partner preferences are never
    shown, FR020), so nothing here can be read back into their list. No
    count, no fraction, no number (baseline §3)."""
    yours: list[dict[str, Any]] = []
    for wish in wishes(seeker):
        fit = item_fit(wish, other)
        status = "unknown" if fit is None else "met" if fit >= 1.0 else "close" if fit >= 0.5 else "differs"
        yours.append(
            {
                "field": wish.field,
                "values": list(wish.values),
                "min": wish.min,
                "max": wish.max,
                "must": wish.importance >= cfg.MUST_HAVE,
                "importance": wish.importance,
                "status": status,
            }
        )
    order = {"met": 0, "close": 1, "differs": 2, "unknown": 3}
    yours.sort(key=lambda y: (order[y["status"]], -y["importance"]))
    theirs_met = [
        wish.field
        for wish in sorted(wishes(other), key=lambda w: -w.importance)
        if (fit := item_fit(wish, seeker)) is not None and fit >= 1.0
    ]
    return {"yours": yours, "theirs_met": theirs_met}


def common_points(seeker: dict, other: dict) -> list[dict[str, Any]]:
    """[Owner, 2026-09-28] The generic "points of match" for a reader who
    has not said what they want yet: facts both people share, strongest
    first, as `{"key": ..., **params}` for `discovery.shelf.reason`. Only
    biodata a searchable profile already shows; no count, no number."""
    out: list[dict[str, Any]] = []

    def same(field: str) -> Any:
        a, b = _fact(field, seeker), _fact(field, other)
        return b if a and b and _lower(a) == _lower(b) else None

    mine = {_lower(h): h for h in (seeker.get("hobbies") or [])}
    shared = [h for h in (other.get("hobbies") or []) if _lower(h) in mine]
    if shared:
        out.append({"key": "sharedHobbies", "list": ("hobby", shared[:2])})
    if (v := same("mother_tongue")) is not None:
        out.append({"key": "sameTongue", "value": ("mother_tongue", v)})
    if (v := same("sub_community")) is not None:
        out.append({"key": "sameCommunity", "value": ("sub_community", v)})
    if (v := same("family_values")) is not None:
        out.append({"key": "sameFamilyValues", "value": ("family_values", v)})
    if (v := same("family_type")) is not None:
        out.append({"key": "sameFamilyType", "value": ("family_type", v)})
    if (v := same("diet")) is not None:
        out.append({"key": "sameDiet", "value": ("diet", v)})
    if (v := same("education")) is not None:
        out.append({"key": "sameEducation", "value": ("education_level", v)})
    my_city = str(seeker.get("locality") or "").split(",")[0].strip()
    their_city = str(other.get("locality") or "").split(",")[0].strip()
    if my_city and _lower(my_city) == _lower(their_city):
        out.append({"key": "sameCity", "city": my_city})
    else:
        here, there = _geo(seeker), _geo(other)
        if here and there and their_city:
            km = distance_km(here, there)
            if km <= cfg.NEARBY_REASON_KM:
                out.append({"key": "nearby", "city": their_city, "km": max(5, int(round(km / 5.0)) * 5)})
        if their_city and _would_relocate(other):
            out.append({"key": "openToMove", "city": their_city})
    return out

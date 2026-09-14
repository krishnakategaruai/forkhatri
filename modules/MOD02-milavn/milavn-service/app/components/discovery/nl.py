"""Natural-language understanding for Discovery and Create (thesis §40 "natural
language", §84 #9 "AI removes friction", §33 "AI must not become a shortcut
around permissions").

Deterministic on purpose: a small grammar over the module's own vocabulary
(interest taxonomy, intent categories, locality names, day/time words in
English, Hindi and Telugu). It never invents an activity, never touches
permissions, and every interpretation is echoed back to the person as chips
so they can correct it — "AI" that stays legible.

Two entry points:
  understand(text) -> filters for Search   ("badminton this weekend near me")
  smart_fill(text) -> a draft for Create   ("badminton tomorrow 7pm at Madhapur for 8")
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.config.interests import INTEREST_TAXONOMY, TAG_LABELS, TAG_TO_CATEGORY
from app.config.localities import LOCALITIES

IST = ZoneInfo("Asia/Kolkata")

CATEGORIES = ("play", "meet", "eat", "learn", "work", "explore", "celebrate", "help")

# Category synonyms (en/hi/te + common Hinglish) -> intent category.
_CATEGORY_WORDS: dict[str, str] = {
    "play": "play",
    "sport": "play",
    "sports": "play",
    "game": "play",
    "games": "play",
    "match": "play",
    "खेल": "play",
    "ఆట": "play",
    "ఆటలు": "play",
    "meet": "meet",
    "meetup": "meet",
    "hangout": "meet",
    "chai": "meet",
    "coffee": "meet",
    "catch up": "meet",
    "मिलना": "meet",
    "కలవడం": "meet",
    "eat": "eat",
    "food": "eat",
    "dinner": "eat",
    "lunch": "eat",
    "breakfast": "eat",
    "biryani": "eat",
    "brunch": "eat",
    "खाना": "eat",
    "భోజనం": "eat",
    "learn": "learn",
    "class": "learn",
    "workshop": "learn",
    "course": "learn",
    "talk": "learn",
    "सीखना": "learn",
    "నేర్చుకోవడం": "learn",
    "work": "work",
    "cowork": "work",
    "networking": "work",
    "startup": "work",
    "career": "work",
    "काम": "work",
    "పని": "work",
    "explore": "explore",
    "trek": "explore",
    "hike": "explore",
    "walk": "explore",
    "ride": "explore",
    "trip": "explore",
    "घूमना": "explore",
    "అన్వేషణ": "explore",
    "celebrate": "celebrate",
    "festival": "celebrate",
    "party": "celebrate",
    "diwali": "celebrate",
    "bathukamma": "celebrate",
    "त्योहार": "celebrate",
    "పండుగ": "celebrate",
    "help": "help",
    "volunteer": "help",
    "cleanup": "help",
    "clean-up": "help",
    "drive": "help",
    "मदद": "help",
    "సహాయం": "help",
}

_WHEN_WORDS: dict[str, str] = {
    "today": "today",
    "tonight": "today",
    "this evening": "today",
    "आज": "today",
    "ఈరోజు": "today",
    "ఈ రోజు": "today",
    "tomorrow": "tomorrow",
    "कल": "tomorrow",
    "రేపు": "tomorrow",
    "weekend": "weekend",
    "this weekend": "weekend",
    "saturday": "weekend",
    "sunday": "weekend",
    "वीकेंड": "weekend",
    "వీకెండ్": "weekend",
    "this week": "week",
    "week": "week",
    "इस हफ्ते": "week",
    "ఈ వారం": "week",
}

_DISTANCE_WORDS: dict[str, str] = {
    "near me": "zone",
    "nearby": "zone",
    "close by": "zone",
    "around me": "zone",
    "मेरे पास": "zone",
    "नज़दीक": "zone",
    "నా దగ్గర": "zone",
    "దగ్గరలో": "zone",
    "my area": "locality",
    "my locality": "locality",
    "in my locality": "locality",
    "same locality": "locality",
    "anywhere": "city",
    "whole city": "city",
    "across the city": "city",
}

_WEEKDAYS = {
    "monday": 0,
    "mon": 0,
    "tuesday": 1,
    "tue": 1,
    "wednesday": 2,
    "wed": 2,
    "thursday": 3,
    "thu": 3,
    "friday": 4,
    "fri": 4,
    "saturday": 5,
    "sat": 5,
    "sunday": 6,
    "sun": 6,
}
_DAYPART = {"morning": 8, "noon": 12, "afternoon": 15, "evening": 18, "tonight": 19, "night": 20, "सुबह": 8, "शाम": 18, "रात": 20, "ఉదయం": 8, "సాయంత్రం": 18, "రాత్రి": 20}


@dataclass(slots=True)
class Understanding:
    category: str | None = None
    when: str | None = None
    distance: str | None = None
    query: str | None = None
    chips: list[str] = field(default_factory=list)  # what we understood, in the person's words


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _find_phrase(text: str, table: dict[str, str]) -> tuple[str | None, str | None]:
    # Longest phrase first so "this weekend" beats "weekend", "near me" beats "me".
    for phrase in sorted(table, key=len, reverse=True):
        if re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", text):
            return table[phrase], phrase
    return None, None


def _find_interest(text: str) -> tuple[str | None, str | None, str | None]:
    """Returns (tag, label, category) for the first interest label found in the text."""
    for items in INTEREST_TAXONOMY.values():
        for tag, label, category in items:
            for needle in {label.lower(), tag.replace("_", " ").lower()}:
                if needle and re.search(rf"(?<!\w){re.escape(needle)}(?!\w)", text):
                    return tag, label, category
    return None, None, None


def understand(text: str) -> Understanding:
    t = _norm(text)
    u = Understanding()
    if not t:
        return u
    remainder = t
    when, phrase = _find_phrase(t, _WHEN_WORDS)
    if when:
        u.when = when
        u.chips.append(phrase or when)
        remainder = remainder.replace(phrase or "", " ")
    dist, phrase = _find_phrase(t, _DISTANCE_WORDS)
    if dist:
        u.distance = dist
        u.chips.append(phrase or dist)
        remainder = remainder.replace(phrase or "", " ")
    tag, label, cat = _find_interest(t)
    if tag:
        u.category = cat
        u.query = label
        u.chips.append(label or tag)
        remainder = re.sub(rf"(?<!\w){re.escape((label or '').lower())}(?!\w)", " ", remainder)
    else:
        cat2, phrase = _find_phrase(t, _CATEGORY_WORDS)
        if cat2:
            u.category = cat2
            u.chips.append(phrase or cat2)
            remainder = remainder.replace(phrase or "", " ")
    leftover = re.sub(r"\b(in|at|on|for|the|a|an|me|some|something|find|show|any|to|do|go|and|with|near)\b", " ", remainder)
    leftover = re.sub(r"[^\wऀ-ॿఀ-౿ ]+", " ", leftover)
    leftover = re.sub(r"\s+", " ", leftover).strip()
    if leftover and not u.query:
        u.query = leftover
    return u


@dataclass(slots=True)
class Draft:
    category: str | None = None
    title: str | None = None
    time_start: str | None = None  # ISO 8601 with offset
    locality_city: str | None = None
    locality_locality: str | None = None
    capacity: int | None = None
    matched: list[str] = field(default_factory=list)


def _parse_time(t: str) -> tuple[int | None, int, str | None]:
    """Returns (hour24, minute, matched_phrase)."""
    m = re.search(r"(?<!\d)(\d{1,2})(?::(\d{2}))?\s*(am|pm)(?!\w)", t)
    if m:
        h, mi, ap = int(m.group(1)), int(m.group(2) or 0), m.group(3)
        if ap == "pm" and h < 12:
            h += 12
        if ap == "am" and h == 12:
            h = 0
        return h, mi, m.group(0)
    m = re.search(r"(?<!\d)(\d{1,2}):(\d{2})(?!\d)", t)
    if m:
        return int(m.group(1)), int(m.group(2)), m.group(0)
    m = re.search(r"(?<!\d)(\d{1,2})\s*(baje|बजे|గంటలకు)", t)
    if m:
        h = int(m.group(1))
        return (h + 12 if 1 <= h <= 6 else h), 0, m.group(0)
    for word, hour in _DAYPART.items():
        if re.search(rf"(?<!\w){re.escape(word)}(?!\w)", t):
            return hour, 0, word
    return None, 0, None


def smart_fill(text: str, *, now: datetime | None = None, default_city: str | None = None) -> Draft:
    t = _norm(text)
    d = Draft()
    if not t:
        return d
    now = (now or datetime.now(IST)).astimezone(IST)
    remainder = t

    # Category via interest label or synonym.
    tag, label, cat = _find_interest(t)
    if tag:
        d.category = cat
        d.matched.append(label or tag)
    else:
        cat2, phrase = _find_phrase(t, _CATEGORY_WORDS)
        if cat2:
            d.category = cat2
            d.matched.append(phrase or cat2)
            pass  # the word stays in the title: "chai and chapters" is a name, not only a category hint

    # Day.
    day = now.date()
    day_phrase = None
    if re.search(r"(?<!\w)(tomorrow|कल|రేపు)(?!\w)", t):
        day = day + timedelta(days=1)
        day_phrase = "tomorrow"
    elif re.search(r"(?<!\w)(today|tonight|आज|ఈరోజు)(?!\w)", t):
        day_phrase = "today"
    else:
        for name, wd in sorted(_WEEKDAYS.items(), key=lambda kv: -len(kv[0])):
            if re.search(rf"(?<!\w){name}(?!\w)", t):
                delta = (wd - now.weekday()) % 7 or 7
                day = day + timedelta(days=delta)
                day_phrase = name
                break
    if day_phrase:
        d.matched.append(day_phrase)
        remainder = re.sub(rf"(?<!\w){re.escape(day_phrase)}(?!\w)", " ", remainder)

    # Time.
    hour, minute, tphrase = _parse_time(t)
    if tphrase:
        d.matched.append(tphrase)
        remainder = remainder.replace(tphrase, " ")
    if day_phrase or tphrase:
        h = hour if hour is not None else 18
        start = datetime(day.year, day.month, day.day, h, minute, tzinfo=IST)
        if start < now:
            start = start + timedelta(days=1) if not day_phrase else start
        d.time_start = start.isoformat()

    # Where: locality names from the module's own hierarchy.
    for loc in sorted(LOCALITIES, key=lambda x: -len(x.locality)):
        if re.search(rf"(?<!\w){re.escape(loc.locality.lower())}(?!\w)", t):
            d.locality_city, d.locality_locality = loc.city, loc.locality
            d.matched.append(loc.locality)
            remainder = re.sub(rf"(?<!\w)(at|in|near)?\s*{re.escape(loc.locality.lower())}(?!\w)", " ", remainder)
            break
    if d.locality_city is None and default_city:
        d.locality_city = default_city

    # How many.
    m = re.search(r"(?<!\w)(?:for|max|upto|up to)\s*(\d{1,3})(?:\s*(?:people|ppl|persons|players|folks|लोग|మంది))?(?!\w)", t) or re.search(
        r"(?<!\d)(\d{1,3})\s*(?:people|ppl|persons|players|folks|लोग|మంది)(?!\w)", t
    )
    if m:
        d.capacity = max(2, min(500, int(m.group(1))))
        d.matched.append(m.group(0))
        remainder = remainder.replace(m.group(0), " ")

    # Title: what is left, tidied. Keep the interest label if the rest is empty.
    leftover = re.sub(r"\b(at|on|for|the|a|an|to|with|near|by|from|lets|let's|let us|plan|planning|organise|organize|host|hosting|create)\b", " ", remainder)
    leftover = re.sub(r"[^\wऀ-ॿఀ-౿' ]+", " ", leftover)
    leftover = re.sub(r"\s+", " ", leftover).strip()
    if not leftover and label:
        leftover = label
    if leftover:
        d.title = leftover[:1].upper() + leftover[1:]
        d.title = d.title[:140]
    return d


def category_label_words() -> dict[str, str]:
    """Exposed for tests/docs: every word the parser understands as a category."""
    return dict(_CATEGORY_WORDS) | {TAG_LABELS[t].lower(): TAG_TO_CATEGORY[t] for t in TAG_LABELS}

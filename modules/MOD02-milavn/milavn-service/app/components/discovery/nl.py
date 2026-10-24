"""Natural-language understanding for Discovery and Create (thesis §40 "natural
language", §84 #9 "AI removes friction", §33 "AI must not become a shortcut
around permissions").

Deterministic on purpose: a small grammar over the module's own vocabulary
(interest taxonomy, intent categories, locality names, day/time words in
English, Hindi, Telugu, Marathi and Kannada). It never invents an activity, never touches
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

IST = ZoneInfo("Asia/Kolkata")

CATEGORIES = ("play", "meet", "eat", "learn", "work", "explore", "celebrate", "help", "professional")

# Category synonyms (en/hi/te/mr/kn + common Hinglish) -> intent category.
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
    "खेळ": "play",
    "ಆಟ": "play",
    "ಆಟಗಳು": "play",
    "ಕ್ರೀಡೆ": "play",
    "meet": "meet",
    "meetup": "meet",
    "hangout": "meet",
    "chai": "meet",
    "coffee": "meet",
    "catch up": "meet",
    "मिलना": "meet",
    "కలవడం": "meet",
    "भेटणे": "meet",
    "भेटीगाठी": "meet",
    "ಭೇಟಿ": "meet",
    "eat": "eat",
    "food": "eat",
    "dinner": "eat",
    "lunch": "eat",
    "breakfast": "eat",
    "biryani": "eat",
    "brunch": "eat",
    "खाना": "eat",
    "భోజనం": "eat",
    "जेवण": "eat",
    "ಊಟ": "eat",
    "ತಿಂಡಿ": "eat",
    "learn": "learn",
    "class": "learn",
    "workshop": "learn",
    "course": "learn",
    "talk": "learn",
    "सीखना": "learn",
    "నేర్చుకోవడం": "learn",
    "शिकणे": "learn",
    "ಕಲಿಕೆ": "learn",
    "work": "work",
    "cowork": "work",
    "networking": "work",
    "startup": "work",
    "career": "work",
    "काम": "work",
    "పని": "work",
    "ಕೆಲಸ": "work",
    "professional": "professional",
    "professionals": "professional",
    "consulting": "professional",
    "consultant": "professional",
    "expert": "professional",
    "experts": "professional",
    "conference": "professional",
    "seminar": "professional",
    "masterclass": "professional",
    "पेशेवर": "professional",
    "विशेषज्ञ": "professional",
    "నిపుణులు": "professional",
    "వృత్తిపరమైన": "professional",
    "व्यावसायिक": "professional",
    "तज्ज्ञ": "professional",
    "ವೃತ್ತಿಪರ": "professional",
    "ತಜ್ಞರು": "professional",
    "explore": "explore",
    "trek": "explore",
    "hike": "explore",
    "walk": "explore",
    "ride": "explore",
    "trip": "explore",
    "घूमना": "explore",
    "అన్వేషణ": "explore",
    "भटकंती": "explore",
    "फिरणे": "explore",
    "ಸುತ್ತಾಟ": "explore",
    "celebrate": "celebrate",
    "festival": "celebrate",
    "party": "celebrate",
    "diwali": "celebrate",
    "bathukamma": "celebrate",
    "त्योहार": "celebrate",
    "పండుగ": "celebrate",
    "सण": "celebrate",
    "ಹಬ್ಬ": "celebrate",
    "help": "help",
    "volunteer": "help",
    "cleanup": "help",
    "clean-up": "help",
    "drive": "help",
    "मदद": "help",
    "సహాయం": "help",
    "मदत": "help",
    "ಸಹಾಯ": "help",
}

# [054] Event format words (en/hi/te/mr/kn) -> event format. Checked before the category words, so "book club" or
# "tournament" filters by what kind of event it is rather than guessing a category from the same word.
_FORMAT_WORDS: dict[str, str] = {
    "workshop": "workshop",
    "workshops": "workshop",
    "कार्यशाला": "workshop",
    "వర్క్‌షాప్": "workshop",
    "कार्यशाळा": "workshop",
    "ಕಾರ್ಯಾಗಾರ": "workshop",
    "webinar": "webinar",
    "webinars": "webinar",
    "वेबिनार": "webinar",
    "వెబినార్": "webinar",
    "ವೆಬಿನಾರ್": "webinar",
    "talk": "talk",
    "lecture": "talk",
    "व्याख्यान": "talk",
    "ఉపన్యాసం": "talk",
    "ಉಪನ್ಯಾಸ": "talk",
    "panel": "panel",
    "panel discussion": "panel",
    "परिचर्चा": "panel",
    "चर्चासत्र": "panel",
    "ಚರ್ಚಾಗೋಷ್ಠಿ": "panel",
    "masterclass": "masterclass",
    "master class": "masterclass",
    "book club": "book_club",
    "reading circle": "book_club",
    "पुस्तक क्लब": "book_club",
    "బుక్ క్లబ్": "book_club",
    "ಪುಸ್ತಕ ಕ್ಲಬ್": "book_club",
    "ಬುಕ್ ಕ್ಲಬ್": "book_club",
    "skill share": "skill_share",
    "skill-share": "skill_share",
    "skillshare": "skill_share",
    "office hours": "office_hours",
    "ask me anything": "office_hours",
    "bootcamp": "bootcamp",
    "boot camp": "bootcamp",
    "multi-day": "bootcamp",
    "conference": "conference",
    "summit": "conference",
    "सम्मेलन": "conference",
    "సదస్సు": "conference",
    "संमेलन": "conference",
    "ಸಮ್ಮೇಳನ": "conference",
    "expo": "expo",
    "exhibition": "expo",
    "प्रदर्शनी": "expo",
    "ప్రదర్శన": "expo",
    "ಪ್ರದರ್ಶನ": "expo",
    "cultural night": "cultural_night",
    "concert": "cultural_night",
    "music night": "cultural_night",
    "सांस्कृतिक संध्या": "cultural_night",
    "संगीत संध्या": "cultural_night",
    "సాంస్కృతిక కార్యక్రమం": "cultural_night",
    "సంగీత కచేరీ": "cultural_night",
    "सांस्कृतिक कार्यक्रम": "cultural_night",
    "संगीत मैफल": "cultural_night",
    "ಸಾಂಸ್ಕೃತಿಕ ಕಾರ್ಯಕ್ರಮ": "cultural_night",
    "ಸಂಗೀತ ಕಛೇರಿ": "cultural_night",
    "tournament": "tournament",
    "league": "tournament",
    "टूर्नामेंट": "tournament",
    "టోర్నమెంట్": "tournament",
    "स्पर्धा": "tournament",
    "ಪಂದ್ಯಾವಳಿ": "tournament",
    "ಟೂರ್ನಮೆಂಟ್": "tournament",
    "festival": "festival",
    "mela": "festival",
    "उत्सव": "festival",
    "मेला": "festival",
    "ఉత్సవం": "festival",
    "जत्रा": "festival",
    "ಉತ್ಸವ": "festival",
    "ಜಾತ್ರೆ": "festival",
    "satsang": "satsang",
    "bhajan": "satsang",
    "bhajan sandhya": "satsang",
    "भजन संध्या": "satsang",
    "kirtan": "satsang",
    "सत्संग": "satsang",
    "भजन": "satsang",
    "कीर्तन": "satsang",
    "సత్సంగం": "satsang",
    "భజన": "satsang",
    "కీర్తన": "satsang",
    "ಸತ್ಸಂಗ": "satsang",
    "ಭಜನೆ": "satsang",
    "ಕೀರ್ತನೆ": "satsang",
    "live darshan": "darshan_stream",
    "darshan": "darshan_stream",
    "दर्शन": "darshan_stream",
    "దర్శనం": "darshan_stream",
    "ದರ್ಶನ": "darshan_stream",
    "town hall": "town_hall",
    "townhall": "town_hall",
    "टाउन हॉल": "town_hall",
    "టౌన్ హాల్": "town_hall",
    "ಟೌನ್ ಹಾಲ್": "town_hall",
    "volunteering": "volunteering",
    "volunteer drive": "volunteering",
    "seva": "volunteering",
    "सेवा": "volunteering",
    "సేవ": "volunteering",
    "ಸೇವೆ": "volunteering",
    "trip": "trip",
    "yatra": "trip",
    "यात्रा": "trip",
    "యాత్ర": "trip",
    "सहल": "trip",
    "ಯಾತ್ರೆ": "trip",
    "ಪ್ರವಾಸ": "trip",
    "meetup": "meetup",
    "meet-up": "meetup",
    "मीटअप": "meetup",
    "మీటప్": "meetup",
    "ಮೀಟಪ್": "meetup",
}

_WHEN_WORDS: dict[str, str] = {
    "today": "today",
    "tonight": "today",
    "this evening": "today",
    "आज": "today",
    "ఈరోజు": "today",
    "ఈ రోజు": "today",
    "आज संध्याकाळी": "today",
    "आज रात्री": "today",
    "ಇಂದು": "today",
    "ಇವತ್ತು": "today",
    "ಇಂದು ಸಂಜೆ": "today",
    "ಇಂದು ರಾತ್ರಿ": "today",
    "उद्या संध्याकाळी": "tomorrow",
    "उद्या सकाळी": "tomorrow",
    "ನಾಳೆ ಸಂಜೆ": "tomorrow",
    "ನಾಳೆ ಬೆಳಿಗ್ಗೆ": "tomorrow",
    "tomorrow": "tomorrow",
    "कल": "tomorrow",
    "రేపు": "tomorrow",
    "उद्या": "tomorrow",
    "ನಾಳೆ": "tomorrow",
    "weekend": "weekend",
    "this weekend": "weekend",
    "saturday": "weekend",
    "sunday": "weekend",
    "वीकेंड": "weekend",
    "వీకెండ్": "weekend",
    "आठवड्याच्या शेवटी": "weekend",
    "शनिवार": "weekend",
    "रविवार": "weekend",
    "ವೀಕೆಂಡ್": "weekend",
    "ವಾರಾಂತ್ಯ": "weekend",
    "ಶನಿವಾರ": "weekend",
    "ಭಾನುವಾರ": "weekend",
    "this week": "week",
    "week": "week",
    "इस हफ्ते": "week",
    "ఈ వారం": "week",
    "या आठवड्यात": "week",
    "ಈ ವಾರ": "week",
}

# Who it is for (English only for now; Hindi and Telugu wording needs native review before it is added).
_AUDIENCE_WORDS: dict[str, str] = {
    "beginner friendly": "beginner_friendly",
    "beginner-friendly": "beginner_friendly",
    "beginners": "beginner_friendly",
    "family friendly": "family_friendly",
    "family-friendly": "family_friendly",
    "family and kids": "family_friendly",
    "kids": "family_friendly",
    "elder friendly": "elder_friendly",
    "elder-friendly": "elder_friendly",
    "seniors": "elder_friendly",
}

# A festival name is a topic, not a kind of event: "diwali cooking" is a cooking event, not a celebration. When more
# words follow, the festival stays in the search words instead of narrowing to the Celebrate category.
_SOFT_CATEGORY_WORDS = {"diwali", "bathukamma", "festival", "party"}

_DISTANCE_WORDS: dict[str, str] = {
    "near me": "zone",
    "nearby": "zone",
    "close by": "zone",
    "around me": "zone",
    "मेरे पास": "zone",
    "नज़दीक": "zone",
    "నా దగ్గర": "zone",
    "దగ్గరలో": "zone",
    "माझ्या जवळ": "zone",
    "जवळपास": "zone",
    "ನನ್ನ ಹತ್ತಿರ": "zone",
    "ಹತ್ತಿರದಲ್ಲಿ": "zone",
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
    # [2026-10-06] Day names in Hindi, Telugu, Marathi and Kannada. Without them "रविवार शाम 6 बजे" read only the
    # time and, that time being past today, landed on tomorrow (ONBOARDING-REDESIGN §2.10).
    "सोमवार": 0,
    "मंगलवार": 1,
    "मंगळवार": 1,
    "बुधवार": 2,
    "गुरुवार": 3,
    "बृहस्पतिवार": 3,
    "शुक्रवार": 4,
    "शनिवार": 5,
    "रविवार": 6,
    "इतवार": 6,
    "సోమవారం": 0,
    "మంగళవారం": 1,
    "బుధవారం": 2,
    "గురువారం": 3,
    "శుక్రవారం": 4,
    "శనివారం": 5,
    "ఆదివారం": 6,
    "ಸೋಮವಾರ": 0,
    "ಮಂಗಳವಾರ": 1,
    "ಬುಧವಾರ": 2,
    "ಗುರುವಾರ": 3,
    "ಶುಕ್ರವಾರ": 4,
    "ಶನಿವಾರ": 5,
    "ಭಾನುವಾರ": 6,
}
# Marathi/Kannada day words that leave a Create title (en/hi/te titles are left exactly as before).
_MR_KN_DAY_WORDS = {"उद्या", "ನಾಳೆ", "ಇಂದು", "ಇವತ್ತು"}
_DAYPART = {"morning": 8, "noon": 12, "afternoon": 15, "evening": 18, "tonight": 19, "night": 20, "सुबह": 8, "शाम": 18, "रात": 20, "ఉదయం": 8, "సాయంత్రం": 18, "రాత్రి": 20, "सकाळी": 8, "दुपारी": 15, "संध्याकाळी": 18, "रात्री": 20, "ಬೆಳಿಗ್ಗೆ": 8, "ಮಧ್ಯಾಹ್ನ": 15, "ಸಂಜೆ": 18, "ರಾತ್ರಿ": 20}


@dataclass(slots=True)
class Understanding:
    category: str | None = None
    event_format: str | None = None  # [054]
    when: str | None = None
    distance: str | None = None
    query: str | None = None
    audience: str | None = None  # family_friendly | elder_friendly | beginner_friendly
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
    fmt, fphrase = _find_phrase(t, _FORMAT_WORDS)
    if fmt:
        u.event_format = fmt
        u.chips.append(fphrase or fmt)
        remainder = re.sub(rf"(?<!\w){re.escape(fphrase or '')}(?!\w)", " ", remainder)
        t = re.sub(rf"(?<!\w){re.escape(fphrase or '')}(?!\w)", " ", t)  # the same word is not read again as a category
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
    aud, aphrase = _find_phrase(t, _AUDIENCE_WORDS)
    if aud:
        u.audience = aud
        u.chips.append(aphrase or aud)
        remainder = re.sub(rf"(?<!\w){re.escape(aphrase or '')}(?!\w)", " ", remainder)
        t = re.sub(rf"(?<!\w){re.escape(aphrase or '')}(?!\w)", " ", t)
    tag, label, cat = _find_interest(t)
    if tag:
        u.category = cat
        u.query = label
        u.chips.append(label or tag)
        remainder = re.sub(rf"(?<!\w){re.escape((label or '').lower())}(?!\w)", " ", remainder)
    else:
        cat2, phrase = _find_phrase(t, _CATEGORY_WORDS)
        rest = re.sub(rf"(?<!\w){re.escape(phrase or '')}(?!\w)", " ", remainder) if phrase else ""
        rest = re.sub(r"\b(in|at|on|for|the|a|an|me|some|something|find|show|any|to|do|go|and|with|near)\b", " ", rest)
        if cat2 and phrase in _SOFT_CATEGORY_WORDS and re.search(r"[\wऀ-ॿఀ-౿ಀ-೿]{3,}", rest):
            pass  # keep the festival word in the search words
        elif cat2:
            u.category = cat2
            u.chips.append(phrase or cat2)
            remainder = remainder.replace(phrase or "", " ")
    leftover = re.sub(r"\b(in|at|on|for|the|a|an|me|some|something|find|show|any|to|do|go|and|with|near)\b", " ", remainder)
    leftover = re.sub(r"[^\wऀ-ॿఀ-౿ಀ-೿ ]+", " ", leftover)
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
    place: dict | None = None  # the full approximate place, when it matched one the caller knows
    capacity: int | None = None
    event_format: str | None = None  # [054]
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
    m = re.search(r"(?<!\d)(\d{1,2})\s*(baje|बजे|గంటలకు|वाजता|ಗಂಟೆಗೆ)", t)
    if m:
        h = int(m.group(1))
        return (h + 12 if 1 <= h <= 6 else h), 0, m.group(0)
    for word, hour in _DAYPART.items():
        if re.search(rf"(?<!\w){re.escape(word)}(?!\w)", t):
            return hour, 0, word
    return None, 0, None


def smart_fill(text: str, *, now: datetime | None = None, default_city: str | None = None, known_places: list[dict] | None = None) -> Draft:
    t = _norm(text)
    d = Draft()
    if not t:
        return d
    now = (now or datetime.now(IST)).astimezone(IST)
    remainder = t

    # [054] The kind of event, when the sentence names one ("book club", "tournament"); the word stays in the title.
    fmt, fphrase = _find_phrase(t, _FORMAT_WORDS)
    if fmt:
        d.event_format = fmt
        d.matched.append(fphrase or fmt)

    # Category via interest label or synonym.
    tag, label, cat = _find_interest(t)
    if tag:
        d.category = cat
        if (label or tag).lower() not in {m.lower() for m in d.matched}:  # "satsang" is both a format and an interest: one chip
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
    day_word = None  # the Marathi/Kannada day word as written ("उद्या", "ನಾಳೆ"), so it leaves the title too
    if m_day := re.search(r"(?<!\w)(tomorrow|कल|రేపు|उद्या|ನಾಳೆ)(?!\w)", t):
        day = day + timedelta(days=1)
        day_phrase, day_word = "tomorrow", m_day.group(1)
    elif m_day := re.search(r"(?<!\w)(today|tonight|आज|ఈరోజు|ಇಂದು|ಇವತ್ತು)(?!\w)", t):
        day_phrase, day_word = "today", m_day.group(1)
    else:
        for name, wd in sorted(_WEEKDAYS.items(), key=lambda kv: -len(kv[0])):
            if re.search(rf"(?<!\w){name}(?!\w)", t):
                delta = (wd - now.weekday()) % 7 or 7
                day = day + timedelta(days=delta)
                day_phrase = name
                break
    if day_phrase:
        d.matched.append(day_phrase)
        remainder = re.sub(rf"(?<!\w){re.escape(day_word if day_word in _MR_KN_DAY_WORDS else day_phrase)}(?!\w)", " ", remainder)

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

    # Where: area names the caller knows (the member's own place and places real events already use).
    for loc in sorted((k for k in (known_places or []) if k.get("locality_locality")), key=lambda x: -len(x["locality_locality"])):
        name = loc["locality_locality"]
        if re.search(rf"(?<!\w){re.escape(name.lower())}(?!\w)", t):
            d.locality_city, d.locality_locality, d.place = loc["locality_city"], name, loc
            d.matched.append(name)
            remainder = re.sub(rf"(?<!\w)(at|in|near)?\s*{re.escape(name.lower())}(?!\w)", " ", remainder)
            break
    if d.locality_city is None and default_city:
        d.locality_city = default_city

    # How many.
    m = re.search(r"(?<!\w)(?:for|max|upto|up to)\s*(\d{1,3})(?:\s*(?:people|ppl|persons|players|folks|लोग|మంది|लोक|जण|ಜನ|ಮಂದಿ))?(?!\w)", t) or re.search(
        r"(?<!\d)(\d{1,3})\s*(?:people|ppl|persons|players|folks|लोग|మంది|लोक|जण|ಜನ|ಮಂದಿ)(?!\w)", t
    )
    if m:
        d.capacity = max(2, min(500, int(m.group(1))))
        d.matched.append(m.group(0))
        remainder = remainder.replace(m.group(0), " ")

    # Title: what is left, tidied. Keep the interest label if the rest is empty.
    leftover = re.sub(r"\b(at|on|for|the|a|an|to|with|near|by|from|lets|let's|let us|plan|planning|organise|organize|host|hosting|create)\b", " ", remainder)
    leftover = re.sub(r"[^\wऀ-ॿఀ-౿ಀ-೿' ]+", " ", leftover)
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

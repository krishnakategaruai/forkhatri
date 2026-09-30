# [IMP42 — Refactor C (AI)] RulesProvider: the no-network engine behind every
# AI endpoint. It is what runs when AI_PROVIDER=rules or no Anthropic key is
# configured, and what the service falls back to when Claude is unreachable —
# so every screen keeps working with a usable answer. It grows the keyword
# approach services/opportunities.py's `_extract_fields` started (English,
# Hindi, Telugu and Hinglish words) and reuses app/ranking.py's allow-listed
# signals for the shortlist, scaled to 1–10, so the rules shortlist can never
# disagree with the feed's own notion of fit.
from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any

from app.ranking import DEFAULT_WEIGHTS, RankingSignals, score, top_signal_keys

from app.integrations.ai.base import AiResult, AiUnavailable, ImageInput
from app.integrations.ai.vocab import (
    DURATIONS,
    MAX_DESCRIPTION,
    MAX_TITLE,
    REASON_CODES,
    has_value,
    redact_contacts,
    strip_title_label,
)

_WORD = r"(?<![a-z0-9])(?:{})(?![a-z0-9])"


def _kw(*words: str) -> re.Pattern[str]:
    """Latin words match on word boundaries; Devanagari/Telugu match as substrings."""
    latin = [re.escape(w) for w in words if re.match(r"^[a-z0-9 .'/+-]+$", w)]
    other = [re.escape(w) for w in words if not re.match(r"^[a-z0-9 .'/+-]+$", w)]
    parts = []
    if latin:
        parts.append(_WORD.format("|".join(latin)))
    if other:
        parts.append("|".join(other))
    return re.compile("|".join(parts), re.I)


# ---- type detection ---------------------------------------------------------

_TYPE_HINTS: dict[str, list[tuple[re.Pattern[str], int]]] = {
    "employment": [
        (_kw("hiring", "job", "jobs", "vacancy", "vacancies", "opening", "openings", "full time", "full-time", "part time", "part-time",
             "salary", "ctc", "recruit", "recruitment", "staff", "employee", "walk-in", "walk in", "naukri", "nokri", "bharti",
             "boys", "girls", "workers", "helpers", "helper", "बॉय", "बॉयज़", "लड़के", "कर्मचारी", "हेल्पर", "सहायक",
             "पास", "चलेगा", "బాయ్స్", "బాయ్", "సిబ్బంది", "హెల్పర్", "తరగతి",
             "नौकरी", "भर्ती", "वेतन", "सैलरी", "स्टाफ", "ఉద్యోగం", "ఉద్యోగాలు", "జీతం", "నియామకం", "స్టాఫ్"), 3),
        (_kw("per month", "monthly", "pm", "shift", "interview", "qualification", "fresher", "freshers", "experience",
             "महीना", "इंटरव्यू", "నెల", "నెలకు", "ఇంటర్వ్యూ"), 1),
    ],
    "freelance": [
        (_kw("freelance", "freelancer", "project", "project basis", "gig", "contract", "proposal", "proposals", "deliverable",
             "deliverables", "remote work", "per hour", "hourly", "milestone", "फ्रीलांस", "प्रोजेक्ट", "ఫ్రీలాన్స్", "ప్రాజెక్ట్"), 3),
        # Software and creative deliverables: something to be BUILT or MADE is
        # project work, never a home-visit service (FE1: "React dashboard"
        # was read as a local service).
        (_kw("dashboard", "website", "web app", "webapp", "mobile app", "android app", "ios app", "landing page", "e-commerce site",
             "react", "next.js", "angular", "flutter", "wordpress", "shopify", "api", "backend", "frontend", "full stack", "ui/ux",
             "figma", "logo design", "logo", "branding kit", "video editing", "content writing", "copywriting", "seo",
             "वेबसाइट", "ऐप", "డాష్‌బోర్డ్", "వెబ్‌సైట్", "యాప్"), 3),
        (_kw("build", "develop", "developer", "design", "designer", "content", "video", "portfolio", "budget", "deadline",
             "app", "बजट", "బడ్జెట్"), 1),
    ],
    "local_service": [
        (_kw("plumber", "electrician", "carpenter", "painter", "mechanic", "repair", "repairs", "fix", "leaking", "leak", "service needed",
             "home visit", "प्लंबर", "इलेक्ट्रीशियन", "मरम्मत", "ठीक करना", "ప్లంబర్", "ఎలక్ట్రీషియన్", "రిపేర్"), 3),
        # Generic "I need …" words say nothing about the KIND of work; they
        # only tip a tie towards a local service.
        (_kw("need a", "need an", "looking for a", "chahiye", "chaiye", "urgent", "urgently", "aaj", "kal", "today", "tomorrow",
             "this week", "at home", "at my", "flat", "2bhk", "3bhk", "house", "चाहिए", "घर", "కావాలి", "అవసరం", "ఇల్లు", "ఇంట్లో"), 1),
    ],
    "partnership": [(_kw("partner", "partners", "partnership", "tie-up", "tie up", "collaborate", "collaboration", "joint venture",
                         "distributor", "franchise", "साझेदार", "साझेदारी", "భాగస్వామి", "భాగస్వామ్యం"), 3)],
    "training": [(_kw("training", "course", "crash course", "classes", "class", "workshop", "coaching", "batch", "certification",
                      "प्रशिक्षण", "कोर्स", "क्लास", "శిక్షణ", "కోర్సు", "క్లాస్"), 3)],
    "community": [(_kw("volunteer", "volunteers", "community", "seva", "free of cost", "donation", "drive", "camp",
                       "सेवा", "समुदाय", "स्वयंसेवक", "సేవ", "సమాజం", "వాలంటీర్"), 3)],
}


def detect_type(text: str) -> tuple[str, float]:
    low = text.lower()
    scores: dict[str, int] = {}
    for type_, hints in _TYPE_HINTS.items():
        total = 0
        for pattern, weight in hints:
            total += weight * len(pattern.findall(low))
        scores[type_] = total
    best = max(scores, key=lambda k: (scores[k], k == "employment"))
    if scores[best] == 0:
        return "employment", 0.3
    ordered = sorted(scores.values(), reverse=True)
    margin = ordered[0] - (ordered[1] if len(ordered) > 1 else 0)
    return best, 0.85 if margin >= 3 else 0.6


# ---- money and numbers ------------------------------------------------------

_AMOUNT = re.compile(
    r"(?:₹|rs\.?|inr|rupees?|रु\.?|रुपये|రూ\.?|రూపాయలు)?\s*(\d{1,3}(?:,\d{2,3})+|\d+(?:\.\d+)?)\s*"
    r"(k|thousand|lakhs?|lacs?|lakh|l|cr|crores?|hazaar|hazar|हज़ार|हजार|लाख|వేలు|వేల|లక్ష|లక్షలు)?",
    re.I,
)
# "12 se 15 tak" (Hindi), "12 nundi 15 varaku" (Telugu), in either script.
_RANGE_SEP = r"\s*(?:-|–|—|to|se|से|nundi|nunchi|నుండి|నుంచి|and|/)\s*"
_RANGE_END = r"(?:\s*(?:tak|तक|varaku|వరకు))?"
_UNIT_MULT = {
    "k": 1_000, "thousand": 1_000, "hazaar": 1_000, "hazar": 1_000, "हज़ार": 1_000, "हजार": 1_000, "వేలు": 1_000, "వేల": 1_000,
    "lakh": 100_000, "lakhs": 100_000, "lac": 100_000, "lacs": 100_000, "l": 100_000, "लाख": 100_000, "లక్ష": 100_000, "లక్షలు": 100_000,
    "cr": 10_000_000, "crore": 10_000_000, "crores": 10_000_000,
}
_MONTHLY = _kw("per month", "a month", "monthly", "pm", "p.m.", "/month", "/ month", "month", "mahina", "mahine", "महीना", "महीने", "प्रति माह", "నెల", "నెలకు")
_DAILY = _kw("per day", "a day", "daily", "/day", "roz", "रोज़", "रोज", "प्रति दिन", "రోజు", "రోజుకు")
_HOURLY = _kw("per hour", "an hour", "hourly", "/hr", "/hour", "per hr", "ghanta", "घंटा", "प्रति घंटा", "గంట", "గంటకు")
_MONEY_CONTEXT = _kw("salary", "ctc", "pay", "paying", "stipend", "budget", "rate", "charges", "charge", "fee", "fees", "package",
                     "₹", "rs", "rs.", "inr", "rupees", "rupee", "वेतन", "सैलरी", "बजट", "रु", "रुपये", "जీతం", "జీతం", "బడ్జెట్", "రూ")


def _to_rupees(number: str, unit: str | None) -> int:
    value = float(number.replace(",", ""))
    if unit:
        value *= _UNIT_MULT.get(unit.lower(), 1)
    return int(round(value))


def find_money(text: str) -> tuple[int | None, int | None, str | None]:
    """(min, max, period) in rupees. Picks the first amount that sits next to
    a money word, so a phone number or a pincode is never read as pay."""
    low = text.lower()
    range_re = re.compile(
        r"(?:₹|rs\.?|inr|rupees?|रु\.?|రూ\.?)?\s*(\d{1,3}(?:,\d{2,3})+|\d+(?:\.\d+)?)\s*"
        r"(k|thousand|lakhs?|lacs?|l|hazaar|hazar|हज़ार|हजार|लाख|వేలు|వేల|లక్ష|లక్షలు)?" + _RANGE_SEP +
        r"(?:₹|rs\.?|inr|रु\.?|రూ\.?)?\s*(\d{1,3}(?:,\d{2,3})+|\d+(?:\.\d+)?)\s*"
        r"(k|thousand|lakhs?|lacs?|l|hazaar|hazar|हज़ार|हजार|लाख|వేలు|వేల|లక్ష|లక్షలు)?" + _RANGE_END,
        re.I,
    )
    candidates: list[tuple[int, int | None, int]] = []  # (pos, min, max)
    for m in range_re.finditer(low):
        window = low[max(0, m.start() - 40): m.end() + 40]
        if not _MONEY_CONTEXT.search(window):
            continue
        unit2 = m.group(4) or m.group(2)
        unit1 = m.group(2) or unit2
        a, b = _to_rupees(m.group(1), unit1), _to_rupees(m.group(3), unit2)
        if a < 10 or b < 10:
            continue
        candidates.append((m.start(), min(a, b), max(a, b)))
    if not candidates:
        for m in _AMOUNT.finditer(low):
            window = low[max(0, m.start() - 40): m.end() + 40]
            if not _MONEY_CONTEXT.search(window):
                continue
            digits = m.group(1).replace(",", "")
            if re.fullmatch(r"[6-9]\d{9}", digits) or re.fullmatch(r"\d{6}", digits):
                continue  # phone number or pincode, never money
            value = _to_rupees(m.group(1), m.group(2))
            if value < 10:
                continue
            candidates.append((m.start(), None, value))
    if not candidates:
        return None, None, None
    pos, lo, hi = candidates[0]
    window = low[max(0, pos - 30): pos + 60]
    period = "hourly" if _HOURLY.search(window) else "daily" if _DAILY.search(window) else "monthly" if _MONTHLY.search(window) else None
    return lo, hi, period


_YEARS = re.compile(
    r"(\d{1,2})\s*(?:\+|plus)?\s*(?:-|–|to|se|से|nundi|నుండి|నుంచి)?\s*(\d{1,2})?\s*\+?\s*(?:years?|yrs?|yr|saal|साल|वर्ष|సంవత్సరాలు|సంవత్సరాల|సం\.?)\s*(?:of\s+)?(?:experience|exp\b|अनुभव|అనుభవం)?",
    re.I,
)
_FRESHER = _kw("fresher", "freshers", "no experience", "without experience", "beginner", "beginners", "फ्रेशर", "अनुभव नहीं", "ఫ్రెషర్", "అనుభవం అవసరం లేదు")


def find_experience_months(text: str) -> tuple[int | None, int | None]:
    low = text.lower()
    exp_words = re.search(r"experience|exp\b|अनुभव|అనుభవం|saal|साल|years?|yrs?", low)
    if _FRESHER.search(low) and not exp_words:
        return 0, None
    for m in _YEARS.finditer(low):
        window = low[max(0, m.start() - 30): m.end() + 30]
        if not re.search(r"experience|exp\b|अनुभव|అనుభవం|experienced|worked", window):
            continue
        lo = int(m.group(1)) * 12
        hi = int(m.group(2)) * 12 if m.group(2) else None
        return (min(lo, hi), max(lo, hi)) if hi is not None else (lo, None)
    if _FRESHER.search(low):
        return 0, None
    return None, None


# ---- field readers ----------------------------------------------------------

_SHIFT = (
    ("night", _kw("night shift", "night", "nights", "रात", "नाइट", "రాత్రి", "నైట్")),
    ("rotational", _kw("rotational", "rotating", "rotation", "रोटेशनल", "రొటేషనల్")),
    ("flexible", _kw("flexible", "flexi", "any shift", "लचीला", "ఫ్లెక్సిబుల్")),
    ("day", _kw("day shift", "morning shift", "general shift", "दिन की शिफ्ट", "डे शिफ्ट", "డే షిఫ్ట్", "పగటి షిఫ్ట్")),
)
_QUALIFICATION = (
    ("postgraduate", _kw("post graduate", "postgraduate", "post-graduate", "masters", "master's", "mba", "m.tech", "mtech", "m.sc", "msc", "m.com", "mcom", "pg", "पोस्ट ग्रेजुएट", "పోస్ట్ గ్రాడ్యుయేట్")),
    ("graduate", _kw("graduate", "graduation", "degree", "bachelor", "bachelors", "b.tech", "btech", "b.e", "b.com", "bcom", "b.sc", "bsc", "bba", "bca", "ग्रेजुएट", "स्नातक", "డిగ్రీ", "గ్రాడ్యుయేట్")),
    ("iti", _kw("iti", "आईटीआई", "ఐటీఐ")),
    ("diploma", _kw("diploma", "डिप्लोमा", "డిప్లొమా")),
    ("12th", _kw("12th", "12 th", "intermediate", "inter", "hsc", "plus two", "+2", "12वीं", "बारहवीं", "ఇంటర్", "ఇంటర్మీడియట్", "12వ")),
    ("10th", _kw("10th", "10 th", "matric", "matriculation", "ssc", "sslc", "10वीं", "दसवीं", "పదో తరగతి", "10వ", "టెన్త్")),
    ("below_10th", _kw("below 10th", "no qualification", "no education", "8th pass", "8th", "unskilled", "कोई पढ़ाई नहीं", "చదువు అవసరం లేదు")),
    ("any", _kw("any qualification", "any graduate", "qualification not required", "कोई भी योग्यता", "ఏ అర్హత అయినా")),
)
_ENGLISH = (
    ("fluent", _kw("fluent english", "excellent english", "english fluency", "fluent in english", "अच्छी अंग्रेज़ी", "ఫ్లూయెంట్ ఇంగ్లీష్")),
    ("good", _kw("good english", "english speaking", "communication skills", "spoken english", "इंग्लिश", "అంగ్ల భాష")),
    ("basic", _kw("basic english", "little english", "थोड़ी अंग्रेज़ी", "బేసిక్ ఇంగ్లీష్")),
    ("none", _kw("no english", "english not required", "english not needed", "अंग्रेज़ी ज़रूरी नहीं", "ఇంగ్లీష్ అవసరం లేదు")),
)
_ASSETS = (
    ("two_wheeler", _kw("bike", "two wheeler", "two-wheeler", "2 wheeler", "scooty", "scooter", "own vehicle", "बाइक", "स्कूटी", "बाइक", "బైక్", "స్కూటీ", "టూ వీలర్")),
    ("four_wheeler", _kw("four wheeler", "four-wheeler", "4 wheeler", "own car", "अपनी कार", "సొంత కారు")),
    ("driving_licence", _kw("driving licence", "driving license", "dl", "licence", "license", "ड्राइविंग लाइसेंस", "లైసెన్స్", "డ్రైవింగ్ లైసెన్స్")),
    ("smartphone", _kw("smartphone", "smart phone", "android phone", "own phone", "स्मार्टफोन", "స్మార్ట్‌ఫోన్", "స్మార్ట్ ఫోన్")),
    ("laptop", _kw("laptop", "own laptop", "own system", "लैपटॉप", "ల్యాప్‌టాప్", "ల్యాప్ టాప్")),
    ("own_tools", _kw("own tools", "own equipment", "अपने औज़ार", "సొంత పరికరాలు")),
)
_INCENTIVE = (
    ("incentive_only", _kw("incentive only", "commission only", "only incentive", "only commission", "सिर्फ कमीशन", "కమీషన్ మాత్రమే")),
    ("fixed_plus_incentive", _kw("incentive", "incentives", "commission", "plus incentives", "fixed + incentive", "इंसेंटिव", "कमीशन", "ఇన్సెంటివ్", "కమీషన్")),
)
_CLOCK = r"\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.|बजे|గంటలు)"
_TIMINGS = re.compile(
    rf"((?:{_CLOCK}|\d{{1,2}}:\d{{2}}|\d{{1,2}})\s*(?:-|–|to|se|से|నుండి)\s*(?:{_CLOCK}|\d{{1,2}}:\d{{2}}(?:\s*(?:am|pm))?)(?:\s*వరకు)?)",
    re.I,
)
# "सुबह 6 से दोपहर 2 बजे तक", "ఉదయం 6 నుండి సాయంత్రం 7 వరకు", "morning 9 to evening 6":
# a time of day on either side makes a bare number a clock time (N7 critique).
_DAYPART = (r"(?:सुबह|सवेरे|दोपहर|शाम|रात|subah|subha|dopahar|dopehar|shaam|sham|raat|morning|afternoon|evening|night|"
            r"ఉదయం|మధ్యాహ్నం|సాయంత్రం|రాత్రి|udayam|madhyahnam|sayantram|ratri)")
_CLOCK_NUM = r"\d{1,2}(?:[:.]\d{2})?\s*(?:बजे|గంటల(?:కు)?|గంటలు|am|pm|a\.m\.|p\.m\.)?"
_TIMINGS_DAYPART = re.compile(
    rf"((?:{_DAYPART}\s*{_CLOCK_NUM}\s*(?:-|–|to|se|से|nundi|nunchi|నుండి|నుంచి)\s*(?:{_DAYPART}\s*)?{_CLOCK_NUM}"
    rf"|{_CLOCK_NUM}\s*(?:-|–|to|se|से|nundi|nunchi|నుండి|నుంచి)\s*{_DAYPART}\s*{_CLOCK_NUM})"
    rf"(?:\s*(?:तक|tak|వరకు|varaku))?)",
    re.I,
)
_TIMINGS_LABEL = re.compile(r"(?:timings?|hours|shift timing|समय|టైమింగ్స్|సమయం)\s*[:\-–]?\s*([^\n.]{3,60})", re.I)
_INTERVIEW = re.compile(r"(?:interview|walk-?in|इंटरव्यू|ఇంటర్వ్యూ)[^\n.]{0,120}", re.I)
_HEADCOUNT_NOUN = (r"(?:openings?|vacanc(?:y|ies)|posts?|positions?|people|persons?|staff|workers?|helpers?|boys|girls|candidates?|nos\.?|"
                   r"लोग|पद|स्टाफ|हेल्पर(?:्स)?|सहायक|कर्मचारी|लड़के|लड़कियाँ|बॉय(?:ज़)?|వ్యక్తులు|పోస్టులు|మంది|ఖాళీలు|హెల్పర్లు|హెల్పర్|సిబ్బంది|బాయ్స్)")
# "2 हेल्पर", "3 सेल्स स्टाफ", "5 delivery boys": a number, at most one word, then who is wanted.
_OPENINGS = re.compile(rf"(\d{{1,3}})\s*(?:\+\s*)?(?:[^\s\d,.।]+\s+)?{_HEADCOUNT_NOUN}(?![a-z])", re.I)
_NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5, "छह": 6, "सात": 7, "आठ": 8, "नौ": 9, "दस": 10,
    "ఒక": 1, "ఒకరు": 1, "ఇద్దరు": 2, "ముగ్గురు": 3, "నలుగురు": 4, "ఐదుగురు": 5, "ఆరుగురు": 6, "పదిమంది": 10,
}
_OPENINGS_WORD = re.compile(
    rf"(?<![\w])({'|'.join(sorted(map(re.escape, _NUMBER_WORDS), key=len, reverse=True))})\s+(?:[^\s\d,.।]+\s+)?{_HEADCOUNT_NOUN}"
    rf"|(?<![\w])(ఒకరు|ఇద్దరు|ముగ్గురు|నలుగురు|ఐదుగురు|ఆరుగురు|పదిమంది)(?![\w])",
    re.I,
)


def find_openings(text: str) -> int | None:
    m = _OPENINGS.search(text) or _OPENINGS_LEAD.search(text)
    if m:
        return int(m.group(1))
    w = _OPENINGS_WORD.search(text)
    if w:
        return _NUMBER_WORDS.get((w.group(1) or w.group(2)).lower())
    return None


# "8वीं पास", "10th pass", "class 8 pass", "8వ తరగతి", "కక్ష 8" → the level it
# stands for (8th → below_10th). Needs a pass/class word, so "9th floor" is not a qualification.
_QUAL_NUMBER = re.compile(
    r"(\d{1,2})\s*(?:वीं|वी|th|st|nd|rd|వ|వది)?\s*(?:कक्षा\s*|class\s*|std\.?\s*)?(?:पास|pass(?:ed)?|class|std|standard|తరగతి|పాస్|ఉత్తీర్ణత)"
    r"|(?:class|std\.?|standard|कक्षा|తరగతి)\s*(\d{1,2})\s*(?:पास|pass(?:ed)?|పాస్)?",
    re.I,
)


def find_qualification(text: str) -> str | None:
    m = _QUAL_NUMBER.search(text)
    if m:
        n = int(m.group(1) or m.group(2))
        if 1 <= n <= 9:
            return "below_10th"
        if n in (10, 11):
            return "10th"
        if n == 12:
            return "12th"
    return _first(_QUALIFICATION, text.lower())


def find_timings(text: str) -> str | None:
    m = _TIMINGS_DAYPART.search(text) or _TIMINGS.search(text) or _TIMINGS_LABEL.search(text)
    return m.group(1).strip(" ,.;।") if m else None
_OPENINGS_LEAD = re.compile(r"(?:need|hiring|require|looking for|want|चाहिए|కావాలి)\s*(\d{1,3})\b", re.I)

_DURATION = (
    ("ongoing", _kw("ongoing", "long term", "long-term", "retainer", "continuous", "regular basis", "लंबे समय", "దీర్ఘకాలం")),
    ("over_6_months", _kw("over 6 months", "more than 6 months", "6+ months", "one year", "1 year", "12 months", "साल भर", "ఒక సంవత్సరం")),
    ("3_6_months", _kw("3-6 months", "3 to 6 months", "4 months", "5 months", "6 months", "3 months to 6")),
    ("1_3_months", _kw("1-3 months", "1 to 3 months", "2 months", "3 months", "a month", "1 month", "one month", "2-3 months", "एक महीना", "दो महीने", "ఒక నెల", "రెండు నెలలు")),
    ("1_4_weeks", _kw("2 weeks", "3 weeks", "4 weeks", "two weeks", "three weeks", "few weeks", "1-4 weeks", "दो हफ्ते", "रెండు వారాలు", "కొన్ని వారాలు")),
    ("under_1_week", _kw("under a week", "within a week", "1 week", "one week", "a week", "few days", "2 days", "3 days", "couple of days", "एक हफ्ता", "कुछ दिन", "ఒక వారం", "కొన్ని రోజులు")),
)
_LEVEL = (
    ("expert", _kw("expert", "experts", "senior", "specialist", "advanced", "highly experienced", "एक्सपर्ट", "అనుభవజ్ఞుడు")),
    ("intermediate", _kw("intermediate", "mid level", "mid-level", "some experience", "2-3 years", "मध्यम", "మధ్యస్థ")),
    ("entry", _kw("entry level", "entry-level", "beginner", "fresher", "junior", "student", "शुरुआती", "ఫ్రెషర్")),
)
_URGENT_TODAY = _kw("today", "urgent", "urgently", "asap", "immediately", "right now", "abhi", "aaj", "आज", "अभी", "तुरंत", "ఈరోజు", "ఇప్పుడే", "అత్యవసరం", "వెంటనే")
_THIS_WEEK = _kw("this week", "within the week", "in a few days", "by weekend", "tomorrow", "kal", "कल", "इस हफ्ते", "రేపు", "ఈ వారం")
_QUESTION = re.compile(r"([^.?!\n]{8,160}\?)")

_WORK_MODE = (
    ("remote", _kw("remote", "work from home", "wfh", "from home", "online only", "घर से", "ఇంటి నుండి", "రిమోట్")),
    ("both", _kw("hybrid", "remote or office", "on-site or remote", "हाइब्रिड", "హైబ్రిడ్")),
    ("on_site", _kw("on site", "on-site", "onsite", "at our office", "at the shop", "in office", "site visit", "at home", "at my", "ऑफिस में", "ఆఫీసులో", "సైట్")),
)
_INDIC_WORD = r"[ऀ-ॿఀ-౿‌‍]{2,}"
_LOCATION = [
    # An explicit label wins, in any script: "Location: Kukatpally", "स्थान: कुकटपल्ली", "ప్రాంతం: కూకట్‌పల్లి".
    re.compile(r"(?:location|area|address|place|venue|स्थान|जगह|पता|इलाका|इलाक़ा|లొకేషన్|స్థలం|ప్రాంతం|చిరునామా|ఏరియా)\s*[:\-–]\s*([^\n,.;।]{3,40})", re.I),
    re.compile(r"(?:\bin|\bat|\bnear|\baround|\bfrom)\s+((?:[A-Z][A-Za-z'-]+)(?:[ ]+[A-Z][A-Za-z'-]+){0,2})"),
    # A place heading the notice: "Kukatpally: delivery boys needed" (label words are in _LOCATION_STOP).
    re.compile(r"^\s*([A-Z][A-Za-z'-]{3,}(?:[ ][A-Z][A-Za-z'-]{3,})?)\s*[:\-–]\s", re.M),
    # A Devanagari or Telugu place name inside an English or Hinglish sentence: "needed in कुकटपल्ली".
    re.compile(rf"(?:\bin|\bat|\bnear|\baround|\bmein|\blo)\s+({_INDIC_WORD}(?:\s{_INDIC_WORD})?)"),
    # Place next to the city: "कुकटपल्ली, हैदराबाद", "Kukatpally, Hyderabad".
    re.compile(rf"({_INDIC_WORD}|[A-Z][A-Za-z'-]{{2,}})\s*,?\s*(?:हैदराबाद|హైదరాబాద్|Hyderabad|सिकंदराबाद|సికింద్రాబాద్|Secunderabad)(?![A-Za-z])"),
    re.compile(r"\b([A-Z][A-Za-z'-]{2,}(?:[ ][A-Z][A-Za-z'-]{2,})?)\s*(?:में|के पास|లో|దగ్గర|వద్ద|mein|me|mei|ke paas|lo)(?![A-Za-z])"),  # Latin place + Hindi/Telugu/Hinglish postposition
    re.compile(r"([ऀ-ॿ]{2,}(?:\s[ऀ-ॿ]{2,})?)\s*(?:में|के पास)"),
    re.compile(r"([ఀ-౿]{2,}(?:\s[ఀ-౿]{2,})?)\s*(?:లో|దగ్గర|వద్ద)"),
]
_LOCATION_STOP = {"need", "urgent", "hiring", "looking", "we", "our", "the", "a", "an", "office", "home", "salary", "shift", "day", "night",
                  "morning", "evening", "monday", "friday", "saturday", "sunday", "week", "month", "year", "react", "python", "english",
                  "hindi", "telugu", "hyderabad only", "job", "work", "any", "all", "class", "please", "contact", "call", "whatsapp",
                  "urgent", "urgently", "hiring", "opening", "openings", "vacancy", "notice", "requirement", "required", "wanted",
                  "note", "timings", "timing", "experience", "qualification", "budget", "title", "role", "position", "duration",
                  "location", "address", "area", "attention", "alert", "update", "details", "important",
                  # Devanagari / Telugu words that take में / లో but are not places
                  "घर", "ऑफिस", "दफ्तर", "दुकान", "शहर", "काम", "इस", "उस", "हमारे", "हमारी", "मेरे", "मेरी", "समय", "महीने", "हफ्ते",
                  "ఇంట్", "ఇంటి", "ఆఫీస్", "ఆఫీసు", "షాప్", "నగరం", "ఈ", "ఆ", "మా", "నెల", "వారం", "సమయం"}


def _first(pairs: tuple[tuple[str, re.Pattern[str]], ...], text: str) -> str | None:
    for value, pattern in pairs:
        if pattern.search(text):
            return value
    return None


def _all(pairs: tuple[tuple[str, re.Pattern[str]], ...], text: str) -> list[str]:
    return [value for value, pattern in pairs if pattern.search(text)]


# Hindi/Telugu grammar words: a "place" containing one is a phrase, not a name.
_PARTICLES = frozenset({"की", "का", "के", "को", "से", "पर", "और", "है", "हैं", "एक", "यह", "वह", "ని", "కి", "కు", "మరియు", "ఒక"})


def find_location(text: str) -> str | None:
    for pattern in _LOCATION:
        for m in pattern.finditer(text):
            candidate = m.group(1).strip(" .,")
            if candidate.lower() in _LOCATION_STOP or len(candidate) < 3:
                continue
            if candidate.split()[0].lower() in _LOCATION_STOP:
                continue
            if any(w in _PARTICLES for w in candidate.split()):
                continue  # "की बेकरी में" is "in the bakery", not a place
            return candidate[:80]
    return None


def find_title(text: str) -> str:
    lines = [ln.strip(" \t-•*#") for ln in text.splitlines() if ln.strip(" \t-•*#")]
    first = lines[0] if lines else text.strip()
    # A label line ("Job opening:", "Urgent -", "ज़रूरत है:") names no work;
    # the title is what follows it, on the same line or the next (FE1: titles
    # were cut at the first colon).
    first = strip_title_label(first)
    if not first and len(lines) > 1:
        first = strip_title_label(lines[1])
    first = re.split(r"(?<=[.!?।])\s+|।", first)[0].strip()
    if len(first) > 70:
        head = first.split(",")[0].strip()
        if len(head) >= 12:
            first = head
    if len(first) > MAX_TITLE:
        first = first[: MAX_TITLE - 1].rsplit(" ", 1)[0] + "…"
    return first.rstrip(".!:,।")


# ---- capabilities -----------------------------------------------------------

# Everyday words for a taxonomy slug the taxonomy's own aliases may not list.
_CAPABILITY_SYNONYMS: dict[str, tuple[str, ...]] = {
    "plumbing": ("plumber", "pipe", "tap", "leak", "leaking", "sink", "bathroom fitting", "प्लंबर", "नल", "ప్లంబర్", "పైపు"),
    "electrical": ("electrician", "wiring", "fan", "switch board", "mcb", "इलेक्ट्रीशियन", "बिजली", "ఎలక్ట్రీషియన్", "కరెంట్"),
    "home_repair": ("carpenter", "painter", "painting", "repair", "handyman", "मरम्मत", "बढ़ई", "వడ్రంగి", "రిపేర్"),
    "car_repair": ("mechanic", "car service", "garage", "मैकेनिक", "మెకానిక్"),
    "catering": ("caterer", "cook", "cooks", "chef", "food for", "meals", "खाना", "कैटरिंग", "వంట", "క్యాటరింగ్"),
    "events": ("event", "wedding", "function", "decor", "decoration", "शादी", "పెళ్ళి", "పెళ్లి", "ఈవెంట్"),
    "photography": ("photographer", "photo shoot", "photoshoot", "camera", "फोटोग्राफर", "ఫోటోగ్రాఫర్"),
    "video_editing": ("video editor", "reels", "editing", "वीडियो", "వీడియో"),
    "software": ("developer", "software", "programmer", "coding", "app", "backend", "full stack", "full-stack", "डेवलपर", "డెవలపర్", "సాఫ్ట్‌వేర్"),
    "react": ("react", "reactjs", "react.js", "frontend", "front-end", "next.js"),
    "python": ("python", "django", "fastapi", "flask"),
    "accounting": ("accountant", "accounts", "bookkeeping", "tally", "अकाउंटेंट", "అకౌంటెంట్"),
    "gst_filing": ("gst", "gst return", "जीएसटी", "జీఎస్టీ"),
    "tax": ("income tax", "itr", "tax filing", "टैक्स", "పన్ను"),
    "legal": ("lawyer", "advocate", "legal", "वकील", "లాయర్", "న్యాయవాది"),
    "property_law": ("property", "registration", "agreement", "sale deed", "प्रॉपर्टी", "ఆస్తి"),
    "tutoring": ("tutor", "tuition", "teacher", "teach", "ट्यूशन", "शिक्षक", "ట్యూషన్", "టీచర్"),
    "mathematics": ("maths", "math", "गणित", "గణితం"),
    "tailoring": ("tailor", "stitching", "blouse", "दर्जी", "सिलाई", "టైలర్", "కుట్టు"),
    "textiles": ("saree", "sarees", "fabric", "cloth", "साड़ी", "कपड़ा", "చీర", "చీరలు", "బట్టలు"),
    "wholesale": ("wholesale", "bulk", "थोक", "హోల్‌సేల్"),
    "sales": ("sales", "salesman", "sales executive", "telecaller", "marketing executive", "field sales", "सेल्स", "సేల్స్"),
    "marketing": ("marketing", "branding", "campaign", "मार्केटिंग", "మార్కెటింగ్"),
    "social_media": ("instagram", "social media", "facebook page", "सोशल मीडिया", "సోషల్ మీడియా"),
    "content_writing": ("content writer", "copywriter", "blog", "articles", "लेखक", "కంటెంట్ రైటర్"),
    "delivery": ("delivery", "delivery boy", "delivery partner", "rider", "डिलीवरी", "డెలివరీ"),
    "logistics": ("logistics", "transport", "driver", "ड्राइवर", "డ్రైవర్"),
    "bakery": ("baker", "bakery", "cake", "cakes", "बेकरी", "केक", "బేకరీ", "కేక్"),
    "interior_design": ("interior", "interiors", "इंटीरियर", "ఇంటీరియర్"),
    "architecture": ("architect", "3d visualiser", "3d visualizer", "elevation", "floor plan", "आर्किटेक्ट", "ఆర్కిటెక్ట్"),
    "printing": ("printing", "flex", "banner", "visiting cards", "प्रिंटिंग", "ప్రింటింగ్"),
    "yoga": ("yoga", "योग", "యోగా"),
    "health_wellness": ("nurse", "physiotherapist", "physio", "caretaker", "wellness", "नर्स", "నర్స్"),
    "handicraft": ("handicraft", "handmade", "craft", "हस्तशिल्प", "హస్తకళ"),
    "education": ("school", "teacher", "faculty", "स्कूल", "పాఠశాల"),
    "product_management": ("product manager", "product management"),
    "startup": ("startup", "co-founder", "cofounder", "स्टार्टअप", "స్టార్టప్"),
}


# Nouns that turn a skill word into a description of data or a screen:
# "sales charts", "marketing report", "delivery status", "event list".
_DATA_NOUN_AFTER = re.compile(
    # Not "dashboard", "page" or "screen": in "React dashboard" the skill is
    # React and the dashboard is what gets built.
    r"^[\s-]*(?:and\s+\w+\s+)?(?:charts?|graphs?|reports?|data|figures|numbers|analytics|stats|statistics|trends?|"
    r"forecasts?|summary|summaries|kpis?|metrics|records?|entries|history|status|tracking|tracker|totals?|"
    r"चार्ट|रिपोर्ट|डेटा|आंकड़े|చార్ట్|రిపోర్ట్|డేటా)(?![a-z])",
    re.I,
)
# Verbs that make what follows data, not a trade: "show daily sales", "track deliveries".
_DATA_VERB_BEFORE = re.compile(r"\b(?:show|shows|showing|display|displays|track|tracks|tracking|monitor|monitors|analy[sz]e|plot|plots)\s+(?:\w+\s+){0,2}$", re.I)


def _data_context(low: str, m: re.Match[str]) -> bool:
    after = low[m.end(): m.end() + 30]
    before = low[max(0, m.start() - 40): m.start()]
    return bool(_DATA_NOUN_AFTER.match(after) or _DATA_VERB_BEFORE.search(before))


def capability_mentioned_only_as_data(text: str, term: dict[str, Any]) -> bool:
    """True when every literal mention of this skill in the text is data
    ("sales charts"), so a reader — Claude included — should not list it.
    False when it is mentioned as a skill, or not literally at all (Claude may
    map a Hindi or Telugu description to a slug by meaning)."""
    low = text.lower()
    slug = term["slug"]
    words = {slug.replace("_", " "), slug.replace("-", " ")}
    for key in ("name_en", "name_hi", "name_te"):
        if term.get(key):
            words.add(str(term[key]).lower())
    words.update(str(a).lower() for a in (term.get("aliases") or []) if a)
    words.update(_CAPABILITY_SYNONYMS.get(slug, ()))
    words = {w for w in words if len(w) >= 3}
    if not words:
        return False
    matches = list(_kw(*sorted(words, key=len, reverse=True)).finditer(low))
    return bool(matches) and all(_data_context(low, m) for m in matches)


def find_capabilities(text: str, terms: list[dict[str, Any]]) -> list[str]:
    """Slugs whose slug, localized names, taxonomy aliases or everyday
    synonyms appear in the text. Returns capability slugs only."""
    low = text.lower()
    hits: list[tuple[int, str]] = []
    for term in terms:
        slug = term["slug"]
        words = {slug.replace("_", " "), slug.replace("-", " ")}
        for key in ("name_en", "name_hi", "name_te"):
            if term.get(key):
                words.add(str(term[key]).lower())
        words.update(str(a).lower() for a in (term.get("aliases") or []) if a)
        words.update(_CAPABILITY_SYNONYMS.get(slug, ()))
        words = {w for w in words if len(w) >= 3}
        if not words:
            continue
        pattern = _kw(*sorted(words, key=len, reverse=True))
        # A mention counts only in a skill sense: "sales executive" is a
        # trade, "sales charts" is data on a dashboard (FE1).
        m = next((m for m in pattern.finditer(low) if not _data_context(low, m)), None)
        if m:
            hits.append((m.start(), slug))
    hits.sort()
    out: list[str] = []
    for _, slug in hits:
        if slug not in out:
            out.append(slug)
    return out


# ---- the draft --------------------------------------------------------------

def _local_date(text: str) -> str | None:
    low = text.lower()
    today = date.today()
    if re.search(r"\b(today|aaj)\b|आज|ఈరోజు", low):
        return today.isoformat()
    if re.search(r"\b(tomorrow|kal)\b|कल|రేపు", low):
        return (today + timedelta(days=1)).isoformat()
    m = re.search(r"\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b", low)
    if m:
        d, mo = int(m.group(1)), int(m.group(2))
        y = int(m.group(3)) if m.group(3) else today.year
        y = y + 2000 if y < 100 else y
        try:
            return date(y, mo, d).isoformat()
        except ValueError:
            return None
    return None


_CONTACT_LEAD = re.compile(
    r"(?:\b(?:or|and)\s+|या\s+|లేదా\s+)?(?:\b(?:call|contact|whatsapp|wa|ph|phone|mob|mobile|email|e-mail|mail)\b|संपर्क|कॉल|ఫోన్|కాల్)?(?:\s*\b(?:us|me|on|at|to|now|directly)\b)*\s*[:\-]?\s*\[(?:phone|email)\](?:\s+for\s+(?:more\s+)?(?:details|info\w*|enquir\w*))?",
    re.I,
)


def strip_contacts(text: str) -> str:
    """A public description never carries a phone number or e-mail; contact
    goes through Vyapar's own response method and disclosure controls."""
    cleaned = _CONTACT_LEAD.sub("", redact_contacts(text))
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+([.,;!?।])", r"\1", cleaned)
    cleaned = re.sub(r"([.,;।])\s*(?:or|and|या|లేదా)?\s*([.,;।])", r"\1", cleaned)
    return cleaned.strip(" ,;\n")


def draft_from_text(text: str, terms: list[dict[str, Any]], force_type: str | None = None) -> dict[str, Any]:
    """`force_type` reads the text as that type (posting tips read a posted
    job's description as a job, whatever its words suggest)."""
    text = text.strip()
    type_, type_conf = (force_type, 1.0) if force_type else detect_type(text)
    title = find_title(text)
    location = find_location(text)
    work_mode = _first(_WORK_MODE, text.lower())
    capabilities = find_capabilities(text, terms)
    lo, hi, period = find_money(text)
    confidence: dict[str, float] = {
        "type": type_conf,
        "title": 0.6 if len(title) <= 80 else 0.4,
        "description": 0.9,
    }
    draft: dict[str, Any] = {
        "type": type_,
        "title": title,
        "description": strip_contacts(text)[:MAX_DESCRIPTION],
        "location": location,
        "work_mode": work_mode,
        "timing": None,
        "required_capabilities": capabilities,
    }
    if location:
        confidence["location"] = 0.55
    if work_mode:
        confidence["work_mode"] = 0.6
    if capabilities:
        confidence["required_capabilities"] = 0.65

    low = text.lower()
    if type_ == "employment":
        xmin, xmax = find_experience_months(text)
        openings = find_openings(text)
        timings = find_timings(text)
        qualification = find_qualification(text)
        interview = _INTERVIEW.search(text)
        monthly_lo, monthly_hi = (lo, hi) if period in (None, "monthly") else (
            (lo * 26 if lo else None, hi * 26 if hi else None) if period == "daily" else (None, None)
        )
        draft["employment"] = {
            "salary_min_rupees": monthly_lo,
            "salary_max_rupees": monthly_hi,
            "incentive_type": _first(_INCENTIVE, low) or ("none" if (monthly_lo or monthly_hi) else None),
            "openings": openings,
            "shift": _first(_SHIFT, low),
            "job_timings": timings,
            "interview_details": interview.group(0).strip() if interview else None,
            "min_qualification": qualification,
            "english_level": _first(_ENGLISH, low),
            "experience_min_months": xmin,
            "experience_max_months": xmax,
            "fresher_ok": xmin == 0,
            "requires_assets": _all(_ASSETS, low),
        }
        for key, present in (("salary", monthly_lo or monthly_hi), ("openings", openings), ("job_timings", timings),
                             ("interview_details", interview), ("min_qualification", draft["employment"]["min_qualification"]),
                             ("english_level", draft["employment"]["english_level"]), ("experience", xmin is not None),
                             ("shift", draft["employment"]["shift"]), ("requires_assets", draft["employment"]["requires_assets"])):
            if present:
                confidence[key] = 0.6
    elif type_ == "freelance":
        hourly = period == "hourly"
        draft["freelance"] = {
            "budget_type": "hourly" if hourly else ("fixed" if (lo or hi) else None),
            "budget_min_rupees": None if hourly else lo,
            "budget_max_rupees": None if hourly else hi,
            "hourly_rate_min_rupees": lo if hourly else None,
            "hourly_rate_max_rupees": hi if hourly else None,
            "duration": _first(_DURATION, low),
            "experience_level": _first(_LEVEL, low),
            "screening_questions": [q.strip() for q in _QUESTION.findall(text)][:3],
        }
        if lo or hi:
            confidence["budget"] = 0.6
            confidence["budget_type"] = 0.6
        if draft["freelance"]["duration"]:
            confidence["duration"] = 0.55
        if draft["freelance"]["experience_level"]:
            confidence["experience_level"] = 0.5
    elif type_ == "local_service":
        urgency = "today" if _URGENT_TODAY.search(low) else "this_week" if _THIS_WEEK.search(low) else None
        draft["local_service"] = {
            "preferred_date": _local_date(text),
            "budget_rupees": hi or lo,
            "urgency": urgency,
        }
        if urgency:
            confidence["urgency"] = 0.6
        if draft["local_service"]["preferred_date"]:
            confidence["preferred_date"] = 0.6
        if hi or lo:
            confidence["budget"] = 0.55
    else:
        timings = find_timings(text)
        if timings:
            draft["timing"] = timings
            confidence["timing"] = 0.5
    draft["confidence"] = confidence
    draft["missing"] = []
    return draft


# ---- shortlist (rules) ------------------------------------------------------

_MAX_SCORE = sum(DEFAULT_WEIGHTS[k] for k in ("capability_fit", "location_fit", "experience_fit", "trust_fit", "timing_fit", "value_fit"))


def rank_applicant(opportunity: dict[str, Any], a: dict[str, Any]) -> dict[str, Any]:
    """One applicant's 1–10 score from the allow-listed ranking signals.
    `a` carries only structured facts (see services/ai.py) — never a name."""
    wanted = set(opportunity.get("required_capabilities") or [])
    have = set(a.get("capabilities") or [])
    overlap = len(wanted & have)
    capability_fit = overlap / len(wanted) if wanted else (0.5 if have else 0.2)
    distance = a.get("distance_km")
    remote = opportunity.get("work_mode") == "remote"
    location_fit = 1.0 if remote else (max(0.0, 1.0 - distance / 25.0) if distance is not None else 0.3)
    years = a.get("experience_years")
    need_months = opportunity.get("experience_min_months")
    unrelated = bool(wanted) and overlap == 0  # experience in another trade is not experience for this work
    if years is None or unrelated:
        experience_fit = 0.3 if years is None else 0.1
    elif need_months:
        experience_fit = min(1.0, (years * 12) / need_months)
    else:
        experience_fit = min(1.0, 0.4 + years / 10.0)
    trust_fit = 1.0 if a.get("verified") else 0.4 if a.get("has_profile") else 0.1
    timing_fit = {"now": 1.0, "this_week": 0.7, "later": 0.3}.get(a.get("availability") or "", 0.5)
    bid, value = a.get("bid_rupees"), opportunity.get("value_rupees")
    if bid and value:
        value_fit = 1.0 if bid <= value else max(0.0, 1.0 - (bid - value) / value)
    else:
        value_fit = 0.5
    signals = RankingSignals(
        capability_fit=capability_fit, location_fit=location_fit, experience_fit=experience_fit,
        trust_fit=trust_fit, timing_fit=timing_fit, value_fit=value_fit,
    )
    match_score = max(1, min(10, int(round(1 + 9 * score(signals) / _MAX_SCORE))))
    if unrelated:
        match_score = min(match_score, 3)  # nearby and verified never outranks "cannot do this work"
    reasons = [k for k in top_signal_keys(signals, 3) if k in REASON_CODES and getattr(signals, k) >= 0.6]
    if wanted and overlap < len(wanted):
        # [Backend A, 2026-09-29] exactly one skills verdict per applicant: a
        # partial overlap (2 of 3 = 0.67) is the partial_capability_overlap
        # risk below, never also "has the skills this needs".
        reasons = [k for k in reasons if k != "capability_fit"]
    if bid and value and bid <= value and "bid_within_budget" not in reasons:
        reasons.append("bid_within_budget")
    if a.get("cover_text") and len(a["cover_text"]) >= 120 and len(reasons) < 3:
        reasons.append("cover_text_specific")
    risks: list[str] = []
    if wanted and overlap == 0:
        risks.append("no_capability_overlap")
    elif wanted and overlap < len(wanted):
        risks.append("partial_capability_overlap")
    if not remote and distance is not None and distance > 25:
        risks.append("far_away")
    if not a.get("has_profile"):
        risks.append("no_public_profile")
    elif not a.get("verified"):
        risks.append("unverified")
    if not a.get("cover_text"):
        risks.append("no_cover_text")
    if bid and value and bid > value:
        risks.append("bid_above_budget")
    if bid and value and bid < value * 0.4:
        risks.append("bid_far_below_budget")
    if years is None and a.get("has_profile"):
        risks.append("no_experience_listed")
    if a.get("availability") == "later":
        risks.append("not_available_now")
    return {"ref": a["ref"], "match_score": match_score, "reasons": reasons[:3], "risks": risks[:3], "summary": None}


# ---- posting tips (rules) ---------------------------------------------------

def rule_tips(draft: dict[str, Any]) -> list[dict[str, Any]]:
    """The tips every deployment gives, from the draft alone. Codes come from
    vocab.TIP_CODES; the service adds the localized text."""
    t = draft.get("type") or "employment"
    e, f, s = draft.get("employment") or {}, draft.get("freelance") or {}, draft.get("local_service") or {}
    tips: list[tuple[str, str]] = []
    title = draft.get("title") or ""
    if not title:
        tips.append(("add_title", "high"))
    elif len(title) > 80:
        tips.append(("shorten_title", "medium"))
    if len(draft.get("description") or "") < 80:
        tips.append(("add_description", "high"))
    if not draft.get("location") and draft.get("work_mode") != "remote":
        tips.append(("add_location", "high"))
    if not draft.get("required_capabilities"):
        tips.append(("add_capabilities", "high"))
    elif len(draft.get("required_capabilities") or []) > 4:
        tips.append(("fewer_capabilities", "medium"))
    if t == "employment":
        if not (e.get("salary_min_paise") or e.get("salary_max_paise")):
            tips.append(("add_salary", "high"))
        if not e.get("job_timings"):
            tips.append(("add_job_timings", "medium"))
        if not e.get("openings"):
            tips.append(("add_openings", "low"))
        if e.get("min_qualification") in ("graduate", "postgraduate"):
            tips.append(("lower_min_qualification", "medium"))
        if e.get("english_level") in ("good", "fluent"):
            tips.append(("relax_english_level", "medium"))
        if (e.get("experience_min_months") or 0) > 24:
            tips.append(("reduce_experience", "medium"))
        if not e.get("interview_details"):
            tips.append(("add_interview_details", "low"))
        if e.get("incentive_type") in ("fixed_plus_incentive", "incentive_only") and "incentive" not in (draft.get("description") or "").lower():
            tips.append(("mention_incentives", "low"))
        if draft.get("work_mode") == "on_site" and draft.get("location"):
            tips.append(("set_remote_or_both", "low"))
    elif t == "freelance":
        if f.get("budget_type") == "hourly":
            if not (f.get("hourly_rate_min_paise") or f.get("hourly_rate_max_paise")):
                tips.append(("add_hourly_rate", "high"))
        elif not (f.get("budget_min_paise") or f.get("budget_max_paise")):
            tips.append(("add_budget", "high"))
        if not f.get("duration"):
            tips.append(("add_duration", "medium"))
        if not f.get("screening_questions"):
            tips.append(("add_screening_questions", "low"))
        if draft.get("work_mode") == "on_site":
            tips.append(("set_remote_or_both", "medium"))
    elif t == "local_service":
        if not s.get("preferred_date"):
            tips.append(("add_preferred_date", "medium"))
        if not s.get("urgency"):
            tips.append(("set_urgency", "medium"))
        if not s.get("budget_paise"):
            tips.append(("add_budget", "medium"))
    else:
        if not draft.get("timing"):
            tips.append(("add_timing", "medium"))
    if not draft.get("deadline"):
        tips.append(("add_deadline", "low"))
    order = {"high": 0, "medium": 1, "low": 2}
    tips.sort(key=lambda x: order[x[1]])
    return [{"code": code, "impact": impact, "text": None} for code, impact in tips]


# ---- proposal (rules) -------------------------------------------------------

def proposal_improvements(opportunity: dict[str, Any], text: str, applicant: dict[str, Any]) -> list[str]:
    low = (text or "").lower()
    out: list[str] = []
    matched = set(opportunity.get("required_capabilities") or []) & set(applicant.get("capabilities") or [])
    if matched and not any(m.replace("_", " ") in low for m in matched):
        out.append("mention_matching_skills")
    if applicant.get("experience_years") and (matched or not opportunity.get("required_capabilities")) and not re.search(r"\byears?\b|\byrs?\b|साल|సంవత్సర", low):
        out.append("mention_experience")
    if not re.search(r"available|start|from|join|तुरंत|available|అందుబాటు|వెంటనే", low):
        out.append("state_availability")
    if opportunity.get("type") in ("freelance", "local_service") and not re.search(r"₹|rs\b|rupee|price|rate|charge|quote|बजट|రూ", low):
        out.append("state_price")
    questions = [str(q.get("text") if isinstance(q, dict) else q) for q in opportunity.get("screening_questions") or [] if q]
    if questions and not any(q[:20].lower() in low for q in questions):
        out.append("answer_screening_questions")
    if len(text or "") > 900:
        out.append("keep_it_short")
    if re.search(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)|@", text or ""):
        out.append("remove_contact_details")
    if len(text or "") < 60:
        out.append("be_specific_to_this_work")
    return out[:4]


class RulesProvider:
    name = "rules"

    async def draft_opportunity(self, text: str, language: str, entry: str, capability_terms: list[dict[str, Any]]) -> AiResult:
        return AiResult(data=draft_from_text(text, capability_terms), provider=self.name, model=None)

    async def read_opportunity_image(self, image: ImageInput, language: str, capability_terms: list[dict[str, Any]]) -> AiResult:
        raise AiUnavailable("unsupported_without_ai")

    async def shortlist(self, opportunity: dict[str, Any], applicants: list[dict[str, Any]], language: str) -> AiResult:
        return AiResult(data={"applicants": [rank_applicant(opportunity, a) for a in applicants]}, provider=self.name)

    async def posting_tips(self, draft: dict[str, Any], rule_tips_: list[dict[str, Any]], language: str) -> AiResult:
        return AiResult(data={"tips": rule_tips_}, provider=self.name)

    async def improve_proposal(self, opportunity: dict[str, Any], text: str, applicant: dict[str, Any], language: str) -> AiResult:
        return AiResult(
            data={"cover_text": None, "improvements": proposal_improvements(opportunity, text, applicant)},
            provider=self.name,
        )


__all__ = ["RulesProvider", "draft_from_text", "rank_applicant", "rule_tips", "proposal_improvements", "has_value", "DURATIONS"]

"""Bounded, text-only detection heuristics (SP064 / DEC-V1-006).

# What this module IS: a handful of cheap regular expressions over the text of
# one message, run at send time, producing zero or more `Signal`s. Each signal
# names its type and the *class* of pattern that matched — never the matched
# text, never the message.
#
# What this module is NOT, structurally: it imports no database session, no
# other component, and no media library. It cannot read Home Circle
# relationship data or Trust evidence because it has no way to query anything
# (SP064's "absence, not an unused capability"), and it cannot scan an image
# because it only ever receives a `str`.
#
# The categories are DEC-V1-006's own Tier 2/3/4 examples: off-platform
# pressure, financial manipulation / romance-scam indicators, explicit sexual
# solicitation, and self-declared-minor phrases. Nothing broader.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

__all__ = ["Signal", "scan_text"]


@dataclass(frozen=True, slots=True)
class Signal:
    signal_type: str
    pattern_class: str


# Indian mobile numbers: optional +91 / 0, then a 10-digit number starting 6-9,
# with spaces, dashes or dots allowed between groups.
# Grouped 3-3-4 ("987 654 3210") or 5-5 ("98765 43210", the most common way
# Indians write a mobile number), or unbroken.
_PHONE: Final = re.compile(
    r"(?<!\d)(?:\+?91[\s\-.]?|0)?[6-9](?:\d{2}[\s\-.]?\d{3}[\s\-.]?\d{4}|\d{4}[\s\-.]?\d{5})(?!\d)"
)
# UPI virtual payment address: name@handle where the handle is a known PSP.
_UPI: Final = re.compile(
    r"\b[a-z0-9._\-]{2,}@(?:upi|ybl|okaxis|oksbi|okhdfcbank|okicici|paytm|apl|ibl|axl|"
    r"phonepe|gpay|fam|freecharge|airtel|jio|sbi|hdfcbank|icici|axisbank|kotak|"
    r"indus|federal|barodampay|cnrb|pnb|boi|uco|idfcfirst)\b",
    re.IGNORECASE,
)
_MONEY_ASK: Final = re.compile(
    r"\b(?:send|transfer|lend|give|need|want|pay)\b[^.?!\n]{0,40}?"
    r"(?:₹|rs\.?|rupees?|inr|money|cash|paise|lakh|lakhs|crore)\b"
    r"|\b(?:₹|rs\.?)\s?\d[\d,]*\b[^.?!\n]{0,30}?\b(?:send|transfer|urgent|urgently|need)\b"
    r"|\b(?:gift\s?card|western\s?union|bitcoin|crypto|usdt)\b",
    re.IGNORECASE,
)
_OFF_PLATFORM: Final = re.compile(
    r"\b(?:whatsapp|whats\s?app|wa\.me|telegram|t\.me|signal\s+app|snap(?:chat)?|insta(?:gram)?\s+(?:me|id|dm)|"
    r"dm\s+me\s+on|text\s+me\s+on|call\s+me\s+on|message\s+me\s+on|"
    r"my\s+(?:whatsapp|telegram|insta(?:gram)?)\s+(?:is|number|id))\b",
    re.IGNORECASE,
)
_SEXUAL: Final = re.compile(
    r"\b(?:send\s+(?:me\s+)?(?:nudes?|nude\s+pics?|naked\s+(?:pics?|photos?)|sexy\s+(?:pics?|photos?))|"
    r"nudes?\b|sexting|video\s+sex|phone\s+sex|cam\s+sex|"
    r"(?:have|want)\s+sex\s+with|hook\s?up\s+tonight|one\s+night\s+stand)\b",
    re.IGNORECASE,
)
# "I'm 16", "I am 17 years", "im only 15", "main 16 saal ki hoon", "nenu 17".
_MINOR: Final = re.compile(
    r"\b(?:i\s*am|i'?m|im|iam|main|mai|mein|nenu|naa\s+age|my\s+age\s+is|age\s*[:=]?)\s*"
    r"(?:only\s+|just\s+)?(?:1[0-7])\b(?!\s*(?:lakh|k\b|,|\d))"
    r"|\b(?:1[0-7])\s*(?:years?\s*old|yrs?\s*old|saal\s*k[ia]|saal\s+ki\s+hoon|sanvatsara)\b"
    r"|\b(?:class|std|standard)\s*(?:9|10|11|12|ix|x|xi|xii)(?:th)?\b\s*(?:student|me|mein|lo)?"
    r"|\bschool\s+(?:student|girl|boy|jaati|jata)\b",
    re.IGNORECASE,
)

_RULES: Final[tuple[tuple[str, str, re.Pattern[str]], ...]] = (
    ("self_declared_minor", "minor_phrase", _MINOR),
    ("sexual_solicitation", "sexual_keyword", _SEXUAL),
    ("money_ask", "money_request_phrase", _MONEY_ASK),
    ("contact_upi_id", "upi_vpa", _UPI),
    ("contact_phone_number", "indian_mobile_number", _PHONE),
    ("off_platform_push", "messaging_app_mention", _OFF_PLATFORM),
)


def scan_text(content: str) -> list[Signal]:
    """Return every signal the text triggers, most severe first. Pure function."""
    if not content:
        return []
    text = content.strip()
    if len(text) > 4000:
        text = text[:4000]
    found: list[Signal] = []
    for signal_type, pattern_class, pattern in _RULES:
        if pattern.search(text):
            found.append(Signal(signal_type, pattern_class))
    return found

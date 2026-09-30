# [Trust pack, 2026-09-30 — VISION-2040 item 1] Scam shield: "nobody charges
# job seekers", on every text a poster writes.
#
# Why: a fee before the job (registration, security deposit, uniform/kit,
# training, "processing") is the top fear of Indian job seekers, and it is
# written in English, Hindi, Telugu and Hinglish, often as "pay ₹500 on GPay
# 98xxxxxxxx". Workstream B's check matched a phrase list and also caught the
# honest "We pay ₹18,000 a month" (its "pay ₹" / "pay rs" entries). This
# module replaces the matching with named rules that each say who pays whom:
#
#   fee_phrase      a named charge on the applicant: registration fee, security
#                   deposit, kit/uniform charge, training fee, joining fee,
#                   processing/placement/interview/form fee, caution money ...
#                   in en/hi/te and Hinglish ("registration fees dena hoga").
#   applicant_pays  the applicant is told to pay or deposit an amount:
#                   "candidates must pay ₹2,000", "pehle 500 rupay jama karo",
#                   "₹1000 dena padega", "పెట్టుబడిగా ₹2000 కట్టాలి".
#   pay_before      money before joining / interview / the job starts.
#   phone_payment   a phone number together with a payment app or a
#                   send/transfer instruction ("send ₹300 on PhonePe to
#                   9876543210"). A phone number next to a salary is fine.
#
# Two tiers:
#   * HIRING — the post itself, its screening questions and interview
#     details, and the poster's replies in an application thread. Every rule.
#   * OFFER — a professional's priced package. Charging a client for a
#     service is the point of a package, so only a charge tied to getting a
#     JOB (placement fee, "pay and get a job", registration fee for the job)
#     or a phone-plus-payment instruction is refused.
#
# The check never stores the text. A refusal is logged as a trust event
# (audit_events, action `trust.seeker_charge_blocked`, outcome `rejected`)
# on its own connection, because the refusal rolls the request back.
# Test corpus: scripts/check_trust_pack.py (SCAM_CORPUS / CLEAN_CORPUS).
# Traces to: FR11, FR22, FR39, FR40, SP040, VISION-2040 item 1
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

from app.errors import ApiError

Tier = Literal["hiring", "offer"]

# --------------------------------------------------------------------------
# Vocabulary. Kept as words, joined into regexes once. Latin text is matched
# case-insensitively on word boundaries; Devanagari and Telugu are matched as
# substrings (their vowel signs are combining marks, so \b does not apply).
# --------------------------------------------------------------------------
_CHARGE_NOUNS_EN = r"(?:fees?|charges?|amount|money|deposit|payment|paisa|paise|rupees?|rs\.?)"
_FEE_KINDS_EN = (
    r"registration|regn|reg\.?|joining|processing|placement|interview|application|form|document(?:ation)?|verification|"
    r"medical|training|kit|uniform|id\s*card|onboarding|enrol(?:l)?ment|file|security|caution|refundable|admission|"
    r"certificate|visa|agent|consultancy|job\s*guarantee|guarantee"
)
# "registration fee", "kit charge", "uniform deposit", "security deposit", "caution money"
_FEE_PHRASE_EN = re.compile(rf"\b(?:{_FEE_KINDS_EN})\s*(?:-|\s)?\s*{_CHARGE_NOUNS_EN}\b", re.I)
_FEE_STANDALONE_EN = re.compile(
    r"\b(?:security\s+deposit|caution\s+(?:money|deposit)|refundable\s+deposit|advance\s+payment|pay\s+in\s+advance|"
    r"pay\s+to\s+apply|candidates?\s+pays?|applicants?\s+pays?|laptop\s+deposit)\b", re.I)

_FEE_PHRASE_HI = (
    "पंजीकरण शुल्क", "रजिस्ट्रेशन फीस", "रजिस्ट्रेशन शुल्क", "रजिस्ट्रेशन चार्ज", "जमानत राशि", "सिक्योरिटी डिपॉजिट",
    "सिक्योरिटी मनी", "किट शुल्क", "किट चार्ज", "किट के पैसे", "यूनिफॉर्म शुल्क", "यूनिफॉर्म चार्ज", "यूनिफ़ॉर्म के पैसे",
    "प्रशिक्षण शुल्क", "ट्रेनिंग फीस", "ट्रेनिंग चार्ज", "जॉइनिंग फीस", "ज्वाइनिंग फीस", "प्रोसेसिंग फीस", "फॉर्म फीस",
    "अग्रिम भुगतान", "उम्मीदवार भुगतान", "इंटरव्यू फीस", "प्लेसमेंट फीस",
)
_FEE_PHRASE_TE = (
    "రిజిస్ట్రేషన్ ఫీజు", "రిజిస్ట్రేషన్ ఛార్జ్", "సెక్యూరిటీ డిపాజిట్", "కిట్ ఫీజు", "కిట్ ఛార్జ్", "యూనిఫాం ఫీజు",
    "యూనిఫాం ఛార్జ్", "శిక్షణ ఫీజు", "ట్రైనింగ్ ఫీజు", "జాయినింగ్ ఫీజు", "ప్రాసెసింగ్ ఫీజు", "ముందస్తు చెల్లింపు",
    "అభ్యర్థి చెల్లించాలి", "ఇంటర్వ్యూ ఫీజు", "ప్లేస్‌మెంట్ ఫీజు", "డిపాజిట్ కట్టాలి",
)

# A money amount with its currency written next to it (so "10th pass" or
# "2 openings" is never read as money).
_MONEY = (r"(?:(?:₹|rs\.?|inr|rupees?)\s*\d[\d,]*(?:\.\d+)?"
          r"|\d[\d,]*(?:\.\d+)?\s*(?:/-|rs\b|rupees?|rupay|rupaye|rupiya|रुपये|रुपए|रुपया|రూపాయలు|రూ))")
# The applicant is the one paying: "(you|candidates|applicants) (must|have to|need to|should)? (pay|deposit|transfer)".
_APPLICANT_PAYS_EN = re.compile(
    r"\b(?:you|candidates?|applicants?|job\s*seekers?|selected\s+(?:candidates?|people)|freshers?)\s+"
    r"(?:will\s+)?(?:must|have\s+to|has\s+to|need\s+to|needs\s+to|should|are\s+required\s+to|is\s+required\s+to)?\s*"
    r"(?:pay|deposit|transfer)\b", re.I)
# Hinglish: "registration fees dena hoga", "paise dene honge", "deposit karna padega", "500 rupay jama karo"
_HINGLISH_FEE_VERB = re.compile(
    r"\b(?:fees?|paise|paisa|rupay|rupaye|rupees|charges?|deposit)\s+(?:bhi\s+)?(?:jama\s+)?"
    r"(?:karna|karni|karne|karo|karein|kariye|dena|dene|deni|do|dijiye|bharna|bharo|bharni|lagega|lagegi|lagenge)\b", re.I)
_HINGLISH_MONEY_VERB = re.compile(
    _MONEY + r"[^.\n]{0,15}?\b(?:jama|deposit|pay|bharna|bharo|dena|dene|do)\s*(?:karna|karo|karein|kariye|karne|hoga|padega|honge)?\b", re.I)
_HI_MONEY = ("रुपये", "रुपए", "₹", "पैसे", "फीस", "शुल्क", "डिपॉजिट")
_HI_PAY = ("जमा करना होगा", "जमा करने होंगे", "जमा करें", "जमा कराने होंगे", "देने होंगे", "देना होगा", "देनी होगी",
           "भुगतान करना होगा", "भरना होगा", "भरने होंगे")
_TE_MONEY = ("₹", "రూపాయలు", "డబ్బు", "డబ్బులు", "ఫీజు", "డిపాజిట్")
_TE_PAY = ("కట్టాలి", "చెల్లించాలి", "జమ చేయాలి", "ఇవ్వాలి")
# Money before the job: "pay ₹500 before joining", "before the interview, deposit ..."
_PAY_BEFORE_EN = re.compile(
    r"\b(?:pay|deposit|transfer|send)\b[^.\n]{0,40}\bbefore\s+(?:joining|the\s+interview|interview|starting|you\s+start|the\s+job|training)\b"
    r"|\bbefore\s+(?:joining|the\s+interview|interview)\b[^.\n]{0,30}\b(?:pay|deposit)\b", re.I)
_PHONE = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)")
_PAYMENT_APP = r"(?:upi|g\s?pay|google\s*pay|phone\s?pe|paytm|bhim|upi\s*id|qr\s*code)"
_PHONE_TEXT = r"(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}"
# "send ₹300 to ...", "transfer 500 rs", "pay ₹500 on GPay / to 98765 43210"
_SEND_MONEY = re.compile(
    r"\b(?:send|transfer)\b[^.\n]{0,20}" + _MONEY
    + r"|\bpay\s+" + _MONEY + r"\s+(?:to|on|via|through|at|in)\s+(?:(?:this|my|our|the)\s+)?(?:number\s+)?(?:"
    + _PAYMENT_APP + "|" + _PHONE_TEXT + ")",
    re.I)
_APP_NEAR_MONEY = re.compile(r"\b(?:pay|send|transfer|jama)\b[^.\n]{0,30}\b" + _PAYMENT_APP + r"\b", re.I)
# A charge tied to getting a JOB (the only rule set a priced package, a
# training course or a community post gets).
_JOB_WORDS = r"(?:job|naukri|placement|joining|posting|appointment|offer\s+letter|selection)"
_JOB_FEE_EN = re.compile(
    r"\b(?:placement|job\s*guarantee|joining|appointment|selection|offer\s+letter)\s*(?:fees?|charges?|amount|money|deposit)\b"
    r"|\bpay\b[^.\n]{0,30}\b(?:get|guaranteed?)\b[^.\n]{0,15}\b" + _JOB_WORDS
    + r"|\b(?:registration|security|deposit)\b[^.\n]{0,20}\bfor\s+(?:the\s+|a\s+)?" + _JOB_WORDS, re.I)
_JOB_FEE_HI_TE = ("नौकरी के लिए फीस", "नौकरी के लिए पैसे", "नौकरी पक्की", "प्लेसमेंट फीस", "जॉइनिंग फीस",
                  "ఉద్యోగం కోసం ఫీజు", "ప్లేస్‌మెంట్ ఫీజు", "జాయినింగ్ ఫీజు", "ఉద్యోగం గ్యారంటీ")


@dataclass(frozen=True)
class ScamMatch:
    rule: str      # fee_phrase | applicant_pays | pay_before | phone_payment | job_fee
    matched: str   # the matched words (never the whole text)


def _normalise(text: str) -> str:
    text = unicodedata.normalize("NFC", text or "")
    return re.sub(r"\s+", " ", text).strip()


def _first(pattern: re.Pattern, text: str) -> str | None:
    m = pattern.search(text)
    return m.group(0).strip() if m else None


def _first_word(words: tuple[str, ...], text: str) -> str | None:
    return next((w for w in words if w in text), None)


def _near(words_a: tuple[str, ...], words_b: tuple[str, ...], text: str, window: int = 40) -> str | None:
    """A word of `words_b` with a word of `words_a` at most `window`
    characters before it: "500 रुपये जमा करने होंगे", "₹2000 కట్టాలి"."""
    for b in words_b:
        i = text.find(b)
        while i != -1:
            if any(a in text[max(0, i - window):i] for a in words_a):
                return text[max(0, i - window):i + len(b)].strip()
            i = text.find(b, i + 1)
    return None


def detect(text: str | None, tier: Tier = "hiring") -> ScamMatch | None:
    """The first rule the text breaks, or None. Pure; never raises."""
    t = _normalise(text or "")
    if not t:
        return None
    if tier == "hiring":
        hit = (_first(_FEE_PHRASE_EN, t) or _first(_FEE_STANDALONE_EN, t)
               or _first_word(_FEE_PHRASE_HI, t) or _first_word(_FEE_PHRASE_TE, t))
        if hit:
            return ScamMatch("fee_phrase", hit)
        m = _APPLICANT_PAYS_EN.search(t)
        if m and re.search(_MONEY, t[m.start():m.start() + 80], re.I):
            return ScamMatch("applicant_pays", m.group(0).strip())
        hit = (_first(_HINGLISH_FEE_VERB, t) or _first(_HINGLISH_MONEY_VERB, t)
               or _near(_HI_MONEY, _HI_PAY, t) or _near(_TE_MONEY, _TE_PAY, t))
        if hit:
            return ScamMatch("applicant_pays", hit)
        hit = _first(_PAY_BEFORE_EN, t)
        if hit:
            return ScamMatch("pay_before", hit)
    hit = _first(_JOB_FEE_EN, t) or _first_word(_JOB_FEE_HI_TE, t)
    if hit:
        return ScamMatch("job_fee", hit)
    if _PHONE.search(t):
        hit = _first(_SEND_MONEY, t) or _first(_APP_NEAR_MONEY, t)
        if hit:
            return ScamMatch("phone_payment", hit)
    return None


def refuse(match: ScamMatch, lang: str, *, field: str, opportunity_type: str | None = None, surface: str) -> ApiError:
    """The one refusal shape: 422 seeker_charge_not_allowed with a localized
    explanation of WHY (the rule), plus the field and the matched words so a
    composer can underline them."""
    extra = {"field": field, "matched": match.matched, "rule": match.rule, "surface": surface,
             "explanation": _explanation(match.rule, lang)}
    if opportunity_type:
        extra["type"] = opportunity_type
    return ApiError(422, "trust_safety.error.seekerChargeNotAllowed", lang, error_code="seeker_charge_not_allowed", extra=extra)


def _explanation(rule: str, lang: str) -> str:
    from app.i18n import translate

    return translate(f"trust_safety.scamShield.rule.{rule}", lang)


def check_fields(fields: dict[str, str | None], lang: str, *, tier: Tier = "hiring", surface: str,
                 opportunity_type: str | None = None) -> None:
    """Raises the refusal for the first field whose text breaks a rule."""
    for name, value in fields.items():
        match = detect(value, tier)
        if match is not None:
            raise refuse(match, lang, field=name, opportunity_type=opportunity_type, surface=surface)


async def log_block(actor_id: str | None, *, surface: str, object_kind: str, object_id: str | None, exc: ApiError) -> None:
    """[Trust event] Recorded on its own connection: the refusal rolls the
    request back and would take an in-transaction row with it. Only the
    rule, the field and the matched words are kept — never the text."""
    from app.audit import audit_out_of_band

    details = exc.extra if isinstance(exc.extra, dict) else {}
    try:
        await audit_out_of_band(
            actor_id=actor_id, action="trust.seeker_charge_blocked", object_kind=object_kind, object_id=object_id or "new",
            reason_code=str(details.get("rule") or details.get("field") or "seeker_charge"), outcome="rejected",
            details={"surface": surface, "field": details.get("field"), "rule": details.get("rule"),
                     "matched": (details.get("matched") or "")[:80], "type": details.get("type")},
        )
    except Exception:  # logging must never turn a clean refusal into a 500
        import logging

        logging.getLogger(__name__).exception("could not record the seeker-charge trust event")


async def guard(actor_id: str | None, fields: dict[str, str | None], lang: str, *, tier: Tier = "hiring", surface: str,
                object_kind: str, object_id: str | None, opportunity_type: str | None = None) -> None:
    """check_fields + the trust event. Use where the caller has no other
    check to run (enquiry replies, packages)."""
    try:
        check_fields(fields, lang, tier=tier, surface=surface, opportunity_type=opportunity_type)
    except ApiError as exc:
        await log_block(actor_id, surface=surface, object_kind=object_kind, object_id=object_id, exc=exc)
        raise

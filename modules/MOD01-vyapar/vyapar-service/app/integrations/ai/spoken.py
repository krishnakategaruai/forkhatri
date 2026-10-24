# [Voice interview, 2026-09-30] Readers for SPOKEN answers, in English, Hindi,
# Telugu, Hinglish and Tenglish. [2026-10-06] Marathi and Kannada (both
# scripts' words plus common romanised forms) are added alongside; every
# en/hi/te form below is unchanged.
#
# The voice interview asks one question at a time, so each answer is short
# and about one thing: "पंद्रह से अठारह हज़ार", "Kukatpally lo", "repu
# udayam", "ఇద్దరు", "haan". The rules engine (rules_provider.py) reads whole
# notices and looks for context words ("salary", "₹") before it trusts a
# number; here the question IS the context. So this module only:
#
#   * turns spoken numbers into digits (English, Hindi in both scripts,
#     Telugu in both scripts, including ढाई / साढ़े / రెండున్నర), keeping a
#     trailing "हज़ार / వేలు / thousand" as a word so the existing money
#     reader still propagates it across a range ("15 से 18 हज़ार");
#   * recognises the control words a person says instead of an answer
#     (skip, yes, no, repeat) in all three languages;
#   * reads working hours, days and deadlines, and names.
#
# Everything is pure (no I/O) and deterministic; app/services/
# voice_interview.py decides what each reading means for a field.
from __future__ import annotations

import re
import unicodedata
from datetime import date, timedelta

# ---- normalising ------------------------------------------------------------

_PUNCT = re.compile(r"[!?।॥;:\"'“”‘’()\[\]{}…]+|(?<!\d)[.,]|[.,](?!\d)")


def norm(text: str) -> str:
    """NFC, lower case, punctuation to spaces, single spaces. For matching only."""
    t = unicodedata.normalize("NFC", text or "").lower()
    t = t.replace("‌", "").replace("‍", "")
    # Devanagari nukta variants that speech engines spell either way
    t = t.replace("ज़", "ज").replace("ड़", "ड").replace("फ़", "फ").replace("ँ", "ं")
    t = _PUNCT.sub(" ", t)
    return re.sub(r"\s+", " ", t).strip()


# ---- control words ----------------------------------------------------------

def _forms(*words: str) -> tuple[str, ...]:
    return tuple(sorted({norm(w) for w in words}, key=len, reverse=True))


_YES = _forms(
    "yes", "yeah", "yep", "yup", "ya", "right", "correct", "that's right", "thats right", "that is right", "ok", "okay",
    "sure", "exactly", "yes please", "yes it is", "haan", "haa", "han", "ha", "haanji", "haan ji", "ji haan", "ji", "jee",
    "sahi", "sahi hai", "theek hai", "thik hai", "bilkul", "haan sahi hai",
    "हाँ", "हां", "हा", "जी", "जी हाँ", "हाँ जी", "सही", "सही है", "ठीक है", "बिल्कुल", "हाँ सही है", "हाँ ठीक है",
    "avunu", "avnu", "aunu", "avunandi", "sare", "sari", "correct andi", "అవును", "అవునండి", "ఔను", "సరే", "సరి",
    "కరెక్ట్", "అవును సరే", "హా", "హా అవును",
)
_NO = _forms(
    "no", "nope", "not right", "wrong", "incorrect", "no no", "that's wrong", "thats wrong", "nahi", "nahin", "nai", "na",
    "galat", "nahi nahi", "नहीं", "ना", "नहीं जी", "जी नहीं", "गलत", "नहीं नहीं",
    "kaadu", "kadu", "ledu", "ledhu", "kaadandi", "ledandi", "tappu", "కాదు", "కాదండి", "లేదు", "లేదండి", "తప్పు",
)
_SKIP = _forms(
    "skip", "skip it", "skip this", "skip this one", "next", "next one", "next question", "pass", "leave it",
    "not now", "don't know", "dont know", "i don't know", "i dont know", "no idea", "later",
    "chhodo", "chodo", "chhod do", "chod do", "rehne do", "rahne do", "aage", "aage badho", "pata nahi", "baad mein",
    "छोड़ो", "छोडो", "छोड़ दो", "छोड दो", "रहने दो", "आगे", "आगे बढ़ो", "पता नहीं", "बाद में", "स्किप",
    "vaddu", "vadhu", "vadileyandi", "vadilei", "vadileyi", "skip cheyyi", "skip cheyandi", "teliyadu", "taruvata",
    "వద్దు", "వద్దండి", "వదిలేయండి", "వదిలెయ్", "స్కిప్", "తెలియదు", "తర్వాత", "తరువాత",
)
_REPEAT = _forms(
    "repeat", "repeat please", "please repeat", "say again", "say that again", "again", "pardon", "come again", "what",
    "sorry", "sorry what", "once more", "one more time",
    "phir se", "fir se", "phir se boliye", "fir se bolo", "dobara", "dubara", "kya", "kya bola", "kya kaha",
    "फिर से", "फिर से बोलिए", "फिर से बोलो", "दोबारा", "क्या", "क्या बोला", "क्या कहा",
    "malli", "malli cheppandi", "malli cheppu", "enti", "emannaru", "మళ్ళీ", "మళ్లీ", "మళ్ళీ చెప్పండి", "మళ్లీ చెప్పండి",
    "ఏంటి", "ఏమన్నారు",
)
_POLITE = _forms("please", "plz", "sir", "madam", "ji", "जी", "अंडी", "andi", "అండి")


def _more(forms: tuple[str, ...], *words: str) -> tuple[str, ...]:
    # `forms` plus `words`, longest first; the existing forms stay as they are.
    return tuple(sorted(set(forms) | set(_forms(*words)), key=len, reverse=True))


# [Marathi + Kannada, 2026-10-06] Standard Marathi (हो / नाही, not Hindi
# हाँ / नहीं) and standard Kannada, as people say them and as a speech
# recogniser writes them, plus the romanised forms people type. नको and ಬೇಡ
# ("don't want") are a "no": to "Do they need a bike?" they are the answer.
_YES = _more(
    _YES,
    "हो", "होय", "हो हो", "हो बरोबर", "होय बरोबर", "बरोबर", "बरोबर आहे", "ठीक आहे", "चालेल", "हो चालेल", "अगदी बरोबर",
    "ho", "hoy", "ho barobar", "barobar", "barobar aahe", "barobar ahe", "theek aahe", "thik ahe", "chalel",
    "ಹೌದು", "ಹೌದು ಸರಿ", "ಹೌದ್", "ಹೂಂ", "ಹೂ", "ಸರಿ", "ಸರಿ ಇದೆ", "ಸರಿಯಾಗಿದೆ", "ಆಯ್ತು", "ಆಯಿತು", "ಓಕೆ", "ಹೌದು ಸರ್",
    "houdu", "haudu", "hoon", "aytu", "aaytu", "sari ide",
)
_NO = _more(
    _NO,
    "नाही", "नाही नाही", "नाही हो", "नको", "नको नको", "चूक", "चुकीचे", "चुकीचं", "बरोबर नाही",
    "naahi", "nako", "nako nako", "chuk", "chukiche",
    "ಇಲ್ಲ", "ಇಲ್ಲಾ", "ಇಲ್ಲ ಇಲ್ಲ", "ಬೇಡ", "ಬೇಡ ಬೇಡ", "ಅಲ್ಲ", "ತಪ್ಪು", "ಸರಿ ಇಲ್ಲ", "ಸರಿಯಲ್ಲ",
    "illa", "illaa", "beda", "alla", "sari illa",
)
_SKIP = _more(
    _SKIP,
    "वगळा", "हे वगळा", "पुढे", "पुढे चला", "पुढचा", "पुढचा प्रश्न", "सोडा", "सोडून द्या", "राहू द्या", "माहीत नाही",
    "माहिती नाही", "मला माहीत नाही", "नंतर", "नंतर सांगतो", "नंतर सांगते", "स्किप करा",
    "vagla", "pudhe", "pudhe chala", "pudhcha", "soda", "sodun dya", "rahu dya", "mahit nahi", "mahiti nahi", "nantar",
    "ಬಿಡಿ", "ಬಿಟ್ಟುಬಿಡಿ", "ಬಿಟ್ಟು ಬಿಡಿ", "ಮುಂದೆ", "ಮುಂದಿನದು", "ಮುಂದಿನ ಪ್ರಶ್ನೆ", "ಗೊತ್ತಿಲ್ಲ", "ಗೊತ್ತಿಲ್ಲಾ", "ನನಗೆ ಗೊತ್ತಿಲ್ಲ",
    "ಆಮೇಲೆ", "ನಂತರ", "ಆಮೇಲೆ ಹೇಳ್ತೀನಿ", "ಸ್ಕಿಪ್", "ಸ್ಕಿಪ್ ಮಾಡಿ",
    "bidi", "bittubidi", "bittu bidi", "munde", "mundina prashne", "gottilla", "amele", "aamele", "skip maadi",
)
_REPEAT = _more(
    _REPEAT,
    "पुन्हा", "पुन्हा सांगा", "पुन्हा एकदा", "परत", "परत सांगा", "परत एकदा", "काय", "काय म्हणालात", "काय म्हणाला",
    "समजले नाही", "समजलं नाही", "कळले नाही", "कळलं नाही",
    "punha", "punha sanga", "parat sanga", "parat ekda", "kay", "kaay", "kay mhanalat",
    "ಮತ್ತೆ", "ಮತ್ತೊಮ್ಮೆ", "ಮತ್ತೆ ಹೇಳಿ", "ಇನ್ನೊಮ್ಮೆ", "ಇನ್ನೊಮ್ಮೆ ಹೇಳಿ", "ಏನು", "ಏನಂದ್ರಿ", "ಏನು ಹೇಳಿದ್ರಿ", "ಏನು ಹೇಳಿದಿರಿ",
    "ಅರ್ಥ ಆಗಲಿಲ್ಲ", "ಅರ್ಥವಾಗಲಿಲ್ಲ",
    "matte", "matte heli", "mattomme", "innomme", "innomme heli", "enu", "enandri",
)
_POLITE = _more(_POLITE, "कृपया", "सर", "मॅडम", "ದಯವಿಟ್ಟು", "ಸರ್", "ಮೇಡಂ")


def _match_whole(t: str, forms: tuple[str, ...]) -> bool:
    return t in forms


def _match_lead(t: str, forms: tuple[str, ...]) -> str | None:
    """The rest after a leading form ("no, Madhapur" -> "madhapur"), or None."""
    for f in forms:
        if t == f:
            return ""
        if t.startswith(f + " "):
            return t[len(f) + 1:].strip()
    return None


def control_intent(text: str) -> tuple[str, str]:
    """(intent, rest). intent is skip | repeat | yes | no | answer. `rest` is
    what follows a leading yes/no ("haan, 2 log" -> "2 log"); for an answer it
    is the normalised text."""
    t = norm(text)
    stripped = t
    for p in _POLITE:  # "skip please", "haan ji"
        stripped = re.sub(rf"(?:^|\s){re.escape(p)}$", "", stripped).strip() or stripped
    if _match_whole(stripped, _SKIP):
        return "skip", ""
    if _match_whole(stripped, _REPEAT):
        return "repeat", ""
    for intent, forms in (("yes", _YES), ("no", _NO)):
        if _match_whole(stripped, forms):
            return intent, ""
    for intent, forms in (("yes", _YES), ("no", _NO)):
        rest = _match_lead(t, forms)
        # Only real yes/no words lead an answer: "na" or "ha" inside a
        # sentence are too short to mean "no"/"yes" on their own. Marathi
        # "हो"/"ho" (yes) leads Hindi "हो गया", so it never leads an answer.
        if rest and len(rest) >= 2 and not any(t.startswith(f + " ") for f in ("na", "ha", "ji", "ya", "ok", "ho", "हो")):
            return intent, rest
    return "answer", t


# ---- numbers ----------------------------------------------------------------

_HI_1_99 = (
    "एक दो तीन चार पांच छह सात आठ नौ दस ग्यारह बारह तेरह चौदह पंद्रह सोलह सत्रह अठारह उन्नीस बीस "
    "इक्कीस बाईस तेईस चौबीस पच्चीस छब्बीस सत्ताईस अट्ठाईस उनतीस तीस इकतीस बत्तीस तैंतीस चौंतीस पैंतीस छत्तीस "
    "सैंतीस अड़तीस उनतालीस चालीस इकतालीस बयालीस तैंतालीस चवालीस पैंतालीस छियालीस सैंतालीस अड़तालीस उनचास पचास "
    "इक्यावन बावन तिरपन चौवन पचपन छप्पन सत्तावन अट्ठावन उनसठ साठ इकसठ बासठ तिरसठ चौंसठ पैंसठ छियासठ सड़सठ "
    "अड़सठ उनहत्तर सत्तर इकहत्तर बहत्तर तिहत्तर चौहत्तर पचहत्तर छिहत्तर सतहत्तर अठहत्तर उन्यासी अस्सी इक्यासी "
    "बयासी तिरासी चौरासी पचासी छियासी सत्तासी अट्ठासी नवासी नब्बे इक्यानवे बानवे तिरानवे चौरानवे पचानवे छियानवे "
    "सत्तानवे अट्ठानवे निन्यानवे"
).split()
_NUM_WORDS: dict[str, float] = {norm(w): i for i, w in enumerate(_HI_1_99, start=1)}
_NUM_WORDS.update({norm(w): v for w, v in {
    "पाँच": 5, "छः": 6, "छे": 6, "पन्द्रह": 15, "अठ्ठारह": 18,
    # English
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
    "eighty": 80, "ninety": 90,
    # Hinglish
    "ek": 1, "do": 2, "teen": 3, "tin": 3, "char": 4, "chaar": 4, "paanch": 5, "panch": 5, "chhe": 6, "chhah": 6,
    "saat": 7, "aath": 8, "nau": 9, "das": 10, "gyarah": 11, "gyara": 11, "barah": 12, "bara": 12, "terah": 13,
    "chaudah": 14, "pandrah": 15, "pandra": 15, "solah": 16, "sola": 16, "satrah": 17, "atharah": 18, "athara": 18,
    "unnis": 19, "bees": 20, "pachees": 25, "pachchis": 25, "tees": 30, "chalis": 40, "chaalis": 40, "pachas": 50,
    "pachaas": 50, "sattar": 70, "assi": 80, "nabbe": 90,
    # Telugu
    "ఒకటి": 1, "ఒక": 1, "ఒకరు": 1, "రెండు": 2, "మూడు": 3, "నాలుగు": 4, "ఐదు": 5, "అయిదు": 5, "ఆరు": 6, "ఏడు": 7,
    "ఎనిమిది": 8, "తొమ్మిది": 9, "పది": 10, "పదకొండు": 11, "పన్నెండు": 12, "పదమూడు": 13, "పద్నాలుగు": 14,
    "పదిహేను": 15, "పదహేను": 15, "పదహారు": 16, "పదిహారు": 16, "పదిహేడు": 17, "పదిహెడు": 17, "పద్దెనిమిది": 18,
    "పందొమ్మిది": 19, "ఇరవై": 20, "ముప్పై": 30, "ముప్పయి": 30, "నలభై": 40, "యాభై": 50, "అరవై": 60, "డెబ్బై": 70,
    "ఎనభై": 80, "తొంభై": 90,
    "ఇద్దరు": 2, "ముగ్గురు": 3, "నలుగురు": 4, "ఐదుగురు": 5, "ఆరుగురు": 6, "ఏడుగురు": 7, "పదిమంది": 10,
    "ఒకటిన్నర": 1.5, "రెండున్నర": 2.5, "మూడున్నర": 3.5, "నాలుగున్నర": 4.5,
    "రెండొందలు": 200, "మూడొందలు": 300, "నాలుగొందలు": 400, "ఐదొందలు": 500, "ఆరొందలు": 600, "ఏడొందలు": 700,
    "ఎనిమిదొందలు": 800, "తొమ్మిదొందలు": 900, "వెయ్యి": 1000,
    # Tenglish
    "okati": 1, "rendu": 2, "moodu": 3, "mudu": 3, "naalugu": 4, "nalugu": 4, "aidu": 5, "aaru": 6, "edu": 7,
    "enimidi": 8, "tommidi": 9, "padi": 10, "padihenu": 15, "paddenimidi": 18, "iravai": 20, "muppai": 30,
    "yabhai": 50, "iddaru": 2, "mugguru": 3, "naluguru": 4, "veyyi": 1000,
    # halves
    "ढाई": 2.5, "डेढ़": 1.5, "डेढ": 1.5, "dhai": 2.5, "dedh": 1.5,
}.items()})

# [Marathi + Kannada, 2026-10-06] Added with setdefault, so no Hindi, Telugu
# or English reading above changes.
_MR_1_99 = (
    "एक दोन तीन चार पाच सहा सात आठ नऊ दहा अकरा बारा तेरा चौदा पंधरा सोळा सतरा अठरा एकोणीस वीस "
    "एकवीस बावीस तेवीस चोवीस पंचवीस सव्वीस सत्तावीस अठ्ठावीस एकोणतीस तीस एकतीस बत्तीस तेहेतीस चौतीस पस्तीस छत्तीस "
    "सदतीस अडतीस एकोणचाळीस चाळीस एक्केचाळीस बेचाळीस त्रेचाळीस चव्वेचाळीस पंचेचाळीस सेहेचाळीस सत्तेचाळीस अठ्ठेचाळीस "
    "एकोणपन्नास पन्नास एक्कावन्न बावन्न त्रेपन्न चोपन्न पंचावन्न छप्पन्न सत्तावन्न अठ्ठावन्न एकोणसाठ साठ एकसष्ठ बासष्ठ "
    "त्रेसष्ठ चौसष्ठ पासष्ठ सहासष्ठ सदुसष्ठ अडुसष्ठ एकोणसत्तर सत्तर एकाहत्तर बाहत्तर त्र्याहत्तर चौऱ्याहत्तर पंच्याहत्तर "
    "शहात्तर सत्याहत्तर अठ्ठ्याहत्तर एकोणऐंशी ऐंशी एक्याऐंशी ब्याऐंशी त्र्याऐंशी चौऱ्याऐंशी पंच्याऐंशी शहाऐंशी सत्त्याऐंशी "
    "अठ्ठ्याऐंशी एकोणनव्वद नव्वद एक्क्याण्णव ब्याण्णव त्र्याण्णव चौऱ्याण्णव पंच्याण्णव शहाण्णव सत्त्याण्णव अठ्ठ्याण्णव "
    "नव्व्याण्णव"
).split()
assert len(_MR_1_99) == 99
_KN_UNITS = {1: "ಒಂದು", 2: "ಎರಡು", 3: "ಮೂರು", 4: "ನಾಲ್ಕು", 5: "ಐದು", 6: "ಆರು", 7: "ಏಳು", 8: "ಎಂಟು", 9: "ಒಂಬತ್ತು"}
_KN_TEENS = {10: "ಹತ್ತು", 11: "ಹನ್ನೊಂದು", 12: "ಹನ್ನೆರಡು", 13: "ಹದಿಮೂರು", 14: "ಹದಿನಾಲ್ಕು", 15: "ಹದಿನೈದು", 16: "ಹದಿನಾರು",
             17: "ಹದಿನೇಳು", 18: "ಹದಿನೆಂಟು", 19: "ಹತ್ತೊಂಬತ್ತು"}
# Kannada writes 21–99 as one word: the tens stem + "ತ್ತ" joined to the unit
# (ಇಪ್ಪತ್ತೈದು = 25, ಮೂವತ್ತೆರಡು = 32; 3 and 4 also contract: ಇಪ್ಪತ್ಮೂರು, ಇಪ್ಪತ್ನಾಲ್ಕು).
_KN_TENS_STEM = {20: ("ಇಪ್ಪ",), 30: ("ಮೂವ",), 40: ("ನಲವ", "ನಲ್ವ"), 50: ("ಐವ",), 60: ("ಅರವ",), 70: ("ಎಪ್ಪ",),
                 80: ("ಎಂಬ", "ಎಂಭ"), 90: ("ತೊಂಬ",)}
_KN_JOIN = {1: ("ತ್ತೊಂದು",), 2: ("ತ್ತೆರಡು",), 3: ("ತ್ಮೂರು", "ತ್ತಮೂರು", "ತ್ತ್ಮೂರು"), 4: ("ತ್ನಾಲ್ಕು", "ತ್ತನಾಲ್ಕು", "ತ್ತ್ನಾಲ್ಕು"),
            5: ("ತ್ತೈದು",), 6: ("ತ್ತಾರು",), 7: ("ತ್ತೇಳು",), 8: ("ತ್ತೆಂಟು",), 9: ("ತ್ತೊಂಬತ್ತು", "ತ್ತೊಂಭತ್ತು")}
_MR_KN_NUMBERS: dict[str, float] = {w: i for i, w in enumerate(_MR_1_99, start=1)}
_MR_KN_NUMBERS.update({w.replace("ऱ", "र"): i for i, w in enumerate(_MR_1_99, start=1) if "ऱ" in w})
_MR_KN_NUMBERS.update({w: v for v, w in {**_KN_UNITS, **_KN_TEENS}.items()})
for _tens, _stems in _KN_TENS_STEM.items():
    for _stem in _stems:
        _MR_KN_NUMBERS[_stem + "ತ್ತು"] = _tens
        for _unit, _joins in _KN_JOIN.items():
            for _j in _joins:
                _MR_KN_NUMBERS[_stem + _j] = _tens + _unit
_MR_KN_NUMBERS.update({
    # Marathi spelling variants, hundreds, people and fractions
    "छपन्न": 56, "पंचाहत्तर": 75, "सत्त्याहत्तर": 77, "पंचाण्णव": 95, "नव्याण्णव": 99, "एक्याण्णव": 91, "शंभर": 100,
    "एकशे": 100, "दोनशे": 200, "तीनशे": 300, "चारशे": 400, "पाचशे": 500, "सहाशे": 600, "सातशे": 700, "आठशे": 800,
    "नऊशे": 900, "दोघे": 2, "दोघी": 2, "दोघं": 2, "तिघे": 3, "तिघी": 3, "चौघे": 4, "चौघी": 4,
    "दीड": 1.5, "अडीच": 2.5, "अर्धा": 0.5, "पाऊण": 0.75,
    # Marathi, romanised ("don" is left out: "don t know" would read as 2)
    "paach": 5, "saha": 6, "daha": 10, "akra": 11, "pandhra": 15, "vees": 20, "pannas": 50, "shambhar": 100,
    "didh": 1.5, "adich": 2.5,
    # Kannada variants, hundreds, people and fractions
    "ಒಂಭತ್ತು": 9, "ಒಬ್ಬರು": 1, "ಒಬ್ಬ": 1, "ಒಬ್ಬಳು": 1, "ಇಬ್ಬರು": 2, "ಮೂವರು": 3, "ನಾಲ್ವರು": 4, "ಐವರು": 5,
    "ಇನ್ನೂರು": 200, "ಮುನ್ನೂರು": 300, "ನಾನೂರು": 400, "ನಾನ್ನೂರು": 400, "ಐನೂರು": 500, "ಆರುನೂರು": 600, "ಆರ್ನೂರು": 600,
    "ಏಳುನೂರು": 700, "ಏಳ್ನೂರು": 700, "ಎಂಟುನೂರು": 800, "ಎಂಟ್ನೂರು": 800, "ಒಂಬೈನೂರು": 900, "ಒಂಬತ್ತುನೂರು": 900,
    "ಒಂದೂವರೆ": 1.5, "ಎರಡೂವರೆ": 2.5, "ಮೂರೂವರೆ": 3.5, "ನಾಲ್ಕೂವರೆ": 4.5, "ಐದೂವರೆ": 5.5, "ಅರ್ಧ": 0.5, "ಮುಕ್ಕಾಲು": 0.75,
    # Kannada, romanised
    "ondu": 1, "eradu": 2, "mooru": 3, "nalku": 4, "naalku": 4, "elu": 7, "entu": 8, "ombattu": 9, "hattu": 10,
    "hadinaidu": 15, "ippattu": 20, "moovattu": 30, "nalavattu": 40, "aivattu": 50, "obbaru": 1, "ibbaru": 2,
    "ondoovare": 1.5, "eradoovare": 2.5,
})
for _w, _v in _MR_KN_NUMBERS.items():
    _NUM_WORDS.setdefault(norm(_w), _v)
# Marathi and Kannada hundreds that a smaller number follows in one amount:
# "दोनशे पन्नास" = 250, "ಇನ್ನೂರು ಐವತ್ತು" = 250.
_MR_KN_HUNDREDS = {norm(w) for w, v in _MR_KN_NUMBERS.items() if v >= 100 and norm(w) in _NUM_WORDS
                   and _NUM_WORDS[norm(w)] == v and not w.isascii()}
_TENS = {v for v in (20, 30, 40, 50, 60, 70, 80, 90)}
_HUNDRED = {norm(w) for w in ("hundred", "sau", "सौ", "వంద", "వందలు", "వందల", "నూరు", "vanda", "vandalu")}
_BIG: dict[str, int] = {norm(w): v for w, v in {
    "thousand": 1000, "hazaar": 1000, "hazar": 1000, "हजार": 1000, "హజార్": 1000, "వేలు": 1000, "వేల": 1000,
    "velu": 1000, "vela": 1000, "k": 1000,
    "lakh": 100_000, "lakhs": 100_000, "lac": 100_000, "lacs": 100_000, "लाख": 100_000, "లక్ష": 100_000,
    "లక్షలు": 100_000, "లక్షల": 100_000, "laksha": 100_000, "lakshalu": 100_000,
    "crore": 10_000_000, "करोड": 10_000_000, "కోటి": 10_000_000,
}.items()}
_HALF_PLUS = {norm(w) for w in ("साढ़े", "साढे", "sadhe", "saadhe")}
_TOKEN = re.compile(r"\d[\d,]*(?:\.\d+)?|[a-zऀ-ॿఀ-౿]+")
# [Marathi + Kannada, 2026-10-06]
_HUNDRED |= {norm(w) for w in ("शे", "ನೂರು", "ನೂರ", "nooru")} - set(_NUM_WORDS)
for _w, _v in {"कोटी": 10_000_000, "hajar": 1000, "ಸಾವಿರ": 1000, "ಸಾವಿರದ": 1000, "savira": 1000, "saavira": 1000,
               "ಲಕ್ಷ": 100_000, "ಲಕ್ಷದ": 100_000, "ಲಕ್ಷಗಳು": 100_000, "ಕೋಟಿ": 10_000_000, "koti": 10_000_000}.items():
    _BIG.setdefault(norm(_w), _v)
_HALF_PLUS |= {norm(w) for w in ("साडे", "sade", "saade")}
# Marathi quarter prefixes: सव्वा दोन = 2.25, पावणे दोन = 1.75.
_FRACTION_PREFIX = {norm(w): v for w, v in {"सव्वा": 0.25, "savva": 0.25, "पावणे": -0.25, "pavne": -0.25}.items()}
_TOKEN = re.compile(r"\d[\d,]*(?:\.\d+)?|[a-zऀ-ॿఀ-౿ಀ-೿]+")


def _num(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else f"{v:g}"


def words_to_digits(text: str) -> str:
    """"पंद्रह से अठारह हज़ार" -> "15 से 18 हजार"; "two thousand five hundred"
    -> "2500"; "ఐదొందలు" -> "500"; "15,000" stays. Only for answers to a
    numeric question: "do" is two here, but "give" in a sentence."""
    t = norm(text)
    tokens = [(m.start(), m.end(), m.group(0)) for m in _TOKEN.finditer(t)]
    out: list[str] = []
    pos = 0
    i = 0
    while i < len(tokens):
        s, e, w = tokens[i]
        kind = _kind(w)
        if kind is None:
            i += 1
            continue
        # a run of number tokens separated only by spaces
        run = [(kind, w)]
        j = i + 1
        end = e
        while j < len(tokens) and t[end:tokens[j][0]].strip() == "":
            k2 = _kind(tokens[j][2])
            if k2 is None:
                break
            prev_kind, prev_w = run[-1]
            # "15 18" or "पंद्रह अठारह" are two numbers, not one; "twenty five" is one.
            if k2 == "num" and prev_kind == "num" and not (_value(prev_w) in _TENS and _value(tokens[j][2]) < 10) \
                    and not (prev_w in _MR_KN_HUNDREDS and _value(tokens[j][2]) < 100):  # "दोनशे पन्नास" = 250
                break
            if k2 == "num" and prev_kind == "big" and _value(tokens[j][2]) >= 1000:
                break
            run.append((k2, tokens[j][2]))
            end = tokens[j][1]
            j += 1
        replacement = _render(run)
        if replacement is not None:
            out.append(t[pos:s])
            out.append(replacement)
            pos = end
        i = j
    out.append(t[pos:])
    return re.sub(r"\s+", " ", "".join(out)).strip()


def _kind(w: str) -> str | None:
    if w[0].isdigit():
        return "num"
    if w in _NUM_WORDS:
        return "num"
    if w in _HUNDRED:
        return "hundred"
    if w in _BIG:
        return "big"
    if w in _HALF_PLUS:
        return "half"
    if w in _FRACTION_PREFIX:
        return "frac"
    return None


def _value(w: str) -> float:
    if w[0].isdigit():
        return float(w.replace(",", ""))
    return _NUM_WORDS.get(w, 0)


def _render(run: list[tuple[str, str]]) -> str | None:
    kinds = [k for k, _ in run]
    if kinds == ["num"] and run[0][1][0].isdigit():
        return None  # already digits
    if all(k in ("hundred", "big", "half", "frac") for k in kinds):
        return None  # "lakh" alone is not a number
    # "पंद्रह हज़ार" / "18 వేలు": keep the multiplier as a word, so a range
    # "15 से 18 हज़ार" still reads as thousands on both sides.
    if kinds[-1] == "big" and kinds.count("big") == 1 and "hundred" not in kinds and "half" not in kinds and "frac" not in kinds:
        n = sum(_value(w) for k, w in run if k == "num")
        return f"{_num(n)} {run[-1][1]}"
    total, cur, half, frac = 0.0, None, False, 0.0
    for k, w in run:
        if k == "half":
            half = True
        elif k == "frac":
            frac = _FRACTION_PREFIX[w]
        elif k == "num":
            v = _value(w) + (0.5 if half else 0) + frac
            half, frac = False, 0.0
            cur = (cur or 0) + v
        elif k == "hundred":
            cur = (cur or 1) * 100
        elif k == "big":
            total += (cur or 1) * _BIG[w]
            cur = None
    value = total + (cur or 0)
    return _num(value)


def first_int(text: str) -> int | None:
    m = re.search(r"\d[\d,]*", words_to_digits(text))
    if not m:
        return None
    try:
        return int(float(m.group(0).replace(",", "")))
    except ValueError:
        return None


# ---- working hours ----------------------------------------------------------

_DAYPART_WORDS: dict[str, str] = {norm(w): p for w, p in {
    "morning": "am", "subah": "am", "subha": "am", "सुबह": "am", "सवेरे": "am", "udayam": "am", "ఉదయం": "am",
    "podduna": "am", "పొద్దున": "am", "పొద్దున్నే": "am",
    "afternoon": "noon", "dopahar": "noon", "dopehar": "noon", "दोपहर": "noon", "madhyahnam": "noon", "మధ్యాహ్నం": "noon",
    "evening": "pm", "shaam": "pm", "sham": "pm", "शाम": "pm", "sayantram": "pm", "saayantram": "pm", "సాయంత్రం": "pm",
    "night": "night", "raat": "night", "रात": "night", "ratri": "night", "రాత్రి": "night",
}.items()}
for _w, _p in {  # [Marathi + Kannada, 2026-10-06]
    "सकाळ": "am", "सकाळी": "am", "दुपार": "noon", "दुपारी": "noon", "संध्याकाळ": "pm", "संध्याकाळी": "pm", "सायंकाळी": "pm",
    "रात्र": "night", "रात्री": "night", "sakali": "am", "dupari": "noon", "sandhyakali": "pm",
    "ಬೆಳಿಗ್ಗೆ": "am", "ಬೆಳಗ್ಗೆ": "am", "ಮುಂಜಾನೆ": "am", "ಮಧ್ಯಾಹ್ನ": "noon", "ಸಂಜೆ": "pm", "ರಾತ್ರಿ": "night",
    "beligge": "am", "belagge": "am", "madhyahna": "noon", "sanje": "pm",
}.items():
    _DAYPART_WORDS.setdefault(norm(_w), _p)
_DP = "|".join(sorted(map(re.escape, _DAYPART_WORDS), key=len, reverse=True))
_MARK = r"am|pm|a m|p m|baje|बजे|గంటలకు|గంటల|గంటలు|o clock|oclock" + r"|वाजता|वाजेपर्यंत|ಗಂಟೆಯವರೆಗೆ|ಗಂಟೆಗೆ|ಗಂಟೆ"
_SEP = r"-|–|to|till|until|se|से|nundi|nunchi|నుండి|నుంచి" + r"|वाजल्यापासून|पासून|ते|ಗಂಟೆಯಿಂದ|ರಿಂದ"
_HOURS_RANGE = re.compile(
    rf"(?:({_DP})\s*)?(\d{{1,2}})(?:[:.](\d{{2}}))?\s*({_MARK})?(?:\s*(?:in the\s+|ki\s+|की\s+)?({_DP}))?\s*(?:{_SEP})\s*"
    rf"(?:({_DP})\s*)?(\d{{1,2}})(?:[:.](\d{{2}}))?\s*({_MARK})?(?:\s*(?:in the\s+)?({_DP}))?"
)
_HOURS_COUNT = re.compile(r"(\d{1,2})\s*(?:hours?|hrs?|ghante|ghanta|घंटे|घंटा|గంటలు|గంటల|तास|taas|ಗಂಟೆಗಳು|ಗಂಟೆಗಳ|ಗಂಟೆ|gante)")


def _to24(h: int, mark: str | None, part: str | None, default: str) -> int:
    mark = (mark or "").replace(" ", "")
    if mark == "am":
        return 0 if h == 12 else h
    if mark == "pm":
        return h if h == 12 else h + 12
    p = part or default
    if p == "am":
        return 0 if h == 12 else h
    if p == "noon":
        return h if h in (11, 12) else h + 12
    if p == "pm":
        return h if h == 12 else h + 12
    if p == "night":
        return 0 if h == 12 else (h if h <= 5 else h + 12)
    return h


def parse_hours(text: str) -> dict | None:
    """{"start": (h, m), "end": (h, m), "shift": day|night} or {"hours": n}."""
    t = words_to_digits(text)
    m = _HOURS_RANGE.search(t)
    if m:
        p1 = _DAYPART_WORDS.get(m.group(1) or m.group(5) or "")
        p2 = _DAYPART_WORDS.get(m.group(6) or m.group(10) or "")
        h1, h2 = int(m.group(2)), int(m.group(7))
        if 0 < h1 <= 24 and 0 < h2 <= 24:
            mk1, mk2 = m.group(4), m.group(9)
            mk1 = mk1 if mk1 and mk1.replace(" ", "") in ("am", "pm") else None
            mk2 = mk2 if mk2 and mk2.replace(" ", "") in ("am", "pm") else None
            if h1 > 12 or h2 > 12:  # "10 to 18": already a 24-hour clock
                s24, e24 = h1 % 24, h2 % 24
            else:
                default1 = "am" if 5 <= h1 <= 11 else ("pm" if h1 == 12 else ("pm" if h1 <= 4 else "night"))
                s24 = _to24(h1, mk1, p1, default1 if not p1 else p1)
                e24 = _to24(h2, mk2, p2, "am")
                if not (mk2 or p2) and e24 <= s24:
                    e24 = (e24 + 12) % 24 if e24 + 12 > s24 else e24
            night = s24 >= 18 or s24 < 5 or (e24 < s24 and e24 <= 8)
            return {"start": (s24, int(m.group(3) or 0)), "end": (e24, int(m.group(8) or 0)), "shift": "night" if night else "day"}
    c = _HOURS_COUNT.search(t)
    if c and 1 <= int(c.group(1)) <= 16:
        return {"hours": int(c.group(1))}
    return None


# ---- days and deadlines -----------------------------------------------------

_WEEKDAYS: dict[str, int] = {norm(w): d for w, d in {
    "monday": 0, "mon": 0, "tuesday": 1, "tue": 1, "wednesday": 2, "wed": 2, "thursday": 3, "thu": 3, "friday": 4, "fri": 4,
    "saturday": 5, "sat": 5, "sunday": 6, "sun": 6,
    "somvar": 0, "somwar": 0, "सोमवार": 0, "mangalvar": 1, "mangalwar": 1, "मंगलवार": 1, "budhvar": 2, "budhwar": 2,
    "बुधवार": 2, "guruvar": 3, "guruwar": 3, "गुरुवार": 3, "वीरवार": 3, "brihaspativar": 3, "बृहस्पतिवार": 3,
    "shukravar": 4, "shukrawar": 4, "शुक्रवार": 4, "shanivar": 5, "shaniwar": 5, "शनिवार": 5, "ravivar": 6, "raviwar": 6,
    "रविवार": 6, "itvar": 6, "इतवार": 6,
    "somavaram": 0, "సోమవారం": 0, "mangalavaram": 1, "మంగళవారం": 1, "budhavaram": 2, "బుధవారం": 2, "guruvaram": 3,
    "గురువారం": 3, "sukravaram": 4, "shukravaram": 4, "శుక్రవారం": 4, "shanivaram": 5, "శనివారం": 5, "aadivaram": 6,
    "adivaram": 6, "ఆదివారం": 6,
}.items()}
for _w, _d in {  # [Marathi + Kannada, 2026-10-06]
    "मंगळवार": 1, "ಸೋಮವಾರ": 0, "ಮಂಗಳವಾರ": 1, "ಬುಧವಾರ": 2, "ಗುರುವಾರ": 3, "ಶುಕ್ರವಾರ": 4, "ಶನಿವಾರ": 5, "ಭಾನುವಾರ": 6,
    "ಆದಿತ್ಯವಾರ": 6, "somavara": 0, "mangalavara": 1, "budhavara": 2, "guruvara": 3, "shukravara": 4, "shanivara": 5,
    "bhanuvara": 6,
}.items():
    _WEEKDAYS.setdefault(norm(_w), _d)
_MONTHS: dict[str, int] = {norm(w): i for w, i in {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3, "april": 4, "apr": 4, "may": 5, "june": 6,
    "jun": 6, "july": 7, "jul": 7, "august": 8, "aug": 8, "september": 9, "sep": 9, "sept": 9, "october": 10, "oct": 10,
    "november": 11, "nov": 11, "december": 12, "dec": 12,
    "जनवरी": 1, "फरवरी": 2, "मार्च": 3, "अप्रैल": 4, "मई": 5, "जून": 6, "जुलाई": 7, "अगस्त": 8, "सितंबर": 9, "सितम्बर": 9,
    "अक्टूबर": 10, "अक्तूबर": 10, "नवंबर": 11, "नवम्बर": 11, "दिसंबर": 12, "दिसम्बर": 12,
    "జనవరి": 1, "ఫిబ్రవరి": 2, "మార్చి": 3, "ఏప్రిల్": 4, "మే": 5, "జూన్": 6, "జూలై": 7, "ఆగస్టు": 8, "సెప్టెంబర్": 9,
    "అక్టోబర్": 10, "నవంబర్": 11, "డిసెంబర్": 12,
}.items()}
for _w, _m in {  # [Marathi + Kannada, 2026-10-06] ("मे" for May is left out: Hindi speech often writes में as मे)
    "जानेवारी": 1, "फेब्रुवारी": 2, "एप्रिल": 4, "जुलै": 7, "ऑगस्ट": 8, "सप्टेंबर": 9, "ऑक्टोबर": 10, "नोव्हेंबर": 11,
    "डिसेंबर": 12, "ಜನವರಿ": 1, "ಫೆಬ್ರವರಿ": 2, "ಮಾರ್ಚ್": 3, "ಏಪ್ರಿಲ್": 4, "ಮೇ": 5, "ಜೂನ್": 6, "ಜುಲೈ": 7, "ಆಗಸ್ಟ್": 8,
    "ಸೆಪ್ಟೆಂಬರ್": 9, "ಅಕ್ಟೋಬರ್": 10, "ನವೆಂಬರ್": 11, "ಡಿಸೆಂಬರ್": 12,
}.items():
    _MONTHS.setdefault(norm(_w), _m)
_TODAY = re.compile(r"(?<![a-z])(?:today|aaj|aj|abhi|right now|now|immediately|asap|urgent|urgently|turant|ivvala|ee roju|eeroju|ippude|ventane)(?![a-z])"
                    r"|आज|अभी|तुरंत|ఈరోజు|ఈ రోజు|ఇవ్వాళ|ఇప్పుడే|వెంటనే|అర్జెంట్")
_TOMORROW = re.compile(r"(?<![a-z])(?:tomorrow|kal|repu|reppu)(?![a-z])|कल|రేపు")
_DAY_AFTER = re.compile(r"(?<![a-z])(?:day after tomorrow|parso|parson|ellundi)(?![a-z])|परसों|परसो|ఎల్లుండి")
_THIS_WEEK = re.compile(r"(?<![a-z])(?:this week|within the week|is hafte|iss hafte|ee vaaram|ee varam)(?![a-z])|इस हफ्ते|इस सप्ताह|ఈ వారం")
_FLEXIBLE = re.compile(r"(?<![a-z])(?:any ?day|any time|anytime|whenever|flexible|no hurry|no rush|koi bhi din|kabhi bhi|eppudaina|e roju aina)(?![a-z])"
                       r"|कोई भी दिन|कभी भी|जल्दी नहीं|ఎప్పుడైనా|ఏ రోజైనా|తొందర లేదు")
_ONGOING = re.compile(r"(?<![a-z])(?:ongoing|long term|long-term|regular|continuous|no end date|lambe samay)(?![a-z])|लंबे समय|रेगुलर|దీర్ఘకాలం|రెగ్యులర్")
_NEXT = re.compile(r"(?<![a-z])(?:next|coming|agle|agla|vache|vachche)(?![a-z])|अगले|अगला|आने वाले|వచ్చే")
_SPAN = re.compile(
    r"(?:(\d+(?:\.\d+)?)\s*)?(?<![a-z])(days?|din|दिन|రోజుల|రోజులు|రోజు|weeks?|hafte|hafta|हफ्ते|हफ्ता|सप्ताह|వారాల|వారాలు|వారం|"
    r"months?|mahine|mahina|महीने|महीना|నెలల|నెలలు|నెల"
    r"|दिवसा|आठवड|महिन|ದಿನ|ವಾರ|ತಿಂಗಳ)(?![a-z])"  # Marathi and Kannada stems (दिवसांत, आठवड्यात, ವಾರದಲ್ಲಿ, ತಿಂಗಳು)
)
_SPAN_UNIT = {"day": 1, "din": 1, "दिन": 1, "రోజుల": 1, "రోజులు": 1, "రోజు": 1,
              "week": 7, "hafte": 7, "hafta": 7, "हफ्ते": 7, "हफ्ता": 7, "सप्ताह": 7, "వారాల": 7, "వారాలు": 7, "వారం": 7,
              "month": 30, "mahine": 30, "mahina": 30, "महीने": 30, "महीना": 30, "నెలల": 30, "నెలలు": 30, "నెల": 30,
              "दिवसा": 1, "आठवड": 7, "महिन": 30, "ದಿನ": 1, "ವಾರ": 7, "ತಿಂಗಳ": 30}
_DAY_OF_MONTH = re.compile(
    r"(?<!\d)(\d{1,2})\s*(?:st|nd|rd|th|tarikh|tareekh|तारीख|తేదీ|వ తేదీ|వ"
    r"|तारखेला|तारखेपर्यंत|तारखेच्या|तारखेस|ನೇ ತಾರೀಖು|ನೇ ತಾರೀಕು|ನೇ ತಾರೀಖಿನಂದು|ತಾರೀಖು|ತಾರೀಕು|ರಂದು|ನೇ)?\s*(?:ko|को)?\s*"
    r"(?:(" + "|".join(sorted(map(re.escape, _MONTHS), key=len, reverse=True)) + r"))?(?![\d:])"
)
# [Marathi + Kannada, 2026-10-06] Added as further alternatives.
_TODAY = re.compile(_TODAY.pattern + r"|(?<![a-z])(?:lagech|tabadtob|ivattu|eevattu|indu|eegale|takshana)(?![a-z])"
                    r"|आत्ता|आताच|लगेच|ताबडतोब|आजच|ಇಂದು|ಇವತ್ತು|ಈವತ್ತು|ಈಗಲೇ|ತಕ್ಷಣ|ಕೂಡಲೇ|ಅರ್ಜೆಂಟ್")
_TOMORROW = re.compile(_TOMORROW.pattern + r"|(?<![a-z])(?:udya|naale|nale)(?![a-z])|उद्या|ನಾಳೆ")
_DAY_AFTER = re.compile(_DAY_AFTER.pattern + r"|(?<![a-z])(?:naadiddu|nadiddu)(?![a-z])|परवा|ನಾಡಿದ್ದು")
_THIS_WEEK = re.compile(_THIS_WEEK.pattern + r"|(?<![a-z])(?:ya athavdyat|ee vaara)(?![a-z])|या आठवड्यात|ह्या आठवड्यात|ಈ ವಾರ")
_FLEXIBLE = re.compile(_FLEXIBLE.pattern + r"|(?<![a-z])(?:kadhihi|yavaga aadru|yavaga adru|yavagadru)(?![a-z])"
                       r"|कधीही|कोणत्याही दिवशी|कोणताही दिवस|घाई नाही|ಯಾವಾಗಾದರೂ|ಯಾವಾಗ ಬೇಕಾದರೂ|ಯಾವ ದಿನವಾದರೂ|ಅವಸರ ಇಲ್ಲ|ಆತುರ ಇಲ್ಲ")
_ONGOING = re.compile(_ONGOING.pattern + r"|दीर्घकाळ|कायमस्वरूपी|रेग्युलर|ದೀರ್ಘಕಾಲ|ರೆಗ್ಯುಲರ್|ಖಾಯಂ")
_NEXT = re.compile(_NEXT.pattern + r"|(?<![a-z])(?:pudhchya|mundina)(?![a-z])|पुढच्या|पुढील|येत्या|ಮುಂದಿನ|ಬರುವ")
_DMY = re.compile(r"(?<!\d)(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?(?!\d)")


def _next_weekday(today: date, wd: int) -> date:
    days = (wd - today.weekday()) % 7
    return today + timedelta(days=days or 7)


def parse_day(text: str, today: date) -> dict | None:
    """{"date": date|None, "flexible": bool, "ongoing": bool, "span_days": int|None}."""
    t = words_to_digits(text)
    raw = norm(text)

    def at(d: date) -> dict:
        return {"date": d, "flexible": False, "ongoing": False, "span_days": (d - today).days}

    if _ONGOING.search(raw):
        return {"date": None, "flexible": False, "ongoing": True, "span_days": None}
    if _DAY_AFTER.search(raw):
        return at(today + timedelta(days=2))
    if _TOMORROW.search(raw):
        return at(today + timedelta(days=1))
    for word, wd in sorted(_WEEKDAYS.items(), key=lambda kv: -len(kv[0])):
        if re.search(rf"(?<![a-zऀ-ॿఀ-౿ಀ-೿]){re.escape(word)}(?![a-z])", raw):
            return at(_next_weekday(today, wd))
    m = _DMY.search(t)
    if m:
        d, mo = int(m.group(1)), int(m.group(2))
        y = int(m.group(3)) if m.group(3) else today.year
        y = y + 2000 if y < 100 else y
        try:
            found = date(y, mo, d)
            if found < today and not m.group(3):
                found = date(y + 1, mo, d)
            return at(found)
        except ValueError:
            pass
    if _TODAY.search(raw):
        return at(today)
    if _THIS_WEEK.search(raw):
        return {"date": None, "flexible": False, "ongoing": False, "span_days": 6}
    if _FLEXIBLE.search(raw):
        return {"date": None, "flexible": True, "ongoing": False, "span_days": None}
    s = _SPAN.search(t)
    if s:
        n = float(s.group(1)) if s.group(1) else 1.0
        unit = s.group(2)
        unit = unit.rstrip("s") if unit.startswith(("day", "week", "month")) else unit
        days = int(round(n * _SPAN_UNIT[unit]))
        if 0 < days <= 730:
            return at(today + timedelta(days=days))
    m = _DAY_OF_MONTH.search(t)
    if m and (m.group(2) or re.search(r"st|nd|rd|th|tarikh|tareekh|तारीख|తేదీ|వ|तारख|ತಾರೀ|ರಂದು|ನೇ", t[m.start():m.end()])):
        d = int(m.group(1))
        if m.group(2):
            mo = _MONTHS[m.group(2)]
            for y in (today.year, today.year + 1):
                try:
                    found = date(y, mo, d)
                except ValueError:
                    return None
                if found >= today:
                    return at(found)
        else:
            y, mo = today.year, today.month
            for _ in range(13):
                try:
                    found = date(y, mo, d)
                    if found >= today:
                        return at(found)
                except ValueError:
                    pass
                y, mo = (y + 1, 1) if mo == 12 else (y, mo + 1)
    return None


# ---- names ------------------------------------------------------------------

_NAME_LEAD = re.compile(
    r"^(?:my name is|my name's|i am|i'm|this is|it's|call me|name is|mera naam|mera nam|मेरा नाम|मेरा नाम है|मैं|"
    r"naa peru|na peru|నా పేరు|నేను|"
    r"maze nav|majhe nav|majha nav|माझे नाव|माझं नाव|मी|nanna hesaru|ನನ್ನ ಹೆಸರು|ನಾನು)\s+", re.I)
_NAME_TAIL = re.compile(r"\s+(?:hai|hoon|hun|है|हूं|हूँ|andi|అండి|ని|గారు|आहे|aahe|ಅಂತ)$", re.I)


def parse_name(text: str) -> str | None:
    t = re.sub(r"\s+", " ", _PUNCT.sub(" ", unicodedata.normalize("NFC", text or ""))).strip()
    t = _NAME_LEAD.sub("", t).strip()
    t = _NAME_TAIL.sub("", t).strip()
    if not t or any(c.isdigit() for c in t) or len(t) > 60 or len(t.split()) > 5 or len(t) < 2:
        return None
    return " ".join(w[:1].upper() + w[1:] if w.isascii() else w for w in t.split())


__all__ = ["control_intent", "first_int", "norm", "parse_day", "parse_hours", "parse_name", "words_to_digits"]

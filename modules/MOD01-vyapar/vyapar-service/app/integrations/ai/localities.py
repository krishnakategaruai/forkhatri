# [IMP42 — Refactor C (AI), N7 critique fix 2026-09-29] Find a known locality
# in what a person wrote, in any script.
#
# "हिमायतनगर की बेकरी…" and "హిమాయత్‌నగర్‌లో…" must both mean Himayatnagar,
# and (2026-10-06) Kannada "ಜಯನಗರದಲ್ಲಿ" / Marathi "कोथरूडमध्ये" their places,
# the locality Vyapar already knows. No locality is stored in Hindi or Telugu,
# so every form is reduced to a CONSONANT SKELETON: Devanagari and Telugu are
# transliterated letter by letter, vowels, vowel signs and spacing are dropped,
# aspiration and a few spelling variants are folded (dh→d, sh→s, c→k, w→v,
# ph→p), and repeated letters collapse. हिमायतनगर, హిమాయత్‌నగర్, "Himayat Nagar"
# and "Himayatnagar" all become h-m-y-t-n-g-r. A match returns the name exactly
# as Vyapar stores it, so search, filters and cards see one spelling.
#
# The known names come from the caller (app/services/ai.py reads the
# localities of active listings and opportunities), so nothing here is a
# hard-coded place list. Short skeletons (under four letters: "Uppal",
# "Abids") are matched only by their exact Latin name, because three
# consonants are too common to be evidence of a place.
from __future__ import annotations

import re
import unicodedata
from typing import Iterable

_DEVANAGARI = {
    "क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "n", "च": "ch", "छ": "chh", "ज": "j", "झ": "jh", "ञ": "n",
    "ट": "t", "ठ": "th", "ड": "d", "ढ": "dh", "ण": "n", "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n",
    "प": "p", "फ": "ph", "ब": "b", "भ": "bh", "म": "m", "य": "y", "र": "r", "ल": "l", "ळ": "l", "व": "v",
    "श": "sh", "ष": "sh", "स": "s", "ह": "h", "ं": "n", "ँ": "", "ः": "", "ऋ": "r", "ृ": "r",
}
# Consonant + nukta: ड़ is an r-sound, ज़ a z, फ़ an f.
_NUKTA = {"क": "k", "ख": "kh", "ग": "g", "ज": "z", "ड": "r", "ढ": "rh", "फ": "f", "य": "y"}
_TELUGU = {
    "క": "k", "ఖ": "kh", "గ": "g", "ఘ": "gh", "ఙ": "n", "చ": "ch", "ఛ": "chh", "జ": "j", "ఝ": "jh", "ఞ": "n",
    "ట": "t", "ఠ": "th", "డ": "d", "ఢ": "dh", "ణ": "n", "త": "t", "థ": "th", "ద": "d", "ధ": "dh", "న": "n",
    "ప": "p", "ఫ": "ph", "బ": "b", "భ": "bh", "మ": "m", "య": "y", "ర": "r", "ఱ": "r", "ల": "l", "ళ": "l",
    "వ": "v", "శ": "sh", "ష": "sh", "స": "s", "హ": "h", "ం": "n", "ః": "", "ఋ": "r", "ృ": "r",
}
# [Kannada, 2026-10-06] Same letter values as Telugu (the scripts are siblings).
_KANNADA = {
    "ಕ": "k", "ಖ": "kh", "ಗ": "g", "ಘ": "gh", "ಙ": "n", "ಚ": "ch", "ಛ": "chh", "ಜ": "j", "ಝ": "jh", "ಞ": "n",
    "ಟ": "t", "ಠ": "th", "ಡ": "d", "ಢ": "dh", "ಣ": "n", "ತ": "t", "ಥ": "th", "ದ": "d", "ಧ": "dh", "ನ": "n",
    "ಪ": "p", "ಫ": "ph", "ಬ": "b", "ಭ": "bh", "ಮ": "m", "ಯ": "y", "ರ": "r", "ಱ": "r", "ಲ": "l", "ಳ": "l", "ೞ": "l",
    "ವ": "v", "ಶ": "sh", "ಷ": "sh", "ಸ": "s", "ಹ": "h", "ಂ": "n", "ಃ": "", "ಋ": "r", "ೃ": "r",
}
_KANNADA_NUKTA = {"ಜ": "z", "ಫ": "f"}  # ಜ಼, ಫ಼ in loanwords
_NUKTA_SIGN = "़"
# Telugu case endings glued to a place name: హిమాయత్‌నగర్‌లో ("in Himayatnagar").
_TELUGU_SUFFIXES = ("లోని", "లో", "నుండి", "నుంచి", "దగ్గర", "వద్ద", "కి", "కు")
# [Marathi + Kannada, 2026-10-06] Case endings glued to a place name: Kannada
# ಜಯನಗರದಲ್ಲಿ ("in Jayanagar"), ಮೈಸೂರಿನಿಂದ ("from Mysuru"); Marathi कोथरूडमध्ये,
# बाणेरजवळ, पुण्यात, कोथरूडला. Tried only when the word as written (with a
# Telugu ending taken off) names no known place, so no Hindi or Telugu
# reading changes.
_MR_KN_SUFFIXES = (
    "ದಲ್ಲಿರುವ", "ನಲ್ಲಿರುವ", "ಯಲ್ಲಿರುವ", "ದಲ್ಲಿ", "ನಲ್ಲಿ", "ಯಲ್ಲಿ", "ಲ್ಲಿ", "ದಿಂದ", "ನಿಂದ", "ಯಿಂದ", "ಕ್ಕೆ", "ಹತ್ತಿರ", "ಬಳಿ", "ಗೆ",
    "मधील", "मध्ये", "मधे", "जवळ", "पासून", "हून", "च्या", "चा", "ची", "चे", "ात", "ला",
)
_INDIC_TOKEN = re.compile(r"[ऀ-ॿఀ-౿ಀ-೿‌‍]+")
_LATIN_TOKEN = re.compile(r"[A-Za-z]+")
# A city name is less specific than a locality: in "हैदराबाद के कुकटपल्ली में"
# the answer is Kukatpally.
_CITIES = frozenset({"hyderabad", "secunderabad", "warangal", "kurnool", "vijayawada", "visakhapatnam", "bengaluru", "bangalore",
                     "chennai", "mumbai", "delhi", "new delhi", "pune", "kolkata"})


_VIRAMA = {"्", "్", "್"}
# Independent vowels and vowel signs → a vowel letter. Vowels are dropped from
# the skeleton, but they must be present until then: without them हिल्स
# ("hills") would read h-l-s as "lh" and lose its h to the aspiration fold.
_VOWELS = {
    **{c: "a" for c in "अआऐऔािैौఅఆఐఔాైౌ"},
    **{c: "i" for c in "इईीిీఇఈ"},
    **{c: "u" for c in "उऊुूఉఊుూ"},
    **{c: "e" for c in "एेఎఏెే"},
    **{c: "o" for c in "ओोఒఓొో"},
    # Kannada
    **{c: "a" for c in "ಅಆಐಔಾೈೌ"},
    **{c: "i" for c in "ಇಈಿೀ"},
    **{c: "u" for c in "ಉಊುೂ"},
    **{c: "e" for c in "ಎಏೆೇ"},
    **{c: "o" for c in "ಒಓೊೋ"},
}


def transliterate(text: str) -> str:
    """Devanagari/Telugu/Kannada → rough Latin, keeping a vowel after each syllable."""
    out: list[str] = []
    chars = unicodedata.normalize("NFC", text)
    i = 0
    while i < len(chars):
        ch = chars[i]
        consonant = None
        if i + 1 < len(chars) and chars[i + 1] == _NUKTA_SIGN and ch in _NUKTA:
            consonant, i = _NUKTA[ch], i + 1
        elif ch in _DEVANAGARI and ch not in "ंँःऋृ":
            consonant = _DEVANAGARI[ch]
        elif ch in _TELUGU and ch not in "ంఃఋృ":
            consonant = _TELUGU[ch]
        elif i + 1 < len(chars) and chars[i + 1] == "಼" and ch in _KANNADA_NUKTA:
            consonant, i = _KANNADA_NUKTA[ch], i + 1
        elif ch in _KANNADA and ch not in "ಂಃಋೃ":
            consonant = _KANNADA[ch]
        if consonant is not None:
            out.append(consonant)
            nxt = chars[i + 1] if i + 1 < len(chars) else ""
            if nxt not in _VIRAMA and nxt not in _VOWELS:
                out.append("a")  # the inherent vowel
        elif ch in _DEVANAGARI:
            out.append(_DEVANAGARI[ch])  # anusvara n, vocalic r
        elif ch in _TELUGU:
            out.append(_TELUGU[ch])
        elif ch in _KANNADA:
            out.append(_KANNADA[ch])
        elif ch in _VOWELS:
            out.append(_VOWELS[ch])
        elif "a" <= ch.lower() <= "z":
            out.append(ch.lower())
        # virama, nukta, ZWNJ/ZWJ, spaces, punctuation: dropped
        i += 1
    return "".join(out)


def skeleton(text: str) -> str:
    """The comparison key: consonants only, variants folded, repeats collapsed."""
    s = transliterate(text).lower()
    s = re.sub(r"y\b", "", s) if s.endswith("y") else s  # "Kukatpally": final y is a vowel sound
    s = s.replace("ch", "C").replace("c", "k").replace("C", "c")
    s = re.sub(r"(?<=[aeiou])w(?![aeiou])", "", s)  # "Gachibowli": ow is a vowel sound (गाचीबौली)
    s = s.replace("q", "k").replace("z", "j").replace("x", "ks").replace("w", "v").replace("f", "p")
    s = re.sub(r"(?<=[bcdgjklmnprstvy])h", "", s)  # aspiration and sh: dh→d, bh→b, sh→s, kh→k
    s = re.sub(r"m(?=[pb])", "n", s)                # anusvara before p/b is written m in Latin
    s = re.sub(r"[aeiou]", "", s)
    return re.sub(r"(.)\1+", r"\1", s)


def _strip_telugu_suffix(token: str) -> str:
    token = token.replace("‌", "").replace("‍", "")
    for suffix in _TELUGU_SUFFIXES:
        if token.endswith(suffix) and len(token) > len(suffix) + 2:
            return token[: -len(suffix)]
    return token


def _strip_mr_kn_suffix(token: str) -> str:
    token = token.replace("‌", "").replace("‍", "")
    for suffix in _MR_KN_SUFFIXES:
        if token.endswith(suffix) and len(token) > len(suffix) + 2:
            return token[: -len(suffix)]
    return token


def find_known_locality(text: str, known: Iterable[str]) -> str | None:
    """The known locality named in the text, in any script, or None. A
    locality beats a city; otherwise the earliest mention wins."""
    names = [n.strip() for n in known if n and n.strip()]
    if not names or not text:
        return None
    by_key: dict[str, str] = {}
    for name in names:
        key = skeleton(re.sub(r"[^A-Za-z ]", " ", name))
        if key and key not in by_key:
            by_key[key] = name
    hits: list[tuple[int, int, str]] = []  # (is_city, position, name)

    # 1. Exact Latin name, any case ("himayatnagar", "Jubilee Hills").
    low = text.lower()
    for name in names:
        m = re.search(r"(?<![a-z])" + re.escape(name.lower()) + r"(?![a-z])", low)
        if m:
            hits.append((name.lower() in _CITIES, m.start(), name))

    # 2. Devanagari / Telugu / transliterated Latin: 1–3 word windows by skeleton.
    for pattern, min_len in ((_INDIC_TOKEN, 4), (_LATIN_TOKEN, 5)):
        tokens = [(m.start(), m.group(0)) for m in pattern.finditer(text)]
        for i in range(len(tokens)):
            for width in (3, 2, 1):
                window = tokens[i: i + width]
                if len(window) < width:
                    continue
                words = [w for _, w in window]
                last = words[-1]
                words[-1] = _strip_telugu_suffix(last)
                key = skeleton("".join(words))
                if not (len(key) >= min_len and key in by_key):
                    words[-1] = _strip_mr_kn_suffix(last)  # Marathi/Kannada ending, only as a second try
                    key = skeleton("".join(words))
                    # Kannada writes a final "m" as anusvara: ಮಲ್ಲೇಶ್ವರಂ = Malleshwaram.
                    if key not in by_key and key.endswith("n") and any("ಀ" <= ch <= "೿" for ch in words[-1]):
                        key = key[:-1] + "m" if key[:-1] + "m" in by_key else key
                if len(key) >= min_len and key in by_key:
                    name = by_key[key]
                    hits.append((name.lower() in _CITIES, window[0][0], name))
                    break
    if not hits:
        return None
    hits.sort()
    return hits[0][2]

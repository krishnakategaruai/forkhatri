# [IMP-B, owner 2026-09-30] Spelling-tolerant text matching for search.
#
# Indian names and places are typed many ways: "Krishna"/"krishna"/"Krishnaa",
# "Kukatpally"/"Kukatpalli", "Dilsukhnagar"/"Dilsuk nagar", "LB Nagar"/"L.B.
# Nagar". `fold()` lower-cases, strips accents and punctuation, and reduces
# the common romanisation variants (doubled vowels, aspirated consonants,
# w/v, y/i at word end, final 'a') to one key, so both sides of a comparison
# land on the same spelling. `matches_prefix()` then says whether every query
# word starts some word of the text. Devanagari and Telugu text is compared as
# typed (lower-cased); transliterating it to Latin would need a library and
# is not attempted.
from __future__ import annotations

import re
import unicodedata

# Words split on whitespace and punctuation only: Devanagari and Telugu vowel
# signs are combining marks, which `\w` does not match, so a \w-based split
# would cut "बिजली" into pieces.
_WORD = re.compile(r"[^\s\-.,;:/!?()\[\]{}\"'`|&+*=<>#@%^~]+", re.UNICODE)
_ASPIRATES = (("kh", "k"), ("gh", "g"), ("chh", "c"), ("ch", "c"), ("jh", "j"), ("th", "t"), ("dh", "d"),
              ("ph", "f"), ("bh", "b"), ("sh", "s"), ("w", "v"), ("z", "j"), ("q", "k"), ("ck", "k"))


def _fold_word(word: str) -> str:
    if not word.isascii():
        return word
    w = word
    for a, b in _ASPIRATES:
        w = w.replace(a, b)
    w = w.replace("ee", "i").replace("oo", "u").replace("ou", "u")  # before collapsing doubles: "aneeta" -> "anita"
    w = re.sub(r"(.)\1+", r"\1", w)          # doubled letters: "krishnaa" -> "krishna", "palli" -> "pali"
    if len(w) > 3 and w.endswith("y"):     # "kukatpally" -> "kukatpali"
        w = w[:-1] + "i"
    if len(w) > 3 and w.endswith("a"):     # "krishna" -> "krishn"
        w = w[:-1]
    return w


def words(text: str | None) -> list[str]:
    if not text:
        return []
    norm = unicodedata.normalize("NFKD", text)
    norm = "".join(ch for ch in norm if not unicodedata.combining(ch) or not ch.isascii()).lower()
    # "l.b. nagar" -> "lb nagar": join single letters split by dots
    norm = re.sub(r"\b([a-z])\.\s*(?=[a-z]\b)", r"\1", norm)
    return [_fold_word(w) for w in _WORD.findall(norm)]


def fold(text: str | None) -> str:
    return " ".join(words(text))


def prefix_hits(query_words: list[str], text: str | None) -> int:
    """How many query words start a word in `text` (folded both sides)."""
    hay = words(text)
    return sum(1 for q in query_words if any(h.startswith(q) for h in hay))


def contains_phrase(query: str, text: str | None) -> bool:
    fq, ft = fold(query), fold(text)
    return bool(fq) and fq in ft

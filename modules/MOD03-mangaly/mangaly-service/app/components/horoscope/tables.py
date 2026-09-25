"""The classical tables behind Ashta Koota (Guna Milan) and Mangal dosha.

Everything here is fixed data from the standard Jyotisha texts as used by the
common North-Indian matching practice (Muhurta Chintamani / Brihat Parashara
tradition; the same tables Shaadi.com, Drik Panchang and AstroSage publish).
No runtime data, no I/O: pure constants and tiny lookups, so `interface.py`'s
scoring reads as the rules themselves.

Rashi keys are the twelve `mangaly-web/lib/profileCategoryConfig.ts` RASHIS
values (`mesh` ... `meen`), so a rashi the person typed and a rashi we computed
compare as the same token. Nakshatra keys are lower-case ASCII slugs; the
member-facing names come from the `horoscope` i18n namespace.
"""

from __future__ import annotations

from typing import Final

# --- Zodiac -----------------------------------------------------------------

RASHIS: Final[tuple[str, ...]] = (
    "mesh",
    "vrishabh",
    "mithun",
    "kark",
    "simha",
    "kanya",
    "tula",
    "vrishchik",
    "dhanu",
    "makar",
    "kumbh",
    "meen",
)

# Rashi lord (the seven classical grahas; Rahu/Ketu own no sign).
RASHI_LORD: Final[dict[str, str]] = {
    "mesh": "mars",
    "vrishabh": "venus",
    "mithun": "mercury",
    "kark": "moon",
    "simha": "sun",
    "kanya": "mercury",
    "tula": "venus",
    "vrishchik": "mars",
    "dhanu": "jupiter",
    "makar": "saturn",
    "kumbh": "saturn",
    "meen": "jupiter",
}

# Naisargika (natural) friendship between the seven grahas: for each planet,
# who is a friend and who is an enemy; everyone else is neutral.
_FRIENDS: Final[dict[str, frozenset[str]]] = {
    "sun": frozenset({"moon", "mars", "jupiter"}),
    "moon": frozenset({"sun", "mercury"}),
    "mars": frozenset({"sun", "moon", "jupiter"}),
    "mercury": frozenset({"sun", "venus"}),
    "jupiter": frozenset({"sun", "moon", "mars"}),
    "venus": frozenset({"mercury", "saturn"}),
    "saturn": frozenset({"mercury", "venus"}),
}
_ENEMIES: Final[dict[str, frozenset[str]]] = {
    "sun": frozenset({"venus", "saturn"}),
    "moon": frozenset(),
    "mars": frozenset({"mercury"}),
    "mercury": frozenset({"moon"}),
    "jupiter": frozenset({"mercury", "venus"}),
    "venus": frozenset({"sun", "moon"}),
    "saturn": frozenset({"sun", "moon", "mars"}),
}


def relation(planet: str, other: str) -> str:
    """How `planet` regards `other`: 'same' | 'friend' | 'neutral' | 'enemy'."""
    if planet == other:
        return "same"
    if other in _FRIENDS[planet]:
        return "friend"
    if other in _ENEMIES[planet]:
        return "enemy"
    return "neutral"


# --- Nakshatras ---------------------------------------------------------------

NAKSHATRAS: Final[tuple[str, ...]] = (
    "ashwini",
    "bharani",
    "krittika",
    "rohini",
    "mrigashira",
    "ardra",
    "punarvasu",
    "pushya",
    "ashlesha",
    "magha",
    "purva_phalguni",
    "uttara_phalguni",
    "hasta",
    "chitra",
    "swati",
    "vishakha",
    "anuradha",
    "jyeshtha",
    "mula",
    "purva_ashadha",
    "uttara_ashadha",
    "shravana",
    "dhanishta",
    "shatabhisha",
    "purva_bhadrapada",
    "uttara_bhadrapada",
    "revati",
)

# Spellings people type by hand (profile field `horoscope.nakshatra` is free
# text) -> canonical key. Matching is done on a lower-cased, de-punctuated
# form, so "Purva Phalguni", "purva-phalguni" and "Pubba" all resolve.
NAKSHATRA_ALIASES: Final[dict[str, str]] = {
    "ashwini": "ashwini",
    "aswini": "ashwini",
    "ashvini": "ashwini",
    "bharani": "bharani",
    "krittika": "krittika",
    "kritika": "krittika",
    "krithika": "krittika",
    "karthika": "krittika",
    "rohini": "rohini",
    "mrigashira": "mrigashira",
    "mrigasira": "mrigashira",
    "mrigashirsha": "mrigashira",
    "mrigasheersha": "mrigashira",
    "makayiram": "mrigashira",
    "ardra": "ardra",
    "arudra": "ardra",
    "thiruvathira": "ardra",
    "punarvasu": "punarvasu",
    "punarpoosam": "punarvasu",
    "pushya": "pushya",
    "pushyami": "pushya",
    "poosam": "pushya",
    "pooyam": "pushya",
    "ashlesha": "ashlesha",
    "aslesha": "ashlesha",
    "ayilyam": "ashlesha",
    "magha": "magha",
    "makha": "magha",
    "makam": "magha",
    "purvaphalguni": "purva_phalguni",
    "poorvaphalguni": "purva_phalguni",
    "pubba": "purva_phalguni",
    "pooram": "purva_phalguni",
    "uttaraphalguni": "uttara_phalguni",
    "uthraphalguni": "uttara_phalguni",
    "uttara": "uttara_phalguni",
    "uthiram": "uttara_phalguni",
    "hasta": "hasta",
    "hastha": "hasta",
    "atham": "hasta",
    "chitra": "chitra",
    "chitta": "chitra",
    "chithirai": "chitra",
    "swati": "swati",
    "swathi": "swati",
    "chothi": "swati",
    "vishakha": "vishakha",
    "visakha": "vishakha",
    "visakam": "vishakha",
    "anuradha": "anuradha",
    "anusham": "anuradha",
    "anizham": "anuradha",
    "jyeshtha": "jyeshtha",
    "jyeshta": "jyeshtha",
    "jyestha": "jyeshtha",
    "kettai": "jyeshtha",
    "thrikketta": "jyeshtha",
    "mula": "mula",
    "moola": "mula",
    "moolam": "mula",
    "purvaashadha": "purva_ashadha",
    "purvashadha": "purva_ashadha",
    "poorvashada": "purva_ashadha",
    "purvashada": "purva_ashadha",
    "pooradam": "purva_ashadha",
    "uttaraashadha": "uttara_ashadha",
    "uttarashadha": "uttara_ashadha",
    "uttarashada": "uttara_ashadha",
    "uthrashada": "uttara_ashadha",
    "uthradam": "uttara_ashadha",
    "shravana": "shravana",
    "sravana": "shravana",
    "thiruvonam": "shravana",
    "dhanishta": "dhanishta",
    "dhanishtha": "dhanishta",
    "avittam": "dhanishta",
    "shatabhisha": "shatabhisha",
    "satabhisha": "shatabhisha",
    "shathabhisha": "shatabhisha",
    "sadayam": "shatabhisha",
    "chathayam": "shatabhisha",
    "purvabhadrapada": "purva_bhadrapada",
    "poorvabhadra": "purva_bhadrapada",
    "purvabhadra": "purva_bhadrapada",
    "pooruruttathi": "purva_bhadrapada",
    "uttarabhadrapada": "uttara_bhadrapada",
    "uttarabhadra": "uttara_bhadrapada",
    "uthrattathi": "uttara_bhadrapada",
    "revati": "revati",
    "revathi": "revati",
}

# Yoni: the animal of each nakshatra (index = nakshatra index). The texts also
# give each animal a sex; it does not change the Yoni score.
YONI: Final[tuple[str, ...]] = (
    "horse",  # Ashwini
    "elephant",  # Bharani
    "sheep",  # Krittika
    "serpent",  # Rohini
    "serpent",  # Mrigashira
    "dog",  # Ardra
    "cat",  # Punarvasu
    "sheep",  # Pushya
    "cat",  # Ashlesha
    "rat",  # Magha
    "rat",  # Purva Phalguni
    "cow",  # Uttara Phalguni
    "buffalo",  # Hasta
    "tiger",  # Chitra
    "buffalo",  # Swati
    "tiger",  # Vishakha
    "deer",  # Anuradha
    "deer",  # Jyeshtha
    "dog",  # Mula
    "monkey",  # Purva Ashadha
    "mongoose",  # Uttara Ashadha
    "monkey",  # Shravana
    "lion",  # Dhanishta
    "horse",  # Shatabhisha
    "lion",  # Purva Bhadrapada
    "cow",  # Uttara Bhadrapada
    "elephant",  # Revati
)

_YONI_ORDER: Final[tuple[str, ...]] = (
    "horse",
    "elephant",
    "sheep",
    "serpent",
    "dog",
    "cat",
    "rat",
    "cow",
    "buffalo",
    "tiger",
    "deer",
    "monkey",
    "mongoose",
    "lion",
)
# 4 = same animal, 3 = friendly, 2 = neutral, 1 = unfriendly, 0 = sworn
# enemies (horse/buffalo, elephant/lion, sheep/monkey, serpent/mongoose,
# dog/deer, cat/rat, cow/tiger). Symmetric.
_YONI_POINTS: Final[tuple[tuple[int, ...], ...]] = (
    (4, 2, 2, 3, 2, 2, 2, 1, 0, 1, 3, 3, 2, 1),
    (2, 4, 3, 3, 2, 2, 2, 2, 3, 1, 2, 3, 2, 0),
    (2, 3, 4, 2, 1, 2, 1, 3, 3, 1, 2, 0, 3, 1),
    (3, 3, 2, 4, 2, 1, 1, 1, 1, 2, 2, 2, 0, 2),
    (2, 2, 1, 2, 4, 2, 1, 2, 2, 1, 0, 2, 1, 1),
    (2, 2, 2, 1, 2, 4, 0, 2, 2, 1, 3, 3, 2, 1),
    (2, 2, 1, 1, 1, 0, 4, 2, 2, 2, 2, 2, 1, 2),
    (1, 2, 3, 1, 2, 2, 2, 4, 3, 0, 3, 2, 2, 1),
    (0, 3, 3, 1, 2, 2, 2, 3, 4, 1, 2, 2, 2, 1),
    (1, 1, 1, 2, 1, 1, 2, 0, 1, 4, 1, 1, 2, 1),
    (3, 2, 2, 2, 0, 3, 2, 3, 2, 1, 4, 2, 2, 1),
    (3, 3, 0, 2, 2, 3, 2, 2, 2, 1, 2, 4, 3, 2),
    (2, 2, 3, 0, 1, 2, 1, 2, 2, 2, 2, 3, 4, 2),
    (1, 0, 1, 2, 1, 1, 2, 1, 1, 1, 1, 2, 2, 4),
)


def yoni_points(a: str, b: str) -> int:
    return _YONI_POINTS[_YONI_ORDER.index(a)][_YONI_ORDER.index(b)]


# Gana: deva (divine), manushya (human), rakshasa (demonic) temperament.
GANA: Final[tuple[str, ...]] = (
    "deva",  # Ashwini
    "manushya",  # Bharani
    "rakshasa",  # Krittika
    "manushya",  # Rohini
    "deva",  # Mrigashira
    "manushya",  # Ardra
    "deva",  # Punarvasu
    "deva",  # Pushya
    "rakshasa",  # Ashlesha
    "rakshasa",  # Magha
    "manushya",  # Purva Phalguni
    "manushya",  # Uttara Phalguni
    "deva",  # Hasta
    "rakshasa",  # Chitra
    "deva",  # Swati
    "rakshasa",  # Vishakha
    "deva",  # Anuradha
    "rakshasa",  # Jyeshtha
    "rakshasa",  # Mula
    "manushya",  # Purva Ashadha
    "manushya",  # Uttara Ashadha
    "deva",  # Shravana
    "rakshasa",  # Dhanishta
    "rakshasa",  # Shatabhisha
    "manushya",  # Purva Bhadrapada
    "manushya",  # Uttara Bhadrapada
    "deva",  # Revati
)

# (bride's gana, groom's gana) -> points out of 6.
GANA_POINTS: Final[dict[tuple[str, str], int]] = {
    ("deva", "deva"): 6,
    ("manushya", "manushya"): 6,
    ("rakshasa", "rakshasa"): 6,
    ("deva", "manushya"): 6,
    ("manushya", "deva"): 5,
    ("deva", "rakshasa"): 1,
    ("rakshasa", "deva"): 1,
    ("manushya", "rakshasa"): 0,
    ("rakshasa", "manushya"): 0,
}

# Nadi: adi (vata), madhya (pitta), antya (kapha) - the cycle 1-2-3 repeating
# over the 27 nakshatras: forward for 1..9, backward for 10..18, forward for
# 19..27.
NADI: Final[tuple[str, ...]] = (
    "adi",
    "madhya",
    "antya",
    "antya",
    "madhya",
    "adi",
    "adi",
    "madhya",
    "antya",
    "antya",
    "madhya",
    "adi",
    "adi",
    "madhya",
    "antya",
    "antya",
    "madhya",
    "adi",
    "adi",
    "madhya",
    "antya",
    "antya",
    "madhya",
    "adi",
    "adi",
    "madhya",
    "antya",
)

# Varna by Moon rashi (water signs brahmin, fire kshatriya, earth vaishya,
# air shudra); the rank decides "groom's varna not below the bride's".
VARNA: Final[dict[str, str]] = {
    "kark": "brahmin",
    "vrishchik": "brahmin",
    "meen": "brahmin",
    "mesh": "kshatriya",
    "simha": "kshatriya",
    "dhanu": "kshatriya",
    "vrishabh": "vaishya",
    "kanya": "vaishya",
    "makar": "vaishya",
    "mithun": "shudra",
    "tula": "shudra",
    "kumbh": "shudra",
}
VARNA_RANK: Final[dict[str, int]] = {"brahmin": 4, "kshatriya": 3, "vaishya": 2, "shudra": 1}

# Vashya by rashi (whole-sign form of the classical split-sign rule, the
# form every matching site uses).
VASHYA: Final[dict[str, str]] = {
    "mesh": "chatushpada",
    "vrishabh": "chatushpada",
    "dhanu": "chatushpada",
    "makar": "chatushpada",
    "mithun": "manava",
    "kanya": "manava",
    "tula": "manava",
    "kumbh": "manava",
    "kark": "jalachara",
    "meen": "jalachara",
    "simha": "vanachara",
    "vrishchik": "keeta",
}
_VASHYA_ORDER: Final[tuple[str, ...]] = ("chatushpada", "manava", "jalachara", "vanachara", "keeta")
_VASHYA_POINTS: Final[tuple[tuple[float, ...], ...]] = (
    (2, 1, 1, 0, 1),
    (1, 2, 0.5, 0, 1),
    (1, 0.5, 2, 1, 1),
    (0, 0, 1, 2, 0),
    (1, 1, 1, 0, 2),
)


def vashya_points(a: str, b: str) -> float:
    return _VASHYA_POINTS[_VASHYA_ORDER.index(a)][_VASHYA_ORDER.index(b)]


# Tara: counting from one nakshatra to the other (inclusive), 1..27, the
# remainder mod 9 names the tara; 3 (vipat), 5 (pratyari) and 7 (vadha) are
# the inauspicious ones.
TARA_NAMES: Final[tuple[str, ...]] = (
    "janma",
    "sampat",
    "vipat",
    "kshema",
    "pratyari",
    "sadhaka",
    "vadha",
    "mitra",
    "ati_mitra",
)
TARA_BAD: Final[frozenset[int]] = frozenset({3, 5, 7})

# Bhakoot: rashi distances (counted both ways) that form a dosha.
BHAKOOT_DOSHA_PAIRS: Final[frozenset[frozenset[int]]] = frozenset(
    {frozenset({2, 12}), frozenset({5, 9}), frozenset({6, 8})}
)

# Mangal dosha houses, counted from Lagna and from the Moon. The 2nd house is
# included (the South-Indian reading; the North-Indian one leaves it out and
# is therefore never stricter than this).
MANGLIK_HOUSES: Final[frozenset[int]] = frozenset({1, 2, 4, 7, 8, 12})
MARS_OWN_SIGNS: Final[frozenset[str]] = frozenset({"mesh", "vrishchik"})
MARS_EXALTED_SIGN: Final[str] = "makar"

# Guna Milan reading bands, out of 36.
BANDS: Final[tuple[tuple[float, str], ...]] = (
    (33, "excellent"),
    (25, "very_good"),
    (18, "acceptable"),
    (0, "not_recommended"),
)


def band_for(total: float) -> str:
    for floor, name in BANDS:
        if total >= floor:
            return name
    return "not_recommended"

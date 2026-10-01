"""Places: a small built-in table of Indian cities for "near me" discovery.

Counsel consultations happen online, so location is about local knowledge
(courts, registrations, taxes, farming conditions, language), not travel.
No external geocoding API is used: a consultant picks a city from this list
(or types another one), and a viewer picks theirs or lets the browser find the
nearest listed city from its own coordinates. Distances are straight-line
(haversine) between city centres, rounded, so they are honest approximations.
"""

from __future__ import annotations

import math

# id, English, Hindi, Telugu, lat, lng. English is what is stored in provider.city.
CITIES: list[tuple[str, str, str, str, float, float]] = [
    ("hyderabad", "Hyderabad", "हैदराबाद", "హైదరాబాద్", 17.3850, 78.4867),
    ("warangal", "Warangal", "वारंगल", "వరంగల్", 17.9689, 79.5941),
    ("karimnagar", "Karimnagar", "करीमनगर", "కరీంనగర్", 18.4386, 79.1288),
    ("nizamabad", "Nizamabad", "निज़ामाबाद", "నిజామాబాద్", 18.6725, 78.0941),
    ("khammam", "Khammam", "खम्मम", "ఖమ్మం", 17.2473, 80.1514),
    ("vijayawada", "Vijayawada", "विजयवाड़ा", "విజయవాడ", 16.5062, 80.6480),
    ("visakhapatnam", "Visakhapatnam", "विशाखापत्तनम", "విశాఖపట్నం", 17.6868, 83.2185),
    ("guntur", "Guntur", "गुंटूर", "గుంటూరు", 16.3067, 80.4365),
    ("nellore", "Nellore", "नेल्लोर", "నెల్లూరు", 14.4426, 79.9865),
    ("tirupati", "Tirupati", "तिरुपति", "తిరుపతి", 13.6288, 79.4192),
    ("kurnool", "Kurnool", "कुरनूल", "కర్నూలు", 15.8281, 78.0373),
    ("rajahmundry", "Rajahmundry", "राजमहेंद्रवरम", "రాజమహేంద్రవరం", 17.0005, 81.8040),
    ("kakinada", "Kakinada", "काकीनाडा", "కాకినాడ", 16.9891, 82.2475),
    ("eluru", "Eluru", "एलुरु", "ఏలూరు", 16.7107, 81.0952),
    ("nuzvid", "Nuzvid", "नूज़िवीडु", "నూజివీడు", 16.7880, 80.8460),
    ("ongole", "Ongole", "ओंगोल", "ఒంగోలు", 15.5057, 80.0499),
    ("anantapur", "Anantapur", "अनंतपुर", "అనంతపురం", 14.6819, 77.6006),
    ("kadapa", "Kadapa", "कडप्पा", "కడప", 14.4674, 78.8241),
    ("bengaluru", "Bengaluru", "बेंगलुरु", "బెంగళూరు", 12.9716, 77.5946),
    ("mysuru", "Mysuru", "मैसूरु", "మైసూరు", 12.2958, 76.6394),
    ("chennai", "Chennai", "चेन्नई", "చెన్నై", 13.0827, 80.2707),
    ("coimbatore", "Coimbatore", "कोयंबटूर", "కోయంబత్తూరు", 11.0168, 76.9558),
    ("kochi", "Kochi", "कोच्चि", "కొచ్చి", 9.9312, 76.2673),
    ("thiruvananthapuram", "Thiruvananthapuram", "तिरुवनंतपुरम", "తిరువనంతపురం", 8.5241, 76.9366),
    ("mumbai", "Mumbai", "मुंबई", "ముంబై", 19.0760, 72.8777),
    ("pune", "Pune", "पुणे", "పుణే", 18.5204, 73.8567),
    ("nagpur", "Nagpur", "नागपुर", "నాగ్‌పూర్", 21.1458, 79.0882),
    ("ahmedabad", "Ahmedabad", "अहमदाबाद", "అహ్మదాబాద్", 23.0225, 72.5714),
    ("surat", "Surat", "सूरत", "సూరత్", 21.1702, 72.8311),
    ("delhi", "Delhi", "दिल्ली", "ఢిల్లీ", 28.6139, 77.2090),
    ("gurugram", "Gurugram", "गुरुग्राम", "గురుగ్రామ్", 28.4595, 77.0266),
    ("noida", "Noida", "नोएडा", "నోయిడా", 28.5355, 77.3910),
    ("jaipur", "Jaipur", "जयपुर", "జైపూర్", 26.9124, 75.7873),
    ("lucknow", "Lucknow", "लखनऊ", "లక్నో", 26.8467, 80.9462),
    ("varanasi", "Varanasi", "वाराणसी", "వారణాసి", 25.3176, 82.9739),
    ("chandigarh", "Chandigarh", "चंडीगढ़", "చండీగఢ్", 30.7333, 76.7794),
    ("amritsar", "Amritsar", "अमृतसर", "అమృత్‌సర్", 31.6340, 74.8723),
    ("ludhiana", "Ludhiana", "लुधियाना", "లూధియానా", 30.9010, 75.8573),
    ("dehradun", "Dehradun", "देहरादून", "డెహ్రాడూన్", 30.3165, 78.0322),
    ("indore", "Indore", "इंदौर", "ఇండోర్", 22.7196, 75.8577),
    ("bhopal", "Bhopal", "भोपाल", "భోపాల్", 23.2599, 77.4126),
    ("kolkata", "Kolkata", "कोलकाता", "కోల్‌కతా", 22.5726, 88.3639),
    ("bhubaneswar", "Bhubaneswar", "भुवनेश्वर", "భువనేశ్వర్", 20.2961, 85.8245),
    ("patna", "Patna", "पटना", "పాట్నా", 25.5941, 85.1376),
    ("guwahati", "Guwahati", "गुवाहाटी", "గువాహటి", 26.1445, 91.7362),
]

# Older or common spellings people type, mapped to the list above.
ALIASES = {
    "bangalore": "bengaluru", "mysore": "mysuru", "vizag": "visakhapatnam", "vishakhapatnam": "visakhapatnam",
    "rajamahendravaram": "rajahmundry", "rajamundry": "rajahmundry", "gurgaon": "gurugram", "new delhi": "delhi",
    "bombay": "mumbai", "madras": "chennai", "calcutta": "kolkata", "trivandrum": "thiruvananthapuram", "cochin": "kochi",
    "secunderabad": "hyderabad", "cuddapah": "kadapa", "nuzividu": "nuzvid", "nuzividu town": "nuzvid", "anantapuramu": "anantapur",
}

# "Nearby" means within this straight-line distance of the viewer's city.
NEARBY_KM = 150
# Same metropolitan area (e.g. Secunderabad and Hyderabad) counts as "your city".
SAME_CITY_KM = 30

_BY_ID = {c[0]: c for c in CITIES}


def resolve(name: str | None) -> str | None:
    """A city id from an id, an English name, a local-language name or a known alias."""
    if not name:
        return None
    key = " ".join(name.strip().lower().split())
    if key in _BY_ID:
        return key
    if key in ALIASES:
        return ALIASES[key]
    for c in CITIES:
        if key in (c[1].lower(), c[2], c[3]):
            return c[0]
    return None


def label(name: str | None, lang: str) -> str | None:
    """The city in the viewer's language when it is a listed city; otherwise as typed."""
    cid = resolve(name)
    if not cid:
        return name
    c = _BY_ID[cid]
    return {"hi": c[2], "te": c[3]}.get(lang, c[1])


def distance_km(a: str | None, b: str | None) -> int | None:
    ca, cb = _BY_ID.get(resolve(a) or ""), _BY_ID.get(resolve(b) or "")
    if not ca or not cb:
        return None
    lat1, lon1, lat2, lon2 = map(math.radians, (ca[4], ca[5], cb[4], cb[5]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return round(2 * 6371 * math.asin(math.sqrt(h)))


def listing(lang: str) -> list[dict]:
    rows = [{"id": c[0], "name": {"hi": c[2], "te": c[3]}.get(lang, c[1]), "value": c[1], "lat": c[4], "lng": c[5]} for c in CITIES]
    return sorted(rows, key=lambda r: r["name"])

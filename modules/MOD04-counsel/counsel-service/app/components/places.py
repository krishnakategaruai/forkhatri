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

# id, English, Hindi, Telugu, Marathi, Kannada, lat, lng. English is what is stored in provider.city.
CITIES: list[tuple[str, str, str, str, str, str, float, float]] = [
    ("hyderabad", "Hyderabad", "हैदराबाद", "హైదరాబాద్", "हैदराबाद", "ಹೈದರಾಬಾದ್", 17.3850, 78.4867),
    ("warangal", "Warangal", "वारंगल", "వరంగల్", "वरंगल", "ವರಂಗಲ್", 17.9689, 79.5941),
    ("karimnagar", "Karimnagar", "करीमनगर", "కరీంనగర్", "करीमनगर", "ಕರೀಂನಗರ", 18.4386, 79.1288),
    ("nizamabad", "Nizamabad", "निज़ामाबाद", "నిజామాబాద్", "निजामाबाद", "ನಿಜಾಮಾಬಾದ್", 18.6725, 78.0941),
    ("khammam", "Khammam", "खम्मम", "ఖమ్మం", "खम्मम", "ಖಮ್ಮಂ", 17.2473, 80.1514),
    ("vijayawada", "Vijayawada", "विजयवाड़ा", "విజయవాడ", "विजयवाडा", "ವಿಜಯವಾಡ", 16.5062, 80.6480),
    ("visakhapatnam", "Visakhapatnam", "विशाखापत्तनम", "విశాఖపట్నం", "विशाखापट्टणम", "ವಿಶಾಖಪಟ್ಟಣ", 17.6868, 83.2185),
    ("guntur", "Guntur", "गुंटूर", "గుంటూరు", "गुंटूर", "ಗುಂಟೂರು", 16.3067, 80.4365),
    ("nellore", "Nellore", "नेल्लोर", "నెల్లూరు", "नेल्लोर", "ನೆಲ್ಲೂರು", 14.4426, 79.9865),
    ("tirupati", "Tirupati", "तिरुपति", "తిరుపతి", "तिरुपती", "ತಿರುಪತಿ", 13.6288, 79.4192),
    ("kurnool", "Kurnool", "कुरनूल", "కర్నూలు", "कर्नूल", "ಕರ್ನೂಲು", 15.8281, 78.0373),
    ("rajahmundry", "Rajahmundry", "राजमहेंद्रवरम", "రాజమహేంద్రవరం", "राजमहेंद्रवरम", "ರಾಜಮಹೇಂದ್ರವರಂ", 17.0005, 81.8040),
    ("kakinada", "Kakinada", "काकीनाडा", "కాకినాడ", "काकिनाडा", "ಕಾಕಿನಾಡ", 16.9891, 82.2475),
    ("eluru", "Eluru", "एलुरु", "ఏలూరు", "एलुरू", "ಏಲೂರು", 16.7107, 81.0952),
    ("nuzvid", "Nuzvid", "नूज़िवीडु", "నూజివీడు", "नुझिवीडू", "ನೂಜಿವೀಡು", 16.7880, 80.8460),
    ("ongole", "Ongole", "ओंगोल", "ఒంగోలు", "ओंगोल", "ಒಂಗೋಲು", 15.5057, 80.0499),
    ("anantapur", "Anantapur", "अनंतपुर", "అనంతపురం", "अनंतपूर", "ಅನಂತಪುರ", 14.6819, 77.6006),
    ("kadapa", "Kadapa", "कडप्पा", "కడప", "कडप्पा", "ಕಡಪ", 14.4674, 78.8241),
    ("bengaluru", "Bengaluru", "बेंगलुरु", "బెంగళూరు", "बंगळुरू", "ಬೆಂಗಳೂರು", 12.9716, 77.5946),
    ("mysuru", "Mysuru", "मैसूरु", "మైసూరు", "म्हैसूर", "ಮೈಸೂರು", 12.2958, 76.6394),
    ("chennai", "Chennai", "चेन्नई", "చెన్నై", "चेन्नई", "ಚೆನ್ನೈ", 13.0827, 80.2707),
    ("coimbatore", "Coimbatore", "कोयंबटूर", "కోయంబత్తూరు", "कोइम्बतूर", "ಕೊಯಮತ್ತೂರು", 11.0168, 76.9558),
    ("kochi", "Kochi", "कोच्चि", "కొచ్చి", "कोची", "ಕೊಚ್ಚಿ", 9.9312, 76.2673),
    ("thiruvananthapuram", "Thiruvananthapuram", "तिरुवनंतपुरम", "తిరువనంతపురం", "तिरुवनंतपुरम", "ತಿರುವನಂತಪುರ", 8.5241, 76.9366),
    ("mumbai", "Mumbai", "मुंबई", "ముంబై", "मुंबई", "ಮುಂಬೈ", 19.0760, 72.8777),
    ("pune", "Pune", "पुणे", "పుణే", "पुणे", "ಪುಣೆ", 18.5204, 73.8567),
    ("nagpur", "Nagpur", "नागपुर", "నాగ్‌పూర్", "नागपूर", "ನಾಗಪುರ", 21.1458, 79.0882),
    ("ahmedabad", "Ahmedabad", "अहमदाबाद", "అహ్మదాబాద్", "अहमदाबाद", "ಅಹಮದಾಬಾದ್", 23.0225, 72.5714),
    ("surat", "Surat", "सूरत", "సూరత్", "सुरत", "ಸೂರತ್", 21.1702, 72.8311),
    ("delhi", "Delhi", "दिल्ली", "ఢిల్లీ", "दिल्ली", "ದೆಹಲಿ", 28.6139, 77.2090),
    ("gurugram", "Gurugram", "गुरुग्राम", "గురుగ్రామ్", "गुरुग्राम", "ಗುರುಗ್ರಾಮ", 28.4595, 77.0266),
    ("noida", "Noida", "नोएडा", "నోయిడా", "नोएडा", "ನೋಯ್ಡಾ", 28.5355, 77.3910),
    ("jaipur", "Jaipur", "जयपुर", "జైపూర్", "जयपूर", "ಜೈಪುರ", 26.9124, 75.7873),
    ("lucknow", "Lucknow", "लखनऊ", "లక్నో", "लखनौ", "ಲಕ್ನೋ", 26.8467, 80.9462),
    ("varanasi", "Varanasi", "वाराणसी", "వారణాసి", "वाराणसी", "ವಾರಾಣಸಿ", 25.3176, 82.9739),
    ("chandigarh", "Chandigarh", "चंडीगढ़", "చండీగఢ్", "चंदीगड", "ಚಂಡೀಗಢ", 30.7333, 76.7794),
    ("amritsar", "Amritsar", "अमृतसर", "అమృత్‌సర్", "अमृतसर", "ಅಮೃತಸರ", 31.6340, 74.8723),
    ("ludhiana", "Ludhiana", "लुधियाना", "లూధియానా", "लुधियाना", "ಲೂಧಿಯಾನ", 30.9010, 75.8573),
    ("dehradun", "Dehradun", "देहरादून", "డెహ్రాడూన్", "डेहराडून", "ಡೆಹ್ರಾಡೂನ್", 30.3165, 78.0322),
    ("indore", "Indore", "इंदौर", "ఇండోర్", "इंदूर", "ಇಂದೋರ್", 22.7196, 75.8577),
    ("bhopal", "Bhopal", "भोपाल", "భోపాల్", "भोपाळ", "ಭೋಪಾಲ್", 23.2599, 77.4126),
    ("kolkata", "Kolkata", "कोलकाता", "కోల్‌కతా", "कोलकाता", "ಕೋಲ್ಕತ್ತಾ", 22.5726, 88.3639),
    ("bhubaneswar", "Bhubaneswar", "भुवनेश्वर", "భువనేశ్వర్", "भुवनेश्वर", "ಭುವನೇಶ್ವರ", 20.2961, 85.8245),
    ("patna", "Patna", "पटना", "పాట్నా", "पाटणा", "ಪಾಟ್ನಾ", 25.5941, 85.1376),
    ("guwahati", "Guwahati", "गुवाहाटी", "గువాహటి", "गुवाहाटी", "ಗುವಾಹಟಿ", 26.1445, 91.7362),
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
# Column of each language's name in a CITIES row (English is column 1).
_COLUMN = {"hi": 2, "te": 3, "mr": 4, "kn": 5}


def _name(c: tuple, lang: str) -> str:
    return c[_COLUMN.get(lang, 1)]


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
        if key == c[1].lower() or key in c[2:6]:
            return c[0]
    return None


def label(name: str | None, lang: str) -> str | None:
    """The city in the viewer's language when it is a listed city; otherwise as typed."""
    cid = resolve(name)
    if not cid:
        return name
    c = _BY_ID[cid]
    return _name(c, lang)


def distance_km(a: str | None, b: str | None) -> int | None:
    ca, cb = _BY_ID.get(resolve(a) or ""), _BY_ID.get(resolve(b) or "")
    if not ca or not cb:
        return None
    lat1, lon1, lat2, lon2 = map(math.radians, (ca[6], ca[7], cb[6], cb[7]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return round(2 * 6371 * math.asin(math.sqrt(h)))


def listing(lang: str) -> list[dict]:
    rows = [{"id": c[0], "name": _name(c, lang), "value": c[1], "lat": c[6], "lng": c[7]} for c in CITIES]
    return sorted(rows, key=lambda r: r["name"])

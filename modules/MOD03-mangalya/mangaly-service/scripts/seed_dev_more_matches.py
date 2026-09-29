"""Seed 24 more Mangaly candidates so Home and Discover have people to scroll.

Why this exists: after `seed_dev_accounts.py` and `seed_dev_families.py` the
development database holds about four brides and four grooms who can see each
other. The product owner looked at Home's "New matches" rail and Discover
(2026-09-22) and asked for "more pictures to scroll there". A matrimony app
with eight people in it cannot be judged as a matrimony app.

What it creates:
  * 14 brides (female, looking for a groom) and 10 grooms (male, looking for a
    bride), aged 24-34. Most live in Hyderabad, so they land in the results of
    the Hyderabad families already seeded (Varun Tandon wants a bride of
    25-31, Arjun Khanna 26-33, Rohan Bhatia 28-37; Divya Mehra wants a groom of
    27-34, Meera Sharma 28-36, Ishita Malhotra 29-38). A few live in
    Bengaluru, Chennai, Vijayawada and Visakhapatnam.
  * Mostly Telugu, Tamil and Kannada families, plus Khatri/Punjabi families
    (ForKhatri is a Khatri community app), each with a full biodata the
    family lens reads (education, work, employer, college, income band,
    height, mother tongue, community, native place, family, horoscope) and
    two to four answers in the product's own prompt model
    (`in_my_words.prompt_N = {q, a}`), which is what the candidate lens reads.
    Every option value is one `mangaly-web/lib/profileCategoryConfig.ts`
    knows, every prompt key is one in `lib/profileSections.ts`, and every
    interest tag is one in `lib/profileFormat.ts`, so nothing renders as a raw
    translation key.
  * About half chose to show their first name and all their photos openly
    (migration 043, category `openly`), and published one prompt answer
    (migration 039, `public: true`), so Discover's openly-shared tiles have
    real examples next to closed ones.
  * Nine passed the live face match. That is written through
    `mangaly_trust.record_face_match()` (migration 045), the same function the
    product calls after the browser check, in each person's own context, so
    the consent row and the two-year freshness come out exactly as they would
    for a real member. No other verification is invented.
  * Photos: one head-and-shoulders portrait (primary, the photo Discover may
    show before any connection) and one to three lifestyle pictures each
    (places, food, temples, books; no other people's faces).

Images: all from Unsplash (https://unsplash.com), under the Unsplash License
(https://unsplash.com/license): free to use, including commercially, no
permission or attribution required; it does not allow selling unaltered
copies or compiling them into a competing service, neither of which this
does. Only development data uses them. The portraits are real people, so they
never leave the development database. Portraits are cropped around the face by
Unsplash's own image service (`fit=facearea`). The files are kept in
`scripts/assets/more-matches/` and the script downloads any that are missing.

Idempotent: accounts are keyed by phone number; a second run skips everyone
already present and writes nothing for them.

Phone numbers use the same reserved 8-digit dummy block as
`seed_dev_families.py` (+91 then 8 digits, never a real Indian mobile), in the
set `+9112000NNN` so they never collide with the family sets `+91100S000M`.

This writes profiles directly as `mangaly_owner` (the admin-seeding exception
`seed_dev_accounts.py` documents).

Run, in order:
    python -m scripts.seed_dev_more_matches            (add --fetch-only to download images only)
    python -m scripts.reindex_discovery
    (platform) set MANGALY_SOURCE_DSN=postgresql://mangaly_owner:mangaly_owner_dev_password@localhost:5433/mangaly
    (platform) .venv\\Scripts\\python scripts\\import_module_identities.py
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from uuid import UUID, uuid4

import asyncpg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.components.identity_bridge.credentials import CredentialHasher  # noqa: E402

DB_DSN = "postgresql://mangaly_owner:mangaly_owner_dev_password@localhost:5433/mangaly"
MEDIA_ROOT = Path(__file__).resolve().parents[1] / ".local-media"
ASSETS = Path(__file__).resolve().parent / "assets" / "more-matches"
DEV_PASSWORD = "MangalyDev123!"
FACE_MATCH_NOTICE_VERSION = "2026-09-22"  # app/components/trust/interface.py

CITY = {
    "hyd": "Hyderabad, Telangana",
    "blr": "Bengaluru, Karnataka",
    "chn": "Chennai, Tamil Nadu",
    "vja": "Vijayawada, Andhra Pradesh",
    "vsk": "Visakhapatnam, Andhra Pradesh",
}

# Lifestyle pictures: key -> Unsplash photo id. Places, food, temples, books.
LIFESTYLE: dict[str, str] = {
    "charminar": "1696941515998-d83f24967aca",
    "charminar-street": "1741545979534-02f59c742730",
    "mecca-masjid": "1657981630164-769503f3a9a8",
    "hussain-sagar-buddha": "1712422813106-dfb845a8a7ed",
    "hyd-towers": "1730315661998-dadff57d7f8c",
    "hyd-night": "1601619933635-023753974a65",
    "cable-bridge": "1588240892395-6d21ab49d9c8",
    "hill-fort": "1569596732936-4e06a8afee28",
    "lake-bridge-boat": "1707500923104-4548b53b4688",
    "dosa": "1668236543090-82eba5ee5976",
    "dosa-leaf": "1694849789325-914b71ab4075",
    "banana-leaf-meal": "1625398407796-82650a8c135f",
    "idli-stack": "1683533678059-63c6a0e9e3ef",
    "tiffin-tray": "1680359871322-aabe6b33eff5",
    "thali": "1742281257687-092746ad6021",
    "rotis": "1567337710282-00832b415979",
    "biryani": "1589302168068-964664d93dc0",
    "gopuram": "1692173248120-59547c3d4653",
    "gopuram-colour": "1708346561250-ea0f8b54bc1c",
    "stone-arch": "1665003815164-8f5bc853ef44",
    "temple-carvings": "1665003725647-3ae0f01140b1",
    "temple-tank": "1674981324574-a0ebb0bef50d",
    "temple-stone": "1665003786611-7343c682a98d",
    "temple-sky": "1759134334610-488eb3937c82",
    "backwaters-palms": "1677475455506-1e429162f44f",
    "vembanad": "1661174607003-d9d36388c916",
    "houseboat": "1755547944443-3bb7114e2b1f",
    "lake-house": "1593417033942-bcdf26b74700",
    "book-cappuccino": "1544716278-ca5e3f4abd8c",
    "book-glasses": "1544716278-e513176f20b5",
    "book-tea": "1474366521946-c3d4b507abf2",
    "latte-window": "1543233604-3baca4d35513",
    "mug-book": "1630262344136-309cf5d39c02",
    "cafe-latte": "1558210834-473f430c09ac",
    "hampi-ruins": "1616606484004-5ef3cc46e39d",
    "hampi-field": "1722934804353-0d9f6a55ab5e",
    "hampi-temple": "1620766182966-c6eb5ed2b788",
    "hampi-hills": "1561981969-65ee8dfc7351",
    "hampi-arch": "1689947674042-13f46d7f2bbf",
    "ghats-clouds": "1622725859789-8e9ccf920693",
    "ghats-valley": "1660294534711-75a9474fecb0",
    "ghats-field": "1706408660346-18d868dced23",
    "ghats-sunset": "1707111762867-a88c90b7d9fa",
    "ghat-road": "1702799464711-544e9663a781",
    "waterfall": "1609775015123-e7573e73a7a7",
    "vizag-coast": "1609854534028-b512f5246abc",
    "vizag-rocks": "1605487564762-5e477c7d2bea",
    "vizag-hill-view": "1710237893364-ff94968aa034",
    "vizag-beach-town": "1655979521437-ae1875109d79",
    "diyas": "1577083753695-e010191bacb5",
    "diya-circle": "1635192592106-77a5aacbe1a3",
    "diya": "1605292356183-a77d0a9c9d1d",
}


def P(q: str, a: str, public: bool = False) -> dict:
    """One prompt answer. `public` publishes that one sentence (migration 039)."""
    value = {"q": q, "a": a}
    if public:
        value["public"] = True
    return value


def person(
    *,
    slug: str,
    phone: str,
    name: str,
    gender: str,
    dob: date,
    city: str,
    portrait: str,
    lifestyle: list[str],
    about: str,
    education: str,
    occupation: str,
    employer: str,
    college: str,
    income: str,
    height: int,
    tongue: str,
    diet: str,
    relocation: str,
    native: str,
    hobbies: list[str],
    family: dict,
    horoscope: dict,
    wants_children: str,
    involvement: str,
    age_range: tuple[int, int],
    prompts: list[dict],
    marital: str = "never_married",
    community: dict | None = None,
    pref_locality: str | None = "Hyderabad",
    openly: tuple[str, ...] = (),
    face_match: bool = False,
) -> dict:
    partner = {
        "looking_for": "groom" if gender == "female" else "bride",
        "age_range": {"min": age_range[0], "max": age_range[1]},
    }
    if pref_locality:
        partner["locality"] = pref_locality
    attrs: dict[str, dict] = {
        "basics": {"about": about, "height_cm": height, "mother_tongue": tongue, "have_children": "no"},
        "education": {"highest_education_level": education},
        "profession": {"occupation": occupation},
        "education_career": {"income_band": income, "employer": employer, "college": college},
        "marital_history": {"marital_status": marital},
        "relocation": {"relocation_willingness": relocation},
        "lifestyle": {"diet": diet},
        "food_travel_hobbies": {"hobbies": hobbies},
        "community": {"native_place": native, **(community or {})},
        "family": family,
        "family_involvement_expectations": {"level": involvement},
        "career_children_living_financial": {"wants_children": wants_children},
        "horoscope": horoscope,
        "partner_preference": partner,
        "in_my_words": {f"prompt_{i + 1}": p for i, p in enumerate(prompts[:3])},
    }
    if openly:
        attrs["openly"] = {key: True for key in openly}
    return {
        "slug": slug,
        "phone": phone,
        "name": name,
        "gender": gender,
        "dob": dob,
        "city": CITY[city],
        "portrait": portrait,
        "lifestyle": lifestyle,
        "attrs": attrs,
        "face_match": face_match,
    }


PEOPLE: list[dict] = [
    # ------------------------------------------------------------------ brides
    person(
        slug="sravya-reddy", phone="+9112000101", name="Sravya Reddy", gender="female",
        dob=date(1999, 3, 8), city="hyd", portrait="1614940685083-c5409b57da6e",
        lifestyle=["charminar-street", "latte-window"],
        about="Sravya is a UX designer at Microsoft in Gachibowli. Her family is from Nellore and has lived "
        "in Hyderabad for twenty years; her father is a retired bank manager and her brother works in Pune.",
        education="bachelors", occupation="UX Designer", employer="Microsoft", college="NIFT Hyderabad",
        income="20_40", height=163, tongue="telugu", diet="non_vegetarian", relocation="open_to_discussion",
        native="Nellore, Andhra Pradesh", hobbies=["art", "street_food", "road_trips"],
        family={"family_type": "nuclear", "family_values": "moderate", "father_occupation": "Retired bank manager",
                "mother_occupation": "Homemaker", "brothers": 1, "sisters": 0, "lives_with_parents": "yes"},
        horoscope={"matching_required": "open", "manglik": "no"},
        wants_children="yes", involvement="close_knit", age_range=(27, 34),
        prompts=[
            P("ideal_weekend", "Saturday is Lamakaan for whatever play is on, Irani chai at Nimrah after. "
              "Sunday I do nothing and defend that fiercely.", public=True),
            P("on_children", "Yes, two. And I want my amma close by for it; she has already bought tiny silver "
              "anklets 'just in case'."),
            P("when_we_disagree", "I need twenty minutes and a walk. After that I will talk it all the way "
              "through. I don't go silent for days."),
        ],
        openly=("first_name", "photos"), face_match=True,
    ),
    person(
        slug="harini-venkatesh", phone="+9112000102", name="Harini Venkatesh", gender="female",
        dob=date(1997, 11, 19), city="hyd", portrait="1749700332031-cf99864959ea",
        lifestyle=["book-cappuccino", "temple-tank"],
        about="Harini is a paediatrician at a children's hospital in Banjara Hills. Her father teaches at "
        "Osmania University and her mother is a school principal; her younger sister is studying law.",
        education="masters", occupation="Paediatrician", employer="Rainbow Children's Hospital",
        college="Osmania Medical College", income="10_20", height=158, tongue="tamil", diet="vegetarian",
        relocation="no", native="Madurai, Tamil Nadu", hobbies=["reading", "music", "volunteering"],
        family={"family_type": "nuclear", "family_values": "moderate", "father_occupation": "Professor, Osmania University",
                "mother_occupation": "School principal", "brothers": 0, "sisters": 1, "lives_with_parents": "yes"},
        horoscope={"matching_required": "yes", "manglik": "no", "rashi": "kark", "nakshatra": "Pushya"},
        wants_children="yes", involvement="close_knit", age_range=(28, 35),
        prompts=[
            P("my_work_means", "Night shifts at a children's hospital. Some weeks I will be tired and smell of "
              "hand sanitiser. I'd like someone who finds that more interesting than inconvenient."),
            P("simple_pleasures", "Filter coffee in a steel tumbler, M.S. Subbulakshmi on the speaker, and a "
              "Sunday with no calls from the ward."),
            P("caring_for_parents", "I'm the daughter who lives in the same city, so I'm the one who takes Appa "
              "for his check-ups. I'd like that to be normal in our house."),
        ],
        face_match=True,
    ),
    person(
        slug="nandini-rao", phone="+9112000103", name="Nandini Rao", gender="female",
        dob=date(1998, 6, 2), city="hyd", portrait="1759840278381-bf7d5e332050",
        lifestyle=["temple-stone", "diyas"],
        about="Nandini is a chartered accountant with KPMG. She grew up in a joint family in Warangal; her "
        "father runs a textile shop in Koti and her elder brother is a doctor in Karimnagar.",
        education="bachelors", occupation="Chartered Accountant", employer="KPMG", college="Villa Marie College",
        income="10_20", height=160, tongue="telugu", diet="non_vegetarian", relocation="open_to_discussion",
        native="Warangal, Telangana", hobbies=["cooking", "pilgrimages", "movies"],
        family={"family_type": "joint", "family_values": "traditional", "father_occupation": "Textile business, Koti",
                "mother_occupation": "Homemaker", "brothers": 1, "sisters": 0, "lives_with_parents": "yes"},
        horoscope={"matching_required": "yes", "manglik": "no", "rashi": "tula", "nakshatra": "Swati"},
        wants_children="yes", involvement="close_knit", age_range=(28, 34),
        prompts=[
            P("festivals_and_visits", "Bathukamma at my grandmother's in Warangal is not optional. I'll happily "
              "do Sankranti at your side if we keep that one.", public=True),
            P("about_money", "I'm a CA, so yes, there will be a spreadsheet. There will also be one unplanned "
              "trip to Srisailam every year."),
            P("joint_or_nuclear", "I grew up in a joint family of eleven and loved it. I'm open to either, as "
              "long as nobody expects me to stop working."),
        ],
        openly=("first_name", "photos"),
    ),
    person(
        slug="keerthana-iyer", phone="+9112000104", name="Keerthana Iyer", gender="female",
        dob=date(1996, 1, 25), city="chn", portrait="1514836894203-facaaeba1140",
        lifestyle=["book-glasses", "temple-sky"],
        about="Keerthana is a journalist covering urban affairs for a Chennai daily. She is an only child; "
        "her father is a retired railway officer and her mother teaches veena.",
        education="masters", occupation="Journalist", employer="The Hindu", college="Asian College of Journalism",
        income="5_10", height=165, tongue="tamil", diet="vegetarian", relocation="yes",
        native="Thanjavur, Tamil Nadu", hobbies=["reading", "photography", "beaches"],
        family={"family_type": "nuclear", "family_values": "liberal", "father_occupation": "Retired railway officer",
                "mother_occupation": "Veena teacher", "brothers": 0, "sisters": 0, "lives_with_parents": "yes"},
        horoscope={"matching_required": "no"},
        wants_children="undecided", involvement="independent", age_range=(29, 36),
        prompts=[
            P("my_work_means", "I report on cities: water, buses, the lakes nobody protects. Odd hours, and a "
              "lot of opinions about flyovers."),
            P("which_city", "I'm in Chennai now and ready to move to Hyderabad. I only ask for a balcony and a "
              "good library nearby."),
            P("quietly_proud", "I learned to swim at twenty-nine, in a class full of ten-year-olds. Best "
              "decision of my adult life."),
        ],
    ),
    person(
        slug="pooja-kapoor", phone="+9112000105", name="Pooja Kapoor", gender="female",
        dob=date(1998, 9, 14), city="hyd", portrait="1607189200597-4d0923ef98c6",
        lifestyle=["rotis", "hill-fort"],
        about="Pooja is a brand manager with ITC Foods and an MBA from ISB. Her grandfather moved from "
        "Jalandhar to Secunderabad in 1971; her father runs an auto-parts business and her mother a boutique.",
        education="masters", occupation="Brand Manager", employer="ITC Foods", college="ISB Hyderabad",
        income="20_40", height=166, tongue="punjabi", diet="eggetarian", relocation="open_to_discussion",
        native="Jalandhar, Punjab", hobbies=["fitness", "road_trips", "cooking"],
        community={"sub_community": "khatri", "gotra": "Kashyap"},
        family={"family_type": "nuclear", "family_values": "moderate",
                "father_occupation": "Auto-parts business, Secunderabad", "mother_occupation": "Boutique owner",
                "brothers": 1, "sisters": 0, "lives_with_parents": "yes"},
        horoscope={"matching_required": "open", "manglik": "no"},
        wants_children="yes", involvement="moderate", age_range=(28, 34),
        prompts=[
            P("my_family_in_words", "Punjabi by blood, Hyderabadi by every other measure. My dadaji came to "
              "Secunderabad in 1971 and we've argued about the best haleem ever since.", public=True),
            P("ideal_weekend", "An early run at KBR Park, the aloo parathas my mother makes only on Sundays, "
              "and a long drive out to Shamirpet in the evening."),
            P("daily_chores", "I cook, you clean, and we both pretend the laundry does itself until one of us "
              "breaks. Open to negotiation."),
        ],
        openly=("first_name", "photos"), face_match=True,
    ),
    person(
        slug="aishwarya-hegde", phone="+9112000106", name="Aishwarya Hegde", gender="female",
        dob=date(1995, 12, 3), city="blr", portrait="1706943262459-3ef6ce03305c",
        lifestyle=["ghats-clouds", "dosa-leaf", "ghats-sunset"],
        about="Aishwarya is a product manager at Flipkart in Bengaluru and is open to moving to Hyderabad. "
        "Her father is a doctor in Udupi and her younger sister is an architect.",
        education="masters", occupation="Product Manager", employer="Flipkart", college="IIM Bangalore",
        income="40_plus", height=162, tongue="kannada", diet="vegetarian", relocation="yes",
        native="Udupi, Karnataka", hobbies=["trekking", "music", "board_games"],
        family={"family_type": "nuclear", "family_values": "liberal", "father_occupation": "Doctor",
                "mother_occupation": "Retired school teacher", "brothers": 0, "sisters": 1, "lives_with_parents": "no"},
        horoscope={"matching_required": "open"},
        wants_children="yes", involvement="moderate", age_range=(29, 35),
        prompts=[
            P("ideal_weekend", "Nandi Hills at 5 am before the crowds, benne dosa at CTR after. I'll drive, you "
              "choose the music."),
            P("moving_abroad", "I've been offered London twice and said no twice. I want to build a life here, "
              "near both our families."),
            P("feel_supported", "When someone remembers the small thing, that I had a big review on Tuesday, "
              "and asks how it went."),
        ],
    ),
    person(
        slug="tejaswini-naidu", phone="+9112000107", name="Tejaswini Naidu", gender="female",
        dob=date(2001, 4, 18), city="vsk", portrait="1617297873650-aef8f4e00b9b",
        lifestyle=["vizag-coast", "vizag-rocks"],
        about="Tejaswini is a marine biologist with the National Institute of Oceanography in Visakhapatnam. "
        "Her father is a merchant navy captain; she has two elder brothers.",
        education="masters", occupation="Marine Biologist", employer="CSIR-NIO", college="Andhra University",
        income="5_10", height=157, tongue="telugu", diet="non_vegetarian", relocation="open_to_discussion",
        native="Visakhapatnam, Andhra Pradesh", hobbies=["beaches", "photography", "gardening"],
        family={"family_type": "joint", "family_values": "moderate", "father_occupation": "Captain, merchant navy",
                "mother_occupation": "Homemaker", "brothers": 2, "sisters": 0, "lives_with_parents": "yes"},
        horoscope={"matching_required": "yes", "rashi": "meen"},
        wants_children="yes", involvement="close_knit", age_range=(26, 32), pref_locality=None,
        prompts=[
            P("simple_pleasures", "RK Beach at sunrise with a flask of tea, and fried fish from the stalls by "
              "the fishing harbour.", public=True),
            P("my_work_means", "I count sea turtle nests along the coast. It is less romantic than it sounds "
              "and involves a lot more sand."),
            P("parents_nearby", "Vizag is home. I'd move for the right person, but my parents should be a short "
              "flight away, not a long one."),
        ],
        openly=("first_name", "photos"),
    ),
    person(
        slug="shruti-malhotra", phone="+9112000108", name="Shruti Malhotra", gender="female",
        dob=date(1999, 7, 7), city="hyd", portrait="1558377235-76f53857000b",
        lifestyle=["biryani", "hyd-night"],
        about="Shruti is a software engineer at Google in Hyderabad, an IIIT Hyderabad graduate. Her father is "
        "a chartered accountant and her mother lectures in Hindi; her elder sister lives in Delhi.",
        education="bachelors", occupation="Software Engineer", employer="Google", college="IIIT Hyderabad",
        income="40_plus", height=164, tongue="hindi", diet="non_vegetarian", relocation="no",
        native="Amritsar, Punjab", hobbies=["badminton", "movies", "street_food"],
        community={"sub_community": "khatri", "gotra": "Vashisht"},
        family={"family_type": "nuclear", "family_values": "liberal", "father_occupation": "Chartered accountant",
                "mother_occupation": "Hindi lecturer", "brothers": 0, "sisters": 1, "lives_with_parents": "yes"},
        horoscope={"matching_required": "no"},
        wants_children="undecided", involvement="moderate", age_range=(27, 33),
        prompts=[
            P("perpetual_argument", "Whether Paradise biryani is overrated. It is. I'm prepared to lose this "
              "argument for the next fifty years."),
            P("work_after_marriage", "I'm staying in tech. If we have children I'd want us both to slow down "
              "for a while, not just me."),
            P("i_wind_down_by", "Badminton at Gachibowli three evenings a week. I'm competitive, fair warning."),
        ],
    ),
    person(
        slug="lakshmi-subramanian", phone="+9112000109", name="Lakshmi Subramanian", gender="female",
        dob=date(1997, 2, 11), city="hyd", portrait="1646979200020-941e1deb2670",
        lifestyle=["gopuram-colour", "diya-circle", "banana-leaf-meal"],
        about="Lakshmi is an HR business partner at Deloitte and a trained Bharatanatyam dancer who teaches on "
        "Sundays. Her father is an engineer with BHEL and her mother is a Carnatic vocalist.",
        education="masters", occupation="HR Business Partner", employer="Deloitte", college="Symbiosis Pune",
        income="10_20", height=159, tongue="tamil", diet="vegetarian", relocation="open_to_discussion",
        native="Coimbatore, Tamil Nadu", hobbies=["classical_dance", "music", "spirituality"],
        family={"family_type": "nuclear", "family_values": "traditional", "father_occupation": "Engineer, BHEL",
                "mother_occupation": "Carnatic vocalist", "brothers": 1, "sisters": 0, "lives_with_parents": "yes"},
        horoscope={"matching_required": "yes", "manglik": "no", "rashi": "simha", "nakshatra": "Magha"},
        wants_children="yes", involvement="close_knit", age_range=(29, 35),
        prompts=[
            P("faith_looks_like", "A lamp lit every evening and Margazhi mornings at the temple. Quiet and "
              "regular, never something I'd push on anyone.", public=True),
            P("quietly_proud", "My arangetram at fourteen. I still dance every Sunday and teach six girls in "
              "our colony."),
            P("in_laws_role", "I'd like your parents to feel they gained a daughter. That also means they'll "
              "get my honest opinion."),
        ],
        openly=("first_name", "photos"),
    ),
    person(
        slug="ritika-sethi", phone="+9112000110", name="Ritika Sethi", gender="female",
        dob=date(2000, 10, 22), city="hyd", portrait="1618559850638-2aed8a8e8cdc",
        lifestyle=["hampi-arch", "mug-book", "charminar"],
        about="Ritika runs her own interior design studio in Jubilee Hills. Her father has a furniture "
        "business in Begumpet; her younger sister is finishing college.",
        education="bachelors", occupation="Interior Designer", employer="Self-employed (own studio)",
        college="JNAFAU Hyderabad", income="10_20", height=161, tongue="punjabi", diet="eggetarian",
        relocation="no", native="Ludhiana, Punjab", hobbies=["art", "photography", "road_trips"],
        community={"sub_community": "arora", "gotra": "Gautam"},
        family={"family_type": "nuclear", "family_values": "moderate", "father_occupation": "Furniture business, Begumpet",
                "mother_occupation": "Homemaker", "brothers": 0, "sisters": 1, "lives_with_parents": "yes"},
        horoscope={"matching_required": "open"},
        wants_children="yes", involvement="moderate", age_range=(26, 32),
        prompts=[
            P("our_first_home", "Lots of plants, one wall of books and a proper kitchen. I will fight you on "
              "the sofa colour and I will win.", public=True),
            P("ideal_weekend", "Antique hunting at Chor Bazaar, dosa at Govind's, and a nap I will deny taking."),
            P("small_spending", "I spend too much on cushions and hand-block prints. I've made my peace with "
              "it; you may need to as well."),
        ],
        openly=("first_name", "photos"), face_match=True,
    ),
    person(
        slug="meghana-chowdary", phone="+9112000111", name="Meghana Chowdary", gender="female",
        dob=date(1998, 1, 30), city="vja", portrait="1610189012906-4c0aa9b9781e",
        lifestyle=["temple-carvings", "cafe-latte"],
        about="Meghana is an assistant professor of English in Vijayawada and is willing to move to Hyderabad. "
        "Her father farms and runs a rice mill in Krishna district; her brother is an engineer in Hyderabad.",
        education="masters", occupation="Assistant Professor", employer="Andhra Loyola College",
        college="University of Hyderabad", income="5_10", height=160, tongue="telugu", diet="non_vegetarian",
        relocation="yes", native="Vijayawada, Andhra Pradesh", hobbies=["reading", "cooking", "pilgrimages"],
        family={"family_type": "joint", "family_values": "traditional",
                "father_occupation": "Agriculture and rice mill", "mother_occupation": "Homemaker",
                "brothers": 1, "sisters": 0, "lives_with_parents": "yes"},
        horoscope={"matching_required": "yes", "manglik": "no", "rashi": "vrishabh", "nakshatra": "Rohini"},
        wants_children="yes", involvement="close_knit", age_range=(28, 34),
        prompts=[
            P("festivals_and_visits", "Dasara at the Kanaka Durga temple with the whole family. I'd love to "
              "bring you to at least one."),
            P("running_the_home", "I grew up where Amma ran everything and Nanna never noticed. I want a home "
              "where we both notice."),
            P("life_goal", "To write one good novel in Telugu before I'm forty. I have three chapters and a lot "
              "of confidence."),
        ],
    ),
    person(
        slug="anusha-goud", phone="+9112000112", name="Anusha Goud", gender="female",
        dob=date(2002, 5, 15), city="hyd", portrait="1708182564325-fb1d3a3864d3",
        lifestyle=["tiffin-tray"],
        about="Anusha is a research associate in formulation development at Dr. Reddy's Laboratories. Her "
        "father is a government school headmaster in Karimnagar; she has two younger sisters.",
        education="masters", occupation="Research Associate (Pharma)", employer="Dr. Reddy's Laboratories",
        college="JNTU Hyderabad", income="5_10", height=155, tongue="telugu", diet="non_vegetarian",
        relocation="open_to_discussion", native="Karimnagar, Telangana", hobbies=["cooking", "movies", "yoga"],
        family={"family_type": "joint", "family_values": "moderate",
                "father_occupation": "Government school headmaster", "mother_occupation": "Anganwadi supervisor",
                "brothers": 0, "sisters": 2, "lives_with_parents": "no"},
        horoscope={"matching_required": "yes"},
        wants_children="yes", involvement="close_knit", age_range=(25, 31),
        prompts=[
            P("at_my_table", "Bagara rice, mutton curry and Amma's gongura pachadi. If you don't like gongura "
              "we need to talk.", public=True),
            P("working_towards", "A PhD, eventually. I work on drug formulations now and one day I want to run "
              "my own lab."),
        ],
        openly=("first_name",),
    ),
    person(
        slug="simran-chopra", phone="+9112000113", name="Simran Chopra", gender="female",
        dob=date(1996, 8, 27), city="hyd", portrait="1572470176170-98fa8abcb741",
        lifestyle=["hussain-sagar-buddha", "waterfall"],
        about="Simran is a dentist with her own clinic in Kondapur. Her father is a retired Army colonel who "
        "settled in Secunderabad; her brother is in the Army. She was married briefly; it ended by mutual consent.",
        education="masters", occupation="Dentist", employer="Own clinic, Kondapur", college="Army College of Dental Sciences",
        income="20_40", height=163, tongue="hindi", diet="vegetarian", relocation="no",
        native="Delhi", hobbies=["yoga", "reading", "volunteering"], marital="divorced",
        community={"sub_community": "khatri", "gotra": "Atri"},
        family={"family_type": "nuclear", "family_values": "liberal", "father_occupation": "Retired Army colonel",
                "mother_occupation": "School counsellor", "brothers": 1, "sisters": 0, "lives_with_parents": "yes"},
        horoscope={"matching_required": "no"},
        wants_children="yes", involvement="independent", age_range=(30, 38),
        prompts=[
            P("non_negotiable", "Honesty early. I was married before, briefly, and it ended kindly. I'd rather "
              "you hear that from me in the first line than from anyone else."),
            P("how_i_say_sorry", "Out loud and quickly, usually with chai. I don't let things sit overnight."),
            P("simple_pleasures", "Monsoon evenings at Durgam Cheruvu, a good paperback, and the first mirchi "
              "bajji of the season."),
        ],
        face_match=True,
    ),
    person(
        slug="pranavi-varma", phone="+9112000114", name="Pranavi Varma", gender="female",
        dob=date(2000, 12, 9), city="hyd", portrait="1771507213365-c6047b40e2e1",
        lifestyle=["mecca-masjid", "idli-stack", "stone-arch"],
        about="Pranavi is a product analyst at Amazon in Hyderabad. Her father is an SBI branch manager and her "
        "mother teaches Telugu; the family is from Rajahmundry.",
        education="bachelors", occupation="Product Analyst", employer="Amazon", college="JNTU Hyderabad",
        income="10_20", height=158, tongue="telugu", diet="vegetarian", relocation="open_to_discussion",
        native="Rajahmundry, Andhra Pradesh", hobbies=["music", "street_food", "photography"],
        family={"family_type": "nuclear", "family_values": "moderate", "father_occupation": "Bank manager, SBI",
                "mother_occupation": "Telugu teacher", "brothers": 1, "sisters": 0, "lives_with_parents": "yes"},
        horoscope={"matching_required": "open"},
        wants_children="yes", involvement="moderate", age_range=(26, 32),
        prompts=[
            P("ideal_weekend", "Tank Bund in the evening, pani puri at Gokul Chat, and a late show at Prasads.",
              public=True),
            P("home_should_feel", "Like my grandmother's house in Rajahmundry: the door always open, someone "
              "always making coffee."),
            P("when_i_am_upset", "I go very quiet and very tidy. If the kitchen is suddenly spotless, ask me "
              "what's wrong."),
        ],
        openly=("first_name", "photos"),
    ),
    # ------------------------------------------------------------------ grooms
    person(
        slug="siddharth-reddy", phone="+9112000201", name="Siddharth Reddy", gender="male",
        dob=date(1994, 5, 10), city="hyd", portrait="1649433658557-54cf58577c68",
        lifestyle=["dosa", "hampi-hills"],
        about="Siddharth is a cardiologist at Yashoda Hospitals. His parents live in Nalgonda, where his father "
        "farms and his mother was a government doctor; his sister is married and lives in Chicago.",
        education="doctorate", occupation="Cardiologist", employer="Yashoda Hospitals", college="Gandhi Medical College",
        income="40_plus", height=178, tongue="telugu", diet="non_vegetarian", relocation="no",
        native="Nalgonda, Telangana", hobbies=["cricket", "reading", "road_trips"],
        family={"family_type": "joint", "family_values": "moderate", "father_occupation": "Agriculturist",
                "mother_occupation": "Retired government doctor", "brothers": 0, "sisters": 1, "lives_with_parents": "no"},
        horoscope={"matching_required": "open", "manglik": "no"},
        wants_children="yes", involvement="close_knit", age_range=(25, 31),
        prompts=[
            P("my_work_means", "I'm a cardiologist, so I'll sometimes leave dinner halfway. I'll always come "
              "back and finish the conversation.", public=True),
            P("parents_nearby", "My parents are in Nalgonda, ninety minutes away. We go most second Sundays and "
              "I'd love for you to come."),
            P("ideal_weekend", "Sunday cricket, then breakfast at Chutneys with far too many chutneys."),
        ],
        openly=("first_name", "photos"), face_match=True,
    ),
    person(
        slug="aravind-krishnan", phone="+9112000202", name="Aravind Krishnan", gender="male",
        dob=date(1996, 2, 14), city="hyd", portrait="1757744705465-ea08b0ddc38a",
        lifestyle=["thali", "gopuram"],
        about="Aravind is a senior software engineer at Microsoft. His father is a retired ISRO scientist and "
        "his mother teaches mathematics; his younger brother is studying in Chennai.",
        education="masters", occupation="Senior Software Engineer", employer="Microsoft", college="IIIT Hyderabad",
        income="40_plus", height=175, tongue="tamil", diet="vegetarian", relocation="open_to_discussion",
        native="Tiruchirappalli, Tamil Nadu", hobbies=["music", "cooking", "board_games"],
        family={"family_type": "nuclear", "family_values": "liberal", "father_occupation": "Retired ISRO scientist",
                "mother_occupation": "Mathematics teacher", "brothers": 1, "sisters": 0, "lives_with_parents": "yes"},
        horoscope={"matching_required": "no"},
        wants_children="yes", involvement="moderate", age_range=(25, 31),
        prompts=[
            P("on_housework", "I cook South Indian breakfasts properly: pongal, adai, the works. I'm less good "
              "at folding clothes. Teach me."),
            P("when_we_disagree", "Say it plainly, then let's go for a walk. Nothing was ever solved by two "
              "people staring at each other in a room."),
            P("quietly_proud", "I taught my mother to use UPI and now she sends me payment requests for the "
              "vegetables."),
        ],
        face_match=True,
    ),
    person(
        slug="kunal-bhasin", phone="+9112000203", name="Kunal Bhasin", gender="male",
        dob=date(1995, 9, 1), city="hyd", portrait="1581382575275-97901c2635b7",
        lifestyle=["ghat-road", "hampi-field"],
        about="Kunal is an associate director with JP Morgan in Hyderabad. He grew up across seven Air Force "
        "stations; his father is a retired Air Force officer and his sister is a lawyer in Gurugram.",
        education="masters", occupation="Associate Director, Finance", employer="JP Morgan", college="XLRI Jamshedpur",
        income="40_plus", height=181, tongue="punjabi", diet="non_vegetarian", relocation="no",
        native="Patiala, Punjab", hobbies=["fitness", "road_trips", "movies"],
        community={"sub_community": "khatri", "gotra": "Bhardwaj"},
        family={"family_type": "nuclear", "family_values": "moderate", "father_occupation": "Retired Air Force officer",
                "mother_occupation": "Homemaker", "brothers": 0, "sisters": 1, "lives_with_parents": "yes"},
        horoscope={"matching_required": "open"},
        wants_children="yes", involvement="moderate", age_range=(26, 31),
        prompts=[
            P("my_family_in_words", "Air Force family: seven schools in twelve years. Hyderabad is the first "
              "city I chose myself, and I plan to stay.", public=True),
            P("saving_or_spending", "A saver by habit, but I'll spend without blinking on a good trip. Ladakh "
              "on a motorbike is still on the list."),
            P("daily_routine_say", "Gym at six, office by nine, home by seven most days. I'd like our evenings "
              "to be ours."),
        ],
        openly=("first_name", "photos"),
    ),
    person(
        slug="ishaan-dhawan", phone="+9112000204", name="Ishaan Dhawan", gender="male",
        dob=date(1993, 12, 12), city="blr", portrait="1729157661483-ed21901ed892",
        lifestyle=["ghats-field", "ghats-valley", "hampi-temple"],
        about="Ishaan founded a climate-technology company in Bengaluru that builds solar cold storage for "
        "farmers, and is open to moving to Hyderabad. His father teaches economics; his mother is an architect.",
        education="bachelors", occupation="Founder, climate-tech company", employer="Self-employed (own company)",
        college="IIT Bombay", income="20_40", height=177, tongue="hindi", diet="vegetarian", relocation="yes",
        native="Chandigarh", hobbies=["trekking", "reading", "volunteering"],
        community={"sub_community": "khatri", "gotra": "Kashyap"},
        family={"family_type": "nuclear", "family_values": "liberal", "father_occupation": "Professor of economics",
                "mother_occupation": "Architect", "brothers": 0, "sisters": 0, "lives_with_parents": "no"},
        horoscope={"matching_required": "no"},
        wants_children="undecided", involvement="independent", age_range=(26, 32),
        prompts=[
            P("working_towards", "Solar cold storage for small farmers. Four years in, twelve people, one very "
              "patient investor."),
            P("supporting_your_work", "Whatever you're building, I want to hear about it at dinner. I'll be "
              "your most annoying cheerleader."),
            P("which_city", "I'm in Bengaluru, but Hyderabad's rents and its biryani have both made strong cases."),
        ],
    ),
    person(
        slug="aditya-suri", phone="+9112000205", name="Aditya Suri", gender="male",
        dob=date(1997, 3, 30), city="hyd", portrait="1552642986-ccb41e7059e7",
        lifestyle=["hyd-towers", "hampi-ruins"],
        about="Aditya is a product designer at Swiggy and a keen street photographer. His father runs a "
        "Punjabi restaurant in Secunderabad; his elder brother manages it with him.",
        education="bachelors", occupation="Product Designer", employer="Swiggy", college="NID Ahmedabad",
        income="20_40", height=180, tongue="punjabi", diet="non_vegetarian", relocation="open_to_discussion",
        native="Amritsar, Punjab", hobbies=["photography", "street_food", "music"],
        community={"sub_community": "khatri", "gotra": "Vashisht"},
        family={"family_type": "joint", "family_values": "moderate", "father_occupation": "Restaurant owner, Secunderabad",
                "mother_occupation": "Homemaker", "brothers": 1, "sisters": 0, "lives_with_parents": "yes"},
        horoscope={"matching_required": "open"},
        wants_children="yes", involvement="close_knit", age_range=(24, 30),
        prompts=[
            P("at_my_table", "My dad runs a Punjabi restaurant in Secunderabad, so there is always too much "
              "butter. I also make a very respectable pesarattu.", public=True),
            P("simple_pleasures", "The old city at dawn with my camera, then Nimrah chai and Osmania biscuits "
              "before the crowds arrive."),
            P("if_families_disagree", "We decide together first, then talk to both families together. Never one "
              "of us alone in the middle."),
        ],
        openly=("first_name", "photos"), face_match=True,
    ),
    person(
        slug="sai-charan-yadav", phone="+9112000206", name="Sai Charan Yadav", gender="male",
        dob=date(1999, 7, 19), city="hyd", portrait="1589386417686-0d34b5903d23",
        lifestyle=["cable-bridge", "lake-bridge-boat"],
        about="Sai Charan is an assistant executive engineer with the Greater Hyderabad Municipal Corporation. "
        "He lives with his parents, elder brother and sister-in-law; the family is from Siddipet.",
        education="bachelors", occupation="Assistant Executive Engineer", employer="GHMC", college="JNTU Hyderabad",
        income="10_20", height=174, tongue="telugu", diet="non_vegetarian", relocation="no",
        native="Siddipet, Telangana", hobbies=["cricket", "pilgrimages", "movies"],
        family={"family_type": "joint", "family_values": "traditional", "father_occupation": "Agriculturist",
                "mother_occupation": "Homemaker", "brothers": 1, "sisters": 1, "lives_with_parents": "yes"},
        horoscope={"matching_required": "yes", "manglik": "no", "rashi": "makar", "nakshatra": "Shravana"},
        wants_children="yes", involvement="close_knit", age_range=(23, 28),
        prompts=[
            P("joint_or_nuclear", "Joint family, and happy in it. My mother wants a daughter-in-law she can "
              "gossip with, not one who serves her."),
            P("festivals_and_visits", "Bonalu in Siddipet every Ashadam: the whole village, the drums, and more "
              "food than you'll believe."),
            P("my_work_means", "I build roads and storm drains for GHMC. When Hyderabad floods my phone doesn't "
              "stop; please don't take it personally."),
        ],
    ),
    person(
        slug="harsha-vardhan", phone="+9112000207", name="Harsha Vardhan", gender="male",
        dob=date(1995, 10, 4), city="vja", portrait="1609770653328-a4d1dd377970",
        lifestyle=["backwaters-palms", "book-tea"],
        about="Harsha practises law at the Andhra Pradesh High Court with his father, a senior advocate. He is "
        "the only son; his sister is a doctor in Guntur.",
        education="masters", occupation="Advocate", employer="High Court of Andhra Pradesh", college="NALSAR Hyderabad",
        income="10_20", height=172, tongue="telugu", diet="non_vegetarian", relocation="open_to_discussion",
        native="Guntur, Andhra Pradesh", hobbies=["reading", "cricket", "spirituality"],
        family={"family_type": "joint", "family_values": "moderate", "father_occupation": "Senior advocate",
                "mother_occupation": "Retired lecturer", "brothers": 0, "sisters": 1, "lives_with_parents": "yes"},
        horoscope={"matching_required": "yes", "rashi": "kanya"},
        wants_children="yes", involvement="close_knit", age_range=(24, 30), pref_locality=None,
        prompts=[
            P("big_decisions", "Argued, written down, slept on, decided together. I'm a lawyer; I can't help the "
              "'written down' part.", public=True),
            P("at_my_table", "Guntur chillies in everything. I'm told this is a problem, so I'm willing to keep "
              "a milder pot."),
            P("caring_for_parents", "I'm the only son. My parents will live with us eventually, and I'd like us "
              "both to be at peace with that before we begin."),
        ],
        openly=("first_name", "photos"),
    ),
    person(
        slug="naveen-shetty", phone="+9112000208", name="Naveen Shetty", gender="male",
        dob=date(1998, 8, 8), city="blr", portrait="1712425718137-491250cfde88",
        lifestyle=["lake-house", "vembanad"],
        about="Naveen is a machine learning engineer with Walmart Global Tech in Bengaluru and plays guitar in "
        "a weekend band. His father runs a restaurant in Mangaluru and his mother is a nurse.",
        education="masters", occupation="Machine Learning Engineer", employer="Walmart Global Tech", college="IISc Bangalore",
        income="20_40", height=176, tongue="kannada", diet="non_vegetarian", relocation="yes",
        native="Mangaluru, Karnataka", hobbies=["music", "beaches", "fitness"],
        family={"family_type": "nuclear", "family_values": "liberal", "father_occupation": "Restaurant owner, Mangaluru",
                "mother_occupation": "Nurse", "brothers": 1, "sisters": 0, "lives_with_parents": "no"},
        horoscope={"matching_required": "no"},
        wants_children="yes", involvement="moderate", age_range=(24, 29), pref_locality=None,
        prompts=[
            P("simple_pleasures", "Ghee roast in Mangaluru, a guitar on the terrace, and rain on a tiled roof.",
              public=True),
            P("moving_abroad", "Not interested. My parents and the sea are both here, and I'm keeping both."),
            P("feel_supported", "When you tell me the truth about my music, even the bad songs. Especially the "
              "bad songs."),
        ],
        openly=("first_name", "photos"), face_match=True,
    ),
    person(
        slug="mohit-anand", phone="+9112000209", name="Mohit Anand", gender="male",
        dob=date(1992, 11, 23), city="hyd", portrait="1607346256330-dee7af15f7c5",
        lifestyle=["houseboat", "diya"],
        about="Mohit runs his family's jewellery business in Abids, which his great-grandfather started. Three "
        "generations live together in the family home; his two younger brothers work in the business.",
        education="bachelors", occupation="Jeweller (family business)", employer="Family business, Abids",
        college="Nizam College", income="40_plus", height=179, tongue="punjabi", diet="vegetarian", relocation="no",
        native="Hyderabad, Telangana", hobbies=["cooking", "pilgrimages", "cricket"],
        community={"sub_community": "khatri", "gotra": "Gautam"},
        family={"family_type": "joint", "family_values": "traditional", "father_occupation": "Jeweller",
                "mother_occupation": "Homemaker", "brothers": 2, "sisters": 0, "lives_with_parents": "yes"},
        horoscope={"matching_required": "yes", "manglik": "no", "rashi": "dhanu"},
        wants_children="yes", involvement="close_knit", age_range=(26, 32),
        prompts=[
            P("my_family_in_words", "Three generations in one house in Abids, all Punjabi, all speaking "
              "Hyderabadi Urdu at the dinner table."),
            P("work_after_marriage", "The business is mine to run, not yours to join unless you want to. Your "
              "career is yours."),
            P("faith_looks_like", "Gurudwara on Sundays with my grandmother, the Balkampet Yellamma temple with "
              "my mother. Both, always."),
        ],
    ),
    person(
        slug="vishnu-teja", phone="+9112000210", name="Vishnu Teja", gender="male",
        dob=date(1999, 1, 17), city="vsk", portrait="1625241152315-4a698f74ceb7",
        lifestyle=["vizag-hill-view", "vizag-beach-town"],
        about="Vishnu is a lieutenant in the Indian Navy with the Eastern Naval Command in Visakhapatnam. His "
        "father is a retired headmaster in Srikakulam; his sister is a software engineer in Hyderabad.",
        education="bachelors", occupation="Naval Officer (Lieutenant)", employer="Indian Navy",
        college="Indian Naval Academy, Ezhimala", income="10_20", height=177, tongue="telugu",
        diet="non_vegetarian", relocation="yes", native="Srikakulam, Andhra Pradesh",
        hobbies=["fitness", "beaches", "trekking"],
        family={"family_type": "nuclear", "family_values": "moderate", "father_occupation": "Retired headmaster",
                "mother_occupation": "Homemaker", "brothers": 0, "sisters": 1, "lives_with_parents": "no"},
        horoscope={"matching_required": "open"},
        wants_children="yes", involvement="moderate", age_range=(23, 28), pref_locality=None,
        prompts=[
            P("my_work_means", "Weeks at sea, sometimes without signal. When I'm home I'm entirely home: phone "
              "away, dinner cooked.", public=True),
            P("our_first_home", "Navy quarters for a while, so a new city every few years. I'll make each one "
              "feel like ours."),
        ],
        openly=("first_name", "photos"),
    ),
]


# --------------------------------------------------------------------- images
def portrait_url(photo_id: str) -> str:
    """Head-and-shoulders crop around the face, 4:5 like the Discover tile."""
    return f"https://images.unsplash.com/photo-{photo_id}?w=800&h=1000&fit=facearea&facepad=3&q=80"


def lifestyle_url(photo_id: str) -> str:
    return f"https://images.unsplash.com/photo-{photo_id}?w=900&h=1125&fit=crop&q=80"


def ensure_asset(path: Path, url: str) -> bytes | None:
    """The asset from `scripts/assets/more-matches/`, downloaded first if it is
    missing. curl with a hard deadline, for the reason `seed_dev_families.py`
    gives (urllib hung on Windows); a missing picture skips that picture, it
    never fails the run."""
    if path.exists() and path.stat().st_size > 0:
        return path.read_bytes()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        done = subprocess.run(  # noqa: S603 - fixed argv, no shell
            ["curl", "-sSL", "--max-time", "30", "--fail", "-o", str(path), url],
            capture_output=True,
            timeout=40,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"        (image unavailable: {url} - {exc})")
        return None
    if done.returncode != 0 or not path.exists() or path.stat().st_size == 0:
        print(f"        (image unavailable: {url} - curl exit {done.returncode})")
        path.unlink(missing_ok=True)
        return None
    return path.read_bytes()


def photos_for(spec: dict) -> list[bytes]:
    shots: list[bytes] = []
    portrait = ensure_asset(ASSETS / f"portrait-{spec['slug']}.jpg", portrait_url(spec["portrait"]))
    if portrait is None:
        return []  # no face, no gallery: a profile must never lead with a landscape
    shots.append(portrait)
    for key in spec["lifestyle"]:
        blob = ensure_asset(ASSETS / f"life-{key}.jpg", lifestyle_url(LIFESTYLE[key]))
        if blob:
            shots.append(blob)
    return shots


# ------------------------------------------------------------------------- db
async def seed_one(conn: asyncpg.Connection, spec: dict, credential_hash: str) -> bool:
    existing = await conn.fetchval(
        "SELECT id FROM mangaly_identity.account WHERE phone_identifier = $1", spec["phone"]
    )
    if existing:
        print(f"  SKIP  {spec['name']} - already seeded ({spec['phone']})")
        return False

    photos = photos_for(spec)
    if not photos:
        print(f"  MISS  {spec['name']} - portrait could not be fetched, not seeded")
        return False

    account_id, profile_id = uuid4(), uuid4()
    # One transaction per person: a failure never leaves half a profile behind.
    async with conn.transaction():
        await conn.execute(
            """
            INSERT INTO mangaly_identity.account
                (id, phone_identifier, credential_hash, status, identifier_verified_at, display_name)
            VALUES ($1, $2, $3, 'active', now(), $4)
            """,
            account_id, spec["phone"], credential_hash, spec["name"],
        )
        await conn.execute(
            """
            INSERT INTO mangaly_profile.profile
                (id, account_id, name, date_of_birth, gender, city_locality, status)
            VALUES ($1, $2, $3, $4, $5, $6, 'active')
            """,
            profile_id, account_id, spec["name"], spec["dob"], spec["gender"], spec["city"],
        )

        directory = MEDIA_ROOT / str(profile_id)
        directory.mkdir(parents=True, exist_ok=True)
        for order, blob in enumerate(photos):
            filename = f"{uuid4()}.jpg"
            (directory / filename).write_bytes(blob)
            await conn.execute(
                """
                INSERT INTO mangaly_profile.profile_media
                    (id, profile_id, media_type, storage_ref, is_primary, upload_status,
                     uploaded_at, sort_order)
                VALUES ($1, $2, 'photo', $3, $4, 'complete', now(), $5)
                """,
                uuid4(), profile_id, f"local://{profile_id}/{filename}", order == 0, order,
            )

        written = 0
        for category, fields in spec["attrs"].items():
            for key, value in fields.items():
                await conn.execute(
                    """
                    INSERT INTO mangaly_profile.profile_attribute
                        (id, profile_id, category, attribute_key, state, value)
                    VALUES ($1, $2, $3, $4, 'value', $5::jsonb)
                    """,
                    uuid4(), profile_id, category, key, json.dumps(value),
                )
                written += 1

        verified = ""
        if spec["face_match"]:
            await record_face_match(conn, account_id)
            verified = ", face match"

    openly = ", ".join(spec["attrs"].get("openly", {})) or "nothing"
    print(
        f"  OK    {spec['name']} ({spec['gender']}, {spec['city'].split(',')[0]}) - {spec['phone']}: "
        f"{len(photos)} photos, {written} attributes, open: {openly}{verified}"
    )
    return True


async def record_face_match(conn: asyncpg.Connection, account_id: UUID) -> None:
    """The product's own write path (migration 045), in the person's context:
    `record_face_match` refuses anyone but the person themselves."""
    await conn.execute("SELECT set_config('mangaly.account_id', $1, true)", str(account_id))
    await conn.execute("SELECT set_config('mangaly.authz_context', $1, true)", str(account_id))
    await conn.fetch(
        "SELECT * FROM mangaly_trust.record_face_match($1, true, $2)",
        account_id, FACE_MATCH_NOTICE_VERSION,
    )
    await conn.execute("SELECT set_config('mangaly.authz_context', '', true)")
    await conn.execute("SELECT set_config('mangaly.account_id', '', true)")


async def main(argv: list[str]) -> int:
    if "--fetch-only" in argv:
        for spec in PEOPLE:
            got = photos_for(spec)
            print(f"  {spec['name']}: {len(got)} image(s)")
        return 0

    credential_hash = CredentialHasher().hash(DEV_PASSWORD)
    conn = await asyncpg.connect(DB_DSN)
    created = 0
    try:
        for spec in PEOPLE:
            if await seed_one(conn, spec, credential_hash):
                created += 1
    finally:
        await conn.close()

    brides = sum(1 for p in PEOPLE if p["gender"] == "female")
    print(f"\n  {created} candidates created, {len(PEOPLE) - created} skipped "
          f"({brides} brides and {len(PEOPLE) - brides} grooms in the set).")
    print(f"  Password for every seeded account: {DEV_PASSWORD}")
    print("  Next: python -m scripts.reindex_discovery, then the platform's import_module_identities.py")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:])))

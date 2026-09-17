"""Seed four complete Mangaly families — candidate + parent + sibling + relative.

Why this exists, alongside `seed_dev_accounts.py`: that script seeds four lone
candidates in four different cities, which is enough to look at a profile screen
but not enough to exercise the product. Nobody can match anybody (different
cities, no `looking_for`), and no account has a Home Circle, so the parent,
sibling and relative roles have nothing to be seen through. The product owner
asked (2026-09-17) for "atleast 4 sets in same location … 1 parent + 1 candidate
+ 1 relative + 1 sibling" so each role can actually be tried in the app.

What it creates, all in Hyderabad so they are in each other's results:
  * 4 candidates — 2 looking for a groom, 2 looking for a bride, so the
    two-way `_looking_for_each_other()` rule in `discovery.interface` has real
    pairs to return rather than an empty deck.
  * 12 family members — a parent, a sibling and a relative per candidate, each a
    real account with a display name and NO candidate profile of their own,
    which is what a family member actually is (`platform-basic-identity`: the
    module holds the profile, the platform holds the person).
  * Photos: one portrait (the always-visible minimum photo) plus three
    lifestyle images per candidate, so Discover has a gallery to scroll rather
    than a single face.
  * Hinge-style written answers under the `self_expression` category, which is
    the material a candidate reads on another candidate; the Shaadi-style
    factual columns (education, profession, marital status, diet, relocation)
    are the material a parent reads. Both are seeded so the two audiences can
    be compared on screen.

This writes profiles directly as `mangaly_owner` (same admin-seeding exception
`seed_dev_accounts.py` documents). It deliberately does NOT create the Home
Circle memberships: those are relationships, and relationships are created
through the real invite/accept flow by `seed_dev_family_circles.py`, never by
inserting membership rows behind the application's back.

Run, in order:
    python -m scripts.seed_dev_families
    python -m scripts.reindex_discovery
    (platform) .venv\\Scripts\\python scripts\\import_module_identities.py
    python -m scripts.seed_dev_family_circles
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from uuid import uuid4

import asyncpg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.components.identity_bridge.credentials import CredentialHasher  # noqa: E402

DB_DSN = "postgresql://mangaly_owner:mangaly_owner_dev_password@localhost:5433/mangaly"
MEDIA_ROOT = Path(__file__).resolve().parents[1] / ".local-media"
DEV_PASSWORD = "MangalyDev123!"
CITY = "Hyderabad, Telangana"

# Every seeded identifier lives in one reserved block: +91 followed by EIGHT
# digits (1 00S 000M — set, then member), at the product owner's request
# (2026-09-17) that dummy mobile numbers be 8 digits rather than 10. A real
# Indian mobile number is 10 digits and never starts with 1, so nothing seeded
# here can be mistaken for — or collide with — a real person's number, or with
# `seed_dev_accounts.py`'s +91900000000x block.
# The seeded written answers, mapped onto the app's own prompt questions
# (`mangaly-web/lib/profileSections.ts`). Anything else is never rendered.
PROMPT_MAPPING = {
    "weekend": ("prompt_1", "ideal_weekend"),
    "i_value": ("prompt_2", "non_negotiable"),
    "about_me": ("prompt_3", "simple_pleasures"),
}

FAMILIES: list[dict] = [
    {
        "surname": "Sharma",
        "candidate": {
            "phone": "+9110010001",
            "name": "Meera Sharma",
            "gender": "female",
            "dob": date(1996, 4, 12),
            "looking_for": "groom",
            "attrs": {
                "education": {"highest_education_level": "masters"},
                "profession": {"occupation": "Architect"},
                "marital_history": {"marital_status": "never_married"},
                "relocation": {"relocation_willingness": "open_to_discussion"},
                "lifestyle": {"diet": "vegetarian"},
                "partner_preference": {"age_range": {"min": 28, "max": 36}, "locality": "Hyderabad"},
                "family_involvement_expectations": {"level": "close_knit"},
            },
            "prompts": {
                "about_me": "I design buildings for a living and rearrange my own flat for fun. "
                "Sunday mornings are for the Necklace Road walk and filter coffee after.",
                "i_value": "Someone who says what they mean. I would rather have an honest "
                "disagreement than a polite silence.",
                "weekend": "Sketching at Golconda, or cooking far too much food for two people.",
            },
        },
        "circle": [
            {"phone": "+9110010002", "name": "Rajesh Sharma", "relationship": "parent"},
            {"phone": "+9110010003", "name": "Nikhil Sharma", "relationship": "sibling"},
            {"phone": "+9110010004", "name": "Sunita Kapoor", "relationship": "relative"},
        ],
    },
    {
        "surname": "Khanna",
        "candidate": {
            "phone": "+9110020001",
            "name": "Arjun Khanna",
            "gender": "male",
            "dob": date(1993, 9, 3),
            "looking_for": "bride",
            "attrs": {
                "education": {"highest_education_level": "bachelors"},
                "profession": {"occupation": "Software Engineer"},
                "marital_history": {"marital_status": "never_married"},
                "relocation": {"relocation_willingness": "yes"},
                "lifestyle": {"diet": "non_vegetarian"},
                "partner_preference": {"age_range": {"min": 26, "max": 33}, "locality": "Hyderabad"},
                "pets": {"preference": "love_pets"},
            },
            "prompts": {
                "about_me": "Backend engineer, terrible badminton player, extremely serious about "
                "biryani rankings within a two-kilometre radius.",
                "i_value": "Curiosity. I like people who ask a second question.",
                "weekend": "Long drives towards Vikarabad, or losing an afternoon in a bookshop.",
            },
        },
        "circle": [
            {"phone": "+9110020002", "name": "Kavita Khanna", "relationship": "parent"},
            {"phone": "+9110020003", "name": "Riya Khanna", "relationship": "sibling"},
            {"phone": "+9110020004", "name": "Mohan Khanna", "relationship": "relative"},
        ],
    },
    {
        "surname": "Malhotra",
        "candidate": {
            "phone": "+9110030001",
            "name": "Ishita Malhotra",
            "gender": "female",
            "dob": date(1994, 12, 28),
            "looking_for": "groom",
            "attrs": {
                "education": {"highest_education_level": "doctorate"},
                "profession": {"occupation": "Research Scientist"},
                "marital_history": {"marital_status": "never_married"},
                "relocation": {"relocation_willingness": "no"},
                "lifestyle": {"diet": "eggetarian"},
                "partner_preference": {"age_range": {"min": 29, "max": 38}, "locality": "Hyderabad"},
                "career_children_living_financial": {"wants_children": "open_to_discussion"},
            },
            "prompts": {
                "about_me": "I study plant genetics, which means I spend a lot of time being "
                "patient with things that grow slowly. It has made me calmer.",
                "i_value": "Kindness that shows up when nobody is watching.",
                "weekend": "Botanical garden, then the same dosa place I have gone to for years.",
            },
        },
        "circle": [
            {"phone": "+9110030002", "name": "Suresh Malhotra", "relationship": "parent"},
            {"phone": "+9110030003", "name": "Aditya Malhotra", "relationship": "sibling"},
            {"phone": "+9110030004", "name": "Neha Sethi", "relationship": "relative"},
        ],
    },
    {
        "surname": "Bhatia",
        "candidate": {
            "phone": "+9110040001",
            "name": "Rohan Bhatia",
            "gender": "male",
            "dob": date(1991, 6, 17),
            "looking_for": "bride",
            "attrs": {
                "education": {"highest_education_level": "masters"},
                "profession": {"occupation": "Chartered Accountant"},
                "marital_history": {"marital_status": "divorced"},
                "relocation": {"relocation_willingness": "open_to_discussion"},
                "lifestyle": {"diet": "vegetarian"},
                "partner_preference": {"age_range": {"min": 28, "max": 37}, "locality": "Hyderabad"},
                "independence": {"preference": "balanced"},
            },
            "prompts": {
                "about_me": "Numbers by day, tabla badly by night. I was married before; it ended "
                "respectfully and I would rather say so upfront than halfway through.",
                "i_value": "Directness, and people who are gentle with waiters.",
                "weekend": "Cycling by the lake before it gets hot, then nothing at all.",
            },
        },
        "circle": [
            {"phone": "+9110040002", "name": "Anjali Bhatia", "relationship": "parent"},
            {"phone": "+9110040003", "name": "Tanvi Bhatia", "relationship": "sibling"},
            {"phone": "+9110040004", "name": "Vikas Bhatia", "relationship": "relative"},
        ],
    },
]


def fetch_bytes(url: str) -> bytes | None:
    """Dummy imagery only. Returns None rather than raising: a seed run must not
    fail outright because a public image host was briefly unreachable — a
    profile with fewer photos is still a usable profile.

    Uses curl rather than `urllib.request`, which hung indefinitely here on
    Windows against hosts curl reached in under a second (urllib's automatic
    system-proxy lookup is the usual cause). A seeding script that silently
    never finishes is worse than one that skips a photo, so the fetch is given
    a hard deadline it cannot exceed."""
    try:
        done = subprocess.run(  # noqa: S603 — fixed argv, no shell
            ["curl", "-sSL", "--max-time", "15", "--fail", url],
            capture_output=True,
            timeout=25,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"        (photo unavailable: {url} — {exc})")
        return None
    if done.returncode != 0 or not done.stdout:
        print(f"        (photo unavailable: {url} — curl exit {done.returncode})")
        return None
    return done.stdout


def portrait_url(gender: str, index: int) -> str:
    """randomuser.me: consented, generated stock headshots meant for test data
    (same source `seed_dev_accounts.py` already uses)."""
    return f"https://randomuser.me/api/portraits/{'women' if gender == 'female' else 'men'}/{index}.jpg"


def lifestyle_url(seed: str) -> str:
    """A non-portrait photo — the travel/hobby shots real matrimony galleries
    carry. Keeps a candidate's gallery from being four different faces, which is
    what using four portraits for one person would produce."""
    return f"https://picsum.photos/seed/{seed}/900/1200"


async def insert_account(conn: asyncpg.Connection, *, phone: str, name: str, credential_hash: str):
    """One account row, with the platform display name Home Circle screens read
    (migration 019). Returns None when the identifier is already seeded, so the
    whole script is safe to re-run."""
    existing = await conn.fetchval(
        "SELECT id FROM mangaly_identity.account WHERE phone_identifier = $1", phone
    )
    if existing:
        return None
    account_id = uuid4()
    await conn.execute(
        """
        INSERT INTO mangaly_identity.account
            (id, phone_identifier, credential_hash, status, identifier_verified_at, display_name)
        VALUES ($1, $2, $3, 'active', now(), $4)
        """,
        account_id,
        phone,
        credential_hash,
        name,
    )
    return account_id


async def insert_candidate_profile(conn: asyncpg.Connection, *, account_id, spec: dict) -> None:
    profile_id = uuid4()
    await conn.execute(
        """
        INSERT INTO mangaly_profile.profile
            (id, account_id, name, date_of_birth, gender, city_locality, status)
        VALUES ($1, $2, $3, $4, $5, $6, 'active')
        """,
        profile_id,
        account_id,
        spec["name"],
        spec["dob"],
        spec["gender"],
        CITY,
    )

    # Photo 1 is the portrait and is primary. FR006/DEC-V1-016: the primary photo
    # is the one Discover may show before any connection exists, so every seeded
    # candidate has one — a profile with no visible photo is the case the owner
    # specifically did not want to keep hitting.
    photos: list[bytes] = []
    portrait = fetch_bytes(portrait_url(spec["gender"], abs(hash(spec["phone"])) % 90))
    if portrait:
        photos.append(portrait)
    for n in range(3):
        shot = fetch_bytes(lifestyle_url(f"{spec['phone']}-{n}"))
        if shot:
            photos.append(shot)

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
            uuid4(),
            profile_id,
            f"local://{profile_id}/{filename}",
            order == 0,
            order,
        )

    attrs = dict(spec["attrs"])
    # DEC-V1-017: `looking_for` lives under partner_preference and is what the
    # ranking engine reads. Merged rather than assigned so a family's own
    # partner_preference block above is not silently dropped.
    attrs["partner_preference"] = {**attrs.get("partner_preference", {}), "looking_for": spec["looking_for"]}
    # The candidate's own words, in the product's own prompt model
    # (`in_my_words.prompt_N = {q, a}`), which is what every screen renders —
    # the profile view a candidate reads, and the owner's own editor. Writing
    # them under any other category leaves them invisible.
    attrs["in_my_words"] = {
        slot: {"q": question, "a": spec["prompts"][key]}
        for key, (slot, question) in PROMPT_MAPPING.items()
        if spec["prompts"].get(key)
    }

    for category, fields in attrs.items():
        for key, value in fields.items():
            await conn.execute(
                """
                INSERT INTO mangaly_profile.profile_attribute
                    (id, profile_id, category, attribute_key, state, value)
                VALUES ($1, $2, $3, $4, 'value', $5::jsonb)
                """,
                uuid4(),
                profile_id,
                category,
                key,
                json.dumps(value),
            )
    print(f"        {len(photos)} photos, {sum(len(v) for v in attrs.values())} attributes")


async def main() -> int:
    credential_hash = CredentialHasher().hash(DEV_PASSWORD)
    conn = await asyncpg.connect(DB_DSN)
    created = skipped = 0
    try:
        for family in FAMILIES:
            print(f"\n  {family['surname']} family")
            spec = family["candidate"]
            account_id = await insert_account(
                conn, phone=spec["phone"], name=spec["name"], credential_hash=credential_hash
            )
            if account_id is None:
                print(f"    SKIP  {spec['name']} — already seeded")
                skipped += 1
            else:
                print(f"    OK    {spec['name']} (candidate, looking for {spec['looking_for']}) — {spec['phone']}")
                await insert_candidate_profile(conn, account_id=account_id, spec=spec)
                created += 1

            for member in family["circle"]:
                member_id = await insert_account(
                    conn, phone=member["phone"], name=member["name"], credential_hash=credential_hash
                )
                if member_id is None:
                    print(f"    SKIP  {member['name']} — already seeded")
                    skipped += 1
                    continue
                # No profile row on purpose: a family member is a person in the
                # circle, not a candidate. Giving them a profile would put them
                # in Discover, which is exactly the confusion to avoid.
                print(f"    OK    {member['name']} ({member['relationship']}) — {member['phone']}")
                created += 1

        print(f"\n  {created} accounts created, {skipped} already present.")
        print(f"  Password for every seeded account: {DEV_PASSWORD}")
        print("  Next: python -m scripts.reindex_discovery, then the platform's")
        print("  import_module_identities.py, then python -m scripts.seed_dev_family_circles")
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

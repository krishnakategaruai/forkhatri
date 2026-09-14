"""Seed realistic dummy accounts + profiles directly into Postgres.

Connects as `mangaly_owner` (bypasses RLS — this is an admin seeding script,
never application code) and writes straight to `mangaly_identity.account` /
`mangaly_profile.*`, using the same Argon2id hasher `identity_bridge` uses so
every seeded account logs in for real via the password path.

Why this exists: the OTP-based signup/login screens are slow to drive by hand
or by script for every fresh test session (six digits, a log-scrape, a
rate-limit window) and the user has said not to use that flow for general
dev/browser testing — seed once, then log in with a password like any other
account. Real photos come from randomuser.me (public dummy-headshot API,
generated/consented stock photos meant for exactly this use), saved into
`.local-media/` through the same `storage_ref` contract `storage.py` uses.

Run: python -m scripts.seed_dev_accounts
"""

from __future__ import annotations

import asyncio
import sys
import urllib.request
from datetime import date
from pathlib import Path
from uuid import uuid4

import asyncpg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.components.identity_bridge.credentials import CredentialHasher  # noqa: E402

DB_DSN = "postgresql://mangaly_owner:mangaly_owner_dev_password@localhost:5433/mangaly"
MEDIA_ROOT = Path(__file__).resolve().parents[1] / ".local-media"
DEV_PASSWORD = "MangalyDev123!"

# One representative field per enhanced-matching category, matching
# `lib/profileCategoryConfig.ts` on the frontend exactly.
SEED_PROFILES = [
    {
        "phone": "+919000000001",
        "name": "Ananya Reddy",
        "gender": "female",
        "dob": date(1995, 3, 14),
        "city": "Hyderabad, Telangana",
        "attrs": {
            "education": {"highest_education_level": "masters"},
            "profession": {"occupation": "Product Manager"},
            "marital_history": {"marital_status": "never_married"},
            "relocation": {"relocation_willingness": "open_to_discussion"},
            "partner_preference": {"age_range": {"min": 28, "max": 35}},
            "lifestyle": {"diet": "vegetarian"},
            "communication_style": {"style": "thoughtful"},
        },
        "declined": [("horoscope", "matching_required")],
    },
    {
        "phone": "+919000000002",
        "name": "Rahul Varma",
        "gender": "male",
        "dob": date(1992, 11, 2),
        "city": "Bengaluru, Karnataka",
        "attrs": {
            "education": {"highest_education_level": "bachelors"},
            "profession": {"occupation": "Software Engineer"},
            "marital_history": {"marital_status": "never_married"},
            "relocation": {"relocation_willingness": "yes"},
            "partner_preference": {"locality": "Bengaluru or Hyderabad"},
            "lifestyle": {"diet": "non_vegetarian"},
            "independence": {"preference": "balanced"},
            "pets": {"preference": "love_pets"},
        },
        "declined": [],
    },
    {
        "phone": "+919000000003",
        "name": "Priya Nair",
        "gender": "female",
        "dob": date(1997, 7, 21),
        "city": "Kochi, Kerala",
        "attrs": {
            "education": {"highest_education_level": "doctorate"},
            "profession": {"occupation": "Research Scientist"},
        },
        "declined": [("marital_history", "marital_status"), ("relocation", "relocation_willingness")],
    },
    {
        "phone": "+919000000004",
        "name": "Karthik Iyer",
        "gender": "male",
        "dob": date(1990, 1, 9),
        "city": "Chennai, Tamil Nadu",
        "attrs": {
            "education": {"highest_education_level": "masters"},
            "profession": {"occupation": "Chartered Accountant"},
            "marital_history": {"marital_status": "divorced"},
            "relocation": {"relocation_willingness": "no"},
            "partner_preference": {"age_range": {"min": 27, "max": 34}},
            "food_travel_hobbies": {"hobbies": "Trekking, cooking, cricket"},
            "career_children_living_financial": {"wants_children": "yes"},
            "family_involvement_expectations": {"level": "close_knit"},
        },
        "declined": [],
    },
]


def fetch_photo(gender: str) -> bytes:
    ru_gender = "women" if gender == "female" else "men"
    idx = uuid4().int % 90
    url = f"https://randomuser.me/api/portraits/{ru_gender}/{idx}.jpg"
    with urllib.request.urlopen(url, timeout=15) as res:
        return res.read()


async def main() -> int:
    hasher = CredentialHasher()
    credential_hash = hasher.hash(DEV_PASSWORD)

    conn = await asyncpg.connect(DB_DSN)
    try:
        created = []
        for spec in SEED_PROFILES:
            existing = await conn.fetchval(
                "SELECT id FROM mangaly_identity.account WHERE phone_identifier = $1", spec["phone"]
            )
            if existing:
                print(f"  SKIP  {spec['name']} — account already seeded ({spec['phone']})")
                continue

            account_id = uuid4()
            await conn.execute(
                """
                INSERT INTO mangaly_identity.account
                    (id, phone_identifier, credential_hash, status, identifier_verified_at)
                VALUES ($1, $2, $3, 'active', now())
                """,
                account_id,
                spec["phone"],
                credential_hash,
            )

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
                spec["city"],
            )

            photo_bytes = fetch_photo(spec["gender"])
            directory = MEDIA_ROOT / str(profile_id)
            directory.mkdir(parents=True, exist_ok=True)
            filename = f"{uuid4()}.jpg"
            (directory / filename).write_bytes(photo_bytes)
            storage_ref = f"local://{profile_id}/{filename}"

            await conn.execute(
                """
                INSERT INTO mangaly_profile.profile_media
                    (id, profile_id, media_type, storage_ref, is_primary, upload_status)
                VALUES ($1, $2, 'photo', $3, true, 'complete')
                """,
                uuid4(),
                profile_id,
                storage_ref,
            )

            for category, fields in spec["attrs"].items():
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
                        __import__("json").dumps(value),
                    )
            for category, key in spec["declined"]:
                await conn.execute(
                    """
                    INSERT INTO mangaly_profile.profile_attribute
                        (id, profile_id, category, attribute_key, state, value)
                    VALUES ($1, $2, $3, $4, 'declined', NULL)
                    """,
                    uuid4(),
                    profile_id,
                    category,
                    key,
                )

            created.append(spec["name"])
            print(f"  OK    {spec['name']} — {spec['phone']} / password: {DEV_PASSWORD}")

        print(f"\n  {len(created)} accounts seeded, {len(SEED_PROFILES) - len(created)} already present.")
        print(f"  Every seeded account's password is: {DEV_PASSWORD}")
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

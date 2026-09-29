"""Two fresh families with NO Home Circle yet, for building circles by hand.

The product owner (2026-09-21) asked to watch Home Circles being built in the
app itself, one family per Chrome window with a tab per person, and named who
starts each one:

  * Mehra family  — the PARENT starts it (P1). Harish Mehra has no profile of
    his own; he finds his daughter Divya and asks to join her circle, then
    brings in her brother and her aunt.
  * Tandon family — the CANDIDATE starts it (C2). Varun Tandon invites his
    mother, his sister and his uncle.

Only the people are seeded here. Every membership is created through the
product's own invite → accept flow, never inserted (the standing rule for
relationships). Divya looks for a groom and Varun for a bride, both in
Hyderabad, so the two families can also find each other in Discover.

Reuses `seed_dev_families.py`'s account/profile helpers and its reserved
8-digit number block (+91 1005… and +91 1006…). Idempotent.

    python -m scripts.seed_dev_circle_demo
    python -m scripts.reindex_discovery
    (platform) .venv\\Scripts\\python scripts\\import_module_identities.py
"""

from __future__ import annotations

import asyncio
import sys
from datetime import date
from pathlib import Path

import asyncpg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.components.identity_bridge.credentials import CredentialHasher  # noqa: E402
from scripts.seed_dev_families import (  # noqa: E402
    DB_DSN,
    DEV_PASSWORD,
    insert_account,
    insert_candidate_profile,
)

FAMILIES: list[dict] = [
    {
        "surname": "Mehra",
        "starts": "parent",
        "candidate": {
            "key": "c1",
            "phone": "+9110050001",
            "name": "Divya Mehra",
            "gender": "female",
            "dob": date(1997, 8, 3),
            "looking_for": "groom",
            "attrs": {
                "basics": {"height_cm": 162, "mother_tongue": "telugu"},
                "education": {"highest_education_level": "masters"},
                "profession": {"occupation": "Data Scientist"},
                "marital_history": {"marital_status": "never_married"},
                "relocation": {"relocation_willingness": "open_to_discussion"},
                "lifestyle": {"diet": "vegetarian"},
                "partner_preference": {"age_range": {"min": 27, "max": 34}, "locality": "Hyderabad"},
                "family_involvement_expectations": {"level": "close_knit"},
            },
            "prompts": {
                "about_me": "Filter coffee before anything else, a kolam at the door on festival days, "
                "and a long walk around KBR Park when a model will not converge.",
                "i_value": "Someone who talks things through the same evening instead of going quiet for a week.",
                "weekend": "Chilkur early in the morning, then idli at Ram ki Bandi with my brother.",
            },
        },
        "people": [
            {"key": "p1", "phone": "+9110050002", "name": "Harish Mehra", "relationship": "parent"},
            {"key": "s1", "phone": "+9110050003", "name": "Karan Mehra", "relationship": "sibling"},
            {"key": "r1", "phone": "+9110050004", "name": "Pooja Arora", "relationship": "relative"},
        ],
    },
    {
        "surname": "Tandon",
        "starts": "candidate",
        "candidate": {
            "key": "c2",
            "phone": "+9110060001",
            "name": "Varun Tandon",
            "gender": "male",
            "dob": date(1994, 1, 21),
            "looking_for": "bride",
            "attrs": {
                "basics": {"height_cm": 178, "mother_tongue": "hindi"},
                "education": {"highest_education_level": "bachelors"},
                "profession": {"occupation": "Civil Engineer"},
                "marital_history": {"marital_status": "never_married"},
                "relocation": {"relocation_willingness": "yes"},
                "lifestyle": {"diet": "eggetarian"},
                "partner_preference": {"age_range": {"min": 25, "max": 31}, "locality": "Hyderabad"},
                "family_involvement_expectations": {"level": "moderate"},
            },
            "prompts": {
                "about_me": "I build flyovers for a living and still stop to watch the Charminar traffic "
                "like it is a puzzle someone should solve.",
                "i_value": "Keeping a promise to my parents and to whoever I marry — both, not one over the other.",
                "weekend": "Cricket at the ground by 6, then my mother's pesarattu. Non-negotiable.",
            },
        },
        "people": [
            {"key": "p2", "phone": "+9110060002", "name": "Rekha Tandon", "relationship": "parent"},
            {"key": "s2", "phone": "+9110060003", "name": "Ananya Tandon", "relationship": "sibling"},
            {"key": "r2", "phone": "+9110060004", "name": "Deepak Chopra", "relationship": "relative"},
        ],
    },
]


# [DEC-V1-019] A parent whose daughter has never signed up. Only the parent is
# seeded: the daughter's profile is created BY HIM in the app (Me → "Create a
# profile for my son or daughter"), with her number +91 1007 0001, which is how
# she takes it over later. Nothing about her is inserted here.
PARENT_ONLY = [{"key": "p3", "phone": "+9110070002", "name": "Sunil Kapoor"}]


async def main() -> int:
    credential_hash = CredentialHasher().hash(DEV_PASSWORD)
    conn = await asyncpg.connect(DB_DSN)
    try:
        for family in FAMILIES:
            print(f"\n  {family['surname']} family (circle started by the {family['starts']})")
            spec = family["candidate"]
            account_id = await insert_account(
                conn, phone=spec["phone"], name=spec["name"], credential_hash=credential_hash
            )
            if account_id is None:
                print(f"    SKIP  {spec['key']}  {spec['name']} — already seeded")
            else:
                print(f"    OK    {spec['key']}  {spec['name']} (candidate, looking for {spec['looking_for']})")
                await insert_candidate_profile(conn, account_id=account_id, spec=spec)
            for person in family["people"]:
                person_id = await insert_account(
                    conn, phone=person["phone"], name=person["name"], credential_hash=credential_hash
                )
                state = "SKIP" if person_id is None else "OK  "
                print(f"    {state}  {person['key']}  {person['name']} ({person['relationship']}, no profile)")
        print("\n  Kapoor family (the parent creates his daughter's profile in the app)")
        for person in PARENT_ONLY:
            person_id = await insert_account(
                conn, phone=person["phone"], name=person["name"], credential_hash=credential_hash
            )
            state = "SKIP" if person_id is None else "OK  "
            print(f"    {state}  {person['key']}  {person['name']} (parent, no profile, no circle yet)")
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

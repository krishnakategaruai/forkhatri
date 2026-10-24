r"""Development-only: 20 realistic Milavn QA members. Refuses to run outside development.

    platform\identity-service\.venv\Scripts\python modules\MOD02-milavn\scripts\seed_qa_members.py
    ... seed_qa_members.py --remove     # delete exactly these 20 and their Milavn data

Step 1 creates identity.member + a development password credential (phones
+919800020001..20, emails *@qa.forkhatri.test), idempotently, like
platform/identity-service/scripts/seed_dev_members.py.
Step 2 makes each member enter Milavn THROUGH THE PRODUCT API: a dev session
(platform/identity-service/scripts/dev_session.py <uuid> --cookie-header), live place
search (GET /profile/places), onboarding (POST /profile), the one-time woman/man
answer (PUT /circles/gender/me, each member's own truthful answer), and a short bio
(PATCH /profile/enrichment). No Milavn row is inserted directly.
Requires the identity (8100) and Milavn (8001) APIs running in development.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path
from uuid import UUID

import asyncpg
import httpx
from argon2 import PasswordHasher

REPO = Path(__file__).resolve().parents[3]
IDENTITY_DIR = REPO / "platform" / "identity-service"
PYTHON = IDENTITY_DIR / ".venv" / "Scripts" / "python.exe"
DEV_PASSWORD = "ForKhatri-dev-2026"
IDENTITY_DSN = os.environ.get(
    "IDENTITY_OWNER_DSN", "postgresql://identity_owner:identity_owner_dev_password@localhost:5433/forkhatri_identity"
)
MILAVN_DSN = os.environ.get(
    "MILAVN_OWNER_DSN", "postgresql://milavn_owner:milavn_owner_dev_password@localhost:5433/forkhatridb"
)
MILAVN_API = os.environ.get("MILAVN_API_URL", "http://localhost:8001").rstrip("/")

# (name, gender, language, profession, place search, interests, bio)
RAW = [
    ("Ananya Iyer", "woman", "en", "Chartered accountant", "Banjara Hills|Hyderabad", ["networking", "yoga", "book-club"], "CA by day, yoga by morning."),
    ("Rohan Deshmukh", "man", "en", "Doctor", "Hadapsar|Pune", ["running", "cycling", "volunteering", "trekking"], "Physician; weekend cyclist."),
    ("Sneha Reddy", "woman", "te", "Lawyer", "Hanamkonda|Hanumakonda", ["book-club", "poetry", "festivals"], "Advocate who loves Telugu poetry."),
    ("Vikram Chowdary", "man", "te", "Software engineer", "Vijayawada|NTR", ["coding", "badminton", "startups"], "Backend engineer, badminton on weekends."),
    ("Priya Nair", "woman", "en", "Teacher", "Indiranagar|Bengaluru", ["book-club", "kids-activities", "language-exchange", "music"], "Primary school teacher."),
    ("Arjun Mehra", "man", "hi", "Shop owner", "Karol Bagh|Delhi", ["street-food", "cricket", "festivals"], "Runs a family fabric shop."),
    ("Kavita Joshi", "woman", "hi", "Chef", "Bandra West|Mumbai", ["potluck", "street-food", "workshops", "dance"], "Pastry chef, always baking."),
    ("Suresh Babu", "man", "te", "Photographer", "Adyar|Chennai", ["photography-walks", "trekking", "music", "coffee-meetups"], "Wedding and street photographer."),
    ("Meera Kulkarni", "woman", "hi", "Homemaker", "Dharampeth|Nagpur", ["parenting", "festivals", "cleanup-drives"], "Mother of two, active in the colony."),
    ("Aditya Sharma", "man", "en", "Student", "Jaipur|Jaipur", ["football", "coding", "board-games"], "Final-year engineering student."),
    ("Divya Menon", "woman", "en", "Software engineer", "Whitefield|Bengaluru", ["coding", "cycling", "coffee-meetups"], "Frontend developer."),
    ("Karthik Raman", "man", "en", "Chartered accountant", "T Nagar|Chennai", ["networking", "cricket", "career"], "CA, cricket club captain."),
    ("Pooja Agarwal", "woman", "hi", "Doctor", "Vaishali Nagar|Jaipur", ["yoga", "volunteering", "swimming"], "Paediatrician."),
    ("Imran Qureshi", "man", "hi", "Chef", "Madhapur|Hyderabad", ["street-food", "potluck", "cricket", "festivals"], "Biryani chef."),
    ("Lakshmi Prasad", "woman", "te", "Teacher", "Kakinada|Andhra", ["dance", "music", "book-club"], "Telugu teacher and classical dancer."),
    ("Nitin Bhosale", "man", "hi", "Lawyer", "Shivajinagar|Pune", ["workshops", "networking", "running"], "Corporate lawyer."),
    ("Farah Khan", "woman", "en", "Photographer", "Powai|Mumbai", ["photography-walks", "theatre", "coffee-meetups"], "Photographer and theatre lover."),
    ("Gaurav Malhotra", "man", "hi", "Shop owner", "Lajpat Nagar|Delhi", ["badminton", "networking", "street-food"], "Electronics shop owner."),
    ("Shalini Rao", "woman", "en", "Student", "Gachibowli|Hyderabad", ["language-exchange", "theatre", "board-games", "poetry"], "Masters student in literature."),
    ("Manoj Patil", "man", "hi", "Homemaker", "Nagpur|Maharashtra", ["parenting", "volunteering", "kids-activities"], "Stay-at-home dad, volunteers at the school."),
]
MEMBERS = [
    {
        "id": UUID(f"c2000000-0000-4000-8000-0000000000{i:02d}"),
        "name": r[0], "gender": r[1], "language": r[2], "profession": r[3],
        "query": r[4], "interests": r[5], "bio": r[6],
        "phone": f"+9198000200{i:02d}",
        "email": f"{r[0].lower().replace(' ', '.')}@qa.forkhatri.test",
    }
    for i, r in enumerate(RAW, start=1)
]


def cookie_for(member_id: UUID) -> str:
    out = subprocess.run(
        [str(PYTHON), str(IDENTITY_DIR / "scripts" / "dev_session.py"), str(member_id), "--cookie-header"],
        capture_output=True, text=True, cwd=IDENTITY_DIR,
    )
    if out.returncode != 0:
        raise RuntimeError(f"dev_session failed for {member_id}: {out.stderr.strip()}")
    return out.stdout.strip().removeprefix("Cookie: ")


async def seed_identity() -> None:
    pw = PasswordHasher().hash(DEV_PASSWORD)
    conn = await asyncpg.connect(IDENTITY_DSN)
    try:
        async with conn.transaction():
            for m in MEMBERS:
                await conn.execute(
                    "INSERT INTO identity.member (id, display_name, phone_e164, email, preferred_language) "
                    "VALUES ($1,$2,$3,$4,$5) ON CONFLICT (id) DO UPDATE SET display_name = EXCLUDED.display_name, "
                    "preferred_language = EXCLUDED.preferred_language, updated_at = now()",
                    m["id"], m["name"], m["phone"], m["email"], m["language"],
                )
                await conn.execute(
                    "INSERT INTO identity.password_credential (member_id, password_hash) VALUES ($1,$2) "
                    "ON CONFLICT (member_id) DO UPDATE SET password_hash = EXCLUDED.password_hash, updated_at = now()",
                    m["id"], pw,
                )
    finally:
        await conn.close()
    print(f"identity: {len(MEMBERS)} members ready (password {DEV_PASSWORD})")


def enter_milavn() -> None:
    used: set[str] = set()
    with httpx.Client(base_url=MILAVN_API, timeout=30) as http:
        for m in MEMBERS:
            headers = {"Cookie": cookie_for(m["id"])}
            search, _, want = m["query"].partition("|")  # live search by name; keep the hit in the intended city
            found = http.get("/profile/places", params={"q": search}, headers=headers)
            found.raise_for_status()
            options = [p for p in found.json() if p["label"] not in used and want in p["label"]]
            if not options:
                raise RuntimeError(f"no place found for {m['query']!r}")
            place = options[0]
            used.add(place["label"])
            body = {
                "locality_city": place["locality_city"], "locality_zone": place["locality_zone"],
                "locality_locality": place["locality_locality"], "locality_state": place["locality_state"],
                "locality_lat": place["lat"], "locality_lng": place["lon"],
                "interests": m["interests"], "language_preference": m["language"],
            }
            http.post("/profile", json=body, headers=headers).raise_for_status()
            http.put("/circles/gender/me", json={"gender": m["gender"]}, headers=headers).raise_for_status()
            e = http.patch("/profile/enrichment", data={"bio": m["bio"]}, headers=headers)
            e.raise_for_status()
            print(f"milavn: {m['name']} | {place['label']} | {e.json()['interests']}")


async def remove() -> None:
    ids = [m["id"] for m in MEMBERS]
    for dsn, schema_like in ((MILAVN_DSN, "milavn%"), (IDENTITY_DSN, "identity")):
        conn = await asyncpg.connect(dsn)
        try:
            cols = await conn.fetch(
                "SELECT c.table_schema, c.table_name, c.column_name FROM information_schema.columns c "
                "JOIN information_schema.tables t USING (table_schema, table_name) "
                "WHERE t.table_type = 'BASE TABLE' AND c.table_schema LIKE $1 AND c.data_type = 'uuid' "
                "AND (c.column_name LIKE '%member_id%' OR (c.table_schema = 'identity' "
                "AND c.table_name = 'member' AND c.column_name = 'id'))",
                schema_like,
            )
            pending = [(r["table_schema"], r["table_name"], r["column_name"]) for r in cols]
            for _ in range(8):  # repeat until foreign-key order sorts itself out
                left = []
                for s, t, c in pending:
                    try:
                        async with conn.transaction():
                            await conn.execute(f'DELETE FROM "{s}"."{t}" WHERE "{c}" = ANY($1::uuid[])', ids)
                    except (asyncpg.ForeignKeyViolationError, asyncpg.InsufficientPrivilegeError):
                        left.append((s, t, c))
                pending = left
                if not pending:
                    break
            if pending:
                print("could not clear:", pending)
        finally:
            await conn.close()
    print("removed the 20 QA members and their Milavn data (uploaded photo files, if any, stay on disk).")


def main() -> int:
    if os.environ.get("FORKHATRI_ENVIRONMENT", "development") != "development":
        print("Refusing: QA members are for development only.")
        return 2
    if "--remove" in sys.argv:
        asyncio.run(remove())
        return 0
    asyncio.run(seed_identity())
    enter_milavn()
    return 0


if __name__ == "__main__":
    sys.exit(main())

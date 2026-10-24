r"""Development-only: brand-new members for "first time in the app" tests. Refuses to run outside development.

    platform\identity-service\.venv\Scripts\python modules\MOD02-milavn\scripts\seed_fresh_members.py
    ... seed_fresh_members.py --remove     # delete exactly these members (and nothing else)

Unlike seed_qa_members.py, these members get only a ForKhatri identity and a development
password: no module has ever seen them, so each module's signup and first-run screens can be
walked exactly as a new person meets them. Phones +919800020021..29, emails *@qa.forkhatri.test,
password ForKhatri-dev-2026 (sign in at the hub with "Use a password instead").
Once a test has walked a module's first-run, that member is no longer fresh; run --remove and
then this script again for a clean set (module rows they created must be removed by that module's
own delete-my-data flow first).
"""

from __future__ import annotations

import asyncio
import os
import sys
from uuid import UUID

import asyncpg
from argon2 import PasswordHasher

DEV_PASSWORD = "ForKhatri-dev-2026"
IDENTITY_DSN = os.environ.get(
    "IDENTITY_OWNER_DSN", "postgresql://identity_owner:identity_owner_dev_password@localhost:5433/forkhatri_identity"
)

# (name, language): realistic people for practical first-time tests, three per module.
RAW = [
    ("Padmavathi Gupta", "te"),   # 21 Milavn: 60-year-old, wants a temple trip with other women
    ("Sonal Deshpande", "en"),    # 22 Milavn: busy working woman in Pune, weekend activity
    ("Ravi Shankar Khatri", "hi"),  # 23 Milavn: organiser who wants to post a satsang quickly
    ("Sujatha Reddy", "te"),      # 24 Mangalya: mother making her daughter's profile on a shared phone
    ("Ramesh Babu Khatri", "te"),  # 25 Mangalya: father with a biodata PDF and photos on WhatsApp
    ("Anjali Verma", "en"),       # 26 Mangalya: candidate working abroad
    ("Venkatesh Naidu", "te"),    # 27 Vyapar: plumber who can barely type, wants work today
    ("Mohan Lal Khatri", "hi"),   # 28 Vyapar: shop owner hiring a helper
    ("Kamala Devi", "te"),        # 29 Vyapar: homemaker selling pickles from home
]
MEMBERS = [
    {
        "id": UUID(f"c2000000-0000-4000-8000-0000000000{i:02d}"),
        "name": name,
        "language": lang,
        "phone": f"+9198000200{i:02d}",
        "email": f"{name.lower().replace(' ', '.')}@qa.forkhatri.test",
    }
    for i, (name, lang) in enumerate(RAW, start=21)
]


async def seed() -> None:
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
    for m in MEMBERS:
        print(f"{m['id']}  {m['phone']}  {m['language']}  {m['name']}")
    print(f"{len(MEMBERS)} fresh members ready (password {DEV_PASSWORD})")


async def remove() -> None:
    conn = await asyncpg.connect(IDENTITY_DSN)
    try:
        ids = [m["id"] for m in MEMBERS]
        async with conn.transaction():
            await conn.execute("DELETE FROM identity.password_credential WHERE member_id = ANY($1::uuid[])", ids)
            await conn.execute("DELETE FROM identity.member WHERE id = ANY($1::uuid[])", ids)
    finally:
        await conn.close()
    print(f"removed {len(MEMBERS)} fresh members")


def main() -> int:
    if os.environ.get("FORKHATRI_ENVIRONMENT", "development") != "development":
        print("Refusing: fresh test members are for development only.")
        return 2
    asyncio.run(remove() if "--remove" in sys.argv else seed())
    return 0


if __name__ == "__main__":
    sys.exit(main())

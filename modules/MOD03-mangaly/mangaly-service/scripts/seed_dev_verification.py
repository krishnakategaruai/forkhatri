"""Development seed: verification evidence for the seeded candidates.

Verification is granted by operators, not by members, and Mangaly's operations
surface does not exist yet — so in development the rows are written the way an
operator action eventually will write them. Each row carries the provenance
baseline §13.4 requires: what was verified, by what method, and when.

The spread is deliberate. Some candidates have a government-ID check, some add
community confirmation, and some have nothing at all — because "no evidence
yet" is a real and common state, and §25 says a sparse profile must not be
permanently disadvantaged. A screen that has only ever been seen with every
badge lit is a screen nobody has actually tested.

Run: python -m scripts.seed_dev_verification
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402

# Owner connection, for the same narrow reason `scripts/reindex_discovery.py`
# uses one: `mangaly_app` is correctly RLS-constrained and an unscoped SELECT
# over every profile returns nothing. Granting verification is an operator
# action, so an operator-level connection is the honest representation of it.
_OWNER_URL = (
    "postgresql+asyncpg://mangaly_owner:mangaly_owner_dev_password@localhost:5433/mangaly"
)

# name -> [(layer, provenance, source_category, months_ago)]
EVIDENCE: dict[str, list[tuple[str, str, str, int]]] = {
    # DEC-V1-016: document/ID verification is dropped, so `identity_age` and
    # `operational_verification` are never granted. What a member can actually
    # earn is the face match against their own photos, recorded as a
    # `profile_facts` claim, plus phone authenticity from ForKhatri sign-in.
    "Rahul Varma": [
        ("profile_facts", "Live face match against uploaded photos", "face_match", 2),
        ("community_verification", "Confirmed by two Home Circle members", "community", 1),
        ("account_authenticity", "Phone number confirmed by OTP", "otp", 7),
    ],
    "Karthik Iyer": [
        ("profile_facts", "Live face match against uploaded photos", "face_match", 5),
        ("account_authenticity", "Phone number confirmed by OTP", "otp", 5),
    ],
    "Arjun Khanna": [
        ("profile_facts", "Live face match against uploaded photos", "face_match", 1),
        ("community_verification", "Confirmed by one Home Circle member", "community", 1),
    ],
    "Rohan Bhatia": [
        ("account_authenticity", "Phone number confirmed by OTP", "otp", 6),
    ],
    "Ananya Reddy": [
        ("profile_facts", "Live face match against uploaded photos", "face_match", 2),
        ("account_authenticity", "Phone number confirmed by OTP", "otp", 6),
    ],
    "Priya Nair": [
        ("account_authenticity", "Phone number confirmed by OTP", "otp", 4),
    ],
    # Meera Sharma and Ishita Malhotra are left with no evidence on purpose.
}

UPSERT = text(
    """
    INSERT INTO mangaly_trust.verification_layer_status
        (id, profile_id, layer, status, provenance, source_category,
         verified_at, freshness_expires_at, updated_at)
    VALUES
        (gen_random_uuid(), :profile_id, CAST(:layer AS mangaly_trust.layer_type),
         'verified', :provenance, :source_category,
         now() - make_interval(months => :months_ago), NULL, now())
    ON CONFLICT (profile_id, layer) DO UPDATE SET
        status = EXCLUDED.status,
        provenance = EXCLUDED.provenance,
        source_category = EXCLUDED.source_category,
        verified_at = EXCLUDED.verified_at,
        updated_at = now()
    """
)


async def main() -> None:
    engine = create_async_engine(_OWNER_URL)
    written = 0
    async with engine.begin() as conn:
        rows = (
            await conn.execute(text("SELECT id, name FROM mangaly_profile.profile"))
        ).all()
        by_name = {name: pid for pid, name in rows}
        missing = [n for n in EVIDENCE if n not in by_name]
        if missing:
            print(f"  (not seeded, profile absent: {', '.join(missing)})")
        for name, layers in EVIDENCE.items():
            pid = by_name.get(name)
            if pid is None:
                continue
            for layer, provenance, source, months in layers:
                await conn.execute(
                    UPSERT,
                    {
                        "profile_id": pid,
                        "layer": layer,
                        "provenance": provenance,
                        "source_category": source,
                        "months_ago": months,
                    },
                )
                written += 1
            print(f"  {name}: {', '.join(l for l, *_ in layers)}")
    await engine.dispose()
    print(f"\n{written} verification record(s) written.")


asyncio.run(main())

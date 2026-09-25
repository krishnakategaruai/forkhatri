"""Seed one relationship manager and one assisted family for development (DEC-V1-032).

Makes the `asha` persona (Asha Reddy, +919800000001) a relationship manager —
languages Telugu, Hindi and English, region Hyderabad — and assigns Varun
Tandon to her, with one suggestion (the best match Discover would give Varun)
and one call scheduled for tomorrow evening. The product owner's own account
(+919999900001) is never touched.

Idempotent: re-running updates the RM row, keeps the one active assignment,
and adds nothing twice. Writes as `mangaly_owner` (the same admin-seeding
exception `seed_dev_accounts.py` documents); the notification the real flow
sends is written too, so Varun's family sees "You have a relationship manager".

Run:
    python -m scripts.seed_dev_rm
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone

import asyncpg

DB_DSN = "postgresql://mangaly_owner:mangaly_owner_dev_password@localhost:5433/mangaly"
RM_PHONE = "+919800000001"
OWNER_PHONE = "+919999900001"
MEMBER_NAME = "Varun Tandon"
IST = timezone(timedelta(hours=5, minutes=30))

SUGGESTION_NOTE = (
    "Varun, I spoke with the family on Sunday. Same city, vegetarian home, and she "
    "would like to stay in Hyderabad after marriage — the two things you asked for. "
    "Have a look at her answers; I can set up a call with her father if you like."
)
CALL_SUMMARY = "First call with Varun and his mother: what matters most, and how they want me to reach out."


async def main() -> None:
    conn = await asyncpg.connect(DB_DSN)
    try:
        rm = await conn.fetchrow(
            "SELECT a.id, a.display_name, p.id AS profile_id FROM mangaly_identity.account a "
            "LEFT JOIN mangaly_profile.profile p ON p.account_id = a.id "
            "WHERE a.phone_identifier = $1",
            RM_PHONE,
        )
        if rm is None:
            raise SystemExit(f"no Mangaly account at {RM_PHONE}; run the platform's seed_dev_members first")
        if RM_PHONE == OWNER_PHONE:
            raise SystemExit("refusing to touch the product owner's account")
        member = await conn.fetchrow(
            "SELECT a.id, a.display_name FROM mangaly_identity.account a "
            "JOIN mangaly_profile.profile p ON p.account_id = a.id WHERE p.name = $1",
            MEMBER_NAME,
        )
        if member is None:
            raise SystemExit(f"{MEMBER_NAME} not found; run seed_dev_families + seed_dev_family_circles first")

        photo_ref = None
        if rm["profile_id"]:
            photo_ref = await conn.fetchval(
                "SELECT storage_ref FROM mangaly_profile.profile_media WHERE profile_id = $1 "
                "AND is_primary AND media_type::text = 'photo' AND upload_status::text = 'complete' LIMIT 1",
                rm["profile_id"],
            )
        if photo_ref is None:
            photo_ref = await conn.fetchval(
                "SELECT photo_ref FROM mangaly_profile.member_profile WHERE account_id = $1", rm["id"]
            )

        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO mangaly_operations.relationship_manager
                    (account_id, display_name, languages, region, photo_ref, active)
                VALUES ($1, $2, $3, $4, $5, true)
                ON CONFLICT (account_id) DO UPDATE
                   SET display_name = EXCLUDED.display_name, languages = EXCLUDED.languages,
                       region = EXCLUDED.region, photo_ref = EXCLUDED.photo_ref, active = true
                """,
                rm["id"],
                rm["display_name"] or "Asha Reddy",
                ["Telugu", "Hindi", "English"],
                "Hyderabad",
                photo_ref,
            )
            assignment_id = await conn.fetchval(
                "SELECT id FROM mangaly_operations.rm_assignment "
                "WHERE member_account_id = $1 AND status = 'active'",
                member["id"],
            )
            created = False
            if assignment_id is None:
                assignment_id = await conn.fetchval(
                    "INSERT INTO mangaly_operations.rm_assignment (rm_account_id, member_account_id, note) "
                    "VALUES ($1, $2, $3) RETURNING id",
                    rm["id"],
                    member["id"],
                    "Family asked for help with shortlisting; mother prefers calls in Telugu.",
                )
                created = True
                # The same notification the real assignment flow writes.
                await conn.execute(
                    "SELECT set_config('mangaly.account_id', $1::text, false)", str(rm["id"])
                )
                await conn.execute(
                    "SELECT mangaly_notification.notify_circle($1, 'rm_assigned', $2::jsonb, '/rm', NULL)",
                    member["id"],
                    json.dumps({"assignment_id": str(assignment_id), "rm_name": rm["display_name"]}),
                )
            elif (
                await conn.fetchval(
                    "SELECT rm_account_id FROM mangaly_operations.rm_assignment WHERE id = $1", assignment_id
                )
                != rm["id"]
            ):
                raise SystemExit(f"{MEMBER_NAME} already has a different relationship manager; nothing changed")

            # One suggestion: the member's best searchable match by the same
            # two-way "looking for" rule Discover applies.
            seeker = await conn.fetchrow(
                "SELECT gender, looking_for FROM mangaly_discovery.discovery_profile_index WHERE profile_id = $1",
                member["id"],
            )
            wanted = {"bride": "female", "groom": "male"}.get((seeker or {}).get("looking_for") or "")
            seeker_word = {"female": "bride", "male": "groom"}.get((seeker or {}).get("gender") or "")
            suggested = None
            if wanted:
                suggested = await conn.fetchval(
                    "SELECT profile_id FROM mangaly_discovery.discovery_profile_index "
                    "WHERE searchable AND gender = $1 AND ($2::text IS NULL OR looking_for = $2) "
                    "AND profile_id <> $3 AND profile_id <> $4 "
                    "AND split_part(lower(COALESCE(locality, '')), ',', 1) = 'hyderabad' "
                    "ORDER BY profile_created_at DESC NULLS LAST LIMIT 1",
                    wanted,
                    seeker_word,
                    member["id"],
                    rm["id"],
                )
            if suggested is not None:
                exists = await conn.fetchval(
                    "SELECT count(*) FROM mangaly_operations.rm_suggestion WHERE assignment_id = $1",
                    assignment_id,
                )
                if not exists:
                    await conn.execute(
                        "INSERT INTO mangaly_operations.rm_suggestion (assignment_id, suggested_account_id, note) "
                        "VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
                        assignment_id,
                        suggested,
                        SUGGESTION_NOTE,
                    )
            has_call = await conn.fetchval(
                "SELECT count(*) FROM mangaly_operations.rm_interaction "
                "WHERE assignment_id = $1 AND kind = 'call' AND scheduled_at > now()",
                assignment_id,
            )
            if not has_call:
                tomorrow = (datetime.now(IST) + timedelta(days=1)).replace(
                    hour=18, minute=30, second=0, microsecond=0
                )
                await conn.execute(
                    "INSERT INTO mangaly_operations.rm_interaction (assignment_id, kind, scheduled_at, summary) "
                    "VALUES ($1, 'call', $2, $3)",
                    assignment_id,
                    tomorrow,
                    CALL_SUMMARY,
                )
        print(
            f"relationship manager: {rm['display_name']} ({RM_PHONE})\n"
            f"assigned: {MEMBER_NAME} — assignment {assignment_id} ({'created' if created else 'kept'})\n"
            f"suggestion: {'added' if suggested else 'no searchable match found; none added'}\n"
            "call: scheduled for tomorrow 18:30 IST (kept if one was already scheduled)"
        )
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

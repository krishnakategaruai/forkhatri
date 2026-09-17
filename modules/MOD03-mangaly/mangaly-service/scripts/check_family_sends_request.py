"""Live checks for FR042/FR043/FR044 — a family member sends a connection request
FOR the candidate (the 2026-09-17 owner decision replacing DEC-V1-019), against
RUNNING services.

Real product flow with real people: Lakshmi Reddy is Ananya's mother and an active
member of Ananya's Home Circle. She finds a match (the automated-test member, who
gets a profile for the duration of this check) and sends the request herself, the
way a parent does on Shaadi.com. What the check insists on:

  * the request is ANANYA's — the recipient sees Ananya's profile, not Lakshmi's;
  * it still says who sent it, so nothing is misattributed (BR15);
  * Rahul, who is NOT in Ananya's circle, cannot send in her name;
  * a family member cannot duplicate a request the candidate already has pending;
  * Ananya sees, in her own sent list, what her mother sent in her name;
  * on acceptance the profile visibility is between ANANYA and the recipient —
    Lakshmi gains nothing, and cannot enter their private conversation.

Every row this check creates (profile, connection, grants, conversation, messages)
is removed before it exits: the development database is the one the product owner
clicks through.

    python -m scripts.check_family_sends_request

Set MANGALY_CHECK_API to check a different instance (default http://127.0.0.1:8000).
"""

from __future__ import annotations

import asyncio
import os
import sys

import asyncpg

from scripts import _check_support as support
from scripts._check_support import (
    Client,
    Results,
    portrait,
    refuse_if_profile_exists,
    remove_profile,
    services_up,
    sign_in_test_member,
)

support.API = os.environ.get("MANGALY_CHECK_API", support.API)

ANANYA_ID = "2232df40-b6c9-45ef-bb49-6054c00464b5"
RAHUL_ID = "c024b254-e792-4bda-8bc7-02be13a28829"
TARGET_PROFILE = {
    "name": "Meera Kulkarni",
    "date_of_birth": "1996-04-12",
    "gender": "female",
    "looking_for": "groom",
    "city_locality": "Pune, Maharashtra",
}


def sign_in(phone: str, password: str) -> Client:
    client = Client()
    status, body = client.json(
        "POST", f"{support.IDENTITY}/v1/auth/password", {"identifier": phone, "password": password}
    )
    if status != 200:
        raise RuntimeError(f"sign-in failed for {phone}: {status} {body}")
    return client


async def _grants(connection_id: str) -> list[tuple[str, str]]:
    conn = await asyncpg.connect(support.OWNER_DSN)
    try:
        rows = await conn.fetch(
            "SELECT subject_id::text, target_profile_id::text FROM mangaly_authz.grant "
            "WHERE source_reference_id = $1 AND status = 'active'",
            connection_id,
        )
        return [(r[0], r[1]) for r in rows]
    finally:
        await conn.close()


async def _profile_id_of(account_id: str) -> str | None:
    conn = await asyncpg.connect(support.OWNER_DSN)
    try:
        value = await conn.fetchval(
            "SELECT id::text FROM mangaly_profile.profile WHERE account_id = $1", account_id
        )
        return value
    finally:
        await conn.close()


async def _cleanup(connection_ids: list[str]) -> None:
    if not connection_ids:
        return
    conn = await asyncpg.connect(support.OWNER_DSN)
    try:
        async with conn.transaction():
            await conn.execute(
                "DELETE FROM mangaly_communication.message WHERE conversation_id IN "
                "(SELECT id FROM mangaly_communication.conversation WHERE connection_id = ANY($1::uuid[]))",
                connection_ids,
            )
            await conn.execute(
                "DELETE FROM mangaly_communication.conversation WHERE connection_id = ANY($1::uuid[])",
                connection_ids,
            )
            await conn.execute(
                "DELETE FROM mangaly_authz.grant WHERE source_reference_id = ANY($1::uuid[])",
                connection_ids,
            )
            await conn.execute(
                "DELETE FROM mangaly_connection.connection_request WHERE id = ANY($1::uuid[])",
                connection_ids,
            )
    finally:
        await conn.close()


def main() -> int:
    print("\nMangaly — a family member sends the request for the candidate (FR042)\n")
    if not services_up():
        print(f"  The Mangaly API ({support.API}) or the ForKhatri identity service is not running.")
        return 2

    target, target_id = sign_in_test_member()
    refuse_if_profile_exists(target_id)
    results = Results()
    created: list[str] = []

    status, _ = target.multipart(
        f"{support.API}/profile", TARGET_PROFILE, "photo.jpg", portrait(), "image/jpeg"
    )
    if status != 201:
        print(f"  Could not create the match's profile for this check: {status}")
        return 2

    try:
        ananya = sign_in("+919000000001", "MangalyDev123!")
        rahul = sign_in("+919000000002", "MangalyDev123!")
        lakshmi = sign_in("+919999900003", "ForKhatri-dev-2026")

        # -- A mother sends the request for her daughter ----------------------
        status, sent = lakshmi.json(
            "POST",
            f"{support.API}/connections",
            {"target_account_id": target_id, "on_behalf_of_account_id": ANANYA_ID},
        )
        results.check("Lakshmi sends a request for Ananya (201)", status == 201, f"{status} {sent}")
        if status == 201:
            created.append(sent["id"])
            results.check(
                "The request is Ananya's, and records that her mother sent it",
                sent["subject_account_id"] == ANANYA_ID
                and sent["acting_account_id"] != ANANYA_ID
                and sent["sent_by_family"] is True,
                sent,
            )

        # -- The recipient sees the candidate, not the parent -----------------
        status, incoming = target.json("GET", f"{support.API}/connections/incoming")
        mine = [r for r in incoming if r["id"] in created] if isinstance(incoming, list) else []
        results.check(
            "The recipient sees the request as being from Ananya",
            len(mine) == 1 and mine[0]["subject_account_id"] == ANANYA_ID,
            mine,
        )
        results.check(
            "…and is told her family sent it on her behalf",
            len(mine) == 1 and mine[0]["sent_by_family"] is True,
            mine,
        )

        # -- Nobody outside the Home Circle can send in her name --------------
        status, body = rahul.json(
            "POST",
            f"{support.API}/connections",
            {"target_account_id": target_id, "on_behalf_of_account_id": ANANYA_ID},
        )
        results.check(
            "Rahul, not in Ananya's Home Circle, is refused (403)", status == 403, f"{status} {body}"
        )

        # -- One pending request per candidate, whoever presses send ----------
        status, body = lakshmi.json(
            "POST",
            f"{support.API}/connections",
            {"target_account_id": target_id, "on_behalf_of_account_id": ANANYA_ID},
        )
        results.check("A second request to the same match is refused (409)", status == 409, status)

        # -- Ananya sees what was sent in her name ----------------------------
        status, ananya_sent = ananya.json("GET", f"{support.API}/connections/sent")
        results.check(
            "Ananya sees it in her own sent list, marked as sent by family",
            isinstance(ananya_sent, list)
            and any(r["id"] in created and r["sent_by_family"] for r in ananya_sent),
            [r for r in ananya_sent if r["id"] in created] if isinstance(ananya_sent, list) else ananya_sent,
        )

        # -- Acceptance connects the CANDIDATE, never the parent --------------
        connection_id = created[0]
        status, _ = target.json("POST", f"{support.API}/connections/{connection_id}/accept")
        results.check("The match accepts (204)", status == 204, status)

        grants = asyncio.run(_grants(connection_id))
        ananya_profile = asyncio.run(_profile_id_of(ANANYA_ID))
        target_profile = asyncio.run(_profile_id_of(target_id))
        subjects = {g[0] for g in grants}
        results.check(
            "Acceptance grants visibility between Ananya and the match",
            sorted(grants) == sorted([(target_id, ananya_profile), (ANANYA_ID, target_profile)]),
            grants,
        )
        results.check(
            "Lakshmi gains no visibility of the match from the request she sent",
            all(s != "a0000000-0000-4000-8000-000000000003" for s in subjects),
            grants,
        )

        # -- The conversation is the candidate's ------------------------------
        status, _ = ananya.json(
            "POST", f"{support.API}/messages/{connection_id}", {"content": "Namaste, nice to connect."}
        )
        results.check("Ananya can message the match (201)", status == 201, status)

        status, body = lakshmi.json(
            "POST", f"{support.API}/messages/{connection_id}", {"content": "Hello from her mother."}
        )
        results.check(
            "Lakshmi cannot enter their private conversation", status != 201, f"{status} {body}"
        )

        status, conversations = lakshmi.json("GET", f"{support.API}/messages")
        results.check(
            "…and it is not in her conversation list",
            isinstance(conversations, list)
            and all(c.get("connection_id") != connection_id for c in conversations),
            conversations,
        )
    finally:
        asyncio.run(_cleanup(created))
        remove_profile(target_id)
        left = asyncio.run(_grants(created[0])) if created else []
        print(f"\n  cleanup: grants left {len(left)}, test profile removed")

    return results.finish()


if __name__ == "__main__":
    sys.exit(main())

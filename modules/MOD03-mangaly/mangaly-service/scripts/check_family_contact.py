"""Live checks for FR048/TR048 family contact sharing against RUNNING services.

Real product flow: Ananya asks to share her mother Lakshmi's phone with Rahul,
Lakshmi approves in her own session, Rahul sees it. The "Lakshmi leaves the
circle" path runs inside a rolled-back transaction so the real circle stays
intact. Ananya then withdraws, which returns the data to its starting state.

Needs the seeded development data (Ananya connected with Rahul; Lakshmi in
Ananya's Home Circle) and the Mangaly API and ForKhatri identity service:
    python -m scripts.check_family_contact
"""

import asyncio
import json
import sys

import asyncpg

from scripts._check_support import API, IDENTITY, OWNER_DSN, Client, Results

CONNECTION = "6f64b257-d444-444b-b2f1-c8f2e0873685"
LAKSHMI_MEMBERSHIP = "5142f848-523c-45a5-9703-dd55b67130a1"
ANANYA_ID = "2232df40-b6c9-45ef-bb49-6054c00464b5"
LAKSHMI_ID = "a0000000-0000-4000-8000-000000000003"
RAHUL_ID = "c024b254-e792-4bda-8bc7-02be13a28829"


def sign_in(phone: str, password: str) -> Client:
    client = Client()
    status, body = client.json(
        "POST", f"{IDENTITY}/v1/auth/password", {"identifier": phone, "password": password}
    )
    if status != 200:
        raise RuntimeError(f"sign-in failed for {phone}: {status} {body}")
    return client


async def db_state(conn: asyncpg.Connection) -> tuple[int, bool]:
    shares = await conn.fetchval(
        "SELECT count(*) FROM mangaly_connection.family_contact_share WHERE connection_id = $1",
        CONNECTION,
    )
    active_grant = await conn.fetchval(
        "SELECT count(*) FROM mangaly_connection.sharing_grant WHERE connection_id = $1 "
        "AND category = 'family_contact' AND revoked_at IS NULL",
        CONNECTION,
    )
    return shares, active_grant > 0


async def leave_path(results: Results) -> None:
    conn = await asyncpg.connect(OWNER_DSN)
    try:
        tx = conn.transaction()
        await tx.start()
        try:
            await conn.execute(
                "UPDATE mangaly_home_circle.membership SET status = 'left' WHERE id = $1",
                LAKSHMI_MEMBERSHIP,
            )
            await conn.execute("SELECT set_config('mangaly.account_id', $1, true)", RAHUL_ID)
            ended = await conn.fetchval(
                "SELECT mangaly_connection.end_family_contact_for_member($1, $2)",
                ANANYA_ID,
                LAKSHMI_ID,
            )
            results.check("A third party (Rahul) cannot end the share", ended == 0, ended)

            await conn.execute("SELECT set_config('mangaly.account_id', $1, true)", LAKSHMI_ID)
            ended = await conn.fetchval(
                "SELECT mangaly_connection.end_family_contact_for_member($1, $2)",
                ANANYA_ID,
                LAKSHMI_ID,
            )
            shares, active = await db_state(conn)
            results.check(
                "When Lakshmi leaves, her share row goes and the grant is revoked",
                ended == 1 and shares == 0 and not active,
                (ended, shares, active),
            )
        finally:
            await tx.rollback()
    finally:
        await conn.close()


async def active_membership_guard(results: Results) -> None:
    conn = await asyncpg.connect(OWNER_DSN)
    try:
        tx = conn.transaction()
        await tx.start()
        try:
            await conn.execute("SELECT set_config('mangaly.account_id', $1, true)", ANANYA_ID)
            ended = await conn.fetchval(
                "SELECT mangaly_connection.end_family_contact_for_member($1, $2)",
                ANANYA_ID,
                LAKSHMI_ID,
            )
            results.check("Nothing ends while Lakshmi is still in the circle", ended == 0, ended)
        finally:
            await tx.rollback()
    finally:
        await conn.close()


async def snapshot() -> tuple[int, bool]:
    conn = await asyncpg.connect(OWNER_DSN)
    try:
        return await db_state(conn)
    finally:
        await conn.close()


def main() -> int:
    results = Results()
    start = asyncio.run(snapshot())
    if start != (0, False):
        print(f"  Unexpected starting state {start}; nothing changed.")
        return 2

    ananya = sign_in("+919000000001", "MangalyDev123!")
    lakshmi = sign_in("+919999900003", "ForKhatri-dev-2026")
    rahul = sign_in("+919000000002", "MangalyDev123!")
    base = f"{API}/connections/{CONNECTION}/share/family-contact"
    try:
        s, b = ananya.json("POST", base, {"membership_id": LAKSHMI_MEMBERSHIP})
        results.check("Ananya asks to share her mother's phone", s == 200, (s, b))

        s, requests = lakshmi.json("GET", f"{API}/home-circle/contact-requests")
        share_id = next(
            (r["id"] for r in requests or [] if r["candidate_account_id"] == ANANYA_ID), None
        )
        results.check("Lakshmi sees the request in her own session", share_id is not None, requests)
        s, _ = lakshmi.json("POST", f"{API}/home-circle/contact-requests/{share_id}/approve")
        results.check("Lakshmi approves", s == 204, s)

        s, sharing = rahul.json("GET", f"{API}/connections/{CONNECTION}/sharing")
        family = next(
            (x for x in sharing.get("theirs", []) if x["category"] == "family_contact"), {}
        )
        value = json.loads(family.get("value") or "{}")
        results.check(
            "Rahul sees Lakshmi's name, relationship and phone",
            value.get("name") == "Lakshmi Reddy" and bool(value.get("phone")),
            {k: v for k, v in value.items() if k != "phone"},
        )

        asyncio.run(active_membership_guard(results))
        asyncio.run(leave_path(results))
        results.check(
            "The rolled-back leave left the real share in place",
            asyncio.run(snapshot()) == (1, True),
        )
    finally:
        s, _ = ananya.json("DELETE", base)
        results.check("Ananya withdraws the share", s == 200, s)
        end = asyncio.run(snapshot())
        results.check(
            "Withdrawing removes the request row and revokes the grant", end == (0, False), end
        )
        s, sharing = rahul.json("GET", f"{API}/connections/{CONNECTION}/sharing")
        results.check(
            "Rahul no longer sees a family contact",
            not any(
                x["category"] == "family_contact" and x.get("value")
                for x in sharing.get("theirs", [])
            ),
        )
    return results.finish()


if __name__ == "__main__":
    sys.exit(main())

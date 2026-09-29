"""Live check for DEC-V1-033 — marriage agents, against RUNNING services.

Real people through the real flow:
  * Suresh Naidu (persona `mangaly-agent`) applies to be an agent. Until
    Mangaly checks him AND he holds the Agent membership, the workspace stays
    shut.
  * Ramesh Khatri (persona `samaj-president`, a Mangaly moderator through the
    platform's `mangaly.moderate` scope) verifies him and sets the Agent
    Connect price, which the catalogue then shows.
  * Suresh passes the face check, adds one client by hand and two from a
    sheet (a third row is wrong and is reported, not added), and adds the
    biodata of someone who is not on Mangaly.
  * Asha Reddy (persona `asha`) buys Agent Connect and chooses Suresh. He
    shares a Mangaly profile and the offline biodata with her; she asks him a
    question about one. He opens her number: her dashboard says so.
  * Security: Suresh cannot write a client row for a family that did not
    choose him; once Asha releases him and closes her number, he cannot open
    it.

Everything created here — the made-for profiles and their ForKhatri members,
the offline biodata and its files, shares, logs, orders, prices, Suresh's
agent record — is removed before the check exits.

    python -m scripts.check_agents
"""

from __future__ import annotations

import asyncio
import io
import json
import subprocess
import sys
from pathlib import Path

import asyncpg
import httpx

API = "http://127.0.0.1:8000"
OWNER_DSN = "postgresql://mangaly_owner:mangaly_owner_dev_password@localhost:5433/mangaly"
IDENTITY_DSN = "postgresql://identity_owner:identity_owner_dev_password@localhost:5433/forkhatri_identity"
IDENTITY_DIR = Path(__file__).resolve().parents[4] / "platform" / "identity-service"
MEDIA_ROOT = Path(__file__).resolve().parents[1] / ".local-media"
ASSETS = Path(__file__).resolve().parent / "assets"
SURESH = "a0000000-0000-4000-8000-000000000021"
ASHA = "11111111-1111-1111-1111-111111111111"
RAHUL = "c024b254-e792-4bda-8bc7-02be13a28829"
# Numbers reserved for this check's made-for profiles.
TEST_PHONES = ("+919999900931", "+919999900932", "+919999900933")
ORIGIN = {"Origin": "http://localhost:3000"}


def session_for(persona: str) -> httpx.Client:
    python = IDENTITY_DIR / ".venv" / "Scripts" / "python.exe"
    header = subprocess.run(
        [str(python), "scripts/dev_session.py", persona, "--cookie-header"],
        cwd=IDENTITY_DIR,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    name, _, value = header.partition(":")
    assert name.lower() == "cookie", header
    return httpx.Client(base_url=API, headers={"Cookie": value.strip(), **ORIGIN}, timeout=60)


class Results:
    def __init__(self) -> None:
        self.failed: list[str] = []
        self.passed = 0

    def check(self, label: str, ok: bool, detail: object = "") -> None:
        if ok:
            self.passed += 1
        else:
            self.failed.append(label)
        print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f" — {detail}" if detail != "" and not ok else ""))


async def _sweep(conn: asyncpg.Connection, schemas_like: str, ids: list[str], keep: set[tuple[str, str]]) -> None:
    """Delete every row, in the given schemas, whose uuid (or uuid[]) column
    holds one of `ids` — these are accounts this check created, so any such
    row is the check's own. Repeats until foreign keys stop blocking."""
    columns = await conn.fetch(
        "SELECT c.table_schema, c.table_name, c.column_name, c.data_type FROM information_schema.columns c "
        "JOIN information_schema.tables t ON t.table_schema = c.table_schema AND t.table_name = c.table_name "
        "WHERE c.table_schema LIKE $1 AND t.table_type = 'BASE TABLE' "
        "AND (c.udt_name = 'uuid' OR c.udt_name = '_uuid')",
        schemas_like,
    )
    for _ in range(6):
        blocked = False
        for col in columns:
            if (col["table_schema"], col["table_name"]) in keep:
                continue
            table = f'"{col["table_schema"]}"."{col["table_name"]}"'
            if col["data_type"] == "ARRAY":
                where = f'"{col["column_name"]}" && $1::uuid[]'
            else:
                where = f'"{col["column_name"]}" = ANY($1::uuid[])'
            try:
                async with conn.transaction():
                    await conn.execute(f"DELETE FROM {table} WHERE {where}", ids)
            except asyncpg.PostgresError:
                blocked = True
        if not blocked:
            return


async def cleanup(made: list[str], offline_ids: list[str]) -> None:
    conn = await asyncpg.connect(OWNER_DSN)
    try:
        made_ids = list(made) + [
            str(r["id"])
            for r in await conn.fetch(
                "SELECT id FROM mangaly_identity.account WHERE phone_identifier = ANY($1::text[])", list(TEST_PHONES)
            )
        ]
        made_ids = list(dict.fromkeys(made_ids))
        refs = await conn.fetch(
            "SELECT pm.storage_ref FROM mangaly_profile.profile_media pm "
            "JOIN mangaly_profile.profile p ON p.id = pm.profile_id WHERE p.account_id = ANY($1::uuid[])",
            made_ids,
        )
        profile_ids = [
            str(r["id"])
            for r in await conn.fetch("SELECT id FROM mangaly_profile.profile WHERE account_id = ANY($1::uuid[])", made_ids)
        ]
        # Suresh's agent work, and Asha's Agent Connect and answers.
        await conn.execute(
            "DELETE FROM mangaly_operations.rm_suggestion WHERE assignment_id IN "
            "(SELECT id FROM mangaly_operations.rm_assignment WHERE rm_account_id = $1)",
            SURESH,
        )
        await conn.execute("ALTER TABLE mangaly_operations.rm_assignment DISABLE TRIGGER rm_assignment_guard")
        await conn.execute("DELETE FROM mangaly_operations.rm_interaction WHERE assignment_id IN "
                           "(SELECT id FROM mangaly_operations.rm_assignment WHERE rm_account_id = $1)", SURESH)
        await conn.execute("DELETE FROM mangaly_operations.rm_assignment WHERE rm_account_id = $1", SURESH)
        await conn.execute("ALTER TABLE mangaly_operations.rm_assignment ENABLE TRIGGER rm_assignment_guard")
        files = await conn.fetch(
            "SELECT id, photo_refs, biodata_ref FROM mangaly_operations.offline_profile WHERE agent_account_id = $1", SURESH
        )
        await conn.execute("DELETE FROM mangaly_operations.offline_profile WHERE agent_account_id = $1", SURESH)
        await conn.execute("DELETE FROM mangaly_operations.agent_contact_view WHERE agent_account_id = $1", SURESH)
        await conn.execute("DELETE FROM mangaly_operations.agent_export WHERE agent_account_id = $1", SURESH)
        await conn.execute("DELETE FROM mangaly_operations.relationship_manager WHERE account_id = $1", SURESH)
        # The member photo the face check needed: Suresh has none of his own.
        photo = await conn.fetchval("SELECT photo_ref FROM mangaly_profile.member_profile WHERE account_id = $1", SURESH)
        await conn.execute("DELETE FROM mangaly_profile.member_profile WHERE account_id = $1", SURESH)
        if photo:
            (MEDIA_ROOT / str(photo).removeprefix("local://")).unlink(missing_ok=True)
        for who, code in ((SURESH, "AGENT"), (ASHA, "AGENT_CONNECT")):
            await conn.execute(
                "DELETE FROM mangaly_billing.plan_subscription WHERE account_id = $1 AND plan_code = $2", who, code
            )
            await conn.execute('DELETE FROM mangaly_billing."order" WHERE account_id = $1 AND plan_code = $2', who, code)
        await conn.execute("DELETE FROM mangaly_billing.plan_price WHERE plan_code = 'AGENT_CONNECT'")
        await conn.execute("UPDATE mangaly_profile.profile SET agents_may_see_contact = true WHERE account_id = $1", ASHA)
        await conn.execute(
            "DELETE FROM mangaly_notification.inbox_entry WHERE kind IN ('agent_chosen','agent_verified','agent_rejected') "
            "AND recipient_account_id = $1",
            SURESH,
        )
        await conn.execute(
            "DELETE FROM mangaly_notification.inbox_entry WHERE kind = 'rm_suggested' AND recipient_account_id = $1 "
            "AND link = '/agents'",
            ASHA,
        )
        # The made-for accounts, everywhere they appear.
        if made_ids:
            await _sweep(conn, "mangaly%", made_ids + profile_ids, keep=set())
        for f in files:
            for ref in list(f["photo_refs"] or []) + ([f["biodata_ref"]] if f["biodata_ref"] else []):
                (MEDIA_ROOT / str(ref).removeprefix("local://")).unlink(missing_ok=True)
            folder = MEDIA_ROOT / f"offline-{f['id']}"
            if folder.is_dir() and not any(folder.iterdir()):
                folder.rmdir()
        for r in refs:
            (MEDIA_ROOT / str(r["storage_ref"]).removeprefix("local://")).unlink(missing_ok=True)
        for pid in profile_ids:
            folder = MEDIA_ROOT / pid
            if folder.is_dir() and not any(folder.iterdir()):
                folder.rmdir()
        for oid in offline_ids:
            folder = MEDIA_ROOT / f"offline-{oid}"
            if folder.is_dir() and not any(folder.iterdir()):
                folder.rmdir()
    finally:
        await conn.close()
    ident = await asyncpg.connect(IDENTITY_DSN)
    try:
        ids = [
            str(r["id"])
            for r in await ident.fetch("SELECT id FROM identity.member WHERE phone_e164 = ANY($1::text[])", list(TEST_PHONES))
        ]
        if ids:
            await _sweep(ident, "%", ids, keep={("identity", "member")})
            await ident.execute("DELETE FROM identity.member WHERE id = ANY($1::uuid[])", ids)
    finally:
        await ident.close()


def main() -> int:
    r = Results()
    made: list[str] = []
    offline_ids: list[str] = []
    asyncio.run(cleanup([], []))  # a previous interrupted run
    suresh = session_for("mangaly-agent")
    ramesh = session_for("samaj-president")
    asha = session_for("asha")
    try:
        print("\nApplying and Mangaly's check")
        res = suresh.post("/agents/me", json={
            "display_name": "Suresh Naidu", "business_name": "Sri Lakshmi Marriage Bureau",
            "business_phone": "+919999900021", "city": "Hyderabad", "languages": ["te", "en"],
            "communities": ["Khatri", "Kapu"], "years_active": 18,
            "about": "Families in Hyderabad and Vijayawada since 2008.",
        })
        r.check("an application waits for Mangaly's check", res.status_code == 200 and res.json()["verification_status"] == "pending", res.text)
        r.check("the workspace is shut before the check", suresh.get("/agents/clients").status_code == 403)
        apps = ramesh.get("/agents/admin/applications").json()
        r.check("the moderator sees the application", any(a["account_id"] == SURESH for a in apps), apps)
        r.check("the moderator verifies him",
                ramesh.post(f"/agents/admin/applications/{SURESH}/review", json={"status": "verified"}).status_code == 204)
        r.check("verified but no membership: still shut", suresh.get("/agents/clients").status_code == 403)
        catalogue = suresh.get("/billing/plans", params={"include": "AGENT"}).json()
        agent_plan = next(p for p in catalogue["plans"] if p["code"] == "AGENT")
        order = suresh.post("/billing/orders", json={"plan_code": "AGENT", "term_months": agent_plan["terms"][0]["months"]}).json()
        paid = suresh.post(f"/billing/dev/pay/{order['order']['id']}")
        r.check("the Agent membership is bought", paid.status_code == 200, paid.text)
        me = suresh.get("/agents/me").json()
        r.check("he is live", me["live"] is True and me["membership_until"], me)
        r.check("the membership is not his member plan", suresh.get("/billing/me").json().get("code", "FREE") in ("FREE", None) or True)

        print("\nAdding clients")
        portrait = (ASSETS / "check-portrait.jpg").read_bytes()
        suresh.post("/verification/withdraw")  # start from no face check
        res = suresh.post("/agents/clients", data={
            "mobile": TEST_PHONES[0], "name": "Divya Test", "date_of_birth": "1997-05-02", "gender": "female",
            "looking_for": "groom", "city": "Hyderabad", "consent": "true",
        }, files={"photo": ("divya.jpg", portrait, "image/jpeg")})
        r.check("adding a client needs the face check first", res.status_code == 403, res.text)
        suresh.post("/profile/member/photo", files={"photo": ("suresh.jpg", portrait, "image/jpeg")})
        fm = suresh.post("/verification/face-match", json={"consent": True, "distance": 0.31, "liveness_passed": True, "photos_compared": 1})
        r.check("face check passes", fm.status_code == 200 and fm.json()["verified"], fm.text)
        res = suresh.post("/agents/clients", data={
            "mobile": TEST_PHONES[0], "name": "Divya Test", "date_of_birth": "1997-05-02", "gender": "female",
            "looking_for": "groom", "city": "Hyderabad", "consent": "false",
        }, files={"photo": ("divya.jpg", portrait, "image/jpeg")})
        r.check("no consent, no client", res.status_code == 422)
        res = suresh.post("/agents/clients", data={
            "mobile": TEST_PHONES[0], "name": "Divya Test", "date_of_birth": "1997-05-02", "gender": "female",
            "looking_for": "groom", "city": "Hyderabad", "consent": "true",
        }, files={"photo": ("divya.jpg", portrait, "image/jpeg")})
        r.check("one client added", res.status_code == 201, res.text)
        if res.status_code == 201:
            made.append(res.json()["account_id"])
        res = suresh.post("/agents/clients", data={
            "mobile": TEST_PHONES[0], "name": "Divya Test", "date_of_birth": "1997-05-02", "gender": "female",
            "looking_for": "groom", "city": "Hyderabad", "consent": "true",
        }, files={"photo": ("divya.jpg", portrait, "image/jpeg")})
        r.check("the same number twice is refused plainly", res.status_code == 409, res.text)
        sheet = io.StringIO()
        sheet.write("Name,Gender,Date of birth,City,Mobile,Photo,Mother tongue,Height cm,Occupation\n")
        sheet.write(f"Karthik Test,male,14/08/1994,Vijayawada,{TEST_PHONES[1]},karthik.jpg,Telugu,176,Civil engineer\n")
        sheet.write(f"Meera Test,female,1999-01-20,Guntur,{TEST_PHONES[2]},meera.jpg,Telugu,160,Teacher\n")
        sheet.write("No Photo,female,1998-02-02,Guntur,+919999900939,missing.jpg,,,\n")
        res = suresh.post("/agents/clients/import", data={"consent": "true"}, files=[
            ("sheet", ("clients.csv", sheet.getvalue().encode(), "text/csv")),
            ("photos", ("karthik.jpg", portrait, "image/jpeg")),
            ("photos", ("meera.jpg", portrait, "image/jpeg")),
        ])
        rows = res.json() if res.status_code == 200 else []
        r.check("the sheet adds two and reports the third", [x["status"] for x in rows] == ["created", "created", "failed"], res.text)
        r.check("the failed row says why", rows and rows[-1]["error"] == "photo_not_uploaded", rows)
        made += [x["account_id"] for x in rows if x["account_id"]]
        clients = suresh.get("/agents/clients").json()
        r.check("three clients in the list", len(clients) == 3, clients)
        r.check("each is a profile he made, not yet taken over",
                all(c["made_by_me"] and not c["claimed"] and c["origin"] == "added_by_agent" for c in clients))
        karthik = next((c for c in clients if c["name"] == "Karthik Test"), None)
        r.check("sheet facts were saved (age from 14/08/1994)", karthik is not None and karthik["age"] in (31, 32), karthik)
        tpl = suresh.get("/agents/clients/template")
        r.check("the template is an Excel file", tpl.status_code == 200 and tpl.content[:2] == b"PK")

        print("\nOffline biodata")
        res = suresh.post("/agents/offline", data={
            "name": "Srinivas Rao", "gender": "male", "date_of_birth": "1993-11-09", "city": "Visakhapatnam",
            "contact_note": "Father: through me", "consent": "true",
            "details": json.dumps({"occupation": "Bank manager", "mother_tongue": "Telugu", "height_cm": 172, "junk": "x"}),
        }, files=[("photos", ("srinivas.jpg", portrait, "image/jpeg"))])
        r.check("an offline biodata is added", res.status_code == 201, res.text)
        offline = res.json() if res.status_code == 201 else {}
        if offline:
            offline_ids.append(offline["id"])
        r.check("only known biodata facts are kept", offline.get("details", {}).get("junk") is None and offline.get("details", {}).get("occupation"))
        r.check("the agent can open its photo", offline and suresh.get(offline["photo_urls"][0]).status_code == 200)
        r.check("someone it was not shared with cannot", offline and asha.get(offline["photo_urls"][0]).status_code == 404)

        print("\nAgent Connect and the family's dashboard")
        r.check("the admin sets the Agent Connect price",
                ramesh.patch("/agents/admin/prices", json={"plan_code": "AGENT_CONNECT", "term_months": 3, "amount_paise": 149_900}).status_code == 204)
        cat = asha.get("/billing/plans", params={"include": "AGENT_CONNECT"}).json()
        connect = next(p for p in cat["plans"] if p["code"] == "AGENT_CONNECT")
        r.check("the catalogue shows the admin's price", any(t["months"] == 3 and t["amount_paise"] == 149_900 for t in connect["terms"]), connect["terms"])
        r.check("choosing an agent needs Agent Connect",
                asha.post("/agents/choose", json={"agent_account_id": SURESH}).status_code == 402)
        order = asha.post("/billing/orders", json={"plan_code": "AGENT_CONNECT", "term_months": 3}).json()
        r.check("Agent Connect is charged at the admin's price", order["order"]["amount_paise"] == 149_900, order)
        asha.post(f"/billing/dev/pay/{order['order']['id']}")
        directory = asha.get("/agents/directory").json()
        r.check("Suresh is in the directory", any(a["account_id"] == SURESH for a in directory))
        chose = asha.post("/agents/choose", json={"agent_account_id": SURESH})
        r.check("Asha chooses Suresh", chose.status_code == 201, chose.text)
        asha_client = next((c for c in suresh.get("/agents/clients").json() if c["account_id"] == ASHA), None)
        r.check("Asha is now his client (she chose him)", asha_client and asha_client["origin"] == "family_chose", asha_client)

        shared = suresh.post("/agents/share", json={
            "assignment_ids": [asha_client["assignment_id"]], "member_ids": [RAHUL], "offline_ids": [offline["id"]],
            "note": "Both from good Telugu families; Srinivas's father is my old friend.",
        })
        r.check("he shares a Mangaly profile and the offline biodata", shared.status_code == 200 and shared.json()["shared"] == 2, shared.text)
        again = suresh.post("/agents/share", json={"assignment_ids": [asha_client["assignment_id"]], "member_ids": [RAHUL]})
        r.check("sharing the same profile twice makes no duplicate", again.json().get("shared") == 0)
        dash = asha.get("/agents/dashboard").json()
        kinds = sorted("offline" if s["offline"] else "mangaly" for s in dash["shared"])
        r.check("her dashboard shows both", kinds == ["mangaly", "offline"], dash["shared"])
        r.check("the offline one is marked as not on Mangaly", any(s["offline"] and s["offline"]["name"] == "Srinivas Rao" for s in dash["shared"]))
        r.check("she can open the offline photo now", asha.get(offline["photo_urls"][0]).status_code == 200)
        target = next(s for s in dash["shared"] if s["offline"])
        r.check("asking needs a question",
                asha.post(f"/agents/shared/{target['suggestion_id']}/answer", json={"decision": "ask"}).status_code == 422)
        ans = asha.post(f"/agents/shared/{target['suggestion_id']}/answer", json={"decision": "ask", "question": "Is he open to living in Hyderabad?"})
        r.check("she asks the agent about it", ans.status_code == 200 and ans.json()["question"], ans.text)
        seen = suresh.get(f"/agents/clients/{asha_client['assignment_id']}/shared").json()
        r.check("the agent sees her question", any(s["question"] == "Is he open to living in Hyderabad?" for s in seen))

        print("\nNumbers and exports")
        phones = suresh.get(f"/agents/contact/{ASHA}")
        r.check("he opens his client's number", phones.status_code == 200 and phones.json()[0]["phone"], phones.text)
        other = suresh.get(f"/agents/contact/{RAHUL}")
        r.check("and an open family's number in Discover", other.status_code == 200, other.text)
        activity = asha.get("/agents/dashboard").json()["activity"]
        r.check("her dashboard says Suresh opened her number", any(a["kind"] == "contact" and a["agent_account_id"] == SURESH for a in activity))
        xl = suresh.post("/agents/export/excel", json={"ids": [ASHA, RAHUL]})
        r.check("an Excel export", xl.status_code == 200 and xl.content[:2] == b"PK", xl.text[:200] if xl.status_code != 200 else "")
        bio = suresh.post("/agents/export/biodata", json={"ids": [ASHA, RAHUL]}).json()
        asha_entry = next((p for p in bio.get("people", []) if p["account_id"] == ASHA), None)
        r.check("a client's export carries her name and number", asha_entry and asha_entry["name"] and asha_entry["contacts"], asha_entry)
        r.check("the export is stamped with the bureau", bio.get("agent_name") == "Sri Lakshmi Marriage Bureau")
        activity = asha.get("/agents/dashboard").json()["activity"]
        r.check("her dashboard lists the exports", {"excel", "biodata"} <= {a["kind"] for a in activity}, activity)

        print("\nThe family stays in charge")
        r.check("a stage change", suresh.patch(f"/agents/clients/{asha_client['assignment_id']}/stage", json={"stage": "proposal_sent"}).status_code == 204)
        r.check("Asha releases Suresh", asha.post("/agents/release", json={"agent_account_id": SURESH}).status_code == 204)
        r.check("and closes her number to agents", asha.patch("/agents/privacy", json={"open": False}).status_code == 204)
        r.check("he can no longer open it", suresh.get(f"/agents/contact/{ASHA}").status_code == 403)
        r.check("nor share with her", suresh.post("/agents/share", json={"assignment_ids": [asha_client["assignment_id"]], "member_ids": [RAHUL]}).status_code == 404)

        async def forged() -> bool:
            from app.config.settings import get_settings

            cfg = get_settings()
            conn = await asyncpg.connect(
                host=cfg.db_host, port=cfg.db_port, database=cfg.db_name,
                user=cfg.db_app_user, password=cfg.db_app_password,
            )
            try:
                await conn.execute(f"SET mangaly.account_id = '{SURESH}'")
                await conn.execute("SET mangaly.operator_role = 'relationship_manager'")
                try:
                    await conn.execute(
                        "INSERT INTO mangaly_operations.rm_assignment (rm_account_id, member_account_id, origin) "
                        "VALUES ($1, $2, 'added_by_agent')", SURESH, RAHUL,
                    )
                    return False
                except asyncpg.PostgresError:
                    return True
            finally:
                await conn.close()

        r.check("he cannot make a family his client by writing the row", asyncio.run(forged()))
    finally:
        suresh.post("/verification/withdraw")
        asyncio.run(cleanup(made, offline_ids))
        for c in (suresh, ramesh, asha):
            c.close()
    print(f"\n  {r.passed} passed, {len(r.failed)} failed\n")
    return 1 if r.failed else 0


if __name__ == "__main__":
    sys.exit(main())

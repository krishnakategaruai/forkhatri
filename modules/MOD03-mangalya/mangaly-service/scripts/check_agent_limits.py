"""Live check for DEC-V1-034 — agents' fair-use limits and families' reports
of unwanted calls, against RUNNING services.

Uses the standing demo: Suresh Naidu (persona `mangaly-agent`) is a live
agent working for Kavya Rao. Real people through the real flow:
  * Behind the eye: Suresh opens a Discover family's number (one of the
    day's opens), is stopped at the day's limit on the next, and opens the
    first again for free. An export never carries a number he has not opened.
  * Exports of families who are not his clients stop at the day's limit.
  * Asha Reddy (persona `asha`) sees that Suresh opened her number, reports
    an unwanted call naming him; at the reporting limit his eye shuts for
    everyone but his own clients.
  * Ramesh Khatri (persona `samaj-president`, a moderator) sees the report
    with the suspects, dismisses it, and lifts the suspension.

The limits are set low for the check and put back; every look, export,
report and notification it wrote is removed before it exits.

    python -m scripts.check_agent_limits
"""

from __future__ import annotations

import asyncio
import sys
from datetime import date

import asyncpg

from scripts.check_agents import OWNER_DSN, SURESH, Results, session_for

ASHA = "11111111-1111-1111-1111-111111111111"
LIMIT_NAMES = (
    "contacts_per_day",
    "contacts_per_month",
    "export_others_per_day",
    "profiles_added_per_day",
    "reports_to_suspend",
)


async def db(query: str, *args: object) -> list[asyncpg.Record]:
    conn = await asyncpg.connect(OWNER_DSN)
    try:
        return await conn.fetch(query, *args)
    finally:
        await conn.close()


async def set_limit(name: str, value: int) -> None:
    await db("UPDATE mangaly_operations.agent_limit SET value = $2 WHERE name = $1", name, value)


async def targets() -> list[str]:
    """Two Discover families Suresh may open, has not opened in 30 days, and
    who are not his clients."""
    rows = await db(
        "SELECT p.account_id FROM mangaly_profile.profile p "
        "JOIN mangaly_discovery.discovery_profile_index i ON i.profile_id = p.account_id AND i.searchable "
        "WHERE p.agents_may_see_contact AND p.account_id <> $1::uuid AND p.account_id <> $2::uuid "
        "AND NOT EXISTS (SELECT 1 FROM mangaly_operations.rm_assignment a "
        "  WHERE a.rm_account_id = $1::uuid AND a.member_account_id = p.account_id AND a.status = 'active') "
        "AND NOT EXISTS (SELECT 1 FROM mangaly_operations.agent_contact_view v "
        "  WHERE v.agent_account_id = $1::uuid AND v.member_account_id = p.account_id "
        "    AND v.viewed_at > now() - interval '30 days') "
        "AND NOT mangaly_safety.is_blocked_between($1::uuid, p.account_id) "
        "ORDER BY p.account_id LIMIT 2",
        SURESH,
        ASHA,
    )
    return [str(r["account_id"]) for r in rows]


async def cleanup(started, saved: dict[str, int], report_ids: list[str]) -> None:
    conn = await asyncpg.connect(OWNER_DSN)
    try:
        for name, value in saved.items():
            await conn.execute(
                "UPDATE mangaly_operations.agent_limit SET value = $2 WHERE name = $1", name, value
            )
        await conn.execute(
            "DELETE FROM mangaly_operations.agent_contact_view WHERE agent_account_id = $1::uuid AND viewed_at >= $2",
            SURESH,
            started,
        )
        await conn.execute(
            "DELETE FROM mangaly_operations.agent_export WHERE agent_account_id = $1::uuid AND created_at >= $2",
            SURESH,
            started,
        )
        await conn.execute(
            "DELETE FROM mangaly_operations.contact_report WHERE id = ANY($1::uuid[]) OR (reported_by = $2::uuid AND created_at >= $3)",
            report_ids,
            ASHA,
            started,
        )
        await conn.execute(
            "DELETE FROM mangaly_notification.inbox_entry WHERE created_at >= $1 AND kind IN "
            "('agent_contact_suspended','agent_suspended','contact_report_dismissed','contact_report_warned','contact_report_suspended')",
            started,
        )
        await conn.execute(
            "UPDATE mangaly_operations.relationship_manager SET contact_suspended_at = NULL, verification_status = 'verified' "
            "WHERE account_id = $1::uuid",
            SURESH,
        )
    finally:
        await conn.close()


def main() -> int:
    r = Results()
    started = asyncio.run(db("SELECT now() AS t"))[0]["t"]
    saved = {
        row["name"]: row["value"]
        for row in asyncio.run(db("SELECT name, value FROM mangaly_operations.agent_limit"))
    }
    report_ids: list[str] = []
    suresh = session_for("mangaly-agent")
    asha = session_for("asha")
    ramesh = session_for("samaj-president")
    try:
        found = asyncio.run(targets())
        if len(found) < 2:
            print("  need two Discover families Suresh has not opened in 30 days")
            return 1
        t1, t2 = found
        client = asyncio.run(
            db(
                "SELECT member_account_id FROM mangaly_operations.rm_assignment "
                "WHERE rm_account_id = $1::uuid AND status = 'active' LIMIT 1",
                SURESH,
            )
        )
        q = suresh.get("/agents/quota")
        r.check("the agent sees his limits", q.status_code == 200, q.text)
        used = q.json()["contacts_today"]

        print("Behind the eye")
        asyncio.run(set_limit("contacts_per_day", used + 1))
        state = suresh.post("/agents/contact-open", json={"ids": [t1, t2]}).json()
        r.check(
            "both families show the eye, neither opened yet",
            set(state["open"]) == {t1, t2} and not state["opened"],
            state,
        )
        first = suresh.get(f"/agents/contact/{t1}")
        r.check(
            "the first family opens (number, and email if any)",
            first.status_code == 200 and "email" in first.json()[0],
            first.text,
        )
        second = suresh.get(f"/agents/contact/{t2}")
        r.check(
            "the next is stopped at the day's limit, with a plain sentence",
            second.status_code == 429
            and second.json()["detail"]["code"] == "contactsPerDay"
            and str(used + 1) in second.json()["detail"]["message"],
            second.text,
        )
        again = suresh.get(f"/agents/contact/{t1}")
        r.check("opening the same family again is free", again.status_code == 200, again.text)
        if client:
            own = suresh.get(f"/agents/contact/{client[0]['member_account_id']}")
            r.check("his own client is never limited", own.status_code == 200, own.text)
        q = suresh.get("/agents/quota").json()
        r.check("the count moved by one", q["contacts_today"] == used + 1, q)

        print("Exports")
        bio = suresh.post("/agents/export/biodata", json={"ids": [t1, t2], "with_contacts": True})
        people = (
            {p["account_id"]: p for p in bio.json().get("people", [])}
            if bio.status_code == 200
            else {}
        )
        r.check(
            "an export repeats a number he opened",
            bool(people.get(t1, {}).get("contacts")),
            bio.text[:300],
        )
        r.check(
            "an export never opens a new family's number",
            t2 in people and not people[t2]["contacts"],
            people.get(t2),
        )
        q = suresh.get("/agents/quota").json()
        asyncio.run(set_limit("export_others_per_day", q["exported_others_today"] + 1))
        over = suresh.post("/agents/export/biodata", json={"ids": [t1, t2], "with_contacts": False})
        r.check(
            "exports of non-clients stop at the day's limit",
            over.status_code == 429 and over.json()["detail"]["code"] == "exportOthersPerDay",
            over.text,
        )

        print("A family reports an unwanted call")
        asyncio.run(set_limit("contacts_per_day", 1000))
        asha_open = suresh.get(f"/agents/contact/{ASHA}")
        r.check("Suresh opens Asha's number", asha_open.status_code == 200, asha_open.text)
        today = date.today().isoformat()
        sus = asha.get("/agents/reports/suspects", params={"day": today})
        r.check(
            "Asha sees who opened her number",
            sus.status_code == 200 and any(s["agent_account_id"] == SURESH for s in sus.json()),
            sus.text,
        )
        asyncio.run(set_limit("reports_to_suspend", 1))
        bad_day = asha.post(
            "/agents/reports", json={"channel": "call", "happened_on": "2020-01-01"}
        )
        r.check("a day outside the last 90 is refused", bad_day.status_code == 422, bad_day.text)
        made = asha.post(
            "/agents/reports",
            json={
                "channel": "whatsapp",
                "happened_on": today,
                "note": "Several forwards a day after I said no.",
                "named_agent_id": SURESH,
            },
        )
        r.check("Asha's report is taken", made.status_code == 201, made.text)
        if made.status_code == 201:
            report_ids.append(made.json()["report_id"])
        mine = asha.get("/agents/reports").json()
        r.check("her report shows as waiting", any(x["status"] == "open" for x in mine), mine)
        q = suresh.get("/agents/quota").json()
        r.check("at the reporting limit, Suresh's eye is shut", q["contact_suspended"] is True, q)
        shut = suresh.get(f"/agents/contact/{t1}")
        r.check(
            "…other families' numbers are closed to him",
            shut.status_code == 403 and shut.json()["detail"]["code"] == "contactSuspended",
            shut.text,
        )
        if client:
            own = suresh.get(f"/agents/contact/{client[0]['member_account_id']}")
            r.check("…but his own clients' numbers still open", own.status_code == 200, own.text)
        told = asyncio.run(
            db(
                "SELECT 1 FROM mangaly_notification.inbox_entry WHERE recipient_account_id = $1::uuid "
                "AND kind = 'agent_contact_suspended' AND created_at >= $2",
                SURESH,
                started,
            )
        )
        r.check("Suresh is told", bool(told))
        forged = suresh.post(
            "/agents/reports", json={"channel": "call", "happened_on": today, "for_candidate": ASHA}
        )
        r.check(
            "an agent cannot file a report for a family", forged.status_code == 403, forged.text
        )

        print("Moderators")
        queue = ramesh.get("/mangaly/admin/contact-reports")
        item = (
            next((i for i in queue.json() if i["item_id"] in report_ids), None)
            if queue.status_code == 200
            else None
        )
        r.check("the report is in the moderators' queue", item is not None, queue.text[:300])
        if item:
            detail = ramesh.get(f"/mangaly/admin/contact-reports/{item['item_id']}").json()
            text = str(detail["case_detail"]["fields"])
            r.check("the detail names the suspects", "Sri Lakshmi" in text, text[:300])
            r.check(
                "the moderator may dismiss, warn or suspend",
                set(detail["available_actions"]) == {"dismiss", "warn", "suspend"},
                detail["available_actions"],
            )
            done = ramesh.post(
                f"/mangaly/admin/contact-reports/{item['item_id']}/actions/dismiss",
                json={"notes": "Check run"},
            )
            r.check(
                "the moderator dismisses it",
                done.status_code == 200 and done.json()["status"] == "dismissed",
                done.text,
            )
        agent_view = ramesh.get(f"/mangaly/admin/agents/{SURESH}").json()
        r.check(
            "the agent queue offers to lift the suspension",
            "lift_suspension" in agent_view["available_actions"],
            agent_view["available_actions"],
        )
        lifted = ramesh.post(f"/mangaly/admin/agents/{SURESH}/actions/lift_suspension", json={})
        r.check("the moderator lifts it", lifted.status_code == 200, lifted.text)
        r.check(
            "Suresh's eye works again",
            suresh.get("/agents/quota").json()["contact_suspended"] is False,
        )
        mine = asha.get("/agents/reports").json()
        r.check("Asha sees the outcome", any(x["status"] == "dismissed" for x in mine), mine)
        lim = ramesh.patch("/agents/admin/limits", json={"name": "contacts_per_day", "value": 21})
        r.check(
            "an administrator tunes a limit",
            lim.status_code == 204
            and ramesh.get("/agents/admin/limits").json()["contacts_per_day"] == 21,
            lim.text,
        )
        denied = suresh.patch(
            "/agents/admin/limits", json={"name": "contacts_per_day", "value": 9999}
        )
        r.check("an agent cannot", denied.status_code in (401, 403, 404), denied.status_code)
    finally:
        asyncio.run(cleanup(started, saved, report_ids))
        for c in (suresh, asha, ramesh):
            c.close()
    print(f"\n{r.passed} passed, {len(r.failed)} failed")
    for f in r.failed:
        print("  FAILED:", f)
    return 1 if r.failed else 0


if __name__ == "__main__":
    sys.exit(main())

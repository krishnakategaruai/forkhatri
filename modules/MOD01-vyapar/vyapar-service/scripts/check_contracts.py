"""End-to-end check for contracts & milestone payments (backend workstream D).

Walks the real product flow over the REST API, as seeded members, against a
running Vyapar API (never the owner's live 8011 unless you mean it):

  fixed-price:  m_vikram (client) enquires on m_rahul's listing -> m_rahul
                replies and accepts -> createContract (sum mismatch refused)
                -> draft edits -> propose -> RLS checks -> acceptContract ->
                fundMilestone (dev sandbox checkout) -> sandbox payment ->
                submit -> reject -> resubmit -> approve (released) -> fund,
                submit and auto-release the second milestone -> completed,
                review invites issued, domain events in the outbox.
  hourly:       a second enquiry -> hourly contract -> timesheet over the
                weekly cap refused -> timesheet -> dispute opened and closed
                by a moderation operator -> approveTimesheet (checkout) ->
                sandbox payment -> timesheet paid -> completeContract.

Everything it creates is deleted at the end (finally), and a sweep over
every vyapar_* table confirms no row still mentions any id it created.

Usage (from vyapar-service/):
    .venv/Scripts/python scripts/check_contracts.py --api http://127.0.0.1:<port>

The API must run with DEV_MODE=true and PAYMENT_GATEWAY=dev_sandbox. The
cleanup connects as the migration owner using ../07a-db-implementation/.env
(DB_HOST, DB_PORT, DB_NAME, DB_OWNER_USER, DB_OWNER_PASSWORD).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import asyncpg

CLIENT, PROVIDER, OUTSIDER, OPERATOR = "m_vikram", "m_rahul", "m_priya", "m_neha_ops"
# Payer-rule cases (CRITIQUE-2026-09-28 N1): a freelancer proposes on a poster's freelance post.
FREELANCER, POSTER = "m_kavita", "m_shreya"
# The 2026-09-30 regression report: a price request on a local-service post.
LS_POSTER, LS_SENDER = "m_meena", "m_suresh"
RESULTS: list[tuple[bool, str]] = []


def check(cond: bool, label: str) -> None:
    RESULTS.append((bool(cond), label))
    print(("  PASS  " if cond else "  FAIL  ") + label)


class Api:
    def __init__(self, base: str) -> None:
        self.base = base.rstrip("/")

    def call(self, method: str, path: str, member: str, body: dict | None = None, lang: str = "en") -> tuple[int, dict]:
        req = urllib.request.Request(
            self.base + path, method=method, data=json.dumps(body).encode() if body is not None else None,
            headers={"X-Dev-Member-Id": member, "Content-Type": "application/json", "X-Vyapar-Language": lang},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
                return resp.status, (json.loads(raw) if raw else {})
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            try:
                return exc.code, json.loads(raw)
            except ValueError:
                return exc.code, {"raw": raw.decode(errors="replace")}


def owner_dsn() -> str:
    env_path = Path(__file__).resolve().parents[2] / "07a-db-implementation" / ".env"
    values: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if "=" in line:
            k, v = line.split("=", 1)
            values[k.strip()] = v.strip()
    values.update({k: v for k, v in os.environ.items() if k.startswith("DB_")})
    return (f"postgres://{values['DB_OWNER_USER']}:{values['DB_OWNER_PASSWORD']}"
            f"@{values['DB_HOST']}:{values['DB_PORT']}/{values['DB_NAME']}")


async def settled(db: asyncpg.Connection, sql: str, *args, want=None, timeout: float = 3.0):
    """Reads a DB-side fact right after an API call. The API's request
    transaction can commit a few milliseconds after its response is sent
    (FastAPI tears down yield dependencies after the response), so poll
    briefly instead of trusting the first read."""
    deadline = asyncio.get_running_loop().time() + timeout
    while True:
        value = await db.fetchval(sql, *args)
        if value == want or asyncio.get_running_loop().time() >= deadline:
            return value
        await asyncio.sleep(0.1)


def code(body: dict) -> str | None:
    return (body.get("error") or {}).get("code")


def milestone(contract: dict, mid: str) -> dict:
    return next(m for m in contract["milestones"] if m["id"] == mid)


def pay_sandbox(api: Api, funding: dict) -> None:
    st, res = api.call("POST", f"/v1/payments/orders/{funding['payment_order_id']}/simulate", CLIENT, {"outcome": "succeeded"})
    check(st == 200 and res.get("result", {}).get("applied") is True, f"sandbox payment applied for order {funding['payment_order_id'][:8]}")


async def main(api_base: str) -> int:
    api = Api(api_base)
    db = await asyncpg.connect(owner_dsn())
    tracked: dict[str, set[str]] = {"enquiry": set(), "contract": set(), "milestone": set(), "dispute": set(), "timesheet": set(), "order": set()}
    started_at = await db.fetchval("SELECT now()")
    listing_id = await db.fetchval(
        "SELECT id::text FROM vyapar_listings.listings WHERE owner_id = $1 AND state IN ('active_verified','active_unverified') ORDER BY created_at LIMIT 1", PROVIDER)
    if listing_id is None:
        print(f"no active listing for {PROVIDER}; seed data missing")
        return 2
    enquiries_sent: dict[str, int] = {}
    package_ids: set[str] = set()
    opportunity_ids: set[str] = set()
    try:
        # ---------------------------------------------------------------- setup: an accepted enquiry
        def accepted_enquiry(message: str) -> str:
            st, enq = api.call("POST", "/v1/enquiries", CLIENT, {"listing_id": listing_id, "message": message})
            check(st == 201, f"client sends an enquiry ({st})")
            if st != 201:
                raise SystemExit(f"cannot continue: {enq}")
            enquiries_sent[CLIENT] = enquiries_sent.get(CLIENT, 0) + 1
            tracked["enquiry"].add(enq["id"])
            st, _ = api.call("POST", f"/v1/enquiries/{enq['id']}/messages", PROVIDER, {"body": "Yes, I can take this on. Weekday evenings work for me."})
            check(st == 201, "provider replies")
            st, acc = api.call("POST", f"/v1/enquiries/{enq['id']}/accept", PROVIDER)
            check(st == 200 and acc["state"] == "in_progress", "provider accepts the enquiry (in_progress)")
            return enq["id"]

        print("\n== Fixed-price contract ==")
        enquiry_id = accepted_enquiry("We need weekly maths coaching for two junior accountants at Sethi Textiles, about three months.")

        st, body = api.call("POST", "/v1/contracts", CLIENT, {
            "enquiry_id": enquiry_id, "title": "Maths coaching for accounts team", "kind": "fixed", "total_paise": 800000, "propose": True,
            "milestones": [{"title": "Month 1: arithmetic and percentages", "amount_paise": 300000},
                           {"title": "Month 2: ratios and interest", "amount_paise": 400000}]})
        check(st == 422 and code(body) == "milestones_must_sum_to_total", f"milestones not summing to total are refused ({st} {code(body)})")

        st, body = api.call("POST", "/v1/contracts", PROVIDER, {"enquiry_id": enquiry_id, "title": "Wrong side", "total_paise": 100000})
        check(st == 403 and code(body) == "not_client", f"provider cannot create the contract ({st} {code(body)})")

        st, c = api.call("POST", "/v1/contracts", CLIENT, {
            "enquiry_id": enquiry_id, "title": "Maths coaching for accounts team", "kind": "fixed", "total_paise": 800000,
            "description": "Two evening sessions a week at the Karol Bagh office.",
            "milestones": [{"title": "Month 1: arithmetic and percentages", "amount_paise": 300000, "due_date": str(date.today() + timedelta(days=30))}]})
        check(st == 201 and c["state"] == "draft" and c["my_role"] == "client", f"createContract -> draft ({st})")
        cid = c["id"]
        tracked["contract"].add(cid)

        st, body = api.call("POST", "/v1/contracts", CLIENT, {"enquiry_id": enquiry_id, "title": "Duplicate", "total_paise": 100000,
                                                             "milestones": [{"title": "x1", "amount_paise": 100000}]})
        check(st == 409 and code(body) == "duplicate_contract", f"a second live contract on the same enquiry is refused ({st})")

        st, c = api.call("POST", f"/v1/contracts/{cid}/milestones", CLIENT, {"title": "Month 2 & 3: ratios, interest, GST", "amount_paise": 500000})
        check(st == 201 and len(c["milestones"]) == 2, "addMilestone on the draft")
        m1, m2 = c["milestones"][0]["id"], c["milestones"][1]["id"]
        tracked["milestone"].update({m1, m2})
        st, c = api.call("PATCH", f"/v1/contracts/{cid}/milestones/{m2}", CLIENT, {"title": "Months 2-3: ratios, interest and GST"})
        check(st == 200 and milestone(c, m2)["title"].startswith("Months 2-3"), "updateMilestone on the draft")

        st, c = api.call("POST", f"/v1/contracts/{cid}/propose", CLIENT)
        check(st == 200 and c["state"] == "proposed", "proposeContract -> proposed")
        st, body = api.call("POST", f"/v1/contracts/{cid}/milestones", CLIENT, {"title": "Late add", "amount_paise": 1000})
        check(st == 400 and code(body) == "draft_only", "milestones are frozen once proposed")

        # RLS: only the two parties (and moderation operators) can read it
        st, body = api.call("GET", f"/v1/contracts/{cid}", OUTSIDER, lang="hi")
        check(st == 404 and code(body) == "contract_not_found" and any("ऀ" <= ch <= "ॿ" for ch in body["error"]["message"]),
              f"outsider gets 404 with a Hindi message ({st})")
        st, body = api.call("GET", f"/v1/contracts/{cid}", PROVIDER)
        check(st == 200 and body["my_role"] == "provider", "provider can read the contract")
        st, pv = api.call("GET", f"/v1/contracts/{cid}", PROVIDER, lang="te")
        st2, cv = api.call("GET", f"/v1/contracts/{cid}", CLIENT)
        check(pv["sandbox"] is True and cv["sandbox"] is True, "sandbox flag is true for both parties (dev_sandbox gateway)")
        check(cv["payment_notice"].startswith("Test mode") and pv["payment_notice"] and pv["payment_notice"] != cv["payment_notice"]
              and any("ఀ" <= ch <= "౿" for ch in pv["payment_notice"]), "provider gets the payment notice too, localized (Telugu)")
        st, body = api.call("GET", f"/v1/contracts/{cid}", OPERATOR)
        check(st == 200 and body["my_role"] == "operator", "moderation operator can read the contract")

        st, c = api.call("POST", f"/v1/contracts/{cid}/accept", PROVIDER)
        check(st == 200 and c["state"] == "active", "acceptContract -> active")

        st, body = api.call("POST", f"/v1/contracts/{cid}/milestones/{m1}/submit", PROVIDER, {"note": "Done"})
        check(st == 400 and code(body) == "milestone_not_funded", "provider cannot submit an unfunded milestone")
        st, body = api.call("POST", f"/v1/contracts/{cid}/milestones/{m1}/fund", PROVIDER)
        check(st == 403 and code(body) == "not_client", "provider cannot fund")

        st, f1 = api.call("POST", f"/v1/contracts/{cid}/milestones/{m1}/fund", CLIENT)
        check(st == 200 and f1["checkout_url"] and f1["payment_order_id"] and f1["sandbox"] is True, f"fundMilestone returns a checkout ({st})")
        tracked["order"].add(f1["payment_order_id"])
        st, f1b = api.call("POST", f"/v1/contracts/{cid}/milestones/{m1}/fund", CLIENT)
        check(st == 200 and f1b["payment_order_id"] == f1["payment_order_id"], "funding again hands back the same open checkout")
        st, c = api.call("GET", f"/v1/contracts/{cid}", CLIENT)
        check(milestone(c, m1)["state"] == "pending", "milestone stays pending until the gateway confirms")

        pay_sandbox(api, f1)
        st, c = api.call("GET", f"/v1/contracts/{cid}", CLIENT)
        check(milestone(c, m1)["state"] == "funded" and c["ledger"]["held_paise"] == 300000, "payment success -> funded, ₹3,000 held in the ledger")

        st, c = api.call("POST", f"/v1/contracts/{cid}/milestones/{m1}/submit", PROVIDER, {"note": "Eight sessions held; worksheets shared."})
        check(st == 200 and milestone(c, m1)["state"] == "submitted" and milestone(c, m1)["auto_release_at"], "submitMilestone -> submitted with auto_release_at")
        st, c = api.call("POST", f"/v1/contracts/{cid}/milestones/{m1}/reject", CLIENT, {"note": "Please share the percentage worksheet answers too."})
        check(st == 200 and milestone(c, m1)["state"] == "rejected" and milestone(c, m1)["auto_release_at"] is None, "rejectMilestone -> rejected, auto-release cleared")
        st, c = api.call("POST", f"/v1/contracts/{cid}/milestones/{m1}/submit", PROVIDER, {"note": "Answers added."})
        check(st == 200 and milestone(c, m1)["state"] == "submitted", "provider resubmits")
        st, c = api.call("POST", f"/v1/contracts/{cid}/milestones/{m1}/approve", CLIENT)
        check(st == 200 and milestone(c, m1)["state"] == "released" and c["ledger"]["released_paise"] == 300000 and c["ledger"]["held_paise"] == 0,
              "approveMilestone -> released, ledger released ₹3,000")
        check(c["ledger"]["fee_paise"] == 0 and c["platform_fee_bps"] == 0, "no platform fee by default")
        check(c["state"] == "active", "contract stays active while a milestone is open")

        st, f2 = api.call("POST", f"/v1/contracts/{cid}/milestones/{m2}/fund", CLIENT)
        tracked["order"].add(f2["payment_order_id"])
        pay_sandbox(api, f2)
        st, c = api.call("POST", f"/v1/contracts/{cid}/milestones/{m2}/submit", PROVIDER, {"note": "Months 2-3 complete."})
        check(st == 200 and milestone(c, m2)["state"] == "submitted", "second milestone funded and submitted")
        # Time shortcut only: make the 14-day window already over, then run the pass.
        await db.execute("UPDATE vyapar_contracts.contract_milestones SET auto_release_at = now() - interval '1 minute' WHERE id = $1", m2)
        st, res = api.call("POST", "/v1/contracts/jobs/auto-release", CLIENT)
        check(st == 200 and res["released"] >= 1 and res["completed"] >= 1, f"auto-release pass releases and completes ({res})")
        st, c = api.call("GET", f"/v1/contracts/{cid}", CLIENT)
        check(c["state"] == "completed" and c["ledger"]["released_paise"] == 800000, "fixed contract completed, ₹8,000 released in total")

        invites = await settled(db, "SELECT count(*) FROM vyapar_reviews.review_invites WHERE interaction_kind = 'enquiry' AND interaction_id = $1::uuid", enquiry_id, want=2)
        check(invites == 2, f"review invites issued to both parties ({invites})")
        enq_state = await settled(db, "SELECT state FROM vyapar_enquiries.enquiries WHERE id = $1::uuid", enquiry_id, want="resolved")
        check(enq_state == "resolved", f"source enquiry resolved ({enq_state})")
        events = {r["event_type"] for r in await db.fetch(
            "SELECT event_type FROM vyapar_enquiries.outbox_event WHERE payload->>'contract_id' = $1", cid)}
        want = {"contract.proposed", "contract.accepted", "milestone.funded", "milestone.submitted", "milestone.approved", "contract.completed"}
        check(want <= events, f"domain events in the outbox: {sorted(events & want)}")
        notes = {r["template_id"] for r in await db.fetch(
            "SELECT template_id FROM vyapar_integration.notifications WHERE link = $1", f"/contracts/{cid}")}
        check({"contractProposed", "contractAccepted", "milestoneFunded", "milestoneSubmitted", "milestoneReleased", "contractCompleted"} <= notes,
              f"notifications sent: {sorted(notes)}")

        st, page = api.call("GET", "/v1/contracts?role=client&limit=1", CLIENT)
        check(st == 200 and page["items"] and page["items"][0]["id"] == cid, "listMyContracts as client")
        st, page = api.call("GET", "/v1/contracts?role=provider&state=completed&limit=5", PROVIDER)
        check(st == 200 and any(i["id"] == cid for i in page["items"]), "listMyContracts as provider, filtered by state")
        st, page = api.call("GET", "/v1/contracts?role=client&limit=1", OUTSIDER)
        check(st == 200 and all(i["id"] != cid for i in page["items"]), "outsider's list does not include it")

        # ------------------------------------------------------------ hourly
        print("\n== Hourly contract ==")
        enquiry2 = accepted_enquiry("Could you continue with a weekly hourly arrangement for GST practice sessions after the course?")
        st, h = api.call("POST", "/v1/contracts", CLIENT, {
            "enquiry_id": enquiry2, "title": "GST practice sessions (hourly)", "kind": "hourly", "total_paise": 1000000,
            "hourly_rate_paise": 50000, "weekly_hours_cap": 10, "propose": True})
        check(st == 201 and h["state"] == "proposed" and h["kind"] == "hourly", f"hourly contract created and proposed ({st})")
        hid = h["id"]
        tracked["contract"].add(hid)
        st, h = api.call("POST", f"/v1/contracts/{hid}/accept", PROVIDER)
        check(st == 200 and h["state"] == "active", "provider accepts the hourly contract")

        today = date.today()
        last_monday = today - timedelta(days=today.isoweekday() - 1 + 7)
        st, body = api.call("POST", f"/v1/contracts/{hid}/timesheets", PROVIDER, {"week_start": str(last_monday), "hours": 12})
        check(st == 422 and code(body) == "weekly_cap_exceeded", "hours over the weekly cap are refused")
        st, body = api.call("POST", f"/v1/contracts/{hid}/timesheets", PROVIDER, {"week_start": str(last_monday + timedelta(days=1)), "hours": 2})
        check(st == 422 and code(body) == "week_start_not_monday", "week must start on a Monday")
        st, h = api.call("POST", f"/v1/contracts/{hid}/timesheets", PROVIDER, {"week_start": str(last_monday), "hours": 6, "note": "Three 2-hour sessions"})
        check(st == 201 and h["timesheets"][0]["amount_paise"] == 300000, "submitTimesheet: 6 h x ₹500 = ₹3,000")
        ts_id = h["timesheets"][0]["id"]
        tracked["timesheet"].add(ts_id)

        st, h = api.call("POST", f"/v1/contracts/{hid}/disputes", PROVIDER, {"reason": "Two sessions last week ran over and were not counted."})
        check(st == 201 and h["state"] == "disputed", "openDispute -> disputed")
        dispute_id = h["disputes"][0]["id"]
        tracked["dispute"].add(dispute_id)
        st, lst = api.call("GET", "/v1/contracts/disputes?state=open", OPERATOR)
        check(st == 200 and any(d["id"] == dispute_id for d in lst), "moderation console lists the open dispute")
        st, body = api.call("GET", "/v1/contracts/disputes", CLIENT)
        check(st == 403, "members cannot list every dispute")
        st, body = api.call("POST", f"/v1/contracts/{hid}/disputes/{dispute_id}/resolve", CLIENT, {"outcome": "closed"})
        check(st == 403, "a party cannot resolve their own dispute")
        st, h = api.call("POST", f"/v1/contracts/{hid}/disputes/{dispute_id}/resolve", OPERATOR,
                         {"outcome": "closed", "notes": "Both agreed to log the overrun in next week's sheet."})
        check(st == 200 and h["state"] == "active" and h["disputes"][0]["state"] == "closed", "operator closes the dispute, contract active again")

        st, ft = api.call("POST", f"/v1/contracts/{hid}/timesheets/{ts_id}/approve", CLIENT)
        check(st == 200 and ft["checkout_url"] and ft["amount_paise"] == 300000, "approveTimesheet returns the checkout for ₹3,000")
        tracked["order"].add(ft["payment_order_id"])
        tracked["milestone"].add(ft["milestone_id"])
        pay_sandbox(api, ft)
        st, h = api.call("GET", f"/v1/contracts/{hid}", CLIENT)
        check(h["timesheets"][0]["state"] == "paid" and milestone(h, ft["milestone_id"])["state"] == "released"
              and h["ledger"]["released_paise"] == 300000 and h["ledger"]["held_paise"] == 0,
              "paid timesheet: milestone released, ledger released ₹3,000")
        st, h = api.call("POST", f"/v1/contracts/{hid}/complete", CLIENT)
        check(st == 200 and h["state"] == "completed", "completeContract (hourly)")
        invites2 = await settled(db, "SELECT count(*) FROM vyapar_reviews.review_invites WHERE interaction_kind = 'enquiry' AND interaction_id = $1::uuid", enquiry2, want=2)
        check(invites2 == 2, "review invites for the hourly contract")
        st, body = api.call("POST", f"/v1/contracts/{hid}/cancel", CLIENT, {})
        check(st == 400 and code(body) == "contracts_invalid_transition", "a completed contract cannot be cancelled")

        # ------------------------------------------- dispute resolved for the provider
        print("\n== Dispute resolved in the provider's favour ==")
        enquiry3 = accepted_enquiry("One more short module please: a two-week refresher on TDS calculations for the same team.")
        st, d = api.call("POST", "/v1/contracts", CLIENT, {
            "enquiry_id": enquiry3, "title": "TDS refresher (two weeks)", "total_paise": 250000, "propose": True,
            "milestones": [{"title": "TDS refresher, four sessions", "amount_paise": 250000}]})
        did = d["id"]
        tracked["contract"].add(did)
        dm = d["milestones"][0]["id"]
        api.call("POST", f"/v1/contracts/{did}/accept", PROVIDER)
        st, fd = api.call("POST", f"/v1/contracts/{did}/milestones/{dm}/fund", CLIENT)
        tracked["order"].add(fd["payment_order_id"])
        pay_sandbox(api, fd)
        api.call("POST", f"/v1/contracts/{did}/milestones/{dm}/submit", PROVIDER, {"note": "All four sessions held."})
        st, d = api.call("POST", f"/v1/contracts/{did}/milestones/{dm}/reject", CLIENT, {"note": "Only three sessions happened."})
        st, d = api.call("POST", f"/v1/contracts/{did}/disputes", PROVIDER, {"reason": "The fourth session was held on Saturday; attendance sheet shared.", "milestone_id": dm})
        check(st == 201 and d["state"] == "disputed", "provider disputes the sent-back milestone")
        tracked["dispute"].add(d["disputes"][0]["id"])
        st, d = api.call("POST", f"/v1/contracts/{did}/disputes/{d['disputes'][0]['id']}/resolve", OPERATOR,
                         {"outcome": "resolved_provider", "notes": "Attendance sheet confirms four sessions."})
        check(st == 200 and milestone(d, dm)["state"] == "released" and d["state"] == "completed",
              f"operator resolves for the provider: released and completed ({st} {d.get('state') if isinstance(d, dict) else d})")
        invites3 = await settled(db, "SELECT count(*) FROM vyapar_reviews.review_invites WHERE interaction_kind = 'enquiry' AND interaction_id = $1::uuid", enquiry3, want=2)
        check(invites3 == 2, f"review invites after an operator-resolved completion ({invites3})")

        # ------------------------------------------------ who pays (CRITIQUE-2026-09-28 N1)
        print("\n== Who pays: proposal on a post (poster pays) ==")
        deadline = (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()
        st, opp = api.call("POST", "/v1/opportunities", POSTER, {
            "type": "freelance", "title": "Content writer for our festive product launch (5 articles)",
            "description": "Five 800-word articles for the Diwali range on our store blog, in English, delivered over three weeks.",
            "compensation": "Rs 12,500 to Rs 25,000 for all five", "work_mode": "remote", "source_segment": "community", "deadline": deadline})
        check(st == 201, f"poster drafts a freelance project ({st})")
        opp_id = opp["id"]
        opportunity_ids.add(opp_id)
        if opp.get("unconfirmed_fields"):
            api.call("PATCH", f"/v1/opportunities/{opp_id}/confirm", POSTER, {"fields": opp["unconfirmed_fields"]})
        api.call("PATCH", f"/v1/opportunities/{opp_id}", POSTER,
                 {"structured": {"budget_type": "fixed", "budget_min_paise": 1250000, "budget_max_paise": 2500000}})
        st, opp = api.call("POST", f"/v1/opportunities/{opp_id}/publish", POSTER)
        check(st == 200 and opp.get("state") == "active", f"poster publishes it ({st} {opp.get('state') or code(opp)})")
        st, prop = api.call("POST", "/v1/enquiries", FREELANCER, {
            "opportunity_id": opp_id, "bid_amount_paise": 2500000, "timeline_days": 21,
            "message": "I can write all five festive articles in three weeks, with one round of edits on each."})
        check(st == 201 and prop.get("action_type") == "propose", f"freelancer sends a proposal ({st} {prop.get('action_type')})")
        if st != 201:
            raise SystemExit(f"cannot continue: {prop}")
        tracked["enquiry"].add(prop["id"])
        enquiries_sent[FREELANCER] = enquiries_sent.get(FREELANCER, 0) + 1
        st, roles = api.call("GET", f"/v1/contracts/roles?enquiry_id={prop['id']}", POSTER)
        check(st == 200 and roles["client_member_id"] == POSTER and roles["basis"] == "poster_pays"
              and roles["can_create"] is False and roles["blocked_reason"] == "enquiry_not_accepted",
              "getContractRoles before acceptance: poster is the client, not yet creatable")
        st, acc = api.call("POST", f"/v1/enquiries/{prop['id']}/accept", POSTER)
        check(st == 200 and acc["state"] == "in_progress", "poster accepts the proposal")
        st, roles = api.call("GET", f"/v1/contracts/roles?enquiry_id={prop['id']}", POSTER)
        check(roles["my_role"] == "client" and roles["can_create"] is True and roles["provider_member_id"] == FREELANCER,
              "poster: my_role client, can_create true")
        st, roles = api.call("GET", f"/v1/contracts/roles?enquiry_id={prop['id']}", FREELANCER)
        check(roles["my_role"] == "provider" and roles["can_create"] is False and roles["blocked_reason"] == "not_client",
              "freelancer: my_role provider, can_create false (not_client)")
        st, body = api.call("GET", f"/v1/contracts/roles?enquiry_id={prop['id']}", CLIENT)
        check(st == 404, "a third member cannot read the roles of someone else's enquiry")
        st, body = api.call("POST", "/v1/contracts", FREELANCER, {
            "enquiry_id": prop["id"], "title": "Festive launch: five articles", "total_paise": 2500000,
            "milestones": [{"title": "Five articles delivered", "amount_paise": 2500000}]})
        check(st == 403 and code(body) == "not_client", f"freelancer creating the contract gets 403 not_client ({st} {code(body)})")
        st, pc = api.call("POST", "/v1/contracts", POSTER, {
            "enquiry_id": prop["id"], "title": "Festive launch: five articles", "total_paise": 2500000,
            "milestones": [{"title": "Articles 1-2", "amount_paise": 1000000}, {"title": "Articles 3-5", "amount_paise": 1500000}]})
        check(st == 201 and pc["client_member_id"] == POSTER and pc["provider_member_id"] == FREELANCER and pc["my_role"] == "client",
              f"poster creates it and is the client ({st})")
        if st == 201:
            tracked["contract"].add(pc["id"])
            st, roles = api.call("GET", f"/v1/contracts/roles?enquiry_id={prop['id']}", POSTER)
            check(roles["can_create"] is False and roles["blocked_reason"] == "duplicate_contract" and roles["live_contract_id"] == pc["id"],
                  "roles then point at the live contract")

        # The live 2026-09-30 case: a price request on a local-service post
        # (Suresh asked for a quote on Meena's evening-delivery post).
        print("\n== Who pays: price request on a local-service post (poster pays) ==")
        st, lopp = api.call("POST", "/v1/opportunities", LS_POSTER, {
            "type": "local_service", "title": "Evening delivery partner for festive sweet boxes",
            "description": "Deliver 10-15 sweet boxes each evening between 6 and 9 pm across Karol Bagh and Rajendra Nagar for one week.",
            "compensation": "Rs 600 per evening", "location": "Karol Bagh, Delhi", "work_mode": "on_site",
            "source_segment": "community", "deadline": deadline})
        check(st == 201, f"poster drafts a local-service post ({st})")
        lopp_id = lopp["id"]
        opportunity_ids.add(lopp_id)
        if lopp.get("unconfirmed_fields"):
            api.call("PATCH", f"/v1/opportunities/{lopp_id}/confirm", LS_POSTER, {"fields": lopp["unconfirmed_fields"]})
        st, lopp = api.call("POST", f"/v1/opportunities/{lopp_id}/publish", LS_POSTER)
        check(st == 200 and lopp.get("state") == "active", f"poster publishes it ({st})")
        st, quote = api.call("POST", "/v1/enquiries", LS_SENDER, {
            "opportunity_id": lopp_id, "sub_choice": "request_quote",
            "message": "I deliver on a two-wheeler in that area every evening; what would you pay for the full week?"})
        check(st == 201 and quote.get("action_type") == "enquire", f"a price request on the post ({st} {quote.get('action_type')})")
        if st != 201:
            raise SystemExit(f"cannot continue: {quote}")
        tracked["enquiry"].add(quote["id"])
        enquiries_sent[LS_SENDER] = enquiries_sent.get(LS_SENDER, 0) + 1
        st, acc = api.call("POST", f"/v1/enquiries/{quote['id']}/accept", LS_POSTER)
        check(st == 200 and acc["state"] == "in_progress", "poster accepts the price request")
        st, roles = api.call("GET", f"/v1/contracts/roles?enquiry_id={quote['id']}", LS_SENDER)
        check(roles["client_member_id"] == LS_POSTER and roles["basis"] == "poster_pays" and roles["my_role"] == "provider"
              and roles["blocked_reason"] == "not_client", "price request on a post: the poster is the client, the requester does the work")
        st, body = api.call("POST", "/v1/contracts", LS_SENDER, {
            "enquiry_id": quote["id"], "title": "Sweet box deliveries, one week", "total_paise": 420000,
            "milestones": [{"title": "Evenings 1-3", "amount_paise": 180000}, {"title": "Evenings 4-7", "amount_paise": 240000}]})
        check(st == 403 and code(body) == "not_client", f"the requester cannot create it as the payer ({st} {code(body)})")
        st, lc = api.call("POST", "/v1/contracts", LS_POSTER, {
            "enquiry_id": quote["id"], "title": "Sweet box deliveries, one week", "total_paise": 420000,
            "milestones": [{"title": "Evenings 1-3", "amount_paise": 180000}, {"title": "Evenings 4-7", "amount_paise": 240000}]})
        check(st == 201 and lc["client_member_id"] == LS_POSTER and lc["provider_member_id"] == LS_SENDER, "the poster creates it and pays")
        if st == 201:
            tracked["contract"].add(lc["id"])

        print("\n== Who pays: package request to a profile (requester pays) ==")
        st, existing = api.call("GET", f"/v1/listings/{listing_id}/packages", PROVIDER)
        check(st == 200 and existing == [], "provider's profile has no packages before the check")
        st, pkgs = api.call("PUT", f"/v1/listings/{listing_id}/packages", PROVIDER, {"packages": [
            {"tier": "basic", "name": "Four evening maths sessions", "price_paise": 400000, "delivery_days": 14}]})
        if st == 422:  # the route may take a bare list
            st, pkgs = api.call("PUT", f"/v1/listings/{listing_id}/packages", PROVIDER, [
                {"tier": "basic", "name": "Four evening maths sessions", "price_paise": 400000, "delivery_days": 14}])
        check(st == 200 and bool(pkgs), f"provider publishes a package on their profile ({st})")
        if st != 200:
            raise SystemExit(f"cannot continue: {pkgs}")
        package_ids.update(p["id"] for p in pkgs)
        pkg_id = pkgs[0]["id"]
        st, preq = api.call("POST", f"/v1/listings/{listing_id}/packages/{pkg_id}/request", CLIENT,
                            {"message": "Please book the four-session package for our junior accountant from next week."})
        check(st == 201, f"client requests the package ({st})")
        penq = preq["enquiry"]["id"]
        tracked["enquiry"].add(penq)
        enquiries_sent[CLIENT] = enquiries_sent.get(CLIENT, 0) + 1
        api.call("POST", f"/v1/enquiries/{penq}/accept", PROVIDER)
        st, roles = api.call("GET", f"/v1/contracts/roles?enquiry_id={penq}", CLIENT)
        check(roles["client_member_id"] == CLIENT and roles["basis"] == "requester_pays" and roles["can_create"] is True,
              "package request: the sender (requester) is the client")
        st, body = api.call("POST", "/v1/contracts", PROVIDER, {"enquiry_id": penq, "title": "Maths package", "total_paise": 400000,
                                                               "milestones": [{"title": "Four sessions", "amount_paise": 400000}]})
        check(st == 403 and code(body) == "not_client", "the profile owner cannot make themselves the payer")
        st, kc = api.call("POST", "/v1/contracts", CLIENT, {"enquiry_id": penq, "title": "Maths package", "total_paise": 400000,
                                                           "milestones": [{"title": "Four sessions", "amount_paise": 400000}]})
        check(st == 201 and kc["client_member_id"] == CLIENT and kc["provider_member_id"] == PROVIDER, "requester creates it as the client")
        if st == 201:
            tracked["contract"].add(kc["id"])
    finally:
        await cleanup(db, tracked, started_at, listing_id, enquiries_sent, package_ids, opportunity_ids)
        await db.close()

    failed = [label for ok, label in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    for label in failed:
        print("  failed:", label)
    return 1 if failed else 0


async def cleanup(db: asyncpg.Connection, tracked: dict[str, set[str]], started_at, listing_id: str, enquiries_sent: dict[str, int],
                  package_ids: set[str], opportunity_ids: set[str]) -> None:
    print("\n== Cleanup ==")
    enquiry_ids = list(tracked["enquiry"])
    contract_ids = [r["id"] for r in await db.fetch(
        "SELECT id::text FROM vyapar_contracts.contracts WHERE enquiry_id = ANY($1::uuid[])", enquiry_ids)]
    tracked["contract"].update(contract_ids)
    tracked["milestone"].update(r["id"] for r in await db.fetch(
        "SELECT id::text FROM vyapar_contracts.contract_milestones WHERE contract_id = ANY($1::uuid[])", list(tracked["contract"])))
    tracked["dispute"].update(r["id"] for r in await db.fetch(
        "SELECT id::text FROM vyapar_contracts.contract_disputes WHERE contract_id = ANY($1::uuid[])", list(tracked["contract"])))
    tracked["order"].update(r["id"] for r in await db.fetch(
        "SELECT id::text FROM vyapar_payments.payment_orders WHERE kind = 'contract_milestone' AND ref_id = ANY($1::uuid[])", list(tracked["milestone"])))
    ids = sorted(set().union(*tracked.values()) | set(opportunity_ids) | set(package_ids))
    patterns = [f"%{i}%" for i in ids]
    if not ids:
        print("  nothing to clean")
        return
    async with db.transaction():
        n = {}
        n["payment_orders"] = await db.execute("DELETE FROM vyapar_payments.payment_orders WHERE id = ANY($1::uuid[])", list(tracked["order"]))
        n["contracts"] = await db.execute("DELETE FROM vyapar_contracts.contracts WHERE id = ANY($1::uuid[])", list(tracked["contract"]))
        n["review_invites"] = await db.execute(
            "DELETE FROM vyapar_reviews.review_invites WHERE interaction_kind = 'enquiry' AND interaction_id = ANY($1::uuid[])", enquiry_ids)
        n["notifications"] = await db.execute(
            "DELETE FROM vyapar_integration.notifications WHERE created_at >= $1 AND (link LIKE ANY($2) OR params::text LIKE ANY($2) OR idempotency_key LIKE ANY($2))",
            started_at, patterns)
        for table in ("vyapar_enquiries.outbox_event", "vyapar_reviews.outbox_event"):
            n[table] = await db.execute(f"DELETE FROM {table} WHERE created_at >= $1 AND payload::text LIKE ANY($2)", started_at, patterns)
        n["audit_events"] = await db.execute(
            "DELETE FROM vyapar_integration.audit_events WHERE at >= $1 AND (object_id LIKE ANY($2) OR details::text LIKE ANY($2))", started_at, patterns)
        n["enquiries"] = await db.execute("DELETE FROM vyapar_enquiries.enquiries WHERE id = ANY($1::uuid[])", enquiry_ids)
        if package_ids:
            n["listing_packages"] = await db.execute("DELETE FROM vyapar_listings.listing_packages WHERE id = ANY($1::uuid[])", list(package_ids))
        n["impressions_opportunity"] = await db.execute(
            "DELETE FROM vyapar_commercial.impressions WHERE target_kind = 'opportunity' AND target_id = ANY($1::uuid[]) AND at >= $2",
            list(opportunity_ids), started_at)
        if opportunity_ids:
            # The post this run published: its saves/views, outbox rows, then the post itself.
            opp_patterns = [f"%{o}%" for o in opportunity_ids]
            for table in ("vyapar_opportunities.member_opportunity", "vyapar_opportunities.outbox_event"):
                n[table] = await db.execute(f"DELETE FROM {table} x WHERE x::text LIKE ANY($1)", opp_patterns)
            n["opportunities"] = await db.execute("DELETE FROM vyapar_opportunities.opportunities WHERE id = ANY($1::uuid[])", list(opportunity_ids))
        n["impressions"] = await db.execute(
            "DELETE FROM vyapar_commercial.impressions WHERE target_kind = 'listing' AND target_id = $1::uuid AND surface = 'enquiry' AND member_id IS NULL AND at >= $2",
            listing_id, started_at)
        for sender, count in enquiries_sent.items():
            key = f"enquiry:{sender}:day"
            await db.execute(
                """UPDATE vyapar_platform.rate_limit_counter SET hit_count = greatest(hit_count - $2, 0)
                    WHERE rate_limit_key = $1 AND window_start = (SELECT max(window_start) FROM vyapar_platform.rate_limit_counter WHERE rate_limit_key = $1)""",
                key, count)
            await db.execute("DELETE FROM vyapar_platform.rate_limit_counter WHERE rate_limit_key = $1 AND hit_count = 0", key)
    for k, v in n.items():
        print(f"  {k}: {v}")
    # Sweep: no row in any vyapar_* table may still mention an id this run created.
    tables = await db.fetch(
        "SELECT schemaname, tablename FROM pg_tables WHERE schemaname LIKE 'vyapar\\_%' ORDER BY 1, 2")
    leftovers = []
    for t in tables:
        q = f'SELECT count(*) FROM "{t["schemaname"]}"."{t["tablename"]}" x WHERE x::text LIKE ANY($1)'
        count = await db.fetchval(q, patterns)
        if count:
            leftovers.append(f"{t['schemaname']}.{t['tablename']}={count}")
    check(not leftovers, f"no leftover rows mention the test ids ({', '.join(leftovers) or 'clean'})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--api", default=os.environ.get("VYAPAR_CHECK_API_BASE"), help="Base URL of a running Vyapar API (or VYAPAR_CHECK_API_BASE)")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # ₹ and Hindi in labels on a Windows console
    if not args.api:
        parser.error("--api (or VYAPAR_CHECK_API_BASE) is required")
    sys.exit(asyncio.run(main(args.api)))

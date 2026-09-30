"""End-to-end check for the Vyapar trust pack (VISION-2040 items 1-5),
against a running Vyapar API on a private port (DEV_MODE=true,
PAYMENT_GATEWAY=dev_sandbox).

  1 scam shield     a test corpus (en/hi/te/Hinglish, fee phrases, "applicant
                    pays", money before joining, phone + payment app) is caught
                    and a clean corpus ("We pay ₹18,000 a month") is not; the
                    rule runs on post text, interview details, screening
                    questions, the poster's replies to applicants and package
                    descriptions; every refusal is a 422 seeker_charge_not_allowed
                    with a localized explanation and a trust event in the audit log.
  2 honest terms    a local-service post needs a budget or a stated fee basis;
                    "paid on time" is asked only of the PAID person (after 30
                    days of a hire, or when a contract stage is released), the
                    payer can neither see nor answer it, and the count shows on
                    the payer's profile and posts only after 3 answers.
  3 close the loop  "N applicants still waiting" before closing; close, expiry
                    and a filled post give every waiting applicant a final
                    answer (declined, post_closed) and one polite notification
                    in their language; a renewed post takes them back; a
                    seeker-charge pause, an operator suspension and a review-
                    queue removal all show in listMyRestrictions with a case the
                    member can appeal, and an upheld appeal restores the item.
  4 profession      advocates and architects (Kavita Dhawan, Deepak Bhalla, and
                    a new advocate) cannot be promoted, show no reviews, badges,
                    prices, headline or description to others, rank neutrally,
                    and a promotion bought before the rule is cancelled by the
                    trust pass; a CA gets a wording note and no restriction.
  5 council badges  claim formats per register, the dev stub never "verifies",
                    the badge reads "Pending check" until an operator checks the
                    register through the existing verification queue, then
                    "Registered with Bar Council of Telangana · Checked on <date>".

Everything it creates is deleted at the end, the rate-limit counters it used
are restored, and a sweep over every vyapar_* table confirms nothing mentions
an id this run created.

Usage (from vyapar-service/):
    .venv/Scripts/python scripts/check_trust_pack.py --api http://127.0.0.1:<port>
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import secrets
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

import asyncpg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SUNITA, RAVI, MEENA, SURESH, GAURAV = "m_sunita", "m_ravi", "m_meena", "m_suresh", "m_gaurav"
VIKRAM, RAHUL, OPERATOR = "m_vikram", "m_rahul", "m_neha_ops"
KAVITA, DEEPAK, ANITA = "m_kavita", "m_deepak", "m_anita"
RESULTS: list[tuple[bool, str]] = []

# ---------------------------------------------------------------------------
# The test corpus (also the documentation of what the shield is for).
# ---------------------------------------------------------------------------
SCAM_CORPUS = [  # (text, tier) — each must be refused
    ("Kitchen helper needed. Registration fee ₹500 to be paid at the time of interview.", "hiring"),
    ("Security deposit of Rs 2000 required, refundable after 6 months.", "hiring"),
    ("Delivery boys wanted. Pay ₹1,500 kit charge (T-shirt, bag) on joining.", "hiring"),
    ("Training fee 3000 rupees, salary starts after training.", "hiring"),
    ("Candidates must pay Rs 1200 for the ID card and medical test.", "hiring"),
    ("Registration fees dena hoga 500, uske baad joining.", "hiring"),
    ("Pehle 500 rupay jama karo, phir interview ka time milega.", "hiring"),
    ("Pay ₹299 before joining to confirm your seat.", "hiring"),
    ("Send ₹300 on PhonePe to 98765 43210 to book your interview slot.", "hiring"),
    ("Pay ₹500 on GPay 9876543210 and your offer letter comes today.", "hiring"),
    ("नौकरी के लिए 500 रुपये जमा करने होंगे।", "hiring"),
    ("रजिस्ट्रेशन फीस 300 रुपये, इंटरव्यू के दिन लाएँ।", "hiring"),
    ("ఉద్యోగం కోసం ₹2000 కట్టాలి.", "hiring"),
    ("సెక్యూరిటీ డిపాజిట్ ₹5000 జాయినింగ్ రోజు.", "hiring"),
    ("Placement fee ₹5,000 — 100% job guaranteed after the course.", "offer"),
    ("Pay ₹1000 and get a guaranteed job in Dubai.", "offer"),
]
CLEAN_CORPUS = [  # must pass
    ("We pay ₹18,000 a month in hand. Call 9876543210 between 10 and 6.", "hiring"),
    ("Kitchen helpers for weddings. ₹700 per day, meals provided.", "hiring"),
    ("Uniform provided, payment on the 5th of every month.", "hiring"),
    ("You must submit 10th and 12th certificates at the interview.", "hiring"),
    ("Documents jama karo interview ke din: Aadhaar aur 2 photo.", "hiring"),
    ("दस्तावेज़ जमा करने होंगे: आधार और फ़ोटो।", "hiring"),
    ("Salary paid via UPI every month. Call 9876543210.", "hiring"),
    ("Walk-in interview at 10 am, Secunderabad. Bring your Aadhaar.", "hiring"),
    ("Budget ₹1,500 for fixing a leaking tap and basin pipe.", "hiring"),
    ("GST return filing (monthly): ₹1,499 per GSTIN, up to 100 invoices.", "offer"),
    ("Spoken English course, fee ₹2,000 for 8 weekend classes.", "offer"),
    ("Tax filing for salaried people; documents checklist shared after booking.", "offer"),
]


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
            with urllib.request.urlopen(req, timeout=60) as resp:
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


def code(body: dict) -> str | None:
    return (body.get("error") or {}).get("code")


def details(body: dict) -> dict:
    return (body.get("error") or {}).get("details") or {}


def has_script(text: str | None, lo: str, hi: str) -> bool:
    return any(lo <= ch <= hi for ch in (text or ""))


class Run:
    def __init__(self, api: Api, db: asyncpg.Connection) -> None:
        self.api, self.db = api, db
        self.opps: set[str] = set()
        self.enquiries: set[str] = set()
        self.extra_ids: set[str] = set()  # cases, contracts, milestones, orders, asks, promotions, records ...
        self.members = {SUNITA, RAVI, MEENA, SURESH, GAURAV, VIKRAM, RAHUL, KAVITA, DEEPAK, ANITA, OPERATOR}
        self.test_member = f"m_check_trust_{secrets.token_hex(3)}"
        self.deadline = (datetime.now(timezone.utc) + timedelta(days=20)).isoformat()

    def post(self, member: str, body: dict, publish: bool = True, lang: str = "en") -> tuple[int, dict]:
        base = {"entry_mode": "create", "source_segment": "community", "work_mode": "on_site", "response_method": "in_app",
                "location": "Secunderabad", "deadline": self.deadline}
        st, opp = self.api.call("POST", "/v1/opportunities", member, {**base, **body}, lang=lang)
        if st != 201:
            return st, opp
        self.opps.add(opp["id"])
        if opp.get("unconfirmed_fields"):
            self.api.call("PATCH", f"/v1/opportunities/{opp['id']}/confirm", member, {"fields": opp["unconfirmed_fields"]})
        if publish:
            st, opp2 = self.api.call("POST", f"/v1/opportunities/{opp['id']}/publish", member, lang=lang)
            return st, opp2 if st == 200 else {**opp2, "id": opp["id"]}
        return st, opp

    def apply(self, member: str, opportunity_id: str, message: str) -> str | None:
        st, enq = self.api.call("POST", "/v1/enquiries", member, {"opportunity_id": opportunity_id, "message": message})
        if st != 201:
            print("    apply failed", member, st, enq)
            return None
        self.enquiries.add(enq["id"])
        return enq["id"]

    def stage(self, opportunity_id: str, enquiry_id: str, stage: str) -> tuple[int, dict]:
        return self.api.call("POST", f"/v1/opportunities/{opportunity_id}/applicants/{enquiry_id}/stage", SUNITA, {"stage": stage})


# ---------------------------------------------------------------------------
async def section_scam_shield(r: Run) -> None:
    from app.services import scam_shield

    print("\n== 1. Scam shield: test corpus ==")
    missed = [t for t, tier in SCAM_CORPUS if scam_shield.detect(t, tier) is None]
    check(not missed, f"every scam phrasing is caught ({len(SCAM_CORPUS) - len(missed)}/{len(SCAM_CORPUS)}; missed: {missed})")
    false_pos = [(t, scam_shield.detect(t, tier)) for t, tier in CLEAN_CORPUS if scam_shield.detect(t, tier) is not None]
    check(not false_pos, f"no honest text is refused ({len(CLEAN_CORPUS) - len(false_pos)}/{len(CLEAN_CORPUS)}; wrongly refused: {false_pos})")
    rules = {scam_shield.detect(t, tier).rule for t, tier in SCAM_CORPUS if scam_shield.detect(t, tier)}
    check({"fee_phrase", "applicant_pays", "pay_before", "phone_payment", "job_fee"} <= rules, f"all five rules are exercised ({sorted(rules)})")

    st, res = r.api.call("POST", "/v1/trust/scam-check", SUNITA, {"text": "Pehle 500 rupay jama karo", "opportunity_type": "employment"}, lang="hi")
    check(st == 200 and res["allowed"] is False and res["rule"] == "applicant_pays" and has_script(res["explanation"], "ऀ", "ॿ"),
          f"checkScamShield explains the refusal in Hindi ({res.get('rule')})")
    st, res = r.api.call("POST", "/v1/trust/scam-check", SUNITA, {"text": "Spoken English course, fee ₹2,000", "opportunity_type": "training"})
    check(st == 200 and res["allowed"] is True, "a course fee on a training post is allowed (job-fee rules only there)")

    print("\n== 1. Scam shield: every place a poster writes ==")
    started = await r.db.fetchval("SELECT now()")
    job = {"type": "employment", "title": "Helpers for wedding catering, Secunderabad",
           "description": "Kapoor Caterers needs helpers for the wedding season: serving, cleaning and packing.",
           "required_capabilities": ["catering"], "structured": {"salary_min_paise": 1500000, "salary_max_paise": 1800000}}
    st, res = r.post(SUNITA, {**job, "description": job["description"] + " Registration fees dena hoga ₹500."}, publish=False, lang="hi")
    check(st == 422 and code(res) == "seeker_charge_not_allowed" and details(res).get("rule") == "fee_phrase"
          and has_script(details(res).get("explanation"), "ऀ", "ॿ"), f"post text: Hinglish registration fee refused, explained in Hindi ({st})")
    st, res = r.post(SUNITA, {**job, "structured": {**job["structured"], "interview_details": "Send ₹300 on PhonePe to 98765 43210 to book a slot"}}, publish=False)
    check(st == 422 and details(res).get("rule") == "phone_payment", f"interview details: phone + payment app refused ({details(res).get('rule')})")
    st, res = r.post(SUNITA, {"type": "freelance", "title": "Menu cards and price list design for Kapoor Caterers",
                              "description": "Design a two-page menu card and a price list for our catering business.",
                              "structured": {"budget_type": "fixed", "budget_min_paise": 500000, "budget_max_paise": 800000,
                                             "screening_questions": [{"text": "Can you pay the refundable security deposit of ₹2,000 before we start?"}]}},
                     publish=False)
    check(st == 422 and code(res) == "seeker_charge_not_allowed", "screening question: security deposit refused")
    await asyncio.sleep(0.5)
    events = await r.db.fetch(
        "SELECT reason_code, details FROM vyapar_integration.audit_events WHERE action = 'trust.seeker_charge_blocked' AND actor_id = $1 AND at >= $2",
        SUNITA, started)
    check(len(events) == 3 and all(json.loads(e["details"])["surface"] == "opportunity" for e in events)
          and not any("PhonePe" in e["details"] and "98765" in e["details"] for e in events),
          f"each refusal is a trust event with the rule, never the whole text ({len(events)} events)")
    st, honest = r.post(SUNITA, {**job, "description": job["description"] + " We pay ₹18,000 a month in hand, paid on the 5th."})
    check(st == 200 and honest.get("state") == "active", f"an honest 'We pay ₹18,000' post publishes (was refused by the old phrase list) ({st})")
    r.honest_job = honest["id"]

    # the poster's reply to an applicant
    enq = r.apply(RAVI, honest["id"], "Namaste, I have served at weddings for two seasons and can start this week.")
    r.honest_ravi = enq
    st, res = r.api.call("POST", f"/v1/enquiries/{enq}/messages", SUNITA, {"body": "Thik hai. Pehle 500 rupay jama karo, phir kal aa jao."}, lang="hi")
    check(st == 422 and code(res) == "seeker_charge_not_allowed" and details(res).get("surface") == "enquiry_reply",
          f"poster's reply asking the applicant for money is refused ({st})")
    st, _ = r.api.call("POST", f"/v1/enquiries/{enq}/messages", SUNITA, {"body": "Thik hai, kal subah 10 baje Secunderabad office aa jao."})
    check(st == 201, "a normal reply from the poster goes through")
    st, _ = r.api.call("POST", f"/v1/enquiries/{enq}/messages", RAVI, {"body": "They asked me for a registration fee on the phone, is that normal?"})
    check(st == 201, "the applicant can still write about a fee (e.g. to ask or report) — only the poster side is checked")

    # a professional's priced package ("offer" tier)
    anita_listing = await r.db.fetchval(
        "SELECT id::text FROM vyapar_listings.listings WHERE owner_id = $1 AND state IN ('active_verified','active_unverified')", ANITA)
    used = {x["tier"] for x in await r.db.fetch("SELECT tier FROM vyapar_listings.listing_packages WHERE listing_id = $1::uuid", anita_listing)}
    free_tier = next((t for t in ("premium", "standard", "basic") if t not in used), None)
    r.anita_listing = anita_listing
    if free_tier is None:
        check(True, "package check skipped: Anita already has all three tiers")
    else:
        st, res = r.api.call("PUT", f"/v1/listings/{anita_listing}/packages", ANITA, {"packages": [{
            "tier": free_tier, "name": "Job placement assistance", "price_paise": 500000,
            "description": "Placement fee ₹5,000 — 100% job guaranteed in an accounts team."}]})
        check(st == 422 and details(res).get("rule") == "job_fee" and details(res).get("field", "").endswith(".description"),
              f"package: a placement fee for a job is refused ({st} {details(res).get('field')})")
        st, res = r.api.call("PUT", f"/v1/listings/{anita_listing}/packages", ANITA, {"packages": [{
            "tier": free_tier, "name": "GST return filing (monthly)", "price_paise": 149900,
            "description": "GSTR-1 and GSTR-3B for one GSTIN, up to 100 invoices. Fee ₹1,499 a month."}]})
        pkg = next((p for p in res if p["tier"] == free_tier), None) if st == 200 else None
        check(pkg is not None, f"package: an honest service fee is saved ({st})")
        if pkg:
            r.extra_ids.add(pkg["id"])
            r.api.call("DELETE", f"/v1/listings/{anita_listing}/packages/{pkg['id']}", ANITA)


async def section_honest_terms(r: Run) -> None:
    print("\n== 2. Honest terms: a local service must say what it pays ==")
    ls = {"type": "local_service", "title": "Gas stove and chimney cleaning at our kitchen",
          "description": "Deep-clean a 4-burner gas stove and the chimney filter in our catering kitchen.",
          "required_capabilities": ["cleaning"], "structured": {"urgency": "this_week"}}
    st, res = r.post(SUNITA, ls)
    check(st == 422 and code(res) == "pay_basis_required", f"publish refused without a budget or fee basis ({st} {code(res)})")
    oid = res.get("id")
    st, _ = r.api.call("PATCH", f"/v1/opportunities/{oid}", SUNITA, {"structured": {"budget_paise": 120000}})
    st, res = r.api.call("POST", f"/v1/opportunities/{oid}/publish", SUNITA)
    check(st == 200 and res["compensation"] == "Budget ₹1,200" and res["pay_period"] == "budget", f"with a budget it publishes ({st})")
    r.api.call("POST", f"/v1/opportunities/{oid}/close", SUNITA)


async def section_close_loop(r: Run) -> None:
    print("\n== 3. Close the loop: close, renew, expire ==")
    st, job = r.post(SUNITA, {"type": "employment", "title": "Counter cashier for the sweets counter, Secunderabad",
                               "description": "Billing and packing at the Kapoor Caterers sweets counter, 10 am to 7 pm.",
                               "required_capabilities": ["catering"], "structured": {"salary_min_paise": 1400000, "salary_max_paise": 1600000}})
    check(st == 200, f"a job is posted ({st})")
    jid = job["id"]
    e_meena = r.apply(MEENA, jid, "I can do billing and packing; I run a bakery counter on weekends.")
    e_suresh = r.apply(SURESH, jid, "I have worked at a shop counter and can handle billing.")
    r.stage(jid, e_suresh, "shortlisted")
    st, cc = r.api.call("GET", f"/v1/opportunities/{jid}/close-check", SUNITA)
    check(st == 200 and cc["waiting"] == 2 and cc["new"] == 1 and cc["shortlisted"] == 1
          and cc["message"] == "2 applicants are still waiting for an answer." and "2 people" in cc["close_message"],
          f"close check: 2 still waiting ({cc.get('message')})")
    st, cc_hi = r.api.call("GET", f"/v1/opportunities/{jid}/close-check", SUNITA, lang="hi")
    check(has_script(cc_hi.get("message"), "ऀ", "ॿ"), "close check in the poster's Hindi")
    st, other = r.api.call("GET", f"/v1/opportunities/{jid}/close-check", MEENA)
    check(st == 404, "an applicant cannot read the poster's close check")
    st, det = r.api.call("GET", f"/v1/opportunities/{jid}", SUNITA)
    check((det.get("applicants_waiting") or {}).get("waiting") == 2, "the poster's detail read carries applicants_waiting")
    st, det_m = r.api.call("GET", f"/v1/opportunities/{jid}", MEENA)
    check(det_m.get("applicants_waiting") is None and det_m.get("restriction") is None, "others never see applicants_waiting or restriction")

    st, _ = r.api.call("POST", f"/v1/opportunities/{jid}/close", SUNITA)
    check(st == 200, "the poster closes the post")
    rows = {str(x["id"]): x for x in await r.db.fetch(
        "SELECT id, stage, state, state_reason FROM vyapar_enquiries.enquiries WHERE id = ANY($1::uuid[])", [e_meena, e_suresh])}
    check(all(x["stage"] == "declined" and x["state"] == "closed" and x["state_reason"] == "post_closed" for x in rows.values()),
          f"both applicants reach a final answer: declined, thread closed, reason post_closed ({[dict(x) for x in rows.values()]})")
    st, notes = r.api.call("GET", "/v1/notifications", MEENA)
    mine = [n for n in notes if n["kind"] == "applicantPostClosed" and e_meena in (n.get("link") or "")]
    check(len(mine) == 1 and "closed" in mine[0]["body"] and "judgement" in mine[0]["body"] and "not selected" not in mine[0]["body"].lower(),
          f"one polite notification that the post closed, not a rejection ({mine[0]['title'] if mine else None})")
    st, notes = r.api.call("GET", "/v1/notifications", SURESH, lang="te")
    mine = [n for n in notes if n["kind"] == "applicantPostClosed" and e_suresh in (n.get("link") or "")]
    check(len(mine) == 1 and has_script(mine[0]["body"], "ఀ", "౿"), "read in Telugu, it renders in Telugu")
    events = [x["event_type"] for x in await r.db.fetch(
        "SELECT event_type FROM vyapar_enquiries.outbox_event WHERE payload->>'id' = ANY($1::text[])", [e_meena, e_suresh])]
    check(events.count("applicant.declined") == 2, f"applicant.declined domain events for both ({events})")

    # The applicant still sees which post it was, now that RLS hides the closed post from them.
    st, th = r.api.call("GET", f"/v1/enquiries/{e_meena}", MEENA)
    st2, mine = r.api.call("GET", "/v1/enquiries/mine", MEENA)
    row_m = next((x for x in mine if x["id"] == e_meena), {}) if st2 == 200 else {}
    st3, _ = r.api.call("GET", f"/v1/opportunities/{jid}", MEENA)
    check(st3 == 404 and th.get("target_name") == job["title"] and th.get("target_state") == "closed"
          and row_m.get("target_name") == job["title"] and row_m.get("target_state") == "closed" and th.get("counterpart_name") == "Sunita Kapoor",
          f"after closing, the applicant's thread and Requests row still name the post, marked closed ({th.get('target_name')!r}, {row_m.get('target_state')})")
    st, renewed = r.api.call("POST", f"/v1/opportunities/{jid}/renew", SUNITA)
    check(st == 200 and renewed["state"] == "active", "the post is renewed")
    again = r.apply(MEENA, jid, "Applying again now that the counter job is open again.")
    check(again is not None, "closed-for-everyone is not a decision about her: she can apply to the renewed post")
    st, cc1 = r.api.call("GET", f"/v1/opportunities/{jid}/close-check", SUNITA)
    check(cc1.get("message") == "1 applicant is still waiting for an answer." and "the 1 person still waiting" in (cc1.get("close_message") or ""),
          f"one waiting: singular in English ({cc1.get('close_message')})")
    st, cc1_te = r.api.call("GET", f"/v1/opportunities/{jid}/close-check", SUNITA, lang="te")
    st, cc2_hi = r.api.call("GET", f"/v1/opportunities/{jid}/close-check", SUNITA, lang="hi")
    check("వ్యక్తికి" in (cc1_te.get("close_message") or "") and "व्यक्ति को" in (cc2_hi.get("close_message") or ""),
          "and in Telugu and Hindi (plural forms chosen per language)")

    # expiry: the hourly pass, acting as the poster
    st, job2 = r.post(SUNITA, {"type": "employment", "title": "Packing staff for Diwali sweet boxes",
                                "description": "Pack and label Diwali sweet boxes at our Secunderabad kitchen, 3 weeks.",
                                "required_capabilities": ["catering"], "structured": {"salary_min_paise": 1200000, "salary_max_paise": 1300000}})
    e_gaurav = r.apply(GAURAV, job2["id"], "I can pack boxes for the full three weeks, evening shift too.")
    await r.db.execute("UPDATE vyapar_opportunities.opportunities SET deadline = now() - interval '1 hour' WHERE id = $1::uuid", job2["id"])
    st, res = r.api.call("POST", "/v1/opportunities/jobs/expire", OPERATOR)
    row = await r.db.fetchrow("SELECT stage, state, state_reason FROM vyapar_enquiries.enquiries WHERE id = $1::uuid", e_gaurav)
    opp_state = await r.db.fetchval("SELECT state FROM vyapar_opportunities.opportunities WHERE id = $1::uuid", job2["id"])
    check(st == 200 and opp_state == "expired" and row["stage"] == "declined" and row["state_reason"] == "post_closed",
          f"expiry gives the waiting applicant a final answer too ({opp_state}, {dict(row)})")


async def section_paid_on_time(r: Run) -> None:
    print("\n== 2. Paid on time (asked of the paid person) + a post that fills ==")
    st, job = r.post(SUNITA, {"type": "employment", "title": "Helpers for the wedding season, Kapoor Caterers",
                               "description": "Serving, cleaning and packing at weddings across Secunderabad, November to February.",
                               "required_capabilities": ["catering"],
                               "structured": {"salary_min_paise": 1500000, "salary_max_paise": 1800000, "openings": 3}})
    jid = job["id"]
    apps = {m: r.apply(m, jid, msg) for m, msg in (
        (RAVI, "I served at weddings last season and can work nights."),
        (MEENA, "I can help with the dessert counter and packing."),
        (SURESH, "I can do serving and setting up tables."),
        (GAURAV, "I have a bike and can also help with deliveries."))}
    for m in (RAVI, SURESH):
        st, a = r.stage(jid, apps[m], "hired")
        check(st == 200 and a["stage"] == "hired", f"{m} hired")
    st, still = r.api.call("GET", f"/v1/opportunities/{jid}", SUNITA)
    check(still["state"] == "active", "two hires of three openings: the post stays open")
    st, a = r.stage(jid, apps[MEENA], "hired")
    opp = await r.db.fetchrow("SELECT state, state_reason FROM vyapar_opportunities.opportunities WHERE id = $1::uuid", jid)
    g = await r.db.fetchrow("SELECT stage, state_reason FROM vyapar_enquiries.enquiries WHERE id = $1::uuid", apps[GAURAV])
    check(opp["state"] == "closed" and opp["state_reason"] == "filled", f"the third hire fills the post: closed as filled ({dict(opp)})")
    check(g["stage"] == "declined" and g["state_reason"] == "post_closed", "the applicant still waiting gets a final answer")
    st, notes = r.api.call("GET", "/v1/notifications", GAURAV)
    check(any(n["kind"] == "applicantPostFilled" and apps[GAURAV] in (n.get("link") or "") and "filled" in n["body"] for n in notes),
          "and is told the openings were filled")

    # Meena's hire gets a contract: her question comes from the released stage, not the hire.
    st, c = r.api.call("POST", "/v1/contracts", SUNITA, {
        "enquiry_id": apps[MEENA], "title": "Dessert counter for the Reddy wedding", "kind": "fixed", "total_paise": 300000,
        "milestones": [{"title": "Dessert counter, 12 December", "amount_paise": 300000}], "propose": True})
    check(st == 201, f"a contract for Meena's work ({st} {code(c)})")
    cid, mid = c["id"], c["milestones"][0]["id"]
    r.extra_ids.update({cid, mid})
    r.api.call("POST", f"/v1/contracts/{cid}/accept", MEENA)
    st, f = r.api.call("POST", f"/v1/contracts/{cid}/milestones/{mid}/fund", SUNITA)
    r.extra_ids.add(f.get("payment_order_id") or "")
    r.api.call("POST", f"/v1/payments/orders/{f['payment_order_id']}/simulate", SUNITA, {"outcome": "succeeded"})
    r.api.call("POST", f"/v1/contracts/{cid}/milestones/{mid}/submit", MEENA, {"note": "Counter served 300 guests."})
    st, c = r.api.call("POST", f"/v1/contracts/{cid}/milestones/{mid}/approve", SUNITA)
    check(st == 200 and c["milestones"][0]["state"] == "released", "the stage is released")

    # Hires count after 30 days: this run moves its own three hires back 31 days.
    await r.db.execute("UPDATE vyapar_enquiries.enquiries SET stage_changed_at = now() - interval '31 days' WHERE id = ANY($1::uuid[])",
                       [apps[RAVI], apps[SURESH], apps[MEENA]])
    st, res = r.api.call("POST", "/v1/trust/jobs/run", OPERATOR)
    check(st == 200 and res["paid_on_time_asked"] >= 3, f"the trust pass asks the paid people ({res})")
    asks = {x["source_id"]: x for x in await r.db.fetch(
        "SELECT id::text, source_kind, source_id::text, payee_id, payer_id FROM vyapar_reviews.paid_on_time_asks WHERE payer_id = $1", SUNITA)}
    r.extra_ids.update(x["id"] for x in asks.values())
    check(apps[RAVI] in asks and apps[SURESH] in asks and mid in asks and apps[MEENA] not in asks,
          "asked: Ravi and Suresh (hired 30+ days), Meena for the released stage (not twice)")
    check(all(a["payee_id"] != SUNITA for a in asks.values()), "the payer is never the one asked")
    st, res2 = r.api.call("POST", "/v1/trust/jobs/run", OPERATOR)
    n_after = await r.db.fetchval("SELECT count(*) FROM vyapar_reviews.paid_on_time_asks WHERE payer_id = $1", SUNITA)
    check(n_after == len(asks), "a second pass asks nobody twice")

    st, ravi_asks = r.api.call("GET", "/v1/paid-on-time/asks", RAVI, lang="hi")
    ra = next((a for a in ravi_asks if a["id"] == asks[apps[RAVI]]["id"]), None)
    check(ra is not None and has_script(ra["question"], "ऀ", "ॿ") and ra["payer_name"] == "Sunita Kapoor",
          f"Ravi sees the question in Hindi ({ra['question'] if ra else None})")
    st, notes = r.api.call("GET", "/v1/notifications", RAVI)
    check(any(n["kind"] == "paidOnTimeAsk" for n in notes), "and got one notification")
    st, sunita_asks = r.api.call("GET", "/v1/paid-on-time/asks", SUNITA, {} if False else None)
    check(st == 200 and not any(a["id"] in {x["id"] for x in asks.values()} for a in sunita_asks), "the payer cannot list the questions about her")
    st, res = r.api.call("POST", f"/v1/paid-on-time/asks/{asks[apps[RAVI]]['id']}/answer", SUNITA, {"paid_on_time": True})
    check(st == 404 and code(res) == "paid_on_time_ask_not_found", "the payer cannot answer for the payee")

    st, a1 = r.api.call("POST", f"/v1/paid-on-time/asks/{asks[apps[RAVI]]['id']}/answer", RAVI, {"paid_on_time": True})
    check(st == 200 and a1["answer"] is True, "Ravi: yes")
    st, res = r.api.call("POST", f"/v1/paid-on-time/asks/{asks[apps[RAVI]]['id']}/answer", RAVI, {"paid_on_time": False})
    check(st == 409 and code(res) == "paid_on_time_already_answered", "an answer is final")
    r.api.call("POST", f"/v1/paid-on-time/asks/{asks[apps[SURESH]]['id']}/answer", SURESH, {"paid_on_time": False})
    st, s = r.api.call("GET", f"/v1/members/{SUNITA}/paid-on-time", RAVI)
    check(st == 200 and s["shown"] is False and s["label"] is None and s["answered"] == 0, "two answers: nothing is shown yet (fewer than 3)")
    r.api.call("POST", f"/v1/paid-on-time/asks/{asks[mid]['id']}/answer", MEENA, {"paid_on_time": True})
    st, s = r.api.call("GET", f"/v1/members/{SUNITA}/paid-on-time", RAVI)
    check(s["shown"] and s["label"] == "Paid on time: 2 of 3" and s["answered"] == 3 and s["paid_on_time"] == 2, f"three answers: '{s.get('label')}'")
    st, s_hi = r.api.call("GET", f"/v1/members/{SUNITA}/paid-on-time", RAVI, lang="hi")
    check(s_hi["label"] == "समय पर पेमेंट: 3 में से 2", f"in Hindi: '{s_hi.get('label')}'")
    sunita_listing = await r.db.fetchval(
        "SELECT id::text FROM vyapar_listings.listings WHERE owner_id = $1 AND state IN ('active_verified','active_unverified')", SUNITA)
    st, prof = r.api.call("GET", f"/v1/listings/{sunita_listing}", GAURAV)
    check((prof.get("paid_on_time") or {}).get("label") == "Paid on time: 2 of 3", "on Sunita's profile")
    st, det = r.api.call("GET", f"/v1/opportunities/{r.honest_job}", GAURAV)
    check((det.get("poster_paid_on_time") or {}).get("label") == "Paid on time: 2 of 3", "and on her open posts")
    r.fill_job = jid


async def section_restrictions(r: Run) -> None:
    print("\n== 3. Every restriction has a reason and a human appeal ==")
    st, job = r.post(SUNITA, {"type": "employment", "title": "Tandoor helper for the Secunderabad kitchen",
                               "description": "Help the tandoor cook with dough, skewers and cleaning, evening shift.",
                               "required_capabilities": ["catering"], "structured": {"salary_min_paise": 1300000, "salary_max_paise": 1500000}})
    jid = job["id"]
    for reporter, text in ((VIKRAM, "Their manager asked me to pay ₹1,000 on the phone before the trial day."),
                           (RAHUL, "When I called they asked for a ₹1,000 deposit.")):
        st, _ = r.api.call("POST", "/v1/reports", reporter, {"object_kind": "opportunity", "object_id": jid, "reason": "asked_for_money",
                                                             "evidence_text": text})
    state = await r.db.fetchval("SELECT state FROM vyapar_opportunities.opportunities WHERE id = $1::uuid", jid)
    check(state == "paused", f"two independent reports pause the post ({state})")
    st, lst = r.api.call("GET", "/v1/me/restrictions", SUNITA)
    item = next((x for x in lst if x["object_id"] == jid), None) if st == 200 else None
    check(item is not None and item["restriction"] == "paused" and item["under_review"] and item["can_appeal"] and item["case_id"]
          and item["reason_code"] == "seeker_charge_reports" and item["appeal_link"] == "/moderation/outcomes",
          f"listMyRestrictions: paused, under review, appealable now ({item})")
    st, det = r.api.call("GET", f"/v1/opportunities/{jid}", SUNITA)
    check((det.get("restriction") or {}).get("case_id") == (item or {}).get("case_id"), "the poster's detail read carries the same restriction")
    case_id = item["case_id"] if item else None
    r.extra_ids.add(case_id or "")
    st, ap = r.api.call("POST", "/v1/appeals", SUNITA, {"case_id": case_id,
                        "text": "We never ask staff for money. The number on the post was an old manager's; he no longer works with us."})
    check(st == 201, f"the poster appeals the interim hold without waiting for a decision ({st} {code(ap)})")
    r.extra_ids.add(ap.get("appeal_id") or "")
    st, dec = r.api.call("POST", f"/v1/admin/appeals/{ap.get('appeal_id')}/decide", OPERATOR,
                         {"decision": "overturned", "reason_code": "appeal_evidence_accepted"})
    after = await r.db.fetchrow("SELECT state, state_reason FROM vyapar_opportunities.opportunities WHERE id = $1::uuid", jid)
    case = await r.db.fetchrow("SELECT state, action FROM vyapar_trust_safety.moderation_cases WHERE id = $1::uuid", case_id)
    check(st == 200 and after["state"] == "active" and after["state_reason"] is None and case["state"] == "actioned" and case["action"] == "restore",
          f"a person upholds the appeal: the post is live again and the case is closed ({dict(after)}, {dict(case)})")
    st, lst = r.api.call("GET", "/v1/me/restrictions", SUNITA)
    check(not any(x["object_id"] == jid for x in lst), "and it no longer shows as restricted")

    # Operator removal from the review queue: now a decided case with a notice.
    st, _ = r.api.call("POST", f"/v1/admin/opportunities-queue/{jid}/decide", OPERATOR, {"action": "remove", "reason": "duplicate"})
    st, lst = r.api.call("GET", "/v1/me/restrictions", SUNITA, lang="hi")
    item = next((x for x in lst if x["object_id"] == jid), None)
    check(item is not None and item["restriction"] == "removed" and item["can_appeal"] and not item["under_review"]
          and has_script(item["reason_label"], "ऀ", "ॿ"), f"a review-queue removal is appealable, with a Hindi reason ({item and item['reason_label']})")
    if item:
        r.extra_ids.add(item["case_id"])
    st, notes = r.api.call("GET", "/v1/notifications", SUNITA)
    check(any(n["kind"] == "moderationOutcome" and (n.get("link") or "") == "/moderation/outcomes" for n in notes),
          "the poster is told, with the appeal path")


async def section_profession(r: Run) -> None:
    print("\n== 4. Profession-aware profiles ==")
    kavita = await r.db.fetchval("SELECT id::text FROM vyapar_listings.listings WHERE owner_id = $1 AND state = 'active_verified'", KAVITA)
    deepak = await r.db.fetchval("SELECT id::text FROM vyapar_listings.listings WHERE owner_id = $1 AND state = 'active_verified'", DEEPAK)
    r.kavita_listing = kavita
    st, pub = r.api.call("GET", f"/v1/listings/{kavita}", RAVI)
    prof = pub.get("profession") or {}
    check(prof.get("profession") == "advocate" and prof.get("restricted") and prof.get("contact_label") == "Contact"
          and prof.get("regulator") == "Bar Council of India" and "Rule 36" in prof.get("rule_reference", ""),
          "Kavita Dhawan's profile names the rule: advocate, Bar Council of India, Rule 36")
    check(pub["headline"] is None and pub["description"] is None and pub["reputation"] is None and pub["packages"] == []
          and pub["sponsored"] is False and pub["rates"] is None, "others see no headline, pitch, reviews, prices or promotion")
    check(pub["name"] == "Kavita Dhawan" and pub["locality"] and pub["capability_labels"] and pub["languages"] is not None,
          "name, practice areas, languages and locality stay")
    check(not any(b["key"] in ("reliable", "top_recommended", "rising", "repeat_hires", "responds_fast", "verified_business") for b in pub["badges"]),
          f"no ranking badges, and no 'Verified business owner' for a Bar Council credential ({[b['key'] for b in pub['badges']]})")
    st, own = r.api.call("GET", f"/v1/listings/{kavita}", KAVITA)
    check(own["headline"] and "headline" in own["profession"]["hidden_fields"] and own["profession"]["note"],
          "the owner still sees her own text, and which fields others do not see")
    st, res = r.api.call("POST", "/v1/promotions", KAVITA, {"target_kind": "listing", "target_id": kavita, "product_id": "boost_7d"})
    check(st == 403 and code(res) == "promotion_not_permitted_for_profession", f"promotion refused: 403 promotion_not_permitted_for_profession ({st})")
    st, opt = r.api.call("GET", f"/v1/promotions/options?target_kind=listing&target_id={kavita}", KAVITA)
    check(st == 200 and opt["eligible"] is False and opt["reason"] == "notPermittedForProfession" and opt["products"] == [],
          "promotion options: not eligible, no products offered")
    st, res = r.api.call("PUT", f"/v1/listings/{kavita}/packages", KAVITA, {"packages": [{"tier": "basic", "name": "Rent agreement drafting",
                                                                                        "price_paise": 250000}]})
    check(st == 403 and code(res) == "packages_not_permitted_for_profession", "price packages refused")
    st, reviews = r.api.call("GET", f"/v1/listings/{kavita}/reviews", RAVI)
    check(st == 200 and (reviews if isinstance(reviews, list) else reviews.get("items", [])) == [], "no public reviews")
    st, sr = r.api.call("GET", "/v1/listings/search?q=Kavita", RAVI)
    hit = next((x for x in sr.get("results", []) if x["listing"]["id"] == kavita), None)
    check(hit is not None and hit["relevance_reason"] == "matchesFilters" and hit["listing"]["reputation"] is None,
          "still found in search, with a neutral reason and no counts")

    st, dpub = r.api.call("GET", f"/v1/listings/{deepak}", RAVI)
    check((dpub.get("profession") or {}).get("profession") == "architect" and dpub["headline"] is None,
          "Deepak Bhalla (architecture skill) is an architect profile: same limits (Council of Architecture)")
    st, res = r.api.call("POST", "/v1/promotions", DEEPAK, {"target_kind": "listing", "target_id": deepak, "product_id": "boost_7d"})
    check(st == 403 and code(res) == "promotion_not_permitted_for_profession", "an architect cannot promote either")
    # A promotion bought before the rule existed (inserted as history would have it) is cancelled by the pass.
    product = await r.db.fetchrow("SELECT id, version, price_paise FROM vyapar_commercial.products WHERE id = 'boost_7d' ORDER BY version DESC LIMIT 1")
    legacy = await r.db.fetchval(
        """INSERT INTO vyapar_commercial.promotions (owner_id, target_kind, target_id, product_id, product_version, price_paise, tax_paise,
             state, starts_at, ends_at) VALUES ($1, 'listing', $2::uuid, $3, $4, $5, 0, 'active', now(), now() + interval '7 days') RETURNING id::text""",
        DEEPAK, deepak, product["id"], product["version"], product["price_paise"])
    r.extra_ids.add(legacy)
    st, res = r.api.call("POST", "/v1/trust/jobs/run", OPERATOR)
    row = await r.db.fetchrow("SELECT state, reject_reason FROM vyapar_commercial.promotions WHERE id = $1::uuid", legacy)
    check(res.get("promotions_cancelled", 0) >= 1 and row["state"] == "cancelled" and row["reject_reason"] == "profession_rules",
          f"a promotion from before the rule is cancelled by the trust pass ({dict(row)})")
    st, notes = r.api.call("GET", "/v1/notifications", DEEPAK)
    check(any(n["kind"] == "promotionCancelledProfession" and legacy in (n.get("link") or "") for n in notes), "and the owner is told why")

    st, apub = r.api.call("GET", f"/v1/listings/{r.anita_listing}", RAVI)
    ap = apub.get("profession") or {}
    check(ap.get("profession") == "chartered_accountant" and ap.get("restricted") is False and apub["headline"]
          and "non-assurance" in (ap.get("note") or ""), "a CA gets a wording note and no restriction (ICAI, from 1 Apr 2026)")
    st, opt = r.api.call("GET", f"/v1/promotions/options?target_kind=listing&target_id={r.anita_listing}", ANITA)
    check(opt.get("reason") != "notPermittedForProfession", "and may still promote")
    st, rules = r.api.call("GET", "/v1/profession-rules", RAVI, lang="te")
    check(st == 200 and {x["profession"] for x in rules} >= {"advocate", "architect", "chartered_accountant"}
          and any(x["term_label"] == "లీగల్ సర్వీసులు" or has_script(x["term_label"], "ఀ", "౿") for x in rules),
          "listProfessionRules is data, labelled in the reader's language")


async def section_new_advocate_and_credentials(r: Run) -> None:
    print("\n== 4/5. A new advocate joins; council badge; operator suspension and appeal ==")
    await r.db.execute("SELECT vyapar_identity.ensure_member($1, $2, $3, $4)", r.test_member, "Farhan Qureshi", "+919800054321", "en")
    r.members.add(r.test_member)
    st, me = r.api.call("PATCH", "/v1/me/profile", r.test_member, {
        "locality": "Abids", "categories": ["legal"], "capabilities": ["property_law"], "languages": ["en", "hi", "te"],
        "headline": "Best property lawyer in Hyderabad, lowest fees guaranteed", "description": "Call now for a free consultation!"})
    check(st == 200 and me["profile"]["profession"]["profession"] == "advocate", f"a new advocate's profile is recognised from its category ({st})")
    lid = me["profile"]["id"]
    r.test_listing = lid
    for kind in ("privacy", "terms"):
        r.api.call("POST", f"/v1/legal/{kind}/accept", r.test_member, {})
    st, otp = r.api.call("POST", f"/v1/listings/{lid}/otp/request", r.test_member, {"phone": "+919800054321"})
    r.api.call("POST", f"/v1/listings/{lid}/otp/verify", r.test_member, {"code": otp.get("dev_code")})
    st, sub = r.api.call("POST", f"/v1/listings/{lid}/submit", r.test_member)
    check(st == 200 and sub["state"] == "active_unverified", f"published through the normal submit ({st} {sub.get('state')})")
    st, pub = r.api.call("GET", f"/v1/listings/{lid}", RAVI)
    check(pub["headline"] is None and pub["description"] is None, "the 'lowest fees guaranteed' pitch never reaches others")
    # Neutral order in "profiles that match your post": two advocates in Abids
    # with the same skill; the verified one gets no boost, so name decides.
    st, opp = r.post(SUNITA, {"type": "freelance", "title": "Lease deed and title check for our new Abids outlet",
                              "description": "Kapoor Caterers is leasing a shop in Abids and needs the lease deed drafted and the title checked.",
                              "location": "Abids", "required_capabilities": ["property_law"],
                              "structured": {"budget_type": "fixed", "budget_min_paise": 1500000, "budget_max_paise": 2500000}})
    st, cards = r.api.call("GET", f"/v1/opportunities/{opp.get('id')}/matching-profiles", SUNITA)
    order = [c["id"] for c in cards] if st == 200 else []
    kav = await r.db.fetchval("SELECT id::text FROM vyapar_listings.listings WHERE owner_id = $1 AND state = 'active_verified'", KAVITA)
    check(lid in order and kav in order and order.index(lid) < order.index(kav)
          and all(not c["reputation"] and not c["badges"] for c in cards if c["id"] in (lid, kav)),
          f"matching profiles: advocates in neutral name order, no verified-first boost, no counts ({[c['name'] for c in cards]})")
    kc = next((c for c in cards if c["id"] == kav), {})
    check((kc.get("profession") or {}).get("restricted") is True and kc.get("headline") is None and kc.get("reputation") is None
          and all(b["key"] == "verified_business" for b in kc.get("badges", [])),
          "the card carries the profession flags and no headline, counts or reputation badges")
    st, sim = r.api.call("GET", f"/v1/listings/{kav}/similar", RAVI)
    fc = next((c for c in sim if c["id"] == lid), {}) if st == 200 else {}
    check((fc.get("profession") or {}).get("profession") == "advocate" and fc.get("headline") is None,
          f"'Similar profiles' cards too ({[c['name'] for c in sim] if st == 200 else st})")

    # council register claims
    st, types = r.api.call("GET", "/v1/credentials/types", r.test_member)
    check(st == 200 and len(types) == 6 and next(t for t in types if t["credential_type"] == "coa_registration")["fixed_council"] == "Council of Architecture",
          "six registers offered, with fixed councils where there is one")
    st, res = r.api.call("POST", "/v1/me/profile/credentials", r.test_member, {"credential_type": "icai_membership", "registration_number": "21234"})
    check(st == 422 and code(res) == "credential_number_invalid", "ICAI number with 5 digits refused")
    st, res = r.api.call("POST", "/v1/me/profile/credentials", r.test_member, {"credential_type": "bar_council_enrolment",
                                                                                "registration_number": "TS/2451/2016", "council": "Telangana"})
    check(st == 422 and code(res) == "credential_council_invalid", "Bar Council must be named as a State Bar Council")
    st, res = r.api.call("POST", "/v1/me/profile/credentials", r.test_member, {"credential_type": "digilocker_document",
                                                                                "registration_number": "LLB2014OU5521", "council": "Osmania University"})
    check(st == 422 and code(res) == "credential_document_uri_invalid", "a DigiLocker document needs its DigiLocker URI")
    st, cred = r.api.call("POST", "/v1/me/profile/credentials", r.test_member, {
        "credential_type": "bar_council_enrolment", "registration_number": "ts / 2451 / 2016", "council": "Bar Council of Telangana",
        "registered_on": "2016-08-12"})
    check(st == 201 and cred["status"] == "claimed" and cred["registration_number"] == "TS/2451/2016" and cred["check_source"] == "dev_stub"
          and cred["checked_on"] is None and cred["checked_on_label"] == "Pending check" and cred["verification_record_id"],
          f"claimed; the dev stub checked nothing and says so; queued for an operator ({cred.get('status')}, {cred.get('check_source')})")
    r.extra_ids.update({cred.get("id") or "", cred.get("verification_record_id") or ""})
    st, res = r.api.call("POST", "/v1/me/profile/credentials", r.test_member, {
        "credential_type": "bar_council_enrolment", "registration_number": "TS/2451/2016", "council": "Bar Council of Telangana"})
    check(st == 409 and code(res) == "credential_exists", "one entry per register")
    st, pub = r.api.call("GET", f"/v1/listings/{lid}", RAVI)
    badge = next(iter(pub.get("council_badges") or []), {})
    check(badge.get("label") == "Bar Council of Telangana: pending check" and badge.get("status") == "claimed" and pub["credential_verified"] is False,
          f"the public badge reads 'pending check' and nothing claims verification ({badge.get('label')})")
    st, queue = r.api.call("GET", "/v1/admin/verification-queue", OPERATOR)
    check(any(q["id"] == cred["verification_record_id"] and "TS/2451/2016" in (q["credential_name"] or "") and q["issuer"] == "Bar Council of Telangana"
              for q in queue), "it is in the existing operator verification queue with council and number")
    st, _ = r.api.call("POST", f"/v1/admin/verification-queue/{cred['verification_record_id']}/verify", OPERATOR, {"reason_code": "register_checked"})
    st, pub = r.api.call("GET", f"/v1/listings/{lid}", RAVI)
    badge = next(iter(pub.get("council_badges") or []), {})
    today = datetime.now(timezone(timedelta(minutes=330))).date()
    month = today.strftime("%b")
    check(badge.get("status") == "verified" and badge.get("label") == "Registered with Bar Council of Telangana"
          and badge.get("check_source") == "operator" and badge.get("checked_on_label") == f"Checked on {today.day} {month} {today.year}"
          and pub["credential_verified"] is True, f"after a person checked the register: '{badge.get('label')} · {badge.get('checked_on_label')}'")
    st, pub_hi = r.api.call("GET", f"/v1/listings/{lid}", RAVI, lang="hi")
    check(has_script((pub_hi.get("council_badges") or [{}])[0].get("checked_on_label"), "ऀ", "ॿ"), "the badge in Hindi")

    # operator suspension -> appeal -> restored
    st, _ = r.api.call("POST", f"/v1/listings/{lid}/suspend?reason=fake_listing", OPERATOR)
    st, lst = r.api.call("GET", "/v1/me/restrictions", r.test_member)
    item = next((x for x in lst if x["object_id"] == lid), None)
    check(item is not None and item["restriction"] == "suspended" and item["can_appeal"] and item["case_id"],
          f"an operator suspension is now a decided case the member can appeal ({item and item['restriction']})")
    st, prof = r.api.call("GET", "/v1/me/profile", r.test_member)
    check(((prof.get("profile") or {}).get("restriction") or {}).get("case_id") == (item or {}).get("case_id"), "shown on the member's own profile read")
    st, notes = r.api.call("GET", "/v1/notifications", r.test_member)
    check(any(n["kind"] == "moderationOutcome" for n in notes), "and told, with the appeal path")
    if item:
        r.extra_ids.add(item["case_id"])
        st, ap = r.api.call("POST", "/v1/appeals", r.test_member, {"case_id": item["case_id"],
                            "text": "I am enrolled with the Bar Council of Telangana, TS/2451/2016; the register shows my name."})
        r.extra_ids.add(ap.get("appeal_id") or "")
        st, _ = r.api.call("POST", f"/v1/admin/appeals/{ap.get('appeal_id')}/decide", OPERATOR, {"decision": "overturned", "reason_code": "appeal_evidence_accepted"})
        state = await r.db.fetchval("SELECT state FROM vyapar_listings.listings WHERE id = $1::uuid", lid)
        check(state in ("active_unverified", "active_verified"), f"an upheld appeal restores the profile ({state})")


# ---------------------------------------------------------------------------
async def main(api_base: str) -> int:
    api = Api(api_base)
    db = await asyncpg.connect(owner_dsn())
    r = Run(api, db)
    started_at = await db.fetchval("SELECT now()")
    r.started_at = started_at
    # detail reads of seeded profiles record a "recently viewed" row for the reader: restored at the end
    r.views_before = {(x["member_id"], str(x["listing_id"])): (x["viewed_at"], x["saved_at"]) for x in await db.fetch(
        "SELECT * FROM vyapar_listings.member_listing WHERE member_id = ANY($1::text[])", sorted(r.members))}
    counters = {(x["rate_limit_key"], x["window_start"]): x["hit_count"] for x in await db.fetch(
        """SELECT * FROM vyapar_platform.rate_limit_counter
            WHERE rate_limit_key LIKE ANY(ARRAY['enquiry:%','report:%','listing_search:%','precall%'])""")}
    try:
        for section in (section_scam_shield, section_honest_terms, section_close_loop, section_paid_on_time,
                        section_restrictions, section_profession, section_new_advocate_and_credentials):
            try:
                await section(r)
            except Exception as exc:  # a crash in one section is a failure, never a skipped cleanup
                import traceback

                traceback.print_exc()
                check(False, f"{section.__name__} crashed: {exc!r}")
    finally:
        await cleanup(r, counters)
        await db.close()
    failed = [label for ok, label in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    for label in failed:
        print("  failed:", label)
    return 1 if failed else 0


async def cleanup(r: Run, counters: dict) -> None:
    print("\n== Cleanup ==")
    db, started_at = r.db, r.started_at
    if r.opps:
        r.enquiries.update(x["id"] for x in await db.fetch(
            "SELECT id::text FROM vyapar_enquiries.enquiries WHERE opportunity_id = ANY($1::uuid[])", list(r.opps)))
    contract_ids = [x["id"] for x in await db.fetch(
        "SELECT id::text FROM vyapar_contracts.contracts WHERE enquiry_id = ANY($1::uuid[])", list(r.enquiries))]
    milestone_ids = [x["id"] for x in await db.fetch(
        "SELECT id::text FROM vyapar_contracts.contract_milestones WHERE contract_id = ANY($1::uuid[])", contract_ids)]
    order_ids = [x["id"] for x in await db.fetch(
        "SELECT id::text FROM vyapar_payments.payment_orders WHERE ref_id = ANY($1::uuid[])", milestone_ids)]
    listing_ids = [x["id"] for x in await db.fetch("SELECT id::text FROM vyapar_listings.listings WHERE owner_id = $1", r.test_member)]
    object_ids = list(r.opps) + listing_ids
    case_ids = [x["id"] for x in await db.fetch(
        "SELECT id::text FROM vyapar_trust_safety.moderation_cases WHERE object_id = ANY($1::uuid[])", object_ids)]
    ask_ids = [x["id"] for x in await db.fetch(
        "SELECT id::text FROM vyapar_reviews.paid_on_time_asks WHERE source_id = ANY($1::uuid[])", list(r.enquiries) + milestone_ids)]
    record_ids = [x["id"] for x in await db.fetch(
        "SELECT id::text FROM vyapar_listings.verification_records WHERE listing_id = ANY($1::uuid[])", listing_ids)]
    promo_ids = [i for i in r.extra_ids if i and await db.fetchval(
        "SELECT EXISTS (SELECT 1 FROM vyapar_commercial.promotions WHERE id::text = $1)", i)]
    ids = sorted({i for i in (set(r.opps) | r.enquiries | set(contract_ids) | set(milestone_ids) | set(order_ids) | set(listing_ids)
                              | set(case_ids) | set(ask_ids) | set(record_ids) | set(promo_ids) | {x for x in r.extra_ids if x}) if i}
                 | {r.test_member})
    patterns = [f"%{i}%" for i in ids]
    n: dict[str, str] = {}
    async with db.transaction():
        n["notifications"] = await db.execute(
            """DELETE FROM vyapar_integration.notifications WHERE created_at >= $1
                AND (link LIKE ANY($2) OR params::text LIKE ANY($2) OR idempotency_key LIKE ANY($2) OR member_id = $3)""",
            started_at, patterns, r.test_member)
        n["webhook_deliveries"] = await db.execute(
            "DELETE FROM vyapar_integration.webhook_deliveries WHERE created_at >= $1 AND payload::text LIKE ANY($2)", started_at, patterns)
        for table in ("vyapar_enquiries.outbox_event", "vyapar_opportunities.outbox_event", "vyapar_reviews.outbox_event",
                      "vyapar_listings.outbox_event", "vyapar_commercial.outbox_event"):
            n[table] = await db.execute(f"DELETE FROM {table} WHERE created_at >= $1 AND payload::text LIKE ANY($2)", started_at, patterns)
        n["audit_events"] = await db.execute(
            """DELETE FROM vyapar_integration.audit_events WHERE at >= $1 AND (object_id LIKE ANY($2) OR details::text LIKE ANY($2)
                 OR actor_id = $3 OR (action = 'trust.seeker_charge_blocked' AND actor_id = ANY($4::text[])))""",
            started_at, patterns, r.test_member, sorted(r.members))
        n["paid_on_time_asks"] = await db.execute("DELETE FROM vyapar_reviews.paid_on_time_asks WHERE id = ANY($1::uuid[])", ask_ids)
        n["moderation_cases"] = await db.execute("DELETE FROM vyapar_trust_safety.moderation_cases WHERE id = ANY($1::uuid[])", case_ids)
        n["review_invites"] = await db.execute(
            "DELETE FROM vyapar_reviews.review_invites WHERE interaction_kind = 'enquiry' AND interaction_id = ANY($1::uuid[])", list(r.enquiries))
        n["payment_orders"] = await db.execute("DELETE FROM vyapar_payments.payment_orders WHERE id = ANY($1::uuid[])", order_ids)
        n["contracts"] = await db.execute("DELETE FROM vyapar_contracts.contracts WHERE id = ANY($1::uuid[])", contract_ids)
        n["impressions"] = await db.execute(
            "DELETE FROM vyapar_commercial.impressions WHERE at >= $1 AND target_id = ANY($2::uuid[])", started_at, object_ids)
        n["analytics_events"] = await db.execute(
            "DELETE FROM vyapar_analytics.analytics_events WHERE at >= $1 AND object_id = ANY($2::text[])", started_at, ids)
        n["commercial_order_history"] = await db.execute(
            "DELETE FROM vyapar_commercial.commercial_order_history WHERE order_id = ANY($1::uuid[])", promo_ids)
        n["promotions"] = await db.execute("DELETE FROM vyapar_commercial.promotions WHERE id = ANY($1::uuid[])", promo_ids)
        n["enquiries"] = await db.execute("DELETE FROM vyapar_enquiries.enquiries WHERE id = ANY($1::uuid[])", list(r.enquiries))
        for table in ("vyapar_opportunities.member_opportunity",):
            n[table] = await db.execute(f"DELETE FROM {table} x WHERE x::text LIKE ANY($1)", patterns)
        n["opportunities"] = await db.execute("DELETE FROM vyapar_opportunities.opportunities WHERE id = ANY($1::uuid[])", list(r.opps))
        # the new advocate: profile (credentials, records, contacts cascade), OTPs, views, acceptances, the member
        n["member_listing"] = await db.execute("DELETE FROM vyapar_listings.member_listing WHERE listing_id = ANY($1::uuid[]) OR member_id = $2",
                                               listing_ids, r.test_member)
        n["otp_challenges"] = await db.execute("DELETE FROM vyapar_listings.otp_challenges WHERE member_id = $1", r.test_member)
        n["listings"] = await db.execute("DELETE FROM vyapar_listings.listings WHERE owner_id = $1", r.test_member)
        for schema, table, col in (("vyapar_privacy", "privacy_settings", "member_id"), ("vyapar_privacy", "acceptances", "member_id"),
                                   ("vyapar_platform", "idempotency_key", "member_id")):
            await db.execute(f"DELETE FROM {schema}.{table} WHERE {col} = $1", r.test_member)
        n["members"] = await db.execute("DELETE FROM vyapar_identity.members WHERE id = $1", r.test_member)
        # rate-limit counters: back to exactly what they were
        now_rows = await db.fetch(
            """SELECT * FROM vyapar_platform.rate_limit_counter
                WHERE rate_limit_key LIKE ANY(ARRAY['enquiry:%','report:%','listing_search:%','precall%'])""")
        for x in now_rows:
            key = (x["rate_limit_key"], x["window_start"])
            if key in counters:
                await db.execute("UPDATE vyapar_platform.rate_limit_counter SET hit_count = $3 WHERE rate_limit_key = $1 AND window_start = $2",
                                 key[0], key[1], counters[key])
            elif any(m in x["rate_limit_key"] for m in r.members):
                await db.execute("DELETE FROM vyapar_platform.rate_limit_counter WHERE rate_limit_key = $1 AND window_start = $2", key[0], key[1])
        # "recently viewed" rows this run's reads added or moved
        for x in await db.fetch("SELECT * FROM vyapar_listings.member_listing WHERE member_id = ANY($1::text[]) AND viewed_at >= $2",
                                sorted(r.members), started_at):
            before = r.views_before.get((x["member_id"], str(x["listing_id"])))
            if before is None:
                await db.execute("DELETE FROM vyapar_listings.member_listing WHERE member_id = $1 AND listing_id = $2", x["member_id"], x["listing_id"])
            else:
                await db.execute("UPDATE vyapar_listings.member_listing SET viewed_at = $3, saved_at = $4 WHERE member_id = $1 AND listing_id = $2",
                                 x["member_id"], x["listing_id"], *before)
        seeded = [x["id"] for x in await db.fetch(
            "SELECT id::text FROM vyapar_listings.listings WHERE owner_id = ANY($1::text[]) AND state IN ('active_verified','active_unverified')",
            [KAVITA, DEEPAK, ANITA, SUNITA])]
        n["seeded_profile_impressions"] = await db.execute(
            "DELETE FROM vyapar_commercial.impressions WHERE at >= $1 AND member_id IS NULL AND target_id = ANY($2::uuid[])", started_at, seeded)
        n["seeded_profile_events"] = await db.execute(
            "DELETE FROM vyapar_analytics.analytics_events WHERE at >= $1 AND object_id = ANY($2::text[])", started_at, seeded)
        # badge caches recompute on the next read
        await db.execute("UPDATE vyapar_identity.members SET badges_computed_at = NULL WHERE id = ANY($1::text[])", sorted(r.members))
    for k, v in n.items():
        print(f"  {k}: {v}")
    leftovers = []
    for t in await db.fetch("SELECT schemaname, tablename FROM pg_tables WHERE schemaname LIKE 'vyapar\\_%' ORDER BY 1, 2"):
        count = await db.fetchval(f'SELECT count(*) FROM "{t["schemaname"]}"."{t["tablename"]}" x WHERE x::text LIKE ANY($1)', patterns)
        if count:
            leftovers.append(f"{t['schemaname']}.{t['tablename']}={count}")
    check(not leftovers, f"no leftover rows mention an id this run created ({', '.join(leftovers) or 'clean'})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--api", default=os.environ.get("VYAPAR_CHECK_API_BASE"), help="Base URL of a running Vyapar API (or VYAPAR_CHECK_API_BASE)")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # rupee sign, Hindi and Telugu on a Windows console
    if not args.api:
        parser.error("--api (or VYAPAR_CHECK_API_BASE) is required")
    sys.exit(asyncio.run(main(args.api)))

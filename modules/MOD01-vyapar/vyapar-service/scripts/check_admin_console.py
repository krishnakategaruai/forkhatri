"""End-to-end check for Vyapar's side of the Admin & Governance Console (ADR-012, TR-PLAT-01).

Walks the real product flow over the REST API as seeded members, against a
PRIVATE Vyapar API (never the owner's live 8011):

  access      a non-operator (m_priya) gets 403 on the manifest and every view;
              the seeded operator (m_neha_ops) sees all six views; host admin
              scopes simulated with the dev provider (X-Dev-Admin-Scopes) open
              exactly their views; an unknown scope opens nothing; a personal
              access token is refused; the /internal dashboard bridge needs the
              platform service key.
  commercial  m_vikram boosts his verified business (sandbox payment) -> the order
              appears in the commercial view -> detail -> refund.
  moderation  m_vikram reports the job ("asked me for money") -> urgent item ->
              a session-scoped moderator (m_priya + vyapar.moderate) sees it
              through RLS and limits it.
  appeals     m_rahul appeals -> appeals view -> the operator overturns it.
  verification m_rahul sends a GST certificate -> verification view -> ask for
              a clearer copy.
  opportunities m_rahul shares a forwarded job (unconfirmed fields) -> review
              queue -> return to the poster -> approve.
  disputes    m_vikram hires m_rahul through an enquiry and a contract, then
              opens a dispute -> disputes view -> closed with notes.
  members     person summary: plan/facts/flags, localized; 404 for no account.
  forkhatri   (with --forkhatri-api) a real platform session resolves through
              the corrected identity contract; admin_scopes arrive.

Everything it creates is deleted at the end (finally), seeded rows it touched
are restored, and a sweep over every vyapar_* table confirms no row still
mentions an id it created.

Usage (from vyapar-service/):
    .venv/Scripts/python scripts/check_admin_console.py --api http://127.0.0.1:<port> [--forkhatri-api http://127.0.0.1:<port2>]

The API must run with DEV_MODE=true, PAYMENT_GATEWAY=dev_sandbox and migration
024 applied. The --forkhatri-api instance runs with IDENTITY_PROVIDERS=bearer,forkhatri
against the identity service on IDENTITY_SERVICE_INTERNAL_URL. Cleanup connects
as the migration owner using ../07a-db-implementation/.env.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path

import asyncpg

POSTER, REPORTER, OPERATOR, OUTSIDER = "m_rahul", "m_vikram", "m_neha_ops", "m_priya"
BUYER = REPORTER
ALL_VIEWS = {"moderation", "verification", "opportunities", "appeals", "disputes", "commercial"}
UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
SERVICE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RESULTS: list[tuple[bool, str]] = []


def check(cond: bool, label: str) -> None:
    RESULTS.append((bool(cond), label))
    print(("  PASS  " if cond else "  FAIL  ") + label)


class Api:
    def __init__(self, base: str) -> None:
        self.base = base.rstrip("/")

    def call(self, method: str, path: str, member: str | None = None, body: dict | None = None, *,
             lang: str = "en", scopes: str | None = None, headers: dict | None = None) -> tuple[int, dict]:
        h = {"Content-Type": "application/json", "X-Vyapar-Language": lang}
        if member:
            h["X-Dev-Member-Id"] = member
        if scopes is not None:
            h["X-Dev-Admin-Scopes"] = scopes
        h.update(headers or {})
        req = urllib.request.Request(self.base + path, method=method, headers=h,
                                     data=json.dumps(body).encode() if body is not None else None)
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


def env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0].strip()
            if "=" in line:
                k, v = line.split("=", 1)
                values[k.strip()] = v.strip()
    return values


def owner_dsn() -> str:
    values = env_file(SERVICE_DIR.parent / "07a-db-implementation" / ".env")
    values.update({k: v for k, v in os.environ.items() if k.startswith("DB_")})
    return (f"postgres://{values['DB_OWNER_USER']}:{values['DB_OWNER_PASSWORD']}"
            f"@{values['DB_HOST']}:{values['DB_PORT']}/{values['DB_NAME']}")


def code(body: dict) -> str | None:
    return (body.get("error") or {}).get("code")


def find(items: list[dict], item_id: str) -> dict | None:
    return next((i for i in items if i.get("item_id") == item_id), None)


def no_raw_ids(item: dict) -> bool:
    return not any(UUID_RE.search(item.get(k) or "") for k in ("summary_text", "subject_title", "reason", "status_label"))


async def main(api_base: str, forkhatri_base: str | None) -> int:
    api = Api(api_base)
    db = await asyncpg.connect(owner_dsn())
    started_at = await db.fetchval("SELECT now()")
    listing = await db.fetchrow(
        """SELECT id::text, verification_state, state, state_reason, verification_document, verification_claim,
                  verified_at, verification_expires_at, updated_at
             FROM vyapar_listings.listings WHERE owner_id = $1 AND state IN ('active_verified','active_unverified')
            ORDER BY created_at LIMIT 1""", POSTER)
    if listing is None:
        print(f"no active listing for {POSTER}; seed data missing")
        return 2
    credits_before = {r["id"]: r["credit_paise"] for r in await db.fetch(
        "SELECT id::text, credit_paise FROM vyapar_commercial.promotions WHERE owner_id = ANY($1::text[]) AND credit_paise > 0", [POSTER, BUYER])}
    tracked: dict[str, set[str]] = {k: set() for k in (
        "opportunity", "promotion", "order", "case", "appeal", "verification", "enquiry", "contract", "token", "member")}
    counters = {"report": 0, "enquiry": 0}
    try:
        # ================================================================ access
        print("\n== Access ==")
        st, body = api.call("GET", "/vyapar/admin/manifest", OUTSIDER)
        check(st == 403 and code(body) == "admin_console_permission_required", f"non-operator: manifest 403 ({st} {code(body)})")
        for view in sorted(ALL_VIEWS):
            st, _ = api.call("GET", f"/vyapar/admin/{view}", OUTSIDER)
            check(st == 403, f"non-operator: {view} queue 403 ({st})")
        st, body = api.call("GET", f"/vyapar/admin/members/{POSTER}/summary", OUTSIDER)
        check(st == 403, f"non-operator: member summary 403 ({st})")

        st, manifest = api.call("GET", "/vyapar/admin/manifest", OPERATOR)
        views = {v["view_id"]: v for v in manifest.get("views", [])} if st == 200 else {}
        check(st == 200 and manifest.get("module_id") == "vyapar" and set(views) == ALL_VIEWS,
              f"seeded operator: manifest lists all six views ({st} {sorted(views)})")
        mod = views.get("moderation", {})
        check(mod.get("list_endpoint") == "/vyapar/admin/moderation" and mod.get("detail_endpoint") == "/vyapar/admin/moderation/{item_id}"
              and mod.get("action_endpoints") == ["/vyapar/admin/moderation/{item_id}/actions/{action_id}"]
              and mod.get("required_permission_scope") == "vyapar.moderate" and mod.get("nav_group") == "moderation",
              "descriptor paths are relative to the API base, with scope and nav group")
        check(views.get("verification", {}).get("required_permission_scope") == "vyapar.verify"
              and views.get("commercial", {}).get("required_permission_scope") == "vyapar.commercial"
              and views.get("disputes", {}).get("nav_group") == "disputes", "verification/commercial scopes and the disputes nav group")
        st, hi = api.call("GET", "/vyapar/admin/manifest", OPERATOR, lang="hi")
        st2, te = api.call("GET", "/vyapar/admin/manifest", OPERATOR, lang="te")
        hi_titles = {v["view_id"]: v["title"] for v in hi.get("views", [])}
        te_titles = {v["view_id"]: v["title"] for v in te.get("views", [])}
        check(hi_titles.get("appeals") == "अपीलें" and te_titles.get("appeals") == "అప్పీళ్లు" and views["appeals"]["title"] == "Appeals",
              "view titles are localized (en/hi/te)")

        st, m = api.call("GET", "/vyapar/admin/manifest", OUTSIDER, scopes="vyapar.verify")
        check(st == 200 and [v["view_id"] for v in m.get("views", [])] == ["verification"],
              f"dev admin scope vyapar.verify opens only the verification view ({st})")
        st, _ = api.call("GET", "/vyapar/admin/moderation", OUTSIDER, scopes="vyapar.verify")
        check(st == 403, f"...and not the moderation view ({st})")
        st, m = api.call("GET", "/vyapar/admin/manifest", OUTSIDER, scopes="vyapar.moderate")
        check(st == 200 and {v["view_id"] for v in m.get("views", [])} == {"moderation", "opportunities", "appeals", "disputes"},
              "vyapar.moderate opens moderation, opportunities, appeals and disputes")
        st, _ = api.call("GET", "/vyapar/admin/manifest", OUTSIDER, scopes="milavn.moderate")
        check(st == 403, f"another module's scope grants nothing in Vyapar ({st})")

        st, tok = api.call("POST", "/v1/integrations/tokens", OUTSIDER, {"name": "Admin console check", "scopes": ["read"], "expires_in_days": 1})
        check(st == 201 and tok.get("token"), f"member creates a personal access token ({st})")
        if st == 201:
            tracked["token"].add(tok["id"])
            bearer = {"Authorization": f"Bearer {tok['token']}"}
            st, body = api.call("GET", "/vyapar/admin/manifest", None, headers=bearer, scopes="vyapar.moderate")
            check(st == 403 and code(body) == "not_available_to_tokens", f"a token never reaches admin routes, even with a scope header ({st} {code(body)})")
            st, body = api.call("POST", "/vyapar/admin/moderation/moderation_case:00000000-0000-4000-8000-000000000000/actions/dismiss", None,
                                {"notes": "x"}, headers=bearer)
            check(st == 403 and code(body) == "not_available_to_tokens", f"...nor admin actions ({st})")

        service_key = env_file(SERVICE_DIR / ".env").get("IDENTITY_SERVICE_KEY", "")
        dash = f"/internal/v1/dashboard-summary/{listing['id']}"
        st, body = api.call("GET", dash)
        check(st == 401 and code(body) == "service_unauthorized", f"internal dashboard bridge without the service key: 401 ({st} {code(body)})")
        st, _ = api.call("GET", dash, headers={"X-ForKhatri-Service-Key": "wrong-key"})
        check(st == 401, f"...with a wrong key: 401 ({st})")
        st, body = api.call("GET", dash, headers={"X-ForKhatri-Service-Key": service_key})
        check(st in (200, 404) and (st == 404 or "name" in body), f"...with the platform service key: answered ({st})")
        st, _ = api.call("GET", dash, headers={"X-ForKhatri-Service-Key": service_key, "X-Forwarded-For": "203.0.113.9"})
        check(st == 404, f"...through the public edge (X-Forwarded-For): 404 ({st})")

        # ================================================================ a real job to work with
        print("\n== Setup: m_rahul posts a job ==")
        st, job = api.call("POST", "/v1/opportunities", POSTER, {
            "title": "Counter helper for electrical spares shop", "type": "employment",
            "description": "Help at the counter of our electrical spares shop near Abids: billing, stock and customer help. 10am to 7pm, Sundays off.",
            "location": "Abids, Hyderabad", "work_mode": "on_site", "response_method": "in_app", "source_segment": "community",
            "structured": {"salary_min_paise": 1400000, "salary_max_paise": 1800000, "openings": 1, "shift": "day"},
        })
        check(st == 201, f"job draft created ({st} {code(job)})")
        if st != 201:
            raise SystemExit(f"cannot continue: {job}")
        job_id = job["id"]
        tracked["opportunity"].add(job_id)
        st, job = api.call("POST", f"/v1/opportunities/{job_id}/publish", POSTER)
        check(st == 200 and job.get("state") == "active", f"job published ({st} {code(job)})")

        # ================================================================ commercial
        print("\n== Commercial view: a boost order and a refund ==")
        # Boosting needs a verified business, so the buyer is m_vikram (verified listing).
        boost_listing = await db.fetchrow(
            "SELECT id::text, name FROM vyapar_listings.listings WHERE owner_id = $1 AND state = 'active_verified' ORDER BY created_at LIMIT 1", BUYER)
        st, promo = api.call("POST", "/v1/promotions", BUYER, {"target_kind": "listing", "target_id": boost_listing["id"], "product_id": "boost_3d"})
        check(st == 201, f"m_vikram drafts a 3-day boost for his business ({st} {code(promo)})")
        promo_id = promo.get("id") or promo.get("promotion_id")
        if promo_id:
            tracked["promotion"].add(promo_id)
            st, bought = api.call("POST", f"/v1/promotions/{promo_id}/confirm-purchase", BUYER, {"confirmed": True})
            check(st == 200 and bought.get("payment_order_id"), f"confirm purchase opens a sandbox checkout ({st} {code(bought)})")
            if bought.get("payment_order_id"):
                tracked["order"].add(bought["payment_order_id"])
                st, paid = api.call("POST", f"/v1/payments/orders/{bought['payment_order_id']}/simulate", BUYER, {"outcome": "succeeded"})
                check(st == 200, f"sandbox payment succeeds ({st})")
            item_id = f"promotion_order:{promo_id}"
            st, queue = api.call("GET", "/vyapar/admin/commercial", OPERATOR)
            item = find(queue if st == 200 else [], item_id)
            check(item is not None and item["module_id"] == "vyapar" and item["priority"] == "normal" and item["reason"] == "Paid"
                  and boost_listing["name"] in item["summary_text"] and "₹" in item["summary_text"] and no_raw_ids(item),
                  f"the boost order is in the commercial view, in words ({item and item['summary_text']})")
            st, queue = api.call("GET", "/vyapar/admin/commercial", OUTSIDER, scopes="vyapar.commercial")
            check(st == 200 and find(queue, item_id) is not None, "a session-scoped vyapar.commercial operator sees it too (RLS)")
            st, detail = api.call("GET", f"/vyapar/admin/commercial/{item_id}", OPERATOR)
            actions = {a["action_id"]: a for a in detail.get("available_actions", [])}
            check(st == 200 and {"reject", "refund"} <= set(actions) and actions["refund"]["requires_reason"]
                  and actions["refund"]["reason_labels"].get("policy_other"), f"detail offers reject and refund with reasons ({sorted(actions)})")
            st, body = api.call("POST", f"/vyapar/admin/commercial/{item_id}/actions/refund", OPERATOR, {"notes": "Paid twice by mistake"})
            check(st == 422 and code(body) == "reason_required", f"an action that needs a reason refuses without one ({st} {code(body)})")
            st, body = api.call("POST", f"/vyapar/admin/commercial/{item_id}/actions/refund", OPERATOR, {"notes": "x", "reason_code": "spam"})
            check(st == 422 and code(body) == "reason_not_allowed", f"a reason from another list is refused ({st} {code(body)})")
            st, body = api.call("POST", f"/vyapar/admin/commercial/{item_id}/actions/approve", OPERATOR, {"notes": "x"})
            check(st == 409 and code(body) == "action_not_available", f"an action the item doesn't offer is refused ({st} {code(body)})")
            st, updated = api.call("POST", f"/vyapar/admin/commercial/{item_id}/actions/refund", OPERATOR,
                                   {"notes": "Member paid twice for the same boost; refunding in full.", "reason_code": "policy_other"})
            check(st == 200 and updated.get("item_id") == item_id and updated.get("reason") == "Refunded" and "refunded so far" in updated.get("summary_text", ""),
                  f"refund returns the updated item ({st} {updated.get('reason')})")
            st, detail = api.call("GET", f"/vyapar/admin/commercial/{item_id}", OPERATOR)
            labels = [h["label"] for h in detail.get("case_detail", {}).get("history", [])]
            notes = [h.get("notes") for h in detail.get("case_detail", {}).get("history", [])]
            check(any(l.startswith("Refund of ₹") for l in labels) and any(l.startswith("Admin Console: Refund") for l in labels)
                  and "Member paid twice for the same boost; refunding in full." in notes and "refund" not in {a["action_id"] for a in detail.get("available_actions", [])},
                  f"history shows the refund and the console action with notes; refund no longer offered ({labels})")
            n = await db.fetchval(
                "SELECT count(*) FROM vyapar_integration.audit_events WHERE action = 'refund_processed' AND object_id = $1", bought.get("payment_order_id"))
            c = await db.fetchval(
                "SELECT count(*) FROM vyapar_integration.audit_events WHERE action = 'admin_action.vyapar.commercial' AND object_id = $1", promo_id)
            check(n == 1 and c == 1, f"audited like the existing refund endpoint, plus one admin_action.vyapar.commercial event ({n}, {c})")

        # ================================================================ moderation
        print("\n== Moderation view: a job seeker reports a fee request ==")
        st, rep = api.call("POST", "/v1/reports", REPORTER, {
            "object_kind": "opportunity", "object_id": job_id, "reason": "asked_for_money",
            "evidence_text": "When I called, they said I must pay ₹1,500 as a uniform and training deposit before joining."})
        check(st == 201 and rep.get("received"), f"m_vikram reports the job ({st} {code(rep)})")
        counters["report"] += 1 if st == 201 else 0
        case_id = await db.fetchval(
            "SELECT id::text FROM vyapar_trust_safety.moderation_cases WHERE object_id = $1 AND state IN ('open','in_review','escalated')", job_id)
        if case_id:
            tracked["case"].add(case_id)
        item_id = f"moderation_case:{case_id}"
        st, queue = api.call("GET", "/vyapar/admin/moderation", OPERATOR)
        item = find(queue if st == 200 else [], item_id)
        check(item is not None and item["priority"] == "urgent" and item["due_at"] and item["reason"] == "Asked a job seeker for money"
              and "Counter helper" in item["summary_text"] and no_raw_ids(item),
              f"urgent item with a due time, in words ({item and item['summary_text']})")
        check(st == 200 and all(no_raw_ids(i) for i in queue) and all(i["item_id"].split(":")[0] == "moderation_case" for i in queue),
              "no queue item shows a raw id; review disputes stay in the disputes view")
        st, queue_hi = api.call("GET", "/vyapar/admin/moderation", OPERATOR, lang="hi")
        hi_item = find(queue_hi if st == 200 else [], item_id)
        check(hi_item is not None and hi_item["reason"] == "नौकरी खोजने वाले से पैसे माँगे", "the same item in Hindi")
        st, queue = api.call("GET", "/vyapar/admin/moderation", OUTSIDER, scopes="vyapar.moderate")
        check(st == 200 and find(queue, item_id) is not None, "a session-scoped moderator sees the case through RLS (vyapar.authz_permissions)")
        st, detail = api.call("GET", f"/vyapar/admin/moderation/{item_id}", OUTSIDER, scopes="vyapar.moderate")
        hist = detail.get("case_detail", {}).get("history", [])
        acts = {a["action_id"]: a for a in detail.get("available_actions", [])}
        check(st == 200 and any(h["action"] == "reported" and h["by"] == "A member (kept private)" and "uniform" in (h.get("notes") or "") for h in hist)
              and REPORTER not in json.dumps(detail),
              "detail history shows the report and its evidence, never the reporter")
        check({"dismiss", "limit", "remove", "suspend"} <= set(acts) and acts["dismiss"]["reason_codes"] == ["no_violation"]
              and "asked_for_money" in acts["limit"]["reason_codes"], f"graduated actions with reason codes ({sorted(acts)})")
        st, updated = api.call("POST", f"/vyapar/admin/moderation/{item_id}/actions/limit", OUTSIDER,
                               {"notes": "Deposit request confirmed by the caller; limiting while the poster responds.", "reason_code": "asked_for_money"},
                               scopes="vyapar.moderate")
        check(st == 200 and updated.get("status") == "actioned" and updated.get("status_label") == "Action taken",
              f"the session-scoped moderator limits it; updated item returned ({st} {updated.get('status')})")
        row = await db.fetchrow("SELECT state, action, operator_id FROM vyapar_trust_safety.moderation_cases WHERE id = $1::uuid", case_id)
        audit_row = await db.fetchrow(
            "SELECT actor_id, details FROM vyapar_integration.audit_events WHERE action = 'admin_action.vyapar.moderation' AND object_id = $1", case_id)
        details = json.loads(audit_row["details"]) if audit_row else {}
        check(row and row["action"] == "limit" and row["operator_id"] == OUTSIDER and audit_row and details.get("permission_source") == "session",
              "decided through decide_moderation_case; audited as a session-granted permission")
        limited = await db.fetchval("SELECT distribution_limited FROM vyapar_opportunities.opportunities WHERE id = $1::uuid", job_id)
        check(limited is True, "the job's distribution is limited (the existing graduated action ran)")

        # ================================================================ appeals
        print("\n== Appeals view ==")
        st, outcomes = api.call("GET", "/v1/moderation/outcomes", POSTER)
        mine = next((o for o in outcomes if o.get("case_id") == case_id), None) if st == 200 else None
        check(mine is not None and mine["can_appeal"], "m_rahul sees the decision and may appeal")
        st, appeal = api.call("POST", "/v1/appeals", POSTER, {
            "case_id": case_id, "text": "The deposit line was a mistake by my shop manager; we never charge staff. I have removed it and spoken to him."})
        check(st == 201, f"m_rahul appeals ({st} {code(appeal)})")
        appeal_id = appeal.get("appeal_id")
        if appeal_id:
            tracked["appeal"].add(appeal_id)
            item_id = f"appeal:{appeal_id}"
            st, queue = api.call("GET", "/vyapar/admin/appeals", OPERATOR)
            item = find(queue if st == 200 else [], item_id)
            check(item is not None and item["due_at"] and item["status"] == "open" and no_raw_ids(item) and "Rahul" in item["summary_text"],
                  f"appeal item with its 7-day due time ({item and item['summary_text']})")
            st, detail = api.call("GET", f"/vyapar/admin/appeals/{item_id}", OPERATOR)
            acts = {a["action_id"] for a in detail.get("available_actions", [])}
            labels = [h["action"] for h in detail.get("case_detail", {}).get("history", [])]
            check(st == 200 and acts == {"upheld", "overturned"} and "appeal_filed" in labels and "decided_limit" in labels,
                  f"detail: history has the decision and the appeal ({labels})")
            st, updated = api.call("POST", f"/vyapar/admin/appeals/{item_id}/actions/overturned", OPERATOR,
                                   {"notes": "Poster removed the deposit line and explained; first occurrence.", "reason_code": "appeal_evidence_accepted"})
            check(st == 200 and updated.get("status") == "overturned", f"overturned via decide_appeal ({st} {updated.get('status')})")
            limited = await db.fetchval("SELECT distribution_limited FROM vyapar_opportunities.opportunities WHERE id = $1::uuid", job_id)
            check(limited is False, "the job is restored")
            st, detail = api.call("GET", f"/vyapar/admin/appeals/{item_id}", OPERATOR)
            check(st == 200 and detail.get("available_actions") == [], "a decided appeal offers no more actions")

        # ================================================================ verification
        print("\n== Verification view ==")
        st, rec = api.call("POST", f"/v1/listings/{listing['id']}/verification", POSTER, {"document_type": "gst", "identifier": "36ABCDE1234F1Z5"})
        check(st == 201 and rec.get("identifier_masked"), f"m_rahul sends a GST certificate ({st} {code(rec)})")
        if st == 201:
            tracked["verification"].add(rec["id"])
            item_id = f"verification_record:{rec['id']}"
            st, queue = api.call("GET", "/vyapar/admin/verification", OUTSIDER, scopes="vyapar.verify")
            item = find(queue if st == 200 else [], item_id)
            check(item is not None and item["due_at"] and "GST certificate" in item["summary_text"] and no_raw_ids(item),
                  f"verification item with its 3-business-day target ({item and item['summary_text']})")
            st, detail = api.call("GET", f"/vyapar/admin/verification/{item_id}", OUTSIDER, scopes="vyapar.verify")
            cd = detail.get("case_detail", {})
            check(st == 200 and cd.get("identifier_masked") and "36ABCDE1234F1Z5" not in json.dumps(detail)
                  and {a["action_id"] for a in detail.get("available_actions", [])} == {"verify", "reject", "needs_clearer_copy"},
                  "detail shows the masked identifier only, with verify/reject/clearer-copy")
            st, updated = api.call("POST", f"/vyapar/admin/verification/{item_id}/actions/needs_clearer_copy", OUTSIDER,
                                   {"notes": "Photo is cut off at the bottom; GSTIN row not visible.", "reason_code": "document_illegible"},
                                   scopes="vyapar.verify")
            check(st == 200 and updated.get("status") == "needs_clearer_copy" and updated.get("reason") == "Document illegible / too blurry to read",
                  f"clearer copy requested via request_clearer_verification_copy ({st} {updated.get('status')})")

        # ================================================================ opportunities
        print("\n== Opportunities view: a shared forward ==")
        st, fwd = api.call("POST", "/v1/opportunities", POSTER, {
            "entry_mode": "share", "source_segment": "community", "type": "employment",
            "raw_input": "Hiring delivery rider for Begumpet medical store\nOwn two-wheeler needed. Evening shift. Call the store.",
        })
        check(st == 201 and fwd.get("state") == "draft", f"m_rahul shares a forwarded job; it has unconfirmed details ({st})")
        if st == 201:
            tracked["opportunity"].add(fwd["id"])
            item_id = f"opportunity_review:{fwd['id']}"
            st, queue = api.call("GET", "/vyapar/admin/opportunities", OPERATOR)
            item = find(queue if st == 200 else [], item_id)
            check(item is not None and "not confirmed" in (item["reason"] or "") and no_raw_ids(item),
                  f"review item says what needs checking ({item and item['summary_text']})")
            st, updated = api.call("POST", f"/vyapar/admin/opportunities/{item_id}/actions/return", OPERATOR,
                                   {"notes": "Please add the pay and the store's area.", "reason_code": "missing_details"})
            check(st == 200 and updated.get("status") == "draft", f"returned to the poster via decide_opportunity_review ({st})")
            st, updated = api.call("POST", f"/vyapar/admin/opportunities/{item_id}/actions/approve", OPERATOR, {"notes": "Store confirmed on call."})
            check(st == 200 and updated.get("status") == "active", f"an operator can approve a queued opportunity (fixed) ({st} {code(updated)})")
            st, detail = api.call("GET", f"/vyapar/admin/opportunities/{item_id}", OPERATOR)
            labels = [h["label"] for h in detail.get("case_detail", {}).get("history", [])]
            check(sum(1 for l in labels if l.startswith("Admin Console:")) == 2 and not any(l.startswith("Recorded action") for l in labels),
                  f"history: two console actions, each shown once ({labels})")

        # ================================================================ disputes
        print("\n== Disputes view: a contract dispute ==")
        st, enq = api.call("POST", "/v1/enquiries", REPORTER, {"listing_id": listing["id"], "message": "Need a licensed electrician to rewire two rooms at our Tarnaka flat next week."})
        check(st == 201, f"m_vikram enquires ({st} {code(enq)})")
        if st == 201:
            counters["enquiry"] += 1
            tracked["enquiry"].add(enq["id"])
            api.call("POST", f"/v1/enquiries/{enq['id']}/messages", POSTER, {"body": "Yes, I can do it on Tuesday and Wednesday."})
            api.call("POST", f"/v1/enquiries/{enq['id']}/accept", POSTER)
            st, c = api.call("POST", "/v1/contracts", REPORTER, {
                "enquiry_id": enq["id"], "title": "Rewiring two rooms, Tarnaka", "kind": "fixed", "total_paise": 1200000, "propose": True,
                "milestones": [{"title": "Rewiring and new switchboards", "amount_paise": 1200000, "due_date": str(date.today() + timedelta(days=10))}]})
            check(st == 201, f"contract proposed ({st} {code(c)})")
            if st == 201:
                tracked["contract"].add(c["id"])
                st, c = api.call("POST", f"/v1/contracts/{c['id']}/accept", POSTER)
                st, c = api.call("POST", f"/v1/contracts/{c['id']}/disputes", REPORTER,
                                 {"reason": "The electrician changed the agreed date twice and now asks for a higher price for the same work."})
                check(st == 201 and c.get("state") == "disputed", f"m_vikram opens a dispute ({st})")
                dispute_id = (c.get("disputes") or [{}])[0].get("id")
                item_id = f"contract_dispute:{dispute_id}"
                st, queue = api.call("GET", "/vyapar/admin/disputes", OPERATOR)
                item = find(queue if st == 200 else [], item_id)
                check(item is not None and "Rewiring two rooms" in item["summary_text"] and no_raw_ids(item),
                      f"dispute item in words ({item and item['summary_text']})")
                st, detail = api.call("GET", f"/vyapar/admin/disputes/{item_id}", OPERATOR)
                check(st == 200 and {a["action_id"] for a in detail.get("available_actions", [])} == {"resolved_client", "resolved_provider", "closed"}
                      and detail["case_detail"].get("held_amount") == "₹0", "detail: resolution choices and the held amount")
                st, updated = api.call("POST", f"/vyapar/admin/disputes/{item_id}/actions/closed", OPERATOR,
                                       {"notes": "Both agreed on the phone to keep the original price and a new date."})
                check(st == 200 and updated.get("status") == "closed", f"closed via resolve_dispute ({st} {code(updated)})")
                row = await db.fetchrow("SELECT d.notes, c.state FROM vyapar_contracts.contract_disputes d JOIN vyapar_contracts.contracts c ON c.id = d.contract_id WHERE d.id = $1::uuid", dispute_id)
                check(row and row["state"] == "active" and row["notes"].startswith("Both agreed"), "the contract continues; notes stored on the dispute")

        # ================================================================ member summary
        print("\n== Member summary ==")
        st, summ = api.call("GET", f"/vyapar/admin/members/{POSTER}/summary", OPERATOR)
        labels = {f["label"]: f["value"] for f in summ.get("facts", [])}
        check(st == 200 and set(summ) >= {"plan", "facts", "flags", "deep_link"} and "Business listings" in labels and "Paid to Vyapar so far" in labels,
              f"operator: summary with facts ({labels})")
        st, summ_te = api.call("GET", f"/vyapar/admin/members/{POSTER}/summary", OPERATOR, lang="te")
        check(st == 200 and any(f["label"] == "వ్యాపార లిస్టింగ్‌లు" for f in summ_te.get("facts", [])), "labels localized (Telugu)")
        st, summ_v = api.call("GET", f"/vyapar/admin/members/{POSTER}/summary", OUTSIDER, scopes="vyapar.verify")
        check(st == 200 and not any(f["label"] == "Paid to Vyapar so far" for f in summ_v.get("facts", [])), "a verify-only operator doesn't see money facts")
        st, body = api.call("GET", "/vyapar/admin/members/m_nobody_has_this_id/summary", OPERATOR)
        check(st == 404, f"no Vyapar account: 404 ({st})")
        st, plan_summary = api.call("GET", "/vyapar/admin/members/m_anita/summary", OPERATOR)
        check(st == 200 and (plan_summary.get("plan") is None or {"tier", "name", "status", "renews_at"} <= set(plan_summary["plan"])),
              f"plan shape when present ({plan_summary.get('plan')})")

        # ================================================================ forkhatri session
        if forkhatri_base:
            await forkhatri_checks(Api(forkhatri_base), db, tracked)
    finally:
        await cleanup(db, tracked, counters, started_at, listing, credits_before)
        await db.close()

    failed = [label for ok, label in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    for label in failed:
        print("  failed:", label)
    return 1 if failed else 0


async def forkhatri_checks(api: Api, db: asyncpg.Connection, tracked: dict[str, set[str]]) -> None:
    print("\n== ForKhatri session: corrected resolve contract ==")
    identity_dir = REPO_ROOT / "platform" / "identity-service"
    py = identity_dir / ".venv" / "Scripts" / "python.exe"
    out = subprocess.run([str(py), str(identity_dir / "scripts" / "dev_session.py"), "milavn-moderator", "--cookie-header"],
                         capture_output=True, text=True, cwd=str(identity_dir), timeout=60)
    line = next((l for l in out.stdout.splitlines() if l.startswith("Cookie: ")), None)
    check(line is not None, f"dev session opened for milavn-moderator ({out.stderr.strip()[:120]})")
    if line is None:
        return
    name, _, token = line.removeprefix("Cookie: ").partition("=")
    settings = env_file(SERVICE_DIR / ".env")
    identity_url = settings.get("IDENTITY_SERVICE_INTERNAL_URL", "").rstrip("/")
    try:
        req = urllib.request.Request(
            f"{identity_url}/internal/v1/sessions/resolve", method="POST", data=json.dumps({"session_token": token}).encode(),
            headers={"Content-Type": "application/json", "X-ForKhatri-Service": settings.get("IDENTITY_SERVICE_NAME", "vyapar"),
                     "X-ForKhatri-Service-Key": settings.get("IDENTITY_SERVICE_KEY", "")})
        with urllib.request.urlopen(req, timeout=10) as resp:
            claims = json.loads(resp.read())
        check("admin_scopes" in claims and "preferred_language" in claims,
              f"identity resolve answers Vyapar's headers with admin_scopes ({claims.get('admin_scopes')})")
        member_id = claims["member_id"]
        existed = await db.fetchval("SELECT EXISTS (SELECT 1 FROM vyapar_identity.members WHERE id = $1)", member_id)
        if not existed:
            tracked["member"].add(member_id)
        cookie = {"Cookie": f"{name}={token}"}
        st, me = api.call("GET", "/v1/integrations/me", None, headers=cookie)
        check(st == 200 and me.get("member_id") == member_id, f"Vyapar resolves the platform session (no longer 401/503) ({st})")
        st, body = api.call("GET", "/vyapar/admin/manifest", None, headers=cookie)
        vy = [s for s in claims.get("admin_scopes") or [] if s.startswith("vyapar.")]
        check((st == 403) if not vy else (st == 200), f"manifest follows the session's Vyapar scopes {vy or '(none)'} ({st})")
        st, body = api.call("GET", "/vyapar/admin/manifest", None, headers={**cookie, "X-Dev-Admin-Scopes": "vyapar.moderate"})
        check((st == 403) if not vy else (st == 200), f"the dev scope header is ignored on a platform session ({st})")
    finally:
        req = urllib.request.Request(f"{identity_url}/v1/auth/sign-out", method="POST", data=b"{}",
                                     headers={"Content-Type": "application/json", "Cookie": f"{name}={token}"})
        try:
            urllib.request.urlopen(req, timeout=10).read()
        except urllib.error.URLError:
            pass


async def cleanup(db: asyncpg.Connection, tracked: dict[str, set[str]], counters: dict[str, int], started_at, listing, credits_before) -> None:
    print("\n== Cleanup ==")
    opp_ids = list(tracked["opportunity"])
    enquiry_ids = list(tracked["enquiry"])
    tracked["case"].update(r["id"] for r in await db.fetch(
        "SELECT id::text FROM vyapar_trust_safety.moderation_cases WHERE object_id = ANY($1::uuid[])", opp_ids))
    tracked["appeal"].update(r["id"] for r in await db.fetch(
        "SELECT id::text FROM vyapar_trust_safety.appeals WHERE case_id = ANY($1::uuid[])", list(tracked["case"])))
    tracked["promotion"].update(r["id"] for r in await db.fetch(
        "SELECT id::text FROM vyapar_commercial.promotions WHERE target_id = ANY($1::uuid[])", opp_ids))
    tracked["order"].update(r["id"] for r in await db.fetch(
        "SELECT id::text FROM vyapar_payments.payment_orders WHERE ref_id = ANY($1::uuid[])", list(tracked["promotion"])))
    tracked["contract"].update(r["id"] for r in await db.fetch(
        "SELECT id::text FROM vyapar_contracts.contracts WHERE enquiry_id = ANY($1::uuid[])", enquiry_ids))
    extra = [r["id"] for r in await db.fetch(
        """SELECT id::text FROM vyapar_contracts.contract_milestones WHERE contract_id = ANY($1::uuid[])
           UNION ALL SELECT id::text FROM vyapar_contracts.contract_disputes WHERE contract_id = ANY($1::uuid[])""", list(tracked["contract"]))]
    ids = sorted(set().union(*[v for k, v in tracked.items() if k != "member"]) | set(extra))
    if not ids and not tracked["member"]:
        print("  nothing to clean")
        return
    patterns = [f"%{i}%" for i in ids] or ["%__none__%"]
    n: dict[str, str] = {}
    async with db.transaction():
        n["notifications"] = await db.execute(
            "DELETE FROM vyapar_integration.notifications WHERE created_at >= $1 AND (link LIKE ANY($2) OR params::text LIKE ANY($2) OR idempotency_key LIKE ANY($2))",
            started_at, patterns)
        n["webhook_deliveries"] = await db.execute(
            "DELETE FROM vyapar_integration.webhook_deliveries WHERE created_at >= $1 AND payload::text LIKE ANY($2)", started_at, patterns)
        for table in ("vyapar_opportunities.outbox_event", "vyapar_enquiries.outbox_event", "vyapar_reviews.outbox_event",
                      "vyapar_commercial.outbox_event", "vyapar_listings.outbox_event"):
            n[table] = await db.execute(f"DELETE FROM {table} WHERE created_at >= $1 AND payload::text LIKE ANY($2)", started_at, patterns)
        n["audit_events"] = await db.execute(
            "DELETE FROM vyapar_integration.audit_events WHERE at >= $1 AND (object_id LIKE ANY($2) OR details::text LIKE ANY($2))", started_at, patterns)
        n["access_tokens"] = await db.execute("DELETE FROM vyapar_integration.access_tokens WHERE id = ANY($1::uuid[])", list(tracked["token"]))
        n["moderation_cases"] = await db.execute("DELETE FROM vyapar_trust_safety.moderation_cases WHERE id = ANY($1::uuid[])", list(tracked["case"]))
        n["verification_records"] = await db.execute(
            "DELETE FROM vyapar_listings.verification_records WHERE id = ANY($1::uuid[])", list(tracked["verification"]))
        n["commercial_order_history"] = await db.execute(
            "DELETE FROM vyapar_commercial.commercial_order_history WHERE order_id = ANY($1::uuid[])", list(tracked["promotion"]))
        n["promotions"] = await db.execute("DELETE FROM vyapar_commercial.promotions WHERE id = ANY($1::uuid[])", list(tracked["promotion"]))
        n["payment_orders"] = await db.execute("DELETE FROM vyapar_payments.payment_orders WHERE id = ANY($1::uuid[])", list(tracked["order"]))
        n["contracts"] = await db.execute("DELETE FROM vyapar_contracts.contracts WHERE id = ANY($1::uuid[])", list(tracked["contract"]))
        n["review_invites"] = await db.execute(
            "DELETE FROM vyapar_reviews.review_invites WHERE interaction_kind = 'enquiry' AND interaction_id = ANY($1::uuid[])", enquiry_ids)
        n["enquiries"] = await db.execute("DELETE FROM vyapar_enquiries.enquiries WHERE id = ANY($1::uuid[])", enquiry_ids)
        n["impressions"] = await db.execute(
            """DELETE FROM vyapar_commercial.impressions WHERE target_id = ANY($1::uuid[])
                  OR (target_kind = 'listing' AND target_id = $2::uuid AND surface = 'enquiry' AND member_id IS NULL AND at >= $3)""",
            opp_ids, listing["id"], started_at)
        n["analytics_events"] = await db.execute(
            "DELETE FROM vyapar_analytics.analytics_events WHERE at >= $1 AND (object_id = ANY($2::text[]) OR props::text LIKE ANY($3))", started_at, ids, patterns)
        n["opportunities"] = await db.execute("DELETE FROM vyapar_opportunities.opportunities WHERE id = ANY($1::uuid[])", opp_ids)
        n["members"] = await db.execute("DELETE FROM vyapar_identity.members WHERE id = ANY($1::text[])", list(tracked["member"]))
        # Seeded rows this run touched, put back exactly.
        await db.execute(
            """UPDATE vyapar_listings.listings SET verification_state = $2, state = $3, state_reason = $4, verification_document = $5,
                 verification_claim = $6, verified_at = $7, verification_expires_at = $8, updated_at = $9 WHERE id = $1::uuid""",
            listing["id"], listing["verification_state"], listing["state"], listing["state_reason"], listing["verification_document"],
            listing["verification_claim"], listing["verified_at"], listing["verification_expires_at"], listing["updated_at"])
        for pid, credit in credits_before.items():
            await db.execute("UPDATE vyapar_commercial.promotions SET credit_paise = $2 WHERE id = $1::uuid", pid, credit)
        for kind, member in (("report", REPORTER), ("enquiry", REPORTER)):
            if counters[kind]:
                key = f"{kind}:{member}:day"
                await db.execute(
                    """UPDATE vyapar_platform.rate_limit_counter SET hit_count = greatest(hit_count - $2, 0)
                        WHERE rate_limit_key = $1 AND window_start = (SELECT max(window_start) FROM vyapar_platform.rate_limit_counter WHERE rate_limit_key = $1)""",
                    key, counters[kind])
                await db.execute("DELETE FROM vyapar_platform.rate_limit_counter WHERE rate_limit_key = $1 AND hit_count = 0", key)
    for k, v in n.items():
        print(f"  {k}: {v}")
    tables = await db.fetch("SELECT schemaname, tablename FROM pg_tables WHERE schemaname LIKE 'vyapar\\_%' ORDER BY 1, 2")
    leftovers = []
    sweep = patterns + [f"%{m}%" for m in tracked["member"]]
    for t in tables:
        count = await db.fetchval(f'SELECT count(*) FROM "{t["schemaname"]}"."{t["tablename"]}" x WHERE x::text LIKE ANY($1)', sweep)
        if count:
            leftovers.append(f"{t['schemaname']}.{t['tablename']}={count}")
    check(not leftovers, f"no leftover rows mention the test ids ({', '.join(leftovers) or 'clean'})")
    restored = await db.fetchval("SELECT verification_state FROM vyapar_listings.listings WHERE id = $1::uuid", listing["id"])
    check(restored == listing["verification_state"], f"seeded listing's verification state restored ({restored})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--api", default=os.environ.get("VYAPAR_CHECK_API_BASE"), help="Base URL of a private Vyapar API (dev provider)")
    parser.add_argument("--forkhatri-api", default=None, help="Optional: a second private API with IDENTITY_PROVIDERS=bearer,forkhatri")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if not args.api:
        parser.error("--api (or VYAPAR_CHECK_API_BASE) is required")
    sys.exit(asyncio.run(main(args.api, args.forkhatri_api)))

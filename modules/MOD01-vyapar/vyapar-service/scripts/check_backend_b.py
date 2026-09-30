"""End-to-end check for backend workstream B (migration 019).

What it does, as real members through the real API (dev header identity):
  * Anita Khatri (Khatri & Associates, verified CA firm, Banjara Hills) sets
    her call hours, a daily call cap and WhatsApp, and publishes two priced
    packages (basic GST filing, standard monthly bookkeeping).
  * Suresh Kohli (electrician, Dilsukhnagar) requests her basic package; she
    accepts; he gets Call/WhatsApp actions, calls once, and the second call is
    refused with daily_cap_reached. "matching_only" is checked too.
  * Sunita Kapoor (Kapoor Caterers) posts a kitchen-helper job; Suresh has a
    saved search with alerts that matches it; two members (Rahul, Gaurav)
    report "asked for money" and the job is paused and raised to High.
  * The "nobody charges job seekers" check, badges and the feed filters
    (distance sort, radius, salary sort, availability, near_you) are checked.

It starts its own uvicorn on a free private port, kills only that PID, and
removes every row it created (and restores the preferences and rate-limit
counters it touched) in a finally block, so the shared dev DB is left as it
was. Run from vyapar-service/:  .venv/Scripts/python scripts/check_backend_b.py
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import asyncpg
import httpx

SERVICE_DIR = Path(__file__).resolve().parents[1]
try:  # Hindi/Telugu details must print on a cp1252 Windows console too
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass
sys.path.insert(0, str(SERVICE_DIR))

OWNER_DSN = os.environ.get("VYAPAR_OWNER_DSN", "postgres://vyapar_owner:vyapar_owner_dev_password@localhost:5433/vyapar")
APP_DSN = os.environ.get("VYAPAR_APP_DSN", "postgres://vyapar_app:vyapar_app_dev_password@localhost:5433/vyapar")

ANITA, SURESH, SUNITA, RAHUL, GAURAV, RAVI = "m_anita", "m_suresh", "m_sunita", "m_rahul", "m_gaurav", "m_ravi"
ANITA_LISTING = "00000000-0000-4000-8000-000000000001"
PREF_COLS = ("call_hours_start", "call_hours_end", "call_days", "max_calls_per_day", "calls_from", "whatsapp_ok", "call_ok")
RATE_KEYS = [f"listing_search:m_rahul:minute", f"enquiry:{SURESH}:day", f"enquiry:{RAVI}:day", f"report:{RAHUL}:day", f"report:{GAURAV}:day", f"listing_search:{SURESH}:minute"]

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail and not ok else ""))


def free_port() -> int:
    for port in range(8091, 8099):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise SystemExit("no free port in 8091-8098")


class Api:
    def __init__(self, base: str) -> None:
        self.http = httpx.Client(base_url=base, timeout=30)

    def bearer(self, token: str, method: str, path: str, **kw):
        return self.http.request(method, path, headers={"Authorization": f"Bearer {token}"}, **kw)

    def call(self, member: str, method: str, path: str, lang: str = "en", **kw):
        return self.http.request(method, path, headers={"X-Dev-Member-Id": member, "X-Vyapar-Language": lang}, **kw)


async def snapshot(conn) -> dict:
    prefs = {m: dict(await conn.fetchrow(f"SELECT {', '.join(PREF_COLS)} FROM vyapar_identity.members WHERE id = $1", m))
             for m in (ANITA, SUNITA)}
    counters = {}
    for key in RATE_KEYS:
        counters[key] = [dict(r) for r in await conn.fetch(
            "SELECT window_start, window_seconds, hit_count, limit_max FROM vyapar_platform.rate_limit_counter WHERE rate_limit_key = $1", key)]
    return {"prefs": prefs, "counters": counters}


class _Safe:
    """Runs each cleanup statement on its own, so one failure never leaves
    the rest of this run's data behind; failures are reported at the end."""

    def __init__(self, conn) -> None:
        self.conn, self.errors = conn, []

    async def execute(self, sql: str, *args):
        try:
            return await self.conn.execute(sql, *args)
        except Exception as exc:  # noqa: BLE001 — report and carry on cleaning
            self.errors.append(f"{sql[:70]}: {exc}")


async def cleanup(raw_conn, snap: dict, created: dict) -> None:
    opp_ids = created["opportunities"]
    enq_ids = created["enquiries"]
    ids_text = [str(i) for i in opp_ids + enq_ids]
    conn = _Safe(raw_conn)
    if True:
        if created["contracts"]:
            await conn.execute("DELETE FROM vyapar_contracts.contracts WHERE id = ANY($1::uuid[])", created["contracts"])  # cascades milestones, ledger, events
            for cid in created["contracts"]:
                await conn.execute("DELETE FROM vyapar_integration.notifications WHERE params::text LIKE '%' || $1 || '%' OR link LIKE '%' || $1 || '%'", str(cid))
                await conn.execute("DELETE FROM vyapar_integration.audit_events WHERE object_id = $1 OR details::text LIKE '%' || $1 || '%'", str(cid))
        for tid in created["tokens"]:
            await conn.execute("DELETE FROM vyapar_integration.audit_events WHERE details::text LIKE '%' || $1 || '%'", str(tid))
        if created["tokens"]:
            await conn.execute("DELETE FROM vyapar_integration.access_tokens WHERE id = ANY($1::uuid[])", created["tokens"])
        await conn.execute("DELETE FROM vyapar_platform.idempotency_key WHERE member_id = ANY($1::text[]) AND created_at > $2",
                           [ANITA, SURESH, SUNITA, RAHUL, GAURAV], created["started"])
        if enq_ids:
            await conn.execute("DELETE FROM vyapar_enquiries.enquiries WHERE id = ANY($1::uuid[])", enq_ids)  # cascades messages + contact_attempts
        if opp_ids:
            await conn.execute("DELETE FROM vyapar_enquiries.contact_attempts WHERE opportunity_id = ANY($1::uuid[])", opp_ids)
            await conn.execute("DELETE FROM vyapar_enquiries.enquiries WHERE opportunity_id = ANY($1::uuid[])", opp_ids)
            await conn.execute("DELETE FROM vyapar_trust_safety.moderation_cases WHERE object_id = ANY($1::uuid[])", opp_ids)  # cascades reports
            await conn.execute("DELETE FROM vyapar_commercial.impressions WHERE target_id::text = ANY($1::text[])", [str(i) for i in opp_ids])
            await conn.execute("DELETE FROM vyapar_opportunities.member_opportunity WHERE opportunity_id = ANY($1::uuid[])", opp_ids)
            await conn.execute("DELETE FROM vyapar_opportunities.opportunities WHERE id = ANY($1::uuid[])", opp_ids)
        await conn.execute("DELETE FROM vyapar_commercial.impressions WHERE target_id::text = $1 AND at > $2", ANITA_LISTING, created["started"])
        await conn.execute("DELETE FROM vyapar_listings.listing_packages WHERE id = ANY($1::uuid[])", created["packages"])
        await conn.execute("DELETE FROM vyapar_opportunities.saved_searches WHERE id = ANY($1::uuid[])", created["searches"])
        for ident in ids_text:
            await conn.execute("DELETE FROM vyapar_integration.notifications WHERE params::text LIKE '%' || $1 || '%' OR link LIKE '%' || $1 || '%'", ident)
            await conn.execute("DELETE FROM vyapar_integration.webhook_deliveries WHERE payload::text LIKE '%' || $1 || '%'", ident)
            for schema in ("vyapar_opportunities", "vyapar_enquiries", "vyapar_listings"):
                await conn.execute(f"DELETE FROM {schema}.outbox_event WHERE payload::text LIKE '%' || $1 || '%'", ident)
        for member, prefs in snap["prefs"].items():
            await conn.execute(
                f"UPDATE vyapar_identity.members SET {', '.join(f'{c} = ${i + 2}' for i, c in enumerate(PREF_COLS))} WHERE id = $1",
                member, *[prefs[c] for c in PREF_COLS],
            )
        for pid in created["partnerships"]:
            await conn.execute("DELETE FROM vyapar_integration.notifications WHERE params::text LIKE '%' || $1 || '%' OR link LIKE '%' || $1 || '%'", str(pid))
            await conn.execute("DELETE FROM vyapar_enquiries.outbox_event WHERE payload::text LIKE '%' || $1 || '%'", str(pid))
            await conn.execute("DELETE FROM vyapar_enquiries.partnership_requests WHERE id = $1::uuid", str(pid))
        for blocker, blocked in created["blocks"]:
            await conn.execute("DELETE FROM vyapar_enquiries.blocks WHERE blocker_id = $1 AND blocked_id = $2", blocker, blocked)
        await conn.execute("UPDATE vyapar_identity.members SET badges = '[]', badges_computed_at = NULL WHERE id = ANY($1::text[])",
                           [ANITA, SURESH, SUNITA])
        for key, rows in snap["counters"].items():
            # Put the key back exactly as it was: remove what this run added, re-insert the originals.
            await conn.execute("DELETE FROM vyapar_platform.rate_limit_counter WHERE rate_limit_key = $1", key)
            for r in rows:
                await conn.execute(
                    """INSERT INTO vyapar_platform.rate_limit_counter (rate_limit_key, window_start, window_seconds, hit_count, limit_max)
                       VALUES ($1, $2, $3, $4, $5)""",
                    key, r["window_start"], r["window_seconds"], r["hit_count"], r["limit_max"],
                )
    for err in conn.errors:
        print("CLEANUP ERROR", err)
    if conn.errors:
        results.append(("cleanup", False, "; ".join(conn.errors)))


def run_checks(api: Api, created: dict, owner_loop_query) -> None:
    # ---- 3. Badges (pure rules + live read) --------------------------------
    from datetime import datetime, timedelta, timezone

    from app.reputation import compute_badge_keys

    now = datetime.now(timezone.utc)
    keys = compute_badge_keys({"reviews": 20, "recommends": 19, "answered": 6, "median_minutes": 45, "repeat_hirers": 3,
                               "verified_business": True, "member_since": now - timedelta(days=30)}, now)
    check("badges: thresholds (all six earned)", set(keys) == {"responds_fast", "reliable", "rising", "top_recommended", "verified_business", "repeat_hires"}, str(keys))
    keys = compute_badge_keys({"reviews": 4, "recommends": 4, "answered": 4, "median_minutes": 10, "member_since": now - timedelta(days=400)}, now)
    check("badges: below every threshold -> none", keys == [], str(keys))
    r = api.call(ANITA, "GET", f"/v1/members/{ANITA}/badges", lang="hi")
    body = r.json()
    check("badges: GET /v1/members/{id}/badges", r.status_code == 200 and any(b["key"] == "verified_business" for b in body["badges"]), r.text[:300])
    vb = next((b for b in body.get("badges", []) if b["key"] == "verified_business"), {})
    check("badges: localized label (hi)", any("ऀ" <= ch <= "ॿ" for ch in vb.get("label", "")), r.text[:300])

    # ---- 1. Contact preferences --------------------------------------------
    r = api.call(ANITA, "PATCH", "/v1/listings/contact-preferences",
                 json={"call_hours_start": "00:00", "call_hours_end": "23:59", "call_days": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
                       "max_calls_per_day": 1, "whatsapp_ok": True, "call_ok": True, "calls_from": "anyone"})
    check("contact prefs: update", r.status_code == 200 and r.json()["max_calls_per_day"] == 1, r.text[:300])
    r = api.call(ANITA, "GET", "/v1/listings/contact-preferences")
    check("contact prefs: read back", r.status_code == 200 and r.json()["call_hours_start"] == "00:00" and r.json()["timezone"] == "UTC+05:30", r.text[:300])
    r = api.call(ANITA, "PATCH", "/v1/listings/contact-preferences", json={"call_hours_start": "10:00", "call_hours_end": "10:00"})
    check("contact prefs: empty window refused", r.status_code == 422 and r.json()["error"]["code"] == "empty_window", r.text[:300])
    r = api.call(ANITA, "GET", f"/v1/listings/{ANITA_LISTING}/contact-preferences")
    check("contact prefs: listing inherits member", r.status_code == 200 and r.json()["overrides"] == [] and r.json()["effective"]["max_calls_per_day"] == 1, r.text[:300])
    r = api.call(SURESH, "PATCH", f"/v1/listings/{ANITA_LISTING}/contact-preferences", json={"call_ok": False})
    check("contact prefs: non-owner cannot override a listing", r.status_code == 404, r.text[:200])

    # ---- 4. Packages ------------------------------------------------------
    r = api.call(ANITA, "PUT", f"/v1/listings/{ANITA_LISTING}/packages", json={"packages": [
        {"tier": "basic", "name": "GST return filing (monthly)", "name_hi": "जीएसटी रिटर्न फाइलिंग (मासिक)",
         "description": "GSTR-1 and GSTR-3B for one GSTIN, up to 100 invoices.", "price_paise": 149900, "delivery_days": 5, "revisions": 1,
         "includes": ["GSTR-1", "GSTR-3B", "Filing acknowledgement"]},
        {"tier": "standard", "name": "Bookkeeping + GST", "description": "Monthly books in Tally, GST filing and a one-page P&L.",
         "price_paise": 499900, "delivery_days": 10, "revisions": 2, "includes": ["Tally books", "GST filing", "Monthly P&L"]},
    ]})
    pk = r.json() if r.status_code == 200 else []
    created["packages"] += [p["id"] for p in pk]
    check("packages: upsert two tiers", r.status_code == 200 and [p["tier"] for p in pk] == ["basic", "standard"], r.text[:300])
    check("packages: rupee label", pk and pk[0]["price_label"] == "₹1,499", str(pk[:1]))
    r = api.call(SURESH, "GET", f"/v1/listings/{ANITA_LISTING}/packages", lang="hi")
    check("packages: viewer reads Hindi name", r.status_code == 200 and r.json()[0]["name"] == "जीएसटी रिटर्न फाइलिंग (मासिक)", r.text[:300])
    r = api.call(ANITA, "PUT", f"/v1/listings/{ANITA_LISTING}/packages", json={"packages": [
        {"tier": "premium", "name": "A", "price_paise": 1}, {"tier": "premium", "name": "B", "price_paise": 2}]})
    check("packages: duplicate tier refused", r.status_code == 422 and r.json()["error"]["code"] == "duplicate_package_tier", r.text[:200])
    r = api.call(SURESH, "PUT", f"/v1/listings/{ANITA_LISTING}/packages", json={"packages": [{"tier": "premium", "name": "X", "price_paise": 1}]})
    check("packages: non-owner cannot edit", r.status_code == 404, r.text[:200])
    r = api.call(SURESH, "GET", f"/v1/listings/{ANITA_LISTING}")
    check("listing detail carries packages + badges", r.status_code == 200 and len(r.json()["packages"]) == 2 and any(b["key"] == "verified_business" for b in r.json()["badges"]), r.text[:300])

    basic_id = pk[0]["id"] if pk else "00000000-0000-0000-0000-000000000000"
    r = api.call(SURESH, "POST", f"/v1/listings/{ANITA_LISTING}/packages/{basic_id}/request",
                 json={"message": "Namaste, I need monthly GST filing for my electrical contracting firm in Dilsukhnagar."})
    if r.status_code == 201:
        created["enquiries"].append(r.json()["enquiry"]["id"])
    check("packages: request opens an enquiry", r.status_code == 201, r.text[:300])
    enquiry_id = r.json()["enquiry"]["id"] if r.status_code == 201 else None
    if not enquiry_id:
        return
    row = None
    for _ in range(20):  # get_conn commits in dependency teardown, which can finish just after the response
        row = owner_loop_query("SELECT sub_choice, package_id::text AS package_id FROM vyapar_enquiries.enquiries WHERE id = $1", enquiry_id)
        if row and row["package_id"]:
            break
        time.sleep(0.1)
    check("packages: enquiry tagged request_package + package_id", row and row["sub_choice"] == "request_package" and row["package_id"] == basic_id, str(row))

    # ---- 1. Contact actions ------------------------------------------------
    r = api.call(SURESH, "GET", f"/v1/enquiries/{enquiry_id}/contact-actions")
    check("contact actions: nothing before acceptance", r.status_code == 200 and r.json()["revealed"] is False and r.json()["contact_actions"] == [], r.text[:300])
    r = api.call(SURESH, "POST", f"/v1/enquiries/{enquiry_id}/contact-attempts", json={"channel": "call"})
    check("contact attempt: refused before acceptance", r.status_code == 400 and r.json()["error"]["code"] == "not_revealed", r.text[:200])
    r = api.call(ANITA, "POST", f"/v1/enquiries/{enquiry_id}/accept")
    check("enquiry accepted by provider", r.status_code == 200 and r.json()["state"] == "in_progress", r.text[:200])
    r = api.call(SURESH, "GET", f"/v1/enquiries/{enquiry_id}/contact-actions", lang="te")
    body = r.json()
    call = next((a for a in body.get("contact_actions", []) if a["channel"] == "call"), None)
    wa = next((a for a in body.get("contact_actions", []) if a["channel"] == "whatsapp"), None)
    check("contact actions: call href tel:+91", call is not None and call["href"] == "tel:+919000000002" and call["available_now"], json.dumps(body)[:400])
    check("contact actions: whatsapp wa.me with localized text", wa is not None and wa["href"].startswith("https://wa.me/919000000002?text=") and "%E0%B0" in wa["href"], json.dumps(wa)[:300])
    r = api.call(SURESH, "POST", f"/v1/enquiries/{enquiry_id}/contact-attempts", json={"channel": "call"})
    check("contact attempt: first call recorded", r.status_code == 201 and r.json()["calls_today"] == 1, r.text[:300])
    body = r.json()
    call = next((a for a in body.get("contact_actions", []) if a["channel"] == "call"), {})
    check("contact actions: cap hit -> available_now false, daily_cap_reached", call.get("available_now") is False and call.get("reason") == "daily_cap_reached" and call.get("next_window"), json.dumps(call)[:300])
    r = api.call(SURESH, "POST", f"/v1/enquiries/{enquiry_id}/contact-attempts", json={"channel": "call"})
    check("contact attempt: second call refused (429 daily_cap_reached)", r.status_code == 429 and r.json()["error"]["code"] == "daily_cap_reached", r.text[:300])
    r = api.call(ANITA, "GET", f"/v1/enquiries/{enquiry_id}/contact-attempts")
    check("contact attempts: callee sees 'contacted you'", r.status_code == 200 and len(r.json()) == 1 and not r.json()[0]["mine"] and "contacted you" in r.json()[0]["summary"], r.text[:300])
    r = api.call(SURESH, "GET", f"/v1/enquiries/{enquiry_id}/contact-attempts")
    check("contact attempts: caller sees 'You contacted'", r.status_code == 200 and r.json()[0]["mine"] and r.json()[0]["summary"].startswith("You contacted"), r.text[:300])
    api.call(ANITA, "PATCH", "/v1/listings/contact-preferences", json={"calls_from": "matching_only", "reset": ["max_calls_per_day"]})
    r = api.call(SURESH, "GET", f"/v1/enquiries/{enquiry_id}/contact-actions")
    call = next((a for a in r.json().get("contact_actions", []) if a["channel"] == "call"), {})
    check("contact actions: matching_only hides href from a non-matching caller", call.get("reason") == "not_matching" and call.get("href") is None, json.dumps(call)[:300])
    r = api.call(RAHUL, "GET", f"/v1/enquiries/{enquiry_id}/contact-actions")
    check("contact actions: outsider gets 404", r.status_code == 404, r.text[:200])

    # ---- Agent tokens: contracts:write scope ------------------------------
    r = api.call(SURESH, "POST", "/v1/integrations/tokens", json={"name": "Backend B check (read only)", "scopes": ["read"], "expires_in_days": 1})
    read_token = r.json().get("token") if r.status_code in (200, 201) else None
    if r.status_code in (200, 201):
        created["tokens"].append(r.json()["id"])
    r = api.call(SURESH, "POST", "/v1/integrations/tokens",
                 json={"name": "Backend B check (contracts)", "scopes": ["read", "contracts:write", "enquiries:write"], "expires_in_days": 1})
    check("tokens: contracts:write is an accepted scope", r.status_code in (200, 201), r.text[:300])
    contracts_token = r.json().get("token") if r.status_code in (200, 201) else None
    if r.status_code in (200, 201):
        created["tokens"].append(r.json()["id"])
    contract_body = {"enquiry_id": enquiry_id, "title": "Monthly GST filing — October", "total_paise": 149900,
                     "milestones": [{"title": "October GSTR-1 and GSTR-3B filed", "amount_paise": 149900}]}
    if read_token:
        r = api.bearer(read_token, "POST", "/v1/contracts", json=contract_body)
        check("tokens: read-only token cannot write contracts", r.status_code == 403 and r.json()["error"]["code"] == "scope_required", r.text[:300])
    if contracts_token:
        r = api.bearer(contracts_token, "POST", "/v1/contracts", json=contract_body)
        if r.status_code == 201:
            created["contracts"].append(r.json()["id"])
        check("tokens: contracts:write token creates a contract", r.status_code == 201, r.text[:300])
        r = api.bearer(contracts_token, "GET", f"/v1/enquiries/{enquiry_id}/contact-actions")
        check("tokens: read scope reaches contact actions", r.status_code == 200 and r.json()["revealed"], r.text[:200])
        r = api.bearer(contracts_token, "POST", "/v1/promotions", json={"target_kind": "listing", "target_id": ANITA_LISTING, "custom_days": 3})
        check("tokens: boosts stay with the member (not_available_to_tokens)", r.status_code == 403 and r.json()["error"]["code"] == "not_available_to_tokens", r.text[:200])

    # ---- 5. Saved search (before the opportunity it should match) ----------
    r = api.call(SURESH, "POST", "/v1/opportunities/saved-searches",
                 json={"query": "", "name": "Kitchen jobs", "alert": True, "filters": {"skills": ["catering"], "type": "employment"}})
    if r.status_code == 201:
        created["searches"].append(r.json()["id"])
    check("saved search: create with alert", r.status_code == 201 and r.json()["alert"] and r.json()["filters"]["skills"] == ["catering"], r.text[:300])
    r = api.call(SURESH, "GET", "/v1/opportunities/saved-searches")
    check("saved search: list", r.status_code == 200 and any(s["name"] == "Kitchen jobs" for s in r.json()), r.text[:300])
    time.sleep(1.1)

    # ---- 2. Seeker protection ----------------------------------------------
    r = api.call(SUNITA, "POST", "/v1/opportunities/seeker-charge-check",
                 json={"text": "Kitchen helper", "structured": {"type": "employment", "candidate_pays": True, "candidate_pays_amount": 50000}})
    check("seeker charge: candidate_pays refused", r.status_code == 200 and r.json()["allowed"] is False and r.json()["code"] == "seeker_charge_not_allowed", r.text[:300])
    r = api.call(SUNITA, "POST", "/v1/opportunities/seeker-charge-check",
                 json={"text": "Kitchen helper. Pay ₹500 uniform charge on joining.", "structured": {"type": "employment"}}, )
    check("seeker charge: kit/uniform wording refused", r.json().get("allowed") is False, r.text[:300])
    r = api.call(SUNITA, "POST", "/v1/opportunities/seeker-charge-check",
                 json={"text": "Kitchen helpers for weddings. ₹700 per day, meals provided.", "structured": {"type": "employment"}})
    check("seeker charge: clean post allowed", r.json().get("allowed") is True, r.text[:300])
    from app.services import hooks
    from app.errors import ApiError
    try:
        hooks.run_seeker_charge_checks("Security deposit of Rs 2000 required", {"type": "employment"}, "hi")
        raised = None
    except ApiError as exc:
        raised = exc
    check("seeker charge: hook registered and raises coded error", raised is not None and raised.code == "seeker_charge_not_allowed" and raised.status_code == 422, str(raised))

    r = api.call(SUNITA, "POST", "/v1/opportunities", json={
        "entry_mode": "create", "type": "employment", "source_segment": "community",
        "title": "Kitchen helpers for wedding catering (Secunderabad)",
        "description": "Kapoor Caterers needs 4 kitchen helpers for the wedding season: prep, washing, packing. Meals provided.",
        "compensation": "₹700 per day", "value_amount": 700, "location": "Secunderabad", "work_mode": "on_site",
        "timing": "Immediate start, 3 weeks", "required_capabilities": ["catering"],
        "structured": {"salary_min_paise": 1800000, "salary_max_paise": 2100000, "openings": 4},
    })
    opp_id = r.json().get("id") if r.status_code == 201 else None
    if opp_id:
        created["opportunities"].append(opp_id)
    check("opportunity created (Sunita)", opp_id is not None, r.text[:300])
    if not opp_id:
        return
    unconfirmed = r.json().get("unconfirmed_fields") or []
    if unconfirmed:
        api.call(SUNITA, "PATCH", f"/v1/opportunities/{opp_id}/confirm", json={"fields": unconfirmed})
    r = api.call(SUNITA, "POST", f"/v1/opportunities/{opp_id}/publish")
    check("opportunity published", r.status_code == 200 and r.json()["state"] == "active", r.text[:300])
    owner_loop_query("UPDATE vyapar_opportunities.opportunities SET lat = 17.4399, lng = 78.4983 WHERE id = $1 RETURNING id", opp_id)

    r = api.call(SURESH, "GET", f"/v1/opportunities/{opp_id}/seeker-protection", lang="hi")
    check("seeker protection notice (hi)", r.status_code == 200 and r.json()["applies"]
          and any("ऀ" <= ch <= "ॿ" for ch in r.json()["body"]) and r.json()["report_reason"] == "asked_for_money", r.text[:300])

    # Saved-search alert, inside a transaction that is rolled back.
    alerts = owner_loop_query("__saved_search_alerts__", SURESH)
    check("saved search: alert fires for the new matching post (rolled back)", alerts == 1, str(alerts))
    capped = owner_loop_query("__saved_search_alerts_capped__", SURESH)
    check("saved search: no alert once the daily cap is used (cap shared)", capped == 0, str(capped))

    # ---- 5. Feed filters ----------------------------------------------------
    r = api.call(SURESH, "GET", "/v1/opportunities/feed", params={"sort": "distance"})
    feed = r.json()
    ok_sorted = True
    for s in feed.get("sections", []):
        d = [i["distance_km"] for i in s["items"] if i["distance_km"] is not None]
        ok_sorted &= d == sorted(d)
    check("feed: sort=distance orders every section", r.status_code == 200 and ok_sorted and feed["distance_available"], r.text[:200])
    check("feed: cards carry distance_km", any(i.get("distance_km") is not None for s in feed.get("sections", []) for i in s["items"]), "")
    items = [i for s in feed.get("sections", []) for i in s["items"]]
    job = next((i for i in items if i["type"] == "employment"), None)
    check("feed: employment cards carry seeker_protection", job is None or (job.get("seeker_protection") or {}).get("applies") is True, json.dumps(job)[:200] if job else "")
    r = api.call(SURESH, "GET", "/v1/opportunities/feed", params={"radius_km": 5})
    items5 = [i for s in r.json().get("sections", []) for i in s["items"]]
    check("feed: radius_km=5 keeps only <=5 km (or remote)",
          r.status_code == 200 and all(i["work_mode"] == "remote" or (i["distance_km"] is not None and i["distance_km"] <= 5) for i in items5),
          json.dumps([(i["title"][:25], i["distance_km"], i["work_mode"]) for i in items5])[:400])
    near = next((s for s in feed.get("sections", []) if s["key"] == "near_you"), None)
    r_member = owner_loop_query("SELECT radius_km FROM vyapar_identity.members WHERE id = $1", SURESH)
    check("feed: near_you is distance-based", near is None or all(i["distance_km"] is not None and i["distance_km"] <= r_member["radius_km"] for i in near["items"]), json.dumps(near)[:300] if near else "")
    r = api.call(SURESH, "GET", "/v1/opportunities/feed/section/public", params={"sort": "salary_high"})
    vals = [i["value_amount"] for i in r.json() if i["value_amount"] is not None] if r.status_code == 200 else None
    check("feed section: sort=salary_high", vals is not None and vals == sorted(vals, reverse=True), str(vals))
    r = api.call(SURESH, "GET", "/v1/opportunities/feed/section/community", params={"availability": "now", "type": "employment"})
    check("feed section: availability=now + type filter", r.status_code == 200 and any(i["id"] == opp_id for i in r.json()) and all(i["type"] == "employment" for i in r.json()), r.text[:300])
    r = api.call(SURESH, "GET", "/v1/opportunities/feed/section/community", params={"sort": "verified_first"})
    check("feed section: sort=verified_first", r.status_code == 200, r.text[:200])
    r = api.call(SURESH, "GET", "/v1/opportunities/feed", params={"sort": "nonsense"})
    check("feed: invalid sort is a 422", r.status_code == 422, r.text[:200])

    # ---- 2. Two independent 'asked_for_money' reports -> paused -----------
    r = api.call(RAHUL, "POST", "/v1/reports", json={"object_kind": "opportunity", "object_id": opp_id, "reason": "asked_for_money",
                                                     "evidence_text": "On the phone they asked ₹500 for the uniform before joining."})
    check("report 1 (asked_for_money) accepted", r.status_code == 201, r.text[:200])
    state = owner_loop_query("SELECT state FROM vyapar_opportunities.opportunities WHERE id = $1", opp_id)
    check("one report does not pause", state and state["state"] == "active", str(state))
    r = api.call(GAURAV, "POST", "/v1/reports", json={"object_kind": "opportunity", "object_id": opp_id, "reason": "asked_for_money"})
    check("report 2 (asked_for_money) accepted", r.status_code == 201, r.text[:200])
    row = owner_loop_query(
        """SELECT o.state, o.state_reason, o.distribution_limited, c.severity, c.primary_reason, c.reporter_count
             FROM vyapar_opportunities.opportunities o
             JOIN vyapar_trust_safety.moderation_cases c ON c.object_id = o.id AND c.state IN ('open','in_review','escalated')
            WHERE o.id = $1""", opp_id)
    check("two reports pause the job and open a High case",
          row and row["state"] == "paused" and row["state_reason"] == "seeker_charge_reports" and row["severity"] == "high" and row["reporter_count"] == 2,
          str(row))
    note = owner_loop_query("SELECT title FROM vyapar_integration.notifications WHERE idempotency_key = $1", f"seeker_charge_paused:{opp_id}")
    check("poster notified in their language", note is not None and note["title"], str(note))


# ---------------------------------------------------------------------------
# Pre-accept calling (critique L1). Sunita posts a kitchen-electrician job;
# Suresh (electrician) matches it, Ravi (plumber) does not; Rahul meets the
# call-hours window; Gaurav is blocked by Sunita.
# ---------------------------------------------------------------------------
def run_precall_checks(api: "Api", created: dict, owner_loop_query) -> None:
    from datetime import datetime, timedelta, timezone

    from app.integrations.identity.scopes import required_scopes

    check("precall: tap needs enquiries:write, read needs read",
          required_scopes("POST", "/v1/opportunities/x/contact-attempts") == ("enquiries:write",)
          and required_scopes("GET", "/v1/opportunities/x/contact-actions") == ("read",), "")

    # Type rule: only employment and local_service.
    r = api.call(SUNITA, "POST", "/v1/opportunities", json={
        "entry_mode": "create", "type": "partnership", "source_segment": "community", "title": "Festive catering partner wanted",
        "description": "Looking for a sweets maker to partner with Kapoor Caterers for the Diwali season.", "location": "Secunderabad",
        "allow_precall": True})
    check("precall: refused on a partnership post (422 precall_not_for_type)",
          r.status_code == 422 and r.json()["error"]["code"] == "precall_not_for_type", r.text[:300])
    r = api.call(SUNITA, "POST", "/v1/opportunities", json={
        "entry_mode": "create", "type": "partnership", "source_segment": "community", "title": "Festive catering partner wanted",
        "description": "Looking for a sweets maker to partner with Kapoor Caterers for the Diwali season.", "location": "Secunderabad"})
    if r.status_code == 201:
        created["opportunities"].append(r.json()["id"])
        r2 = api.call(SUNITA, "PATCH", f"/v1/opportunities/{r.json()['id']}", json={"allow_precall": True})
        check("precall: PATCH on a partnership post refused", r2.status_code == 422 and r2.json()["error"]["code"] == "precall_not_for_type", r2.text[:300])

    r = api.call(SUNITA, "POST", "/v1/opportunities", json={
        "entry_mode": "create", "type": "employment", "source_segment": "community",
        "title": "Electrician for kitchen equipment (Kapoor Caterers)",
        "description": "Maintain tandoor blowers, cold rooms and kitchen wiring at our Secunderabad kitchen. Full time, day shift.",
        "compensation": "₹22,000 a month", "value_amount": 22000, "location": "Secunderabad", "work_mode": "on_site",
        "timing": "Start this month", "required_capabilities": ["electrical"],
        "structured": {"salary_min_paise": 2000000, "salary_max_paise": 2400000, "openings": 1},
    })
    opp_id = r.json().get("id") if r.status_code == 201 else None
    check("precall: job created with the switch off by default", opp_id is not None and r.json().get("allow_precall") is False, r.text[:300])
    if not opp_id:
        return
    created["opportunities"].append(opp_id)
    unconfirmed = r.json().get("unconfirmed_fields") or []
    if unconfirmed:
        api.call(SUNITA, "PATCH", f"/v1/opportunities/{opp_id}/confirm", json={"fields": unconfirmed})
    r = api.call(SUNITA, "POST", f"/v1/opportunities/{opp_id}/publish")
    check("precall: job published", r.status_code == 200 and r.json()["state"] == "active", r.text[:300])

    # Off: nothing to tap, no number, refused.
    r = api.call(SURESH, "GET", f"/v1/opportunities/{opp_id}/contact-actions")
    b = r.json()
    check("precall off: reason precall_off, no href anywhere",
          r.status_code == 200 and b["reason"] == "precall_off" and all(a["href"] is None and a["reason"] == "precall_off" for a in b["contact_actions"]),
          json.dumps(b)[:300])
    check("precall off: the number is nowhere in the response", "9000000004" not in r.text, "")
    r = api.call(SURESH, "POST", f"/v1/opportunities/{opp_id}/contact-attempts", json={"channel": "call"})
    check("precall off: tap refused (403 precall_off)", r.status_code == 403 and r.json()["error"]["code"] == "precall_off", r.text[:200])

    r = api.call(SUNITA, "PATCH", f"/v1/opportunities/{opp_id}", json={"allow_precall": True})
    check("precall: poster switches it on (WhatsApp only by default, W2)",
          r.status_code == 200 and r.json()["allow_precall"] is True and r.json()["precall_channel"] == "whatsapp_only", r.text[:300])
    check("W2: honest disclosure copy for the poster", "will see your phone number" in (r.json().get("precall_disclosure") or ""),
          str(r.json().get("precall_disclosure")))
    r = api.call(SURESH, "GET", f"/v1/opportunities/{opp_id}/contact-actions")
    call = next((a for a in r.json().get("contact_actions", []) if a["channel"] == "call"), {})
    wa = next((a for a in r.json().get("contact_actions", []) if a["channel"] == "whatsapp"), {})
    check("W2: whatsapp_only -> call has no href (reason whatsapp_only), WhatsApp available",
          call.get("reason") == "whatsapp_only" and call.get("href") is None and wa.get("available_now") and r.json().get("precall_channel") == "whatsapp_only",
          r.text[:400])
    r = api.call(SURESH, "POST", f"/v1/opportunities/{opp_id}/contact-attempts", json={"channel": "call"})
    check("W2: call tap refused on a WhatsApp-only post (403 precall_whatsapp_only)",
          r.status_code == 403 and r.json()["error"]["code"] == "precall_whatsapp_only", r.text[:200])
    r = api.call(SUNITA, "PATCH", f"/v1/opportunities/{opp_id}", json={"precall_channel": "call_and_whatsapp"})
    check("W2: poster allows calls too", r.status_code == 200 and r.json()["precall_channel"] == "call_and_whatsapp"
          and "calls or messages" in (r.json().get("precall_disclosure") or ""), r.text[:300])
    r = api.call(SUNITA, "GET", f"/v1/opportunities/{opp_id}/contact-actions")
    check("precall: never for the poster (own_post)", r.status_code == 200 and r.json()["reason"] == "own_post" and r.json()["contact_actions"] == [], r.text[:200])
    r = api.call(SUNITA, "PATCH", "/v1/listings/contact-preferences",
                 json={"call_hours_start": "00:00", "call_hours_end": "23:59", "call_days": [], "max_calls_per_day": 2,
                       "calls_from": "matching_only", "call_ok": True, "whatsapp_ok": True})
    check("precall: poster sets matching_only and a cap of 2 calls a day", r.status_code == 200, r.text[:200])

    # not_matching (Ravi is a plumber).
    r = api.call(RAVI, "GET", f"/v1/opportunities/{opp_id}/contact-actions")
    call = next((a for a in r.json().get("contact_actions", []) if a["channel"] == "call"), {})
    check("precall: non-matching caller gets not_matching and no href", call.get("reason") == "not_matching" and call.get("href") is None and "9000000004" not in r.text, r.text[:300])
    r = api.call(RAVI, "POST", f"/v1/opportunities/{opp_id}/contact-attempts", json={"channel": "call"})
    check("precall: non-matching tap refused (403 not_matching)", r.status_code == 403 and r.json()["error"]["code"] == "not_matching", r.text[:200])

    # Available for Suresh (electrician).
    r = api.call(SURESH, "GET", f"/v1/opportunities/{opp_id}/contact-actions", lang="hi")
    b = r.json()
    call = next((a for a in b.get("contact_actions", []) if a["channel"] == "call"), {})
    wa = next((a for a in b.get("contact_actions", []) if a["channel"] == "whatsapp"), {})
    check("precall: matching caller can call now (tel:+91 href)", b.get("available") and call.get("href") == "tel:+919000000004" and call.get("available_now"), json.dumps(b)[:400])
    check("precall: WhatsApp text is localized and names the job",
          (wa.get("href") or "").startswith("https://wa.me/919000000004?text=") and "Electrician%20for%20kitchen" in wa.get("href", "") and "%E0%A4" in wa.get("href", ""),
          json.dumps(wa)[:300])
    r = api.call(SURESH, "GET", f"/v1/opportunities/{opp_id}")
    d = r.json()
    check("precall: detail carries allow_precall + precall_actions",
          r.status_code == 200 and d.get("allow_precall") is True and (d.get("precall_actions") or {}).get("available") is True, json.dumps(d.get("precall_actions"))[:300])
    r = api.call(SUNITA, "GET", f"/v1/opportunities/{opp_id}")
    check("precall: poster's own detail has no precall_actions", r.status_code == 200 and r.json().get("precall_actions") is None, "")

    # Tap 1 (call): records, notifies, opens a lightweight application.
    r = api.call(SURESH, "POST", f"/v1/opportunities/{opp_id}/contact-attempts", json={"channel": "call"})
    b = r.json()
    if b.get("application_enquiry_id"):
        created["enquiries"].append(b["application_enquiry_id"])
    check("precall: first tap recorded and opens an application",
          r.status_code == 201 and b["application_created"] and b["application_enquiry_id"] and b["my_taps_today"] == 1 and b["calls_today"] == 1,
          r.text[:400])
    row = None
    for _ in range(20):
        row = owner_loop_query("SELECT applied_via, action_type, profile_snapshot IS NOT NULL AS snap FROM vyapar_enquiries.enquiries WHERE id = $1",
                               b.get("application_enquiry_id") or "00000000-0000-0000-0000-000000000000")
        if row:
            break
        time.sleep(0.1)
    check("precall: application is applied_via=call with a profile snapshot", row and row["applied_via"] == "call" and row["action_type"] == "apply" and row["snap"], str(row))
    note = None
    for _ in range(20):
        note = owner_loop_query("SELECT title, member_id FROM vyapar_integration.notifications WHERE idempotency_key = $1", f"precall:{b.get('attempt_id')}")
        if note:
            break
        time.sleep(0.1)
    check("precall: poster notified ('Suresh called about your ... job')", note and note["member_id"] == SUNITA and "Suresh" in note["title"], str(note))

    # Tap 2 (WhatsApp): no second application.
    r = api.call(SURESH, "POST", f"/v1/opportunities/{opp_id}/contact-attempts", json={"channel": "whatsapp"})
    check("precall: second tap reuses the application", r.status_code == 201 and not r.json()["application_created"] and r.json()["my_taps_today"] == 2, r.text[:300])

    # daily_cap_reached: anyone may call now; Ravi's call is the poster's 2nd of 2.
    api.call(SUNITA, "PATCH", "/v1/listings/contact-preferences", json={"calls_from": "anyone"})
    r = api.call(RAVI, "POST", f"/v1/opportunities/{opp_id}/contact-attempts", json={"channel": "call"})
    if r.status_code == 201 and r.json().get("application_enquiry_id"):
        created["enquiries"].append(r.json()["application_enquiry_id"])
    check("precall: second caller's call recorded (poster at 2/2)", r.status_code == 201 and r.json()["calls_today"] == 2, r.text[:300])
    r = api.call(RAVI, "GET", f"/v1/opportunities/{opp_id}/contact-actions")
    call = next((a for a in r.json().get("contact_actions", []) if a["channel"] == "call"), {})
    check("precall: poster's cap -> daily_cap_reached, no href, next_window",
          call.get("reason") == "daily_cap_reached" and call.get("href") is None and call.get("next_window"), json.dumps(call)[:300])
    r = api.call(RAVI, "POST", f"/v1/opportunities/{opp_id}/contact-attempts", json={"channel": "call"})
    check("precall: call over the cap refused (429 daily_cap_reached)", r.status_code == 429 and r.json()["error"]["code"] == "daily_cap_reached", r.text[:200])

    # caller_limit_reached: Suresh's 3rd tap is allowed, the 4th is not.
    r = api.call(SURESH, "POST", f"/v1/opportunities/{opp_id}/contact-attempts", json={"channel": "whatsapp"})
    check("precall: caller's third tap allowed", r.status_code == 201 and r.json()["my_taps_today"] == 3, r.text[:200])
    wa = next((a for a in r.json().get("contact_actions", []) if a["channel"] == "whatsapp"), {})
    check("precall: after 3 taps -> caller_limit_reached, no href", wa.get("reason") == "caller_limit_reached" and wa.get("href") is None, json.dumps(wa)[:300])
    r = api.call(SURESH, "POST", f"/v1/opportunities/{opp_id}/contact-attempts", json={"channel": "whatsapp"})
    check("precall: fourth tap refused (429 precall_caller_limit)", r.status_code == 429 and r.json()["error"]["code"] == "precall_caller_limit", r.text[:200])

    # outside_hours: a window that opens in two hours; the cap is lifted.
    now = datetime.now(timezone(timedelta(minutes=330)))
    start, end = (now + timedelta(hours=2)).strftime("%H:%M"), (now + timedelta(hours=3)).strftime("%H:%M")
    api.call(SUNITA, "PATCH", "/v1/listings/contact-preferences", json={"call_hours_start": start, "call_hours_end": end, "reset": ["max_calls_per_day"]})
    r = api.call(RAHUL, "GET", f"/v1/opportunities/{opp_id}/contact-actions")
    b = r.json()
    call = next((a for a in b.get("contact_actions", []) if a["channel"] == "call"), {})
    wa = next((a for a in b.get("contact_actions", []) if a["channel"] == "whatsapp"), {})
    check("precall: outside the poster's hours -> outside_hours, no href, next_window at the window start",
          call.get("reason") == "outside_hours" and call.get("href") is None and (call.get("next_window") or "")[11:16] == start, json.dumps(call)[:300])
    check("precall: WhatsApp still available outside call hours", wa.get("available_now") is True and wa.get("href"), json.dumps(wa)[:200])
    r = api.call(RAHUL, "POST", f"/v1/opportunities/{opp_id}/contact-attempts", json={"channel": "call"})
    check("precall: call outside hours refused (409 outside_hours)", r.status_code == 409 and r.json()["error"]["code"] == "outside_hours", r.text[:200])

    # Blocked member: reads exactly like "off".
    r = api.call(SUNITA, "POST", "/v1/enquiries/block", json={"blocked_id": GAURAV})
    created["blocks"].append((SUNITA, GAURAV))
    r = api.call(GAURAV, "GET", f"/v1/opportunities/{opp_id}/contact-actions")
    check("precall: blocked member sees precall_off, no number", r.status_code == 200 and r.json()["reason"] == "precall_off" and "9000000004" not in r.text, r.text[:200])

    # Poster's view of the applicants now includes the callers.
    r = api.call(SUNITA, "GET", "/v1/enquiries/mine", params={"role": "received"})
    got = {e["sender_id"] for e in r.json() if e.get("opportunity_id") == opp_id} if r.status_code == 200 else set()
    check("precall: callers appear as applicants for the poster", {SURESH, RAVI} <= got, str(got))


# ---------------------------------------------------------------------------
# [FE2 — Discover redesign, 2026-09-29] results + facets + themed rows, the
# viewer's own posts kept out of Discover, and money labels always with
# the rupee sign and period. Read-only: creates nothing.
# ---------------------------------------------------------------------------
def run_discover_checks(api: "Api", created: dict, owner_loop_query) -> None:
    import re as _re

    from app.services.opportunities import legacy_compensation_label

    check("money: bare '15000' on a job reads as a monthly rupee amount",
          legacy_compensation_label("15000", "employment", "en") == "₹15,000 a month", legacy_compensation_label("15000", "employment", "en") or "")
    check("money: free text is kept as written", legacy_compensation_label("Negotiable", "freelance", "en") == "Negotiable", "")

    r = api.call(SUNITA, "GET", "/v1/opportunities/feed/results")
    body = r.json() if r.status_code == 200 else {}
    items = body.get("items", [])
    check("results: 200 with total and facets", r.status_code == 200 and "facets" in body and body.get("total", -1) >= len(items), r.text[:300])
    check("results: the viewer's own posts are not in Discover", all(i["poster_id"] != SUNITA for i in items), str([i["id"] for i in items if i["poster_id"] == SUNITA]))
    check("results: no bare number as pay", all(not _re.fullmatch(r"[0-9,]+", (i.get("compensation_label") or "x")) for i in items),
          str([i.get("compensation_label") for i in items][:10]))
    type_sum = sum(f["count"] for f in body.get("facets", {}).get("type", []))
    check("facets: kind counts add up to the total when no kind is chosen", type_sum == body.get("total"), f"{type_sum} vs {body.get('total')}")

    r = api.call(SUNITA, "GET", "/v1/opportunities/feed/results", params={"types": "employment,local_service"})
    b2 = r.json()
    check("results: types filter keeps only those kinds", r.status_code == 200 and all(i["type"] in ("employment", "local_service") for i in b2["items"]), r.text[:200])
    emp = next((f["count"] for f in b2["facets"]["type"] if f["value"] == "freelance"), None)
    check("facets: a kind's own count ignores the kind filter (disjunctive)", emp == next((f["count"] for f in body["facets"]["type"] if f["value"] == "freelance"), None), str(emp))

    r = api.call(SUNITA, "GET", "/v1/opportunities/feed/results", params={"verified_only": "true"})
    check("results: verified_only total equals the verified facet", r.status_code == 200 and r.json()["total"] == body["facets"]["verified"], r.text[:200])

    r = api.call(SUNITA, "GET", "/v1/opportunities/feed/results", params={"posted_within": "week"})
    check("results: posted_within=week keeps only posts from the last 7 days",
          r.status_code == 200 and all((i.get("posted_days_ago") or 0) <= 7 for i in r.json()["items"]), r.text[:200])

    r = api.call(SUNITA, "GET", "/v1/opportunities/feed/results", params={"types": "employment", "pay_kind": "monthly", "pay_min_paise": 2000000})
    check("results: monthly pay >= 20,000 keeps only jobs that state it",
          r.status_code == 200 and all(i["type"] == "employment" and i.get("structured") and ((i["structured"].get("salary_max_paise") or i["structured"].get("salary_min_paise") or 0) >= 2000000) for i in r.json()["items"]),
          r.text[:300])

    r = api.call(SUNITA, "GET", "/v1/opportunities/feed/rows")
    rows = r.json().get("rows", []) if r.status_code == 200 else []
    check("rows: themed rows with titles and See-all filters", r.status_code == 200 and rows and all(x["title_key"] and isinstance(x["see_all"], dict) for x in rows), r.text[:300])
    check("rows: never the viewer's own posts", all(i["poster_id"] != SUNITA for x in rows for i in x["items"]), "")
    r = api.call(SUNITA, "GET", "/v1/opportunities/feed")
    check("feed sections: never the viewer's own posts", r.status_code == 200 and all(i.get("poster_id") != SUNITA for sec in r.json()["sections"] for i in sec["items"]), "")


# ---------------------------------------------------------------------------
# Follow-ups from FE2: contact times in IST in the reader's language, and the
# "Use my location" position override on the feed endpoints.
# ---------------------------------------------------------------------------
def run_followup_checks(api: "Api", created: dict, owner_loop_query) -> None:
    from datetime import datetime, timedelta, timezone

    # (1) The attempts recorded by the earlier checks, read back in each language.
    opp_id = next((o for o in reversed(created["opportunities"])), None)
    r = api.call(SURESH, "GET", f"/v1/opportunities/{opp_id}/contact-actions", lang="hi")
    attempts = r.json().get("attempts", []) if r.status_code == 200 else []
    check("IST: attempts present to read back", bool(attempts), r.text[:200])
    if attempts:
        a = attempts[0]
        at_utc = datetime.fromisoformat(a["at"])
        at_ist = at_utc.astimezone(timezone(timedelta(minutes=330)))
        check("IST: at_local is the same instant at +05:30", a["at_local"].endswith("+05:30") and datetime.fromisoformat(a["at_local"]) == at_utc, json.dumps(a)[:300])
        check("IST: summary shows the IST clock time, not UTC", at_ist.strftime("%H:%M") + " IST" in a["summary"], a["summary"])
        check("IST: Hindi summary uses Hindi month names", "सित॰" in a["summary"] or at_ist.month != 9, a["summary"])
    r = api.call(SURESH, "GET", f"/v1/opportunities/{opp_id}/contact-actions", lang="te")
    s = (r.json().get("attempts") or [{}])[0].get("summary", "")
    check("IST: Telugu summary is Telugu with IST", "సంప్రదించారు" in s and " IST" in s, s)

    # (2) Position override. Suresh is saved at Dilsukhnagar; Banjara Hills is ~10 km west.
    saved = owner_loop_query("SELECT lat, lng FROM vyapar_identity.members WHERE id = $1", SURESH)
    banjara = {"lat": 17.4156, "lng": 78.4347}
    base = api.call(SURESH, "GET", "/v1/opportunities/feed/results", params={"limit": 100})
    here = api.call(SURESH, "GET", "/v1/opportunities/feed/results", params={"limit": 100, **banjara})
    check("position: results accept lat/lng", base.status_code == 200 and here.status_code == 200, here.text[:200])

    def items(resp):
        body = resp.json()
        return body.get("items") or [i for s in body.get("sections", []) for i in s.get("items", [])]

    b_by_id = {i["id"]: i.get("distance_km") for i in items(base)}
    moved = [(i["id"], b_by_id.get(i["id"]), i.get("distance_km")) for i in items(here) if i.get("distance_km") is not None and b_by_id.get(i["id"]) is not None]
    check("position: distances are measured from the override", any(abs(x - y) > 1 for _, x, y in moved), str(moved[:5]))
    # Every distance is measured from the override point (checked against the DB's own haversine).
    sample = [i for i in items(here) if i.get("distance_km") is not None][:5]
    wrong = []
    for i in sample:
        exp = owner_loop_query("SELECT vyapar_platform.distance_km($1, $2, lat, lng) AS d FROM vyapar_opportunities.opportunities WHERE id = $3::uuid",
                               banjara["lat"], banjara["lng"], i["id"])["d"]
        if abs(exp - i["distance_km"]) > 0.15:
            wrong.append((i["title"][:20], i["distance_km"], round(exp, 2)))
    check("position: distances are measured from the override point", sample and not wrong, str(wrong or len(sample)))
    r = api.call(SURESH, "GET", "/v1/opportunities/feed", params={"radius_km": 3, **banjara})
    near = [i for i in items(r) if i["work_mode"] != "remote"]
    check("position: radius applies around the override",
          r.status_code == 200 and all(i.get("distance_km") is not None and i["distance_km"] <= 3 for i in near) and r.json().get("distance_available"),
          json.dumps([(i["title"][:20], i.get("distance_km")) for i in near])[:300])
    r = api.call(SURESH, "GET", "/v1/opportunities/feed/section/community", params=banjara)
    check("position: section endpoint accepts lat/lng", r.status_code == 200, r.text[:200])
    r = api.call(SURESH, "GET", "/v1/opportunities/feed/section/community/page", params=banjara)
    check("position: section page endpoint accepts lat/lng", r.status_code == 200, r.text[:200])
    r = api.call(SURESH, "GET", "/v1/opportunities/feed/rows", params=banjara)
    check("position: rows accept lat/lng", r.status_code == 200, r.text[:200])
    r = api.call(SURESH, "GET", "/v1/opportunities/feed/results", params={"lat": 17.4})
    check("position: lat without lng -> 422 position_incomplete", r.status_code == 422 and r.json()["error"]["code"] == "position_incomplete", r.text[:200])
    r = api.call(SURESH, "GET", "/v1/opportunities/feed/results", params={"lat": 95, "lng": 78.4})
    check("position: out-of-range latitude -> 422", r.status_code == 422, r.text[:200])
    r = api.call(SURESH, "GET", "/v1/opportunities/feed/rows", params={"lat": 17.4, "lng": 181})
    check("position: out-of-range longitude -> 422", r.status_code == 422, r.text[:200])
    after = owner_loop_query("SELECT lat, lng FROM vyapar_identity.members WHERE id = $1", SURESH)
    check("position: never stored (member coordinates unchanged)", dict(after) == dict(saved), f"{dict(saved)} -> {dict(after)}")


# ---------------------------------------------------------------------------
# Feed relevance (critique L13/L14): Anita (CA, skills only on her business
# profile), Suresh (electrician, Dilsukhnagar) and a fresher (no skills yet).
# Three members post real accounting work so Anita has something to match.
# ---------------------------------------------------------------------------
VIKRAM, DEEPAK, NEW = "m_vikram", "m_deepak", "m_new"


def _post(api: "Api", created: dict, member: str, body: dict) -> str | None:
    base = {"entry_mode": "create", "source_segment": "community", "work_mode": "on_site"}
    r = api.call(member, "POST", "/v1/opportunities", json={**base, **body})
    if r.status_code != 201:
        print("post failed", r.status_code, r.text[:300])
        return None
    oid = r.json()["id"]
    created["opportunities"].append(oid)
    unconfirmed = r.json().get("unconfirmed_fields") or []
    if unconfirmed:
        api.call(member, "PATCH", f"/v1/opportunities/{oid}/confirm", json={"fields": unconfirmed})
    r = api.call(member, "POST", f"/v1/opportunities/{oid}/publish")
    if r.status_code != 200:
        print("publish failed", r.status_code, r.text[:300])
        return None
    return oid


def _rows_ok(body: dict) -> tuple[bool, str]:
    from app.services.feed import PERSONAL_ROW_MIN_ITEMS, ROW_MIN_ITEMS, _is_personal_row

    ids = [i["id"] for row in body["rows"] for i in row["items"]]
    keys = [row["key"] for row in body["rows"]]
    ok = (len(ids) == len(set(ids))
          and all(len(row["items"]) >= (PERSONAL_ROW_MIN_ITEMS if _is_personal_row(row["key"]) else ROW_MIN_ITEMS) for row in body["rows"])
          and len(body["rows"]) <= 6 and not ({"verified", "community"} & set(keys))
          and all(row.get("title") for row in body["rows"]))
    return ok, f"keys={keys} slots={len(ids)} distinct={len(set(ids))}"


def run_rows_checks(api: "Api", created: dict, owner_loop_query) -> None:
    posts = [
        _post(api, created, SUNITA, {"type": "local_service", "title": "GST filing for our catering business (monthly)",
                                     "description": "Kapoor Caterers needs GSTR-1 and GSTR-3B filed every month and advice on input credit.",
                                     "location": "Secunderabad", "required_capabilities": ["gst_filing"], "timing": "Every month from October",
                                     "structured": {"budget_paise": 1500000}}),
        _post(api, created, VIKRAM, {"type": "employment", "title": "Accountant for textile wholesale (Charminar)",
                                     "description": "Sethi Textiles needs a full-time accountant for billing, Tally and GST returns.",
                                     "location": "Charminar", "required_capabilities": ["accounting", "gst_filing"],
                                     "structured": {"salary_min_paise": 2500000, "salary_max_paise": 3200000, "openings": 1}}),
        _post(api, created, DEEPAK, {"type": "freelance", "title": "Income tax filing for a design studio and two partners",
                                     "description": "Bhalla Design Studio needs ITR filing for the firm and both partners, with advance-tax planning.",
                                     "location": "Jubilee Hills", "work_mode": "both", "required_capabilities": ["tax"],
                                     "structured": {"budget_type": "fixed", "budget_min_paise": 1200000, "budget_max_paise": 1800000, "duration": "1_4_weeks"}}),
    ]
    check("rows: three accounting posts published by other members", all(posts), str(posts))
    posts = [p for p in posts if p]

    # L14: Anita's skills come from her business profile.
    r = api.call(ANITA, "GET", "/v1/opportunities/feed")
    for_you = next((s for s in r.json().get("sections", []) if s["key"] == "for_you"), None)
    got = {i["id"] for i in (for_you or {}).get("items", [])}
    check("L14: Anita gets For you from her business profile's skills", for_you is not None and set(posts) <= got, str(got))
    r = api.call(ANITA, "GET", "/v1/opportunities/feed/rows")
    body = r.json()
    ok, detail = _rows_ok(body)
    check("L13: Anita's rows: unique posts, row minimums, <=6 rows, no Verified/Community", r.status_code == 200 and ok, detail)
    first = body["rows"][0] if body.get("rows") else {}
    check("L14: Anita's first row is For you with her accounting posts",
          first.get("key") == "for_you" and set(posts) <= {i["id"] for i in first.get("items", [])}, json.dumps(first)[:300])
    pay = next((row for row in body.get("rows", []) if row["key"] == "pay_20k"), None)
    check("L14: no 'Pay 20,000+' row of unrelated jobs for Anita",
          pay is None or all(set(i["required_capabilities"]) & {"accounting", "gst_filing", "tax"} for i in pay["items"]), json.dumps(pay)[:300] if pay else "")
    if len(posts) > 1:
        r = api.call(ANITA, "GET", f"/v1/opportunities/{posts[1]}/why")
        check("L14: Why this? credits her skills", r.status_code == 200 and "capability_fit" in r.json()["signals"], r.text[:200])
        r = api.call(ANITA, "GET", f"/v1/opportunities/{posts[1]}")
        check("L14: detail marks her matching skills", r.status_code == 200 and r.json().get("capability_match") == [True, True], str(r.json().get("capability_match")))

    # L13: Suresh's Near you never opens on unrelated work.
    r = api.call(SURESH, "GET", "/v1/opportunities/feed/rows")
    body = r.json()
    ok, detail = _rows_ok(body)
    check("L13: Suresh's rows: unique posts, row minimums, <=6 rows, no Verified/Community", r.status_code == 200 and ok, detail)
    near = next((row for row in body.get("rows", []) if row["key"] == "near_you"), None)
    home_repair = {"carpenter", "painter", "tile_fitter", "ac_technician", "mason", "plumbing", "electrical"}  # taxonomy: home_repair
    check("L13: Suresh's Near you holds only his kind of work (no Python job, no grants)",
          near is None or all(i["type"] in ("employment", "local_service") and (not i["required_capabilities"] or set(i["required_capabilities"]) & home_repair)
                              for i in near["items"]),
          json.dumps([(i["title"][:30], i["required_capabilities"]) for i in (near or {}).get("items", [])])[:300])
    check("L13: no Python job or grant anywhere in Suresh's first row",
          not body.get("rows") or all("Python" not in i["title"] and i["type"] != "community" for i in body["rows"][0]["items"]),
          json.dumps([i["title"][:30] for i in (body.get("rows") or [{}])[0].get("items", [])]))

    # The fresher: no skills, shown jobs and local work near the position they share.
    r = api.call(NEW, "GET", "/v1/opportunities/feed/rows", params={"lat": 17.3688, "lng": 78.5247})
    body = r.json()
    ok, detail = _rows_ok(body)
    check("L13: fresher's rows: unique posts, row minimums, <=6 rows", r.status_code == 200 and ok, detail)
    check("L14: fresher gets no For you and the add-your-skills prompt",
          all(row["key"] != "for_you" for row in body.get("rows", [])) and body.get("enrichment_prompt") == "sparseProfile", detail)
    near = next((row for row in body.get("rows", []) if row["key"] == "near_you"), None)
    check("L13: fresher's Near you is jobs and local work only",
          near is None or all(i["type"] in ("employment", "local_service") for i in near["items"]),
          json.dumps([(i["title"][:30], i["type"]) for i in (near or {}).get("items", [])])[:300])
    r = api.call(NEW, "GET", "/v1/opportunities/feed/rows", lang="te")
    check("rows: server-localized titles (te)", r.status_code == 200 and all(row["title"] and "rows." not in row["title"] for row in r.json()["rows"]),
          json.dumps([row["title"] for row in r.json().get("rows", [])], ensure_ascii=False))


# ---------------------------------------------------------------------------
# Owner, 2026-09-30: "all the real functionality is actually created as dummy".
# Trade filter, Businesses search, notifications language + dedupe + links.
# ---------------------------------------------------------------------------
MEENA = "m_meena"


def run_owner_checks(api: "Api", created: dict, owner_loop_query) -> None:
    # ---- 1. Trade filter --------------------------------------------------
    a = _post(api, created, MEENA, {"type": "local_service", "title": "Need a plumber for a leaking tap — Himayatnagar",
                                    "description": "Kitchen tap leaking since yesterday, need someone this evening.",
                                    "location": "Himayatnagar, Hyderabad", "required_capabilities": ["plumbing"],
                                    "structured": {"budget_paise": 60000, "urgency": "today"}})
    b = _post(api, created, MEENA, {"type": "local_service", "title": "Nal wala chahiye — overhead tank pipe broken",
                                    "description": "Pipe from the overhead tank cracked, water leaking on the stairs.",
                                    "location": "Himayatnagar, Hyderabad", "required_capabilities": ["plumber", "nal wala"],
                                    "structured": {"budget_paise": 150000, "urgency": "today"}})
    check("trade: two plumbing posts (one skill slug, one free-text 'plumber')", bool(a and b), str((a, b)))
    r = api.call(RAHUL, "GET", "/v1/opportunities/feed/results", params={"skills": "plumbing", "limit": 100})
    got = {i["id"] for i in r.json().get("items", [])}
    check("trade: Plumbers tile (skills=plumbing) returns both posts", r.status_code == 200 and {a, b} <= got, f"{len(got)} items")
    facet = next((f for f in r.json().get("facets", {}).get("skills", []) if f["value"] == "plumbing"), None)
    check("trade: the Plumbing chip counts what the filter returns", facet is not None and facet["count"] >= 2, str(facet))
    r = api.call(RAHUL, "GET", "/v1/opportunities/feed/results", params={"skills": "home_repair", "limit": 100})
    check("trade: a category tile (home_repair) returns every skill under it",
          r.status_code == 200 and {a, b} <= {i["id"] for i in r.json().get("items", [])}, r.text[:200])
    # The home feed keeps the member's own radius: Suresh (Dilsukhnagar, 12 km) is within reach of Himayatnagar.
    r = api.call(SURESH, "GET", "/v1/opportunities/feed", params={"skills": "plumbing"})
    ids = {i["id"] for s in r.json().get("sections", []) for i in s["items"]}
    check("trade: the sectioned feed applies the same trade filter", r.status_code == 200 and bool({a, b} & ids), str(len(ids)))
    r = api.call(RAHUL, "GET", "/v1/opportunities/feed/results", params={"skills": "plumbing", "radius_km": 3, "limit": 100})
    check("trade: a radius the person picks still cuts the search",
          r.status_code == 200 and not ({a, b} & {i["id"] for i in r.json().get("items", [])}), "")
    r = api.call(RAHUL, "GET", "/v1/opportunities/feed/results", params={"skills": "electrical", "limit": 100})
    check("trade: an electrician filter does not return the plumbing posts",
          r.status_code == 200 and not ({a, b} & {i["id"] for i in r.json().get("items", [])}), "")
    if a:
        r = api.call(RAHUL, "GET", f"/v1/opportunities/{a}")
        check("trade: a post in a known locality gets coordinates (distance works)", r.status_code == 200 and
              owner_loop_query("SELECT lat IS NOT NULL AS ok FROM vyapar_opportunities.opportunities WHERE id = $1", a)["ok"], "")

    # ---- Card place + distance wording (Priya, Madhapur) ----------------------
    r = api.call("m_priya", "GET", "/v1/opportunities/feed/results", params={"limit": 100})
    cards = r.json().get("items", [])
    with_d = [c for c in cards if c.get("distance_km") is not None]
    check("cards: a distance label on every card with a distance, never '0.0 km'",
          r.status_code == 200 and with_d and all(c.get("distance_label") and "0.0" not in c["distance_label"] for c in with_d),
          str([(c["distance_km"], c.get("distance_label")) for c in with_d[:5]]))
    check("cards: under 0.5 km reads 'In your area'",
          all(c["distance_label"] == "In your area" for c in with_d if c["distance_km"] < 0.5), "")
    check("cards: location shows the locality, not the city",
          all(c.get("location_label") and "hyderabad" not in c["location_label"].lower() for c in cards if c.get("location")),
          str([c.get("location_label") for c in cards[:5]]))
    r = api.call("m_priya", "GET", "/v1/opportunities/feed/results", params={"limit": 20}, lang="te")
    check("cards: the distance label is localized (te)",
          any(c.get("distance_label") and ("కి.మీ." in c["distance_label"] or "ప్రాంతంలో" in c["distance_label"]) for c in r.json().get("items", [])), "")

    # ---- 2. Businesses search -----------------------------------------------
    def search(member, **params):
        r = api.call(member, "GET", "/v1/listings/search", params=params)
        return r.status_code, r.json()

    status, body = search(RAHUL, q="anita")
    names = [x["listing"]["name"] for x in body.get("results", [])]
    check("search: 'anita' finds Anita Khatri's profile (owner name)", status == 200 and any("Anita" in n or "Khatri" in n for n in names), str(names[:5]))
    status, body = search(RAHUL, q="aneeta")
    check("search: spelling-tolerant ('aneeta' -> Anita)", any("Anita" in x["listing"]["name"] or "Khatri" in x["listing"]["name"] for x in body.get("results", [])), str([x["listing"]["name"] for x in body.get("results", [])][:5]))
    status, body = search(RAHUL, q="khatri associates")
    check("search: business name, partial words", any("Khatri" in (x["listing"].get("business_name") or x["listing"]["name"]) for x in body.get("results", [])), "")
    status, body = search(RAHUL, q="ameerpet")
    check("search: a place becomes a distance filter around it",
          status == 200 and (body.get("place") or {}).get("name") == "Ameerpet" and body["results"]
          and all(x["distance_km"] is not None and x["distance_km"] <= (body.get("radius_km") or 5) for x in body["results"]),
          json.dumps({"place": body.get("place"), "radius": body.get("radius_km"), "n": len(body.get("results", []))}))
    status, body = search(RAHUL, q="plumber ameerpet")
    first = (body.get("results") or [{}])[0].get("listing", {})
    check("search: trade word + place ranks the plumber near Ameerpet first", "plumbing" in first.get("capabilities", []), json.dumps(first)[:200])
    status, body = search(RAHUL, q="plumber", locality="Kompally")
    check("search: nothing close -> broadens automatically and says so",
          status == 200 and body.get("results") and body.get("broadened") and body.get("notice_text"),
          json.dumps({"broadened": body.get("broadened"), "notice": body.get("notice_text"), "n": len(body.get("results", []))}, ensure_ascii=False))
    status, body = search(RAHUL, q="ca")
    acct = {"accounting", "accountant", "gst_filing", "tax"}
    check("search: 'CA' finds chartered accountants only (short words match whole words)",
          status == 200 and body.get("results") and all(set(x["listing"]["capabilities"]) & acct for x in body["results"])
          and any(x["listing"]["owner_id"] == ANITA for x in body["results"]),
          str([(x["listing"]["name"], x["listing"]["capabilities"]) for x in body.get("results", [])][:5]))
    status, body = search(RAHUL, q="बिजली मिस्त्री")
    check("search: Hindi trade word finds electricians", status == 200 and any("electrical" in x["listing"]["capabilities"] for x in body.get("results", [])),
          str([x["listing"]["name"] for x in body.get("results", [])][:5]))

    # ---- 3. Notifications ----------------------------------------------------
    r = api.call(DEEPAK, "POST", "/v1/partnership-requests", json={
        "recipient_listing_id": ANITA_LISTING, "need": "A CA to handle GST for our design studio clients.",
        "offer": "Referrals from 40 interior clients a year.", "expectations": "Quarterly review meeting and fair fees.",
        "category": "accounting_tax", "locality": "Banjara Hills", "timing": "Starting next month, ongoing.",
        "next_step": "A 20-minute call this week to agree terms."})
    if r.status_code == 201:
        created["partnerships"].append(r.json()["id"])
    check("notif: partnership request sent (real flow)", r.status_code == 201, r.text[:200])
    titles = {}
    for lang in ("hi", "te", "en"):
        rr = api.call(ANITA, "GET", "/v1/notifications", lang=lang)
        n = next((x for x in rr.json() if r.status_code == 201 and x["link"] and r.json()["id"] in x["link"]), None)
        titles[lang] = n["title"] if n else None
    check("notif: the same notification reads in the reader's language (hi, te, en)",
          titles["hi"] and titles["te"] and titles["en"] and len({titles["hi"], titles["te"], titles["en"]}) == 3,
          json.dumps(titles, ensure_ascii=False))
    rr = api.call(ANITA, "GET", "/v1/notifications/page", lang="te")
    check("notif: the paged inbox renders in the reader's language too",
          rr.status_code == 200 and any(x["title"] == titles["te"] for x in rr.json().get("items", [])), "")
    from app.i18n import translate
    check("notif: glossary wording ('matches your skills', 'posts')",
          "skills" in translate("notifications.strongMatch.body", "en") and "posts" in translate("notifications.digest.title", "en", count=3)
          and "opportunit" not in translate("notifications.savedSearchMatch.body", "en"), "")

    dedupe = owner_loop_query("__notification_passes__")
    check("notif: two match passes never announce the same post to the same member twice", dedupe["dup_pairs"] == 0, str(dedupe))
    check("notif: no match or alert for an expired or closed post", dedupe["stale"] == 0, str(dedupe))
    check("notif: a second digest pass sends nothing", dedupe["digest_second"] == 0, str(dedupe))
    check("notif: every new notification links to the thing it is about", dedupe["bad_links"] == 0, str(dedupe))


async def main() -> int:
    port = free_port()
    created = {"opportunities": [], "enquiries": [], "packages": [], "searches": [], "tokens": [], "contracts": [], "blocks": [], "partnerships": []}
    owner = await asyncpg.connect(OWNER_DSN)
    created["started"] = await owner.fetchval("SELECT now()")
    snap = await snapshot(owner)
    proc = subprocess.Popen(
        [str(SERVICE_DIR / ".venv" / "Scripts" / "python.exe"), "-m", "uvicorn", "app.main:app", "--port", str(port), "--log-level", "warning"],
        cwd=str(SERVICE_DIR), stdout=subprocess.DEVNULL, stderr=open(SERVICE_DIR / "scripts" / "check_backend_b.server.log", "w"),
    )
    print(f"uvicorn pid {proc.pid} on port {port}")
    loop = asyncio.get_running_loop()

    async def saved_search_alerts(member_id: str, fresh_cap: bool = True) -> int:
        from app.config import get_settings
        from app.services.notifications import _saved_search_alerts

        app_conn = await asyncpg.connect(APP_DSN)
        try:
            tr = app_conn.transaction()
            await tr.start()
            await app_conn.execute("SELECT set_config('vyapar.service_role', 'dispatcher', true)")
            await app_conn.execute("SELECT set_config('vyapar.authz_context', 'm_neha_ops', true)")
            if fresh_cap:
                # The live server's matcher may already have used today's cap;
                # clear it inside this rolled-back transaction only.
                await app_conn.execute("DELETE FROM vyapar_platform.rate_limit_counter WHERE rate_limit_key = $1", f"notify:{member_id}:day")
            else:
                await app_conn.execute(
                    "SELECT vyapar_platform.check_and_increment($1, 86400, 0)", f"notify:{member_id}:day")
            members = await app_conn.fetch(
                "SELECT id, capabilities, help_with, locality, lat, lng, radius_km, language FROM vyapar_identity.members WHERE id = $1", member_id)
            n = await _saved_search_alerts(app_conn, {m["id"]: m for m in members}, {}, get_settings())
            await tr.rollback()
            return n
        finally:
            await app_conn.close()

    async def notification_passes() -> dict:
        """The real match and digest passes, run twice inside one transaction
        that is rolled back: nothing reaches any real inbox."""
        from app.services.notifications import run_digest_pass, run_strong_match_pass

        conn = await asyncpg.connect(OWNER_DSN)
        tr = conn.transaction()
        await tr.start()

        class _Pool:
            def acquire(self_inner):
                class _C:
                    async def __aenter__(self2):
                        return conn

                    async def __aexit__(self2, *exc):
                        return False
                return _C()

        try:
            hour = (datetime.now(timezone.utc) + timedelta(minutes=330)).hour
            await conn.execute("UPDATE vyapar_privacy.privacy_settings SET digest_enabled = true, digest_hour = $1", hour)
            await conn.execute("DELETE FROM vyapar_platform.rate_limit_counter WHERE rate_limit_key LIKE 'notify:%'")
            pool = _Pool()
            await run_strong_match_pass(pool)
            await run_strong_match_pass(pool)
            await run_digest_pass(pool)
            second = await run_digest_pass(pool)
            new = await conn.fetch("SELECT * FROM vyapar_integration.notifications WHERE created_at = now()")
            pairs = []
            for n in new:
                p = n["params"] if isinstance(n["params"], dict) else json.loads(n["params"] or "{}")
                if n["kind"] == "opportunity_match":
                    for oid in ([p["opportunity_id"]] if p.get("opportunity_id") else []) + list(p.get("opportunity_ids") or []):
                        pairs.append((n["member_id"], oid))
            dup = 0
            for member, oid in set(pairs):
                c = await conn.fetchval(
                    """SELECT count(*) FROM vyapar_integration.notifications
                        WHERE member_id = $1 AND kind = 'opportunity_match'
                          AND (params->>'opportunity_id' = $2 OR params->'opportunity_ids' ? $2)""", member, oid)
                dup += c > 1
            stale = 0
            for _, oid in set(pairs):
                stale += not await conn.fetchval(
                    """SELECT state = 'active' AND (deadline IS NULL OR deadline > now())
                         FROM vyapar_opportunities.opportunities WHERE id = $1::uuid""", oid)
            bad_links = sum(1 for n in new if not ((n["link"] or "").startswith("/opportunities/") or (n["link"] or "").startswith("/?")))
            return {"new": len(new), "dup_pairs": dup, "stale": stale, "digest_second": second, "bad_links": bad_links}
        finally:
            await tr.rollback()
            await conn.close()

    def owner_query(sql: str, *args):
        async def run():
            if sql == "__notification_passes__":
                return await notification_passes()
            if sql == "__saved_search_alerts__":
                return await saved_search_alerts(*args)
            if sql == "__saved_search_alerts_capped__":
                return await saved_search_alerts(*args, fresh_cap=False)
            return await owner.fetchrow(sql, *args)
        return asyncio.run_coroutine_threadsafe(run(), loop).result(60)

    try:
        api = Api(f"http://127.0.0.1:{port}")
        for _ in range(60):
            try:
                if api.http.get("/health").status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            await asyncio.sleep(0.5)
        else:
            print("server did not start; see scripts/check_backend_b.server.log")
            return 1
        await loop.run_in_executor(None, run_checks, api, created, owner_query)
        await loop.run_in_executor(None, run_precall_checks, api, created, owner_query)
        await loop.run_in_executor(None, run_followup_checks, api, created, owner_query)
        await loop.run_in_executor(None, run_rows_checks, api, created, owner_query)
        await loop.run_in_executor(None, run_owner_checks, api, created, owner_query)
        await loop.run_in_executor(None, run_discover_checks, api, created, owner_query)
    finally:
        await cleanup(owner, snap, created)
        await owner.close()
        # The venv python.exe is a launcher with a child interpreter: stop this
        # run's own process tree (and nothing else) by its root PID.
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
        try:
            proc.wait(10)
        except subprocess.TimeoutExpired:
            pass
        print("cleanup done; server stopped")
    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

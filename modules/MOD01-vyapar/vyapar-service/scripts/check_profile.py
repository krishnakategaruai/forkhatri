"""End-to-end check for "one Vyapar profile per member" (owner decision,
2026-09-30), against a running Vyapar API on a private port.

  constraint:    the database refuses a second live profile for a member;
                 POST /v1/listings answers 409 profile_exists with the id.
  consolidation: Meena (3 listings before migration 026) has one profile,
                 "Meena Sahni" with the business section "Meena's Oven", the
                 verification, contacts and history of the verified listing,
                 the skills of all three; the two others are archived as
                 merged; her listing list shows one; search finds her by the
                 business name; the card title reads "Meena Sahni · Meena's Oven".
  identity:      a new member arriving from ForKhatri (identity synced through
                 the same ensure_member() the session provider calls) gets
                 name, phone and language prefilled and is asked only for the
                 locality; "use my location" resolves it; the first PATCH
                 creates the profile; a business section can be added and
                 removed; a typed locality is normalised.

Everything it creates is deleted at the end; reads it makes of seeded
profiles leave no trace (views, impressions and saved rows are restored),
and a sweep over every vyapar_* table confirms nothing mentions the test
member or listing.

Usage (from vyapar-service/):
    .venv/Scripts/python scripts/check_profile.py --api http://127.0.0.1:<port>
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import asyncpg

MEENA = "m_meena"
OTHER = "m_ravi"
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


def code(body: dict) -> str | None:
    return (body.get("error") or {}).get("code")


async def main(api_base: str) -> int:
    api = Api(api_base)
    db = await asyncpg.connect(owner_dsn())
    test_member = f"m_check_profile_{secrets.token_hex(3)}"
    started_at = await db.fetchval("SELECT now()")
    max_imp = await db.fetchval("SELECT coalesce(max(id), 0) FROM vyapar_commercial.impressions")
    max_evt = await db.fetchval("SELECT coalesce(max(id), 0) FROM vyapar_analytics.analytics_events")
    meena_id = await db.fetchval(
        "SELECT id::text FROM vyapar_listings.listings WHERE owner_id = $1 AND state IN ('draft','submitted','active_unverified','active_verified')", MEENA)
    seen_before = {(r["member_id"], str(r["listing_id"])): dict(r) for r in await db.fetch(
        "SELECT * FROM vyapar_listings.member_listing WHERE listing_id = $1::uuid", meena_id)}
    try:
        # ------------------------------------------------------------ constraint
        print("\n== One profile per member ==")
        check(await db.fetchval("SELECT count(*) FROM vyapar_listings.profile_consolidation_plan()") == 0, "dry-run plan is empty: nothing left to merge")
        multi = await db.fetchval(
            """SELECT count(*) FROM (SELECT owner_id FROM vyapar_listings.listings
                WHERE state IN ('draft','submitted','active_unverified','active_verified') GROUP BY owner_id HAVING count(*) > 1) x""")
        check(multi == 0, "no member has more than one live profile")
        refused = False
        try:
            async with db.transaction():
                await db.execute(
                    """INSERT INTO vyapar_listings.listings (owner_id, kind, name, locality) VALUES ($1, 'professional', 'Second profile', 'Himayatnagar')""",
                    MEENA)
                raise RuntimeError("inserted")  # never keep it
        except asyncpg.UniqueViolationError:
            refused = True
        except RuntimeError:
            refused = False
        check(refused, "the database refuses a second live profile (listings_one_profile_per_owner)")
        st, res = api.call("POST", "/v1/listings", MEENA, {"kind": "business", "name": "Meena's Second Oven", "locality": "Himayatnagar"})
        check(st == 409 and code(res) == "profile_exists" and res["error"]["details"].get("existing_listing_id") == meena_id,
              f"POST /v1/listings answers 409 profile_exists with the existing id ({code(res)})")

        # ------------------------------------------------------------ consolidation
        print("\n== Meena, consolidated ==")
        st, me = api.call("GET", "/v1/me/profile", MEENA)
        p = me.get("profile") or {}
        check(st == 200 and me["exists"] and p.get("id") == meena_id, "getMyProfile returns her one profile")
        check(p.get("name") == "Meena Sahni" and p.get("has_business") and p.get("business_name") == "Meena's Oven"
              and p.get("card_title") == "Meena Sahni · Meena's Oven", f"person plus business section ({p.get('card_title')})")
        check(p.get("verification_state") == "verified" and p.get("state") == "active_verified", "the verified listing survived, with its verification")
        check({"bakery", "cakes", "tutoring"} <= set(p.get("capabilities", [])) and p.get("headline") == "Weekend baking workshops for beginners",
              f"skills and the person's headline folded in from the professional listing ({p.get('capabilities')})")
        merged = await db.fetch("SELECT name, state, state_reason FROM vyapar_listings.listings WHERE owner_id = $1 AND state = 'archived'", MEENA)
        check(len(merged) == 2 and all(r["state_reason"] == f"merged_into:{meena_id}" for r in merged),
              f"the other two are archived as merged ({[r['name'] for r in merged]})")
        st, mine = api.call("GET", "/v1/listings/mine", MEENA)
        check(st == 200 and [x["id"] for x in mine] == [meena_id], f"her listing list shows one profile ({len(mine)})")
        dangling = await db.fetchval(
            """SELECT (SELECT count(*) FROM vyapar_enquiries.enquiries e JOIN vyapar_listings.listings l ON l.id = e.listing_id WHERE l.state_reason LIKE 'merged_into:%')
                    + (SELECT count(*) FROM vyapar_reviews.reviews r JOIN vyapar_listings.listings l ON l.id = r.subject_listing_id WHERE l.state_reason LIKE 'merged_into:%')
                    + (SELECT count(*) FROM vyapar_listings.listing_packages k JOIN vyapar_listings.listings l ON l.id = k.listing_id WHERE l.state_reason LIKE 'merged_into:%')""")
        check(dangling == 0, "no enquiry, review or package still points at a merged listing")
        st, found = api.call("GET", "/v1/listings/search?q=Oven", OTHER)
        hit = next((r["listing"] for r in found.get("results", []) if r["listing"]["id"] == meena_id), None)
        check(hit is not None and hit["card_title"] == "Meena Sahni · Meena's Oven", "search finds her by the business name; the card reads person · business")
        st, detail = api.call("GET", f"/v1/listings/{meena_id}", OTHER)
        check(st == 200 and detail["has_business"] and detail["business_name"] == "Meena's Oven", "listing detail keeps working with the same id")

        # ------------------------------------------------------------ identity prefill
        print("\n== A new member from ForKhatri: nothing asked twice ==")
        # the identity sync the ForKhatri session provider performs on sign-in
        await db.execute("SELECT vyapar_identity.ensure_member($1, $2, $3, $4)", test_member, "Lakshmi Naidu", "+919800012345", "te")
        st, me = api.call("GET", "/v1/me/profile", test_member, lang="te")
        check(st == 200 and me["exists"] is False and me["missing"] == ["locality"],
              f"only the locality is asked for ({me.get('missing')})")
        check(me["prefill"]["name"] == "Lakshmi Naidu" and me["prefill"]["phone"] == "+919800012345" and me["prefill"]["language"] == "te"
              and set(me["prefilled_from_identity"]) == {"name", "phone", "language"}, "name, phone and language come from the identity")
        st, loc = api.call("POST", "/v1/me/profile/locate", test_member, {"lat": 17.4021, "lng": 78.4846})
        check(st == 200 and loc["matched"] and loc["locality"] == "Himayatnagar", f"'use my location' resolves the locality ({loc.get('locality')})")
        st, far = api.call("POST", "/v1/me/profile/locate", test_member, {"lat": 28.6139, "lng": 77.2090})
        check(st == 200 and far["matched"] is False and far["locality"] is None, "a position far from any known locality is not guessed")
        st, me = api.call("PATCH", "/v1/me/profile", test_member, {"locality": loc["locality"], "lat": 17.4021, "lng": 78.4846}, lang="te")
        p = me.get("profile") or {}
        check(st == 200 and me["exists"] and p.get("name") == "Lakshmi Naidu" and p.get("primary_phone") == "+919800012345"
              and p.get("languages") == ["te"] and p.get("locality") == "Himayatnagar" and p.get("state") == "draft",
              f"first PATCH creates the profile from the identity ({p.get('name')}, {p.get('locality')})")
        test_listing = p.get("id")
        check(any(c["channel"] == "phone" and c["disclosure"] == "after_accept" for c in p.get("contacts", [])), "the identity phone is a contact, shown after acceptance")
        member_loc = await db.fetchval("SELECT locality FROM vyapar_identity.members WHERE id = $1", test_member)
        check(member_loc == "Himayatnagar", "the member row learns the locality too (no other screen asks again)")
        st, again = api.call("GET", "/v1/me/profile", test_member)
        check(again["profile"]["id"] == test_listing, "the same profile on every read")
        st, res = api.call("POST", "/v1/listings", test_member, {"kind": "professional", "name": "Lakshmi Naidu — Tiffins", "locality": "Himayatnagar"})
        check(st == 409 and code(res) == "profile_exists", "a second profile is refused")
        st, me = api.call("PATCH", "/v1/me/profile", test_member, {"business": {"name": "Lakshmi Tiffins", "headline": "Home-style breakfast tiffins"},
                                                                   "headline": "Home cook, breakfast and lunch", "capabilities": ["cook"]})
        p = me["profile"]
        check(p["has_business"] and p["kind"] == "business" and p["card_title"] == "Lakshmi Naidu · Lakshmi Tiffins"
              and p["business_headline"] == "Home-style breakfast tiffins" and p["capabilities"] == ["cook"], f"business section added ({p['card_title']})")
        st, me = api.call("PATCH", "/v1/me/profile", test_member, {"remove_business": True})
        check(not me["profile"]["has_business"] and me["profile"]["kind"] == "professional", "business section removed")
        st, me = api.call("PATCH", "/v1/me/profile", test_member, {"locality": "KPHB"})
        check(me["profile"]["locality"] == "Kukatpally", f"a typed locality is normalised to the known name ({me['profile']['locality']})")
    finally:
        await cleanup(db, test_member, meena_id, seen_before, max_imp, max_evt, started_at)
        await db.close()

    failed = [label for ok, label in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    for label in failed:
        print("  failed:", label)
    return 1 if failed else 0


async def cleanup(db, test_member: str, meena_id: str, seen_before: dict, max_imp: int, max_evt: int, started_at) -> None:
    print("\n== Cleanup ==")
    listing_ids = [r["id"] for r in await db.fetch("SELECT id FROM vyapar_listings.listings WHERE owner_id = $1", test_member)]
    async with db.transaction():
        n = {}
        # the check's own search and detail reads (anonymous listing impressions logged during this run)
        n["impressions"] = await db.execute(
            "DELETE FROM vyapar_commercial.impressions WHERE id > $1 AND member_id IS NULL AND target_kind = 'listing' AND at >= $2",
            max_imp, started_at)
        n["analytics_events"] = await db.execute(
            "DELETE FROM vyapar_analytics.analytics_events WHERE id > $1 AND object_id = ANY($2::text[])", max_evt, [meena_id, *map(str, listing_ids)])
        # views of Meena's profile by this check: restore exactly what was there
        for row in await db.fetch("SELECT member_id FROM vyapar_listings.member_listing WHERE listing_id = $1::uuid", meena_id):
            before = seen_before.get((row["member_id"], meena_id))
            if before is None:
                await db.execute("DELETE FROM vyapar_listings.member_listing WHERE member_id = $1 AND listing_id = $2::uuid", row["member_id"], meena_id)
            else:
                await db.execute("UPDATE vyapar_listings.member_listing SET viewed_at = $3, saved_at = $4 WHERE member_id = $1 AND listing_id = $2::uuid",
                                 row["member_id"], meena_id, before["viewed_at"], before["saved_at"])
        n["listing_outbox"] = await db.execute(
            "DELETE FROM vyapar_listings.outbox_event WHERE created_at >= $1 AND payload::text LIKE ANY($2)", started_at,
            [f"%{test_member}%", *[f"%{i}%" for i in listing_ids]])
        n["listings"] = await db.execute("DELETE FROM vyapar_listings.listings WHERE owner_id = $1", test_member)
        n["member_rows"] = 0
        for schema, table, col in (("vyapar_privacy", "privacy_settings", "member_id"), ("vyapar_privacy", "acceptances", "member_id"),
                                   ("vyapar_integration", "notifications", "member_id"), ("vyapar_integration", "audit_events", "actor_id")):
            await db.execute(f"DELETE FROM {schema}.{table} WHERE {col} = $1", test_member)
        n["members"] = await db.execute("DELETE FROM vyapar_identity.members WHERE id = $1", test_member)
    for k, v in n.items():
        print(f"  {k}: {v}")
    patterns = [f"%{test_member}%", *[f"%{i}%" for i in listing_ids]]
    leftovers = []
    for t in await db.fetch("SELECT schemaname, tablename FROM pg_tables WHERE schemaname LIKE 'vyapar\\_%' ORDER BY 1, 2"):
        count = await db.fetchval(f'SELECT count(*) FROM "{t["schemaname"]}"."{t["tablename"]}" x WHERE x::text LIKE ANY($1)', patterns)
        if count:
            leftovers.append(f"{t['schemaname']}.{t['tablename']}={count}")
    extra_views = await db.fetchval("SELECT count(*) FROM vyapar_commercial.impressions WHERE id > $1 AND target_id = $2::uuid", max_imp, meena_id)
    check(not leftovers and extra_views == 0, f"no leftover rows from this check ({', '.join(leftovers) or 'clean'})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--api", default=os.environ.get("VYAPAR_CHECK_API_BASE"), help="Base URL of a running Vyapar API (or VYAPAR_CHECK_API_BASE)")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if not args.api:
        parser.error("--api (or VYAPAR_CHECK_API_BASE) is required")
    sys.exit(asyncio.run(main(args.api)))

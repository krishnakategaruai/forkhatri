"""End-to-end check for Vyapar's learned taste (recommendations that learn),
against a running Vyapar API on a private port (DEV_MODE=true).

Two new members join through the normal member path (first request, first
run, privacy + terms): Satish Goud, an electrician in Dilsukhnagar, and Sai
Ram Electricals, a shop in Kothapet that posts an electrician job. Satish then
uses Discover the way a person does, and the check confirms:

  cold start    with no history the results, rows and reasons are identical
                to the ranking with personalisation off; taste confidence 0
  each action   viewing, saving, sharing, opening the source, applying,
                "More like this" and being hired each teach the taste, with
                the right source (applied / saved) and weight order
                (hired > applied > saved > viewed)
  decay         an action 30 days old counts half (pure model check)
  negatives     "Not my skill" on a delivery post avoids Delivery at once and
                sends delivery posts to the end of the results; "Too far"
                sets a distance limit (never below 3 km); "Pay too low" sets a
                pay floor and value_fit
  exploration   about 1 in 8 result slots is "Something new near your
                skills", at slots 8, 16 ..., the same picks on a repeat call;
                "Why this?" says so
  rows          For you stays first, at most 6 rows, a taste row appears
  control       getMyTaste in en/hi/te, removeMyTasteItem, resetMyTaste
                (back to the cold-start ranking), data export includes taste
  privacy       turning personalisation off empties the taste, uses none of
                it, and an action taken while off is never learned later
  profession    an advocate's profile stays neutral in search after the
                member saved and contacted her
  RLS           an operator cannot read or write another member's taste
  deletion      account deletion deletes the taste

Everything it creates is deleted at the end, and a sweep over every vyapar_*
table confirms nothing mentions an id this run created.

Usage (from vyapar-service/):
    .venv/Scripts/python scripts/check_taste.py --api http://127.0.0.1:<port>
"""
from __future__ import annotations

import argparse
import asyncio
import os
import secrets
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import asyncpg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.check_trust_pack import Api, owner_dsn  # noqa: E402

RESULTS: list[tuple[bool, str]] = []
OPERATOR, KAVITA = "m_neha_ops", "m_kavita"
DILSUKHNAGAR = (17.3688, 78.5247)
KOTHAPET = (17.3676, 78.5440)


def check(cond: bool, label: str) -> None:
    RESULTS.append((bool(cond), label))
    print(("  PASS  " if cond else "  FAIL  ") + label)


def app_dsn() -> str:
    from app.config import get_settings

    return get_settings().database_url


def has_script(text: str | None, lo: str, hi: str) -> bool:
    return any(lo <= ch <= hi for ch in (text or ""))


class Run:
    def __init__(self, api: Api, db: asyncpg.Connection, tag: str | None = None) -> None:
        tag = tag or secrets.token_hex(3)
        self.api, self.db = api, db
        self.me = f"m_check_taste_{tag}"
        self.shop = f"m_check_taste_shop_{tag}"
        self.opps: set[str] = set()
        self.enquiries: set[str] = set()

    def call(self, method, path, body=None, member=None, lang="en"):
        return self.api.call(method, path, member or self.me, body, lang=lang)

    def results(self, member=None, full: bool = False):
        st, res = self.call("GET", "/v1/opportunities/feed/results?limit=100", member=member)
        assert st == 200, (st, res)
        return res if full else res["items"]

    def rows(self) -> dict:
        st, res = self.call("GET", "/v1/opportunities/feed/rows")
        assert st == 200, (st, res)
        return res

    def taste(self, lang="en") -> dict:
        st, res = self.call("GET", "/v1/me/taste", lang=lang)
        assert st == 200, (st, res)
        return res

    async def model(self) -> dict:
        import json

        self.taste()  # the taste is rebuilt on the member's next read after any action

        raw = await self.db.fetchval("SELECT model FROM vyapar_privacy.member_taste WHERE member_id = $1", self.me)
        return json.loads(raw) if isinstance(raw, str) else (raw or {})


async def join(r: Run, member: str, name: str, place: str, latlng, caps: list[str], headline: str, business: dict | None = None) -> None:
    r.call("GET", "/v1/first-run/state", member=member)  # just-in-time member
    st, _ = r.call("POST", "/v1/first-run/step", {"step": 5, "display_name": name, "language": "en", "locality": place,
                                                 "lat": latlng[0], "lng": latlng[1], "radius_km": 15, "work_mode": "on_site",
                                                 "capabilities": caps}, member=member)
    assert st == 200, st
    for kind in ("privacy", "terms"):
        r.call("POST", f"/v1/legal/{kind}/accept", member=member)
    # the one profile (a draft is enough to post and apply)
    r.call("GET", "/v1/me/profile", member=member)
    patch = {"name": name, "headline": headline, "capabilities": caps, "categories": ["home_repair"], "locality": place,
             "lat": latlng[0], "lng": latlng[1], "experience_years": 6, "languages": ["te", "en"], "availability": "now"}
    if business:
        patch["business"] = business
    st, _ = r.call("PATCH", "/v1/me/profile", patch, member=member)
    assert st == 200, ("profile", st, _)


async def live_posts(r: Run, where: str, *args) -> list[str]:
    rows = await r.db.fetch(
        f"""SELECT id::text FROM vyapar_opportunities.opportunities o
             WHERE state = 'active' AND NOT distribution_limited AND (deadline IS NULL OR deadline >= now())
               AND poster_id NOT LIKE 'm_check_%' AND {where} ORDER BY id""", *args)
    return [x["id"] for x in rows]


# ---------------------------------------------------------------------------
async def section_setup_and_cold_start(r: Run) -> None:
    print("\n== Setup: two members join ==")
    await join(r, r.me, "Satish Goud", "Dilsukhnagar", DILSUKHNAGAR, ["electrical"], "Electrician: house wiring, MCB and fan fitting")
    await join(r, r.shop, "Venkatesh Yadav", "Kothapet", KOTHAPET, ["electrical"], "Owner, Sai Ram Electricals",
               {"name": "Sai Ram Electricals", "headline": "Electrical contractors for homes and shops, Kothapet"})
    deadline = (datetime.now(timezone.utc) + timedelta(days=20)).isoformat()
    st, opp = r.call("POST", "/v1/opportunities", {
        "entry_mode": "create", "source_segment": "community", "work_mode": "on_site", "response_method": "in_app",
        "type": "employment", "title": "Electrician for house wiring and repairs — Kothapet",
        "description": "Sai Ram Electricals needs an electrician for house wiring, MCB and fan fitting jobs around Kothapet and LB Nagar.",
        "location": "Kothapet", "deadline": deadline, "required_capabilities": ["electrical"],
        "structured": {"salary_min_paise": 1800000, "salary_max_paise": 2200000}}, member=r.shop)
    check(st == 201, f"the shop's job is created ({st})")
    r.opps.add(opp["id"])
    if opp.get("unconfirmed_fields"):
        r.call("PATCH", f"/v1/opportunities/{opp['id']}/confirm", {"fields": opp["unconfirmed_fields"]}, member=r.shop)
    st, pub = r.call("POST", f"/v1/opportunities/{opp['id']}/publish", member=r.shop)
    check(st == 200 and pub.get("state") == "active", f"and published ({st} {pub.get('state')})")
    r.shop_job = opp["id"]

    print("\n== Cold start: no history ranks exactly as before ==")
    t = r.taste()
    check(t["confidence"] == 0 and t["actions_counted"] == 0 and t["enabled"], f"getMyTaste: nothing learned yet ({t['summary']})")
    on = [(c["id"], c["relevance_reason"]) for c in r.results()]
    rows_on = [(row["key"], [c["id"] for c in row["items"]]) for row in r.rows()["rows"]]
    r.call("PATCH", "/v1/privacy", {"personalised_recommendations": False})
    off = [(c["id"], c["relevance_reason"]) for c in r.results()]
    rows_off = [(row["key"], [c["id"] for c in row["items"]]) for row in r.rows()["rows"]]
    r.call("PATCH", "/v1/privacy", {"personalised_recommendations": True})
    check(on == off and len(on) > 20, f"results identical with and without personalisation ({len(on)} posts)")
    check(rows_on == rows_off, f"rows identical ({[k for k, _ in rows_on]})")
    check(not any(reason.startswith("taste") or reason == "explore" for _, reason in on), "no taste or explore reason without history")

    from app.services.feed import _opportunity_signals
    from app.taste import Taste

    row = await r.db.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1::uuid", r.shop_job)
    sig = _opportunity_signals(row, {"capabilities": ["electrical"], "taste": Taste.empty()}, 2.0)
    check(sig.taste_fit == 0 and sig.value_fit == 0, "signals: taste_fit and value_fit are 0 with an empty taste")


async def section_learning(r: Run) -> None:
    print("\n== Learning from each kind of action ==")
    ac = await live_posts(r, "'ac_technician' = ANY(required_capabilities)")
    plumbing = await live_posts(r, "'plumbing' = ANY(required_capabilities)")
    electrical = await live_posts(r, "'electrical' = ANY(required_capabilities) AND type = 'employment'")
    public = await live_posts(r, "source_segment = 'public'")
    r.ac, r.plumbing = ac, plumbing

    st, _ = r.call("GET", f"/v1/opportunities/{plumbing[0]}")
    t = r.taste()
    m = await r.model()
    check(st == 200 and m.get("w", {}).get("skill:plumbing", 0) > 0 and t["actions_counted"] == 0,
          f"viewing a plumbing post teaches a little and is not a meaningful action ({m.get('w', {}).get('skill:plumbing')})")
    view_w = m["w"]["skill:plumbing"]

    st, _ = r.call("POST", f"/v1/opportunities/{ac[0]}/save")
    m = await r.model()
    check(st == 200 and m["src"].get("skill:ac_technician") == "saved" and m["n"] == 1,
          f"saving an AC-repair post: skill learned, source 'saved' (n={m.get('n')})")
    saved_w = m["w"]["skill:ac_technician"]
    check(saved_w > view_w, f"a save weighs more than a view ({saved_w} > {view_w})")

    st, _ = r.call("POST", f"/v1/opportunities/{plumbing[1 if len(plumbing) > 1 else 0]}/share")
    m = await r.model()
    check(st == 200 and m["n"] == 2, f"sharing counts ({m['n']})")
    if public:
        st, _ = r.call("POST", f"/v1/opportunities/{public[0]}/external-open")
        m = await r.model()
        check(st == 200 and m["n"] == 3, f"opening a shared-from-elsewhere source counts ({m['n']})")

    st, enq = r.call("POST", "/v1/enquiries", {"opportunity_id": electrical[0], "message": "Namaste, I am an electrician in Dilsukhnagar with 6 years of house wiring work."})
    check(st == 201, f"applying to an electrical job ({st})")
    if st == 201:
        r.enquiries.add(enq["id"])
    m = await r.model()
    check(m["src"].get("skill:electrical") == "applied", f"applying teaches the skill with source 'applied' ({m['src'].get('skill:electrical')})")
    applied_w = m["w"].get("skill:electrical", 0)
    check(applied_w > saved_w, f"an application weighs more than a save ({applied_w} > {saved_w})")

    st, t = r.call("POST", f"/v1/opportunities/{ac[-1]}/more-like-this")
    check(st == 200 and t["confidence"] > 0, f"moreLikeThis returns the updated taste ({st}, confidence {t.get('confidence')})")
    mlt = next((i for i in t.get("likes", []) if i["id"] == "skill:ac_technician"), None)
    check(mlt is not None and mlt["source"] == "more_like_this" and "From posts you asked for more of" in t["summary_text"],
          f"'More like this' has its own source and line ({mlt and mlt['source']}; {t.get('summary_text')})")
    st, why = r.call("GET", f"/v1/opportunities/{ac[-1]}/why")
    check(st == 200 and "taste_fit_saved" not in why["signals"], f"and is never explained as 'saved' ({why.get('signals')})")
    st, _ = r.call("POST", f"/v1/opportunities/{r.shop_job}/more-like-this", member=r.shop)
    check(st == 400, f"moreLikeThis on your own post is refused ({st})")
    st, _ = r.call("POST", "/v1/opportunities/00000000-0000-0000-0000-000000000000/more-like-this")
    check(st == 404, f"moreLikeThis on an unknown post is 404 ({st})")

    # hired: Satish applies to the shop's job and the shop hires him
    st, enq = r.call("POST", "/v1/enquiries", {"opportunity_id": r.shop_job, "message": "I can start this week, I live 2 km away in Dilsukhnagar."})
    check(st == 201, f"applying to Sai Ram Electricals' job ({st})")
    r.enquiries.add(enq["id"])
    before = (await r.model())["w"].get("skill:electrical", 0)
    st, res = r.call("POST", f"/v1/opportunities/{r.shop_job}/applicants/{enq['id']}/stage", {"stage": "hired"}, member=r.shop)
    check(st == 200 and res.get("stage") == "hired", f"the shop hires him ({st} {res.get('stage')})")
    after = (await r.model())["w"].get("skill:electrical", 0)
    check(after > before, f"being hired is the strongest positive ({before} -> {after})")

    print("\n== Decay (pure model) ==")
    from app.taste import PostEvents, build_model

    now = datetime.now(timezone.utc)
    f = {"skill": {"electrical"}}
    today = build_model([PostEvents(features=f, actions={"applied": now})], now=now)["w"]["skill:electrical"]
    month = build_model([PostEvents(features=f, actions={"applied": now - timedelta(days=30)})], now=now)["w"]["skill:electrical"]
    check(abs(month / today - 0.5) < 0.01, f"30 days old counts half ({today} vs {month})")
    old = build_model([PostEvents(features=f, actions={"applied": now - timedelta(days=400)})], now=now)
    check(old["n"] == 0 and not old["w"], "older than a year is not used")


async def section_negatives(r: Run) -> None:
    print("\n== Hard negatives: Not my skill, Too far, Pay too low ==")
    delivery = await live_posts(r, "required_capabilities = ARRAY['delivery']")
    delivery_jobs = await live_posts(r, "required_capabilities = ARRAY['delivery'] AND type = 'employment'")
    # the contradiction found in the web test: he applied to a delivery job once, then says "wrong trade"
    st, enq = r.call("POST", "/v1/enquiries", {"opportunity_id": delivery_jobs[-1], "message": "I have a bike and can do deliveries in the evening."})
    if st == 201:
        r.enquiries.add(enq["id"])
    before = (await r.model()).get("w", {}).get("skill:delivery", 0)
    check(st == 201 and before > 0, f"after applying to a delivery job, Delivery is a like ({st}, weight {before})")
    delivery = [x for x in delivery if x != delivery_jobs[-1]]
    st, _ = r.call("POST", f"/v1/opportunities/{delivery[0]}/not-interested", {"reason": "not_my_capability"})
    t = r.taste()
    check(st == 200 and any(i["id"] == "skill:delivery" for i in t["avoids"]) and "Not interested in: Delivery" in t["summary_text"],
          f"'Not my skill' avoids Delivery at once ({t['summary_text']})")
    delivery_label = next(i["label"] for i in t["avoids"] if i["id"] == "skill:delivery")
    check(not any(i["label"] == delivery_label for i in t["likes"]) and "Delivery" not in t["summary_text"].split("Not interested in")[0],
          "the recent 'wrong trade' wins: Delivery is no longer a like, and not in 'You often apply to'")
    keys = [x["key"] for x in r.rows()["rows"]]
    check(not any(k.startswith("taste_applied:") and k.split(":", 1)[1] == "delivery" for k in keys),
          f"no 'Because you applied to Delivery' row ({keys})")
    from app.taste import Taste, post_features

    drow = await r.db.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1::uuid", delivery_jobs[0])
    check(Taste(await r.model()).fit(post_features(drow, 3.0))[0] == 0, "and a delivery post gets no taste boost at all")
    check(not any(i["kind"] == "word" for i in t["likes"] + t["avoids"]),
          f"no bare title words are shown ({[i['label'] for i in t['likes'] + t['avoids'] if i['kind'] == 'word']})")
    labels = [(i["direction"], i["label"]) for i in t["likes"] + t["avoids"]]
    check(len(labels) == len(set(labels)), "one line per trade (a word that names a skill is shown by the skill's label)")
    res = r.results(full=True)
    items = res["items"]
    ids = [c["id"] for c in items]
    deliv = {x for x in delivery if x in ids}
    first_delivery = min(ids.index(x) for x in deliv) if deliv else len(ids)
    others_after = [c for c in items[first_delivery:] if c["id"] not in deliv]
    check(not others_after and (deliv or res["total"] > len(items)),
          f"delivery posts moved to the end of the results ({len(deliv)} in the first {len(ids)} of {res['total']}, first at {first_delivery})")
    check(delivery[0] not in ids, "and the hidden post itself is gone")

    far = await r.db.fetch(
        """SELECT id::text, vyapar_platform.distance_km($1, $2, lat, lng) AS d FROM vyapar_opportunities.opportunities
            WHERE state = 'active' AND work_mode = 'on_site' AND lat IS NOT NULL AND (deadline IS NULL OR deadline >= now())
              AND poster_id NOT LIKE 'm_check_%' AND vyapar_platform.distance_km($1, $2, lat, lng) BETWEEN 9 AND 14
            ORDER BY 2 LIMIT 1""", *DILSUKHNAGAR)
    if far:
        st, _ = r.call("POST", f"/v1/opportunities/{far[0]['id']}/not-interested", {"reason": "too_far"})
        t = r.taste()
        lim = t["distance_limit_km"]
        check(st == 200 and lim is not None and 3 <= lim < far[0]["d"], f"'Too far' at {far[0]['d']:.1f} km sets a limit of {lim} km")
        items = r.results()
        avoided = set(delivery) | set(delivery_jobs)

        def demoted(c) -> bool:
            return c["id"] in avoided or (c["work_mode"] != "remote" and c["distance_km"] is not None and c["distance_km"] > lim)

        dem = [i for i, c in enumerate(items) if demoted(c)]
        keep = [i for i, c in enumerate(items) if not demoted(c)]
        check(not dem or not keep or max(keep) < min(dem),
              f"on-site posts beyond {lim} km and delivery posts come after all the others ({len(dem)} demoted of {len(items)})")
        check(any(i["id"] == "distance_limit" for i in t["avoids"]), "the limit is listed and can be removed")
    from app.taste import PostEvents, build_model

    now = datetime.now(timezone.utc)
    near = build_model([PostEvents(features={"dist": {"0_3"}}, actions={"hidden": now}, hidden_reason="too_far", distance_km=2.0)], now=now)
    check(near["dist_limit"] == 3.0, f"the limit never goes below 3 km ({near['dist_limit']})")

    low = await r.db.fetch(
        """SELECT id::text, salary_max_paise FROM vyapar_opportunities.opportunities
            WHERE state = 'active' AND type = 'employment' AND salary_max_paise BETWEEN 800000 AND 1400000
              AND (deadline IS NULL OR deadline >= now()) AND poster_id NOT LIKE 'm_check_%' ORDER BY id LIMIT 1""")
    if low:
        st, _ = r.call("POST", f"/v1/opportunities/{low[0]['id']}/not-interested", {"reason": "value_too_low"})
        t = r.taste()
        check(st == 200 and (t["pay_floor_paise"] or 0) > low[0]["salary_max_paise"], f"'Pay too low' raises the pay floor ({t['pay_floor_paise']})")
        from app.services.feed import _opportunity_signals
        from app.taste import Taste

        row = await r.db.fetchrow("SELECT * FROM vyapar_opportunities.opportunities WHERE id = $1::uuid", r.shop_job)
        member = {"capabilities": ["electrical"], "taste": Taste(await r.model())}
        check(_opportunity_signals(row, member, 2.0).value_fit == 1.0, "a job paying above the floor gets value_fit 1")


async def section_exploration_rows_why(r: Run) -> None:
    print("\n== Exploration, rows, Why this? ==")
    items = r.results()
    explore = [i for i, c in enumerate(items) if c["relevance_reason"] == "explore"]
    check(explore and all((i + 1) % 8 == 0 for i in explore) and len(explore) <= len(items) // 8,
          f"about 1 slot in 8 is 'something new near your skills' (slots {[i + 1 for i in explore]} of {len(items)})")
    again = [c["id"] for c in r.results()]
    check([c["id"] for c in items] == again, "the same order on a repeat call (seeded per member per day)")
    if explore:
        st, why = r.call("GET", f"/v1/opportunities/{items[explore[0]]['id']}/why")
        check(st == 200 and why["signals"][0] == "explore", f"Why this? on an explore post says so ({why.get('signals')})")
    tasted = [c for c in items if c["relevance_reason"].startswith("taste_fit")]
    st, why = r.call("GET", f"/v1/opportunities/{r.ac[0]}/why")
    check(st == 200 and any(s.startswith("taste_fit") for s in why["signals"]) or bool(tasted),
          f"taste reasons appear on cards or Why this? ({why.get('signals')}, {len(tasted)} cards)")
    rows = r.rows()
    keys = [x["key"] for x in rows["rows"]]
    check(keys and keys[0] == "for_you" and len(keys) <= 6, f"For you first, at most 6 rows ({keys})")
    check(any(k.startswith("taste_") for k in keys), f"a personal taste row is shown ({[x['title'] for x in rows['rows']]})")
    fy = next(x for x in rows["rows"] if x["key"] == "for_you")
    check(sum(1 for c in fy["items"] if c["relevance_reason"] == "explore") <= 1, "For you carries at most one explore card")


async def section_control(r: Run) -> None:
    print("\n== getMyTaste in three languages, remove, export, reset ==")
    t = r.taste()
    check(t["summary_text"].startswith("You often apply to: Electrical") and "Usually" in t["summary_text"],
          f"English summary ({t['summary_text']})")
    hi, te = r.taste("hi"), r.taste("te")
    check(has_script(hi["summary_text"], "ऀ", "ॿ") and has_script(te["summary_text"], "ఀ", "౿"),
          f"Hindi and Telugu summaries ({hi['summary_text'][:50]} / {te['summary_text'][:50]})")
    st, t2 = r.call("PATCH", "/v1/me/taste", {"remove": "skill:delivery"})
    check(st == 200 and not any(i["id"] == "skill:delivery" for i in t2["avoids"]) and "Delivery" not in t2["summary_text"],
          "removeMyTasteItem lifts 'Not my skill' for Delivery")
    st, _ = r.call("PATCH", "/v1/me/taste", {"remove": "skill:no_such_skill"})
    check(st == 404, f"removing an unknown item is 404 ({st})")
    st, exp = r.call("POST", "/v1/privacy/export")
    check(st == 201 and exp["document"]["taste"]["stored"] and exp["document"]["taste"]["model"]["n"] >= 5,
          "the data export includes the learned taste")
    await r.db.execute("DELETE FROM vyapar_privacy.data_requests WHERE member_id = $1", r.me)

    print("\n== RLS: no operator reads or writes someone else's taste ==")
    app = await asyncpg.connect(app_dsn())
    try:
        async with app.transaction():
            await app.execute("SELECT set_config('vyapar.authz_context', $1, true)", OPERATOR)
            seen = await app.fetchval("SELECT count(*) FROM vyapar_privacy.member_taste WHERE member_id = $1", r.me)
            upd = await app.execute("UPDATE vyapar_privacy.member_taste SET model = '{}' WHERE member_id = $1", r.me)
            try:
                await app.fetchval("SELECT vyapar_privacy.personalisation_allowed($1)", r.me)
                fn_refused = False
            except asyncpg.PostgresError:
                fn_refused = True
        check(seen == 0 and upd == "UPDATE 0", f"an operator sees 0 rows and updates 0 ({seen}, {upd})")
        check(fn_refused, "and the definer reads refuse another member's id")
        async with app.transaction():
            await app.execute("SELECT set_config('vyapar.authz_context', $1, true)", r.me)
            own = await app.fetchval("SELECT count(*) FROM vyapar_privacy.member_taste WHERE member_id = $1", r.me)
        check(own == 1, "the member sees their own row")
    finally:
        await app.close()

    st, t3 = r.call("DELETE", "/v1/me/taste")
    check(st == 200 and t3["confidence"] == 0 and t3["actions_counted"] == 0, "resetMyTaste forgets everything")
    items = r.results()
    check(not any(c["relevance_reason"].startswith("taste") or c["relevance_reason"] == "explore" for c in items),
          "after a reset the ranking is back to the cold-start behaviour")


async def section_privacy_and_profession(r: Run) -> None:
    print("\n== Privacy switch ==")
    st, _ = r.call("POST", f"/v1/opportunities/{r.ac[0]}/save")
    check(r.taste()["confidence"] > 0, "learning again after the reset")
    st, ps = r.call("PATCH", "/v1/privacy", {"personalised_recommendations": False})
    t = r.taste()
    check(st == 200 and ps["personalised_recommendations"] is False and not t["enabled"] and t["confidence"] == 0,
          f"switch off: nothing used ({t['summary_text']})")
    check((await r.model()) == {}, "and the stored taste is emptied")
    r.call("POST", f"/v1/opportunities/{r.plumbing[0]}/save")
    check(not any(c["relevance_reason"].startswith("taste") for c in r.results()), "no taste reasons while it is off")
    r.call("PATCH", "/v1/privacy", {"personalised_recommendations": True})
    t = r.taste()
    check(t["enabled"] and t["confidence"] == 0, f"switched back on: what was saved while off is not learned ({t['actions_counted']})")
    r.call("POST", "/v1/privacy/withdraw-consent", {"field": "behavioral_analytics"})
    check(not r.taste()["enabled"], "turning off usage analytics stops learning too")
    r.call("PATCH", "/v1/privacy", {"behavioral_analytics": True})
    await r.db.execute("DELETE FROM vyapar_privacy.data_requests WHERE member_id = $1", r.me)

    print("\n== Profession rules win: an advocate stays neutral ==")
    kavita = await r.db.fetchval("SELECT id::text FROM vyapar_listings.listings WHERE owner_id = $1 AND state = 'active_verified'", KAVITA)
    if kavita:
        r.call("POST", f"/v1/listings/{kavita}/save")
        r.call("GET", f"/v1/listings/{kavita}")
        st, res = r.call("GET", "/v1/listings/search?q=advocate")
        mine = [x for x in res.get("results", []) if x["listing"]["id"] == kavita]
        check(st == 200 and mine and mine[0]["relevance_reason"] == "matchesFilters",
              f"after saving and opening her profile, Kavita's result is still neutral ({mine[0]['relevance_reason'] if mine else None})")
        from app.services.discovery import _listing_signals
        from app.taste import Taste

        t = Taste({"w": {"lskill:legal": 3.0}, "ln": 10})
        row = await r.db.fetchrow("SELECT * FROM vyapar_listings.listings WHERE id = $1::uuid", kavita)
        check(_listing_signals(row, None, 1.0, taste=t).taste_fit > 0, "(for a non-restricted profession the taste term is live)")

    print("\n== Account deletion deletes the taste ==")
    r.call("POST", f"/v1/opportunities/{r.ac[0]}/more-like-this")
    before = await r.db.fetchval("SELECT count(*) FROM vyapar_privacy.member_taste WHERE member_id = $1", r.me)
    st, res = r.call("POST", "/v1/privacy/delete")
    after = await r.db.fetchval("SELECT count(*) FROM vyapar_privacy.member_taste WHERE member_id = $1", r.me)
    check(before == 1 and st in (200, 201) and after == 0, f"deleted with the account ({before} -> {after}, {st} {res.get('state')})")


# ---------------------------------------------------------------------------
async def main(api_base: str) -> int:
    api = Api(api_base)
    db = await asyncpg.connect(owner_dsn())
    r = Run(api, db)
    r.started_at = await db.fetchval("SELECT now()")
    counters = {(x["rate_limit_key"], x["window_start"]): x["hit_count"] for x in await db.fetch(
        "SELECT * FROM vyapar_platform.rate_limit_counter WHERE rate_limit_key LIKE ANY(ARRAY['enquiry:%','listing_search:%'])")}
    views_before = {(x["member_id"], str(x["listing_id"])) for x in await db.fetch("SELECT * FROM vyapar_listings.member_listing")}
    r.views_before = views_before
    try:
        for section in (section_setup_and_cold_start, section_learning, section_exploration_rows_why, section_negatives,
                        section_control, section_privacy_and_profession):
            try:
                await section(r)
            except Exception as exc:
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
    db, started = r.db, r.started_at
    members = [r.me, r.shop]
    r.opps.update(x["id"] for x in await db.fetch("SELECT id::text FROM vyapar_opportunities.opportunities WHERE poster_id = ANY($1::text[])", members))
    r.enquiries.update(x["id"] for x in await db.fetch(
        "SELECT id::text FROM vyapar_enquiries.enquiries WHERE sender_id = ANY($1::text[]) OR provider_id = ANY($1::text[])", members))
    ids = sorted(set(r.opps) | r.enquiries | set(members))
    patterns = [f"%{i}%" for i in ids]
    async with db.transaction():
        await db.execute("""DELETE FROM vyapar_integration.notifications WHERE created_at >= $1
                             AND (member_id = ANY($3::text[]) OR link LIKE ANY($2) OR params::text LIKE ANY($2) OR idempotency_key LIKE ANY($2))""",
                         started, patterns, members)
        await db.execute("DELETE FROM vyapar_integration.webhook_deliveries WHERE created_at >= $1 AND payload::text LIKE ANY($2)", started, patterns)
        for table in ("vyapar_enquiries.outbox_event", "vyapar_opportunities.outbox_event", "vyapar_reviews.outbox_event",
                      "vyapar_listings.outbox_event", "vyapar_commercial.outbox_event"):
            await db.execute(f"DELETE FROM {table} WHERE created_at >= $1 AND payload::text LIKE ANY($2)", started, patterns)
        await db.execute("DELETE FROM vyapar_integration.audit_events WHERE at >= $1 AND (object_id LIKE ANY($2) OR details::text LIKE ANY($2) OR actor_id = ANY($3::text[]))",
                         started, patterns, members)
        await db.execute("DELETE FROM vyapar_reviews.review_invites WHERE interaction_id::text = ANY($1::text[])", list(r.enquiries))
        await db.execute("DELETE FROM vyapar_enquiries.enquiries WHERE id::text = ANY($1::text[])", list(r.enquiries))
        await db.execute("DELETE FROM vyapar_opportunities.member_opportunity WHERE member_id = ANY($1::text[]) OR opportunity_id::text = ANY($2::text[])",
                         members, list(r.opps))
        await db.execute("DELETE FROM vyapar_commercial.impressions WHERE at >= $1 AND (target_id::text = ANY($2::text[]) OR member_id = ANY($3::text[]))",
                         started, list(r.opps), members)
        from app.events import pseudonymize

        await db.execute("DELETE FROM vyapar_analytics.analytics_events WHERE at >= $1 AND (object_id = ANY($2::text[]) OR member_pseudo = ANY($3::text[]))",
                         started, ids, [pseudonymize(m) for m in members])
        await db.execute("DELETE FROM vyapar_opportunities.opportunities WHERE id::text = ANY($1::text[])", list(r.opps))
        await db.execute("DELETE FROM vyapar_listings.member_listing WHERE member_id = ANY($1::text[])", members)
        for table in ("vyapar_privacy.member_taste", "vyapar_privacy.privacy_settings", "vyapar_privacy.acceptances",
                      "vyapar_privacy.data_requests", "vyapar_platform.idempotency_key"):
            await db.execute(f"DELETE FROM {table} WHERE member_id = ANY($1::text[])", members)
        await db.execute("DELETE FROM vyapar_listings.listings WHERE owner_id = ANY($1::text[])", members)
        await db.execute("DELETE FROM vyapar_identity.members WHERE id = ANY($1::text[])", members)
        for x in await db.fetch("SELECT * FROM vyapar_platform.rate_limit_counter WHERE rate_limit_key LIKE ANY(ARRAY['enquiry:%','listing_search:%','notify:%'])"):
            key = (x["rate_limit_key"], x["window_start"])
            if key in counters:
                await db.execute("UPDATE vyapar_platform.rate_limit_counter SET hit_count = $3 WHERE rate_limit_key = $1 AND window_start = $2",
                                 key[0], key[1], counters[key])
            elif any(m in x["rate_limit_key"] for m in members):
                await db.execute("DELETE FROM vyapar_platform.rate_limit_counter WHERE rate_limit_key = $1 AND window_start = $2", key[0], key[1])
        # the shop's poster applicants view and seeded posters' counts recompute on the next read
        await db.execute("UPDATE vyapar_identity.members SET badges_computed_at = NULL WHERE badges_computed_at IS NOT NULL AND id IN "
                         "(SELECT poster_id FROM vyapar_opportunities.opportunities WHERE state = 'active')")
    leftovers = []
    for t in await db.fetch("SELECT schemaname, tablename FROM pg_tables WHERE schemaname LIKE 'vyapar\\_%' ORDER BY 1, 2"):
        count = await db.fetchval(f'SELECT count(*) FROM "{t["schemaname"]}"."{t["tablename"]}" x WHERE x::text LIKE ANY($1)', patterns)
        if count:
            leftovers.append(f"{t['schemaname']}.{t['tablename']}={count}")
    check(not leftovers, f"no leftover rows mention an id this run created ({', '.join(leftovers) or 'clean'})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--api", default=os.environ.get("VYAPAR_CHECK_API_BASE"))
    parser.add_argument("--cleanup-only", metavar="TAG", help="Only remove what an interrupted run with this tag created")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.cleanup_only:
        async def _only(tag: str) -> int:
            db = await asyncpg.connect(owner_dsn())
            r = Run(Api("http://unused"), db, tag)
            r.started_at = await db.fetchval("SELECT min(created_at) FROM vyapar_identity.members WHERE id = ANY($1::text[])", [r.me, r.shop])                 or await db.fetchval("SELECT now() - interval '1 day'")
            await cleanup(r, {})
            await db.close()
            return 0 if all(ok for ok, _ in RESULTS) else 1
        sys.exit(asyncio.run(_only(args.cleanup_only)))
    if not args.api:
        parser.error("--api (or VYAPAR_CHECK_API_BASE) is required")
    sys.exit(asyncio.run(main(args.api)))

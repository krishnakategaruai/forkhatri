"""Offline evaluation of Vyapar's learned taste: is the ranking better, not just different?

Replays the seeded marketplace (the live posts seed_marketplace.py created,
read-only) for five realistic personas, each with a synthetic but plausible
history of actions over many sessions:

  electrician  lives in Dilsukhnagar, lists "Electrical" only; applies to
               electrical and AC-repair work near home, saves the odd plumbing
               job, marks delivery posts "Not my skill" and a far job "Too far"
  ca           a CA in Begumpet who lists "Accounting"; saves and applies to GST
               filing, tax and accountant work, marks a low-paid one "Pay too low"
  fresher      no skills listed, Ameerpet; applies to delivery, telecalling,
               field sales and data entry, marks cooking / mason posts
               "Not my kind of work"
  tailor       lists "Tailoring", Charminar; applies to tailoring and saree-shop
               counter sales
  driver       lists "Driver", Miyapur; applies to driver and delivery jobs

Each history is ordered in time; the last 20% of each persona's positive
actions (applied / saved) are held out. The ranking under test orders every
post the persona could see (the same hard filters as Discover: live, not their
own, on-site posts within their radius) minus what they already acted on in
the first 80%. Reported per persona and overall, averaged over 40 random
timelines each: precision@5, recall@10, nDCG@10 for

  (a) today's ranking without taste (cold start: exactly the old ranking),
  (b) with taste (taste_fit, value_fit from "Pay too low", hard negatives),
  (c) with taste and exploration (1 slot in 8), which is what Discover ships.

Fairness check: the same histories and candidates are replayed with the
posters' name, community, gender and religion fields flipped in the fixture;
the learned models and every score must be byte-identical.

The ranking code under test is the production code: app.taste (model),
app.services.feed._opportunity_signals / relevance_order / with_exploration.
Nothing is written to the database.

Usage (from vyapar-service/):
    .venv/Scripts/python scripts/eval_recommendations.py [--timelines 40] [--seed 7]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import math
import random
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

import asyncpg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.check_trust_pack import owner_dsn  # noqa: E402  (same .env reader every check script uses)

NOW = datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
@dataclass
class Persona:
    key: str
    caps: list[str]
    lat: float
    lng: float
    radius_km: int
    locality: str
    likes: Callable[[dict], float]            # 0..1: how much this person wants this post (latent, never shown to the ranker)
    negatives: list[tuple[Callable[[dict], bool], str]]  # (which posts, "Not interested" reason)


def skills(row) -> set[str]:
    return set(row["required_capabilities"] or [])


def near(row, km: float) -> bool:
    return row["distance_km"] is not None and row["distance_km"] <= km


PERSONAS = [
    Persona("electrician", ["electrical"], 17.3688, 78.5247, 15, "Dilsukhnagar",
            likes=lambda r: (1.0 if skills(r) & {"electrical", "ac_technician"} else 0.35 if skills(r) & {"plumbing", "tile_fitter"} else 0.0)
            * (1.0 if r["distance_km"] is None or r["distance_km"] <= 10 else 0.5),
            negatives=[(lambda r: bool(skills(r) & {"delivery"}), "not_my_capability"),
                       (lambda r: bool(skills(r) & {"electrical"}) and r["distance_km"] is not None and r["distance_km"] > 11, "too_far")]),
    Persona("ca", ["accounting"], 17.4447, 78.4676, 15, "Begumpet",
            likes=lambda r: 1.0 if skills(r) & {"gst_filing", "tax", "accountant", "accounting", "bookkeeping"} else
            (0.3 if skills(r) & {"data_entry", "office_assistant"} else 0.0),
            negatives=[(lambda r: bool(skills(r) & {"delivery", "driver"}), "not_my_capability"),
                       (lambda r: r["type"] == "employment" and 0 < (r["salary_max_paise"] or 0) < 1_500_000, "value_too_low")]),
    Persona("fresher", [], 17.4375, 78.4483, 15, "Ameerpet",
            likes=lambda r: 1.0 if skills(r) & {"delivery", "telecaller", "field_sales", "data_entry"} else
            (0.4 if skills(r) & {"packer", "sales", "counter_sales", "office_assistant"} else 0.0),
            negatives=[(lambda r: bool(skills(r) & {"cook", "mason", "labourer"}), "wrong_type")]),
    Persona("tailor", ["tailoring"], 17.3616, 78.4747, 20, "Charminar",
            likes=lambda r: 1.0 if skills(r) & {"tailoring", "counter_sales", "textiles"} else 0.0,
            negatives=[(lambda r: bool(skills(r) & {"delivery"}), "not_my_capability")]),
    Persona("driver", ["driver"], 17.4960, 78.3570, 20, "Miyapur",
            likes=lambda r: 1.0 if skills(r) & {"driver", "delivery"} else (0.3 if skills(r) & {"packer"} else 0.0),
            negatives=[(lambda r: bool(skills(r) & {"react", "python", "software", "accountant"}), "not_my_capability")]),
]


def haversine(lat1, lng1, lat2, lng2):
    from app.services.taste import _haversine

    return _haversine(lat1, lng1, lat2, lng2)


# ---------------------------------------------------------------------------
def eligible(rows: list[dict], p: Persona) -> list[dict]:
    """The Discover hard filters for this persona (live, not own, on-site within radius)."""
    out = []
    for r in rows:
        r = dict(r)
        r["distance_km"] = haversine(p.lat, p.lng, r["lat"], r["lng"])
        if r["work_mode"] == "on_site" and r["distance_km"] is not None and r["distance_km"] > p.radius_km:
            continue
        out.append(r)
    return out


def timeline(pool: list[dict], p: Persona, rng: random.Random):
    """A plausible history: over ~60 days the person opens posts they want,
    saves some, applies to most of what they really want, and marks what they
    don't want as Not interested. Returns [(when, row, action, reason)]."""
    events = []
    wanted = [r for r in pool if p.likes(r) > 0]
    rng.shuffle(wanted)
    t = NOW - timedelta(days=60)
    for r in wanted:
        t += timedelta(hours=rng.uniform(10, 60))
        lk = p.likes(r)
        roll = rng.random()
        if roll < 0.75 * lk:
            events.append((t, r, "applied", None))
        elif roll < 0.95 * lk:
            events.append((t, r, "saved", None))
        else:
            events.append((t, r, "viewed", None))
    unwanted = [(r, reason) for r in pool for pred, reason in p.negatives if pred(r) and p.likes(r) < 0.5]
    rng.shuffle(unwanted)
    seen = set()
    for r, reason in unwanted[: max(2, len(unwanted) // 2)]:
        if r["id"] in seen:
            continue
        seen.add(r["id"])
        events.append((NOW - timedelta(days=60) + timedelta(hours=rng.uniform(0, 1400)), r, "hidden", reason))
    events.sort(key=lambda e: e[0])
    return events


def split(events):
    positives = [e for e in events if e[2] in ("applied", "saved")]
    n_test = max(1, round(0.2 * len(positives)))
    test = positives[-n_test:]
    cutoff = test[0][0]
    train = [e for e in events if e[0] < cutoff]
    return train, {e[1]["id"] for e in test}


def model_from(train, p: Persona) -> dict:
    from app.taste import PostEvents, build_model, monthly_top, post_features, project_top

    by_post: dict = {}
    for when, r, action, reason in train:
        ev = by_post.get(r["id"])
        if ev is None:
            ev = by_post[r["id"]] = PostEvents(features=post_features(r, r["distance_km"]), actions={}, distance_km=r["distance_km"],
                                               monthly=monthly_top(r), project=project_top(r))
        ev.actions[action] = when
        if reason:
            ev.hidden_reason = reason
    cutoff = max((e[0] for e in train), default=NOW)
    return build_model(list(by_post.values()), now=cutoff + timedelta(hours=12))


def member_of(p: Persona, model: dict | None) -> dict:
    from app.taste import Taste, categories_of

    return {"id": f"eval_{p.key}", "capabilities": p.caps, "categories": sorted(categories_of(p.caps)), "lat": p.lat, "lng": p.lng,
            "radius_km": p.radius_km, "locality": p.locality, "taste": Taste(model) if model is not None else Taste.empty()}


def rank(candidates: list[dict], member: dict, explore: bool = False) -> list[dict]:
    from app.services.feed import _scored, explore_pool, relevance_order, with_exploration

    scored = [(*_scored(r, member, r["distance_km"]), r) for r in candidates]
    ordered = relevance_order(scored, member)
    if explore:
        ordered, _ = with_exploration(ordered, explore_pool(ordered, member, day=date(2026, 10, 1)))
    return ordered


def metrics(ordered: list[dict], relevant: set) -> tuple[float, float, float]:
    ids = [r["id"] for r in ordered]
    p5 = sum(1 for i in ids[:5] if i in relevant) / 5
    r10 = sum(1 for i in ids[:10] if i in relevant) / len(relevant)
    dcg = sum(1 / math.log2(k + 2) for k, i in enumerate(ids[:10]) if i in relevant)
    idcg = sum(1 / math.log2(k + 2) for k in range(min(10, len(relevant))))
    return p5, r10, dcg / idcg


FLIP = {"poster_name": ("Ramesh Naidu", "Fatima Begum"), "poster_community": ("Khatri", "Other"),
        "poster_gender": ("male", "female"), "poster_religion": ("Hindu", "Muslim")}


def with_person_fields(rows: list[dict], flipped: bool) -> list[dict]:
    return [{**r, **{k: v[1 if flipped else 0] for k, v in FLIP.items()}} for r in rows]


# ---------------------------------------------------------------------------
async def main(timelines: int, seed: int) -> int:
    from app.taxonomy_cache import refresh_taxonomy_cache

    pool = await asyncpg.create_pool(owner_dsn(), min_size=1, max_size=2)
    await refresh_taxonomy_cache(pool)
    async with pool.acquire() as conn:
        rows = [dict(r) for r in await conn.fetch(
            """SELECT * FROM vyapar_opportunities.opportunities
                WHERE state = 'active' AND NOT distribution_limited AND (deadline IS NULL OR deadline >= now())""")]
    await pool.close()
    print(f"Marketplace: {len(rows)} live posts (read-only)\n")

    rng = random.Random(seed)
    table: dict[str, dict[str, list[tuple[float, float, float]]]] = {}
    fairness_ok, fairness_checked = True, 0
    for p in PERSONAS:
        pool_rows = eligible(rows, p)
        table[p.key] = {"a": [], "b": [], "c": []}
        for t in range(timelines):
            events = timeline(pool_rows, p, rng)
            if sum(1 for e in events if e[2] in ("applied", "saved")) < 3:
                continue
            train, relevant = split(events)
            touched = {e[1]["id"] for e in train}
            candidates = [r for r in pool_rows if r["id"] not in touched]
            relevant &= {r["id"] for r in candidates}
            if not relevant:
                continue
            model = model_from(train, p)
            table[p.key]["a"].append(metrics(rank(candidates, member_of(p, None)), relevant))
            table[p.key]["b"].append(metrics(rank(candidates, member_of(p, model)), relevant))
            table[p.key]["c"].append(metrics(rank(candidates, member_of(p, model), explore=True), relevant))
            if t < 5:  # fairness: flip every person field on history and candidates
                from app.services.feed import _opportunity_signals

                flipped_train = [(w, with_person_fields([r], True)[0], a, rs) for w, r, a, rs in train]
                plain_train = [(w, with_person_fields([r], False)[0], a, rs) for w, r, a, rs in train]
                m1, m2 = model_from(plain_train, p), model_from(flipped_train, p)
                same_model = json.dumps(m1, sort_keys=True) == json.dumps(m2, sort_keys=True)
                c1, c2 = with_person_fields(candidates, False), with_person_fields(candidates, True)
                s1 = [_opportunity_signals(r, member_of(p, m1), r["distance_km"]).model_dump() for r in c1]
                s2 = [_opportunity_signals(r, member_of(p, m2), r["distance_km"]).model_dump() for r in c2]
                fairness_checked += len(c1)
                fairness_ok &= same_model and s1 == s2

    def avg(xs, i):
        return sum(x[i] for x in xs) / len(xs) if xs else float("nan")

    header = f"{'persona':<12} {'n':>3} | {'P@5 a':>6} {'P@5 b':>6} {'P@5 c':>6} | {'R@10 a':>6} {'R@10 b':>6} {'R@10 c':>6} | {'nDCG a':>6} {'nDCG b':>6} {'nDCG c':>6}"
    print("a = today's ranking (no taste) · b = with taste · c = with taste + exploration (ships)\n")
    print(header)
    print("-" * len(header))
    allx = {"a": [], "b": [], "c": []}
    for key, cols in table.items():
        for k in allx:
            allx[k] += cols[k]
        print(f"{key:<12} {len(cols['a']):>3} | " + " ".join(f"{avg(cols[k], 0):6.3f}" for k in "abc") + " | "
              + " ".join(f"{avg(cols[k], 1):6.3f}" for k in "abc") + " | " + " ".join(f"{avg(cols[k], 2):6.3f}" for k in "abc"))
    print("-" * len(header))
    print(f"{'all':<12} {len(allx['a']):>3} | " + " ".join(f"{avg(allx[k], 0):6.3f}" for k in "abc") + " | "
          + " ".join(f"{avg(allx[k], 1):6.3f}" for k in "abc") + " | " + " ".join(f"{avg(allx[k], 2):6.3f}" for k in "abc"))
    print(f"\nFairness: flipping poster name / community / gender / religion on {fairness_checked} scored posts "
          f"(and on every post in the histories) changes {'nothing' if fairness_ok else 'SOMETHING'}: "
          f"{'PASS' if fairness_ok else 'FAIL'}")
    return 0 if fairness_ok else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--timelines", type=int, default=40)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(asyncio.run(main(args.timelines, args.seed)))

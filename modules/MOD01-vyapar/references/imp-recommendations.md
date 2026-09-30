# Recommendations that learn (2026-09-30)

Vyapar's ranking now learns from each member's **own** actions. It stays inside the
FR19/SP019 fairness rules: it learns only over **content** attributes of posts and
profiles, never over who posted them, and never from other members' behaviour.
A member with no history ranks exactly as before.

## What was built

| Piece | Where |
|---|---|
| Learned taste model (pure, no I/O) | `vyapar-service/app/taste.py` |
| Load / refresh / show / control / export / delete | `vyapar-service/app/services/taste.py` |
| API: getMyTaste, resetMyTaste, removeMyTasteItem, moreLikeThis | `vyapar-service/app/routers/taste.py` |
| New allow-listed signal `taste_fit` (weight 2.0) | `vyapar-service/app/ranking.py` |
| Feed, results, rows, "Why this?", exploration, hard negatives | `vyapar-service/app/services/feed.py` |
| Alerts (strong match, digest) rank with taste | `vyapar-service/app/services/notifications.py` |
| Light taste term for profile search and similar profiles | `app/services/discovery.py`, `app/profile_cards.py` |
| Privacy switch, export, deletion | `app/services/privacy.py` |
| Table, column, switch, definer reads | `07a-db-implementation/migrations/030-member-taste.sql` (also in `schema.sql`) |
| Checks (67, real API, full cleanup) | `vyapar-service/scripts/check_taste.py` |
| Offline evaluation | `vyapar-service/scripts/eval_recommendations.py` |
| Localized phrases (en/hi/te) | server `app/i18n/locales/*/ranking.json`, `discover.json`; web `locales/*/ranking.json`, `explore.json`, `app/components/opportunity/labels.ts` |

## Design

### What it learns from (the member's own actions only)

| Action | Weight | "Why this?" source |
|---|---|---|
| Hired (poster set stage `hired`) | +5 | applied |
| Marked done (`completed_at`) | +4 | applied |
| Applied / sent a proposal or quote (any enquiry on a post) | +3 | applied |
| Contacted / asked a price on a profile | +3 | (profiles) |
| More like this | +3 | more_like_this |
| Saved | +2 | saved |
| Shared, opened the source | +1.5 | saved / other |
| Opened the detail | +0.5 (not a "meaningful" action) | other |
| Withdrew an application | −1.5 | — |
| Not interested | −3, on the groups its reason speaks about | — |

Not-interested reasons map to feature groups: *Not my skill* (`not_my_capability`) → skill,
category, trade words; *Too far* → distance band; *Pay too low* (`value_too_low`) → pay band;
*Not my kind of work* (`wrong_type`) → kind of post, work mode, shift, experience;
*Wrong timing* → shift; *Already filled* (`already_found`) → nothing; plain *Not interested* →
every group at 40%. A hidden post overrides everything else done to it.

Each action decays with a **30-day half-life**; actions older than a year are ignored. Per
post the strongest positive action counts fully and each further one adds 25% of its weight.

### What it learns over (content only)

`skill`, `cat` (the skill's trade category), `type` (job / project / local service ...),
`mode` (work mode), `dist` (distance band from the member's home: 0–3, 3–8, 8–15, 15–30,
30+ km), `pay` (monthly bands for jobs, budget bands for projects), `shift`, `exp`
(fresher / up to 2 years / 3+ years), and `word` — trade words in the title, folded with
`text_fold` (en/hi/te). A title word is learned **only** when it is trade vocabulary (a
skill's names and aliases in the three languages, plus a short list of work words): free
title words can be a business or family name, and a surname can stand for a community.
Profiles: `lskill`, `lcat`, `lkind`, `ldist` (skills only when the owner shows them).

`app/taste.py` reads only the keys in `CONTENT_KEYS`; the definer functions of migration
030 return no poster id, name or any person column. That structural absence is the
fairness control, and the evaluation proves it (flip test below).

### From model to ranking

`taste_fit` = weighted overlap (per group: skill .30, category .15, words .15, kind .10,
pay .10, distance .08, mode .05, shift .04, experience .03) between the post's features and
the learned weights, normalised per group, negatives pulling it down, clamped to 0..1,
**times confidence**. Confidence = meaningful actions / 10 (capped at 1). The signal's
weight is 2.0, so its effective weight ramps from 0 (no history — scores are bit-for-bit
the old ones) to 2.0 after 10 actions. `explain()` and `top_signal_keys()` read it like any
other signal; a card whose top signal is `taste_fit` gets the phrase for where the match
came from: `taste_fit_applied` "like jobs you applied to", `taste_fit_saved` "similar to
posts you saved", `taste_fit` "matches what you usually look for".

### Hard negatives (soft filters, reversible)

- **Not my skill** → that skill is *avoided*: a post whose skills are all avoided (or, with
  no skills, whose title names the trade) goes to the end of the relevance order, out of
  alerts, out of taste rows. It lifts itself if the member later applies to that trade, or
  through `PATCH /v1/me/taste`.
- **Too far** → a distance limit of 85% of the nearest "too far" post, never below 3 km,
  raised again by a later application farther away. On-site posts beyond it go to the end;
  Near you uses it as its radius.
- **Pay too low** → a pay floor 10% above the highest pay rejected (to the next ₹500),
  lowered by a later application below it. `value_fit` (previously always 0) is 1 at or
  above the floor, 0 below, 0.3 when pay is not stated; 0 when there is no floor.

Hard filters (radius, hidden, expired, own posts, distribution limits) are untouched: the
taste only reorders what already passed them.

### Exploration

Results (relevance order) and the For you row reserve **1 slot in 8** (slots 8, 16, ...) for
a relevant-but-unexplored post: paid work whose skill is in the same trade family as the
member's skills or liked skills, but which the member has neither listed nor acted on, and
which no hard negative demotes. The pick is seeded per member per day, so the page is stable
within a day. Its card reason (and "Why this?") is `explore`: "something new near your skills".

### Rows

After For you, when confidence ≥ 0.5 (about 5 actions): **"Because you applied to
<trade>"** (the member's top applied trades, those outside their listed skills first, the
first with a post left to show) and **"More like what you saved"** (paid work sharing a skill
with what they saved or shared). Both are personal rows (shown with 1 card), obey
one-post-per-row and the 6-row cap.

### Alerts

The strong-match pass and the digest score with the full score (taste and pay floor
included). Posts the member hid or demotes are never announced. Caps unchanged: ≤ 3 alerts
a day, each post once. The digest lists its posts best first.

### Businesses search and similar profiles

A light term: `taste_fit` for a profile from what the member saved, opened or contacted
(skills, category, kind, distance band). In search it lives inside the FR19 score, which
only orders after text relevance and distance, so it breaks ties. In similar / matching
profiles it is a coarse tie-breaker after skill and category overlap. Advocates and
architects (council rules) get no taste term: profession rules win.

### Refresh

`load_taste()` reads the member's actions through `member_taste_events()` /
`member_taste_listing_events()`, fingerprints them, and rebuilds only when the fingerprint
changed or the stored model is over an hour old. So every action (including an unsave or
an undo) is reflected on the member's very next read, without a hook in each write path.
The hourly loop (`run_taste_refresh_pass`) keeps stored models current for the alert passes.
A taste failure never breaks a feed (`taste_or_empty`, inside a savepoint).

### Privacy and RLS

- `vyapar_privacy.member_taste` (one row per member): RLS admits **only the member and the
  dispatcher** — operators are deliberately excluded, so no admin can read or write a
  member's taste (checked). The three definer functions refuse any id but your own unless
  the caller is the dispatcher.
- Switch: `privacy_settings.personalised_recommendations` (default on, in `GET/PATCH
  /v1/privacy`). Learning also stops when **Usage analytics** (`behavioral_analytics`) is off,
  because that switch promises nothing is recorded. Turning either off empties the model at
  once and moves the reset point, so actions taken while off are never learned later.
- Data export (`POST /v1/privacy/export`) includes `taste` (what the member sees and the
  stored model). Account deletion deletes the row.
- Admin diagnostics: `explain()` lists `taste_fit` with its value, weight and contribution.
  The listing diagnostic is viewer-independent, so it shows 0 there; opportunity scores stay
  "member relative" as before. No admin route writes taste.

### Fixes from the web end-to-end test (2026-10-01)

1. **Recent negative wins.** A "Not my skill" answer cancels every positive learned for that
   skill *before* it (a correction, not one vote among many); a later application counts
   again. A skill in avoids never gives a post a taste boost, never appears in likes or
   "You often apply to", and never gets a "Because you applied to <trade>" row.
2. **Trades, not words.** getMyTaste shows a learned title word only as the skill it names,
   by its taxonomy label in the member's language ("rider" -> "Delivery rider"); words that
   name no skill are not shown (they still count internally). One line per trade.
3. **"More like this" has its own source** `more_like_this`: the line "From posts you asked
   for more of: …" and the card phrase `taste_fit_more_like_this` ("like posts you asked for
   more of"), en/hi/te.

## Contract

### `GET /v1/me/taste` — getMyTaste

```json
{
  "enabled": true,
  "confidence": 0.8,
  "actions_counted": 8,
  "summary": [
    "You often apply to: Electrical work, AC technician",
    "You often save: Plumbing",
    "Usually within 8 km",
    "Usually ₹18,000+ a month",
    "Not interested in: Delivery rider"
  ],
  "summary_text": "You often apply to: Electrical work, AC technician · You often save: Plumbing · Usually within 8 km · Usually ₹18,000+ a month · Not interested in: Delivery rider",
  "likes": [
    {"id": "skill:electrical", "kind": "skill", "label": "Electrical work", "direction": "like", "source": "applied", "strength": 1.0},
    {"id": "type:employment", "kind": "post_type", "label": "Jobs", "direction": "like", "source": "applied", "strength": 1.0},
    {"id": "dist:3_8", "kind": "distance", "label": "3–8 km away", "direction": "like", "source": "applied", "strength": 0.8},
    {"id": "skill:ac_technician", "kind": "skill", "label": "AC technician", "direction": "like", "source": "more_like_this", "strength": 0.6}
  ],
  "avoids": [
    {"id": "skill:delivery", "kind": "skill", "label": "Delivery rider", "direction": "avoid", "source": null, "strength": 1.0},
    {"id": "distance_limit", "kind": "distance_limit", "label": "Nothing farther than 8 km", "direction": "avoid", "source": null, "strength": 1.0},
    {"id": "pay_floor", "kind": "pay_floor", "label": "Pay at least ₹15,500 a month", "direction": "avoid", "source": null, "strength": 1.0}
  ],
  "distance_limit_km": 7.7,
  "pay_floor_paise": 1550000,
  "usual_distance_km": 6.2,
  "usual_monthly_pay_paise": 1800000,
  "updated_at": "2026-10-01T06:12:40.114Z"
}
```

Language follows the request (`X-Vyapar-Language` / `Accept-Language`): Hindi "आप अक्सर इनमें
आवेदन करते हैं: …", Telugu "మీరు తరచుగా వీటికి అప్లై చేస్తారు: …". With the switch off:
`enabled: false`, `confidence: 0`, summary "Personalised recommendations are off. Nothing is
being learned."

### `DELETE /v1/me/taste` — resetMyTaste

Forgets everything; actions before now never count again. Returns the (empty) `TasteOut`.

### `PATCH /v1/me/taste` — removeMyTasteItem

```json
{ "remove": "skill:delivery" }
```

Returns the updated `TasteOut`. Actions before now no longer count for that item (removing
an avoided skill lifts its "Not my skill" filter; `distance_limit` / `pay_floor` drop the
"Too far" / "Pay too low" learning). Unknown id → `404` `taste_item_not_found`.

### `POST /v1/opportunities/{id}/more-like-this` — moreLikeThis

No body. A strong positive (+3); also un-hides the post if it was hidden. Returns the updated
`TasteOut`. Own post → `400` `own_post`; unknown post → `404` `opportunity_not_found`.

### Additive fields elsewhere

- `relevance_reason` / "Why this?" `signals` may now be `taste_fit`, `taste_fit_applied`,
  `taste_fit_saved`, `taste_fit_more_like_this` or `explore` (translated under `ranking:signal.*`).
- Rows: keys `taste_applied:<skill>` (title_key `becauseApplied`, `{trade}`) and
  `taste_saved` (title_key `moreLikeSaved`).
- `GET/PATCH /v1/privacy`: `personalised_recommendations: boolean`.
- Data export document: `taste: {stored, shown, model, reset_at, removed, updated_at}`.

## Evaluation

`scripts/eval_recommendations.py` replays the 120 live seeded posts for five personas with
synthetic but realistic histories (40 random timelines each, seed 7), holds out the last 20%
of each persona's positive actions and ranks everything they could see (Discover's hard
filters) minus what they already touched. *a* = today's ranking without taste; *b* = with
taste; *c* = with taste and exploration (what Discover ships).

| Persona | n | P@5 a | P@5 b | P@5 c | R@10 a | R@10 b | R@10 c | nDCG@10 a | nDCG@10 b | nDCG@10 c |
|---|---|---|---|---|---|---|---|---|---|---|
| Electrician, Dilsukhnagar (lists Electrical) | 22 | 0.191 | 0.191 | 0.191 | 0.955 | 0.955 | 0.955 | 0.955 | 0.955 | 0.955 |
| CA, Begumpet (lists Accounting, saves GST work) | 40 | 0.025 | 0.075 | 0.075 | 0.275 | 0.575 | 0.550 | 0.097 | 0.354 | 0.347 |
| Fresher, Ameerpet (no skills; delivery, telecalling) | 40 | 0.135 | 0.435 | 0.435 | 0.200 | 0.744 | 0.698 | 0.164 | 0.693 | 0.670 |
| Tailor, Charminar | 40 | 0.105 | 0.180 | 0.180 | 0.625 | 0.900 | 0.900 | 0.555 | 0.878 | 0.878 |
| Driver, Miyapur | 40 | 0.215 | 0.360 | 0.360 | 0.575 | 0.912 | 0.912 | 0.551 | 0.928 | 0.928 |
| **All** | 182 | **0.129** | **0.254** | **0.254** | **0.484** | **0.804** | **0.788** | **0.416** | **0.743** | **0.736** |

(Re-run on 2026-10-01 after the three web-test fixes below; the live marketplace had also
changed slightly since the first run, which moved the baseline too.)

Reading it: taste doubles precision@5 and lifts nDCG@10 from 0.42 to 0.74 overall. The
biggest gain is where listed skills say least about what the person wants (the fresher with
no skills, the CA whose GST work is a different skill from "Accounting"). The electrician
already ranks well on his listed skill, and taste neither helps nor hurts there (the held-out
set is 1–2 posts, so P@5 is capped near 0.2). Exploration costs 1–2 points of recall — the
price of one slot in eight going to something new.

**Fairness check: PASS.** The same histories and over 2,100 candidate scorings replayed with the
posters' name, community, gender and religion flipped in the fixture give byte-identical
learned models and signals.

## Checks

`scripts/check_taste.py` (67 checks, through the real API, two members who join through the
normal path, full cleanup and a sweep of every `vyapar_*` table): cold start identical to
personalisation-off (results, rows, reasons); each action type teaches with the right source
and order (hired > applied > saved > viewed); 30-day decay halves; "Not my skill", "Too far"
(≥ 3 km), "Pay too low" act at once; exploration at slots 8, 16 … and deterministic; "Why
this?" says explore / taste; For you first, ≤ 6 rows, a taste row appears; en/hi/te
summaries; remove / reset; export; privacy switch and usage analytics stop learning and
nothing done while off is learned later; an advocate stays neutral; operators can neither
read nor write taste; account deletion deletes it.

Run: `.venv/Scripts/python scripts/check_taste.py --api http://127.0.0.1:<port>`
(`--cleanup-only <tag>` removes what an interrupted run left).

## Not done here

- Web UI for the taste page ("What Vyapar has learned") and the privacy toggle: the API and
  translations for the card phrases exist; a parallel web session is adding the "More like
  this" / "Not interested" menu.
- Dwell time and return visits are not logged anywhere yet, so they are not learned.

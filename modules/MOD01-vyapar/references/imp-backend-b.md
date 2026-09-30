# IMP — Backend workstream B: contact control, seeker protection, count badges, service packages, discovery filters, MCP tools (2026-09-28)

**Scope.** Six features, all in the service layer behind thin routers, with typed models, `operation_id`s and stable error codes. There is one migration, `019-contact-trust-discovery.sql`. It has been applied to the dev DB and appended to `schema.sql` as section 14.

**Files owned or added:**
- `app/services/{contact,packages,saved_searches,hooks}.py`
- `app/routers/{contact,packages,saved_searches,badges}.py`
- `scripts/check_backend_b.py`

**Files edited:**
- services: `app/services/{feed,trust_safety,discovery,listings,notifications}.py`
- routers: `app/routers/{feed,trust_safety}.py`
- `app/reputation.py`, `app/profile_cards.py`, `app/config.py`, `app/main.py` (router registration only)
- `app/integrations/identity/scopes.py`
- the i18n catalogs, in en, hi and te
- `vyapar-mcp/`

**Not touched:** `services/opportunities.py`, `services/enquiries.py`, `first_run.py`, their routers, `payments`, `vyapar-web/`.

**Verification.**
- `vyapar-service/scripts/check_backend_b.py` passes **59/59**. It works as follows:
  - It starts its own uvicorn on a free port from 8091 and stops only its own process tree.
  - It runs with realistic personas. Anita Khatri is the CA firm. Suresh Kohli is the electrician. Sunita Kapoor is the caterer. Rahul and Gaurav are the reporters.
  - Afterwards it deletes every row it created and restores the preferences and rate-limit counters it touched. A post-run query confirmed that no test rows remain.
- `python -c "import app.main"` passes.
- The MCP server loads **59 tools**.

---

## Migration 019 (additive only)

| # | Change |
|---|---|
| 1 | `vyapar_identity.members` gains the contact preferences below, plus `badges jsonb` and `badges_computed_at`, the on-read badge cache. |
| 1 | `vyapar_listings.listings` gains the same preference columns as nullable overrides, where `NULL` means inherit from the member. |
| 1 | New `vyapar_enquiries.contact_attempts (enquiry_id, caller_id, callee_id, channel call\|whatsapp, at)`. RLS: both parties read it; only the caller writes. |
| 1 | New functions `contact_preferences_for(member)` and `contact_attempts_today(callee, channel, offset_min)`, both SECURITY DEFINER, minimal projection. |
| 2 | `reports.reason` CHECK gains `asked_for_money` (appended). `severity_for_reason('asked_for_money')` is `medium`, so one report never limits a post by itself. |
| 2 | New `apply_seeker_charge_reports(opportunity, threshold, texts)`. At 2 or more distinct reporters it pauses the post (`state_reason='seeker_charge_reports'`, distribution limited), raises the case to High and notifies the poster in their own language. |
| 3 | New functions `badge_inputs(ids[])`, `member_badges(ids[], max_age)` and `store_badges(id, jsonb)`. `store_badges` accepts only known keys. |
| 4 | New `vyapar_listings.listing_packages`, with `UNIQUE(listing_id, tier)`, so at most 3 per listing. RLS: visible if the listing is visible; only the owner writes. |
| 4 | `enquiries.package_id uuid` added. `sub_choice = 'request_package'` is documented; `sub_choice` has no CHECK, so every existing value is unchanged. |
| 5 | New `vyapar_opportunities.saved_searches (member_id, query, filters jsonb, alert, last_alerted_at)`. RLS: self access; the dispatcher may stamp `last_alerted_at`. |
| 6 | `access_tokens.scopes` CHECK gains `contracts:write` (appended). |

Contact preference columns added in change 1: `call_hours_start/end time`, `call_days text[]` (mon..sun; empty means every day), `max_calls_per_day int` (NULL means unlimited), `calls_from anyone|matching_only`, `whatsapp_ok`, `call_ok`.

New config values, with defaults and no hardcoded hosts:
- `CONTACT_TIMEZONE_OFFSET_MINUTES=330` (IST)
- `CONTACT_DEFAULT_COUNTRY_CODE=91`
- `BADGES_CACHE_SECONDS=86400`
- `SEEKER_CHARGE_REPORT_THRESHOLD=2`

---

## API contract

All routes take `X-Vyapar-Language: en|hi|te`. Errors use the standard envelope `{"detail": ..., "error": {"code", "message", "details"}}`.

### 1. Contact actions with poster control

| Method and path | operationId | Who |
|---|---|---|
| `GET /v1/listings/contact-preferences` | `getContactPreferences` | self |
| `PATCH /v1/listings/contact-preferences` | `updateContactPreferences` | self |
| `GET /v1/listings/{listing_id}/contact-preferences` | `getListingContactPreferences` | listing owner |
| `PATCH /v1/listings/{listing_id}/contact-preferences` | `updateListingContactPreferences` | listing owner |
| `GET /v1/enquiries/{enquiry_id}/contact-actions` | `getEnquiryContactActions` | either party |
| `GET /v1/enquiries/{enquiry_id}/contact-attempts` | `listContactAttempts` | either party |
| `POST /v1/enquiries/{enquiry_id}/contact-attempts` | `recordContactAttempt` | either party (caller) |

```jsonc
// PATCH /v1/listings/contact-preferences   (every field optional; "reset" = back to default / inherit)
{"call_hours_start": "09:00", "call_hours_end": "18:00", "call_days": ["mon","tue","wed","thu","fri","sat"],
 "max_calls_per_day": 5, "calls_from": "matching_only", "whatsapp_ok": true, "call_ok": true, "reset": []}
// -> 200 ContactPreferencesOut
{"call_hours_start": "09:00", "call_hours_end": "18:00", "call_days": ["mon","tue","wed","thu","fri","sat"],
 "max_calls_per_day": 5, "calls_from": "matching_only", "whatsapp_ok": true, "call_ok": true, "timezone": "UTC+05:30"}
// Listing variant -> {"listing_id": "...", "effective": ContactPreferencesOut, "overrides": ["call_ok"]}
```

```jsonc
// GET /v1/enquiries/{id}/contact-actions   (after acceptance: state in_progress | resolved)
{"enquiry_id": "…", "revealed": true, "counterpart_id": "m_anita", "counterpart_name": "Anita Khatri",
 "calls_today": 1, "max_calls_per_day": 1,
 "contact_actions": [
   {"channel": "call", "label": "Call", "href": "tel:+919000000002", "available_now": false,
    "next_window": "2026-09-29T00:00:00+05:30", "reason": "daily_cap_reached",
    "reason_label": "They have taken all the calls they accept today. Next window: Tue 29 Sep, 00:00",
    "window": "mon-sun 00:00-23:59"},
   {"channel": "whatsapp", "label": "WhatsApp",
    "href": "https://wa.me/919000000002?text=Hi%20Anita%20Khatri%2C%20this%20is%20Suresh%20Kohli%20from%20Vyapar%2C%20about%20%22Khatri%20%26%20Associates%22.",
    "available_now": true, "next_window": null, "reason": null, "reason_label": null, "window": "mon-sun 00:00-23:59"}],
 "attempts": [{"id": "…", "enquiry_id": "…", "caller_id": "m_suresh", "callee_id": "m_anita", "channel": "call",
               "at": "2026-09-28T…", "mine": true, "summary": "You contacted Anita Khatri by Call on 28 Sep 2026, 14:05"}]}
```

Rules for `contact-actions`:
- **Before acceptance:** the response is `{"revealed": false, "contact_actions": []}`. No href and no number are sent. The number comes only from `contacts_for_viewer(listing, true)`, which is the existing rule.
- **`reason` values:**
  - `outside_hours` and `day_off` apply to calls only.
  - `daily_cap_reached` applies to calls only. It counts every caller's attempts per IST day.
  - `not_matching` means `calls_from = matching_only` and the caller's capabilities do not overlap the opportunity's `required_capabilities` (or the listing's capabilities). This uses the ranking capability signal. The href is then `null`.
- **WhatsApp:** it is never capped by hours. The prefilled text is localized (`contact.prefill.whatsapp`).

```jsonc
// POST /v1/enquiries/{id}/contact-attempts   {"channel": "call"}
// -> 201 ContactActionsOut (updated)
// errors: 400 not_revealed | 400 channel_off | 403 not_matching | 429 daily_cap_reached (details.next_window) | 404 enquiries_not_found
```

### 2. "Nobody charges job seekers"

| Method and path | operationId |
|---|---|
| `GET /v1/opportunities/{opportunity_id}/seeker-protection` | `getOpportunitySeekerProtection` |
| `POST /v1/opportunities/seeker-charge-check` | `checkSeekerCharge` |
| `POST /v1/reports` with `reason: "asked_for_money"` | `createReport` (existing) |

```jsonc
// seeker_protection (also on every employment feed card as `seeker_protection`)
{"applies": true, "title": "Nobody charges job seekers",
 "body": "No fee, deposit or kit charge may be asked from applicants. Report if asked.",
 "report_reason": "asked_for_money", "report_label": "Report: asked me for money"}

// POST /v1/opportunities/seeker-charge-check
{"text": "Kitchen helper. Pay ₹500 uniform charge on joining.", "structured": {"type": "employment", "candidate_pays": false}}
// -> {"allowed": false, "code": "seeker_charge_not_allowed", "message": "No fee, deposit or kit charge may be asked from applicants. Remove it to post this opportunity."}
```

**The check.** `trust_safety.check_seeker_charge(text, structured, lang)` raises `ApiError(422, code="seeker_charge_not_allowed")`, with `details.field` set to `candidate_pays` or `text`. It raises when any of these holds:
- `structured.candidate_pays` is true;
- `candidate_pays_amount` or `candidate_pays_paise` is non-zero (also read from a nested `structured` object);
- the text matches `opportunities.ADVANCE_PAYMENT_PATTERNS` (reused read-only) or the added kit, uniform, training and deposit phrases in en, hi and te.

**Reports.** The first `asked_for_money` report opens a Medium case and leaves the post live. The second, from a different reporter, does all of the following:
- pauses the opportunity;
- sets `distribution_limited`;
- raises the case to High with `primary_reason='asked_for_money'`;
- notifies the poster (`opportunityPausedSeekerCharge`, in their language, with the appeal path).

**Hook for the opportunities owner (not wired by B; that file belongs to another agent).** `app/services/hooks.py` holds the registries. Add these calls:

```python
from app.services import hooks
# in create_opportunity / update_opportunity / publish_opportunity, before writing:
hooks.run_seeker_charge_checks(text=" ".join(filter(None, [title, description, requirements, compensation])),
                               structured=body.model_dump(), lang=lang)   # raises 422 seeker_charge_not_allowed
# in get_opportunity, after building `out`:
extra = await hooks.run_opportunity_enrichers(conn, ctx, lang, out.model_dump())  # {"seeker_protection": {...}, "poster_badges": [...]}
# in enquiries.get_enquiry:
extra = await hooks.run_enquiry_enrichers(conn, ctx, lang, out.model_dump())      # {"contact_actions": [...], "contact_attempts": [...]}
```

The `run_*` helpers import their registrants lazily, so there is no import cycle.

### 3. Count-based badges (no star score)

| Method and path | operationId |
|---|---|
| `GET /v1/members/{member_id}/badges` | `getMemberBadges` |

`badges: [{key, label, description, earned_at}]`, localized, appears on:
- `GET /v1/listings/{id}` (`ListingOut.badges`);
- every `searchListings` result card (`listing.badges`);
- `ProfileCard.badges` (similar and matching profiles);
- every feed card (`poster_badges`);
- the opportunity enricher above.

| key | rule |
|---|---|
| `responds_fast` | median first reply under 2 h over at least 5 answered enquiries (180 days) |
| `reliable` | at least 5 revealed published reviews and at least 90% recommend |
| `rising` | member for less than 90 days and at least 3 recommends |
| `top_recommended` | at least 20 reviews and at least 95% recommend |
| `verified_business` | owns an `active_verified` listing |
| `repeat_hires` | at least 3 distinct senders with 2 or more resolved/closed enquiries each |

**Caching.** Badges are cached on the member row. They are recomputed on read once older than `BADGES_CACHE_SECONDS`, and `earned_at` is kept while the badge is held.

```json
{"member_id": "m_anita", "badges": [
  {"key": "rising", "label": "Rising", "description": "New on Vyapar and already recommended by 3 or more people", "earned_at": "2026-09-28T…"},
  {"key": "verified_business", "label": "Verified business", "description": "Business documents checked by Vyapar", "earned_at": "2026-09-28T…"}]}
```

### 4. Tiered service packages

| Method and path | operationId | Who |
|---|---|---|
| `GET /v1/listings/{listing_id}/packages` | `listListingPackages` | anyone who can see the listing |
| `PUT /v1/listings/{listing_id}/packages` | `upsertListingPackages` | owner (upsert by tier; tiers not sent are kept) |
| `DELETE /v1/listings/{listing_id}/packages/{package_id}` | `deleteListingPackage` | owner |
| `POST /v1/listings/{listing_id}/packages/{package_id}/request` | `requestListingPackage` | viewer |

The listing detail response also includes `packages`.

```jsonc
// PUT body
{"packages": [{"tier": "basic", "name": "GST return filing (monthly)", "name_hi": "जीएसटी रिटर्न फाइलिंग (मासिक)", "name_te": null,
               "description": "GSTR-1 and GSTR-3B for one GSTIN, up to 100 invoices.", "description_hi": null, "description_te": null,
               "price_paise": 149900, "delivery_days": 5, "revisions": 1, "includes": ["GSTR-1", "GSTR-3B", "Filing acknowledgement"]}]}
// -> 200 [PackageOut]; name/description resolve to the viewer's language when a variant exists
[{"id": "…", "listing_id": "…", "tier": "basic", "tier_label": "Basic", "name": "GST return filing (monthly)",
  "description": "…", "price_paise": 149900, "price_label": "₹1,499", "delivery_days": 5, "revisions": 1,
  "includes": ["GSTR-1","GSTR-3B","Filing acknowledgement"], "sort": 0, "name_hi": "…", "name_te": null, "description_hi": null, "description_te": null}]
// errors: 422 duplicate_package_tier | 422 too_many_packages | 404 listing_not_found | 404 package_not_found

// POST …/request   {"message": "Namaste, I need monthly GST filing for my electrical contracting firm."}  (Idempotency-Key honoured)
// -> 201 {"enquiry": EnquiryOut, "package": PackageOut}
```

**How a package request works.** It is a normal enquiry created through `enquiries.create_enquiry`, so every enquiry rule, cap and block still applies. It is saved with `sub_choice='request_package'` and `package_id`. A system note ("Requested the Basic package: … (₹1,499)") is added to the thread.

### 5. Discovery filters that work

These routes take the same query parameters:
- `GET /v1/opportunities/feed` (`listOpportunityFeed`);
- `GET /v1/opportunities/feed/section/{key}` (`listOpportunityFeedSection`);
- `GET /v1/opportunities/feed/section/{key}/page` (`listOpportunityFeedSectionPage`).

| Parameter | Values and meaning |
|---|---|
| `skills` | Comma-separated slugs (existing parameter). |
| `q` | Free text: full-text search or a title match. |
| `type` | employment, freelance, local_service, partnership, training or community. |
| `work_mode` | on_site, remote or both. |
| `radius_km` | 1–500. Anything measurably farther is excluded, except remote work. A post without coordinates falls back to matching the locality text. |
| `availability` | `now` means urgent wording or a deadline within 7 days. `this_week` means within 14 days. `later` covers the rest. |
| `sort` (alias `sort_by`) | `relevance` is the default: FR19 score plus diversification. The other values are `distance`, `freshness`, `verified_first` (poster has a verified listing) and `salary_high` (`value_amount`). |

- **Distance and Near You:** distance is a real Haversine (`vyapar_platform.distance_km`) from the member's lat/lng. `near_you` is distance-based within the member's radius (or `radius_km`). It falls back to locality text only when the member has no coordinates.
- **Card fields:** cards are `FeedCard`, which is `OpportunityOut` plus `distance_km`, `poster_badges` and `seeker_protection`.
- **Response fields:** `FeedResponse` adds `filters` (as applied) and `distance_available`. All changes are additive.

| Method and path | operationId |
|---|---|
| `POST /v1/opportunities/saved-searches` | `saveSearch` |
| `GET /v1/opportunities/saved-searches` | `listSavedSearches` |
| `DELETE /v1/opportunities/saved-searches/{search_id}` | `deleteSavedSearch` |

```jsonc
// POST
{"query": "", "name": "Kitchen jobs", "alert": true,
 "filters": {"skills": ["catering"], "type": "employment", "radius_km": 15, "availability": "now", "sort": "relevance"}}
// -> 201 {"id": "…", "name": "Kitchen jobs", "query": "", "filters": {...FeedFilters}, "alert": true, "last_alerted_at": null, "created_at": "…"}
// errors: 429 too_many_saved_searches (max 20) | 404 saved_search_not_found | 422 validation_error
```

**Alerts.** The existing strong-match pass (`run_strong_match_pass`) now also runs `_saved_search_alerts`:
- It looks for new posts since `last_alerted_at` that match each `alert=true` search, using the same candidate query the feed uses.
- It shares the per-member cap `notify:{member}:day` (`RATE_LIMIT_NOTIFY_STRONG_MATCH_PER_DAY`, unchanged) and respects the opportunity mute.
- It sends template `saved_search_match`.

### 6. Agent tokens and the MCP server

- **`contracts:write` scope.** `scopes.py` maps `/v1/contracts` writes to `contracts:write`. Migration 019 widens the DB CHECK. Scope labels are in en, hi and te. The check script confirms two things: a `read`-only token gets `403 scope_required` on `POST /v1/contracts`, and a `contracts:write` token creates a contract. Boosts stay forbidden to tokens (`403 not_available_to_tokens`).
- **New MCP tools.** They call the public REST API only. The README tables list their scopes.

| Group | Tools |
|---|---|
| Enquiries | `accept_enquiry`, `close_enquiry`, `withdraw_enquiry` |
| Contact | `get_contact_actions`, `record_contact_attempt`, `get_contact_preferences`, `update_contact_preferences` |
| Partnerships | `list_partnerships`, `get_partnership`, `respond_partnership`, `create_partnership_request` |
| Reviews and badges | `submit_review`, `list_review_invites`, `get_member_badges` |
| Boosts | `list_boost_products`, `buy_boost` |
| Packages | `list_listing_packages`, `upsert_listing_packages`, `request_listing_package` |
| Saved searches and feed | `save_search`, `list_saved_searches`, `delete_saved_search`, `search_opportunities`, `check_seeker_charge` |
| Applicants and AI | `list_applicants`, `set_applicant_stage`, `draft_opportunity`, `get_ai_shortlist` |
| Contracts | `create_contract`, `fund_milestone`, `approve_milestone` |

The applicant, AI and contract tools use the paths from `imp-backend-d.md`, `routers/ai.py` and the applicant contract:
- `GET /v1/opportunities/{id}/applicants`
- `POST /v1/opportunities/{id}/applicants/{enquiry_id}/stage`
- `POST /v1/ai/draft-opportunity` (`{"text", "language"}`)
- `GET /v1/opportunities/{id}/ai-shortlist`
- `POST /v1/contracts` (`ContractCreateIn`)
- `POST /v1/contracts/{id}/milestones/{mid}/fund`
- `POST /v1/contracts/{id}/milestones/{mid}/approve`

## Bugs found by the check (fixed)
1. **Saved-search alerts would have broken the strong-match pass.** Stamping `last_alerted_at` from the dispatcher context violated the `saved_searches` RLS `WITH CHECK`. The error would have rolled back the whole pass, including the ordinary strong-match notifications. The policy now admits the dispatcher for that write.
2. **An explicit `radius_km` let in posts with no coordinates.** They now fall back to matching the locality text instead.

## Notes for other owners
- **`get_conn` commits after the response is sent.** It commits in FastAPI's `yield`-dependency teardown, which runs after the response goes out. A client that reads the DB (or another endpoint, via a pooled connection) immediately after a 2xx can occasionally miss the write. The check script polls for this. It is existing behaviour across the app and worth knowing for the `main.py` / `db.py` owner.
- **The daily notify cap is already used up.** The live 8011 matcher increments `notify:{member}:day` past its cap every pass (for example, 64 for m_suresh today). `check_and_increment` counts refused calls too. The result is correct, because notifications are still capped, but the counter is not a count of notifications sent.

---

## Pre-accept calling (critique L1, owner-approved 2026-09-28)

A per-post switch, "Let people call me before I accept". It is Apna's "Call HR" and WorkIndia's "Click to call HR", with the poster's protections applied to every caller.

**Migration `023-precall.sql`.** 022 was taken by FE1's taxonomy roles. It is applied and appended to `schema.sql` as section 16. It makes four changes, all additive:
- `opportunities.allow_precall boolean NOT NULL DEFAULT false`, with the CHECK `NOT allow_precall OR type IN ('employment','local_service')`.
- `contact_attempts` gains `opportunity_id`, and `enquiry_id` becomes nullable, with the CHECK that one of the two is set. A tap is therefore recorded even when no application could be created.
- `enquiries.applied_via` CHECK gains `call`.
- A new function `vyapar_integration.notify_precall(attempt_id, texts)` (SECURITY DEFINER). It checks three things before writing a notification in the poster's language: the attempt is the caller's own, the post allows pre-accept calling, and the poster has not blocked the caller.

**Setting.** `allow_precall` is on `OpportunityCreate`, `OpportunityPatch` and `OpportunityOut`, so it also appears on every feed card.
- Setting it on another type returns `422 precall_not_for_type`, with `details: {field, opportunity_type, allowed_types}`.
- A PATCH that changes the type to one without calling switches it off rather than refusing the edit.

| Method and path | operationId | Token scope |
|---|---|---|
| `GET /v1/opportunities/{id}/contact-actions` | `getOpportunityContactActions` | `read` |
| `POST /v1/opportunities/{id}/contact-attempts` | `recordOpportunityContactAttempt` | `enquiries:write` (a tap may open an application; `scopes.WRITE_SCOPE_BY_SUFFIX`) |

```jsonc
// GET /v1/opportunities/{id}/contact-actions   (Suresh, electrician; post requires "electrical")
{"opportunity_id": "…", "allow_precall": true, "available": true, "reason": null, "reason_label": null,
 "poster_name": "Sunita Kapoor",
 "contact_actions": [
   {"channel": "call", "label": "Call", "href": "tel:+919000000004", "available_now": true,
    "next_window": null, "reason": null, "reason_label": null, "window": null},
   {"channel": "whatsapp", "label": "WhatsApp",
    "href": "https://wa.me/919000000004?text=Hi%20Sunita%20Kapoor%2C%20I%20saw%20your%20job%20%22Electrician%20for%20kitchen%20equipment%22%20on%20Vyapar…",
    "available_now": true, "next_window": null, "reason": null, "reason_label": null, "window": null}],
 "calls_today": 0, "max_calls_per_day": 2, "my_taps_today": 0, "my_taps_limit": 3,
 "application_enquiry_id": null, "attempts": []}

// Not available: the number is withheld entirely
{"channel": "call", "href": null, "available_now": false, "reason": "outside_hours",
 "next_window": "2026-09-28T22:40:00+05:30", "reason_label": "Outside their call hours. Next window: Mon 28 Sep, 22:40", "window": "22:40-23:40"}
```

**Per-action `reason` values.** The first four are evaluated in this order:
1. `not_matching`: the poster set `calls_from = matching_only` and the caller's capabilities do not overlap `required_capabilities`.
2. `caller_limit_reached`: this caller has tapped 3 times on this post today (`PRECALL_CALLER_TAPS_PER_DAY`).
3. `daily_cap_reached`: calls only; the poster's `max_calls_per_day` has been used, counted across every caller and every source.
4. `outside_hours` or `day_off`: calls only.

`precall_off` applies when the switch is off, the post is not active, or the poster has blocked the caller. A block reads exactly like "off".

**Top-level `reason` values:**
- `precall_off`: also returned for an anonymous caller. Each action is then listed with `href: null`.
- `own_post`: the poster themself; no actions.
- `no_contact`: the poster has no usable phone or WhatsApp number.

**Rules that shape the response:**
- The phone number appears only inside `href`, and only while `available_now` is true.
- WhatsApp is not limited by call hours or the call cap, the same as in the enquiry flow.
- The WhatsApp prefill (`contact.prefill.whatsappJob`) is in the viewer's language and names the job.
- The poster's settings come from the member defaults (`/v1/listings/contact-preferences`), overridden by the post's `listing_id` listing or else their newest active listing. The number is that listing's phone or WhatsApp contact (`after_accept` counts because the poster opted in; `hidden` never does).

```jsonc
// POST /v1/opportunities/{id}/contact-attempts   {"channel": "call"}
// -> 201 PrecallAttemptOut = PrecallActionsOut (after the tap) +
{"attempt_id": "…", "application_created": true, "application_error_code": null}
// errors: 400 own_post | 403 precall_off | 403 not_matching | 429 precall_caller_limit
//         | 429 daily_cap_reached | 409 outside_hours (details.next_window) | 400 channel_off | 404 opportunity_not_found
```

**What each tap does:**
- It counts toward the poster's daily call cap and toward the caller's 3 taps a day on this post.
- It notifies the poster in their language: "Suresh called about your Electrician for kitchen equipment (Kapoor Caterers) job", or the WhatsApp variant.
- When the caller has no open application, it creates one through `enquiries.create_enquiry` with `applied_via='call'`. That path uses the one-tap profile snapshot, and the first message is "I contacted you by Call from Vyapar about this job." followed by the profile summary. The caller therefore appears on the applicants board.
- If the application is refused (for example, no profile yet, terms not accepted, or a declined earlier application), the tap is still recorded and `application_error_code` gives the reason.

**Detail read.** `GET /v1/opportunities/{id}` returns `allow_precall` and, for viewers other than the poster when the switch is on, `precall_actions`: the same object as `getOpportunityContactActions`. This is merged through the hooks enricher `contact.enrich_opportunity_with_precall`.

**MCP.**
- New tools: `get_opportunity_contact_actions` and `record_opportunity_contact_attempt`.
- `post_opportunity` gains an `allow_precall` parameter.
- The server now loads 61 tools.

**Verification.** `scripts/check_backend_b.py` now runs **91/91**. It covers:
- the type rule, on both create and PATCH;
- off, `own_post`, `not_matching` (Ravi, a plumber), available (Suresh), the application with `applied_via=call` and a snapshot, and the notification to the poster;
- reuse of an existing application, `daily_cap_reached` (poster at 2/2), `caller_limit_reached` (4th tap), and `outside_hours` with `next_window` (Rahul);
- a blocked member (Gaurav) and callers shown on the applicants board;
- the absence of the number from every unavailable response.

All data is cleaned up afterwards, including the block, both members' preferences and the enquiry counters.

**Files changed:**
- migration `023-precall.sql` and `schema.sql` §16
- `app/services/opportunities.py` (setting, validation, output, detail merge)
- `app/services/enquiries.py` (one line: `AppliedVia` gains `call`)
- `app/services/contact.py`, `app/routers/contact.py`
- `app/integrations/identity/scopes.py`, `app/config.py` (`PRECALL_CALLER_TAPS_PER_DAY=3`)
- i18n catalogs: contact, notifications and opportunities, in en, hi and te
- `vyapar-mcp`

---

## Follow-ups from FE2 (2026-09-29)

### Contact times in IST, in the reader's language
- **Finding.** The attempt summary was already converted to +05:30 (for example, 15:01 UTC showed as 20:31). What remained wrong:
  - day and month names were always English ("28 Sep") even in Hindi and Telugu;
  - there was no zone label;
  - the only machine field, `at`, is UTC, so a client printing it directly shows a time 5½ hours off;
  - a naive timestamp would have been converted using the host clock.
- **Fix** (`services/contact.py`, `to_local()` / `format_local()`). Every time a person reads is Asia/Kolkata. That is a fixed +05:30 with no daylight saving, taken from `CONTACT_TIMEZONE_OFFSET_MINUTES`; this Windows host has no `tzdata`, so `ZoneInfo` cannot be used. Day and month names come from the reader's catalog (`contact.date.*` in en, hi and te), and the text always ends with the zone label, e.g. "28 सित॰ 2026, 20:31 IST". A naive value is treated as UTC.
- **Where it applies.** Attempt summaries, and every `reason_label` "Next window: …" (e.g. "Tue 29 Sep, 01:30 IST"), on both enquiry and pre-accept actions. The MCP tools return these same strings.
- **Response change.** `ContactAttemptOut` gains `at_local` (the same instant as ISO with `+05:30`). `at` stays UTC for machine use. `enquiry_id` is nullable, because a pre-accept tap with a refused application has no enquiry.

```json
{"id": "…", "enquiry_id": "…", "caller_id": "m_suresh", "callee_id": "m_sunita", "channel": "call",
 "at": "2026-09-28T15:01:00+00:00", "at_local": "2026-09-28T20:31:00+05:30", "mine": true,
 "summary": "आपने Sunita Kapoor से कॉल द्वारा 28 सित॰ 2026, 20:31 IST को संपर्क किया"}
```

### "Use my location": viewer position override on the feed endpoints
The following endpoints accept optional `lat` (-90..90) and `lng` (-180..180):
- `GET /v1/opportunities/feed/results`
- `GET /v1/opportunities/feed/rows`
- `GET /v1/opportunities/feed`
- `GET /v1/opportunities/feed/section/{key}`
- `GET /v1/opportunities/feed/section/{key}/page`

**Behaviour:**
- For that request only, the position replaces the member's saved coordinates for distance (`distance_km`), the radius filter, "Near you" and `distance_available`. Nothing else in the feed logic changed.
- It is never written anywhere: not to the member row, and not to saved searches, since `FeedFilters` has no position.
- Send both values or neither. One without the other returns `422 position_incomplete` ("Send both latitude and longitude, or neither.", in en/hi/te). An out-of-range value returns `422 validation_error`.

The MCP `search_opportunities` tool accepts the same optional `lat` and `lng`.

```
GET /v1/opportunities/feed/results?lat=17.4156&lng=78.4347&radius_km=3
```

**Verification.** `scripts/check_backend_b.py` now runs **121/121** on a private port. The new checks cover:
- `at_local` being the same instant at +05:30, the summary showing the IST clock time, and the Hindi and Telugu wording;
- distances re-measured from the override (a Banjara Hills job reads about 0 km for a member saved in Dilsukhnagar);
- the radius applied around the override;
- all five endpoints accepting the override, `position_incomplete`, and out-of-range latitude and longitude;
- the member's stored coordinates unchanged afterwards.

---

## Feed relevance and honest pre-accept contact (critique L13, L14, W2; 2026-09-29)

### L14: skills from the member's profiles
- **New module `app/viewer_profile.py`** (`viewer_skills()` / `viewer_capabilities()`). It is the one answer to "what can this viewer do": the member's own skills plus the capabilities and categories of every **active** listing they own. Drafts, suspended and archived listings are excluded.
- **Where it is used:**
  - feed ranking (`_member_profile`, which now also carries `categories`);
  - all feed endpoints and rows;
  - "Why this?";
  - the opportunity detail's `capability_match` and similar list;
  - `calls_from = matching_only` on both contact flows.
- **Check result.** Anita's member row has no skills, and her business profile says accounting, GST filing and tax. Her feed now has For you with the three accounting posts, her first row is For you, "Why this?" credits `capability_fit`, and the detail marks both skills as matching.

### L13: themed rows (`GET /v1/opportunities/feed/rows`)
Rows are filled in priority order, most specific first:
1. For you, then up to 2 skill-category rows.
2. Near you: within the radius, kinds of work the member does only.
3. The pay band that fits the member: `pay_20k` (monthly jobs) only when the member's skills match an employment post, or when they have no skills yet. `pay_projects` (freelance or local work with a budget over ₹10,000) only for members whose skills match such work.
4. New today, then Starting this week.
5. The generic Projects and Work from home rows, from what is left.

Rules for every row:
- **One row per post.** A post shown in one row is claimed and never appears in another.
- **Minimum and cap.** A row with fewer than 3 unclaimed posts is hidden and claims nothing. The home stops at 6 rows.
- **Dropped rows.** "Verified" and "Community" are no longer rows. They matched nearly the whole feed, so they stay as filters and card badges.
- **Relevance tiers.** Every row is ordered by relevance to the viewer first, in these tiers:
  - 0: their own skill;
  - 1: a related skill in the same trade category (plumbing is related for an electrician: both are Home repair);
  - 2: open local work that asks for no particular skill;
  - 3: anything else.

  The FR19 score comes next, and the row's own order (freshness or pay) breaks ties.
- **Near you** admits only tiers 0–2. A member with no skills gets jobs and local work. A Python job or a grant can no longer open an electrician's Near you.
- **Titles.** `FeedRow` gains `title`, the row title already localized by the server (`discover.rows.*`, en/hi/te), as a fallback. **FE2 needs one new web key:** `explore.rows.projectsBudget` = "Projects with a budget over {{amount}}". Until it exists, use `title`.
- **Current dev data.** On today's dev DB (about 20 active posts, each needing specific skills), Suresh and a fresher see few rows. Their only related posts are few or their own. The home no longer pads itself with repeats or unrelated rows, and it grows as posts grow.

### W2: pre-accept contact channel (migration `025-precall-channel.sql`, `schema.sql` §18)
- **New column.** `opportunities.precall_channel` is `whatsapp_only` (default for new posts) or `call_and_whatsapp`. Posts that already allowed pre-accept calling were backfilled to `call_and_whatsapp`, keeping what they chose. It is settable on create and PATCH, and returned on every opportunity.
- **Honest copy.** Every job and local-service post has a `precall_disclosure` in the reader's language:
  - `whatsapp_only`: "Anyone who messages you on WhatsApp from this post will see your phone number. They can't ring you from Vyapar."
  - `call_and_whatsapp`: "Anyone who calls or messages you from this post will see your phone number, and can reach you on it later."

  **FE1 should replace `hiring.json` → `precall.explain`** ("…your number is never shown outside them", which is untrue) with this text, and add the channel choice to the switch.
- **API behaviour.** `GET /v1/opportunities/{id}/contact-actions` returns `precall_channel`. On a WhatsApp-only post the call action has `href: null` and `reason: "whatsapp_only"`. `POST …/contact-attempts {"channel": "call"}` returns `403 precall_whatsapp_only`.
- **Production fix.** A masked or proxy number (Exotel / Knowlarity class) is logged as a vendor backlog item in `09a-external-dependencies.md`. `contact.py` is the one place that builds the href.
- **MCP.** `post_opportunity` gains `precall_channel`, and the tool text tells the agent to warn the member that the number is shown.

**Verification.** `scripts/check_backend_b.py` now passes **139/139** on private port 8091, and every test post and setting is removed afterwards. The new checks cover:
- **Personas:** three real accounting posts by Sunita, Vikram and Deepak; Anita (L14 as above); Suresh; and a fresher (`m_new`, sharing a Dilsukhnagar position).
- **L13 invariants for all three:**
  - unique posts across rows, at least 3 per row, at most 6 rows, and no Verified or Community rows;
  - Suresh's Near you only jobs and local work in his trade category, with no Python job or grant in his first row;
  - the fresher gets no For you, the add-your-skills prompt, and a Near you of jobs and local work only;
  - Telugu row titles.
- **W2:** a new switch defaults to WhatsApp only, the disclosure copy is right, a call on a WhatsApp-only post is refused, and switching to calls updates the copy. The existing call checks then run on `call_and_whatsapp`.

The coordinator's `Depends(get_conn, scope="function")` change is in place, and the checks pass with it. The polling stays in as a harmless guard.


---

## Owner, 2026-09-30: "all the real functionality is actually created as dummy"

Each fix below was traced to its cause in the code and proven through the API as the real personas. Proof ran on a private port against the shared dev DB; 8011 serves it once the restore agent restarts it.

### 1. Trade filter returned nothing ("Plumbers" → 0 opportunities)
**Causes:**
- **Expired data:** the only plumbing post had expired on 20 September.
- **Exact slugs only:** the filter compared skill slugs exactly, so a category tile, a free-text skill ("plumber") or a title naming the trade never matched.
- **Radius on explicit searches:** `feed/results` also applied the member's home radius to on-site posts, so a city-wide trade search dropped everything beyond about 10 km of home.

**Fixes:**
- **`app/trade_match.py`** is the one matcher, used by `feed/results`, the sectioned feed, sections and saved searches.
  - A category slug expands to every skill under it (`home_repair` → plumbing, electrical, carpenter…).
  - A skill matches its slug, a free-text skill, or a title containing any of its names (en/hi/te) or aliases. ASCII words match at a word start; Hindi and Telugu match as substrings.
- **Migration `026-trade-words-and-seed-marker.sql`** adds the words people type: plumber, electrician, नलसाज, ప్లంబర్, CA, … It also adds a nullable `seed_batch` marker to members, listings and opportunities.
- **Skill facet count:** the chosen skill's facet is counted the way the filter matches.
- **Radius scope:** `feed/results` applies a radius only when the person picks one (`radius_km`). The home feed, sections and rows keep the member's home radius as a hard constraint.
- **Coordinates for posts:** a post whose location names a known Hyderabad locality now gets coordinates, on create and when its location is edited (`app/geo.py`, a gazetteer of about 35 localities). `OpportunityCreate` and `OpportunityPatch` also accept explicit `lat` and `lng`. Profiles are geocoded from their locality in the same way.

**Proof (Rahul, Kukatpally):**
- Plumbers tile: 4 posts, nearest first.
- Electricians: 6 posts.
- Home repair category: 21 posts.
- A picked 3 km radius still cuts the list.

### 2. Businesses search found nothing real
**Causes:**
- **Match was too narrow:** full-text search on the listing row only. The owner's name was never searched, spelling variants failed, and a typed place was matched as text.
- **Nowhere to go from zero:** an empty result had no automatic next step.

`GET /v1/listings/search` (`searchListings`) has the same parameters as before. What changed:
- **Matching:**
  - Every query word must prefix-match a word in the listing name, `business_name`, the owner's name, the skills (names in three languages plus aliases, and categories), the headline or the description.
  - Matching is spelling-tolerant: `app/text_fold.py` folds case, accents, doubled letters, ee/oo, aspirates and a final "a", so "krishna", "Krishnaa", "aneeta" (Anita) and "Kukatpalli" all match.
  - Words of one or two letters ("CA", "AC") must match a whole word.
- **Weights:** the field hit sets the weight: name 3, skills 2, headline 1.5, description 1.
- **Place:** a place in `q` or in `locality` becomes a distance filter around it (5 km), taken out of the text words.
- **Ranking:** relevance, then distance, then the FR19 score. `sort_by` still overrides the order.
- **Zero results broaden automatically, in this order:**
  1. widen the radius around the place (15, then 30 km);
  2. drop the place;
  3. accept any of the words.

  The response says which step ran.
- **Response additions:** `place {name, lat, lng}`, `radius_km`, `broadened: [widenedRadius | droppedPlace | anyWord]`, `notice_text` (server-localized), and `notice` = the same key. New keys `discover.notice.{widenedRadius, droppedPlace, anyWord}` exist in en/hi/te. **FE:** show `notice_text` (or add these keys to the web catalog).

**Proof (Rahul):**

| Query | Result |
|---|---|
| "krishna" / "krishnaa" | Krishna Rao Plumbing Works |
| "ameerpet" | 7 profiles within 5 km of Ameerpet |
| "plumber ameerpet" | Krishna Rao, then Ravi Mehra |
| "electrician kukatpally" | Ramesh Naidu |
| "tailor charminar" | Salma Khatoon |
| "ca" | only chartered accountants |
| "बिजली मिस्त्री" | electricians |
| "plumber" near Kompally | broadens, and says so |

### 3. Notifications
**(a) Language: read in the reader's language.**
- **Template on write:** `send_notification(..., i18n=spec)` stores `params._i18n = {title, body, values, key_values}`. `notify_member`, `notify_interaction_party`, trust and safety, verification, pre-accept calling, the seeker pause and the match, alert and digest passes all pass it.
- **SQL writers:** migration `027-notification-texts.sql` makes the five SQL functions that receive pre-rendered texts keep them all, under `params._texts`: `notify_interaction_party`, `notify_workspace_member`, contracts `notify_party`, `apply_seeker_charge_reports` and `notify_precall`. It was generated from their live definitions, changing only the params value.
- **Read path:** `GET /v1/notifications` and `/page` render with `render_notification(row, lang)`. The order is the spec, then the reader's-language texts, then the stored text. A missing key or unfilled placeholder falls back rather than showing `{name}`.
- **Backfill:** `scripts/backfill_notification_i18n.py` (idempotent, owner role) has been run.
  - 90 existing rows are now templated.
  - Values are rebuilt from the post or listing, or read back from the displayed text by matching each language's template (exactly what the reader saw).
  - A handful of legacy rows stay as stored. Their templates have no catalog key (`enquiry_new`, `daily_digest`, `opp_strong_match`, `review_invite`), or the catalog wording has changed since they were sent (3 contract rows).

**(b) Wording (GLOSSARY).** "This post matches your skills.", "{count} new posts for you", "Your post was paused", "The person who posted…", in en/hi/te.

**(c) Duplicates:**
- **Matches:** a match is keyed `match:{member}:{post}` permanently (it was per day, and returned after 7 days). Every pass skips posts already announced to the member by any kind (match, saved-search alert or digest), the member's own posts, and expired or closed posts (`deadline > now()`).
- **Saved-search alerts:** they exclude already-announced posts, and their key is the set of posts.
- **Digest:**
  - It counts only posts not already announced, and lists them in params.
  - It runs at the member's hour in IST (it compared against the UTC hour before).
  - It is never sent twice within 20 hours, and is skipped when there is nothing new.
- **Matching skills:** matching now uses the member's profile skills too (L14).
- **Cleanup:** 16 duplicate "New match" rows already in inboxes were removed, keeping the earliest.

**(d) Links:**
- A match opens the post.
- A saved-search alert opens the post (one) or Discover with the saved filters (several).
- A digest opens Discover on "New today" (`/?posted_within=today&sort=freshness`), and 32 old digest rows were re-linked.

**Proof.** Suresh's inbox reads "New match / नया मिलान / కొత్త మ్యాచ్: …" in en, hi and te. A partnership request to Anita reads in three languages. The real match and digest passes, run twice in a rolled-back transaction:
- zero duplicate (member, post) pairs;
- zero expired or closed posts;
- a second digest sends 0;
- every link points at its subject.

### 4. A living marketplace: `scripts/seed_marketplace.py`
- **What it creates,** through the public API as each member:
  - 22 new members, created through the real member path: first request, first run, privacy and terms, their one profile via `/v1/me/profile` (business section where they have a shop), contact OTP and submit;
  - 111 posts across all 22 trade categories and 32 Hyderabad localities, from those members and the existing dev personas. The spread is employment 77, local work 22 and projects 11. Pay is real per trade: delivery ₹15–22k a month, plumbing ₹500–1,500 a visit, projects ₹8–85k. Deadlines are 7–30 days out, titles are Hinglish or Telugu-English, and about a third allow pre-accept WhatsApp;
  - 23 priced packages;
  - 6 two-way reviews through the real enquiry → accept → reply → resolve → review flow.
- **Written directly as the owner role** (no API does these): the `seed_batch` marker, and a staggered `published_at` of 0–9 days, so "New today" is about a third of the feed rather than all of it.
- **Guards:**
  - The owner's account (`m_krishna`) is asserted never to be used.
  - The script is idempotent: a second run created 0 posts.
  - `--clean` removes all marked rows and what hangs off them. This was verified inside a rolled-back transaction: 110 posts, 22 profiles, 22 members and 6 enquiries.
- **It has been run.** The dev DB now has 121 live posts and 35 active profiles.

### Checks
`scripts/check_backend_b.py` passes 162/163 on private port 8091. The one failure is FE2's own `money: free text is kept as written` check (their `legacy_compensation_label("Negotiable", "freelance")`); it is not in this workstream. New checks:
- **Trade:**
  - the slug post and the free-text "nal wala / plumber" post both come back from the Plumbers tile and from the Home repair tile;
  - the chip count is right;
  - the sectioned feed applies the same filter;
  - Electricians excludes plumbing;
  - a picked radius cuts;
  - posts get coordinates.
- **Search:** owner name; spelling ("aneeta" → Anita); business name; place as distance; trade word plus place; auto-broaden with notice; "CA" whole-word; a Hindi trade word.
- **Notifications:** hi, te and en rendering of one real notification; the paged inbox; glossary wording; the rolled-back two-pass dedupe, expiry, digest and link checks.

The personas used are Rahul, Meena, Deepak, Anita and Suresh. Everything they create is removed afterwards.

**Notes.**
- **Migration numbering:** two migrations are numbered 026: mine (`026-trade-words-and-seed-marker.sql`, created 10:31) and Backend A's `026-one-profile-per-member.sql` (10:33). Both are idempotent and independent, and init.sh runs them in name order. I left both names as they are.
- **Not done here:** `openapi.json` is not regenerated and 8011 is not restarted, as the coordinator asked.

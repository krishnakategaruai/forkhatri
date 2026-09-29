# IMP42 — Backend workstream C: AI assistance (drafts, photo reading, shortlist, posting tips, proposal help) (2026-09-28)

## What was built

This workstream adds five AI-assisted operations. Each works the same way: Claude answers when it is configured, and a built-in rules engine answers when it is not.

| Operation | Who uses it | What it gives back |
|---|---|---|
| `draftOpportunity` | a poster typing or dictating a notice (English, Hindi, Telugu, Hinglish) | a full draft: type, title, description, location, skills, and the typed employment / freelance / local-service fields from migration 018. It also gives a confidence value per field, the fields still `missing`, and a question in the poster's language for each missing field. |
| `readOpportunityImage` | a poster with a photo or PDF of a notice | the same draft, read by Claude vision. Under the rules engine it answers `501 unsupported_without_ai`. |
| `getAiShortlist` | the poster of an opportunity | each applicant scored 1–10 with localized reasons and risks, highest first |
| `getPostingTips` | a poster, from a draft or a posted opportunity | concrete tips, each with an impact level (for example: lower the minimum qualification to 12th, add job timings, add a salary) |
| `improveProposal` | an applicant | a suggested cover text, the improvements still worth making, and a suggested bid range |

**Guarantees, the same for all five:**
- **Suggestions only.** AI never writes to the database. Every answer is a suggestion the person confirms through the existing endpoints (`createOpportunity`, `createEnquiry` and so on). The only rows written are the audit rows below.
- **Closed vocabularies.** Every provider answer is validated in `app/integrations/ai/vocab.py` before anyone sees it. The vocabularies are:
  - opportunity types;
  - taxonomy capability slugs, read live;
  - the migration-018 enums;
  - reason, risk, tip and improvement codes.

  An invented type, slug or code is dropped. Money and counts are clamped. An unknown applicant reference is ignored. The Claude request also carries a strict JSON schema whose enums *are* these vocabularies.
- **Minimum data sent.** Only the fields an answer needs are sent to Claude. Phone numbers and e-mail addresses are removed before sending. Applicants are sent as opaque references (`a1`, `a2`), and no member name or id appears in any prompt. Drafts and cover texts also drop contact details from the text they return, because contact goes through Vyapar's own disclosure controls.
- **Audit trail.** Every call writes one row to `vyapar_integration.ai_events` (migration 020): member, kind, provider, model, sha256 of the input, latency, tokens, outcome and access-token id. The input text itself is never stored.
- **Daily limit.** Each member has a daily cap, `AI_DAILY_LIMIT` (default 50), shared across all five operations. Over the cap the API answers `429` with code `ai_limit_reached`.
- **Fallback.** When Claude is unreachable, rate-limited, refuses, or returns bad JSON, the rules engine answers instead. The response then says `"source": "rules"` and the audit row records `outcome = fallback`. Photo reading has no rules fallback: it answers `501` with no key configured and `503` on a Claude failure.

## Files

**New (owned by this workstream):**

| Area | File |
|---|---|
| Adapter seam | `vyapar-service/app/integrations/ai/__init__.py`: `get_ai_provider()`, `get_rules_provider()`, `set_ai_provider()` for hosts |
| | `…/ai/base.py`: `AiProvider` protocol, `AiResult`, `AiUnavailable`, `ImageInput` |
| | `…/ai/config.py`: `AiSettings` (`AI_PROVIDER`, `ANTHROPIC_API_KEY`, `VYAPAR_AI_MODEL`, `AI_DAILY_LIMIT`, `AI_TIMEOUT_SECONDS`, `AI_MAX_INPUT_CHARS`) |
| | `…/ai/vocab.py`: closed vocabularies, validators, contact redaction, "what is missing" |
| | `…/ai/anthropic_provider.py`: Claude via the official `anthropic` SDK. It uses `output_config.format` JSON schema, `effort: low` and vision. |
| | `…/ai/rules_provider.py`: the keyword engine (en/hi/te/Hinglish). It extends `opportunities._extract_fields`. Its shortlist scores come from `app/ranking.py` signals scaled to 1–10. |
| Service | `vyapar-service/app/services/ai.py`: SQL, limit, audit, validation, localization |
| Router | `vyapar-service/app/routers/ai.py`: 5 routes, typed models, `operation_id`s, documented errors |
| i18n | `app/i18n/locales/{en,hi,te}/ai.json`: errors, questions, reasons, risks, tips, improvements, cover-text phrases |
| Migration | `07a-db-implementation/migrations/020-ai.sql`: applied to the dev DB as `vyapar_owner` (idempotent) |
| Check | `vyapar-service/scripts/check_ai.py` |
| Config | `vyapar-service/.env.example` (new): every `.env` key, secrets as `CHANGE_ME`, plus the AI block |

**Edited (shared files, minimal edits):**
- `app/main.py`: one import and one `include_router` line, placed after workstream D's.
- `requirements.txt`: `anthropic>=1.8` (1.8.0 installed in `.venv`).
- `07a-db-implementation/schema.sql`: section 15 appended (`ai_events`).

**Not touched:** every other service and router, `scopes.py`, `vyapar-web/`, `vyapar-mcp/`, `.env`.

## Configuration

```ini
AI_PROVIDER=rules            # anthropic | rules. "anthropic" needs a real key, otherwise rules is used.
ANTHROPIC_API_KEY=CHANGE_ME
VYAPAR_AI_MODEL=claude-sonnet-5   # Claude Sonnet 5 by default for cost; any current model id
AI_DAILY_LIMIT=50
AI_TIMEOUT_SECONDS=45
AI_MAX_INPUT_CHARS=6000
```

A host with its own model gateway implements `AiProvider` and calls `set_ai_provider()` at startup. The core never imports a host.

## Dependency on workstream A (migration 018): verified

The shortlist, tips and proposal code read the opportunity and enquiry rows through `to_jsonb(row)` and `.get()`. A column that did not exist yet would therefore be `None` instead of an error. Migration 018 has now landed. Its column names match this workstream's vocabulary exactly:
- **Opportunity columns:** `salary_min_paise`, `salary_max_paise`, `incentive_type`, `openings`, `shift`, `job_timings`, `interview_details`, `min_qualification`, `english_level`, `experience_min_months`, `experience_max_months`, `requires_assets`, `budget_type`, `budget_min_paise`, `budget_max_paise`, `hourly_rate_min_paise`, `hourly_rate_max_paise`, `duration`, `experience_level`, `screening_questions` (`[{id, text}]`), `preferred_date`, `budget_paise`, `urgency`.
- **Enquiry columns:** `bid_amount_paise`, `bid_type`, `stage`, `profile_snapshot`.

The shortlist uses the following sources:
- **Bid:** `bid_amount_paise`. A bid is compared with the budget only when `bid_type` matches the opportunity's `budget_type`.
- **Budget:** the typed budget or salary. The legacy `value_amount` is the fallback.
- **Skills and years:** `profile_snapshot`, when the applicant has no active listing.

## API contract

All routes are under `/v1` and tagged `ai`, with the shared error envelope `{"detail", "error": {"code", "message", "details"}}`. Every request accepts an optional `language` (`en|hi|te`) in the body, or `?language=` on GET. When it is absent, `X-Vyapar-Language` or `Accept-Language` decides. The answer (questions, reasons, tips, cover text, and the Claude-written text fields) is in that language. The examples below are real responses from the rules engine against the dev database.

### 1. `draftOpportunity`: `POST /v1/ai/draft-opportunity`

Request: `{"text": string (1..AI_MAX_INPUT_CHARS), "language"?: "en"|"hi"|"te", "entry"?: "text"|"voice"}`

```json
{"text": "Hiring 5 delivery boys in Kukatpally. Salary 15k-18k per month + incentives. Own bike and driving licence required. 10th pass, freshers ok. Timings 9am to 7pm. Walk-in interview Mon-Sat 11am. Call 9876543210", "language": "en"}
```

Response `200`:

```json
{
  "type": "employment",
  "title": "Hiring 5 delivery boys in Kukatpally",
  "description": "Hiring 5 delivery boys in Kukatpally. Salary 15k-18k per month + incentives. Own bike and driving licence required. 10th pass, freshers ok. Timings 9am to 7pm. Walk-in interview Mon-Sat 11am.",
  "location": "Kukatpally",
  "work_mode": null,
  "timing": null,
  "required_capabilities": ["delivery"],
  "capability_labels": ["Delivery & logistics"],
  "employment": {
    "salary_min_paise": 1500000, "salary_max_paise": 1800000,
    "incentive_type": "fixed_plus_incentive", "openings": 5, "shift": null,
    "job_timings": "9am to 7pm", "interview_details": "Walk-in interview Mon-Sat 11am",
    "min_qualification": "10th", "english_level": null,
    "experience_min_months": 0, "experience_max_months": null,
    "requires_assets": ["two_wheeler", "driving_licence"]
  },
  "freelance": null,
  "local_service": null,
  "confidence": {"type": 0.85, "title": 0.6, "description": 0.9, "location": 0.55, "required_capabilities": 0.65, "salary": 0.6, "openings": 0.6, "job_timings": 0.6, "interview_details": 0.6, "min_qualification": 0.6, "experience": 0.6, "requires_assets": 0.6},
  "missing": [],
  "questions": [],
  "source": "rules",
  "language": "en"
}
```

How the fields are filled:
- **Typed blocks.** Exactly one of `employment` / `freelance` / `local_service` is set, the one matching `type`. The others are `null`.
- **Freelance block:** `{budget_type: fixed|hourly, budget_min_paise, budget_max_paise, hourly_rate_min_paise, hourly_rate_max_paise, duration: under_1_week|1_4_weeks|1_3_months|3_6_months|over_6_months|ongoing, experience_level: entry|intermediate|expert, screening_questions: [{text}]}`.
- **Local-service block:** `{preferred_date: "YYYY-MM-DD", budget_paise, urgency: today|this_week|flexible}`.
- **Money** is always in paise.
- **`experience_min_months: 0`** means freshers are welcome.
- **Field codes.** The `confidence` keys and `missing` entries are field codes from this list: `type title description location work_mode timing required_capabilities salary incentive_type openings shift job_timings interview_details min_qualification english_level experience requires_assets budget budget_type hourly_rate duration experience_level screening_questions preferred_date urgency`.
- **`questions[i]`** is the localized question for `missing[i]`.

Hindi example (`"language": "hi"`, input `"Kukatpally में 3 सेल्स स्टाफ चाहिए। वेतन 12000 से 15000 महीना। 12वीं पास। 1 साल अनुभव।"`), abridged:

```json
{"type": "employment", "title": "Kukatpally में 3 सेल्स स्टाफ चाहिए", "location": "Kukatpally",
 "required_capabilities": ["sales"], "capability_labels": ["बिक्री"],
 "employment": {"salary_min_paise": 1200000, "salary_max_paise": 1500000, "min_qualification": "12th", "experience_min_months": 12, "...": "..."},
 "missing": ["job_timings"], "questions": ["काम के घंटे क्या हैं?"], "source": "rules", "language": "hi"}
```

Telugu voice example (`"entry": "voice"`, input `"Madhapur లో ప్లంబర్ కావాలి ఈరోజు, కిచెన్ సింక్ లీక్ అవుతోంది. బడ్జెట్ రూ 800"`), abridged:

```json
{"type": "local_service", "location": "Madhapur", "required_capabilities": ["plumbing"], "capability_labels": ["ప్లంబింగ్"],
 "local_service": {"preferred_date": "2026-09-28", "budget_paise": 80000, "urgency": "today"}, "missing": [], "source": "rules", "language": "te"}
```

Errors:
- `422 text_too_long`
- `422 validation_error` (empty text, unknown language)
- `429 ai_limit_reached`

### 2. `readOpportunityImage`: `POST /v1/ai/read-opportunity-image`

Request: `{"image_url"?: string, "upload_id"?: string, "language"?: ...}`.
- `image_url` is either an `https://` URL, or the `/uploads/<name>` URL that `uploadFile` returned.
- `upload_id` is the bare file name `uploadFile` returned.
- A PDF must be uploaded; a PDF link is refused. The upload limit is 5 MB, and the name must be flat (no path traversal).

Response: the same shape as `draftOpportunity`, with `"source": "ai"`.

Under the rules engine:

```json
HTTP 501
{"detail": "Reading a photo needs the AI assistant, which is not switched on here. Please type the details instead.",
 "error": {"code": "unsupported_without_ai", "message": "Reading a photo needs the AI assistant, which is not switched on here. Please type the details instead.", "details": {"i18n_key": "ai.error.unsupportedWithoutAi"}}}
```

Errors:
- `501 unsupported_without_ai`
- `503 unavailable` (Claude failed; there is no fallback for photo reading)
- `422 image_required`
- `422 image_not_found`
- `422 pdf_needs_upload`
- `413 image_too_large`
- `429 ai_limit_reached`

### 3. `getAiShortlist`: `GET /v1/opportunities/{opportunity_id}/ai-shortlist?language=`

Poster only. It reads the enquiries on the opportunity, excluding `withdrawn` and `restricted`. For each applicant it uses:
- their best matching active listing;
- `profile_snapshot`, when they have no active listing;
- their first message as the cover text;
- their bid.

```json
{
  "opportunity_id": "00000000-0000-4000-8000-000000000103",
  "applicant_count": 1,
  "items": [{
    "enquiry_id": "00000000-0000-4000-8000-000000000205",
    "sender_id": "m_priya",
    "listing_id": "00000000-0000-4000-8000-000000000005",
    "name": "Priya Malhotra — Full-stack developer",
    "kind": "professional",
    "verified": true,
    "experience_years": 8,
    "distance_km": 2.4,
    "availability": "this_week",
    "stage": "new",
    "bid_paise": null,
    "match_score": 3,
    "reasons": [{"code": "location_fit", "text": "close to the work"}, {"code": "trust_fit", "text": "verified profile"}, {"code": "timing_fit", "text": "available now"}],
    "risks": [{"code": "no_capability_overlap", "text": "none of the required skills on their profile"}],
    "summary": null
  }],
  "source": "rules",
  "language": "en"
}
```

The response has these rules:
- **Order.** Items are sorted by `match_score`, highest first.
- **Reason codes:** `capability_fit location_fit experience_fit trust_fit timing_fit value_fit cover_text_specific bid_within_budget quick_to_apply`.
- **Risk codes:** `no_capability_overlap partial_capability_overlap far_away unverified no_cover_text bid_above_budget bid_far_below_budget no_experience_listed not_available_now no_public_profile`.
- **`summary`** is one sentence from Claude, or `null` from the rules engine.
- **Skill guard.** An applicant with none of the required skills is capped at 3 and always shows `no_capability_overlap`, whether Claude or the rules scored them. Experience in another trade never counts as experience for this work.
- **`name`** is the applicant's own public listing name, which the poster already sees in Enquiries. It is never sent to Claude.

No applicants gives `200` with `{"applicant_count": 0, "items": []}` and makes no provider call.

Errors:
- `403 poster_only`
- `404 opportunity_not_found`
- `429 ai_limit_reached`

### 4. `getPostingTips`: `POST /v1/ai/posting-tips`

Request: `{"draft"?: DraftIn, "opportunity_id"?: uuid, "language"?: ...}`. `DraftIn` is the draft shape above (all fields optional), plus an optional `deadline`. With `opportunity_id`, the posted opportunity is used, and only its poster may ask.

```json
{"draft": {"type": "employment", "title": "Sales executive", "description": "Sales job",
           "employment": {"min_qualification": "graduate", "english_level": "fluent"}}}
```

```json
{"tips": [
  {"code": "add_description", "impact": "high", "text": "Describe the work in a few more lines: duties, place, timings."},
  {"code": "add_location", "impact": "high", "text": "Add the area or locality — nearby people respond most."},
  {"code": "add_capabilities", "impact": "high", "text": "Pick the skills or trades needed so the right people see it."},
  {"code": "add_salary", "impact": "high", "text": "Add a salary or range — posts with pay get far more responses."},
  {"code": "add_job_timings", "impact": "medium", "text": "Add working hours such as 9 am to 6 pm."},
  {"code": "lower_min_qualification", "impact": "medium", "text": "Lower the minimum qualification to 12th if the work allows — more responses."},
  {"code": "relax_english_level", "impact": "medium", "text": "Ask only for basic English if the work does not need more."},
  {"code": "add_openings", "impact": "low", "text": "Say how many people you need."}
 ],
 "source": "rules", "language": "en"}
```

The response has these rules:
- **Length and order.** At most 8 tips, ordered high, then medium, then low impact.
- **Tip codes:** `add_title shorten_title add_description add_location set_remote_or_both add_capabilities fewer_capabilities add_salary add_job_timings add_openings lower_min_qualification relax_english_level reduce_experience add_interview_details add_budget add_hourly_rate add_duration add_screening_questions add_preferred_date set_urgency add_timing add_deadline mention_incentives`.
- **With Claude.** The rules tips are always computed first. Claude may reword them in the draft's own terms, drop any that do not apply, or add tips, but only with these codes.

Errors:
- `422 draft_or_opportunity_required`
- `403 poster_only`
- `404 opportunity_not_found`
- `429 ai_limit_reached`

### 5. `improveProposal`: `POST /v1/ai/improve-proposal`

Request: `{"opportunity_id": uuid, "text"?: string, "language"?: ...}`

```json
{"opportunity_id": "00000000-0000-4000-8000-000000000103", "text": "I can do this. Call me on 9876543210", "language": "en"}
```

```json
{"cover_text": "I can do this. I can start this week.",
 "improvements": [
   {"code": "remove_contact_details", "text": "Leave out phone numbers and e-mail; share them in the chat once connected."},
   {"code": "state_price", "text": "Give your price or rate."},
   {"code": "be_specific_to_this_work", "text": "Refer to this particular work, not a general message."}],
 "bid": {"min_paise": 6000000, "median_paise": 6000000, "max_paise": 6000000, "sample_size": 0, "basis": "poster_budget",
         "poster_min_paise": 6000000, "poster_max_paise": 6000000, "market_min_paise": null, "market_max_paise": null,
         "note": {"code": "poster_budget", "text": "Based on the budget the poster stated: ₹60,000."}},
 "source": "rules", "language": "en"}
```

**Bid rule (revised 2026-09-29 after FE1).**
- **Never below the poster.** A suggested bid is never below the range the poster stated. The poster's range comes from, in order:
  - the typed `budget_min/max_paise`;
  - `hourly_rate_min/max_paise` for hourly work;
  - `budget_paise`;
  - the legacy `value_amount`.

  A single figure is a range of one.
- **Similar work compared.** The 25th, 50th and 75th percentiles of similar work are computed, then held inside that range.
- **Always explained.** `note` says what happened, localized, with both ranges written as ₹ amounts in Indian digit grouping:

| `note.code` | When | Example (en) |
|---|---|---|
| `market` | similar work falls inside the poster's range (or the poster stated none) | "Based on 4 similar opportunities (₹45,000–₹55,000)." |
| `clamped_to_poster_budget` | similar work usually pays less; the suggestion is raised to the poster's floor | "Similar work usually goes for ₹20,000–₹50,000, but this poster has offered ₹40,000–₹60,000 — so the suggestion stays within their budget." |
| `market_above_poster_budget` | similar work usually pays more; the suggestion is held at the poster's ceiling | "Similar work usually pays ₹70,000–₹90,000, more than this poster's budget of ₹40,000–₹60,000. The suggestion stays at their budget; if the work needs more, say why in your message." |
| `poster_budget` | too little similar work; the poster's own range | "Based on the budget the poster stated: ₹60,000." |
| `none` | nothing to go on | "No budget was given and there is too little similar work to compare — quote what the work is worth to you." |

`poster_min_paise` / `poster_max_paise` and `market_min_paise` / `market_max_paise` (the market figures before clamping) are returned, so the UI can show both. The rule lives in one function, `suggest_bid()`, so the Claude path uses it too.

With `"text": ""` the rules engine writes a complete cover text in the requested language, for example `"Namaste, I would like to apply for \"3D visualiser for two villa projects\". I can start this week. Please let me know a good time to talk."`.

The response has these rules:
- **Cover text claims.** It mentions only skills from the applicant's own listing that this work asks for, and years of experience only when those skills match. It never includes contact details.
- **Bid `basis`:**
  - `capability_overlap` or `same_type`: the 25th/50th/75th percentiles of `value_amount` across at least 3 similar opportunities the caller can see, held inside the poster's range.
  - `poster_budget`: not enough similar opportunities, so the poster's own stated range is used.
  - `none`: there is nothing to go on.

  See the bid rule and the `note` codes above.
- **Improvement codes:** `mention_matching_skills mention_experience state_availability state_price answer_screening_questions keep_it_short remove_contact_details be_specific_to_this_work polite_opening clear_next_step`. From the rules engine they describe what the suggested text still lacks.

Errors:
- `404 opportunity_not_found`
- `422 text_too_long`
- `429 ai_limit_reached`

### Error codes (all localized en/hi/te under `ai.error.*`)

`ai_limit_reached` (429), `text_too_long` (422), `unsupported_without_ai` (501), `unavailable` (503), `poster_only` (403), `image_not_found` (422), `image_too_large` (413), `image_required` (422), `pdf_needs_upload` (422), `draft_or_opportunity_required` (422). The shared codes `opportunity_not_found` (404) and `validation_error` (422) also apply.

### Audit table `vyapar_integration.ai_events` (migration 020)

Columns: `id, member_id, kind (draft|read_image|shortlist|tips|proposal), provider (anthropic|rules), model, input_hash (sha256), latency_ms, tokens_in, tokens_out, outcome (ok|fallback|unsupported_without_ai|refused|unreachable|rate_limited|api_error|bad_json|error), credential_id, created_at`.

Access rules:
- **Read:** the member themselves, and operators with the `analytics` permission (RLS).
- **Runtime role:** `vyapar_app` may only `SELECT` and `INSERT`, so the rows cannot be changed.
- **Resilience:** the audit row is written on its own connection, so it survives a request that then fails.

## Update 2026-09-29: five rules-reader bugs found by FE1 in the browser, fixed

| # | FE1 report | Cause | Fix (rules reader, and Claude validation where it applies) |
|---|---|---|---|
| 1 | "React dashboard" project text classified as local service (with other wording, employment) | Type detection had no software-deliverable signals, and generic words ("need a", "chahiye", "కావాలి", "urgent") counted as strong local-service signals | Software and creative deliverables (dashboard, website, app, React, Flutter, API, logo, SEO …) are strong freelance signals. Generic "I need" words are only weak local-service hints. Hiring words for workers ("boys", "बॉय", "బాయ్స్") count towards employment. Claude reads the type by meaning. |
| 2 | "sales" picked up as a skill from "sales charts" | Skills were matched as bare substrings | A mention counts only in a skill sense: it is ignored when followed by a data word (charts, report, data, analytics, status, trends …) or preceded by a verb such as show, track or monitor. "React dashboard" still yields `react`, because the dashboard is what gets built. **Claude:** a skill whose every literal mention is data-only is dropped from Claude's answer too (`capability_mentioned_only_as_data`). A skill Claude maps by meaning, with no literal mention, is kept. |
| 3 | Titles cut at the first colon | A label line ("Job opening:", "Urgent:") was taken as the title | `strip_title_label()` (in `vocab.py`) removes only known label words in en, hi and te before a colon or dash. A label on its own line takes the title from the next line. A place heading ("Kukatpally: …") is kept. **Claude:** the same function is applied to Claude's title in `clean_draft`. |
| 4 | Devanagari place names not recognised; "X nundi Y varaku" and "X se Y tak" not parsed as ranges | Places were matched only as Latin words after "in/at", or Devanagari followed by में. `nundi`, `nunchi`, `tak`, `varaku` and `వేల` were missing from the range grammar. | New location patterns, tried in order: an explicit label in any script (`स्थान:`, `ప్రాంతం:`, `Location:`); a Devanagari or Telugu name after "in/at/mein/lo"; a name next to Hyderabad or Secunderabad in any script; a place heading the notice. Stop words cover non-places such as घर and ఇంట్. Ranges accept `se/से/nundi/nunchi/నుండి/నుంచి … tak/तक/varaku/వరకు` and `వేల`, in both the salary and the experience grammar. |
| 5 | The improve-proposal bid range came out below the poster's own budget | A single stated budget of ₹60,000 produced a suggested minimum of ₹48,000 (80%), and similar-work percentiles were never compared with the poster's range | `suggest_bid()` holds every suggestion inside the poster's stated range and always returns a localized `note` explaining it (see the bid rule above). The endpoint uses the same function whether Claude or the rules engine answers. |

`check_ai.py` gains 15 FE1 cases, all through the live API except two direct calls to `suggest_bid()`:
- **Bug 1:** "React dashboard", long and short wording, is freelance; a home repair stays a local service.
- **Bug 2:** "sales charts" adds no sales skill, while React stays; "sales executive" does add it.
- **Bug 3:** a label before a colon is dropped; a label on its own line takes the title from the next line.
- **Bug 4:** a Devanagari place inside English; `स्थान:` with `12 से 15 हज़ार तक`; `nundi … varaku`; `se … tak`.
- **Bug 5:** the live bid is never below the poster's minimum and carries a Hindi note; similar work that pays less is raised with a reason; similar work that pays more is held with a reason.

They run as a separate persona (Rahul Chadha), who is included in the cleanup.

## Verification

- **2026-09-29: `scripts/check_ai.py` 59/59 passed** (44 earlier plus 15 FE1 cases). It ran on the private port 8021 with `AI_PROVIDER=rules AI_DAILY_LIMIT=15`, and the instance was stopped by its own PID. Cleanup removed all 38 `ai_events` rows the run created and restored 6 rate-limit counters. The dev DB still holds a few `ai_events` rows and counters dated 2026-09-28 from other sessions' browser testing on the live service. They were left untouched.
- **Earlier run: `scripts/check_ai.py`: 44/44 passed** against a private uvicorn on port 8021, run with `AI_PROVIDER=rules AI_DAILY_LIMIT=15`. It covered:
  - drafts in en/hi/te/Hinglish, including freelance;
  - phone numbers dropped from drafts;
  - validation errors;
  - photo reading answering `501` in Hindi, plus path traversal and missing-upload refusals;
  - the shortlist: scores, Telugu labels, order, the skill guard (Priya, a software developer applying to architecture work, scores at most 3 and shows why), `403` for a non-poster, empty with no applicants, `404` on a bad id;
  - tips from a draft and from an opportunity, Hindi text, and `403` / `422`;
  - proposals: contact details removed, no unrelated experience claimed, no hints repeating what the text already says, a bid range, and a Telugu cover text;
  - the cap answering `429 ai_limit_reached` in Telugu at exactly 15;
  - one audit row per call with a hash and no text column;
  - the five `operation_id`s present in OpenAPI.
- **Cleanup.** The check uses seed personas only, never the owner's account, and is read-only on business data. On exit it deleted its `ai_events` rows and restored the AI rate-limit counters. A post-run count showed 0 `ai_events` rows and 0 `ai:*` counters. The instance was stopped by its own PID.
- **Offline test of `AnthropicProvider`** with a fake SDK client:
  - the request uses `claude-sonnet-5`, a strict JSON schema, `effort: low`, the Hindi instruction and the voice note;
  - the phone number and e-mail are redacted before sending;
  - hostile answers are cleaned: an invented type becomes the default, and an invented slug, asset, enum or code is dropped;
  - rupees become paise and a swapped salary range is reordered;
  - a score of 42 is clamped to 10, and an unknown reference is ignored;
  - `stop_reason: refusal` falls back to the rules engine.
- **`python -c "import app.main"` passes.**

## Bugs found and fixed while testing (read as a poster or applicant would)

1. **Rules shortlist.** A nearby, verified developer scored 6/10 for architecture work she has no skill for, with "has the experience asked for" as a reason. Experience now counts only in a matching trade, and no overlap with the required skills caps the score at 3. The same guard is applied to Claude's scores.
2. **Rules cover text.** It had the applicant claim "8 years of experience in this" and list unrelated skills. It now claims only matching skills and years.
3. **Bid range mislabel.** The bid range was labelled `same_type` with a sample of 1, but it was really the poster's own budget. It is now labelled `poster_budget` and uses the typed budget.
4. **Contact details left in text.** Drafts and cover texts kept the poster's phone number and left fragments such as "Call me" or "for details". Both are now removed cleanly.
5. **Keyword misreadings:**
   - Hindi salary ranges (`12000 से 15000`) were read as job timings. Timings now need a clock marker.
   - A Latin place name followed by में / లో / "mein" was not recognised as a location.
   - Whole paragraphs became titles. The title is now the first sentence, cut at a comma when long.
   - The location grabbed "Kukatpally. Salary" across a sentence break.
6. **Migration 018 alignment.** `screening_questions` is `[{id, text}]` jsonb, and it would have crashed the proposal rules. The shortlist also compared bids with the legacy `value_amount` instead of the typed budget. Both are fixed.

## Backlog / follow-ups (not done here, by ownership or because blocked)

- **No Anthropic key exists** in the environment or in any module `.env`, so no real Claude call has been made. The Claude path is proven offline only. When a key is added (`AI_PROVIDER=anthropic`, `ANTHROPIC_API_KEY=…`), run `check_ai.py` again (drafts will then say `source: ai`) and try one real photo through `readOpportunityImage`.
- **Access tokens (workstream B owns `app/integrations/identity/scopes.py`).** `POST /v1/ai/*` is not in `WRITE_SCOPE_BY_PREFIX`, so an agent using a personal access token gets `403 not_available_to_tokens` on the four POST routes. `GET …/ai-shortlist` already works with the `read` scope. The AI POSTs write nothing, so the fix is one line: `("/v1/ai", ("read",))`.
- **`vyapar-mcp/`** (out of scope for this workstream): expose `draftOpportunity`, `getAiShortlist`, `getPostingTips` and `improveProposal` as MCP tools once the scope line above exists.
- **`vyapar-web/`** (out of scope):
  - an "Describe it / Speak it" composer that fills the form from `draftOpportunity` and asks `questions[]`;
  - a "Read a photo" button that appears only when `readOpportunityImage` does not answer `501`;
  - a "Best matches" sort on the applicant list;
  - tips beside the composer;
  - "Improve my message" in the apply sheet.
- **`vyapar-service/openapi.json`** was not regenerated, because it is a shared file. The live `/openapi.json` already lists the five operations.
- **Refusal fallback.** The default model is Claude Sonnet 5, which does not need the server-side refusal fallback. If `VYAPAR_AI_MODEL` is moved to `claude-opus-5` or a Fable model, add `fallbacks` as the Mangaly reader does. A refusal already falls back to the rules engine here.

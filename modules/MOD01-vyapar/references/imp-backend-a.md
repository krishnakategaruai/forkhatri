# IMP (backend workstream A): structured opportunities, structured applications, applicant pipeline, two-level taxonomy (2026-09-28)

This entry covers four changes, built through the service layer and exposed in the REST API.
1. **Typed fields for each opportunity type.** A job has salary, shift and qualification; a project has budget, duration and screening questions; a local service has a date, a budget and urgency. The service also returns posting suggestions.
2. **Structured applications and proposals.** A proposal carries a bid, a timeline, milestones and screening answers. A job application can be one tap with a profile snapshot.
3. **A hiring pipeline for the poster.** The poster can list, compare, shortlist, hire and decline applicants.
4. **A two-level taxonomy.** Categories hold skills and roles. It now covers the blue-collar roles WorkIndia's audience searches for, with a one-line description in every language.

Every existing route, field and screen behaves as before. The new fields are additive.

## Files

| Area | File |
|---|---|
| Migration | `07a-db-implementation/migrations/018-structured-opportunities.sql`: new columns, index, stage-event trigger, taxonomy data (idempotent). Applied to the dev DB as `vyapar_owner` with `psql -v ON_ERROR_STOP=1 -f`, twice, to prove it is idempotent. |
| Schema/seeds | `schema.sql` has the same columns. `seeds.sql` re-applies migration 018's taxonomy data with `\ir` so a fresh seed carries the same tree. |
| Services | `app/services/opportunities.py` (structured fields, validation, derived compensation, publish gate, suggestions). `app/services/enquiries.py` (structured proposals, one tap, profile snapshot, stored action type). New `app/services/applicants.py` (list, compare, stage). New `app/services/taxonomy.py` (tree). `app/services/first_run.py` (the hard-coded category scope and descriptions are replaced by the DB tree; function signatures unchanged). |
| Cache | `app/taxonomy_cache.py` also caches kind, parent and description (`categories()`, `children_of()`, `term_for()`, `description_for()`). `label_for`/`labels_for` are unchanged. |
| Routers | `app/routers/opportunities.py` gains 4 routes. New `app/routers/taxonomy.py` is registered in `main.py`. |
| i18n | en/hi/te: `opportunities.error.*`, `opportunities.compensation.*`, `opportunities.suggestion.*`, `enquiries.error.*`, `enquiries.oneTap.*`, `notifications.applicantHired`, `notifications.applicantDeclined` (merged into the catalogs without replacing other workstreams' keys). |
| Hooks | Workstream B's `app/services/hooks.py` is wired into the opportunities and enquiries services (section 5). |
| Check | `vyapar-service/scripts/check_structured_hiring.py`: **97/97 passed** on a private port (8018). That includes 9 hook checks and the shortlist-calling and skills-verdict cases (sections 6 and 7). Everything it created was deleted, the daily enquiry counters were restored, and a sweep over every `vyapar_*` table found no leftover row. |
| OpenAPI | `vyapar-service/openapi.json` regenerated: 216 operations, all ids unique. |

## Bug found and fixed on the way

`enquiries._resolve_action_type` stored `opportunities.TYPE_ACTION_LABEL[type]` as the enquiry's `action_type`. Since the i18n pass those values are button-label keys (`submitProposal`, `enquireNow`). The column's CHECK allows only `enquire|apply|propose|contact|register`, so **every response to a freelance or local-service opportunity failed on insert**; only employment (`apply`) worked.

The stored action type now has its own mapping, `ACTION_TYPE_BY_OPPORTUNITY_TYPE`:

| Opportunity type | Stored `action_type` |
|---|---|
| freelance | `propose` |
| local_service | `enquire` |
| employment | `apply` |
| partnership | `contact` |
| training, community | `register` |

`TYPE_ACTION_LABEL` stays the display label. The check script covers this case.

## Conventions

- **Money** is always an integer number of **paise** (`₹18,000` = `1800000`). Salaries are monthly and in-hand.
- **Language** comes from `X-Vyapar-Language: en|hi|te` (or `Accept-Language`).
- **Errors** use the standard envelope: `{"detail": ..., "error": {"code", "message", "details"}}`. The `code` values listed below are stable.
- **Auth:** send the member session as usual; the dev API also accepts `X-Dev-Member-Id`. Agent tokens need `read` for GET and `opportunities:write` for the POST routes under `/v1/opportunities`.

---

## 1. Structured opportunity fields

### Request: `createOpportunity` `POST /v1/opportunities` and `updateOpportunity` `PATCH /v1/opportunities/{id}`

Both take an optional `structured` object beside the existing fields. On create, only the fields for the opportunity's `type` are accepted. On PATCH the object is **partial**: fields you send replace the stored ones and the rest stay. Changing `type` drops the old type's fields.

| Type | Field | Values |
|---|---|---|
| employment | `salary_min_paise`, `salary_max_paise` | int ≥ 0 (monthly, in-hand) |
| | `incentive_type` | `none` \| `fixed_plus_incentive` \| `incentive_only` |
| | `incentive_max_paise` | int ≥ 0 (ignored when `incentive_type` is `none` or null) |
| | `openings` | 1–1000 |
| | `shift` | `day` \| `night` \| `rotational` \| `flexible` |
| | `job_timings` | text ≤ 200 |
| | `interview_details` | text ≤ 500 |
| | `min_qualification` | `below_10th` \| `10th` \| `12th` \| `diploma` \| `iti` \| `graduate` \| `postgraduate` \| `any` |
| | `english_level` | `none` \| `basic` \| `good` \| `fluent` |
| | `experience_min_months`, `experience_max_months` | 0–600 |
| | `requires_assets` | string[] ≤ 10, lower-cased and de-duplicated (`bike`, `smartphone`, `laptop`, …) |
| freelance | `budget_type` | `fixed` \| `hourly` (inferred from the amounts when omitted) |
| | `budget_min_paise`, `budget_max_paise` | int ≥ 0 (fixed) |
| | `hourly_rate_min_paise`, `hourly_rate_max_paise` | int ≥ 0 (hourly) |
| | `duration` | `under_1_week` \| `1_4_weeks` \| `1_3_months` \| `3_6_months` \| `over_6_months` \| `ongoing` |
| | `experience_level` | `entry` \| `intermediate` \| `expert` |
| | `screening_questions` | `[{id?, text}]`, at most 5; `id` is assigned `q1`, `q2`… when omitted |
| local_service | `preferred_date` | `YYYY-MM-DD` |
| | `budget_paise` | int ≥ 0 |
| | `urgency` | `today` \| `this_week` \| `flexible` |

```json
POST /v1/opportunities
{
  "title": "Kitchen helper and baker for catering unit",
  "type": "employment",
  "description": "Help our catering kitchen in Secunderabad with prep and daily baking for wedding orders.",
  "location": "Secunderabad", "work_mode": "on_site",
  "required_capabilities": ["bakery", "catering"],
  "response_method": "in_app", "source_segment": "community",
  "structured": {
    "salary_min_paise": 1800000, "salary_max_paise": 2400000,
    "incentive_type": "fixed_plus_incentive", "incentive_max_paise": 300000,
    "openings": 2, "shift": "day", "job_timings": "7 am to 4 pm, Sunday off",
    "interview_details": "Walk in at our Secunderabad kitchen, 11 am to 1 pm",
    "min_qualification": "10th", "english_level": "basic",
    "experience_min_months": 12, "requires_assets": ["smartphone"]
  }
}
```

### Response: every `OpportunityOut` (create, get, patch, publish, mine, similar, feed cards…)

`OpportunityOut` gains two fields:
- `structured`: every field is present; fields belonging to other types are `null`, `[]` for `requires_assets`/`screening_questions`.
- `compensation_label`: the money line in the caller's language, falling back to the free-text `compensation`.

`compensation` itself is kept in sync as the derived line, in the language the post was written in, so old clients still show pay.

```json
{
  "id": "…", "type": "employment", "state": "active",
  "compensation": "₹18,000 to ₹24,000 a month + incentives up to ₹3,000",
  "compensation_label": "₹18,000 से ₹24,000 प्रति माह + ₹3,000 तक इंसेंटिव",
  "structured": {
    "salary_min_paise": 1800000, "salary_max_paise": 2400000,
    "incentive_type": "fixed_plus_incentive", "incentive_max_paise": 300000,
    "openings": 2, "shift": "day", "job_timings": "7 am to 4 pm, Sunday off",
    "interview_details": "Walk in at our Secunderabad kitchen, 11 am to 1 pm",
    "min_qualification": "10th", "english_level": "basic",
    "experience_min_months": 12, "experience_max_months": null, "requires_assets": ["smartphone"],
    "budget_type": null, "budget_min_paise": null, "budget_max_paise": null,
    "hourly_rate_min_paise": null, "hourly_rate_max_paise": null, "duration": null,
    "experience_level": null, "screening_questions": [],
    "preferred_date": null, "budget_paise": null, "urgency": null
  }
}
```

How the money line reads, in English:

| Type | Label |
|---|---|
| Job | "₹18,000 a month", or "₹18,000 to ₹24,000 a month" |
| Job, incentives on top | the salary line + "+ incentives up to ₹3,000" or "+ incentives" |
| Job, incentives only | "Incentives only, up to …" |
| Fixed-price project | "Fixed price ₹40,000 to ₹60,000" |
| Hourly project | "₹500 an hour", or "₹400 to ₹600 an hour" |
| Local service | "Budget ₹1,500" |

Hindi and Telugu have the same forms.

### Validation errors (422)

| Code | When |
|---|---|
| `structured_field_not_for_type` | A field of another type was sent. `details.field` and `details.opportunity_type` say which. |
| `salary_range_invalid` / `experience_range_invalid` / `budget_range_invalid` | min > max |
| `budget_fields_mismatch` | Both a fixed budget and an hourly rate were sent, or the amounts contradict `budget_type`. |
| `too_many_screening_questions` | More than 5 screening questions. |
| `validation_error` | Wrong enum value or type (standard). |

### Publish gate: `publishOpportunity` `POST /v1/opportunities/{id}/publish`

The existing rules still apply. In addition:

| Type | Needs | Otherwise |
|---|---|---|
| employment | both `salary_min_paise` and `salary_max_paise` | 422 `salary_required` |
| freelance | a budget or an hourly rate | 422 `budget_required` |

Local service has no money gate.

### `getOpportunitySuggestions` `GET /v1/opportunities/{id}/suggestions`

Poster only; anyone else gets 404 `opportunity_not_found`. Rule-based tips computed from what is missing or restrictive on the row, localized. Each tip names the field so the composer can focus it.

```json
{
  "opportunity_id": "…",
  "suggestions": [
    {"code": "lower_qualification", "field": "min_qualification", "impact": "more_responses",
     "message": "Lower the minimum qualification to 12th if the work allows it. You will likely get more responses."},
    {"code": "add_job_timings", "field": "job_timings", "impact": "better_fit",
     "message": "Add the job timings (for example 9 am to 6 pm), so people know if it suits them."}
  ]
}
```

`impact` is `more_responses` | `better_fit` | `trust`. The codes, by type:

| Applies to | Codes |
|---|---|
| All types | `expand_description`, `add_skills`, `fewer_skills` (more than 5), `add_location`, `consider_remote` (on-site job or project) |
| Employment | `add_salary`, `lower_qualification` (graduate or above), `relax_english` (good or fluent), `lower_experience` (more than 24 months), `add_job_timings`, `add_interview_details`, `add_openings`, `add_shift` |
| Freelance | `add_budget`, `add_duration`, `add_screening_question`, `relax_experience_level` (expert), `add_deadline` |
| Local service | `add_preferred_date`, `add_local_budget`, `add_urgency` |

A tip disappears once the poster acts on it.

---

## 2. Structured applications and proposals: `createEnquiry` `POST /v1/enquiries`

The body gains the fields below. The existing `Idempotency-Key`, the 20-a-day cap and the one-open-enquiry-per-target rule are unchanged.

| Field | Notes |
|---|---|
| `message` | Now optional in the schema (default `""`, ≤ 1000). The service still requires **20 characters** for every action except `apply`. An `apply` may be empty. |
| `bid_amount_paise`, `bid_type` (`fixed`\|`hourly`), `timeline_days` | `propose` only. Bid and timeline are **required** for a proposal. `bid_type` defaults to the project's `budget_type`, else `fixed`. |
| `milestones` | `[{title, amount_paise, due_days}]`, at most 10. `propose` + fixed only, and they must add up exactly to `bid_amount_paise`. |
| `screening_answers` | `[{question_id, answer}]`. Opportunity targets only. `question_id` must be one of the opportunity's questions. For `propose`, **every** question must be answered. |
| `applied_via` | `form` \| `one_tap` \| `voice` \| `agent`. Derived when omitted: an access token gives `agent`; an empty `apply` message gives `one_tap`; anything else gives `form`. |

The action is resolved on the server from the target's type (see the bug fix above): employment gives `apply`, freelance `propose`, local service `enquire`.

**One tap.** `{"opportunity_id": "…", "message": ""}` on a job. The service stores `profile_snapshot` and writes the first thread message from it in the sender's language, for example: "Hello, I'd like to apply. Weekend baking workshops for beginners. I have 5 years of experience. I'm based in Himayatnagar."

**Profile snapshot.** `profile_snapshot` is stored for **every** opportunity response. It is taken from the sender's most recent non-archived listing (a professional profile first) and member row. A later profile edit never changes what the poster saw.

```json
POST /v1/enquiries
{
  "opportunity_id": "…",
  "message": "I keep books for four wholesale traders in Begum Bazaar and file their GST every month.",
  "bid_amount_paise": 4500000, "timeline_days": 90,
  "milestones": [
    {"title": "Books set up in Tally", "amount_paise": 1500000, "due_days": 15},
    {"title": "Three months of GST returns", "amount_paise": 3000000, "due_days": 90}
  ],
  "screening_answers": [{"question_id": "q1", "answer": "Yes, monthly GSTR-1 and GSTR-3B for four wholesale shops."}]
}
```

`EnquiryOut` (create, get, mine, mine/page) gains these fields:

```json
{
  "action_type": "propose", "state": "open",
  "stage": "new", "stage_changed_at": null,
  "bid_amount_paise": 4500000, "bid_type": "fixed", "timeline_days": 90,
  "milestones": [{"title": "Books set up in Tally", "amount_paise": 1500000, "due_days": 15}, {"…": "…"}],
  "screening_answers": [{"question_id": "q1", "answer": "Yes, …"}],
  "applied_via": "form",
  "profile_snapshot": {
    "name": "Anita Khatri", "headline": "Chartered Accountants for small businesses", "experience_years": 12,
    "capabilities": ["accounting", "gst_filing", "tax"], "locality": "Banjara Hills",
    "languages": ["en", "hi"], "availability": "this_week",
    "listing_id": "…", "listing_kind": "business"
  }
}
```

The errors, all 422 except the last:

| Code | When |
|---|---|
| `message_too_short` | The message is shorter than 20 characters (every action except `apply`). |
| `proposal_fields_not_allowed` | A bid, timeline or milestones on anything that is not a proposal. |
| `bid_required` | A proposal without a bid and a timeline. |
| `milestones_hourly` | Milestones on an hourly proposal. |
| `milestones_total` | The milestones don't add up to the bid. |
| `unknown_screening_question` | An answer to a question the opportunity doesn't ask (`details.question_ids`). |
| `screening_answers_required` | A proposal with a screening question unanswered (`details.question_ids`). |
| `screening_answers_not_allowed` | Screening answers on a listing enquiry. |
| **409** `already_declined` | The sender was already declined on this opportunity. |

---

## 3. Applicant pipeline (poster only)

`stage` (`new` → `shortlisted` → `hired` | `declined`) is separate from the thread `state`. `hired` and `declined` are final.
- **Hiring** calls the existing `acceptEnquiry` path (thread `open`/`awaiting_response` → `in_progress`). Contact disclosure then follows its existing rule.
- **Declining** closes an open thread (`state_reason: "declined"`). It sends the applicant an in-app notification in their own language (`applicantDeclined`); the poster types nothing.
- **Hiring** also notifies the applicant (`applicantHired`).
- The migration-018 trigger writes **`applicant.shortlisted` / `applicant.hired` / `applicant.declined`** to `vyapar_enquiries.outbox_event` in the same transaction. The payload is `{id, sender_id, provider_id, opportunity_id, stage, previous_stage, thread_state, audience}`, and webhooks fan out from it as for other events.

A caller who is not the poster, including an applicant, gets 404 `opportunity_not_found`. Withdrawn applications and those from blocked senders (not delivered) are never listed.

### `listOpportunityApplicants` `GET /v1/opportunities/{id}/applicants`

| Query parameter | Values |
|---|---|
| `stage` | optional: `new` \| `shortlisted` \| `hired` \| `declined` |
| `sort` | `newest` (default) \| `match` |
| `limit` | 1–100, default 20 |
| `cursor` | from `next_cursor` |

```json
{
  "items": [{
    "enquiry_id": "…", "sender_id": "m_meena", "name": "Meena Sahni",
    "profile": {"name": "Meena Sahni", "headline": "Weekend baking workshops for beginners", "experience_years": 5,
                "capabilities": ["bakery", "tutoring", "cakes"], "capability_labels": ["Baking", "Tutoring", "Custom cakes"],
                "locality": "Himayatnagar", "languages": ["en", "hi"], "availability": "this_week",
                "listing_id": "…", "listing_kind": "professional"},
    "action_type": "apply", "applied_via": "one_tap",
    "stage": "new", "stage_changed_at": null, "thread_state": "open",
    "bid_amount_paise": null, "bid_type": null, "timeline_days": null, "milestones": [],
    "screening_answers": [],
    "message_preview": "Hello, I'd like to apply. …",
    "created_at": "2026-09-28T10:12:03+05:30",
    "match_score": 54,
    "match_signals": ["capability_fit", "experience_fit", "timing_fit"],
    "match_reasons": ["matches your capabilities", "matches your experience", "good timing for you"],
    "matched_capability_labels": ["Baking"], "missing_capability_labels": ["Catering"]
  }],
  "next_cursor": null,
  "total": 2,
  "stage_counts": {"new": 2, "shortlisted": 0, "hired": 0, "declined": 0}
}
```

- **`screening_answers`** items are `{question_id, question, answer}`, where `question` is the text the poster wrote.
- **`match_score`** runs 0–100. It is rule-based and uses only `app/ranking.py`'s allow-listed signals and weights: capability overlap with the required skills; location (a remote job, or the same locality); experience against `experience_min_months` or `experience_level`; availability; and, for a proposal, whether the bid is inside the budget. It never uses a sensitive attribute.
- **`total`** respects the `stage` filter; **`stage_counts`** does not.

### `compareApplicants` `GET /v1/opportunities/{id}/applicants/compare?ids=<enquiry_id>,<enquiry_id>[,…]`

Takes 2 to 4 ids and returns items in the requested order.

```json
{"opportunity_id": "…", "opportunity_title": "Kitchen helper and baker for catering unit",
 "required_capabilities": ["bakery", "catering"], "required_capability_labels": ["Baking", "Catering"],
 "items": [ApplicantOut, ApplicantOut]}
```

The errors are 422 `compare_count` (fewer than 2 or more than 4 ids) and 404 `applicant_not_found` (`details.enquiry_ids`).

### `setApplicantStage` `POST /v1/opportunities/{id}/applicants/{enquiry_id}/stage`

The body is `{"stage": "shortlisted" | "hired" | "declined" | "new"}`, and the call returns the updated `ApplicantOut`. Repeating the current stage is a no-op that returns 200.

| Error | When |
|---|---|
| 409 `stage_final` | The applicant is already hired or declined (`details.stage`). |
| 400 `applicant_not_available` | Hiring when the thread has already ended (closed, restricted or resolved). |
| 404 `applicant_not_found` | The enquiry is not on this opportunity, or the caller is not its poster. |

---

## 4. Taxonomy tree: `getTaxonomyTree` `GET /v1/taxonomy/tree`

Served from the in-process taxonomy cache (refreshed at startup, on admin edits and hourly), so no query per request. Categories and their children are sorted by the localized label.

```json
{
  "language": "te",
  "categories": [{
    "slug": "hospitality_housekeeping", "label": "ఆతిథ్యం & హౌస్‌కీపింగ్",
    "description": "వంట, శుభ్రత, భద్రత మరియు ఇంటి సహాయం", "icon": "cleaning_services",
    "children": [
      {"slug": "cook", "label": "వంటవారు", "description": "ఇళ్లు, హాస్టళ్లు, క్యాంటీన్లు లేదా రెస్టారెంట్లలో భోజనం తయారు చేస్తారు"},
      {"slug": "maid", "label": "ఇంటి పనిమనిషి", "description": "…"}
    ]
  }]
}
```

- **Size.** 22 categories and 57 skills/roles now. Every active capability has a parent, and every category has at least one child.
- **New categories:** `hospitality_housekeeping`, `sales_telecalling`, `office_admin`, `healthcare`, `manufacturing_labour`, `beauty_personal_care`.
- **Renamed category:** `logistics` is now "Drivers, Delivery & Logistics".
- **New roles:** `driver`, `cook`, `security_guard`, `housekeeping`, `maid` (Domestic help), `telecaller`, `field_sales`, `counter_sales`, `receptionist`, `office_assistant`, `data_entry`, `accountant`, `machine_operator`, `labourer`, `carpenter`, `painter`, `ac_technician`, `mechanic`, `beautician`, `nurse`, `lab_technician`, `teacher`, `graphic_designer`, `digital_marketer`.
- **Roles already in the taxonomy** are placed under a parent: delivery, tailoring, plumbing, electrical, tutoring, software, content_writing, video_editing, and the rest. Their names are kept; the new ones use the everyday word in each language (बढ़ई/వడ్రంగి, रसोइया/వంటవారు, मज़दूर/కూలీ).
- **First run.** `listScopedCapabilityOptions` and `listCategoryOptions` read the same tree and descriptions. `CATEGORY_CAPABILITY_SCOPE` and `CATEGORY_DESCRIPTIONS` are gone from `first_run.py`; the function signatures are unchanged.

---

## 5. Workstream B's hooks, wired in (`app/services/hooks.py`)

**"Nobody charges job seekers."** `createOpportunity`, `updateOpportunity` and `publishOpportunity` call `hooks.run_seeker_charge_checks` before anything is written. The check covers the record as it will be stored:
- the free text: title, description, requirements and compensation;
- the structured text fields a fee could hide in: `job_timings`, `interview_details` and the screening questions;
- the type, and a new request flag `candidate_pays`.

`candidate_pays` is optional on create and patch. It is not stored; `true` is refused.

A refusal is **422 `seeker_charge_not_allowed`**. The message is localized, and `details.field` is `text` or `candidate_pays` (plus `details.matched` for text). Before the frontend saves, it can use B's `POST /v1/opportunities/seeker-charge-check` to show the problem inline.

The old publish-time auto flag for advance-payment wording is still in place. It no longer fires, because such text is now refused before it is stored.

**Opportunity detail enrichers.** `getOpportunity` merges `hooks.run_opportunity_enrichers`, which adds two fields to `OpportunityOut`. Both are set only on the detail read.

```json
"seeker_protection": {"applies": true, "title": "Nobody charges job seekers",
  "body": "No fee, deposit or kit charge may be asked from applicants. Report if asked.",
  "report_reason": "asked_for_money", "report_label": "Report: asked me for money"},
"poster_badges": [{"key": "verified_business", "label": "…", "description": "…", "earned_at": "…"}]
```

`seeker_protection` is `null` for types other than employment. `poster_badges` is `[]` when the poster has none.

**Enquiry thread enricher.** `getEnquiry` merges `hooks.run_enquiry_enrichers`, which adds two fields to `EnquiryOut` (set on the thread read only). Both are `[]` until the enquiry is accepted; after that `contact_actions` has `call` and/or `whatsapp`.

```json
"contact_actions": [{"channel": "call", "label": "Call", "href": "tel:+91…", "available_now": true,
                     "next_window": null, "reason": null, "reason_label": null, "window": "mon-sat 09:00-18:00"},
                    {"channel": "whatsapp", "label": "WhatsApp", "href": "https://wa.me/…", "available_now": true, "…": "…"}],
"contact_attempts": [{"id": "…", "enquiry_id": "…", "caller_id": "…", "callee_id": "…", "channel": "call",
                      "at": "…", "mine": true, "summary": "You contacted … by Call on 28 Sep 2026, 14:05"}]
```

Recording a tap stays on B's `POST /v1/enquiries/{id}/contact-attempts`. The exact rules (hours, daily cap, `not_matching`) are in `references/imp-backend-b.md`.

The fields are plain objects in the OpenAPI schema. Importing B's models into these services would create an import cycle (trust_safety imports opportunities), so the shapes above are the contract.

**Checked live:**
- text fee, `candidate_pays: true` and a fee in `interview_details`: all refused;
- a legacy draft with a deposit: refused at publish;
- a job detail carries `seeker_protection` and `poster_badges` (`verified_business` for Kapoor Caterers);
- a project detail has none;
- a thread has no contact actions before hiring and `call` + `whatsapp` after.

---

## 6. Calling shortlisted applicants (critique L11, 2026-09-29)

WorkIndia and Apna let an employer call the people they shortlisted: a candidate consents to contact by applying. Vyapar now does the same. The rule is in `app/services/shortlist_contact.py`.

**When the poster moves an applicant to `shortlisted`:**
- The poster gets the applicant's Call and WhatsApp in the existing `ContactAction` shape.
- The applicant's call hours, daily cap and "matching only" setting do **not** apply. The applicant's channel switches (`call_ok`, `whatsapp_ok`) do.
- The number comes only from `contacts_for_viewer(listing, true)`, for a listing the applicant owns (the one in their snapshot, else their newest active listing).
- The actions appear in three places:
  - each row of `listOpportunityApplicants` and `compareApplicants`: `contact_actions` and `contact_revealed`;
  - the result of `setApplicantStage`;
  - the poster's `getEnquiry`: `contact_actions`.

**The applicant does not get the poster's number.** That happens only after hiring or acceptance (B's accepted-enquiry rule, with the poster's call hours), or through the post's own `allow_precall` switch (B's opportunity-level pre-call actions).

**The applicant is notified** in their own language: `applicantShortlisted`, e.g. "Shortlisted: {title}" / "{poster} shortlisted your application and may call you. Keep your phone handy." It is sent once per application.

**Hidden again** the moment the applicant leaves the shortlist, whether to `declined` or back to `new`: the very next read carries `contact_actions: []`. After `hired`, the row shows B's accepted-enquiry actions instead.

**Recorded.**
- Every grant (`applicant_contact_revealed`) and every hide (`applicant_contact_hidden`) is written to `vyapar_integration.audit_events`, with the actor, the enquiry and `{opportunity_id, applicant_id}`.
- Every tap is a `vyapar_enquiries.contact_attempts` row, which both sides see in the thread's `contact_attempts`.

New operation: **`recordApplicantContactAttempt`** `POST /v1/opportunities/{id}/applicants/{enquiry_id}/contact-attempts` `{"channel": "call" | "whatsapp"}`. It is poster only and returns 201 with the `ApplicantOut`.

| Error | When |
|---|---|
| 400 `not_revealed` | The applicant is not shortlisted or hired. |
| 400 `channel_off` | That channel is not offered right now. |
| 404 `applicant_not_found` | The enquiry is not on this opportunity, or the caller is not its poster. |

**Contact flags on the thread.** `getEnquiry` returns two flags; the names are the ones FE2's contact card already reads. Both are `null` outside the thread read.
- `can_contact_counterpart`: whether the viewer may reach the other side.
- `counterpart_can_contact`: whether the other side may reach the viewer.

| Situation | Poster sees | Applicant sees |
|---|---|---|
| Applied, not shortlisted | `false` / `false` | `false` / `false` |
| Shortlisted | `true` / `false` | `false` / `true` |
| Shortlisted, post has `allow_precall` | `true` / `true` | `true` / `true` |
| Hired or accepted | `true` / `true` | `true` / `true` |
| Declined | `false` / `false` | `false` / `false` |

For an enquiry on a listing (not an opportunity), both flags are `true` only once it is accepted.

## 7. One skills verdict, and `missing_skills` (2026-09-29)

The applicants board showed both "+ has the skills this needs" and "− only some of the required skills" for someone with 2 of 3 skills. The cause was the AI shortlist's rules provider, which listed the `capability_fit` reason whenever the overlap was at least 0.6, and also the partial-overlap risk.

**AI shortlist.** One guard in `app/integrations/ai/rules_provider.py`: a partial overlap is now only the `partial_capability_overlap` risk. `capability_fit` is a reason only when every required skill is present.

**`ApplicantOut`** (list, compare, stage, tap) now carries exactly one verdict, computed from the actual overlap:

```json
"skills_match": {"state": "some", "kind": "reason", "matched_count": 2, "required_count": 3,
                 "matched_skills": ["React / frontend", "Software development"], "missing_skills": ["Startup operations"],
                 "text": "Has 2 of 3 skills: React / frontend, Software development",
                 "missing_text": "Missing: Startup operations"},
"missing_skills": [{"slug": "startup", "label": "Startup operations"}],
"match_reasons": ["Has 2 of 3 skills: React / frontend, Software development", "Has the experience you asked for"],
"match_risks": []
```

How `state` maps to the text:

| `state` | `text` | `kind`, where it goes |
|---|---|---|
| `all` | "Has all N required skills" ("Has the required skill: X" when only one is required) | `reason`, first entry of `match_reasons` |
| `some` | "Has 2 of 3 skills: A, B" | `reason`, first entry of `match_reasons` |
| `none` | "None of the required skills" | `risk`, in `match_risks` |
| `not_required` | no skills line | none |

- `match_reasons` is now worded for the **poster**: "Lives near the work", "Has the experience you asked for", "Can start soon", "Bid is within your budget". Before, it reused the viewer-facing `ranking.signal.*` texts ("close to you", "matches your capabilities").
- `match_risks` also carries "Bid is above your budget".
- All of these are in en, hi and te under `enquiries.applicant.*`.
- For the missing chip, the UI should show `missing_text` or build its own "Missing: …" line from `missing_skills[].label`, never "No <skill>".
- `missing_capability_labels` stays for existing clients.

## Notes for the frontend

- The composer should send `structured` and stop writing free-text `compensation` for employment and freelance; the server derives it. Render `compensation_label`.
- For a job, the Apply button can send `{"opportunity_id", "message": ""}` for one tap. For a project, the proposal form needs a bid, a timeline and an answer to every screening question. Milestones are optional, but when sent they must add up to the bid.
- Poster screen:
  - tabs from `stage_counts`;
  - `sort=match` for "Best match";
  - per-row actions call `setApplicantStage`; after `hired`, open the thread with `/v1/enquiries/{enquiry_id}`, whose contacts follow the accept rule;
  - compare 2–4 applicants with `compareApplicants`.
- Suggestions: call `getOpportunitySuggestions` after each composer save and show `message` next to `field`.
- Opportunity detail: render `seeker_protection` (with its report action) and `poster_badges`. Thread: render `contact_actions` as the Call/WhatsApp buttons, and `contact_attempts` as the log.
- Composer: handle 422 `seeker_charge_not_allowed` next to `details.field`.
- Applicants board:
  - the skills line is `skills_match.text`, shown as a reason or a risk according to `kind`;
  - the missing chip is `skills_match.missing_text`;
  - a shortlisted row has `contact_actions` (Call / WhatsApp buttons); log each tap with `recordApplicantContactAttempt`.
- Contact card: `counterpart_can_contact` and `can_contact_counterpart` from `getEnquiry`.

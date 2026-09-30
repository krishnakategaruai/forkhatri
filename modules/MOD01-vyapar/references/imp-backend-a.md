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

## 8. Pay labels in the viewer's language, and paid work only in Discover's skill rows (2026-09-29)

**Pay labels.**
- `compensation_label` is rendered in the viewer's language everywhere an opportunity is returned. `listMyOpportunities` and the lifecycle routes (publish, pause, resume, close, renew, save, unsave, confirm) used to default to English; they now take the caller's language too.
- The terminology agent's yearly rule is kept. "₹9–14 LPA" and "6 lakh per annum" become "₹9–14 lakh a year (₹75,000–₹1,17,000 a month)" (`opportunities.compensation.yearlyLakh`); "LPA" is never output.
- Legacy free text with pay units now uses the `GLOSSARY.md` "Pay" wording in en/hi/te. The stored `compensation` is never rewritten.

| Stored text | en | hi | te |
|---|---|---|---|
| `₹250 per visit` | ₹250 a visit | ₹250 प्रति विज़िट | ఒక్కో విజిట్‌కు ₹250 |
| `from ₹300 per visit` | From ₹300 a visit | ₹300 प्रति विज़िट से शुरू | ఒక్కో విజిట్‌కు ₹300 నుండి |
| `₹700/day`, `700 per day` | ₹700 a day | ₹700 रोज़ | రోజుకు ₹700 |
| `₹800 per hour`, `₹15,000 per month`, `₹2k a week` | an hour / a month / a week, as above | प्रति घंटा / प्रति माह / प्रति सप्ताह | గంటకు / నెలకు / వారానికి |
| `Pay per visit` (also per day, per hour, per month) | Paid per visit | प्रति विज़िट भुगतान | ఒక్కో విజిట్‌కు చెల్లింపు |
| `Negotiable` | Pay negotiable | भुगतान पर बात हो सकती है | చెల్లింపు చర్చించుకోవచ్చు |
| Anything else (e.g. `Best in industry`) | stays as written | stays as written | stays as written |

The helpers are in `services/opportunities.py`: `legacy_compensation_label` and `_unit_pay_label`. The new keys are `opportunities.compensation.{daily, perVisit, weekly, startingFrom, negotiable, unitOnly.*}`.

**New fields on `OpportunityOut`** (every place it is returned, including feed cards), so a card can lead with the monthly figure:

```json
"pay_period": "year",               // month | year | week | day | visit | hour | fixed | budget | null
"pay_monthly_min_paise": 7500000,   // ₹75,000
"pay_monthly_max_paise": 11700000   // ₹1,17,000
```

- **Structured salary:** `pay_period` is `month`, and the monthly min/max are the stated salary, exact.
- **Yearly lakh text:** `year`, with the monthly min/max converted and rounded to ₹1,000, the same figures as the label.
- **Monthly unit or bare amount on a job:** `month` with that amount.
- **Other units:** `pay_period` is set (`hour`, `fixed`, `budget`, `day`, `visit`, `week`) and the monthly fields are `null`, because they are not salaries.
- **Unparseable text:** everything is `null`.

**Discover rows** (`listOpportunityRows`, in `services/feed.py`'s rows builder only).
- **The cause:** Priya's "Software & IT" row held the T-Hub startup grant and the Startup India seed fund. Both are `community` posts requiring `startup`, a skill I had placed under Software & IT in migration 018.
- **Fix, category rows:** a skill-category row now holds only paid work (`employment`, `freelance`, `local_service`) whose required skills overlap the category.
- **Fix, related work:** the same grants then surfaced in Near you as "related work" (a skill in the same trade). That tier now also counts only paid work, as the builder's own docstring intended ("a grant … never opens … Near you"). Grants still reach a member whose own skill they name (For you), and still appear in the generic rows.
- **Checked live:** for Priya, no community, programme or grant post appears in any category row or in Near you.

**Deployed:** the shared API on 127.0.0.1:8011 was restarted after `import app.main` passed. It serves the seeded "Pay per visit" post as "ఒక్కో విజిట్‌కు చెల్లింపు" in Telugu.

## 9. Critique Pass 5 fixes (CRITIQUE-2026-09-28.md; N2, N3, N5, N11, N12; 2026-09-29)

**N2: personal rows on sparse data** (`listOpportunityRows`)
- **The bug:** every persona got exactly one row, "Starting this week", because the 3-card minimum hid every personal row.
- **Personal rows show with a single card.** These are For you, the member's own skill-category rows and Near you. The 3-card minimum now applies only to the generic rows (pay band, New today, Starting this week, Projects, Work from home).
- **New fields on `RowsResponse`:**
  - `has_personal_rows: bool` is true only when at least one personal row is present. Show "picked for you" only then.
  - `viewer_categories: string[]` holds the member's own trade categories, most relevant first (skill overlap plus the categories on their listings). The trade rail can put them first.
- **Checked live:** Priya gets For you, `has_personal_rows: true` and `viewer_categories: ["software_it"]`. A member with no skills and no place gets `has_personal_rows: false`.

**N3: expired posts**
- A post whose `deadline` has passed is treated as Expired (GLOSSARY "Post past its date": Expired / समय-सीमा ख़त्म / గడువు ముగిసింది).
- **Never in the feed.** The one feed candidate query (`feed._candidates`) now requires `deadline IS NULL OR deadline >= now()`, which covers every row, section, result and saved-search match. Similar opportunities apply the same rule. "Starting this week" also requires `now <= deadline`.
- **Marked on reads.** `OpportunityOut.deadline_passed: bool` is true once the last date has passed, so the detail can show Expired.
- **Apply refused.** `createEnquiry` on an expired post returns **400 `opportunity_expired`**: "This post has expired. Its last date has passed, so it no longer takes applications." (en/hi/te).
- **Checked:** 8 past-deadline active posts in the dev data; none leaks into rows or results.

**N5: one-tap messages in the reader's language**
- **The bug:** a one-tap application message is generated by Vyapar, not written by the applicant. It was stored as text in the applicant's language, so Meena read Suresh's Telugu.
- **The fix:** migration 018 (re-applied, idempotent) adds `enquiry_messages.template_key` and `template_params`. A one-tap message is stored as `oneTap` plus `{headline, experience_years, locality}` from the snapshot. `body` keeps the sender-language rendering as a fallback.
- **Rendered per reader:** in the thread (`getEnquiry`, and the reply result), on the board (`message_preview`) and in compare. Existing one-tap messages were backfilled (1 row in dev).
- **Free text** is shown exactly as written.
- **New output fields:**
  - on each message: `message_language` (the language of `body` as served) and `templated` (true when Vyapar generated it);
  - on `ApplicantOut`: `message_language` and `message_templated`.

  The web can offer "Translate" when `message_language` differs from the viewer's.
- **Not changed:** no notification carries the message text. The AI shortlist still reads the stored `body` as cover text.

**N11: experience only in the matching trade**
- **The bug:** an electrician applying to a bakery job showed both "None of the required skills" and "Has the experience you asked for".
- **The fix mirrors the AI shortlist rule:** when none of the required skills match, `experience_fit` is 0.1 (0.3 if no experience is listed), so no experience reason appears. The applicant's `match_score` is also capped at 30.
- **Checked:** Ravi, a plumber, on the bakery job gets only "Can start soon", with a score of 28.

**N12: the glossary term "applicant"**
- **Seeker-protection notice:**
  - en: "Nobody may charge people who apply" / "No fee, deposit or kit charge may be asked from people who apply. Report if asked."
  - hi: "आवेदन करने वालों से …"
  - te: "అప్లై చేసినవారి నుండి …", replacing ఉద్యోగార్థులు / అభ్యర్థులు.
- **The same term** replaces "job seeker" and అభ్యర్థులు in: the Telugu `asked_for_money` report reason (trust_safety and admin console); the English admin label ("Asked an applicant for money"); the Telugu admin `seeker_charge` label; the Telugu `opportunityPausedSeekerCharge` notification; and my Telugu `relax_english` tip.
- **"Business existence verified (GST Certificate / GSTIN)" is not emitted by the server.**
  - The phrase is in the web catalog, `vyapar-web/locales/*/verification.json` → `status.verified`.
  - The server sends only the operator's `claim_scope` text.
  - The badge the server does emit (`verified_business`) already reads "Verified business owner".
  - **For the web workstream:** change `status.verified` to the glossary's "Business verified" (बिज़नेस वेरिफ़ाइड / బిజినెస్ వెరిఫైడ్).

**Deployed:** 8011 was restarted after `import app.main` passed.

## 10. Lifecycle: active → expired when the last date passes; renew brings it back (2026-09-29)

**The gap.** Section 9 hid past-deadline posts from the feed and refused applications, but their `state` stayed `active`. Seeded freelance posts 103 and 111 (deadlines 24 and 28 Sep) are examples.

**The pass.** `run_opportunity_expiry_pass` (in `services/opportunities.py`) moves every `active`, `paused` or `stale` post whose `deadline` has passed to **`expired`**, with `state_reason = 'deadline_passed'`.
- **When it runs:** from the hourly loop in `main.py`, beside the other lifecycle passes. For development there is also a trigger, **`runOpportunityExpiry`** `POST /v1/opportunities/jobs/expire`. It returns `{expired, notified}`, and outside `DEV_MODE` it answers 404 `dev_only`.
- **How it runs:** each post is expired in its own transaction, as its poster. That is the same RLS rule every poster update follows; no operator id is hardcoded. So the existing trigger writes the `opportunity.expired` domain event, and webhooks see it.
- **The poster is notified** in their language: `opportunityExpired`.
  - en: "Your post expired: {title}" / "Its last date has passed, so it no longer shows in Discover or takes applications. Renew it to bring it back."
  - hi: "आपकी पोस्ट की समय-सीमा ख़त्म हो गई: {title}" / "…इसे वापस लाने के लिए रिन्यू करें।"
  - te: "మీ పోస్ట్ గడువు ముగిసింది: {title}" / "…మళ్ళీ చూపించడానికి రిన్యూ చేయండి."
  - The link goes to the post.
- **Idempotent:** an expired post is never picked again, and the notification key includes the deadline date.
- **Effect on reads:** an expired post is readable only by its poster, under the existing visibility rule. Everyone else gets 404, as for any closed post.

**Renew** (`renewOpportunity` `POST /v1/opportunities/{id}/renew`). It now takes an optional body, `{"deadline": "<ISO date-time>"}`.
- **With a deadline:** it must be in the future, else 422 `deadline_in_past` ("Choose a last date in the future.").
- **Without a body, and the old deadline has passed:** the post gets its original posting window again, from publish to deadline, clamped to 7–30 days (14 when unknown).
- **Otherwise:** the deadline is left alone.
- Either way the post returns to `active`, `state_reason` is cleared, and applying works again. Without this, a renewed post would have stayed hidden and kept refusing applications.
- The existing 90-day rule (`too_old_to_renew`) is unchanged.

**Checked:**
- a post whose last date passed becomes `expired` / `deadline_passed`, with one notification and one `opportunity.expired` event;
- a second pass changes nothing;
- no active, paused or stale post is left past its date;
- renewing with a past date is refused;
- renewing without a body gives a date 14 days out, and an application then succeeds.

**On the dev DB:** the first run expired 8 seeded posts (103, 104, 105, 106, 111, 117, 118 and 122), and each poster got one notification. That is the same thing the hourly loop does on its own.

**Deployed:** 8011 was restarted after `import app.main` passed.

> *Sections 8–10 restored from the 29 Sep stash on 2026-09-30 (see restore-2026-09-30.md).*

## 11. One Vyapar profile per member (owner decision, 2026-09-30)

Owner, on Meena's hub showing "3 Profiles": "how do a person have 3 profiles … each user will get one profile." And on being asked for their name and locality again: "i already logged in as user, but still it is asking me this", "locality can be taken current right".

### Model (migration `026-one-profile-per-member.sql`)

- **The profile is the member's one live `vyapar_listings.listings` row.** Live means draft, submitted, active_unverified or active_verified.
- **Same table, same ids.** Verification records, reviews, packages, contacts, promotions, impressions, enquiries, partnerships, opportunities, campaigns, entitlements, workspace members, contracts, moderation cases, reports and saved rows all keep pointing at a valid id.
- **Enforced by the database:** `listings_one_profile_per_owner`, a unique index on `owner_id` over the live states.
- **Suspended listings** are moderation history. They are never merged into a live profile, and they do not count as "the profile".
- **The business is a section of the profile:** `business_name`, `business_headline` and `business_description` on the same row.
  - Business verification (GST/Udyam) stays on the row's `verification_state` and `verification_records`.
  - `kind` keeps its meaning for existing readers: `business` when a business section exists, else `professional`.
- **`name` is the person** (the identity display name). The search index covers both the person's name and the business name.
- **`ensure_member()`** now refreshes the display name and phone from the ForKhatri identity on every sign-in. Before, it only inserted, so the name and phone could go stale. The dev stub, which passes the id as the name, never overwrites real values.

### Consolidation (idempotent; dry run first)

The dry run is `SELECT * FROM vyapar_listings.profile_consolidation_plan();`. It is empty after the migration.

How the survivor is chosen, in order: verified or expiring first; then by state (active_verified, active_unverified, submitted, draft); then the most enquiries plus reviews; then the oldest.
- **Business section:** from the survivor if it is a business, else from the best merged business listing.
- **Person's headline, description and availability:** from a merged, non-draft professional listing.
- **Skills, categories, languages, services and evidence:** the union of all non-draft listings. The largest experience wins.
- **Every reference is re-pointed to the survivor:**
  - duplicate contacts are dropped;
  - package tiers: the survivor's own tier wins;
  - saved and viewed rows are merged;
  - an open enquiry that would duplicate another is closed (`state_reason = 'merged_duplicate'`), never dropped. None occurred.
- **Merged listings** become `archived`, with `state_reason = 'merged_into:<id>'`. `merged_from` on the survivor records what was folded in.

**What merged on the dev database:**

| Member | Profile (id) | Business section | Merged into it |
|---|---|---|---|
| m_meena | "Meena Sahni" (…0007, verified) | Meena's Oven | …0018 "Meena Sahni — Baking classes" (professional); …dab9 "ravi" (junk draft, contributed nothing) |
| m_sunita | "Sunita Kapoor" (…0003, verified) | Kapoor Caterers | …0014 "Kapoor Decor & Events" (verified business). Its name is kept in `merged_from`, its services folded in. |
| m_deepak | "Deepak Bhalla" (…0009, verified) | Bhalla Design Studio | …0017 "Deepak Bhalla — Vastu-aware planning" (professional) |
| m_vikram | "Vikram Sethi" (…0004) | Sethi Textiles | nothing. The suspended "Sethi Uniforms" (…0016) was not merged. |

Every other live profile was renamed to the member's name. A business listing's own name moved into its business section, e.g. "Anita Khatri · Khatri & Associates". Afterwards, no enquiry, review, package, contact, verification record or promotion points at a merged listing.

**Fresh databases.** `seeds.sql` drops the index before its (historical) listing inserts and re-applies migration 026 at the end, so a new database consolidates the same way.

### API

**`getMyProfile`** `GET /v1/me/profile`
- Returns the member's one profile.
- On first read it creates the profile from what the identity already knows: name, phone (as a contact shown after acceptance), language, plus locality and coordinates from the member row. A known locality supplies coordinates.
- If a required field is missing, nothing is created and `missing` says what to ask.

```json
{"exists": true,
 "profile": { "...every ListingOut field...": "", "id": "…0007", "name": "Meena Sahni",
              "has_business": true, "business_name": "Meena's Oven", "business_headline": "…",
              "business_description": "…", "card_title": "Meena Sahni · Meena's Oven", "kind": "business" },
 "prefill": {"name": "Meena Sahni", "phone": "+919000000008", "locality": "Himayatnagar", "lat": 17.402, "lng": 78.484, "language": "en"},
 "missing": [],
 "prefilled_from_identity": ["name", "phone", "language"]}
```

For a new member with no locality yet, `exists` is false, `profile` is null, `missing` is `["locality"]`, and `prefill` carries the name, phone and language. The web asks only for what is in `missing`.

**`updateMyProfile`** `PATCH /v1/me/profile`
- **Body:** every listing-patch field, plus `business: {name, headline?, description?}` or `remove_business: true`. Only the fields sent change.
- **Returns:** the same shape as `getMyProfile`.
- **First PATCH:** creates the profile when it doesn't exist yet. It needs a name (from the identity or the body) and a locality; otherwise 422 `profile_fields_missing` (`details.missing`).
- **A typed locality** is normalised to the known name ("KPHB" → "Kukatpally"). The member row learns it too, so no other screen asks again.
- **Refusals:**
  - 409 `business_verified_cannot_remove`: removing a verified business section.
  - 409 `profile_suspended`: changing a suspended profile.

**`locateMyProfile`** `POST /v1/me/profile/locate`
- Body `{"lat": 17.4021, "lng": 78.4846}` → `{"matched": true, "locality": "Himayatnagar", "lat": 17.4021, "lng": 78.4846, "distance_km": 0.06}`.
- The nearest known locality comes from the `app/geo.py` gazetteer, then from the places in Vyapar's own data (`vyapar_listings.nearest_locality`), within 15 km.
- Beyond 15 km it returns `{"matched": false, "locality": null, …}`, and the web asks the member to type a locality.
- It never saves anything: the client sends the result back in a PATCH.

**`createListing`** `POST /v1/listings`
- When the member already has any non-archived listing: 409 `profile_exists`, with `details.existing_listing_id` and `details.profile_id`.
- A concurrent second create is caught by the index and gives the same 409.

**Listing detail and search** keep the same ids. Every `ListingOut` now carries `has_business`, `business_name`, `business_headline`, `business_description` and `card_title` ("Meena Sahni · Meena's Oven", or just the name). Search matches the business name as strongly as the person's name.

**`listMyListings`** no longer lists listings merged into the profile. Other archived listings are still shown.

**Token scopes:** `GET /v1/me/profile` needs `read`; `PATCH` and `locate` need `listings:write` (added to `app/integrations/identity/scopes.py`).

**MCP:** new `get_my_profile` and `update_my_profile` (headline, description, capabilities, locality, availability, experience_years, business_name, business_headline). The old listing tools (`get_profile`, `search_profiles`, …) are unchanged.

**Errors** (en/hi/te, `listings.error.*`): `profile_exists`, `profile_fields_missing`, `profile_suspended`, `business_verified_cannot_remove`.

**Checked:** `vyapar-service/scripts/check_profile.py`, **26/26** on private port 8018. It cleans up after itself, restores the views it caused, and a sweep found no leftover rows. It covers:
- the one-profile constraint in the database;
- 409 `profile_exists` with the id;
- Meena's consolidated profile (person plus business, verification kept, skills folded in, two merged listings archived, one listing in her list, found by business name);
- prefill from identity, where only the locality is asked;
- locate, including a position far away;
- the first PATCH creating the profile with phone and language;
- adding and removing a business section;
- locality normalisation.

**Deployed:** 8011 was restarted after `import app.main` passed. `GET /v1/me/profile` as m_meena answers "Meena Sahni · Meena's Oven".

**Not changed, for the web account agent:**
- `/v1/members/me` still reports `profiles {business, professional}` by kind. For Meena, `business` is now the one profile and `professional` is null. Build the hub on `getMyProfile` instead.
- The hub's profile count should read one profile.

### 11b. Workspaces and verification after consolidation (2026-09-30, second pass)

**The bug.** Meena's "Business Workspace" listed three workspaces, one named "ravi". `listMyWorkspaces` returned every listing she owned, archived merged ones included.

**Workspaces** (`services/workspace.py`, plus migration 026 section 8, idempotent):
- **`listMyWorkspaces`** (`GET /v1/workspace/mine`) returns at most one owned workspace: the one on the member's profile. That is the live listing, or a suspended one only when no live one exists. It is named after the business when there is one ("Meena's Oven"). Workspaces the member was invited to are still listed (Priya: her own, plus Nanda Labs as operator). Archived listings, including merged ones, are never a workspace.
- **`getWorkspace`** (`GET /v1/workspace/{id}`) on a merged listing answers 404 `workspace_not_found` with `details.merged_into = <profile id>`, so the web can redirect to the profile's workspace. The workspace name is the business name when there is one.
- **Entitlements** (`listMyEntitlements`) are labelled with the business name.
- **Migration 026** already re-points entitlements, workspace members and campaigns from merged listings to the survivor. Section 8 then retires any duplicates that creates:
  - one open plan per workspace: the active one, or else the one that renews last, stays; the others become `cancelled`;
  - one seat per person per workspace: the active admin seat, or else the strongest, stays; the others become `expired`.
  - Rows are never deleted, so payments stay attached to their entitlement. On the dev database nothing needed retiring: the only plan is Shreya's, on Nanda Labs.

**Verification per section** (`ListingOut`, so profile, detail and search all carry it):
- `profile_status`: `draft` | `submitted` | `active` | `suspended` | `archived`. The person's card reads "Active", never "Active · Verified".
- `business_verified`: the business section is verified by a business document (GST, Udyam, PAN or shop licence). The "My business" section shows "Business verified" (GLOSSARY).
- `credential_verified`: the person is verified by a credential (degree, licence), from a `credential` document or a credential reference.
- Meena: `active`, `business_verified: true`, `credential_verified: false`. Priya: `active`, `credential_verified: true`, `business_verified: false`.
- `state` and `verification_state` are unchanged for existing clients.

**Checked:** `check_profile.py` **33/33** on private port 8018, adding:
- Meena has one workspace named "Meena's Oven";
- a merged listing's workspace answers 404 pointing at the profile;
- Vikram's suspended listing is not a second workspace;
- Priya keeps her invited workspace;
- at most one open plan per workspace;
- the verification flags for Meena and Priya.

`check_structured_hiring.py` **130/130** against the restored 29 Sep code. One check was adjusted: another workstream now renders the notification inbox in the reader's request language, so the check reads Ravi's inbox in Hindi.

**Deployed:** 8011 was healthy on the restore agent's restart (10:45). It was restarted after `import app.main` passed, to pick up this pass.

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
- Discover home:
  - show "picked for you" only when `has_personal_rows` is true;
  - order the trade rail by `viewer_categories`;
  - show Expired when `deadline_passed` is true, and handle 400 `opportunity_expired` on Apply;
  - offer "Translate" when a message's `message_language` differs from the viewer's.
- My posts: an `expired` post (`state_reason: deadline_passed`) shows Expired with a Renew button. `renewOpportunity` may send `{deadline}`.
- Pay: render `compensation_label` as sent; it is already in the viewer's language. When `pay_period` is `year`, lead with `pay_monthly_min_paise`.
- Profile (section 11):
  - build the hub on `getMyProfile`, and ask only for the fields in `missing`;
  - "use my location" calls `locateMyProfile`;
  - the card title is `card_title`;
  - the person's status comes from `profile_status`;
  - "Business verified" shows in the business section from `business_verified`, and a personal credential from `credential_verified`;
  - the workspace list is `listMyWorkspaces` (one owned workspace); a 404 carrying `merged_into` redirects to the profile's workspace.

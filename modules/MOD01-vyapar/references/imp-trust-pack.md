# IMP — Trust pack: scam shield, honest terms and "paid on time", close the loop, profession-aware profiles, council badges (2026-09-30)

VISION-2040 §5 "next 3 builds" #1: items 1–5 of the ranked list, backend and API. This file is the contract the web agent builds against.

## Conventions

- Language: `X-Vyapar-Language: en|hi|te`. Every message, label and explanation below is already in the reader's language.
- Errors: the standard envelope `{"detail": …, "error": {"code", "message", "details"}}`. The `code` values in this file are stable.
- Auth: the member session (dev: `X-Dev-Member-Id`). Token scopes are listed per route.
- Money is in paise. Dates are ISO 8601.
- GLOSSARY words throughout: post, applicant, "the person who posted", request, Verified, promotion. Enums never reach the screen; every enum below comes with its label.

## Files

| Area | File |
|---|---|
| Migration | `07a-db-implementation/migrations/028-trust-pack.sql` (idempotent, applied twice to the dev DB as `vyapar_owner`) |
| Services | new `app/services/{scam_shield,profession_rules,paid_on_time,close_loop,restrictions,credentials,trust_jobs}.py`; edited `trust_safety.py`, `opportunities.py`, `enquiries.py`, `applicants.py`, `packages.py`, `listings.py`, `profile.py`, `discovery.py`, `commercial.py`, `reviews.py`, `verification.py`, `admin_ops.py`, `app/reputation.py`, `app/identity_trust_stub.py`, `app/config.py`, `app/services/hooks.py` |
| Adapter | new `app/integrations/credentials/` (`CredentialRegistry`, `DevStubRegistry`) |
| Router | new `app/routers/trust_pack.py` (registered in `main.py`; the hourly loop also runs `run_trust_pass`) |
| Scopes | `app/integrations/identity/scopes.py` |
| i18n | en/hi/te: `trust_safety.scamShield.*`, `trust_safety.restriction.*`, `trust_safety.reasonCode.*` (10 new), `opportunities.error.payBasisRequired`, `opportunities.closeLoop.*`, `notifications.{applicantPostClosed,applicantPostFilled,applicantsWaiting,paidOnTimeAsk,councilCredentialExpired,promotionCancelledProfession}`, `listings.profession.*`, `listings.error.packagesNotPermittedForProfession`, `commercial.error.notPermittedForProfession`, `reviews.error.notPermittedForProfession`, `reputation.paidOnTime.*`, `verification.council.*` |
| MCP | 7 new tools in `vyapar-mcp` (see the last section) |
| Check | `vyapar-service/scripts/check_trust_pack.py` |
| Vendor blocker | Council and DigiLocker lookups, logged in `09a-external-dependencies.md` |

---

## 1. Scam shield on every text a poster writes

**Rules** (`app/services/scam_shield.py`). Each names who pays whom, so the honest "We pay ₹18,000 a month" is no longer refused (the old phrase list matched "pay ₹").

| `rule` | Catches (en / hi / te / Hinglish) |
|---|---|
| `fee_phrase` | a named charge on the applicant: registration fee, security deposit, kit / uniform charge, training fee, joining / processing / placement / interview / form fee, caution money; रजिस्ट्रेशन फीस, सिक्योरिटी डिपॉजिट, किट के पैसे; రిజిస్ట్రేషన్ ఫీజు, సెక్యూరిటీ డిపాజిట్ … |
| `applicant_pays` | "candidates must pay ₹2,000", "registration fees dena hoga", "pehle 500 rupay jama karo", "500 रुपये जमा करने होंगे", "₹2000 కట్టాలి" (a money amount must be written next to it, so "documents jama karo" passes) |
| `pay_before` | money before joining / the interview / starting |
| `phone_payment` | a phone number with "send / transfer ₹…" or "pay ₹… on GPay / PhonePe / UPI / to 98…" |
| `job_fee` | a charge for getting a job: placement fee, "pay and get a guaranteed job" |

**Where it runs.**

| Surface | Tier | Refusal `details.field` |
|---|---|---|
| Post create / patch / publish: title, description, requirements, pay text, job timings, interview details, screening questions, and a pasted share-mode text (`raw_input`) | jobs, projects, local services: every rule. Training, community, partnership: `job_fee` and `phone_payment` only (a course fee or a government form fee is legitimate there). | `text` (unchanged) or `candidate_pays` |
| The poster's reply in a thread on their own post (`POST /v1/enquiries/{id}/messages`) | as the post's type | `message` |
| A package (`PUT /v1/listings/{id}/packages`): name, descriptions, includes | `job_fee`, `phone_payment` (a service may have a price; a job may not) | `packages[0].description` … |

The applicant's own messages are not checked, so they can still ask about or report a fee. A business answering a price request on its profile is not checked either.

**Refusal: 422 `seeker_charge_not_allowed`.**
```json
{"detail": {"message": "Vyapar does not allow asking people who apply for any fee, deposit or charge. Remove it and try again.",
            "field": "text", "matched": "Registration fees", "rule": "fee_phrase", "surface": "opportunity", "type": "employment",
            "explanation": "It names a charge on the applicant (registration fee, security deposit, kit or uniform charge, training fee and the like). Real employers never charge the people they hire."},
 "error": {"code": "seeker_charge_not_allowed", "message": "Vyapar does not allow …",
           "details": {"field": "text", "matched": "Registration fees", "rule": "fee_phrase", "surface": "opportunity",
                       "explanation": "It names a charge …", "type": "employment", "i18n_key": "trust_safety.error.seekerChargeNotAllowed"}}}
```
Show `message`, then `explanation`, next to `details.field`; underline `details.matched`. The applicant-side notice ("Nobody may charge people who apply", with the report action) is unchanged (`seeker_protection`).

**Trust event.** Every refusal writes `vyapar_integration.audit_events` on its own connection (the refusal rolls the request back): `action = trust.seeker_charge_blocked`, `outcome = rejected`, `reason_code = <rule>`, `details = {surface, field, rule, matched (≤80 chars), type}`. The text itself is never stored.

**Pre-check (never raises, stores nothing):** `checkScamShield` `POST /v1/trust/scam-check` (token scope `read`). The existing `checkSeekerCharge` keeps working and now uses the same rules.
```json
// request
{"text": "Pehle 500 rupay jama karo, phir joining", "surface": "opportunity", "opportunity_type": "employment"}
// surface: opportunity | enquiry_reply | package
// response
{"allowed": false, "code": "seeker_charge_not_allowed", "message": "Vyapar does not allow …",
 "explanation": "It asks the applicant to pay or deposit money. On Vyapar, the person who posted pays; the person who works is never asked to pay.",
 "rule": "applicant_pays", "matched": "rupay jama karo"}
// clean text
{"allowed": true, "code": null, "message": null, "explanation": null, "rule": null, "matched": null}
```
Use it before sending a reply to an applicant and before saving a package, as the composer already does with `checkSeekerCharge`.

---

## 2. Honest terms and "paid on time"

### Pay on every post (verified, one gap closed)

- A **job** already needs a monthly in-hand salary range to publish (422 `salary_required`); a **project** needs a budget (422 `budget_required`).
- **New:** a **local service** needs a budget (`structured.budget_paise`) or a stated fee basis in `compensation` ("₹300 a visit", "Pay per visit"). Otherwise publishing is refused with **422 `pay_basis_required`** (`details.field = "structured.budget_paise"`), "Say what this job pays: add a budget, or how it is paid (for example ₹300 a visit)."

### "Paid on time", confirmed by the person who was paid

**Who is asked.** Only the payee, never the payer:
- every **released contract stage** (the provider is asked about the client);
- every **hire** after `PAID_ON_TIME_ASK_AFTER_HIRE_DAYS` (30) days (the hired applicant is asked about the person who posted), unless the thread has a contract, whose stages ask instead.

The hourly trust pass opens the question and sends one notification (`paidOnTimeAsk`, link `/paid-on-time/{ask_id}`): "Were you paid on time? {title}" / "One question, Yes or No. The person who paid never sees your answer; others see only the total once three people have answered."

**`listMyPaidOnTimeAsks`** `GET /v1/paid-on-time/asks?state=open|all` (default `open`; scope `read`)
```json
[{"id": "0b8…", "source_kind": "hire", "title": "Helpers for the wedding season, Kapoor Caterers",
  "payer_id": "m_sunita", "payer_name": "Sunita Kapoor",
  "question": "Were you paid on time for Helpers for the wedding season, Kapoor Caterers?",
  "asked_at": "2026-09-30T06:12:40+00:00", "answered": false, "answer": null, "answered_at": null,
  "link": "/enquiries/9d1…"}]
```
`source_kind` is `hire` or `milestone`; for a stage, `link` is `/contracts/{id}`.

**`answerPaidOnTime`** `POST /v1/paid-on-time/asks/{ask_id}/answer` (scope `reviews:write`), body `{"paid_on_time": true}`, returns the ask with `answered: true`.
- 404 `paid_on_time_ask_not_found`: not the caller's question (the payer or anyone else).
- 409 `paid_on_time_already_answered`: an answer is final.

**The count.** Shown only after `PAID_ON_TIME_MIN_ANSWERS` (3) answers, so no single answer can be traced. No stars, no score.
- `getMemberPaidOnTime` `GET /v1/members/{member_id}/paid-on-time`:
```json
{"member_id": "m_sunita", "answered": 3, "paid_on_time": 2, "shown": true, "label": "Paid on time: 2 of 3", "min_answers": 3}
// below 3 answers
{"member_id": "m_sunita", "answered": 0, "paid_on_time": 0, "shown": false, "label": null, "min_answers": 3}
```
  Hindi label: "समय पर पेमेंट: 3 में से 2". Telugu: "సమయానికి చెల్లింపు: 3లో 2".
- The same object (or `null` while hidden) is on **`ListingOut.paid_on_time`** (profile detail and `getMyProfile`) and on **`OpportunityOut.poster_paid_on_time`** (opportunity detail). Put it in the Pay block at the top of a job, next to the poster's name.

---

## 3. Close the loop

### Every applicant reaches a final answer

When a post **closes** (`closeOpportunity`), **expires** (hourly pass) or **fills** (the hire that reaches `structured.openings` closes the post with `state_reason: "filled"`), every applicant still `new` or `shortlisted` whose thread is not `in_progress`:
- gets `stage: "declined"`; an open thread becomes `state: "closed"`, `state_reason: "post_closed"`;
- gets one notification in their language (`applicantPostClosed`, or `applicantPostFilled`), link `/enquiries/{id}`: "Update on {title}" / "This post has closed, so your application won't go further this time. It isn't a judgement of you. There are similar posts on Vyapar." Never "rejected" or "not selected".
- The usual `applicant.declined` event fires.

**The applicant still sees which post it was.** Once a post is closed, expired or removed, RLS hides it from the applicant, so their Requests row and thread used to read "Untitled". The thread now reads it through a participant-only function (`vyapar_enquiries.enquiry_targets`, migration 028 §8), which returns only the title and state, for old rows too:
- `listMyEnquiries` and `getEnquiry` carry `target_name` (the post title, or the profile name) and the new `target_state` (the post's `closed | expired | removed | active | …`, or the listing's state);
- `getEnquiry` now also carries `counterpart_name`.

Show the title as usual with a "Closed" / "Expired" chip from `target_state`, and don't link to a post the reader can no longer open.

A thread the poster already accepted (`in_progress`) is left alone. If the post is renewed, these applicants can apply again (`already_declined` now ignores `state_reason: post_closed`).

### "N applicants still waiting" before closing

**`getOpportunityCloseCheck`** `GET /v1/opportunities/{id}/close-check` (the person who posted only; others 404 `opportunity_not_found`). Show it in the Close confirmation.
```json
{"waiting": 2, "new": 1, "shortlisted": 1, "oldest_waiting_days": 3,
 "message": "2 applicants are still waiting for an answer.",
 "close_message": "If you close this post now, the 2 people still waiting will be told politely that it has closed."}
// one waiting (plural forms per language: server keys `…waiting.one/.other`, `…closeMessage.some.one/.other`)
{"waiting": 1, "new": 1, "shortlisted": 0, "oldest_waiting_days": 0,
 "message": "1 applicant is still waiting for an answer.",
 "close_message": "If you close this post now, the 1 person still waiting will be told politely that it has closed."}
// nobody waiting
{"waiting": 0, "new": 0, "shortlisted": 0, "oldest_waiting_days": null, "message": null,
 "close_message": "Nobody is waiting for an answer. Closing stops new applications."}
```
The same `waiting / new / shortlisted / oldest_waiting_days / message` object is on the poster's own opportunity detail as **`OpportunityOut.applicants_waiting`** (null when nobody waits, and always null for other readers). Show it as a nudge above the applicants button.

**Weekly nudge.** The hourly pass notifies a poster whose applicants have waited more than `APPLICANTS_WAITING_NUDGE_DAYS` (7) days, once a week per post (`applicantsWaiting`, link `/opportunities/{id}/applicants`): "People are waiting for your answer: {title}" / "Waiting more than a week without an answer: {count}. Shortlist, hire or decline; declining takes one tap and they're told politely."

### Every restriction has a reason and a human appeal

Before this pass, three restrictions could not be appealed at all:
- an operator suspending a listing (`suspendListing`);
- an operator removing a post from the review queue (`decideOpportunityReview` `remove`);
- the interim holds: the seeker-charge report pause and the automated hold on a new profile.

Now the first two record a decided moderation case (`source: operator`) and notify the member (`moderationOutcome`, link `/moderation/outcomes`). Interim holds can be appealed while they wait for a decision. The existing `createAppeal` `POST /v1/appeals` is the one appeal path: an upheld (`overturned`) appeal restores the post or profile, closes the case, and the member is told.

**`listMyRestrictions`** `GET /v1/me/restrictions` (scope `read`): everything of the caller's that the platform restricts now.
```json
[{"object_kind": "opportunity", "object_id": "71bc…", "title": "Tandoor helper for the Secunderabad kitchen",
  "restriction": "paused", "restriction_label": "Paused by Vyapar",
  "reason_code": "seeker_charge_reports", "reason_label": "reported by people who were asked for money",
  "case_id": "c4fa…", "under_review": true, "can_appeal": true, "appeal_state": null,
  "appeal_deadline": "2026-10-15T06:11:52+00:00", "appeal_link": "/moderation/outcomes",
  "message": "A person from our team will look at this. You can add your side now; you don't have to wait for the decision."}]
```
- `restriction`: `removed | paused | suspended | limited | held | hidden`, each with `restriction_label`.
- `message` depends on the state: under review, can appeal, appeal open, or "To talk to a person about this, write to {grievance contact}".
- Appeal with `POST /v1/appeals {"case_id": "<case_id>", "text": "…"}`.
- The same object is on the owner's own reads: **`OpportunityOut.restriction`** (the poster's opportunity detail) and **`ListingOut.restriction`** (`getListing` by the owner, `getMyProfile`). It is null otherwise.

---

## 4. Profession-aware profiles

**Data, not code.** `vyapar_listings.profession_rules` has one row per taxonomy term. A profile falls under a rule through its categories, its skills, or a skill's parent category. When several rules match, the most restrictive answer wins for each switch.

| Term | Profession | Council | Promotion | Public reviews and badges | Ranking boost | Public prices | Fields others see |
|---|---|---|---|---|---|---|---|
| category `legal` | advocate | Bar Council of India (Rule 36) | no | no | no | no | name, business name, categories, skills (practice areas), languages, locality, experience, council register entries, contacts |
| skill `architecture` | architect | Council of Architecture | no | no | no | no | same |
| category `accounting_tax` | chartered_accountant | ICAI | yes | yes | yes | yes | all (wording note only) |

Seeded profiles covered: **Kavita Dhawan** (advocate) and **Deepak Bhalla** (architecture plus interior design: the architect rule wins). Neither had a promotion, review or package to remove. Anita Khatri and Harsha Vardhan get the CA note.

**`ListingOut.profession`** (every listing read: detail, search card, my profile; null when no rule applies):
```json
{"profession": "advocate", "profession_label": "Advocate", "regulator": "Bar Council of India", "restricted": true,
 "allow_promotion": false, "allow_public_reviews": false, "allow_ranking_boost": false, "allow_public_prices": false,
 "permitted_fields": ["business_name", "capabilities", "categories", "contacts", "council_credentials", "experience_years", "languages", "locality", "name"],
 "hidden_fields": ["headline", "description", "business_headline", "business_description", "rates", "evidence_links", "intent_state", "availability"],
 "contact_label": "Contact",
 "note": "Information only. Under the Bar Council of India's rules, advocates may not advertise or seek work, so this profile shows only the details the Bar Council allows, with no reviews, ratings, prices or promotion.",
 "rule_reference": "Bar Council of India Rules, Part VI, Chapter II, Section IV, Rule 36 (with the 2008 amendment on websites)",
 "rules_checked_on": "2026-09-30", "source_url": "https://www.barcouncilofindia.org/…"}
```

**What changes for a restricted profile.**
- **Viewed by someone else:**
  - the fields in `hidden_fields` come back `null` (or `[]`);
  - `reputation` is `null`;
  - `badges` keeps only `verified_business`;
  - `packages` is `[]`;
  - `sponsored` is `false`;
  - `listListingReviews` returns only reviews the viewer wrote or received.

  Show `note` once, as "Information only", and use `contact_label` ("Contact") for the action, never "Ask for a price".
- **Viewed by the owner:** everything is returned. `hidden_fields` says what others do not see, so the editor can say so.
- **Search** (`searchListings`):
  - the profile is still found by name, skill and place;
  - its `relevance_reason` is `matchesFilters`;
  - it gets no trust, reputation or freshness score and is never "verified first";
  - it never gets a Sponsored slot;
  - among equal matches, order is distance, then name.
- **Profile recommendation cards** (`ProfileCard`, from "Similar profiles" `listSimilarProfiles` and `listMatchingProfiles`) carry the same `profession` object. When it is restricted, the card's `headline` and `availability` are `null`, `reputation` is `null` and `badges` keeps only `verified_business`, exactly as on the listing detail. A card has no prices.
- **Profile recommendations** ("Similar profiles" on a profile, `listMatchingProfiles` on a post): the same neutral order. Among equal skill matches such a profile gets no verified-first or "available now" boost and is ordered by nearness to the viewer, then name. Its cards carry no counts or reputation badges.
- **Promotion:** `createPromotion` and `confirmPromotionPurchase` → **403 `promotion_not_permitted_for_profession`**, "Your profession's council does not allow advertising, so this profile can't be promoted. People still find you in search." `listPromotionOptions` → `eligible: false`, `reason: "notPermittedForProfession"`, `products: []`. Campaign items go through the same check.
- **Packages:** `upsertListingPackages` → **403 `packages_not_permitted_for_profession`**. `requestListingPackage` → 404 for others.
- **Reviews:** `createReview` about such a profile → **403 `reviews_not_permitted_for_profession`**. `getReviewInviteStatus` → `can_review: false`, `blocked_reason: "profession_rules"`.
- **Existing promotions:** the migration and the hourly trust pass cancel any live promotion on a restricted profile (`state: cancelled`, `reject_reason: profession_rules`, order history written). The owner is told (`promotionCancelledProfession`: "Your promotion was stopped … Our team will refund any amount paid.").
- **Badge fix found on the way:** "Verified business owner" was given to anyone with an `active_verified` listing, so Kavita (verified by her Bar Council credential) carried it. It now needs a business document (GST, Udyam, PAN or shop licence) on a profile with a business section, the same test as `business_verified`.

**`listProfessionRules`** `GET /v1/profession-rules`: the table above, with `term_label`, `profession_label` and `note` localized.

---

## 5. Council-verified badges

**Registers** (`listCredentialTypes` `GET /v1/credentials/types`):

| `credential_type` | Council | Number format |
|---|---|---|
| `icai_membership` | fixed: Institute of Chartered Accountants of India | 6 digits (`212345`) |
| `medical_council_registration` | "National Medical Commission" or "<State> Medical Council" | as printed |
| `allied_health_registration` | fixed: National Commission for Allied and Healthcare Professions | as on the register |
| `bar_council_enrolment` | "Bar Council of <State>" | `TS/1234/2015` (spaces and case normalised) |
| `coa_registration` | fixed: Council of Architecture | `CA/2010/12345` |
| `digilocker_document` | the issuer (e.g. Osmania University) | document number, plus `document_uri` (`in.gov.…`) |

```json
[{"credential_type": "bar_council_enrolment", "label": "Bar Council enrolment", "fixed_council": null,
  "council_suggestions": ["Bar Council of Telangana", "Bar Council of Andhra Pradesh", "…"],
  "number_hint": "State/number/year, e.g. TS/1234/2015", "needs_document_uri": false}]
```

**Add, list, re-check, remove** (the member in person; tokens are refused on `/credentials`):
- `addCredential` `POST /v1/me/profile/credentials` → 201
```json
// request
{"credential_type": "bar_council_enrolment", "registration_number": "ts / 2451 / 2016",
 "council": "Bar Council of Telangana", "registered_on": "2016-08-12"}
// response (CredentialOut)
{"id": "…", "credential_type": "bar_council_enrolment", "type_label": "Bar Council enrolment",
 "council": "Bar Council of Telangana", "registration_number": "TS/2451/2016", "registered_on": "2016-08-12",
 "status": "claimed", "label": "Bar Council of Telangana: pending check",
 "checked_on": null, "checked_on_label": "Pending check", "check_source": "dev_stub",
 "last_attempt_at": "2026-09-30T06:20:11+00:00", "expires_at": null,
 "verification_record_id": "28b3…", "check_note": null, "listing_id": "45ff…"}
```
  Errors: 422 `credential_number_invalid` (`details.field: registration_number`), 422 `credential_council_invalid` (`council`), 422 `credential_document_uri_invalid` (`document_uri`), 409 `credential_exists` (`details.credential_id`), 403 `profile_required`.
- `listMyCredentials` `GET /v1/me/profile/credentials`
- `recheckCredential` `POST /v1/me/profile/credentials/{id}/recheck`
- `deleteCredential` `DELETE /v1/me/profile/credentials/{id}` → `{"deleted": true}`

**How a claim becomes a badge.**
1. The claim goes to the configured `CredentialRegistry` (`CREDENTIAL_REGISTRY`, default `dev_stub`). The dev stub answers `not_checked` with `source: dev_stub`. It never says verified, and `last_checked_at` stays empty.
2. Whatever a registry cannot settle is put in the **existing operator verification queue** as a `credential` record ("Bar Council enrolment: TS/2451/2016", issuer "Bar Council of Telangana").
3. An operator checks the public register and approves or rejects it there (`approveVerification` / `rejectVerification`). The claim becomes `verified` (`check_source: operator`, checked now, valid `CREDENTIAL_RECHECK_DAYS` = 365 days) or `failed`.
4. After a year the hourly pass marks it `expired` and tells the member (`councilCredentialExpired`).

A real registry adapter sets `verified` or `failed` itself with `source: registry`.

**On the profile:** `ListingOut.council_badges` (detail, search cards, my profile) lists the public entries (`claimed` and `verified` only):
```json
[{"id": "…", "credential_type": "bar_council_enrolment", "type_label": "Bar Council enrolment",
  "council": "Bar Council of Telangana", "registration_number": "TS/2451/2016", "registered_on": "2016-08-12",
  "status": "verified", "label": "Registered with Bar Council of Telangana",
  "checked_on": "2026-09-30", "checked_on_label": "Checked on 30 Sep 2026", "check_source": "operator"}]
```
- Render `label` · `checked_on_label`. Hindi: "Bar Council of Telangana में रजिस्टर्ड · 30 सित॰ 2026 को जाँचा गया"; the month comes from the reader's catalogue.
- A claimed entry reads "Bar Council of Telangana: pending check" · "Pending check". Never draw a tick for it.
- `credential_verified` is true only after a real check. A credential reference from the development Identity & Trust stand-in now carries `source: "dev_stub"` and no longer counts.
- The Bar Council itself requires the enrolment number on an advocate's website, so `registration_number` is public.

---

## Hourly trust pass and dev trigger

`run_trust_pass` runs in the hourly loop in `main.py`:
- refreshes the profession-rules cache;
- cancels promotions on restricted profiles;
- expires council badges whose year is up;
- opens "paid on time" questions;
- sends the "applicants waiting" nudges.

**`runTrustPass`** `POST /v1/trust/jobs/run` runs it now (dev only; 404 `dev_only` otherwise):
```json
{"promotions_cancelled": 0, "paid_on_time_asked": 3, "applicants_waiting_nudged": 0, "credentials_expired": 0}
```

New settings (defaults in `app/config.py`, all overridable in `.env`):
- `CREDENTIAL_REGISTRY=dev_stub`
- `CREDENTIAL_RECHECK_DAYS=365`
- `PAID_ON_TIME_ASK_AFTER_HIRE_DAYS=30`
- `PAID_ON_TIME_MIN_ANSWERS=3`
- `APPLICANTS_WAITING_NUDGE_DAYS=7`

## Token scopes and MCP

- `/v1/paid-on-time` writes need `reviews:write`.
- `/v1/trust/scam-check` needs `read`.
- `/credentials` is refused for tokens, except `GET /v1/credentials/types`.
- New MCP tools:
  - `check_scam_shield`
  - `list_paid_on_time_questions`
  - `answer_paid_on_time`
  - `get_paid_on_time`
  - `list_my_restrictions`
  - `get_close_check`
  - `list_profession_rules`

## Checks

`scripts/check_trust_pack.py` passed **103/103** on private port 8093, including:
- the corpus (16 scam phrasings caught, 12 honest ones allowed);
- every surface;
- paid on time, with a real contract stage released through the dev sandbox;
- close, expiry and fill;
- the seeker-charge pause, appealed and restored;
- a review-queue removal, now appealable;
- Kavita Dhawan and Deepak Bhalla's profiles;
- a legacy promotion cancelled by the pass;
- two advocates in Abids listed in name order in a post's matching profiles, with no verified-first boost, and cards carrying `profession` with no headline or counts;
- a closed post still named in the applicant's thread and Requests row;
- singular and plural close-check messages in en/hi/te;
- a new advocate with a Bar Council claim checked by an operator, then suspended, appealed and restored.

It deletes everything it created, restores the rate limits and "recently viewed" rows it touched, and its sweep finds no leftover rows.

The existing checks all still pass:

| Script | Result |
|---|---|
| `check_structured_hiring.py` | 130/130 |
| `check_profile.py` | 33/33 |
| `check_contracts.py` | 92/92 |
| `check_admin_console.py` | 77/77 |
| `check_backend_b.py` | 168/168 |
| `check_ai.py` | 68/68 |

## Notes for the frontend

- **Composer, reply box, package editor:** call `checkScamShield` before sending. On 422 `seeker_charge_not_allowed`, show `message` + `details.explanation` at `details.field`.
- **Job and package page:** show the Pay block with `compensation_label`, and `poster_paid_on_time.label` next to "Posted by {name}" when it is not null.
- **Applicants board:**
  - `applicants_waiting.message` as a nudge;
  - the Close dialog shows `getOpportunityCloseCheck.close_message`;
  - after closing, the applicant list shows everyone as Declined.
- **Inbox:** `paidOnTimeAsk` opens a two-button sheet (Yes / No) that calls `answerPaidOnTime`. List open ones with `listMyPaidOnTimeAsks`.
- **Restrictions:** a banner on any restricted post or profile from `restriction` (`restriction_label`, `reason_label`, `message`), with "Appeal" (`POST /v1/appeals` with `case_id`) while `can_appeal`. `listMyRestrictions` feeds a "What's restricted" list next to My moderation outcomes.
- **Profile:**
  - when `profession.restricted`: hide reviews, badges, Promote, packages and "Ask for a price"; show `profession.note` as "Information only" and a neutral `profession.contact_label` button;
  - in the owner's editor, mark `profession.hidden_fields` as "Not shown to others (Bar Council rules)";
  - `council_badges` under the name as "label · checked_on_label";
  - the owner adds entries from `listCredentialTypes` with `addCredential`.
- **Promote screen:** handle 403 `promotion_not_permitted_for_profession` and `reason: notPermittedForProfession` with the message as sent.

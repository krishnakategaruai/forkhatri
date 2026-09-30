# IMP: Voice interview, backend (2026-09-30)

Owner: "Voice should like, we ask questions in their perspective and waits until we receive answer!"

Voice posting and voice profile setup are now a guided conversation:

1. The app asks one question, in the person's everyday words and language, and speaks it.
2. It waits for the answer.
3. It reads back what it understood and asks for a yes or no.
4. It asks the next question, but only about what is still missing.
5. It ends with a summary to review.

The backend never publishes or saves anything by itself. The person reviews the draft, then posts it with `createOpportunity` or saves it with `PATCH /v1/me/profile`.

Two operations do the work. Both are stateless (the client sends the confirmed answers on every turn) and deterministic. No model is needed to choose a question.

| Operation | Route | Token scope |
|---|---|---|
| `nextInterviewQuestion` | `POST /v1/voice/interview/next` | `read` |
| `interpretInterviewAnswer` | `POST /v1/voice/interview/interpret` | `read` |

The MCP tools are `next_interview_question` and `interpret_interview_answer`.

## The client loop

```
answers = {}, skipped = []
loop:
  step = next({flow, language, answers, skipped})
  if step.done: show step.summary, then let the person post/save step.draft; stop
  speak step.question (show step.hint and step.options as chips, if any)
  heard = interpret({flow, field: step.field, language, text: transcript, answers})
  switch heard.intent / heard.understood:
    understood and needs_confirmation:
        speak heard.readback, listen, interpret(same field, the reply)
          -> intent "yes": answers[field] = heard.value; merge heard.also into answers
          -> intent "no":  ask step.question again (or offer heard.alternatives)
    understood and not needs_confirmation:  answers[field] = heard.value   (the answer was itself yes/no)
    intent "skip":   if step.optional: skipped.push(field)   else speak heard.reprompt
    intent "repeat": speak heard.reprompt (the same question)
    otherwise:       speak heard.reprompt and listen again for the same field
```

- **At the read-back step, read only `intent`.** For example, "no" to "Do they need a bike?" is an answer (`understood: true`, value `[]`). But "no" to "I heard ₹15,000 — is that right?" rejects the read-back. The same call returns `intent: "no"` in both cases.
- **`also` holds what the first answer already stated.** For example: "I need 2 delivery boys in Kukatpally, salary 15 to 18 thousand". The read-back names every item. Once the person says yes, the client merges them, so those questions are never asked.
- **A required field that is skipped is asked again, last.** Its question then starts with "We need this one." Set `optional: false` to stop the client from offering Skip.

## `POST /v1/voice/interview/next`

Request:

```json
{ "flow": "post_job", "language": "en",
  "answers": { "work": {"title": "Delivery boys", "description": "I need 2 delivery boys in Kukatpally, salary 15 to 18 thousand", "required_capabilities": ["delivery"]},
               "location": "Kukatpally", "salary": {"min_paise": 1500000, "max_paise": 1800000}, "openings": 2 },
  "skipped": [] }
```

Response while questions remain:

```json
{ "done": false, "field": "job_timings", "question": "What hours will they work?",
  "hint": "Like nine in the morning to six in the evening", "kind": "text", "options": null,
  "optional": false, "progress": {"asked": 5, "total": 8},
  "summary": null, "draft": null }
```

- `kind` is one of `text`, `choice`, `number` or `yesno`.
- `options` is filled for `choice`, as `[{"value": "remote", "label": "From their own place"}, ...]`. Asset chips include `{"value": "none", "label": "Nothing extra"}`, which means `[]`.
- `progress.total` counts only the questions this interview asks. Things already known are not counted.
- For a post, when the member has a saved locality, `location` comes as `kind: "yesno"`. The question is `"Is the work in Kukatpally?"` (Hindi `"क्या काम Kukatpally में है?"`). "yes", "haan" or "avunu" gives the saved locality. "no" gives the open question as `reprompt`. A place name is taken as the answer.

Response when done (post):

```json
{ "done": true,
  "summary": [ {"field": "work", "label": "Work", "value_label": "Delivery boys"},
               {"field": "location", "label": "Area", "value_label": "Kukatpally"},
               {"field": "salary", "label": "Pay", "value_label": "₹15,000 to ₹18,000 a month"},
               {"field": "openings", "label": "People needed", "value_label": "2 people"},
               {"field": "job_timings", "label": "Hours", "value_label": "9 am to 6 pm"} ],
  "draft": { "draft_type": "opportunity", "type": "employment", "title": "Delivery boys", "description": "…",
             "location": "Kukatpally", "work_mode": "on_site", "timing": null,
             "required_capabilities": ["delivery"], "capability_labels": ["Delivery rider"],
             "employment": {"salary_min_paise": 1500000, "salary_max_paise": 1800000, "incentive_type": "none", "openings": 2,
                            "shift": "day", "job_timings": "9 am to 6 pm", "min_qualification": "10th", "english_level": null,
                            "interview_details": null, "experience_min_months": 0, "experience_max_months": null,
                            "requires_assets": ["two_wheeler", "smartphone"]},
             "freelance": null, "local_service": null,
             "confidence": {"title": 1.0, "location": 1.0, "salary": 1.0, "...": 1.0},
             "missing": [], "questions": [], "source": "rules", "language": "en",
             "deadline": null, "compensation": null } }
```

The post draft has the same shape `draftOpportunity` returns, plus three fields:

| Field | Meaning |
|---|---|
| `draft_type` | Always `"opportunity"`. |
| `deadline` | Project only. `YYYY-MM-DD`, sent as `createOpportunity.deadline`. |
| `compensation` | Local service, only when no budget was given. Values like `"₹300 per visit"`, `"Pay per visit"` or `"negotiable"`, sent as `createOpportunity.compensation`. This satisfies `pay_basis_required`. |

A job always carries both `salary_min_paise` and `salary_max_paise`, because the publish gate needs both. A single amount is a range of one.

Response when done (profile). The draft is the body for `PATCH /v1/me/profile`, carrying only what the interview learned:

```json
{ "done": true,
  "summary": [ {"field": "work", "label": "Work", "value_label": "Electrician"},
               {"field": "locality", "label": "Area", "value_label": "Boduppal"},
               {"field": "own_assets", "label": "Your own tools or vehicle", "value_label": "A bike, own tools"} ],
  "draft": { "draft_type": "profile", "name": null, "locality": "Boduppal", "capabilities": ["electrical"],
             "headline": "Electrician", "experience_years": 5, "own_assets": ["two_wheeler", "own_tools"] } }
```

`null` fields are left unchanged by the PATCH. `draft_type` is ignored by it.

## `POST /v1/voice/interview/interpret`

Request:

```json
{ "flow": "post_job", "field": "salary", "language": "hi", "text": "पंद्रह से अठारह हज़ार महीना", "answers": {} }
```

Response:

```json
{ "understood": true, "value": {"min_paise": 1500000, "max_paise": 1800000},
  "readback": "मैंने सुना: ₹15,000 से ₹18,000 प्रति माह। सही है?", "confidence": 0.9, "alternatives": [],
  "intent": "answer", "reprompt": null, "needs_confirmation": true, "also": {}, "source": "rules" }
```

More examples:

| Said (field) | Result |
|---|---|
| `"I need 2 delivery boys in Kukatpally, salary 15 to 18 thousand"` (work) | value `{"title": "Delivery boys", …, "required_capabilities": ["delivery"]}`; `also` = location, salary, openings; readback `I heard “Delivery boys”, in Kukatpally, ₹15,000 to ₹18,000 a month, 2 people — is that right?` |
| `"పదిహేను నుండి పద్దెనిమిది వేలు"` (salary) | `{"min_paise": 1500000, "max_paise": 1800000}`; `నేను విన్నది: నెలకు ₹15,000 నుండి ₹18,000. సరేనా?` |
| `"700 a day"` (salary) | `{"min_paise": 1820000, …}`; `I heard ₹700 a day, about ₹18,200 a month — is that right?` |
| `"Kukatpally lo"`, `"कुकटपल्ली में"`, `"కూకట్‌పల్లి లో"` (location) | `"Kukatpally"` (Vyapar's own spelling) |
| `"do log"`, `"ఇద్దరు"` (openings) | `2`; `2 लोग` / `2 మంది` |
| `"सुबह 9 से शाम 6 बजे तक"` (job_timings) | `{"job_timings": "सुबह 9 से शाम 6 बजे तक", "shift": "day"}` |
| `"repu udayam"` (when) | `{"preferred_date": "<tomorrow>", "urgency": "this_week"}`; `రేపు (గురువారం, 1 అక్టోబర్)` |
| `"तीन सौ प्रति विज़िट"` (local budget) | `{"budget_paise": null, "compensation": "₹300 per visit"}` |
| `"గంటకు ఐదొందలు"` (project budget) | `{"budget_type": "hourly", "min_paise": 50000, "max_paise": 50000}` |
| `"in two weeks"` (deadline) | `{"deadline": "<+14 days>", "duration": "1_4_weeks"}` |
| `"nahi"` (requires_assets) | understood, `[]`, `needs_confirmation: false` |
| `"haan"` (requires_assets) | not understood, `reprompt`: `क्या चाहिए: बाइक, फ़ोन, लाइसेंस, या कुछ और?` |
| `"skip"` / `"chhodo"` / `"vaddu"` | `intent: "skip"`; a required field gets `reprompt: "We need this one. …"` |
| `"repeat"` / `"phir se"` / `"malli cheppandi"` | `intent: "repeat"`, `reprompt` = the same question |
| `"blah"` (salary) | `intent: "unclear"`, `reprompt: "Sorry, I didn't catch the amount. How much will you pay each month?"` |
| `"डिलीवरी बॉय चाहिए, रजिस्ट्रेशन फीस 500 रुपये देनी होगी"` (work) | `understood: false`, `reprompt` = the scam-shield reason in Hindi + `कृपया किसी से पैसे माँगे बिना फिर से बताइए।` |

Errors:

- A field that is not in the flow gives `422 voice_unknown_field`. Its details list the flow's fields.
- An unknown flow gives `422`.

## Fields and value shapes

| Flow | Field (order) | Optional | Kind | Value |
|---|---|---|---|---|
| post_job | `work` | | text | `{title, description, required_capabilities[]}` |
| | `location` | | text / yesno | `"Kukatpally"` |
| | `salary` | | number | `{min_paise, max_paise}` (monthly) |
| | `openings` | | number | `2` |
| | `job_timings` | | text | `{job_timings, shift}` |
| | `min_qualification` | yes | choice | `"10th"` (`"any"` for "no") |
| | `experience` | yes | number | `{min_months, max_months}` (`0` = someone new is fine) |
| | `requires_assets` | yes | choice | `["two_wheeler", "smartphone"]` or `[]` |
| post_local | `work`, `location` | | | as above |
| | `when` | | text | `{preferred_date, urgency}` |
| | `budget` | | number | `{budget_paise, compensation}`: one of the two is set |
| post_project | `work` | | text | as above |
| | `budget` | | number | `{budget_type: fixed\|hourly, min_paise, max_paise}` |
| | `deadline` | | text | `{deadline, duration}` (`ongoing` has no date) |
| | `work_mode` | | choice | `remote` \| `on_site` \| `both` |
| | `location` | | text / yesno | skipped when `work_mode` is `remote` |
| profile | `name` | | text | asked only when the identity has no real name |
| | `work` | | text | as above; becomes `capabilities` and `headline` |
| | `locality` | | text | asked only when unknown |
| | `experience_years` | yes | number | `5` |
| | `own_assets` | yes | choice | same vocabulary as `requires_assets` |

The profile flow reads the member's own profile and identity, never writing to them. It skips `name`, `locality`, `work`, `experience_years` and `own_assets` when those are already known. A full profile such as Meena's is asked one question. Post flows ask about everything, but offer the saved locality as a yes/no question.

## How answers are read

- **Rules first, in `app/integrations/ai/spoken.py` (new) and the existing readers.**
  - Spoken numbers in every script become digits: "पंद्रह", "ढाई हज़ार", "साढ़े तीन", "ఐదొందలు", "రెండున్నర", "fifteen", "do", "iddaru". A trailing "हज़ार / వేలు / thousand" stays a word, so `find_money` still carries it across a range.
  - Money, headcount, studies and experience use `rules_provider` (`find_money`, `find_openings`, `find_qualification`, `find_experience_months`).
  - Localities in any script match known names through `localities.find_known_locality` (known localities plus the `geo.py` gazetteer).
  - Skills match the live taxonomy terms and aliases through `find_capabilities`. A place's own words are taken out first, so कुकटपल्ली is not read as "कुक".
  - Hours, days ("kal", "repu", "parso", "agle somvar", "15 tarikh", "in 2 weeks") and names use `spoken.py`.
  - The first answer is also read by `draft_from_text` to fill `also`.
- **Claude only as a fallback.** It is called when `AI_PROVIDER=anthropic`, a real key is set, and the rules could not read the answer. Claude only rewrites the answer into plain English words ("20000 per month"). The same rules then read those words, so the value passes the same validation.
  - The call counts toward the member's `AI_DAILY_LIMIT`.
  - It writes one `ai_events` row with `kind = 'interview'` (a hash, never the text).
  - The response says `"source": "ai"`.
  - Rules answers are free: they neither count toward the limit nor write rows.
- **Scam shield.** Free-text answers are checked with `scam_shield.detect` (`work`, `job_timings`, `budget`, `when`, `deadline` and `name`). Posts use the hiring tier and a profile uses the offer tier. A match returns `understood: false` and the localized reason as `reprompt`. `createOpportunity` still runs its own guard.
- **Read-backs use the glossary formats.**
  - Pay: `opportunities.compensation.*` (₹15,000 to ₹18,000 a month · ₹15,000 से ₹20,000 प्रति माह · నెలకు ₹15,000 నుండి ₹20,000; Budget ₹2,000; ₹300 a visit).
  - Place: "in {place}", "{place} में", "{place}లో".
  - Headcount: "2 people", "2 लोग", "2 మంది".

## Storage

Migration `07a-db-implementation/migrations/029-voice-interview.sql` is applied to the dev DB and appended to `schema.sql`:

- `vyapar_listings.listings.own_assets text[]` (default `{}`) stores the answer to "Do you have your own tools or vehicle?". It uses the same closed vocabulary as `opportunities.requires_assets`. `ListingPatch` / `PATCH /v1/me/profile` accept it, `ListingOut` returns it, and the MCP `update_my_profile` takes it.
- `ai_events.kind` now also allows `'interview'`.

The interview has no table: it is stateless.

## Files

| Change | Files |
|---|---|
| New | `vyapar-service/app/services/voice_interview.py` (service) |
| | `vyapar-service/app/integrations/ai/spoken.py` (spoken readers) |
| | `vyapar-service/app/routers/voice.py` |
| | `vyapar-service/app/i18n/locales/{en,hi,te}/voice.json` |
| | `vyapar-service/scripts/check_voice_interview.py` |
| | `07a-db-implementation/migrations/029-voice-interview.sql` |
| Edited | `app/main.py` (router) |
| | `app/integrations/identity/scopes.py` (`/v1/voice` needs `read`) |
| | `app/integrations/ai/anthropic_provider.py` (`interpret_answer`) and `base.py` (note) |
| | `app/services/listings.py` (`own_assets`) |
| | `07a-db-implementation/schema.sql` |
| | `vyapar-service/openapi.json` (regenerated: 261 operations, ids unique) |
| | `vyapar-mcp/vyapar_mcp/server.py` and `README.md` |

## Check

```
AI_PROVIDER=rules .venv/Scripts/python -m uvicorn app.main:app --port <private port>
VYAPAR_CHECK_API=http://127.0.0.1:<port> .venv/Scripts/python -m scripts.check_voice_interview
```

Result: 284 passed, 0 failed. The script covers:

- all four flows in English, Hindi and Telugu, with realistic transcripts;
- skipping known fields, the saved-locality yes/no, and a remote project never asking the area;
- control words in all three languages;
- a required skip being asked again last;
- the scam-shield reprompt in all three languages;
- every post draft being accepted by `createOpportunity` and meeting its pay gate;
- every profile draft being accepted by `PATCH /v1/me/profile`.

It cleans up the 9 draft posts it creates, the profile it creates for `m_new`, and `m_new`'s member row.

The existing checks still pass on the same build:

| Check | Result |
|---|---|
| `check_ai` | 68 of 68 |
| `check_profile` | 33 of 33 |
| `check_structured_hiring` | 130 of 130 |
| `check_trust_pack` | 103 of 103 |
| `check_contracts` | 92 of 92 |
| `check_admin_console` | 77 of 77 |
| `check_backend_b` | 168 of 168 |

The Claude fallback was checked separately against a local stand-in for the Messages API. The rules could not read "jitna market mein chalta hai utna", so it was sent to the stand-in and read back as ₹20,000 a month (`source: "ai"`, one `ai_events` row with `kind = 'interview'`). A rules-readable answer never reached it. The rows and rate-limit counters were then restored.

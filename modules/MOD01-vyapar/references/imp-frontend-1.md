# IMP (frontend workstream FE1): AI-first posting composer, structured responses, applicants board, voice input, taxonomy picker (2026-09-28/29)

This entry covers the posting and hiring side of `vyapar-web`. Every API call goes through the typed SDK. Every user-visible string is a key in `locales/{en,hi,te}/hiring.json`, with real Hindi and Telugu (491+ keys, the same key set in all three languages). Money is always paise on the wire and Indian-format rupees on screen.

**Checks:** `npx tsc --noEmit` is clean. `eslint` is clean on every FE1 file (see "Known outside FE1" for the repo-wide lint).

## What was built

| # | Area | Where |
|---|---|---|
| 1 | **SDK** | `lib/sdk/hiring-types.ts` holds the wire types: structured fields, `OpportunityWrite`, suggestions, `CreateEnquiryBody`, profile snapshot, the applicant pipeline and AI. `lib/sdk/domains/hiring.ts` adds `sdk.posting` (typed create/update/confirm/publish/suggestions), `sdk.responses` (typed createEnquiry with an Idempotency-Key), `sdk.applicants` (list/compare/setStage) and `sdk.ai` (the five AI operations). The taxonomy tree and badges come from FE2's `sdk.taxonomy` and `sdk.badges`, agreed after a brief duplicate. `Opportunity` gains `structured`, `compensation_label` and `allow_precall`. |
| 2 | **Posting composer** | Everything is in `app/opportunities/new/page.tsx` and `app/components/composer/*`. It is described in its own section below. |
| 3 | **Response composers** | These are in `app/components/respond/*`. `/enquiries/new` routes jobs, projects and local services to `StructuredResponse`. Listings and the other types keep the old composer. Each composer is described in its own section below. |
| 4 | **Applicants board** | `/opportunities/[id]/applicants` has the controller `useApplicantsBoard`, plus `ApplicantCard`, `ApplicantDetail` and `CompareTable`. It is described in its own section below. |
| 5 | **Opportunity detail** | `OpportunityDetailView` takes three new slots (`primaryActionSlot`, `precallSlot`, `applicantsSlot`) and FE2's parts are untouched. The page: <br>• shows the typed fields as facts: pay (`compensation_label`, falling back to free text), shift, openings, experience ("1 year+"), qualification, English, things needed, timings, interview, budget type, duration, level, when and date; <br>• shows the type chip as Job / Freelance project / Local service everywhere; <br>• opens one-tap Apply in place; <br>• shows "Applied ✓ · Open conversation" (or Hired / Not selected) once the viewer has responded (critique L12); <br>• mounts FE2's `PrecallActions` when `allow_precall` is on, with Apply outlined and Call as the one filled accent, also in the phone action bar; <br>• gives the poster an `ApplicantsSummary` card with per-stage counts and "Review n new". |
| 6 | **First run** | The skills step is now one `SkillPicker` on the taxonomy tree. Free text still goes to `capabilities_other`, so the old first-run-only lists are no longer used. |
| 7 | **VoiceInput** | `app/components/VoiceInput.tsx` uses the Web Speech API, with `lang` set to en-IN, hi-IN or te-IN from the app language. A हिं / తె / EN switch sits in the field. It shows a live interim caption. Nothing is saved until the person taps Keep; Try again and Discard are the alternatives. Errors appear inline (not-allowed, no-speech, network, no mic). The mic is hidden without browser support. It is used in the describe box, description, interview, apply note, proposal answers and cover text, quote note, and the upload note. |
| 8 | **Taxonomy picker** | `app/components/taxonomy/SkillPicker.tsx` shows category → roles/skills, each with its one-liner. <br>• Phone: you tap into a category, then back out. Desktop: two columns. <br>• Search matches the label, the category, the description, the slug and the English name (`useTaxonomyAliases`), so "mali" finds తోటమాలి. <br>• "Use '…' as written" appears only when nothing matches (L3). <br>• A collapsible mode shows chips plus "Change or add" once something is picked. |
| 9 | **Migration 022** | `07a-db-implementation/migrations/022-taxonomy-trade-roles.sql` (L3 + review) adds mason, tile fitter, welder, packer/loader and gardener (mali), with Hindi and Telugu names, one-liners and search aliases. It renames the "Delivery & logistics" role to "Delivery rider", moves wholesale supply under Textiles & Retail and fixes both category one-liners. It was applied twice to the dev DB (idempotent) and is added to `seeds.sql` after 018. Backend B took 023. |
| 10 | **Money** | `lib/money.ts` (L2) adds `formatRupees`, `formatRupeeRange` and `formatDateIN` ("28 Sept 2026"). `rupeesToPaise` now reads: <br>• 15k, हज़ार/వేలు, lakh/लाख/లక్ష and crore; <br>• Devanagari and Telugu digits; <br>• decimals; <br>• per-unit suffixes. <br>Two numbers give null. `MoneyInput` groups digits as you type (1,50,000) and shows "= ₹15,000" under the field for anything else. |

## Posting composer (item 2)

**Start screen.** One "Describe what you need" box, with:
- voice input;
- example sentences;
- "Draft it", which calls `draftOpportunity`;
- one "Use a photo or screenshot" button;
- "Skip — fill in myself";
- "Paste a forwarded message or link", the legacy share mode, kept in `LegacyComposer`.

On desktop, a "How it works" side panel sits beside it.

**The photo button (L7).** It tries `readOpportunityImage`. If that answers 501 or 503, the answer is remembered for the session and the photo is simply attached on the same screen. The text box then becomes its note, and the photo is saved as `raw_image_url`. There is no detour.

**Draft → form:**
- Fields the draft is unsure of show "Please check" / "✓ Looks right".
- Every amount and the openings the AI filled are always flagged (L8).
- Each missing field, and any half-filled salary or budget range, is asked as a question chip. The chip is answered with the same control the form uses.
- The type the poster tapped wins over the type the draft inferred, and the amounts are carried across (`retypeAiDraft`).

**Field order, per type:**
- **Job:** title, role, exact area, monthly in-hand salary min–max (with presets), incentives, openings, shift, timings, experience (with "Freshers welcome"), minimum qualification, English, things needed, interview, description.
- **Project:** title, skills, fixed or hourly budget range, duration, level, up to 3 screening questions (presets or your own), description.
- **Local service:** what, where, when, date, budget, description.
- **Other types:** generic fields.
- **Jobs and local services:** the "Calls before you accept" switch, off by default, with an explanation and a link to `/profile/contact`.
- **More options:** apply-by date, work mode, and My own / Found elsewhere.

**Check & publish:**
- The form is saved as a draft (create, then PATCH).
- `getOpportunitySuggestions` and `getPostingTips` are merged into one de-duplicated list of "Get more responses" cards, highest impact first. Each card applies its change in one tap (chips or a single button), which PATCHes the draft and re-reads the rule suggestions. Tips that need text offer "Add it" or "Edit it", which jump back to the field.
- Publish stays disabled until every flagged money or openings field has been touched or confirmed (L8).

**Preview and errors:**
- The live preview is a sticky side panel on desktop and collapsible on a phone.
- `salary_required`, `budget_required`, range errors and `seeker_charge_not_allowed` land on their field. For a fee charge, the field is found from `details.matched`.
- `acceptance_required` shows the in-place acceptance prompt (see "Bugs found").
- Prefill works: `?type=` and `&skills=`.

## Response composers (item 3)

- **Job, one-tap Apply.** It opens as a sheet on the detail page, and as a page at `/enquiries/new`. It shows the profile snapshot the poster will see, built as the server builds it: the newest live listing, a professional one first. An optional voice note follows. It sends `applied_via: one_tap`. When sent, it shows a "Sent" card, not a modal.
- **Proposal.** The fields, in order:
  - Fixed or hourly. The default comes from the project.
  - The price, with the poster's budget and "You receive ₹X — Vyapar takes no fee".
  - The timeline, as chips or a typed number of days.
  - Optional milestones (up to 5), with a live "₹X left to assign / adds up ✓ / over by".
  - An answer under each screening question.
  - The cover text, with voice input and "Improve with AI" / "Write it for me". This offers the suggested note (Use this note / Keep mine), the hints still worth adding (minus ones the form already satisfies) and a suggested price with its basis, marked when it is below the poster's own budget.
  - A work sample.

  Errors land on their own field, localized.
- **Local service.** Choose Send a quote (price, and when you can come) or Ask a question (ready question chips), plus an optional note. A "They will read" preview shows the message the taps compose in the sender's language. It sends `sub_choice`.

## Applicants board (item 4)

- **Tabs and sort.** Tabs are New / Shortlisted / Hired / Declined, with counts from `stage_counts`. Sort is Newest or Best match. Best match uses `getAiShortlist` (x/10, reasons in green +, risks as –). If that fails, it falls back to `sort=match` with a "matches n of m skills" count and never a percentage.
- **Card.** Each card shows:
  - the name;
  - Verified (a badge or the AI's `verified`) and other earned badges;
  - "Called you" for `applied_via=call`, and "One-tap apply";
  - the headline, years of experience, and distance (from the AI) or the locality;
  - the applied date;
  - price, days and milestones;
  - the reasons, reworded for the poster (the server's `match_reasons` read "matches **your** experience");
  - the message.
- **Actions.**
  - Shortlist is immediate, with an Undo toast.
  - Hire has an inline confirm that says it shares numbers.
  - Decline is held for 5 seconds with Undo, then sent. Leaving the page sends it immediately.
  - Hired shows Open conversation, and "Start a contract" for anything but a salaried job.
- **Compare.** Pick 2 to 4 people. A sheet shows a column per person and a row per attribute, with the best score, most skills and fewest days in bold, every screening answer, and actions per column.
- **Layout and hired contact.** On desktop, the list sits beside a detail pane. On a phone, a card's name expands the detail in place. For a hired applicant, the detail mounts FE2's `ContactActionsBlock` (Call / WhatsApp / number).

## Tested live, two-sided, through the real UI

The web app ran on a private `next dev` on 3031 (`VYAPAR_WEB_DIST_DIR=.next-fe1`) against a private uvicorn on 8031. The owner's 3011 and 8011 were not touched.

The Chrome DevTools MCP server disconnected mid-session. After that, the checks drove a private headless Chromium, the Playwright build already on the machine, over CDP on port 9331. Each persona had its own browser context (script: `scratchpad/cdp.py`). The screens were checked at 390 and 1440 px, in light and dark, in en, hi and te.

1. **Job.** Sunita (Kapoor Caterers) describes a baker job, then Draft, the form, Check & publish, Publish. Meena one-tap applies from the sheet. Sunita sees "Review 1 new" and opens the board. She shortlists (the toast appears), then hires through the confirm step. The hired pane shows Call / WhatsApp / +91 number.
2. **Project.** Shreya posts a React dashboard project with 2 screening questions. Priya sends a proposal with 3 milestones (the counter went "left to assign" → "adds up ✓"), both answers and "Write it for me". Arjun sends a second proposal. Shreya sorts by Best match (9/10 vs 3/10, with the skill guard), compares both, hires Priya from the compare sheet through the card's confirm, declines Arjun, then taps Undo.
3. **Local service in Hindi.** Anita describes a plumbing job in Devanagari. The missing location is asked as a question chip and answered in place, then she publishes. Ravi sends a Hindi quote (₹750, today, with a note) from a phone.
4. **First run in Telugu.** The picker drills in on a phone and shows two columns on desktop. The search "mali" finds తోటమాలి. "tandoor" offers "Use as written". `m_new` was restored exactly afterwards.
5. **Read-only screens.**
   - "Called you" on Suresh's pre-accept call on Sunita's electrician post, which belongs to backend B.
   - "Applied ✓" for Suresh on that post.
   - L7: a photo attached in place.
   - L8: the critique's own Telugu-in-Latin text. The half-read salary is flagged and asked as a range.

**Cleanup:** `scratchpad/cleanup_fe1.py` deleted the 4 test opportunities, the 4 enquiries and every row that referenced them: messages, outbox, notifications, impressions, member_opportunity and idempotency keys. It also restored the enquiry counters, removed the legal acceptances the runs created for Priya and Arjun, removed FE1's `ai_events` rows and removed one uploaded photo. A sweep of every `vyapar_*` table found no leftovers. The private servers and the browser were stopped by PID. `.next-fe1` and its two `tsconfig.json` include lines were removed.

**Screenshots:** 21 files named `fe1-*` in `screenshots/2026-09-28/`, and 40 in `screenshots/2026-09-29/`. They cover the composer (start, job, project, local in Hindi, review, question chip, L7, L8), the apply sheet, the proposal (empty, milestones, AI, accept, sent, phone), the quote (Hindi), the detail pages (viewer, poster, applied), the board (job, project, best match, compare, hire, decline-undo, called-you, Telugu) and first run (Telugu).

## Bugs found and fixed while reading the screens as a user

- **The AI draft overrode the poster's chosen type.** A project was read as a local service and its budget was lost. The chosen type now wins, and the amounts carry across.
- **A proposal failed with "Something went wrong".** The cause was `403 acceptance_required` for members who had not accepted the current privacy notice or terms, and nothing in the app handled it. The new `AcceptancePrompt` shows the notice in place with "Accept and continue", then retries. It is wired into Apply, Proposal, Quote and Publish.
- **CSS class collisions with FE2.** `.vy-sheet` put the apply sheet in the corner, and `.vy-remaining` also clashed. Mine are now `.vy-hsheet` and `.vy-msleft`.
- **The "selected" accent showed on the first card on a phone,** where there is no detail pane. It is now shown on desktop only.
- **Wording.** The server's applicant reasons were written for the applicant ("matches your experience"), so the poster now sees them reworded. The skills pill read "1/2" with no word. The fact read "1 year" where "1 year+" was meant. The preview said "Employment" and the composer "Job".
- **"Improve with AI" repeated advice.** It said to answer the questions after they were answered, and to state a price when one was set.
- **The suggested price was below the poster's own budget** without saying so. It is now marked.
- **The milestone day field showed a bare number.** It now reads "Day 12".
- **Colour literals.** My CSS used a colour literal for the backdrop and the over-budget text. Both now use the design-system tokens (`color-mix` on `--surface-sunken` for the backdrop, and `.vy-error` for the over-budget line), so the incoming palette applies.

## Reported to other owners (not fixed here)

- **Backend C: rules drafting.**
  - "Need a React developer … admin dashboard … fixed budget" is read as a local service.
  - "sales" is taken as a skill from "sales charts".
  - The title is cut at the first colon or comma ("…Nanda Labs: login").
  - Devanagari place names (बंजारा हिल्स) are not read as a location.
  - `nundi … varaku` and `se … tak` are not read as ranges (critique L8).
- **Backend C: improveProposal.** The bid range uses other posts' `value_amount` (₹32,500–₹50,000) below the poster's typed budget (₹60,000–₹90,000). The engine also suggests "answer the screening questions" because it only sees the cover text.
- **Backend A plus the owner (critique L11).** A number is revealed only on Hire, which notifies "hired". Proposed fix: make Shortlist the step that reveals contact. This needs a backend and product decision, so it is not changed in the UI.
- **FE2.** `PrecallActions` also prints "You have applied to this job. Open it" under the new "Applied ✓" button, so the same fact appears twice.

## Blocked / known outside FE1

- **Reading photos.** `readOpportunityImage` needs `ANTHROPIC_API_KEY`, and there is none, so it always answers 501. The UI handles that with the in-place attach (L7).
- **The platform fee.** No endpoint exposes the rate. The proposal says "Vyapar takes no fee", matching `CONTRACT_PLATFORM_FEE_BPS=0`, backend D's stated policy.
- **Voice.** Speech recognition needs a real microphone and permission. Headless checks confirm the mic, the language switch and the fallbacks render, but not recognition itself.
- **Repo-wide `npm run lint`.**
  - It reports pre-existing errors in files FE1 doesn't own (the admin pages, `DevMemberSwitcher`, `EnquiryThread`, `boost`, `campaigns` …).
  - It also scans the private `.next-*` build folders. `eslint.config.mjs` should ignore `.next-*/**`; that is a shared file, so I left it alone.
- **The Chrome DevTools MCP server disconnected** part-way through, which is why the later checks ran in the private headless Chromium.

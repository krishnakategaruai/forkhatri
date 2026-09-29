# Vyapar screen research — best patterns available in 2025–2026

**Written:** 2026-09-28. **Author:** UX research agent (Upwork/WorkIndia persona).
**Scope:** nine screens the build needs next. For each: what the best products
actually do, named references with URLs, and the Vyapar pattern that follows
Vyapar's own fixed rules (`DESIGN-ENHANCEMENT.md`: near-monochrome, one saffron
accent, gradients/glass/glow, floating command hub, dark-first + light mode).
Only **patterns and information structure** are borrowed — never a competitor's
chrome, colour or copy.

**Sourcing note.** `support.upwork.com`, `help.fiverr.com`, `workindia.in` and
`upwork.com/resources` returned HTTP 403 to automated fetches (same as prior
passes). Where a claim rests on a secondary write-up of those products it is
marked _(secondary)_. Anything not confirmed by a fetched page is marked
**[unverified]**. The product owner's real screenshots in
`references/upwork/` and `references/workindia/` are treated as ground truth
where they apply.

**Cross-cutting form rules used throughout** (verified):
NN/g's ten form recommendations — single column, labels above fields (never
placeholder-as-label), mark optional not required, logical/frequency ordering,
explain formats, no Reset buttons, highly visible specific errors
([nngroup.com/articles/web-form-design](https://www.nngroup.com/articles/web-form-design/)).
NN/g on wizards — use them for infrequent tasks, show a labelled step list,
enforce sequence, allow back, each step self-sufficient, re-use last-time
answers as defaults ([nngroup.com/articles/wizards](https://www.nngroup.com/articles/wizards/)).
Vercel Geist field conventions — label is a short Title Case noun, placeholder
is action-oriented ("Select a category"), validate on blur, error names the
field and ends in a period, group option lists past ~10 items
([vercel.com/geist/select](https://vercel.com/geist/select)).
Linear — one neutral palette with one accent "as punctuation", 120–180 ms
eased motion, list/board/split as _views of one dataset_ rather than separate
screens ([linear.app/now/how-we-redesigned-the-linear-ui](https://linear.app/now/how-we-redesigned-the-linear-ui);
[designsystems.one/design-systems/linear](https://www.designsystems.one/design-systems/linear)).
All of these already map onto Vyapar primitives (`.vy-field`/`.vy-label`,
`.vy-chip[aria-pressed]`, `.vy-pane-list/.vy-pane-detail`, `.vy-with-sidebar`).

---

## 1. Post an opportunity — type-specific composers

**What the best products do.**

- **Upwork (freelance project):** a sequenced wizard — title → skills (3–5 of
  max 10) → scope (size, duration, experience level) → budget (hourly range or
  fixed) → description → review/post. An AI option ("describe your project in
  a sentence or two") drafts the whole post, which the client then edits
  _(secondary: [upwork.com/resources/how-to-post-job-on-upwork](https://www.upwork.com/resources/how-to-post-job-on-upwork),
  [gigradar.io/blog/how-to-post-a-job-on-upwork](https://gigradar.io/blog/how-to-post-a-job-on-upwork),
  [upwork.com/uma](https://www.upwork.com/uma))_.
- **Apna (job):** one long single-column form, roughly: title → exact area
  (not just city) → salary _range_ → job type → shift/weekly-off → experience
  → education → English level → candidate requirements (shift comfort,
  joining timeline) → verified HR number → description → hiring process
  ([apna.co/career-central/how-to-post-your-first-job-on-apna](https://apna.co/career-central/how-to-post-your-first-job-on-apna/)).
  Apna's **nudges** (day 2 after activation) suggest "relax job criteria or
  increase job attractiveness"; jobs edited on a nudge got **+23 % leads per
  job**, adoption ~10 % ([apna.co/career-central/apna-cos-latest-updates…](https://apna.co/career-central/apna-cos-latest-updates-to-transform-recruitment/)).
- **WorkIndia (job):** title → monthly in-hand salary min–max (explicitly
  _excluding_ incentives) → openings → location → candidate requirements
  (qualification, experience, gender, English, must-have skills) → company
  details; posting is sold as "3 minutes" and responses arrive as calls
  _(secondary: [internshala.com/blog/employer-how-to-post-job-on-workindia](https://internshala.com/blog/employer-how-to-post-job-on-workindia/))_.
  The specific "12th pass instead of Graduate → more responses" wording is
  **[unverified]** — no fetched page shows it; Apna's nudge is the verified
  equivalent.
- **Naukri (recruiter):** AI pre-fills industry/functional area/role _from the
  pasted description_, a keyword suggester appears as you type, and the
  candidate-profile section is optional
  ([recruiterzone.naukri.com/new-naukri-job-posting-form](https://recruiterzone.naukri.com/new-naukri-job-posting-form/) — page fetched via search summary, not full text; treat details as _secondary_).

**Recommended Vyapar pattern.**

- **Entry, above the fold:** one screen, "What do you want to post?" — three
  neutral chips (Job · Freelance project · Local service), a single
  multiline `.vy-textarea` "Say it in one line", a mic button inside the field
  (see §9) and one primary button "Draft it". Nothing else. Typing is optional:
  "Skip, fill in myself" is a `.vy-btn-ghost`.
- **Draft → structured form:** the AI fills a **single-column** form of the
  type's fields; AI-inferred values render with a small neutral "Unconfirmed"
  `.vy-badge` (this is FR12's existing review requirement, moved inline).
  Field order per type (most-scanned first, per Apna/WorkIndia):
  - _Job:_ title · monthly salary min–max (₹, in-hand) · incentives toggle +
    amount · openings · shift/timings (chips: Day/Night/Rotational + time
    range) · locality · qualification (chips) · English level (chips: None/
    Basic/Good) · experience · interview (walk-in address / call / in-app) ·
    description.
  - _Freelance:_ title · category→specialty (§5) · budget type (Fixed / Hourly
    segmented) + amount or range · duration · experience level · skills chips
    · description · up to 3 screening questions (each a short text input,
    "Yes/No" or "Short answer").
  - _Local service:_ what · where (locality + radius) · when (Today / This
    week / Pick date) · budget (optional) · photo upload · description.
- **Step count:** mobile shows this as **2 steps** (Draft, Check & publish);
  desktop shows the same form in `.vy-detail` (form left, live preview card
  right). No progress bar needed for two steps; a step label is enough.
- **Suggestions step (Apna nudge, but at publish time not day 2):** on "Check
  & publish", a nested `.vy-card-nested` "Reach more people" lists at most
  three one-tap suggestions with the reason: "Accept 12th pass (Graduate
  excludes most nearby candidates)", "Add a salary range", "Mention timings".
  Each is a chip that mutates the field in place; accepting shows the field
  updated, no dialog. Re-surface the same card on the poster's opportunity
  page 48 h after publish if responses < N (the Apna timing).
- **States:** _loading_ — skeleton of the field list, never a spinner;
  _empty draft_ — the AI returned nothing: keep the form, show "Couldn't draft
  that — fill in below"; _error on publish_ — inline `.vy-error` under the
  button naming the field; draft autosaves (NN/g "save and resume").

## 2. Proposal / apply composer

**What the best products do.**

- **Upwork proposal:** terms first (hourly rate _or_ fixed bid; "by project"
  vs "by milestone" with milestone rows), then cover letter (~200–300 words
  advised), attachments/profile highlights, then **screening questions**,
  then a final review; clients see the first lines in the list before opening
  _(secondary: [gigradar.io/blog/how-to-apply-on-upwork](https://gigradar.io/blog/how-to-apply-on-upwork),
  [upwork.com/resources/cover-letter-tips](https://www.upwork.com/resources/cover-letter-tips))_.
  Upwork support article on screening questions + final review exists but
  returned 403 ([support.upwork.com/…/35081434907027](https://support.upwork.com/hc/en-us/articles/35081434907027-Answering-Screening-Questions-and-Final-Review)).
- **Indeed Apply:** "Apply now" keeps the person on Indeed; saved profile
  pre-fills required fields _and_ employer questions; conversion "drops
  sharply" past 20 screener questions
  ([docs.indeed.com/indeed-apply](https://docs.indeed.com/indeed-apply/),
  [indeed.com/help/…/204652920](https://www.indeed.com/help/job-seekers/articles/204652920-applying-for-a-job-on-indeed)).
- **WorkIndia job detail (owner screenshots):** sticky bottom bar with **two
  equal actions** — outlined "Apply" and filled "Click to call HR"
  (`references/workindia/README.md`).

**Recommended Vyapar pattern.**

- **Job → one-tap Apply.** The composer is a _confirmation card_, not a form:
  profile summary (name, top 3 capabilities, experience, locality) as a
  `.vy-card-nested`, up to 3 poster screening questions as chips/short inputs
  _only if the poster set them_, an optional note (mic-enabled), then one
  primary "Apply". If the profile is thin, an inline "Add what you can do"
  chip grid (reuse first-run's capability chips) sits _inside_ the card — no
  detour to onboarding.
- **Freelance → Proposal.** Order: **Price** (Fixed/Hourly segmented control,
  ₹ amount; when Fixed, a "By milestone" toggle expands 1–5 rows of _name ·
  amount · due_) → **Timeline** (chips: <1 week / 1–4 weeks / 1–3 months /
  Ongoing) → **Screening answers** (rendered as the poster's question text
  above each answer field) → **Cover note** (live counter "0/1000 · at least
  20", mic) → **Work sample** (`FileUpload`) → Send. Desktop: form in
  `.vy-detail-main`, the opportunity's brief pinned in `.vy-detail-aside` so
  the person never scrolls away from what they are answering.
- **Local service → Quote.** Price + earliest date + one line; same shell.
- **Cross-cutting:** the privacy line ("Your number is not shared until you
  both accept") once, under the send button; duplicate-thread 409 → "Open it"
  link (still an open UX-CRITIQUE item). Sent state: replace the form with a
  compact "Sent · you'll hear in Activity" card, no success modal.

## 3. Applicants / responses list for a poster

**What the best products do.**

- **Upwork "Review proposals":** tabs _All / Shortlisted / Messaged /
  Archived_; sorted **best match first**; per-proposal actions message /
  shortlist / hire / decline-archive; Uma Recruiter adds a ranked shortlist
  with thumbs-up/down feedback; reported +30 % hires, −11 % time-to-hire
  _(secondary: [uphunt.io/blog/upwork-uma-recruiter…](https://uphunt.io/blog/upwork-uma-recruiter-ai-shortlist-freelancer-guide-2026),
  [upalerts.app/blog/uma-recruiter-shortlist-guide](https://upalerts.app/blog/uma-recruiter-shortlist-guide))_.
- **Indeed Candidates tab:** statuses _Awaiting review / Reviewed / Contacted /
  Hired / Rejected_; filters by location, screener answers (yes/maybe/no),
  date; bulk export; row shows highlighted qualifications matching the post
  ([indeed.com/hire/resources/howtohub/how-to-manage-candidates-on-indeed](https://www.indeed.com/hire/resources/howtohub/how-to-manage-candidates-on-indeed)).
- **Apna:** dashboard shows applicant + number; guidance to "shortlist
  immediately when the basics match (location, shift, salary)" and call top
  fits within 24 h ([apna.co/career-central/guide-to-hiring-candidates-from-apna](https://apna.co/career-central/guide-to-hiring-candidates-from-apna/)).
- **Naukri Response Manager:** three marks — _Shortlisted / Maybe / Rejected_;
  WhatsApp icon opens a chat without saving the number _(secondary:
  [naukri.com/blog/recruiter-job-posting](https://www.naukri.com/blog/recruiter-job-posting/))_.
- **Kanban:** Greenhouse/Workable offer board _and_ list of the same pipeline;
  board earns its place only with ≥4 stages and drag-to-move
  ([support.greenhouse.io/…/204636805](https://support.greenhouse.io/hc/en-us/articles/204636805-Current-pipeline-per-job),
  [help.workable.com/…/115012857047](https://help.workable.com/hc/en-us/articles/115012857047-Candidate-profile-in-pipeline-view-overview)).

**Recommended Vyapar pattern.**

- **One dataset, two views (Linear).** Mobile and desktop default to a
  **list** in `.vy-pane-list` with a second row of count chips — _New (12) ·
  Shortlisted (3) · Contacted (2) · Hired · Declined_ — the two-level tab
  pattern already recorded from Upwork's own app
  (`references/upwork/README.md`). Desktop ≥1024 adds a "Board" toggle that
  lays the same five states as columns; drag moves state, and every card
  keeps the same three actions.
- **Row anatomy:** name + locality/distance · **match score as a count-based
  line** ("Matches 4 of 5: shift, locality, 12th pass, 2 yrs") — never a
  percentage (FR20 rule) · the applicant's first proposal line or asked price
  · reputation line (counts, no stars) · actions: Shortlist (toggle),
  Call/WhatsApp (only after acceptance, §4), overflow ⋯ → Decline with a
  one-tap reason.
- **Compare:** select 2–3 rows → a `.vy-card-floating` sheet with a
  column-per-person, row-per-attribute table (price, timeline, experience,
  match reasons, samples). Same matrix shape as §7's packages — one table
  component.
- **Filters:** chips row _Nearest · Best match · Newest · Asked ≤ ₹_ plus the
  poster's screening answers as Yes/No filters (Indeed). Desktop: a
  `.vy-with-sidebar` filter rail.
- **Empty:** "No responses yet — 3 things that help" reusing the §1
  suggestion card. Never a lone illustration.

## 4. Contact actions — Call / WhatsApp after acceptance, calling hours, daily cap

**What the best products do.**

- **WorkIndia / Job Hai / Apna:** the primary conversion is a **direct call**
  from the detail page or the applicant list; Job Hai's employer pitch is
  "get direct phone calls from relevant candidates"
  ([employer.jobhai.com/hire](https://employer.jobhai.com/hire); WorkIndia
  screenshots). Apna restricts calling for out-of-radius applicants in
  pay-per-job listings (a _platform-side_ cap on who may call).
- **Urban Company / Ola:** a per-order **proxy number** so neither side sees
  the other's real number; the mapping expires after the job
  ([medium.com/uc-engineering/masking-phone-numbers…](https://medium.com/uc-engineering/masking-phone-numbers-to-protect-user-privacy-in-a-marketplace-94c2e7c5f29f) — fetch refused this pass, content from search summary, _secondary_;
  [dqindia.com/ola-cabs-introduces-number-masking…](https://www.dqindia.com/ola-cabs-introduces-number-masking-to-protect-privacy-of-customers/)).
- **WhatsApp click-to-chat:** `https://wa.me/<E.164>?text=<encoded>` opens
  the app on mobile and WhatsApp Web on desktop, with the starter message
  editable before send ([whatsform.com/blog/whatsapp-link-pre-filled-message](https://whatsform.com/blog/whatsapp-link-pre-filled-message/),
  [u2l.ai/blog/whatsapp-click-to-chat-link](https://u2l.ai/blog/whatsapp-click-to-chat-link)).
- Calling-hours and per-day caps as _poster-set_ controls: no competitor
  page found that exposes these to the poster — **[unverified as a
  competitor pattern]**; the closest precedents are WhatsApp Business
  "business hours"/away messages and Apna's platform-side caps.

**Recommended Vyapar pattern.**

- **Before acceptance:** one primary "Apply/Enquire", no phone. After both
  sides accept (FR24), the detail page and thread header gain a **two-button
  row** — "Call" (tel: link) and "WhatsApp" (wa.me with a prefilled, editable
  line: "Hi, I'm <name> from Vyapar about <title>") — equal weight, secondary
  style; the accent stays on the in-app primary. Desktop: same row in the
  thread header; WhatsApp opens Web.
- **Poster controls (settings + per post):** "When can people call?" — a
  from/to time chip pair (default 10:00–19:00) and days; "Calls per day" —
  a stepper (default 10, "Unlimited" for verified businesses). Outside hours,
  the caller sees "Available from 10 am — send a message instead" and the
  message button becomes primary; at the cap, the Call button disables with
  the same inline explanation. Store on the opportunity, override in
  settings.
- **Privacy:** show "Your number is shown only to people you accepted" once
  above the row. A proxy number (Exotel/Knowlarity class vendor) is the
  production path — log as an external-vendor blocker, build the UI now.

## 5. Two-level category → specialty picker; desktop mega-menu; outcome pages

**What the best products do.**

- **Fiverr gig setup:** category → subcategory → (some categories) service
  type → metadata chips; Fiverr _recommends_ subcategories from the chosen
  category ([fiverrtutorials.com/create-fiverr-gig](https://fiverrtutorials.com/create-fiverr-gig);
  help.fiverr.com pages 403).
- **WorkIndia onboarding (owner screenshots):** search box → picture-card
  multi-select of job types → skills grouped _by the type just chosen_.
- **Upwork mega-menu:** click-to-reveal (not hover) so it works on touch;
  narrow columns; groupings by user intent (Solutions / Industries / Roles),
  one-line descriptions under headings
  ([blog.logrocket.com/ux-design/mega-menu-design-examples](https://blog.logrocket.com/ux-design/mega-menu-design-examples/)).
- **Toptal "Hire Talent" menu:** each category carries a plain-language
  one-liner ("Seasoned software engineers, coders, and architects…")
  ([toptal.com](https://www.toptal.com/)). Both Upwork and Toptal run
  **"Hire a <role>" landing pages** — one role, one outcome, proof, CTA
  ([upwork.com/hire/landing-pages-freelancers](https://www.upwork.com/hire/landing-pages-freelancers/),
  [toptal.com/designers/landing-page](https://www.toptal.com/designers/landing-page)).

**Recommended Vyapar pattern.**

- **Picker, mobile:** step 1 a searchable 2-column grid of ~12 top categories
  (icon + name + one-liner, neutral tiles; selected tile gets the accent
  border only); step 2 a chip grid of specialties scoped to that category
  with "Other…" free text last. Search matches both levels at once and jumps
  straight to the specialty. Backed by the real taxonomy endpoint (closes the
  IntentBar hardcoded-list finding).
- **Picker, desktop:** a `.vy-pane` split — categories as a left list,
  specialties as chips on the right, keyboard ↑↓ and Enter (Linear).
- **Mega-menu (desktop ≥900):** two top items, **Hire** and **Find work**,
  opened on click. Three narrow columns: _By category_ (top 8 + "All"), _By
  outcome_ ("Get a website built", "Hire a delivery rider", "Find a tutor
  nearby"), _For you_ (Post an opportunity, Register your business). Every
  item is `name + one plain-language line`, `.vy-card-floating` surface, no
  imagery.
- **Outcome landing pages** (`/hire/<specialty>`, `/work/<specialty>`): H1 is
  the outcome, one line on how Vyapar does it (community-first, no fee), a
  `.vy-grid` of 6 matching listings or opportunities from the live feed, the
  count-based trust line, one primary CTA. Same template both directions.

## 6. Discover feed filters

**What the best products do.**

- Baymard: desktop → persistent left sidebar, results update instantly;
  mobile → full-screen overlay or bottom sheet from a **sticky "Filter &
  Sort" button**, with a prominent **"Show X results"** button rather than
  live refresh; result counts next to options are "one of the single
  highest-impact improvements"; collapse low-value groups by default
  ([baymard.com/blog/ecommerce-filter-ui](https://baymard.com/blog/ecommerce-filter-ui)).
  Applied filters must be visible as removable chips (28 % of sites fail
  this); on mobile a horizontally scrolling chip row with a truncation cue
  ([baymard.com/blog/how-to-design-applied-filters](https://baymard.com/blog/how-to-design-applied-filters)).
  Baymard's 2025 benchmark: 78 % of mobile sites have poor-to-mediocre
  filtering _(secondary: [uxpin.com/studio/blog/filter-ui-and-ux](https://www.uxpin.com/studio/blog/filter-ui-and-ux/))_.

**Recommended Vyapar pattern.**

- Keep the existing `FilterSheet` (radius 5/10/25/Any, mode, availability,
  verified-only, sort) and add: **Distance** as a chip row with counts
  ("Within 5 km (14)"), **Sort** as a segmented control (Relevance ·
  Nearest · Newest · Verified first), **Availability** (Now · This week ·
  Any). Sticky "Filters (2)" chip + "Show 14 results" primary button in the
  sheet footer; nothing applies until that tap.
- Desktop: the same groups in a `.vy-with-sidebar` rail, instant apply, no
  footer button. Applied filters render as removable neutral chips above the
  grid on both layouts. Sort is _not_ a filter — keep it in the toolbar.
- Zero results keep FR17's explicit broadening options ("Changed: radius →
  25 km"), never a silent relax.

## 7. Profile trust — count-based badges; tiered service packages

**What the best products do.**

- **Fiverr packages:** three tiers with name, description, price, delivery
  days, revisions, up to ~5 included features; buyers see a
  column-per-tier / row-per-attribute matrix with ✓ marks; recommended price
  ratio ≈1 : 2 : 3.5 ([laymanseo.com/tools/fiverr/fiverr-package-planner](https://www.laymanseo.com/tools/fiverr/fiverr-package-planner/),
  [fiverrtutorials.com/fiverr-gig-guide/pricing-packages-strategy](https://fiverrtutorials.com/fiverr-gig-guide/pricing-packages-strategy)).
- **Upwork Project Catalog:** Starter / Standard / Advanced with a "Compare
  tiers" side-by-side chart and add-ons _(secondary — support pages 403:
  [gigradar.io/blog/upwork-project-catalog-for-agencies](https://gigradar.io/blog/upwork-project-catalog-for-agencies))_.
- **Malt:** no bidding; profile leads with skills, project types, and
  recommendations; verified profile + insured projects as the trust line
  ([en.malt.fr](https://en.malt.fr/); [help.malt.com/…/29517405925778](https://help.malt.com/hc/en-us/articles/29517405925778-How-do-I-complete-and-modify-my-profile-on-Malt)).
- **Count-based trust:** specific numbers ("127 clients served", "N completed
  in the last 30 days") read as more credible than generic phrases; verified
  badges reduce perceived risk _(secondary: [tw3marketing.com/2026/09/13/website-trust-signals](https://tw3marketing.com/2026/09/13/website-trust-signals/),
  [regulaforensics.com/blog/freelancer-id-verification](https://regulaforensics.com/blog/freelancer-id-verification/))_.

**Recommended Vyapar pattern.**

- **Trust strip** under the profile name, one line, three axes kept
  visually distinct as today: verification badge (green, tappable →
  `TrustContextSheet`) · counts ("12 jobs completed · 4 repeat clients ·
  replies in ~2 h") · "Member since 2025". Badges are _earned counts_ with
  neutral pills: "10+ completed", "Repeat clients", "Responds fast" — no
  stars, no score.
- **Packages:** on mobile, three horizontally snapping `.vy-card` tiles
  (name, ₹, delivery, 3 bullet features) with the middle one pre-selected;
  "Compare" expands a `.vy-card-nested` matrix (rows: price, delivery,
  revisions, features ✓/—). Desktop shows the matrix directly in
  `.vy-detail-aside`. Selection uses the accent border only; "Enquire about
  Standard" is the single primary action.

## 8. Contracts & milestones — funded/held → submitted → approved

**What the best products do.**

- **Upwork fixed-price:** milestone states _Created (unfunded) → Funded (in
  escrow) → In review (after "Submit work") → Approved / Changes requested →
  Pending (5-day hold) → Available_; 14-day client review window with
  **auto-release on silence**; the clock starts only on the formal Submit
  button, not on a chat message _(secondary:
  [gigradar.io/blog/upwork-payment-protection-fixed-price](https://gigradar.io/blog/upwork-payment-protection-fixed-price);
  official: [support.upwork.com/…/211068218](https://support.upwork.com/hc/en-us/articles/211068218-How-to-use-milestones-in-fixed-price-jobs) — 403)_.
- **Owner screenshot:** Upwork's Contracts screen leads with "Earnings
  available now", then Active contracts with a one-sentence empty state and a
  single CTA (`references/upwork/README.md`).

**Recommended Vyapar pattern.**

- **Contract page = vertical timeline** in `.vy-detail-main`: one row per
  milestone with a small state dot on the ink ramp (hollow = not funded,
  filled neutral = held, accent = _needs your action_, green = paid). Each
  row: name · ₹ · due · state word · **one** context action for the current
  viewer (Fund · Submit work · Approve / Request changes · —). The aside shows
  the running totals: Held · Paid · Remaining, plus the review deadline
  ("Auto-approves in 6 days") as plain text.
- Vocabulary: _Held_ not "escrow"; _Submitted_ not "In review"; _Approved →
  Paid_. Request-changes requires a one-line reason and resets the window.
- Mobile: same timeline; the current-step action pinned as a sticky footer.
- Money movement itself is an external-vendor blocker (payment gateway /
  escrow rails in India); the UI ships with a "Held (recorded)" state until
  then.

## 9. Voice input in Indian languages

**What the best products do / the evidence.**

- **Web Speech API:** `lang` (e.g. `hi-IN`, `te-IN`), `interimResults` for a
  live caption, `isFinal` + `confidence` per result, error codes `no-speech`
  / `not-allowed` / `network`; Chrome sends audio to a server (no offline)
  except the optional on-device mode from Chrome 139
  ([developer.mozilla.org/…/SpeechRecognition](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition);
  _secondary:_ [medium.com/@roman_fedyskyi/on-device-speech-uis-in-chrome-139](https://medium.com/@roman_fedyskyi/on-device-speech-uis-in-chrome-139-4b9f0397b9c9)).
  Explicit `hi-IN`/`te-IN` quality on Chrome Android is **[unverified]**
  from fetched pages; a 2026 benchmark reports Google ASR WER ≈16 % Hindi,
  ≈33 % Telugu ([arxiv.org/pdf/2602.03868](https://arxiv.org/pdf/2602.03868)) —
  Telugu needs the confirm step more than Hindi.
- **FormBharo (2026):** voice form-filling for low-income Hindi speakers;
  end-to-end accuracy fell ~41 points on real speech vs clean transcripts,
  recovered by rule-based validation per field — i.e. **confirm per field,
  don't trust free speech** ([arxiv.org/abs/2608.06027](https://arxiv.org/abs/2608.06027)).
- **VUI practice:** four visible states (idle / listening / processing /
  confirmed), live transcript, explicit confirmation before commit, typed
  fallback always available, language switch in place
  ([aufaitux.com/blog/voice-user-interface-design-best-practices](https://www.aufaitux.com/blog/voice-user-interface-design-best-practices/)).
- **Bhashini** (GoI, 22 languages) is the national ASR fallback for
  languages Chrome handles poorly ([play.google.com/…/com.dibd.bhashini](https://play.google.com/store/apps/details?id=com.dibd.bhashini&hl=en_IN);
  [en.wikipedia.org/wiki/Bhashini](https://en.wikipedia.org/wiki/Bhashini)).
- Flipkart shipped Hindi/English voice search for the "next 200 million"
  users ([business-standard.com/…/flipkart-starts-voice-search…](https://www.business-standard.com/article/companies/flipkart-starts-voice-search-in-hindi-and-english-to-tap-next-200-mn-users-121030400751_1.html)).

**Recommended Vyapar pattern.**

- **One shared `VoiceInput` wrapper** for every `.vy-textarea`/`.vy-input`
  that accepts prose: a mic icon inside the field's trailing edge (neutral
  at rest; accent ring only while listening; a small dot pulsing in
  `--dur-move` for processing). Language follows the app locale; a tiny
  "हिं / తె / EN" chip next to the mic switches recognition language without
  leaving the field.
- **Live transcript** appears _in the field itself_ as interim text on
  `--text-secondary`; on final it turns `--text-primary` and a compact
  confirm row appears under the field: "Keep" (primary) · "Retry" · "Edit".
  Nothing is saved until Keep. For structured fields (salary, timings,
  locality) the transcript is parsed into the chip/number and the parsed
  value — not the raw text — is what the person confirms (FormBharo).
- **Errors:** `not-allowed` → inline "Allow the microphone in your browser"
  with the field still typeable; `no-speech` after 5 s → "Didn't catch that —
  tap and try again"; `network` → fall back to typing and, when built, to a
  Bhashini server call. Never a modal.
- Placement priority: §1 "say it in one line", §2 cover note / apply note,
  enquiry message, report/appeal text.

---

## Reading order for the build agent

1. §1 and §9 together (the composer _is_ the voice surface).
2. §2, then §3 (they share the match-reasons line and the compare matrix).
3. §4 (settings + thread header), §6 (extend `FilterSheet`), §5 (taxonomy
   endpoint first, then picker, then mega-menu, then landing template).
4. §7 and §8 last — both depend on payment rails logged as vendor blockers.

Everything above uses existing Vyapar primitives (`.vy-detail`, `.vy-pane`,
`.vy-with-sidebar`, `.vy-card-nested`, `.vy-card-floating`,
`.vy-chip[aria-pressed]`, `FilterSheet`, `FileUpload`, `TrustContextSheet`);
no new colour, no new surface effect, and the floating command hub stays.

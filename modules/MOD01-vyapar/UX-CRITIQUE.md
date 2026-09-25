# UX Critique — MOD01 Vyapar (Upwork / WorkIndia lens)

**Standing, repeatable document.** Re-run this critique after any meaningful change to
the screens below; update the relevant section in place rather than starting over.
Grounded strictly in what Vyapar's own sealed pipeline already committed to
(`03-ux.md`'s "Comparable applications" and "Product vocabulary" cross-flow
conventions, and FR22 DEC-002 in `02-functional-requirements.md`), plus targeted
live research to resolve details those sealed documents left open. This is a
verification pass against the product's own commitments, not a competing design
proposal.

**Last run:** 2026-09-17 (THIRD pass, same day — full-coverage sweep of every
screen listed in the module's screen inventory, not a sample). **Reviewer:** UX
critique agent (Upwork/WorkIndia persona).

---

## THIRD PASS (2026-09-17) — full-coverage verification sweep

This pass re-opened and re-read every file in `vyapar-web/app/**/*.tsx` (42 files)
plus their paired locale entries in `vyapar-web/locales/en/*.json` (the actual
frontend i18next tree — distinct from `vyapar-service/app/i18n/locales/`, which
holds only backend-emitted error/notification strings; a prior pass's "no
`privacyLine`/`safetyNotice` found" search had grepped the wrong tree). Every
finding below either (a) confirms a prior finding is now genuinely fixed, (b)
finds a prior "fix" is incomplete, or (c) is new this pass. Screens not
separately numbered below (Reviews, Partnerships-detail, Workspace/Campaigns,
Boost/Promotions beyond the confirmations noted) were re-read and found
unchanged from the prior pass's verdict — no regressions.

### Confirmed RESOLVED this pass (previously open, now genuinely fixed in code)

1. **Businesses directory Filters/Locality sheet (was Top-5 #2).**
   `app/components/FilterSheet.tsx` now exists — radius (5/10/25 km, "Any"),
   service mode, availability, verified-only, and sort-by (relevance/distance/
   freshness/verified-first), wired into `app/businesses/page.tsx` behind a
   "Filters" toggle button that shows an active-filter count. This is a real,
   structural restoration of FR15's filter acceptance criteria, not a relabel —
   `changeFilters` re-runs the search with the new filter state every time.
   Genuinely fixed.
2. **Listing Detail Trust context sheet (was Top-5 #5).** Re-confirmed:
   `TrustContextSheet` in `app/components/Verification.tsx` (lines 42-88) is a
   real modal — explains scope/date, "what this doesn't mean," and an optional
   Report link that scrolls to the in-place `ReportSheet` — wired to
   `VerificationBadge` via `onOpenTrustSheet` in both `listings/[id]/page.tsx`
   and `listings/mine`'s badge usage. Still no *sticky* footer on Listing
   Detail (this specific sub-item remains open, see below), but the trust-sheet
   gap itself is closed.
3. **Opportunity screenshot upload (was Top-5 #3).** `app/opportunities/new/page.tsx`'s
   upload mode now renders `<FileUpload accept="image/*" />` (a real
   `<input type="file">` → `POST /v1/uploads`, see `app/components/FileUpload.tsx`),
   not a pasted-URL field. The exact WhatsApp-forwarded-screenshot scenario FR11
   names is now actually usable. Genuinely fixed, and the same `FileUpload`
   component is now reused for the Propose attachment and the appeal evidence
   attachment (see #4 below) — one shared upload path, not three divergent ones.
4. **Enquiry composer Propose attachment + rate-type (was Top-5 #4).**
   `app/enquiries/new/page.tsx`'s Propose sub-flow now has a Fixed/Hourly radio
   toggle before the rate field and a `FileUpload` for a work-sample attachment.
   Both are real, wired fields feeding `finalMessage()`. Genuinely fixed.
5. **Verification queue reason code + public lookup link (was Screens-9-14
   Top-5 #1 and #2).** `app/admin/verification/page.tsx` now gates Reject and
   Needs-clearer-copy behind a mandatory `REASON_CODES` select (identical
   pattern to moderation's), and renders a real `PUBLIC_LOOKUP_URL` link
   (GST/Udyam public portals) per document type. Both genuinely fixed.
6. **Moderation prior-case history + appeal evidence attachment (was
   Screens-9-14 Top-5 #3 and #4).** `app/admin/moderation/page.tsx`'s
   `CaseCard` now renders `prior_case_history` (action, reason, date) behind an
   expand toggle, not a bare count. `app/moderation/outcomes/page.tsx`'s
   `OutcomeCard` now has a real `FileUpload` for optional appeal evidence, sent
   as `evidence_urls`. Both genuinely fixed.
7. **Boost audience category localization (was Screens-9-14 Top-5 #5).**
   `app/boost/[kind]/[id]/page.tsx` now renders `opts.audience.category_labels[i]`
   (the real translated taxonomy name) instead of `category.replace(/_/g, " ")`.
   Genuinely fixed.
8. **Admin Ops / Admin Commercial raw-enum leaks.** Both files' own code
   comments describe a "final sweep" that translated `opportunity.type`,
   taxonomy `kind`/`status`, and every other operator-facing enum via i18n
   keys with `defaultValue` fallbacks. Read in full this pass and confirmed —
   no raw enum renders directly in either file.

### Confirmed STILL OPEN (re-verified, not actually fixed despite appearing to be)

1. **HIGH — Enquiry composer's duplicate-enquiry recovery is dead code: the
   locale strings and state exist, but nothing renders them.**
   `app/enquiries/new/page.tsx`'s catch block correctly sets
   `duplicateEnquiryId` from the 409 response and calls
   `t("enquiries:compose.alreadyOpenWithName", ...)`. The locale keys are
   genuinely present and well-written —
   `vyapar-web/locales/en/enquiries.json`'s `compose.alreadyOpenWithName`
   ("You already have an open enquiry with {{name}}.") and `compose.openIt`
   ("Open it") both exist, clearly authored for exactly this recovery path.
   **But `duplicateEnquiryId` is never read anywhere in the component's JSX** —
   there is no button, no link, nothing that uses it. A member who hits this
   exact situation sees the error text but has no "Open it" affordance at all,
   even though the string for one was written. This is a half-applied fix:
   whoever wrote it built the state and the copy but never wired the render.
   Same root problem for the safety line: `compose.privacyLine` ("Your phone
   number is not shared. Replies arrive in Activity. Never pay in advance.")
   exists in the locale file, written specifically for this screen, and is
   never rendered anywhere in `enquiries/new/page.tsx`. **Fix:** add
   `{duplicateEnquiryId && <a className="vy-btn vy-btn-secondary" href={`/enquiries/${duplicateEnquiryId}`}>{t("enquiries:compose.openIt")}</a>}`
   next to the error message, and render `t("enquiries:compose.privacyLine")`
   once, near the Send button, for every action type.
2. **MEDIUM — FR55's safety line still doesn't appear on Opportunity Detail
   itself.** Confirmed again this pass: `app/opportunities/[id]/page.tsx` has
   no "never pay to apply" text anywhere in the file. The only place any
   version of this line exists is `enquiries:detail.safetyNotice` (shown on
   the enquiry thread, and only once contact is disclosed) and the
   still-unrendered `compose.privacyLine` above. UX09's own wireframe wants it
   visible on the detail screen, especially for Public/External items where
   the member is about to leave Vyapar entirely.
3. **MEDIUM — IntentBar's category/locality parsing is still a hardcoded
   14/14-item English list**, unchanged from the prior pass:
   `app/components/IntentBar.tsx`'s `KNOWN_CATEGORIES`/`KNOWN_LOCALITIES`
   arrays are the same fixed lists, not backed by the real taxonomy/locality
   endpoints. Notably, `app/first-run/page.tsx` (built more recently, see
   `capabilityOptions` fetched from `/v1/first-run/capability-options`) shows
   the correct pattern already exists elsewhere in the codebase — IntentBar
   just hasn't been updated to use it.
4. **MEDIUM — Activity screen rows are still bare titles with no state.**
   Re-confirmed: `app/activity/page.tsx`'s `ActivityItem` interface has only
   `kind/id/title/group` — no status/state field at all, so there is nothing
   for the row to show even if the JSX wanted to. Every neighbouring list this
   pass found (Enquiries/mine, Businesses, Discover, My Listings) resolves
   state/freshness/counterpart into the row; Activity is now the one list in
   the app that doesn't, and it needs a backend field addition
   (`/v1/activity`'s response), not just a frontend change.
5. **LOW-MEDIUM — Discover feed cards still have no overflow menu.**
   Re-confirmed via `app/components/LivingCard.tsx`: the shared card component
   has no "⋯" affordance and no prop for one. UX08 names Not interested/Share/
   Report as a per-card overflow on the feed; today only Opportunity Detail
   has "Not interested," so a member must open the detail screen to hide
   something they don't want to see on Discover.
6. **LOW — Listing Detail's "Enquire Now" action row is still not a sticky
   footer.** Re-confirmed in `app/listings/[id]/page.tsx`: the action row
   (lines 216-254) is inline in normal scroll flow, not pinned. UX07 names a
   sticky footer explicitly. Minor relative to the trust-sheet fix already
   landed.
7. **LOW — Sponsored placement on Discover home is still a separate block,
   not interleaved.** Re-confirmed in `app/page.tsx` (`feed?.sponsored?.map`
   renders before the `sections.map`). As noted last pass, this is a genuine
   doc-gap (UX08 doesn't state an interleaving rule the way UX06 does for
   Businesses results) rather than a code bug — still worth closing in UX08.

### New this pass

1. **MEDIUM — Listing creation (`app/listings/new/page.tsx`) still forces
   free-text typing for categories/capabilities that a sibling screen has
   already solved with tap-only chips.** `app/first-run/page.tsx` (step 2,
   `step2cap`) fetches the real taxonomy via
   `/v1/first-run/capability-options` and renders it as a multi-select chip
   grid with an "other" free-text fallback — exactly the "structured choices
   plus free text" pattern FR44 names and the product owner's forced-typing
   rule wants. `app/listings/new/page.tsx` — the screen that creates the very
   listing FR01/FR04 govern, arguably higher-stakes than first-run's own
   capability step — still has the member type a comma-separated string into
   a plain `<input>` for `categories` and `capabilities`
   (`splitList(categories)`/`splitList(capabilities)`, lines 45-46, 128-137).
   The same taxonomy endpoint that already powers first-run's chips could
   power this screen's chips too; today the two screens disagree on how the
   identical underlying data (taxonomy capability slugs) should be captured,
   and the higher-stakes screen is the one still requiring typing.
   **Fix:** reuse `/v1/first-run/capability-options` (or the equivalent
   category-taxonomy endpoint) to render chip multi-selects on
   `listings/new`, keeping the free-text field only as the "other" overflow,
   matching first-run's own already-built pattern.
2. **Confirmed clean — no raw-enum leaks found in any newly-read screen this
   pass.** Explicitly checked: `app/opportunities/[id]/page.tsx`'s
   `work_mode` (translated via `opportunities:workMode.<value>`, with its own
   code comment naming the bug class), `app/admin/ops/page.tsx`'s
   `opportunity.type` and taxonomy `kind`/`status` (both translated with
   `defaultValue` fallbacks per their own "final sweep" comments),
   `app/enquiries/mine/page.tsx`'s `action_type`/`state` (both resolved via
   `STATE_KEY`/`actionType.*`, replacing a previously-live bug the file's own
   comment names — "this row used to render literally as 'enquire · open'").
   The class of bug this critique has repeatedly flagged appears to have had
   a genuine, systematic cleanup pass run against it since the last critique
   run, not just spot fixes.
3. **Confirmed clean — no forced-typing-before-one-tap violations found
   beyond what's already documented (FR25's five required fields).** Every
   other compose/action screen read this pass (Report, Appeal, Boost confirm,
   Refund, first-run) either offers a real one-tap default or explains why
   typing is the sealed requirement itself.

---
**Code read (first pass):** `vyapar-web/app/page.tsx`, `app/businesses/page.tsx`,
`app/listings/[id]/page.tsx`, `app/opportunities/[id]/page.tsx`,
`app/opportunities/new/page.tsx`, `app/post/page.tsx`, `app/enquiries/new/page.tsx`,
`app/activity/page.tsx`, `app/profile/page.tsx`, `app/components/IntentBar.tsx`, plus
`locales/en/enquiries.json`. Sealed docs read: `02-functional-requirements.md` FR01–FR29
in full, `03-ux.md` cross-flow conventions and UX01–UX13 in full.
**Code read (second pass, this run):** `app/components/Verification.tsx`,
`app/admin/verification/page.tsx`, `app/admin/moderation/page.tsx`,
`app/moderation/outcomes/page.tsx`, `app/components/Reputation.tsx`,
`app/components/ReviewComposer.tsx`, `app/components/ReportSheet.tsx`,
`app/partnerships/new/page.tsx`, `app/partnerships/[id]/page.tsx`,
`app/boost/[kind]/[id]/page.tsx`, `app/promotions/page.tsx`, `app/promotions/[id]/page.tsx`,
`app/components/PerformanceReport.tsx`, `app/workspace/[listingId]/page.tsx`,
`app/campaigns/[id]/page.tsx`, plus `vyapar-service/app/routers/verification.py` and
locale parity checks across `locales/{en,hi,te}/{verification,trustSafety,commercial}.json`.
Sealed docs read this pass: FR08–FR10, FR25–FR35, FR39–FR41 in full from
`02-functional-requirements.md`.

---

## What the sealed docs already committed to (baseline, not my invention)

- **Comparable-app research is real and cited in `03-ux.md`.** Vyapar's *primary* peer
  set is Indian community apps (Brahmakshatriya Samaj – Khatri, Mera Samaj, Kutumb) —
  business directory as a first-class destination, "Register your business",
  consented contact after acceptance. **Feature-level** comparables — Sulekha, Urban
  Company, Apna, Naukri, Upwork, IndiaMART — are explicitly scoped as valid only for
  individual action words and specific patterns ("learn from comparable products, but
  must not copy their mental model" — PM Planning P1.5, cited in UX06).
- **FR22 DEC-002** fixes the exact label-per-type vocabulary and its sources: Enquire
  Now (Sulekha), Apply (Naukri/Apna), Submit a Proposal (Upwork,
  support.upwork.com/hc/en-us/articles/211062998), Contact (IndiaMART), Register
  (portal convention), Apply on source website (Naukri's "Apply on Company Website").
  This is a **label decision**, not a field-structure decision.
- **UX12's sealed Compose-enquiry wireframe is itself generic.** Re-reading it closely:
  for a listing, it adds two chips ("Ask a question" / "Request a quote"); for *every
  opportunity type* it specifies only "fixed type shown as text" + one Textarea "Your
  message" (20–1000 chars) + optional attachment. UX12 does **not** sealed-spec a
  separate rate/timeline pair for Propose, nor a profile-recap for Apply — that
  structure is not in the approved UX flow. This matters for the verdict below: the
  2026-09-17 rewrite of `enquiries/new/page.tsx` is *better* than the sealed UX12 spec
  (closer to real Upwork/WorkIndia), but it is now **ahead of, not conformant with,**
  the Sealed UX12 document. UX12 should be updated to match the code, or the code's
  extra structure should be pulled back — right now the two disagree and only the code
  was checked into this critique's scope.
- **UX06/UX07's research is Sulekha-grounded** (verification wording, "Enquire Now",
  "Responds In 15 Mins", filters), explicitly rejecting star ratings/aggregate scores
  per FR28.
- **UX08/UX09 are Apna-grounded** for card anatomy and type-specific detail sections.

Supplementary live research done for this pass (fills gaps the sealed docs left open —
exact field layouts, not the peer choice itself):

- Upwork's live proposal screen: cover letter + a separately editable rate + project
  duration/timeline, work samples/portfolio links, an AI "Get tips" affordance, and a
  boost/Connects option (support.upwork.com/hc/en-us/articles/211062998-How-to-submit-a-proposal-on-Upwork,
  support.upwork.com/hc/en-us/articles/211060388-Edit-your-proposal).
- Upwork's job-post screen: title, skills, scope, fixed/hourly budget, description —
  read to check Vyapar's own opposite-side Composer (upwork.com/resources/how-to-post-job-on-upwork).
- WorkIndia / comparable blue-collar apps: near-zero-typing apply, profile-as-application,
  30-second registration (Play Store listing; Blueforce.app's explicit "one-tap
  application, no resume, no cover letter, profile auto-fills the application" as the
  named pattern this class of app is judged against). WorkIndia's own site returned 403
  in the sealed docs' research and again here — not opened, cited only via secondary
  sources, exactly as the sealed docs already flagged.
- Marketplace trust-signal research: verification badges materially reduce perceived
  risk and dispute rates in P2P marketplaces (multiple UX-practice sources); low-
  literacy/low-tech-literacy gig workers specifically benefit from photograph-based
  input over typed input and from never being trapped without a back path — both
  directly relevant to Vyapar's Apply/Register flows.

---

## Screen 1 — Home / Discover feed (`app/page.tsx`)

**Reference:** UX08 (Apna-grounded, sections + IntentBar-style search-first home per
the coordinator's 2026-09-15 fix). **Verdict: matches research, with one vocabulary
slip.**

- The five-section structure (For You / Explore / Near You / Community / Public), the
  `IntentBar` at the top, freshness stamps, source segment + submitter, and the
  one-line relevance reason are all present and match FR18/UX08 field-by-field. This is
  a genuine structural match, not a relabelled list.
- `discover:home.openDirectory` button correctly routes to `/businesses` and sits above
  the fold — matches the "no-scrolling-burden" fix and UX08's cross-link card.
- **Gap vs. UX08's sealed wireframe:** UX08 specifies a `Sponsored` label is used
  **as text** and confined to an eligible audience, inserted as an additional card,
  never swapping an organic slot. The code (`feed?.sponsored?.map`) renders sponsored
  cards in their own block above all sections, not woven in "after every 5 organic
  cards" the way UX06 describes for Businesses results. For opportunities, UX08 doesn't
  explicitly require the interleaving rule UX06 states for listings, so this is a
  minor doc-gap rather than a code bug — flag for UX08 to state the sponsored placement
  rule explicitly, the way UX06 does.
- **Missing:** the "Not sure yet" enrichment card path (FR18 sparse-profile fallback)
  is present (`enrichment_prompt`), good — but there is no visible "Not interested" affordance
  on the home cards themselves (`LivingCard` doesn't expose an overflow menu here); UX08
  specifies overflow "⋯" → Not interested / Share / Report on every card. That control
  only exists on the Opportunity Detail page today, not on the feed card. **Fix:** add
  the overflow menu to `LivingCard` on the Discover feed, per UX08's card wireframe —
  today a member must open the detail screen to hide something they don't want to see,
  which contradicts Apna's and every comparable app's list-level filtering ergonomics.

## Screen 2 — Businesses & Professionals directory (`app/businesses/page.tsx`)

**Reference:** UX06 (Sulekha/Urban Company-grounded). **Verdict: matches research
structurally, generic-in-disguise on filters.**

- IntentBar-first search, sponsored slot, verification label, reputation line, relevance
  reason — all present and correctly wired to FR15/FR28's exact vocabulary (no star
  average, `New on Vyapar` fallback via `useReputationText`).
- Zero-result broadening (`broadening_options`, explicit "Changed" semantics via
  `applyBroadening`) matches FR17's "never silently relax a hard filter" rule and UX06's
  wireframe closely — a real structural match, not cosmetic.
- **Gap:** UX06 specifies a dedicated **Filters sheet** (distance / service mode /
  availability / verification / freshness, with a live "Show N results" count) reachable
  from a "Filters" chip with a count badge, plus a separate **Locality sheet** ("Use my
  location", radius stepper). Neither exists in `businesses/page.tsx` — the only input
  is the single `IntentBar` free-text field with client-side keyword matching against a
  small hardcoded list (`KNOWN_CATEGORIES`, `KNOWN_LOCALITIES` in `IntentBar.tsx`).
  A member cannot set a radius, service mode, "verified only", or a freshness filter
  through any UI control today — those are FR15 acceptance criteria ("filter by
  locality/radius, service mode, availability, verification state, and freshness") that
  the sealed UX06 screen renders as sheets and the actual code does not expose at all.
  This is the one place where the "fewer taps" design direction has gone past
  simplification into **removing FR15-required capability**, not just deferring its UI.
  **Fix:** add the Filters and Locality sheets from UX06 (they don't need to reappear
  as four dropdowns — a single bottom sheet with the five groups, exactly as UX06
  specifies, keeps the fewer-taps ethos while restoring FR15 compliance).
- `KNOWN_CATEGORIES`/`KNOWN_LOCALITIES` are a fixed 14/14-item English list baked into
  the component, not the platform taxonomy (FR48). This will misparse or silently drop
  the category/locality signal for anything outside those lists (e.g. "tailor",
  "caterer", any Hindi/Telugu locality name) — a real functional gap behind the
  "conversational" UI, not just cosmetic. **Fix:** back `IntentBar`'s parsing with the
  real taxonomy/locality endpoints, or at minimum expand + localize the lists.

## Screen 3 — Listing Detail (`app/listings/[id]/page.tsx`)

**Reference:** UX07 (Sulekha-grounded trust framing). **Verdict: matches research.**

- Verification badge, reputation line, "member-provided" tagging, per-channel contact
  disclosure display, credential reference (FR06), review list, Enquire Now / Save /
  Share / Propose partnership — all present and structurally correct, not relabelled
  generic components. `VerificationBadge`/`ReputationLine` are dedicated components
  matching the exact trust-label vocabulary from `03-ux.md`'s cross-flow conventions
  table (`Business existence verified (…) · date`, `New on Vyapar`, counts-not-stars).
- Share uses the Web Share API with a clipboard fallback exactly as UX07/cross-flow
  convention (5) specifies.
- **Gap:** UX07's sealed wireframe specifies a **Trust context sheet** ("What was
  checked" — explains scope/date/expiry, "what this doesn't mean," a Report link) reached
  by tapping the trust block. The code renders `VerificationBadge` inline but there is
  no separate sheet/detail affordance visible in this file (would need to confirm inside
  `Verification.tsx`, not read this pass — flag for the next run of this critique to
  check `VerificationPanel`/`VerificationBadge` directly). If that sheet doesn't exist,
  a customer has no way to learn *what* was actually checked before contacting a
  provider — this is exactly the trust-signal gap the P2P-marketplace research flags as
  reducing conversion/disputes, and it's a named, sealed UX07 requirement, not a
  nice-to-have.
- The sticky "Enquire Now" footer the sealed UX07 wireframe specifies (primary button
  pinned above the safe area, bottom nav hidden on detail) is not implemented as sticky
  — the action row is inline in normal scroll flow. Minor relative to the trust-sheet
  gap, but worth a CSS fix since it's an explicit UX07 requirement ("Sticky footer").

## Screen 4 — Opportunity Detail (`app/opportunities/[id]/page.tsx`)

**Reference:** UX09 (Apna-grounded). **Verdict: matches research well.**

- Type-adapted primary action reading the server's `type_action_label` (never a second
  front-end mapping) is exactly UX09 DEC-003's intent and avoids the classic
  "label says Apply, everything else is generic" trap.
- "Apply on source website" vs. "Open official website" distinction for Public/External
  items by type — correctly implements UX09 DEC-001 (Naukri's "Apply on Company
  Website" pattern), not a made-up label.
- "Why this?" sheet with top-N signals, gap line, and a distinct sponsored-disclosure
  sentence ("shown to more people because…") — matches FR20/UX09 exactly, including the
  "never a percentage" rule.
- Not-interested with the seven structured reasons (`NOT_INTERESTED_REASON_KEYS`)
  matches FR55/UX09's radio list verbatim.
- **Gap:** UX09 specifies the primary action sits in a **sticky footer** alongside a
  Save icon button, and the safety line ("Never pay to apply…") is always visible on
  the page, not only inside the enquiry composer. The safety line does not appear on
  this detail screen at all in the code read — only inside `enquiries/new` (`compose.help`
  strings), and only for some action types. **Fix:** render the FR55 safety line on
  Opportunity Detail itself, per UX09's wireframe, especially for Public/External items
  where it matters most (member is about to leave Vyapar).

## Screen 5 — Enquiry / Response composer (`app/enquiries/new/page.tsx`)

This is the screen explicitly called out as just rewritten — judged in most depth.
**Reference:** UX12 (sealed) is a single generic textarea + listing-only chips; the
rewrite instead builds four distinct structured sub-UIs referencing Upwork/WorkIndia by
name in its own comments. **Verdict: genuinely closer to the real reference apps than
the sealed spec — but not fully structural yet, and now diverges from Sealed UX12.**

Per sub-flow:

- **Propose (Freelance/Project → Upwork).** Rate + timeline + cover letter as three
  separate fields matches Upwork's real proposal screen structurally (cover letter,
  editable rate, editable timeline — support.upwork.com/hc/en-us/articles/211062998).
  This is a real structural match, not cosmetic. **What's still missing against the
  live Upwork screen:** (1) no work-sample/portfolio attachment option, even though
  FR22 explicitly allows a ≤5MB attachment on every enquiry type and Upwork's own
  screen foregrounds "add work samples" — the attachment control exists nowhere in this
  file for *any* action type, including Propose where it matters most; (2) the rate
  field is a single free-text input with no unit/type distinction (fixed vs. hourly),
  so "₹45,000" and "₹800/hr" are indistinguishable data — Upwork forces this choice
  structurally because it changes what the client compares across proposals. **Fix:**
  add a file input (reuse the existing `<input type="file">` pattern from the
  verification screens) and a rate-type radio (Fixed / Hourly) before the amount field.
- **Apply (Employment → WorkIndia).** The "your profile is the application" pattern
  (`myListing.capability_labels`, `yourExperience`) plus a canned `applyDefaultNote`
  that satisfies the 20-character minimum with zero typing is a genuine structural
  match to WorkIndia's near-zero-typing apply flow, confirmed by the locale strings
  (`applyDefaultNote: "Applying via Vyapar — please see my capabilities above…"`). This
  is the single best-matched sub-flow in the app to its stated reference. One caveat:
  if the member has no professional listing at all (`myListing` null), the screen shows
  "No experience listed yet — add it on your professional listing" but still lets them
  apply with just the default note — a labourer with a thin/no profile can still apply
  in one tap, which is correct for the audience, but nothing on this screen offers the
  one-tap "add your capability now" shortcut WorkIndia-style apps use to close that gap
  before the employer sees an empty profile. **Fix:** when `myListing` is null or empty,
  show a one-tap "add what you can do" affordance inline (not a separate onboarding
  flow) rather than only the passive "add it on your professional listing" sentence.
- **Enquire (Listing/Local-service → Sulekha/IndiaMART).** "Ask a question" / "Request a
  quote" chips that pre-seed the message text — matches UX12's own sealed spec for
  listings (the one place UX12 *does* specify structure) and IndiaMART's request-a-quote
  convention cited in the cross-flow vocabulary. Correct.
- **Register (Training/Community-Government).** One-tap-first with an optional note —
  reasonable, no strong reference-app pattern contradicts it, matches UX12's "fixed type
  shown as text" minimalism.
- **Cross-cutting gaps against UX12's own sealed wireframe** (independent of the
  Upwork/WorkIndia framing): (1) no live character counter ("0/1000 · at least 20") —
  UX12 explicitly specifies one; the plain textarea gives no feedback until submit is
  attempted; (2) no context card showing the target's trust label (UX12: "target
  name/title, one-line summary, trust label"); today only a plain `<p>` with the name;
  (3) the privacy/safety line ("Your phone number is not shared. Replies arrive in
  Activity. Never pay in advance.") from UX12's wireframe is absent for every action
  type; (4) the specific blocker copy UX12 mandates ("You've sent 20 enquiries today…",
  "You already have an open enquiry with <name>." + an "Open it" link to the existing
  thread) is not implemented — the code falls back to a generic `ApiError` message with
  no link to the existing thread, which is worse than UX12's spec for the exact
  situation (duplicate enquiry) most likely to frustrate a member. **Fix (highest
  priority of this section):** add the live character counter, the trust-labelled
  context card, the safety line, and — most importantly — parse the daily-cap/duplicate
  error into UX12's specific copy with a real link to the existing thread; today a
  member who already has an open enquiry gets a dead-end generic error instead of a way
  to their existing conversation.

## Screen 6 — Post / Opportunity Composer (`app/post/page.tsx`, `app/opportunities/new/page.tsx`)

**Reference:** UX10 (Vyapar_02-derived), with Upwork's job-post screen and WorkIndia's
minimal-typing posting as the supplementary comparables. **Verdict: matches research,
correctly graded by type.**

- The 2026-09-15 fix that added a `skillsLabel` field is well-reasoned in its own code
  comment: Upwork's post-a-job flow has a distinct skills/experience/budget step before
  publish, and Vyapar's ranking (FR19 `capability_fit`) needs that data — so adding it
  serves both the reference pattern and the actual ranking signal, not just visual
  parity. This is the single best example in the codebase of "grounded in a cited
  pattern, not invented" reasoning, and it deliberately keeps the field optional and
  singular precisely because WorkIndia's low-typing case (local_service/community posts)
  shouldn't be forced through Upwork's full multi-field wizard. This is correct
  audience-differentiated design, not a copy-paste of either reference.
- Segment tag (Community/Public), source-name-required-when-public, and the
  Create/Share/Upload three-mode chooser all match FR11/UX10.
- **Gap vs. UX10's sealed spec:** the **Review & Publish "Here's what we understood"**
  screen — where inferred/uncertain fields are marked `Unconfirmed` and must be
  confirmed before publish (FR12, a Must-priority acceptance criterion) — does not
  appear in this file. The code posts directly to `/v1/opportunities` and routes
  straight to the detail page, where the `is_poster && state === "draft"` block in
  `opportunities/[id]/page.tsx` does show unconfirmed-field confirmation — so the
  requirement is met, just relocated onto the detail screen rather than as UX10's
  dedicated interstitial Review screen. That's a legitimate implementation choice as
  long as it's consistent, but the raw-input preservation UX10 requires ("Collapsible
  'Original message / screenshot'") is not visible on the detail page in the code read
  — worth confirming on the next pass whether `raw_input`/`raw_image_url` are ever shown
  back to the contributor anywhere, since FR11 requires the raw input be preserved and
  UX10 requires it be visibly re-checkable.
- **Real functional gap, not cosmetic:** "Upload a screenshot" takes a pasted image
  **URL**, not a file upload, with an honest code comment explaining why (no Object
  Storage wiring yet). This is disclosed, not hidden, which is the right way to carry a
  known gap — but it means the FR11 acceptance criterion "Upload a screenshot image
  ≤5MB" (the single most WorkIndia-native input method — "photograph your job/resume
  instead of typing it," per the low-literacy gig-worker research above) is not actually
  buildable by the audience most likely to want it: someone who received a WhatsApp
  forward as an image, not a URL. **Fix priority: high** — this is the literal scenario
  FR11's intent paragraph names ("WhatsApp forwards become structured inputs"), and the
  current control cannot ingest a WhatsApp-forwarded image at all without the member
  first uploading it somewhere else to get a URL, which defeats the point.

## Screen 7 — Activity (`app/activity/page.tsx`)

**Reference:** UX11/FR55. **Verdict: matches research, minimally.**

- All eight groups implemented (to_review, responded, partnerships, saved, posted,
  recently_viewed, shared, completed) — a superset of FR55's six named groups, correctly
  extended for FR26/FR27's Activity requirements.
- **Gap:** every row is a plain title-only `<a>` card. UX11 (not read in full this pass,
  but referenced consistently across UX09/UX10/UX12 as showing state chips, freshness,
  and thread status inline) implies each Activity row should carry enough context to
  act without opening the item — e.g. an enquiry's current state, an opportunity's
  freshness/stale flag. Today a member sees only a bare title with no state, which turns
  Activity into a plain list rather than the "manage everything you've acted on"
  control surface FR55 intends. **Fix:** surface at least the state/status field already
  returned by each detail endpoint on the Activity row itself.

## Screen 8 — Profile (`app/profile/page.tsx`)

**Reference:** UX13 (compact rows, not full-size cards, per the "2040/no-scroll-burden"
correction). **Verdict: matches research.**

- Compact link rows (`memberLinks`/`operatorLinks`) rather than large cards, exactly per
  the standing "primary choices visible on first screen without scrolling" correction,
  and operator links are conditionally rendered per permission so ordinary members never
  see a 403-bound link — a real access-control-aware detail, not just visual tidiness.
- Workspace invite accept/decline inline — matches FR34's "team invitation is an
  account-level decision" comment.
- Not fully read this pass (language switch, "Back to ForKhatri" exit, help/grievance
  entry per UX13) — flag for the next run to confirm those exist, since UX13 names them
  as P0 elements and they weren't visible in the first 80 lines read.

## Screen 9 — Verification (`app/components/Verification.tsx`, `app/admin/verification/page.tsx`)

**Reference:** FR08/FR09/FR10, UX07. **Verdict: the member-facing half is excellent
(and resolves last pass's open question); the operator queue has two real FR47 gaps.**

- **Resolved from last pass:** `Verification.tsx` now contains `TrustContextSheet` —
  exactly the "what was checked / what this doesn't mean / Report" modal UX07 named and
  last pass could not confirm existed. It's wired as a single shared component reached
  by tapping `VerificationBadge`, correctly scoped per FR10's eight-state vocabulary
  (`DOC_KEY`, `sheetExplain.<state>`), and its own code comment explicitly credits this
  critique's prior finding. This is a genuine fix, not a relabel — closes item 5 of the
  previous Top 5.
- `VerificationPanel`'s one-document-per-request flow (options gated by `kind`, no
  Aadhaar anywhere in the option list, credential name+issuer required only for
  `credential`) matches FR08/FR09 exactly, including hiding the form while a request is
  pending (`latest?.state === "pending"`) rather than allowing a duplicate submission.
- **Gap 1 (high): the operator queue has no way to enter a reason code on Reject or
  Needs-clearer-copy.** `admin/verification/page.tsx`'s `decide()` posts
  `{}` — no `reason_code` field at all — for every one of the three actions, even
  though FR47's own acceptance criterion is "Verify / Reject (reason) / Needs clearer
  copy" and FR08's is "Operator Reject with reason." Contrast this with the sibling
  moderation queue (`admin/moderation/page.tsx`), which correctly requires a
  `REASON_CODES` select before its Apply button is even enabled. The consequence is
  concrete: `verification.json`'s own rejected-state copy is `"reasonLabel": "reason:
  {{reason}}"`, and today that will always interpolate `null`/`undefined` because the
  UI has no control to set it. **Fix:** add the same reason-select-before-enabling
  pattern from the moderation queue to the three verification decision buttons.
- **Gap 2 (high): no public-registry lookup link.** FR47's acceptance criteria
  explicitly names "Lookup link where applicable" (i.e., to the public GST/Udyam
  portal), and FR08's DEC-001 chose *manual operator lookup against public GST/Udyam
  portals* over a paid KYC API specifically as the V1 verification method — that
  decision's entire mechanism depends on the operator actually being able to reach the
  registry from this screen. `admin/verification/page.tsx` shows only the masked
  identifier and (if present) the uploaded image; there is no lookup link anywhere in
  the file. Without it, an operator has no way to do the manual check DEC-001 committed
  to, and Verify/Reject decisions reduce to eyeballing a masked string. **Fix:** add a
  computed link per `document_type` (GST/Udyam have public search portals; PAN and
  Shops & Establishment don't — show plain text for those) next to each queue card.

## Screen 10 — Moderation (`app/admin/moderation/page.tsx`, `app/moderation/outcomes/page.tsx`)

**Reference:** FR39/FR40/FR41. **Verdict: the best-built operator surface in the app;
one real FR40 gap, one real FR41 gap.**

- Both `decide()` (case) and `decide()` (appeal) correctly gate their action buttons on
  a chosen `reasonCode` — exactly the "mandatory reason code" FR40 requires, and the
  contrast with Screen 9 above shows this pattern was deliberately built once and not
  reused. Severity styling, overdue flagging, evidence-as-read-only display (no edit
  path anywhere in the file, matching FR40's "operators cannot edit evidence"), and the
  six graduated actions all match FR40 field-for-field.
- `moderation/outcomes/page.tsx`'s appeal flow correctly enforces "one Appeal" (button
  disappears once `appeal_state` is set), shows the appeal deadline and grievance
  channel per FR41/FR53, and opens in place on the card rather than a separate screen.
- **Gap 1 (medium): FR40's "history" acceptance criterion is only a bare count.**
  `CaseCard` shows `item.prior_cases` as a number (`· {{n}} prior cases`) with no way to
  actually see what those prior cases were — no reason, action, or date for any of
  them. FR40 requires operators see "the object, evidence, severity … and history"
  before deciding; a raw count doesn't let an operator distinguish "one dismissed false
  report six months ago" from "two upheld removals last week," which is exactly the
  distinction graduated-response moderation depends on. **Fix:** expand `prior_cases`
  from a count into a small expandable list (action, reason code, date) on the card.
- **Gap 2 (medium): FR41's "optional evidence" on an appeal has no control.** The
  requirement text is explicit — "up to 1000 characters, optional evidence" — but
  `OutcomesPage`'s appeal form is a single `<textarea>` with no attachment/evidence
  input anywhere in the file. A member appealing "this listing isn't a scam" has no way
  to attach the proof the spec itself names as part of the appeal. **Fix:** reuse the
  existing file-input pattern from `Verification.tsx`/`opportunities/new` for one
  optional evidence attachment on the appeal form.

## Screen 11 — Reviews (`app/components/Reputation.tsx`, `app/components/ReviewComposer.tsx`)

**Reference:** FR27/FR28/FR29, UX16. **Verdict: matches research closely, no bugs found.**

- `ReviewComposer` correctly gates on the server-reported `can_review`/`already_reviewed`
  invite status rather than re-deriving eligibility client-side, enforces the comment's
  "optional, but 20-500 if present" rule (`commentValid`), caps tags at 3
  (`toggleTag`'s `current.length < 3` guard), and uses a per-open `Idempotency-Key` so a
  double-tap files one review — all matching FR27 exactly.
- `ReviewList`'s subject-only, no-edit, one-tap-into-radio-chips Dispute flow matches
  FR29's "Dispute this review" with no edit/hide control for the subject, and its own
  code comment names the deliberate structural absence (`SP029`).
- `useReputationText`'s day-count singular-form fix (explicit `days === 1` branch rather
  than relying on i18next pluralization) is a real, well-reasoned grammar fix — the kind
  of detail this class of bug (raw/awkward interpolation) usually gets wrong, handled
  correctly here.
- No raw enum leakage found: every `tag.*` interpolation carries a `defaultValue`
  fallback to the raw tag only if the translation key is missing, which is the correct
  degrade-gracefully pattern (not the bug pattern of *always* rendering the raw value).

## Screen 12 — Partnerships (`app/partnerships/new/page.tsx`, `app/partnerships/[id]/page.tsx`)

**Reference:** FR25/FR26, UX17. **Verdict: matches research; heavier typing than the
2040 direction generally favours, but it's what FR25 itself requires, not a code
choice.**

- FR25 mandates five distinct 10-500 character fields (need/offer/expectations/
  timing/next_step) plus category/locality — `partnerships/new/page.tsx` implements
  exactly those fields with exactly that minimum, correctly disables Send until every
  field clears its own minimum (`valid` computed per-field, not a single blob check),
  and shows a live per-field counter/hint. This is forced typing, but it's the sealed
  FR25 acceptance criterion itself, not a screen inventing extra typing beyond spec —
  worth flagging to the product owner as a design-direction tension (five required
  long-text fields is a lot for a "2040, fewer taps" product) but not a code bug.
- `partnerships/[id]/page.tsx` correctly restricts each action to the matching role and
  state (`!request.is_sender && pending` for Accept/Decline, `request.is_sender &&
  pending` for Withdraw), discloses contact only once `disclosed_contacts.length > 0`
  (i.e., only after Accept, per FR26), and shows the 30-day resend-cooldown notice only
  for the sender on a Declined request — all matching FR26's state table precisely.
  `ReviewComposer` appearing only once `state === "closed"` correctly gates FR27
  eligibility on the exact interaction FR27 names.
- One real but minor gap: FR25's failure path says "recipient has disabled partnership
  requests → action hidden" — this file can't be checked against that rule since it
  lives on the *sender's* compose screen and the listing-detail "Propose partnership"
  button (not reviewed this pass); flag for a future pass to confirm that opt-out is
  actually respected where the button lives.

## Screen 13 — Promotions / Boost (`app/boost/[kind]/[id]/page.tsx`, `app/promotions/page.tsx`, `app/promotions/[id]/page.tsx`, `app/components/PerformanceReport.tsx`)

**Reference:** FR30/FR31/FR32, UX20. **Verdict: the strongest commercial-flow match in
the app — one real i18n leak.**

- The boost confirmation screen's disclosure list (product, price, tax, credit, total,
  starts/ends, what changes, what doesn't, renewal, refund, receipt) is a field-for-
  field match to FR30's "price including tax and what the boost does and does not
  change" and FR54's full-disclosure requirement, on the one screen UX20 calls for
  fewer taps around. "No reach estimate is shown" is called out by name in the code
  comment with its own DEC-001 citation — a real, sourced restraint, not an omission.
- `promotions/[id]/page.tsx`'s poll-until-webhook pattern (re-reads the order every 3s
  while `payment_state === "pending"`, capped at 10 tries) is a legitimate, disclosed
  way to handle the FR31 Awaiting-Payment → Active transition without the member
  staring at a spinner past the async webhook.
- `PerformanceReport`'s five separate counts, `boosted`/`organic` split shown only when
  `comparable` is true, and the "too little data" fallback below 10 impressions are a
  precise implementation of FR32's exact acceptance criteria, including "no
  projections/guarantees/causal language" — there is genuinely no such copy anywhere in
  the component.
- **Gap (medium): the boost audience "Only for {{category}}" chip is not actually
  translated.** `boost/[kind]/[id]/page.tsx` builds the chip label with
  `category.replace(/_/g, " ")` — a raw taxonomy value with underscores swapped for
  spaces, not a lookup against `commercial:onlyCategory`'s translated category name.
  Every other string on this screen is correctly localized (`commercial.json` has full
  en/hi/te parity for `product.*`, `report.kind.*`, `historyReason.*`), which makes this
  one spot stand out: a Hindi- or Telugu-reading member sees the English category slug
  inside an otherwise fully translated disclosure screen — the same "raw enum leaking
  into UI text" class of bug IMP26/27 already fixed elsewhere. **Fix:** resolve the
  category id to its taxonomy display name (already translated per FR48) instead of
  string-munging the raw value.

## Screen 14 — Workspace / Campaigns (`app/workspace/[listingId]/page.tsx`, `app/campaigns/[id]/page.tsx`)

**Reference:** FR33/FR34/FR35, UX21. **Verdict: matches research; no bugs found.**

- The single-screen merge of plan/team/campaigns (no separate billing/team/campaign
  sub-screens) is exactly UX21's "fewer screens" direction, and every section is gated
  on server-reported `capabilities` rather than a second front-end permission check —
  the same "server decides, screen only renders" pattern this critique has praised
  elsewhere (Screen 4's `type_action_label`).
- The plan disclosure explicitly states an FR33 "never included" line (verification,
  reputation, ranking, eligibility, private member data) and shows grace-period and
  Paused-with-complete-payment states distinctly — matching FR33's 7-day-grace-then-
  Paused failure path exactly.
- Team invite/role-switch/revoke and the 10-item campaign builder (`chosenItems.length
  >= options.max_items` disables further checkboxes) match FR34/FR35's caps and role
  split precisely; revoke has no confirmation dialog, consistent with the standing
  "no unnecessary intermediate screens" preference, while Close/Cancel actions on the
  neighbouring Partnership and Promotion screens correctly do explain consequence in
  place rather than popping a dialog.
- `campaigns/[id]/page.tsx` correctly reuses `PerformanceReport` at `targetKind:
  "campaign"` for the FR35 "campaign-level report" requirement rather than building a
  second report component.

---

## Top 5 fixes from this pass (Verification/Moderation/Reviews/Partnerships/Promotions/Workspace)

1. **Add a mandatory reason-code control to the three operator Verification-queue
   decisions** (`admin/verification/page.tsx`) — today Reject and Needs-clearer-copy
   post no reason at all, directly contradicting FR47's "Reject (reason)" acceptance
   criterion and leaving the listing's own `reasonLabel` copy template with nothing to
   interpolate. Reuse the `REASON_CODES`-select-before-enable pattern already built
   correctly in the sibling `admin/moderation/page.tsx`.
2. **Add the FR47-required public GST/Udyam lookup link to the Verification queue**
   (`admin/verification/page.tsx`) — FR08's DEC-001 chose manual operator lookup against
   public registries specifically *instead of* a paid KYC API, and that decision has no
   way to actually be carried out without a link from this screen; today there is none.
3. **Give the moderation queue's `prior_cases` count an actual expandable history**
   (`admin/moderation/page.tsx`) — FR40 requires operators see "history" before choosing
   a graduated action; a bare number can't distinguish a stale dismissed report from a
   pattern of upheld removals.
4. **Add an optional evidence attachment to the appeal form** (`moderation/outcomes/page.tsx`)
   — FR41 names "optional evidence" explicitly; the form is currently text-only.
5. **Localize the boost audience category chip properly** (`boost/[kind]/[id]/page.tsx`)
   — `category.replace(/_/g, " ")` leaks the raw English taxonomy slug into an otherwise
   fully translated hi/te screen; resolve it to the taxonomy's translated display name
   instead.

Everything else read this pass — Reviews, Partnerships (aside from the FR25 opt-out
flag noted above, unverifiable from this file), and Promotions/Workspace/Campaigns
beyond the one i18n leak — is a genuine, field-level structural match to its FR/UX
source, with no raw-enum leaks, no forced-typing-before-one-tap violations beyond what
FR25 itself mandates, and no RLS-shaped red flags in the router code read for this pass
(all operator-gated admin endpoints check `operator_permissions` per-call from
`vyapar_identity.members`, consistent with the pattern used elsewhere in the codebase).

---

## Top 5 fixes, prioritized across the whole app (previous pass — Screens 1-8)

Status update: **item 5 below is now resolved** — `TrustContextSheet` exists in
`Verification.tsx` and is wired to `VerificationBadge`, confirmed this pass. Items 1-4
were not re-checked this pass (out of this run's scope) and should be re-verified on
the next run.

1. **Enquiry composer: parse the daily-cap/duplicate error into UX12's actual copy with
   a link to the existing thread**, and add the missing safety line + live character
   counter + trust-labelled context card. This is the highest-traffic screen in the app
   (every conversion funnel ends here) and today it silently downgrades the one
   situation — a duplicate open enquiry — where the sealed spec specifically demands a
   recovery path (`enquiries/new/page.tsx`).
2. **Restore FR15's filter/locality controls on the Businesses directory** (`Filters`
   and `Locality` bottom sheets from UX06). The IntentBar's free-text parsing against a
   small hardcoded English list is not a substitute for radius/service-mode/
   verification/freshness filtering — this is a removed FR-Must capability, not a
   simplification (`businesses/page.tsx`, `IntentBar.tsx`).
3. **Make "Upload a screenshot" actually accept an uploaded image file**, not only a
   pasted URL. This is the exact WhatsApp-forward scenario FR11's own intent paragraph
   names, and it is currently unusable by the audience it was designed for
   (`opportunities/new/page.tsx`).
4. **Add the attachment control to the enquiry/Propose flow** (FR22 explicitly allows
   one; Upwork's real proposal screen foregrounds work samples) and a Fixed/Hourly
   distinction on the rate field, so "Submit a Proposal" is a complete structural match
   to its named reference, not just three text fields (`enquiries/new/page.tsx`).
5. **Confirm and, if missing, build UX07's Trust context sheet on Listing Detail.**
   Marketplace trust research consistently finds that *explaining* a verification badge
   (not just displaying it) is what moves conversion and reduces disputes — this is a
   sealed, Must-priority UX07 element that needs a direct code check next run
   (`listings/[id]/page.tsx`, `Verification.tsx`).

---

## Current prioritized list of every UNRESOLVED issue (as of the third,
## full-coverage pass, 2026-09-17) — ranked by how much it hurts a real user
## completing a real task

All five items above and all five from the Verification/Moderation pass are
now **resolved** (see "Confirmed RESOLVED this pass" above) — they are kept in
place for history, not because they're still open. This list supersedes them.

1. **Enquiry composer's duplicate-thread recovery and safety line are written
   but never rendered** (`app/enquiries/new/page.tsx`). The locale strings
   (`compose.alreadyOpenWithName`, `compose.openIt`, `compose.privacyLine`) and
   the `duplicateEnquiryId` state all exist and are correctly populated from
   the 409 response — but no JSX anywhere in the file reads
   `duplicateEnquiryId` or calls `t("enquiries:compose.openIt")` or
   `t("enquiries:compose.privacyLine")`. This is the highest-traffic screen in
   the app (every conversion funnel ends here), and it's the single
   highest-severity finding this pass precisely because it *looks* fixed on a
   locale-file or state-variable grep and isn't — a member hitting the exact
   scenario the fix was written for still hits a dead end.
2. **FR55's "never pay to apply" safety line still doesn't appear on
   Opportunity Detail** (`app/opportunities/[id]/page.tsx`), the screen where
   a member is about to leave Vyapar for a Public/External source — the exact
   moment UX09 names it for.
3. **IntentBar's category/locality understanding is still a hardcoded 14-item
   English list** (`app/components/IntentBar.tsx`), not the real taxonomy the
   rest of the app (including the more-recently-built `first-run` capability
   step) already uses. Misparses or silently drops anything outside the list.
4. **Listing creation still forces typed, comma-separated categories/
   capabilities** (`app/listings/new/page.tsx`) even though the sibling
   first-run flow already solved the identical data-capture problem with
   tap-only taxonomy chips (`app/first-run/page.tsx` step 2). The two screens
   now visibly disagree on how to capture the same data, and the more
   consequential screen (the listing itself) is the one still requiring typing.
5. **Activity screen rows carry no state/status at all** (`app/activity/page.tsx`),
   a backend gap (`/v1/activity`'s `ActivityItem` has no status field), not
   just a frontend rendering choice — every other list in the app resolves
   state inline; Activity is now the one exception.
6. **Discover feed cards have no overflow menu** (`app/components/LivingCard.tsx`) —
   Not interested/Share/Report exist elsewhere but not as a per-card affordance
   on the home feed, per UX08.
7. **Listing Detail's primary action row still isn't a sticky footer**
   (`app/listings/[id]/page.tsx`) — a named UX07 requirement, cosmetic-only
   relative to items 1-6.
8. **Sponsored placement on Discover home renders as one separate block, not
   interleaved into the organic sections** (`app/page.tsx`) — flagged again as
   a doc-gap in UX08 (which, unlike UX06, never states an interleaving rule)
   rather than a clear-cut code bug.
9. **[Research addendum, see below] No voice-input affordance on any typed
   field in the app** (`app/enquiries/new/page.tsx`,
   `app/components/ReportSheet.tsx`, `app/moderation/outcomes/page.tsx`,
   every listing/opportunity form) — the Web Speech API is unused throughout;
   sourced ACM guidance names this as a recurring effective inclusion pattern
   for low-literate users specifically. Flagged for product-owner
   prioritization, not built.
10. **[Research addendum, see below] Social/community-submitter trust framing
    is under-weighted visually on cards and absent on Opportunity Detail**
    (`app/components/LivingCard.tsx` renders `submitter_name` at the same
    `.vy-muted` 13px/lowest-emphasis style as a freshness stamp; the
    `Opportunity` interface in `app/opportunities/[id]/page.tsx` has no
    `submitter_name` field at all). Research on emergent/mixed-literacy users
    finds social-network trust outweighs institutional signals for this
    audience — the opposite of how much visual weight this gets today.

### Addendum (2026-09-17, same day) — coordinator-supplied research grounding
check: why gig/marketplace apps fail India's blue-collar/mixed-literacy users

The coordinator relayed a round of the product owner's own internet research
(ACM's emergent-user e-commerce adoption paper — trust from social networks,
not institutions; ACM's "Actionable UI Design Guidelines for Smartphone
Applications Inclusive of Low-Literate Users"; 2026 reporting on Indian
gig-worker onboarding fee sensitivity) and asked this pass to check Vyapar
against it specifically, not add it as a separate task.

**Already correctly designed, confirmed against the code (not assumed):**

1. No paywall on discovery/posting/enquiries — `app/enquiries/new/page.tsx`,
   `app/opportunities/new/page.tsx`, `app/businesses/page.tsx` all call their
   respective endpoints with no purchase/entitlement gate anywhere in the
   request path; the only paid surfaces in the whole app are the explicitly
   optional Boost/Promotions flow (`app/boost/[kind]/[id]/page.tsx`) and
   Workspace plans (`app/workspace/[listingId]/page.tsx`) — never core
   discovery or the enquire/apply/propose/register actions themselves.
   Matches the research finding that upfront fees before real value badly
   hurt gig-worker conversion.
2. No star ratings, no penalty for being new — `app/components/Reputation.tsx`'s
   `useReputationText` renders count-based reputation ("New on Vyapar" /
   counts-not-stars), confirmed again this pass with no regression.
3. "Why this?" explanation sheet — `app/opportunities/[id]/page.tsx`'s
   `showWhy`/`WhyResponse` (signals, gap, sponsored disclosure) directly
   answers the algorithmic-opacity trust problem the research names.
4. Three-axis trust system (verification / reputation / member-provided) kept
   visually distinct per `app/components/LivingCard.tsx`'s own code comment —
   matches the finding that trust signals outperform visual polish for
   conversion.

**New gap this addendum surfaces — not previously flagged in this critique:**

5. **MEDIUM-HIGH — No voice-input affordance anywhere in the app, despite
   every structured composer being exactly the kind of typed-field flow the
   research flags as an inclusion barrier.** Grepped the entire
   `vyapar-web/app` tree for `SpeechRecognition`/`webkitSpeech`/`voice`/`mic`:
   zero matches. Every typed field in Apply's note, Propose's cover letter,
   Enquire's message, Register's note (`app/enquiries/new/page.tsx`), the
   Report evidence textarea (`app/components/ReportSheet.tsx`), the Appeal
   textarea (`app/moderation/outcomes/page.tsx`), and every listing/
   opportunity free-text field is a plain `<textarea>`/`<input>` with no mic
   button, even though the Web Speech API (`SpeechRecognition`) is available
   in the Chrome-based browsers this product's target Android users
   overwhelmingly run. This is consistent with the ACM low-literate-user
   guidelines naming voice input as a recurring, effective inclusion pattern
   specifically for the emergent/mixed-literacy segment Vyapar's own FR22
   design intent (near-zero-typing Apply, WorkIndia-style) already gestures
   at but doesn't fully deliver — the structured composers reduce typing
   volume but never eliminate the need to type at all for anyone who can't
   comfortably type in the first place. **Not a directive to build this
   immediately** — flagging as a researched, sourced finding for the product
   owner to prioritize, same status as the "call directly" open question
   already on file from earlier passes.
6. **MEDIUM — "Posted by <name>, from your community" is present in the data
   model but rendered at the lowest-emphasis text style in the design
   system, and is missing entirely on Opportunity Detail.** Two distinct
   findings here:
   - On cards (`app/page.tsx`, `app/opportunities/section/[key]/page.tsx`),
     `submitter_name` is real data, correctly fetched and shown — but it's
     concatenated into the same `meta` string as the freshness stamp and
     relevance reason, all rendered via `LivingCard`'s single `<p
     className="vy-muted">` line. `globals.css` defines `.vy-muted` as
     `font-size: 13px; color: var(--text-tertiary)` — the single
     lowest-emphasis, smallest text style available in the whole design
     system, identical in weight to a throwaway freshness stamp. Research
     on low-literate/emergent users says social-network trust (who posted
     this, do I know them or their community) outweighs institutional
     signals for exactly this audience — that means "from your community ·
     posted by Asha" deserves *more* visual weight than a verification
     badge gets today, not the least. **Fix:** give submitter/community
     framing its own visually distinct treatment on `LivingCard` (e.g. a
     small avatar-initial chip or a slightly higher-contrast text style),
     separate from the catch-all muted meta line, rather than one more
     clause in a de-emphasized sentence a quick-scanning low-literacy user
     is likely to skip.
   - On Opportunity Detail itself (`app/opportunities/[id]/page.tsx`), the
     `Opportunity` interface has no `submitter_name` field at all — only
     `source_segment` (rendered as a plain "Community"/"Public" badge). A
     member who taps into the detail screen from a card that told them "from
     your community, posted by Asha" loses that specific person's name
     entirely once they're on the one screen where they'd act (Apply/
     Propose/Enquire) — the exact moment social trust should be most
     reinforced, not silently dropped. **Fix:** add `submitter_name` (and,
     where available, the submitter's own reputation line) to the
     Opportunity Detail response and render it near the title, not just on
     the upstream card.

Total screens covered this pass: all 32 screen files named in the module's
screen inventory (Home, Businesses, Listing Detail, My Listings, New Listing,
Opportunity Detail, New Opportunity/Post, Section "See all", Enquiry Composer,
Enquiry Detail, My Enquiries, Activity, Profile, Privacy, Notifications,
Verification (member + operator), Report/Block, Moderation Outcomes/Appeals,
Partnerships (new + detail), Reviews, Boost/Promotions (+ Checkout +
Performance Report), Workspace/Campaigns, First-run, and all four Admin
screens: Verification queue, Moderation queue, Commercial, Ops), plus the
shared components each one depends on (LivingCard, FilterSheet, IntentBar,
FileUpload, ReportSheet, NotificationBell, CommandHub, Verification.tsx,
Reputation.tsx, ReviewComposer.tsx). Genuine defects found this pass: 8 open
(1 high, 3 medium, 4 low/medium as ranked above) plus 13 confirmed resolved
since the last critique run (2 of them — Propose attachment/rate-type and the
screenshot-upload fix — resolved together with their Top-5 write-ups above).
No net-new severe defect class (raw-enum leaks, forced-typing violations, or
RLS-shaped gaps) was found in any screen read for the first time this pass.

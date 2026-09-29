# IMP — Frontend workstream FE2: contact, contracts, packages, badges, seeker protection, Discover filters and rows, Hire / Find work, outcomes (2026-09-28 → 29)

**Scope.** Vyapar web (`vyapar-web/`) for backend workstreams B and D, plus the Discover redesign the owner asked for on 2026-09-29, for which FE2 also owned `services/feed.py` / `routers/feed.py`.

**Hand-over.** On 2026-09-29 the coordinator moved Discover's *visual* design (`app/page.tsx`, `app/components/discover/*`, the filter UI) to a new design-lead agent. FE2 stopped editing those files at that point. The data logic, the SDK and the two new feed endpoints below stay as the base for that work.

**Checks.**
- `npx tsc --noEmit`: clean.
- `npx eslint` over every file FE2 created or edited: clean, apart from one error that was already there before FE2. It is `react-hooks/set-state-in-effect` in `Reputation.tsx` (`ReviewList`), where FE2 changed only the date line.
- `npm run lint` over the whole app: still reports errors, all of them earlier `set-state-in-effect` errors in files FE2 did not write (admin, boost, campaigns, privacy, workspace and others). Private build folders (`.next-*`) are now ignored, which removed about 16,000 warnings that came from generated files.
- `scripts/check_backend_b.py`: **105/105**. That count includes 16 new Discover checks, and the script cleans up after itself.

---

## 1. SDK (`lib/sdk/domains/*`, typed from the contracts)

| Domain | File | Operations |
|---|---|---|
| `sdk.contact` | `contact.ts` | `preferences`, `updatePreferences`, `listingPreferences`, `updateListingPreferences`, `actions`, `attempts`, `recordAttempt`, `precallActions`, `recordPrecallAttempt` |
| `sdk.packages` | `packages.ts` | `list`, `upsert` (PUT), `remove`, `request` (Idempotency-Key) |
| `sdk.savedSearches` | `savedSearches.ts` | `create`, `list`, `remove` |
| `sdk.badges`, `sdk.seekerProtection` | `trust.ts` | `forMember`; `get`, `check` |
| `sdk.contracts` | `contracts.ts` | all 19 member operations of imp-backend-d (`create`, `list`, `get`, `propose`, `accept`, `cancel`, `complete`, `add/update/deleteMilestone`, `fundMilestone`, `submit/approve/rejectMilestone`, `openDispute`, `submit/approve/rejectTimesheet`) |
| `sdk.taxonomy` | `taxonomy.ts` | `tree` (shared with FE1's hiring screens) |
| `sdk.feed` | `opportunities.ts` (edited) | every filter is passed to `get` / `section` / `sectionPage`; new: `results(params, limit)` and `rows()` |

Other SDK changes:
- **`client.put`** was added.
- **`types.ts`** gained optional fields only:
  - `badges` and `packages` on `Listing`;
  - `badges` on `ProfileCardData` and `SearchListing`;
  - `distance_km`, `poster_badges` and `seeker_protection` on feed cards and `Opportunity`;
  - the enquiry's `target_name`, `counterpart_name`, bid and milestones;
  - `FeedFilterValues`, `FeedFacets`, `ResultsResponse` and `RowsResponse`.

Data hooks are in `app/hooks/trade.ts`: `useContactActions`, `useContactPreferences`, `useListingContactPreferences`, `useSavedSearches`, `useContracts`, and `useContract` (which runs actions and replaces the contract with the returned one). Presentational components never fetch.

## 2. Contact actions and preferences

- **Enquiry thread (`contact/ContactActionsBlock` → `ContactActionsView`).**
  - Once the enquiry is accepted, the thread shows "You can call X" with two equal secondary buttons, Call (`tel:`) and WhatsApp (`wa.me`). The number is shown small (+91 90000 00009), with the call window underneath ("Takes calls Mon–Sat, 9 am–7 pm").
  - Critique L4: the link (`tel:` or `wa.me`) opens inside the tap itself, and the attempt is recorded right after (`POST …/contact-attempts` with fetch `keepalive`), so a slow connection never makes Call look dead. The same applies to pre-accept calling and to the applicant contact on the applicants board (`lib/contactTap.ts`).
  - When a call is blocked, the button stays but is disabled, and the server's own reason and next window are shown beside it.
  - History reads "You contacted X on WhatsApp on 28 Sept 2026, 8:31 pm". It is written on the client in IST: the server's `summary` uses a UTC clock (see Blocked).
  - Coordinator fixes:
    - The old plain "Contact details" block is gone. Non-phone channels are listed inside the card.
    - The card now says from the viewer's side: "X's number is shared because the enquiry was accepted", followed by the "Never pay in advance" line.
    - For the upcoming shortlist reveal, the card handles `counterpart_can_contact` ("Sunita may call you about this"). It is optional until backend A ships it.
- **Pre-accept calling (`contact/PrecallActions.tsx`).** FE1 mounts it next to Apply.
  - Call is the filled accent button when it can be used, and turns quiet when it can't. WhatsApp is an icon button.
  - Reasons are calm one-liners: "Calls open tomorrow, 7 am.", "Daily call limit reached — apply instead.", "Calls are for people whose skills match — apply instead." With an application already open, these read "…You can still message them in your application."
  - `precall_off`, `own_post` and `no_contact` render nothing.
  - "Your application was sent as well. Open it" appears only right after a tap that created the application. FE1's action bar shows an application that already existed.
- **Preferences.**
  - `/profile/contact` is one compact form:
    - calls and WhatsApp on/off;
    - seven day chips;
    - "Any time" or an hour pair picked from lists;
    - calls per day with "No limit";
    - who may call.
  - A live sentence under the form reads "People can call you Mon–Sat, 9 am–7 pm, up to 1 call a day. WhatsApp is open any time." On desktop it sits in a sticky side column.
  - The listing owner view has a per-listing override (`contact/ListingContactOverride`): "Same as my account" or "Own hours for this profile". Switching back sends `reset` for every field.
  - The Profile hub gained the tiles "Calls & WhatsApp" and "Contracts".

## 3. Badges and seeker protection

- **`trust/Badges.tsx` (`BadgeList`).** Each badge is a neutral pill with an icon and a label. Tapping it shows the description in place; on a card the tap doesn't open the card. There are no stars and no accent. Badges appear on:
  - listing detail (under the reputation line);
  - profile cards (similar and matching);
  - business search results;
  - feed and Discover cards;
  - the "About the poster" section of opportunity detail;
  - outcome pages.
- **`trust/SeekerProtectionNotice.tsx`.** On employment detail, a calm nested notice shows the server's localized title and body. Its "Report: asked me for money" action opens the page's ReportSheet in place, with `asked_for_money` already chosen. That works through `requestReport()`, a window event.
- **ReportSheet** offers `asked_for_money` first for opportunities and enquiries, in en, hi and te.
- **OpportunityDetailView** got only small inserts: the notice, the badges, and hiding FE1's generic "free to respond" line when the full notice is shown.

## 4. Service packages

- **Owner (`packages/PackagesEditor`).** Three tier forms (Basic, Standard, Premium), each with name, price, days, revisions, up to 5 "included" lines and a description. A tier left empty is not offered. "Stop offering this tier" removes it. Three columns on wide screens.
- **Viewer (`packages/PackagesCompare`).**
  - Phones get tabs, with Standard pre-selected.
  - Desktop gets a table with a column per tier and a row per attribute, marked ✓ or —.
  - "Request this package" opens a prefilled, editable message in place ("Namaste Khatri & Associates, I'd like the Standard package: GST + TDS compliance (₹3,499).") and sends an enquiry with an Idempotency-Key. It then shows "Request sent. Open the conversation".
  - The button is secondary, so "Enquire now" stays the page's one primary action.

## 5. Contracts and milestones

- **`/contracts`.** Tabs: All · I'm paying · I'm doing the work. Rows show a "Needs you" chip. At 1024px and up, the list sits beside a detail pane, the same pattern as Enquiries.
  - A bug was fixed here: both the phone and the desktop row rendered on desktop.
- **`/contracts/new?enquiry=`.**
  - Only the paying side sees the form; the other side is told who starts the contract.
  - The form is pre-filled from the proposal: bid, bid type and milestones.
  - Fixed price: milestone rows with a live "₹8,000 left to assign" counter, plus "Split evenly" and "Put the rest in the last one".
  - Hourly: rate, weekly cap and budget.
  - Buttons: "Send to X" and "Save as draft". A "How it works" column sits beside the form.
- **`/contracts/[id]` (`ContractDetail` → `ContractDetailView`).**
  - A vertical timeline: Not funded, Held, Submitted, Paid, plus Changes requested and In dispute.
  - Each milestone carries at most one action, for the person whose turn it is. Only the current step gets the accent.
  - Shows the 14-day auto-approve countdown with its date.
  - A Money card: Held · Paid · Refunded · Not yet funded · Total.
  - Hourly contracts have weekly timesheets: log hours (the week is chosen from recent Mondays), approve and pay, or send back.
  - Also: report a problem (dispute), the event history, and End or Finish contract.
  - On phones the current action is pinned at the bottom. It is safe by design:
    - it never approves in one tap ("Review the work" scrolls to the milestone);
    - it hides while any note box is open;
    - `scroll-padding` keeps focused controls above it.
  - This was found live: the footer covered "Send back" and approved a milestone by mistake.
  - The history shows one line per action: "Payment started" is hidden once the payment settles.
- **Funding** uses the boosts checkout. The checkout honours `?return=/contracts/<id>` (same-app paths only) and says "Back to the contract".
- **Sandbox.** When the order the contract opened reports `sandbox: true`, a dashed "Test payments" note is shown. Otherwise the note reads "Held and paid amounts are recorded by Vyapar…".
- **Entry points.** "Start a contract" (for the paying side) or "Open contract" on the thread; Activity; the Profile hub.
- **Critique L5.** "Start a contract" appears only for freelance projects, local services and profile enquiries, never on a salaried job thread (`useContractEligible`). `/contracts/new` refuses a job thread with a plain explanation. FE1's applicants board still links "Start contract" for hires, so that link should check the same rule.

## 6. Discover: filters, rows, saved searches (data logic by FE2; visuals now with the design lead)

### Backend (FE2-owned, additive; documented for the design lead)

**Every feed route accepts these new filters:**

| Filter | Values and meaning |
|---|---|
| `types` | comma list of kinds; the legacy single `type` still works |
| `pay_kind` | `monthly` or `project` |
| `pay_min_paise` / `pay_max_paise` | A pay filter shows only posts that state their pay. |
| `posted_within` | `today`, `week` or `month` |
| `shift` | `day`, `night` or `flexible` (includes rotational) |
| `experience` | `fresher`, `1` or `3`: the member's own experience. It keeps posts asking for at most that much. |
| `verified_only` | the poster owns a verified business listing |
| `segment` | `community` or `public` |

**`GET /v1/opportunities/feed/results`** (`listOpportunityResults`, `limit` ≤ 100, default 60):
```jsonc
{"items": [FeedCard…], "total": 15,
 "facets": {"type": [{"value":"employment","count":9}, …], "work_mode": […], "posted_within": […], "shift": […],
            "experience": […], "verified": 12, "skills": [{"value":"catering","count":2,"label":"Catering"}, …8]},
 "filters": {…as applied}, "distance_available": true, "near_label": "Dilsukhnagar", "radius_km": 12}
```
Facets are disjunctive: each dimension counts with every other active filter applied, but not its own.

**`GET /v1/opportunities/feed/rows`** (`listOpportunityRows`):
```jsonc
{"rows": [{"key":"near_you","title_key":"nearYou","title_params":{"km":12,"place":"Dilsukhnagar"},
           "see_all":{"radius_km":12,"sort":"distance"},"items":[FeedCard ≤10],"total":11}, …],
 "enrichment_prompt": null, "distance_available": true}
```
- Row keys: `for_you`, `near_you`, `category:<slug>` (up to 2, from the member's skills), `new_today`, `starting_now`, `pay_20k` (₹20,000+ a month), `verified`, `community`, `projects` and `remote`.
- Empty rows are dropped.
- Each row leads with cards not already shown in an earlier row.
- `title_key` maps to `explore.rows.*` in the web locales.

**Other backend changes:**
- **Own posts.** Discover (the sections, section pages, results, rows and saved-search matches) never shows the viewer's own posts (`o.poster_id <> $1` in the one candidate query).
- **Money labels.** `compensation_label` always has ₹ and a period. A bare legacy "15000" now reads "₹15,000 a month" for jobs, "Fixed price …" for projects and "Budget …" for local services (`legacy_compensation_label`). Feed cards are now localized: they used to be English only.

### Web

This is the web as FE2 left it on handover.
- `app/page.tsx` works in two modes, with the filters in the URL:
  - with nothing narrowing the list, it shows themed rows that scroll sideways, with snap on phones and ‹ › arrows on desktop;
  - with any query or filter, it shows one ranked list with its count.
- The Discover screen itself:
  - **Top:** an Opportunities | Businesses switch, one search field (mic, clear), and a location chip with a 1–50 km slider and "Anywhere".
  - **Desktop:** a slim sticky sidebar, 248px, with no inner scrollbar. Its sections collapse and show counts, and the pay filter has presets with an echo in Indian format.
  - **Phone:** a sticky bar with "Filters (n)", Sort and quick chips. The bottom sheet has a live "Show N results".
  - **Results header:** the count ("5 opportunities near Dilsukhnagar"), removable chips, a Sort select, and "Save this search" with an alert bell.
  - **Cards (`DiscoverCard`):**
    - the title in the normal colour, with ALL-CAPS titles shown in sentence case;
    - the pay line, then place · distance, then when it was posted, then badges;
    - the kind of post as a chip;
    - the reason it was shown behind "Why this?".
- **Saved searches** are listed under Activity (open, alert on/off, delete), next to a Contracts summary card.
- **"See all"** section pages carry the filters.
- `/businesses` now runs the search in its URL (`q`, `category`, `locality`, `skills`). Before, links from Discover's search box and elsewhere landed on an empty directory.

## 7. Desktop Hire / Find work menu and outcome pages

- **`nav/HireMenu`** sits in the top-left bar next to the language switch, which is now one shared flex row with no guessed offsets. It opens by click.
  - Three columns: categories, the chosen category's specialties with one-line descriptions (from `/v1/taxonomy/tree`), and outcomes or shortcuts.
  - Hire links to Businesses filtered by skill; Find work links to Discover filtered by skill.
  - If the taxonomy can't be read, the menu is hidden. Escape and a click outside close it.
- **`/outcomes/[slug]`** has 6 outcomes: hire-shop-staff, home-repair, build-website, cater-event, gst-accounts, market-business.
  - Each page has plain-language copy, the specialties with their descriptions, and matching profiles from the existing search (the viewer's own listings are excluded).
  - "Post this" leads to `/opportunities/new?type=&skills=`. FE1's composer has to read those parameters.

## 8. Cross-cutting fixes found by reading screens as a user

- US-order dates ("8/31/2026") were replaced with the Indian format ("31 Aug 2026") across 14 screens (`lib/format.ts` `formatDate`). FE1's `OpportunityDetailView` was left alone.
- `lib/format.ts` covers ₹ without ".00", Indian digit grouping, IST date and time, and "10 am" times.
- Plural forms were added ("up to 1 call a day").
- Colours are tokens only (for the new palette agent); FE2's CSS (`app/styles/fe2.css`) has no colour literals.
- `next.config.ts`:
  - `devIndicators: false` (coordinator request);
  - `distDir` from `VYAPAR_WEB_DIST_DIR`, so a private `next dev` can run beside the owner's.
- `next dev` added `.next-fe2` / `.next-palette` includes to `tsconfig.json`; the palette agent uses the same mechanism.

## 8a. i18n key check (critique L10)

`vyapar-web/scripts/check-i18n-keys.py` is the critique's checker, made CI-ready: it defaults to the web root and exits 1 when keys are missing. It finds every literal `t("ns:key")` under `app/` and checks it against en, hi and te, counting plural forms. It now reports **0 missing**. The 4 keys that were missing got real en, hi and te values:
- `discover:broaden.*` (locale values only; the design lead owns the view);
- `privacy:delete.blocked` and `privacy:delete.done`;
- `adminOps:stale.done`.

Run it with `python scripts/check-i18n-keys.py`.

## 9. Test data and cleanup

**Personas:** Meena (client), Suresh (electrician), Sunita (poster), Vikram, Anita, Ravi and Rahul. The owner's account was never used.

**Flows exercised through the product, from both sides:**
- contract: create → accept → fund (sandbox checkout) → submit → request changes → resubmit → approve;
- WhatsApp tap recorded;
- the four pre-accept calling cases;
- package request;
- saved search.

**Cleanup:** a scratch script removed every row that referenced FE2's ids, 97 rows across 12 tables. It also reset Suresh's and Sunita's calling preferences to the defaults. A final sweep of all `vyapar_*` tables found **0** rows left.

## 10. Screenshots

Screenshots are in `screenshots/2026-09-28/fe2-*` (23) and `screenshots/2026-09-29/fe2-*` (16). They cover:
- the thread contact card;
- contact preferences;
- contract create, proposed, timeline, changes requested (both sides), list and pane;
- the precall cases: matching, outside hours, not matching, cap reached;
- Discover rows, results, sheet, Telugu, saved search;
- the Hire menu and an outcome page;
- packages: compare, tabs, request, editor;
- Activity.

## 11. Blocked or left for others

1. **Server clock in `summary`.** `contact_attempts.summary` (backend B) formats time in UTC. The web writes its own IST line, but the MCP and API text is still off by 5½ hours.
2. **Sandbox label for the provider side.** Only the client can read the payment order, so the provider sees the generic "recorded" note. A `sandbox` field on `ContractOut` would fix this (backend D).
3. **"Use my location"** in the Discover location popover needs a coordinates override on the feed endpoints. Until then the popover shows the member's saved area with a link to change it.
4. **The composer** must read `?type=&skills=` from outcome pages and menu links (FE1).
5. **Shortlist reveal** (backend A, announced): the web handles an optional `counterpart_can_contact` on contact-actions and needs the final field name.
6. **Payouts:** the payment-partner blocker (BLOCKER-01) remains. The UI states it.
7. **Pre-existing lint errors** in files FE2 didn't write (listed above).
8. **FE1 raw key** seen on opportunity detail during testing: `apply.apply` on the Apply button (FE1's in-progress work).

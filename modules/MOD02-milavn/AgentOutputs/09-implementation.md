---
step: 09-implementation
module: MOD02
status: In Progress
approver: Engineering Manager / Tech Lead
updated: 2026-09-13
items: "20 | approved: 0 | blockers: 0"
---

# 09 — Implementation — MOD02 Milavn

Working application: **web** `modules/MOD02-milavn/milavn-web` (Next.js 16, port **3001**) · **API** `modules/MOD02-milavn/milavn-service` (FastAPI, port **8001**) · **DB** `forkhatridb` on `localhost:5433`, schemas `milavn_*` (migrations `07a-db-implementation/migrations/001–015`).

Run: `milavn-service/.venv/Scripts/python -m uvicorn app.main:app --port 8001` (no `--reload` on Windows, see README) and `npm run dev` in `milavn-web`. Open `http://localhost:3001` → *Continue as* one of the seeded members → onboarding → Around You.

## Revision history
| Date | Change | Reason / Ref |
|---|---|---|
| 2026-09-13 | Step 9 started directly on the user's instruction (autonomous per-FR loop, no approval gate for implementation; login/auth skipped because it is owned by the parent ForKhatri platform). Foundations + first vertical slices built and browser-tested (headless Chrome via CDP, mobile viewport 412×915): FR001–FR009 (profile, Around You, four discovery modes, cards, ranking, why-reason, filters), FR010–FR019 (create/edit/cancel, Activity/Occurrence, share link, RSVP lifecycle, notifications on change, QR/manual check-in, non-punitive no-show), FR020–FR029 (circles, types, suggestions job, community memory, calendars incl. minimal Organization scope), FR030–FR037 (trust levels, qualitative reputation), FR038–FR041 (approximate location, precision setting), FR042–FR045 (reason-only people), FR046–FR050 (SSR public page, share channels), FR051–FR057 (notification classes + inbox + organizer broadcast), FR058–FR059 (waitlist promotion, co-organizers), FR061–FR065 (report, block, safety block, moderation queue on the shared console contract), FR066–FR069 (feedback), FR076–FR088 (platform-owned auth stubbed; onboarding, permission priming, nav shell, system states, settings, inbox, help, logout/delete). | User: "Start step 9 directly now… loop on each req… show me working application." |
| 2026-09-13 | Browser-testing pass (screens driven over CDP, screenshots reviewed) found and fixed: `reputation_labels()` failed with "malformed array literal" for any member with a signal (`labels || 'x'` ambiguity → `array_append`, migration 006); Notification Dispatch could not read an announcement body under RLS with no acting member (migration 007 `occurrence_update_message`); Leaflet map collapsed to 0 px inside the flex screen (explicit size); FR082 notification priming rendered as a cramped toast → inline banner; circle "upcoming" empty copy was the calendar's. Added `seeds-dev.sql` (12 occurrences across the next two weeks, four circles incl. a private one, an organization scope, participations, reputation signals) so every screen has realistic content. In-process scheduler for reminders (10 min) and circle suggestions (hourly) added to the service lifespan. | Loop steps 4–7 (test, modernise, improve, re-test). |
| 2026-09-13 | Second regression pass: all five browser scenarios green with zero console errors (fresh onboarding as `Kiran Das`; Discover→Participate→Connect→Contribute loop; create→organizer tools→announcement delivered→moderation; Hindi UI; dark+light). Fixed: the circle-formation job wrote other members' suggestion rows against a member-self RLS policy → definer-owned `create_formation_suggestion` / `suggestion_member_ids` / `suggestion_exists_for_pair` (migration 008); `series.upcoming` count was overwritten by a list (detail page crash on recurring items). Environment: the API moved to **port 8002** — two ghost `LISTENING` sockets with dead owner PIDs sit on `127.0.0.1:8001` on this machine and Windows round-robins connections across listeners, which made a server on 8001 answer only some requests (the symptom looked like "stale code"). Cover photos re-sourced from Wikimedia Commons after screenshot review. `tsc` clean; ESLint 0 errors (React-Compiler heuristics kept as warnings); `ruff` clean. | Loop steps 4–8. |
| 2026-09-13 | FR002 taken to the edge ("every rendering surface reads the person's language"): the Hindi screenshot showed English leaking in from the API — ranking reasons, trust labels, category labels and distance labels were built as English prose server-side. Reasons are now `(i18n key, params)` rendered in the request language (a `ContextVar` bound by one middleware from `X-Milavn-Language`, so no call site threads a `lang` argument), with full Hindi/Telugu catalogs on both the API (`app/i18n/locales`) and the web (`locales/hi`, `locales/te` now cover the whole UI chrome); dates use `Intl` with `hi-IN`/`te-IN` and a native "Today". Verified in the browser: the Hindi home screen has no English except member/activity names. | Loop step 5 (modernise) + 7 (re-test). |
| 2026-09-13 | Edge-flow pass (`edge-flows.mjs`: anonymous public page, feedback prompt → send, edit → save, co-organizer delegation, QR check-in) surfaced three defects, all fixed forward: the edit endpoint built `:p::enum` casts dynamically (SQLAlchemy cannot parse a bind followed by `::` → `CAST()`); feedback upsert needed UPDATE on `milavn_trust.feedback` (migration 010); the 24-hour reminder job read member-scoped tables with no acting member (definer-owned `reminder_candidates()`, migration 009). Modernised FR018: the organizer's QR now encodes a plain URL (`/a/<slug>?checkin=<token>`) so a participant scans it with the phone camera and the page redeems it — no in-app scanner. All six scenarios green, zero console errors. | Loop steps 4–8. |
| 2026-09-13 | Polish pass on UI04 "photography-led cards": stock covers are now chosen per activity, not per category — `discovery.cover_url()` matches title/description against an ordered, word-boundary keyword list (bathukamma → food → board games → founders → yoga → cricket → badminton → football → cycling → running → trek → clean-up → book club → photo walk → chai/coffee → music → festival) and falls back to the category cover; 17 keyword photos were downloaded from Wikimedia Commons into `milavn-web/public/assets/covers/kw-*.jpg` (each reviewed by eye; weak first hits for yoga, cricket, chai, founders, clean-up were replaced). API moved back to **8001** as the parallel-development rule asks: the "ghost listener" that had forced 8002 was diagnosed — uvicorn `--reload` on Windows spawns the real server as a `multiprocessing` child that inherits the listening socket, and killing the reloader leaves that orphan serving stale code (three such orphans were found and stopped, on 8001 and 8002). The API therefore runs without `--reload`; README/CODING-GUIDE/settings/.env.local updated. `edge-flows.mjs` feedback step made idempotent (feedback is one-per-occurrence, so a re-run must find the prompt hidden, not fail). All six scenarios green again, zero console errors; `tsc`, `ruff`, ESLint (0 errors) clean. | UI04, FR004, FR066 — krishna kategaru (autonomous). |
| 2026-09-13 | Glass surfaces were not glass: the compiled CSS had no `backdrop-filter` on `.topbar` or the floating nav, so scrolled card text showed through the sticky header (seen in the Around You screenshot). Cause: Next 16 / Turbopack's Lightning CSS drops the property when a rule declares both `backdrop-filter` and `-webkit-backdrop-filter`; rules with only the unprefixed property kept it. Fixed by removing the hand-written `-webkit-` duplicates (the bundler adds prefixes itself from targets) and raising the header to 94% surface. Verified in the compiled stylesheet and by screenshot. | UI Design System Foundation (04-ui.md) — krishna kategaru (autonomous). |
| 2026-09-14 | **Customer / UX / product-owner walk of the whole story** ("open → understand what's around → find → tap → understand → join → show up → meet → come back", thesis §67) against the brand foundation and §84 principles, screen by screen, three identities (fresh member, organizer, moderator), dark/light, English/Hindi. Changed: (1) *Make something happen* (§71) is now a labelled extended button that folds to `+` on scroll; (2) empty cards say **Be the first** instead of `0 going`; (3) Home's circle strip has a heading, *See all*, and two-line names instead of `Kondapur Ri…`; (4) Calendar mode fits all seven days; (5) Detail gained *Why this*, a **Where** mini-map (locality-level, tap for directions) and **Add to calendar** (.ics built after hydration); (6) Create gained one-tap *When* chips (§40 one-tap actions); (7) **Circles have a home locality** — migration 012, `Near me / All` discovery with the viewer's locality first, new circles default to the creator's locality (the user asked "can I find nearby circles?" and the answer was no); (8) **Need over noise** (§84 #13): migration 011 de-duplicates inbox deliveries (same member/class/title/occurrence within 24 h) and an identical organizer update within an hour is refused with 409 — both proven over the API; (9) organizer console: *Capacity* label, timed updates list with *Show all*, all strings localised; (10) moderation queue rows read `Spam or duplicate · “One-off Saturday Trek” / Reported activity` instead of raw ids; (11) Hindi/Telugu web catalogs completed to full parity with English (66 keys each), API error messages completed, and reputation + circle-type labels now translate per request (they were English in Hindi screens); (12) the Next dev badge that covered the Home tab is off. Seeds and the organizer scenario updated (unique announcement text). All six browser scenarios green, zero console errors; `ruff`, `tsc`, ESLint (0 errors) clean. | Product-owner pass on the user's instruction ("check like a customer and UI/UX user, modernise, own the product, check the complete story") — krishna kategaru (autonomous). |
| 2026-09-14 | **Beyond the MVP + "2030" pass** on the user's instruction ("why limit ourselves to MVP… honestly I didn't like the UI/UX… make it super modern, with AI upgrades"). Diagnosis: on a laptop the app was a 480px phone column in an empty canvas with the tab bar floating mid-screen. Built: (1) **responsive shell** — ≥ 900px gets a left rail (`SideNav`: brand, *Make something happen*, five destinations + People, signed-in person), card grids (2–3 columns), two-column detail with a sticky glass action card, centred dialogs, a landing-style Welcome; phones unchanged; (2) **visual layer** — ambient radial light on the base, gradient primary buttons with glow, hairline-glow cards with hover lift, softer radii, honest disabled state, map tiles that follow the theme, page-enter motion; (3) **AI that removes friction, legibly** — `discovery/nl.py`, a deterministic grammar over the module's own vocabulary (interests, categories, localities, day/time words in en/hi/te): **Ask Milavn** on Home/Search turns "badminton this weekend near me" into filters shown as chips, and an empty result widens itself (drop distance, then date) and says so; **Smart fill** on Create turns "badminton tomorrow 7pm at Madhapur for 8 people" into category/title/when/where/capacity with the matched words echoed; nothing is created or decided silently (thesis §33/§40/§84 #9); (4) **conversation & moments** (Meetup/WhatsApp/Strava behaviours, the Milavn way; migration 013): a per-activity **Plan together** thread for the organizer(s) and RSVP'd people only, **Moments** photos addable only by people who were there and visible to the same set, a members-only **circle board**; blocked pairs filtered; rate-limited and idempotent; all visibility via `can_view_thread()` / `was_there()` definer helpers + RLS; (5) **person page** `/p/[id]` (identity, bio, interests, reputation labels, locality at *their* precision via migration 014's `public_locality()`, circles you share, public activities they host; no follow/like/DM) linked from organizer cards, people, circle members, attendees, thread avatars; **named circle-mates going** on the detail (`circle_peer_ids()`); (6) **on-device QR** (`qrcode`) replacing the third-party image service for share/check-in/created pages; (7) 30+ new strings in en/hi/te. Verified: API smoke (thread 403 for outsiders, person page, understand/smart-fill, moments, board), desktop + phone tours, light theme, Hindi, zero console and network failures; `ruff`, `tsc`, ESLint 0 errors. | User instruction — krishna kategaru (autonomous). |
| 2026-09-14 | **Identity v2 after the owner rejected the visual result outright** ("very old styled screens… colour combinations are the worst… be better than Partiful/Luma/Meetup, still modern in 2030"). Research first (recorded in `DESIGN-DIRECTION-2030.md`, sources linked): Partiful's animated pages and 40px display type, Luma's cover-tinted pages, Meetup 2025's photography and colour-coded icons, Airbnb's tactile icons, 2026→2030 agentic/ambient/voice direction, India's vernacular/voice/WhatsApp/low-RAM realities, and the thesis's own §31–§32 (natural language + voice), §69 (modern, warm, trustworthy, local, energetic, minimal, progressive). Built: (1) **poster cards** — the photograph is the card, glass info tray, category accent line, host as a glass pill, saffron date pill; horizontal snap rails on phones, bento grid on desktop (first card spans two columns); (2) **colour roles fixed** — warm paper is the default surface, navy is the primary action, saffron is the accent, one hue per category (`data-cat`), dark only by explicit choice; (3) **editorial type** — Fraunces for greetings, headlines and poster titles, Anek for body and the Indian scripts; (4) **personal canvas** on Home — "Good morning, Asha." + a three-line *your week* digest composed from real counts (`/discovery/digest`, en/hi/te) + Ask Milavn with **voice input** (browser speech recognition in en-IN/hi-IN/te-IN) and quick prompts; (5) **designed pickers** replace the browser's native controls — `PlacePicker` (city chips, zone-grouped locality chips, search) and `WhenPicker` (14-day strip + meeting-hour chips) on Create and Onboarding; (6) **cover-tinted detail page**, date tile, glass action card; (7) **poster image for WhatsApp status** rendered on the device (`lib/poster.ts`, 1080×1350 with QR) in the share sheet; (8) living ambient background, staggered rise, orb empty states, welcome landing with a floating cover collage. Fixed a regression I had introduced in the moderation action endpoint (queue-item signature) and a broken discovery route. Verified: phone + desktop tours, dark theme, poke scenario, six legacy scenarios (onboarding scenario updated for the new picker); `tsc`, ESLint 0 errors, `ruff` clean. | Product-owner instruction — krishna kategaru (autonomous). |
| 2026-09-14 | **Owner's layout rules + real time.** (1) Alerts are no longer a tab: a bell with the unread count sits in every main header to the *left* of the profile avatar, which is *always the last* item (`TopActions`); the tab bar has four destinations with Profile last; the rail lost its Alerts item; the inbox got a back button. (2) Profile is about the person — identity, stats, reputation, interests, rails of what they attend and host — and every preference (language, appearance, location precision, notification settings, help, sign-out, delete) moved behind one gear icon into a sheet. (3) Consistent modern icon set (`lucide-react`) for navigation and header actions. (4) Real time on the device: `useLiveStatus` gives posters a red **Live** pulse while an activity is on and "in N min" up to 90 minutes before; Home gains a **Happening now** rail; **Use where I am** reads the device position once and re-renders Around You / digest for the locality the person is actually in (`?lat&lng` → nearest locality, request-scoped, never persisted; FR038/FR041 intact). Answered the owner's question honestly: location is one-shot, not tracked. Scenarios updated for the greeting header and the new place picker. | User instructions ("keep alerts left and profile always right last", "don't waste space for settings in profile", "real time right now") — krishna kategaru (autonomous). |
| 2026-09-14 | **Messaging (owner decision, design direction §5–§7 completed).** After the owner challenged the "not doing" list and asked for a Snapchat-like chat, each item was mapped to the thesis/brand and approved: reactions instead of likes, no public ratings, circle moments rings only, finite groups, video skipped for now, **locality only — never exact locations** (owner restated), external models later/async, curated themes. Built (migration 015, `milavn_connect`): conversations, members, messages, reactions, presence; **trust-scoped** by one definer helper `can_message()` (shared circle or shared activity, blocks honoured) with all creation through `create_conversation()`; RLS on every table; REST for state and a **WebSocket** (`/ws/chat`) for live events (message, reaction, retract, typing, presence/expression) with an in-process hub and polling fallback; unread counts; 30-second presence heartbeat (a timestamp, never a location). Web: Chats tab before Profile (Profile stays last), chat list with presence dots and mood badges, chat room with grouped bubbles, tap-to-react, photos, typing indicator, and **on-device expressions** (`lib/expressions.ts`: MediaPipe face landmarker blendshapes → smile/laugh/surprised/wink/thinking/love/neutral; only the word leaves the device; opt-in camera with a visible preview; manual mood row as fallback); **Message** button on person pages when allowed. Verified: two-member WebSocket smoke (Priya receives Asha's message, reaction, typing and expression events live), stranger refused with 403, non-member read 404, unread and group creation; browser scenario at phone and desktop; zero server errors. | Owner: "go… video you can skip… yes I agree with your recommendations" — krishna kategaru (autonomous). |

## Coverage check
| Parent Tech Req | Implementation items | Covered |
|---|---|---|
| TR-CROSSCUT-01..04, TR16 (RLS), TR46/TR47 (platform identity) | IMP01 | Yes |
| TR01 (FR001–FR003, FR085) | IMP02 | Yes |
| TR02–TR06 (FR004–FR009, FR033) | IMP03 | Yes |
| TR07–TR11 (FR010–FR014) | IMP04 | Yes |
| TR12, TR14, TR15, TR39 (FR015, FR016, FR018, FR019, FR058) | IMP05 | Yes |
| TR13, TR37, TR38 (FR017, FR051–FR057, FR059, FR063, FR086) | IMP06 | Yes |
| TR16–TR24 (FR020–FR029) | IMP07 | Yes |
| TR25–TR28, TR44 (FR030–FR037, FR066–FR069) | IMP08 | Yes |
| TR29, TR30 (FR038–FR041) | IMP09 | Yes |
| TR31, TR32 (FR042–FR045) | IMP10 | Yes |
| TR33–TR36 (FR046–FR050) | IMP11 | Yes |
| TR41, TR42 (FR061, FR062, FR064, FR087) | IMP12 | Yes |
| TR43, TR-PLAT-01 (FR065) | IMP13 | Yes |
| TR40, TR45 (FR060, FR070–FR075) | IMP14 (recorded, no build — deferred by design) | Yes |
| TR46 (FR076–FR082) | IMP15 | Yes |
| TR47 (FR083–FR088) | IMP16 | Yes |
| TR03/TR29 external services (MapTiler/OpenCage placeholders) | IMP17 | Yes |
| Seed data & assets | IMP18 | Yes |
| Browser verification harness | IMP19 | Yes |
| FR089, FR090, FR098, FR100 (ask-first discovery, smart fill, digest, use-where-I-am) | IMP21 | Yes |
| FR091, FR092, FR093, FR094, FR095, FR099, FR101 (thread, moments, board, person page, circle locality, poster, de-dup/live) | IMP22 | Yes |
| FR096, FR097 (trust-scoped messaging, live expressions + expressive avatars) | IMP23 | Yes |
| DESIGN-DIRECTION-2030 identity v2 (poster system, colour roles, type, pickers, icons, responsive shell) | IMP24 | Yes |
| Design system (04-ui.md Foundation) | IMP20 | Yes |

## Set-level quality gate
| Check | Result |
|---|---|
| Every requirement has a comment block before its code | Pass — every component `interface.py`, foundation module, route module and page/component carries the `[TRxx] … Approach … Traces to` block (IMPLEMENTATION-TEST-STANDARDS §2). |
| No frozen/protected path touched | Pass — applied migration `001-initial.sql` untouched; fixes were made forward as migrations 002–005. |
| Implementation matches ER model exactly | Pass with recorded additions — no table/column changed; migrations 002–005 add SECURITY DEFINER read/write helpers only (see IMP01 Deviations). |
| Runs against the real DB as the non-owning role | Pass — boot asserts `milavn_app` owns 0 tables; `SET LOCAL`-only session variables. |
| Manually tested in a browser | Pass — golden path and core-loop scenarios (`milavn-web/scripts/scenarios/*.mjs`), screenshots in `milavn-web/.logs/`. Zero console errors. |

## Open blockers
| ID | Item | What's needed | From |
|---|---|---|---|
| (none) | — | — | — |

---

## IMP01 — Foundations: config, DB engine, RLS session discipline, event bus, idempotency, rate limiting, platform identity stub
**Traces from:** TR-CROSSCUT-01, TR-CROSSCUT-02, TR-CROSSCUT-03, TR-CROSSCUT-04, TR16, TR46, TR47
**Status / Confidence:** Done / High

**Files touched**
- `milavn-service/app/config/settings.py`, `app/config/dev_identities.json` — comment block: Yes
- `milavn-service/app/db/engine.py`, `app/db/session.py` — Yes
- `milavn-service/app/events/bus.py` — Yes
- `milavn-service/app/idempotency/__init__.py`, `app/rate_limiting/__init__.py` — Yes
- `milavn-service/app/api/deps.py`, `app/main.py`, `app/i18n/*` — Yes
- `milavn-service/app/components/identity_bridge/interface.py`, `app/components/authorization/interface.py` — Yes
- `07a-db-implementation/migrations/002-read-model-helpers.sql`, `003-organizer-write-paths.sql`, `004-dispatcher-reads.sql`, `005-people-precision.sql` — Yes (header comments)

**Approach**
Same shape as MOD03 Mangaly's service so both modules share one engineering model: one FastAPI process, one package per `architecture.md` component with a single `interface.py`, raw parameterised SQL through SQLAlchemy async, one transaction per request that is also the authorization boundary (`SET LOCAL milavn.member_id` via `set_config(...,true)`), transactional-outbox event bus with in-process subscribers run after commit, one shared idempotency guard keyed `(endpoint, actor, key)` with a request fingerprint, one shared fixed-window rate limiter. Authentication is the parent platform's: the Identity Bridge resolves `X-Milavn-Member-Id` against a development registry (`dev_identities.json`, same ids as the seed data) and exposes only `resolve()`/`display_names_for()` — the shape the real platform call will keep.

**Deviations from plan (if any)**
- **SECURITY DEFINER helpers (migrations 002–005), recorded for the ER-model owner (Step 7a):** the Sealed RLS policies are correct but made four already-required behaviours unimplementable from an ordinary request: (1) FR006 "how many are going" / FR008 "N people from your circles are going" — participation rows of *other* members are (rightly) invisible, so counts come from `going_count`/`interested_count`/`circle_peers_going` (counts only, never identities); (2) FR037 qualitative reputation — `reputation_signal` is internal-only, so `reputation_labels()` returns labels and never the weight; (3) organizer-side participation writes (FR018/FR019) and TR39 waitlist promotion — the participant policy's `WITH CHECK (member_id = self)` blocks them, so `organizer_set_status`/`promote_next_waitlisted` re-check the organizer relationship themselves; (4) Notification Dispatch runs with no acting member after commit, so `occurrence_brief`/`active_member_ids`/`deliver` are definer-owned. No policy was widened and no table changed.
- **TR39 lock:** `SELECT … FOR UPDATE` on `occurrence` must pass the UPDATE policy, which a participant cannot; the critical section is serialised with `pg_advisory_xact_lock(hashtext(occurrence_id))` — the same one-writer-per-occurrence guarantee.
- `tzdata` added (Windows has no system tz database; FR004's IST day boundaries need one).

**Assumptions** Postgres `forkhatridb` on 5433 with roles `milavn_owner`/`milavn_app` (dev passwords in `07a-db-implementation/.env`, never committed).
**Decisions** DEC-001: raw SQL + dataclasses rather than ORM models — every query is explicit about which RLS context it runs in, which is the whole point of this module's data layer.
**Review history** (none yet)
**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

---

## IMP02 — Member Profile & onboarding (FR001, FR002, FR003, FR085)
**Traces from:** TR01
**Status / Confidence:** Done / High — browser-tested (`golden-path.mjs`: welcome → locality → interests → language → home).

**Files touched**
- `milavn-service/app/components/profile/interface.py`, `app/api/routes/profile.py`, `app/config/interests.py`, `app/config/localities.py` — Yes
- `milavn-web/app/onboarding/page.tsx`, `app/me/page.tsx`, `lib/identity.tsx` — Yes

**Approach**
`POST /profile` validates locality + ≥1 interest and names each missing field (FR001 failure outcome, translated). Language is a person-level column (FR002) read by every rendering surface via `X-Milavn-Language`. Photo/bio/extra interests are a separate enrichment write (FR003) — a failed upload can never block the profile. Onboarding: soft-ask → `navigator.geolocation` → nearest approximate locality (FR081; denial silently reveals the manual picker), springy chip grid, native-script language options (UI02 DEC-001).

**Deviations** none. **Assumptions** Interest taxonomy is the implementation-stage list in `config/interests.py` (BR01 assumption). **Decisions** none.
**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

---

## IMP03 — Discovery: Around You, four modes, cards, ranking, why-reason, filters (FR004–FR009, FR033)
**Traces from:** TR02, TR03, TR04, TR05, TR06
**Status / Confidence:** Done / High — browser-tested (feed grouping, calendar strip, search + filters sheet, map pins + preview sheet + list alternative).

**Files touched**
- `milavn-service/app/components/discovery/interface.py`, `app/api/routes/discovery.py`, `app/api/schemas.py` — Yes
- `milavn-web/app/page.tsx`, `app/discover/page.tsx`, `components/ActivityCard.tsx`, `components/ModeSwitcher.tsx`, `components/MapView.tsx` — Yes

**Approach**
`RankingEngine` scores locality proximity, interest match, trust, freshness (weights from `ranking_weight_config` v1: 0.35/0.30/0.20/0.15) plus circle relevance, circle-peer social signal and time fit — popularity is structurally absent. The `why_reason` is the dominant real factor; an item with no factor-grounded reason is excluded (TR04), never "Recommended for you". Cards carry all six answers (FR006). Today/Tomorrow/This weekend/Coming up are IST-bounded. `MilavnActivityFeedReader` is the only surface Dashboard may import (TR02).

**Deviations** Interest match uses title/description text and tag→intent-category mapping (no occurrence tag table exists in the Sealed model — not invented). **Decisions** none.
**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

---

## IMP04 — Create / edit / cancel, Activity vs Occurrence, shareable link (FR010–FR014)
**Traces from:** TR07, TR08, TR09, TR10, TR11
**Status / Confidence:** Done / High — browser-tested create → "It's live!" with QR + link.

**Files touched** `milavn-service/app/components/activity/interface.py`, `app/api/routes/occurrences.py`; `milavn-web/app/create/page.tsx` — Yes

**Approach** Four-field minimal form with springy category chips; "More options" accordion for description, visibility/circle, weekly repeat, cover, high-risk. An Activity umbrella row is created only when "Repeats" is on (TR08 non-forced wrapper); `POST /occurrences/{id}/series` adds dated occurrences to a series. Canonical slug `occ-<12 hex>` is returned in the create response (FR014). Creation is idempotent and rate-limited; every occurrence gets exactly one trust level on creation (FR030).

**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

---

## IMP05 — RSVP lifecycle, capacity & waitlist, check-in, non-punitive no-show (FR015, FR016, FR018, FR019, FR058)
**Traces from:** TR12, TR14, TR15, TR39
**Status / Confidence:** Done / High — API-verified (idempotent replay returned the original result; withdrawal promoted the waitlisted member; organizer marked check-in) and browser-tested (Going → "You're going · Withdraw" with spring bounce).

**Files touched** `activity/interface.py` (`set_participation`, `mark_attendance`, `issue/redeem_checkin_token`), `routes/occurrences.py`; `components/DetailClient.tsx`, `app/organizer/[id]/page.tsx` — Yes

**Approach** One-tap Interested/Going with a full status machine and append-only history; capacity → waitlist position; promotion under an advisory lock (IMP01). No-show writes a small named signal and nothing else (FR019/TR15). QR token is organizer-issued and optional; manual mark is the primary path (TR14).

**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

---

## IMP06 — Notification classes, inbox, organizer broadcast & tools (FR017, FR051–FR057, FR059, FR063, FR086)
**Traces from:** TR13, TR37, TR38
**Status / Confidence:** Done / High

**Files touched** `components/notification/interface.py`, `routes/notifications.py`, migration 004; `milavn-web/app/notifications/page.tsx`, `app/organizer/[id]/page.tsx` — Yes

**Approach** Subscribers on the in-process bus deliver Important (cancellation, material time/place change, announcement, waitlist promotion), Social (someone joined — to the organizer), Opportunity (new in your circle) and Useful (24-hour reminders via `send_reminders()`), each writing the inbox row and the `notification_outbox` hand-off. Important can never be muted (CHECK constraint + API). Attendee list is organizer/co-organizer only (FR056); organizer identity/location revealed to RSVP'd participants (FR063).

**Deviations** Reminder and circle-suggestion jobs are callable functions (`send_reminders`, `run_suggestion_job`) — no platform scheduler is named yet (TR17 constraint); a dev trigger exists at `POST /circles/suggestions/run`.
**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

---

## IMP07 — Circles, suggestions, community memory, calendars, minimal Organization scope (FR020–FR029)
**Traces from:** TR16–TR24
**Status / Confidence:** Done / High — browser-tested (join, detail with memory pills, member list).

**Files touched** `components/circle/interface.py`, `routes/circles.py`, `routes/calendar.py`; `milavn-web/app/circles/*`, `app/calendar/page.tsx` — Yes

**Approach** Enum-enforced types; open types join immediately, private/organization are creator-added; leave is a soft-delete; nothing outside the Circle package reads membership (TR18). Suggestions come from `co_participation_pairs()` and require a human accept (FR022). Community memory is an aggregate definer function (FR024). Calendars are query shapes over Occurrence (personal/circle/organization/community/public). `organization_scope` stays exactly `{id, display_name, created_by}` (TR23 DEC-001).

**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

---

## IMP08 — Trust levels & qualitative reputation & feedback (FR030–FR037, FR066–FR069)
**Traces from:** TR25, TR26, TR27, TR28, TR44
**Status / Confidence:** Done / High

**Files touched** `components/trust/interface.py`, `routes/feedback.py`, migration 002 (`reputation_labels`, `record_signal`) — Yes; `DetailClient.tsx` (trust accordion, feedback prompt), `app/me/page.tsx` — Yes

**Approach** Organizer level: platform-verified identity → ForKhatri Verified; a track record → Community Verified; else Community Submitted (deterministic, FR030). Reputation is appended as named behaviours and surfaced only as labels (`New to the community`, `Reliable attendee`, …) — no endpoint returns a number (FR035/FR037). Feedback is optional, private, only after attending, and only ever *adds* a positive signal for a high rating (FR069).

**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

---

## IMP09 — Approximate location & precision (FR038–FR041)
**Traces from:** TR29, TR30
**Status / Confidence:** Done / High

**Files touched** `components/locationprivacy/interface.py`, `routes/privacy.py`, `config/localities.py`, migration 005 — Yes; `app/me/page.tsx` — Yes

**Approach** City → Zone → Locality hierarchy with centroids (development stand-in for OpenCage); distances are centroid-to-centroid ("~4.6 km away"), never exact. Precision is a single setting every consumer reads through this component (`precise` requires a consent grant no feature asks for yet, FR039).

**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

---

## IMP10 — People discovery, reason-only (FR042–FR045)
**Traces from:** TR31, TR32
**Status / Confidence:** Done / High

**Files touched** `components/connect/interface.py`, `routes/connect.py`; `milavn-web/app/people/page.tsx` — Yes

**Approach** Suggestions are `(person, reason)` tuples from shared circles and attended-together occurrences; blocked pairs never appear; the other person's locality is shown at *their* precision; no Match/Like model exists anywhere; copy is activity-framed.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

---

## IMP11 — Public, server-rendered event page & sharing (FR046–FR050)
**Traces from:** TR33, TR34, TR35, TR36
**Status / Confidence:** Done / High — `curl` without any member header returns the full contract; Next.js renders `/a/<slug>` server-side with `generateMetadata` (title, description, Open Graph, canonical).

**Files touched** `routes/public.py`; `milavn-web/app/a/[slug]/page.tsx`, `components/DetailClient.tsx` — Yes

**Approach** The SSR route fetches `/public/occurrences/{slug}` (no auth) and renders all eight elements in the initial HTML; a signed-in viewer is then enriched client-side via `/occurrences/by-slug/{slug}`. Non-public items 404 (RLS underneath + explicit check). Share: Web Share API plus WhatsApp / SMS / email / Instagram-copy / copy-link / QR.

**Decisions** QR images come from `api.qrserver.com` in development (an external dependency to record in 09a); to be replaced by an in-repo generator before release.
**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

---

## IMP12 — Report, block, safety guidelines, contact support (FR061, FR062, FR064, FR087)
**Traces from:** TR41, TR42
**Status / Confidence:** Done / High — browser-tested report sheet → "A moderator will look at this."

**Files touched** `components/safety/interface.py`, `routes/safety.py`; `DetailClient.tsx`, `app/people/page.tsx`, `app/me/page.tsx` (Help & support) — Yes

**Approach** Report is idempotent, rate-limited and publishes its audit event in the same transaction. Block is enforced everywhere through `is_blocked_either_way()`. High-risk occurrences show the safety block on both detail and public page. "Contact support" reuses the report mechanism (FR087).

**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

---

## IMP13 — Moderation queue on the shared Admin & Governance Console contract (FR065)
**Traces from:** TR43, TR-PLAT-01
**Status / Confidence:** Done / Medium — the console container does not exist yet; Milavn ships its manifest + endpoints and a queue-list page that renders those same shapes.

**Files touched** `routes/admin.py` (`/milavn/admin/manifest`, `/moderation`, `/moderation/{id}`, `/moderation/{id}/actions/{action}`); `milavn-web/app/admin/moderation/page.tsx` — Yes

**Approach** Exactly TR-PLAT-01's `AdminViewDescriptor`, `AdminQueueItem` and action-dispatch shapes; moderator scope `milavn.moderate` is resolved by the Identity Bridge and bound as `milavn.permission_scope`; every action is a recorded human decision with its own audit event.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

---

## IMP14 — Deferred by design (FR060, FR070–FR075)
**Traces from:** TR40, TR45
**Status / Confidence:** Recorded, no build (per BR16/BR17/BR18 and ADR-009) / High
No code exists for external event ingestion, AI intent mapping, Vyapar demand signals or sponsorship — enforced by absence. FR060's human-authorization boundary is the Authorization Engine every write already passes through.
**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

---

## IMP15 — Platform-owned auth, permission priming (FR076–FR082)
**Traces from:** TR46
**Status / Confidence:** Done (platform parts stubbed) / High

**Files touched** `routes/identity.py`, `components/identity_bridge/interface.py`; `milavn-web/app/welcome/page.tsx`, `components/AppChrome.tsx`, `app/onboarding/page.tsx`, `DetailClient.tsx` — Yes

**Approach** Sign-up/log-in/reset/OTP are ForKhatri platform flows and are **not built here** (user instruction + ADR-004). `/welcome` stands in for the platform session hand-off (choose a development identity); launch routing (FR076) sends a member with no profile to onboarding and everyone else to Around You. Location priming is inline in onboarding (FR081); notification priming is tied to the first "Going" (FR082, UX02 DEC-001).

**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

---

## IMP16 — Nav shell, system states, settings, inbox, help, logout/delete (FR083–FR088)
**Traces from:** TR47
**Status / Confidence:** Done / High

**Files touched** `components/TabBar.tsx`, `components/States.tsx`, `components/OfflineBanner.tsx`, `app/me/page.tsx`, `app/notifications/page.tsx` — Yes

**Approach** Floating translucent 5-tab bar with a spring-morphing pill and unread badge (UI03); skeleton → content cross-fade, on-brand line-art empty/error states, offline banner (UI18); settings for language, appearance (system/light/dark), location precision, help & support; logout clears the local member; delete-account confirms and hands off (the platform orchestrates deletion — IA088).

**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

---

## IMP17 — External services with placeholder config (map tiles, geocoding)
**Traces from:** TR03, TR29
**Status / Confidence:** Done / Medium
Map tiles: OpenStreetMap in development, swappable via `NEXT_PUBLIC_MAP_TILE_URL` (MapTiler placeholder key in `settings.py`). Geocoding: in-repo locality table (`config/localities.py`) standing in for OpenCage (placeholder key). Both are pure config changes later, per the config-placeholder convention.
**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

---

## IMP18 — Seed data & assets
**Status / Confidence:** Done / High
`07a-db-implementation/seeds.sql` (3 members, a recurring series + a standalone occurrence, a capacity-2 occurrence with a waitlist, a public circle, a report) plus activity created through the app; 9 development identities in `dev_identities.json` (incl. `Kiran Das`, kept profile-less for fresh-onboarding tests); category cover photos (`milavn-web/public/assets/covers/*.jpg`) searched and downloaded from Wikimedia Commons (CC — a badminton court, friends over coffee, Hyderabadi biryani, a students' workshop, a coworking table, Indian hikers, Bathukamma, volunteers) after the random-Flickr source proved irrelevant on screenshot review; avatars from pravatar. All to be replaced with licensed/own photography before release (09a).
**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

---

## IMP19 — Browser verification harness
**Status / Confidence:** Done / High
The shared Chrome DevTools MCP browser was held by another session, so a private headless Chrome (`--remote-debugging-port=9333`) is driven over CDP by `milavn-web/scripts/cdp.mjs`; scenarios in `scripts/scenarios/` (`golden-path.mjs`, `core-loop.mjs`) navigate, click, type, assert text and capture screenshots to `.logs/`. Findings fixed from screenshots: map container collapsed to 0 px (explicit size), notification priming rendered as an inline banner not a toast, circle "upcoming" empty copy, cover-photo relevance.
**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

---

## IMP20 — Design system realisation (04-ui.md Foundation)
**Status / Confidence:** Done / High
`milavn-web/app/globals.css` is the single realisation of the Foundation: navy/off-white/saffron/green/terracotta tokens with a first-class dark theme (system + explicit toggle), Anek Latin/Devanagari/Telugu via `next/font`, 4px spacing, 16px cards / 24px sheets, `ease-standard`/`ease-spring`/`ease-micro`, skeleton cross-fade, photo-card scrim, trust pill always paired with text, floating glass nav, spring pop on selections/RSVP. Every string comes from `locales/<lang>/common.json` (English complete; Hindi/Telugu partial with fallback).
**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

## IMP21 — Ask-first discovery, Smart fill, weekly digest, use-where-I-am (FR089, FR090, FR098, FR100)
**Status / Confidence:** Done / High
**Why:** thesis §31–§32/§40 (natural language, voice), §67 (immediately understand); owner instruction to be AI-first without a model in the permission path (§33).
**What:** `milavn-service/app/components/discovery/nl.py` (deterministic grammar over interests, categories, localities, day/time words in en/hi/te: `understand()`, `smart_fill()`), routes `/discovery/understand`, `/discovery/smart-fill`, `/discovery/digest`, `?lat&lng` on `/discovery/around-you` (request-scoped, snapped to the nearest locality, never persisted). Web: `components/AskBar.tsx` (voice via browser speech recognition in en-IN/hi-IN/te-IN, quick prompts, chips), Search widening in `app/discover/page.tsx`, Smart fill in `app/create/page.tsx`, digest + *Use where I am* on `app/page.tsx`.
**Verified:** parser unit checks (12 asks, 4 sentences), API smoke, browser scenarios `poke.mjs` (ask-from-home, smart-fill-create), `final.mjs`.
**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

## IMP22 — Thread, Moments, Board, Person page, Circle locality, Poster, De-dup/Live (FR091–FR095, FR099, FR101)
**Status / Confidence:** Done / High
**Why:** validated behaviours from Meetup/Strava/WhatsApp (thesis §57) kept trust-scoped and privacy-first (§21, FR040); local relevance (§84 #6); need over noise (§84 #13); share via WhatsApp (§43).
**What:** migrations 011 (`deliver()` duplicate guard), 012 (circle `locality_*`), 013 (`occurrence_message`, `occurrence_photo`, `circle_post`, `can_view_thread()`, `was_there()`, `circle_peer_ids()`, `public_card()`, `hosted_public_ids()`), 014 (`public_locality()`); `components/conversation/interface.py`, `routes/conversation.py`, `connect.public_profile()`, `routes/connect.py` `/people/{id}`; web `components/Thread.tsx`, `components/Moments.tsx`, board in `app/circles/[id]/page.tsx`, `app/p/[id]/page.tsx`, `lib/poster.ts`, `useLiveStatus` in `components/ActivityCard.tsx`, *Happening now* rail.
**Verified:** API smoke (403 for outsiders, 404 for blocked pairs, 409 on duplicate announcement, one alert after join/withdraw/join), browser scenarios `poke.mjs`, `edge-flows.mjs`, `tour3.mjs`.
**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

## IMP23 — Trust-scoped messaging with live expressions and expressive avatars (FR096, FR097)
**Status / Confidence:** Done / High (camera path verified manually only)
**Why:** owner decision 2026-09-14 after the "not doing" review — Snapchat-like chat, done the Milavn way: trust-scoped, reactions instead of likes, expressions as words never frames (§21, Brand §9/§15).
**What:** migration 015 (`milavn_connect`: conversation, member, message, reaction, presence; `can_message()`, `create_conversation()`, `presence_of()`, `unread_count()`); `components/connect/chat.py` (hub + logic), `routes/chat.py` (REST + `/ws/chat` WebSocket + `/presence` heartbeat). Web: `app/chats/page.tsx`, `app/chats/[id]/page.tsx` (WebSocket with polling fallback, reactions, photos, typing, presence stage), `lib/expressions.ts` (MediaPipe face landmarker blendshapes → 7 expressions, on device), `components/MoodAvatar.tsx` (hash-seeded SVG cartoon whose brows/eyes/mouth/cheeks animate per expression), Chats tab, Message button on person pages, 30-second presence heartbeat in `AppChrome`.
**Verified:** `ws_smoke.py` (two members: message/reaction/typing/expression events received live; stranger 403; non-member 404; group; unread), browser scenario `chat.mjs` at phone and desktop (send, react, mood, new chat sheet, person Message). Camera-based detection requires a real webcam — verified by design review only; the mood row is the tested fallback.
**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

## IMP24 — Identity v2 and responsive shell (DESIGN-DIRECTION-2030 §4)
**Status / Confidence:** Done / High
**Why:** the owner rejected the first visual pass ("very old styled screens… colour combinations are the worst… be better than Partiful/Luma/Meetup, still modern in 2030"). Researched direction recorded in `DESIGN-DIRECTION-2030.md` with sources.
**What:** `globals.css` layers (2030 layer, poster system, identity v2, colour roles): warm paper default, navy primary / saffron accent, per-category hues via `data-cat`, Fraunces display type (`app/layout.tsx`), poster cards (`components/ActivityCard.tsx`), rails/bento, `SideNav` rail ≥ 900px, two-column detail with cover-tinted backdrop, `PlacePicker`/`WhenPicker`, Lucide icons, header order People · Alerts · Profile-last (`TopActions`), profile settings behind a gear sheet, on-device QR (`components/QrCode.tsx`).
**Verified:** phone and desktop tours (`tour4.mjs`, `final.mjs`), light and dark, Hindi; six legacy scenarios + `poke.mjs` green; `tsc`, ESLint 0 errors.
**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

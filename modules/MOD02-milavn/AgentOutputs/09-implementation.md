---
step: 09-implementation
module: MOD02
status: In Progress
approver: Engineering Manager / Tech Lead
updated: 2026-09-13
items: "20 | approved: 0 | blockers: 0"
---

# 09 — Implementation — MOD02 Milavn

Working application: **web** `modules/MOD02-milavn/milavn-web` (Next.js 16, port **3001**) · **API** `modules/MOD02-milavn/milavn-service` (FastAPI, port **8001**) · **DB** `forkhatridb` on `localhost:5433`, schemas `milavn_*` (migrations `07a-db-implementation/migrations/001–034`).

Run: `milavn-service/.venv/Scripts/python -m uvicorn app.main:app --port 8001` (no `--reload` on Windows, see README) and `npm run dev` in `milavn-web`. Sign in once at the ForKhatri entrance (`http://localhost:3100`, Identity & Trust Service on `:8100`), then open `http://localhost:3001` → onboarding (first visit) → Around You. The former *Continue as* chooser is retired (IMP25).

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
| 2026-09-14 | **Chat and avatar redesign after the owner called them "very old."** Researched Snapchat's actual chat system before touching code (sources in the message to the owner): Bitmoji's "reactive head that mirrors facial expressions," the friend-status pattern, and 2026 bubble-design research (rounded tails, avatar+status+timestamp structure). Adapted the *pattern*, kept Milavn's own navy/saffron — Snapchat's yellow/black was never adopted. Rebuilt `components/MoodAvatar.tsx`: idle blink+sway so a face is never static at rest, a glow ring while the person is active, a radial highlight and optional glasses for variety. Rebuilt the chat room: the presence stage is now a glass panel (not bare heads floating on the page); message bubbles have a real speech-bubble tail (CSS clip-path) and grouped-message spacing; a three-dot typing indicator; the mood row shows the person's own avatar reacting live next to the emoji strip, closing the loop instead of only lighting up a chip; an `expression`-kind message now renders as the sender's animated avatar, not a flat emoji. Chats list upgraded to the same avatar system with presence rings. Verified live in the real ForKhatri platform session (Chrome DevTools MCP, `chrome-devtools-milavn` profile): mood change shows simultaneously in the stage and the composer preview at 412px and 1440px, zero console errors; `tsc`/ESLint clean. | Owner: "i didnt like your chat and the avatar, its very old... do research on snapchat, chat window" — krishna kategaru (autonomous). |
| 2026-09-14 | **Messaging (owner decision, design direction §5–§7 completed).** After the owner challenged the "not doing" list and asked for a Snapchat-like chat, each item was mapped to the thesis/brand and approved: reactions instead of likes, no public ratings, circle moments rings only, finite groups, video skipped for now, **locality only — never exact locations** (owner restated), external models later/async, curated themes. Built (migration 015, `milavn_connect`): conversations, members, messages, reactions, presence; **trust-scoped** by one definer helper `can_message()` (shared circle or shared activity, blocks honoured) with all creation through `create_conversation()`; RLS on every table; REST for state and a **WebSocket** (`/ws/chat`) for live events (message, reaction, retract, typing, presence/expression) with an in-process hub and polling fallback; unread counts; 30-second presence heartbeat (a timestamp, never a location). Web: Chats tab before Profile (Profile stays last), chat list with presence dots and mood badges, chat room with grouped bubbles, tap-to-react, photos, typing indicator, and **on-device expressions** (`lib/expressions.ts`: MediaPipe face landmarker blendshapes → smile/laugh/surprised/wink/thinking/love/neutral; only the word leaves the device; opt-in camera with a visible preview; manual mood row as fallback); **Message** button on person pages when allowed. Verified: two-member WebSocket smoke (Priya receives Asha's message, reaction, typing and expression events live), stranger refused with 403, non-member read 404, unread and group creation; browser scenario at phone and desktop; zero server errors. | Owner: "go… video you can skip… yes I agree with your recommendations" — krishna kategaru (autonomous). |
| 2026-09-14 | **ForKhatri platform identity (IMP25).** The development member stand-in is replaced by the real platform session: one `fk_session` cookie resolved by the Identity Bridge against the Identity & Trust Service, fail-closed 503, dev header off by default, WebSocket on the cookie, entrance redirect with `return_to`, platform sign-out, persistent way back to the ForKhatri hub. Live-verified 19/19. | Product owner: one ForKhatri sign-in, one member identity, then choose a module (`docs/ParentApp/07-tech-reqs.md` TR10–TR17). |
| 2026-09-14 | **Chat room v3 (IMP26).** The owner asked, honestly, whether the v2 room looked like a 2040 app; it did not (stage panel took a third of the phone, a timestamp under every message, tailed shadow bubbles, emoji chips always above the keyboard, "Not active" with no recency). Rebuilt the room's structure keeping navy/saffron and every avatar feature; migration 016 (`presence_of` + `last_seen_at`, `shared_context()`). The owner then reported "not syncing": "Here now" came from the app heartbeat, not from being in the chat — in-chat presence now comes from the socket hub. Verified with a real second participant over the WebSocket, both directions. | Owner: "is this a 2040 app?", "did you look at the screen?", "user is chatting but you're not syncing" — krishna kategaru (autonomous). |
| 2026-09-15 | **World research + paid spots (IMP27).** Five research tracks (friendship science, attendance behaviour, recommendation research, 2023–2026 product innovations, Indian community context) synthesised into `RESEARCH-BEHAVIOUR-2026.md` with a ranked roadmap (FR102–FR113). Built FR102 paid spots end to end on Milavn's side (migration 017) behind a Payment Services port; vendor and MOD06 logged as blocker B1. Verified 22/22 lifecycle scenario, hold-expiry scenario, browser flow. | Owner: "do rigorous research… make it the best meetup app of my community… run autonomously"; "payments section… skip the vendor, keep it as a blocker" — krishna kategaru (autonomous). |
| 2026-09-15 | **Discovery that fits (IMP30).** Who it's for (family, elders, beginners), food and drink with vegetarian and alcohol-free defaults for Eat/Celebrate, a real Free filter, returning-host reason, labelled fair start for new hosts, per-host variety cap, and "Not interested" with a reason (migration 020). Scenario 11/11; one crash found and fixed (variable-name collision). "Women only" deferred: needs a platform gender attribute. | Research roadmap items 9–10 — krishna kategaru (autonomous). |
| 2026-09-15 | **Research roadmap, first two batches (IMP28, IMP29).** Showing up: "Still coming?" with a kind way to free a spot, reminders 3 days and 2 hours before that repeat the member's plan, and a one-tap plan (migration 018). Belonging and safety: thank the host, "Would you come again?" instead of 1–5 chips, first-timer welcome for host and newcomer, "After the activity" for hosts, and Share my plan on WhatsApp with the Telangana T-Safe line for evenings (migration 019). Scenarios 11/11 and 15/15; two defects found by the scenarios and fixed (trust outbox grant; 500 on an invalid answer). | Research roadmap items 2–4 and 6–8 — krishna kategaru (autonomous). |
| 2026-09-15 | **IMP31 added** — regulars (keep my spot each time, own attendance count, welcome back) and photo privacy (don't include me, ask before sharing, remove a photo of me); migration 021. | Research roadmap items 11–12 — krishna kategaru (autonomous). |
| 2026-09-15 | **IMP32 added** — would meet again (private, mutual only); migration 022. | Research roadmap item 5 — krishna kategaru (autonomous). |
| 2026-09-17 | **IMP35–IMP37 added** — the remaining twelve picks from the competitor research; migrations 024–034. | Owner's selection — krishna kategaru (autonomous). |
| 2026-09-17 | **IMP34 added** — bringing someone with you (guests count against capacity; the waitlist keeps a party together); migration 023. First of the 14 capabilities the owner picked from the competitor research. | Owner's selection — krishna kategaru (autonomous). |
| 2026-09-15 | **IMP33 added** — defect fix: a past activity the member attended offered "You're going · Withdraw"; nothing stopped joining or withdrawing after the end. | Found during the FR106 browser check — krishna kategaru (autonomous). |

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
| FR096, FR097 (trust-scoped messaging, live expressions + expressive avatars) | IMP23, IMP26 | Yes |
| FR102 (paid spots — Milavn side; vendor/MOD06 blocked) | IMP27 | Yes (blocker B1 open) |
| FR103–FR105 (still coming?, two reminders, one-tap plan) | IMP28 | Yes |
| FR107–FR109 (thank the host + come again, welcome newcomers, share my plan) | IMP29 | Yes |
| FR110–FR111 (who it's for + food defaults, honest discovery) | IMP30 | Yes ("women only" deferred) |
| FR112–FR113 (regulars and welcome back, photo privacy) | IMP31 | Yes |
| FR106 (would meet again) | IMP32 | Yes |
| FR015–FR016 (after an activity ends — defect fix) | IMP33 | Yes |
| FR114 (bringing someone with you) | IMP34 | Yes |
| FR115, FR121 (circle door, assistants) | IMP35 | Yes |
| FR116–FR120 (familiar faces, steady host, cards, free now, polls) | IMP36 | Yes |
| FR122–FR124 (followed calendars, chapters, drives) | IMP37 | Yes (payments blocked) |
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
| B1 | FR102 money movement: the payment vendor (gateway/UPI rails) behind MOD06 Payment Services, and MOD06 itself (not built yet). Milavn's side is complete and uses a clearly labelled development sandbox until then. | MOD06 to implement or confirm the proposed contract in `milavn-service/app/components/payments/interface.py` (charges, cancel, refunds, events with a shared key) on its reserved port 8016; the owner to choose and contract the vendor; then set `PAYMENTS_PROVIDER=payment_services`, `PAYMENT_SERVICES_KEY`, `PAYMENT_SERVICES_WEBHOOK_KEY`. | Product owner (external dependency), MOD06 |
| B2 | FR102 organizer payouts (money reaching the host) | Belongs to MOD06; the organizer console already says payouts are not connected. | MOD06 |
| B3 | Festival-aware suggestions (research roadmap item 14) | Owner to confirm which community traditions Milavn serves: Somavamsha Sahasrarjuna Kshatriya / Patkar Khatri (Hyderabad), Punjabi Khatri, or both — festival calendars and date rules differ (`RESEARCH-BEHAVIOUR-2026.md` §1.10). | Product owner |

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

## IMP25 — ForKhatri platform identity: one sign-in, one member (ParentApp TR10–TR17)
**Traces from:** TR46, TR47, FR076–FR080, FR088; `docs/ParentApp/07-tech-reqs.md` TR10–TR17, TR24
**Status / Confidence:** Done / High

**Why:** the product owner decided ForKhatri is one app with one sign-in and one member identity; modules are entered from the hub (`docs/ForKhatri-Unified-Umbrella-App-Interpretation.md`). Milavn's IMP01/IMP15 development stand-in (`X-Milavn-Member-Id` + `/welcome` chooser in localStorage) had to give way to the platform session.

**Files touched**
- API: `app/components/identity_bridge/interface.py` (rewritten), `app/api/deps.py`, `app/api/routes/chat.py` (WebSocket), `app/config/settings.py`, `app/main.py` (CORS header list, client shutdown), `app/api/routes/occurrences.py` (creator identity level from the resolved member), `await` added at every `display_names_for` call (`routes/admin.py`, `circles.py`, `public.py`, `safety.py`, `components/circle`, `connect`, `conversation`, `discovery`, `notification`), `app/i18n/locales/*/common.json` (`auth.identityUnavailable`), `.env.example` (new), `.env` (local, not committed), `tests/conftest.py` + `tests/test_identity_bridge.py` (new).
- Web: `lib/platform.ts` (new), `lib/api.ts`, `lib/identity.tsx`, `components/AppChrome.tsx`, `components/SideNav.tsx`, `components/TopActions.tsx`, `components/DetailClient.tsx`, `app/welcome/page.tsx`, `app/me/page.tsx`, `app/chats/[id]/page.tsx`, `app/globals.css` (hub link), `locales/*/common.json` (`platform.*`), `.env.local`, `.env.example` (new).

**Approach**
- *Bridge (TR14/TR15).* `resolve_session(token)` → `POST /internal/v1/sessions/resolve` with `X-ForKhatri-Service`/`-Key` over one `httpx.AsyncClient` (2 s timeouts). Cache keyed by SHA-256 of the token: 30 s positive (never beyond `session_expires_at`), 5 s negative. Unreachable, 403 (key refused) or 5xx → `IdentityServiceUnavailable` → HTTP 503; never cached, never anonymous. `display_names_for` is now `async`, batches `POST /internal/v1/members/lookup` at 200, caches 60 s (unknown ids included), and degrades to "Community member" with a 5 s outage backoff.
- *Milavn-owned data stays in Milavn (TR11).* Scopes (`milavn.moderate`) come from `config/dev_identities.json` keyed by `member_id` — the interim role source until Milavn has a role table; the same file gives seeded members their dev avatar/handle. Other members: handle derived from the display name, no avatar (the web prefers the Milavn profile photo). `milavn_profile.member_profile` stays the member-link row, created lazily by onboarding (a platform member without it is routed to onboarding).
- *Request layer.* `deps.resolve_member_identity` is the only entry point for HTTP and the chat WebSocket: `fk_session` first; the legacy header/`milavn_member` cookie only when `DEV_IDENTITY_ENABLED=true` (default false; `/identity/dev/members` 404 otherwise). Because a cookie now authenticates, state-changing requests and the WebSocket handshake with a foreign `Origin` are refused (403 / close 4403).
- *Web (TR16/TR17).* Every call sends `credentials: 'include'` and no member header; `/identity/me` decides who is here. 401 on a member-only surface → `window.location.assign(<entrance>/?return_to=<href>)`; the public activity page (`/a/[slug]`, FR046) keeps rendering signed out and its RSVP call-to-action goes to the entrance and back. 503 → a retry state, not a redirect. `/welcome` is kept and hands off (return to Milavn home). Sign-out → `POST <identity>/v1/auth/sign-out` then the entrance; "Delete my account" opens the ForKhatri account area. A persistent way back to the hub: a glass grid icon first in the phone header actions, a "‹ ForKhatri" pill above the brand in the desktop rail.

**Verified**
- `pytest` 15 passed (bridge cache hit/expiry, digest-keyed cache, negative cache, 503 on outage and on refused key, moderator scope source, lookup fallback/backoff/batching, RLS binding from the cookie, dev header off/on, cross-origin POST 403); `ruff` clean; `tsc --noEmit` clean; ESLint 0 errors (warnings pre-existing).
- Live against the running Identity & Trust Service (Playwright, 412×915 and 1440×900), 19/19 — screenshots and `results.json` in `milavn-web/.logs/platform-identity/`: Asha (existing profile) home, circles, chats with platform names, host name on detail, chat WebSocket authenticated by cookie with no member id in the URL and live message delivery; Krishna (no Milavn profile) → onboarding → home; signed-out `/circles` → `http://localhost:3100/?return_to=http%3A%2F%2Flocalhost%3A3001%2Fcircles`; public activity page signed out; `X-Milavn-Member-Id` alone → 401; sign-out → Identity API 204, platform session 401 at once, Milavn API 401 after 26.4 s.

**Deviations / open items**
- Header follow-up (real-Chrome review at 390 px): the hub grid icon crowded the phone home header and wrapped the location line. The hub link now sits as a small "‹ ForKhatri" link above the Milavn wordmark (phone home), as a "Back to ForKhatri" row in the profile settings sheet, and in the desktop rail. The location line stays on one line with an ellipsis, and the actions keep People · Alerts · Profile (avatar right-most). Verified at 360/390/430/1440 (`.logs/platform-identity/20-*`, `21-*`).
- The contract (TR14) matched the running service exactly; nothing contradicted it.
- Pre-existing, not caused here: hydration mismatch in `DetailClient.tsx` date formatting (`formatDateLong`, server vs browser) shows the Next dev "1 Issue" badge on activity pages.
- `milavn-web/scripts/scenarios/*.mjs` (CDP harness) still sign in through localStorage/`X-Milavn-Member-Id`; they need the cookie (or `DEV_IDENTITY_ENABLED=true`) before they run again.
- Role source is still a JSON file; a Milavn role table (and moderator assignment flow) is the follow-up.
- Production: `platform_session_cookie` must become `__Host-fk_session`, the service key a real secret, and the web moves under the `/milavn` zone `basePath` (TR22).

**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

## IMP26 — Chat room v3: honest presence, visible context, a thread that reads like a conversation (FR096, FR097)
**Traces from:** FR096, FR097; DESIGN-DIRECTION-2030 §5–§6; TS188, TS191, TS192
**Status / Confidence:** Done / High (camera expression detection still verified by design review only)

**Why:** the owner showed the v2 room and asked whether it honestly looked like a 2040 app. It did not: the glass "stage" spent about a third of a phone on two cartoons whether or not anyone was there; every message carried its own "2 h ago"; bubbles had drop-shadowed tails; seven emoji chips sat permanently above the keyboard; an away person read as a flat "Not active". Colour and theme were not to change (owner: bring the avatar/Bitmoji *features*, not Snapchat's look). During the rebuild the owner also caught that the new markup was live before its styles ("did you look at the screen?") and that presence was wrong ("user is chatting but you're not syncing"): "Here now" meant *used Milavn in the last two minutes*, not *is in this chat*.

**Files**
- DB: `07a-db-implementation/migrations/016-chat-presence-context.sql` — `presence_of(uuid[])` also returns `last_seen_at`; new definer `shared_context(viewer, other)`: the soonest unfinished activity both are in (participant or organizer), otherwise a circle both belong to; it answers only for the member bound to the request (`milavn.member_id`), so the app role cannot probe what two other people share.
- API: `app/components/connect/chat.py` — `Person.last_seen_at`, `SharedContext`, `Conversation.context`, `shared_context()`; `Hub` counts open sockets per member per conversation (`present_in()`). `app/api/routes/chat.py` — `last_seen_at`, `context`, and per-member `here` on `GET /chats/{id}`; the "left" event is published only when a member's last socket on that conversation closes (a second tab keeps them here).
- Web: `app/chats/[id]/page.tsx` (rewritten), `components/MoodAvatar.tsx` (screen-reader name only from a localised label, otherwise decorative), `app/globals.css` (chat-room block replaced; v2 `.stage`, `.mood-row`, `.composer--chat`, `.cam-preview` rules removed; the shared `.msg__bubble` used by the activity thread kept), `locales/{en,hi,te}/common.json` (+23 chat keys each).
- Tests: `milavn-service/tests/test_chat_presence_hub.py` (new, 3 tests).
- Data: the six scenario-run messages in the Asha–Priya chat and one duplicate from the second sync run were soft-deleted (`deleted_at`; nothing hard-deleted) and replaced by a realistic exchange about the Charminar crawl, badminton and the lake clean-up.

**Approach (choice → reason)**
- *Presence, Snapchat's "Friends in Chat" pattern* → the other person's avatar rises above the composer only while they have this chat open, shows their live expression as a word, and carries the typing dots. The header has three honest states: **Here now** (socket in this chat) · **Active now** (heartbeat < 2 min) · **Active 12 min ago** (`last_seen_at`).
- *Why you can talk (FR096)* → a slim strip under the header names the next shared activity with date and time (or the shared circle) and links to it.
- *A conversation, not a log* → one person's messages within 10 minutes merge into one silhouette; a 45-minute pause or a new day opens a centred "Today · 8:03 pm" marker; no per-message timestamps (tapping a message shows its time in the reaction bar); no avatars beside bubbles in 1:1 (header and dock carry identity), kept in groups; mine solid navy (saffron in dark), theirs raised paper, no gradients; reactions as a pill on the bubble corner; double-tap = ❤️; Unsend for your own messages.
- *Your avatar is the mood control* → a tray of your own avatar in all seven expressions (tap shares your live mood, tapping it again sends it as a sticker) plus the opt-in on-device **Mirror my face** camera with its privacy line.
- *Quick replies* → only when the last message is theirs and the draft is empty; worded for the shared activity ("On my way", "See you there", "Running 5 min late"), otherwise generic.
- *One composer pill* → send appears only with text (photo otherwise); the textarea grows to five lines; the page (not an inner element) scrolls to the end because the footer is sticky.

**Verified**
- Database: `shared_context` returns the Charminar crawl for Asha→Priya; the same call on Priya's behalf inside Asha's request context returns nothing.
- Live with two real participants (TS191): Asha in the milavn Chrome profile at 412×880; Priya through a platform development session (test mode) driving the real Milavn WebSocket. On Asha's screen: Priya joins → *Here now*, ring and dock; smile → header and dock change with "Smiling"; typing → "Priya is typing…" and dots; her message arrives without reload; laugh; her 👍 lands on Asha's message. On Priya's socket: Asha's quick reply (58.6 s), mood (97.9 s) and sticker (113.4 s). Priya leaves → *Active just now*, dock empty. After the `here` fix, reloading at 1440×900 once Priya had left shows *Active now* and no dock (before the fix it wrongly showed *Here now*).
- `pytest` 18 passed (3 new hub tests + identity bridge); `ruff` clean; `tsc --noEmit` clean; ESLint 0 errors.
- *Mirror my face, after the owner's screenshot* (the tray stayed open over the conversation, the camera preview floated over the header, and the dev overlay showed "1 Issue"): starting the mirror now closes the tray and puts your live avatar, its expression word and a 30 px mirrored camera preview on the right of the presence dock (people who are here stay on the left). A new expression is applied after two matching readings (~0.4 s) so it follows the face without flicker. The "Issue" was MediaPipe printing `INFO: Created TensorFlow Lite XNNPACK delegate` through `console.error`; while a session runs, only `INFO:` lines are dropped. One scripted run on the owner's real camera (412×580): tray closed, dock on, stream live, last message still above the dock, expression sampled each second `Neutral ×6 → Smiling ×2 → Neutral → Love it`; zero console errors; camera stopped at the end.

**Deviations / open items**
- The seeded "Street food crawl at Charminar" starts at 12:00 am, and the strip shows that as it is.
- In-chat presence lives in the single API process's hub; a broker replaces it when there are several processes (already noted in `chat.py`).
- The sync scenario ran as a manual script (`priya_live.py`, scratchpad); Step 10 turns TS191 into an automated test.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

## IMP27 — Paid spots: Milavn's side of paid activities (FR102)
**Traces from:** FR102, BR18 boundary, FR036, thesis §38 and §53–§55; `RESEARCH-BEHAVIOUR-2026.md` roadmap item 1; TS193–TS195
**Status / Confidence:** Done on Milavn's side / High · money movement **blocked (B1)**

**Why:** the owner asked for "the payments section and everything you can implement, but skip adding the payment vendor; this is an external dependency I will take care of; keep it as a blocker." Some activities have real costs (court bookings, food crawls). The thesis says to monetise value creation, never belonging, and never to make trust purchasable; research on deposits (Halpern et al. 2015) shows charging to commit drives most people away. So free stays the default and a price is only for real costs, with one clear refund sentence.

**Files**
- DB: `migrations/017-paid-spots.sql` — `occurrence.price_paise`, `refund_cutoff_hours`; schema `milavn_ticketing` (`ticket`, `payment_event`) with member-self RLS; definer functions for every cross-member write: `held_spot_count`, `open_ticket_count`, `ticket_by_reference`, `record_payment_event` (idempotent), `attach_charge`, `mark_paid` (under the TR39 per-activity lock; returns `going`, `refund_no_spot` or `refund_cancelled`), `mark_failed`, `mark_void`, `mark_refund_pending`, `mark_refunded`, `expire_holds`, `create_waitlist_offer`, `tickets_to_settle`, `money_summary` (aggregates only), `offer_context`.
- API: `components/payments/interface.py` (new: provider-agnostic port with `none`, `sandbox` (localhost only) and `payment_services` (MOD06 HTTP contract) adapters, event-caller key check); `components/ticketing/interface.py` (new: join/hold, waitlist offer, withdraw with the refund rule, payment events, cancellation refunds, hold-expiry job); `api/routes/payments.py` (new: `GET/POST /occurrences/{id}/ticket`, `POST …/ticket/withdraw`, `GET …/money`, `GET /tickets/mine`, `POST /payments/events`, sandbox checkout routes); `components/activity/interface.py` (price fields, validation, `PaymentRequired`, holds count against capacity, paid spots are offered rather than auto-promoted, `join_waitlist`); `api/routes/occurrences.py` (price on create/edit, price lock once tickets exist, Going toggle refused on paid activities, paid spot must be withdrawn through the refund flow); `components/discovery/interface.py` + `api/schemas.py` (`price_paise` on cards, holds reduce spots left); `components/notification/interface.py` (paid, offered, refund started, refunded, host "is going"); `config/settings.py` (`payments_provider`, Payment Services URL on MOD06's reserved port 8016, keys); `main.py` (router, cancellation subscriber, minute hold-expiry loop); `i18n/locales/*` (7 messages × 3 languages); `.env` (`PAYMENTS_PROVIDER=sandbox`, local only).
- Web: `app/create/page.tsx` (Entry: Free/Paid, ₹ price, refund window chips, organizer note); `components/DetailClient.tsx` (price and refund line, Join · ₹, hold and "Complete payment", waitlist, Paid · Withdraw with a refund-preview dialog, return-from-checkout confirmation); `app/pay/sandbox/page.tsx` (new: "TEST CHECKOUT · NO REAL MONEY MOVES"); `app/organizer/[id]/page.tsx` (totals only, payouts not connected); `app/me/page.tsx` ("Payments & refunds" in settings); `components/ActivityCard.tsx` (price pill); `lib/format.ts` (`formatInr`); `components/AppChrome.tsx` (`/pay/` chromeless); `app/globals.css`; `locales/*` (`pay.*`).
- Tests: `tests/test_paid_spots.py` (9).

**Approach (choice → reason)**
- *15-minute hold that counts against capacity* → two people can never pay for the same last spot.
- *Full waitlist is free; a freed paid spot is offered in order with a window* (12 h, never past 1 h before the start, at least 30 min) → nobody is charged for something they did not choose again; a lapsed or failed offer passes to the next person.
- *One refund rule* (full refund up to the cutoff, none after; always full when the host cancels or a late payment finds the activity full) → readable in one sentence before paying; the withdraw dialog states the exact amount.
- *Totals only for organizers; no "who paid" anywhere* → thesis §55 and the research anti-pattern list.
- *Price and refund window lock once anyone is paying or has paid* → nobody's terms change under them.
- *Provider-agnostic port with a localhost-only sandbox* → the whole product flow is real and testable now; connecting MOD06 is a configuration change.
- *Payment data never reaches trust or ranking* → FR036, enforced by a unit test over the trust and discovery sources.

**Verified**
- `paid_spots_scenario.py` (TS193): 22/22 through the real flow with platform sessions for Priya (host), Asha and Vikram — see TS193 for every step. All rows it created were removed afterwards.
- `paid_hold_expiry_scenario.py` (TS195): Asha's lapsed hold expired by the API's own minute job and the spot was offered to Vikram; removed afterwards. (First attempt failed on the script's database helper, not the app; its leftover activity was removed and the run repeated.)
- Browser (milavn Chrome profile, 412×580): activity page shows "₹250 per person · Full refund if you withdraw by Saturday, 19 September at 7:00 am" and "Join · ₹250"; the test checkout opens with its banner; after "Pay ₹250 (test)" the page returns as "You're going · ✓ Paid ₹250 · Withdraw" with the plan-together thread unlocked. Create shows Entry Free/Paid, ₹ price, refund chips and the organizer note. The test payment was removed; one realistic paid activity remains for the owner to try ("Sunday badminton, shared court booking", Priya, ₹250, 8 spots).
- `pytest` 32 passed; `ruff` clean; `tsc --noEmit` clean; ESLint 0 errors.

**Deviations / open items**
- **B1 (blocker):** no money moves until MOD06 Payment Services and the owner's payment vendor are connected; see Open blockers.
- **B2:** organizer payouts belong to MOD06.
- Notification texts for payments are English only, like the existing notification subscribers (a platform-wide gap, not specific to FR102).
- Scenario scripts live in the session scratchpad; Step 10 turns TS193/TS195 into automated tests.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

## IMP28 — Showing up: still coming?, two reminders, one-tap plan (FR103, FR104, FR105)
**Traces from:** FR103–FR105, FR052, thesis §38; `RESEARCH-BEHAVIOUR-2026.md` roadmap items 2–4; TS196–TS198
**Status / Confidence:** Done / High

**Why:** the research's strongest, cheapest attendance levers. Early cancellation is worth more to organizers than guilt: a reminder that says a missed spot affects someone else cut missed visits from 21.1% to 14.2% and raised early cancellations (Berliner Senderey et al. 2020); two reminders beat one (Steiner et al. 2018); asking *how* someone will get there raises follow-through, most for people living alone (Milkman et al. 2011; Nickerson & Rogers 2010). The thesis already asked for "still coming?" prompts without punishing anyone (§38).

**Files**
- DB: `migrations/018-showing-up.sql` — `participation.plan_travel`, `plan_with`, `confirmed_at`; `milavn_notification.reminder_sent`; definer `claim_reminders(kind)` (claims and records due reminders in one statement); `reminder_candidates()` narrowed to people only Interested.
- API: `components/notification/interface.py` (`reminder_copy`, staged `send_reminders`); `components/activity/interface.py` (`AttendancePlan`, `my_plan`, `set_plan`, `confirm_attendance`, `NotParticipating`); `api/routes/occurrences.py` (`PUT /occurrences/{id}/plan`, `POST /occurrences/{id}/confirm`, detail adds `my_plan` and `still_coming_due`); `i18n/locales/*` (`plan.notGoing`).
- Web: `components/DetailClient.tsx` ("Still coming?" card with *Yes, I'm coming* / *Can't make it · free my spot* — paid spots open the refund dialog; plan card with two chip rows collapsing to "Your plan: … · Change"); `locales/*` (`show.*`).
- Tests: `tests/test_showing_up.py` (5).

**Approach (choice → reason)**
- *Kind, prosocial words and no penalties anywhere* → the anti-pattern list and the owner's non-punitive no-show decision; a unit test fails if penalty words appear.
- *Windows wide enough for a 10-minute job, claimed in the database* → no duplicates even if runs overlap or the API restarts.
- *Not asked of the host, or of someone who joined within 3 hours* → a question that makes no sense is noise.
- *Plan is private to the member and the host, and repeated back two hours before* → the mechanism that made planning prompts work; "on my own" becomes a welcome line.
- *Plan answers do not bump `updated_at`* → answering must not postpone the still-coming check.

**Verified**
- `showing_up_scenario.py` 11/11 through the real flow and the real job code: three activities hosted by Priya (tomorrow, in 3 days, in 2 hours); Asha and Vikram joined; Asha's plan saved and an unknown value refused; the job sent 8 reminders and a second run sent nothing new; "Still coming tomorrow?" with `?confirm=1`, "In 3 days" with day, time and Madhapur, "Starts at …" repeating "by metro or bus" and the say-hello line; Asha's page asked in place, her "Yes" was recorded once; Vikram freed his spot; the host received no attendee reminders. All rows removed afterwards (the "joined within 3 hours" guard was passed by shifting the participation clock, the only shortcut).
- Browser (412×580): Asha going to "Morning walk around Durgam Cheruvu" (a realistic activity left for the owner) sees "You're going" then "How are you getting there?" and "Coming with" chips in place.
- `pytest` 32 passed; `ruff` clean; `tsc` clean; ESLint 0 errors.

**Deviations / open items**
- Reminder and notification texts are English only, matching every existing notification (platform-wide gap: notifications should render in each member's language).
- The "Still coming?" card itself was verified through the API (`still_coming_due`) and the scenario; it appears on screen only inside the last 28 hours, so the browser check showed the plan card.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

## IMP29 — Belonging and safety: thank the host, one private question, welcome newcomers, share my plan (FR107, FR108, FR109)
**Traces from:** FR107–FR109, FR066–FR069, FR056, FR063/FR064; `RESEARCH-BEHAVIOUR-2026.md` roadmap items 6–8; TS199–TS201
**Status / Confidence:** Done / High

**Why:** research items with strong evidence and low cost. Thanks is worth more to hosts than people expect (Kumar & Epley 2018) and keeps volunteers going (Grant & Gino 2010); one short private question beats ratings that inflate (Galesic & Bosnjak 2009; Zervas et al. 2021; owner decision: no public star ratings); newcomers stay when someone welcomes them (Choi et al. 2010; Morgan & Halfaker 2018); safety built into the format is standard in the best IRL products and matters for evening mobility in India (Timeleft, 222, Bumble; Time Use Survey 2019; Telangana T-Safe).

**Files**
- DB: `migrations/019-belonging.sql` — `milavn_trust.thanks` (sender/host RLS), `feedback.come_again`, definers `thanks_message`, `is_first_timer`, `after_summary`, `reputation_labels` + "appreciated_host" (3+ thanks); **fix:** `SELECT, INSERT, UPDATE` on every component's `outbox_event` for the app role.
- API: `components/trust/interface.py` (`COME_AGAIN`, `submit_feedback(come_again)`, `give_thanks` → `thanks.given` once, `has_thanked`, `thanks_received`, label text); `components/activity/interface.py` (`Attendee.company`, `first_time`, `is_first_timer`, `after_summary`); `api/routes/feedback.py` (`come_again` validated as yes/maybe/no, `POST /feedback/thanks`); `api/routes/occurrences.py` (attendees add `company`, `first_time`; `GET /occurrences/{id}/after`; detail adds `first_time`, `thanked`); `components/notification/interface.py` ("is going · first time" for the host; `_on_thanks` in the attendee's words); `i18n/locales/*` (`reputation.appreciated_host`).
- Web: `components/DetailClient.tsx` (thanks card with four presets and own words; "Would you come again?" replaces the 1–5 chips; "Your first Milavn activity" card; "Share my plan with family" → WhatsApp, T-Safe line for evening activities in Telangana); `app/organizer/[id]/page.tsx` ("First time" and "On their own" chips; "After the activity" with came, first-timers, would come again and thank-you notes); `locales/*` (`belong.*`).

**Approach (choice → reason)**
- *Thanks notifies once; rewording is free* → no notification spam, and people can fix a typo.
- *Only people who checked in or attended can thank or answer* → feedback means something; the host cannot thank themselves.
- *First-timer = no check-in before this activity's start* (not account age) → it is about showing up, which is what the welcome is for.
- *Counts for the host; individual answers for nobody* → FR067/FR069 and the no-ratings decision.
- *Share my plan sends words, never a location beyond the locality* → the owner's locality-only rule; WhatsApp is how families already coordinate.

**Verified**
- `belonging_scenario.py` 15/15 through the real flow: Priya hosts; Asha (returning) and Ravi Kumar (a real first-timer: no earlier check-ins) join; Ravi's plan "on my own"; Priya's list and notification mark Ravi as first time; Ravi's page shows the card and Priya's does not; Asha cannot thank before check-in (409); Priya checks both in with the organizer tool; Asha thanks with a preset, rewords without a second notification, answers Yes; an unknown answer is refused (422); Priya is notified once in Asha's words; "After the activity" shows 2 / 1 / 1 of 1 and the note; a participant gets 403. All rows removed afterwards.
- **Defects found and fixed by the scenario:** (1) the app role could not mark `milavn_trust.outbox_event` rows dispatched, so the first thank-you crashed the response after commit — granted in migration 019 (applied to all four outboxes); (2) an unknown come-again answer returned 500 — now validated in the request model (422), and the scenario check was tightened from "any error" to exactly 422.
- Browser (412×580): Asha on "Morning walk around Durgam Cheruvu" taps "Share my plan with family"; the captured WhatsApp text reads "I'm going to Morning walk around Durgam Cheruvu on Wednesday, 16 September at 6:30 am in Madhapur, hosted by Priya on Milavn. I'll message you when I'm back." with the link, and no T-Safe line (morning).
- `pytest` 32 passed; `ruff` clean; `tsc` clean; ESLint 0 errors.

**Deviations / open items**
- The thanks card, the come-again card and the first-activity card were verified through the API and scenario; the browser session (Asha) has no attended activity or first-timer status to show them on screen without fabricating data.
- Notification texts are English only (platform-wide gap, as in IMP27/IMP28).

**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

## IMP30 — Discovery that fits: who it's for, food defaults, returning hosts, fair start, variety, "Not interested" (FR110, FR111)
**Traces from:** FR110, FR111, FR005/FR007/FR008/FR009; `RESEARCH-BEHAVIOUR-2026.md` roadmap items 9–10; TS202–TS203
**Status / Confidence:** Done / High ("women only" deferred)

**Why:** whether a community member can come depends on family, elders, first-timers and food (Pew 2021: 81% of Indians limit meat); the research ranked the organizer as the strongest signal for new events (Zhang & Wang 2015), explanations must be simple and checkable (Herlocker et al. 2000), new hosts need a fair, labelled share (Abdollahpouri et al. 2019), and people need a way to say "not for me" and why (Harper et al. 2015). The Discover "Free" chip was a disabled placeholder that became untrue with paid spots.

**Files**
- DB: `migrations/020-discovery-fit.sql` — `occurrence.audience_tags`, `food_tags` (checked values; veg and non-veg exclusive); `milavn_discovery.hidden_occurrence` (self RLS); definers `hosts_attended` (own history only, bound to the request's member) and `host_track_record`.
- API: `components/activity/interface.py` (`AUDIENCE_TAGS`, `FOOD_TAGS`, `invalid_tags`, tags on create/update/read); `components/discovery/interface.py` (`RankingEngine.score` + `host_times`, `host_held`, `host_name`; reasons `host_before` and `new_host`; `cap_per_host`; `hide`, `hidden_for` with "joined activities never disappear"; search filters `free`, `audience`, `food`; hidden items excluded from Around You, calendar, map and search); `api/routes/discovery.py` (filters, `POST /discovery/hide`); `api/routes/occurrences.py`, `api/schemas.py` (tags); `i18n/locales/*` (two reasons × 3 languages).
- Web: `app/create/page.tsx` ("Who it's for" chips; "Food & drink" row for Eat/Celebrate with Veg + Alcohol-free pre-selected and a note); `app/discover/page.tsx` (real Free chip, Family & kids chip, who-for and food in More filters); `components/DetailClient.tsx` (tag pills; "Not interested" with four reasons in the More sheet); `lib/api.ts`; `locales/*` (`fit.*`).
- Tests: `tests/test_discovery_fit.py` (4).

**Verified**
- `discovery_fit_scenario.py` 11/11 through the real flow (Priya hosts; Asha searches, checks in at Priya's chai meetup through the organizer tool, hides activities) — see TS202/TS203. All rows removed afterwards.
- **Defect found and fixed by the scenario:** a new per-host dictionary reused the name `held`, which the paid-spots code uses inside the same loop; creating any activity crashed. Renamed to `track_record` and re-run. (A second failure was in the test script itself: the card's own `status` field overwrote the stored HTTP status; fixed in the script, not the app.)
- Browser (412×580): on Create, choosing Eat shows "Who it's for" (Family & kids, Elder-friendly, Beginners welcome) and "Food & drink" with Veg ✓ and Alcohol-free ✓ pre-selected and the default note.
- `pytest` 36 passed; `ruff` clean; `tsc` clean; ESLint 0 errors.

**Deviations / open items**
- **"Women only" is not shipped:** enforcing it needs a gender attribute, and the platform identity holds basic information only (standing decision). A label that cannot be enforced would mislead; recorded for the owner/platform to decide.
- "Too far" and "bad time" are stored with each hide but do not yet change ranking weights; they are the data for that tuning.
- The fair-start reason rarely wins against locality in practice (by design, it is a small boost); it is unit-tested rather than forced in the scenario.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

## IMP31 — Regulars and welcome back; photo privacy (FR112, FR113)
**Traces from:** FR112, FR113, FR012, FR092, FR103–FR104; `RESEARCH-BEHAVIOUR-2026.md` roadmap items 11–12; TS204–TS205
**Status / Confidence:** Done / High

**Why:** repeated time together is what turns acquaintances into friends (Hall 2019) and habits form in a stable context (Wood & Neal 2007), so a person who comes back each week should not have to re-join each week; after a miss, a warm welcome works and a broken streak drives people away (Milkman et al. 2021; Silverman & Barasch 2023). Photos of identifiable people are personal data (DPDP Rules 2025), consent to take is not consent to publish, and photo abuse is a real harm for women in South Asia (Sambasivan et al.).

**Files**
- DB: `migrations/021-regulars-and-photo-privacy.sql` — `milavn_activity.series_regular` (self RLS); definer `keep_regular_spots(occurrence)` (free, active, future series dates only; skips the host and anyone blocked either way; waitlist place when full; advisory lock per occurrence); `series_recent_attendance` (last four held dates, answers only for the bound member); `claim_reminders` gains `missed_last`; `occurrence_photo.removed_at` / `removal_requested_by`; `milavn_activity.photo_preference` (self RLS); definers `photo_opt_outs` (only people who were there, shown only to someone who was there) and `request_photo_removal` (any thread viewer; returns the uploader).
- API: `components/activity/interface.py` (`is_regular`, `set_regular`, `recent_attendance`; `occurrence.created` payload now carries `activity_id`); `api/routes/occurrences.py` (`POST /occurrences/{id}/regular`, refused for paid series, the host and anyone without a check-in in the series; detail `series.regular`, `series.my_recent`); `components/notification/interface.py` (`reminder_copy(missed_last=)`, subscribers `_on_series_date_added` and `_on_photo_removed`); `components/conversation/interface.py` (removed photos excluded; `photo_preference`, `set_photo_preference`, `photo_opt_outs` with first name + last initial, `request_photo_removal` publishing `photo.removed`); `api/routes/conversation.py` (`opt_outs` on the photo list, `POST …/photos/{photo}/remove`, `GET/PUT /moments/preference`); `i18n/locales/*` (`regular.*`, `moments.notFound`).
- Web: `components/DetailClient.tsx` (series section: "You've been to X of the last Y", "Keep a spot for me each time" / "Stop keeping my spot"); `components/Moments.tsx` (inline "Before you share" card with opt-out names and two confirmations; "I'm in this photo · remove it" for others' photos); `app/me/page.tsx` (Settings → "Photos of me"); `locales/*` (`regular.*`, `moments.*`).
- Tests: `tests/test_showing_up.py` + welcome-back wording (37 passing).

**Verified**
- `regulars_photos_scenario.py` 15/15 through the real flow and the real reminder job (Priya hosts a weekly ride; Asha and Ravi checked in by Priya; Vikram withdrew) — see TS204/TS205. All activities, the series, preferences, reminder rows, notifications and the uploaded file removed afterwards.
- Browser (412×580): Profile → Settings shows "Photos of me" with "Fine to include me" / "Please don't include me".
- `pytest` 37 passed; `ruff` clean; `tsc` clean; ESLint 0 errors.

**Deviations / open items**
- A regular is offered after one check-in, not two as first planned: with one, the person has actually come, which is the fairness concern; asking for two delayed the benefit for weekly groups by a fortnight.
- The children rule is a confirmation by the person sharing; Milavn cannot verify a parent, and does not do face recognition (by design).
- Notification texts are English only (platform-wide gap, as in IMP27–IMP30).

**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

## IMP32 — Would meet again: private picks, mutual only (FR106)
**Traces from:** FR106, FR042–FR045, FR062; `RESEARCH-BEHAVIOUR-2026.md` roadmap item 5; TS206
**Status / Confidence:** Done / High

**Why:** after meeting someone new, people underestimate how much the other person liked them (Boothby et al. 2018) and so rarely follow up; a mutual, private choice removes the fear of rejection and turns a one-off meeting into a second one (Hall 2019). It stays count-free, activity-framed and mutual only so it can never become a popularity score or a dating mechanic (FR044–FR045).

**Files**
- DB: `migrations/022-meet-again.sql` — `milavn_connect.meet_again` (chooser-only read/delete RLS; inserts only through the definer); `meet_again_told` (definer-only; stops repeat notifications); definers `meet_again_candidates` (after the start, only for someone who was there, never themselves or a blocked person), `pick_meet_again` (returns picked / mutual / new_mutual), `my_connections` (mutual only, bound to the request's member).
- API: `components/connect/interface.py` (`meet_again_candidates`, `pick_meet_again` publishing `connection.formed` only for a new mutual pair, `connections`); `api/routes/connect.py` (`GET /people/meet-again/{occurrence}`, `POST /people/meet-again`, `GET /people/connections`, declared before `/people/{member_id}`); `components/notification/interface.py` (`_on_connection_formed`: both told once, by first name, link to the person page); `i18n/locales/*` (`meet.notThere`).
- Web: `components/DetailClient.tsx` ("Would you meet anyone again?" card after the thanks card, optimistic toggle with rollback); `app/people/page.tsx` ("You'd both meet again" section); `locales/*` (`meet.*`).

**Verified**
- `meet_again_scenario.py` 13/13 through the real flow (Priya hosts and checks in Asha, Ravi and Meera; Vikram does not come) — see TS206. Activity, picks, told rows and notifications removed afterwards.
- Browser (412×580), Asha on the seed "Held last week: street cricket" (she attended): the card lists Meera Iyer and the host Vikram Rao with the privacy line; nothing was picked, so no data was written.
- `pytest` 37 passed; `ruff` clean; `tsc` clean; ESLint 0 errors.

**Deviations / open items**
- No discovery boost from connections yet: showing "someone you'd meet again is going" would reveal attendance, which is private (FR040). It needs an explicit opt-in design first.
- Notification text is English only (platform-wide gap).

**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

## IMP33 — After an activity ends: attendance is a record, not an RSVP (FR015, FR016 — defect fix)
**Traces from:** FR015, FR016, FR018, FR040; TS207
**Status / Confidence:** Done / High

**Defect:** on a past activity Asha had attended, the page showed "✓ You're going · Withdraw", "2 going", "Why this: 1 person from your circles is going" and "Meera Iyer going". Tapping Withdraw would have erased a real attendance record (which feeds reputation and "Thank the host"). The API also let anyone join, withdraw or switch to Interested after the end.

**Fix**
- API `components/activity/interface.py` `set_participation`: `AlreadyAttended` when a checked-in/attended member tries to withdraw or step down; `OccurrenceEnded` for any change once the activity is over (end time, or three hours after the start when no end is set — the same rule as the chat context). Ticketing's own settlement (`via_ticket`) and a walk-in scanning a still-valid check-in code (`checking_in`) are exempt. `api/routes/occurrences.py` maps both to 409 with localised messages (`occurrence.ended`, `occurrence.alreadyAttended`, 3 languages).
- Web `components/DetailClient.tsx`: checked-in/attended shows "✓ Attended" (free and paid alike); an ended activity shows "This activity has ended" instead of Going/Interested/Withdraw; the count reads "N went"; spots-left and interested are hidden; "Why this" is hidden; circle mates read "went"; the privacy line reads "Who went is private". `locales/*` (`detail.ended`, `wentCount`, `attendeesPrivatePast`, `circleMatesWent`).

**Verified**
- `ended_activity_scenario.py` 6/6 (Priya hosts; Asha checked in; Ravi Going; Meera tries after the end) — see TS207; all rows removed.
- Browser (412×580), Asha on "Held last week: street cricket": "✓ Attended" in the action bar, "2 went", "Who went is private — only the organizer sees the list.", no "Why this" line, and "From your circles: Meera Iyer went".
- `pytest` 37 passed; `ruff` clean; `tsc` clean; ESLint 0 errors.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

## IMP34 — Bringing someone with you (FR114)
**Traces from:** FR114, FR015–FR016, FR058, FR102, FR112; TS208; the 2026-09-17 competitor research
**Status / Confidence:** Done / High

**Why:** the owner picked this first from the research: in this community people bring a spouse, a cousin or a child, and every comparable product counts those people (Meetup counts up to five guests per RSVP and keeps a party together on the waitlist; Partiful makes plus-ones first-class; 222 offers one so nobody arrives alone). Milavn only had "coming with: family" as a private plan note, which no capacity arithmetic saw — so a host could plan for twelve and have twenty arrive.

**Files**
- DB: `migrations/023-bring-someone-with-you.sql` — `occurrence.max_guests_per_member` and `participation.guest_count` (both 0..4, default 0); `spots_taken()` (people + guests) and `guest_total()`; `promote_next_waitlisted()` rewritten to promote the first waitlisted party that FITS the freed room, skipping (never splitting or demoting) a party that does not; `keep_regular_spots()` (FR112) now measures the same way.
- API: `components/activity/interface.py` (the column through `Occurrence`/create/update with validation — refused on paid activities; `spots_taken`, `guest_total`, `my_guest_count`; `set_participation(guests=…)` with the party in every capacity decision, the new `NoRoomForGuests` guard for someone already going, guests cleared on withdrawal, and a freed guest promoting the next party; `Attendee.guests`); `components/discovery/interface.py` and `components/ticketing/interface.py` count spots the same way; `api/routes/occurrences.py` (create/update field, `guests` on the participation body, `guests`/`spots_left` in the response, `max_guests_per_member`/`my_guests`/`guest_total` on the detail, `guests` on the attendee list, 409 mapping); `i18n/locales/*` (`guest.noRoom`).
- Web: `app/create/page.tsx` ("Can people bring someone?" — hidden for paid); `components/DetailClient.tsx` ("Bringing someone?" chips in place once Going, the guest total beside the going count, and spots-left/Full now taken from the server instead of being re-derived on screen); `app/organizer/[id]/page.tsx` ("+N" beside the attendee); `locales/*` (`guest.*`, with singular/plural forms).

**Verified**
- `guests_scenario.py` 8/8 against the live API — party of 3 waits as one, party of 2 fits exactly, raising guests beyond the room is refused (409), a freed guest promotes the waiting party of 1. Demo activity and every participation row removed afterwards.
- Browser (412×580) as Asha: Going reveals Just me / +1 / +2 in place; +1 survives a reload; the header reads "2 going · 2 guests · Full".
- **Three defects found by looking at the screen, all fixed:** the detail page computed "spots left" from people only (`capacity - going`), so it advertised room that guests had taken — it now uses the server's count everywhere; "1 guests" needed a singular form in all three languages; and on the create page, switching Entry to Paid left "Can people bring someone?" showing (the condition tested the computed `pricePaise`, which is `0` — falsy — until a price is typed, rather than the `paid` toggle itself) — now gated on `paid`, and choosing Paid also resets any guest count already picked.
- `pytest` 37 passed; `ruff` clean; `tsc` clean.

**Deviations / open items**
- Guests are free-activity only. Paid activities need a ticket per person, which is the vendor-blocked path (B1).
- The host sees a count, not names. Partiful can require plus-one names; that is a bigger privacy decision for this community and is not built.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

## IMP35 — Getting into a circle: questions, the organizer's yes, and assistants (FR115, FR121)
**Traces from:** FR115, FR121, FR020–FR021, FR059; TS209; the 2026-09-17 competitor research (picks 2, 3, 17)
**Status / Confidence:** Done / High

**Why:** every product that runs real communities screens its door — Meetup asks up to five questions and holds each request as pending, Luma has approval-required registration, Geneva and Heylo screen applicants — and Meetup's own guidance (with Liu & Suel's study this module already cites) says groups survive when the organizer is not alone. Milavn circles were join-instantly and had exactly two roles.

**Files**
- DB: `migrations/024-circle-join-questions-and-approval.sql` (`circle.join_policy`, `join_questions`, `join_request` with one pending row per person, definers `request_to_join`, `pending_join_requests`, `decide_join_request`, `my_join_request_status`); `025-circle-dispatch-reads.sql` (`circle_name`, `circle_organizer_ids` for the notification dispatcher); `026-circle-join-prompt.sql` (`join_prompt` — name, policy and questions readable to a non-member, nothing else); `030-circle-assistants.sql` (role `assistant`, `can_moderate_circle`, `set_circle_role`); `031-assistants-can-let-people-in.sql` (both join definers and the notify list now ask `can_moderate_circle`).
- API: `components/circle/interface.py` (`invalid_join_setup`, `request_join`, `my_request_status`, `pending_requests`, `decide_request`, `join_prompt`, `set_role`); `api/routes/circles.py` (join takes answers and returns joined/pending; `GET /{id}/join-prompt`, `GET /{id}/requests`, `POST /{id}/requests/{request}/decide`, `POST /{id}/roles`; detail carries policy, questions, my status, waiting list and the umbrella); `components/notification/interface.py` (`_on_circle_join_requested`, `_on_circle_join_decided`); `i18n/locales/*`.
- Web: `app/circles/page.tsx` (create: "Who can join?" with up to two questions); `app/circles/[id]/page.tsx` (answer in place, "Waiting to be let in", the waiting-list card with answers, assistant chips and one-tap role change); `locales/*` (`join.*`, `role.*`).

**Verified**
- `circle_join_scenario.py` 16/16 against the live API; assistant rules in `community_batch_scenario.py`. Every row removed.
- **Two defects found and fixed while testing:** the "you are in" notification never arrived, because the dispatcher cannot read a `join_request` row (its RLS is the requester's own) — the circle now travels in the event payload; and the waiting list was gated on `viewer_role == "organizer"`, so an assistant could decide requests through the API but never saw them on screen.
- Browser (412×580): the circle screen shows the waiting list, the assistant label ("Helps run it") and the role control.
- `pytest` 37 passed; `ruff` clean; `tsc` clean.

**Deviations / open items**
- A declined request is silent by design; the person sees the state on the circle page if they look.
- Questions are asked once, at the door. Meetup re-asks on rejoin; Milavn keeps the last answers on the request row instead.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

## IMP36 — Deciding together, and being around (FR116, FR117, FR118, FR119, FR120)
**Traces from:** FR116–FR120, FR024, FR034–FR037, FR108; TS210; the 2026-09-17 research (picks 6, 7, 8, 9, 20, 27)
**Status / Confidence:** Done / High

**Why:** Partiful polls for a date before the event exists and Dice lets friends vote on which show to attend — the same small primitive, and the way a family actually decides. Couchsurfing's Hangouts exist because most meeting up is not planned a week ahead. Timeleft's table cards and 222's written intro both exist because the first two minutes are the hard part. Meetup marks people you have met before, and is adding a badge for hosts who keep showing up.

**Files**
- DB: `migrations/027-familiar-faces-and-steady-hosts.sql` (`familiar_count`, `reputation_labels` + `steady_host`); `028-free-right-now.sql` (`free_now`, `free_now_nearby` — shared-circle only); `029-circle-polls.sql` (`poll`, `poll_option`, `poll_vote`, all circle-scoped by RLS).
- API: `components/circle/interface.py` (`create_poll`, `polls`, `vote`, `close_poll`); `components/connect/interface.py` (`set_free_now`, `clear_free_now`, `my_free_now`, `free_now_nearby`, `familiar_count` on the person page); `config/icebreakers.py` (the prompts, chosen by category and stable per activity); `api/routes/circles.py` and `api/routes/connect.py`; `api/routes/occurrences.py` (`GET /{id}/conversation-cards`, only for people going and only around the time); `i18n/locales/*` (`reputation.steady_host`).
- Web: `app/circles/[id]/page.tsx` (ask the circle, vote by tapping, voters by name, settle, and "Create the activity" at the most-picked time); `app/people/page.tsx` ("Free right now" with one tap); `app/p/[id]/page.tsx` ("You have both been to N activities"); `components/DetailClient.tsx` (conversation cards with "Another one"); `locales/*` (`poll.*`, `free.*`, `cards.*`, `person.familiar*`).

**Verified**
- `community_batch_scenario.py` 23/23: votes by name, only the asker settles, shared-circle-only visibility for free-now, the familiar count for a pair and zero for a stranger.
- Browser (412×580): the circle screen shows the question with Meera's name against Sunday.
- **Defect found on screen and fixed:** a date option rendered as "just now" — it was formatted with the relative-time helper meant for the past; it now shows the actual date.
- `pytest` 37 passed; `ruff` clean; `tsc` clean.

**Deviations / open items**
- Activity-kind polls exist in the API; the screen currently creates date polls only. Proposing a specific activity to a circle is the natural next step.
- Conversation cards are English only in this pass (the prompts are content, and translating them well is a writing job, not a string swap).

**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

## IMP37 — Bigger than one circle: chapters, drives, followed calendars (FR122, FR123, FR124)
**Traces from:** FR122–FR124, FR026–FR029, FR102; TS211; the 2026-09-17 research (picks 14, 18, 23)
**Status / Confidence:** Done / High (payments remain blocker B1)

**Why:** one community often runs in several cities (Meetup Pro networks); a calendar is a thing you follow, not a file you export once (Luma); and the capability the Indian products have that none of the Western ones do is collecting money for something the community needs — Mera Samaj's own case study is an admin collecting in months what had taken twelve years by hand.

**Files**
- DB: `migrations/032-follow-a-calendar.sql` (`calendar_follow`, `followed_host_ids`, `public_activities_of`); `033-chapters.sql` (`circle_group`, `circle.group_id`, `group_chapters`, `set_circle_group`); `034-community-fundraisers.sql` (`fundraiser`, `fundraiser_pledge`, `fundraiser_totals`, `fundraiser_pledges`).
- API: `components/activity/interface.py` (`follow_host`, `followed_host_ids`, `is_following`, `public_activities_of`); `api/routes/public.py` (`GET /public/hosts/{id}/calendar.ics`, a real VCALENDAR built server-side); `components/circle/interface.py` (`create_group`, `set_group`, `groups`, `chapters`, `group_of`, `create_fundraiser`, `fundraisers`, `pledge`, `pledge_list`, `mark_pledge_paid`, `close_fundraiser`); `api/routes/circles.py` and `api/routes/connect.py`.
- Web: `app/circles/[id]/page.tsx` ("Part of …" with sister chapters, and Drives with totals, the promises-only note and one-tap promise); `app/p/[id]/page.tsx` (Follow, and "Add to my calendar app").

**Verified**
- `community_batch_scenario.py` 23/23: the umbrella and its other chapter, totals visible to all with individual amounts only to organizers, a member refused the pledge list, following private to the follower, and the .ics feed carrying the public activity.
- Browser (412×580): the circle screen shows "Part of Sahasrarjun Samaj", the sister chapter, and the drive with "₹2,000 promised of ₹15,000".
- **Defects found on screen and fixed:** "1 members" and "1 people" needed singular forms in all three languages.
- `pytest` 37 passed; `ruff` clean; `tsc` clean.

**Deviations / open items**
- **Money does not move (blocker B1).** A pledge is a promise, clearly labelled, and an organizer ticks off what has arrived by hand. `paid_at`/`payment_reference` are where Payment Services attaches with nothing else to change.
- The feed is public-activities-only by necessity (an .ics URL is unauthenticated). A private per-member feed would need a token, which is a separate decision.
- An umbrella has no page of its own yet; chapters are reached from a circle that belongs to one.

**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

# 02a - Functional requirements, as built (FR089 - FR160) - MOD02 Milavn

**Document status (2026-11-22, as built).** Continuation of `02-functional-requirements.md` (sealed FR001-FR088). FR089-FR124 have full text in `AgentOutputs/02-functional-requirements.md`; section 1 summarises them. FR125-FR160 are new here and describe what was built 2026-09-18 to 2026-10-24, taken from code, migrations 035-055, `PLAN-places-events-groups.md`, `ONBOARDING-REDESIGN-2026-10.md`, `AgentOutputs/EVENT-PAGE-LEARNING-2026-10.md` and the QA-RUN files. Endpoints are in `API-REFERENCE.md`; tables in `07a-er-model.md` appendix A; traceability in `TRACEABILITY.md`.

Automated tests that exist (`milavn-service/tests/`): `test_admin_queue_grouping`, `test_chat_presence_hub`, `test_circle_posts_and_activity_chat`, `test_circle_suggestion_groups`, `test_discovery_fit`, `test_first_run`, `test_identity_bridge`, `test_paid_spots`, `test_showing_up`. Browser scenarios: `milavn-web/scripts/scenarios/*.mjs`. Everything else is manual (QA-RUN files). Common errors: 401 not signed in, 403 not allowed, 404 hidden by RLS, 409 conflict, 422 validation, 429 rate limit.

## 1. FR089-FR124 summary

| FR | Feature | Main endpoints | Status |
|---|---|---|---|
| 089 | Ask-first natural-language discovery | GET /discovery/understand, /discovery/search | built |
| 090 | Smart fill for creation | GET /discovery/smart-fill | built |
| 091 | Activity thread (Plan together) | /occurrences/{id}/messages | built |
| 092 | Moments (photos after) | /occurrences/{id}/photos | built |
| 093 | Circle board | /circles/{id}/posts | built, extended by FR142 |
| 094 | Person page | GET /people/{member_id} | built |
| 095 | Circle home locality, nearby | GET /circles/discover | built |
| 096 | Trust-scoped messaging | /chats/*, WS /ws/chat | built, gaps in 08 |
| 097 | Live expressions, avatars | client side | built; critique M3 doubts value |
| 098 | Weekly digest | GET /discovery/digest | built |
| 099 | Poster image | client `lib/poster.ts` | built |
| 100 | Use where I am | GET /profile/places/nearest | built |
| 101 | Notification de-dup, live status | migration 011 | built |
| 102 | Paid spots | /occurrences/{id}/ticket, /payments/* | sandbox only; vendor blocked (B1) |
| 103-105 | Still coming, two reminders, one-tap plan | /occurrences/{id}/confirm, /plan | built |
| 106 | Would meet again | /people/meet-again | built |
| 107-109 | Thank host, newcomers, share my plan | /feedback/thanks | built |
| 110-111 | Who it is for; honest discovery | /discovery/hide | built |
| 112-113 | Regulars; photo privacy | /occurrences/{id}/regular, /moments/preference | built |
| 114 | Bring someone with you | participation guests | built; paid events cannot allow guests |
| 115, 121 | Circle door questions; assistants | /circles/{id}/join, /roles | built |
| 116-120 | Familiar faces, steady host, conversation cards, free right now, polls | /people/free-now, /circles/{id}/polls | built |
| 122-124 | Follow calendar, chapters, fundraisers | /public/hosts/{id}/calendar.ics, /circles/groups, /circles/{id}/fundraisers | built; pledge payment marked by hand |

## 2. New requirements

### FR125 Date-bound circles (temple visit, travel)
A circle may carry dates and type `temple` or `travel` (migration 035). Actor: member creating a circle. Endpoints: POST/PATCH /circles. Data: `circle`. Status: built. Test: manual (QA-RUN-community 8). BR05.

### FR126 Samaj updates to every chapter
An umbrella organizer posts one update that notifies every chapter (036, 037). Endpoints: POST /circles/groups/{id}/updates, GET /circles/groups/{id}/chapters. Data: `circle_group`, `circle_group_update`. Notice text English only (gap). Built.

### FR127 Live India place search
Type any Indian place, pick from suggestions. Source: shared places adapter (OpenStreetMap Nominatim, 1 request/second, cached); `PLACES_PROVIDER=none` disables. Flow: GET /profile/places?q= then PATCH /profile/place, or place on event/circle creation. Rule: only the approximate area and its centre are stored (FR038, BR09); the hardcoded 33-locality list was removed after a one-time carry-over (migration 050-live-places). Data: `member_profile.locality_*`, `occurrence.locality_*`, `circle.locality_state`. Screen: PlacePicker. Acceptance: a Jaipur member picks Bani Park; distance and map read the stored centre. Built. Gaps: thin Jaipur results, comma queries fail, OSM public-server policy (08 S-11). Tests: `test_first_run.py` partly, QA-RUN-fun 19.

### FR128 Exact venue after a confirmed spot
Organizer adds full address, arrival notes, optional map pin; public screens show the area only. Readers: organizer, co-organizers, people going/checked in/attended (a paid ticket makes `going`). Rules: RLS on `occurrence_venue`, write via `set_event_venue()`; changing the address clears the old pin; calendar feed and public page show area only. Endpoints: POST/PATCH /occurrences, GET /occurrences/{id}. Screens: event page going and hosting states. Built. Test: manual probe of about 30 endpoints (QA-RUN-safety 21, PASS). Gap: pin falls back to the city centre but looks exact.

### FR129 Online and hybrid events, protected join link
`attendance_mode` in_person/online/hybrid; organizer's own Meet/Zoom/Teams/YouTube link, provider detected and labelled. Link visible to confirmed attendees from 15 minutes before start (`ONLINE_JOIN_OPEN_MINUTES`) until the end; earlier Join returns 409; organizers always see it. Endpoint: POST /occurrences/{id}/join-online (marks checked in, `record_online_join()`). Built. Tests: manual (QA-RUN-professional 2, community 9).

### FR130 Recording and notes after an event
Organizer adds links; only confirmed attendees and organizer see them; `javascript:` refused. PUT /occurrences/{id}/followup. Data `occurrence_followup`. Built.

### FR131 Professional category and event formats
Category `professional` added to the eight; `event_format` (workshop, webinar, talk, panel, masterclass, book club, skill-share, office hours, bootcamp, conference, expo, cultural night, tournament, festival, satsang/bhajan, live darshan stream, town hall, volunteering drive, trip, meetup) separate from category. List: `milavn-web/lib/event-formats.ts`. Built. Gap: 20-option dropdown without search.

### FR132 Agenda, speakers, stalls
Sessions (time, title, details, speakers), speakers (name, bio, optional Milavn member link), stalls (number, name, description). Multi-day = one occurrence, one booking for all days. Read as visible as the event; write organizer/co-organizer. Endpoints: GET /occurrences/{id}/program; POST/DELETE sessions, speakers, stalls. Data `event_session`, `event_speaker`, `event_stall`. Screen EventProgram. Built. Gap: one check-in per ticket, no per-day count.

### FR133 Tournament teams
Organizer sets `team_size_max`; only confirmed attendees create or join teams; one team per person; size checked under lock; leaving the event removes the person from the team (trigger). Endpoints: POST /occurrences/{id}/teams, POST .../teams/{team_id}/join, DELETE .../members/{member_id}. Data `event_team`, `event_team_member`. Test: manual (QA-RUN-fun 14, PASS).

### FR134 Ticket types
Tiers with name (1-60), price (Rs 1 to Rs 100,000), quota, active; capacity stays one number; tier quota checked on top under the per-event advisory lock; quota cannot drop below sold. Endpoints: POST/PATCH/DELETE /occurrences/{id}/ticket-types, GET /ticketing, GET /ticket-admin. Data `ticket_type`, `ticket`. Tests: `test_paid_spots.py`, QA-RUN-professional 1.

### FR135 Discount codes
Percent or fixed, usage limit, expiry, never below Rs 1; plain messages for expired and used-up; organizer toggles. Endpoints: POST /discount-codes, PATCH /discount-codes/{id}, POST /ticket/quote. Data `discount_code`. A code already expired at creation is refused (fixed 2026-10-06).

### FR136 Booking, QR ticket, check-in by ticket
Quote, hold (expires, checked every minute), sandbox checkout, ticket with private QR and ticket code; organizer scans or types it. Withdraw: full refund before the 24 h cutoff, zero after; freed spot offered to the waitlist, with or without ticket types (migration 055). Endpoints: POST/GET /occurrences/{id}/ticket, /ticket/withdraw, /checkin/ticket, GET /tickets/mine, GET /occurrences/{id}/money, /payments/sandbox/*. Sandbox only; vendor and payouts blocked (B1, B2) and legally unreviewed (08 S-01).

### FR137 Organizer contact
Phone/email shown after confirmed booking or to every signed-in member, as chosen. PUT /occurrences/{id}/contact. Data `occurrence_contact`. Built.

### FR138 Link to Counsel
With `COUNSEL_BOOKING_URL` set, "Book a one-to-one with this expert" links to the organizer's Counsel page; empty hides it. Built (Counsel stays one-to-one, owner rule 2026-09-30).

### FR139 Flexible circle kinds
Custom `kind_label` over built-in kinds (temple, travel, local, interest). Data `circle.kind_label`.

### FR140 Women-only circles
"Women only" fixed at creation. Entry needs the member's own one-time answer "woman" (`member_gender`, private). DB trigger `circle_membership_women_only` covers every entry path; error WO001 becomes a respectful 403; inviting an ineligible member sends nothing. Endpoints GET/PUT /circles/gender/me. Built but self-declared; wording must not claim verification (critique C2). Tests: manual (QA-RUN-community 8, safety 23).

### FR141 Trip plan
Travel circles keep ordered stops with optional day and note. PUT /circles/{id}/trip-plan. Data `trip_stop`. Cost split: not built.

### FR142 Circle posts with photos and files
Up to 10 photos (10 MB) and 5 files (15 MB) per post, types pdf/doc/docx/xls/xlsx/ppt/pptx/txt, extension and first-bytes check, private, gated routes. POST /circles/{id}/posts and /posts/media. Data `circle_post_media`.

### FR143 Circle albums
Members add photos to named albums; uploader/organizer/assistant removes a photo; organizer/assistant removes an album; duplicate name 409. /circles/{id}/albums*. Data `circle_album`, `circle_album_photo`. Gap: cannot tie an album to one event.

### FR144 Circle notifications and setting
Per member per circle: all / highlights / off. New posts grouped and updated in place; one push per circle per person per hour; author not notified. GET/PUT /circles/{id}/notify. Data `circle_notify_setting`. Test: manual (QA-RUN-safety 20, PASS).

### FR145 Co-hosting circles
Host invites another circle; its organizer accepts; the event shows in both; one bell entry per person. /occurrences/{id}/cohosts, /cohost-candidates, /circles/{id}/cohost-invites/{occurrence_id}/respond. Data `occurrence_cohost`. Gap: card lacks "co-hosted with".

### FR146 First run, place only
Decision 2026-10-06: one screen, one answer (place); language from ForKhatri, never asked or overwritten; interests optional, asked later on Home; new profiles start at Zone precision; big-city shortcuts per language. Code `app/onboarding/page.tsx`, `lib/first-run.ts`. Test `test_first_run.py`.

### FR147 Editable interests
Add and remove, own words allowed, "Spiritual and temple" group; old tags stay valid. PUT /profile/interests, GET /profile/interests/taxonomy. Test `test_first_run.py`.

### FR148 A quiet Home widens
Empty Home widens to nearby cities and online events and says so; smart fill reads Hindi and Telugu day names. Code `discovery/interface.py pick_wider`, `nl.py`. Test `test_first_run.py`.

### FR149 Event page, four states
`DetailClient.tsx` renders deciding, going, hosting, recap. Built; remaining polish items from EVENT-PAGE-LEARNING partly open.

### FR150 Public event page
Server-rendered `/a/[slug]` from GET /public/occurrences/{slug}; area only, no attendee list. The earlier signed-out skeleton defect (relative API base on the server): fix *unverified*; verify by opening a slug signed out.

### FR151 Languages
English, Hindi, Telugu, Marathi, Kannada (1,297 web keys and 247 service keys each). Notices are stored in the language at send time (gap).

### FR152 Circle invites, links, recommendations (044, 046)
Invitation is accepted, never a silent add; organizer/assistant invite is approval; invite-link tokens; recommendations from people you know. /circles/{id}/invites, /invite-link, /circles/join/{token}, /circles/invites/mine, /circles/recommended.

### FR153 Circle deletion and covers (041, 042)
Organizer deletes only without upcoming events; cover upload and removal. DELETE /circles/{id}, POST/DELETE /circles/{id}/cover.

### FR154 Private media (045)
Circle and chat media only through database-checked routes (API-209 to 214).

### FR155 One open report per reporter (047)
POST /safety/reports returns the existing open report.

### FR156 Reminders expire at start (048)
`expires_at`; inbox and unread count ignore expired reminders.

### FR157 Activity chat and post social layer (049)
One group chat per occurrence for host and confirmed people, closing about 24 h after end; post comments, reactions, pins; announcements take reactions not replies. GET /chats/activity/{id}, /circles/{id}/posts/{post_id}/comments|reactions|pin. Test `test_circle_posts_and_activity_chat.py`.

### FR158 Platform member insights (039)
GET /internal/v1/insights/members (service key) gives city totals to the ForKhatri dashboard.

### FR159 Dismiss a notification
DELETE /notifications/{id}. **Partial**: needs the GRANT DELETE of migration 055, not applied in the dev database (08 S-12).

### FR160 Moderation console
`/admin/moderation`; /milavn/admin/* with dismiss, warn, escalate, restrict. Test `test_admin_queue_grouping.py`.

## 3. Not built
Per-day check-in; recurring events that create later dates by themselves; paid events with guests; real payments and payouts; steward approval for women-only; first contact as a request in chat; host verification for large events; DPDP retention and export; clean demo tenant. Speed networking and breakout rooms need in-app video, which is excluded (owner decision 2026-10-05).

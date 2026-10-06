# Milavn plan: live places, exact venues, large events, flexible groups

Status: PROPOSED. Nothing here is built. Waiting for owner approval.
Written 2026-10-05. Source: audit of milavn-service and milavn-web the same day.

## Why
- Places come from a hardcoded list of 33 localities (mostly Hyderabad). Members elsewhere in India cannot pick their own place.
- An event has no exact venue address, so "Going" cannot reveal where to turn up.
- Large events (workshops, talks, professionals' meetups) cannot sell tiered tickets or give a proper event page.
- Group types are a fixed list, and a women-only group cannot actually be enforced.

Group formats belong in Milavn, not Counsel (owner rule 2026-09-30). Counsel stays one-to-one advice.

## Step 1. Live India place search
What a member sees: type a place, pick from suggestions anywhere in India (state, district, city, area). No fixed list.
- A shared place-search utility (the shared integrations utility), so the data source can be swapped later without touching Milavn. Start with free OpenStreetMap-based data.
- The place picker, profile, events and circles all use it.
- Milavn keeps storing only an approximate area on public screens, as FR038 and BR09 require.
- The hardcoded list in `milavn-service/app/config/localities.py` is removed after existing data is carried over.
- Open point: existing events and profiles that point at the old list need a one-time carry-over.

## Step 2. Exact venue, shown after Going
What a member sees: before joining, the approximate area. After "Going" or buying a ticket, the full address, a map link and arrival notes.
- A separate venue address field on each event, visible only to people with a confirmed spot, the organizer and co-organizers.
- Directions link opens the exact venue, not a search on the area label.
- Online and hybrid events get a join link in the same protected spot.

## Step 3. Large events with tickets
What an organizer does: create a large event with ticket types (for example Standard, Early bird, VIP), each with its own price and quota, plus discount codes.
What a member gets: an event page (about, schedule, venue after booking, organizer details), a booking flow, and a QR ticket.
- Ticket types and per-type quotas on top of the existing paid spots, waitlist and refunds.
- QR ticket and organizer check-in by scan (check-in exists today).
- Organizer contact and organizer page link on the event.
- A professionals/consulting event category so these are easy to find.
- Payments use the shared payment utility. A real payment vendor is still a separate backlog item, so this runs on the sandbox until then.
- Optional link out to Counsel: "book a one-to-one with this expert".

## Step 4. Flexible, enforceable groups
What a member sees: create a group with any name and purpose, plus a women-only option.
- Group kinds become flexible: members can add their own label, while a few built-in kinds (temple, travel, local, interest) stay as shortcuts.
- Women-only setting that is enforced at join, not just screened by questions. It relies on the member's own profile answer, so it needs a clear, respectful wording and a way to report misuse.
- Travel groups get a simple trip plan: dates, route stops and who pays what. Cost split is optional.
- All Telugu and Hindi text is written accurately and respectfully (owner rule).

## Order and checking
1. Step 1, then Step 2 (Step 2 depends on the new place data).
2. Step 3 and Step 4 can run in parallel after that.
3. Each step: real flow tested in the browser as realistic people, no junk test data left behind, English/Hindi/Telugu text added, screens checked on mobile.

## Phase 2 (owner approved 2026-10-05): event formats and circle social
No in-app video. Online sessions use the organizer's own Google Meet / Zoom / Teams / YouTube link; offline events give the exact venue with a map.
Not possible without in-app video, so not built: speed networking rotation, breakout rooms.
- Step 5, events: event format (workshop, webinar, talk, panel, masterclass, book club, skill-share, office hours, bootcamp/multi-day, conference, expo, concert/cultural night, tournament, festival, satsang/bhajan, live darshan stream, town hall, volunteering drive, trip, meetup), agenda with sessions and speakers, multi-day events, expo stalls, team registration for tournaments, meeting-link provider detected and labelled, join link revealed close to start, tapping Join marks attendance, recording/notes link after the event, map pin for the exact venue.
- Step 6, circles: images and files on posts, circle photo albums, notifications for new posts, announcements, polls and events, per-circle notification setting (all / highlights / off), circles co-hosting an event with another circle.

## Decisions needed
- Free OpenStreetMap-based place data to start (recommended), or a paid geocoder now?
- Women-only: rely on the member's profile answer, or add a separate check?
- Travel cost split in Step 4 now, or later?

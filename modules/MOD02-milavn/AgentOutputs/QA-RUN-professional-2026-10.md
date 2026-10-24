# Milavn QA run: Professional group (2026-10-06)

People: #1 Ananya Iyer, #2 Rohan Deshmukh, #3 Sneha Reddy, #4 Vikram Chowdary, #5 Priya Nair.
Method: every scenario run through the real API as each person, plus real screens (390px mobile, one 1280px desktop glance) in the milavn browser. Everything created was deleted at the end; the 20 QA members are kept.

## Scenarios

1. Paid CA workshop on GST: PASS-WITH-NOTES.
   - Early bird Rs 499 (quota 10), Standard Rs 799 (quota 30), code GST20 (20%), 3 sessions each with a speaker, exact address, contact.
   - #3 booked Early bird with GST20: quote and charge were Rs 399.20, paid in the test checkout, QR ticket and ticket code appeared, exact address, arrival notes, map link and organizer phone/email appeared only after paying.
   - #5 (browsing) saw only the area, the agenda and speakers, ticket types, and "address shown once you are going". No address, phone or email in the page or the API.
   - Quota 10 could not be filled with 5 people, so I lowered Early bird to 1 (equal to sold): it showed "Sold out", quote and booking were refused (409), Standard stayed open.
   - Notes: the organizer can scan a ticket for a future event (no "too early" check); editing quota to 0 shows a raw validation list instead of a friendly message.
2. Online webinar on loans: PASS.
   - Free, 100 places, Google Meet. #4 marked Going. Event starting in 45 minutes: link hidden (state "later"), Join refused with "opens 15 minutes before the start". Event starting in 10 minutes: link shown labelled "Google Meet", Join marked #4 checked in.
   - After the start the organizer added recording and notes links; only #4 (and the organizer) saw them, #5 and #1 saw nothing. A javascript: link was refused.
   - Outsider (#5) gets the same "opens in 15 minutes" message as attendees, with no link.
3. Office hours with a lawyer: PASS-WITH-NOTES.
   - Weekly, 30 minutes, online, capacity 3. #1, #2, #4 got in; #5 was waitlisted at position 1. When #1 cancelled, #5 was promoted at once and notified "You're in". (Free events promote directly; there is no accept step, as designed.)
   - Bug fixed: adding the next week's date to the series lost the join link (see below).
   - Note: "weekly" only creates the first date; the organizer must add each following date by hand.
4. Doctors' networking circle: PASS-WITH-NOTES.
   - Approval-only with 2 questions. #1 applied and was approved; #4 applied and was declined.
   - #4 and #5 saw no posts, no polls, no members and could not post ("Join the circle first"). #1 saw both posts.
   - Note: a declined person can apply again straight away and shows as pending again (no wait time, no "declined" state).
5. Business expo: PASS-WITH-NOTES.
   - 2 days, Rs 300, 4 stalls (A1 to A4, visible to everyone), one booking covers both days (page says "Runs 2 days... One booking covers every day"). #5 booked and paid; address only after paying.
   - Check-in works with the ticket code, and a second scan says "already checked in", so day 2 entry is accepted.
   - Note: there is only one check-in per ticket, not one per day, so the organizer cannot count day 2 separately (needs a design decision and a migration; not changed).
6. Hybrid panel: PASS.
   - Address plus Zoom link, 3 speakers. #3 (not booked), #3 as Interested, #2 and anonymous visitors saw no address and no link. #1 after Going saw the address and notes; the Zoom link appears from 15 minutes before the start (labelled Zoom). Public pages and the host calendar file show only the area.
7. Expert link to Counsel: PASS.
   - Setting `COUNSEL_BOOKING_URL=http://localhost:3014/p/{member_id}` in milavn-service `.env` (Counsel web is on port 3014) and restarting only the Milavn API: "Book a one-to-one with this expert" appeared on a masterclass (button in Telugu for #3) and linked to Counsel's page for the organizer. With the setting removed (restored to the original file, which had no such line) and the API restarted, the link was gone.
   - Milavn API is running again on 8001 with the original settings.

## Bugs fixed
- `milavn-web/public/assets/covers/professional.jpg` was missing, so every Professional event had a broken cover image (the title overlapped the alt text). Added the file (copy of the Work cover, a placeholder until a dedicated photo exists).
- `milavn-service/app/api/routes/occurrences.py` (add a date to a recurring event): the exact address, arrival notes and join link were not carried over, so next week's online office hours had no link. Now copied from the first date unless the new date sets its own. Verified (Zoom link present, labelled Zoom).
- `milavn-web/components/DetailClient.tsx`: "Thank the host", "Would meet again" and "Will you come again?" appeared as soon as someone tapped Join or was checked in, even before the event ended. They now show only after the event has ended.

## Bugs not fixed
- No per-day check-in for multi-day events (scenario 5).
- A declined circle applicant can re-apply immediately (scenario 4).
- Recurring "weekly" does not create the later dates by itself (scenario 3).
- The detail page sometimes showed English text from the server (category name, "Why this" reason) on a Telugu page, right after the API restart. Likely the first request goes out before the member's language is applied; not investigated further.
- Quota below sold: a friendly message exists in the server but the form's own minimum of 1 produces a raw validation list for 0.

## UX observations
- The ticket section for someone holding an unpaid hold shows only "From Rs 499"; the chosen ticket type is not named until paid.
- Online events still show a map of the area before booking; harmless but unnecessary.
- Button "Book a one-to-one with this expert" in Telugu says "these experts" (plural) for a single organizer.
- Desktop glance of the event page looked right (cover, ticket section, side panel with Join).

## Hindi / Telugu items for native review
- Telugu "ఈ నిపుణులతో వ్యక్తిగత సంప్రదింపు బుక్ చేయండి" (one-to-one with this expert): plural "experts"; consider singular wording.
- Telugu "మొదట చేరేవారు అవ్వండి" (be the first to join) and "చెక్-ఇన్ అయ్యారు" (checked in): check naturalness.
- Telugu "Google Meetలో చేరండి" and "చేరండి నొక్కగానే మీ హాజరు కూడా నమోదవుతుంది": check naturalness.
- No Hindi screens were reviewed in this run (the Professional group's members use English and Telugu).

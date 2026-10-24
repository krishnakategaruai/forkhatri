# Milavn QA run: group "fun" (2026-10-06)

People: #11 Divya Menon, #12 Karthik Raman, #13 Pooja Agarwal, #14 Imran Qureshi, #15 Lakshmi Prasad.
Method: real API calls signed in as each person (server side), plus screens at 390px and one 1280px glance for the place picker, event page, discovery, circle photos.
Everything created was removed afterwards (events, tickets, codes, circles, posts, albums, files, notifications). The 5 QA members are kept; #11 and #13 are back at their original places.

## Scenarios

| # | Scenario | Result | Evidence |
|---|---|---|---|
| 13 | Biryani food walk | PASS-WITH-NOTES | Free, capacity 6, "up to 1 guest": three people each bringing one guest filled all 6 seats, spots_left 0; the 4th person got "full, you're on the waitlist". Paid cap-2 event: 2 paid, 3rd person waitlisted. NOTE: a paid event cannot allow guests (creation refused with a 422, and the create screen hides the guest chips when Paid is chosen), so "paid + 1 guest" as written is not possible by design. |
| 14 | Badminton tournament, teams of 4 | PASS | 2-day event, team size 4. Captain #11 made "Smashers", #13 and #14 joined, #15 made it 4 (full). Fifth person (#12) got "This team is full." A second team or joining another team was refused ("already in a team"). Not-booked people cannot register or join ("Book your spot first"). #14 cancelling their spot dropped them from the team (size 3). Captain cancelling passed captaincy to the next member. |
| 15 | Monthly book club + PDF | PASS-WITH-NOTES | Recurring Book club (rule monthly) with a second date added, poll "Which book next?", PDF posted to the circle. PDF: member 200 application/pdf; non-member #11 404; signed-out 404; also 404 through the web origin (3001), upper-case path and `..` paths. Joining the circle gave access, leaving removed it again. Non-member also sees no posts and cannot see the circle-only event. NOTE: the Create screen's "Repeats weekly" switch only sets a label; it never offers monthly and does not create the later dates (the series endpoint is not used by any screen). |
| 16 | Photo walk album | PASS | #12 and #14 each added 2 real files to "Charminar walk" (PNG and JPEG); a fake .jpg was refused (415); duplicate album name refused (409). #14 could not remove #12's photo (403); organizer #12 removed #14's (204) and its file then returned 404. Album list/photos: non-member gets empty list or 404, signed-out 401, files 404 to non-members. Screen: Photos tab shows the album and a "From posts" section with the post photo. Album belongs to the circle, not to the event, so it is not "after the event" aware. |
| 17 | Quiz night online, Rs 99, codes | PASS-WITH-NOTES | Expired code: "This code has expired." Used-up code (max 1, used by #13): "This code has already been used the maximum number of times." (quote and booking). Valid fixed code: Rs 99 became Rs 79, paid, QR ticket issued. Zoom link detected as provider "zoom", stays "later" until 15 minutes before start, and is hidden from a non-attendee. BUG FIXED: an organizer could create a code that had already expired. |
| 18 | Diwali cooking skill-share | PASS after fixes | #14 created Learn / Skill-share, Beginners welcome + Family & kids. Before the fix, "diwali cooking" was read as category Celebrate and found nothing even for #14 in the same city. After the fix it is found with any word order. NOTE: #11 lives in Bengaluru and the event is in Hyderabad; discovery is limited to the viewer's own city, so #11 cannot see it (by design). |
| 19 | Trek in a new city | PASS-WITH-NOTES | #13 chose Bani Park/Sodala (Jaipur) and #11 Koramangala (Bengaluru) through the live picker (screen checked). Each sees only their own city's trek: around-you "weekend", search "this weekend" ("trek this weekend" understood as Explore + this weekend), map pins, "~4.5 km away" for #13 after moving to Sodala. No Hyderabad events, no missing pins. Notes below on Jaipur place data and the venue pin. |

## Bugs fixed (not committed)

- `milavn-service/app/api/routes/tickets.py`: refuse a discount code whose expiry is already in the past (422, existing "Please check the details" message).
- `milavn-service/app/components/discovery/nl.py`: festival words (diwali, bathukamma, festival, party) no longer force the Celebrate category when other words follow ("diwali cooking" stays a text search); "beginners / family friendly / elder friendly / kids / seniors" are now understood as the "who it is for" filter.
- `milavn-service/app/api/routes/discovery.py`: `/discovery/understand` also returns `audience`.
- `milavn-web/components/AskBar.tsx`, `milavn-web/app/discover/page.tsx`: apply the understood audience as the existing filter chip and clear it with "clear".
- `milavn-service/app/components/activity/interface.py` (`list_visible`): search words are now matched one by one in any order (before: the whole phrase had to appear exactly, so "cooking diwali" or any extra word found nothing). Places column made null-safe.
- Milavn API (8001) was restarted once to load these.

## Bugs not fixed / gaps

1. Paid events cannot allow guests (a person bringing a friend must pay for them). Needs a product decision (guest pays, or guest seat free).
2. Recurring events: only a "Repeats weekly" label; no monthly option and no automatic later dates on the Create screen.
3. Event photos/"After the event" wall and circle albums are separate things; an album cannot be tied to one event.
4. Live place search for Jaipur is thin: "Malviya Nagar" and "C Scheme" return only other cities or nothing; "Malviya Nagar, Jaipur" returns nothing (comma queries with a city fail); "Mansarovar" returns Gujarat. Data comes from OpenStreetMap through the shared utility.
5. Venue pin: when the exact address cannot be found, the pin falls back to the middle of the city (Nahargarh Fort address pinned near MI Road) while the screen says "where to reach". It is approximate but looks exact.
6. Discovery shows only the viewer's own city; people travelling cannot browse another city without changing their place.
7. Event creation response omits `team_size_max` (the event page does show it).
8. The hidden series endpoint requires the full event body although it falls back to the parent's values.

## UX observations

- Discover (Hindi screen): the understood chips appear twice ("समझा:" and "आपकी बात से:" rows), and the chip words stay in English ("this weekend", "trek").
- Album cover collage shows a dark empty cell when the first photo is very small (test image only).
- "Charminar walk" album naturally belongs to a Hyderabad circle; the circle was created in Chennai only because #12 lives there.

## Hindi / Telugu for native review

- No new user-visible strings were added. The audience words in natural-language search are English only on purpose; Hindi and Telugu forms ("शुरुआती", "परिवार", "ప్రారంభకులు" and similar) need a native reviewer before they are added.
- Hindi event page (seen on #13's screen): "कहाँ पहुँचना है", "पहले जुड़ने वाले बनें", "यह क्यों: आपके इलाके Bani Park में" read well; the line "सिर्फ़ आयोजक सूची देखता है" under the going-count and "समुदाय में नए" badge are worth a native check.

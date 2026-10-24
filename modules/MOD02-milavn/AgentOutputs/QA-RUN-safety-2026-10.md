# Milavn QA run: safety group (2026-10-06)

People: #16 Nitin Bhosale, #17 Farah Khan, #18 Gaurav Malhotra, #19 Shalini Rao, #20 Manoj Patil (plus the milavn-moderator persona).
Method: real API calls with each person's own session, plus screens at 390px (emulated phone) in Hindi and Telugu.

## Results

| # | Scenario | Result | Evidence |
|---|---|---|---|
| 20 | Notification overload | PASS-WITH-NOTES | 5 quick posts gave #16 and #20 (setting All) exactly one entry "5 new posts"; #18 (Highlights) got only the announcement and the poll; #19 (Off) got nothing; author #17 got nothing. Bell on screen shows the grouped entry. The one-push-per-hour rule is in the database function (checked by reading it, not by counting pushes: no database login was available to me). |
| 21 | Venue privacy attack | PASS | As #20 (not booked, and a member of the accepted co-host circle), #18 (interested only), #19 (cancelled) and a signed-out caller, about 30 endpoints each (venue, join link, contact, follow-up, program/teams, ticket-admin, money, attendees, check-in, QR) returned no address, notes, join link, phone, email, other people's ticket ids or QR codes. Organizer-only endpoints answer 403. Team members are hidden from non-attendees. The page source for #20 contains none of the secrets. Follow-up links could not be set before the event starts (409), so that one is only tested as "nothing to leak". |
| 22 | Refund and cutoff | PASS-WITH-NOTES | Before cutoff #18 and #19 were refunded in full (money recorded, "Refunded" notice). After cutoff (event starting in 5 hours, 24 hour cutoff) #19 withdrew with refund 0 and the ticket is void; the ticket page says "refund if you withdraw now: 0". Waitlist: after #18 cancelled, #19 was offered the spot with a payment hold and a "A spot opened" notice; paying took the spot. FAILED for events without ticket types (see bug 1, fixed in code but not applied to the database). |
| 23 | Women-only misuse | PASS-WITH-NOTES | #17 made the circle, #19 joined. #16 cannot join (403 with a kind message), cannot create a women-only circle, and cannot accept an invite. #19 (inside) cannot switch her answer to man (403). #19's report reached the moderator with reason women_only_misuse ("someone in a women-only group who should not be"); a repeat by the same person returns the same report (no duplicate). Note: a man who has not joined anything can set his answer to woman and then enter (answer is self declared by design); I switched #16 back to man. |
| 24 | Hindi and Telugu | PASS-WITH-NOTES | Event page (paid, QR, venue), create form, women-only page with refusal, bell and place search checked at 390px: no raw keys, no horizontal overflow. English leftovers found and fixed: relative times ("4 min ago"), Hindi "12:29 pm बजे", organizer and money notices. Others listed below. |

## Bugs fixed (all uncommitted)

1. Freeing a paid spot on an event without ticket types gave the cancelling person a 500 error and the waitlist never got its offer ("record tt is not assigned yet"). Fixed in `07a-db-implementation/migrations/052-ticket-types-codes-contact.sql` (function `create_waitlist_offer`) and added as new migration `055-fix-waitlist-offer-without-ticket-types.sql`. **Not applied to the running database**: I have no owner database login (a request to read the credentials was refused). Someone with the owner login must run migration 055. Until then events with a waitlist and no ticket types still fail on cancel.
6. The "x" on a notification in the bell failed with 500 ("permission denied for table notification_inbox_entry": the app role has no DELETE right). Fix added to migration 055 (`GRANT DELETE`), **not applied** for the same reason as bug 1. This is also why my notification cleanup could not remove the entries.
2. `GET /circles/invites/mine` returned 500 for anyone with a pending circle invitation (Step 4 added two columns the old invite function does not return). Fixed in `milavn-service/app/components/circle/interface.py` (`my_invites` pads the two columns). Verified. Side effect: the invite card shows women_only false for a women-only circle (the old function does not return it); a clean fix is a database function change.
3. Relative times were always English ("just now", "4 min ago"): `milavn-web/lib/format.ts` `formatRelative` now follows the page language (Hindi and Telugu verified).
4. Hindi date line read "13 अक्टूबर को 12:29 pm बजे": `formatDateLong` in the same file now shows "date · time" in Hindi and Telugu.
5. Money notices ("You're in", "A spot opened", "Refund started", "Refunded", "X is going") were hard-coded English. Now translated per recipient in `milavn-service/app/components/notification/interface.py` (`_on_ticket`), with new keys `notify.ticket.*` in en, hi, te under `milavn-service/app/i18n/locales/`. Verified in Telugu and Hindi. I restarted the Milavn API on 8001 to load it.

## Bugs not fixed

- Many older notices are still hard-coded English and ignore the person's language: cancelled, time or place changed, organizer update, waitlist promotion ("You're in"), regular spot kept, first-timer going (organizer), thanks, photo taken down, meet-again, circle suggestion, "Update from {group}", reminders. They live in `notification/interface.py`. Same pattern as fix 5.
- A notice is stored in the language at the time it was sent, so after switching language old entries stay in the old language (the bell showed Hindi, English and Telugu mixed).
- First load after the account language differs from the browser's remembered language shows server-translated strings (for example "1 person from your circles is going") in the old language until a reload.
- Inviting a man to a women-only circle is accepted (201) and only fails when he accepts. Better to refuse at invite time.
- "Interested" and "waitlisted" people can read and write the event chat (the message says "people who are going and the organizer"). No venue leak, but the wording and the rule disagree; owner decision needed.

## UX observations

- Women-only refusal on the circle page shows two near-identical sentences one under the other.
- Circle page opens on the Events tab for a person who is not a member.
- Poll and announcement alerts use an alarm-clock icon, which reads as a reminder.
- Bell shows "5 new posts" in Hindi correctly, but the preview line is the last post only.

## Hindi and Telugu for native review

- Telugu "Nitin మిమ్మల్ని గమనిస్తారు" (first-event welcome; "will notice/observe you"): probably wants "మీ గురించి చూసుకుంటారు" or similar.
- Telugu uses "గ్రూప్" on the women-only page but "సర్కిల్" elsewhere; Hindi says "समूह" there and "सर्कल" in tabs. Pick one term.
- Hindi "आ रहे हैं" and "शामिल हुए हैं" in the new organizer notice (gender neutral on purpose): confirm tone.
- am/pm kept in Latin letters in both languages (time chips, "12:29 pm"); consider native forms.
- Place names stay as the map source gives them (English): "Shivajinagar, Pune", "Kakinada".
- Hindi refund wording "रिफ़ंड" and Telugu "రీఫండ్" are transliterations; check if the community prefers "धन वापसी" and "డబ్బు వాపసు".

## Cleanup

Circles (with their posts, polls, members) were deleted through the product API. Events can only be cancelled, so six cancelled "QA ..." events (QA Venue Privacy Tournament, QA Refund Early x2, QA Refund Late x2, QA Waitlist Typed) remain with their tickets (all refunded or void), and one women-only report stays open in the moderator list (no delete route). About 30 notification entries across the five members remain, marked read, until migration 055 is applied and they can be dismissed; the next person to run the seed script with --remove will clear them with the members. The 20 QA members are kept; their languages were set back to Hindi/English as seeded.

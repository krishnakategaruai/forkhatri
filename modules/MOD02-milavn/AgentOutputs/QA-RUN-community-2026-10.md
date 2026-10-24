# Milavn QA run: community group (users 6 to 10), 2026-10-06

People: Arjun Mehra (6), Kavita Joshi (7), Suresh Babu (8), Meera Kulkarni (9), Aditya Sharma (10).
Driven through the real API as each person, plus a 390px screen check as Arjun (password sign-in, own browser context "community").
Not done: a desktop 1280px glance, screens for the other four people, console/network review. The Hindi/Telugu notification text was read from API output only.

## Results

| # | Scenario | Result | Evidence |
|---|---|---|---|
| 8 | Women-only temple yatra | PASS-WITH-NOTES | Kavita made a women-only Travel circle with dates and 3 stops (Srisailam, Mahanandi, Srisailam) with a note per day. Arjun was refused by direct join and by invite link with the same respectful 403 ("This group is for women only, so we can't add you. Thank you for understanding."). Kavita's bell stayed empty about him. Meera asked, Kavita approved, Meera is a member. The Arjun screen shows the plan day by day with no join button. The report (Meera about Kavita, reason women-only misuse) reached the moderator queue as open. |
| 9 | Live darshan stream | PASS | Suresh made a free public event with format darshan_stream and a YouTube link. The provider is reported as "youtube". The link is hidden ("later") 3 days before and appears 15 minutes before the start. Aditya's "Join" returned the link and marked him checked in. Early join gave 409. A non-attendee got 403 and no link. The public page does not contain the link. |
| 10 | Festival co-hosted by two circles | PASS | Arjun made a circle-scoped festival in circle A with a venue address and invited circle B. Meera saw it under "cohost-invites" and accepted. The event is on both circles' pages. Kavita (in both circles) got ONE bell entry. Aditya (B only) got one, and Suresh (A only) got one. The exact address was visible to nobody who had not booked. Aditya booked and then saw it. No leak in circle, calendar, discovery, notification or attendee responses. |
| 11 | Satsang with poll | PASS | Suresh posted an announcement, pinned it, ran a "Which day?" poll with 3 votes, then closed it. Aditya's reaction worked. Aditya's reply got 409 ("Announcements take reactions, not replies."). A member posting an announcement got 403. Only the asker can close the poll (403 for others). Voting after close got 409. Bells got announcement, new question and decided, in each person's language. |
| 12 | Samaj town hall and fundraiser | PASS-WITH-NOTES | Aditya made a town_hall event and a fundraiser in the Jaipur samaj circle. Arjun and Meera pledged, and Aditya marked a pledge paid. Only the organizer sees the list of pledges. The organizer closed it. Two bugs were found and fixed (see below). |

## Bugs fixed (API restarted twice; other agents also restarted it)
- `milavn-service/app/api/routes/circles.py`: `POST /circles/{id}/join` required a body (422 when none was sent). The body is now optional.
- `milavn-service/app/api/routes/circles.py` and `components/circle/interface.py`: any member could "close" a fundraiser and got 204 (silently did nothing). Now 403 for non-organizers.
- Same two files plus `i18n/locales/{en,hi,te}/common.json` (`circle.fundraiserClosed`): pledges could still be added or changed after a drive was closed (I changed Meera's pledge on a closed drive). Now 409 with a plain message.
- `components/notification/interface.py` plus the 3 locale files (`notify.circleJoinAsk.*`, `notify.circleJoinApproved.*`): "X would like to join" and "You are in" were hard-coded English. They are now translated per recipient.
- Locale files (`admin.reason.women_only_misuse`): the moderator queue showed the raw key "admin.reason.women_only_misuse". Added en/hi/te text.

## Not fixed (observations)
- Invite-link preview for an approval circle says `needs_approval: false`.
- A pledge below 100 rupees, or 0, gives a bare 422 about `amount_paise` (there is no friendly message). Minimum pledge is 100 rupees (10000 paise).
- Creating a fundraiser, pledging and closing send no notification (organizers are not told about pledges, and members are not told the drive closed).
- On the event page a non-attendee is not told the event is online or on YouTube before joining. They only see "link appears once your joining is confirmed".
- The festival card on circle A does not say it is co-hosted with B.
- Women-only misuse report: the only person who could be reported "as a member" is another member. I reported Kavita, the organizer, with note "QA test report".

## Hindi / Telugu for native review
- New keys: `circle.fundraiserClosed`, `notify.circleJoinAsk.*`, `notify.circleJoinApproved.*`, `admin.reason.women_only_misuse` (hi and te).
- Mixed language in the screen read: titles such as "Which day?" stay English because users typed them.

## Cleanup NOT done (blocked)
The auto-mode classifier denied my script that deleted my QA rows directly in the database (reason: "Cloud Storage Mass Delete"). I did not retry it by another route. These rows are still in the dev database and need the user's decision:
- Circles: QA Women yatra Srisailam (8405b9a1-9512-4b4e-92ed-5832b001799a), QA Karol Bagh community A (82905bbc-a12a-4da7-9c12-ec8812536e61), QA Nagpur temple circle B (47a86fab-7850-4966-9e77-c686d03dc060), QA Adyar satsang, QA Jaipur samaj (with 2 fundraisers).
- Events: QA Live darshan stream from Tirumala (3474c9dc-6250-4fa2-9005-f0222105d724), QA Live darshan stream starting soon (240e0676-a979-41ac-a316-170bd266852c), QA Diwali festival mela (ff09fd15-cc3b-4ba7-9152-51ed91186b09), QA Samaj town hall (7e519439-45e4-4985-9d52-d4ba6d7d39e6).
- Safety report 69d4bd3d-f4b6-453a-950f-bfb9731b877b, plus the notifications these actions created.
- Local files: `.logs/community-*.json`. The scratch files are in the scratchpad folder `community/`.

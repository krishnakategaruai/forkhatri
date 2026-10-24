# Milavn UI/UX review, October 2026

Method: signed in as Asha Reddy over the tunnel and used Milavn at 390px (phone emulation) and 1280px. Screenshots are in the session scratchpad (home390, cal, circles, circle-events, event1, event3, create, notif, map, chats, me, event-desk). Read only; nothing was created or changed.

Limit of this review: the demo data has no upcoming events. Feed, Calendar, Map and Search all showed empty states. I could not open a live ticket picker, an agenda, a women-only badge or a paid or online event page, so those new features are not judged here. Judge them again once a future-dated rich event is seeded. That gap is also finding 1.

## Top 20 issues

**P0**
1. Every first-run surface is empty. Feed says "quiet around Jubilee Hills". Calendar says "Nothing here yet". Map says "0 nearby". Search shows "No matches" before any filter is set. A new member sees a dead app, and the new features cannot be discovered. Fix: seed rolling future events, and give each empty state one action ("Start something", "Browse circles").
2. The circle Events tab has a button labelled "New activity in this circle" (circle-events). It sits in the Upcoming row and also as the big orange button under the title. The label reads like a notification, not "Create an event here". Upcoming has no empty text under it. Fix: rename to "Plan an event here" and add an empty line under Upcoming.
3. Dead links from Alerts. Opening an event from several alerts (for example /a/occ-f711705c5a93) shows "Something didn't load. It's us, not you." with one Try again button. A missing event is not our fault, and retrying cannot help. Fix: a distinct "This event was removed or is private" screen with a way back.
4. The Members tab shows "Ask to help" and a red "Remove" side by side on every member row. Remove removes a person, and a thumb can hit it by accident. Fix: put both in a "..." menu and ask for confirmation.
5. Mixed signals on privacy and attendance. The page says "Who went is private - only the organizer sees the list" and, on the same page, "Vikram Rao, Priya Sharma went". An ended event shows "0 went" next to "You were there". On desktop it shows "2 going", "2 left" and "This activity has ended" together. Fix: one attendance line, driven by event state, and one rule for who sees names.

**P1**
6. The event page for a past event still offers live actions: Plan together, Add to calendar, Send. Fix: past events become a recap with photos first and the chat read only.
7. Hierarchy on the event page. "Updates from the organizer" sits at the very bottom, under Moments, with the destructive "Organizer tools" button after it. Eventbrite and Luma lead with host updates and the primary action. Fix: updates under the title, RSVP bar or ticket picker first.
8. The date is shown twice on desktop (date block and again in the right card), and the category "Play" is repeated on the hero and the date card. Fix: show each fact once.
9. Past events look the same as upcoming ones in lists. The circle page lists a past event under "Past" in the same full-size photo card. Profile "Going to" (7) and "Hosting" (5) are mostly past. Fix: dim and shrink past cards, and show only upcoming first.
10. The circle header spends a lot of space on "A real photo of your people works best / Add a cover photo" for everyone. Fix: show it only to the owner, and use a smaller banner.
11. The circle header has three icon-only buttons (invite, manage, bell). The accessibility names exist but sighted users get no label. The bell state "Notifications: Everything" is not visible. Fix: show the state as text or on long press.
12. Alerts all use the same wave icon with 3 to 4 near-identical "X is going" rows in a row. Fix: group by event ("Lakshmi and 2 others joined ...") and use different icons by type. The small "x" dismiss target is far below 44px.
13. The create flow puts Paid and Free on the main form, but formats, agenda and women-only appear to sit behind "More options" (I could not expand it in my test). Hosts will not find them. Fix: show chips for "Women only", "Online" and "Add agenda" in the main form.
14. The category grid has one orphan tile (Professional) with a label that touches the tile edges, and the "Kind of event" dropdown lists about 20 options with no search. Fix: a 3x3 grid and a searchable picker.
15. Hero photos can mislead. The badminton event shows a Brazil national-team match with olympic sponsor text. That weakens trust for a neighbourhood game. Fix: use the host's photo or a neutral illustration, and show a "Stock image" mark.

**P2**
16. Contrast. The green "ForKhatri Verified" text on the teal photo and the grey small caps labels (WHERE, ORGANIZER) are low contrast. Fix: raise to at least 4.5:1 on a solid chip.
17. Several touch targets are under 44px: the Feed/Calendar/Map/Search tabs are 40px high, the filter chips 36px, "See all" 42x18, the home "Use where I am" link 18px high, and the Speak and Search buttons 40x40.
18. Two different chat avatar styles: cartoon figures for people and a generic purple icon for groups. Everything else uses real photos. Fix: initials or photos only.
19. The home page has two voice and search entries (the search bar and four preset chips) before any content, plus a floating "Make something happen" button that overlaps the first card (home390). Fix: smaller button, and hide it on scroll down.
20. Hindi and Telugu fit was not checked in this pass. The pill tabs, chips and the 40px-high tab bar are the likely places for clipped text. Check before release.

## 10 quick wins (under a day each)
1. Rename "New activity in this circle" and add the empty text under Upcoming.
2. A "not found / private" screen for event deep links.
3. Confirm dialog and an overflow menu for Remove.
4. Hide the cover-photo prompt from non-owners.
5. Grey out past event cards and move them under a "Past" fold.
6. Make "Updates from the organizer" the first block under the title.
7. One attendance line per event state.
8. Raise all tap targets to 44px with padding, not size.
9. Group alerts by event and vary the icons.
10. Default Search to "Upcoming near me" instead of "No matches".

## 5 bigger redesign ideas
1. Event page as a recap or invitation. Upcoming: hero, ticket or RSVP bar pinned to the bottom (Luma and Eventbrite style). Past: photo wall first.
2. Stories-style row of circles on Home (Instagram stories), where a ring means new activity.
3. One adaptive feed card that shows format (online, paid, women only) as small badges, so the new features are visible at a glance.
4. A host mode: after Create, a checklist ("add agenda", "invite circle", "set tickets") instead of burying options.
5. Share sheet with a preview card and WhatsApp as the first target, since sharing is how Meetup and Instagram events spread.

## What is already good: keep
- The dark, calm theme with serif titles and one warm accent. It feels premium and is not cluttered.
- The create screen: describe-in-one-line with "Fill it in", icon tiles, quick time chips and a date strip. It is quick and friendly.
- The desktop layout: side navigation and a sticky event card with Share and Add to calendar.
- Trust cues: ForKhatri Verified, the "what this badge means" disclosure, "Who went is private", and "Would you meet anyone again?" (private mutual choice).
- "From your circles: Vikram and Priya went" social proof.
- The bottom navigation: five clear items with labels, and a notification bell on every top bar.
- Warm copy such as "A hello when they arrive goes a long way".

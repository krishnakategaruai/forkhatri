# Milavn functional benchmark vs event and community platforms (2026-10-06)

Read-only review. Milavn status comes from the service routes and the plan/research files (Steps 1-6 built). Competitor claims carry a source link; anything without one is marked unverified and comes from the earlier 2026-09-17 research pass (RESEARCH-BEHAVIOUR-2026.md section 5) or general knowledge. Milavn items marked "route found" were seen in the code but not clicked through in a browser.

## 1. Capability table

| Capability | Meetup | Eventbrite | Luma | Facebook | Instagram | Others | Milavn |
|---|---|---|---|---|---|---|---|
| Discovery and recommendations | Yes (unverified detail) | Search, yes (unverified) | Local calendars, yes ([Luma](https://help.luma.com/)) | Events and groups feed (unverified) | Not event-led | Nextdoor, Timeleft (earlier research) | Have: discover, around-you, map, recommended, search, digest, "why this", fair-start for new hosts |
| Quick creation (template, duplicate) | Duplicate not confirmed | Unverified | Unverified | Unverified | n/a | Partiful: simple invite (unverified) | Partial: smart-fill route; no duplicate or template found |
| Recurring events | Yes: weekly, 2-weekly, monthly, end date default 6 months ([Meetup help](https://help.meetup.com/hc/en-us/articles/39795590048781-Creating-a-repeating-event)) | Unverified | Unverified | Unverified | n/a | | Have: series, "make it a regular" (free only) |
| RSVP, waitlist, bring a friend | Yes (earlier research) | Tickets | Registration with approval ([Luma](https://help.luma.com/)) | Going/Interested | n/a | Partiful RSVP caps ([summary](https://sacra.com/c/partiful)) | Have: participation, waitlist, party of +N |
| Ticket tiers, discount codes, QR | Limited (unverified) | Yes | QR per guest, Apple/Google Wallet ([Luma check-in](https://help.luma.com/p/check-in)) | No | No | | Have: ticket types, codes, QR, scan check-in. Missing: wallet pass |
| Reminders and notifications | Series notices 6 and 1 days before ([Meetup help](https://help.meetup.com/hc/en-us/articles/39795590048781-Creating-a-repeating-event)) | Email | Email | Push | Push | Partiful text reminders ([summary](https://sacra.com/c/partiful)) | Have: 3-day and 2-hour reminders, "still coming?" at 24h, notifications. Channel (push/WhatsApp/SMS) not confirmed |
| Message all attendees | Yes (partly paywalled, earlier research) | Email | Yes (unverified) | Event chat | Channels | Partiful text blasts ([summary](https://sacra.com/c/partiful)) | Have: announcements, event messages. Partial: one channel only |
| Co-hosts | Yes | Unverified | Hosts and managers ([Luma](https://help.luma.com/)) | Yes (unverified) | Collab posts up to 3 ([Buffer](https://buffer.com/resources/instagram-new-features/)) | | Have: co-organizers and circle co-hosting |
| Organizer analytics | Yes (unverified) | Yes | Event Insights ([Luma](https://help.luma.com/)) | Page insights | Insights | | Missing: no analytics route; only per-event money totals |
| Payouts and refunds | n/a | Payout 3 days after the event, fees by country ([Eventbrite](https://www.eventbrite.com/help/en-us/articles/426093/getting-started-with-eventbrite-payment-processing/)) | Stripe (unverified) | n/a | n/a | Partiful: Venmo/CashApp links | Partial: refunds and sandbox payments yes; payouts explicitly not connected (code comment, MOD06) |
| Group posts, polls, albums | Limited | n/a | n/a | Polls, albums, chats, prompts, topics ([Social Samosa](https://www.socialsamosa.com/2020/10/facebook-new-features-groups), [Search Engine Journal](https://www.searchenginejournal.com/facebook-adds-public-group-discussions-to-news-feed)) | Channels: text, photo, voice, polls ([Instagram](https://about.instagram.com/blog/announcements/introducing-broadcast-channels/)) | | Have: posts with media, comments, reactions, pin, polls, albums, notify per circle |
| Roles and moderation | Co-organizer tiers | n/a | n/a | Admin Assist, keyword rules, conflict alerts ([Social Samosa](https://www.socialsamosa.com/2020/10/facebook-new-features-groups)) | | | Have: roles, join questions, approve joiners, reports, moderation queue, blocks. Missing: auto-rules, conflict alerts |
| Stories-like updates | n/a | n/a | n/a | Stories (unverified detail) | Stories, channels | | Missing: no short-lived update format (only chapter updates route) |
| Follows, trust, reviews | Member profiles | Organizer pages | Follow calendars | Friends | Follow | | Have: follow, host reputation, thanks, mutual "meet again", host recognition. Public star reviews: deliberately none |
| Sharing and growth | Share link | Share link | Share, calendar subscribe | Share | Share | | Have: invite links, host calendar.ics, WhatsApp share, QR ticket. Unverified: per-event "Add to calendar" button and event QR poster |
| Accessibility | unverified | unverified | unverified | unverified | alt text (unverified) | | Partial: aria in 43 web files, no event accessibility fields (step-free, seating, language) |
| Monetization | Subscriptions | Per-ticket fee, buyer pays unless organizer absorbs ([Eventbrite](https://www.eventbrite.com/help/en-us/articles/426093/getting-started-with-eventbrite-payment-processing/)) | Unverified | None | None | | Free by default; paid spots; fundraisers (promises only) |

## 2. Top 15 missing or weak functions (ranked for Milavn's users)

| # | Function | Why it matters | Done well by | Effort | Risk |
|---|---|---|---|---|---|
| 1 | Real payouts to hosts and live payments | Paid events cannot go live without them; hosts will not trust sandbox | Eventbrite (payout after event) | L | High: money, legal, depends on MOD06 |
| 2 | Duplicate event and "same as last time" template | Hosts repeat temple, satsang, trip events; saves minutes every time | Meetup repeat; others unverified | S | Low |
| 3 | Add to calendar on every event, plus WhatsApp-ready event card | Families live on WhatsApp and calendars; lowers no-shows | Luma (calendar), Partiful | S | Low |
| 4 | Organizer insights: views, joins, no-show rate, first-timers (private to host) | Hosts cannot improve without it | Luma Event Insights | M | Medium: keep it private, no public counts |
| 5 | WhatsApp delivery for reminders and announcements | Push is weak in India; WhatsApp is the channel (earlier research) | Partiful uses texts | M | Medium: cost, templates, opt-in rules |
| 6 | Attendee list export and printable check-in sheet | Offline halls with poor signal | Luma guest list | S | Medium: privacy, host-only |
| 7 | Wallet pass or offline-saved QR ticket | Door entry with weak network | Luma wallet | M | Low |
| 8 | Group auto-moderation rules and conflict alerts | Family groups need calm moderation | Facebook Admin Assist | M | Medium |
| 9 | Event accessibility info (step-free, seating, elder-friendly, language spoken) | Elders and families are core users | unverified | S | Low |
| 10 | Short updates ("stories-like", expire in 24h) in circles | Light participation; fewer heavy posts | Instagram, Facebook Stories | M | Medium: moderation of vanishing content, women's photos |
| 11 | Per-event channel to ask host questions before joining | Fewer cancellations | Facebook event chat (unverified) | S | Low |
| 12 | Host-chosen registration questions and approval per event | Women-only, family-only gatherings | Luma approval | M | Low |
| 13 | Multi-host roles beyond co-organizer (check-in-only volunteer) | Big events need door volunteers | Meetup tiers | S | Low |
| 14 | Collaborative posts between two circles | Chapters and samaj bodies co-announce | Instagram Collab (up to 3) | M | Low |
| 15 | Hindi and Telugu conversation cards and notification text (cards are English only) | Owner rule: all three languages | n/a | S | Low |

## 3. What Milavn does better or should keep unique

- Exact venue shown only after "Going" with approximate area in public. Platforms mostly show the full venue (unverified); Luma has approved-guests-only location ([Luma](https://help.luma.com/)).
- Mutual "would meet again" and one-tap thanks, with no counts or leaderboards.
- Women-only enforced at join, plus "who it's for" (family, elders, veg, alcohol-free).
- Kind reminders ("we held your spot") instead of deposits or shaming.
- Circles with join questions, approval, chapters, fundraisers and trip plans in one place.
- Free by default; trust tied to the ForKhatri identity.

## 4. Do not copy

- Per-ticket fee stacking (Eventbrite fees add to the ticket price by default; [source](https://www.eventbrite.com/help/en-us/articles/426093/getting-started-with-eventbrite-payment-processing/)). Small community tickets cannot bear it.
- Paywalling messages, member lists or waitlist priority (Meetup+ backlash, earlier research, unverified here).
- Public attendee lists, "who is going" social proof, no-show or reliability scores, streaks.
- Phone number required to RSVP; contact-import growth loops and invite spam.
- Public photo galleries, face search, live location.
- Public star reviews of hosts or members (marriage-adjacent communities turn this into reputation attacks). Keep private thanks and moderated reports.
- Algorithmic "people you may like" (turns meetups into rishta-hunting).

## 5. Five things to do next

1. Add "duplicate event" and a one-tap "repeat last event" (S). Fastest gain for hosts.
2. Put an "Add to calendar" and "Share on WhatsApp" card on every event page and confirmation (S).
3. Build a private host insights page (views, joins, no-shows, first-timers) and attendee export for check-in (M).
4. Finish the payment path with MOD06: real vendor, host payouts, refund reconciliation (L, starts the vendor decision now).
5. Send reminders and announcements through WhatsApp with opt-in, and complete Hindi/Telugu for cards and reminders (M).

## Caveats

Search tools returned summaries, not full help pages, for several platforms; those cells say unverified. A browser walk-through as realistic members should confirm the "have" cells before any roadmap decision.

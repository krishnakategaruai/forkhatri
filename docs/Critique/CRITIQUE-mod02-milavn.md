# Critique: MOD02 Milavn (meetups, events, circles, tickets, chat)

Written 2026-10-06. Read-only review. Sources: the module's own docs, the code, the existing REVIEW-* and QA-RUN-* files (not repeated here), real screens (phone width, signed in as QA member Kavita Joshi in Hindi, over the tunnel), and outside sources. "Unverified" means I could not open a source. The shared web-search budget ran out mid-task, so some law points rest on pages I fetched and some are flagged.

## 1. What I understand Milavn to be

Milavn is ForKhatri's "real-world participation" module, modelled on Meetup. A member gives a place and interests, sees events "around you" (feed, calendar, map, search, plain-language ask bar in English/Hindi/Telugu), taps Going, and can form or join circles (groups with a board, albums, polls, trip plans, fundraisers, chapters). Hosts can sell tickets (tiers, codes, QR, waitlist offers, refunds), run online or hybrid events with a join link that appears 15 minutes before, and keep the exact venue hidden until a spot is confirmed. Trust is shown as labels, never scores. Women-only circles are enforced at join from a one-time woman/man answer. There is 1:1 and group chat for people who share an activity or circle. Payments run on a sandbox until Payment Services (MOD06) and a vendor exist. Samaj heads are meant to run it. Please correct me if the aim is more "Samaj calendar" than "open meetup network"; much of what follows turns on that.

## 2. Critiques, ranked

### Critical

**C1. Paid events rest on a payment path the 2025 RBI rules may not allow.**
- Claim: Milavn built tiers, codes, waitlist offers, refunds and host totals, and treats the payment vendor and host payouts as a later external dependency ("blocker B1").
- Evidence: The RBI's consolidated Payment Aggregator Directions of 15 September 2025 "prohibit PAs from running marketplaces and mandate that a PA shall aggregate funds only for the merchant with whom it has a contractual relationship", and require escrow, ongoing merchant monitoring and FIU registration ([IndiaCorpLaw, 9 Oct 2025](https://indiacorplaw.in/2025/10/09/decoding-rbis-overhaul-of-the-payment-aggregator-directions/)). A search summary of the Directions also named event-ticketing platforms as covered (unverified in the primary text). Each host is a merchant. GST on admission, e-commerce-operator duties (GST/TCS) and TDS on payouts to hosts also apply (unverified here; confirm with a CA).
- Why it matters: A Samaj member who hosts a Rs 499 workshop would need KYC, a bank account and possibly GST. If ForKhatri pools the money itself it may be running an unauthorised marketplace. Eventbrite pays out "3 days after you complete your event" ([Eventbrite](https://www.eventbrite.com/help/en-us/articles/426093/getting-started-with-eventbrite-payment-processing/)); hosts will expect the same.
- Recommendation: Decide the legal shape before more ticket features: (a) a licensed PA/escrow partner with host onboarding, or (b) a single ForKhatri/Samaj-owned entity as the merchant for Samaj-run events only, or (c) hosts collect by their own UPI and Milavn only records attendance. Write the decision in the guardrails register. Effort L.

**C2. Women-only is a promise the system cannot keep, and the wording says "enforced".**
- Claim: A women-only circle checks a self-declared answer. The safety QA run found a man who has joined nothing can set his answer to "woman" and enter. Inviting a man to a women-only circle is accepted and fails only when he accepts. A misuse report stays open with no status route.
- Evidence: QA-RUN-safety (#23). On the real screen: "यात्रा · केवल महिलाओं के लिए" and "यह समूह केवल महिलाओं के लिए है" on a circle that plans a 3-day yatra to Srisailam with strangers. A Meetup review dated 1 Oct 2026: "To put this behind a paywall is excluding women, and exploiting their need for safety" ([Trustpilot](https://www.trustpilot.com/review/meetup.com)). Women in South Asia often share phones and have little privacy ([Sambasivan et al., SOUPS 2018](https://www.usenix.org/conference/soups2018/presentation/sambasivan)).
- Why it matters: Overnight women's trips are the highest-stakes thing in the module. One incident ends trust in the whole app.
- Recommendation: Stop saying "enforced". For women-only circles require approval by a woman steward, a vouch from a Samaj woman head for new hosts, and a visible "approved by a steward" line. Refuse men at invite time. Add organiser verification before any overnight trip. Effort M.

**C3. The security step was never run, yet money, uploads and chat shipped.**
- Claim: `AgentOutputs/09a-external-dependencies.md` says Step 8 (STRIDE) has "not run" and keeps SEC-BLOCKER-01 open, every dependency "Pending". Since then tickets, QR, file uploads, WebSocket chat and a public page were added.
- Evidence: 09a file (2026-09-13, status In Progress). QA found 500 errors from a missing DELETE grant and an unapplied migration 055 (QA-RUN-safety). On the live page the browser fetches tiles straight from `tile.openstreetmap.org`, and 09a lists `api.qrserver.com` (leaks the share URL) as to-replace.
- Recommendation: Run the Step 8 gate on the current code, especially ticketing, uploads, WebSocket auth and the QR/ticket endpoints. Apply migration 055 and list owner-only database changes. Effort M.

### High

**H1. Anyone who taps "Interested" can message every other attendee.**
- Evidence: `milavn_connect.can_message` (migration 015-chat.sql) allows a direct message when two people share an activity with status going, interested, checked in or attended, with no accept step. "Interested" is a one-tap state on a public event. "Active now" presence is shown. QA-RUN-safety adds that interested and waitlisted people can read and write the event chat.
- Why it matters: This is the usual route for unwanted messages to women.
- Recommendation: First contact becomes a request the receiver accepts; women can limit DMs to "people I have accepted" or "circle admins"; Interested alone never unlocks chat; presence off by default. Effort M.

**H2. Cold start: the product is built for dense Meetup cities, the community is thin.**
- Evidence: A Mumbai member (Bandra West) opens Home to "यह हफ़्ता शांत है" and the feed says "अभी शांति है"; the UI review found the same in Hyderabad. Groups survive only when new people keep arriving ([Liu & Suel 2016](https://research.engineering.nyu.edu/~suel/papers/group.pdf), cited in the module's research file). Discovery shows only the viewer's own city (QA-RUN-fun, note 6).
- Why it matters: Khatri families per city are few. A long tail of member-made badminton games will look empty and members will leave after one visit.
- Recommendation: Launch with a Samaj-curated calendar (festivals, jayanti, satsang, welfare camps) entered by Samaj heads, with member-made events secondary. Show "nearest city with events" when the home city is quiet. Effort M.

**H3. Large events: no host verification or public-assembly guidance.**
- Evidence: The create form (on screen) defaults to "कोई सीमा नहीं" (no capacity limit) and lets any member add tickets. The Bengaluru crush of 4 June 2025 killed 11 and injured 56; the state "admitted that the event was conducted without any standard operating procedure" ([Wikipedia summary](https://en.wikipedia.org/wiki/2025_Bengaluru_crowd_crush)). Hyderabad had a fatal premiere crush on 4 December 2024 ([Wikipedia](https://en.wikipedia.org/wiki/Pushpa_2:_The_Rule)). Telangana police-permission, fire and venue rules: unverified.
- Recommendation: Size tiers. Above a set headcount (for example 100) require a venue and permission checklist and Samaj-head approval; cap default capacity; show who is accountable on every public event. Effort M.

**H4. The place search sits on a service whose policy forbids that use.**
- Evidence: The shared utility defaults to `https://nominatim.openstreetmap.org` with search-as-you-type. The OSMF policy: "Auto-complete search … you must not implement such a service on the client side", "an absolute maximum of 1 request per second", and applications whose primary function is geocoding must run their own service ([policy](https://operations.osmfoundation.org/policies/nominatim/)). Tiles are "best-effort" with no SLA and can be blocked without notice ([tile policy](https://operations.osmfoundation.org/policies/tiles/)). QA found Jaipur localities missing and the venue pin falling back to "the middle of the city" while the screen says "where to reach".
- Recommendation: Self-host Nominatim/Photon or buy a commercial India provider before launch; label an approximate pin as approximate. Effort M.

**H5. Photos, chat and location under the DPDP Act.**
- Evidence: Phased commencement began 13 November 2025, penalties up to Rs 250 crore, special rules for under-18s ([Wikipedia summary](https://en.wikipedia.org/wiki/Digital_Personal_Data_Protection_Act,_2023); check the dates in the official Rules). Albums and "Moments" hold photos of identifiable people, including children at family events. The module's own research file says the parent-approval rule is "a sharer's confirmation, not a verified parent".
- Recommendation: Photos circle-only by default; ask before showing a tagged person or child; a visible grievance contact; a breach plan. Effort M.

**H6. Moderation depends on volunteers and lacks tools for the real risks.**
- Evidence: One moderator persona; the open women-only misuse report has no status route; a declined applicant can re-apply at once (QA professional). Indian group admins report elders dominate: "the elderly admin argued that non-blood relatives should not send too many messages" ([WhatsApp admins study, arXiv 2401.08091](https://arxiv.org/html/2401.08091v2)).
- Recommendation: Written response times, a named Samaj safety lead (preferably a woman), report status visible to the reporter, a cool-off for declined applicants, and the grievance-officer route required by the IT Rules (timelines unverified). Effort M.

**H7. Language and terminology are still uneven, against the owner's own rules.**
- Evidence (screen, Hindi): a circle is called "सर्कल", "समूह" and "मंडली" on one page. The bell shows "Meera Kulkarni would like to join QA Women yatra Srisailam" in English inside a Hindi app. Interests ("Dance", "Street food walks") and times ("6:30 pm") stay Latin. QA-RUN-safety lists many older notices as hard-coded English, and notices frozen in the language at send time.
- Recommendation: One glossary term per concept in all three languages, signed off by native reviewers; store notices as keys plus data and render at read time. Effort M.

### Medium

**M1. The people the research cares most about are not who the app speaks to.** The WHO commission (30 June 2025) says about 100 deaths an hour are linked to loneliness and 1 in 3 older adults is isolated ([WHO](https://www.who.int/news/item/30-06-2025-social-connection-linked-to-improved-heath-and-reduced-risk-of-early-death)). Seed content is badminton, startups and coffee. Recommendation: elder and homemaker tracks (daytime satsang, bhajan, walks, "bring an elder"), phone-assisted sign-up by a Samaj volunteer, large type. Effort M.

**M2. The create form is long for a first-time host.** On a phone the Hindi create screen is about 2,000 px tall: nine category tiles, a type dropdown, date strip, time chips, place, address, arrival help, capacity, entry, guest rules, "who is it for", "more options", and a Create button that stays disabled until filled. Recommendation: three questions first (what, when, where), everything else after. Effort S.

**M3. The "expressions" camera feature has little value and weak science.** The code classifies face blendshapes into a mood word. A 2019 review found facial movements "not universally diagnostic of emotional states" and questioned tech firms "trying to figure out how to 'read emotions'" ([Barrett et al., 2019](https://www.psychologicalscience.org/publications/emotional-expressions-reconsidered-challenges-to-inferring-emotion-from-human-facial-movements.html)). The EU AI Act bans emotion inference in workplaces and schools from 2 February 2025 ([Art. 5](https://artificialintelligenceact.eu/article/5/)); not binding here, but a signal. On-device processing helps, but "camera on in a chat" worries women on shared phones. Recommendation: remove it, keep the manual mood row. Effort S.

**M4. Business model gap.** Free by default is right, but nothing funds hosting, moderation or the Welfare Trust. Luma charges 5% on paid events on its free plan and 0% on Plus ([Luma](https://help.luma.com/p/luma-plus)); Eventbrite adds fees to the buyer by default. Meetup's RSVP-fee test angered users ("he would attend events without paying", [Bernoff](https://bernoff.com/?p=9344)), and a small group closed in December 2024 over cost ([NJHN](https://njhn.org/?p=4361)). Recommendation: one published fee, only on paid tickets, routed to the Trust. Effort S.

**M5. Competing with WhatsApp rather than working with it.** WhatsApp now has Events with RSVP and automatic reminders in groups ([WhatsApp blog](https://blog.whatsapp.com/new-to-communities-events-and-replies-in-announcement-groups), date unverified). Samaj groups already live there. Milavn's edge is private venue, ticketing, safety and a calendar. Recommendation: one tap to post any event to the Samaj WhatsApp group, with RSVPs coming back. Effort M.

**M6. Matchmaking leakage.** Mangalya and Milavn share the same families, so events for singles will turn into rishta-hunting. The research file already bans "people you may like"; add an explicit rule and report reason against marriage solicitation at general events. Effort S.

**M7. Test data is visible to real members.** Kavita's circle strip shows "QA Adyar satsang", "QA Nagpur temple circle B", "QA Women yatra Srisailam" and more. QA could not delete events, a report or notifications (cleanup denied; migration 055 unapplied), and the tunnel is public. Recommendation: a separate clean demo tenant and owner-run cleanup scripts. Effort S.

**M8. No measure of whether people actually make friends.** About 50 hours turn an acquaintance into a casual friend ([Hall 2019](https://journals.sagepub.com/doi/10.1177/0265407518761225), from the module research). The "no counts" rule also removes host insight. Recommendation: private, aggregate-only measures such as repeat attendance, first-timers who return and mutual "meet again". Effort M.

## 3. New in the world

- Meetup Connections: mutual opt-in after events, no follower counts, within 24 hours ([Meetup](https://www.meetup.com/blog/connections-meetups-powerful-new-friendship-tech/)); Milavn already matches the idea. Meetup's 2025 report claims a 20% RSVP lift from an Explore redesign and 10% more clicks from semantic search ([Meetup](https://www.meetup.com/blog/2025-meetup-progress-report/)).
- WhatsApp Events inside groups (link in M5).
- WHO Commission on Social Connection (30 June 2025): global Social Connection Index, loneliness as a public-health priority (link in M1).
- RBI Payment Aggregator Directions 2025 (link in C1): the new rulebook for ticket money.
- DPDP phased commencement from 13 November 2025 (link in H5).
- Women-safety information becoming a paid or hidden feature at competitors (Meetup review in C2): free, steward-backed safety could be Milavn's edge.
- Luma-style host tools: free plan with a small fee on paid events (link in M4).
- Not opened, so unverified: Bumble BFF's move to Geneva and Timeleft's six-person tables, as cited in the module's research file.

## 4. Rethink

1. **Open meetup network or Samaj calendar?** For open: Khatri families trust each other, so bonding is the point. Against: Putnam's bonding versus bridging split ([Bowling Alone summary](https://en.wikipedia.org/wiki/Bowling_Alone)) warns closed circles drift inward, and which Khatri tradition Milavn serves (SSK or Punjabi) is still unconfirmed in the research file.
2. **"Free by default, no counts, no ratings".** For: deposits and shaming push people away (Halpern 2015, in the module research). Against: hosts need numbers to improve and women need to know a host's record; consider steward-only views.
3. **A self-declared woman/man answer.** For: dignity, no ID burden. Against: unenforceable, binary, and Indian law is moving (the 2014 NALSA ruling gave self-perceived identity; Wikipedia reports a 2026 amendment, [Transgender Act page](https://en.wikipedia.org/wiki/Transgender_Persons_(Protection_of_Rights)_Act,_2019), unverified).
4. **Anyone can host.** For: grassroots energy. Against: public-assembly liability and money rules (C1, H3).
5. **Chat inside the app.** For: keeps people from sharing phone numbers. Against: you now run a messaging service (abuse, moderation, DPDP).

## 5. Do not change

- Exact venue only after a confirmed spot, join link only near start; tested on about 30 endpoints with no leak (QA-RUN-safety #21).
- Kind reminders and "we held your spot" instead of deposits or streaks.
- Mutual "would meet again", private thanks, no public ratings.
- No paywall on messages or member lists.
- Approval and join questions on circles; announcements limited to organisers.
- Grouped notifications ("5 new posts") and per-circle settings.
- Honest "why this" explanations and the fair start for new hosts.
- The calm visual direction: serif titles, one warm accent.

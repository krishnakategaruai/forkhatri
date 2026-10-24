# Milavn event page: what we learned, and what to build

Written 2026-10-06 after the owner called the event page `/a/occ-66a7a8db99c2` "too senseless". Learning and proposal only. No app code was changed.

Mockup: `AgentOutputs/onboarding-mockups/event-page.html`. It shows three states: deciding, going on the day, and the organiser.

## How this was checked

- **Event:** "Evening badminton doubles". Asha Reddy hosts it in Madhapur, Mon 14 Sep 2026 at 6:30 pm, 4 spots, free. It had already ended when the owner opened it.
- **Viewers:** I opened the same event in four roles, using the Milavn browser in its own contexts, at 390 px and at 1280 px:
  1. Signed out, over the tunnel and on localhost.
  2. QA member Priya Nair (+919800020005), who has never joined.
  3. Vikram Rao, who is checked in.
  4. Asha, the organiser.
- **Seeing it "before the start":** the database has no upcoming in-person events. The only future event is a QA online stream. So the browser's clock was moved back inside my session only, which makes the page draw itself as it looked before the start. The server was not changed and nothing was booked, paid or posted.
- **Paid event:** I also opened `occ-109ff9bed0a0` (Sunday badminton, ₹250) in the same way.
- **Languages:** Hindi and Telugu were shown in the browser only. Nobody's account language was changed.
- **Screenshots:** in the session scratchpad, folder `evt/`:
  - s01: signed out
  - s02 and s03: ended event, member
  - s04 and s05: deciding
  - s06 and s07: share sheet and More sheet
  - s08 and s09: Hindi and Telugu
  - s10: desktop
  - s11: organiser
  - s12 and s13: checked-in attendee
  - s14 and s15: paid event
  - m01 and m02: the mockup
- **Interruption:** halfway through, another session was adding Marathi and Kannada and broke the Milavn build for a few minutes ("Can't resolve '@/locales/kn/common.json'"). I waited for it to recover.

## 1. What is senseless today

These are things seen on screen, most serious first.

1. **A WhatsApp link shows nothing to a visitor who is not signed in (s01).**
   - The page is a grey loading skeleton that never finishes. The link preview has no title or picture, only "Milavn". This happens on both the tunnel and localhost.
   - Cause: `app/a/[slug]/page.tsx` fetches the public event on the server using `NEXT_PUBLIC_API_BASE`. `.env.local` sets that to the relative path `/tunnel-proxy/api`, and a server cannot fetch a relative path. So no initial data arrives, and the signed-in fetch never runs for a guest.
   - Sharing is how events spread, so this is the most serious problem on the page.

2. **The map draws on top of the action bar and on top of every bottom sheet.**
   - Paid event (s14): on the first screen, the map covers the "Join · ₹250" button.
   - Share sheet (s06): the map hides the title, "Share…", "Poster for WhatsApp status", **WhatsApp** and SMS. Only Email, "Instagram (copy)" and Copy link can be seen.
   - More sheet (s07): the map hides "Not interested".
   - Taps still reach the hidden buttons, but people cannot see them. The map's layers sit above the sheet and the bar.

3. **The organiser sees her own event as if she were a stranger (s11).** Asha's own event shows her:
   - "Interested" and "Going" buttons.
   - "Why this: 2 people from your circles are going".
   - "The full address is shown once you are going."
   - "Who's going is private — only the organizer sees the list.", but no list anywhere on the page.
   - Nothing tells her that she never added the exact place.

4. **A checked-in attendee is told "The full address is shown once you are going." (s13).** The organiser never added a venue. Instead of saying so, the page tells a confirmed person to do something they have already done.

5. **The privacy line contradicts the block right under it.** "Who's going is private — only the organizer sees the list" is followed by "From your circles: Priya Sharma going" (s11, s12). On the ended page, "2 went" sits next to "Who went is private" (s02).

6. **The facts a person needs to decide are missing or buried (s04, s05).**
   - No end time. The calendar file quietly adds 2 hours.
   - A free event never says "Free".
   - Level, indoor or outdoor, and what to bring are missing. "Bring your racquet" is the last line of the page.
   - On the paid event, the playing hours ("7 to 9 am") and what the ₹250 covers appear only in the About text at the bottom.

7. **The host's update on the day is at the very bottom (s11, s12).** "Gate B is open from 6.15" is the most urgent thing on the page that evening. It sits below the chat thread and the photo box.

8. **The same facts are shown more than once.**
   - "Play" appears twice: on the photo and under the date.
   - The date appears twice on a phone (date tile and sentence) and three times on desktop (s10).
   - The price appears three times on one screen: "₹250 per person", "You pay ₹250", "Join · ₹250" (s14).
   - The ForKhatri badge appears twice: in "Why this" and in the organiser card.
   - On desktop, the organiser, place, going count and "Add to calendar" are each shown twice.

9. **The cover photo is misleading (s02, s14).** A neighbourhood game shows a stock photo of an international youth tournament ("LIMA BRAZIL", Youth Olympic boards). Every badminton event uses the same photo.

10. **An ended event still behaves as if it were upcoming (s02).**
    - Nothing at the top says it is over; "This activity has ended" appears only in the bottom bar.
    - "Add to calendar" is still offered.
    - There is no "next date" and no "more from Asha", so the page is a dead end.

11. **"Why this" is a feed idea shown on the detail page (s04).** "Why this: ForKhatri Verified organizer" reads like a system note. The Telugu version is not grammatical: "ForKhatri ధృవీకరించింది నిర్వాహకులు" should be "ForKhatri ధృవీకరించిన నిర్వాహకులు".

12. **Words people would not use:**
    - "Identity verified · Reliable attendee · Community contributor" describes the organiser. "Reliable attendee" is about attending, not hosting.
    - "Same locality".
    - "Moments".
    - "Organizer tools".
    - "Plan together" is the in-page thread. There is also an "Updates from the organizer" block and a separate group chat in Chats, so the same group has three channels.
    - "Share…" and "Instagram (copy)" are hard-coded in English.

13. **"Interested" and "Going" have equal weight (s04).**
    - Two same-sized buttons split the one decision the page exists for.
    - Per the critique (H1), "Interested" also unlocks messaging with attendees.

14. **The map is a "Get directions" link to a Google search for "Madhapur" (s04 snapshot).** It gives directions to a whole neighbourhood. The pin inside a circle also looks exact when the place is only approximate.

15. **Language (s08, s09):**
    - Hindi shows the time as "6:30 pm" and the place names in Latin letters.
    - The Hindi Going button reads "जा रहा/रही हूँ", with a slash.
    - Telugu has the "Why this" error from item 11 and the loan word "ప్రైవేట్".
    - Nothing was clipped at 390 px.

16. **Tap targets:**
    - "Add to calendar" is 106×18 px.
    - The badge explainer is 26 px high.
    - The organiser name link is 24 px high.
    - All are below 44 px.

17. **Paid event (s14):**
    - "Have a discount code?" appears on a ₹250 court-sharing game even when the host made no codes.
    - The refund rule appears twice: in the price box and in the About text.

## 2. Four people, four moments

| Person | What they need from the page | What they get today |
|---|---|---|
| Visitor from WhatsApp, signed out | The event at a glance, and one button to join | A grey skeleton. A blank link preview (s01) |
| Member deciding | What, when (start and end), where (area), who hosts, who's going, price, what to bring, one Join button | Date and category twice, no end time, no "Free", "Why this", a privacy notice, what to bring last, two equal buttons (s04) |
| Attendee on the day | "You're going, starts in 2 h", the host's latest note, exact place with directions, the group chat | "Checked in", the "address after going" note, chat and photos before the host's update, no directions (s13) |
| Organiser | What is missing, who is coming, sending an update, managing | Join buttons on her own event, "Why this", no guest list, "Organizer tools" last (s11) |

## 3. What other products do (research)

"Verified" means I opened the source. "Search summary" means I saw only a search result, so treat it as unverified.

| Topic | Evidence |
|---|---|
| Exact place after joining | **Luma** ("Restrict location to guests"): visitors see "the city and approximate location … but they won't see the address", and approved guests see "the full address everywhere your event appears" ([help.luma.com](https://help.luma.com/p/hiding-your-event-location), verified). **Airbnb Experiences:** the map says "Exact location provided after booking", and hosts are told to send arrival instructions a day or two ahead (search summary: [community.withairbnb.com](https://community.withairbnb.com/t5/Ask-about-your-listing/Exact-location-shown-before-booking/m-p/2147312), [airbnb resources](https://www.airbnb.at/resources/hosting-experiences/a/how-to-host-a-smooth-experience-726)). Milavn's "exact venue after Going" rule matches both. |
| Hidden things annoy people | A Partiful user's complaint: "things I'm not allowed to know until after I RSVP include a) who else is invited or going, and b) where it is", and "the only way to message the host a question … is to post it to the entire group" ([worldspiritsockpuppet](https://worldspiritsockpuppet.substack.com/p/things-i-hate-about-partiful), verified). So show the area clearly and give a private "Ask the host". |
| Friends going decide attendance | "An explicit social filtering signal accounting for whether friends are attending dominates the factors" (Georgiev, Noulas, Mascolo, ICWSM 2014, [AAAI](https://ojs.aaai.org/index.php/ICWSM/article/view/14520), verified). Partiful guests "can immediately see who else is attending" after they RSVP ([Wikipedia](https://en.wikipedia.org/wiki/Partiful) and [party.pro](https://party.pro/partiful/), search summary). Luma hosts can show or hide the guest list (search summary, [help.luma.com](https://help.luma.com/p/managing-your-guest-list)). |
| Three answers, one decision | Meetup uses Going / Maybe / Can't go ([help.meetup.com](https://help.meetup.com/hc/en-us/articles/9389668230541), search summary; the page returned 403). Facebook replaced "Maybe" with "Interested" ([wersm](https://wersm.com/?p=28174), search summary). A local paper's view: "Facebook events don't mean much" ([vindy.com](https://www.vindy.com/life/lifestyles/2019/09/facebook-events-dont-mean-much/), not opened). A soft "Interested" inflates numbers and does not commit anyone. |
| "Good to know" block | Eventbrite's "Good to know" highlights show duration, format and refund policy, plus "ages 21+" when it applies ([eventbrite.co.uk example](https://www.eventbrite.co.uk/e/1994019722668), search summary). Airbnb Experiences has "What guests should bring", guest requirements and an itinerary ([airbnb.co.in best practices](https://www.airbnb.co.in/e/experiences-best-practices), search summary). |
| Fewer steps before paying | Eventbrite moved optional questions to after checkout, and "conversion rates surged by up to 2x" (Eventbrite blog, 25 Aug 2023, [eventbrite.com](https://www.eventbrite.com/blog/?p=408436), verified). The same applies to sign-in before Join. |
| Host updates and chat | Partiful's "Text Blast" lets hosts "message everyone who's confirmed … door codes, announce delays" ([party.pro](https://party.pro/?p=5609), search summary). WhatsApp Events: "Anyone can make an event in a group, and people can RSVP … attendees will get reminders" ([campaignme](https://campaignme.com/whatsapp-rolls-out-event-planning-feature-for-communities/), search summary). Updates are first-class and close to the top, not buried. |
| Sticky action | NN/g: persistent headers make key actions easier to reach, but done badly they "obstruct page content" ([nngroup.com](https://www.nngroup.com/articles/sticky-headers/), search summary). Sticky add-to-cart lift figures attributed to Baymard appear only on third-party blogs, so they are unverified and I did not use them. |
| Link preview | WhatsApp previews need `og:title`, `og:description` and an `og:image` that is under 600 KB, at least 300 px wide and no wider than 4:1 ([Meta developer docs](https://developers.secure.facebook.com/docs/whatsapp/link-previews), search summary). Milavn sends none today (item 1). |
| India ticketing | District (Zomato) "never feels cluttered" and resells tickets ("Book Now, Sell Anytime") ([businesstoday](https://www.businesstoday.in/amp/technology/news/story/zomato-launches-district-app-for-dining-and-live-events-experiences-see-details-454001-2024-11-16), search summary). I found no verified source on how the BookMyShow event page is laid out. |
| Not verified | Exactly what Luma's or Partiful's page shows first on a phone. Their pages need JavaScript and I could not open one. Do not quote any claim about their layout order until someone checks it by hand. |

## 4. Section by section

| Section today (top to bottom) | Evidence | Proposed |
|---|---|---|
| Stock hero photo with a "Play" pill | s02, s14: a misleading tournament photo; "Play" repeated | The host's own photo, or a calm category illustration marked "Illustration". The category appears once, as small text above the title |
| "You're going / Checked in" pill | s13: a small pill | A full-width status strip with a countdown ("You're going · today 6:30 pm · in 2 h"). For organisers: "You're hosting" |
| Date tile plus date sentence plus category | s04: date twice, "Play" twice | One "When" row: "Sat 11 Oct, 6:30–8:30 pm · in 5 days", with "Add to calendar" in that row (44 px). Hidden after the event ends |
| Location label on its own | s04 | One "Where" row: "Madhapur, Hyderabad · indoor court · about 2 km · exact place after you join" |
| "2 going", "2 left", privacy sentence | s05, s11: contradiction | One "Who's going" row: faces from your circles plus "2 of 4 spots left". The privacy sentence is removed (see Decision D1) |
| "Why this" | s04, Telugu error | Removed from the detail page. Stays on feed cards |
| Price box, discount link, "You pay" | s14: price three times | A "Price" row: "Free" or "₹250 · full refund until Sat 7 am". The code field appears only when the host created codes. The total appears only in the button |
| "Where" map plus calendar link | s04, s06, s07, s14: map above sheets; link to the area | A small map lower on the page, labelled "Approximate area", with a dashed circle and no pin, and no directions link before joining. Once going: the exact pin plus "Directions" to that point. The map must sit below sheets and the bar |
| "The full address is shown once you are going." | s11, s13: shown to the host and to attendees | Visitors: inside the Where row. Attendees with no venue set: "Asha hasn't added the exact place yet" plus "Ask Asha". Organiser: an "Add the exact place" task |
| Co-host invite | s11 | Moves into Manage |
| "From your circles" | s11 | Merged into "Who's going" |
| Organiser card (badge, reputation) | s05 | Moves up as one line under the title: "Hosted by Asha Reddy · ✓ ForKhatri verified · hosted 6 games". Tapping it opens the host profile and an explanation of the badge. Drop "Reliable attendee" here |
| About | s05: last | Below "Good to know" |
| (missing) Good to know | not present | New: what to bring, level, indoor or outdoor, women only, age, language, accessibility. These come from the host's answers and tags (`audience_tags` and `food_tags` are shown here, once) |
| Agenda, speakers, stalls, teams | not in data, code only | Unchanged in content. Shown after About and only when present |
| "Plan together" thread | s11, s12 | One chat: a row showing the latest message and the unread count, opening the event's chat in Chats. Owner rule: messages and circles are different things, so no third channel |
| Moments | s11 | Shown during and after the event only, never before |
| Updates from the organiser | s11, s12: at the bottom | "Latest from Asha" card. While deciding: below the facts. Once going: the first block. Older updates fold away |
| Safety tips | not in data | Stays. Shown above the bar for high-risk events, and folded otherwise |
| Series stats (held / upcoming) | code | Replaced by "Next dates" chips, plus "Keep a spot for me" for regulars |
| Thanks, meet again, come again | code (ended) | The recap state: photos first, then these cards |
| "Organizer tools" button | s11: last | The organiser's bottom bar: "Send an update", Manage, Share |
| Sticky bar: Interested / Going / Share | s04 | One primary action with the price in it ("Join · Free", "Join · ₹250", "Join waitlist"), plus Save (☆) and Share icons. Once going: "Directions" plus chat, with "Can't make it" under ⋯. Organiser: Manage |
| Share sheet | s06: map covers it; English strings | WhatsApp first, then "Poster for WhatsApp status", the phone's own share, and Copy link. QR behind "Show QR code". All text translated |
| Desktop right card | s10: everything duplicated | The right card holds only the action, the price and the spots left. The facts appear once, on the left |

## 5. Proposed page (390 px)

### Deciding (member, or a visitor from a link)

```
┌──────────────────────────────────────┐
│ ‹                                 ⋯  │  host photo or illustration (~190px)
│        [court illustration]   Illus. │
├──────────────────────────────────────┤
│ 🏸 Play · Badminton  (Beginners welcome)
│ Evening badminton doubles            │  Fraunces title
│ (A) Hosted by Asha Reddy             │
│     ✓ ForKhatri verified · hosted 6  │
│──────────────────────────────────────│
│ 📅 Sat 11 Oct, 6:30–8:30 pm  Add to cal
│    in 5 days                         │
│ 📍 Madhapur, Hyderabad               │
│    indoor court · ~2 km · exact place│
│    after you join                    │
│ ₹  Free  (or ₹250 · refund till Sat) │
│ (V)(P) Vikram and Priya are going    │
│        from your circles · 2 of 4 left
├──────────── first screen ends ───────┤
│ GOOD TO KNOW  bring racquet · shoes  │
│ ABOUT         host's words           │
│ PROGRAMME     only if present        │
│ WHERE         approximate-area map   │
│ LATEST FROM ASHA  "Courts 3 and 4…"  │
│ ⓘ Safety (folded unless high-risk)   │
├──────────────────────────────────────┤
│ [   Join · Free   ]   ☆   ⤴          │  sticky, above every map layer
└──────────────────────────────────────┘
```

### Going, on the day

```
┌──────────────────────────────────────┐
│ ‹      [short hero]               ⋯  │
│ ✓ You're going · today 6:30 · in 2 h │  status strip
│ Evening badminton doubles            │
│ LATEST FROM ASHA                     │
│  "Gate B open from 6:15" · 20 min ago│
│ WHERE TO GO                          │
│  Sri Sai Arena, Courts 3–4           │
│  Road No. 2, Ayyappa Society         │
│  Arrival: Gate B, parking behind     │
│  [exact pin map]                     │
│  [ Directions ]  [ Call/Ask Asha ]   │
├──────────── first screen ends ───────┤
│ GROUP CHAT  Priya: extra racquets (2)│
│ WHO'S GOING (A)(V)(P)(You) · full    │
│ YOUR PLAN  Just me · two-wheeler  Change
│ TICKET QR  (paid events only)        │
│ GOOD TO KNOW · ABOUT · host card     │
├──────────────────────────────────────┤
│ [   Directions   ]   💬   ⋯(can't go)│
└──────────────────────────────────────┘
```

### Ended (recap)

```
│ Happened on Mon 14 Sep · 4 played    │
│ PHOTOS (moments) first               │
│ Thank Asha · Would you meet again?   │
│ NEXT DATE  Sat 21 Sep  ›  / More from Asha
│ bar: [ Join the next one ]  ⤴        │  no calendar, no plan, no Interested
```

### Organiser

```
│ ★ You're hosting · Sat 11 Oct 6:30   │
│ BEFORE SATURDAY  Add the exact place │  missing items first
│ COMING 2 of 4  Vikram · Priya (+1)   │
│ YOUR UPDATES  last update, sent to 2 │
│ GROUP CHAT                           │
│ bar: [ Send an update ] [ Manage ] ⤴ │
```

## 6. Remove, merge, move, add

- **Remove:**
  - "Why this" on the detail page.
  - The date tile.
  - The second "Play".
  - "Who's going is private…".
  - The always-on "Have a discount code?".
  - "You pay ₹X" when there is no code.
  - "Add to calendar" on ended events.
  - The RSVP buttons for organisers.
  - "Interested" as an equal button.
  - The stock tournament photo.
  - The duplicated desktop card content.
- **Merge:**
  - "From your circles" and the going count into one "Who's going" row.
  - The "Plan together" thread and the Chats group chat into one chat.
  - Price, refund rule and code into one "Price" row.
  - Badge and reputation into the host line.
- **Move:**
  - Host updates to "Latest from Asha", near the top. First block once going.
  - The organiser card up, as one host line.
  - "What to bring" into "Good to know", above About.
  - The co-host invite into Manage.
  - "Organizer tools" into the organiser's bottom bar.
- **Add:**
  - End time.
  - "Free".
  - Good to know.
  - A status strip with a countdown.
  - "Ask the host" privately.
  - "Asha hasn't added the exact place yet".
  - The organiser's "Add the exact place" task.
  - Recap state with the next date or more from the host.
  - Correct OG tags and a server-rendered page for signed-out visitors.
- **Fix (bugs, not design):**
  - The server-side API address for the public page (`app/a/[slug]/page.tsx` needs an absolute internal URL when `NEXT_PUBLIC_API_BASE` is relative).
  - The stacking of the map under sheets and the bar.
  - The Telugu "Why this" string.
  - The hard-coded "Share…" and "Instagram (copy)".
  - Tap targets under 44 px.

## 7. Decisions

The owner asked me to decide. For each open point, this is the choice and the reason. I left a point open only where it would reverse a recorded owner decision, carries legal or money risk, or is purely the owner's taste.

**D1. Who's going.**
- Signed-out visitors see the count only.
- Signed-in members see the count plus the faces and first names of people from their own circles. This is data the page already has.
- Confirmed attendees and the host see the full list: first name and photo. Any attendee can turn on "Hide me from the list".
- Why: friends going is the strongest reason people attend (Georgiev 2014), and Partiful and Luma both show guests. Keeping strangers' names hidden until you commit protects women from being looked up. It also keeps "trust-scoped" contact (milavn-social-decisions).
- Effect: this replaces the "Who's going is private" sentence, which today contradicts itself on screen.

**D2. One primary action.**
- The bar carries "Join · Free" or "Join · ₹X" (or "Join waitlist" when full).
- "Interested" becomes a small ☆ Save that only keeps the event in your list and reminds you.
- Save never opens chat or messages. Today "Interested" opens messaging with attendees (critique H1, safety).
- Why: "Interested" and "Going" split the one decision the page exists for, and Facebook's soft answer is known to mean little.

**D3. Exact place stays hidden until joining.**
- This is the owner-approved plan (Step 2), and Luma and Airbnb do the same.
- The approximate map shows an area circle with no pin and no directions link.
- If the host has not added the place, attendees see "Asha hasn't added the exact place yet · Ask Asha", and the host gets an "Add the exact place" task.

**D4. Host updates go near the top.** "Latest from Asha" sits below the facts while deciding and is the first block once you are going. Older updates fold away.

**D5. One chat.**
- The event page shows the latest message from the event's chat in Chats, plus an unread count.
- The separate in-page "Plan together" thread is retired. Its messages move to that chat during the build.
- Why: today there are three channels for the same people. The owner's standard is that messages are one thing and circles another.

**D6. Ended events become a recap.** The top says when it happened. Photos come first, then thanks and "meet again", then the next date or more from the host. No calendar, plan or join controls.

**D7. The organiser gets her own view.** No Join or Interested buttons. Missing items come first, then who's coming, then her updates. The bar holds "Send an update", Manage and Share.

**D8. Hero picture.**
- Use the host's photo when there is one.
- Otherwise use a category illustration marked "Illustration".
- Stock photos of real people or brands are not used as event covers.
- Why: a stock tournament photo misleads people about a neighbourhood game (UI review item 15).

**D9. Each fact once.**
- "When", "Where", "Price" and "Who's going" rows sit above the fold.
- "Good to know" (what to bring, level, indoor or outdoor, women only, age) sits above About.
- The end time is required when creating an event.
- On desktop, the right card holds only the action, the price and the spots left.

**D10. "Why this" leaves the detail page.** It stays on feed cards, where it explains a recommendation.

**D11. Discount codes.** Show the code field only when the host created at least one active code.

**D12. Signed-out visitors.**
- Render the full public page on the server, with OG title, description and image.
- "Join · Free" goes to the ForKhatri sign-in and comes back to the same event with the join done in one step.
- Why: this follows Eventbrite's lesson about removing steps before the commitment.

**D13. Share.**
- WhatsApp first, then "Poster for WhatsApp status", the phone's own share, and Copy link.
- QR goes behind "Show QR code".
- No English-only labels.

**D14. Wording.**
- The host line reads "Hosted by …" with "✓ ForKhatri verified · hosted N events". The reputation labels move to the host profile.
- "Same locality" becomes "in your area".
- Hindi uses neutral wording, not a slash: the button is "शामिल हों", and the state is "आप जा रहे हैं".
- The Telugu "Why this" error is fixed and Telugu avoids "ప్రైవేట్".
- Times use each language's own format.
- A native speaker reviews all of this before release (owner rule: Telugu and Hindi must be accurate and respectful).

**D15. Tap targets.** Every control on the page is at least 44 px high. That includes "Add to calendar", the badge explainer and the host link.

### Left open for the owner

- **Q1 (money and legal).** Paid events on this page show the host's refund rule and the price as they are now. Who holds the money and what refund promise ForKhatri itself makes are tied to the RBI payment-aggregator question in the critique (C1). Owner or CA to decide before paid events go live.
- **Q2 (taste).** The style of the category illustrations used when there is no host photo: line drawing (as in the mockup), or warm painted scenes.

Nothing in D1–D15 reverses a recorded owner decision. Exact venue only after Going, no follower counts, trust-scoped messaging and locality-only public locations are all kept.

## 8. Limits of this learning

- No upcoming in-person event exists in the data. Paid tiers, agenda, speakers, stalls and teams have no rows at all, so those parts were judged from code only. Seeding one rich future event, realistic and owner-approved, would let the build be checked properly.
- The "before the start" views were made by moving the browser clock. The server still treated the events as past, so some server-driven parts (photo upload allowed, "Checked in") reflect today's data.
- I did not open Luma, Partiful, Meetup or BookMyShow pages on a phone. Layout claims about them are limited to the sourced help articles above.

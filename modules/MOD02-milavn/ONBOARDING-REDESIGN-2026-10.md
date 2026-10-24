# Milavn first run: what we learned, and a proposal

2026-10-06. This is a study document, not a build. No app code was changed.
Mockups: `AgentOutputs/onboarding-mockups/milavn-first-run-proposal.html` (static HTML proposal).
Screenshots of today's screens are in the session scratchpad under `milavn-ob/`. The `p21-*` files are Padmavathi's, `s22-*` Sonal's and `r23-*` Ravi's.

## 1. How we tested

We used three brand-new ForKhatri members whom Milavn had never seen. Each was tested at 390px, signed in with a password at the hub, then tapped Milavn:

| Who | Wants | Language |
|---|---|---|
| **Padmavathi Gupta** (#21), 60, Dilsukh Nagar, Hyderabad | A women's temple trip | Telugu |
| **Sonal Deshpande** (#22), busy working woman in Baner, Pune | Something to do this weekend | English |
| **Ravi Shankar Khatri** (#23), samaj organiser in Karol Bagh, Delhi | To post a Sunday satsang quickly | Hindi |

All three finished the real onboarding.

## 2. Where Milavn is rigid in practice (what actually happened)

1. **She asked for Telugu and got English.** Padmavathi chose Telugu on the hub, and the onboarding appeared in Telugu. But step 3, "Choose your language", has **English already ticked**. She pressed the big button, and Milavn saved English and switched every screen to English.
   - Undoing it takes 3 taps (Profile → gear → తెలుగు), and she has to know the gear exists.
   - Ravi (Hindi) saw the same English default.
   - ForKhatri already knew both languages, so this step is a re-ask that can do harm.
2. **What they wanted to do is not in the list.**
   - The interests screen shows **30 chips, all in English, even in Telugu and Hindi**, with group headings like "SPORTS & PLAY".
   - There is **no spiritual, temple, satsang, bhajan or yatra** interest. Yet Milavn's own circle types include "Temple visit" and its event kinds include "सत्संग / भजन" and "यात्रा".
   - There is no "Other — add your own" and no Skip. You must pick at least one.
   - Padmavathi picked "Festivals" as the nearest thing. Ravi picked "Music, Volunteering".
3. **"You can change these any time" is not true.** Profile → Edit only *adds* interests. The server only inserts them (`update_enrichment`), so nothing picked by mistake can be removed.
4. **The app took them away from what they came for.**
   - Ravi opened `/create` to post his satsang. He was sent to onboarding, and after three screens landed on **Home, not Create**. He had to find "कुछ प्लान करें" again.
   - Sonal typed "something fun to do this weekend" into the hub. Milavn opened at `/` and her words were dropped.
5. **After three forced screens, Home was empty.**
   - Home said "It's quiet around Dilsukh Nagar right now" and "quiet around Baner".
   - Home only looks at the member's own city for the next 21 days. It never widens to nearby places or online events.
   - Its "circles" list shows only circles you are already in. A new member has none, even though the Circles tab lists Hyderabad circles (Kondapur Riders, Jubilee Hills Badminton, Ameerpet Readers).
6. **Search dead ends with a misleading message.**
   - Sonal tapped "This weekend" and got "No matches — try fewer filters", when only one filter was on.
   - Padmavathi typed "ఆడవాళ్ళతో గుడి యాత్ర" ("a temple trip with women"). It understood only "యాత్ర" (trip) and found nothing, because Ask searches events, not circles.
   - The women's Srisailam yatra she wanted was a **circle**, found only by browsing the Circles tab.
7. **"Use my location" fails silently.** When the location is denied or times out, the button just returns with no message. We could not grant location to the test browser, so this is the denial path, and in real life it is a common one.
8. **Extra taps that add nothing:**
   - Picking a place in the search sheet still needs "Continue".
   - The interests "Continue" button is about 2,000px down at 390px.
   - On the circles list, "Join" opens the circle page instead of joining.
   - After answering "I am a woman", she must tap "Ask to join" again.
9. **The organiser's join question is hidden.** On the women-only circle, the "Send request" button sat behind the floating bottom bar at 390px.
10. **Smaller issues:**
    - The Hindi finish button says "मुझे **दिखाओ**", a तुम-form. The respectful form is "दिखाइए".
    - Ravi's smart fill read "रविवार" (Sunday) as tomorrow, Wednesday 7 Oct. This is on the Create screen; we are reporting it here, not fixing it.
    - Edit profile shows the browser's raw "Choose File / No file chosen" in English.
    - Location sharing is pre-set to the most precise level ("Locality").
    - The launch splash flashed English for the Telugu member.

**Today's counts (hub tap → first useful Home):**
- **Screens:** 3 forced.
- **Required answers:** 3. Place, at least 1 interest, and language, which is pre-filled wrongly.
- **Taps:** 6 for Padmavathi, 8 for Sonal, 9 for Ravi, plus typing a place name and a long scroll. Padmavathi needed 3 more to get Telugu back.
- **Result:** in two of three cases, an empty Home.

## 3. What real users of comparable apps reward and complain about

The full source list is in §7. Anything we could not open in full is marked as such there.

- **The first action comes before the profile.**
  - Luma guests register with only name and email: "Guests don't need a Luma account".
  - Partiful RSVPs work from a link with a phone number. Users call it "effortless" and "the easiest system I've ever used".
  - Eventbrite creates the account silently from the checkout email.
  - Duolingo moved signup later and got about 20% more daily users.
  - Baymard: 18% of shoppers abandon when forced to create an account.
- **Location is detected or skippable, and easy to change.**
  - Eventbrite's location step offers "use current location" or **Skip**.
  - Luma lets you browse any city.
  - Meetup reviewers ask for a radius setting and complain about irrelevant far-away groups ("blasted with 900 other groups").
  - NN/g: ask for permission in context, and explain what happens if it is denied.
- **Interest walls cost more than they give, unless they visibly change what you see.**
  - Instagram asks for no interests and learns from what you do.
  - GroupLens (CSCW 2015): choosing *groups* took under half the time of item-by-item rating and gave recommendations users found more useful.
  - Pinterest asks for topics only because they shape the first feed. Milavn's interests only re-rank results and never fill an empty Home.
  - Meetup study: 7 of 7 users "could not discover how to customize their interests" after onboarding.
- **Screening belongs at the door of the group, not at signup.**
  - Facebook Groups membership questions are set per group and asked only when someone asks to join. Admins choose whether they are required.
  - Luma host questions work the same way.
  - So Milavn's GenderAsk placement is right.
- **Forced photo and verification walls create anger.**
  - Bumble BFF: "selfie validation fails, and I cannot move forward in the app."
  - Instagram's photo step has a "Skip".
  - LinkedIn uses a profile-strength meter with the *next* prompt underneath, and the meter disappears when the profile is done.
- **Empty states must show status, teach, and give a direct path** (NN/g 2021).

## 4. Screen by screen: today, evidence, proposal

| # | Today (what is rigid) | What others do / research | Proposal |
|---|---|---|---|
| 1 | **Place**: required. GPS fails silently. Picking a place in the sheet still needs Continue. No "I only know my city" path. | Eventbrite: current location or Skip. Luma: browse by city. NN/g: explain denial. | **Keep it as the only first-run screen** (mockup A, A2). Type straight into the screen, with no sheet. Tap a city chip for "city only". Picking goes straight on. After GPS, ask "Are you near Dilsukh Nagar?" with Yes / Choose another. Explain a denial in one line. Optional: "Choose later" (owner decision Q1). |
| 2 | **Interests**: 30 English chips, at least 1 required, no spiritual or devotional option, no Other, no Skip. Can't remove later. | GroupLens groups; Instagram learns from behaviour; Meetup's "can't edit" complaint; Pinterest only when it changes the feed. | **Remove from first run.** Show it as an optional Home card later (mockup C): 9 picture tiles in the member's language, Spiritual & temple included, "Other — add your own", Skip. Learn from Going, Join and searches. Interests can be added *and* removed on Profile. Needs owner decision Q2, because FR001 needs at least 1 interest today. |
| 3 | **Language**: English pre-ticked. It overrides the ForKhatri choice and silently flips Telugu or Hindi members to English. | No compared app re-asks the language at signup (they use the account or device language; not verified per app). Our own never-reask rule. | **Delete the step.** Use the ForKhatri language. Keep the switch in Settings. |
| 4 | **First Home**: "It's quiet around …". Only your city, 21 days. Circles = only yours. | NN/g empty states; Luma city calendars; Meetup's "far away" complaints → label it honestly. | **Never quiet** (mockup B). Widen step by step to the city, then nearby, then online, each labelled. Show "Groups near you" (open circles in the city). Offer "Start one in a minute" templates (Satsang, Walk, Chai meet). |
| 5 | **Ask/Search**: "No matches — try fewer filters" with one filter. Ask ignores circles. | NN/g: honest status plus a next step. | Say what was searched ("Nothing this weekend in Baner"). Show circles and nearby matches in the same results. Offer "Tell me when something like this is posted". |
| 6 | **Women-only circle**: the just-in-time question is good. After answering, "Ask to join" is a second tap. "Send request" is hidden behind the nav. "Join" on the list only opens the page. | Facebook Groups and Luma ask at the moment of joining. | **Keep GenderAsk as it is.** After the answer, go straight on with the join. Put the organiser's question and Send in one sheet above the nav, with quick-answer chips and voice (mockup E). |
| 7 | **Profile**: empty avatar, no nudge. Raw file input. Interests can only be added. "Location: Locality" is pre-set. | LinkedIn meter plus next prompt; Instagram "Skip" on photo; Bumble's forced photo gets complaints. | A **"Your profile is 40% done" card with one next question** (photo → a line about you → interests). Each can be skipped, and the card hides at 100% (mockup D). Proper photo buttons (camera or gallery). Interest chips with ✕. Owner decision Q4 on the default location-sharing level. |
| 8 | **Deep links and intent**: `/create`, a shared circle link, or the hub's typed request are lost after onboarding. | Luma and Partiful: the link *is* the onboarding. | Remember where the person was going. After the place step, return them there. Pass the hub request on as the Ask query. |
| 9 | **Organiser first run**: three onboarding screens before Create, and smart fill got the day wrong. | Luma: "quick and simple: title, date, location, description". Partiful: phone plus details. | Organisers go place → Create directly. The place they pick for the event can also become their home place if they have none (owner decision Q3). Fix the "रविवार" date bug separately. |

## 5. The proposed new flow (summary)

1. Hub → Milavn. **One screen: "Where should we look?"** (GPS-confirm, a city chip, or typed search). Then Milavn goes straight to whatever the person came for: Home, a shared link, Create, or the hub request.
2. **Home is never empty**, and it offers ready-made templates for starting something.
3. **Asked later, only when it matters:**
   - The woman/man answer, when joining a women-only group (unchanged).
   - Organiser questions, at join.
   - Interests, as an optional Home card, or when a search finds nothing.
   - Photo and a line about you, from the profile card, or before the first hosted event: "Add a photo so guests recognise you".
4. **Prefilled from ForKhatri:** name and language. The place cannot be prefilled, because platform identity holds no place (owner rule).
5. **Still required:** a place, because Milavn is local-first, the server needs `locality_city`, and only the locality is kept, never an address. The gender question stays tied to women-only groups (migration 050).

**After the change (hub tap → Home):**
- **Screens:** 1.
- **Required answers:** 1 (place).
- **Taps:** 2 (GPS + "Yes"), or 1 plus typing.
- **Language:** never wrong.
- **Organiser:** lands on Create, not Home.

## 6. Options and recommendation

- **A. Polish only.** Fix the language default, localise the chips, add Spiritual and Other, remove the extra Continue, allow removing interests, and fix the empty Home. This is quick and needs no rule change, but it keeps 3 screens.
- **B. One-screen start (recommended).** Place only, with interests moved later, plus everything in A. It needs FR001 relaxed to "place only".
- **C. No gate at all.** Browse India-wide or by city, and ask for the place at the first action (Going, Join, Create). This has the lowest friction, Luma-style. But it weakens the local-first promise and needs a server change to allow a place-less profile.

## 7. Questions for the owner

- **Q1.** May a member skip the place ("choose later") and see city-wide or online events, or is a place always required before Home? We recommend that it stays required but takes 1 tap.
- **Q2.** May we drop "at least one interest" from first run (an FR001 change) and ask for interests later as optional?
- **Q3.** For an organiser with no home place, may the event's place set their Milavn home area, if they agree?
- **Q4.** Should location sharing start at "Zone" (less precise) rather than "Locality"?
- **Q5.** Should Home show events from nearby cities and online events when the member's own area is quiet, clearly labelled?
- **Q6.** Should we add the interest group "Spiritual & temple" (Satsang, Bhajan, Yatra, Temple visit, Seva) in all three languages, with an "Other — add your own" that organisers can see?

**Sources:**
- **Luma:** [help.luma.com event-registration-process](https://help.luma.com/p/event-registration-process), [collect-registration-questions](https://help.luma.com/p/collect-registration-questions), [creating-an-event](https://help.luma.com/p/creating-an-event)
- **Partiful:** [Wikipedia: Partiful](https://en.wikipedia.org/wiki/Partiful), [App Store reviews](https://apps.apple.com/us/app/partiful-fun-party-invites/id1662982304?see-all=reviews)
- **Eventbrite:** [onboarding flow (lazyweb)](https://lazyweb.com/canvas/flows/eventbrite/social-login-and-onboarding)
- **Meetup:**
  - [App Store reviews](https://apps.apple.com/us/app/meetup-social-events-groups/id375990038?see-all=reviews)
  - [usability study (uxdesign.cc)](https://uxdesign.cc/meetup-a-usability-case-study-e909c33f1e3e), snippet only
  - [help: changing location](https://help.meetup.com/hc/en-us/articles/360025771311-Changing-your-account-location), snippet only
- **Bumble BFF:**
  - [Bumble: what is BFF](https://bumble.com/the-buzz/what-exactly-is-bumble-bff)
  - [TechCrunch 2025](https://techcrunch.com/2025/09/18/bumble-bffs-revamped-app-is-here-focusing-on-friend-groups-and-community-building)
  - [selfie complaint](https://www.sikayetvar.com/en/bumble-us/bumble-selfie-verification-fails-every-time-on-android)
- **Instagram:** [help: signup](https://help.instagram.com/iphone-app/155940534568753)
- **Facebook Groups:**
  - [membership questions](https://www.socialmediatoday.com/news/facebooks-rolling-out-group-membership-questions-to-improve-filtering-proc/502552/)
  - [Meta 2022 admin tools](https://about.fb.com/news/2022/03/new-tools-for-facebook-group-admins/)
- **LinkedIn:** [profile meter](https://www.linkedin.com/help/learning/answer/391)
- **Research:**
  - [Duolingo delayed signup (First Round)](https://review.firstround.com/the-tenets-of-a-b-testing-from-duolingos-master-growth-hacker/)
  - [Baymard checkout](https://baymard.com/blog/current-state-of-checkout-ux)
  - [GroupLens CSCW 2015](https://grouplens.org/blog/onboarding-new-users-in-recommender-systems/)
  - [Pinterest onboarding (Appcues)](https://goodux.appcues.com/blog/pinterests-value-driven-onboarding-flow)
  - [NN/g empty states 2021](https://www.nngroup.com/articles/empty-state-interface-design/)
  - [NN/g permission requests 2019](https://www.nngroup.com/articles/permission-requests/)
  - [NN/g mobile tutorials](https://www.nngroup.com/articles/mobile-tutorials/)
- **Not verified:** Reddit was blocked, and the full Bumble support pages were not reachable.

## 8. State left behind

- **#21 Padmavathi:**
  - Milavn profile: Dilsukh Nagar, Hyderabad; interest Festivals; language Telugu (we restored it after the English trap).
  - Woman/man answer: woman.
  - No join request was sent (we cancelled it).
- **#22 Sonal:** profile Baner, Pune; interests Trekking, Board games, Yoga; English.
- **#23 Ravi:**
  - Profile Karol Bagh, Delhi; interests Music, Volunteering; Hindi.
  - The Create form was filled with smart fill but **not published**.
- No other data was created.

## 9. Decisions (2026-10-06)

The owner asked us to decide what is best for the app. Decided:

- **Option B**, plus every fix in option A.
- **Q1 Place:** stays required before Home, because Milavn is local first. It must take one tap: the ForKhatri city if known, "Use my location", or a short list of nearby big cities with search for anything else. If location fails, say so and fall back to the list.
- **Q2 Interests:** removed from the first run (FR001 relaxed to "place only"). Asked later as optional chips, after the member has seen Home once, and editable and removable any time.
- **Q3 Organiser's place:** yes, the event's place may become the organiser's home area, but only after they confirm it on screen. Never silently.
- **Q4 Location sharing:** starts at Zone (less precise). Members can choose Locality.
- **Q5 Quiet Home:** shows nearby-city events and online events when the member's own area is quiet, clearly labelled as such.
- **Q6 Spiritual & temple:** add the group (Satsang, Bhajan, Yatra, Temple visit, Seva) in all languages, plus "Other — add your own".
- Also: the member's language from ForKhatri is never overwritten; the member returns to what they came for (a /create or hub link); remove the extra Continue after the woman/man answer; keep Send above the bottom bar; fix "No matches" wording; the Hindi button uses the respectful आप-form; fix smart fill's day reading.

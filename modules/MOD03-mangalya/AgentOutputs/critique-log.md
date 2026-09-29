# Mangaly critique log (critique agent)

Owner brief of 2026-09-24: a full UI/UX redesign. The target is modern, elegant and GenZ-friendly, using bento grids, motion type, ambient motion, glass, scrollytelling and neumorphism where they fit, with nothing redundant. The theme is kumkum red #cc0106 and turmeric yellow #fbd946, plus a maroon dark mode. The app is mobile-first, but the desktop must be equally polished, with no wasted space. The Seeta–Rama art is for the splash and loaders only.

How screens were captured: Playwright Chromium, read-only, no data changed. Viewports were 390x844 at 2x and 1440x900, each in light and dark. Personas were asha (candidate), mangaly-parent (Lakshmi, parent of Ananya), mangaly-family (Vikram, in no circle) and new-member. Telugu (asha) and Hindi (Lakshmi) were also captured. Screenshots are in `%TEMP%/mangaly-critique/shots/`.

Round 1 was captured at 23:00–23:12 IST. The lead changed the colour tokens during the round (sindoor.css saved at 23:07), so every colour note below comes from the recapture at 23:12 (`asha_r2_*`).

Severity levels:
- **P0**: broken, misleading, or against a standing owner rule.
- **P1**: clearly below production standard.
- **P2**: polish.

---

## A. Functional: forward to the functional agent now

| # | Screen | What is wrong | Evidence |
|---|---|---|---|
| F1 | Discover (every persona) | **The same person appears on several shelves.** For asha: 5 shelves, 44 card slots, only 14 different people. Siddharth (ae75bdb0) is on 4 shelves. For Lakshmi/Ananya: 8 shelves, 50 slots, 14 people. 79f9b764 ("32 yrs · Bengaluru") is the hero pick and also appears in *Best matches*, *Would move*, *Shares Ananya's way of life* and *New this month*, so 5 times. *New this month* holds 12 of the 14 profiles, which means it is just "everyone". *Best matches* is also everyone (12). | DOM dump of `section > a[href^=/profile/]` per heading |
| F2 | Profile view (asha → Siddharth) | **The name rule contradicts itself.** The name "SIDDHARTH" is printed above the age. Right under it the page says "Name and contact are shared only after you connect", and the sealed card lists "Their name" as something that unlocks after connecting. The Discover cards also show his name. Other cards show no name ("32 yrs · Bengaluru"). Either showing a first name is the person's own choice (and it's on here), so the sealed list must not claim the name is hidden, or it isn't. The copy has to follow each person's actual setting. | `asha_r2_profile_*` |
| F3 | Profile view | The sealed card says "Their answers, in their own words" open only after connecting, yet one answer is already shown in full on the same page. The list should say "the rest of their answers", or be built from what is actually hidden. | same |
| F4 | Profile view | "Photos confirmed as **you** · Sept 2026" appears on *someone else's* profile. It should read "Photos confirmed as him / as Siddharth". | same |
| F5 | Me (asha), round 1 | At 23:00 the card read **"Seed Candidate One"** with initials "SO", while the header avatar said "AR / Asha". By 23:12 it read "Asha Reddy". Something renamed the profile or served seed data in between. Check whether a script or seed rewrote asha's `display_name`. | `asha_me_m-light.png` vs `asha_r2_me_m-dark.png` |
| F6 | Circle (Lakshmi, parent) | Lakshmi's own member row says "Parent · Joined 14 Sept 2026" and then **"Say how you are related"**. The relation is already Parent, so the prompt should not show. | `mangaly-parent_circle_m-light_full.png` |
| F7 | Circle (Lakshmi) → "Suggested to Ananya" | Lakshmi is the viewer, but it says "Suggested by **your parent**" and "no action has been taken on **your** behalf". That is Ananya's point of view. Lakshmi should read "You suggested this to Ananya". The Hindi has the same problem ("आपके माता-पिता द्वारा सुझाया गया"). The suggested person's title is "Bachelor's degree · Software Engineer", with no age and no name. | `mangaly-parent_hi_circle_m-dark_full.png` |
| F8 | Circle (asha) | The empty members card says "invite a family member **above**", but the invite form is **below** it. | `asha_r2_circle_d-light.png` |
| F9 | Me (asha) | The "Confirm your photos are you" nudge shows although asha has **0/6 photos**. Tapping it opens a page that only says "Add a photo of yourself first", which is a wasted intermediate screen. When there are no photos, the nudge should become "Add your first photo" and open the photo picker. | `asha_me_verify_*` |
| F10 | Discover empty state (Vikram, new-member) | "Tell us who you're looking for… Choose Bride or Groom" has **no control to make that choice**, so it's a dead end. It needs inline Bride/Groom chips right there. Search, Filters and tabs also sit above an empty result set. Console shows a 409 on load for both personas. | `mangaly-family_discover_m-light.png` |
| F11 | Parent Discover | *Your family's picks for Ananya* shows 1 card tagged "You suggested this" with a "Not now" badge. That same person appears again in *Would move* with "Not now" on the photo. What "Not now" means, and who said it, is not stated. | parent discover segments |
| F12 | Me (asha) | "Always shown: your main photo, age, city, education and work", but her Education & career is 0/5 and she has no photo. The preview promise doesn't match her data. That's a minor copy/data mismatch. | `seg_me_1.png` |
| F13 | Profile view (Siddharth) | The badge says "3 photos". The page shows the main photo plus 2 thumbnails, and then says "The rest of their photos" open later. So is it 3 or more? | profile |

---

## B. Discover (`/discover`)

### Mobile, light: **Not acceptable yet.** It reads like a Netflix shelf list, not the owner's photo wall.
1. **P0: wrong model. The owner asked for a photo grid (Instagram/photo-wall ref image 1), and this is 5–8 horizontal shelves.** Each shelf shows 2.1 cards, and the same faces repeat 4–5 times (F1). Fix:
   - Replace the "For you" shelves with a single 2-column masonry photo wall on the phone (3–4 columns at ≥1024px, 5 at 1440).
   - Each person appears once.
   - Tile: 3:4 photo, name + age overlaid bottom-left in 18/700 cream on a 40% scrim gradient, and one glass chip ("Hyderabad"). The verified tick sits top-left. The bookmark appears only on long-press or hover.
   - Keep at most one editorial "reason" row, and only if it adds people not already in the grid (e.g. a single hero "Most compatible today" card as the first full-width tile of the grid, per ref image 3).
   - Delete *Close to home / Would move / In their own words / New this month* as shelves. Turn them into filter chips above the grid: "Near me", "Open to relocate", "Has answers", "New".
2. **P0: the fold is 55% chrome.** Before the first photo there is the "Discover" title, then "Matches for you · looking for Groom", Search + Filters, the tab bar, the "Picked for you" heading and a 2-line subtitle. That puts the first photo at y=306 of 844 CSS px. Fix:
   - Merge the title row and search into one row: small "Discover" wordmark, search icon button, filter icon button, avatar.
   - Drop the "Matches for you · looking for Groom" line. Put "Groom" into a filter chip.
   - Make the tabs a slim segmented control of 32px height.
   - Target: first photo at y ≤ 170.
3. **P1: the text below each photo truncates everywhere.** Examples: "Siddharth, 32 · Hyd…", "You fit each other's pref…", "Cardiologist · Doctora…". Three truncated lines under a small card look unfinished. Fix: overlay name + age on the photo (ref images 2, 3 and 8). Below it, keep at most one line (profession), and never truncate the name. The "You fit each other's preferences" line is the same on every card in the shelf, so it carries no information. Delete it.
4. **P1: the "3 photos" badge is on every card** and says nothing (they all have 3). Replace it with thin story-style progress ticks at the top of the tile when there's more than one photo, or drop it.
5. **P1: cards without a name** ("32 yrs · Bengaluru") sit next to named cards. That's jarring, and it reads as a missing-data bug. When the name is hidden, start the line with a neutral handle, e.g. "Founder · 32", and style it the same way.
6. **P2: the tab bar sits on a slightly darker band** (`surface-2` strip behind "For you / All matches / Saved"), which looks like a leftover box. Remove the band.
7. **P2: lazily loaded photos show a flat cream tile** while loading. Use a blurred LQIP or a shimmering kumkum-to-gold skeleton instead.
8. **P2: the header has three identity items** in 390px ("ForKhatri" hub link with a 4-dot icon, avatar, and "Asha" under the avatar). The name under the avatar costs 20px of height. Drop the label and make the ForKhatri link an icon-only button.

### Mobile, dark: same layout issues. Colour is OK now (red active pill, gold icon, cream ink).
- **P2:** the active nav pill is kumkum red with a **gold icon and cream label**. Pick one: a gold icon with a gold label, or everything cream. The mixed version looks like a bug.
- **P2:** the "Filters" and "Search" outlines (`line-2`, #55291f) barely show on #1a0708. Raise them to ~#7a3a2a, or fill the inputs with `surface`.

### Desktop 1440, light and dark: **wasted and clipped.**
1. **P0: shelves clip the 5th card at the right edge** ("Jeweller (family busine…"). On a 1440 screen the owner expects a real grid, not a phone carousel stretched wider. Use the photo wall from item 1 with 5 columns at 1440. If one hero stays, it gets 2 columns by 2 rows as a bento tile.
2. **P1: the search field is 960px wide** with a tiny "Filters" button beside it. Cap search at 480px. Show the filter chips inline on the same row (Age, City, Community, Diet, Verified), because desktop has the room. Don't hide them in a sheet.
3. **P1: the sidebar** is a floating card that ends at 887px with a large empty middle. Also, the new logo tile (the Seeta–Rama art squeezed into 36px) is an unreadable blob of colour. Put the mangalyam mark (app/icon.svg) back in the sidebar. The owner said the Seeta–Rama art is for the splash and loaders **only**.
4. **P2:** the round-1 dark desktop showed the active nav as a red pill, but Messages and Circle showed a gold pill. The r2 capture is consistently red. Keep it consistent.

---

## C. Profile view (`/profile/[id]`, asha viewing Siddharth)

### Mobile, light and dark: **Below the reference bar.** Nothing in it is immersive, and elements collide.
1. **P0: text collision.** The sticky "Send a request" bar and the glass nav stack sit over the prompt card's 36px quote text. "I'm a cardiologist, so I'll sometimes leave" shows straight through the nav glass (both themes, and it's worse in Telugu, where the verify line is overprinted). Fix, in this order:
   - (a) On `/profile/*`, hide the bottom nav, as Hinge, Bumble and Instagram do on a profile. Show a back arrow and one floating action bar only.
   - (b) Give the action bar an opaque `surface` background with a 16px top fade. Do not use a bare button.
   - (c) Add bottom padding equal to the bar height + safe area.
2. **P0: not the owner's reference.** The refs are full-bleed portrait photos with a huge name + age overlaid and glass chips (refs 2, 3, 8 and 9 "Jane Cooper / Yasmin Cardoso"). The build has a boxed 320px photo, a page title "Profile" (redundant) and the name set tiny in a red overline above the age. Fix:
   - Photo full-bleed at 100vw × ~70vh, with a floating glass back button and a ⋯ button.
   - Story-style progress ticks for the 3 photos, with tap left/right to move between them.
   - Overlaid bottom-left: "Siddharth, 32" in 44/800 display type, then 📍 Hyderabad.
   - A row of glass chips (Doctorate · Cardiologist · Verified).
   - Delete the "Profile" page title.
   - Scrolling (scrollytelling) reveals the prompt card, the photo pair and the sealed card.
3. **P1: the verify card has an empty top strip.** There's a 30px band with a hairline above "Photos confirmed…", which looks like an unrendered header. Reduce it to one inline glass chip under the name ("✓ Photo-verified · Sep 2026"). A whole card is not needed for one line.
4. **P1: the prompt card on mobile hides its question.** Only the red ❝ shows, then the answer. The label "WHAT MY WORK ACTUALLY MEANS TO ME" is visible on desktop but covered on mobile. Put the question above the answer in 13/600 caps on both, and set the answer at 24px, not 36px. At 36px the answer takes 6 lines and dominates the page.
5. **P1: the photo pair leaves a gap on the right** (2 × 155px thumbnails inside a 330px column, left-aligned). Make it a 2-up grid filling the full width, or one tile per photo with the first one full width.
6. **P2:** "32 yrs · Hyderabad, Telangana" wraps to 2 lines (3 in Telugu). Drop ", Telangana". The state adds nothing for a same-state viewer.
7. **P2:** the sealed card's dashed pink border and pink fill in light mode is a third accent (neither kumkum nor turmeric). Use a gold-tint fill with a solid 1px `line-2` border and a small lock glyph.

### Desktop 1440: **the main button is out of view.**
1. **P0: "Send a request" is at y=1170, below the 900px fold.** The owner rule is that primary choices are visible without scrolling. Fix: a two-column layout with a sticky left photo column (position: sticky; top: 24px) and the action bar placed under the name block at the top of the right column, or a sticky footer inside the right column.
2. **P1: below the 520px photo the left column is empty for 600px.** Make the photo column sticky and show all photos stacked or as a carousel there.
3. **P2:** the title "Profile" + back arrow at 40px is heavier than the person's name (26px). Invert that.

---

## D. Messages (`/messages`) — no persona had a conversation, so no thread could be critiqued

### Mobile, light and dark: **Empty state is weak; two buttons do the same job.**
1. **P1: two compose controls**: a red round pencil FAB in the header *and* a "New message" button in the empty state. Keep one. For an empty inbox, keep the in-body button and hide the header pencil until there is at least one thread.
2. **P1: the empty state is bare, left-aligned text with 1100px of empty page under it.** Production chat lists (ref 5, "Chats") lead with a story-avatar row of people you can message. Fix: show the row of Home Circle members and connected families as 64px story avatars (with a gold ring for unread or active), and a centred empty illustration (a turmeric thread / two kalash) with one line of copy. If there are no circle members and no connections, the button should say "Invite family to your circle" and link to /circle. "New message" to nobody is a dead end.
3. **P2:** "Write to someone in your family, or to the family of a match you are connected with." This contradicts the 2026-09-22 chat model: ordinary 1-to-1 chat is between *people*, candidate-to-candidate chat is incognito, and the family group chat is optional. Rewrite it as "Chat one-to-one with family and with the people you're connected to."

### Desktop 1440 dark:
1. **P1: the page header is squeezed into the 360px list pane.** "Messages", the pencil, "ForKhatri" and the avatar are crammed together, with the avatar label "Asha" in 10px. The sidebar already has the ForKhatri link, so it appears twice. Move the account and hub controls to a global top-right slot that is the same on every screen, as Discover and Circle already have.
2. **P2:** the right pane's "Your messages / Choose a conversation" placeholder is fine. Pull it up so it doesn't float in 600px of emptiness with an icon only 50px wide. The list pane and the reading pane use the same `surface`, so no separation is visible. Give the list pane `surface-2`.

---

## E. Circle (`/circle`)

### asha (candidate), mobile light: **Structure OK, but a long form dominates the screen.**
1. **P1: the relation picker is a wall of 16 chips over ~900px.** Show the 5 Home chips (Mother, Father, Brother, Sister, Guardian) plus one "More relatives ▾" chip that expands in place. Keep it in place; no sheet (owner: no intermediate screens).
2. **P1: the members card for an empty circle** uses a 180px house illustration and copy pointing "above". Merge "Members (0)" into the invite card's heading, e.g. "Your Home Circle is empty — add Mother or Father first", and remove the separate card.
3. **P1: "Add to my circle / Join someone's circle" segmented control.** For a candidate with an empty circle, "Join someone's circle" is the rare path. Make it a text link under the form ("Were you invited? Join a circle"). Don't give it a 50/50 split.
4. **P2:** the disabled "Send invitation" is a washed-out salmon (#e87c7c) in light mode and was muddy olive in dark round 1. Keep disabled buttons as `surface-3` fill with `ink-3` text. Never use a desaturated accent.

### Lakshmi (parent), mobile: **Header broken.**
1. **P0: horizontal page overflow.** The "Viewing Ananya's …" chip pushes the header actions off-screen. `document.scrollWidth` is 426px on Discover and 395px on Circle at a 390px viewport, and the avatar is cut off on the right ("La…"). The chip is also cyan text on teal fill (`--family` #0e6a82 / #5cc6dd), which is a leftover of the old palette. In dark mode it looks exactly like selected text. Fix:
   - Move the context to its own row under the title, as a gold-tint chip: "For Ananya ▾" (a dropdown when the person has several candidates).
   - Title row: title, then the icon buttons.
   - Also drop the duplicate "Matches for Ananya" line on Discover, because the chip already says it.
2. **P1: the "Home Circle" title wraps to 2 lines** at 32px (and in Hindi, "होम सर्कल"). Cut the title size to 26px on a phone, or call the tab just "Circle" to match the nav label.
3. **P1: the Ananya header card** uses a teal "AR" initials avatar, but the Me → "Your families" row shows Ananya's real photo. Use the photo everywhere.
4. **P2:** "1 person helping" plus a members list of 1 (Lakshmi herself). If the only helper is you, drop the count chip.

### Desktop 1440: **one stretched column.**
1. **P1:** every card is 1060px wide, the name/phone input is 1030px wide and the button is 1030px wide. Use a bento layout:
   - left 5/12: Members (as person tiles with photo, relation and role)
   - right 7/12: the Invite card (input capped at 480px, button auto-width)
   - below: Requests sent / Suggested as tiles in a 2-column grid

---

## F. Me (`/me`)

### asha (candidate), mobile: **Too long (3,600px), and privacy settings come before content.**
1. **P1: order.** The order is: identity card, verify nudge, status stepper, "Shown openly" privacy block (3 toggles), "Next up Basics" row, Part 1 intro, Photos, the 8 sections, then Part 2. On a matrimony "My profile" (Shaadi, Hinge, ref 6 "My profile"), the *photos* come first, straight after the identity card. Fix:
   - Identity card with an inline completeness ring.
   - The photo bento right under it.
   - Then section tiles.
   - Move "Shown openly" into Settings (the gear is already in the header) or to the end.
2. **P1: two progress systems.** There's the Saved / Discoverable / Well-filled-in stepper with a bar, plus a red progress arc around the avatar, plus per-section counters (0/6, 2/6…). That's three ways of saying "incomplete". Keep the avatar ring and the per-section counters, and delete the stepper card. Its one useful sentence ("A few more details and you start appearing in search") can move under the name.
3. **P1: the section cards are all the same height with a 96px illustration each**, so 8 near-empty cards take about 2,000px. Use a 2-column bento of compact tiles on a phone: icon, name, "0/5", and a tap to edit in place. On desktop, use 3 columns.
4. **P1: inconsistent add buttons.** "Add 4 more details" is a solid outline, while "+ Add details" is a dashed red pill. Use one style.
5. **P2:** "Answers I published · 0 published — manage in In my words" has a doubled "in In". Change to "0 published · open In my words ›".
6. **P2:** "Next up · Basics · Takes a few seconds" points to Basics while Photos (0/6) comes first on the page and matters more. Next up should be Photos.
7. **P2:** the header has 4 controls on the profile page itself: ForKhatri, gear, the avatar and "Asha". On your own profile the avatar is redundant. Drop it here.

### Lakshmi / Vikram (family members), mobile:
1. **P1: the "About you" placeholder looks like filled-in text.** "Retired bank manager, love Carnatic music…" is in `ink-2` at 18px, so it reads as saved content. Use `ink-3` and prefix it with "e.g.". Also, "About you" appears twice (the card title and the field label). Delete the field label.
2. **P1: the photo warning** is a salmon alert box saying the photo "is needed before you can make a profile for your child". Lakshmi already has Ananya's circle, so the message reads as a block. Make it a neutral inline prompt under the avatar with the camera icon as the button.
3. **P2:** "Your families" row: "Circle" is a plain text link next to a big red "Matches for Ananya" button, which looks unbalanced. Use two equal tonal buttons, or make the whole row tappable → Circle, plus one icon button → Discover.
4. **P2:** the avatar colours come from outside the palette (dark green "LR", brown "VR", teal "AR"). Draw initials avatars from a kumkum/turmeric/maroon set only.

### Desktop 1440 (asha): **decent 2-column start, but it wastes space**
1. **P1:** the name is truncated at 1440 ("Seed Candidate O…", seen in round 1) in a 340px left card with plenty of room. Allow a 2-line wrap.
2. **P2:** the Photos card shows 6 empty dashed slots at 250px each. Once the page is empty it is mostly dashed outlines. Show one big "Add photos" drop zone until there's at least one photo.

---

## G. Verify (`/me/verify`)
- **P1:** with no photo this whole page is a dead-end card (F9). With a photo, it wasn't possible to test read-only.
- **P2, desktop:** a 520px card floats at the top of an empty 1200×800 area. Centre it vertically, and add the Seeta–Rama-free illustration of a face in a kolam frame so the page has a subject.

---

## H. Splash and loader
**Splash (both themes, mobile and desktop): good.** It is the strongest screen. The art is centred, the kolam ring and gold wordmark look right, and the tagline reads well.
1. **P2:** the "Skip" button is cream on a ~15% glass pill over maroon, which is hard to see. Give it a 1px gold edge.
2. **P2:** on a phone, 50% of the height is empty above the art (the art starts at y≈310 of 844). Move the art up about 60px so the wordmark isn't pinned to the bottom edge.

**SacredLoader (profile, delayed network): OK, but no header.**
1. **P1:** a full-screen loader with no page title or back button. If loading hangs, the user can't leave. Keep the page header and back arrow visible, and put the loader inside the content area.
2. **P2:** "LOADING…" is letter-spaced caps at 13px in `ink-2`. In Hindi and Telugu, letter-spacing breaks the conjuncts. Use sentence case with no tracking.
3. **P2:** the loader sits at 30% of the height, with 700px of empty cream under it. Centre it vertically.

**Discover skeleton (dark): good shape.** The avatar/header shifts when the account loads, though: "ForKhatri" jumps left. Reserve 44px for the avatar.

---

## I. Cross-cutting
1. **P0:** on a phone, hide the bottom nav on detail pages (profile, thread, verify, create). Every collision found this round comes from the nav + sticky CTA stack (C1, and the Circle/Me forms, where inputs are under the nav in every full-page capture).
2. **P1: header inconsistency.** Discover, Circle and Messages have ForKhatri + avatar + name label. Desktop Discover r2 has only the avatar. Verify has a back button only. Define one header: [back or title] … [page icon actions] [avatar]. The ForKhatri hub link goes inside the avatar menu (it's already in the desktop sidebar footer).
3. **P1: user data stays English in hi/te** ("Hyderabad", "Bengaluru", "Cardiologist", "Associate Director"). The profession is free text and is acceptable. City names come from a known list and should be localised (హైదరాబాద్, हैदराबाद). The month is localised correctly ("సెప్టెం", "सित॰").
4. **P2: `--family` teal** (#0e6a82 / #5cc6dd) is the only non-theme hue left. It shows in the "Viewing Ananya's" chip and in avatars. Replace it with a maroon or gold tint.
5. **Not judged yet:** motion (MotionTitle word-rise, ambient glow) can't be assessed from still screenshots. I'll assess it in a later pass with video capture.

---

## Round 1b (23:20): recheck after the scrollbar and ellipsis fixes, plus the new checklist
The checklist now applies to every screen: visible scrollbars, text clipped with an ellipsis where it could wrap, misaligned left edges, duplicate controls, most visible first. It is run as a DOM audit (`%TEMP%/mangaly-critique/audit.js`) plus a visual check.

1. **P0 (right now): desktop Discover crashes** with the Next.js error overlay: `ReferenceError: title is not defined` at `app/discover/page.tsx:427` in `renderTile` (`<span className="dtile__title">{title}</span>`). It was probably captured mid-edit. On mobile, the same render shows **tiles with no text at all**: no name, age or work under any photo.
2. **P1: ellipsis on mobile Discover (22 lines, audited just before the crash).** The 390px capture still clamps the work line: "Associate Director, Finance · Master's degree", "Founder, climate-tech company · Bachelor's degree", "Jeweller (family business) · Bachelor's degree" and others. Re-verify once the tile renders.
3. **P1: "Viewing Ananya's search" chip ellipsised** in Lakshmi's Circle header at 390px. This is the same element that causes the 426px overflow (section E, P0).
4. **P1: left edges misaligned on desktop:**
   - Discover: the H1 is at x=280, but "Matches for you", the search field, the tabs and the headings start at x=312. That's a 32px step.
   - Circle: the title is at 280, and the subtitle, chip and cards are at 312.
   - Profile: the back arrow is at 293, the title at 332 and the photo at 312.

   Put the page title on the same column as the content. If the back arrow goes to the left of the title, it sits in the gutter (hanging), with the title text at the content edge.
5. **Scrollbars:** the DOM audit found no visible scrollbars in the current build on Discover, Profile, Messages, Circle, Me or Verify, at either width. The desktop shelf scrollbar the owner saw is no longer present. Note that headless screenshots don't render overlay scrollbars, so this relies on the audit.
6. **Duplicate controls, restated:**
   - Messages: header pencil and "New message".
   - ForKhatri link in both the desktop sidebar footer and the page header (Discover mobile, Circle, Messages, Me).
   - Me: avatar in the header on your own profile page.
   - Discover: "Viewing Ananya's search" chip plus "Matches for Ananya".
   - Discover: "Picked for you" and 4 more shelves showing the same people.

---

## Round 2 (~00:00, 25 Sep): checked against the owner's bar, "the best design even in 2040"

Captured with new-headless Chromium and real (non-overlay) scrollbars (`--hide-scrollbars` removed). Viewports: 390x844 at 2x and 1440x900, light and dark. Personas: asha and mangaly-parent. All measurements are CSS px, taken from a DOM dump (`%TEMP%/mangaly-critique/r2.js`).

Each screen is graded on:
- (a) type
- (b) space
- (c) truncation
- (d) scrollbars and overflow
- (e) duplicates
- (f) consistency

### Home (recheck after the lead's changes)
Better. The phone view is now close to the references: a portrait sized to the viewport, then compact 64px rows.

1. **(d) P1, desktop — pointless page scroll.** The page is 913px tall in a 900px viewport, so a page scrollbar appears for 13px of scroll. Trim the bottom padding so the page is at most 100vh.
2. **(b) P1, desktop — empty right column.** The column is 320px wide and holds 2 rows that end at y≈245, leaving 655px empty beside the grid. Fill it with:
   - a Requests row (received and sent)
   - a Messages row (latest thread and unread count)
   - a Circle row with member avatars
   - a "Today's top match" mini card

   Or stretch the rows into bento tiles that match the grid's height.
3. **(f) P1, desktop — names not aligned.** Kunal's meta line wraps to 2 lines, so his name sits at y=384 while Siddharth's and Aditya's sit at 402. Either clamp the meta to 1 line and move the city into a chip, or reserve 2 lines on every card.
4. **(e) P2, desktop — "15" shown three times.** It appears in the red badge, in "See all →" and in the "See all 15 matches" tile. Drop the "See all →" link on desktop.
5. **(c) P1, desktop — profile-strength text cut off.** It is clamped mid-sentence. Shorten it to "Add 3 details to appear in search".
6. **(a) P2 — off-palette colour.** "Asha" uses an orange gradient that is neither kumkum nor turmeric. Use kumkum in light mode and turmeric in dark mode.
7. **Functional — counts disagree.** Home says "New matches 15" and "See all 15 matches", but Discover says "Everyone 14".

**Better treatment for "32 yrs" (people who hide their name):**
- Put the profession in the name slot at the same weight as a name: "Founder 32" at 20px/750 plus 400.
- Add a small lock glyph to signal "name shared after you connect".
- Move the city to the meta line.

### Discover (recheck)
The single photo wall is right.

1. **(c) P0, the most visible item — tile text cut off.** The meta line is still ellipsised on 10 of 14 tiles on the phone and 7 of 14 on desktop, for both personas. `dtile__line` is 11px/500 on 1 line. Fix: show only the profession (drop the city when it matches the viewer's) and allow `line-clamp: 2` at 11.5px. Or put the city in a small glass chip at the top of the tile.
2. **(b) P1, phone — first photo too low (y=240).** Above it sit five control rows:
   - an 11px caps eyebrow
   - the 28px H1
   - search plus Filters
   - the tab band (a darker `surface-2` band, y 124–172)
   - the lens chips

   Merge tabs and lenses into one chip row: Everyone · Top match · Picked · Open to move · Saved. "All matches" duplicates "Everyone". Remove the eyebrow. Target: first photo at y≤150. Right now two "active" markers show at once: the red underline under "For you" and the red "Everyone" pill.
3. **(b) P1, desktop — search too wide.** The search field is 1015px wide. Cap it at 420px, put the lens chips on the same row, and drop the tab row.
4. **(a) P2 — `dtile__why` too small and heavy.** It is 10px/800 caps. Use 11px/600 in sentence case.
5. **(e) P2 — too many overlays on each tile.** Each tile carries a 38px bookmark and a 30px verified circle. Put a 14px verified tick inline after the name and make the bookmark 32px.
6. **Parent at 390px.**
   - The sideways scroll is fixed: scrollWidth is now 390.
   - Two header texts are now truncated: the eyebrow "MATCHES FOR AN…" and the chip "Viewing Ananya's se…". They say the same thing and neither is readable.
   - Fix: drop the eyebrow for parents and shorten the chip to "For Ananya".

### Profile, candidate lens (recheck)
The immersive photo, glass back button, floating bar and sticky desktop photo are right.

1. **(a) P1 — text too large.**
   - Prompt answer: 24px/550, 4 lines on the phone. Use 19px/600 on phone and 22px on desktop.
   - Sealed-card title: 24px/650. Use 18px.
   - Sealed-card list: 15px. Use 14px.
2. **(f) P1, desktop — button and cards misaligned.** The request button is 420px wide (x 752–1172) while the cards are 646px wide (x 752–1398). Make the button full column width, or make it sticky under the photo.
3. **(b) P1 — photo pair leaves a gap.** It leaves 93px empty on the right on desktop and 45px on the phone. Use a 1fr 1fr grid.
4. **(e) P2 — two rows of fine print.** The "Contact details are shared…" line and the "Photos confirmed…" card say two small things in two rows. Merge them into two glass chips on the photo: "Photo-verified" and "Contact after connect".
5. **(f) P2 — double border on the sealed card.** A pink outer border plus a dashed inner one. Use a single 1px `line-2` border.

### Circle (full critique, to drive the redesign)

**asha (candidate, empty circle)**
1. **(d) P1, desktop — pointless page scroll.** The page is 945px tall in a 900px viewport, so a scrollbar appears for nothing. Messages has the same problem at 940px.
2. **(a) Type sizes.**
   - H1 "Home Circle" is 32px/800. For a parent it wraps to 2 lines, because the chip takes up the row. Use 26px on the phone, or title it "Circle" to match the nav.
   - Relation chips are 15px/500 and 44px tall, larger than the Discover lens chips (13px/700, 36px) and the profile chips (12px/600, 30px). Use 13px/600 at 34px tall.
3. **(b) Space.**
   - The 16 relation chips take about 470px on the phone. Show 5, plus a "More relatives ▾" chip that expands in place.
   - The empty Members card with its 180px house takes 250px to say "nobody yet". Remove it and say it in the invite card's heading.
   - Desktop is a single column: the input is 1084px wide and the button 1084px. Use a bento: 5/12 columns of member tiles and 7/12 for the invite card, with the input at most 480px wide and the button auto-width.
4. **(e) Repeats.**
   - The "Looking for Groom" chip repeats what Discover shows.
   - The subtitle sentence and the "Members" heading say the same thing.
   - The segmented control gives the rare path, "Join someone's circle", half the width. Make it a link under the form.
5. **(f) Two tab styles.** This screen uses a neumorphic segmented control; Discover uses underline tabs. Pick one.

**Lakshmi (parent)**
1. **(c) Chip truncated.** "Viewing Ananya's se…" — use "For Ananya".
2. **(a) Explanatory copy too large.** It is 18px/400 over 4 lines. Use 14px over 2 lines.
3. **(e) "Ananya" appears 7 times in the first screen.** Change "In Ananya's Home Circle as Parent" to "You · Parent", and move the paragraph into a tooltip on the call-to-action.
4. **Functional — relation prompt still shown.** Her own row still says "Add your exact relation" even though it shows "Parent".
5. **(f) Off-palette avatar.** Ananya's avatar is a teal initials circle, while Me shows her photo. Use the photo, or maroon/gold initials.
6. **(f) Off-palette chip.** The "1 person helping" chip is pink, a third accent colour. Use gold-tint.

### Messages (full critique)
None of the seeded personas has a conversation.

1. **(e)(f) P1 — header inconsistent and duplicated.**
   - The ForKhatri link is still in the header here, on both phone and desktop. It was removed only on Home and Discover.
   - The pencil button and "New message" do the same thing.
2. **(f) P1, desktop — header squeezed.** The header is crammed into the 360px list pane. Use the global header, with the avatar top right.
3. **(b) P1, phone — empty state.** Three text lines, then about 1,100px of empty page. Add:
   - a story row of circle members and connections
   - centred empty-state art (two kalash, or a turmeric thread)
   - a call-to-action that works: "Invite family" when there are no contacts
4. **(a) Heading weight.** "No messages yet" is 20px/400, the only 400-weight heading in the app. Use 18px/650.
5. **(d) P1, desktop — pointless page scroll.** 940px tall in a 900px viewport.
6. **(b) Desktop — panes not separated.** The list pane and the reading pane are the same colour. Give the list pane `surface-2`.

### Me (full critique, asha)
The page is 3,508px tall on the phone and 2,349px on desktop.

1. **(b) P0, desktop — empty left column.** The left column ends at y≈860 while the right runs to 2,300, leaving about 1,450px of empty left column. Make the left column sticky, or reflow into a bento. The segmented tabs are 950px wide for 3 labels; cap them at 420px.
2. **(b) P1, phone — too long, wrong order.**
   - Put Photos first.
   - Move "Shown openly" to Settings.
   - Turn the 8 section cards (about 270px each) into 2-column tiles about 110px tall.
   - This saves about 1,500px.
3. **(e) P1 — three progress indicators for one fact.** The avatar arc, the stepper with its bar, and the section counts all say "incomplete". The "Next up" card and "Part 1 of 2" add more of the same. Keep the arc and the section counts.
4. **(a) Type hierarchy.**
   - "Your details" is 24px/650, the same as the person's name. Use 18px.
   - `dt` is 11px caps and `dd` 15px/400, so the value outweighs its heading. Use 14px/500 for `dd`.
5. **(f) P1 — inconsistent controls.**
   - Two button styles for "add": a solid outline and a dashed red one.
   - Counts are written "0 /6" in one place and "2 / 6" in another.
6. **(e) P2 — avatar on your own page.** Drop the avatar in the header on /me, since it just links to the page you're on.
7. **Copy.** "manage in In my words" still reads "in In".

---

## Round 3 (00:3x, 25 Sep): luxury pass (Sabyasachi / Tanishq / Taj / Raw Mango / Aman) plus correctness

The serif turn (Cormorant plus italic gold numerals) is the right direction, and the type now reads as couture. The feel is still held back by the component vocabulary around it:
- Filled saturated pills, bold 700–800 sans, glossy red with glow.
- A full-screen petal lattice wallpaper.

In luxury the type is the only loud thing and controls are nearly invisible. Here it is still the other way round.

### Cross-screen P0: the petal-lattice wallpaper
- **What:** a four-petal lattice now tiles every page at high contrast: gold outlines at about 25–35% visible on maroon, and about 20% on ivory. It runs under body text (Circle subtitle, Profile "Contact details…" line) and covers the whole Messages empty screen.
- **Why it hurts:** it reads as gift-wrap or a monogram knock-off, the opposite of Aman/Taj restraint. Luxury uses pattern as a border, a band or a watermark, never as an all-over wallpaper under text.
- **Fix:**
  - Reduce motif opacity to 0.035 (light) and 0.05 (dark).
  - Mask it with a radial fade so it is invisible inside the content column: `mask-image: radial-gradient(ellipse at 50% 40%, transparent 55%, #000 100%)`.
  - Or restrict it to one 64px band under the page title, or to the splash only.

### Cross-screen P1: the chrome vocabulary
1. **Primary button.** "Send a request" and "New message" are saturated #cc0106 (dark: #e3161c) with an 8–22px red glow and a halo ring on the floating bar. Replace with:
   - flat kumkum, no glow
   - a 1px gold keyline inset by 3px
   - 48px tall, 15px/500 text with tracking 0.04em
   - dark mode: velvet #5a0a0c with a gold keyline and ivory text, not bright red
2. **Chips and pills.**
   - The lens "For you 14" is a red fill with a yellow count bubble.
   - Profile and Home chips ("Hyderabad", "Doctorate") are dark pills with borders.
   - "Looking for Groom" is a yellow pill; in dark mode it is almost invisible (dark gold on maroon).

   Replace with 11px/500 small caps text separated by gold middots, and active tabs marked by a 1.5px gold underline. Use no filled pills anywhere except the single primary action.
3. **Weights.**
   - Link buttons are 13px/700 red sans ("Joining someone else's circle instead?", "See all →"). Use 14px Cormorant italic in `--gold-ink` with a hairline underline.
   - Section labels are 11px/800. Use 10px/600 with 0.14em tracking in gold-ink.
   - Body text at 14px/600 should be 15px/400–500.
4. **Glass bubbles on photos.** The grey bookmark circles (38px) and city pills are the cheapest-looking elements on the portraits. Use a 1px gold outline glyph with no bubble, shown on hover on desktop.
5. **Title flourish misaligned.** The gold "·◆·" under "Home Circle" and "Messages" sits under the first word, off-centre (x≈160 on a 320px title). Left-align it to the title's first letter, or centre it under the whole word.
6. **Hindi and Telugu display weight.** Noto Serif at 600 looks much blacker than Cormorant at 600: "नमस्ते," is heavy next to the light Latin "*Asha*". Use weight 500 for `:lang(hi)` and `:lang(te)` display, and 600 only for Latin. Hindi "नए मेल" is ambiguous (मेल also means mail). Use "नए रिश्ते".

### Home: luxury 6/10
Three changes that would raise it most:
1. **Nav.**
   - The latest capture has an outlined active tab with a gold dot, which is the right direction.
   - Labels are still 11px/700. Use 10.5px/500.
   - The desktop sidebar's active item is still a filled red block. Use a 2px foil bar on the left and serif text.
2. **Match count.**
   - Change "New matches 15" (red pill) to "New matches *fifteen*" in italic gold-ink.
   - The desktop "See all 15 matches" tile is a flat red slab. Use ivory or velvet with a gold keyline, "*15*" at 72px Cormorant in foil, and 11px small caps below.
3. **Card chips.** Replace the "Doctorate"/"Telugu" pills with small-caps text, and replace the foil "Verified" pill with a 16px seal next to the name (as on Discover).

Correctness:
- **Truncation (desktop).** The meta line is truncated ("Associate Director, Finance ·…", "Founder, climate-tech company ·…"). The profile-strength row is cut mid-sentence ("start appearing in other…"). Shorten it to "Add 3 details to appear in search".
- **Dead space (desktop).** The right column ends at y≈405, leaving 495px dead.
- **Pointless scroll in Hindi.** The page is 862px on mobile (18px of scroll) and 909px on desktop (9px of scroll, with a scrollbar). Longer Devanagari rows push it over.
- **Transient (seen once, during a reload).** A ~380px **black 10-point star** covered Siddharth's face on Hindi Home. It is the verified-seal SVG rendering unstyled at full width. Give that SVG `width="16" height="16"` attributes (and `fill="currentColor"`) so it can never paint large and black before the CSS applies.

### Discover: luxury 5.5/10
Three changes that would raise it most:
1. **Lens row.** Change the red-filled "For you 14" and the pill borders to serif text tabs with superscript italic counts and a gold underline for the active tab.
2. **City and bookmark on every photo.** Show the city only when it differs from the viewer's, as small caps in the meta line. Make the bookmark a thin gold glyph.
3. **Search and Filters.** The two 44px pills should become one hairline underline field with an italic serif placeholder and a thin filter glyph. This also frees 36px.

Correctness:
- **Name clipping.** `dtile__title` at 20px (phone) and 24.5px (desktop) overflows its box on every tile. `line-height: 1.02` plus `overflow: hidden` clips Cormorant's tall ascenders and descenders. Use `line-height: 1.15` and `overflow: visible`.
- **"Why" line truncated.** `dtile__why` (11px/700) is truncated ("In Visakhapatnam · open to moving"). Shorten it to "Open to move".
- **Telugu.** The eyebrow is 11px/800 Telugu, which is too heavy and too small for Telugu script. Use 12px/500. The lens row is legible.
- **Count mismatch.** Home shows 15; Discover's "For you" shows 14.

### Profile (candidate lens): luxury 6.5/10
The italic Cormorant prompt ("*I'm a cardiologist, so I'll sometimes leave dinner halfway…*") is the most luxurious moment in the app.

Three changes that would raise it most:
1. **Too many boxes.** There are four stacked rounded cards with about 4px gaps, which reads as an app:
   - "Contact…" line
   - verified card
   - prompt card
   - sealed card

   Instead, drop the card chrome on the prompt: italic text between two gold hairlines with 32px of air above and below. Merge "Contact…" and "verified" into one line of small caps. Use 24–32px gaps.
2. **Name panel.** The name sits in a bordered glass panel on the photo, which frames it like a sticker. Use a gradient-only scrim and set the name straight on the photo, as in the Jane Cooper and Yasmin references.
3. **Floating "Send a request".** It has a thick white halo ring and a red glow. Use a flat kumkum button with a gold keyline. Dark mode: velvet with a gold keyline.

Correctness:
- **Motif over text.** The wallpaper motif crosses the "Contact details…" line on mobile light.
- **Scroll-reveal.** The prompt and sealed cards start blurred and reveal on scroll, which works, but the reveal threshold is late. The sealed card is still blurred when half on screen on desktop (y 750–900). Trigger at 15% visibility.

### Circle (candidate asha): luxury 5/10
It now fits one screen on mobile (844), and "join" is a link. Good.

Three changes:
1. **Wallpaper.** The pattern is strongest here: the lower half of the mobile screen is 50% pattern. Mask it (see above).
2. **Relation chips.** They are 44px pills with 15px text. Use 13px/500 with a 1px `--hairline` border at 34px, selected = kumkum text with a gold border (not a fill). "More relatives" is a dashed pill; use an italic serif link "*More relatives…*".
3. **Desktop.** The card is 720px with 400px of empty space to its right. Either centre a 560px card with generous air (Aman-like calm), or put an invitation illustration or quote on the right. Don't leave a lopsided void.

Correctness:
- **Dark contrast.** The "Looking for Groom" chip is nearly invisible (about 1.3:1 contrast).
- **Parent header.** The chip "Viewing Ananya's se…" is still truncated. The 44px serif "Home Circle" wraps to 2 lines. Use 34px and shorten the chip to "For Ananya".
- **Parent Ananya card.** The avatar is still teal "AR". "1 person helping" is still there. The 18px body paragraph remains.
- **Relation prompt.** The prompt is now "Mother or father?" with two chips. That's a sensible fix for the generic "Parent".

### Messages: luxury 5/10
Three changes:
1. **Wallpaper.** On the mobile dark empty state the pattern dominates the whole screen. Mask it.
2. **Button.** "New message" is bright red with a glow. Use flat kumkum or velvet with a gold keyline. Better still for an empty inbox: an italic serif line "*Your conversations will appear here*" plus a quiet link "Invite family to your circle →". Chatting with no contacts is a dead end anyway.
3. **Empty-state icon.** It sits in a 72px bubble. Use a fine 1px gold line drawing (two kalash, or a thread) at 96px, with no bubble.

Correctness:
- **Pointless scroll (desktop).** The page is 916px tall (16px of scroll, with a scrollbar).
- **Avatar placement (desktop).** The avatar sits inside the white panel here, while on other screens it is outside at the page top-right. Make this consistent.
- **Copy.** "Write to someone in your family, or to the family of a match…" should be updated to the one-to-one chat model.

### Me
Not captured this round, because the developer agent is redesigning it. I'll capture it when it's ready.

---

## Continuous watch, 25 Sep 00:05–01:06 (13 cycles)
Each cycle captured Home, Discover, a profile, Circle, Messages, Me, and the family and direct chat threads. Viewports were 390, 620 and 1440, light and dark, with real scrollbars. Each page was loaded fresh and also reached by navigating from a scrolled Discover. The drawer was opened and closed, and focus/pressed states were captured. Scripts: `%TEMP%/mangaly-critique/watch.js`, `thread.js` and `cycle.sh`.

**Found and fixed during the watch:**
- Request popup layered over the ☰ drawer.
- A duplicate connection request from an already-connected person (Siddharth), who also still appeared in Discover.
- Home and Discover counts disagreeing.
- Tiny page scrollbars on Home, Messages and Circle at 1440.
- Two conversations highlighted at once (shared connection id, `?kind` ignored).
- Focus ring drawn as a square box on rounded rows.
- The loud red compose pencil.
- royal.css overrides losing to route stylesheets. That was a cascade-order bug; the fix was to prefix them with `:root`.
- Count bubble, Me hints and 620 rail alignment.
- New thin icon set: the beige disks were removed and the seal became outline gold.

**Still open at 01:06:**
- /me is mid-redesign. It is unstyled, with a 28px stray scroll at 620, and is excluded from the watch until the lead says it's ready.
- Instrument Serif titles (`.dtile__title`, `.profile-hero__name`) have `overflow: hidden` with line-height about 1.02, so ascenders and descenders are at risk. Use 1.2.
- The family-chat avatar stack still clips initials.
- On Circle in dark mode, the "Looking for Groom" chip has low contrast.
- The family-chat title shows "Varun & Asha" plus her own avatar, from asha's side.

**Me deep review (top 8), sent to the lead at 00:52:**
1. Photos first.
2. One consistent next step.
3. Preview should be the real profile component.
4. Prompt hierarchy: the answer should be bigger than the question.
5. Remove the tile drawings.
6. Halve the explanation text.
7. Filled values dominant, empty tiles receding.
8. Header and parent-page cleanup.

**Icon language recommended:** Phosphor Light (1.5px on a 24px grid), round caps, sizes 16/20/28, outline by default, filled only for active or toggled states, `currentColor`, and no containers at rest.

---

## /me deep review after the editorial redesign (25 Sep, ~01:15)
Covered for asha: Details, In my words, Preview with both lenses, "Who sees what" expanded, and the Settings sheet. Covered for mangaly-parent: the single page (it has no tabs). Viewports: 390, 620 and 1440, light and dark. Captures: `%TEMP%/mangaly-critique/me2/`.

**Verdict: 7.5/10. It's a big step up.** It now reads as a person's profile, not a form: photos first, a large Instrument Serif name, underline tabs, hairline rows on desktop, and prompts set as editorial pull-quotes. The Settings sheet is clean on both phone and desktop. What keeps it from a 9 is listed below, most visible first.

1. **P1: Preview with no photo is an empty grey slab.** In both lenses, the "profile card" is a 290px (desktop) or 200px (phone) blank maroon or cream rectangle with the name at the bottom. That's the first thing a candidate sees, and it looks broken, not intentional. Fix: when there is no photo, show her initials large in serif on a soft kumkum-to-gold wash, with a one-line prompt: "Add a photo — this is where it appears". Also cap the desktop frame at 360px wide; at 390 it leaves a void below the new-match lens.
2. **P1: Details on desktop.** The rows are good. But the right column's hairline list starts at x=766 while the photo grid ends at x=680, and the name block ends at y≈640. Below it, the left column is empty for about 380px. Make the left column `position: sticky; top: 24px` so the photos and name stay beside the list while you scroll.
3. **P1: Empty tiles are only marginally quieter than filled ones on phone and 620.**
   - Filled tiles (Basics, Education, Partner preference) have a white card. Empty tiles have a faint card plus a 3-line hint in `ink-3`.
   - The empty hints are longer than the filled values, so the eye goes to the empty tiles.
   - Cut the hints to at most 3 words ("Gotra, sub-community", "Food and habits", "Who's at home", "Optional", "Work, children, money"), or show only "+ Add" for empty tiles, as desktop does.
4. **P1: "Education & career" and "Partner preference" wrap to 2 lines at 390 and 620,** so their values drop lower than Basics' value (misaligned baselines across the row). Title size is about 22px; drop to 19px on tiles under 200px wide, or use "Education" and "Partner" as tile titles.
5. **P2: "50% complete" with a red partial ring is the only red on the page, and it reads as an alert.** Use `ink-2` text and a gold arc, or fold it into the next step: "Next: add photos".
6. **P2: "Who sees what" expanded is a list of five one-sentence rules with no structure.** Group them under "Before you connect" and "After you connect" labels. It's the same information as the Preview lens, so link it: "See it in Preview →".
7. **P2: Parent page (Lakshmi).**
   - The "LR" photo placeholder is 350×440 on desktop (bigger than any real photo on the site) and 110px on the phone. At 1440 it's a huge empty slab. Use a 160px circle with the camera button.
   - "Your families" is well done.
   - The "About you" inputs sit on plain fill with no labels. Placeholders "City" and "Work" vanish on typing. Put labels above the fields at 12px `ink-3`.
   - The red "Make a profile for my child" is the only red on the page. Fine as the primary action.
8. **P2: At 1440 the Preview tab adds a small stray scroll (+25px, page 925 in a 900 viewport). At 620 the Details tab adds +28px.** Trim the bottom padding.
9. **Transient: the loader held for over 1.5s once at 620** (the Seeta–Rama loader filled the page). It was fine on the reload at 3.6s total load. This is only a note: /me is the slowest page to load.

**Developer's functional notes: are they visible?**
- **Preview section list omits Education & career, Community and Horoscope: yes, visibly.** The "someone you have connected with" lens promises "Once you both accept, they see your full profile", but it shows only a Basics block (Marital status, Willing to relocate) between prompts. Her filled Education ("Master's degree · Software Engineer") appears only as a chip on the card, never as a section. Partner preference is also missing. Render every section that has data. Empty sections are hidden, which is correct.
- **Age reads "30" in one place and "30 yrs" in another: yes, visible when switching lens.** The header says "30 · Hyderabad", the connected lens says "Asha *30*", and the new-match lens says "30 yrs". The "30 yrs" form appears because the name is hidden. Use one pattern everywhere: when the name is hidden, show the profession as the title ("Software Engineer *30*"), so the number always reads as an age beside a word, never as a title on its own.

**Rechecks of the lead's fixes:**
- **Circle dark chip "Looking for Groom" is now readable. ✓**
- **Family chat: "Varun's family & yours" ✓.** The list thumbnail now shows Varun's photo, not asha's. Still in the thread header and intro: the stack still includes asha's own "AR", and the initials "DC" and "AT" are still clipped by the overlap.
- **Serif line-height 1.2 ✓.** No title clipping in audits.
- **New regression, Circle at 1440: the invite card is indented.** It starts at x≈485 while the title, subtitle and chip start at x=280. That leaves a 205px empty gutter on the left, as if a members column were missing. Either left-align it to 280, or put the members or empty-state tile in that space.

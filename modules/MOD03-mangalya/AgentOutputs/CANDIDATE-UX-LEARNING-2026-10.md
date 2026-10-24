# Mangalya candidate-to-candidate UX: what we learned, what we take, what we build

Date: 2026-10-07. Learning first, then decisions. No app code was changed.
Owner request: "we need best UI/UX design also. You can find Rebounce, Pure, Nymph, and a few things which can be taken; identify them (which only candidate-to-candidate can be used)."
Mockup: `AgentOutputs/onboarding-mockups/candidate-ux.html` (four phone screens, light and dark, kumkum + turmeric).
Screens walked: Mangalya at http://localhost:3000 as Asha Reddy (candidate, Telugu), 390 px and 1280 px, read-only, own browser context `cand-ux`. Screenshots in the session scratchpad (`cand-ux-*.jpeg`).

Rules this document keeps: the owner's product model (DEC-V1-018/021/022/026/031), "calm, royal, not highlighted", kumkum + turmeric, no grey, red only on the one primary action, no score shown, no visitor lists, "Looking for" and mutual preferences always applied, parents act for the candidate, no screenshots, no platform video calls, no unnecessary intermediate screens, protect the base.

Candidate-to-candidate mode, as used below: both people are candidates with their own accounts, each reading the other's "In my words" lens. The moment a parent or Home Circle member is the one sending, reading or answering, we are in family mode, and the pattern must fit the biodata lens the owner fixed for parents.

---

## 1. The apps the owner named: identified

| Owner's word | What it actually is | Found where | Can we use its ideas? |
|---|---|---|---|
| **Rebounce** | **Rebounce Matrimony App**, by QuackQuack (publisher Verve Mobile Pte. Ltd.). India's matrimony app for divorced, separated and widowed people seeking remarriage, ages 30 to 55. Launched around Aug 2025 (App Store version history), press on 7 Nov 2025; about 700,000 profiles by Aug 2026. Profiles make room for "detailed personal storytelling" (children, co-parenting, family dynamics, lifestyle); "Screened profiles"; "Control your visibility and interactions manually"; human matchmaking through a paid PlusAssist tier (₹499 a month, ₹3,500 half-year, ₹4,899 a year: messages to 20 new people a day, visitor information, 20 contact requests a day). It does not allow AI-altered photos but allows AI help with profile writing and conversation starters. | App Store https://apps.apple.com/app/id6747021516 (v1.2.5, 4.8 from 27 ratings); Global Dating Insights 7 Nov 2025 https://www.globaldatinginsights.com/featured/quackquack-introduces-rebounce-app-for-second-chance-dating/ ; MediaInfoline 7 Nov 2025 https://www.mediainfoline.com/brand/quackquack-launches-rebounce-indias-first-serious-matchmaking-and-matrimony-platform ; GDI 21 Aug 2026 https://www.globaldatinginsights.com/featured/rebounce-indias-dating-market-is-opening-to-second-relationships/ | Yes: the remarriage storytelling fields and the "no AI-altered photos" rule. No: visitor lists (Mangalya rules them out). |
| **Pure** | **PURE: Open-Minded Dating App** (its own tagline: "Shameless dating app"), by Online Classifieds AG, Zug. Started 2012; $100 million gross revenue reported Jan 2026. It is a casual, anonymous "personal ad" app: you write what you are looking for, chats are built to leave no trace. Its App Store text: "Photos self-destruct right after being seen", "in case someone takes a screenshot, you will get a notification", "all chat messages, including photos and audio, shared in chats cannot be saved", automatic "alerts on trigger words that might be used by scammers", "Keep chatting via PURE and do not switch to other messengers". Reviews describe a 24-hour chat timer that both must switch off, and random nicknames after that (secondary sources; Pure's own pages do not list these). | Wikipedia https://en.wikipedia.org/wiki/Pure_(app) ; App Store https://apps.apple.com/us/app/pure-open-minded-dating-app/id690661663 (4.3 from 86K ratings, 18+); https://pure.app/ ; timer and nicknames via https://www.doulike.com/blog/online-dating/pure-dating-app-review/ (unverified against Pure itself) | Only its privacy mechanics (ephemeral chat, scam-word alerts, "stay in the app" nudge). Its framing (casual, anonymous, hookup) must never appear in Mangalya. |
| **Nymph** | **Nymph: Open-Minded Dating App**, by Nymph GmbH, Berlin. A dating app for people in non-monogamous and open relationships, singles and couples. App Store text: "encrypts every chat", "verification process ensures genuine people — no bots, no fakes", photo prompts and voice answers on the profile, swipe discovery with "Standouts", Private mode, hide active status, photo blur, private photos. Google Play rating 2.9 from 3.6K reviews (third-party listing, unverified). | App Store https://apps.apple.com/us/app/-/id6475792735 (4.4 from 1.4K ratings, 18+); https://nymph.so/ ; https://www.apppricinglab.com/app/google_play/so.nymph.android | Only its privacy controls (private photos for connections, hide active status, blur). Its relationship model and swipe deck must never appear in Mangalya. |

All three were found; none had to be guessed. I checked "Rebound" too: it is a different thing (a breakup-tracker app and "RebounDate"), not what the owner meant.

### Other apps studied (all verified from their own pages or listings; dates given)

- **Hinge** (Match Group): Voice Prompts, 30 seconds, "directly beneath the first picture", launched 27 Oct 2021 (https://hinge.co/press/voiceprompts). Match Note, 26 Feb 2025: a private note of up to 255 characters shown after both like each other; "the other person must view the note in order to complete the match"; 68 per cent said it helped (https://hinge.co/press/match-note). Your Turn Limits, 18 Sep 2024: with 8 unanswered chats you must reply or end one before matching again; responsiveness up 20 per cent (https://hinge.co/press/your-turn-limits). Video prompts and polls, 20 Sep 2022; a profile is 6 photos or videos, 3 written prompts, 1 voice prompt (https://techcrunch.com/2022/09/20/hinge-gives-users-new-video-prompts-and-polls/amp/). Chat teardown, 7 Apr 2025: a Like goes to one photo or one answer with a comment; inbox sections "Your Turn", "Their Turn", "Hidden" (14 days quiet); "We Met" asks days later whether you met (https://www.cometchat.com/blog/beyond-the-bubble-hinge).
- **Bumble**: Opening Moves, announced 30 Apr 2024: a woman sets a question that every new match answers first instead of her writing the opener; she can pick a suggested one or write her own (https://www.businesswire.com/news/home/20240430323928/en/Bumble-Gives-Women-More-Choice-to-Make-the-First-Move ; https://fortune.com/2024/05/01/bumble-changes-dating-app-women-make-first-opening-move/). "Up to three at a time" and "two free Compliments a week" come from a 2026 overview, not Bumble (https://www.unilink.us/blog/how-does-bumble-work-2026, unverified). Private Detector blurs unsolicited lewd images; Incognito is a paid feature; photo verification is a posed selfie checked by a person.
- **Aisle** (India): "Nothing casual about this dating app", "slow > speed" (https://www.aisle.co/). App Store: "Comments: start a thoughtful conversation by responding to what caught your eye on someone's profile"; "Private Browsing: browse with complete control. Especially for women to date safely"; "Every profile goes through a 2-step verification process"; Concierge; Plus and Premium (https://apps.apple.com/in/app/aisle-dating-app-for-indians/id1001481078). A "settle down" timeline choice (https://www.globaldatinginsights.com/news/aisles-new-feature-helps-users-display-their-plans-for-settling-down/). Regional apps Arike (Malayalam), Neene, Neetho, Anbe (https://www.medianews4u.com/aisle-launches-malayalam-dating-app-arike/, 4 Aug 2026).
- **Breeze** (Netherlands, no chat): "Every day at 7PM we'll send you a handful of people", "If it is a match, you skip the chat", "fill in the planner and we take care of the rest", "pay upfront to show commitment", "1.500+ partnered bars", "Ghosters get their account frozen", "under 1% no-shows" (https://breeze.social/). 36,000 dates in a month, still growing while other apps fall (https://nltimes.nl/2026/08/18/dating-apps-quickly-falling-favor-dutch-users).
- **Thursday**: works one day a week; matches and chats vanish at midnight; up to 10 matches; weekly singles events (https://sfstandard.com/2024/09/12/single-and-ready-to-mingle-but-only-on-thursdays/).
- **Schmooze** (India, Gen Z): swipe on memes, not people; 48 hours to write before the chat disappears; "Riya", a voice AI you describe your match to (https://apps.apple.com/in/app/id1551217274 ; https://inc42.com/buzz/schmooze-unveils-voice-ai-matchmaker-riya-to-tackle-swipe-fatigue/).
- **Raya**: application and referral; profile linked to Instagram; a photo montage with music; screenshot warning, then removal (https://en.wikipedia.org/wiki/Raya_(app)). 10-day match expiry (https://graziadaily.co.uk/life/real-life/raya-dating-app/, secondary).
- **Feeld**: Incognito ("view profiles without showing up in other people's Discover, unless you like them first"), Private photos (visible only to connections), nudity blurred, paid Pings to jump the queue, opt-out of ping notes (https://feeld.co/ask-feeld/how-to/how-to-stay-private-on-feeld ; https://feeld.co/about/faq).
- **Betterhalf** (India): "Selfie and Govt ID-verified" profiles, a compatibility score, personality quiz, free chat, Crown badge, Sparkle to be first, 24-hour boost, astrologer and wedding services (https://apps.apple.com/in/app/betterhalf-matrimony-app/id1438203766).
- **Shaadi.com**: "Request photo" for profiles without one (https://support.shaadi.com/support/solutions/articles/48000953215); separate privacy for Profile Photo and Photo Album, options not listed in the article (https://support.shaadi.com/support/solutions/articles/48000755528-i-want-to-change-the-privacy-settings-of-my-photos); Shaadi Live: 10 matches in one hour over five-minute video calls (https://www.afaqs.com/news/mktg/shaadicom-launches-shaadi-live); shortlist; Shaadi Meet video calls (App Store id480093204).
- **Jeevansathi**: "100% Screened Profiles", "Restrict unwanted access to contact details & photos/videos", "Send Interests & Connect", video profiles (https://www.jeevansathi.com/); selfie verification, Daily Match Alerts, interest and accept notifications, contact view as premium (https://apps.apple.com/in/app/jeevansathi-com-matrimony-app/id969994186). Calling without showing the number is in its listing text (not re-verified on the site).
- **BharatMatrimony**: SecureConnect (calls without revealing the number; "choose who can call them"), Prime needs a degree, government ID and a photo, Assisted manager in the local language (https://www.globaldatinginsights.com/news/bharatmatrimony-launches-prime-membership-for-premium-users/ ; https://apps.apple.com/app/id465923141).

Not verified, so not used: Bumble's exact Opening Moves count and Compliments quota; Pure's timer length; Raya's 10-day expiry; Nymph's Google Play rating.

---

## 2. What the real Mangalya candidate screens look like today (Asha, 7 Oct 2026)

- **Home** (390 px): date, "Namaskaram, Asha", one daily introduction (Aditya, 29) as a tall full-bleed photo card with his published answer as a quote, "Strong match", photo badge, two reasons, "View profile", "How you fit" disclosure; then "Strong matches" row, "Your search" (2 requests waiting, 0 connections, 0 family picks), two "More like Kunal" rows, matchmaker, profile strength, Home Circle, horoscope, and the plan cards. Calm, serif, kumkum only on the primary button. Reasonable.
- **Discover**: search, Filters, tabs "For you 12 · Horoscope 6 · All · Saved", the matchmaker prompt card, then the two-column photo wall. Each tile: a gold "Strong match" or horoscope line ("28 of 36 gunas"), name or age, photo badge, city and work, a save bookmark, and "Request sent" where true. Good base. Tiles do not yet show the published answer quote on this seed (DEC-V1-021 allows it).
- **Profile (Aditya, pre-connection)**: full-bleed photo, "Aditya 29", chips (Hyderabad, Product Designer, Bachelor's), "Contact details are shared only once you connect", "Why you may fit" (one line), photo badge, "You two" card (Strong match, "1 thing matches", tabs You & them / Horoscope, "What you want", "What they want"), one published prompt as a quote, a "Closed until you connect" card ("Their other answers; their ten quick choices beside yours"), "Nobody is ranked as a person, no score. A request is only a question; no is a normal answer.", the kumkum **Send request** button (a plain button, no note), report or block, then "Similar profiles".
- **Circle**: members (Lakshmi Reddy, mother), invite form with relation chips, "Requests you sent" with "Waiting for an answer" and "Sent by family · 5 Oct" / "You sent · 25 Sep".
- **Messages**: one list: Siddharth Reddy (incognito, lock), "Varun's family, your family" (families), Rekha Tandon (direct, Varun's mother), Varun Tandon (incognito). Desktop shows two panes, phone shows the list. No grouping by who must answer.
- **Me**: photos (six slots), name, "53% complete", Details tab (biodata groups), **In my words** tab: three written prompts with answers, "Your voice introduction: say namaskaram in your own voice, up to a minute. Only people you connect with can hear it", "Ten small questions", Preview.

Where it is thin for two candidates: the request is a bare button (no reply to the thing that caught your eye, no question from the other side); the match moment is a popup that only accepts or declines; the incognito chat begins with nothing to say; there is no way to move from chat to an actual meeting except leaving the app; the inbox does not say whose turn it is; there is no quiet-browsing control; nothing after a meeting feeds the matchmaker.

---

## 3. Pattern table

Use: **C** = candidate-to-candidate only (both people are the candidates; no parent or Home Circle member sends, reads or answers it). **Both** = also fine when a parent manages the profile. **Never** = not in Mangalya.

| # | Pattern | Source (verified) | Use in Mangalya | Why |
|---|---|---|---|---|
| P1 | Request anchored to one thing: "Reply to this answer / this photo" with a short note | Hinge (like a specific photo or prompt with a comment, CometChat 7 Apr 2025); Aisle "Comments"; Bumble Compliments | **C** for anchoring to a prompt answer or a photo; **Both** for a plain note on a request | Prompts are the candidate lens (DEC-V1-018). A parent sends from biodata, so their note is about facts ("same native place, we would like to talk"). The note keeps the request a question, not a verdict. |
| P2 | Opening question: the receiver sets one question every request must answer first | Bumble Opening Moves, 30 Apr 2024 | **C** | Only a candidate can answer in their own voice. When a parent sends on the child's behalf, the question is shown as "Asha would like to know this when you connect", not answered by the parent. Dignified, and it gives the shy side a script. |
| P3 | Before-we-talk note: a private line shown at the match moment that the other must read before the chat opens (health, divorce, "I will keep working", "I live with my parents") | Hinge Match Note, 26 Feb 2025 | **C** (read by the other candidate; parents see the biodata facts instead) | Families already say such things through a broker. Saying it once, in writing, before the first chat, spares both sides a painful second meeting. 255 characters, in any of the three languages. |
| P4 | Voice introduction under the first photo, 30 to 60 seconds | Hinge Voice Prompts, 27 Oct 2021; Nymph voice answers | **C**, keep as built (hear it after connecting) | Already in Me → In my words. Keep it behind the connection: a voice is more identifying than a photo (critique H2). |
| P5 | Inbox grouped by turn: "Waiting on you", "Waiting on them", quiet threads folded away | Hinge Your Turn / Their Turn / Hidden | **Both** | Parents and candidates both lose threads. Cheap, calm, no counts in red. |
| P6 | A cap on unanswered conversations before starting new ones | Hinge Your Turn Limits (8), 18 Sep 2024 | **Never** as a block; **Both** as a one-line nudge ("3 people are waiting for your reply") | Mangalya already limits requests a day by plan; a second gate is a dark pattern risk (critique 13). |
| P7 | Private "how did it go" after a meeting | Hinge We Met | **Both** (asked of whoever attended; never shown to the other side) | Feeds the matchmaker's ordering with a real signal while keeping popularity at zero (DEC-V1-002). |
| P8 | Propose a meeting from the chat: day, time, a place; no long chat first | Breeze (planner, partner bars, <1 per cent no-shows); Thursday (same-day) | **Both**: candidates propose a coffee; parents propose a family meeting | Mangalya already has first-meeting places in Wedding arrangements (OSM cafés). The proposal card lives inside the chat, no new screen. Never Breeze's fee or Thursday's midnight expiry. |
| P9 | Quiet browsing: invisible in Discover except to people you have requested | Feeld Incognito; Bumble Incognito; Aisle Private Browsing "especially for women"; Nymph Private mode | **Both**, free | Women and parent-run profiles want to look without being seen. Must be free (not a Gold feature) and must still obey "Looking for" and mutual preferences on the server. |
| P10 | Private photos opened only to connections; one or two shown openly | Nymph private photos; Feeld; Shaadi album privacy | **Both**, already built (DEC-V1-021 "openly shared") | Keep. Add "Ask to see more photos" (Shaadi's Request photo) as a polite request, answered by the candidate only. |
| P11 | Hide active status; no "online now" | Nymph "hide active status" | **Both**: Mangalya never shows online status or last seen | Being watched is what families fear (DEC-V1-021 rules out view lists). Decide it once and do not add presence dots later. |
| P12 | Chat that leaves no record, with a visible rule | Pure (messages cannot be saved); Mangalya's own incognito session | **C**, already built | Keep. Show the rule plainly in the header: "Ends when either of you leaves, or after 30 quiet minutes." Do not promise "only the two of you can read this" (critique H5); say "not stored". |
| P13 | Scam trigger-word alerts in chat ("send money", UPI, "transfer", dowry phrases) | Pure ("automatic alerts on trigger words that might be used by scammers") | **Both** (all three chat kinds) | DEC-V1-006 already runs a text classifier; this is a user-facing nudge, in en/hi/te, with a one-tap report. Also answers critique H6 (dowry). |
| P14 | "Stay in the app" nudge when someone pastes a phone number or WhatsApp | Pure ("do not switch to other messengers") | **Both**, gentle, once per thread | Contact details are shared after connection by design; the nudge is about scams, so it appears only before a connection or when a stranger pushes. Never a block. |
| P15 | Screenshot notification to the other person | Pure; Raya warning and removal | **Never** as a claim | A web app cannot detect OS screenshots (mangalya-no-screenshots memory). Do not promise it. |
| P16 | Remarriage storytelling fields: children, living arrangement, what I learned, what I need now | Rebounce (co-parenting, family dynamics, "practical compatibility") | **Both** | Marital status exists; add three plain fields and one prompt for second marriages. Jeevansathi reports remarriage at 16 per cent of its users (critique §3). |
| P17 | No AI-altered or AI-generated photos; AI may help write | Rebounce (21 Aug 2026) | **Both** | Matches Mangalya's face-match design. Write it into the photo rules and the guide. |
| P18 | Few, deeper introductions a day instead of an endless deck | Breeze (a handful at 7 PM); Thursday; Hinge Most Compatible | **Both**, already built as Home's daily pick | Keep Home's one introduction and Discover's wall (owner decision). Do not add a timer or a countdown. |
| P19 | "When do you hope to marry" as a visible chip | Aisle "settle down" | **Both** | One chip in Future plans, read by both lenses. |
| P20 | Swipe deck, like or reject by gesture, Standouts by attention | Nymph, Feeld, Schmooze, Tinder-style | **Never** | Rejection by flick is the opposite of "a request is only a question". Popularity weight is zero. |
| P21 | Pay to jump the queue (Pings, Roses, Sparkle, Crown, boosts) | Feeld Pings; Hinge Roses; Betterhalf Sparkle, Crown, boost | **Never** | Paid attention breaks "nobody is ranked as a person" and reads as a dark pattern to families. |
| P22 | Who viewed me, recent visitors | Rebounce PlusAssist "profile visitor information"; Jeevansathi recent visitors; Shaadi | **Never** | DEC-V1-021. Gold today sells "who viewed your profile" (critique H4): see the open question. |
| P23 | Displayed compatibility number or fraction | Betterhalf score; Shaadi "7/10" | **Never** | Guardrail: words and checkable reasons only (DEC-V1-031). |
| P24 | Expiring matches (24 h, 48 h, 10 days, midnight) | Pure, Schmooze, Raya, Thursday | **Never** | Pressure is the casual-app tell. Mangalya's 90-day and 21-day waits after a decline or withdrawal are the opposite kind of pacing and stay. |
| P25 | Anonymous nicknames, personal ads, "turn-ons", open-relationship or couples profiles | Pure, Nymph | **Never** | Identity and family are the product. |
| P26 | Instagram link, music slideshow on the profile | Raya | **Never** | Not calm; a link is a stalking path. |
| P27 | Memes as the matching signal | Schmooze | **Never** | Humour matters, but a shared meme deck is not how a Khatri family judges a match; the ten drawn choices do that work. |
| P28 | Video prompts on the profile | Hinge (2022); Jeevansathi video profiles | **Not now** (C, behind the connection, later) | Video is heavier to capture and more identifying than photos; it needs the same openly / sealed control. Revisit after P1 to P9. |
| P29 | In-app video or masked voice calls | Shaadi Meet, Shaadi Live, Jeevansathi, BharatMatrimony SecureConnect | **Never** in-house (owner: no platform video call service); masked calling only later through the shared integrations utility | Owner decision. |
| P30 | Same-day events, bar takeovers | Thursday AfterParty; Shaadi Live | **Both**, but through Milavn events, not inside Mangalya | Milavn owns events; Mangalya may link a Samaj meet. |
| P31 | Human matchmaker tier with daily message and contact caps | Rebounce PlusAssist; BharatMatrimony Assisted | **Both**, already the Assisted plan and agents | Only fix: state what Assisted delivers (critique H4). |

---

## 4. Screen by screen: the candidate-to-candidate mode

Everything below lands inside screens that exist. No new top-level destination.

### 4.1 Profile (candidate lens, before a connection)

What changes: the published answer gets a small "Reply to this" link; tapping it opens the request box in place under the answer (no sheet). The box carries the other side's opening question when they set one. The kumkum button stays the only red thing.

```
+--------------------------------------+
| <                                    |
| [photo, full bleed]                  |
| Aditya 29                            |
| (Hyderabad)(Product Designer)(B.Des) |
+--------------------------------------+
| lock  Contact shared once you connect|
| Why you may fit                      |
|  . same view on moving (open)        |
|  . photo badge . Sept 2026           |
+--------------------------------------+
| "What is usually on my plate"        |
|  My dad runs a Punjabi restaurant... |
|                     [Reply to this]  |
|  +----------------------------------+|
|  | Reply to "What is usually on..." ||
|  | [ I make a decent pesarattu too..||
|  |   ______________________ ] (mic) ||
|  | Aditya asks everyone first:      ||
|  | "Tea or filter coffee, honestly?"||
|  | [ ____________________________ ] ||
|  |          [  Send request  ]  red ||
|  +----------------------------------+|
| Closed until you both say yes        |
|  . his other answers . ten choices   |
|  . his voice introduction            |
| Report or block                      |
+--------------------------------------+
```

Family mode on the same page: no "Reply to this" (prompts are not in the parent lens). The request box has one note field ("Why we are writing") and the line "Aditya would like to know: Tea or filter coffee? He will ask Asha when they connect."

### 4.2 The match moment ("You both said yes")

Today the request popup ends in accept or decline. After both accept, show one calm card, once: the other candidate's before-we-talk note (if any), which must be read before the chat opens, then their voice introduction and the opening of the sealed answers.

```
+--------------------------------------+
|            . . .  (kolam dots)       |
|        You both said yes             |
|   Asha and Aditya . 7 October        |
|                                      |
|  Before we talk, Aditya wrote:       |
|  +----------------------------------+|
|  | I was married before, for two    ||
|  | years. No children. I would      ||
|  | rather you know this first.      ||
|  +----------------------------------+|
|  [ I have read this ]  (gold outline)|
|                                      |
|  Now open to you:                    |
|   > his voice introduction  0:41     |
|   > his other answers, ten choices   |
|                                      |
|  [ Start the conversation ]  red     |
|  Ends when either of you leaves, or  |
|  after 30 quiet minutes. Not stored. |
+--------------------------------------+
```

Family mode: the parent's popup is unchanged (biodata card). A parent never sees the before-we-talk note; they see the formal fields (marital status) they already can.

### 4.3 Incognito chat (two candidates)

Header states the rule in plain words. Two things are added in place: a scam or money nudge that appears above the composer only when a trigger phrase is detected, and "Propose a meeting", which opens a card inside the thread.

```
+--------------------------------------+
| <  lock  Aditya                      |
|    Ends when either leaves . 30 min  |
|    quiet . not stored  [Propose meet]|
+--------------------------------------+
|  Namaskaram Asha. Your reply about   |
|  pesarattu made my mother laugh.     |
|                       (his, left)    |
|          Then she has to try mine.   |
|                     (yours, right)   |
|                                      |
|  +---- Meeting proposed ------------+|
|  | Sat 11 Oct . 4 pm                ||
|  | Chutneys, Jubilee Hills (cafe)   ||
|  | 2.1 km from you . open till 10   ||
|  | [Accept] [Suggest another time]  ||
|  | Share with my family  (o  )      ||
|  +----------------------------------+|
|                                      |
|  ! This message asks for money.      |
|    Mangalya never asks for money     |
|    and nor should a match. [Report]  |
| [ Write...                 ] (mic)(>)|
+--------------------------------------+
```

Family mode: the families' group and the direct parent chats get the same proposal card ("Family meeting"), the same scam nudge, and no "not stored" line (those chats are kept).

### 4.4 Messages (inbox)

```
+--------------------------------------+
| Messages                    (new)    |
| Waiting on you (2)                   |
|  lock Aditya      Then she has... 2m |
|  Rekha Tandon     Namaste Aunty.. 1d |
| Waiting on them (1)                  |
|  lock Varun       You: see you.. 3d  |
| Families (1)                         |
|  Varun's family, your family   24 Sep|
| Quiet for 14 days  >                 |
+--------------------------------------+
```

### 4.5 Me → In my words (candidate only)

Two new rows under the three prompts and the voice introduction:

```
| A question for everyone who writes to me        |
|  "Tea or filter coffee, honestly?"      [Edit]  |
|  Shown in the request box. Optional.            |
| Before we talk (private)                        |
|  "I was married before..."              [Edit]  |
|  Shown only to a candidate you both said yes to,|
|  before the chat opens. Never to families.      |
```

Settings (Me → gear), for every account: **Quiet browsing** (off by default): "You do not appear in Discover. People you send a request to can still see you." Free.

### 4.6 Discover and Home

No layout change. Discover tiles already may carry the published answer as a quote (DEC-V1-021); turn it on in the candidate lens so "Reply to this" has something to reply to from the wall. Home's daily pick keeps the quote and gains the same "Reply to this".

### 4.7 Desktop (1280 px)

Profile: photo column left, "You two" and the answers right, the in-place request box under the answer in the right column. Chat: the proposal card and the nudge inside the thread pane; the match card as a centred dialog over the two-pane inbox. Nothing else moves.

---

## 5. Decisions

Ordered by value for effort; respects every recorded owner decision. Build order is the row order.

| # | Decision | Mode | Why | Effort |
|---|---|---|---|---|
| D1 | Request with a note, anchored to one answer or photo in the candidate lens; a plain note in family mode. The box opens in place under the answer. | C (anchor), Both (note) | P1. The single biggest lift for two candidates; no new screen. Server: `connection_request.note`, `anchor_kind`, `anchor_id`. | S |
| D2 | Opening question, optional, set in Me → In my words; shown in the request box; parents see it as "will be asked on connecting". | C | P2. Gives the quiet side a script, keeps parents in the biodata lens. | S |
| D3 | Before-we-talk note, 255 characters, private, shown at the match moment and acknowledged before the chat opens. Never shown to families. | C | P3. Honesty before the first chat; fits "a request is only a question". | S to M |
| D4 | Match moment card: "You both said yes", note, newly opened items, "Start the conversation", the chat rule in plain words. Replaces the bare accept outcome for candidates. | C | Makes the opening of the sealed card an event, calmly. | S |
| D5 | Inbox grouped by turn: Waiting on you, Waiting on them, Families, Quiet for 14 days. No red counts. | Both | P5. Cheap; helps parents most. | S |
| D6 | Propose a meeting inside any chat: day and time chips, a place from the first-meeting places already imported, "Share with my family" toggle (off by default in the candidates' chat, on in family chats). Accept or suggest another. | Both | P8. Turns chat into a meeting, the thing families actually want. Reuses Wedding arrangements data. | M |
| D7 | After the meeting day, a private "How did it go?" with three answers; never shown to the other side; feeds ordering only. | Both | P7. First real signal for the engine beyond stated facts. | S |
| D8 | Scam and money nudge in all chats, in en/hi/te, one-tap report; "stay in Mangalya" nudge once per thread before connection. | Both | P13, P14, critique H5 and H6. Uses the existing classifier. | S |
| D9 | Quiet browsing, free, in settings; server-side; obeys Looking for and mutual rules. | Both | P9. Women and parent-run profiles. Not a Gold feature. | M |
| D10 | Chat header copy: "Ends when either of you leaves, or after 30 quiet minutes. Not stored." Remove "Only the two of you can read this". | C | P12, critique H5. Honest. | XS |
| D11 | Mangalya never shows online status or last seen. Recorded so no presence dots are added later. | Both | P11, DEC-V1-021 spirit. | none |
| D12 | Remarriage fields (children; living with me or not; one prompt "What I learned, what I need now") and the "When do you hope to marry" chip. | Both | P16, P19. Second marriages are a real share of the market. | S |
| D13 | Photo rule: no AI-generated or AI-altered photos; AI may help write answers. In the guide and the photo step. | Both | P17. | XS |
| D14 | Not now: video prompts (P28). Later, behind the connection, with the same openly or sealed control. | C | Weight and identifiability. | — |
| D15 | Never: swipe or flick rejection, paid queue-jumping, visitor lists, shown scores or fractions, expiring matches, anonymous nicknames, Instagram links, music slideshows, meme matching, in-house video calls, screenshot-notification claims (P15, P20 to P27, P29). | — | Owner model, guardrails, calm. | — |

**Left open for the owner (only these):**

- **O1. Gold sells "See who viewed your profile" and "See who shortlisted you"** (seen live on Home and on /plans). This contradicts DEC-V1-021 and critique H4, and pattern P22. Removing it changes a pricing decision, so it is the owner's call. Recommendation: replace both with "See who sent you a request" (already free) and keep Gold on unlimited requests and the kundli report.
- **O2. Taste: should the opening question (D2) also appear on the Discover tile** under the quote, or only on the profile? Recommendation: profile only, to keep the wall a photo wall.

Everything else above is decided. Build D1 to D5 first (all small, all in place), then D6 to D9, then D12 and D13.

---

## 6. What was not done, honestly

- Read-only: no request sent, no chat opened (opening an incognito thread could start a session), no setting changed, `/profile/create` untouched (another agent is editing onboarding).
- The 390 px walk covered Home, Discover and the profile; Circle, Messages and Me were captured at desktop width because background tabs ignored the phone resize. The Messages phone view was read from the accessibility tree.
- Bumble's and Pure's own help pages could not be fetched (redirects and 404s), so their details rest on their press releases and App Store text plus one secondary review each, marked above.

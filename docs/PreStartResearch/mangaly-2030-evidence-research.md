# Mangaly toward 2030: evidence research

**Prepared:** 2026-09-28, for the ForKhatri product owner (Mangaly, MOD03)
**Priority of this run:** (1) a Home that adapts to the person's seat (parent or candidate); (2) real reviews; (3) "because" rows; (4) premium tiers; (5) trends to about 2030.
**Rules followed:** every claim has a source; anything I conclude is labelled **Inference**; figures for 2030 are extrapolations from cited trends; no statistics are invented.

## Method and limits (read first)

- **Reddit could not be read.** My tools refuse reddit.com (HTTP 400, "domain not accessible to our user agent"). As forum evidence from candidates and parents I used TeamBlind threads, press interviews that quote users, Trustpilot and App Store reviews instead. Quora pages returned HTTP 403. The report therefore has no r/india, r/indiasocial, r/ABCDesis or r/NRI quotes. It does not pretend to.
- **The Google Play review text could not be read** (the pages render without it). App Store "see all reviews" pages and Trustpilot pages could be read.
- **How the quotes were captured.** Review quotes came through a fetch tool that sometimes shortens long reviews. Quotes with the reviewer's own typos ("Fack app", "promiss", "scamed") are verbatim. Others may be lightly shortened, but I did not reword them.
- **The sample is biased.** Trustpilot draws unhappy reviewers: Shaadi scores 1.2/5 there, yet 4.3/5 from 126,000 App Store ratings. The themes show what makes people angry, not how common each experience is.
- **The review sample** is 129 reviews read across 12 pages:
  - Trustpilot: Shaadi (2 pages, 40 reviews), BharatMatrimony (21), Jeevansathi (20).
  - App Store: Shaadi IN (4), BharatMatrimony GB (10), BharatMatrimony IN (4 summarised), Aisle (10), Betterhalf US (10), Betterhalf IN (5), Jeevansathi IN (3), Hinge IN (2).
- **Where this sits in Mangaly's decisions.** The owner's rules are taken as fixed:
  - roles are per relationship, and only the profile-viewing style and messaging vary by role;
  - Home is the family's desk, not a second Discover (owner, 2026-09-28);
  - the score is never shown;
  - no view counts or popularity indicators (FR026, line 997 of `02-functional-requirements.md`);
  - Discover's "For you" rows (DEC-V1-022).

Every tension with these rules is flagged where it occurs.

---

## 1. The ten strongest findings

| # | Finding | Evidence count | Key sources |
|---|---|---|---|
| 1 | **Fake or inactive profiles are the top trust complaint, and users believe the platforms plant them to sell plans.** | 34 of 129 reviews (26%) | Trustpilot Shaadi, BharatMatrimony, Jeevansathi; App Store Aisle, Betterhalf, BharatMatrimony |
| 2 | **"I paid and nothing happened" is the top money complaint**: premium, VIP, Select, Assisted or Exclusive plans that do not deliver, and refunds refused. | 52 of 129 (40%). 5 of them are about auto-renewal or overcharging. | Same as above |
| 3 | **Families are still involved, most of all in South India, even when the candidate made the profile.** | 5 independent sources | ThePrint 2022 (Shaadi data: 45–50% of South Indian accounts created by parents; 80–90% of educated South Indians want parents involved); Jeevansathi 2026 (69% say parental involvement makes it easier, 75% of women); Bharadwaj 2021 (22% of women's profiles self-managed); The Walrus 2025; ABC 2026 |
| 4 | **Parents and candidates weigh different things.** Parents weigh community, family background and education more; candidates weigh looks, personality and chemistry more. | 4 sources, including 2 peer-reviewed | Agey, Conroy-Beam & Gaulin 2024 (Nepal, arranged-marriage context: the largest gaps are same caste for parents and physical attractiveness for offspring); Buunk, Park & Dubbs 2008; ABC 2026 parent survey (86% family background and education); Jeevansathi 2025 (39% of women put compatibility first) |
| 5 | **The candidate pool is getting older and more varied.** The search now starts at a median age of 29 (was 27), and remarriage seekers are 16% of users (was 11%). | 1 platform dataset (10 years, 30,000+ surveyed), repeated by 4 outlets | Jeevansathi "The Big Shift", Feb 2026 |
| 6 | **Older users need larger text, bigger targets and a stable layout.** Users aged 65 and over complete 55% of tasks against 75% for younger users, and are 43% slower. | 3 NN/g studies (123 participants) plus 1 systematic review | NN/g 2013 and 2019/2020; PMC9376262 (2022) |
| 7 | **Explanations raise trust when acting on a suggestion is costly, and matrimony is costly.** Reciprocal ("why you'd suit each other") explanations beat one-sided ones for trust (3.38 vs 2.93, p ≤ 0.05) when acceptance carries emotional cost. | 4 research sources | Kleinerman, Rosenfeld & Kraus 2018 (287 participants); Herlocker et al. 2000; Tintarev & Masthoff 2012; Spotify 2025 and 2026 (descriptive shelf titles raised engagement in A/B tests) |
| 8 | **Locking basic replies behind a paywall, sales calls and hidden prices are what users call unfair.** Paying for extra capability is accepted. | 12 sales-pressure complaints, 6 paywalled-reply complaints; Shaadi and Jeevansathi hide prices until sign-in | Trustpilot; App Store Betterhalf ("interacting with incoming requests is hidden behind a paywall"); Shaadi and Jeevansathi plan pages; CCPA Dark Patterns Guidelines 2023 |
| 9 | **Verification is expected and is becoming mandatory.** 91% of women rated verified profiles highly important. Tinder made Face Check mandatory for new users in India. | 4 sources | Forbes India 2018 (Shaadi survey); Adgully Sept 2026 (Tinder India); Jeevansathi App Store (selfie verification); Jodii (government ID verified) |
| 10 | **Indian internet use is going vernacular, voice-led and AI-assisted, and daters want fewer, deeper connections.** | 4 sources | IAMAI-Kantar 2024 (98% use Indic content; 1 in 5 use voice) and 2025 (958M users; 44% use AI features); Match Group India, Sept 2026 (72% prefer fewer, deeper connections; 85% want long-term) |

---

## 2. Themes from real reviews (129 reviews, counts per theme)

A review can fall under more than one theme.

| Theme | Count | Share |
|---|---|---|
| Paid, then nothing: plan or assisted service not delivered, refund refused | 52 | 40% |
| Fake, inactive or scam profiles, often suspected to be planted | 34 | 26% |
| Irrelevant matches; preferences, location and filters ignored | 13 | 10% |
| Aggressive sales calls, forced upgrades | 12 | 9% |
| Account blocked or ID demanded without explanation | 11 | 9% |
| Off-platform scams or harassment by matches | 8 | 6% |
| Technical problems (OTP, login, photo quality) | 7 | 5% |
| Basic interaction behind a paywall (reply, read, chat) | 6 | 5% |
| Auto-renewal or overcharging (a subset of the first theme) | 5 | 4% |
| **Praise** (found a partner, free chat, serious intent, helpful support) | 7 | 5% |

### 2.1 Fake and planted profiles (34)
- "Most of the profiles are created by bharat matrimony itself, they are scammy!" (Trustpilot, BharatMatrimony, 2 Sep 2026)
- "Majority of accounts are dormant or abandoned. Clearly created by AI" (Trustpilot, BharatMatrimony, 3 Jun 2026)
- "bait you with fake matches that look real...once you buy premium...gone." (Trustpilot, Shaadi, 28 Nov 2025)
- "fake request...they fulfil the criteria...so they don't have to refund" (Trustpilot, Shaadi, 2 Sep 2025)
- "These profiles conveniently accept interests sent by users, which pushes customers into purchasing a membership." (App Store IN, BharatMatrimony)
- "Lots of fake and duplicate profiles created just to entice you to take premium membership" (App Store GB, BharatMatrimony, 1 Dec 2021)
- A Betterhalf reviewer suspects the app sends "fake likes to encourage you to buy premium." (App Store IN, Betterhalf)
- "The few people I do match with are bots programmed to get your WhatsApp number and then scam u" (App Store, Aisle, 17 Sep 2025)

### 2.2 Paid, then nothing (52)
- "I paid all amount but I can't see any contact details and I can't send massage" (Trustpilot, BharatMatrimony, 22 Jun 2026)
- "Exclusive membership RM service entirely useless—only sends weekly interests list; 12k wasted, no refund." (Trustpilot, Jeevansathi, 25 Sep 2025)
- "Even if you get VIP for which you need to pay 50k. You will get data from same database as other normal users." (App Store IN, Shaadi, 27 Dec 2023)
- "Once you get the assisted service there will be no follow up no calls and don't send profiles" (App Store GB, BharatMatrimony, 19 Oct 2022)
- "They took out 180 cad as auto renewal, we did not renew" (Trustpilot, BharatMatrimony, 8 Jul 2026)
- "Charged for membership renewal even though auto-renewal was off" (Trustpilot, BharatMatrimony, 1 Apr 2026)
- A Betterhalf reviewer says "the moment you pay for a subscription you basically get highlighted only for the first 24 hours" (App Store IN, Betterhalf)

### 2.3 Sales pressure (12) and paywalled replies (6)
- "As soon as registration is completed, they will force you for paid membership" (Trustpilot, BharatMatrimony, 12 Jan 2026)
- "keeps calling you multiple times a days, harassing you to take a paid subscription" (App Store, Betterhalf, 22 Mar 2022)
- "Basic functionality such as interacting with incoming requests is hidden behind a paywall" (App Store, Betterhalf, 28 Jun 2024)
- "You can't see any messages, connect or call anyone until you upgrade" (Trustpilot, BharatMatrimony, 25 May 2026)
- "they want me to pay to chat with the matches. Most free apps let you chat" (App Store, Betterhalf, 22 Sep 2024)

### 2.4 Irrelevant matches (13)
- "location preferences don't matter...I still get shown the girls in India" (App Store, Betterhalf, 31 Dec 2022)
- A Jeevansathi reviewer counts "less than 100 active profiles" in their smaller city (App Store IN, Jeevansathi)
- A Shaadi reviewer complains of the same faces every day and preferences ignored (Trustpilot, Shaadi, 14 Sep 2026)

### 2.5 Blocks and ID demands without explanation (11)
- A Jeevansathi reviewer says the app will "suddenly block your account for fake reasons and force you to provide sensitive documents" (App Store IN, Jeevansathi)
- "asked for a lot of documentation...Shocking service. Avoid at all cost." (Trustpilot, Shaadi, 6 Nov 2025)

### 2.6 What users praise (7)
- "I like the message service provided by jeevansathi its free and useful" (App Store IN, Jeevansathi)
- "People here have clear intentions of what they want" (App Store IN, Aisle)
- "Platform did its job well but we humans have become very choosy." (App Store IN, Hinge)
- "Tech team responded immediately within few hours and helped me out" (App Store GB, BharatMatrimony, 2 Apr 2019)
- A Jeevansathi reviewer found their soulmate there and calls it a decent app with many profiles and good filters (Trustpilot, Jeevansathi, 4 Jul 2025, 3 stars)

**Inference.** The anger is not about paying as such. It is about paying and then being unable to tell whether the other side is real, active and interested. Mangaly's answer is:
- make being real visible (verification layers);
- make activity visible, without view counts;
- never charge for the act of answering someone.

---

## 3. Parents versus candidates

### 3.1 Who the parents are, and how involved they are (evidence)
- **South India is the most parent-led region.** Shaadi's data shows 45–50% of accounts in South India are created by parents, against 25–30% elsewhere. 80–90% of well-educated South Indians surveyed wanted their parents involved even when they made the account themselves. ([ThePrint, 4 Sep 2022](https://theprint.in/feature/parents-no-longer-make-matrimonial-profiles-of-children-but-theres-a-north-south-divide/1109683/))
- **Self-made does not mean parent-free.** "Even if the profile is created by individuals...it gets managed by or is influenced by parents quite a bit." (Ekta Checker, Shaadi, in the same ThePrint article)
- **Self-managed profiles are rising, but parents still matter.** On Jeevansathi, self-managed profiles went from 67% to 77% (2016–2025) and family-managed from 33% to 23%. Yet 69% say parental involvement makes the process easier (75% of women), and siblings are more involved than parents in Tier 3 cities. ([Storyboard18, 12 Feb 2026](https://www.storyboard18.com/brand-marketing/remarriage-seekers-rise-43-over-10-years-in-india-jeevansathi-89517.htm); [Tribune, 13 Feb 2026](https://www.tribuneindia.com/news/business/marriage-timelines-shift-remarriage-rises-jeevansathi-report-reveals-how-india-is-redefining-partner-search-and-marriage/))
- **Women's profiles are far more often parent-run.** In a sample of 150,000 profiles, 57% of men's profiles were self-managed against 22% of women's. Tamil Brahmin profiles were 78% parent-managed. The highest parent share (55%) was among 26–30 year olds. ([Bharadwaj, 4 Mar 2021](https://priyankabharadwaj.substack.com/p/parent-tinder))
- **The family-led market is much bigger.** Betterhalf's founder acknowledged that the family-led matrimony market is "seven to eight times bigger" than Betterhalf's parent-free segment (reported in search summaries of his interviews; I could not read the original quote, so treat it as weak).
- **Parents act on the child's behalf.** A parent: "There are some suitable boys that I have picked, and I have sent interest to them. If they don't come back, I keep doing it for her, life goes on." ([ABC News, 1 Mar 2026](https://www.abc.net.au/news/2026-03-01/marriage-arranged-indian-astrology-dating-app-romance-love-match/106382436))

### 3.2 What parents screen for (evidence)
- **An ABC parent survey** (about 50 Indian-Australian respondents, small): 86% prioritised family background and education, 83% personality and values, 69% religion, 61% financial stability. ([ABC, 1 Mar 2026](https://www.abc.net.au/news/2026-03-01/marriage-arranged-indian-astrology-dating-app-romance-love-match/106382436))
- **Peer-reviewed, arranged-marriage context (Nepal):** parents and offspring diverged most on same caste or ethnicity (preferred more by parents) and physical attractiveness (preferred more by offspring). (Agey, Conroy-Beam & Gaulin, *Evolution and Human Behavior*, 2024, [doi 10.1016/j.evolhumbehav.2024.106612](https://www.sciencedirect.com/science/article/pii/S1090513824000886))
- **Cross-cultural review:** parents prefer social class, family background, ethnicity and education more than their children do. Children prefer attractiveness, humour and creativity more. (Buunk, Park & Dubbs 2008, [Review of General Psychology](https://journals.sagepub.com/doi/10.1037/1089-2680.12.1.47))
- **Horoscope can end a relationship.** The candidate's side on TeamBlind: a couple ended because "the horoscopes didn't match"; the poster asks "Why does horoscope matching matter so much to Indian parents?" ([TeamBlind, 9 Jun 2022](https://www.teamblind.com/post/why-does-horoscope-matching-matter-so-much-to-indian-parents-vakk0uap)). 44% of Indians believe in astrology (Pew, cited by [ABC 2026](https://www.abc.net.au/news/2026-03-01/marriage-arranged-indian-astrology-dating-app-romance-love-match/106382436)).
- **Verification:** 91% of women rated verified profiles highly important, and 82% said they would be more likely to make contact ([Forbes India, 17 May 2018](https://www.forbesindia.com/article/special/aadhaar-latest-tool-against-fake-matrimonial-profiles/50215/1)).
- **Parents' habits come from the paper biodata.** Shaadi runs a free [marriage biodata maker](https://www.shaadi.com/marriage-biodata-maker), which shows the biodata document is still the unit families trade.

### 3.3 What candidates look for (evidence)
- **Jeevansathi Modern Matchmaking Report 2025** (21,000+ respondents): 39% of women put compatibility first and 11% financial stability; 47% of men put love and romance first ([Deccan Chronicle](https://www.deccanchronicle.com/lifestyle/relationship/men-want-love-women-seek-compatibility-jeevansathis-modern-matchmaking-report-1861069); [Mediabrief](https://mediabrief.com/jeevansathis-modern-matchmaking-report-2025/)).
- **Jeevansathi 2026:** 90% say finding the "right person" matters more than age or income ([Tribune, 13 Feb 2026](https://www.tribuneindia.com/news/business/marriage-timelines-shift-remarriage-rises-jeevansathi-report-reveals-how-india-is-redefining-partner-search-and-marriage/)).
- **Match Group India, Sept 2026:** 72% prefer fewer, deeper connections; 64% of young singles prioritise emotional honesty; 60% want clearer statements of intent ([Adgully, 24 Sep 2026](https://www.adgully.com/post/21134/ai-authenticity-trust-anukool-kumar-on-how-tinder-is-building-the-next-dating-experience)).
- **Candidates' own words:**
  - "They treat me like a checklist, and I end up getting objectified during these interactions." (20-something woman, [ABC 2026](https://www.abc.net.au/news/2026-03-01/marriage-arranged-indian-astrology-dating-app-romance-love-match/106382436))
  - "I don't even know if my matches are actually interested in me because their family members are usually the ones operating the account." (Pratiksha Thayil, [The Walrus, 11 Feb 2025](https://thewalrus.ca/ai-arranged-marriage/))
  - "I am 25 and my parents have already created a Shaadi profile for me while I am still struggling to get a decent match on Hinge." ([TeamBlind](https://www.teamblind.com/post/hinge-vs-shaadi-hmjb4821))

### 3.4 How tastes differ by candidate age (evidence is thin; inference labelled)
- **Evidence:**
  - the search starts later (median 27 to 29; half begin at 29);
  - 78% intend to marry within six months once searching;
  - remarriage seekers rose from 11% to 16% of users;
  - 15% of the interest divorced profiles receive comes from never-married users;
  - one in six Jeevansathi success stories is a second marriage.

  (All [Jeevansathi, Feb 2026](https://www.storyboard18.com/brand-marketing/remarriage-seekers-rise-43-over-10-years-in-india-jeevansathi-89517.htm).) The same period saw dedicated remarriage apps appear (SecondSutra, Second Shaadi, Divorcee Matrimony; [App Store](https://apps.apple.com/us/app/secondsutra-matrimony/id6747257823)). Parents are most involved at ages 26–30 ([Bharadwaj 2021](https://priyankabharadwaj.substack.com/p/parent-tinder)).
- **Inference, early 20s:** parent-led, and horoscope-heavy in South India. The candidate wants photos and prompts but often defers to the family.
- **Inference, late 20s to mid 30s:** the typical Mangaly candidate. Self-driven, under time pressure (78% want to marry within six months), and wants fewer, better introductions.
- **Inference, remarriage and 35+:** the candidate is the decider. Parents, if present, are advisers. These members need respectful handling of marital status and children, and no "first marriage" assumptions in copy.

I found no Indian survey that splits partner preferences by age band. Do not treat these age-band notes as measured.

### 3.5 What this means for a seat-adapted Home (inference, decided)

**Rule check.** The owner rule says role changes only the profile-viewing style and messaging. A Home that changes **order, density and type size by seat, while every capability stays reachable from both seats**, is a viewing-style difference and stays within the rule.

**Tension to watch.** Hiding a capability from the parent seat would break the rule. Today the matchmaker brief and the profile-strength tile do not render in a family seat (`app/page.tsx`, the `!forId` guards). The brief is described as the family's own words (DEC-V1-031), yet a parent in the candidate's seat cannot see it on Home. That is capability gating dressed as layout. Recommendation R6 fixes it.

**Also decided.** Adapt by the seat, which is the relationship, never by the person's age. A 62-year-old remarrying candidate gets the candidate seat, with the large-type option they choose.

---

## 4. Home and "because" rows

### 4.1 Evidence
- **Explanations increase acceptance.** Herlocker, Konstan and Riedl (CSCW 2000) presented "experimental evidence that shows that providing explanations can improve the acceptance of ACF systems", and noted that recommenders "have yet to be successful in content domains where higher risk is associated with accepting" a recommendation ([abstract](https://experts.umn.edu/en/publications/explaining-collaborative-filtering-recommendations/)).
- **Reciprocal reasons win in matching.** In online-dating matching (287 participants), when acceptance carries significant monetary or emotional cost, reciprocal explanations (why each would suit the other) beat one-sided explanations; when the cost was negligible, one-sided explanations did better. Trust was 3.38 vs 2.93, p ≤ 0.05. ([Kleinerman, Rosenfeld & Kraus 2018, arXiv 1807.01227](https://arxiv.org/abs/1807.01227))
- **Explanations can backfire.** Explanations serve seven aims: transparency, scrutability, trust, effectiveness, persuasiveness, efficiency and satisfaction. These can conflict: persuasion can reduce effectiveness, and transparency can lower trust ([Tintarev & Masthoff 2012](https://link.springer.com/article/10.1007/s11257-011-9117-5)).
- **Spotify shelf titles are "a promise".** Spotify's descriptive shelves ("Uplifting Women's Fiction") improved engagement and discovery in A/B tests ([ECIR 2025](https://research.atspotify.com/publications/Contextualizing-Spotifys-Audiobook-List-Recommendations-with-Descriptive-Shelves)). Its hypothesis-driven shelves treat the title as "a promise about why the items belong together". Results were +36% relative engagement for albums, +2% for episodes, and −41% for shows. ([Petrov et al., RecSys 2026](https://arxiv.org/html/2607.25823v1))

  **Inference:** a "because" title helps only when its promise holds.
- **Netflix labels its rows.** It labels personalisation rows ("Because you watched…") to disclose the reasoning ([New America case study](https://www.newamerica.org/oti/reports/why-am-i-seeing-this/case-study-netflix/)). A 12-interview study found high reliance on these lists, and frustration when they miss ([Springer 2024](https://link.springer.com/article/10.1007/s12646-024-00807-0)).
- **Cited reasons can inflate trust.** NN/g (Dec 2025): users "may place undeserved trust" in answers that cite sources. One participant who praised the citations "never clicked on any of the citations" ([NN/g](https://www.nngroup.com/articles/explainable-ai/)).

  **Inference:** a reason must be a checkable fact. Mangaly's DEC-V1-022 rule ("a fact both people can check… never a score") matches this evidence.
- **A note on figures I rejected.** Some search summaries attributed figures such as "63% of users" to NN/g. The NN/g article contains no such figures, so they are not used.

### 4.2 Decision for Mangaly (inference, decided)
The owner's rule is that Home is not Discover, and Discover's "For you" rows already exist (DEC-V1-022). So:

1. **The "because" rows live on Discover, not Home.** Add rows there driven by the family's own actions:
   - "Because you saved Divya": similar biodata, excluding people already in progress;
   - "Because your mother suggested Arjun": similar to the family's picks;
   - "Because you asked for: vegetarian, Hyderabad, Telugu": straight from the matchmaker brief, and more convincing than "Picked for you";
   - "Horoscope matches for Kavya": the Guna Milan or Porutham threshold met, with no numeric score word beyond the published guna count the product already shows.

   Each row title must be literally true for every face in it (the Spotify "promise" finding).
2. **On Home, "because" is a line on each desk item, not a row.** Each thing waiting on the family carries its reason:
   - the daily introduction: "Why today: you both speak Telugu · both want to live near family · 27 of 36 gunas";
   - a request: "Sent by Lakshmi, Ananya's mother · waiting 3 days";
   - a family pick: "Suggested by your father".

   Use **reciprocal** reasons for the introduction ("what she is looking for that Kavya has" plus "what Kavya asked for that he has"), because acceptance is costly (Kleinerman 2018). This works within FR020: the other side's values and misses stay private, and only the topics the reader meets are named. The "How you fit each other" panel already does this.
3. **No score, no percentage, no "7/10".** This is already decided in DEC-V1-031.

---

## 5. Premium tiers: what to show, what never to do

### 5.1 Verified prices (INR, as listed on the App Store India pages, September 2026)

| App | Tier and price as listed | What paying unlocks (verified on the product) |
|---|---|---|
| Shaadi.com | 3 months Gold ₹5,200; Gold+ ₹5,900; 6 months Diamond ₹6,900 ([App Store IN](https://apps.apple.com/in/app/shaadi-com-matrimony-app/id480093204)) | Free members can express interest. Premium members can "Connect directly… over Phone, Email or SMS", "Initiate Unlimited Chats", and (Premium Plus) Bold Listing and Spotlight. Prices are not shown on the public plans page. ([Shaadi FAQ](https://www.shaadi.com/info/customer-relations/faq/membership)) |
| BharatMatrimony | Gold 3 months ₹5,900; Prime Gold ₹7,900; Diamond ₹7,900; Platinum ₹9,900; Profile Highlighter 15 days ₹450 ([App Store IN](https://apps.apple.com/in/app/bharat-matrimony-shaadi-app/id465923141)) | Contact views are capped by tier. A reviewer asks why "you can contact with only 40 people even after membership". |
| Jeevansathi | Pro Lite ₹1,699–4,249; Pro ₹2,149–5,199; Pro Max ₹2,450–5,999; Spotlight ₹499; Super Interest ₹599 ([App Store IN](https://apps.apple.com/in/app/jeevansathi-com-matrimony-app/id969994186)) | Chat is free, and reviewers praise it. Paid tiers add contact views (20), more daily matches, calling, spotlights and a relationship manager. Prices are masked "₹ ****" until sign-in ([plans page](https://www.jeevansathi.com/m0/membership/jspc)). |
| Betterhalf | ₹499–4,399 ([App Store IN](https://apps.apple.com/in/app/betterhalf-matrimony-app/id1438203766)) | Reviewers say replying to incoming requests and chatting need a paid plan. |
| Aisle | Plus ₹249; Premium ₹399–1,899; Concierge ₹749–1,499 ([App Store IN](https://apps.apple.com/in/app/aisle-indian-dating-app/id1001481078)) | Connections and premium features. |
| Hinge | Hinge+ ₹499–1,699; HingeX ₹749–2,499; 3 roses ₹999 ([App Store IN](https://apps.apple.com/in/app/hinge-dating-app-match-date/id595287172)) | Unlimited likes, filters, priority. |
| **Mangaly (config)** | Gold ₹2,499 (3 months), ₹3,999 (6), ₹5,999 (12); Assisted ₹19,999 (6), ₹29,999 (12); GST shown separately (`app/config/plans.py`) | Unlimited requests (free: 3 a day), contact request, full kundli report, Assisted relationship manager. Also "see who shortlisted you" and "see who viewed you". |

**Context.** Matrimony.com's average transaction value was about ₹4,488 in one FY25 quarter, and paid subscriptions fell 7.5% year on year ([Storyboard18](https://www.storyboard18.com/advertising/matrimony-com-cuts-ad-spend-by-1-07-amid-fy25-revenue-profit-decline-75089.htm); [Medianama](https://www.medianama.com/2025/02/223-matrimony-dot-com-q3fy25-earnings-call-highlights/)). Mangaly Gold sits well below the incumbents' 3-month prices and above dating apps. **Inference:** that positioning is sound.

### 5.2 What users accept versus what they call unfair (evidence plus Indian regulation)
- **Accepted** (praise or no complaint):
  - free messaging (Jeevansathi praised);
  - paying for extra reach or a human service, when it delivers;
  - Hinge-style paid convenience.
- **Unfair:**
  - replying or reading locked behind payment (6 reviews);
  - assisted or VIP services with no measurable commitment (the largest share of the 52 "paid, then nothing" reviews);
  - auto-renewal surprises (5);
  - sales calls (12);
  - suspected fake engagement to push upgrades (see 2.1).
- **Law:** the CCPA Guidelines for Prevention and Regulation of Dark Patterns (30 Nov 2023) list 13 patterns, including *subscription trap*, *nagging*, *drip pricing*, *false urgency*, *bait and switch* and *confirm shaming* ([Fox Mandal summary](https://foxmandal.in/News/consumer-body-notifies-guidelines-on-dark-patterns/)). RBI's e-mandate rules require a pre-debit notice at least 24 hours before a recurring charge, with an option to cancel from the alert ([Business Today, Apr 2026](https://www.businesstoday.in/personal-finance/banking/story/now-control-your-auto-debit-payments-rbis-new-rules-explained-526860-2026-04-22)).

### 5.3 Where plans belong on Home (decided)
- **Never on Home as a banner or card.** Home is the family's desk. Evidence: sales pressure is a top complaint, and "nagging" is a named dark pattern.
- **Where plans do appear:**
  - in place, at the refused action: the existing `UpgradeNudge`, "one quiet card… never a modal", is the right pattern;
  - one line under Account or Me, "Your plan: Free · See plans".
- **Assisted is a human service.** Sell it only with published commitments (for example, introductions per month and a callback time) and a pro-rated refund if they are missed. **Inference** from the review data: without this, Assisted will draw the same anger as Shaadi VIP, BharatMatrimony Assisted and Jeevansathi Exclusive.

### 5.4 Contradictions and a bug found in the code (flagged)
1. **Tension with recorded decisions:** `plans.py` sells `SEE_WHO_VIEWED_YOU` and `SEE_WHO_SHORTLISTED_YOU`. The FR at line 997 says the system "shall never display profile-view counts… or any popularity/demand indicator, to any viewer including the profile owner". DEC-V1-021 "deliberately has no visitor or view lists". Selling access to who viewed you contradicts both. **Decision:** remove both flags from Gold and Assisted, and drop them from marketing copy.
2. **Bug:** `UpgradeNudge` links to `/plans?plan=…`, but `mangaly-web/app/plans/` contains only `plans.css` and no `page.tsx`. Unless another session is building it now, the upgrade path ends on a 404.
3. **Keep as is:** "No plan ever buys VISIBILITY" (the `plans.py` header). This matches the Betterhalf complaint that paid visibility fades after 24 hours, and avoids it.

---

## 6. Trends to about 2030 (data first, then the extrapolation)

| Trend | Measured data (source) | Extrapolation to ~2030 (inference) |
|---|---|---|
| Internet users | 886M active in 2024 (+8%), 958M in 2025 (+8%); rural 57% ([IAMAI-Kantar 2024 via Medianama](https://www.medianama.com/2025/01/223-rural-adoption-ai-india-internet-2024-kantar-iamai-report/); [2025 via BestMediaInfo, 30 Jan 2026](https://bestmediainfo.com/insights/indias-internet-users-near-one-billion-in-2025-rural-india-leads-growth-iamai-11056899)) | Growth must slow as saturation nears (579M still offline in 2025). At 4–6% a year, about 1.15–1.3B users by 2030, mostly rural and non-English-first. |
| Vernacular | 98% of users access Indic-language content; Tamil, Telugu and Malayalam lead; 57% of urban users prefer regional languages (IAMAI 2024, [Entrepreneur](https://india.entrepreneur.com/news-and-trends/internet-users-in-india-set-to-cross-900-mn-led-by-indic/485634)). Jodii runs in 10 languages for non-graduates ([Matrimony.com](https://www.matrimony.com/product/bharatjodii)). | Telugu and Hindi are the default for a large share of parents, not an add-on. Every screen, notification and AI reply must work in them (already a ForKhatri rule). |
| Voice and AI | 1 in 5 users used voice (2024). 44% used AI features in 2025: 57% of 15–24 year olds and 52% of 25–44 year olds (IAMAI 2025) | Today's 15–24 year olds are Mangaly's 2030 candidates, so AI-mediated search will be normal for them. Parents (45+) were not reported. Voice input and read-aloud are the bridge for them. |
| Older users online | Mobile phones in 93.6% (urban) and 84.1% (rural) of households aged 45+ (LASI); only 13% of Indians aged 60+ have ever used the internet (NITI Aayog 2024) ([ORF, 25 Feb 2026](https://www.orfonline.org/expert-speak/screen-time-may-be-rising-steadily-among-older-indians)) | Parents of 2030 candidates will be about 50–68. The 50s group is largely online; the 60s group less so. Design for a capable but visually older reader, with a relative helping sometimes. |
| Family involvement | Family-managed profiles 33% to 23% over 2016–2025 (about −1.1 points a year); 69% still value parental involvement (Jeevansathi 2026). South India 45–50% parent-created (Shaadi 2022). | If linear, about 17–18% family-managed on Jeevansathi by 2030. Parents move from operating the profile to co-piloting it, which is what the Home Circle already models. |
| Caste filters | Strict caste preference 91% to 54% over 2016–2025 (about −4 points a year); 49% in metros | If the trend holds, about 35–40% by 2030. "Same roots" should stay a preference with an importance weight, never a default wall. |
| Age and remarriage | Median search start 27 to 29; remarriage seekers 11% to 16% (+43%) over 2016–2025 | About 30 median start and about 18–19% remarriage seekers by 2030. Life-stage-aware copy and fields become core, not an edge case. |
| Payments | UPI 24.51B transactions in Aug 2026, +22% year on year ([Business Standard, 1 Sep 2026](https://www.business-standard.com/finance/news/upi-transactions-august-2026-record-volume-npci-126090100506_1.html)); RBI e-mandate rules | UPI (and UPI Autopay with pre-debit notice) is the default way to pay. Auto-renewal must be explicit and cancellable in one step. |
| Verification | 91% of women value verified profiles (2018); Tinder made Face Check mandatory for new users in India (2026); Jeevansathi offers selfie verification | Verified-by-default is table stakes by 2030. Showing when each check was done (Mangaly already shows "Photos confirmed · Sep 2026") is how to stand out. |
| AI matchmakers and calm | Hinge's AI recommendations: "double-digit increase in matches" ([Hinge, 10 Nov 2025](https://hinge.co/newsroom/hinge-2025-product-evolution)). Sitch sends 3–5 curated setups a week ([CNBC, 7 Aug 2025](https://www.cnbc.com/2025/08/07/30-year-old-founder-is-using-ai-to-help-singles-find-love.html)). Match Group India: AI for matching and fake detection, "but not to write messages or decide whom users should date"; 72% want fewer, deeper connections (Sept 2026). US: 78% report dating-app burnout ([Forbes Health 2024](https://www.forbes.com/health/dating/dating-app-fatigue/)). Hinge's Your Turn Limits cut ghosting by 25% in tests ([Hinge newsroom](https://hinge.co/newsroom/your-turn-limits-test)). | The winning pattern is a few explained introductions plus a matchmaker you talk to, with no swipe feed or streaks. This is consistent with Mangaly's daily introduction and AI brief. |
| Privacy law | DPDP Rules notified 13 Nov 2025; most data-fiduciary duties apply after 18 months, around May 2027 ([PIB](https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/nov/doc20251117695301.pdf)) | By 2030, DPDP is fully enforced: itemised consent, purpose-bound retention and 72-hour breach notice. Photo and horoscope privacy controls are compliance, not polish. |

**Accessibility evidence behind the parent seat:**
- NN/g: users 65+ complete 55.3% of tasks against 74.5% for younger users, are 43% slower, and "blamed themselves for problems 90% of the time" ([NN/g 2013](https://www.nngroup.com/articles/usability-seniors-improvements/)).
- Small type remains "an issue for seniors throughout all our studies", and older users "make more mistakes" ([NN/g](https://www.nngroup.com/articles/usability-for-senior-citizens/)).
- Recommendations: at least 12-point default text, a way to increase text size, stable navigation, no moving controls.
- Touch targets of at least 1 cm × 1 cm ([NN/g, 2019](https://www.nngroup.com/articles/touch-target-size/)).
- A systematic review: 13–14.5 pt for intensive reading on smartphones (ages 57–70) and 14–22 pt on tablets (ages 60–89) ([PMC9376262](https://pmc.ncbi.nlm.nih.gov/articles/PMC9376262/)).
- **Mangaly today:** `home.css` has about 21 font sizes of 0.625–0.75rem (10–12px), often uppercase and letter-spaced in muted ink, and 136 such declarations across the app's CSS. There is no text-size setting.

---

## 7. Ranked recommendations for Mangaly

Scores are 1–10 (higher is better). Ease = how easy to build. Helpfulness = value to families. Modernity = fit with the 2030 direction.

| Rank | Recommendation | Evidence | Built? (code checked) | Effort | Ease | Helpful | Modern |
|---|---|---|---|---|---|---|---|
| 1 | **Seat-adapted Home (order and density by relationship seat, same capabilities).** *Parent seat:* (1) Your turn: requests to decide, each with "sent by" and wait time; (2) today's introduction led by biodata facts (age, education, work, city, roots), the Guna/Porutham line and verification layers; (3) where the search stands: waiting, connected, family picks; (4) the candidate's brief (see R6); (5) Circle; (6) kundli tool. Hide: profile-strength ring (not theirs), candidate prompts. *Candidate seat:* (1) Your turn plus unread chats; (2) today's introduction led by photo, shared interests and one published prompt, with reciprocal reasons; (3) search status; (4) matchmaker brief and profile strength; (5) Circle. *Remarriage or 35+ candidate:* same candidate seat, copy with no first-marriage assumptions. | §3 (4 sources on differing priorities; 5 on South Indian parent involvement) | **Partly.** Seat switching exists (`useActiveContext`, `forId`); Home renames things for the seat. Content order is the same for both seats, and there are no parent-first biodata facts. | M | 7 | 9 | 8 |
| 2 | **Readable by default, plus an "Aa" text-size control** (Standard / Larger / Largest), saved per account and offered in the parent seat on first visit. Minimum 16px body and 14px secondary; no 10–11px uppercase labels; targets at least 44–48px; stable navigation. | NN/g seniors studies, touch targets, PMC9376262 | **No.** 136 small font declarations; no setting. | M | 6 | 9 | 7 |
| 3 | **Fix billing contradictions and the missing page:** remove "who viewed you" and "who shortlisted you"; build `/plans`; public prices with GST; replying, accepting and reading messages always free; UPI Autopay only with explicit opt-in, a 24-hour pre-debit notice and one-tap cancel. | §5.2, §5.4; CCPA 2023; RBI | **Partly.** `cancel_auto_renew` exists; the viewed and shortlisted flags are sold; `/plans` has no page. | S–M | 8 | 9 | 7 |
| 4 | **"Because" line on every Home item; reciprocal reasons on the introduction.** | Kleinerman 2018; Herlocker 2000; Tintarev & Masthoff 2012 | **Partly.** The intro shows "why" (reason plus up to 3 common points); family picks show "Suggested by". Reciprocal wording and request wait time are missing. | S | 9 | 8 | 8 |
| 5 | **Action-driven "because" rows on Discover:** "Because you saved…", "Because your mother suggested…", "Because you asked for…" (from the brief), "Horoscope matches for {name}". Every face must satisfy the title. | Spotify 2025 and 2026; Netflix | **Partly.** DEC-V1-022 rows exist ("Suggested by your family", "Same roots" and others); rows driven by saves, the brief or horoscope do not. | M | 6 | 8 | 9 |
| 6 | **Parents see and add to the candidate's brief.** In the family seat, show the candidate's brief read-only and let a parent add "Family hopes" points with importance, labelled by relation. The candidate sees them and decides whether they enter matching. | 69% value parental involvement; DEC-V1-031 says the brief is the family's own words. Removes the capability-gating tension in §3.5. | **No.** The matchmaker tile is hidden when `forId` is set; `/me/matchmaker` covers only the member's own profile. | M | 5 | 8 | 9 |
| 7 | **Trust surfaced where decisions happen:** verification layers with their month on every Home face and at the top of the parent biodata lens; "Sent by Lakshmi, Ananya's mother" on every request, and the writer's relation on direct messages. Show an honest last-active range ("Active this week"), never counts. | 34 fake-profile complaints; 91% of women value verification; Walrus quote on not knowing who operates the account | **Partly.** Verification seals are on Discover tiles and the profile; `sent_by_label` is on requests. Not on Home faces; no activity signal. | S | 8 | 9 | 7 |
| 8 | **Voice and read-aloud for elders:** extend the existing `VoiceInput` beyond the matchmaker to messages, family notes and replies to requests; add read-aloud of a biodata in English, Hindi and Telugu (browser speech synthesis). | IAMAI (1 in 5 use voice; 98% Indic) | **Partly.** `VoiceInput` is on `/me/matchmaker` only; `VoiceIntro` exists for candidate voice prompts. | M | 6 | 7 | 9 |
| 9 | **Publish Assisted commitments** (introductions per month, callback time, named relationship manager), with a pro-rated refund if missed; no outbound sales calls ever. | 52 "paid, then nothing" reviews, largely about VIP, Assisted and Exclusive; 12 sales-call reviews | **No.** The Assisted plan exists in config and the RM console exists (`/rm`); no commitments are defined. | S (policy) plus S (UI) | 8 | 8 | 6 |
| 10 | **Calm pacing:** one daily introduction; when 5 or more requests wait on the family, a quiet Your Turn prompt to answer before sending more (Hinge-style); no streaks, badges or counters. | Hinge Your Turn Limits (−25% ghosting); 72% want fewer, deeper connections; burnout 78% (US) | **Partly.** The daily intro and Your turn exist; there is no waiting-requests prompt. The free tier's 3 requests a day already paces sending. | S | 8 | 7 | 8 |
| 11 | **Shareable biodata card** (formal fields only, watermarked "Shared from Mangaly", never contact details) for the member's own or their child's profile, so families can send it to relatives on WhatsApp as they already do. Another person's biodata is shareable only after connection, only to the member's own Home Circle, and only in the fields that person published. | Shaadi's biodata maker shows the habit | **No.** No print, share or PDF code found. | M | 6 | 7 | 6 |
| 12 | **Life-stage fields and copy for remarriage** (marital history, children, living with them; plus a "Open to someone with children" wish in the brief), handled without stigma. Remarriage members get the same features, with no separate "divorcee" area. | Remarriage 16% and rising; dedicated remarriage apps appearing | **Unverified.** I did not audit the marital-status fields in this run. | S–M | 7 | 7 | 7 |

**Not recommended, with reasons:**
- **Plan banners on Home:** sales pressure is a top complaint, and nagging is a named dark pattern.
- **Any paid visibility boost:** it breaks the `plans.py` rule and draws the Betterhalf "visibility drops after 24 hours" complaint.
- **Numeric match scores or percentages:** owner decision DEC-V1-031, and research on displayed scores steering behaviour.
- **Gamified streaks:** conflict with the calm design bar and with the "fewer, deeper" preference.
- **An age-based UI switch:** adapt by seat plus the user's own text-size choice, never by birth year.

---

## 8. All sources

**Reviews**
- Trustpilot, Shaadi.com, page 1 (Jul–Sep 2026) and page 5 (Aug–Nov 2025): https://www.trustpilot.com/review/shaadi.com ; https://www.trustpilot.com/review/shaadi.com?page=5
- Trustpilot, BharatMatrimony (Jan–Sep 2026): https://www.trustpilot.com/review/bharatmatrimony.com
- Trustpilot, Jeevansathi (Jul 2025–Sep 2026): https://www.trustpilot.com/review/jeevansathi.com
- App Store IN, Shaadi.com (4.3, 126K ratings; plan prices): https://apps.apple.com/in/app/shaadi-com-matrimony-app/id480093204
- App Store GB, BharatMatrimony reviews: https://apps.apple.com/gb/app/465923141?see-all=reviews&platform=iphone
- App Store IN, BharatMatrimony (4.1; plan prices): https://apps.apple.com/in/app/bharat-matrimony-shaadi-app/id465923141
- App Store IN, Jeevansathi (4.4, 54K; plan prices): https://apps.apple.com/in/app/jeevansathi-com-matrimony-app/id969994186
- App Store US, Aisle reviews: https://apps.apple.com/us/app/aisle-indian-dating-app/id1001481078?see-all=reviews&platform=iphone
- App Store IN, Aisle (plan prices): https://apps.apple.com/in/app/aisle-indian-dating-app/id1001481078
- App Store US, Betterhalf reviews: https://apps.apple.com/us/app/betterhalf-matrimony-app/id1438203766?see-all=reviews&platform=iphone
- App Store IN, Betterhalf (plan prices): https://apps.apple.com/in/app/betterhalf-matrimony-app/id1438203766
- App Store IN, Hinge (plan prices): https://apps.apple.com/in/app/hinge-dating-app-match-date/id595287172
- TeamBlind, horoscope thread (9 Jun 2022): https://www.teamblind.com/post/why-does-horoscope-matching-matter-so-much-to-indian-parents-vakk0uap
- TeamBlind, "Hinge vs Shaadi": https://www.teamblind.com/post/hinge-vs-shaadi-hmjb4821

**Surveys, reports, filings, press**
- Jeevansathi "The Big Shift" (Feb 2026), via Storyboard18 (12 Feb 2026): https://www.storyboard18.com/brand-marketing/remarriage-seekers-rise-43-over-10-years-in-india-jeevansathi-89517.htm ; Tribune (13 Feb 2026): https://www.tribuneindia.com/news/business/marriage-timelines-shift-remarriage-rises-jeevansathi-report-reveals-how-india-is-redefining-partner-search-and-marriage/ and https://www.tribuneindia.com/news/top-headlines/marriage-median-age-rises-to-29-remarriage-seekers-up-43-per-cent-in-last-decade-report/
- Jeevansathi Modern Matchmaking Report 2025: https://www.deccanchronicle.com/lifestyle/relationship/men-want-love-women-seek-compatibility-jeevansathis-modern-matchmaking-report-1861069 ; https://mediabrief.com/jeevansathis-modern-matchmaking-report-2025/
- ThePrint, profile creation north–south divide (4 Sep 2022): https://theprint.in/feature/parents-no-longer-make-matrimonial-profiles-of-children-but-theres-a-north-south-divide/1109683/
- ThePrint opinion, Gen Z and parents (11 Aug 2024): https://theprint.in/opinion/the-dating-story/gen-z-is-giving-up-on-dating-apps-turning-to-parents-shaadi-com-linkedin/2218386/
- Bharadwaj, "Parent-Tinder" (4 Mar 2021): https://priyankabharadwaj.substack.com/p/parent-tinder
- The Walrus, AI arranged marriage (11 Feb 2025): https://thewalrus.ca/ai-arranged-marriage/
- ABC News, arranged marriage and astrology (1 Mar 2026): https://www.abc.net.au/news/2026-03-01/marriage-arranged-indian-astrology-dating-app-romance-love-match/106382436
- Shaadi.com annual survey (7 Jul 2011, dated): https://blog.shaadi.com/annual-survey-shades-of-shaadi/
- Forbes India, Aadhaar verification (17 May 2018): https://www.forbesindia.com/article/special/aadhaar-latest-tool-against-fake-matrimonial-profiles/50215/1
- Shaadi membership FAQ: https://www.shaadi.com/info/customer-relations/faq/membership ; plans page: https://www.shaadi.com/info/introduction/membership-plans ; biodata maker: https://www.shaadi.com/marriage-biodata-maker
- Jeevansathi plans page: https://www.jeevansathi.com/m0/membership/jspc
- Matrimony.com, BharatJodii: https://www.matrimony.com/product/bharatjodii
- Matrimony.com FY25: https://www.storyboard18.com/advertising/matrimony-com-cuts-ad-spend-by-1-07-amid-fy25-revenue-profit-decline-75089.htm ; Q3 FY25 call: https://www.medianama.com/2025/02/223-matrimony-dot-com-q3fy25-earnings-call-highlights/
- Betterhalf founder interview (CXOToday): https://cxotoday.com/corner-office/betterhalf-connects-the-hearts-of-new-age-couples-with-advanced-technology-and-zero-involvement-of-parents-in-the-initial-stage/
- Match Group India survey and Tinder Face Check (24 Sep 2026): https://www.adgully.com/post/21134/ai-authenticity-trust-anukool-kumar-on-how-tinder-is-building-the-next-dating-experience ; https://onlinepersonalswatch.com/2026/09/match-group-survey-finds-89-of-indian-gen-z-want-long-term-relationships/
- Hinge 2025 product evolution (10 Nov 2025): https://hinge.co/newsroom/hinge-2025-product-evolution ; Your Turn Limits: https://hinge.co/newsroom/your-turn-limits-test
- Sitch (CNBC, 7 Aug 2025): https://www.cnbc.com/2025/08/07/30-year-old-founder-is-using-ai-to-help-singles-find-love.html
- Forbes Health dating-app burnout (2024): https://www.forbes.com/health/dating/dating-app-fatigue/
- IAMAI-Kantar Internet in India 2024: https://www.medianama.com/2025/01/223-rural-adoption-ai-india-internet-2024-kantar-iamai-report/ ; https://india.entrepreneur.com/news-and-trends/internet-users-in-india-set-to-cross-900-mn-led-by-indic/485634 ; report PDF: https://www.iamai.in/sites/default/files/research/Kantar_%20IAMAI%20report_2024_.pdf
- IAMAI-Kantar 2025 (30 Jan 2026): https://bestmediainfo.com/insights/indias-internet-users-near-one-billion-in-2025-rural-india-leads-growth-iamai-11056899
- ORF, older Indians' screen time (25 Feb 2026): https://www.orfonline.org/expert-speak/screen-time-may-be-rising-steadily-among-older-indians
- UPI August 2026 (1 Sep 2026): https://www.business-standard.com/finance/news/upi-transactions-august-2026-record-volume-npci-126090100506_1.html
- CCPA Dark Patterns Guidelines 2023: https://foxmandal.in/News/consumer-body-notifies-guidelines-on-dark-patterns/
- RBI e-mandate rules (Apr 2026): https://www.businesstoday.in/personal-finance/banking/story/now-control-your-auto-debit-payments-rbis-new-rules-explained-526860-2026-04-22
- DPDP Rules 2025 (PIB, 17 Nov 2025): https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/nov/doc20251117695301.pdf
- SecondSutra (App Store): https://apps.apple.com/us/app/secondsutra-matrimony/id6747257823

**Peer-reviewed and industry UX research**
- Herlocker, Konstan & Riedl, CSCW 2000: https://experts.umn.edu/en/publications/explaining-collaborative-filtering-recommendations/
- Kleinerman, Rosenfeld & Kraus 2018, reciprocal explanations: https://arxiv.org/abs/1807.01227
- Tintarev & Masthoff 2012: https://link.springer.com/article/10.1007/s11257-011-9117-5
- Spotify descriptive shelves, ECIR 2025: https://research.atspotify.com/publications/Contextualizing-Spotifys-Audiobook-List-Recommendations-with-Descriptive-Shelves
- Spotify hypothesis-driven shelves, RecSys 2026: https://arxiv.org/html/2607.25823v1
- New America, Netflix case study: https://www.newamerica.org/oti/reports/why-am-i-seeing-this/case-study-netflix/
- Netflix choice overload interviews (Springer 2024): https://link.springer.com/article/10.1007/s12646-024-00807-0
- NN/g, Explainable AI in chat interfaces (12 Dec 2025): https://www.nngroup.com/articles/explainable-ai/
- NN/g, Usability for Senior Citizens (28 May 2013): https://www.nngroup.com/articles/usability-seniors-improvements/
- NN/g, Usability for Older Adults: https://www.nngroup.com/articles/usability-for-senior-citizens/
- NN/g, Touch Target Size (5 May 2019): https://www.nngroup.com/articles/touch-target-size/
- Font size for older adults, systematic review (2022): https://pmc.ncbi.nlm.nih.gov/articles/PMC9376262/
- Agey, Conroy-Beam & Gaulin 2024, Evolution and Human Behavior: https://www.sciencedirect.com/science/article/pii/S1090513824000886
- Agey et al. 2023, Evolutionary Human Sciences: https://www.cambridge.org/core/journals/evolutionary-human-sciences/article/socioeconomic-benefits-and-limited-parentoffspring-disagreement-in-arranged-marriages-in-nepal/24E4903DDFA4A5EAE041F9E32FCC0EDA
- Buunk, Park & Dubbs 2008: https://journals.sagepub.com/doi/10.1037/1089-2680.12.1.47

**Code checked (Mangaly repository)**
- `modules/MOD03-mangaly/mangaly-web/app/page.tsx` (Home)
- `modules/MOD03-mangaly/mangaly-web/app/home.css`
- `modules/MOD03-mangaly/mangaly-web/components/UpgradeNudge.tsx`
- `modules/MOD03-mangaly/mangaly-web/app/plans/` (CSS only)
- `modules/MOD03-mangaly/mangaly-web/components/VoiceInput.tsx`
- `modules/MOD03-mangaly/mangaly-web/app/me/matchmaker/page.tsx`
- `modules/MOD03-mangaly/mangaly-service/app/config/plans.py`
- `modules/MOD03-mangaly/mangaly-service/app/components/billing/interface.py`
- `modules/MOD03-mangaly/02-functional-requirements.md` (line 997)
- `modules/MOD03-mangaly/v1-decisions.md` (DEC-V1-018 to 031)

---
doc: Behaviour research and improvement roadmap
module: MOD02 Milavn
date: 2026-09-15
status: Working record (Step 9, autonomous) — every item below is either built and recorded in 09-implementation.md or listed as next/blocked
owner: krishna kategaru
---

# Milavn behaviour research — how to become the best meetup app for our community

The owner asked for "rigorous research on how Milavn can behave more logically and make more sense to people, reading research papers, innovations, blogs and ideas, so it becomes the best meetup app for my community." Five research tracks ran in parallel on 2026-09-15. Each track cited only sources it opened or found in search results, and marked what it could not verify. This page keeps the findings that changed a decision, the product behaviours they lead to, and the order we are building them in.

**How to read the evidence tags:** **strong** = meta-analysis, large field experiment or randomised trial · **moderate** = solid observational study, small experiment, or credible industry data · **weak** = practitioner reports, theory, ethnography.

---

## 1. What the research says, in one page

1. **Friendships come from repeated time together, not one big event.** About 50 hours turns an acquaintance into a casual friend, about 90 into a friend (Hall 2019, *JSPR*, moderate). Repeated exposure and nearness make people like each other even without talking (Festinger et al. 1950; Moreland & Beach 1992; Reis et al. 2011, strong). → Favour recurring activities and familiar faces; make "do it again" effortless.
2. **People underestimate how much others liked them** (Boothby et al. 2018, *Psych Science*, strong) **and how much thanks is worth** (Kumar & Epley 2018, strong). → Mutual-only "would meet again", and one-tap thanks to the host.
3. **Showing up is a planning problem.** Asking *when and how* raised flu-shot uptake from 33.1% to 37.3% (Milkman et al. 2011, *PNAS*, strong) and voter turnout 4.1 points, **9.1 points for people living alone** (Nickerson & Rogers 2010, strong). Two reminders beat one (Steiner et al. 2018, 54,066 patients, strong). A reminder that says not coming *affects someone else* cut missed visits from 21.1% to 14.2% and raised early cancellations from 17.2% to 26.3% (Berliner Senderey et al. 2020, 161,587 appointments, strong).
4. **Free events lose many sign-ups** (practitioners report 25–60%, weak), and **deposits push people away**: only 14% accepted deposit programmes vs 90% reward programmes (Halpern et al. 2015, *NEJM*, strong). → Keep Milavn free by default; use kind confirmations and freed spots instead of penalties.
5. **Never shame, never streak.** Social pressure works but shaming conflicts with the community; broken streaks reduce engagement (Silverman & Barasch 2023) while "welcome back after a miss" was the best of 54 gym interventions (+27%, Milkman et al. 2021, *Nature*, strong).
6. **Newcomers stay when someone welcomes them** (Choi et al. 2010 CSCW; Morgan & Halfaker 2018 Teahouse experiment, moderate-strong). Groups survive when new people keep arriving and hosts are not alone (Liu & Suel 2016 on thousands of Meetup groups, moderate; Meetup leadership guidance).
7. **Recommendation signals, in order of strength:** being in the host's circle > content > location/time (Macedo et al. 2015 RecSys, strong); for brand-new events the **organizer** matters most (Zhang & Wang 2015 KDD, moderate). Simple honest explanations beat scores and charts (Herlocker et al. 2000, strong). Recommenders drift to the popular unless new hosts get a fair share (Abdollahpouri et al. 2019; Chaney et al. 2018).
8. **What works in the best IRL products (2023–2026):** small pods so nobody arrives alone (Pie groups of 6, Timeleft tables of 6); mutual follow-ups within 24 h with no counts (Meetup Connections); safety in the format — public venues, first names, share-my-plan (Timeleft, 222, Bumble, Snap Map); a nudge before a harsh message cut negative comments 20% (Nextdoor Kindness Reminder); **putting member messaging behind a paywall backfired** (Meetup+ 2024).
9. **India and our community:** WhatsApp is the channel (500M+ users; Reuters DNR 2025); family groups suffer fatigue and seniority blocks moderation (CSCW study of 32 admins, strong); 81% of Indians limit meat (Pew 2021); women's phones are shared and watched and online photo abuse is real (Sambasivan et al. SOUPS 2018 / CHI 2019, strong); in urban India 53% of women did not leave home on a survey day vs 14% of men (Time Use Survey 2019); Telangana's **T-Safe** ride monitoring works by dialling 100 then option 8; DPDP Rules 2025 treat identifiable photos as personal data and require verifiable parental consent for under-18s.
10. **Community identity needs confirming.** The Hyderabad community that reveres Sahasrarjun is the Somavamsha Sahasrarjuna Kshatriya / Patkar Khatri (SSK) samaj; Punjabi Khatri families have different festivals and languages. Sahasrarjun Jayanti falls on Kartik Shukla Saptami (16 November 2026). Festival defaults must not be seeded until the owner confirms which traditions Milavn serves.

---

## 2. Anti-patterns we will not build

- Public no-show lists, "flaker" labels, reliability scores, streaks that reset, points or badges for attendance.
- Deposits on free community activities; paywalls on member-to-member messaging.
- Fake scarcity or inflated counts; showing "2 going" as social proof on a new event.
- One-way "people you may like" (it turns meetups into rishta-hunting); age or marital status on attendee lists.
- Public photo galleries, face search, downloads of women's or children's photos by default.
- Live location tracking; a single national festival date; defaulting late-night events for women-only or elder-friendly groups.
- Percentages, confidence scores or charts as "why this"; social-proof explanations used as persuasion.

---

## 3. Roadmap (ranked by impact × evidence ÷ effort)

| # | FR | Behaviour | Evidence | Status |
|---|---|---|---|---|
| 1 | FR102 | **Paid spots** (owner request): price only when the host chooses, 15-minute hold, free waitlist with paid offers, one clear refund rule, totals-only organizer view, provider-agnostic Payment Services port | Thesis §53–§55; Halpern 2015 (deposits deter) → free default | **Built** (IMP27). Vendor + MOD06 = blocker |
| 2 | FR103 | **"Still coming?" at T−24 h** with *Still coming* / *Free my spot* (instant waitlist promotion; paid spots follow the refund rule), prosocial wording | Berliner Senderey 2020; Hallsworth 2015 | **Built** (IMP28) |
| 3 | FR104 | **Two reminders (T−3 d, T−2 h)** that repeat the person's own plan (and welcome someone coming alone) | Steiner 2018; Rogers & Milkman 2016 | **Built** (IMP28) |
| 4 | FR105 | **Plan prompt after joining**: "How are you getting there?" and "Coming with: alone / a friend / family" (one tap, optional) | Milkman 2011; Nickerson & Rogers 2010 | **Built** (IMP28) |
| 5 | FR106 | **Would meet again** — after check-in, privately pick people; a connection forms only when both pick each other; no counts anywhere | Boothby 2018; Meetup Connections | **Built** (IMP32) |
| 6 | FR107 | **Thank the host** — one-tap thanks after attending, feeding qualitative reputation; host gets a specific summary (people came, first-timers, thanks) | Kumar & Epley 2018; Grant & Gino 2010 | **Built** (IMP29) |
| 7 | FR108 | **Welcome newcomers** — host sees "first time" and "coming alone" on the attendee list; newcomer gets a "what to expect" card | Choi 2010; Morgan & Halfaker 2018; Bauer 2007 | **Built** (IMP29) |
| 8 | FR109 | **Share my plan** — one tap sends activity, locality, time, host first name and expected end to a family contact on WhatsApp; Telangana T-Safe reminder for evening events | Timeleft/222/Bumble safety; T-Safe; women's mobility data | **Built** (IMP29) |
| 9 | FR110 | **Who it's for** — Family & kids, Elder-friendly, Women only (women hosts), and food defaults Veg / Alcohol-free, all filterable | Pew 2021; India track; intergenerational reviews | **Built** (IMP30); "women only" deferred — needs a gender attribute the platform identity does not hold |
| 10 | FR111 | **Honest discovery upgrades** — organizer-trust and circle signals, a labelled fair-start slot for new hosts, per-host/category caps, "Not interested" with a reason | Macedo 2015; Zhang 2015; Herlocker 2000; Abdollahpouri 2019 | **Built** (IMP30) |
| 11 | FR112 | **Make it a regular / welcome back** — after the second time in a series, one tap to keep a spot each week (opt-in); after a miss, a warm "we held your spot" instead of any streak | Hall 2019; Milkman 2021; Silverman & Barasch 2023 | **Built** (IMP31) — available after the first check-in; free series only |
| 12 | FR113 | **Photo privacy** — "don't include me" and one-tap removal of photos you appear in; children need a parent's approval | DPDP Rules 2025; SOUPS 2018 | **Built** (IMP31) — the parent-approval rule is a sharer's confirmation, not a verified parent |
| 13 | — | Going-solo pods of 4–6; kindness nudge before sending; co-host suggestion | Pie, Timeleft, Nextdoor, Liu & Suel | Later |
| 14 | — | Festival-aware suggestions with regional date rules | India track | **Blocked:** owner to confirm which community traditions Milavn serves (SSK/Patkar Khatri, Punjabi Khatri, or both) |

---

## 4. Sources (as reported by the research tracks)

**Friendship and belonging.** Hall 2019 https://journals.sagepub.com/doi/10.1177/0265407518761225 · Reis et al. 2011 https://www.sas.rochester.edu/psy/people/faculty/reis_harry/assets/pdf/ReisManiaciCaprarielloEastwickFinkel_2011.pdf · Aron et al. 1997 https://journals.sagepub.com/doi/10.1177/0146167297234003 · Boothby et al. 2018 https://journals.sagepub.com/doi/10.1177/0956797618783714 · Kumar & Epley 2018 https://journals.sagepub.com/doi/10.1177/0956797618772506 · Sandstrom & Dunn 2014 https://journals.sagepub.com/doi/abs/10.1177/0146167214529799 · Pettigrew & Tropp 2006 https://ideas.wharton.upenn.edu/wp-content/uploads/2018/07/Pettigrew-Tropp.pdf · Dunbar 2018 https://www.cell.com/trends/cognitive-sciences/abstract/S1364-6613(17)30224-3 · Choi et al. 2010 https://dl.acm.org/doi/10.1145/1718918.1718940 · Morgan & Halfaker 2018 https://dl.acm.org/doi/10.1145/3233391.3233544 · Bauer et al. 2007 https://pubmed.ncbi.nlm.nih.gov/17484552/

**Showing up and organizers.** Steiner et al. 2018 https://www.ajmc.com/view/optimizing-number-and-timing-of-appointment-reminders-a-randomized-trial · Hallsworth et al. 2015 https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0137306 · Berliner Senderey et al. 2020 https://pmc.ncbi.nlm.nih.gov/articles/PMC7310733/ · Milkman et al. 2011 https://scholarsarchive.byu.edu/facpub/9043/ · Nickerson & Rogers 2010 https://journals.sagepub.com/doi/abs/10.1177/0956797609359326 · Halpern et al. 2015 https://www.nejm.org/doi/full/10.1056/NEJMoa1414293 · Milkman et al. 2021 https://www.nature.com/articles/s41586-021-04128-4 · Silverman & Barasch 2023 https://academic.oup.com/jcr/article-abstract/49/6/1095/6623414 · Rogers & Milkman 2016 https://journals.sagepub.com/doi/abs/10.1177/0956797616643071 · Liu & Suel 2016 https://research.engineering.nyu.edu/~suel/papers/group.pdf · Grant & Gino 2010 https://www.semanticscholar.org/paper/a8c362eb46bb591005007d1e7894109d47ce5b2a · Fradkin et al. 2021 https://pubsonline.informs.org/doi/10.1287/mksc.2021.1311

**Recommendation.** Macedo et al. 2015 https://dl.acm.org/doi/10.1145/2792838.2800187 · Pham et al. 2015 https://www3.ntu.edu.sg/home/gaocong/papers/ICDE15_research_391.pdf · Zhang & Wang 2015 https://weizhangltt.github.io/paper/zhang-kdd2015.pdf · Herlocker et al. 2000 https://grouplens.org/site-content/uploads/explain-CSCW-20001.pdf · Abdollahpouri et al. 2019 https://arxiv.org/abs/1901.07555 · Chapelle & Li 2011 https://papers.nips.cc/paper/4321-an-empirical-evaluation-of-thompson-sampling

**Products.** Meetup Connections https://www.meetup.com/blog/connections-meetups-powerful-new-friendship-tech/ · Meetup 2025 report https://www.meetup.com/blog/2025-meetup-progress-report/ · Meetup+ https://www.meetup.com/blog/new-to-meetup-plus-october-2024/ · Timeleft algorithm https://timeleft.com/blog/2023/11/10/timeleft-algorithm-the-maestro-of-your-dinners/ · Timeleft safety https://timeleft.com/safety-guidelines/ · Pie https://techcrunch.com/2025/03/04/andy-dunns-new-app-pie-uses-ai-to-help-you-make-friends · Nextdoor Kindness Reminder https://blog.nextdoor.com/2019/09/18/announcing-our-new-feature-to-promote-kindness-in-neighborhoods · Luma check-in https://help.luma.com/p/check-in · WhatsApp Communities events https://blog.whatsapp.com/new-to-communities-events-and-replies-in-announcement-groups · IRL shutdown https://techcrunch.com/2023/06/26/irl-shut-down-fake-users/

**India.** WhatsApp admins study https://arxiv.org/html/2401.08091v2 · Reuters DNR 2025 India https://reutersinstitute.politics.ox.ac.uk/digital-news-report/2025/india · Pew 2021 https://www.pewresearch.org/short-reads/2021/07/08/eight-in-ten-indians-limit-meat-in-their-diets-and-four-in-ten-consider-themselves-vegetarian/ · Sambasivan et al. SOUPS 2018 https://www.usenix.org/conference/soups2018/presentation/sambasivan · Telangana Women Safety Wing (T-Safe) https://womensafetywing.telangana.gov.in/women-safety-apps/ · DPDP Rules 2025 (MediaNama) https://www.medianama.com/2025/01/223-data-protection-rules-2025-children-data-india/ · Ashoka CSIP, How India Gives https://csip.ashoka.edu.in/how-india-gives-2026/ · Hyderabad Runners https://hyderabadrunners.com/about-us/history/ · SSK samaj https://ssksamaj.org/about-us/

---

## 5. Competitor capability study and the owner's picks (2026-09-17)

A second research pass covered Meetup (help centre, blog, 2026 roadmap, Trustpilot), Luma, Partiful,
Eventbrite, Posh, Dice, Facebook Events/Groups, WhatsApp Communities, Google and Apple invites, and
the friendship/community set: Bumble BFF (now on Geneva), Timeleft, 222, Peanut, Geneva, Mighty
Networks, Skool, Heylo, BAND, Nextdoor, Strava clubs, Discord, Couchsurfing, plus the Indian
products Kutumb, Mera Samaj and Samaj Saathi. The owner reviewed the capability list and picked
fourteen to build; the rest were deliberately not chosen.

| # | Capability | Learned from | Status |
|---|---|---|---|
| 1 | **Bringing someone with you** — +N counted against capacity; the waitlist keeps a party together | Meetup, Partiful, 222 | **Built** (FR114 / IMP34) |
| 2 | Questions before joining a circle | Meetup, Luma, Geneva, Heylo | **Built** (FR115 / IMP35) |
| 3 | Approve each joiner | Meetup, Heylo, Luma | **Built** (FR115 / IMP35) |
| 4 | Waitlist keeps a party together | Meetup | **Built** with item 1 |
| 6 | Poll for the date before fixing it | Partiful | **Built** (FR120 / IMP36) |
| 7 | Vote together on which activity to attend | Dice Groups | **Built** (FR120 / IMP36) — API complete; the screen creates date polls |
| 8 | "I'm free right now" | Couchsurfing Hangouts | **Built** (FR119 / IMP36) |
| 9 | Conversation cards | Timeleft, 222 | **Built** (FR118 / IMP36) — English only so far |
| 14 | Fundraising drives for a community cause | Mera Samaj, Heylo | **Built** (FR124 / IMP37) — promises only; payments are blocker B1 |
| 17 | Layered leadership roles | Meetup (co-organizer / assistant / event organizer) | **Built** (FR121 / IMP35) |
| 18 | Chapters under one umbrella | Meetup Pro Networks | **Built** (FR123 / IMP37) |
| 20 | Recognition for good hosts | Meetup's 2026 "Super Organizer" | **Built** (FR117 / IMP36) |
| 23 | Follow a calendar, not just an event | Luma Calendars and subscriptions | **Built** (FR122 / IMP37) |
| 27 | Familiar faces | Meetup | **Built** (FR116 / IMP36) |

**Deliberately not copied.** Paywalling what was free (Meetup moved direct messages, full member
lists and waitlist priority behind Meetup+ in October 2024 and raised organizer prices; the reviews
since are heavily negative, repeating the 2011 backlash); leaderboards and streaks (Skool reports
real retention gains, but they contradict the count-not-streak decision this file already records);
fee stacking (Eventbrite's ~20% on a small ticket is its top complaint); and requiring a phone
number to RSVP (Partiful's privacy complaint).

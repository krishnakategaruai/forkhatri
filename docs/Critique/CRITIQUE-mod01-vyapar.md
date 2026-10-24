# Critique of MOD01 Vyapar (jobs, local services, businesses and professionals)

Date: 2026-10-06. Critic: MOD01 critique agent. Method: read BR/FR/VISION-2040/CRITIQUE/UX-CRITIQUE/BACKLOG/GLOSSARY, skimmed the service and web code, walked the live app (localhost:3011) at 390px and 1280px, then checked outside sources. Limit: the web-search quota ran out mid-session, so later checks used direct page fetches only. Anything I could not confirm is marked **unverified**.

## 1. What I understand Vyapar to be (please correct me)

Vyapar is a ForKhatri module that mixes Upwork (professionals, proposals, contracts) and WorkIndia (fast local jobs, call or apply in one tap). Every member has one profile, with an optional "My business" section. Posts are jobs, projects, local services, partnerships, training and community or government items. Trust is built from a no-fees-from-applicants scam shield, a "paid on time" count confirmed by the person paid, manual document verification, council badges for regulated professions, and pre-accept calling inside the poster's hours and caps. It is API-first (59 agent tools), voice and AI assisted, and in three languages. Money is a dev-sandbox ledger until a gateway exists. The Samaj runs it.

## 2. Critiques, ranked

### Critical

**C1. The marketplace may not have enough supply and demand on the same street (Effort L).**
- Claim: the strongest personas (rider, tailor, security guard, plumber) are not obviously Khatri-community members. A closed, trust-first network starts each trade with very few people.
- Evidence: the live app shows 20 business profiles in total, a "For you" row holding one card, and a test post "CHAT CHEF" still open (BACKLOG D4). Whether non-Khatri workers can join is **unverified**; the post page says "From your community", which suggests mixing.
- Why it matters: an empty plumber tile makes a worker leave for WorkIndia in one visit.
- Recommend: pick a wedge, for example Khatri business owners hiring and referring (counter staff, accountants, drivers, event crews). Measure "posts that get a hire in 7 days" per trade and open a trade only when it passes. Write down the open-to-all rule.

**C2. The scam defence is text-only, but job fraud happens by phone, WhatsApp and Telegram (Effort M).**
- Claim: the shield catches fee words in posts and poster replies. Voice calls, off-platform moves and pasted forwards are outside it.
- Evidence: `imp-trust-pack.md` lists phrase rules only. Apna names "communication attempts moving off-platform" as a red flag ([Apna](https://apna.co/career-central/how-apna-detects-blocks-fake-recruiters/), fetched 2026-10-06). Fake overseas jobs recruited on Instagram and Telegram trap Indians in Myanmar and Cambodia compounds ([The Week, 2026-03-21](https://www.theweek.in/news/india/2026/03/21/lured-by-jobs-sold-into-slavery-indias-crackdown-on-cyber-trafficking-continues.amp.html)). The post composer offers "Paste a forwarded WhatsApp message or link", which can bring a scam post in.
- Why it matters: pre-call (the owner's decision) shows the poster's number to every matching caller, and a scammer takes the caller's number back.
- Recommend: keep pre-call, but only for posters at a verified tier. Block overseas-placement posts unless the poster shows an emigration registration. After every call, send one tap, "Did they ask for money?". Run the scam shield on forwarded text before a draft is made.

**C3. Vyapar is probably an "aggregator" under the new gig-worker laws, and the backlog treats that as a fee question (Effort M).**
- Claim: D1 says legal review is needed "before Vyapar ever takes a fee from workers". The legal definition does not depend on a fee.
- Evidence: Telangana's 2026 Act (Gazette 28 Apr 2026, read directly: [PRS PDF](https://prsindia.org/files/bills_acts/acts_states/telangana/2026/Act21of2026TG.pdf)) defines an aggregator as "a digital intermediary or a market place for a buyer or user of a service to connect with the seller or the service provider". It requires payout "as per the contract with no delay" and defines termination to include any account block. The central Code is in force and the Social Security (Central) Rules 2026 require aggregators to register each new gig worker on a portal ([Taxmann](https://www.taxmann.com/post/blog/analysis-aggregator-obligations-code-on-social-security/), fetched 2026-10-06). A turnover levy of 1 to 2% applies once notified.
- Why it matters: a Samaj-run app needs this settled before it grows, not after.
- Recommend: get a written legal opinion now on aggregator status, on which Vyapar posts count as "gig work" (jobs probably do not, projects and local services probably do), and on registering workers by API. Keep the reason codes and appeals you already built; they help here.

### High

**H1. Telugu and Hindi users get a translated shell and English content (Effort M).**
- Evidence (my screens, Telugu, 390px): job titles, descriptions, "Join this week", place names and similar-post pay ("₹12,000 to ₹16,000 a month") stay English. Telugu notifications read "కొత్త మ్యాచ్: Painters for 3BHK interior repaint..." BACKLOG D5 says translation is unbuilt.
- Why it matters: this is the audience the module exists for. The rule "no hardcoded strings" is met for the app and missed for the marketplace.
- Recommend: translate each post when it is published (poster's language kept, three languages stored, labelled "translated"), numbers and places confirmed by the poster. Use Bhashini (listed in the vision as free; **unverified** here).

**H2. "Verified" is thin and unexplained (Effort M).**
- Evidence: the service checks GSTIN, PAN and Udyam by regex, then a human operator reviews (`verification.py`). Job cards show "Verified business owner" even on a ₹1,200 plumber job, with no hint of what was checked. Apna Safety checks GST, PAN and CIN records and the recruiter's Aadhaar, and reports 146,000 recruiters verified and 45% less scam exposure in an Aug to Sep 2025 pilot ([Business Today, 2025-09-25](https://www.businesstoday.in/amp/technology/news/story/apnaco-launches-ai-powered-tool-apna-safety-to-curb-job-scams-in-india-during-festive-hiring-495735-2025-09-25)).
- Recommend: a tap-to-explain badge ("GST checked on 12 Sep; phone checked"). Use an official lookup for GSTIN. Show the tier on every card and make contact depend on tier.

**H3. The job page still does not answer a worker's first questions (Effort S).**
- Evidence: the job page shows a pay range and "a month", but no pay day, working hours, weekly off, PF/ESI, or "paid on time" count. Cards show no poster name. VISION-2040 item 2 promised a pay block. Fairwork India 2024 gave a first Fair Pay point to only 2 of 11 platforms ([Fairwork via Business World](https://businessworld.in/article/fairwork-india-report-exposes-unfair-working-conditions-for-gig-workers-535781)).
- Recommend: required pay-day and hours fields, shown in the first screen. Warn the poster if the monthly pay is below the state minimum wage (the notified rate is **unverified** here; fetch it per state). Show poster name and "paid on time n of n" on the card.

**H4. No path when a monthly worker is not paid (Effort M).**
- Evidence: milestones, funding and release exist for projects only. Jobs have reports and appeals (`close_loop`, `restrictions`) but no wage-dispute step. Buyers pay MSMEs in 73 days on average per VISION-2040 (its source: Whalesbook, not re-checked).
- Recommend: use what only a Samaj app has. Set up a Samaj mediation desk with a 7-day reply promise, record outcomes in the poster's count, and link to the Labour Department grievance and e-Shram. A poster with two unresolved wage reports loses calling rights.

**H5. Money held in a ledger before any licensed rail exists (Effort M, blocked).**
- Claim: "held, released and refunded" amounts and a 14-day auto-release (`contract_auto_release_days = 14`) behave like escrow. B1 says a Razorpay account will fix it.
- Evidence: RBI payment-aggregator rules on escrow and settlement are **unverified** here; I could not search them. Check before any live money.
- Recommend: do not call it "held" in any screen until the gateway's own hold product (not Vyapar) is live. Keep the fee at 0 until H3/C3 are done.

**H6. Operator capacity is a hidden dependency (Effort M).**
- Evidence: manual verification, the council check (B6), moderation, appeals and now a mediation desk all queue to "operators". There is no staffing or reply-time target in the BACKLOG.
- Recommend: name the Samaj volunteer roles, write reply-time targets (for example verification in 2 days), and show the queue age on the admin console. A badge nobody checks is worse than none.

**H7. Everyday screens ask a rider to think like a manager (Effort M).**
- Evidence (390px): Profile is an 11-row menu (Requests, Contracts, Saved, Promotions, Studio, Calls and WhatsApp, Privacy, learned preferences, Moderation outcomes, Help) with clipped descriptions and "Recommendat ions" broken across lines. Activity lists "Interaction / Request / Closed" with no job title, pay or next step. The Businesses tab shows "My profiles" in the plural, against the owner's one-profile rule. Cards use icon tiles, with no photo or face.
- Recommend: an order-tracker Activity ("Applied · Sethi Textiles · Counter salesman · Seen"). Hide Contracts, Promotions and Studio until used. Add one real photo per profile. Rename "My profiles".

### Medium

**M1. Notifications overclaim and flood.** A product-consulting profile (m_krishna, 18 unread) gets "New match: Beautician", "Staff nurse", "Painters" with "this post matches your skills". A false match teaches people to ignore real ones. Set a confidence threshold, cap one digest a day, and translate titles (see H1). Effort S.

**M2. The directory mixes job seekers and service sellers.** Businesses lists a telecaller, a nurse and lab technician, a cook and a delivery rider under "Ask for a price". A job seeker is not selling a quote. Split "Hire a person" (invite to apply) from "Book a service" (ask a price). Effort M.

**M3. Referral and "from your community" can shut people out.** Beaman and Magruder (AER 2012) found that referrers favour relatives unless paid for referral quality ([J-PAL summary](https://www.povertyactionlab.org/evaluation/leveraging-social-networks-job-referrals-india)). VISION-2040 item 7 notes the risk, but no one measures it. Track hire rate for vouched versus unvouched applicants and by gender and area; never rank down for lack of a vouch. Effort S.

**M4. Revenue plan can break the trust it sells.** BR10 lists Boost, membership and V1.5 pay-per-response. WorkIndia scores 1.2 of 5 on Trustpilot (90 reviews) for "aggressive sales calls, unexpected charges" ([Trustpilot, Nov 2025 to Feb 2026](https://www.trustpilot.com/review/workindia.in)); Apna sits at 2.4 of 5 with refund and auto-renewal complaints (6 reviews; small sample; [Trustpilot](https://www.trustpilot.com/review/apna.com)). Samaj-run paid promotion also looks like favouritism. Drop pay-per-response, use a flat community membership with no auto-renewal, show where revenue goes (Welfare Trust). Effort S.

**M5. Privacy law arrives on 13 May 2027.** The DPDP Rules make core duties apply 18 months after 13 Nov 2025: verified consent, breach notice, 48-hour pre-deletion notice, and parental consent for under-18s ([SCC Online](https://www.scconline.com/blog/post/2025/12/26/digital-personal-data-protection-rules-2025-key-highlights/)). Vyapar holds phone numbers, ID documents, location and "seeking" status. Add an 18+ gate for work posts (child-labour law is **unverified** here) and a deletion dry run. Effort M.

**M6. The AI is mostly rules today.** B2 says Claude runs only offline; photo reading returns "not available". Screens say "We fill in the form; you check it", which is honest. Keep it labelled, and test pay and place extraction with real Hindi and Telugu speech before promoting voice. Effort M.

**M7. Boundary leak with Milavn and Counsel.** The composer says "A job, project, local service need, training or event". Events belong to Milavn. Remove "event" or hand off. Effort S.

## 3. New in the world

- **Apna Safety**: recruiter checks against GST, PAN, CIN and Aadhaar with risk scores ([Business Today, 2025-09-25](https://www.businesstoday.in/amp/technology/news/story/apnaco-launches-ai-powered-tool-apna-safety-to-curb-job-scams-in-india-during-festive-hiring-495735-2025-09-25)). A free-labour comparator Vyapar must match.
- **LinkedIn** verification badges on jobs and recruiters, after 80.6 million fake accounts removed in H2 2024 ([Rest of World, 2025-12-22](https://restofworld.org/2025/linkedin-job-scams/)).
- **State and central gig laws**: Telangana Act 2026 (Gazette 28 Apr 2026), Karnataka's 1 to 5% welfare fee on payout ([Mondaq](https://www.mondaq.com/india/constitutional-administrative-law/1759312/social-security-for-gig-workers-in-india-do-central-and-state-laws-signal-higher-costs-for-online-platforms), fetched 2026-10-06), and the central Rules of 8 May 2026.
- **IIT Madras CeRAI, "The Algorithmic-Human Manager"** (arXiv 2606.19975, 2026-06-18): interviews with 16 gig workers found algorithmic systems "opaque by design"; it proposes human accountability beside the algorithm. This supports Vyapar's human-appeal design ([arXiv](https://arxiv.org/abs/2606.19975)).
- **Urban Company's 12-point programme** (Oct 2021): after 100+ women beauticians protested, it cut the top commission from 30% to 25%, capped monthly penalties at ₹1,500 and cut algorithmic blocks by 80% ([FPJ](https://www.freepressjournal.in/amp/business/urban-company-cuts-commission-to-25-from-30-after-workers-protest)). A workable worker-voice template.
- **BCI notices of 8 July 2024** to Quikr, Sulekha, Just Dial and Grotal over lawyer listings ([ThePrint](https://theprint.in/judiciary/take-action-against-lawyers-advertising-seeking-work-via-online-portals-bci-to-state-bar-councils/2165531/)). It confirms the profession-aware design.
- **DPDP Rules phases**: 13 Nov 2025, 13 Nov 2026, 13 May 2027 (SCC Online above).
- **Fairwork India 2024** (IIIT Bangalore and Oxford) gives a ready five-principle audit: pay, conditions, contracts, management, representation.

## 4. Rethink

1. **Is Vyapar a labour marketplace first?** For: the owner's rule is Upwork plus WorkIndia, and community-vouched hiring is the one thing national apps lack. Against: C1; a Khatri business network (hire, refer, buy and sell) needs far fewer people to feel alive, and labour can follow.
2. **Employers pay, workers free.** For: protects workers, matches WorkIndia and Apna. Against: both have the worst reviews from paying employers (M4). A community levy may fit a Samaj better.
3. **Pre-call by default for jobs.** For: it mirrors how blue-collar hiring works, and the owner approved it. Against: C2; it works best only once posters are verified. Start it for verified posters only.
4. **One profile per member.** For: matches the ForKhatri identity and ends listing sprawl. Against: a son posting for his father's shop (U10) and a CA who also owns a cloth shop need distinct roles on one identity. Keep one profile, and let it act "for" a business or a person.
5. **Manual verification at launch.** For: honest and cheap. Against: H2, H6; it may not scale past a few hundred requests.

## 5. Do not change

- One profile per member, from the ForKhatri identity.
- Structured apply, proposal and enquiry composers; no generic chat.
- The "nobody may charge people who apply" banner with a one-tap report (live on the job page in all three languages).
- "Paid on time" confirmed by the person paid, never self-claimed.
- Profession-aware rules for lawyers, architects, doctors (no boosts or reviews where councils ban them) plus a lawyer's review before launch.
- Close the loop: every applicant gets a final status; every restriction has a reason and a human appeal.
- Pre-call guards (hours, daily cap, matching callers, WhatsApp-only default) and the private-by-default seeking status.
- API-first design with scoped, audited agent tokens.
- Language, text size and high-contrast controls in one sheet; full Telugu shell.
- "Why this?", "More like this" and "What Vyapar learned about you".
- The Counsel boundary: no mentoring words inside Vyapar.

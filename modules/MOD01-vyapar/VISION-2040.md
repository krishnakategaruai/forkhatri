# Vyapar 2040: what people will need, and what to build now

**Written:** 2026-09-28. **Author:** product strategy research agent.

**Brief.** The owner wants Vyapar designed "as if we are in 2040". This paper reads that as "2040 is next year": what will workers, small businesses and professionals need from a work app in 2027, and what should Vyapar build now to meet it. The three groups carry equal weight.

**Read first:** `references/2026-screen-research.md`, `CRITIQUE-2026-09-28.md`, `UX-CRITIQUE.md`, `references/imp-backend-a…d.md`, `01-business-requirements.md`.

**Labels.** Every claim that has a source carries its URL. Anything marked **[speculation]** is my own judgement, not evidence. **[anecdotal]** marks user-review sites, which are not representative samples.

**Scope rule.** Paid professional services, hiring, retainers and projects belong in Vyapar. A member seeking counselling, mentorship or guidance belongs in MOD04 Counsel. Nothing below moves that line.

---

## 0. The ground truth

**Gig work is growing, but it is not stable.**
- India's gig workforce grew from 77 lakh (FY21) to 1.2 crore (FY25), and NITI Aayog projects 2.35 crore by 2029–30.
- Four in ten gig workers earn under ₹15,000 a month.
- The Economic Survey 2025–26 asks for a minimum per-task pay that includes waiting time.

Sources: [NITI brief](https://www.niti.gov.in/sites/default/files/2022-06/Policy_Brief_India%27s_Booming_Gig_and_Platform_Economy_27062022.pdf), [Down To Earth](https://www.downtoearth.org.in/economy/economic-survey-2026-indias-fast-growing-gig-economy-needs-an-overhaul), [Business Today](https://www.businesstoday.in/union-budget/news/story/economic-survey-2025-26-suggests-minimum-wage-for-gig-workers-513506-2026-01-29).

**Most new jobs are frontline jobs.** WEF's Future of Jobs 2025 puts the largest absolute growth to 2030 in farmworkers, delivery drivers, construction workers, salespersons and food-processing workers. It also expects 39% of core skills to change by 2030 ([WEF digest](https://www.weforum.org/publications/the-future-of-jobs-report-2025/digest/), [WEF press](https://www.weforum.org/press/2025/01/future-of-jobs-report-2025-78-million-new-job-opportunities-by-2030-but-urgent-upskilling-needed-to-prepare-workforces/)).

**Independent professionals are a large and growing market.**
- India has an estimated 15 million freelancers ([secondary compilation](https://affiliatebay.net/freelancing-statistics-india/); treat as indicative).
- India is the largest supplier of online platform labour ([ILO WESO 2021](https://www.ilo.org/publications/flagship-reports/role-digital-labour-platforms-transforming-world-work)).
- 93% of Indian leaders plan to use AI agents within 18 months ([Microsoft Work Trend Index 2025](https://news.microsoft.com/source/asia/2025/08/20/indias-workforce-goes-ai-first-as-frontier-firms-lead-the-transformation-microsoft-work-trend-index-2025/)).

**The social-security rails exist, but few platform workers are on them.**
- The Code on Social Security came into force on 21 Nov 2025. It covers gig and platform workers and puts a 1–2% turnover levy on aggregators ([Wikipedia](https://en.wikipedia.org/wiki/The_Code_on_Social_Security,_2020)).
- e-Shram has 31.89 crore registrations, but only about 11.5 lakh of them are platform workers ([Organiser](https://organiser.org/2026/08/29/377578/bharat/five-years-of-e-shram-31-89-crore-unorganised-workers-join-indias-digital-social-security-net/)).

**Small firms are formalising, and they are paid late.**
- Udyam has about 7.9 crore registered enterprises ([PIB](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2246892&reg=3&lang=1)).
- Buyers pay in about 73 days on average, against a legal limit of 45 days.
- 2.16 lakh delayed-payment cases worth ₹47,677 crore had been filed by December 2024 ([Whalesbook, citing the MSME annual report](https://www.whalesbook.com/news/English/economy/MSME-Payment-Delays-Rs-38-Crore-Stuck-Per-Firm-Report-Shows/6a41b79bfb97bcde4ce565b2)).

**Fraud is the default fear.**
- 42% of Indian WhatsApp users have received job-scam messages asking for payment ([LocalCircles via Business Standard](https://www.business-standard.com/india-news/whatsapp-job-scams-survey-impersonation-fraud-localcircles-report-125052101713_1.html)).
- Fake "registration fees" run from ₹3,000 to ₹25,000 ([HR Katha](https://www.hrkatha.com/features/52019/)).

**What this means for Vyapar.** The winner in 2027 is not the app with the most AI. It is the one a rider trusts with his number, a kirana owner trusts with a hire, and a lawyer or doctor can join without breaking their council's rules. That app gets people paid on time, speaks their language and remembers their work.

Vyapar has two assets that national apps lack. It has a real community that can vouch for its members. And it has an API/MCP core that agents can already use, with 59 tools. Both should be put to work.

---

## 1. The people: workers and small businesses

(Each "2027 day" below is **[speculation]** grounded in the evidence above.)

**1. Ravi, 24, delivery rider, Kukatpally, Hyderabad.**
- **Today:** he runs two apps and earns ₹18–22k a month. About a quarter of that is incentives that change every week ([arXiv 2609.13178](https://arxiv.org/abs/2609.13178)).
- **Needs:** steady work nearby, no fees, pay he can predict, e-Shram and PM-JAY cover, and a work record a lender will accept.
- **Where Vyapar fits:** pre-accept calling (already built), applying by voice in Telugu, a work agent that watches for "driver, ₹20k+, within 8 km", and an earnings diary.

**2. Sunil, 46, kirana owner, Ameerpet.**
- **Today:** he needs a counter helper, a delivery boy, and a CA once a quarter.
- **Needs:** candidates someone he knows can vouch for, calls only at 2–4 pm, and recurring services.
- **Where Vyapar fits:** AI drafting of posts, calling hours and caps (all built), plus community vouches and repeat bookings.

**3. Meena, 33, home-based tailor, Secunderabad.**
- **Today:** she is paid per piece, works 11–4, and never shares her address before an order is confirmed.
- **Where Vyapar fits:** a women-safe mode, women-only crews, and a work record with photos of her pieces.
- **Context:** women are about 10% of India's platform workers ([CGAP](https://www.cgap.org/blog/on-gig-platforms-women-workers-face-triple-barriers-to-inclusion)), and 31% of women name commuting as a barrier to work ([World Bank via Vision IAS](https://visionias.in/current-affairs/monthly-magazine/2026-03-31/economy/female-labour-force-participation-in-india)).

**4. Rajesh, 51, box maker, Jeedimetla.**
- **Today:** he runs a Udyam-registered unit with 22 workers and has ₹40 lakh stuck with two buyers.
- **Where Vyapar fits:** crew posts for rush orders, a B2B requirement post type, and invoice tracking against the 45-day rule.

**5. Priya, 21, B.Com fresher, Warangal.**
- **Where Vyapar fits:** "jobs you nearly match", which names the missing skill and a Skill India course for it; a DigiLocker certificate on her profile; and a first-job vouch from a community elder.

---

## 2. The people: professionals (equal weight)

### 2.1 Six professional personas

**Anita, 38, CA, Andheri, Mumbai (the seed persona).**
- **Needs:** she wants retainers, not one-off jobs. ICAI's revised Code of Ethics lets CA firms advertise non-assurance services from 1 April 2026 ([The Accountant](https://www.theaccountant-online.com/news/icai-advertising-guidelines/)).
- **Where Vyapar fits:** an ICAI-verified badge, monthly packages ("GST filing, ₹3,500/month"), and invoices tracked against the 45-day rule. Freelancers and consultants who register on Udyam get the same delayed-payment protection as factories ([Kanakkupillai](https://www.kanakkupillai.com/learn/why-every-freelancer-service-provider-should-get-udyam-msme-registration/), [MSME Samadhaan](https://samadhaan.msme.gov.in/)).

**Arjun, 29, freelance full-stack developer, Gachibowli.**
- **Today:** half his income comes from overseas clients through Upwork, which has charged a variable 0–15% fee since May 2025, plus paid Connects to bid ([GoLance](https://golance.com/blogs/upwork-fees-explained-2026)).
- **Needs:** community clients (diaspora and local MSMEs) with no bidding war, GST-compliant export invoices under an LUT with e-FIRA ([Xflow](https://www.xflowpay.com/blog/gst-for-freelancers)), and a portfolio linked to shipped work.
- **2027 day [speculation]:** an AI agent qualifies enquiries overnight, and he only takes calls about scoped, funded work.

**Dr Kavitha, 34, physiotherapist, Kondapur.**
- **Today:** she does home visits and runs a small clinic. Physiotherapists must now register under the NCAHP Registration Regulations 2026, notified on 31 Aug 2026 ([KollegeApply](https://news.kollegeapply.com/news/ncahp-registration-rules-2026-renewal-fees-cpd-and-eligibility)).
- **Needs:** a verified registration badge, paid home-visit slots, safety on visits, and no per-lead fees. Practo-style directories draw doctors' complaints about paying for leads and no-shows **[anecdotal: [MouthShut](https://www.mouthshut.com/review/practo-review-qqlsulplptn), [Trustpilot](https://www.trustpilot.com/review/practo.com)]**.

**Adv. Farhan, 41, advocate, City Civil Court, Hyderabad.**
- **Rules he must follow:** under Bar Council Rule 36, advocates may not advertise or solicit. In 2025 the BCI directed state councils to act against lawyers soliciting through online portals, and sent cease-and-desist notices to JustDial, Sulekha and Quikr ([ThePrint](https://theprint.in/judiciary/take-action-against-lawyers-advertising-seeking-work-via-online-portals-bci-to-state-bar-councils/2165531/), [MediaNama](https://www.medianama.com/2025/03/223-the-bar-council-of-india-warns-against-legal-advertising-online/)). Only name, address, contact, qualifications and areas of practice may be shown.
- **Needs:** a listing that stays within those limits. That means no boost, no reviews, no "top lawyer" ranking, and referrals only from people who actually know him.

**Nisha, 36, interior designer (with an architect partner), Jubilee Hills.**
- **Rules her partner must follow:** the Council of Architecture's Professional Conduct Regulations bar architects from advertising and from offering discounts or commissions to win work. They also set a mandatory minimum scale of fees, for example up to 7.5% for individual houses and interiors ([CoA](https://coa.gov.in/showfile.php?lang=1&level=1&sublinkid=302&lid=152), [ArchiEase](https://www.archiease.com/articles/coa-scale-of-charges-india/)). Interior designers who are not registered architects are not bound by CoA.
- **Needs:** a project portfolio with client-confirmed projects, milestone contracts (design, then execution, then handover), and trusted contractor crews to hand work to.

**Two personas share one row:**

| Persona | Needs | Where Vyapar fits |
|---|---|---|
| **Vikram, 45, business consultant, Pune.** He runs process and ERP projects for MSMEs and is Udyam-registered. | Retainers and milestone projects. | Contracts, packages, invoices. Delivering a project is Vyapar's work. If a member wants mentoring or career guidance from him, that is a Counsel session, and Vyapar hands off to MOD04. |
| **Sarita, 27, home tutor (maths, classes 8–10), Secunderabad.** | Trial classes, a monthly fee collected on time, and parents' trust around children. | Recurring bookings, UPI AutoPay once a gateway is live, and visible verification for tutors who visit homes. Classes for a fee are a paid service and stay in Vyapar. |

### 2.2 What professionals will need in 2027

1. **Verified credentials that a client can check in one tap.**
   - ICAI has "Trace a Member" and UDIN document verification ([traceamember.icai.org](https://traceamember.icai.org/), [UDIN](https://udin.icai.org/search-udin)).
   - NMC is building a National Medical Register with Aadhaar-verified doctors ([Business Standard](https://www.business-standard.com/health/all-doctors-to-have-unique-ids-nmc-starts-registration-on-its-portal-124091500281_1.html)).
   - NCAHP keeps a live Central Register for 56 professions.
   - Degrees and Skill India certificates are issued into DigiLocker ([DigiLocker](https://www.digilocker.gov.in/)).

   Fake-profile fraud also hits the professional side: 6 in 10 job seekers met a fake posting in a 2025 survey ([Rest of World on LinkedIn scams](https://restofworld.org/2025/linkedin-job-scams/)).
2. **Rule-aware presence.** Lawyers, architects and doctors each have different advertising rules. The NMC's 2023 conduct regulations are in abeyance, so the 2002 MCI ethics code still governs doctors ([Medical Dialogues](https://medicaldialogues.in/health-news/nmc/breaking-news-nmc-puts-its-controversial-registered-medical-practitioner-professional-conduct-regulations-2023-put-on-hold-116314)). A generic directory that ignores these rules puts its members at risk.
3. **Portfolio careers and retainers.** 70% of Indian freelancers freelance full-time (secondary survey, same compilation as above). Their income comes from repeat clients, not bids **[speculation, consistent with how retainer-based CA and tutoring practices work]**.
4. **AI-augmented solo practice.** The agent tools that large firms get will reach a one-person practice: intake, scoping, proposals, scheduling and follow-ups ([Upwork Uma](https://upalerts.app/blog/what-is-upwork-uma), [LinkedIn Hiring Assistant](https://news.linkedin.com/2025/hiring-assistant-globally-available)).
5. **Getting paid and staying compliant.** 29% of freelance invoices are paid late ([Bonsai data via Clockify](https://clockify.me/late-invoice-statistics)). GST registration is required above ₹20 lakh, and export of services needs an LUT plus a FIRC or e-FIRA to be zero-rated.
6. **Referrals inside a trusted network.** Referral is how Indian hiring works: over 70% of manufacturing jobs are filled through referrals ([J-PAL](https://www.povertyactionlab.org/evaluation/leveraging-social-networks-job-referrals-india)). Professionals refer across disciplines: a CA to a lawyer, an architect to a contractor. **[speculation]** that the pattern carries over from the evidence.
7. **Cross-border clients from the diaspora community** **[speculation]**. Payment needs a licensed cross-border payment aggregator.
8. **Pricing confidence.** Solo professionals under-price. The one regulated counterexample is CoA's minimum fee scale.

### 2.3 Where current platforms fail them

| Platform | Where it fails Indian professionals |
|---|---|
| **Upwork** | A global race to the lowest bid, a 0–15% fee plus paid Connects, and no community trust. |
| **LinkedIn** | A network with no transaction layer (contracts, milestones, Indian invoicing), plus rising fake-recruiter fraud (Rest of World, above). |
| **Toptal** | Accepts under 3% of applicants and is mostly tech. Clients need a $500 deposit and a $79 monthly fee ([Toptal FAQ](https://www.toptal.com/faq), [TECLA](https://www.tecla.io/blog/toptal-review)). The CA, the physio and the tutor are simply out of scope. |
| **Contra** | Commission-free for freelancers ([Contra](https://contra.com/commission-free)), but it is global, built for creative and tech work, and has no Indian council verification. I did not verify whether it handles GST. |
| **Practo, JustDial, Sulekha** | They sell visibility and leads. JustDial, Sulekha and Quikr received BCI cease-and-desist notices over lawyer listings. Reviews and paid ranking erode trust **[anecdotal]**. |

**Vyapar's opening:** council-verified, rule-aware profiles; no bidding and no fee on the professional's earnings; community referrals; and contracts, GST invoices and 45-day protection built in.

---

## 3. The ranked list

Items are ranked by impact on people and feasibility now. Effort: **S** is under 2 weeks for one workstream, **M** is 2–6 weeks, **L** is over 6 weeks or blocked by an outside party.

### 1. Scam shield on every surface (S)
- **Need:** job-fee scams are the top fear (LocalCircles, above). WorkIndia sells its fraud filtering as a differentiator ([BW People](https://www.bwpeople.in/article/workindia-uses-a-new-technology-to-mitigate-fraud-in-job-openings-454224)).
- **Build:** extend "nobody charges job seekers" from post fields to all text a poster writes: post bodies, enquiry threads, AI drafts and voice transcripts. Detect fee, deposit, registration and training-charge language in en/hi/te and block the send. The seeker then sees a calm banner: "Vyapar employers never ask you for money. Report."
- **Reuses:** `check_seeker_charge`, reports and moderation, and the AI's closed vocabularies.
- **Dependencies:** none.
- **Risk:** legitimate deposits exist in local services (equipment rental, for example). Block on employment posts; only warn elsewhere.

### 2. Honest terms and "paid on time" (S)
- **Need:** unpredictable pay is the central complaint. The Survey wants waiting time paid ([Business Standard](https://www.business-standard.com/amp/budget/news/state-must-help-raise-gig-workers-pay-regulate-platforms-economic-survey-126012901498_1.html)), and only 2 of 11 platforms earned Fairwork's first Fair Pay point ([Fairwork 2024](https://fair.work/en/fw/publications/fairwork-india-ratings-2024-labour-standards-in-the-platform-economy/)).
- **Build:**
  - Required fields on posts: in-hand pay, pay basis (day, hour, piece, month, fixed fee or retainer), pay day, and whether travel and waiting time are paid. Professional packages must say what is included.
  - A count badge on the paying side, such as "Paid on time: 14 of 14", confirmed by the worker or professional after each job.
- **Screen:** a Pay block at the top of the job or package page.
- **Reuses:** migration 018 fields, count badges, review invites.
- **Dependencies:** none.
- **Risk:** inflated pay claims. The payee's confirmation catches them.

### 3. Close the loop: every applicant or enquiry gets an answer (S)
- **Need:** Apna's poster nudges raised leads by 23% ([Apna](https://apna.co/career-central/apna-cos-latest-updates-to-transform-recruitment/)). That silence drives people away is **[speculation]**, drawn from the critique passes.
- **Build:**
  - Every applicant sees a stage.
  - A closed post, or a post with no action for 7 days, sends a polite "not selected" in the applicant's language, together with 3 similar jobs.
  - Professionals' enquiries show "Replies within ~1 day".
  - Any restriction on an account shows a reason code and a human appeal path. Declining work never lowers a member's visibility, which answers Fairwork's deactivation findings.
- **Reuses:** `setApplicantStage`, notifications, moderation appeals.
- **Dependencies:** none.
- **Risk:** automated rejections can feel cold. The similar-jobs list softens them.

### 4. Council-verified professional badges (S/M) *(professional)*
- **Need:** see §2.2 point 1. Clients cannot easily check whether a professional is genuine, and fake profiles are common.
- **Build:** a "Registered with…" badge that names the register and shows the date it was last checked. It covers ICAI (member number, checked against Trace a Member), NMC/SMC, NCAHP, the State Bar Council, CoA, and DigiLocker degrees and certificates. Operators check manually first, and each badge re-checks yearly. A CA's audit document can also be checked with its UDIN.
- **Reuses:** Level-3 verification (BR03), the verification operator queue, and the evidence store.
- **Dependencies:** none for manual checks. Automated pulls need DigiLocker requester registration (API Setu). No official ICAI, NMC or Bar Council APIs were verified.
- **Risk:** a suspended licence behind a stale badge. The yearly re-check, the visible date, and a "Report this badge" link cover it.

### 5. Profession-aware profiles and promotion rules (S/M) *(professional)*
- **Need:** see §2.1. Rule 36 and the BCI enforcement against JustDial and Sulekha, CoA's advertising and discount ban, the medical ethics code, and ICAI's new advertising freedom all differ by profession.
- **Build:** a profile template for each regulated profession.
  - **Advocates:** only the BCI-permitted fields; no boost, no reviews, no ranking badges, no "request a quote" pitch.
  - **Architects:** no boost and no discount offers. Fee fields warn when a figure is below the CoA scale.
  - **Doctors and physios:** no testimonials and no outcome claims.
  - **CAs:** promotion only of non-assurance services.

  Show an "Information only" note where the rules require it.
- **Reuses:** listing types, boost eligibility checks (BR10), and taxonomy.
- **Dependencies:** a one-time legal review of each template.
- **Risk:** the rules change. Keep them in a config table with a "rules checked on" date. This is the precondition for inviting any lawyer onto Vyapar.

### 6. Voice first, in the member's language (M)
- **Need:** browser speech recognition has about 16% word error in Hindi and about 33% in Telugu. Voice form-filling loses about 41 points of accuracy without confirmation (`2026-screen-research.md` §9). Bhashini offers free speech recognition, text-to-speech and translation in 22 languages ([Bhashini](https://bhashini.gitbook.io/bhashini-apis)).
- **Build:**
  - Bhashini as the server-side recogniser for Telugu, and as the fallback for Hindi.
  - "Listen" on job pages, so a post can be heard as well as read.
  - Voice-note answers to screening questions.
  - Posts auto-translated into the reader's language, marked as translated.
- **Reuses:** AI drafting with per-field confirmation, and the i18n catalogues.
- **Dependencies:** a Bhashini/ULCA key.
- **Risk:** mistranslated money or places. Numbers and places are always confirmed as parsed values.

### 7. Community vouching and professional referral-out (M)
- **Need:** referral dominates Indian hiring, and the person referring carries the social accountability ([J-PAL](https://www.povertyactionlab.org/evaluation/leveraging-social-networks-job-referrals-india), [CMI](https://www.cmi.no/publications/5386-employee-referral)).
- **Build:**
  - Work-specific vouches ("hired Suresh for wiring twice"), shown as a count plus names when both people consent.
  - A professional "Refer to a colleague" action: a CA hands an enquiry to a lawyer, with the client's consent. No referral fee is allowed where the council bans it, which covers advocates and architects.
- **Reuses:** partnerships, badges, contract completion.
- **Dependencies:** none.
- **Risk:** referral networks can exclude by caste or closed circle (J-PAL). Vouches are never required, never used to push someone down, and never show a community. Vyapar stays open to all.

### 8. A personal work agent with a written mandate (M)
- **Need:** Indeed Career Scout reports 7× faster applying and 38% higher odds of being hired ([Indeed](https://www.indeed.com/news/releases/indeed-introduces-new-suite-of-hiring-products-career-scout-talent-scout-premium-sponsored-jobs-and-indeed-connect)). Upwork's Uma reached every client in May 2026. LinkedIn's Hiring Assistant cut profile review by 62%.
- **Build:** a standing instruction in plain words, stored as a structured mandate.
  - **Worker:** "Driver jobs, ₹18k+ in-hand, within 8 km, verified posters only; never share my number."
  - **Professional:** "Qualify GST enquiries, ask turnover and filing frequency, send my ₹3,500 package, and book a call only if the answers fit."
  - **Poster:** "Shortlist electricians with 5+ jobs done."

  The agent never pays, signs or accepts. Every action appears in an "Agent did" log with an Undo.
- **Reuses:** saved searches, one-tap apply, AI shortlist, packages, the MCP tools and agent tokens.
- **Dependencies:** an Anthropic key and the `/v1/ai` scope line (imp-backend-c).
- **Risk:** spam applications. A daily cap, an agent label, and a poster-side filter.

### 9. Safe visits: women-safe mode and home-visit safety (M)
- **Need:** home-service work leaves women exposed, with no penalty-free way out ([Microsoft Research](https://www.microsoft.com/en-us/research/publication/watched-but-moving-platformization-of-beauty-work-and-its-gendered-mechanisms-of-control/), [ORF](https://www.orfonline.org/research/gender-and-the-gig-economy-a-qualitative-study-of-gig-platforms-for-women-workers-65948)). Tutors and physios who visit homes need two-way trust **[speculation]**.
- **Build:**
  - The address is shared only after the job is accepted.
  - "Women clients only" or "women crew only", chosen by the woman herself.
  - "I'm here" and "I'm done" check-ins, shared with a trusted contact.
  - "Leave safely", with no effect on her badges.
  - Home tutors show their verification to the parents.
- **Reuses:** calling hours, contracts, reports.
- **Dependencies:** SMS through the platform notification service.
- **Risk:** gender filters used to discriminate. They can only be set as the worker's own choice, never as a poster's exclusion on employment posts.

### 10. "Your protections": social security and scheme matching (S/M)
- **Need:**
  - Only about 11.5 lakh platform workers are among 31.89 crore e-Shram registrants.
  - Platform workers on e-Shram get PM-JAY cover of ₹5 lakh ([PIB](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2109421)).
  - Karnataka makes benefits portable ([Business Standard](https://www.business-standard.com/india-news/karnataka-gig-workers-act-explained-benefits-high-court-platforms-126070800776_1.html)), and Telangana's law covers delivery and household work ([Deccan Chronicle](https://www.deccanchronicle.com/southern-states/telangana/telangana-cabinet-approves-welfare-law-for-gig-and-platform-workers-1917754)).
  - myScheme lists 2,500+ schemes ([myScheme](https://www.myscheme.gov.in/)).
- **Build:** a card showing e-Shram status (self-declared) and the likely benefits: PM-JAY, the state welfare board, PM-SVANidhi, and Udyam for self-employed people and professionals. Each benefit deep-links to where to apply.
- **Reuses:** profile, notifications.
- **Dependencies:** no open myScheme API was verified, so start with a curated rules table kept by operators.
- **Risk:** stale rules, so show a "checked on" date. **Legal flag:** if Vyapar ever takes a fee on workers' earnings, it may count as an "aggregator" and owe the welfare levy. Keep `CONTRACT_PLATFORM_FEE_BPS=0` until counsel reviews.

### 11. Portable work record and portfolio (M)
- **Need:** Skill India Digital Hub has 1.5 crore candidates, and its certificates are issued into DigiLocker ([SIDH](https://digitalindiaupdates.com/skill-india-digital-hub-government-report/)). Karnataka legislated portable benefits. That reputation should be portable too is **[speculation]**.
- **Build:**
  - A "Work record": completed-contract counts, "paid on time", vouches and DigiLocker certificates.
  - Professionals add portfolio items that the client confirmed: an architect's project, a developer's shipped app.
  - "Share record" produces a signed PDF and a W3C verifiable credential, with an expiry.
- **Reuses:** badges, contracts, the evidence store.
- **Dependencies:** DigiLocker requester registration, and a key for signing credentials.
- **Risk:** records that follow people unfairly. The member chooses what the record includes.

### 12. Retainers and recurring work (M)
- **Need:** CAs, tutors, cleaners and consultants live on repeat clients. UPI AutoPay and Reserve Pay (block once, debit many times, with a ₹10,000 cap today) exist for exactly this ([Cashfree](https://www.cashfree.com/docs/payments/upi-reserve-pay/reserve-pay)).
- **Build:** "Repeats weekly/monthly" on packages and contracts, which creates the next milestone automatically. Either side can pause or stop it. Reminders go out before each charge.
- **Reuses:** packages, contracts, the ledger.
- **Dependencies:** the gateway merchant account (BLOCKER-01) for AutoPay.
- **Risk:** forgotten subscriptions. One-tap cancel.

### 13. GST invoices, export invoices and the 45-day rule (M)
- **Need:** buyers pay MSMEs in 73 days on average against the 45-day rule. 29% of freelance invoices are paid late. Export needs an LUT plus a FIRC or e-FIRA.
- **Build:**
  - A GST-ready invoice from any completed milestone.
  - An export-of-services invoice (zero-rated under LUT) for foreign clients.
  - A 45-day countdown for Udyam-registered sellers and professionals, with reminders that cite Section 43B(h) ([Busy](https://busy.in/accounting/section-43bh-msme-payment-rule-and-45-day-limit-explained/)).
  - A link to MSME Samadhaan once an invoice is overdue.
  - A note that the buyer is eligible for TReDS when their turnover is ₹250 crore or more ([M1xchange](https://www.m1xchange.com/thought-xchange/how-the-treds-platform-helps-solve-msme-cash-flow-problems/)).
- **Reuses:** contracts, the ledger, Udyam verification.
- **Dependencies:** none for invoices. A partner for TReDS.
- **Risk:** harsh reminders damage relationships. Reminders start only after the due date, in a tone the seller chooses.

### 14. Crew hiring, the thekedar model (M)
- **Need:** labour chowks and contractors take a 10–20% cut, and pay is often late or partial ([Digital Labour Chowk](https://digitallabourchowk.com/2026/01/27/labour-chowk-hiring-issues/), vendor source; [Springer](https://link.springer.com/chapter/10.1007/978-981-95-5827-8_9)).
- **Build:** a post asking for "6 painters × 4 days". A crew lead applies with named members, each of whom has accepted. Every member sees the pay split and gets their own record. The same pattern lets an architect or interior designer hire an execution crew.
- **Reuses:** openings, applications, contracts, badges.
- **Dependencies:** none.
- **Risk:** the lead skimming pay. The split is visible to all, and each member confirms payment.

### 15. Paid-session booking with time slots (M) *(professional)*
- **Need:** physio home visits, tutor trial classes and CA filing calls are paid services that need a slot, not a thread **[speculation, drawn from the personas]**.
- **Build:** a package can offer bookable slots, with calling hours reused as availability, a cancellation window, and a no-show rule the professional sets. There is no per-lead fee, unlike the per-lead model doctors complain about **[anecdotal]**.
- **Reuses:** packages, contact preferences, contracts.
- **Dependencies:** none. Prepaid slots need the gateway.
- **Scope:** mentoring, counselling or guidance sessions route to MOD04 Counsel's appointment flow. Only paid service delivery books here.
- **Risk:** Vyapar drifting into Counsel's scope. A taxonomy flag ("advisory or guidance") hands the booking off to Counsel.

### 16. Earnings diary (S/M)
- **Need:** incentives swing week to week, so workers built GigSaathi just to track what they earn ([arXiv 2609.13178](https://arxiv.org/abs/2609.13178)).
- **Build:** a private view of Vyapar-paid work, plus quick voice entries for other apps. It shows the weekly average and the worst week, and exports a statement.
- **Reuses:** the ledger, voice input.
- **Dependencies:** none.
- **Risk:** sensitive data. It is private by default and never used for ranking.

### 17. Price guidance from real data (M) *(professional and local services)*
- **Need:** pricing confidence (§2.2 point 8). CoA sets minimum fees for architects.
- **Build:** "Typical in Hyderabad: ₹2,500–4,500/month for GST filing (from 38 Vyapar packages)". It is shown in the package composer and to clients, only above a minimum sample size, and it shows CoA minimums for architects.
- **Reuses:** packages, contracts, the MOD05 read feed.
- **Dependencies:** enough volume of data.
- **Risk:** the ranges acting as price anchors or as signals for collusion. Show wide ranges and never "recommended prices".

### 18. Poster screening by voice, asynchronously (M)
- **Need:** Apna's AI calling agent has run 15 lakh interviews with an 80%+ connect rate ([BlueMachines](https://bluemachines.ai/blog/how-apna-scaled-75-lakh-ai-interview-minutes-using-bluemachinesai-and-elevenlabsai)).
- **Build:** up to 3 questions answered by voice in the applicant's language. The poster sees a transcript, a translation and a summary.
- **Reuses:** structured applications, the AI shortlist.
- **Dependencies:** Bhashini (item 6).
- **Risk:** bias. The system summarises answers and never scores accent or fluency.

### 19. Diaspora and cross-border clients (M/L) *(professional)*
- **Need:** India supplies the most online platform labour (ILO). Community clients abroad would avoid Upwork's bidding **[speculation]**.
- **Build:** clients can post from outside India, see prices in their own currency, pay through a licensed cross-border aggregator, and receive an automatic export invoice (item 13) with an e-FIRA reference.
- **Reuses:** contracts, packages.
- **Dependencies:** a PA-CB-licensed partner (e.g. Razorpay or Payoneer) and the merchant account.
- **Risk:** foreign-exchange compliance. The partner holds the licence.

### 20. Pay certainty: held milestones and real payouts (L, blocked)
- **Build:** turn the contract ledger into a real hold-and-release through Razorpay Route or a nodal account. For daily-wage jobs, block money with UPI Reserve Pay when a job is accepted.
- **Reuses:** workstream D.
- **Dependencies:** BLOCKER-01 (merchant account), MOD06.
- **Risk:** holding float is regulated. Use the gateway's product; Vyapar never holds the money.

### 21. Upskilling tied to real demand (M)
- **Need:** 63% of employers call skill gaps their main barrier (WEF).
- **Build:** "You match 4 of 5. Missing: Tally GST", linked to the nearest free SIDH or PMKVY course. The certificate then flows into item 11.
- **Reuses:** taxonomy, shortlist reasons.
- **Dependencies:** a curated course list.
- **Risk:** turning into an ad channel. Free and government courses only.

### 22. B2B requirements, then ONDC (M → L)
- **Need:** ONDC has 7.6 lakh merchants and service providers and now supports B2B trade ([IMPRI](https://www.impriindia.com/insights/policy-update/democratizing-digital-commerce-ondc-and-the-future-of-market-competition-in-india-2026/), [ONDC](https://ondc.org/blog/b2b-business-can-now-be-done-on-ondcs-platform-msme-will-get-benefit/)).
- **Build:** a "Buy for my business" post type (item, quantity, frequency, certifications) that matches verified Udyam firms.
- **Dependencies:** ONDC network registration for phase 2.
- **Risk:** drifting into a transaction marketplace, which the BRs exclude. Vyapar stops at matching and enquiry.

### 23. Works on a weak phone (M)
- **Need:** low-end, often-offline phones **[speculation]**. Karya showed that offline, local-language apps work for rural workers ([Microsoft Research](https://www.microsoft.com/en-us/research/project/project-karya/)).
- **Build:** offline drafts, a light image mode, and WhatsApp or SMS match alerts with deep links.
- **Dependencies:** a WhatsApp Business API provider.
- **Risk:** WhatsApp is also where the scams live. Use a fixed template that carries the scam warning.

### 24. Ready for other people's agents (M)
- **Need:**
  - Clients' agents already post jobs on Upwork ([Semafor](https://www.semafor.com/article/03/12/2026/upworks-ceo-on-the-ai-agents-that-try-to-hire-human-workers)).
  - NPCI is building a Unified Agent Protocol on top of UPI Circle ([Business Standard](https://www.business-standard.com/finance/news/india-may-allow-agentic-ai-led-upi-transactions-under-new-npci-protocol-126070801343_1.html)).
  - AP2 carries signed mandates ([AP2](https://ap2-protocol.org/)).
- **Build:** "via agent X for member Y" on every token action, agent labels on posts and applications, exportable mandates (item 8), and a public MCP/A2A tool card.
- **Reuses:** tokens, scopes, the MCP server, `ai_events`.
- **Dependencies:** UAP is not yet live, so payments stay human-approved.
- **Risk:** unaccountable bots. Every token belongs to a verified human.

### 25. Advance on approved work (L, blocked)
- **Need:** incomes swing and credit files are thin. Credit lines on UPI now extend to small finance banks ([Business Standard](https://www.business-standard.com/finance/personal-finance/rbi-allows-pre-approved-credit-lines-on-upi-from-small-finance-banks-125021300938_1.html)). Account Aggregator data backed ₹3.82 lakh crore of loans in FY26 ([The Hawk](https://www.thehawk.in/news/economy-and-business/indias-account-aggregator-ecosystem-drives-rs-382-lakh-crore-loans-in-fy26)).
- **Build:** "Get paid early" on an approved but unreleased milestone or invoice, offered by a regulated lender, with the fee shown in rupees. This lives in MOD07; Vyapar supplies the data with the member's consent.
- **Dependencies:** an NBFC or bank partner, RBI digital-lending rules, Account Aggregator onboarding via the partner, and MOD07 BLOCKER-002.
- **Risk:** debt traps. No credit push notifications, no advances on unapproved work, and a cap relative to earnings.

---

## 4. Not to do

- **No star ratings or leaderboards.** Counts and vouches only. Lawyers get no ratings at all.
- **No AI that decides.** AI drafts, summarises and suggests. People hire, pay and accept.
- **No voice or face "emotion" scoring, and no screenshot or keystroke tracking.**
- **No streaks or gamified incentives for workers.** That is the "forced volatility" pattern.
- **No crypto, tokens or Web3 reputation.** Use DigiLocker and W3C credentials.
- **No metaverse or AR job fairs, and no avatar interviews.**
- **No paid leads or pay-per-lead fees for professionals,** and no boosts for professions whose councils forbid advertising.
- **No credit sold before the regulated rails exist.**
- **No agents auto-applying at volume.**
- **No separate chat product.** The enquiry thread stays transactional.
- **No mentoring or guidance marketplace in Vyapar.** That belongs to MOD04 Counsel.

---

## 5. The next 3 builds (after today's FE1/FE2 and backend A–D land)

1. **Trust pack** (items 1–5; five S or S/M pieces, about 4–5 weeks, split across two workstreams).
   - **Seeker side:** scam shield, honest terms with "paid on time", and closing the loop with appeals.
   - **Professional side:** council-verified badges and profession-aware templates.

   Close critique L11 in the same pass (today a poster can see an applicant's number only by hiring them). Everything this pack needs already exists, it addresses the first fear of every persona, and it is the legal precondition for listing lawyers, architects and doctors.
2. **Voice first with Bhashini** (item 6, plus item 18). It makes Telugu usable and opens Vyapar to riders, tailors, kirana owners and parents choosing a tutor. Apply for the Bhashini key now.
3. **My work agent** (item 8), for workers, professionals and posters. It turns saved searches, one-tap apply, packages and the 59 MCP tools into a daily benefit, under a written mandate with a log and Undo. This is the "2040" feature people will actually feel. It needs the Anthropic key and the `/v1/ai` scope line.

Next in line: community vouching and referral-out (item 7), and retainers (item 12).

---

## 6. Summary: the top 10

1. **Scam shield:** block and flag any request for money from job seekers, in three languages.
2. **Honest terms:** in-hand pay or fee basis on every post and package, plus a payee-confirmed "paid on time" count.
3. **Close the loop:** every applicant gets a status, polite closure and a human appeal path.
4. **Council-verified badges:** ICAI, NMC/SMC, NCAHP, Bar Council, CoA and DigiLocker, with a checked-on date.
5. **Profession-aware profiles:** BCI, CoA, medical and ICAI rules built into templates, with no boosts where advertising is banned.
6. **Voice first:** Bhashini speech recognition and text-to-speech in Telugu and Hindi, with read-aloud and per-field confirmation.
7. **Vouching and referral-out:** consented, work-specific vouches, and colleague referrals with no banned referral fees.
8. **My work agent:** a plain-language mandate for workers, professionals and posters, with limits, a log and Undo.
9. **Safe visits:** the address shared only after acceptance, women-only choices, check-ins, a penalty-free exit, and visible verification for home tutors.
10. **Your protections:** matching to e-Shram, PM-JAY, state welfare boards and Udyam, with deep links.

**Blocked but important:** real payouts (merchant account), cross-border collection (PA-CB partner), advances on approved work (NBFC partner, MOD07), and ONDC B2B (network registration).

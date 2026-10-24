# ForKhatri master critique, October 2026

Date: 2026-10-06. Written by the lead editor from the eleven critique files and one research note in `docs/Critique/`, the repo-root `CLAUDE.md` and the owner-decision index in memory. There is no new research here. Every fact comes from those files, with their links kept. What a critic could not confirm stays marked **unverified**.

Plain words. **DPDP** is India's data-protection law (the 2023 Act, with Rules notified in November 2025). A **data fiduciary** is the body the law holds responsible for people's data. A **payment aggregator** collects money from buyers and passes it to sellers; the RBI (India's central bank) licenses it. **Escrow** is money held by a neutral party until a job is done. A **cold start** is an app that feels empty because too few people have joined.

**Verdict.** The critics found a well-built product with unusually honest design habits. The build has run ahead of three things code cannot fix: proof that families want it, a legal home for the money and the data, and people to run it day to day. Most serious risks are decisions only you can make, plus a short list of safety fixes that should not wait for those decisions.

---

## 1. Ten findings several critics reached independently

**1. Money cannot be collected as designed, and no legal route is chosen.** Agreed by: Milavn C1; Money C1, C2, C4, C5; Counsel C5, C6, C13; Vyapar H5; Growth 9. The RBI's September 2025 rules say an aggregator may collect only for merchants it contracts with, must use escrow, and "shall not carry out marketplace business." Milavn tickets, Vyapar milestones and Counsel payout holds all look like platform-held money. Razorpay's split-payment product may need Rs 40 lakh turnover (summarised by a fetch tool; verify). Counsel's 2 percent fee is below the gateway's own cost (about 2.36 percent). Best evidence: https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12896&Mode=0

**2. DPDP duties start about May 2027 and the platform has almost none of them.** Agreed by: Platform C3; Privacy C1, C2, C3, H1; Mangalya C3; Milavn H5; Vyapar M5; Counsel C10; AI 5; Growth 17; Architecture M2; research note. No consent notice, no privacy or terms link, no age question, no whole-account delete or export, no named fiduciary or grievance contact, no breach plan. Only Vyapar and Counsel have export and delete. Best evidence: https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/nov/doc20251117695301.pdf

**3. The community is small, so every module starts empty; pick a wedge.** Agreed by: Platform C10; Vyapar C1; Milavn H2; Mangalya C1; Counsel C12; Growth 1, 3; UX 7. Dev numbers (test data, "shape only") show Milavn used by 15 percent, Mangalya 12, Vyapar 4, Counsel 3. The roadmap's own member-validation phase is unticked. Best evidence: https://inc42.com/?p=566045 (Tata Digital lost Rs 4,974 crore in FY26 and is refocusing).

**4. "Verified" promises more than the checks deliver.** Agreed by: Mangalya C2; Privacy C4; Vyapar H2; Counsel C11; Growth 2; UX 12. Mangalya's photo badge is computed in the browser, and a code comment says anyone can post a passing result. Vyapar shows "Verified business owner" on a Rs 1,200 plumber job. Counsel's "Verified professional" can be earned with a mountaineering certificate. Nothing checks that a person belongs to the community, so "Our people. Verified." is not yet true. Best evidence: the code comment in `components/trust/interface.py` (Privacy C4); NIST on face-match errors for South Asian faces, https://nvlpubs.nist.gov/nistpubs/ir/2019/NIST.IR.8280.pdf

**5. Members cannot be reached, and phone members may not be able to sign in.** Agreed by: Platform C1, C7; Growth 4, 10; UX 2; Counsel C9; AI 16; Architecture (WhatsApp as sign-in channel). Production SMS is off, so phone members need a password, yet no password can be set or reset. The hub bell always says "You're all caught up". About 65 percent of dev members have only a mobile number. Best evidence: https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing (rates change from January 2026; re-check).

**6. Women's safety and fraud controls rest on self-declaration.** Agreed by: Milavn C2, H1; Mangalya H3, H5; Privacy H3, H4; Vyapar C2; AI 1. A man can set his answer to "woman" and enter a women-only circle (QA-RUN-safety #23). Tapping "Interested" lets anyone message every attendee. Scam rules read English text only, while fraud runs through phone calls and WhatsApp. Best evidence: https://www.usenix.org/conference/soups2018/presentation/sambasivan (shared phones, women's privacy in South Asia).

**7. Regulated professions carry real legal risk.** Agreed by: Counsel C1, C2, C3, C14; Vyapar (Bar Council notices); Privacy M4; Money C13. The Madras High Court (3 Jul 2024) held that lawyers soliciting through online intermediaries breaches Bar Council rules and said ratings and connection platforms are not allowed. Counsel shows a lawyer with stars, a named review and a price. Best evidence: https://indiankanoon.org/doc/169670340/

**8. Nobody has written down which community this serves or in which languages.** Agreed by: Mangalya C1; Growth 2, 14; UX 14; Platform C13; Vyapar C1. Your notes say Somavanshiya Sahasrarjun Kshatriya (Khatri, Pattegar). Public sources put its centre in north Karnataka and Maharashtra, but the app offers English, Hindi and Telugu, and seed data is Telugu-city and Punjabi-name shaped. Best evidence: https://ssksamaj.org/about-us/ and https://en.wikipedia.org/wiki/Pattegar

**9. "Samaj runs it" has no legal entity and no paid operations behind it.** Agreed by: Privacy H1, H2, H6; Growth 7, 9; Money C5, C6; Platform C12; Vyapar H6; Milavn H6; Mangalya M3, M4; Architecture M7. Verification queues, 2-hour takedowns and a grievance officer depend on volunteers who rotate. One technical owner holds all keys. Under IT Act section 85, people running an unincorporated body can be personally liable. Best evidence: https://www.argus-p.com/updates/updates/update-overview-of-the-it-intermediary-amendment-rules-2026/

**10. Hindi and Telugu are second-class, and voice is the weakest layer.** Agreed by: Platform C13, C14; Vyapar H1; Milavn H7; AI 3, 6, 13; UX 4, 5, 11; Counsel C15. Nearly every Hindi or Telugu phrase the AI critic typed into the hub returned "Not sure yet". Vyapar posts stay English inside a Telugu shell. Latin-script spacing and uppercase are applied to Telugu. Telugu speech recognition scored 18 to 22 percent word error at best. Best evidence: https://arxiv.org/html/2604.19151

**Also repeated:** small counts on the "ForKhatri in numbers" page can identify people (Platform C9, Money C15, Privacy H5, Mangalya M3); place search breaks OpenStreetMap's policy (Milavn H4, Architecture H8, https://operations.osmfoundation.org/policies/nominatim/); "From Rs 590 a month" is really Rs 7,079 up front (Money C8, Mangalya H4); five modules feel like five products (UX 1, Growth 10); parent-made profiles on a child's number (Platform C4, Mangalya C3, Privacy M3).

---

## 2. Disagreements and weak evidence

**Where critics disagree**
- **The wedge.** Growth guesses Milavn plus Mangalya through chapters. Mangalya's critic warns the matrimony pool may be too small until the real count is known. Vyapar's critic prefers a Khatri business network. Milavn's asks whether it is a Samaj calendar or an open meetup network. Architecture says launch one module. None has demand data.
- **Per-module member ids.** Platform recommends them. The research note says they help little while all modules are first-party, because phone, email and name still link people.
- **Dark or light.** The platform critic says test dark-only in daylight; UX says elders and outdoor use favour light; Counsel is near-black, though you rejected a dark look for Vyapar.
- **Isolation.** Architecture says merge Milavn, Vyapar and Counsel into one deployable and isolate only Mangalya and payments; Privacy leans towards more separation.
- **Fee size.** Counsel says "clearly below 10 percent", Money says 5 to 8, Milavn one published fee on paid tickets, Vyapar a flat membership. Nobody has modelled it.
- **Voice.** UX and AI agree browser voice is unreliable; AI asks whether WhatsApp or a phone call reaches more elders, UX says pictures and plain labels may serve more people sooner.

**Weak evidence.** Every critic says the shared web-search allowance ran out. The AI critic only saw fallback rules (all AI keys are placeholders), so Claude's behaviour in Telugu, Hindi and Hinglish is untested. The platform critic never opened the public tunnel, and Architecture did not test the dangerous endpoint from outside. The Counsel booking click was denied and Money could not open Mangalya `/plans` through a tunnel. The 124 dev members include QA accounts, so never quote that figure. Cashfree prices, the UPI fee change and GST/TDS rates are secondary sources only.

**Legal and tax claims to confirm with a lawyer or chartered accountant before relying on them**
1. RBI Payment Aggregator rules: whether MOD06 or ForKhatri would be one; the no-marketplace clause; ticketing named as covered (unverified in primary text); whether Counsel's 24-hour payout hold or Vyapar's 14-day auto-release counts as escrow.
2. Razorpay Route needing Rs 40 lakh turnover; manual payout as the pattern the rules target (inference).
3. GST on tickets, matrimony subscriptions and Counsel fees; GST collection (0.5 percent, section 52) and income-tax deduction (0.1 percent, section 194-O, and its overlap with 194J). The 2025 Income-tax Act renumbers sections, so all section numbers are unverified.
4. The UPI fee from 15 Oct 2026 (0.4 percent above Rs 2,000, capped at Rs 300); recurring-payment limits above Rs 15,000 and 24-hour pre-debit notice.
5. Whether coupons are regulated prepaid instruments; whether bill payment needs a Bharat BillPay partner.
6. Loans: lender-pays-the-referrer and neutral-offer rules (RBI Digital Lending Directions, 8 May 2025); the draft ban on unregulated lending; peer-to-peer, chit-fund and deposit-scheme rules, and whether a Samaj society is exempt (unverified).
7. Trust tax: related-party rules (donations over Rs 50,000), the 20 percent business-receipts limit, whether a trust for one community gets exemption (unverified), and FCRA for overseas donors who are not Indian citizens.
8. Which entity is the data fiduciary, signs the gateway contract and owns the code; volunteers' personal liability under IT Act section 85.
9. DPDP dates (13 Nov 2025, 13 Nov 2026, 13 May 2027), the rumoured cut to 12 months, the 72-hour breach report, and whether a notice in any of 22 languages suffices. Most critics cite Wikipedia or law-firm blogs; the MeitY text was not opened.
10. Whether a parent-made profile for an adult child is lawful; whether the "personal or domestic use" exemption covers the platform; whether the statistics exemption covers the numbers page. The Mangalya critic notes the decisions file wrongly calls a face embedding "biometric data" with top duties, because the Act has no sensitive class.
11. CERT-In 6-hour reporting and 180-day logs; the 2026 IT Rules deadlines (3-hour and 2-hour takedowns).
12. Bar Council Rule 36 and later Bar Council notices (partly unverified); SEBI adviser registration; National Medical Commission fee-splitting and 2020 telemedicine rules (recollection only).
13. 2026 gig-worker laws: is Vyapar an "aggregator" even with no fee; worker registration; child-labour rules; state minimum wage.
14. Whether salary-proof, ID or medical-test exchange after a match is lawful; police and fire rules for large events; gender-identity law for women-only spaces; Aadhaar or DigiLocker use by a private app; whether "From Rs 590 a month" counts as drip pricing under the 13-pattern dark-pattern guidelines (list not fetched).

---

## 3. Fix now: risky today whatever the strategy

| # | Risk | Where |
|---|---|---|
| 1 | **Dev back doors default ON.** Vyapar `DEV_MODE` defaults True, so fake member and admin headers work; an operator queue returned 200. Identity defaults to `ENVIRONMENT=development` with the sign-in code returned and `CHANGE_ME` keys. | `modules/MOD01-vyapar/vyapar-service/app/config.py:25`; `platform/identity-service` |
| 2 | **Public tunnels reach dev tools.** `/dev/v1/personas` listed the owner, president and secretary without sign-in via `/tunnel-proxy/identity/*`; `/dev/v1/sessions` opens a session for any member id. Untested from the internet. Keep "act as" for dev (your CLAUDE.md relies on it) but make it unreachable beyond localhost. | `platform/forkhatri-web/next.config.ts`; `scripts/tunnel.mjs` |
| 3 | **Crisis messages get a shrug.** Hub: "I want to die" returns "Not sure yet". Counsel: "end my life" returns a CA and a lawyer; "my husband beats me" a lawyer only. Show verified helplines first (Tele-MANAS 14416, 181, 112 are unverified; confirm). | `platform/forkhatri-web/lib/intent.ts`; Counsel `ai.py`; Milavn `discovery/nl.py` |
| 4 | **Misleading prices.** "From Rs 590 a month" is Rs 7,079 up front; Assisted is Rs 35,399, lists no deliverables, and `/cancel` refunds nothing; Gold sells "who viewed you" against the module's own no-visitor-lists rule. Screens say "held" for money no licensed rail holds. | Mangalya `/plans`, `plans.py`; Vyapar and Counsel money screens |
| 5 | **Labels that overclaim.** Photo badge; incognito chat "only the two of you can read this" while messages are scanned; Milavn "enforced"; Counsel "Reliability 100%" after one booking; Vyapar delete "removed everywhere". | Mangalya, Milavn, Counsel, Vyapar copy |
| 6 | **Women-only and messaging holes.** Self-declared answer; men can be invited; "Interested" unlocks messages and event chat; "Active now" on by default. | Milavn `circles.py`, `can_message` (migration 015) |
| 7 | **Counsel.** Lawyer ratings, named reviews and prices live; reviewer's full name beside a lawyer; a provider can be paid for a call nobody joined. Switch off legal, health, finance ratings and listings until opinions arrive. | Counsel `p/[id]/page.tsx`, `bookings.py`, `badges.py` |
| 8 | **Parent-made accounts.** Takeover risk on a child's number; level never rises from 0 to 1 after sign-in (bug); child's photos and horoscope stored before they know. | identity `provision_member`; Mangalya `profile.py` |
| 9 | **Small counts and "last seen".** Hide cells under 10; drop matrimonial fields from the open page; remove "last seen" from the admin member list. | `/v1/insights`; `/admin/members` |
| 10 | **QA data visible to real members** ("QA Adyar satsang"); migration 055 unapplied (untracked in git), migration 052 edited after it was applied. | Milavn migrations |
| 11 | **Web-framework advisory** (Next.js 16.3.5, critical, published 2026-09-22; likely not exploitable, the affected feature is unused); no frame-blocking or content-security headers; Counsel `/understand` unauthenticated and unlimited once AI is on. | all `*-web/package.json`; Caddyfile; Counsel API |
| 12 | **Deploy kit points to a folder that no longer exists** (`MOD03-mangaly`) and covers 2 of 5 modules, while the hub shows Vyapar and Counsel as open. | `deploy/docker-compose.yml`, `deploy/scripts/deploy.sh`, `.github/workflows/deploy.yml` |
| 13 | **Place search** breaks OpenStreetMap's policy; a share URL goes to a third-party QR site. | Milavn `PlacePicker`; `09a-external-dependencies.md` |
| 14 | **Agent harvesting and silent misreads.** Agents can open up to 300 families' contacts a month; Milavn smart-fill replaces the typed date with today. | Mangalya agents; Milavn `nl.py` |

---

## 4. Strategic questions only you can answer

Where a critic challenges one of your recorded decisions, both cases are shown.

**Q1. Validate demand or build more?** A: keep building toward seven modules (one community home, shared identity; but Tata Neu, Paytm and Gojek retreated from sprawl). B: pause new modules and interview 30 to 50 families in one city, with go or no-go numbers agreed first. **Recommend B**, which matches your own roadmap rule.

**Q2. Who is "ours", and which languages?** Options: the narrow Deccan Khatri and Pattegar community, a wider Khatri family, allies by invitation; add Kannada or Marathi or stay with three. **Recommend** getting the real count of marriageable members per city from the Samaj first, then a one-paragraph definition. Say "phone verified" until chapter vouching exists.

**Q3. Legal entity and payments route.** (a) A licensed aggregator or escrow partner with host onboarding. (b) One ForKhatri or Samaj entity as merchant for Samaj-run events only. (c) Hosts and consultants collect by their own links; the app records bookings. **Recommend** deciding the entity first (a Section 8 company or registered society; the Welfare Trust a separate registered body), using (c) for early paid features and (a) later. Never pool members' money. Two Samaj office bearers control money; the technical owner holds no money keys.

**Q4. Which modules to pause?** MOD05 duplicates the hub, MOD06 should not be member-visible until a partner kit exists, MOD07 stays referral-only. Counsel launches three to five unregulated areas. Vyapar is a Khatri business network first. **Recommend** one launch chapter with Milavn (a Samaj-curated calendar), Mangalya if the count supports it, and no building on MOD05 to MOD07. This is Growth's guess, not a proven answer.

**Q5. Women-only spaces.** Keep the self-declared answer (dignity, no ID burden, but unenforceable); a woman steward approves each joiner and a Samaj woman head vouches for new hosts; or document checks. **Recommend** steward approval, drop the word "enforced", and verify organisers before overnight trips.

**Q6. AI on or off, premium only?** (Your 2026-10-02 direction.) For: AI costs money and premium needs a reason. Against: a Telugu elder the free tier cannot understand never reaches premium, and cheap models make basic understanding almost free. **Recommend** free basic understanding in three languages, premium for depth, the rule "AI reads wishes, never rates people", a 200-phrase test per language, and the crisis check before any AI goes live.

**Q7. WhatsApp bridge?** None; sign-in codes and transactional notices only; or a full two-way bridge. **Recommend** the middle option plus public share links that preview without login. Keep an in-app inbox as the record; WhatsApp cost and policy are shifting (UX).

**Q8. Public birth time and place.** (Your 2026-09-27 decision.) For: families check kundlis before talking. Against: photo plus birth time and place identifies a woman to a stalker or a fake-profile thief. **Recommend** showing rashi, nakshatra and gotra up front and opening exact details when the family side shows interest. Also decide whether a hard "manglik: no" filter should exist.

**Q9. Screenshot blocking.** (Your 2026-09-29 rule.) For: signals seriousness. Against: blanks the page when a mother switches to WhatsApp and cannot stop a second phone. **Recommend** cover photos only, add per-viewer watermarks.

**Q10. Who runs it daily?** (Your 2026-10-02 direction.) For: legitimacy, free distribution. Against: rotating volunteers, personal liability, 2-hour takedowns. **Recommend** the Samaj governs and two or three paid operators run the queues under a written reply promise.

**Q11. Under 18s.** 18 and over with a date of birth at sign-up (small), or verifiable parental consent (large). **Recommend** 18 and over.

**Q12. Welfare Trust inside Finance.** (Your 2026-10-02 direction.) Critics say a Trust is a registered body with its own board that software cannot be, and a 2 percent fee may leave no surplus. **Recommend** an outside Trust, the app shows its ledger, and the promise is "a share of net surplus, published yearly", never a rupee figure.

**Q13. Hosting.** Free Oracle VM, or about $25 to 60 a month with support. **Recommend** paying before the first real member, with encrypted off-site backups and a restore drill.

Smaller calls: whether the Kartavirya Arjuna image stays the shared hub emblem (Growth 14, UX 14 respect your decision and suggest a neutral skin option); the wedding-arrangements push (Mangalya M2).

---

## 5. Thirty, sixty and ninety days

| | Product | Legal | Engineering | Community |
|---|---|---|---|---|
| **Days 0 to 30** | Community definition and language set; draft notice and terms in three languages; reword overclaiming labels | Hire a lawyer and chartered accountant for the section 2 list: entity, payments route, lawyer listings, gig status, fiduciary | Section 3 items 1, 2, 4, 5, 9, 10, 11, 12; crisis-helpline check; level 0 to 1 fix | Pick one launch chapter; get the marriageable-member count; start 30 to 50 family interviews |
| **Days 31 to 60** | Steward approval for women-only; message requests instead of open DMs; honest pricing; staged birth details if agreed; one shared inbox | Written opinions in hand; guardrails register updated | WhatsApp or SMS sign-in plus set and reset password; consent record; "Your data" delete and export; 18+ gate; run the skipped security step on Milavn; tests and a CI gate | Pre-load the chapter by hand (festival calendar, businesses, consultants named by Samaj heads); name paid operators and a woman safety lead |
| **Days 61 to 90** | Go or pause each module from pilot numbers; model fees per module including gateway cost | Grievance officer page; breach drill | Server speech and Hindi/Telugu test set; shared lexicon; TURN relay and voice-first Counsel; low-end phone test; web app manifest | Pilot with one number: weekly returning households; first "where the money went" page; chapter kit |

**Stop doing:** starting new modules before interviews and the legal route are settled; quoting dev counts in pitches; sharing public tunnel links while dev tools are reachable; saying "held", "enforced" or "verified" where the check is weaker; editing migrations after they are applied; letting each module build its own notifications, voice, rate limits and AI wrapper.

---

## 6. What is right and must be kept

- **Platform:** the opaque HttpOnly session cookie with stored digests; no account enumeration; "basic identity only"; the admin console's role terms, two-person approvals, audit log and audited contact reveal; honest "Planned" labels; the production guard in identity.
- **Vyapar:** one profile per member; the "nobody may charge people who apply" banner; "paid on time" confirmed by the person paid; every applicant gets a final status and every restriction a human appeal; multilingual search, which the AI critic calls the best behaviour in any module.
- **Milavn:** venue shown only after a confirmed spot (about 30 endpoints leaked nothing); no paywall on messages; mutual "would meet again"; no public ratings.
- **Mangalya:** the candidate decides; mutual preferences as hard rules; popularity weight zero; closed vocabulary for AI; no biometric storage; waiting periods; GST-inclusive prices; honest limits written down.
- **Counsel:** one-to-one only; badges that say what was checked; no paid placement; price and cancellation snapshotted; encrypted files; real delete and export; recording off for legal and health.
- **Money:** amounts in paise, idempotency keys, signed webhooks, a sandbox that refuses to run outside localhost; Milavn's "never holds money"; BLOCKER-002 refusing to claim to be a lender.
- **AI and voice:** Claude parses, a plain engine scores; the "What we understood" card; one question at a time with read-back.
- **Growth and architecture:** WhatsApp as partner; no ads; "your number is never shown"; the founder rule of not building everything; the shared integrations seam; checksummed migrations; fail-closed integrations.
- **UX:** conversational sign-in, language carried across modules, reduced-motion handling, Mangalya's calm look, and the "act as" switcher (dev only).

---

## 7. The critique files

| File | Top three findings | Confidence |
|---|---|---|
| CRITIQUE-platform | Phone sign-in cannot work in production; no change-of-number or recovery; no delete, export or consent ahead of DPDP | Medium. Screens plus code. Tunnel not opened; DLT, number recycling and notice language unverified |
| CRITIQUE-mod01-vyapar | Thin supply per trade; text-only scam defence; likely "aggregator" under 2026 gig laws | Medium. Telangana Act read directly; RBI, wage and child-labour law unverified |
| CRITIQUE-mod02-milavn | Paid events and RBI rules; women-only is self-declared; security step never run on shipped money, uploads and chat | Medium-high on code and QA runs; law points unverified |
| CRITIQUE-mod03-mangalya | Community too small and mismatched; forgeable face badge; parent-made profiles and an unaudited matching engine | Medium-high. Live walk as three personas; Hindi/Telugu depth and form submission not covered |
| CRITIQUE-mod04-counsel | Lawyer ratings probably unlawful; finance and medical gates light; provider paid for a call nobody joined | High on code, medium on law (medical rules from recollection); booking click denied |
| CRITIQUE-planned-money-governance | MOD06 would itself be an aggregator; 2 percent fee loses money; no entity receives the money | Medium. Razorpay fetched; Route, Cashfree and tax rates secondary; some screens not opened |
| CRITIQUE-lens-privacy-law-safety | No notice, terms or age gate; no whole-account delete or export; forgeable face badge | Medium. Self-described as not legal advice; several points unverified |
| CRITIQUE-lens-ai-voice-language | Crisis input shrugged off; silent wrong understanding; Hindi and Telugu fail on the free path | High for what was tested; AI mode never ran; no user quotes; helplines unverified |
| CRITIQUE-lens-growth-business-culture | Demand not validated; "Verified" not yet true; empty start and no WhatsApp bridge | Medium. Evidence tagged seen, secondary or unverified; social sites unreadable |
| CRITIQUE-lens-architecture-security-delivery | Dev back doors default on; deploy kit broken and covers 2 of 5 modules; one free VM, nightly dump | High on code and local checks; dev-build timings indicative; tunnel exposure untested |
| CRITIQUE-lens-ux-design-accessibility | Five products not one; bell not one system; accessibility and Telugu type unmanaged | Medium. Measured on screens, mostly Telugu; admin, chat and wedding screens not reviewed |
| RESEARCH-platform-auth-dpdp-2026-10 | DPDP phases; WhatsApp and SMS costs; phone recycling and pre-hijacking | Lower. Written after the platform critic finished; secondary sources; Gazette not checked |

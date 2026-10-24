# Critique: MOD04 Counsel

Written 6 Oct 2026. Read-only review of `modules/MOD04-counsel/` (BACKLOG, service routes and components, web room code), `modules/modules.md`, the owner rules in memory, and the live screens at 390px (home, Discover, one expert profile, booking step 1). Sources were fetched on 6 Oct 2026. Anything I could not confirm is marked **unverified**.

**Limits of this review.** The web-search budget was used up, so regulator pages and Reddit were mostly out of reach. Several legal points below rest on my background knowledge and are flagged for a lawyer or CA to confirm. The browser walk also stopped early. The permission system denied my click on the booking page (and the next navigation), so I did not push past it. Not seen on screen: 1280px width, Bookings, Consult, Notifications, Saved, the call room and the language switch. Those are judged from code only.

## 1. What I understand Counsel to be

Counsel is a paid one-to-one advice marketplace inside ForKhatri. A member describes a problem (or browses 26 areas). They book a 15-minute-granular slot with a verified consultant, pay up front, and meet in Counsel's own browser WebRTC room (video or voice, notes, files, optional recording). Counsel also sells paid written questions, 1 to 3 cheaper follow-ups, and "available now" instant consults. Ranking is rule-based (relevance, verification, experience, Bayesian rating, reliability), with no paid placement. The fee is 2%, refunds follow a snapshotted 24h/6h policy, payouts are held 24h after completion, and badges are earned by numbers. Group formats are Milavn's, there is no platform video service, and the payment, notification and AI vendors are not yet chosen (B1, B2, B7). It is well built. My concerns are what sits outside the code: law, money, networks and the community.

## 2. Critiques, ranked

### Critical

**C1. Lawyer profiles with ratings, prices and reviews are probably unlawful in India.**
- Claim: The Madras High Court held on 3 Jul 2024 that advocates advertising or soliciting through online intermediaries breaches Bar Council Rule 36 and is misconduct. It said intermediaries "are estopped from taking shelter under section 79 of the IT Act". It said approved directories may carry only permitted details, not rating systems or connection platforms. It ordered Quikr, Sulekha and Justdial to remove violating content and told the BCI to start disciplinary action ([P.N. Vignesh v. Bar Council, Madras HC](https://indiankanoon.org/doc/169670340/), read 6 Oct 2026; I found no sign of an appeal in that text).
- Screen evidence: Arjun Nair's profile shows a 4.0 star rating, a named review, a ₹1,500 price, "Book this" and milestone badges.
- Why it matters: A Khatri lawyer could face discipline for being on Counsel, and the Samaj brand carries the exposure.
- Recommend: Get a written opinion before any legal consultant goes live. Until then, hide ratings, reviews and badges in Legal, or list legal advice as a free "find an advocate" directory. This is also a cross-module issue, because Vyapar lists professionals too (C14). Effort M.

**C2. Investment and finance advice is regulated, and the "Finance & Tax" gate is too light.**
- Claim: In seed rules, `finance` needs only identity and qualification, while `investment` in India needs registration. A CA in Finance & Tax can drift into "where should I invest", and the module has no keyword or topic guard. SEBI treats unregistered paid advice seriously. In January 2026 the Securities Appellate Tribunal kept a ₹100 crore deposit requirement against a trading academy that sold stock recommendations through WhatsApp groups ([Avadhut Sathe Trading Academy v. SEBI, SAT, 22 Jan 2026](https://indiankanoon.org/doc/109328994/)).
- Why it matters: Members trust a "verified" label with their savings.
- Recommend: Require a SEBI IA/RA registration number, with a register lookup (B3), for any service that names securities, funds or portfolios. Add a "this is tax and accounts, not investment advice" boundary to Finance services. Review whether the platform is itself exposed (**unverified**; ask counsel). Effort M.

**C3. Medical and mental-health advice: a percentage fee to the platform may be a problem, and nobody has checked.**
- Claim: My recollection is that the NMC Code of Ethics (clause 6.4) bars doctors from commissions and fee-splitting, and that the 2020 Telemedicine Guidelines put duties on platforms and on the doctor (registration number, scope). **Unverified.** I could not open the NMC or MoHFW text (403/404), and Indian Kanoon had no case on it. Counsel takes 2% of each fee, and it also covers "health" and "mental-health".
- Why it matters: Doctors who take part risk their registration. Members could take advice for prescriptions.
- Recommend: Keep health and mental health switched off at launch. Get a medical-law opinion on whether a flat listing fee, rather than a percentage, is safe. Effort S (defer) to M.

### High

**C4. A provider can be paid for a call that never happened.**
- Claim, from code: `auto_progress` marks every confirmed booking in progress at its start time, whether or not anyone joined. It completes it 24h after the end, making payout eligible (`bookings.py`). `no_show()` never checks the recorded `session_event` joins, so a consultant can claim "client did not turn up" and still be paid. Either party can press "complete".
- Why it matters: This is the failure ordinary members fear most, and it will happen in a small community where people know each other.
- Recommend: Decide attendance from join and leave events. Auto-complete only if both joined for at least a minimum time. If only one joined, auto-refund the other. Let a "no-show" claim be disputed within 24h before payout. Effort S/M.

**C5. Payments code will double-pay or lose track once a real gateway is connected.**
- Claim, from code (`money.py`, `bookings.py`):
  - Refund and payout idempotency keys end in a random token (`secrets.token_hex`), so a retry creates a second refund or payout.
  - `request_payout` writes `status='paid'` the moment the call is made, though real payouts are asynchronous and can fail or reverse.
  - Gateway calls are made inside open database transactions, so a rollback after a refund leaves the ledger wrong.
  - If a payer's money is captured after the 15-minute hold expires, there is no auto-refund path.
- Recommend: Use stable keys (booking id plus action). Give payouts pending, paid, failed and reversed states driven by webhooks. Use an outbox so calls happen after commit. Add a daily reconciliation job. Effort M.

**C6. A 2% fee loses money and funds no trust work.**
- Claim: Razorpay's standard fee is 2% per transaction plus 18% GST on that fee, about 2.36% ([Razorpay pricing](https://razorpay.com/pricing/), read 6 Oct 2026). Topmate charges 10% on profile sales and 20% on marketplace-sourced sales ([Topmate pricing](https://topmate.io/pricing), read 6 Oct 2026). Counsel's 2% (BACKLOG D5) is below the gateway cost, before verification, support, disputes, refunds on cancelled calls, or GST on its own fee. UPI collection may cost less (**unverified**).
- Why it matters: Verification, a human dispute desk and the Welfare Trust all depend on this revenue.
- Recommend: Price from cost. Show the split openly: gateway, running costs, and a named Welfare Trust share. Keep it simple and clearly below 10%. A low fee also leaks less, because there is little to gain by going off-platform. Effort S (decision).

**C7. No TURN server means some members cannot join their paid call.**
- Claim: The default is Google STUN only (`ICE_SERVERS`). Backlog B4 admits some office and mobile networks will not connect. TURN exists because direct connections often fail ([webrtc.org](https://webrtc.org/getting-started/turn-server)). I did not find a published share for Indian carriers (**unverified**). Cloudflare's standalone TURN is $0.05 per GB ([Cloudflare](https://developers.cloudflare.com/realtime/turn/)), so a relayed hour of 1:1 video is about ₹4, against a ₹1,200 session.
- Why it matters: Failed joins mean refunds and angry first impressions. Elders on Jio or office Wi-Fi are exactly who will meet this.
- Recommend: Buy TURN before any real session. Test on real Jio and Airtel phones (T8). Effort S.

**C8. Voice and phone beat video for this audience and for no-shows.**
- Claim: In 3.1 million scheduled appointments, video visits cut no-show odds by 15% compared with in-person (aOR 0.85), while phone visits cut them by 50% (aOR 0.5) ([J Telemed Telecare, 2025](https://pubmed.ncbi.nlm.nih.gov/38557212/)). That is healthcare, not paid advice, so treat it as a signal. Counsel's room also relies on `getDisplayMedia` and browser recording. MDN says screen capture is "not Baseline" ([MDN](https://developer.mozilla.org/en-US/docs/Web/API/Screen_Capture_API/Using_Screen_Capture)), and the backlog (T8) says iPhone full screen is unproven.
- Recommend: Make voice the default format. Add an optional "bring your own link or phone call" fallback so a failed room never blocks paid time. This respects the owner's no-platform-video rule. Effort M.

**C9. Reminders and no-show rules do not line up.**
- Claim: Reminders reach only the in-app inbox until WhatsApp or SMS is connected (B2), but a no-show forfeits the whole fee. Text reminders improve attendance in a 2024 meta-analysis of 13 studies ([Eur J Pediatr, Nov 2024](https://pubmed.ncbi.nlm.nih.gov/39279016/); paediatric, so indicative).
- Recommend: Do not enforce "no refund on no-show" until a reminder channel is live, or add a one-tap "I can't make it" link in the reminder. Effort S.

**C10. Reviews show the member's full name on sensitive profiles.**
- Claim, screen and code: Arjun Nair's (legal) review reads "Asha Reddy · 30 Sept 2026" (`p/[id]/page.tsx` prints `display_name`).
- Why it matters: In a tight community, a visible name beside a lawyer, a debt matter or a therapist is stigma. Also, a seeker's chat with a regulated professional falls under DPDP. The Act's phased dates are 13 Nov 2025, 13 Nov 2026 and 13 May 2027 (via [Wikipedia summary](https://en.wikipedia.org/wiki/Digital_Personal_Data_Protection_Act,_2023); **unverified against the Gazette**). AI recap summaries (B7) would send private notes to a foreign vendor.
- Recommend: Show first name and initial or "A member" by default, with the seeker's choice. Offer a "someone outside my town" option so people can consult away from their own neighbours. Ask for explicit consent before any AI summary of a legal or health note. Effort S.

**C11. "Verified professional" is a label a farmer and a trek leader can wear.**
- Claim, screen and code: The profile says "There is no single verified stamp", yet cards and profile milestones show "Verified professional" with "First consultation". The rule (`badges.py`) awards it when identity plus any one of qualification, certification or registration is verified. A mountaineering certificate meets it. Also "Reliability 100%" shows after a single consultation.
- Recommend: Rename it to say exactly what was checked, and drop it from the card. Hide percentages until there are about 10 consultations. Effort S.

**C12. Thin supply, padded screens.**
- Claim, screen: Home shows "1 person" for seven of eight areas, six live consultants, and the same four people listed twice (once under "People you have consulted" and again under "Trusted people"). Discover spends about half the first phone screen on filters before result one. BACKLOG T11 needs 30 to 50 real consultants across 26 areas, which is under two per area.
- Why it matters: Empty-feeling areas look "dummy" (your own rule, 30 Sep 2026).
- Recommend: Launch three to five areas where the Samaj has real supply (for example accounts and tax, business, careers). Have Samaj chapter heads recruit the first 30 by name. Remove duplicate lists and unavailable areas from the home page. Effort M.

### Medium

**C13. Tax and compliance are parked but gate go-live.** GST on the fee and TDS on e-commerce operators (my recollection: section 194-O, 0.1% after Oct 2024, **unverified**) are T3, open. RBI payment-aggregator rules on holding funds and delaying payouts are **unverified** and untouched in the backlog. Get a CA and a payments lawyer before choosing a gateway. Effort S.

**C14. Vyapar and Counsel overlap leaks in both directions.** Vyapar has "refer to Counsel" and free professional listings with per-post calling (my code search). A CA can win the lead free on Vyapar and skip paying Counsel. A lawyer on Vyapar faces the same Rule 36 issue as C1. Set one cross-module policy for regulated professions and for what Vyapar may show. Effort M.

**C15. Search is substring matching, in English-heavy form.** `providers.search` scores `t in hay` on folded text, so "tax" matches "syntax", and Telugu or Hindi spelled in English letters will miss. The natural-language box is rule-based until the AI key exists. Add token matching and a small Telugu/Hindi synonym list. Effort S/M.

**C16. Disclaimers appear late.** Legal, finance and health notices show only at the payment step (`book` page), and D2 (lawyer review of wording) is still open. Put the scope line on cards and profiles too. Effort S.

**C17. Free competition on advice.** Career and tech mentoring is free elsewhere (ADPList, **unverified**; its FAQ page returned 404 for me). T4 (a free short message before booking) is unbuilt. Add a free 10-minute intro or a pro-bono "Samaj seva" slot to build trust. Effort S/M.

**C18. Theme.** Counsel is near-black. You rejected dark "themed" looks for Vyapar (29 Sep 2026). Confirm that Counsel's dark look is deliberate. Effort S.

**C19. Client-side recording is fragile.** Only one browser uploads, up to 500 MB, over mobile uplink. A closed tab loses it. Consider voice-only recording or consent-based notes instead. Effort S.

## 3. New in the world

1. **Phone-first consults** cut no-shows by half in a 3.1M-appointment study ([PubMed 38557212](https://pubmed.ncbi.nlm.nih.gov/38557212/)).
2. **Cheap TURN** is now a commodity: $0.05 per GB at [Cloudflare](https://developers.cloudflare.com/realtime/turn/).
3. **Donating earnings.** Clarity's help centre lists "How do I donate my earnings?" ([clarity.fm/faq](https://clarity.fm/faq), 6 Oct 2026). That is a ready model for a consultant's Welfare Trust share.
4. **Market consolidation.** superpeer.com redirected to Skillshare on 6 Oct 2026 (reason **unverified**). Creator-advice marketplaces are volatile. Do not assume a vendor's survival.
5. **Enforcement is live.** The Madras HC order (Jul 2024) and the SAT ruling (Jan 2026) show that regulators and courts act on online advice, not only on offline advisers.
6. **Telugu and Hindi speech-to-text** (Bhashini, AI4Bharat) for captions and transcripts, already in B6. I did not verify current accuracy (**unverified**).
7. **DigiLocker / API Setu** for credential and identity checks, already in B3. Prioritise it above new features.

## 4. Rethink

1. **"The 2% fee is our advantage."** *For:* simple, low leakage, a good pitch to consultants. *Against:* it is below cost, funds no safety work, and sends nothing to the Welfare Trust. A 2% fee is a subsidy, not a business. Decide who pays the difference.
2. **"Our own video room."** *For:* control, privacy, no vendor. *Against:* it is the most failure-prone part of the module, and Indian users already run advice over WhatsApp calls. Voice-first plus a fallback keeps ownership without the risk.
3. **"26 areas, any expert."** *For:* the Samaj has many professions. *Against:* thin supply and regulated areas bring most of the legal risk. A narrow launch can add areas later.
4. **"Launch with regulated areas."** *For:* law, tax and health are where trust matters most. *Against:* C1 to C3. Start with unregulated areas and add each regulated one after a written opinion.
5. **"Consultant marks complete, 24h hold."** *For:* simple, fast payouts. *Against:* C4. Attendance-based release is fairer to both sides.

## 5. Do not change

- One-to-one only, with groups left to Milavn.
- Specific, per-dimension badges ("each badge says what was checked").
- The Bayesian average for Top rated, and no paid placement.
- Ranking explained plainly, with consultants able to see why they rank where they do.
- Price and cancellation rules snapshotted onto each booking.
- Encrypted private files, malware-scan hook, audit of every document view.
- Full refund when the consultant cancels or no-shows, and automatic refund on unanswered paid questions.
- Real data deletion and export in Counsel (T1).
- Two-person recording consent, and recording off for legal and health.
- The shared integrations library and the mock-only-on-localhost guard.

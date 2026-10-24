# Critique: the planned modules and the money layer

Date: 2026-10-06. Scope: MOD05 Dashboard, MOD06 Payment Services, MOD07 Loans & Finance, the Samaj Welfare Trust, `shared/forkhatri-integrations`, and today's payment code in Milavn, Mangalya, Counsel and Vyapar. Status words: "(fetched)" means I read the page on 6 Oct 2026; "unverified" means I could not confirm it (the shared web-search budget ran out mid-task, so some points rest on background knowledge and are marked).

## 1. What I understand the vision to be

ForKhatri is one sign-in and four live modules. Three more are planned. MOD05 Dashboard is meant to be the personal home plus "Local Information Intelligence" (government schemes, scholarships, health camps) plus a "Fair Exposure" ranking, read-only over every module. MOD06 Payment Services is meant to do bill payments and a cross-module coupon/benefit system, and every other module is meant to call it to collect money (`shared/forkhatri-integrations` already has a `payment_services` adapter waiting for it). MOD07 is a loans/finance referral marketplace, not a lender, with an open regulatory blocker (BLOCKER-002). The Samaj (community heads) runs the app, and a Samaj Welfare Trust inside MOD07 receives earnings and funds relief, scholarships and health camps, with the treasurer and two-person approval. No vendor is connected; every module has a sandbox. On screen today: the hub shows "Payment Services: Planned" and "Loans & Finance: Planned"; the admin console (Ramesh, president) has Today, Queues, Members, Approvals, Team, Organisation, Audit log and Modules, and no money view at all. Please correct me where I have this wrong.

## 2. Critiques, ranked

### Critical

**C1. MOD06 as designed would itself be a Payment Aggregator, and "shall not carry out marketplace business".**
- Claim: modules.md and the library contract make MOD06 collect money from members for other modules and (via `create_payout`) pay consultants and organisers. The RBI Master Direction on Payment Aggregators (15 Sep 2025, fetched) defines a PA as an entity that aggregates customer payments to merchants and "subsequently settles the collected funds to such merchants", requires non-bank PAs to hold ₹15 crore net worth at application and ₹25 crore by year three, and demands a separate escrow with a scheduled bank. It also says "A PA business shall not carry out marketplace business." A platform that holds buyers' money and later pays sellers is that activity. Source: https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12896&Mode=0
- Why it matters: ForKhatri cannot lawfully pool the money of Khatri families, even briefly, with its own bank account. Existing aggregators were told to apply by 31 Dec 2025 or wind down by 28 Feb 2026.
- Recommendation: redefine MOD06 as a thin ledger and orchestration layer over a licensed aggregator's split/escrow product. It must never be the account where money rests. Write this as a design rule in modules.md (ADR-008 says "ledger/PCI", which is ambiguous).
- Effort: M (design) / no code yet.

**C2. Vyapar milestones and Counsel payout holds already look like platform-held funds.**
- Evidence: `contracts.py` calls "held" and "released" "ledger facts, not escrow or payouts" and lists a payout adapter as future work; Counsel holds consultant earnings for 24 hours (`payout_hold_hours`) and refunds on rules. Milavn's header says it "never captures, holds or refunds money itself", which is the correct stance; the other three do not state it.
- Why it matters: the day a real gateway is connected, "held" becomes money in someone's account. Whose account, and which licence, must be decided before B1, not after.
- Recommendation: adopt Milavn's stance for all modules: a module records instructions; the gateway holds the money under its own split/escrow, with delayed settlement. Remove "held" language from UI until then.
- Effort: M.

**C3. The 2% Counsel fee loses money after gateway costs.**
- Evidence: Razorpay's standard page (fetched today) shows 2% on every domestic method, including UPI ("Zero MDR, 2% platform fee applies"), 18% GST on that fee, and Route (split payments) at 0.1% plus platform fee. On a ₹1,000 booking Counsel keeps ₹20 and pays about ₹23.60 to the gateway (₹20 plus ₹3.60 GST), at least ₹1 for Route, and ₹3.60 GST on its own fee if registered (today `tax_minor` is 0). Net is about minus ₹8 per ₹1,000 before support, TDS compliance or refunds. Razorpay does not give the fee back on a refund: "fees and taxes charged for a captured payment are not reversed" (https://razorpay.com/docs/payments/refunds/faqs), so every refunded booking costs ForKhatri about 2.36% and the cancellation policy (50% back from 6 hours) makes it worse. https://razorpay.com/pricing/ . Cashfree lists 1.95% on cards, Easy Split at 0.20 to 0.25%, payouts at Rs 3 to 15 each, and a 0% offer up to Rs 20 lakh GMV for new merchants until 31 Mar 2027 (https://www.cashfree.com/payment-gateway-charges, reported by a research helper, not read by me): so vendor choice moves the margin by about 1 point, which is the whole fee. Negotiated rates exist, but a new community platform will not get them at launch.
- Why it matters: the pitch ("2% against the 10 to 50% others take") is the Counsel selling point and it is also the reason the Trust would receive nothing from Counsel.
- Recommendation: model unit economics per module with gateway cost as a line item (Quote already has `processing_fee_minor`; it is hard-coded to 0). Set the fee as "platform fee plus gateway cost", or make it 5 to 8% and show it. Decide D5 with numbers.
- Effort: S.

**C4. Razorpay Route may not be available to a new platform at all.**
- Evidence: Razorpay's Route documentation (fetched, summarised by the fetch tool, please verify) says Route access requires domestic turnover of ₹40 lakh or more shown in GST returns, and that users who missed the 31 Dec 2025 compliance submission lost Route. https://razorpay.com/docs/payments/route/ . This matches the RBI PAN rule for merchants above ₹40 lakh. A second read of the same documentation by a research helper agrees, and adds that below the threshold Razorpay suggests settling to your own account and paying out manually, which is the pattern PA rules target (inference; take legal advice).
- Why it matters: the library backlog (V2) assumes "RazorpayX, Cashfree Payouts or a marketplace product" will simply be available. A new Samaj app with 124 members will not meet a ₹40 lakh turnover test.
- Recommendation: before choosing a vendor, ask three vendors in writing: can a new entity with no turnover split payments to individual consultants? If not, start with a pass-through model (consultant is the merchant of record with their own payment link) or a licensed escrow partner. Add a vendor questionnaire to BACKLOG.md.
- Effort: S.

**C5. Nobody has decided which legal entity receives the money.**
- Evidence: a merchant account needs a legal entity (company, LLP, trust or society) with PAN and a bank account. BLOCKER-002 (finance posture) is open, the owner says the Samaj runs the app, the Trust is "proposed", and the admin console shows Krishna as sole owner (स्वामी) who alone can switch modules on or off (Admin > Modules, seen on screen). So who signs the gateway contract, who is the data fiduciary, and who owns the code are all open.
- Why it matters: this is upstream of every payment choice (V1, V2, GST registration, TDS, DPDP). It also decides whether "Samaj heads run the app" is real, or whether one technical owner holds root.
- Recommendation: decide the entity structure first (see C6), and record it as a Guardrail. Give a Samaj-appointed role (treasurer plus president, two-person) control over the merchant account and settlement bank account, with the technical owner holding no money keys.
- Effort: M (legal advice needed).

### High

**C6. A for-profit app channelling "earnings" to a Trust creates tax and related-party risk.**
- Evidence (secondary sources; get a CA's confirmation): under the Income-tax Act's related-party rules (s.13(3) of the 1961 Act, now carried into the 2025 Act; section numbers unverified) anyone who donates more than ₹50,000 to a trust becomes a "specified person", so dealings between the app company and the trust must be at arm's length. https://taxguru.in/income-tax/transactions-charitable-trust-persons-section-13-3-income-tax-act-1961.html . Trusts doing "business" lose status if commercial receipts exceed 20%. https://www.taxmann.com/post/blog/apex-court-interprets-definition-of-charitable-purpose-used-in-sec-215-for-tax-exemption/ . If the Trust itself collects subscriptions it could breach that limit; if the company donates, the company's deduction and the Trust's 12A/80G need care. Registrations carry over to the new Act (https://www.taxmann.com/post/blog/opinion-no-policy-changes-in-trust-taxation-old-income-tax-law-v-s-new-income-tax-law).
- Why it matters: the film script (docs/Marketing/pitch-video/01-script.md line 110) promises "What we earn returns to us." A Samaj president will sooner or later ask who audits that sentence.
- Recommendation: choose one clean model: (a) the app is owned by the Samaj body or a Section 8 non-profit, and fees are cost recovery with surplus applied to objects; or (b) a for-profit company with a fixed, published percentage donation covenant. Do not mix. Keep MOD07 out of the Trust; the Trust is an owner of money, not a "finance product".
- Effort: M.

**C7. Welfare fundraising already exists in Milavn with no link to the Trust and no 80G.**
- Evidence: migration 034 (`community-fundraisers`) lets any circle organiser raise money "for a hall, a scholarship, a family in trouble". Money "does not move here"; `mark_paid` is organiser-attested. FCRA matters if donors include foreign citizens of Indian origin (OCI/PIO); NRIs who are Indian citizens are not foreign contributors. https://citizenmatters.in/getting-fcra-registration-for-your-non-profit-bangalore-foreign-funds/ . Donation crowdfunding has no dedicated regulator; platforms fall between income tax, FCRA and payments law. https://anantamias.com/crowdfunding-india/
- Why it matters: two channels will compete (organiser UPI vs Trust), with no receipts that donors can claim. Fraud in "family in trouble" drives are the classic community failure.
- Recommendation: one rule: all drives pay into a named account of a registered body, never an individual's UPI; drives are approved by a second person; the app prints an 80G receipt when the Trust is registered. Until then, label a drive "a pledge among friends".
- Effort: M.

**C8. Mangalya's "From ₹590 a month" is an upfront ₹7,079.**
- Evidence (screen, Asha, Mangalya home, 6 Oct 2026): "Gold: From ₹590 a month", "Assisted: From ₹2,950 a month". The catalogue (`plans.py`) shows these are the 12-month prices incl. 18% GST (₹5,999 × 1.18 ÷ 12 = ₹590; ₹29,999 × 1.18 ÷ 12 = ₹2,950), charged at once (₹7,079 and ₹35,399); the 3-month Gold is ₹833 a month. `/cancel` says "nothing is refunded here". Plans with `auto_renew` exist but no mandate rail is built. Recurring card debits above ₹15,000 need extra authentication and a pre-debit notice at least 24 hours ahead (Razorpay docs https://razorpay.com/docs/payments/recurring-payments/upi/ and NPCI https://www.npci.org.in/product/upi/upi-autopay, via research helper), so a ₹35,399 Assisted renewal cannot be a silent debit.
- Why it matters: ₹35,399 for matchmaking help from families in Hyderabad is serious money. The consumer authority treats "drip pricing" and unclear refund terms as dark patterns (Guidelines for Prevention and Regulation of Dark Patterns, 2023: unverified here).
- Recommendation: show the total first, the monthly price second; show GST; state the refund rule before payment; build a 7-day goodwill refund; default auto-renew off.
- Effort: S.

**C9. Loans & Finance, "referral only", still needs four tests.**
- Evidence: RBI Digital Lending Directions, 8 May 2025 (fetched): fees to a lending service provider must be paid by the lender, not collected from the borrower; money flows straight to the borrower's account and repayments straight to the lender, with no control "directly or indirectly" by an LSP; lenders must publish their LSPs and apps; since 1 Nov 2025 multi-lender platforms must show all matching offers and be "unbiased and objective" (Mondaq summary). https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12848&Mode=0 . The draft Banning of Unregulated Lending Activities bill (Dec 2024; I found no evidence it passed) proposes 2 to 7 years in prison and up to ₹1 crore fine. https://www.businesstoday.in/amp/personal-finance/banking/story/unregulated-lending-govt-proposes-bill-to-oversee-unregulated-loan-apps-rs-1-cr-penalty-10-yr-jail-suggested-458129-2024-12-21
- Why it matters: the Samaj name lends trust, so a mis-sold loan harms the community's name, not just a vendor's.
- Recommendation: resolve BLOCKER-002 as "lead-generation only, regulated partners only, no fee from members, no Samaj-guaranteed loans, no ForKhatri-held repayments". Add a rule that Mangalya "wedding arrangements" never cross-sell loans (stage-based triggers on a wedding are a debt trap; owner policy decision).
- Effort: M.

**C10. Do not let "community credit" drift in.**
- Evidence: the natural next idea after a Trust is a samaj chit fund, member-to-member lending or deposit scheme. Chit funds need state registration (Chit Funds Act 1982 s.4, https://bhattandjoshiassociates.com/chit-fund-regulations-in-india-state-registrars-of-chit-funds/); anything with a promised return is a "deposit" under the Banning of Unregulated Deposit Schemes Act 2019 (https://prsindia.org/billtrack/the-banning-of-unregulated-deposit-schemes-bill-2019); matching lenders and borrowers is P2P NBFC activity (₹2 crore net owned funds, ₹50,000 per lender per borrower; RBI P2P Directions, 28 Nov 2025, https://rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=12934). Community institutions do fail: Kapol Co-operative Bank (a community bank, 1939) lost its licence in 2023 (https://en.wikipedia.org/wiki/Kapol_Co-operative_Bank); Saradha collapsed with 1.7 million depositors (https://en.wikipedia.org/wiki/Saradha_Group_financial_scandal); the 2010 Andhra microfinance crisis followed multiple lending and coercive recovery (https://www.downtoearth.org.in/amp/story/environment/microfinance-institutions-escape-charge-of-abetting-suicide-of-clients-38019).
- Recommendation: a Guardrails line: "ForKhatri will not accept, pool, guarantee or lend members' money." Welfare grants from the Trust are gifts, not loans.
- Effort: S.

**C11. GST, TDS and TCS are all unmodelled, and the Counsel/Vyapar split payment makes ForKhatri a tax collector.**
- Evidence: Counsel T3 and shared B8 leave GST and TDS to "an accountant". Mangalya computes 18% GST; Counsel and Vyapar do not (Vyapar `tax_rate_bp` per product). Under the e-commerce provisions, platforms that collect money for sellers have duties: GST TCS of 0.5% under Section 52 (since 10 Jul 2024, https://www.taxaj.com/learn/gst-on-e-commerce-operators-tcs-under-section-52-step-by-step-guide/) and TDS of 0.1% under Section 194-O (from 1 Oct 2024, https://taxguru.in/income-tax/section-194-o-amendment-lower-tds-rate-e-commerce-payments.html; 5% if the seller gives no PAN or Aadhaar; individuals under ₹5 lakh a year are exempt). Both are secondary sources; how 194-O interacts with 194J (professional fees) and whether GST is inside the 194-O base are unverified, and the 2025 Act renumbers sections. Pass-through of GST on consultants' services (18%, if they cross the registration limit) is also not modelled. Razorpay's own fee carries 18% GST (fetched).
- Recommendation: before real money, get a CA to write a one-page tax matrix per module (who invoices whom, who deducts what), then add the fields to the ledger. Invoices and TDS certificates are part of "payout".
- Effort: M.

### Medium

**C11b. UPI is no longer free from 15 Oct 2026, and the DPDP clock is running.** NPCI's framework (reported 16 Sep 2026, secondary sources, circular not opened) puts 0.4% MDR, capped at ₹300, on person-to-merchant UPI payments above ₹2,000, with small merchants under ₹1 lakh a month staying at zero and merchants barred from passing it on (https://www.scconline.com/blog/post/2026/09/16/npci-released-upi-mdr-faqs-explained/). Gold, Assisted, events and some Counsel sessions exceed ₹2,000, and these are the payments Khatri families make by UPI. Model it in C3. Separately, the DPDP Rules (notified Nov 2025) switch on notice, security, 72-hour breach reporting and children's consent on 13 May 2027, and consent managers on 13 Nov 2026 (https://www.amsshardul.com/insight/enforcement-of-the-dpdp-act-and-notification-of-the-dpdp-rules/); a MeitY proposal to shorten this was reported but not finalised (https://ksandk.com/data-protection-and-data-privacy/dpdp-act-rules-2026-compliance-deadline/). Financial and wedding data in one account makes MOD07 a high-risk data fiduciary use. Effort: S.

**C12. The shared payment contract has no concept of fees, splits, KYC state or tax.** `Charge` reports only reference and status; `ChargeRequest` has no payee, so a split cannot be expressed; `create_payout` takes a decrypted bank account in a dict; Mangalya and Counsel both pass `payer_id=""`, so the ledger cannot tie a charge to a member. Milavn's own contract uses `amount_paise` and `payer_member_id`, the library uses `amount_minor` and `payer_id`. Recommendation: add `payee_id`, `splits`, `gateway_fee_minor`, `tax`, `settlement_date` and fill `payer_id` before any adapter is written. Effort: S.

**C13. Coupons and "benefits" may be regulated instruments.** MOD06 plans coupons that "originate from Mangalya services". Closed-system prepaid instruments and cash-back have specific RBI rules (RBI Master Direction on PPIs; I could not verify the current text, unverified). Bill payments in India run through Bharat BillPay (BBPS) operating units; a non-bank app joins as an agent of one (unverified here, check NPCI BBPS). Recommendation: treat MOD06 bill pay as a white-labelled partner SDK, not a build; make coupons partner-funded discounts, not stored value. Effort: M.

**C14. MOD05 repeats the hub, and its "Local Information" feed is a liability.** The hub already is the dashboard (scope doc: "Dashboard is the hub itself"), while modules.md still lists MOD05 with six BRs. The Local Information pipeline (scholarship and scheme deadlines, blood drives) can publish stale or false notices under the Samaj name. Recommendation: a smaller MOD05 with named human editors, "last checked" dates, and official links only; defer "Fair Exposure" until paid boosts (Vyapar) exist so the rule has something to govern. Effort: M.

**C15. The members dashboard exposes small cells.** `/insights` (screen, 6 Oct): Counsel 4 members (3%), Vyapar 5, cities "0 known", "Women 0 of candidates". As it fills, a district count of 1 to 3 can identify a person. The owner's rule is open-to-all (respect it), but add a minimum cell size (for example hide below 10) and keep the "numbers missing" honesty. Effort: S.

**C16. Admin console has no money lens.** Approvals today cover bans and appointments only ("two people always: one asks, one decides"). There is no screen for revenue, refunds, payouts, disputes with money, Trust balance or donor receipts, and no reconciliation. Treasurer is a role in the appointment list but has no tools. Recommendation: a read-only Finance page first (money in, fees, refunds, payouts, per-module), with every release over a threshold requiring two Samaj office bearers. Effort: M.

**C17. Aadhaar and Account Aggregator are not available to a non-regulated app.** Private entities cannot compel Aadhaar since the Supreme Court's 2018 ruling (https://en.wikipedia.org/wiki/Aadhaar); RBI's NBFC-AA rules limit data users to regulated entities (https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=10598). So "KYC/compliance verification" in MOD07 (BR6) must be done by the partner, with ForKhatri holding consent and status only. This also supports data minimisation under DPDP. Effort: S.

**C18. Refund and dispute rules (D1) are a money decision, not a setting.** Counsel pays consultants 24 hours after completion, refunds 50% from 6 hours, nothing later. Without a dispute mechanism that the Samaj can see, the first angry parent will go to the consumer commission. Recommendation: put dispute, refund and payout rules on one screen that both sides see before paying. Effort: S.

## 3. New in the world

1. RBI Payment Aggregator Master Direction (15 Sep 2025): the rule above, https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12896&Mode=0
2. RBI Digital Lending Directions 2025 and the public Digital Lending Apps directory (since 1 Jul 2025): a member can check whether an app is tied to a regulated lender, https://www.newsonair.gov.in/govt-engages-with-rbi-regulators-to-curb-unauthorized-digital-loan-apps/
3. P2P Directions 2025 (28 Nov 2025), consolidating earlier rules: caps and escrow, https://rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=12934
4. NBFC Account Aggregator Directions 2025 (28 Nov 2025): consent-based data sharing, ₹2 crore net owned funds, https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12936&Mode=0
5. RBI authentication directions (25 Sep 2025): payment authentication changes, https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12898&Mode=0
6. New Income-tax Act 2025 (in force 1 Apr 2026): trust registrations carry over, https://www.outlookmoney.com/tax/cbdt-says-old-tax-approvals-lower-tds-certificates-will-stay-valid-under-new-income-tax-act
7. Banking Laws (Amendment) Act 2025 and the Multi-State Cooperative (Amendment) Act 2023: more oversight of cooperatives, https://www.scconline.com/blog/post/2025/08/01/provisions-of-banking-laws-amendment-act-2025-notified/
8. Participatory budgeting (Porto Alegre): real gains, but weak on the poorest and youngest, https://en.wikipedia.org/wiki/Participatory_budgeting . Idea for the Samaj: publish a simple quarterly "where the money went" page.

## 4. Rethink

1. **"Payment Services is a module members use."** For: bills and coupons raise engagement. Against: it is a licensed business with BBPS partners, thin margins and heavy support; the real need is a hidden settlement layer. Suggest: no member-visible MOD06 until a partner SDK exists.
2. **"The Trust lives inside MOD07."** For: one finance home, treasurer control. Against: a charity is a legal body with its own board, audit, 12A/80G and FCRA; software cannot be that body. Suggest: the Trust is an outside registered entity; the app only shows its ledger.
3. **"Earnings go to welfare."** For: motivates Samaj heads to invest. Against: with a 2% fee and a gateway costing 2.36% there may be no surplus for years, and promises beat reality. Suggest: promise a percentage of net surplus, published yearly.
4. **"Samaj heads run the app."** For: legitimacy and trust. Against: office bearers rotate, disputes in samaj trusts are common, and one technical owner currently holds all keys. Suggest: documented hand-over, two-person control of money and a published succession rule.
5. **"Loans for community members."** For: access to credit is a real need. Against: wedding and festival debt is the main trap; the Samaj's name makes it worse. Suggest: start with financial education and scholarships (Trust grants) before any loan link.

## 5. Do not change

- Amounts in paise, idempotency keys, signed webhooks, `PaymentsNotConfigured` and a sandbox that refuses to run outside localhost (library README). Excellent discipline.
- Milavn's "never holds money" stance and `none` as the default adapter.
- Counsel's ledger that separates gross, platform fee, processing fee, tax, payable and refund, and the price snapshot on each booking.
- Mangalya's rule that plans buy capability, never visibility, and GST as its own line.
- BLOCKER-002 itself: refusing to claim to be a lender is correct. "ForKhatri shall not assume regulated financial roles" should stay as written.
- The two-person approval pattern and audit log in the admin console.
- "Planned" labels on the hub and in the pitch script (never "live" for payments, finance or the Trust).

## 6. Evidence limits

- Screens: the hub (390 px), `/insights`, the admin console at 1280 px, the module switch page, and Mangalya home (plan card). My attempt to open Mangalya `/plans` through a public tunnel link was refused by the permission system, so I did not look at Compare plans, Milavn tickets/fundraiser or Counsel booking screens in a browser; those points rest on code (`plans.py`, migration 034, `money.py`).
- Secondary-source only: TCS/TDS rates, UPI MDR change, Cashfree fees. Unverified: GST on tickets and matrimonial subscriptions, BBPS and PPI rule texts, Cashfree/PhonePe/PayU fee pages, UPI Autopay limits, consumer-commission matrimonial cases, dark-pattern guideline text.

# MOD04 Counsel — 01 Business requirements

**Document status:** 2026-11-22, scope "as built". Written from the code, the live database, the screens, `BACKLOG.md`, `docs/Critique/CRITIQUE-mod04-counsel.md` (6 Oct 2026) and owner decisions in memory. Where something is planned or not built it says so. Facts that could not be verified are marked *unverified*.

Index of the set: README.md (this folder's map) · 01 business · 02 functional · 03 ux · 04 ui · 05 tests · 06 impact · 07 tech · 07a data model · 08 security/performance · 09 implementation · architecture.md · API-REFERENCE.md · GLOSSARY.md · RUNBOOK.md · TRACEABILITY.md · COVERAGE-REPORT.md.

## Contents
1. Vision and problem
2. Users, personas, journeys
3. Business model and revenue (built vs planned)
4. Value proposition and competitors
5. Business requirements BR-01 … BR-15
6. Owner decisions (dated)
7. Policies: trust, safety, refunds, privacy, moderation
8. Legal and regulatory notes (needs lawyer / CA)
9. Success metrics
10. Roadmap and backlog
11. Operating model
12. Risks and known gaps

## 1. Vision and problem
Counsel (MOD04) is a paid **one-to-one advice marketplace** inside ForKhatri, the Khatri Samaj umbrella app. A member who needs a specific answer (a GST question, a startup review, a farming problem) pays a verified person who has done it, for a fixed slot in a browser call room, with notes, files and a recap. Problem: community members get advice through unverified word of mouth with no price clarity, no accountability and no record.

Boundary (owner rules): Counsel is advice, not tuition (30 Sep 2026); group formats belong to Milavn; ForKhatri has no platform video-call service, so Counsel keeps its own peer-to-peer room (30 Sep 2026); ordinary business and professional discovery belongs to Vyapar, and only counselling, mentorship and guidance delivery belongs to Counsel (memory `vyapar-counsel-boundary`).

## 2. Users and journeys
| Persona | Who | Journey |
|---|---|---|
| Seeker | Any signed-in ForKhatri member | Describe need or browse area -> compare cards -> read profile -> pick slot -> pay -> get reminders -> join room -> recap -> review / follow-up |
| Consultant (provider) | A member who offers paid advice | Create profile -> add evidence and proofs -> submit -> admin review -> add services and availability -> accept bookings -> run calls -> complete -> request payout |
| Reviewer / Admin | ForKhatri staff with `counsel.admin` (or listed in ADMIN_MEMBER_IDS in dev) | Review providers and proofs, grant verification, decide disputes and reports, manage areas and settings |
| Platform | Identity service | Resolves sessions; may call internal export/erase |
| Visitor | Not signed in | Can see Home, Discover, profiles and the booking page up to sign-in |

## 3. Business model and revenue
| Item | Built today | Planned / unknown |
|---|---|---|
| Platform fee | `platform_fee_percent` setting, default 2. In code the fee is **taken out of the consultant's price**: gross = listed price, fee = 2% of it, payable = price - fee. Screens say "Includes ForKhatri platform fee (2%)" to the seeker and "ForKhatri keeps 2% of each paid consultation. The rest is yours." to the consultant. | **Owner definition (stated to the documentation lead 2026-11, exact day not recorded): the Counsel fee is an *additional* platform fee for using Counsel**, i.e. charged on top of the consultant's price, not carved out of it. **This differs from what is built** (see Gap G-01). Owner must confirm rate and whether it is shown as a separate line. |
| Fee on follow-ups and questions | Same 2% applies | BACKLOG D5 open |
| Gateway fee | Column `processing_fee_minor` exists, always 0 | Needs a real gateway adapter |
| Tax (GST on fee, TDS on payouts) | `tax_minor` column, always 0 | Needs CA (BACKLOG T3, critique C13) |
| Payments | **Sandbox only**: `PAYMENT_PROVIDER=mock` (default, localhost only) or `sandbox` via shared library; no money moves | Real gateway (Razorpay/Cashfree/Stripe) or MOD06; RBI payment-aggregator position unresolved |
| Payouts | Created through the same adapter; recorded `paid` immediately | Real async payouts, reversal, reconciliation (critique C5) |
| Premium by standing | Standing (new..distinguished) is computed and shown; changes neither price nor ranking | BACKLOG D4, D6 |

Revenue sources in the design: platform fee on consultations, follow-ups and written questions. Revenue also funds verification, dispute desk and (owner direction 2026-10-02) the Welfare Trust inside Finance (MOD07); none of that routing is built.

## 4. Value proposition and competitors
Verified, specifically-labelled expertise (each badge says what was checked), clear price, snapshotted refund rules, a proper working room, community accountability, five languages. Competitors reviewed 30 Sep 2026: Topmate, Practo, LawRato, Clarity.fm, Intro.co, MentorCruise, GrowthMentor, JustAnswer; discovery research 1 Oct 2026: Zocdoc, Upwork, Fiverr. Counsel's pitch to consultants was a 2% fee versus 10-50% elsewhere (critique C6 says 2% is below gateway cost; fee is under review, see G-01).

## 5. Business requirements
| ID | Requirement | Rationale | Status |
|---|---|---|---|
| BR-01 | Onboard consultants through a profile, evidence and admin verification, with granular badges instead of one universal "Verified" | Trust is the product; "verified" must say what was checked | Built |
| BR-02 | Let seekers find the right person by area, free-text need, filters, sorting, nearness, availability | Thin supply makes fit the bottleneck | Built |
| BR-03 | Show honest reputation: Bayesian rating, reliability, repeat clients, reply time, earned milestone badges | Avoid one lucky review winning | Built |
| BR-04 | Transparent price and fee, with price and rules snapshotted per booking | Prevent disputes about what was agreed | Built (fee model differs from owner definition, G-01) |
| BR-05 | Schedule safely: weekly windows, fixed slots, exceptions, notice, buffer, no double booking, custom-time proposals, available-now | Calendars are the core operational risk | Built |
| BR-06 | Collect payment up front, confirm, refund by rule on cancel, no-show, dispute | Trust for both sides | Built on sandbox only |
| BR-07 | Pay consultants for completed work after a hold, to a stored payout method | Consultants need reliable earnings | Built on sandbox only |
| BR-08 | Deliver the consultation in a private call room (video/voice, chat, shared and private notes, actions, files, optional recording by consent) | The product the buyer receives | Built; no TURN server |
| BR-09 | Offer follow-ups (1-3 check-ins) and paid written questions, one-to-one only | Continuity without becoming tuition | Built |
| BR-10 | Keep both sides informed: in-app notifications, two reminders, queued outbound channels | No-shows kill marketplaces | In-app built; outbound queued but undeliverable |
| BR-11 | Protect people: reports, blocks, disputes with admin decision, audit, compliance gating of regulated areas | Safety and legal exposure | Built |
| BR-12 | Respect privacy: export, delete (with safeguards), encryption, retention, audited document views | DPDP readiness | Counsel side built; platform-wide deletion not |
| BR-13 | Serve members in English, Hindi, Telugu, Marathi, Kannada | Community languages | Built (UI); AI parser keywords partly multilingual |
| BR-14 | Respect module boundaries: no group formats, no platform video, nothing that is Vyapar's ordinary discovery | Owner decisions | Built (by omission) |
| BR-15 | Show consultants how they are found and how to improve | Supply retention | Built |

## 6. Owner decisions recorded
| Date | Decision | Source |
|---|---|---|
| 2026-09-12 | Vyapar/Counsel boundary: only counselling, mentorship, guidance delivery is Counsel | memory vyapar-counsel-boundary |
| 2026-09-30 | Counsel is one-to-one advice, "This is not tuitions"; groups go to Milavn; packages become 1-3 follow-ups | memory counsel-one-to-one-groups-in-milavn; migration 008 |
| 2026-09-30 | No platform video-call service; Counsel keeps its own peer-to-peer room | memory no-platform-video-call-service |
| 2026-09-30 | Move payments/notifications to MOD06 / platform later, only when vendor accounts exist | same memory |
| 2026-09-30 | Custom time proposals; consultants earn milestone badges | migrations 003, 005 |
| 2026-10-06 | Marathi and Kannada added | migration 011 |
| 2026-10-02 | Welfare Trust inside MOD07 receives routed earnings (not built in Counsel) | memory samaj-runs-forkhatri-trust-in-finance |
| 2026-11 (day not recorded) | Counsel fee is an additional platform fee for using Counsel | assignment text; **not yet implemented** |
| standing | Every Telugu/Hindi string accurate and respectful; no hardcoded strings; real functionality not dummy; payment vendor blockers handled by building behind an adapter | memory |

## 7. Policies (as built)
- **Cancellation and refunds** (setting `cancellation_policy`, snapshotted onto each booking at creation): seeker cancels 24 h or more before: 100%; 6 h or more: 50%; later: 0%. Consultant cancels: 100%. Seeker no-show: 0% back. Consultant no-show: 100%. An unpaid booking cancelled becomes `expired`. Open decision D1.
- **Payout hold:** 24 h after completion (`payout_hold_hours`).
- **Review window:** setting `review_window_days` = 14 exists; the code does not read it (web asks for reviews for 30 days, `REVIEW_ASK_DAYS`). Drift noted.
- **Recording:** off by default; needs service `recording_allowed`, area rule `recording_allowed`, and consent of both people; legal and health areas disallow it.
- **Retention:** recordings 90 days, other files 365 days (settings).
- **Disclaimers** shown before payment in regulated areas (keys `disclaimer.legal|finance|investment|health`); wording awaits a lawyer (D2).
- **Moderation:** reports and disputes go to admin; suspended consultants have services paused.

## 8. Legal and regulatory notes — needs lawyer / CA
From the critique (mostly secondary sources, treat as *unverified*): Bar Council Rule 36 and the Madras High Court order of 3 Jul 2024 on lawyers soliciting via online intermediaries (C1); SEBI rules for investment advice (C2); NMC/telemedicine rules on fee-splitting for doctors (C3); RBI payment-aggregator and escrow rules (C13, master critique 1); GST on the fee and TDS 194-O (C13); DPDP Act phases (C10). Counsel currently lists legal, finance, investment and health areas with ratings and prices live in the seed data. All **needs lawyer/CA**.

## 9. Success metrics (proposed; none instrumented as dashboards)
Verified consultants live; searches to booking conversion (data exists: impressions, views, bookings); completed consultations; join rate of paid bookings; refund rate; repeat-client share; median reply time; disputes per 100 bookings; call-room failure rate (call feedback table). Dev database today: 8 providers (6 approved), 11 bookings all completed, 8 reviews; these are test data, not usage.

## 10. Roadmap and backlog
Open items live in `BACKLOG.md`: B1 real payments, B2 delivery vendors, B3 professional register checks, B4 TURN server, B5 two-way calendar, B6 transcripts, B7 AI key; T1 platform-wide deletion, T2 install ClamAV, T3 tax, T4 free pre-booking message, T5 time zones/currencies, T7 admin role via platform, T8 real-device call checks, T11 recruit 30-50 consultants; D1-D6 decisions. See 09 "What is NOT built".

## 11. Operating model
Who runs Counsel operations (review desk, dispute desk, support, who is the grievance officer) is **not recorded anywhere in the repo; owner must confirm**. Owner direction 2026-10-02: Samaj heads run ForKhatri.

## 12. Risks and known gaps
| ID | Gap / risk | Source |
|---|---|---|
| G-01 | Fee model differs from owner definition (additional fee vs deducted) | this audit |
| G-02 | Regulated areas live with ratings/prices/named reviews; legal opinion pending | critique C1-C3 |
| G-03 | Provider can be paid for a call nobody joined: auto-progress and auto-complete ignore join events; no-show claims are not checked against `session_event` | C4, code `bookings.py` |
| G-04 | Payments code not gateway-safe: random idempotency keys on refund/payout, payout recorded paid at once, gateway calls inside DB transactions, no late-capture refund | C5 |
| G-05 | No TURN server (only Google STUN), calls can fail on strict networks | C7, B4 |
| G-06 | Reviewer full name shown on profiles | C10, `p/[id]` |
| G-07 | "Verified professional" badge awarded for any one qualification/certification/registration plus identity | C11, `badges.py` |
| G-08 | Substring search ("tax" matches "syntax"); AI keywords limited | C15 |
| G-09 | Reminders only in-app until a delivery vendor exists, yet no-show forfeits the fee | C9 |
| G-10 | No automated tests for Counsel | this audit |
| G-11 | No row-level security; authorisation is in application code only | schema |
| G-12 | `review_window_days` setting unused | code |
| G-13 | `/understand` unauthenticated and unlimited once AI is on | master critique 11 |
| G-14 | Payment and refund idempotency/reconciliation absent | C5 |

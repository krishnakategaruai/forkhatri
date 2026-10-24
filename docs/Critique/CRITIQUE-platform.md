# Critique: the ForKhatri platform (entrance, identity, admin console, umbrella concept)

Date: 2026-10-06. Critic: platform lens. Read-only review of `docs/ParentApp/*`, `platform/identity-service`, `platform/forkhatri-web`, plus the running screens at 390px and 1280px (own browser context `critic-platform`; personas Asha Reddy and Ramesh Khatri; nothing submitted or changed).

**Evidence note.** The shared web-search budget ran out during this review, so research was partly done by a helper agent and by direct page fetches. A URL means a page was opened or its search snippet read (the helper marks which in its notes); anything marked *unverified* is from background knowledge or a single weak source and must be checked before it is quoted. I did not open the public tunnel URL (the browser blocked it), so any statement about what the public tunnel exposes is untested.

## 1. Understanding (please correct me)

ForKhatri is one mobile-first web app for the community. The member signs in once at the entrance with a mobile number or email and a six-digit code (password is the second path). The Identity & Trust Service keeps only basic identity: name, verified phone or email, language and a level (1 or 2). It issues one opaque HttpOnly cookie that every module resolves server-side through a 30-second cache. The hub lists the modules (Milavn, Counsel, Vyapar and Mangalya open; Payments and Loans & Finance planned), has an intent bar with a mic, a bell, an account sheet, and a "ForKhatri in numbers" page open to every member. Samaj office bearers run an admin console (roles by scope, suspensions, two-person approvals for bans and senior appointments, append-only audit log). Each module owns its own tiers, roles and deeper trust. The target is one Oracle free VM behind a Cloudflare Tunnel; nothing is deployed yet.

## 2. Critiques, ranked

### Critical

**C1. The audience is phone-first, but phone sign-in cannot work in production.**
- Claim: production runs `SMS_PROVIDER=disabled`. Phone code requests return `delivery_unavailable`, so phone members "sign in with a password" (`07-tech-reqs.md` TR19, `09-implementation.md`). Yet no password can be set or reset: the account sheet has no password row (screen, 390px), and "password reset/change endpoints" is listed as an open gap.
- Evidence: in dev data 65% of members have only a mobile number (insights screen). Email-only is a small minority of a community with many elders and shop owners.
- Why it matters: on launch day most members cannot get in. The first impression for the Samaj presidents is a failed sign-in.
- Do: pick the delivery channel before anything else. In India that means DLT-registered SMS and/or WhatsApp authentication messages (WhatsApp authentication messages were about Rs 0.13 each from 1 July 2025, per [MyOperator](https://support.myoperator.com/portal/en/kb/articles/whatsapp-has-shifted-to-per-message-pricing-effective-july-1-2025-based-on-message-categories-and-your-recipient-s-country-in-india-there-are-three-paid-categories); Meta's [pricing page](https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing) lists changes from 1 Jan 2026, so re-check; DLT rules *unverified*). Ship "set a password" and "forgot password" at the same time as the channel. Effort M.

**C2. Identifier lifecycle is missing: no change of number or email, no second identifier, no recovery.**
- Claim: `PATCH /v1/me` accepts only name and language. The account sheet shows Mobile and Email read-only (screen). `_member_by_identifier` finds a member by phone OR email, so someone who signs in once by phone and once by email gets two members, which breaks "one member, one identity".
- Why it matters: Indians change numbers often, and operators recycle numbers (TRAI 90-day rule, *unverified*). A recycled number plus OTP-only sign-in hands a stranger the old owner's matrimony profile. With nothing to change or recover, a member who loses a SIM loses the account.
- Do: add "add/verify a second identifier", "change number" (needs the old factor or a Samaj-assisted recovery with a two-person check), and a clear warning when a number has been silent for months. Effort M.

**C3. Account deletion, data export and consent are absent while the DPDP deadlines approach.**
- Claim: no delete, export or consent endpoint exists in the identity service (grep of `app/api/routes`); `00c`/`09` list "cross-module account deletion" as open. The account sheet has no Privacy, Terms, Help or Grievance entry.
- Evidence: the DPDP Act gives access, correction, erasure, withdrawal and grievance rights, and phases in on 13 Nov 2025, 13 Nov 2026 and 13 May 2027 ([Wikipedia summary](https://en.wikipedia.org/wiki/Digital_Personal_Data_Protection_Act,_2023), fetched 2026-10-06). The Rules were notified 14 Nov 2025 and the core duties start about 18 months later, around 13 May 2027 ([SCC Online](https://www.scconline.com/blog/post/2025/12/26/digital-personal-data-protection-rules-2025-key-highlights/)). The Act has no separate tier for sensitive data, so caste and horoscope details carry the same duties as a name; under-18s need verifiable parental consent. Confirm against the MeitY text, which I could not open. The notice may be given in English or any of the 22 scheduled languages (*unverified*). India's matrimony breaches show the risk: an alleged BharatMatrimony dump with caste and family fields in 2020 ([Cyble](https://cyble.com/blog/alleged-user-data-of-bharat-matrimony-for-sale-on-darkweb/)) and a Shadi.com breach with MD5 hashes ([HIBP](https://haveibeenpwned.com/Breach/Shadi)).
- Why it matters: Mangalya holds the most sensitive data in the app; a member (or a widow's family, or a withdrawn candidate) must be able to leave cleanly. Also, who is the data fiduciary (Samaj body, a company, the founder) is not written anywhere.
- Do: name the fiduciary, publish a notice in en/hi/te, build delete and export at the identity layer with a module fan-out. Effort L.

### High

**C4. Pre-provisioned accounts are a pre-hijack and consent risk, and the level never rises.**
- Claim: `provision_member` lets a module create an account for someone else's phone number at level 0 (a parent creating a profile for a child). The child later "signs in" with an OTP. That is the classic pre-hijacking shape (an attacker or well-meaning relative sets state on an account before the owner arrives). The owner must also give consent for data collected about them.
- Code bug: nothing in the identity service ever raises `identity_level` from 0 to 1 after the OTP is verified. Those members stay "waiting to sign in" in the console and dashboard (6 of 124 in the dev data) after they have signed in. Level 2 (ID document) has no code path at all.
- Do: raise to 1 on first verified OTP; on first sign-in show "A profile was created for you by X. Keep, edit or delete?"; add a time limit on unclaimed profiles. Effort S for the level fix, M for the claim step.

**C5. One id and one name across every module breaks contextual privacy.**
- Claim: the same `member_id` and real display name are used in Mangalya, Vyapar, Counsel and Milavn, and `members/lookup` returns names for up to 200 ids to any module. The hub also shows "Counsel / Mangalya, Visited 6 hours ago" (screen). On a shared family phone that reveals a matrimony visit or an advice-seeking visit.
- Why it matters: "trust is contextual" (PA-DEC-02) is right, but identity is not contextual. A woman's matrimony profile can be joined to her business listing by anyone who sees two databases, or by a breach of two.
- Do: use pairwise module ids (OIDC pairwise subject identifiers, the same idea as RFC 8176-era privacy advice; *unverified link*), per-module display names, and an option to hide "visited" on the hub. Effort M.

**C6. Suspension is all-or-nothing and has no appeal.**
- Claim: a platform suspension ends every session and blocks sign-in everywhere, and the error says "Contact ForKhatri support". There is no support or appeal screen anywhere on the hub or account sheet. One person can impose up to 30 days; only bans need two. The reason list has `underage` and `legal_order` but no member-facing explanation.
- Why it matters: a Milavn behaviour issue would lock a family out of Mangalya in the middle of a match. DPDP's grievance right and the IT Rules grievance duty (*unverified*) need a visible path.
- Do: add module-level restrictions before platform-wide ones, a "why and how to appeal" screen, and a response-time promise. Effort M.

**C7. The notification bell is an empty stub, and each module is rolling its own.**
- Claim: the bell opens "You're all caught up" (screen). The code says: "No notification service exists yet: an honest empty state". Meanwhile Milavn already has a notification component and the owner has decided messaging comes later through a shared utility.
- Why it matters: for this audience the channel is WhatsApp, not an in-app bell. A bell that is always empty teaches members to ignore it. Notification fatigue and quiet hours are not designed yet. WhatsApp has 500 million+ users in India ([ITVoice](https://www.itvoice.in/whatsapp-claims-over-500-million-active-users-india-the-largest-market), snippet), and marketing-type messages cost several times a transactional one, so alerts should be transactional or member-initiated. iPhone web push works only for an installed Home Screen app on iOS 16.4+ ([WebKit](https://webkit.org/blog/13878/web-push-for-web-apps-on-ios-and-ipados/)), so a WhatsApp or SMS fallback is needed.
- Do: build the shared inbox and per-channel preferences (in-app, WhatsApp, SMS, email), with module-level categories and quiet hours, before adding more modules. Effort L.

**C8. Sessions are built for one person on one phone; families share phones.**
- Claim: 30-day absolute sessions, no idle timeout, no list of devices, no new-sign-in alert, and only "Sign out" or "Sign out on all devices". The documented "higher-risk action needs re-authorization" is not implemented (no step-up endpoint) while payments, loans and paid Counsel are on the roadmap.
- Why it matters: a parent signs in on a daughter's phone to look at matches and never signs out. The next person can open the hub and the Mangalya module. Sambasivan et al. found that in India, Pakistan and Bangladesh phones are expected to be shared and women's activity open to family scrutiny, and that women cope by locking apps, deleting content or hiding visibility ([SOUPS 2018](https://www.usenix.org/conference/soups2018/presentation/sambasivan)). Their advice: multi-user designs and content hiding. Notification previews that show Mangalya content are the same exposure.
- Do: show "devices signed in", shorten the session on unfamiliar devices, add a step-up (re-code or passkey) for contact reveal, payment and delete. Effort M.

**C9. "ForKhatri in numbers" is open to all, and small counts can identify people.**
- Claim: the page and `/v1/insights` serve counts by city × gender × age band, plus Mangalya candidate stats ("looking for", marital status, mother tongue), to every signed-in member. At 124 members, a city with 2 women of one age band is a person. Today the page also fails soft: Mangalya and Milavn are "not reachable" so it shows "0 women, 0 men, 0% with a known city", and the member sees a half-empty picture (screen).
- Respectful note: the owner decided (2026-09-27) it can be open. I agree with openness for totals; the issue is only the small cells.
- Do: keep it open but suppress any cell under 10 (or merge it into the state), round small numbers, and never show matrimonial fields (marital status, "looking for") outside Mangalya. Also: today's 124 includes QA accounts, so do not quote it in the pitch. Effort S.

**C10. Seven modules at once for a community of this size is a cold-start risk.**
- Claim: the hub shows 4 live and 2 planned modules; in the dev counts Milavn is used by 15%, Mangalya 12%, Vyapar 4%, Counsel 3% (insights screen, test data, so treat as shape only). "Visited" means only a tap on the card.
- Why it matters: network effects are per module (a job board needs both sides, matrimony needs both sexes in a pool, events need hosts). Spreading a few thousand early members over four of them leaves each thin.
- Do: choose one wedge for the first Samaj launch (the one with the clearest repeat use), use the others as dormant doors, and track "weekly returning members per module", not "visited". Evidence: Tata Neu lost Rs 4,974 crore in FY26 and is refocusing on "financial services and loyalty" ([Inc42](https://inc42.com/?p=566045)); Analytics India Magazine called Indian super-apps "super flops" because incumbents own each vertical and each needs different expertise and regulation ([2023](https://analyticsindiamag.com/destined-for-doom-why-superapps-will-be-super-flops-in-india/)); Gojek left Vietnam in 2024 where it had under 1% of volume ([VTV](https://english.vtv.vn/news/gojek-quits-vietnam-to-focus-on-major-markets-20241008000658339.htm)). The nearest comparable, CommuTree (family tree, news, matrimony and social for many samaj groups), has 3.1 stars from 18 ratings and reviews saying "crashes immediately" ([App Store](https://apps.apple.com/us/app/commutree/id885813465)). Fair counterpoint: those were mass-market bundles; a bounded community is a different case, but each module still needs single-purpose quality.

### Medium

**C11. Operations claims are stronger than the setup.** The architecture promises 99.9% availability and RPO ≤ 5 minutes (`08-security-performance.md`), but the deploy kit takes a nightly `pg_dump` and R2 copy is optional ("strongly recommended"). Everything runs on one Oracle Always Free VM, behind a Cloudflare Tunnel whose terms allow termination "at any time, with or without notice" and give no SLA ([Cloudflare terms](https://www.cloudflare.com/terms/), snippet); Oracle reclaims an Always Free instance when CPU p95, network and (for A1) memory are all under 20% for 7 days ([Oracle docs](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm), fetched 2026-10-06). A quiet launch can trigger it. The identity service sits on every request, and an outage returns 503 to every module. Docker images, Compose and the real VM were never run (`09-implementation.md`). Do: state honest targets (RPO 24h), make off-site backup mandatory, and add a status line on the hub. Effort S.

**C12. Admin power sits with volunteers and the founder.** Presidents and secretaries can search every member and see "last seen 3 hours ago" for all 124 (screen, `/admin/members`); contact reveal is audited with a reason, which is good. But the `owner` role holds every permission and can act alone, first owner is a direct database insert, and the "append-only" audit table lives in the same database whose owner role can drop a trigger. Chapter heads in a caste body have local social power. Do: remove "last seen" from the member list, add a monthly audit-log hash anchored outside the database, and publish who holds each role. Effort M.

**C13. Language coverage and quality are narrower than the claim.**
- The admin console mixes scripts in Hindi ("नमस्ते, Ramesh", "Milavn मॉडरेशन" while the hub writes "मिलावन"). The owner's rule (respectful, accurate Indic text) needs a human reviewer pass here. "स्वामी" for the Owner role also reads as a religious title.
- The intent bar is a keyword table (about 60 terms). Telugu is inflected and many people type Hindi or Telugu in Latin letters ("shaadi", "naukri"); those will miss. Intents that land on Payments or Loans & Finance point to modules that are "Planned" (not tested by me).
- Only English, Hindi and Telugu: which other mother tongues the Somavanshiya community uses (Marathi, Gujarati, Kannada) is the owner's to confirm. Do: add a review step and a Latin-script (Hinglish/Tenglish) pass in the parser. Effort M.

**C14. Voice on the hub is a browser dictation button, not a guided conversation.** `CommandOrb.tsx` uses the browser's SpeechRecognition with `lang` set to hi/te/en; support and accuracy depend on browser and the audio goes to the browser vendor (*unverified for iOS Safari and Firefox*). Telugu is the weak spot: on the April 2026 Voice of India benchmark of real phone calls, the best engines (Sarvam, Saarika, Gemini) scored 18-22% word error in Telugu against 5-6% in Hindi, GPT-4o Transcribe scored 69%, and "no system meets [the 20% usability line] consistently" ([arXiv 2604.19151](https://arxiv.org/html/2604.19151)). Microsoft Research India found text interfaces "unusable by first-time low-literacy users" yet a live human operator was up to 10 times more accurate than text ([ToCHI 2011](https://www.microsoft.com/en-us/research/?p=161317)). This is the "mic that transcribes a paragraph" the owner rejected for modules (2026-09-30), and there is no spoken prompt. Do: choose an Indic-specific recognition engine on the server, offer a human-assisted fallback (a Samaj volunteer), decide whether the hub's mic is a convenience or the start of the guided flow, and show a one-line audio notice. Effort M.

**C15. Rate limits ignore shared mobile IPs.** 30 code requests and 30 password attempts per IP per 15 minutes is generous for a laptop, but a whole event hall on one carrier address could lock out real members (*unverified: carrier NAT behaviour*). Do: key the per-IP cap on IP plus device cookie, or raise it and rely on the per-identifier cap. Effort S.

**C16. Desktop hub and sign-in feel unfinished.** At 1280px the hub greeting wraps to one word per line ("Good / afternoon, / Asha") beside a tall emblem, and the account sheet floats over the module rows. The sign-in has a glowing orb while the hub is minimal black; the dark-only look is a strong choice for elders who read in daylight. Light/Dark/System is offered in the account sheet, which is good. Do: cap the greeting width and test in daylight. Effort S.

## 3. New in the world (to adopt or watch)

All links below were not re-checked this session unless noted; treat as leads.
1. **RFC 10017 / BCP 212, OAuth 2.0 for Browser-Based Applications (2026)** (verified: [rfc-editor.org/info/rfc10017](https://www.rfc-editor.org/info/rfc10017)). The platform already follows the backend-held-session advice; keep it.
2. **Passkeys** (FIDO Alliance, Google/Apple support): phone-biometric sign-in could replace OTP for elders who forget passwords. *Unverified for India adoption numbers.*
3. **WhatsApp authentication templates** as the OTP channel in India. *Unverified pricing.*
4. **DPDP consent managers** (phase from Nov 2026 per the Wikipedia summary above): design consent records so a consent manager can read them later.
5. **Pairwise pseudonymous identifiers** (OpenID Connect Core, section 8.1): one id per module.
6. **Small-count suppression and differential privacy** for published statistics (US Census disclosure avoidance is the best known case).
7. **Indic speech models** (Sarvam, Saarika, AI4Bharat IndicVoices with 7,348 hours across 22 languages, [arXiv 2403.01926](https://arxiv.org/abs/2403.01926); Bhashini): server-side Telugu and Hindi recognition. Benchmarks above.
8. **DigiLocker / offline Aadhaar XML** for a Level 2 document check, with a legal check on private-entity use first.

## 4. Rethink

1. **"One identity for everything is a feature."** For: no re-login, one place to suspend, one audit. Against: it joins matrimony, money and advice into one profile. Best middle: one login, pairwise module ids, per-module names.
2. **"Sign-in by OTP only is simple."** For: no passwords to forget. Against: SMS is not delivered, numbers get recycled, and shared phones keep sessions. Offer passkey plus WhatsApp code, and a recovery route through a Samaj officer.
3. **"All seven modules under one roof from the start."** For: one brand, shared trust. Against: thin pools and unfinished basics (notifications, recovery). Try one wedge module for the first chapter.
4. **"The Samaj runs it."** For: legitimacy and long-term care. Against: volunteer workload, local power, and no named fiduciary. Pair it with a small paid support role and published role-holders. One legal point worth a chartered accountant early: under section 2(15) of the Income Tax Act, a charity doing general public utility work can lose exemption if business receipts exceed 20% of total receipts ([TaxGuru](https://taxguru.in/income-tax/character-charitable-purpose-lost-receipts-business-activity-20-total.html), snippet), which bears on a Welfare Trust fed by platform earnings. (Owner asked to keep this out of pitches; this is for the build, not the pitch.)
5. **"Open numbers page builds belonging."** For: members see the community grow. Against: small cells and mixed matrimonial data. Keep open, suppress small cells.

## 5. Do not change

- One opaque HttpOnly session cookie, tokens stored as digests, no tokens in JavaScript.
- Anti-enumeration (same reply for known and unknown identifiers, dummy password check), rate limits in the database, and the Origin allow-list plus `return_to` allow-list.
- Basic identity only on the platform; profile data stays in modules (PA-DEC-01).
- The admin console design: role by scope with terms, two-person approval, "nobody acts on themselves", append-only audit, audited contact reveal, reason codes, Hindi/English/Telugu console. At 390px and 1280px it is clear and usable.
- Honest empty states ("coming" modules labelled Planned, "Mangalya not reachable" on the numbers page).
- Mobile hub: every module visible on the first screen, calm, readable; masked phone and email.
- Dev tools refused in production, with a guard and a separate test token.

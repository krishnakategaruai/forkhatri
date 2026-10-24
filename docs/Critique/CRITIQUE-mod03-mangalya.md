# Critique of MOD03 Mangalya (matrimony)

Date: 2026-10-06. Critic: one member of the critique team. Method: read the module's decisions, backlog, architecture, reference and research files; walked the live app in my own Chrome context as Asha (candidate, 1280px and 390px), Suresh Naidu (broker) and New Member (first-run), read-only; checked outside sources. Not covered: the Vikram and Lakshmi seats, light mode, the Hindi and Telugu screens in depth, any form submission. Note: the shared web-search budget ran out mid-task, so many sources came through direct page fetches. Items marked "repo research" are sources quoted in `docs/PreStartResearch/mangaly-2030-evidence-research.md` that I did not re-open.

## 1. What I understand Mangalya to be

A mobile-first and desktop web app for the community behind ForKhatri (the owner's notes say Somavanshiya Sahasrarjun Kshatriya, also called Khatri or Pattegar). The family is the unit: a parent can make a profile for a son or daughter, a Home Circle of relatives can answer requests and suggest people, and only mutual-preference matches appear. Matching is "AI-first": the family describes the partner in their own words, Claude turns that into a closed list of wishes with 1-10 importance, and a hidden 1-10 score orders Discover while members see only "Strong match / Good match" and checkable reasons. Horoscope (Guna Milan, 10 poruthams, Mangal dosha) is calculated in-house and can be a hard filter; birth time and place are always public. Verification is a browser face match against the member's own photos; ID and age checks were dropped. Candidates chat in an incognito, self-deleting chat; everyone else chats normally. Marriage brokers ("agents") are paid, verified, first-class users who can bring in non-members' biodata. Free / Gold / Assisted plans; after a match, a Wedding arrangements tab (OpenStreetMap places, later partner discounts) and Guides. Please correct me where this is wrong.

## 2. Critiques, ranked

### Critical

**C1. The market may be too small and in the wrong place, and the product does not say which community it serves.**
- Claim: ForKhatri's own notes define the community as SSK / Pattegar / Khatri. Public sources say it is a small, scattered, mostly endogamous group: "concentrated in the districts bordering Karnataka, Andhra Pradesh, Maharashtra", with "mostly found in significant numbers in Hubli, Gadag, Harihar, Belgaum, Bellary" (SSK Samaj Seva Samiti, https://ssksamaj.org/about-us/, fetched 2026-10-06). Pattegar is spread over Gujarat, Maharashtra, Rajasthan, Andhra Pradesh, Karnataka, Telangana and Tamil Nadu (https://en.wikipedia.org/wiki/Pattegar, fetched 2026-10-06). I found no verified population figure (unverified).
- What I saw: the app speaks English, Hindi, Telugu only; no Kannada or Marathi anywhere in the repo's requirements. Test people are Reddy, Rao, Naidu; the agent card reads "Khatri, Kapu, Reddy"; a guide says "Pelli choopulu"; cities are Hyderabad, Bengaluru, Vijayawada; the hero profile's dad "runs a Punjabi restaurant in Secunderabad". So the product is Telugu-city shaped while the community's own site puts its centre in north Karnataka.
- Evidence on pool size: matrimonial-ad data show "a very strong preference for within-caste" marriage (Banerjee, Duflo, Ghatak, Lafortune, https://www.nber.org/papers/w14958; data 2002-03, still the standard reference). Small-city users already complain: "less than 100 active profiles" (Jeevansathi review, repo research). The community already has matrimony services (SSKNA, https://www.sskna.org/; SSK Samaj, https://ssksamaj.org/).
- Why it matters: a matching engine, "For you" rows and a fairness report are worth nothing at 200 profiles; a bride in Hubli sees an empty app in a language she may not read.
- Fix: (a) get the real count of marriageable members per city and language from the Samaj before building more; (b) decide the language set (Kannada, Marathi) and the launch cities from that count; (c) decide in writing whether allied communities are allowed; (d) seed supply from the existing printed or WhatsApp biodata with each family's consent. Effort L.

**C2. The "Photos confirmed as their own" badge claims more than a browser check can prove.**
- Claim: DEC-V1-025 admits the comparison runs in the browser, so "someone who edits the page's code or replays the request can claim a pass", age is self-declared, and the review screen for failures does not exist. Yet the badge appears on the Home hero and every profile ("Photos confirmed as their own · Sept 2026", seen live).
- Evidence: NIST found elevated false-match rates for South Asian faces in one-to-one matching (NISTIR 8280, https://nvlpubs.nist.gov/nistpubs/ir/2019/NIST.IR.8280.pdf, 2019; follow-up 2022). Gartner predicted 30% of enterprises will see face verification as unreliable alone by 2026 because of deepfakes (https://www.gartner.com/en/newsroom/press-releases/2024-02-01-gartner-predicts-30-percent-of-enterprises-will-consider-identity-verification-and-authentication-solutions-unreliable-in-isolation-due-to-deepfakes-by-2026, 1 Feb 2024); a vendor reports camera-injection attacks up 741% on iOS in 2025 (https://signzy.com/blogs/liveness-detection-bypass-deepfake-injection, 7 May 2025, vendor claim). Siblings and cousins look alike, and a community this small is full of relatives.
- Why it matters: families will read the badge as "a real person, who is who they say". Fake-profile worry is the top review theme (34 of 129 reviews, repo research). 78% of Indian women report meeting fake profiles (Juleo/YouGov via https://feminisminindia.com/2025/12/01/from-rishta-to-risk-scams-and-ai-morphing-fueling-gendered-violence-on-indian-matrimonial-sites/, 1 Dec 2025).
- Fix: rename it to what it is ("Selfie matched these photos"), say it does not prove age or identity, run the comparison on the server, and add a cheap human step the Samaj can do (a video call or a Samaj-office reference) for the "verified" tier. Effort M.

**C3. Profiles made for someone who does not know yet.**
- Claim: a parent can create a profile for a child; the platform provisions a member on the child's phone number, stores photos, horoscope, income and family details, and keeps it up to 180 days before the child ever signs in (DEC-V1-019/020).
- Evidence: the Act's consent runs to the data principal, who here is the child; the "personal or domestic purpose" exemption covers the parent as an individual, not the platform as the fiduciary (my reading; get counsel). DPDP Rules were notified 14 Nov 2025 with full compliance due 13 May 2027 (https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/nov/doc20251117695301.pdf; https://dpdp.ind.in/rules.php). Women's profiles are far more often parent-run: 22% self-managed against 57% for men (Bharadwaj, https://priyankabharadwaj.substack.com/p/parent-tinder, 4 Mar 2021, repo research). A woman's wishes can be written by her mother and never read by her.
- Also a factual slip in the decisions file: it says a face embedding is "biometric data" carrying "the highest compliance obligations" under DPDP. The Act has no sensitive or biometric category (https://prsindia.org/billtrack/digital-personal-data-protection-bill-2023, accessed 2026-10-06; Wikipedia agrees). The design (own consent, discard, expiry) is still good, but the legal reasoning should be redone.
- Fix: do not store the child's photos or horoscope until they accept (keep a "draft" only on the parent's side); send the child a plain notice by the number; shorten the 180 days; record the child's own consent at takeover; ask counsel to review. Effort M.

**C4. The matching engine has no audit for the bias it was built to avoid.**
- Claim: DEC-V1-031 replaced the DEC-V1-002 formula, and with it the monthly parity report and diversity re-ranking are no longer clearly attached to the new engine. The new engine allows importance-10 "must" on height, income band, manglik, community and sub-community, applied both ways (seen live on /me/matchmaker: Height, Income, Manglik, Community in the "Add a point" list).
- Evidence: a March 2026 audit of five LLM families on real matrimonial profiles found "same-caste matches are rated most favorably, with average ratings up to 25% higher" (Sima AIunty, https://arxiv.org/abs/2603.29288, 31 Mar 2026). A Dutch regulator found the dating app Breeze justified in suspecting its algorithm discriminated against dark-skinned users (https://arxiv.org/abs/2409.15828, 2024; ruling Sep 2023). Caste is the most severe implicit LLM bias in an 11-model benchmark (https://arxiv.org/abs/2604.01925, Apr 2026).
- Mitigating facts: the vocabulary is closed and has no complexion field; the model only extracts. That is the right design.
- Why it matters: "must be 5'10" and above 20 lakh" is a mutual hard filter that silently removes short or lower-income men and, applied the other way, many women. Nobody sees who was removed, because "a blank never removes anyone" does not cover a stated fact.
- Fix: log extractions; run the parity report on the new engine, split by gender, age, height and income; cap or warn on height and income musts; test Telugu and Hindi extraction with a hand-labelled sample. Effort M.

### High

**H1. Horoscope: the product shows "Strong match" beside a result the family's own tradition rejects, and makes Mangal a filter.**
- Seen live today on a profile: "Strong match · 17.5 of 36 gunas". The 18/36 line is Mangalya's own Discover rule. The previous critique (2026-09-29, P0-3/P0-4) raised this; it is still there.
- Evidence: no peer-reviewed support exists that Guna scores predict marital quality; even astrology sites say so (e.g. https://drprernakohli.in/kundli-matching-premarital-counselling/, 9 Jul 2026, practitioner view). In the best science on pre-meeting prediction, self-report compatibility explained only 4-18% of one person's attraction and could not predict the pair's "relationship variance" (Joel, Eastwick, Finkel, Psychological Science, 2017, doi 10.1177/0956797617714580). In 43 couple studies, the strongest predictors came after people met (commitment, appreciation, conflict) (Joel et al., PNAS, 2020, doi 10.1073/pnas.1917036117). In 2023 the Supreme Court stayed an Allahabad High Court order that sent a woman's horoscope to a university astrology department to decide if she was "Mangalik" (https://www.thehindu.com/news/national/other-states/allahabad-hc-asks-astrologer-to-verify-if-a-rape-victim-is-mangalik-as-accused-denies-marriage-on-this-ground/article66927095.ece, 3 Jun 2023).
- Why it matters: Mangal is a stigma that falls mostly on women. A hard "manglik: no" filter turns that stigma into invisibility. The calculation work itself is impressive (checked against AstroSage on 205 pairs and ProKerala on 2,916; `horoscope-service/docs/PROVIDER-LIMITATIONS.md`).
- Fix: keep horoscope opt-in and tradition-labelled, never in the "match" pill, one result per pair; remove "must" on Mangal or add a visible note; do not paywall the basic result (Gold now sells "the full kundli report"). Effort S-M.

**H2. Public birth time and place plus photo before any connection.**
- Claim: by owner rule, exact birth time and place are visible to every signed-in member and cannot be hidden. Seen live: Asha's profile shows "6:42 am · Visakhapatnam" in her own horoscope row.
- Evidence: real women's photos are lifted for fake profiles and AI morphing; the NCRB conviction rate for cybercrime was 29.6% in 2022 (https://feminisminindia.com/2025/12/01/from-rishta-to-risk-scams-and-ai-morphing-fueling-gendered-violence-on-indian-matrimonial-sites/, 1 Dec 2025). A study of Pakistani Facebook matrimony groups documents the same exposure of families' data (https://arxiv.org/abs/2509.08782, 10 Sep 2025). In a small community, a photo, birth date, time and place, and city identify a woman to any relative or ex.
- Fix: respect the owner's reason (families check kundlis before connecting) but reveal rashi, nakshatra and gotra pre-connection, and exact time and place when the family side opens their interest, or only to viewers who have passed the check. Effort S.

**H3. The broker (agent) design has three problems.**
- (a) Harvesting: Suresh's screen reads "New families opened today: 0 of 20; Last 30 days: 2 of 300". That is up to 300 families' phone numbers a month per agent, with "Show contact" buttons.
- (b) Contradictory money text: the family page says "Any agent's fee is between you and them. Mangalya never collects it", beside "3 months ₹1,499 + GST ... Pay ₹1,768.82".
- (c) "Verified by Mangalya" is an endorsement. Hyderabad brokers are reported to take upfront fees (one victim: ₹50,000 in phases), resell profiles that are already free online, and match "stars and personalities that don't match" (https://www.deccanchronicle.com/news/marriage-brokers-exploit-desperation-during-hyderabad-wedding-season-893521, 11 May 2024).
- Also: agents may upload biodata of people who are not members. They never consented, and an invitation by SMS tells a stranger's phone that someone is searching for a spouse.
- Fix: cap contact views at a few per day, show the family which agent viewed what, publish what "verified" means and who checks it, add an agent complaint path with removal, require the non-member's consent before any data is stored or invited. The owner's aim to bring brokers in is sound; the guardrails are thin. Effort M.

**H4. Plans: "paid then nothing" and a feature that contradicts the product's own rule.**
- Seen: Gold sells "See who viewed your profile" and "See who shortlisted you". v1-decisions (DEC-V1-021) say Mangalya "deliberately has no visitor or view lists (the baseline rules out view counts and being watched)". A viewer list is also a stalking tool for women.
- Assisted is ₹23,599 for 6 months and lists only "A dedicated relationship manager": no number of introductions, no callback time, no refund terms (screen of /plans). The previous critique already asked for this (P1-4).
- Evidence: 52 of 129 reviews are "paid, then nothing" (repo research); Matrimony.com's paid subscriptions fell from 1.07 to 1.00 million, FY24 to FY25 (https://tradebrains.in/how-matrimony-com-is-making-more-money-from-fewer-subscribers/). Prices are now GST-inclusive, which is fixed and good. CCPA's 2023 guidelines list 13 dark patterns including subscription traps (https://pib.gov.in/PressReleasePage.aspx, 8 Dec 2023).
- Fix: drop the viewer list or show it only as "families who sent you a request"; publish Assisted deliverables and a pro-rated refund; state renewal terms on /plans. Effort S.

**H5. Incognito chat says more than it can promise.**
- Seen: "Incognito. You are connected. Only the two of you can read this conversation." Yet DEC-V1-006 runs a text classifier on messages, and a report stores a snapshot. Parent chat is "completely monitored".
- Why it matters: the real scam path is advance-fee requests; romance fraud cases run to ₹20-27 lakh (https://www.thebridgechronicle.com/pune/pune-wakad-fake-matrimonial-profile-27-lakh-cyber-fraud-agn97, 3 Mar 2026; https://lawctopus.com/academike/online-matrimonial-frauds-a-new-frontier-for-family-law-in-india/, 20 Aug 2025). A chat that vanishes when either side leaves also vanishes a harasser's evidence, and the victim has to report inside the session.
- Fix: change the line to what is true; keep the message hash and metadata for the 36-hour grievance window; show candidates when a parent chat is open to family. Effort S.

**H6. No product answer to dowry.**
- Only one guide line mentions it. I found no dowry reason in the report list, no detection, no profile guidance, and many fields (income, family business, employer) that invite it. Dowry Prohibition Act cases rose to 15,489 in 2023 from 13,479 (https://www.thehindu.com/news/national/dowry-cases-rise-by-14-in-2023-over-6100-women-killed-ncrb/article70116195.ece, 2 Oct 2025). The SSK site says dowry "is not at all visible" in the community (https://ssksamaj.org/about-us/), which is an asset to protect.
- Fix: a "Dowry or money demand" report reason, a classifier phrase list in en/hi/te, a one-line pledge at profile creation, and a Samaj-signed rule. Effort S.

### Medium

**M1. "Required verifications" (salary proof, ID, blood test) contradict an earlier decision and may be unlawful.** On 21 Sep the owner dropped documents ("forget doc verification"); on 30 Sep families may ask for salary proof, ID and a medical test after a match. I did not see it in the screens. HIV status in marriage is a legally charged area (Mr X v Hospital Z, 1998, https://www.alec.co.in/judgement-page/mr-x-v-hospital-z-air-1999-sc-495). Fix: limit to optional, family-to-family exchange of documents outside the platform; no platform storage of medical results; legal review. Effort M.

**M2. Wedding arrangements push spending in a community that curbs it.** Seen: 28 halls from OpenStreetMap, each with a "Representative photo" (stock), duplicates ("Mohini Function Hall" twice), mostly no phone; and Asha shows two "Wedding date fixed" connections at once (possibly a seed artefact; the lifecycle rule should be checked). Matrimony.com's wedding-services revenue fell 34.7% to ₹6 crore in FY25 (https://www.storyboard18.com/advertising/matrimony-com-cuts-ad-spend-by-1-07-amid-fy25-revenue-profit-decline-75089.htm) and was about ₹1 crore a quarter in Q2 FY26 (https://inc42.com/?p=538448). Communities pass resolutions to cap wedding cost (a Bhuj Ahir feast and ceremony at ₹28,600, https://indianexpress.com/article/india/band-baaja-budget-bhujs-ahirs-say-no-to-wedding-show-off-embrace-tradition-10098538/, 1 Jul 2025). Fix: lead with Samaj and community halls, "simple wedding" guides and a cost estimator; remove stock photos; plan no vendor revenue. Effort M.

**M3. Samaj heads run the app on a tiny community.** Support and admin staff will know the families they handle (gossip risk) and a "members in numbers" page open to all can re-identify people at small counts. Fix: conflict-of-interest rule (recuse for relatives), counts suppressed below a minimum group size, audit log reviewed by someone outside the Samaj. Effort S.

**M4. Safety operations are thin for the promises made.** The decisions promise 1-hour photo review and a 2-hour removal ceiling (IT Rules, as the decisions file reports it), and DEC-V1-025 says the human review screen "has a table but no Operations screen yet". Fix: build the review screen before launch and publish who is on call. Effort M.

**M5. Screenshot deterrence is theatre.** The guard blanks the page on Print Screen and when the window loses focus (not tested by me). That blanks the page when a mother switches to WhatsApp to call the pandit, and cannot stop a phone camera. Families already exchange biodata as WhatsApp PDFs (Bharadwaj; Shaadi's own biodata maker). Fix: a visible per-viewer watermark and a "shared with you by" trail do more. Effort S.

**M6. Carried over from the previous critique and still true in my walk:** the Circle page says "what each can see" but shows no permissions; Home still repeats the plan cards; Discover shows skeleton tiles for several seconds on the dev build.

## 3. New in the world

- Caste audits of LLM matchmaking now exist (Sima AIunty, https://arxiv.org/abs/2603.29288, Mar 2026) and a general LLM caste-bias benchmark (https://arxiv.org/abs/2505.14971, May 2025): treat LLM extraction as an audited component.
- Regulators now rule on dating-app algorithms: the Breeze decision and a legal-technical guide to mitigation (https://techreg.org/article/view/19591).
- Pre-meeting compatibility is weakly predictable (Joel et al. 2017, 2020): invest in the first meeting, not in score precision.
- Face check is becoming table stakes: Tinder made Face Check mandatory for new users in India (Adgully, 24 Sep 2026, repo research, not re-opened), but injection attacks are rising.
- DPDP Rules phase: full duties from 13 May 2027 (https://dpdp.ind.in/rules.php). Build for them now.
- Fewer, deeper connections: 72% of young Indian singles prefer them (Match Group India, Sep 2026, repo research).
- Remarriage is 16% of Jeevansathi users, up from 11% (Storyboard18, 12 Feb 2026, repo research); Mangalya's guide on second marriage is ahead of many rivals.
- Google Play fee disputes pushed matrimony apps to take payments on the web (https://www.tribuneindia.com/news/business/google-starts-removing-apps-like-shaadi-com-bharat-matrimony-from-play-store-for-not-paying-service-fee-596178/, 1 Mar 2024): the web-first choice helps.

## 4. Rethink

1. **Who is the user?** For: the Samaj funds this and wants community cohesion. Against: C1; marrying across sub-communities and languages is the only way a small pool works. Decide and write it down.
2. **Birth details always public.** For: families check kundlis before talking, and the owner's reasoning is how people really act. Against: H2; exposes women to lifted photos and stalkers. Middle path: reveal in stages.
3. **A hidden score plus a "Strong match" word.** For: no number to game, and reasons are checkable. Against: people still read the word as a verdict, and the engine's hard filters are invisible. Consider showing a short, honest "what we filtered out and why" line.
4. **Brokers as a growth channel.** For: they already own the trust of families and the owner wants to lift them, not replace them. Against: H3; brokers' incentive is volume, the app's is safety. Test with five brokers before scaling.
5. **Incognito chat for candidates.** For: privacy and no pressure. Against: H5; scams and harassment leave no trace. Keep it, but with a short retention for reports.

## 5. Do not change

- The candidate stays the decision owner; parents answer for them; requests are attributed to the person who sent them.
- Mutual preferences are hard rules, and "Looking for" is always applied.
- Popularity weight is zero; reasons are checkable facts; no number is shown to members.
- The closed vocabulary for LLM extraction, and the keyword fallback when no key is set.
- Face-match design: separate consent, nothing biometric stored, two-year expiry, strict threshold (only the claim around it needs changing).
- The waiting periods after a decline (90 days) or withdrawal (21 days).
- GST-inclusive prices (now fixed), and "a plan changes what you can do, not where you appear".
- Horoscope calculation validated against external references, with the library's own tables rejected.
- Guides in three languages, the "story of Mangalya" onboarding, "OpenStreetMap places, partner offers always labelled".
- The honest limits written in the decisions file; that candour is the project's best habit.

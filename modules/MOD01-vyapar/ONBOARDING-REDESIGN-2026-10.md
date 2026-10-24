# Vyapar onboarding: what we learned, and what we decided (2026-10-06)

The owner said the sign-up screens are "theoretically perfect, but practically not practical and very rigid". To test that, three brand-new ForKhatri members went through Vyapar on a 390 px phone screen, from the hub to their real goal. Each one did it in their own language, with realistic details. Every screen was screenshotted, and those screenshots are in `onboarding-mockups/audit-2026-10-06/`. The proposed screens are mocked up in `onboarding-mockups/index.html`.

**No app code was changed.** This document leads with the evidence, then sets out the decisions. The build follows from the decisions.

## 1. Who we tested, and what happened

| Person (QA member) | Goal | What happened | Taps / typed fields / screens before the goal |
|---|---|---|---|
| **#27 Venkatesh Naidu.** Telugu plumber who can barely type; also does some electrical work and borewell motors. | Find work today. | Used the voice interview to answer. Was then dumped back into the step-by-step form at step 2, so he confirmed everything a second time. On the skills step, "borewell motor" was shown only as an "Added: …" line he can't remove. His quote was **lost** the first time: a terms panel appeared under the bottom bar and his tap hit the "Businesses" tab instead. He got through on the second try. His profile is a **draft with no skills**, so hirers can't find him. | about 22 taps, 6 typed fields, 9 screens |
| **#28 Mohan Lal Khatri.** Hindi kirana owner in Chandni Chowk, Delhi. | Hire a shop helper in 5 minutes. | Skipped first run by using the Post tab. Then hit "Create your profile first". "Use my location" took **15 s**, then offered **Hyderabad areas only**. "Kirana" isn't a category. He was asked for his phone again. After saving, he landed on a profile page about packages, GST and OTP, so his posting goal was lost. In the composer, the AI missed "10000 महीना" (10,000 a month), forced a salary range (minimum and maximum), and set the shift to **night** for a 10 am–8 pm job. A terms panel blocked publishing. The job went live after about **6 minutes**. The next time he opened Vyapar, **first run started again from step 1**. | about 25 taps, 6 typed fields, 11 screens |
| **#29 Kamala Devi.** Telugu homemaker selling pickles from home. | Get customers. | "పచ్చళ్ళు" (pickles) isn't in the list. She picked "find customers" and was shown car-mechanic and delivery **jobs**. Business setup re-asked her pickles and her phone, then asked for packages (Basic/Standard/Premium), GST/Udyam and a phone code. "Send for review" showed **"[object Object]"**: there is a terms gate with no button to accept it. **She is still not visible to anyone.** | about 24 taps, 6 typed fields, 11 screens, and the goal was not reached |

#15 Lakshmi Prasad (Kakinada) showed the same location problem: "use my location" offers only Hyderabad areas. The CA and student personas were not walked; their screens are the same ones, and are covered in the table in section 3.

## 2. Where Vyapar is rigid in practice (concrete moments)

1. **The gate that never ends.** The home page always redirects to `/first-run` until 5 steps are done. This happens even for a member who already has a business profile and a live job post (Mohan, `vy28-13`). The Post tab skips the gate, so the rule is inconsistent too.
2. **Re-asking what ForKhatri knows.** Vyapar asks again for:
   - name and language (step 1);
   - phone (the business step 3, `vy28-07`; Vyapar's prefill has `phone: null` even though the identity holds a verified phone);
   - phone verification by OTP before a profile can go live, although sign-in already verified that number;
   - skills already picked at first run (business setup starts empty, `vy29-07`).
3. **Profile before acting.** "Create your profile first" stands between a hirer and his first post (`vy28-03`). Yet `GET /v1/me/profile` already creates the one profile from the identity on first read. Venkatesh passed the same rule without noticing, but Mohan was stopped by it.
4. **Locality is assumed to be Hyderabad.** Outside Hyderabad, the place lookup returns `matched:false`. Kakinada, Delhi and Vijayawada were all checked through the API. The screen then offers a fixed list of 17 Hyderabad localities. Matching for Mohan's Delhi job then suggested people in Kukatpally and LB Nagar (`vy28-12`).
5. **Real life doesn't fit the form.**
   - Several trades: the voice summary only showed one.
   - Several areas: "Miyapur too" was dropped.
   - No shop: "on-site / remote / both" means nothing to a pickle seller or a kirana.
   - No business name.
   - Trades missing from the list: kirana, pickles.
   - Fixed pay is not allowed as an amount; the form insists on a minimum and a maximum.
6. **Jargon and wrong register.**
   - "ఆన్-సైట్ / రిమోట్", and the help line "అన్వేషణ పరిధి కోసం ఉపయోగించబడుతుంది" (bookish wording for "used for your search radius").
   - "మేము మీరు ఏమి పిలవాలి?" is ungrammatical; it should be "మిమ్మల్ని ఏమని పిలవాలి?" ("What should we call you?").
   - "మీరు ఇక్కడకు ఎందుకు వచ్చారు?" reads as "why did you come here?", which is curt.
   - The skills help line says "we will suggest specific skills later", which isn't true.
   - Two categories look almost identical: "ఆరోగ్య సేవలు" (health services) and "ఆరోగ్యం" (health).
7. **Voice doesn't finish the job.**
   - It doesn't read answers back.
   - It doesn't understand number words: "పదేళ్లు" ("ten years") was rejected.
   - The question about own tools or vehicle accepts only one answer.
   - Experience and own tools or vehicle are thrown away when the person returns to the form (`first-run/page.tsx` keeps only name, locality, mode and skills).
   - Afterwards the person repeats steps 2–5 by tapping.
8. **The answers don't change what you see.** "Find customers" still opens a jobs feed (`vy29-05`). The "You're ready" screen is an empty extra tap (`vy27-09`).
9. **Consent at the worst moment.** The terms panel appears only when the person presses Send or Publish, and it is easy to miss under the floating bar:
   - one quote was silently lost;
   - one business could not be submitted at all ("[object Object]").
10. **The business profile reads like an Upwork form.** A pickle maker sees Basic/Standard/Premium packages with "ready in (days)", GST/Udyam/PAN/Shop-licence checks, call-hour settings and a phone code, all on the first save (`vy28-08`, `vy29-08`).

## 3. Screen by screen: today, evidence, proposal

Sources are listed in section 5. **[R]** means a real user review or a research study. **(U)** means unverified.

| Screen today | Rigid in practice | What competitors and research show | Proposal |
|---|---|---|---|
| **S1. Welcome: name and language** (`vy27-01`) | Both already known. Just one more tap. | WorkIndia sells "30-sec registration" [R]. Apna users get stuck on preference screens with a disabled Next [R]. | **Remove.** Name and language come from the identity. Language stays in the header switch. |
| **S2. Where: locality, radius, on-site/remote** (`vy27-05`, `vy28-05`) | Hyderabad-only list; 15 s wait; jargon; Continue hidden under the bottom bar. | WorkIndia users: "can't skip location or update it manually" [R]. Apna Recruiter: "Bengaluru not accepting" [R]. Women search within 3–5 km (IFMR-LEAD) [R]. | **Keep one "Where?" question.** Prefill it, accept any typed town, and show nearby chips only if they really are nearby. **Don't ask radius or work mode**: default them from the trade and change them in filters. |
| **S3. Skills: 22 text categories, then a drill-in** (`vy27-06`, `vy27-07`) | Text-heavy; no pictures; added skills appear only as an "Added: …" line; home trades are missing. | Picture plus voice interfaces are preferred by low-literacy users (Medhi et al.) [R]. Apna and WorkIndia users complain when the category is wrong and the app won't say why [R]. | **Picture tiles for the top trades.** The icons already exist in Discover's TradeRail. Several picks allowed, plus search and speak. "Other" entries become **removable chips**. Add missing roles as taxonomy data (kirana or general store; home-made food and pickles). |
| **S4. "What brings you here?"** (`vy27-08`) | Comes 4th, after skills a hirer doesn't need. It changes nothing on screen. The Telugu reads as curt. | Apna Recruiter: "post a job in under 2 minutes" [R]. Each app splits seekers from hirers at the door. | **Move it first, as the router**: Find work / Hire someone / Get customers. Partners comes later. |
| **S5. "You're ready"** (`vy27-09`) | An empty tap. | LinkedIn's profile-strength meter never blocks use [R]. Naukri: "100% profile, no genuine call" [R]. | **Remove.** Land on results, with a small "40% done, next question" card. |
| **Voice interview** (`vy27-02`–`vy27-05`) | No read-back; number words rejected; data dropped; afterwards the person returns to the form. | Read-back prompts cut voice-entry errors by 1.6× (Microsoft Research, Babajob study) [R]. | **Voice completes the whole start**: read back each answer, accept number words, save everything and go to results. |
| **Post chooser, then "Create your profile first"** (`vy28-02`, `vy28-03`) | Two gates before the composer. | Garage owner on Apna asked for shop documents after paying [R]. JD: "add your business listing for free" [R]. | **Remove the wall.** The one profile always exists from the identity, so the rule is met without a screen. |
| **Business setup (3 steps)** (`vy28-04`–`vy28-07`) | Business name required; 22 categories; work-mode jargon; phone re-asked; first-run skills lost. | JD's free listing asks name, phone and address (U, from a snippet). | **One card**: "What do you sell or offer?" (tiles plus Other) and "Where?". The name is optional and suggested ("Kamala's pickles"). Phone comes from the identity. |
| **Profile page after saving** (`vy28-08`, `vy29-08`) | Packages, GST, phone OTP and call settings all shown at once; "Send for review" fails. | Upwork review waits and Urban Company two-week verification read as rejection [R]. Urban Company and WorkIndia fee complaints [R]. | **Save means live** as "New on Vyapar", which the server already supports. Packages, documents and call settings move into the completion card, one at a time. |
| **Composer** (`vy28-09`–`vy28-12`) | Salary range forced; AI misses Hindi amounts and gets the shift wrong; review step bounces the person back. | Apna Recruiter: "easy to post on mobile" [R]. | Allow **fixed pay**. Read numbers in Hindi and Telugu. Show inferred shift and pay as confirm chips on the same screen. |
| **Terms gate at Send/Publish** (`vy27-13`) | Hidden under the bar; loses the person's input; "[object Object]" on submit. | — | **Ask once, at entry**: one line and "Agree and continue" on the start screen. The server rule (FR53) stays. Any later re-consent keeps the form and appears above the bar. |
| **Desktop** (`vy28-14`) | One stretched column. | — | Same 3 screens, with the results preview beside the question. |

## 4. The new flow (3 screens, then results)

```
Hub "ప్లంబర్ పని కావాలి" ──► Vyapar keeps ?q= and skips straight to results (no gate)

[1] Namaste Venkatesh, what do you want to do today?     (consent line + Agree)
    ( Find work )  ( Hire someone )  ( Get customers )    [ or speak ]
[2a] What work do you do?    [pictures x6] [+ more] [search/speak] chips: Plumber × Other ×
[2b] Who do you need?        → the existing AI composer, prefilled area, fixed pay allowed
[2c] What do you sell/offer? [pictures] [Other] · optional name "Kamala's pickles"
[3] Where?  [Use where I am: Kukatpally]  [any town typed]  [nearby chips only]
──► Results: "12 jobs near you" / "post is live" / "you're visible", plus the completion card:
    "40% · Next: years of experience? [1–2][3–5][6–10][10+]"   (one question per visit)
```

**What is asked now and what later**

- **Now:** goal, trade(s) or need, and area.
- **Later, one question per visit:**
  - experience;
  - tools or vehicle;
  - rates or packages;
  - business name and photo;
  - call hours;
  - GST/Udyam (optional);
  - "also go to" areas.
- **Prefilled from ForKhatri:** name, language and verified phone.

**Before and after counts**

| Measure | Before | After |
|---|---|---|
| Screens to the first real action | 9–11 | 3–4 |
| Required fields | name, language, locality, (skills), goal, plus business name, phone, salary range | goal, trade or need, area |
| Taps | 22–25 | about 5–8 |
| Typed fields | about 6 | 0–1 |

## 5. Evidence base

All reviews are Google Play reviews pulled on 2026-10-06 (`play.google.com/store/apps/details?id=…`).

**What annoys people**

- **Forced preferences and location:**
  - Apna: "Next button shows disabled" (2026-08-11).
  - WorkIndia: "can't skip location or update it manually" (2026-09-10).
  - Apna Recruiter: "Bengaluru… not accepting" (2026-09-28).
- **Wrong category:**
  - Apna: a dental assistant was shown peon and sales jobs (2026-09-06).
  - Naukri: "100% profile… no genuine call" (2026-09-24).
- **Spam and money:**
  - About 15% of 1–2★ reviews for Apna and WorkIndia mention someone asking for money.
  - JD: daily upsell calls after listing (2026-10-03).
  - Urban Company Partner: ₹2,000 interview fee not refunded (2026-09-26).
- **Verification waits:**
  - Apna: a garage owner was asked for shop documents after paying ₹850 (2026-09-02).
  - Urban Company Partner: more than 2 weeks for verification (2019).
  - LinkedIn: "5 hour" ID loop (2026-10-03).

**What works**

- Calling HR directly: WorkIndia (2026-09-01) and Apna (2026-10-01).
- Apna Recruiter: "got candidate applications quickly" (2026-08-24).

**Research**

- **IFMR-LEAD DP-WEE (2023), blue-collar job platform:**
  - free sign-up, an ID only, and employers call workers;
  - women search within 3–5 km and register for more job types;
  - [digitalplatformsandwomen.ifmrlead.org](https://digitalplatformsandwomen.ifmrlead.org/wp-content/uploads/2024/02/DP_WEE_Staus-of-Blue-Collar_Report.pdf); [Scroll, 2023-11-15](https://scroll.in/article/1059001/how-a-gendered-digital-divide-low-quality-of-jobs-keeps-indian-women-out-of-the-workforce).
- **Chakraborty et al., Microsoft Research India and IIT Delhi:** with Babajob voice-menu profiles, read-back cut errors by 1.6× ([paper](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/Chakraborty-dev2013-ivr.pdf)).
- **Medhi, Sagar & Toyama:** text-free interfaces, picture plus voice preferred ([MSR](https://www.microsoft.com/en-us/research/?p=160568)).
- **J-PAL / IGC:** assisted registration ([IGC](https://theigc.org/collections/labour-market-frictions-india-evidence-introduction-job-information-platform)).
- **LinkedIn profile meter:** [help 391](https://www.linkedin.com/help/learning/answer/391).
- **Apna employer steps:** [apna.co guide](https://apna.co/career-central/how-to-post-your-first-job-on-apna/).

**Not verified**

- Reddit (blocked for us).
- Naukri "3× views" claims.
- Upwork profile-review times.
- Indeed applying without an account.
- The Justdial free-listing field list.

## 6. Decisions

Each decision is made for Vyapar and respects the owner rules already recorded.

1. **No first-run gate.** Replace the 5 steps with the 3-question start above. Show it once. Never show it to a member who already has a trade or a post. Honour the hub's `?q=`; the hub side is a platform task.
2. **Name, language and phone are never asked.** They come from the identity, per vyapar-one-profile-per-member. Vyapar's identity adapter passes the **verified phone**, which counts as `contact_verified`. Phone OTP stays only for a *different* number. This stays decoupled: the claim comes through the host adapter.
3. **The one profile exists from the first visit.** It is created from the identity, as the API already does. This keeps the owner rule "without a profile nothing moves forward" without showing a wall. "Create your profile first" is removed.
4. **The goal question comes first and acts as the router** (Find work / Hire someone / Get customers). Partnerships appears later in the profile.
5. **Trades are picked from picture tiles, with several picks allowed.** Search and voice are also offered. "Other — add your own" entries become removable chips; this is the SkillPicker change originally asked for. Free text is kept and shown as written. Missing roles are added as taxonomy data (kirana/general store; home-made food and pickles; borewell/motor repair). The full category grid stays behind "More trades", so the picker is closed by default (collapse-option-fields rule).
6. **One "Where?" field.** Any town is accepted. "Use my location" shows chips only within about 25 km. Elsewhere it says "couldn't name your area, please type it". A gazetteer or geocoder for more cities goes to the shared-integrations backlog (an external vendor). Radius and work mode are not asked: plumber, electrician and similar trades default to "go to the customer", professionals to "both", shops and home sellers to "customers come to me", with plain words for each. All of these can be changed in filters and the profile.
7. **Voice completes the start.** One question at a time, each answer read back ("I heard plumber and electrician — right?"), number words understood in Telugu and Hindi, more than one answer allowed for the tools-and-vehicle question, and everything saved, including experience and tools. Afterwards the person goes to results, never back into the form.
8. **Saving makes you live** as "New on Vyapar" (`active_unverified`, the existing server path). The content-flag moderation hold stays. Document verification is optional and appears in the completion card, never before a first post. This follows the verified WorkIndia evidence on GSTIN.
9. **Consent once, at entry.** One line and "Agree and continue" on screen 1, which satisfies FR53 and DPDP's need for a clear affirmative act. If a later re-consent is ever needed, it keeps the person's form, appears above the bottom bar and re-sends the action itself. The "[object Object]" error is fixed.
10. **Business section is minimal on first save.** "What you sell or offer" and "Where", with the name optional and suggested. Packages become "Add a price list" for service trades only. Call hours keep their safe default; pre-call stays off by default (vyapar-precall-calling).
11. **Composer.** Fixed pay is allowed as one amount; "up to" is optional. Hindi and Telugu amounts and times are parsed. Inferred shift and pay are shown as one-tap confirm chips on the same step. The "check money info" bounce-back to step 1 is removed.
12. **Results first.** Remove the "You're ready" screen. Workers land on jobs near their area for their trades. Hirers land on their live post. Sellers land on a "you're visible" card with a share-to-WhatsApp action. Every type gets the one-question completion card, with a percentage and never blocking.
13. **Copy.** Fix the Telugu and Hindi lines listed in section 2.6, using the respectful register. Replace "on-site/remote" with plain phrases. Merge or rename the two "health" categories.
14. **Matching and discovery honour distance.** Matching profiles and "For you" are limited to the member's area and radius.

**Left for the owner**

- **Q1. Under-18 members (law).** Should a student under 18 be able to look for part-time work? This is the platform's age decision, Q11 in MASTER-CRITIQUE. Until it is decided, Vyapar follows the platform's 18+ recommendation.
- **Q2. Look of the trade tiles (taste).** Our default reuses the line icons already used in Discover. The owner may prefer commissioned illustrations.

## 7. Test data left by this audit (to remove later)

**Members and their state**

| Member | End state |
|---|---|
| #27 Venkatesh Naidu | First run done (voice plus taps). Draft work profile `7de183ca-5dab-4b1f-8ce3-4bcb14279b34`. Terms accepted. |
| #28 Mohan Lal Khatri | Draft business profile `41e6dc69-c529-49f7-a909-290011a4c6a6`. First run not done. Terms accepted. |
| #29 Kamala Devi | First run done. Draft business profile `63423627-76dc-4db9-b2c8-496bd613d190`, phone verified. Not live. |
| #15 Lakshmi Prasad | First run stopped at step 2. |

**Rows to remove**

| What | ID | Who created it | Details |
|---|---|---|---|
| **Live job post** | `8e2300ef-a45d-419a-a73e-06a7fe727224` | Mohan | "Shop helper", Chandni Chowk. |
| **Enquiry (quote)** | `b14dbd61-8246-4982-b2bd-098df0b7c828` | Venkatesh | ₹1,200, today, on Anita Khatri's post `8753fd1f-…`. |

## Final decisions (2026-10-06)

- All 14 decisions above are accepted.
- **Under 18:** Vyapar is for members 18 and over (the safe side of child-labour law and the platform's own Q11 recommendation). Ask the date of birth only when it is not already known; a member under 18 sees a kind explanation, not an error.
- **Trade tiles:** simple line icons in Vyapar's current premium style and colours (no clip-art, no saffron-on-black), a label in the member's language under each, and "Other — add your own" as the last tile. The owner can adjust the look after seeing it.

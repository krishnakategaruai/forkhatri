# Family-made profiles: how matrimony apps handle "created for someone else", the risks, and the best design for Mangalya

Research date: 2026-11-23. Method: web search plus direct page fetches. Every claim carries a source. "Read" means I fetched the page and read the text myself. "Search summary only" means a search result described the page but my own fetch of that page did not return the text. "Not verified" means I could not confirm it. This is research, not legal advice.

---

## 0. What is already in Mangalya (checked in code and decisions)

- `POST /profile/managed` (`mangaly-service/app/api/routes/profile.py`, lines 145-260): requires the maker to be face-verified, asks the platform to provision a member for the child's phone number, answers 409 `childAlreadyJoined` when the number already belongs to a member, builds the profile with `created_by_account_id` set, and adds the maker as founding Home Circle member.
- `POST /profile/claim` sets `claimed_at`. After that only the candidate edits; the creator stays in the circle.
- `POST /profile/disown` ("This isn't me"): the number's owner removes an unclaimed profile; the maker is notified.
- `GET /profile/managed` lists profiles the caller made and the child has not yet claimed.
- DEC-V1-035 (2026-10-06) already decides a better model: the parent is never blocked, the child's number is optional, the profile is "managed by her mother" until the child joins, the child is asked "is this you?" on sign-in and consent is recorded (`account_alias.consented_at`), and a number that already belongs to a member "is no longer a dead end: the profile is managed and that member is asked the same question". Migration 065 (data model and SECURITY DEFINER functions `create_managed_account`, `set_pending_phone`, `made_for_my_number`, `take_over_profile`, `not_my_profile`, `alias_of`) exists in the repo, but no API route calls those functions yet. The decision file says the two-line change to `/profile/managed` was refused by the build session's permission system as a security weakening and is "still to apply (needs the owner's hand)" (`v1-decisions.md` lines 865-879).
- DEC-V1-025 (the maker must be face-verified) was softened by DEC-V1-035 to an optional trust step. **Tension to flag:** the owner's rule of 2026-09-21 ("a person who could create an account [for someone] should always be an email, phone, photo verified person only", `v1-decisions.md` line 790) and the owner's 2026-10-06 answer (the parent should be able to publish) conflict. The recommendation below resolves it without overriding either: the maker is phone-verified always; face-verified is required before the profile becomes visible to other families, not before it is drafted.
- Age rule: `profile.TooYoung` exists (the age check is applied at create time).

So the problem in the brief (case c: account exists, no profile, publish refused, "manage" only works pre-sign-in) is the pre-DEC-V1-035 behaviour. The design question is mostly how to finish DEC-V1-035 safely.

---

## 1. How the major apps handle "profile created for someone else"

Honest summary first: **the official registration flows of Shaadi, BharatMatrimony and Jeevansathi are behind logins/bot walls, and I could not read them.** What I can state is below, with the verification level.

| App | What I could verify | Source and level |
|---|---|---|
| Shaadi.com | A creator option for son, daughter, brother, sister, relative, friend is reported from the App Store listing text. **My own fetch of the listing did not return that sentence** (three fetches). Treat as search-summary only. Shaadi's marketing associate director says that, even for self-created accounts, "especially in the case of women", parents manage or influence them. 45-50% of accounts in the South were created by parents versus 25-30% elsewhere. | Search summary of listing: https://apps.apple.com/app/id480093204 (not reproduced on fetch). Statistics and quote: ThePrint, 4 Sep 2022, read: https://theprint.in/feature/parents-no-longer-make-matrimonial-profiles-of-children-but-theres-a-north-south-divide/1109683 |
| Shaadi.com help | Phone change needs a 4-digit PIN to the new number; contact privacy lets a member hide their number; members can report "Phone number is incorrect". No help article on "created by parent", consent or take-over found. | Search results of https://support.shaadi.com/support/solutions/articles/48000755468-i-want-to-change-or-hide-my-phone-number (search summary only) |
| BharatMatrimony | Its executive (CMO Arjun Bhatia) says about 7% of profiles are set up by parents in 2022, about 70% by individuals, the rest by friends or siblings (ThePrint, read). A different search summary quotes the CEO that third-party creation (parents/family) is allowed and about 25% of the user base (search summary only; not read on the primary page). The App Store listing I read says only "Create your profile for marriage" and does not mention parents. | ThePrint above; App Store listing, read: https://apps.apple.com/us/app/id465923141 |
| Matrimony.com group (Marathi, Parsi, Marwadi Matrimony; same company as BharatMatrimony and Jodii) | The terms treat the creating person as a "Registrant": father, mother, brother, sister, relative or friend (Parsi terms, search summary only; the page returned 403). Marathi terms clause (C), search-summary quote: "In case you are a Registrant of the prospective bride/ bridegroom and has created profile in BM Website/App on behalf of them or is accessing the BM Website/App on behalf of them implies that you have taken their consent for their profile." The same terms allow sharing profile data with the group's other community sites. **This is consent presumed from the maker, not obtained from the candidate.** My direct fetch of the Marathi terms returned 403, so the quote is from the search summary. | https://www.marathimatrimony.com/terms.php ; https://www.parsimatrimony.com/terms.php (both 403 on fetch; search summary only) |
| Jeevansathi | I could not verify creator options or labels. The one help article I read covers registration generally and says nothing about creating for others. An unofficial Scribd copy is described as listing "Profile created to: self, parents, friend, brother, sister, relative" (search summary only, undated). | https://jeevansathi.freshdesk.com/support/solutions/articles/5000703780-how-can-i-register-on-jeevansathi (read) |
| Jodii (Matrimony.com, Tamil, launched Nov 2021) | Launch material: free registration; women can hide their photo and show it only to matches they like. No parent-creation rules found. | Search summary of https://www.matrimony.com/newsroom/jodii-a-vernacular-matrimony-app-in-tamil-launched-to-help-millions-of-common-people-find-their-life (403 on fetch) |
| Betterhalf.ai | Positioned as built for users themselves; founders say it works without meddlesome relatives and give "primacy to the consent of users" over sharing contact details (YourStory interview). No parent mode found. | Search summary only: https://yourstory.com/2022/06/betterhalf-corporate-partners-ai-matrimony-app-match-wedding ; The Walrus article returned 403 on fetch |
| Lokal Matrimony (Telugu-focused) | Terms read: "Each account is tied to a single phone number and must only be used by the individual who registered it." No parent or guardian clause. Age: 21 for males, 18 for females. Profiles may be removed or accounts terminated for false or misleading information. | https://matrimony.getlokalapp.com/policies/v2/terms-and-conditions/ (read) |
| Kaakateeya, TeluguMatrimony | Only app-store descriptions seen; nothing on creator rules. | Not verified |
| Simply Marry | Nothing found. | Not verified |
| Masii (a newer proxy-aware matchmaker, blog dated 12 Feb 2026) | Closest published design to what Mangalya wants. Parents may start; the individual must take part before any match is finalised; on joining, the person chooses the family's role "from full involvement to visibility without veto power"; if the individual does not engage within a reasonable time the proxy profile is paused: "We are not going to facilitate matches where one person does not know they are being matched." No statistics, vendor blog. | https://masii.pages.dev/blog/the-proxy-problem (read) |
| Muzz (Muslim marriage app, Western equivalent) | "Chaperone Mode enables you to share weekly transcripts of your chats on Muzz with a wali." The page does not say who sets it up or whether the other person is told. Shows a guardian-view pattern that is opt-in by the member. | https://muzz.com/help/getting-started/how-is-muzz-halal (read) |

### What I could not find (state plainly)

- Any official help page from Shaadi, BharatMatrimony, Jeevansathi, Jodii or Betterhalf on: whose phone is used when the parent creates for a child; what happens if the candidate already has an account; whether the candidate can claim; whether a "managed by parent" label is shown. These are **not verified**.
- The only verified fact on labels: ThePrint reports that some matrimonial sites let users choose a "created by self" tag, and one woman's profile that her parents created and ran carried "created by self" and listed her parents' contact details (ThePrint, read). So labels are self-declared and can be false.

**Inference (from the above):** the incumbents treat "created for" as a self-declared field, presume consent from the maker, and (as far as any source shows) provide no candidate-side claim, review or approval step. That gap is where Mangalya can be visibly better.

---

## 2. Risks and what sources report

### 2.1 Fake or unwanted profiles in someone's name

- BharatMatrimony complaint, 16 Jan 2018 (read): a man in the UAE received a call from Kerala matrimony customer care about a profile allegedly created with an email address that was not his; he had made no profile. He asked where it was created and how they had his number. The reply apologised and promised a call; it did not answer either question. https://www.consumercomplaints.in/bharat-matrimony-profile-created-without-my-knowledge-c1837718
- Swati Mukund (content creator), Nov 2024 (search summary only): said her and her husband's photos appeared on a fake BharatMatrimony "elite" profile though neither had registered; the company said the profile came from another platform in its network. Reported at https://newsable.asianetnews.com/india/married-woman-slams-bharatmatrimony-after-her-photo-features-in-fake-elite-profile-internet-reacts-watch-shk-smkgkz (not read).
- Kochi, Kerala, 6 Jul 2026 (read): a 26-year-old woman's Instagram photo was downloaded, altered and posted in a WhatsApp group matrimonial listing with false details and a contact number, without her permission. Zero FIR at City Cyber Police, case moved to Ernakulam Rural Cyber Police; accused is booked under the Bharatiya Nyaya Sanhita and the IT Act for cheating by personation, identity theft, and unauthorised use of another's identity (section numbers not given). Preliminary stage. https://www.onmanorama.com/news/kerala/2026/07/06/matrimonial-ad-photo-probe.html
- Hyderabad, September 2025 (search summary only): arrests over fake matrimonial profiles built with edited photos of women (one victim lost Rs 25 lakh). https://telanganatoday.com/cybercrime-police-bust-fake-matrimonial-racket-in-hyderabad (not read).
- Feminism in India, 1 Dec 2025, "From Rishta To Risk: Scams And AI Morphing Fueling Gendered Violence On Indian Matrimonial Sites": the page returned a bot check, so **not read**. Listed only as a lead.
- Deletion: BharatMatrimony complainant (6 May 2022, read) could not delete his profile after several days of emails; the company replied it was "suspended based on your request" (not clear it was deleted). https://www.consumercomplaints.in/bharat-matrimony-not-able-to-delete-my-profile-c3186086

Note: these cases are mostly about third parties misusing photos, not about family-made profiles. They show what "someone made a profile in my name" can become and why a creation path that skips the named person is an abuse path (inference).

### 2.2 Privacy, consent, women's safety (family-made specific)

- Masii (read): consent is "the central problem"; parents may build a profile with the child's photos, filter by their own preferences and advance conversations "before the child knows"; "caring without consent creates matches built on incomplete information" (anecdotes, no data).
- The Swaddle, 5 Dec 2021 (read): a 25-year-old's mother pressured her into paying for a profile; when matches arrived she panicked and deleted it; the five columnists unanimously put the fault on the parent's missed boundaries ("Your relationship must be able to handle the concerns of both sides, not only hers."). https://www.theswaddle.com/woe-is-me-my-mother-forced-me-to-make-a-profile-on-a-marriage-site-will-i-ever-be-able-to-forgive-her
- The Quint (satire, search summary only): the narrator's mother sends "login details to your own profile". https://www.thequint.com/gender/5-stages-of-grief-on-shaadi-website-online-wedding-planning
- Blind thread (search summary only; fetch returned 402): a 25-year-old says "my parents have already created a Shaadi profile for me". https://www.teamblind.com/post/question-for-indian-guys-and-girls-vnfjofvt
- Women are the group most affected: Shaadi's own staffer says profiles of women are managed or influenced by parents "quite a bit" (ThePrint, read).
- One Deccan Herald piece was reported (search summary) to describe a father who uploaded his daughter's profile, and when she asked him to delete it the family reaction was poor. My fetch returned 403, so **not verified**. https://www.deccanherald.com/india/karnataka/bengaluru/battling-stereotypical-mindset-2116981

### 2.3 Legal position in India (reported, not advice)

- **DPDP Act 2023, section 9(1)** (read at dpdpa.com): a Data Fiduciary shall, before processing the personal data of a child "or a person with disability who has a lawful guardian", obtain verifiable consent of the parent or lawful guardian. "Child" means under 18 (section 2(k)). 9(3): no tracking, behavioural monitoring or targeted advertising directed at children. https://www.dpdpa.com/dpdpa2023/chapter-2/section9.html
- **DPDP Rules, rule 10** (read): the fiduciary must check that the person claiming to be the parent is an adult (18+), against details it already holds, details voluntarily provided, or a virtual token from an authorised entity (DigiLocker may be used). https://www.dpdpa.com/dpdparules/rule10.html
- **Rule 11** (read): for persons with disability, due diligence that the guardian was appointed by a court, a designated authority, or a local level committee. https://www.dpdpa.com/dpdparules/rule11.html
- **Section 6** (read): consent must be "free, specific, informed, unconditional and unambiguous with a clear affirmative action"; withdrawal must be as easy as giving it (6(4)). https://www.dpdpa.com/dpdpa2023/chapter-2/section6.html
- **Timing** (search summary only; sources disagree by a day): the Rules were notified mid-November 2025 with phased commencement; the children and persons-with-disabilities provisions are reported as taking effect about 18 months later, around 13-14 May 2027. See https://www.scconline.com/blog/post/2025/12/26/digital-personal-data-protection-rules-2025-key-highlights/ (not read) and https://www.tribuneindia.com/news/business/govt-notifies-digital-personal-data-protection-rules-rollout-in-phases-specified-obligations-for-data-fiduciaries (not read). Verify against the official gazette.
- **What this means (inference, not legal advice):** an adult candidate is the "data principal" for their own profile data; a parent is not an automatic consenting party for an adult. The statute's guardian route is for children and for persons with disability who have a court/authority-appointed guardian, not for ordinary adult sons and daughters. A profile made by a parent about an adult, shown to other families, is data about someone who has not consented yet. That supports a design in which the candidate's own affirmative consent is captured before anything is shown outside the family (this is a design reading of section 6; get counsel to confirm).
- **Criminal law reported in practice:** Kochi case above (BNS and IT Act, personation and identity theft). I did not read the statute sections.
- Platforms' own terms: the Matrimony.com group presumes the registrant has the candidate's consent (see 1). Lokal's terms say an account must be used only by the individual who registered it.

---

## 3. What families and candidates say they want (evidence)

Sample read for this question is small (about 10 sources, mostly features and vendor blogs; I found **no Reddit or Quora thread I could actually read**; searches returned none, so those are not quoted).

| Theme | Evidence | Count |
|---|---|---|
| Parents often lead; candidates still want the final say | Shaadi staffer on southern users: "Even if they create the account, they'd want their parents to decide everything." Pratyoush, who made a profile for his brother: "you cannot move forward without having fulfilled our parents' requirements." (ThePrint, read.) | 1 source |
| Candidates want to know and consent | "caring without consent creates matches built on incomplete information" (Masii, read). Vendor advice: "the child should always be involved in profile creation and decision-making" and "the child's opinions and comfort should always come first" (M4Marry blog, 8 Jun 2026, read; vendor blog, so not neutral) https://blog.m4marry.com/tips-guidance/parents-managing-matrimony-profiles/ | 2 |
| Pressure and resentment when a profile is made or imposed | The Swaddle letter (read); Blind post and Quint satire (search summary only) | 3 (1 read) |
| Parents are not going away, and many candidates accept them | ThePrint: 45-50% of Shaadi accounts in the South created by parents; BharatMatrimony: 7% by parents, 70% self in 2022. A matchmaker who analysed about 150,000 profiles found "roughly half were self-managed", and her advice to avoid parents "simply crumbles" for clients aged 25-30 (Priyanka Bharadwaj, 4 Mar 2021, read) https://priyankabharadwaj.substack.com/p/parent-tinder | 2 |
| Label honesty is poor | Case of "created by self" tag on a parent-run profile showing parents' contact (ThePrint, read) | 1 |
| Shared control is the design the newest players move to | Masii's "from full involvement to visibility without veto power" (read). Muzz Chaperone Mode, a member-initiated guardian view (read). | 2 |

**Parents want** (evidence: ThePrint, Priyanka Bharadwaj): to screen, make first contact and approve; to hold the account in the South especially; to keep it working when the child is busy. **Candidates want** (evidence: Masii, Swaddle, M4Marry): to be told, to see and correct what is said about them, to choose how involved the family is, and to be able to delete. **Inference:** both are served by a visible shared-control model, not by either side owning the profile.

Caveat: no survey in my sample directly asks candidates "do you want your parent to be able to create your profile?" That datum is **not found**.

---

## 4. Design for Mangalya

### 4.1 Principles (all follow from the sources and from owner decisions)

1. A profile about a named adult is a draft until that adult says yes. Nothing is shown to other families before then, unless the person is a minor/guardian case (see 4.4).
2. The parent is never blocked from preparing (DEC-V1-035, owner: "the parent is doing it, then he should be able to").
3. The candidate always finds out, in their own account, with a plain choice: this is me and I accept; this is me, family can help; this is not me, remove it.
4. The label is true and system-generated ("Managed by her mother"), never self-declared by the maker (ThePrint shows self-declared labels are wrong).
5. Every family action is reversible by the candidate and logged where the candidate can see it.
6. Reuse the Home Circle: the maker becomes a circle member with permissions. `created_by_account_id` and `claimed_at` remain the ground truth.

### 4.2 The four cases

Define a profile state machine on the existing columns plus migration 065's `managed_by_account_id` / `pending_phone` / `account_alias`:

`draft (maker only)` -> `published_managed (visible to other families, labelled managed)` -> `claimed (candidate owns, claimed_at set)`; `disowned` (removed) is terminal for that profile.

**(a) Number not on ForKhatri.** Keep what exists, finished per DEC-V1-035.
- Maker (phone-verified) fills in the profile on their device (already built, saved on-device until publish).
- Number is optional. With a number: the platform provisions a pending member; with no number: profile is `managed_by` the maker under the maker's account; label "Managed by her mother".
- Publishing: allowed, but the profile is "managed, unconfirmed". Recommended rule: shown to other families **only after the maker passes the optional face check** (this reconciles owner rule of 2026-09-21 with DEC-V1-035). Until then the maker can preview and share with their own circle only.
- The candidate receives an SMS (when a number exists) saying who made a profile for them and that nothing is sent to anyone until they respond (see 4.3); when they sign in with an OTP they see the claim screen.
- If the candidate does not respond within 30 days: stop new introductions and show the maker "paused: waiting for her" (modelled on Masii's pause; the 30 days is my proposal, not a sourced number).

**(b) Number is on ForKhatri but never opened Mangalya.** Same as (a), because the Mangalya account does not exist yet. Do not tell the maker "this person has an account" (avoid number enumeration, see 4.5); say only "we'll ask her to confirm". The person sees a notice on their next Mangalya open.

**(c) Has a Mangalya account but no profile (the sister case).** Today a dead end. New path:
- The maker still builds the profile as a `managed` draft under the maker's account (not editing her account), exactly as in (a). No Home Circle request is needed first, but one is created at the same time with `family_info` permission only.
- The candidate gets an in-app request and a notification (plus SMS if she has not opened the app recently): "Anita (sister) started a profile for you. Review it." She can: (1) Review and take it (take_over_profile, sets `claimed_at`, consent recorded, circle roles stay as she grants), (2) Take it and keep Anita editing (grant edit permission in the circle), (3) Not mine / not now (not_my_profile, draft deleted, maker told "she declined" with no reason, optional block of repeats).
- Because her account already exists, **nobody edits her account**; they edit a draft that becomes hers when she accepts. This removes the current problem that "manage only works for profiles created before she signed in".

**(d) Already has a profile; family wants to help.** No new profile. The candidate invites or accepts a Home Circle member (already built) and chooses per member: view, suggest edits, edit, message on her behalf. Recommended default for a parent: "suggest edits" (the candidate approves each change; one tap) with "edit directly" as an explicit toggle the candidate can turn on. "Suggest and approve" is the gap in the current model. Edits by family are tagged in an activity list the candidate sees ("Father changed work to Software Engineer, Tue").

### 4.3 What the candidate sees (a/b/c)

A single card, calm, in her language: "Your mother (Lakshmi Reddy, phone-verified) made a profile for you. Nobody outside your family can see it until you say so." Buttons: Review, This is me, This is not me. Under it, a plain list of what the family can do now, with a switch for each (edit, message on my behalf, see my chats: default off). A visible "Managed by" label stays on the profile until she removes it from the settings. The profile page shows to other families: "Managed by her mother" until claimed; after claim, "Profile by her; family helping". Every notification is a bell item, per the owner's layout rule, not a pop-up.

### 4.4 Age and guardians

- Mangalya already checks a minimum age at creation. Keep it, and never allow a profile for a person under 18 to be visible to other families. The DPDP Act defines a child as under 18 (section 2(k), read) and bars tracking and targeted advertising directed at children (9(3)).
- The Marathi/Lokal-style marriage-age rule in the Lokal terms (21 male, 18 female) is a platform rule, not the DPDP age; Mangalya should keep its own existing rule.
- For an adult with a court- or authority-appointed guardian (rule 11), allow the guardian to act, but require the guardian to state this and upload the order; this is a manual-review path. **Not verified** whether common matrimony apps have this; propose only as an exceptions queue, not a main flow.
- Do not let a maker profile a person whose date of birth indicates under the minimum age: the existing `TooYoung` exception covers it.

### 4.5 Abuse prevention

- Phone-verified maker always; face-verified before the profile is visible to other families (owner rule 2026-09-21, reconciled).
- Rate limits (proposed values, no source): a maker may start at most 3 managed drafts per 30 days and 5 active at once; at most 1 SMS or notification to a given number per 7 days; a number that has used "not mine" twice blocks further drafts from that maker for that number. A maker who is declined three times is flagged for review.
- The candidate can always remove: "This isn't me" works on unclaimed drafts (exists). Extend it so the candidate can also delete a claimed profile (account deletion is DEC-V1-036, already built).
- No number enumeration: the maker sees the same message whether the number is known or not.
- The family may not see who else is interested in her until she claims (default for a woman candidate: photo hidden from non-connected families; Jodii offers a photo-hiding choice for women, per the launch material, search summary only).
- Photo upload by a maker triggers the same photo checks as any photo; the face check compares the maker's live face with the maker's own photo, never with the candidate's, so that a malicious maker cannot pass off someone else's photos as consent. **Inference:** this means a maker can still upload a stranger's photo as "my sister"; the candidate review step and the "paused after 30 days" rule are the mitigations, plus the report path.
- Audit: store who created, when, the relation claimed, and the notification sent, so a complaint can be handled. This is what the complainant in the BharatMatrimony case (read) could not get answers to.
- Reporting: a "this profile is of me and I didn't make it" report path available to a non-member via the SMS link (the Kochi case shows why).

### 4.6 Options considered

| Option | What it is | Gains | Costs |
|---|---|---|---|
| 1. Status quo | Refuse when the number is known; "ask to join Home Circle" | Safest; nothing built | Dead end for case (c); parents blocked (owner said no) |
| 2. Presumed consent (incumbent model) | Maker creates and publishes; maker's declaration is consent | Fastest for parents; same as the Matrimony.com terms (search summary) | Weakest on consent; mirrors the complaints; hardest to defend under section 6 (inference) |
| **3. Draft, notify, claim, with visibility gate (recommended)** | Maker builds a managed draft; candidate is notified; shown to other families only after the maker is verified; candidate can claim, share, or disown at any time; pause after 30 days of silence | Fits DEC-V1-035 and migration 065; covers all four cases with one mechanism; consent is affirmative and recorded; reuses `created_by` / `claimed_at` and the Home Circle | Needs a new "pending claim" inbox, one SMS, and activity log; some parents will find the visibility gate annoying |
| 4. Candidate-first only | Candidate must accept before any draft exists | Strongest consent | Blocks the parent-led South use (45-50% per Shaadi data); contradicts the owner's "parent should be able to" |
| 5. Suggest-and-approve only for all family edits | No direct editing even after claim | Strong control for the candidate | Too slow for a parent who is the main user; keep it as a per-member setting instead |

**Recommendation: Option 3.** It is the only option that keeps the parent unblocked (owner, 2026-10-06), makes the candidate's own yes explicit (DPDP section 6 reading), and fits the code that exists.

### 4.7 Build plan on top of existing code

| Step | Effort | Status in code |
|---|---|---|
| Apply the pending `/profile/managed` change per DEC-V1-035: optional `child_phone`, managed account via `create_managed_account` when absent or taken, `set_pending_phone`; keep the face check as a visibility gate rather than a creation gate | M | Migration 065 present; route not changed; needs the owner's hand |
| "Made for my number" inbox and review/claim screen using `made_for_my_number`, `take_over_profile`, `not_my_profile` | M | Functions exist in migration 065; no route or web screen verified |
| Case (c): the same draft path when the number is a member without a profile | M | Currently returns 409 |
| Visibility gate (managed profile hidden from other families until the maker is face-verified) and the "Managed by" label from system data | S | Not verified in Discover code |
| Suggest-and-approve edits for circle members (d) with activity list | L | Not built (permissions exist; approval flow not found) |
| 30-day pause, rate limits, "not mine" blocklist, audit | S-M | Disown notification exists; limits not verified |

---

## 5. Everything not verified

- Official registration flow and labels at Shaadi, BharatMatrimony, Jeevansathi, Jodii, Betterhalf, Kaakateeya, Simply Marry (bot-walled or absent).
- The Shaadi App Store "son, daughter, brother, sister..." sentence: reported by search, not on the pages I fetched.
- Marathi/Parsi terms: quoted from search summaries (pages returned 403).
- DPDP commencement dates for children and disability rules: search summaries only.
- Feminism in India article, Deccan Herald article, Walrus article, Blind thread, Quora and Reddit threads: not read.
- Any candidate survey on proxy profile creation: not found.
- All rate-limit and timeout numbers in section 4.5 are my proposals, not sourced.

## 6. Sources read (fetched and read)

- ThePrint, 4 Sep 2022: https://theprint.in/feature/parents-no-longer-make-matrimonial-profiles-of-children-but-theres-a-north-south-divide/1109683
- Masii, 12 Feb 2026: https://masii.pages.dev/blog/the-proxy-problem
- Priyanka Bharadwaj, 4 Mar 2021: https://priyankabharadwaj.substack.com/p/parent-tinder
- The Swaddle, 5 Dec 2021: https://www.theswaddle.com/woe-is-me-my-mother-forced-me-to-make-a-profile-on-a-marriage-site-will-i-ever-be-able-to-forgive-her
- M4Marry blog, 8 Jun 2026 (vendor): https://blog.m4marry.com/tips-guidance/parents-managing-matrimony-profiles/
- ConsumerComplaints, BharatMatrimony profile created without knowledge, Jan 2018: https://www.consumercomplaints.in/bharat-matrimony-profile-created-without-my-knowledge-c1837718
- ConsumerComplaints, deletion, May 2022: https://www.consumercomplaints.in/bharat-matrimony-not-able-to-delete-my-profile-c3186086
- ConsumerComplaints, fake dating profile, Mar 2020: https://www.consumercomplaints.in/bharat-matrimony-fake-casual-dating-profile-shreya-das-nagpur-c2594034 (low relevance)
- Onmanorama, 6 Jul 2026: https://www.onmanorama.com/news/kerala/2026/07/06/matrimonial-ad-photo-probe.html
- Tribune impact feature (sponsored), 28 Dec 2023: https://www.tribuneindia.com/news/impact-feature/how-shaadi-com-is-making-online-matrimony-safer-with-proactive-anti-scam-efforts-576166
- DPDP Act section 9, section 6; DPDP Rules 10 and 11 (dpdpa.com, URLs above)
- Lokal Matrimony terms: https://matrimony.getlokalapp.com/policies/v2/terms-and-conditions/
- Muzz help: https://muzz.com/help/getting-started/how-is-muzz-halal
- App Store, BharatMatrimony: https://apps.apple.com/us/app/id465923141 ; App Store, Shaadi: https://apps.apple.com/in/app/shaadi-com/id480093204 (no creator text on either page)
- Jeevansathi help: https://jeevansathi.freshdesk.com/support/solutions/articles/5000703780-how-can-i-register-on-jeevansathi
- Shaadi homepage (no creator selector visible): https://www.shaadi.com/
- Himal (paywalled, nothing usable): https://himalmag.com/marriage-2-0/
- Local: `modules/MOD03-mangalya/v1-decisions.md` (DEC-V1-019, 025, 027, 035), `mangaly-service/app/api/routes/profile.py`, migration 065.

## 7. Sources cited from search summaries only (not read directly)

Marathi and Parsi Matrimony terms; Shaadi help (phone change); Jodii launch release; YourStory/Betterhalf; Swati Mukund coverage (Asianet); Telangana Today Hyderabad case; SCC Online and Tribune on DPDP phasing; The Quint; Blind; Deccan Herald.

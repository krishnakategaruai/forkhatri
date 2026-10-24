# Mangalya onboarding: what we learned, and what we will build

Date: 2026-10-06. This is a learning document with decisions. No app code was changed.
Mockups: `AgentOutputs/onboarding-mockups/mangalya-onboarding-proposal.html`.
Screenshots of the walk: session scratchpad `mangalya-audit/` (s24 = Sujatha, s25 = Ramesh, s26 = Anjali, broker = Suresh).

## 1. How we tested

We used brand-new members whom no module had seen before, on a 390px phone, in each person's own language, through the public Mangalya address (the tunnel) opened from the ForKhatri hub:

- **Sujatha Reddy (#24, Telugu).** A mother in Hyderabad making her daughter's profile on a shared phone.
- **Ramesh Babu Khatri (#25, Telugu).** A father with a biodata PDF and photos on WhatsApp.
- **Anjali Verma (#26, English).** A candidate working in London, making her own profile. She does not know her birth time.
- **Suresh Naidu (agent persona).** A broker adding a family's details. Read-only; nothing saved.

Sign-in note for the hub team: password sign-in at `http://localhost:3100` fails without any message, because the hub posts to `/api/identity/v1/auth/login` and gets a 404. We opened each session with the development "act as" endpoint for that member instead.

## 2. Where Mangalya is rigid in practice

These are moments from the real walk, in the order a person meets them.

1. **No way to just look around.** Opening Mangalya always lands on "Who is this profile for?", every visit, until a profile exists. Sujatha wanted to see what the app is like first. There is no "look around" choice and no menu on that screen. Discover works if you type its address, but nothing leads there.
2. **The story is seven screens.** It is seven taps before the first question, or one tap on "Skip". It reads well in Telugu. One line is ambiguous: "ఏదీ దాచని ప్రైవేట్ చాట్" can be read as "a private chat that hides nothing".
3. **A parent is stopped at the first tap.** The moment Sujatha tapped "My daughter", Mangalya asked her to verify her own face before she could type her daughter's name. The verify page is titled "Confirm your photos", although she has no photos yet.
   - She added her own photo, ticked a long consent sentence and tapped "Start camera". The screen stayed on "Camera getting ready…" for more than 20 seconds, with no timeout and no alternative. In our test the camera permission was never answered. In real life the cause would be an old phone, a shared phone with a weak front camera, or a computer with no webcam.
   - "Cancel" returns to the same screen. There is no "do this later and keep filling in".
   - Ramesh hit exactly the same wall, and so did the broker when he opened "Add clients". **Neither parent could make a child's profile at all.**
4. **The child's own mobile number is the first question,** before the name (read from code; we could not get past the gate). It needs 10 digits and is the account the profile will belong to. This breaks in three ordinary cases:
   - The daughter uses her mother's phone: that number is already the mother's account.
   - The daughter already uses another ForKhatri module: the save fails at the very end with "already joined".
   - The family wants to prepare the profile quietly first.
5. **Age is refused only at the end.** Anjali entered a 2012 birth date. Every step accepted it until she pressed "Save profile" after the photo; only then did "You must be at least 18" appear.
6. **The date of birth uses the phone's own date picker,** which opens on today. An elder has to scroll back about 28 years.
7. **The city is free typing with no suggestions.** "London, United Kingdom" was accepted. There is no idea of a home town, which every biodata has. The horoscope sheet already has a good place search, but the wizard does not use it.
8. **Four "work and life" answers are forced on one screen:** education, occupation (typed), marital status and willingness to relocate. The server accepts them blank; only the wizard insists.
   - Education has no Diploma or professional degree (CA, MBBS). Its "Other" cannot be filled in.
   - Relocation offers both "Yes" and "Open to relocating", which mean the same thing.
9. **One photo is required, and one at a time.** Ramesh's WhatsApp photos have to be saved to the gallery and picked one by one.
   - There is nowhere for a family to upload a biodata. The broker's form can (PDF or image, several photos, only name and gender required). **Families get the rigid path; brokers get the flexible one.**
10. **Nothing is saved until the end.** When Ramesh's window was resized or reloaded, he was sent back to "Who is this for?" and every answer was lost. (Going Back inside the wizard does keep answers.)
11. **The setup matchmaker is about six phone screens long:** own words, understood points, an "add a point" list, six "what matters" rows of four buttons, and scales.
    - **Bug:** "Read my words" replaced the points already set from her profile (Age 29–34, United Kingdom) instead of adding to them.
    - It understood "Khatri" and "vegetarian". It missed "does not smoke", "UK or willing to move" and "education matters".
    - Home then said "Matching on Community, Diet" while My profile said "Age 29–34 · United Kingdom".
    - It offered "Horoscope match: Guna Milan with your chart" before she had any chart.
    - The floating "Save and see matches" button covers the Age card.
12. **After setup, the hardest task is suggested first.** My profile shows 50% complete, and "Next up" is the one-minute camera check rather than an easy question.
13. **Things that already work well:**
    - Name prefilled from ForKhatri.
    - Bride or groom worked out from gender.
    - Back keeps answers inside the wizard.
    - "Choose or take" photo, with the camera only on request.
    - A horoscope sheet with "Don't know the time", a direct rashi and nakshatra choice, "Manglik: don't know", and birthplace search that works abroad (Leicester found).
    - Calm look, and complete Telugu.
14. **Small issues:**
    - After a window resize, Ramesh's Telugu screen showed English for a moment.
    - "Remove photo" and photo replacement leave the old file on disk; we deleted our two test leftovers by hand.

**Counts today:**

- **Own profile (Anjali):** 6 screens plus the story. 9 required answers (the server needs 6), 2 typed answers. About 22 taps from the hub to Home with the story skipped, 28 with it.
- **Child profile:** 7 screens plus the gate. 10 required answers, including the child's phone. Blocked at the gate in practice.

## 3. What real users and research say

- **Parents run most daughters' profiles.** In 124,435 profiles on a major site, under a third of women managed their own (Ferry & Subtil 2023, https://csh-delhi.com/wp-content/uploads/2023/11/Digitized_Matchmaking_WP19.pdf). On a 150,000-profile Brahmin site, only 22% of women's profiles were self-managed (https://priyankabharadwaj.substack.com/p/parent-tinder). **The parent path is the main path, not the side path.**
- **Mandatory fields are few; the rest comes later.**
  - Shaadi requires its "compulsory fields" and offers "Other" when a list lacks your answer (https://support.shaadi.com/support/solutions/articles/48000962494, …/48000962495).
  - Shaadi's design team credits "progressive fields" for higher completion (https://design.shaadi.com/dive-into-the-world-of-form-design).
  - The large study found 27,173 profiles with no photo, mostly young women's family-managed profiles (Ferry & Subtil).
- **Photos.** Shaadi has "Request photo" and photo privacy settings (…/48000953215, …/48000755499). Hinge asks for 4–6 photos and 3 prompts, and accepts that about 20% don't finish (https://www.globaldatinginsights.com/featured/hinge-ceo-intentional-dating-and-onboarding-set-hinge-apart/).
- **Verification is mostly opt-in, at a predictable moment.**
  - Opt-in: Hinge selfie ("voluntary"), Bumble outside the USA, Jeevansathi's NRI check (https://identityweek.net/onfido-partners-with-matrimony-site/) and BharatMatrimony's "Prime" (https://bureau.id/resources/blog/how-bharat-matrimony-is-onboarding-trustworthy-users).
  - The loudest complaints are surprise holds: "it asked documents to verify. It would not let me in" and "within seconds of creating a profile, it was deactivated" (https://justuseapp.com/en/app/969994186/jeevansathi-com-matrimony-app/reviews, https://justuseapp.com/en/app/480093204/shaadi-com-matrimony-app/reviews).
  - "Under screening" for 14 days (https://www.consumercomplaints.in/shaadi-com-account-under-screening-from-14-days-c2196198).
- **Sales calls right after signup are the top complaint about BharatMatrimony:** "they don't give a chance to even browse" (https://justuseapp.com/en/app/465923141/bharatmatrimony-matrimony-app/reviews). Mangalya makes no such calls, and should keep it that way.
- **Biodata is the family's real format.** It is a PDF or photo on WhatsApp, with family, horoscope and work, and often the parents' contact details (https://www.nbcnews.com/news/amp/ncna150996).
  - Brokers take "two passport-sized pictures, laudatory biodata" (https://tribuneindia.com/1999/99dec25/saturday/head9.htm), keep files and key in "age, education, caste, height, location, astrological compatibility" (https://openthemagazine.com/new-year-double-issue/the-last-marriage-broker).
  - No big app is documented importing a biodata (gap). One startup claims an AI biodata reader (RokaMaybe, unverified).
- **Unknown birth time is normal.** Guna Milan mostly needs only the Moon's nakshatra. Without a time, the lagna and Mangal dosha are uncertain, so results should be marked "provisional", and families often have a priest's horoscope with the star (https://astromedha.in/insights/vedic/kundli-matching-without-birth-time, https://daanyam.in/blog/kundli-matching-by-name-without-birth-time). Births abroad and Indian births before 1955 need real time-zone history (https://roxyapi.com/blogs/dst-historical-timezone-vedic-kundli-accuracy).
- **Shared phones.** South Asian women commonly share phones with family, and their use is watched (Sambasivan et al., SOUPS 2018, https://www.usenix.org/conference/soups2018/presentation/sambasivan). One number for one person does not fit every family.
- **Shaadi allows one profile per person.** A profile for a relative needs a different email (…/48000962490), so a parent with two children juggles accounts.
- **Gaps:** Reddit could not be read. Jeevansathi's and BharatMatrimony's exact field lists could not be confirmed. Nobody documents a "don't know the birth time" button.

## 4. Screen by screen: today, evidence, proposal

| # | Screen today | What is rigid in practice | Evidence | Proposal |
|---|---|---|---|---|
| S0 | Story, 7 slides | 7 taps before anything | Owner rule: a story at first launch | **Keep, cut to 3 cards** (family together; mutual match and requests; help and agents), with Help holding the rest |
| S1 | Who is it for: 4 choices | No "look around"; no sibling; forced every visit | BharatMatrimony lists self, son, daughter, brother, sister, relative; most daughters' profiles are family-run | **Add "My sister or brother", "Start from a biodata" and "Just look around first"** (mockup S1) |
| Gate | Face check before anything | Parents and brokers blocked at the first tap; no fallback | Opt-in or end-of-flow verification everywhere; surprise holds are hated | **Move the check to "Check and publish"** after the work is done; same rule, no account made before the check (mockup S6) |
| S-child | Child's phone first | Fails for shared phones, existing members, quiet preparation | Shaadi needs a separate identity per profile; families share phones | **Ask the number last, at publish**, with "already on ForKhatri? send her an invite instead" |
| S1-name | Name alone | One tap for a prefilled name | Progressive fields | **Merge** name, date of birth and gender into one "About" card (mockup S2) |
| S2 | Native date picker | Scrolls from today; age refused at the very end | Shaadi's tap-friendly inputs | **Day, month, year dropdowns**, year list starting 18 years back, age checked right there |
| S3 | City, typed | No suggestions, no home town | Biodata always has a native place | **Place search** (reuse the horoscope place search), abroad allowed; "home town" optional later |
| S4 | Work and life, all 4 forced | Typing, overlapping options, no "Other" text | Shaadi's "Other" option | **Searchable occupation, education with Diploma and Professional plus "Other: type"**, three relocation answers; **"Skip for now"** keeps the profile out of search until filled |
| S5 | One photo, required | One at a time; no biodata route | Photo-less family profiles common; brokers already upload biodata | **Several photos at once; "Add later" saves a draft** (never published without a photo) |
| New | Biodata import | Does not exist for families | Biodata is the family's format; gap in the market | **"Start from a biodata"**: read the PDF or image, fill fields, family checks each line (mockup "From her biodata") |
| S6 | Matchmaker, about 6 screens | Long; own words wipe prefilled points; horoscope offered without a chart | Hinge nudges improvements later | **Short setup card**: own words plus Speak plus the 2–3 prefilled points; themes and scales move to My profile; fix the merge bug; hide horoscope until a chart exists (mockup S7) |
| Me | 50%, next = camera check | Hardest step suggested first | Completion meters (Bumble), prompt feedback (Hinge) | **"Next up" is the easiest missing answer**; the camera check is offered, not pushed |
| Horoscope | Sheet works | Rashi shown as 12 open chips | Unknown-time practice | **Keep.** Rashi becomes a dropdown; add "attach a horoscope (jathakam) photo"; mark unknown-time matches "provisional" |
| Family Me | MemberMe | Verify title says "your photos" | — | Retitle to "A one-minute check that it's you" |

## 5. The new flow

**Own profile (Anjali):**

1. Story (3 cards, once).
2. Who is it for: Myself.
3. About: name prefilled, date of birth with an inline age check, gender.
4. Where: place search.
5. Photos: several at once, or "Add later" as a draft.
6. Work and life: skippable.
7. Short matchmaker.
8. Home.

That is 5 screens after the story. Required answers fall from 9 to 5 (name, date of birth, gender, city, photo). Typed answers fall from 2 to 0–1, and taps from about 22 to about 14.

**Child profile (Sujatha or Ramesh):**

1. Who is it for: My daughter.
2. About her.
3. Where.
4. Photos, or start from a biodata, which fills steps 2–5.
5. Work and life.
6. Check and publish: her mobile number, plus the one-minute check that it's you.
7. Short matchmaker.

The parent finishes every step without hitting a wall. Each step is saved on the device and can be resumed. A parent with no working camera keeps the draft and finishes on another phone or later.

## 6. Decisions

| # | Decision | Why |
|---|---|---|
| D1 | Add "Just look around first" (Discover with bride/groom chosen; no requests until a profile exists) | Shows value before asking; Looking-for stays applied |
| D2 | Cut the story to 3 cards, keep it skippable, rest in Help | Owner rule kept; 7 taps was the first rigid moment |
| D3 | Add "My sister or brother" to who-for | Matches BharatMatrimony and real families |
| D4 | Move the parent's face check to just before publishing; no account is provisioned before it passes | Keeps DEC-V1-025 exactly (only verified people create profiles for others) while removing the first-tap wall |
| D5 | Child's phone asked at publish, not first; if the number already belongs to a member, offer "invite her to make you family" instead of an error | Same DEC-V1-019 ownership, no dead end |
| D6 | Check age at the date-of-birth step (server rule unchanged) | Refusal after the photo wastes the whole flow |
| D7 | Date of birth as three dropdowns, year list from 18 years back | Elders and low-literacy users |
| D8 | City via the existing place search; home town optional in the profile | Biodata practice; no new data model needed for the city |
| D9 | Work-and-life answers skippable; profile saved but not in search until added; tell the person plainly | Server already allows it; DEC-V1-001 tiers kept (existence vs discoverable) |
| D10 | Education adds Diploma and Professional; "Other" opens a text box; relocation shows Yes, No, Can discuss | Removes duplicate options; the "Other" rule |
| D11 | Several photos at once; with no photo the work is kept as a device draft, never published | DEC-V1-001 needs one photo to save a profile; a draft is not a profile |
| D12 | Save progress on the device (including photos) at every step; resume on return | Lost answers on reload; avoids storing a child's data on the server before publish (critique C3) |
| D13 | Build "Start from a biodata": the family's PDF or image is read by Mangalya's AI into the closed field list, the family confirms each line; the file is kept only if they tick "attach"; works without AI by letting them attach and type | Families' real format; brokers already have it; no rival documents it |
| D14 | Setup matchmaker becomes one short card; themes and scales move to My profile; "Read my words" adds and never removes; horoscope theme hidden until a chart exists | Owner's AI-first setup kept, at a sensible length |
| D15 | "Next up" chooses the easiest missing answer; the camera check is a separate optional card | Completion by small steps |
| D16 | Horoscope: rashi as a dropdown; unknown-time results labelled "provisional"; optional horoscope photo attachment | Real practice; the collapse rule |
| D17 | Fix: the verify page title for family members; the brief English flash; deleting files when photos are removed | Bugs found in the walk |
| D18 | Voice: "Speak" stays on the matchmaker; a guided voice path for the wizard follows later | Owner's voice rule; out of this build's scope |

**Questions left for the owner (only these):**

- **Q1. Shared-phone daughters (reverses DEC-V1-019).** May a parent publish a child's profile with no number of the child's own, kept under the parent's account as "managed by her mother" until the child joins? We recommend yes, with the child's own consent recorded when she joins.
- **Q2. A fallback when the face check is impossible (operations and legal).** Should there be a Samaj-office or video-call check for parents without a usable camera? We recommend yes, but it needs named volunteers.
- **Q3. Sending a biodata to the AI (privacy).** A biodata holds family names, numbers and birth details. We recommend a clear one-line consent before reading, and deleting the file after reading unless the family attaches it. Please confirm under DPDP.

## 7. End state of the test members

- **Anjali (#26):** a published candidate profile (London, 29). The matchmaker is saved and the horoscope is saved with "Don't know the time" and Simha. Her stock test photo was replaced by a drawn portrait and the old file deleted.
- **Sujatha (#24):** a Mangalya family "My profile" with a drawn photo, not verified, and no child profile.
- **Ramesh (#25):** opened Mangalya only, with no data.
- **Divya (#11):** a development session only, no Mangalya data.
- **Broker:** nothing saved.

## 8. Final decisions (2026-10-06)

- D1 to D17 are accepted as written. D18 (a guided voice path for the wizard) follows later.
- **Q3 decided:** before Mangalya reads a biodata, show one clear consent line in the family's language ("Mangalya will read this file to fill the form for you. The file is deleted after reading unless you choose to attach it."). Without consent, the family attaches and types. Delete the file after reading unless attached.
- **Q1 left for the owner** because it reverses DEC-V1-019. Until then the child's own phone stays required, asked at publish (D5).
- **Q2 left for the owner** because it needs named Samaj volunteers. Until then, if the camera cannot start, the screen says so plainly, keeps the draft on the device, and offers "Try again later"; nothing is lost.

## 9. Owner answers (2026-10-06)

- **Q1, yes.** Owner: "yes, right — the parent is doing it, then he should be able to." A parent can publish a son's or daughter's profile without the child's own phone number. It is kept under the parent's account and shown as managed by the parent until the child joins; the child's number becomes optional. This changes DEC-V1-019.
- **Q2, no.** Owner: "why would that much, is this an app or what?" No Samaj-office or video fallback. The live face check becomes an optional trust step that earns the photo badge, never a gate before creating or publishing a child's profile. This changes DEC-V1-025.

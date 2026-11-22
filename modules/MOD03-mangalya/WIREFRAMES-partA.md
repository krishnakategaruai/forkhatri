# Mangalya wireframes, Part A: profile making, profile view, My profile, horoscope check

As built, read from `mangaly-web` code (static reading, no browser). English strings are from `mangaly-web/locales/en/*.json`. 390 px phone width. SCR ids follow `03-ux.md` as-built addendum (line 2455).

Legend: `[ Button ]` button, `( ) / (x)` radio, `[v]` dropdown, `[x]` checkbox, `(1)` numbered callout.

---

### SCR-03 Profile wizard (`/profile/create`)

Source: `app/profile/create/page.tsx`. Query params: `for=child` (+ `who=son|daughter`) jumps past the chooser; `start=1` ignores any saved draft. Internal screens: `who`, `biodata`, `biodataCheck`, `form` (steps `about`, `where`, `photos`, `work`, `publish`), plus a notice screen (`draftKept`, `alreadyJoined`) and the 3-card story (first time only, not when `for=child`). Self path has 4 steps; for someone else 5 steps (adds Check and publish). Nothing is sent to the server until Publish; every answer is saved on this device (300 ms after each change) and restored on return (shows "Your answers were kept on this phone." and "Start again"). Browser back and the back arrow step back one step, from the first step to the chooser.

#### SCR-03a Who is this profile for?

```
+--------------------------------------+
|        (family vignette art)         |  (1)
|  Who is this profile for?            |  (2)
|  Most families make it together. You |
|  can add who helps later.            |
|                                      |
|  [ Myself                          ] |  (3)
|  [ My daughter                     ] |
|  [ My son                          ] |
|  [ My sister or brother            ] |
|  [ Someone else in my family       ] |
|  [ Start from a biodata            ] |  (4)
|    A PDF or photo, for example from  |
|    WhatsApp. We fill in what we can; |
|    you check it.                     |
|                                      |
|  Just look around first  (link)      |  (5)
|   -> "Who would you like to see?"    |
|      [ Brides ] [ Grooms ]           |
|                                      |
|  Does your son or daughter already   |
|  have a Mangalya profile? Ask them   |
|  to add you to their Home Circle ... |  (6)
+--------------------------------------+
```

| # | Element | What it does | Data | States | Next |
|---|---|---|---|---|---|
| 1 | Vignette art | Decoration (id `family`) | none | n/a | none |
| 2 | Title and hint | Explains the choice | none | n/a | none |
| 3 | Five who-for buttons | Sets `forWhom` (self, daughter, son, sibling, relative); son/daughter pre-set gender and looking-for (bride/groom); self prefills name from session `display_name` | `forWhom` | With `for=child` the Myself option is hidden (4 options) | SCR-03c About |
| 4 | Start from a biodata | Opens biodata screen | none | always shown | SCR-03h |
| 5 | Just look around first | Reveals Brides/Grooms choice; stores browse "looking for" and goes to the photo wall | `writeBrowseLookingFor` | Hidden when `for=child` | `/discover` |
| 6 | Already-has-profile note | Tells a parent to ask the child to add them to Home Circle | none | none | none |

Role notes: candidate picks Myself; parent/family picks daughter, son, sibling or relative. Broker/agent does not use this wizard (agents add offline biodata at `/agent/biodata`, SCR-21).

#### SCR-03b Story, first time (short)

Shown once before the chooser when no draft exists, no `for=child` and the story was not seen. Component `MangalyaStory short`; three skippable cards (D2). On done it marks the story seen and shows SCR-03a. Content strings live in `home.json` (not covered here).

#### SCR-03c Step About (step 1)

```
+--------------------------------------+
| [<]  About · 1 of 5                  |  (1)
| [=====-----------------------------] |  (2)
|        (basics vignette)             |
|  About your daughter                 |  (3)
|  Resumed: "Your answers were kept on |
|  this phone."          [Start again] |  (4)
|                                      |
|  Her name                            |  (5)
|  [___________________________]       |
|  Date of birth                       |  (6)
|  [ Day v ] [ Month v ] [ Year v ]    |
|  "27 years old"  | error: "A bride   |
|   must be at least 18 to have a      |
|   profile on Mangalya."              |
|  I am / They are  (self, relative)   |  (7)
|  [Female] [Male] [Other]             |
|  (sibling: [My sister] [My brother]) |
|  (other: [Bride] [Groom])            |
|  "She will see groom profiles."      |  (8)
|                                      |
|  (error line, aria-live)             |
|  [            Next               ]   |  (9)
+--------------------------------------+
```

| # | Element | What it does | Data | States | Next |
|---|---|---|---|---|---|
| 1 | Back arrow and step label | Steps back (to the chooser from the first step) | `stepName.about`, `stepOf` | n/a | SCR-03a |
| 2 | Progress bar | Width = step/total | none | 4 or 5 steps | none |
| 3 | Title | `title_self/daughter/son/sibling/relative` | `forWhom` | n/a | none |
| 4 | Resume note and Start again | Shown when a device draft was restored; Start again clears the draft and reloads with `?start=1` | draft | only when resumed | SCR-03a |
| 5 | Name field | Required text; label "Your name / Her name / His name / Their name" | `name` | required | none |
| 6 | Date of birth, three dropdowns | Day (follows month length), Month (localized names), Year (18 to 80 years back); age shown live | `dob`, `age` | Under-age: "A bride must be at least 18..." / "A groom must be at least 21 to have a profile on Mangalya." (female 18, male and other 21); Next disabled | none |
| 7 | Gender control | Self and relative: three buttons (Female, Male, Other); sibling: "My sister"/"My brother"; son/daughter: none (preset). Gender Other adds Bride/Groom looking-for choice | `gender`, `lookingFor` | Next disabled until all set | none |
| 8 | "Will see" line | "You will see bride profiles." / "She will see groom profiles." etc. | `lookingFor` | shown once looking-for is known | none |
| 9 | Next | Validates About; Next disabled until name, full date, gender, looking-for are set and age is allowed | `aboutValid` | disabled/enabled | SCR-03d |

#### SCR-03d Step Where (step 2)

```
+--------------------------------------+
| [<]  Where · 2 of 5                  |
| [==========------------------------] |
|  Where do you live?                  |  (1)
|  Search the town or city. Living     |
|  abroad is fine.                     |
|  City or town                        |
|  [ Hyder...                      ]   |  (2)
|   - Hyderabad, Telangana, India      |  (3)
|   - Hyderabad, Pakistan              |
|  [            Next               ]   |  (4)
+--------------------------------------+
```

| # | Element | What it does | Data | States | Next |
|---|---|---|---|---|---|
| 1 | Title | "Where do you live?" for self, "Where does {{name}} live?" for others | `firstName` | n/a | none |
| 2 | Place search | `PlaceSearch` component; type-ahead of places; value must be a picked place | `place.label` saved as `cityLocality`, `place_id` | empty: Next disabled; restored draft shows the saved label | none |
| 3 | Suggestions | Tap one to set | `place` | loading/empty list inside PlaceSearch (unverified detail) | none |
| 4 | Next | enabled when a place is set | `whereValid` | disabled/enabled | SCR-03e |

#### SCR-03e Step Photos (step 3)

```
+--------------------------------------+
| [<]  Photos · 3 of 5                 |
| [===============-------------------] |
|  Add your photos                     |  (1)
|  Choose several at once, for example |
|  from WhatsApp. One is enough to     |
|  begin.                              |
|  +------+ +------+ +------+          |
|  | Main | |      | |      |          |  (2)
|  | photo| | img  | | img  |  [x]     |
|  +------+ +------+ +------+          |
|  [ Choose photos ]  [ Take a photo ] |  (3)
|  [            Next               ]   |  (4)
|  Add photos later (kept as a draft   |
|  on this phone)                      |  (5)
+--------------------------------------+
```

| # | Element | What it does | Data | States | Next |
|---|---|---|---|---|---|
| 1 | Title and hint | "Add your photos" or "Add {{name}}'s photos" | none | n/a | none |
| 2 | Thumbnails | First photo carries the "Main photo" tag; each has a remove button (aria "Remove photo"); up to 6; "{{count}} added" is used on the check screen | `photos[]` (Blob, name, type) held in the device draft | empty: no grid; 6 reached: both buttons disabled | none |
| 3 | PhotoChoice (see SCR-03f) | Choose from gallery or take with camera | files | disabled while busy or at 6 | none |
| 4 | Next | enabled once at least one photo is added | `photos.length` | disabled when empty | SCR-03g (work) |
| 5 | Add photos later | Skips ahead without a photo (draft kept); publishing later needs one photo | none | always shown | SCR-03g |

#### SCR-03f Photo choose / take (components `PhotoChoice`)

```
+--------------------------------------+
|  [ Choose photos ]  [ Take a photo ] |  (1)(2)
+--------------------------------------+
```

| # | Element | What it does | Data | States | Next |
|---|---|---|---|---|---|
| 1 | Choose photos / Choose a photo | Opens the device gallery (`image/jpeg,png,webp`); multiple allowed where `onFiles` is used (wizard); the plain "Choose a photo" label is used for single-photo places | `File[]` | primary style normally, plain (`quiet`) in the wizard; disabled while busy (optional busy label) | back to caller |
| 2 | Take a photo | Opens the camera (`capture="user"`), only on tap, never automatically; on a computer it opens the file dialog | `File` | disabled while busy | back to caller |

Photos are shrunk by `preparePhoto` to JPEG up to 2048 px, quality 0.86, under 8 MB, EXIF location removed (per addendum; not re-read in this component).

#### SCR-03g Step Work and studies (step 4)

```
+--------------------------------------+
| [<]  Work and studies · 4 of 5       |
| [===========================--------] |
|  Your work and studies               |
|  Families search by these first.     |
|  Highest education level             |
|  [ Choose v ]                        |  (1)
|  (if Other) Which course or degree?  |
|  [______________________]            |
|  Occupation                          |
|  [ For example: Software engineer ]  |  (2)
|  Marital status                      |
|  [ Choose v ]                        |  (3)
|  Relocation willingness              |
|  [ Choose v ]                        |  (4)
|  [ Save profile ]  (self)            |  (5)
|   or [ Next ] (someone else)         |
|  Skip for now                        |  (6)
|  The profile can be saved now. It    |
|  appears in search once these four   |
|  are added; add them from My profile |
|  anytime.                            |
+--------------------------------------+
```

| # | Element | What it does | Data | States | Next |
|---|---|---|---|---|---|
| 1 | Highest education | Options: high_school, diploma, bachelors, professional, masters, doctorate, other (labels from `option.highest_education_level.*`); Other reveals a text field | `educationLevel`, `educationOther` | required for the four to count | none |
| 2 | Occupation | Free text with datalist suggestions (Software engineer, Doctor, Teacher, Engineer, Chartered accountant, Lawyer, Banker, Architect, Government job, Own business, Homemaker, Student) | `occupation` | none | none |
| 3 | Marital status | never_married, divorced, widowed, awaiting_divorce | `maritalStatus` | none | none |
| 4 | Relocation willingness | yes, no, open_to_discussion | `relocationWillingness` | none | none |
| 5 | Primary button | Self: label "Save profile" if a photo exists, else "Keep my draft"; click publishes (`createProfile`). Someone else: "Next" | `workValid` | Self: disabled unless About and Where valid and (work complete or no photo); busy: "Publishing…" | self: `/me/matchmaker?setup=1`; other: SCR-03h |
| 6 | Skip for now | Self: saves the profile without the four work answers; someone else: moves to publish | none | disabled while busy | as above |

Server error on save: line under the form shows the server message or "We couldn't reach Mangalya. Check your connection and try again."

#### SCR-03h Step Check and publish (someone else only, step 5)

```
+--------------------------------------+
| [<]  Check and publish · 5 of 5      |
| [====================================]|
|  Ready to show Kavya's profile       |  (1)
|  Name, age, city        Done         |  (2)
|  Photo                  2 added      |
|  Work and studies       Add to appear|
|                         in search    |
|  Her mobile number                   |  (3)
|  [ +91 ____________ ]                |
|  When she signs in with it, the      |
|  profile becomes hers.               |
|  <askJoin question from circle.json> |  (4)
|  (Father)(Mother)(Brother)...        |
|  (o) A one-minute check that it's    |  (5)
|      you                             |
|      Needed once before you publish  |
|      a profile for someone else. ... |
|  [ Publish profile ]                 |  (6)
|   or [ Start the one-minute check ]  |
|  Not now: keep my draft              |  (7)
+--------------------------------------+
```

| # | Element | What it does | Data | States | Next |
|---|---|---|---|---|---|
| 1 | Title | "Ready to show {{name}}'s profile" | `firstName` | n/a | none |
| 2 | Checklist | Basics, Photo ("Add one to publish" when missing), Work ("Add to appear in search" when missing) | `aboutValid`, `whereValid`, `photos`, `workValid` | missing rows styled as missing | none |
| 3 | Child's mobile number | Required, at least 10 digits; used to hand the profile over | `childPhone` | invalid disables the button | none |
| 4 | Relation chips (`RelationChips`) | Pick your relation to them (parent role for son/daughter, sibling role for sibling) | `relation` | required | none |
| 5 | Maker check row | Looks up `getVerification()`: dot filled and "Done. Thank you." when verified; else hint | `verified` | loading: neutral; not verified: button label becomes "Start the one-minute check" | `/me/verify?next=/profile/create` (SCR-09) |
| 6 | Primary | Publish: `createProfileForChild({ ...base, childPhone, relation })`, then uploads extra photos, attached biodata and facts read from it, clears the draft | `made.accountId` | busy: "Publishing…"; server `alreadyJoined`: notice screen; `verificationRequired`: sets not-verified; network/other: error line | `/me/matchmaker?setup=1&manage=<accountId>` |
| 7 | Not now: keep my draft | Keeps draft, shows the notice screen | none | none | SCR-03i |

Rule: at least one photo to save (DEC-V1-001), child's number (DEC-V1-019), maker's face check before publishing for someone else (DEC-V1-025).

#### SCR-03i Draft kept / already joined notice

```
+--------------------------------------+
|        (family vignette)             |
|  Your draft is kept on this phone    |
|  Nothing is shown to anyone yet. ... |
|  [ Look around meanwhile ]           |
|  Back to my draft                    |
+--------------------------------------+
```

Variant when the number already has an account: "This number is already on ForKhatri" / "{{name}} already has a ForKhatri account. Ask {{name}} to add you to their Home Circle with your mobile number; the invitation will appear here. Your draft stays on this phone." Buttons: Look around meanwhile (`/discover`), Back to my draft (returns to the step). Also shown when someone publishes with no photo.

#### SCR-03j Start from a biodata, and check what was read

```
+--------------------------------------+
| [<]  Start from a biodata            |
|  Start from a biodata                |
|  Choose the biodata PDF, or a photo  |
|  of it.                              |
|  Whose biodata is this?              |
|  [ Choose v ]                        |  (1)
|  [ Choose the biodata ]              |  (2)
|  [ ] Mangalya will read this file to |  (3)
|      fill the form for you. ...      |
|  [ ] Also keep the file with the     |  (4)
|      profile (only you can open it)  |
|  (error line)                        |
|  [ Read the biodata ]                |  (5)
|   Attach and type myself  (link)     |  (6)
+--------------------------------------+
```

| # | Element | What it does | Data | States | Next |
|---|---|---|---|---|---|
| 1 | Whose dropdown | Sets `forWhom` (Myself omitted when `for=child`) | `forWhom` | required | none |
| 2 | File chooser | PDF, JPEG, PNG or WebP; button text becomes "Chosen: {{name}}" | `biodata` | none | none |
| 3 | Consent checkbox | Required to read; shown only when the reader is available (`biodataReaderAvailable()`); otherwise the line "Reading a biodata automatically is not available yet. Keep it open beside you and type the details on the next screens." | `consent` | reader off: text, and "Attach and type myself" becomes the primary button | none |
| 4 | Attach checkbox | Keeps the file with the profile (private) | `attachBiodata` | none | none |
| 5 | Read the biodata | `readBiodata(file)` then shows what was read | `BiodataFields` (name, date_of_birth, gender, city, education_level, education_other, occupation, marital_status, birth_time, rashi, nakshatra, gotra, native_place, height_cm) | disabled until file, whose, consent; busy "Reading…"; error shows server message | SCR-03k |
| 6 | Attach and type myself | Keeps the file, goes to About with nothing filled | none | disabled until file and whose | SCR-03c |

Check screen (`biodataCheck`):

```
+--------------------------------------+
| [<]  Start from a biodata            |
|  We read this from the biodata       |
|  Check each line. You can change     |
|  anything on the next screens. ...   |
|  Name           Kavya Rao            |
|  Born           1998-04-12           |
|  Time of birth  Not found, add later |
|  Lives in       Hyderabad            |
|  Native place / Studies / Work /     |
|  Marital status / Height / Rashi /   |
|  Star (nakshatra) / Gotra            |
|  [ Looks right, continue ]           |
+--------------------------------------+
```

If nothing was read: "We could not read details from this file. Please type them on the next screens." Button "Looks right, continue" applies the fields to the form (gender only for self, sibling, relative), stores horoscope and community extras to be written after publish, and goes to SCR-03c.

#### SCR-03k Short matchmaker after publish

Publishing sends the member to `/me/matchmaker?setup=1` (candidate) or `?setup=1&manage=<accountId>` (parent managing a child). See SCR-08.

Flow errors summary: age under 18/21 (inline), no photo (draft kept notice), already-joined number, `verification_required` (button turns into "Start the one-minute check"), network ("We couldn't reach Mangalya. Check your connection and try again.").

---

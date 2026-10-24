# Marathi and Kannada: what a native speaker should read first

All Marathi (mr) and Kannada (kn) text was written on 2026-10-06. Every English string now
has a Marathi and a Kannada value; nothing falls back to English. Before members see it, a
native Marathi speaker and a native Kannada speaker should read the strings below. They carry
matrimony, women-only, safety, money, consent or legal meaning, or the writer was unsure of the
term. Keys are given as `namespace` → `key` (web locale files unless marked API).

Where to find the text:
- Web: `modules/<module>/<app>-web/locales/{mr,kn}/<namespace>.json`
- API: `modules/<module>/<app>-service/app/i18n/locales/{mr,kn}/`
- Hub: the `mr` and `kn` blocks in `platform/forkhatri-web/lib/i18n.ts`, `admin-i18n.ts` and
  `insights-i18n.ts`

## Decisions for the owner

1. **Marriage agents in Mangalya.** Marathi says **मध्यस्थ / विवाह मध्यस्थ**, and a bureau is
   **वधू-वर सूचक मंडळ**, the way Maharashtra speaks. Kannada follows Hindi and Telugu:
   **ವಿವಾಹ ಏಜೆಂಟ್**, avoiding ದಲ್ಲಾಳಿ, which can sound disrespectful. Please confirm both.
2. **Does the AI understand Marathi/Kannada input?** Vyapar's hint "write in Hindi, Telugu or
   English" (`hiring.composer.describeHint`, `voice.entry.postBody`) was given Marathi and
   Kannada inconsistently: some files add the reader's own language, others keep the original
   list. Decide whether the drafting and voice helpers accept mr/kn, then make the hint match.
3. **The Mangalya Me screen language picker** uses a 3-column control, so five languages now
   wrap onto two rows. The owner's rule for 4+ options suggests a dropdown. Not changed, to keep
   the work additive.
4. **Examples were localised.** Marathi Vyapar changed "Bar Council of Gujarat" to "Bar Council
   of Maharashtra and Goa", and the Marathi Mangalya "about me" example changed Hyderabad / Tank
   Bund to पुणे. Kannada uses "PUC" for 12th class. Some Kannada Vyapar examples still name
   Telangana and Osmania University. Milavn's `belong.tsafe` (Telangana police T-Safe, dial
   100 then 8) is translated as it stands, but it is Telangana-only advice.
5. **Product name in the hub insights page.** mr/kn write मंगल्य / ಮಂಗಳ್ಯ (core terms), while
   Hindi/Telugu keep "Mangalya" in Latin there. The Mangalya guides (database) use Latin
   "Mangalya" and "Home Circle" inside Kannada sentences. Pick one form.

## Terms used unevenly (please settle on one form, then a quick replace)

| Where | Variants found | Suggested |
|---|---|---|
| Vyapar mr: ask for a price | दर सांगा / दर विचारा (hiring, explore, contracts, commercial, opportunities, enquiries) vs रेट विचारा (glossary + other files) | the glossary form |
| Vyapar kn API | ಕೆಲಸ (job), ಅರ್ಜಿ ಹಾಕಿ (apply), ರೇಟ್ ತಿಳಿಸಿ | glossary ಉದ್ಯೋಗ / ಅರ್ಜಿ ಸಲ್ಲಿಸಿ / ರೇಟ್ ಕೇಳಿ |
| Vyapar kn `contact` | ಕರೆ for "call" | glossary ಕಾಲ್ |
| Vyapar mr "register" button | मला रस आहे (web) vs मला सहभागी व्हायचे आहे (API) | one of them |
| Mangalya mr "pelli choopulu" | पाहण्याचा कार्यक्रम (UI) vs बघण्याचा कार्यक्रम (guides) | one of them |
| Vyapar "Verified" | व्हेरिफाइड / ವೆರಿಫೈಡ್ (Vyapar glossary) vs पडताळलेले / ಪರಿಶೀಲಿಸಲಾಗಿದೆ (other modules) | intentional per module glossary; confirm |
| Language names inside sentences | translated into the UI language (इंग्रजी, ಇಂಗ್ಲಿಷ್), following Hindi/Telugu; picker labels stay in each language's own script | confirm |

## Hub (entrance, admin console, insights)

- Roles: `role_owner` मालक / ಮಾಲೀಕರು (Hindi स्वामी); `role_grievance_officer` तक्रार निवारण
  अधिकारी / ಕುಂದುಕೊರತೆ ಅಧಿಕಾರಿ; `role_data_protection_officer` डेटा संरक्षण अधिकारी / ದತ್ತಾಂಶ
  ಸಂರಕ್ಷಣಾ ಅಧಿಕಾರಿ.
- Governance: `banHelp` (a permanent ban needs a second approver); `err_approval_four_eyes`
  (the two-person rule); `membersSub`, `contactNote` (every look at contact details is
  recorded).
- Status words: `status_banned` / `kind_ban` बंदी घातलेले / ನಿಷೇಧಿತ; suspended निलंबित / ಅಮಾನತು.
- Report reasons: `reason_impersonation`, `reason_underage`.
- Actions: `qa_escalate` वरिष्ठांकडे पाठवा / ಮೇಲಧಿಕಾರಿಗೆ ಕಳುಹಿಸಿ; `qa_warn` ताकीद द्या / ಎಚ್ಚರಿಕೆ
  ನೀಡಿ.
- Marital status: `awaiting_divorce`, `widowed` (विधवा/विधुर, ವಿಧವೆ/ವಿಧುರ).
- Unsure: `navQueues` रांगा / ಸರತಿಗಳು (ಸರತಿ may feel bookish).
- Module taglines (identity service registry): mr "कुटुंबाच्या साथीने, विश्वासार्ह विवाह
  प्रवास."; kn "ನಂಬಿಕೆಯ ವಿವಾಹ ಪಯಣ", "ನಂಬಿಕಸ್ಥ ವ್ಯಾಪಾರಗಳು", "ನೇರವಾಗಿ ಭೇಟಿಯಾಗಿ".
- Sign-in code email lines: mr "तो {minutes} मिनिटांत संपेल."; kn "ಮುಕ್ತಾಯವಾಗುತ್ತದೆ".
- Short chip labels: म / ಕ.
- Search keywords: kn ಸಾಲ (loan) may match unrelated words. Several Devanagari keywords (लग्न,
  विवाह, शनिवार…) are shared with Hindi; this is harmless but deliberate.

## Mangalya (matrimony)

**Consent and family**
- agents `add.consent`, `offline.consent`: family permission to share biodata.
- verify `intro.consent`: photo/face-check consent. mr uses मी संमती देतो/देते.
- common `requestPrompt.noteFamily` / `noteSelf`: "whoever answers first answers for the family".
- profile `view.share.confirm.family_contact`, `managed.disownConfirm`.

**Safety**
- agents `safety.report.*`, `status.warned`, `error.contactSuspended`.
- profile `safety.reportNote`, `blockConfirm`.
- messages `reason.*`: mr छळवणूक, अल्पवयीन; kn ಕಾನೂನುಬದ್ಧ ವಯಸ್ಸಿಗಿಂತ ಕಡಿಮೆ.
- messages `thread.sessionNote`: deletion and screenshot warning.
- agents `add.error.too_young`: below the legal marriage age.

**Money**
- agents `join.form.promise`, `family.connect.point4`: Mangalya never takes a share or collects fees.
- billing `checkout.*`, `familyNote`, `plan.ASSISTED.name` (mr सहाय्यासह).

**Horoscope**
- profile `option.manglik.*`: mr मंगळ आहे / नाही / सौम्य मंगळ (unsure whether सौम्य fits "partial"); kn ಕುಜ ದೋಷ ಇದೆ / ಇಲ್ಲ / ಭಾಗಶಃ.
- Porutham: kn ಪೊರುತ್ತಂ; Karnataka families may say ಕೂಟ.
- horoscope `class.*`, `porutham.name.*`: classical terms. Planets in mr: रवी/गुरू/शनी.
- Ascendant: mr लग्नराशी.
- Nakshatras: mr शततारका, मृग.

**Kinship**
- circle `relation.*`, home_circle (API): mr वहिनी/नणंद, मेहुणा, चुलत/मावस भावंड; kn ಭಾವ/ಮೈದುನ, ಅತ್ತಿಗೆ/ನಾದಿನಿ, ಸೋದರಮಾವ, ಸೋದರತ್ತೆ. English does not say which side of the family.
- kn `relationshipOption.guardian` ಪೋಷಕರು can also read as "parents".

**Community**
- Sub-community: mr पोटजात; kn ಉಪಜಾತಿ (Hindi uses the softer उप-समुदाय).
- Nuclear family: mr विभक्त कुटुंब.
- Surname: kn ಮನೆತನದ ಹೆಸರು.

**Wedding stages**
- `stageHint.first_meeting`: mr पाहण्याचा कार्यक्रम; kn ಹೆಣ್ಣು ನೋಡುವ ಶಾಸ್ತ್ರ.
- Families agreed: mr सोयरीक पक्की; kn ಕುಟುಂಬಗಳ ಒಪ್ಪಿಗೆ.
- Wedding arrangements: mr लग्नाची तयारी; kn ಮದುವೆ ಸಿದ್ಧತೆಗಳು.
- Halls: mr मंगल कार्यालये.

**Grammar with inserted names**
- Gendered forms are written with both endings (करतो/करते, ಎಂಥವನು/ಳು).
- discovery `shelf.reason.suggestedBy`, `because.title`, and API `notifications.rm_suggestion_decided` read unevenly when the inserted word is a phrase.

**Guides** (database migration 066, 11 guides)
- They quote UI labels (शोधा, मी, ನಾನು, ಹುಡುಕಿ), which must match the real buttons.

## Milavn (circles, events, women-only groups)

**Women-only groups**
- `group.womenOnlyHint`: the approval condition must stay intact.
- `group.askBody`, `circle.womenOnly.askFirst`: the answer stays private.
- `safety.reasons.women_only_misuse`, `admin.reason.women_only_misuse`: kn is an approximation.
- `admin.reason.harassment`: mr छळ.

**Consent**
- `moments.okChildren`: parental consent for children's photos.

**Money**
- `pay.organizerNote`, `pay.mine.note`: nobody sees who paid.
- `pay.withdrawNoRefund`, `pay.refundUntil`, `payments.useWithdraw`: refund is परतावा.
- `drive.*`, `circle.fundraiserClosed`: mr मदत मोहिमा (Hindi सहयोग); kn ವಾಗ್ದಾನ, ನಿಧಿ ಸಂಗ್ರಹ.

**Privacy**
- `notify.circleJoinAsk.body`: the person is not told who decided.

**Other terms**
- `trust.community_verified`: mr समाजाने पडताळलेले.
- `admin.fact.reputation`: kn ಹೆಸರು-ಗೌರವ (unsure).
- Short time forms in `create.quickWhen.*` (e.g. संध्या. 7 वा.).
- `detail.going`: mr मी येणार; kn ಹೋಗುತ್ತೇನೆ. `payments.notPaid` quotes this word, so the two must stay identical.

**Search words in nl.py**
- mr आत्ताच, काल, भेटीगाठी, भटकंती, संगीत मैफल, जण.
- kn ಈಗಷ್ಟೇ, ಇವತ್ತು, ಸಂಗೀತ ಕಛೇರಿ, ಚರ್ಚಾಗೋಷ್ಠಿ.

## Vyapar (jobs, services, money held in advance)

**No-fee and scam rules**
- `hiring.errors.seeker_charge_not_allowed`, `hiring.composer.freeNote`, `opportunities.new.guide3`.
- API `trust_safety.scamShield.rule.*`, `seekerProtection.*`: mr खरे मालक; kn ಶುಲ್ಕ, ಠೇವಣಿ, ಕಿಟ್ ಚಾರ್ಜ್.
- trustSafety `reason.asked_for_money`, `scam`.
- `partnerships.detail.safety`, `enquiries.detail.safetyNotice`, `compose.privacyLine`: "never pay in advance".

**Money and contracts**
- `commercial.disclosure.refundText`, `checkout.note`, `checkout.safety`.
- `workspace.cancelTerms`, `renewalTerms`.
- `contracts.new.how4`: approved automatically after 14 days.
- `contracts.dispute.*`: kn ಇತ್ಯರ್ಥವಾಗಿದೆ.
- API `contracts.label.paymentNotice.live`, `notifications.milestoneFunded`, `contracts.error.notCompletable`, `heldFundsClientOnly`.

**Legal and verification**
- `verification.whatThisDoesntMean`.
- `typeShopsEst`: mr शॉप ॲक्ट (दुकाने व आस्थापना) परवाना.
- API `listings.profession.note.*` (Bar Council, Council of Architecture, ICAI). Least sure: kn ಆಡಿಟ್ ಅಲ್ಲದ (ನಾನ್-ಅಶ್ಯೂರೆನ್ಸ್).
- `commercial.ineligible.notPermittedForProfession`.

**Privacy and consent**
- `privacy.dataRights.deleteWarning`: anonymise is mr निनावी, kn ಅನಾಮಧೇಯ.
- `behavioralAnalyticsHelp`, `personalisedHelp`.
- `hiring.accept.title.*`.
- `paidOnTime.*` and API `notifications.paidOnTimeAsk.body`.

**Reports and appeals**
- trustSafety `report.*`: mr तक्रार; the admin metric might read better as रिपोर्ट.
- `reason.impersonation`: mr तोतयागिरी; kn ಬೇರೆಯವರಂತೆ ನಟಿಸುತ್ತಿದ್ದಾರೆ.
- `outcomes.process`: 15-day appeal, kn ಮೇಲ್ಮನವಿ.
- API `notifications.moderationOutcome`, `appealDecided`: kn ದೂರುಗಳು, ಅಪೀಲ್.
- `reviews.disputeReason.*`.

**Unsure wording**
- `ranking.value_fit`: mr चांगला मोबदला, ambiguous for non-job posts.
- API `reputation.badge.rising.label`: mr उदयोन्मुख may feel too formal.
- API `voice.q.profile.own_assets`: mr अवजारे.
- Activity: mr ॲक्टिव्हिटी.
- `common.nav.discover`: kn ಅನ್ವೇಷಣೆ.
- Impressions: kn ಕಾಣಿಸಿಕೊಂಡ ಬಾರಿ.
- `explore.menu.hire`: kn ಕೆಲಸ ಕೊಡಿ.
- `hiring.board.hire`: mr कामावर घ्या.
- `adminCommercial.diagnostics.*`: operator wording, only lightly reviewed.

**Legal documents in the database** (migration 031, `vyapar_privacy.legal_documents`)
- The Marathi and Kannada **privacy notice** and **terms of use** (version 1) were written
  from the English text. These are legal documents: a native speaker, and ideally the person
  who owns the English text, should read them in full before members accept them.

**Trade and skill names** (migration 031, `vyapar_listings.taxonomy_terms`, 85 terms)
- Every trade, skill and locality term has a Marathi and a Kannada name plus spoken aliases
  used by search and voice. Read the list once for trade words people really use (for example
  plumber, electrician, tailor, cook, driver, housekeeping, pooja samagri supply).
- `GLOSSARY.md` holds the canonical mr/kn term for every Vyapar concept; the review should
  start there.

**Voice answer words** (`vyapar-service/app/integrations/ai/spoken.py`)
- Yes/no/skip/repeat words and number words in Marathi and Kannada, with romanised forms.
  Marathi हो is deliberately not accepted as a leading "yes" because Hindi "हो गया" starts
  the same way.

## Counsel (paid one-to-one advice)

**Consent before paying**
- `book.agree`.
- `room.consent_required`, `room.consent*`, `rec_banner`, `book.recording_optional`: recording only when both people agree.

**Refunds**
- `policy.tier`, `policy.no_show`, `booking.cancel_refund`, `cancel_now_none`.
- `offers.ask_body`, `offers.rule_refund`, `refunded_unanswered`.
- `book.proposed_body`, `requests.waiting_hint`: kn ಹಣ ಕಡಿತವಾಗುವುದಿಲ್ಲ.

**Disclaimers**
- `disclaimer.legal`, `finance`, `investment`, `health`: mr स्वतंत्रपणे काम सोपवले नसल्यास; kn ವಕೀಲರು, ನ್ಯಾಯಾಲಯದಲ್ಲಿ ದಾಖಲಾತಿ, ಔಷಧ ಚೀಟಿ.

**Privacy**
- `privacy.keeps`, `privacy.removes`: what the law requires to be kept.

**Reports and disputes**
- `report.reason.abuse`: mr गैरवर्तन किंवा छळ; kn ನಿಂದನೆ ಅಥವಾ ಕಿರುಕುಳ.
- `booking.dispute_body`: kn ತಕರಾರು or ವಿವಾದ, please confirm.

**Standing levels**
- mr `standing.distinguished` विशेष प्रतिष್ठित (unsure).
- kn ನೆಲೆಗೊಂಡವರು, ಹಿರಿಯರು, ವಿಶಿಷ್ಟರು ("senior" here is not about age).

**Admin and code-filled text**
- `admin.policy_hint`, `fee_hint`: "snapshot" was paraphrased.
- `notif.booking.cancelled`: `{{by}}` is filled in by code and may insert an English word.

**Expertise areas and cities** (migration 011)
- mr: कायदेशीर, कुशल कारागिरी, इतर विशेष तज्ज्ञता, पोषण आणि आहार.
- kn: ವೃತ್ತಿಜೀವನ ಮತ್ತು ಉದ್ಯೋಗ, ಕುಶಲ ವೃತ್ತಿಗಳು, ಪೌಷ್ಟಿಕ ಆಹಾರ, ಸಮುದಾಯ ಮತ್ತು ಸಮಾಜ ಸೇವೆ.
- City: mr नुझिवीडू (Nuzvid).

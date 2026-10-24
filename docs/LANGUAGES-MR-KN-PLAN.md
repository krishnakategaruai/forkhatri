# Adding Marathi (mr) and Kannada (kn) to ForKhatri

Owner request, 2026-10-06. ForKhatri today speaks English, Hindi and Telugu. This adds
Marathi (मराठी, Devanagari script) and Kannada (ಕನ್ನಡ, Kannada script) everywhere a member
can read or hear the app: the ForKhatri entrance (hub), the identity service, and the
Vyapar, Milavn, Mangalya and Counsel web apps and APIs.

## Protect the base (owner rule, 2026-10-06)

The current app is the base and must not regress. Every change here is purely additive:
- No existing English, Hindi or Telugu string, keyword or content is changed or removed.
- Database changes only widen the allowed values (`IN ('en','hi','te')` becomes
  `IN ('en','hi','te','mr','kn')`). Nothing is dropped or renamed, and no existing member's
  language is touched.
- After the work, English and Telugu are checked again on each module's main screens, and each
  module's existing tests are run.
- A safety copy of the pre-change working tree is on git branch `checkpoint/2026-10-06-base`.

## How the work is split

| Part | Who | What |
|---|---|---|
| Hub + identity service | platform agent | language lists, DB check, validators, hub dictionaries (i18n, admin, insights), intent keywords, fonts, module registry text |
| Vyapar (MOD01) | Vyapar agent + translators | code, DB, fonts, voice, AI prompts; web 25 namespaces, API 23 namespaces |
| Milavn (MOD02) | Milavn agent + translators | code, DB, fonts, NL keywords; web 1 + API 1 namespace |
| Mangalya (MOD03) | Mangalya agent + translators | code, DB (guides content etc.), fonts, horoscope text; web 16 + API 12 namespaces |
| Counsel (MOD04) | Counsel agent + translators | code, city names, fonts; web 1 namespace, API strings |
| Lead | coordinator | this plan, the key checker (`scripts/check_locale_parity.py`), cross-module check, review list |

Translators only write `locales/mr/*.json` and `locales/kn/*.json`. Module agents own code,
database and any new keys (added to en/hi/te and handed to the lead for mr/kn).

## Size of the translation

About 8,970 English strings (≈243,000 characters) across the module locale files, plus the
hub dictionaries (≈1,000 strings in three TypeScript files) and any multilingual content
stored in the database (Mangalya guides, Vyapar taxonomy, Counsel city names, module
registry names). Each string gets a real Marathi and Kannada value; nothing falls back to
English.

## Core terms (every module uses these)

Register: Marathi uses the polite **तुम्ही** with **-ा** imperatives (करा, पाहा, निवडा);
elders addressed with **आपण** only where Hindi uses formal honorifics. Standard Marathi, not
Hindi written in Devanagari (आहे / नाही / करा, not है / नहीं / करें). Kannada uses **ನೀವು**
with polite imperatives (ಮಾಡಿ, ನೋಡಿ, ಆಯ್ಕೆಮಾಡಿ) and standard Kannada script.

| English | Hindi (existing) | Marathi | Kannada |
|---|---|---|---|
| ForKhatri | ForKhatri | ForKhatri | ForKhatri |
| Mangalya | मंगल्य | मंगल्य | ಮಂಗಳ್ಯ |
| Vyapar | व्यापार | व्यापार | ವ್ಯಾಪಾರ್ |
| Milavn | Milavn | Milavn | Milavn |
| Counsel | Counsel | Counsel | Counsel |
| Home Circle | होम सर्कल | होम सर्कल | ಹೋಮ್ ಸರ್ಕಲ್ |
| Circle | सर्कल | सर्कल | ಸರ್ಕಲ್ |
| member | सदस्य | सदस्य | ಸದಸ್ಯರು / ಸದಸ್ಯ |
| samaj / community | समाज | समाज | ಸಮಾಜ |
| bride / groom | वधू / वर | वधू / वर | ವಧು / ವರ |
| horoscope | कुंडली | पत्रिका (कुंडली where Hindi stresses chart) | ಜಾತಕ |
| profile | प्रोफ़ाइल | प्रोफाइल | ಪ್ರೊಫೈಲ್ |
| sign in / sign out | साइन इन / साइन आउट | साइन इन / साइन आउट | ಸೈನ್ ಇನ್ / ಸೈನ್ ಔಟ್ |
| save / cancel | सेव करें / रद्द करें | सेव्ह करा / रद्द करा | ಉಳಿಸಿ / ರದ್ದುಮಾಡಿ |
| try again | फिर से कोशिश करें | पुन्हा प्रयत्न करा | ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ |
| search | खोजें | शोधा | ಹುಡುಕಿ |
| messages | संदेश | संदेश | ಸಂದೇಶಗಳು |
| notifications / alerts | सूचनाएँ | सूचना | ಅಧಿಸೂಚನೆಗಳು |
| verified | सत्यापित | पडताळलेले | ಪರಿಶೀಲಿಸಲಾಗಿದೆ |
| report (a person) | रिपोर्ट करें | तक्रार करा | ದೂರು ನೀಡಿ |
| block | ब्लॉक करें | ब्लॉक करा | ಬ್ಲಾಕ್ ಮಾಡಿ |
| women only | सिर्फ़ महिलाएँ | फक्त महिलांसाठी | ಮಹಿಳೆಯರಿಗೆ ಮಾತ್ರ |
| job / salary | नौकरी / वेतन | नोकरी / पगार | ಕೆಲಸ / ಸಂಬಳ |
| ₹15,000 a month | ₹15,000 महीना | ₹15,000 दरमहा | ತಿಂಗಳಿಗೆ ₹15,000 |
| language | भाषा | भाषा | ಭಾಷೆ |
| language picker labels | — | मराठी | ಕನ್ನಡ |

Module agreed terms (Vyapar `GLOSSARY.md`, Mangalya kinship words, Milavn circles vs
messages) follow the meaning of the existing Hindi and Telugu, not word-for-word English.

## What changed where (done 2026-10-06/07)

**Shared**
- `scripts/check_locale_parity.py` (new): compares every language with English per namespace,
  web and server; reports missing/extra keys, placeholder mismatches, untranslated values and
  wrong-script values. Run from the repo root: `python scripts/check_locale_parity.py mr kn`.

**Platform**
- identity-service: `LANGUAGES` in `app/config/settings.py` (used by Accept-Language parsing,
  admin language, registry); pydantic Literals in `auth.py`, `members.py`, `internal.py`;
  `import_module_identities.py`; registry taglines in mr/kn (`COALESCE` fallback to English);
  sign-in code email gains Marathi and Kannada lines (SMS stays English, DLT template).
- forkhatri-web: `Lang` type, `LANG_CODES`, `isLang`, `INTL_LOCALE` in `lib/api.ts`;
  `lib/storage.ts`; picker (`LANGUAGES` with मराठी / ಕನ್ನಡ and short chips म / ಕ) and
  `mr`/`kn` dictionaries in `lib/i18n.ts`, `lib/admin-i18n.ts`, `lib/insights-i18n.ts`;
  Marathi/Kannada words in `lib/intent.ts`; Noto Sans Kannada in `app/layout.tsx`; `:lang`
  rules in `hub.css`, `arrival.css`, `splash.css`, `admin.css`; five chips fit at 390px
  (`arrival.css`); `DevActAs.tsx`, `MemberDetail.tsx`, `e2e-smoke.mjs`.

**Vyapar (MOD01)**
- `GLOSSARY.md` gains Marathi and Kannada columns for every term.
- vyapar-web: `lib/i18n/config.ts`, `languages.ts`, `LanguageSwitcher`, `format.ts`,
  `money.ts`, voice (`speech.ts`, `useInterview.ts`, `VoiceInterview.tsx`, `VoiceInput.tsx`:
  `mr-IN` / `kn-IN`), Anek Kannada font in `layout.tsx`, Indic rules in the 2026 CSS files,
  `scripts/check-i18n-keys.py` covers mr/kn. 25 web namespaces and 23 API namespaces in
  `locales/mr` and `locales/kn`.
- vyapar-service: `app/i18n/__init__.py`, `spoken.py` (yes/no/skip/repeat words and number
  words in Marathi and Kannada), `vocab.py`, `localities.py`, `rules_provider.py`,
  `anthropic_provider.py`, `voice_interview.py`, `notifications.py`, `taxonomy_cache.py`,
  `packages.py` (name_mr/name_kn/description_mr/description_kn), `profile.py`,
  `member_settings.py`, `first_run.py`, `admin_ops.py`, `vyapar-mcp/server.py`.

**Milavn (MOD02)**
- milavn-web: `lib/i18n/config.ts` and `provider.tsx` (mr/kn load on first use, English
  fallback), `lib/format.ts` (`mr-IN-u-nu-latn`, `kn-IN`), Intl locale in date pickers,
  programme, chats, circles and tickets; `AskBar.tsx` speech `mr-IN` / `kn-IN`; Anek Kannada
  font. `locales/{mr,kn}/common.json`.
- milavn-service: `app/i18n/__init__.py`, `components/profile/interface.py`,
  `components/discovery/nl.py` (Marathi and Kannada search words). `app/i18n/locales/{mr,kn}`.

**Mangalya (MOD03)**
- mangaly-web: `lib/i18n/config.ts` and `languages.ts` (lazy mr/kn with English fallback),
  `lib/rm.ts`, `lib/verification.ts` (dates), `VoiceInput.tsx`, `MessageText.tsx`, Noto Serif
  Kannada and Noto Sans Kannada in `layout.tsx`, Indic rules in `editorial.css`, `wedding.css`,
  `home.css`, `me.css`, `royal.css`, `sindoor.css`; `guides/content.json`. 16 web and 12 API
  namespaces in mr/kn. New keys `common:language.mr/kn`, `rm:language.mr/kn`.
- mangaly-service: `app/i18n/__init__.py`, `compatibility/understand.py` (keywords and prompt),
  `scripts/import_osm_places.py` (`name:mr`, `name:kn`). horoscope-service returns codes only.

**Counsel (MOD04)**
- counsel-web: `lib/i18n/config.ts` (`SUPPORTED_LANGUAGES`), `format.ts`, discover language
  filter and professional languages from the shared list, admin expertise names in mr/kn,
  Anek Kannada in `layout.tsx` and `globals.css`. `locales/{mr,kn}/common.json`. New keys
  `lang.mr`, `lang.kn`.
- counsel-service: `app/i18n.py`, `places.py` (45 cities in mr/kn), `ai.py` keywords,
  `providers.py` / `discovery.py` / `provide.py` / `admin.py` (name_mr, name_kn).

## Database migrations (all applied locally, all additive)

| Module | Migration | What it does |
|---|---|---|
| identity | `platform/identity-service/db/migrations/007-marathi-kannada.sql` | widens `members.preferred_language` check to en/hi/te/mr/kn; registry taglines in mr/kn |
| Vyapar | `modules/MOD01-vyapar/07a-db-implementation/migrations/031-marathi-kannada.sql` | widens all nine language checks; adds `name_mr/name_kn/description_mr/description_kn` to `taxonomy_terms` and `listing_packages`; fills taxonomy names and aliases; inserts Marathi and Kannada privacy notice and terms of use (v1) |
| Milavn | none | `language_preference` is free text with no check |
| Mangalya | `modules/MOD03-mangalya/07a-db-implementation/migrations/066-guides-marathi-kannada.sql` | adds mr/kn content to all 11 guides |
| Counsel | `modules/MOD04-counsel/counsel-service/db/migrations/011-marathi-kannada.sql` | adds nullable `name_mr/name_kn` to expertise areas and fills 26 of 26 |

Existing member language counts were unchanged after each migration (identity en 105, hi 13,
te 18; Milavn en 16, hi 10, te 7).

## Risks

- **Volume.** Close to 20,000 new strings. Machine-literal text would break the owner's
  respectful-language rule, so every string is written as a family member would say it, and
  `LANGUAGES-MR-KN-REVIEW.md` lists what a native speaker should read first.
- **Shared locale files.** Other sessions edit en/hi/te at the same time. The key checker is
  run at the end and any English key added meanwhile is translated before finishing.
- **Check constraints.** Every `IN ('en','hi','te')` constraint must be widened by a new
  migration, or saving Marathi/Kannada as a preference fails at the database.
- **Fonts and layout.** Kannada glyphs are taller and wider than Telugu; Kannada and
  Devanagari need their own Noto font, normal letter-spacing, no uppercase transforms and
  enough line-height. Long Marathi/Kannada words may overflow chips and buttons at 390px.
- **Speech.** Browser speech recognition/synthesis must get `mr-IN` / `kn-IN`; where a browser
  has no Kannada voice, the guided conversation must still show the question as text.
- **Number and date formatting.** `Intl` with `mr-IN` / `kn-IN` gives native month names;
  digits stay Latin (as Hindi/Telugu do today).

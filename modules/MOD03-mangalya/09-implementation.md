# 09 - Implementation (as built) - MOD03 Mangalya

**Document status:** 2026-11-22, as-built scope. This is the module-root implementation record. The older pipeline file `AgentOutputs/09-implementation.md` (2026-09-14, 26 TRs) is kept as history. Sources: code, migrations, `git log`, `v1-decisions.md`, `ONBOARDING-REDESIGN-2026-10.md`, owner decisions in memory.

## 1. Folder structure
```
modules/MOD03-mangalya/            (renamed from MOD03-mangaly on 2026-09-29; inner folders keep the old spelling)
  01..08 *.md, 07a-er-model.md, 07a-data-model-appendix.md, 09-implementation.md
  architecture.md, CODING-GUIDE.md, v1-decisions.md, reference.md, BACKLOG.md, ONBOARDING-REDESIGN-2026-10.md
  RUNBOOK.md, TRACEABILITY.md, API-REFERENCE.md, GLOSSARY.md, COVERAGE-REPORT.md
  AgentOutputs/  (pipeline copies, CANDIDATE-UX-LEARNING-2026-10.md, critique logs, onboarding-mockups)
  research/      (wedding-services-partners.md)
  07a-db-implementation/  migrations 001-066, schema.sql (lags), seeds.sql, init.sh
  mangaly-service/   FastAPI app: app/api/routes (21 route files), app/components (22), app/config, scripts, tests
  mangaly-web/       Next.js: app/ (31 routes), components/ (50+), lib/, locales/{en,hi,te,mr,kn}
  horoscope-service/ Node: src/{api,application,domain,provider}, test/, docs/PROVIDER-LIMITATIONS.md
```

## 2. Key files per feature
| Feature | Backend | Web |
|---|---|---|
| Profile and onboarding | `api/routes/profile.py`, `components/profile/`, `config/profile_schema.py`, `profile_tiers.py` | `app/profile/create`, `lib/draft.ts`, `lib/image.ts`, `components/PhotoChoice.tsx`, `components/form/` |
| Biodata reader | `profile.py` (`/profile/biodata/*`), `/profile/documents` | profile/create |
| Managed accounts | migration 065, `profile.py` (`/profile/managed`, `/profile/claim`, `/profile/disown`) | `ClaimProfileNote.tsx` |
| Home Circle | `api/routes/home_circle.py`, `components/home_circle/` | `app/circle`, `CircleInvite.tsx`, `FamilyNotes.tsx`, `RelationChips.tsx` |
| AI matchmaker | `components/compatibility/` (`understand.py`, `engine.py`), `config/matching_engine.py` | `app/me/matchmaker`, `MatchmakerEntry.tsx`, `lib/matchmaker.ts` |
| Discovery | `components/discovery/`, `config/ranking_weights.py` | `app/discover`, `SwipeDeck.tsx`, `DiscoverFilters.tsx`, `HowYouFit.tsx` |
| Horoscope | `components/horoscope/`, `api/routes/horoscope.py`; service `horoscope-service/src` | `app/horoscope/check`, `HoroscopeMatch.tsx`, `PlaceSearch.tsx` |
| Face match | `components/trust/`, `api/routes/verification.py`, migration 045 | `app/me/verify`, `PhotoCheckCard.tsx`, `lib/faceMatch.ts`, `public/models/face-api/` |
| Messages | `components/communication/`, `api/routes/communication.py` | `app/messages`, `ConversationList.tsx` |
| Agents / brokers | `components/agents/`, `api/routes/agents.py`, migrations 059-061 | `app/agent*`, `app/agents`, `AgentClientTools.tsx`, `OfflineBiodataCard.tsx` |
| RM | `components/assisted_matching/`, `rm.py`, 052 | `app/rm*`, `RmCard.tsx` |
| Plans and billing | `config/plans.py`, `components/billing/`, `billing.py`, 051, 059 | `app/plans`, `UpgradeNudge.tsx`, `AgentPlanCheckout.tsx` |
| Wedding and Guides | `components/wedding/`, `places/`, `guides/`, 062-064, 066 | `app/wedding*`, `app/guides*`, `SharePlaceSheet.tsx` |
| Safety and operations | `components/safety/`, `operations/`, `safety.py`, `operations.py`, `admin.py`, 033, 048 | `ProfileSafety.tsx`, `ContactSafety.tsx` |
| Languages | `app/i18n`, locale JSON | `lib/i18n/`, `locales/` |

## 3. Run, test, migrate
See `RUNBOOK.md`. Tests: `pytest` under `mangaly-service/tests` (7 test files), `npm test` in `horoscope-service` (13 files), `npm run lint` in `mangaly-web`. Migrate: apply `07a-db-implementation/migrations/NNN-*.sql` in order.

## 4. Dev tooling
QA and persona sign-in per root CLAUDE.md (dev_session.py; personas asha, new-member, mangalya-family, mangalya-parent, milavn-moderator). Seeds `scripts/seed_dev_*.py`. Never use the OTP screens or "Sign out on all devices". Test scripts must leave no junk data (owner rule).

## 5. Conventions
`CODING-GUIDE.md`; requirement-level comment blocks citing TR/DEC ids; migrations additive with a header explaining why; SECURITY DEFINER functions for cross-account reads; no hardcoded environment values (owner rule); no user-visible hardcoded strings (i18n); Telugu and Hindi accurate and respectful; no screenshots (ScreenGuard); collapse option fields into dropdowns; mobile-first.

## 6. Change log (dated)
| Date | Change | Why / source |
|---|---|---|
| 2026-09-11 to 09-14 | Pipeline foundations and 26 TRs (auth, profile, circle) | `AgentOutputs/09-implementation.md` |
| 2026-09-21/22 | Face match (045), direct chat (046), member profile (047), maker gate, family chat (044) | DEC-V1-024/025/026/027 |
| 2026-09-25 | Waiting periods 90/21 days, parents see full name after accept, siblings only suggest | BACKLOG owner decisions |
| 2026-09-27 | AI matching engine, 1-10 scales, hidden score | DEC-V1-031 |
| 2026-09-28/29 | Plans and billing (051), RM (052), agents (059, 060), honest GST pricing | DEC-V1-032/033/034; commit 782706b rename to Mangalya, 268846d repo clean-up |
| 2026-09-30 | First-run journey, mutual matching, story, help (98e7323) | owner rules |
| 2026-10-01 | Discover photo wall tuning (8874905, 20ae38b, c3e47df); wedding arrangements, Guides, report from profile (1ea2e86); wedding place cards (865f7d0) | owner direction; migrations 062-064 |
| 2026-10-06 | Critique and onboarding study; DEC-V1-035 decisions D1-D17 | owner answers Q1 yes, Q2 no, Q3 consent line |
| 2026-10-06/07 | Web wizard, drafts, photo choose/take + shrink, biodata reader, who-for fix, education options; migration 065 applied to dev DB | DEC-V1-035 |
| around 2026-10-24 | Marathi and Kannada (5-language picker, migration 066) and "final push" (a8f7747) | docs/LANGUAGES-MR-KN-PLAN.md |
| 2026-11-22 | Documentation brought to as-built | this set |

## 7. What is NOT built (honest list)
- **`POST /profile/managed` change:** `child_phone` is still a required form field (`profile.py` line ~150) and the `is_face_verified` refusal (line ~191) is still active, so the parent still has to give the child's number and pass the maker check at publish. Migration 065 and its functions exist; the two-line API change was refused by the build session's permissions as a security weakening and needs the owner's hand. The same face-check gate exists in `agents.py`.
- Human review screen for failed face checks; email verification (platform); guided voice path for the wizard (D18); refunds, invoices; wedding partner offers (table empty, no partners); learning from clicks; dowry report reason and detector; bias audit of the engine; narrowing public birth time; automated web tests; production backup job; payment vendor (sandbox only); real AI key (placeholders: unverified in this environment).
- `scripts/dev.mjs` points at inner folders named `mangalya-*` that do not exist; `deploy/` still names `MOD03-mangaly`.

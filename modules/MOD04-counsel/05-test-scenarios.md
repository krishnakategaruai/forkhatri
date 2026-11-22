# MOD04 Counsel — 05 Test scenarios

**Document status:** 2026-11-22, "as built". **No automated tests for Counsel exist in the repository** (no test files under `modules/MOD04-counsel`; `shared/forkhatri-integrations/tests` covers the shared payments/messaging/delivery library only). `BACKLOG.md` states the 30 Sep and 1 Oct 2026 builds were "checked on screen" and that calls were tried "between two sessions with stand-in cameras"; no QA-RUN record with scenario-level results exists for Counsel. So every scenario below is **manual only**; the Result column says "not recorded" unless the backlog states a check. Layers: F functional, U UI, A API, S security, E edge.

## Contents
1 How to run · 2 Scenarios · 3 Coverage by FR · 4 Suggested automation first

## 1. How to run
Start the stack (RUNBOOK.md). Get a session for a persona without driving the sign-in screens: `platform/identity-service/.venv/Scripts/python platform/identity-service/scripts/dev_session.py <persona> --storage-state <file>` (or `--cookie-header` for curl). Personas for Counsel data: `asha` (seeker), seeded consultants are members `3333...`, `4444...`, `6666...` etc. (see seeds); admin: `milavn-moderator` (in ADMIN_MEMBER_IDS in dev). Never use "Sign out on all devices". Payment is mock/sandbox so no real money moves.

## 2. Scenarios
| TC | Layer | FR | Scenario | Expected | Auto? | Result |
|---|---|---|---|---|---|---|
| TC-001 | F | FR-001 | Create profile, reload | values persist, status draft | manual | not recorded |
| TC-002 | A | FR-005 | Submit without headline / without expertise | 422 incomplete | manual | not recorded |
| TC-003 | F | FR-006 | Admin approves, requests changes, suspends | status changes, services paused on suspend, notification | manual | backlog: admin flow shown with Vikram Rao pending |
| TC-004 | S | FR-004 | Non-owner GETs another provider's proof | 404 | manual | not recorded |
| TC-005 | F | FR-007 | Grant/revoke each dimension | tag appears/disappears publicly | manual | not recorded |
| TC-006 | F | FR-008 | Publish legal service without registration | 422 verification_required with missing list | manual | not recorded |
| TC-007 | F | FR-012 | Sort Top rated: 1 review 5.0 vs many reviews 4.8 | many-review consultant ranks above (Bayesian) | manual | backlog: built and checked |
| TC-008 | F | FR-012 | Filters: price, language, verified, rating, Available now, free in 24 h | results obey each filter | manual | backlog: checked |
| TC-009 | F | FR-013 | "GST for freelance income from abroad" | area finance, CA first | manual | not recorded |
| TC-010 | E | FR-013 | Empty/very long (>600) text; Telugu text | no 500; truncated to 600 | manual | not recorded |
| TC-011 | E | FR-012 | Search "tax" must not match "syntax" | currently DOES match (known G-08) | manual | known fail |
| TC-012 | F | FR-014 | Choose city, sort Nearest, within 150 km | distances shown, filter applies | manual | backlog: checked |
| TC-013 | F | FR-022 | Slots respect notice, advance, buffer, exceptions | no slot inside constraints | manual | not recorded |
| TC-014 | E | FR-022 | Two seekers book same slot at once | second gets 409 slot_taken | manual | not recorded |
| TC-015 | F | FR-030 | Book and pay (mock) | confirmed, ledger gross/fee/payable, 2 notifications | manual | backlog: checked on screen |
| TC-016 | E | FR-030 | Abandon checkout 15 min | booking expires, slot freed | manual | not recorded |
| TC-017 | E | FR-030 | Book own service; book while blocked | own_service; forbidden | manual | not recorded |
| TC-018 | F | FR-031 | Propose time, accept, pay; decline; withdraw; accept after 24 h | per rules; hold_expired after pay_by | manual | backlog: built earlier |
| TC-019 | F | FR-032 | Cancel at 30 h, 10 h, 2 h before | 100%, 50%, 0% refund | manual | not recorded |
| TC-020 | F | FR-032 | Consultant cancels | 100% refund | manual | not recorded |
| TC-021 | F | FR-034 | No-show before 10 min after start | too_early | manual | not recorded |
| TC-022 | F | FR-034/G-03 | Consultant claims no-show though seeker joined | currently allowed (known gap) | manual | known fail |
| TC-023 | F | FR-033 | Complete; wait 24 h hold; request payout | payout row paid, ledger payout | manual | not recorded |
| TC-024 | E | FR-045 | Payout without method; with nothing eligible | payout_method_required; nothing_to_pay | manual | not recorded |
| TC-025 | F | FR-050 | Follow-up offer visible only after completed consultation; buy; book session; cancel 24 h ahead | per rules; unused refunded at expiry | manual | backlog: checked |
| TC-026 | F | FR-051 | Ask question, unanswered past due | auto full refund | manual | backlog: checked |
| TC-027 | E | FR-051 | Third open question to same consultant | 429 | manual | not recorded |
| TC-028 | F | FR-060 | Join before T-15 min; after end +2 h | room closed | manual | not recorded |
| TC-029 | F | FR-061 | Two browsers call; mute, camera, share, PiP, device switch | works | manual | backlog: checked with stand-in cameras; real-device checks open T8 |
| TC-030 | E | FR-061 | Strict network without TURN | may fail (known G-05) | manual | known risk |
| TC-031 | F | FR-066 | Recording without both consents; with consent in legal area | consent_required; recording_not_allowed | manual | not recorded |
| TC-032 | S | FR-065 | Non-participant downloads file | 403 | manual | not recorded |
| TC-033 | S | FR-065 | Upload .exe renamed as image/png | blocked only for evidence/photo (magic) but consultation files trust the header (known) | manual | known gap |
| TC-034 | F | FR-068 | Complete with notes+actions | recap message and notifications | manual | backlog: checked |
| TC-035 | F | FR-070 | Review twice; review before completion; non-seeker | already_reviewed; not_completed; forbidden | manual | not recorded |
| TC-036 | F | FR-072 | Complete consultations to cross a level | badge row and notification once | manual | not recorded |
| TC-037 | F | FR-080/081 | Reminders at 24 h and 15 min | one notification each, not repeated | manual | not recorded |
| TC-038 | F | FR-091 | Open dispute, admin refunds 50% then 100% | capped to remainder; statuses | manual | not recorded |
| TC-039 | F | FR-100/101 | Export; delete with and without blockers | JSON; deletion_blocked then erased, name "Deleted member" | manual | backlog: done in Counsel |
| TC-040 | S | FR-093 | Non-admin calls any /admin route | 403 forbidden | manual | not recorded |
| TC-041 | S | FR-120 | Call APIs without cookie | 401 unauthenticated | manual | not recorded |
| TC-042 | A | FR-103 | Internal routes with wrong service key | 401 service_unauthorized | manual | not recorded |
| TC-043 | A | FR-042 | `/payments/events` with bad signature | 400 bad_event | manual | not recorded |
| TC-044 | U | FR-110 | Switch to Hindi, Telugu, Marathi, Kannada; open each screen | no raw keys, correct fonts | manual | not recorded; locale key parity verified by count (1029 each) |
| TC-045 | U | FR-111 | Theme Auto/Light/Dark persists | persists in localStorage | manual | not recorded |
| TC-046 | U | SCR-01 | Home at 390 px signed out | matches 03-ux | manual | observed 2026-11-22 |
| TC-047 | F | FR-072 | Admin settings change affects only new bookings | old bookings keep snapshot | manual | not recorded |
| TC-048 | F | FR-040/G-01 | Fee shown to seeker and consultant | currently inclusive 2% (owner definition is additional) | manual | known difference |

## 3. Coverage
Every FR group A-L has at least one TC except FR-002, FR-003, FR-009, FR-016, FR-017, FR-023 (partial via TC-008), FR-037, FR-038, FR-062-064, FR-067, FR-071, FR-073, FR-082, FR-090, FR-092 (no web use), FR-102 (retention), which have no scenario yet.

## 4. Suggested automation first
API tests (pytest + httpx against a throwaway DB) for refund tiers, slot engine, EXCLUDE double booking, ledger totals, purchase expiry, privacy erase blockers, admin gating; then Playwright for book-and-pay using `dev_session.py` storage state.

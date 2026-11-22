# Platform traceability matrix

**Document status:** 2026-11-22, as built. Maps BR to FR to screens, endpoints, tables and tests for the platform (identity service, entrance web, shared integrations, deploy).
Sources: `01-business-requirements.md` (BR-01..BR-24), `02-functional-requirements.md` (index with the full BR-to-FR map), `02a/02b/02c` (FR detail), `03-ux.md` (SCR-01..SCR-24), `05-test-scenarios.md` (TC-01..TC-40), `API-REFERENCE.md` (API ids), `07a-er-model.md` (TBL ids).

## How to use
The authoritative BR to FR map is the table at the top of `02-functional-requirements.md`; it is not duplicated here so it cannot drift. Each FR file lists its own screens, endpoints and tables. Use the lookups below to go from an artefact back to its requirement.

## Artefact to document lookup

| Artefact | Where it is defined | Where requirements reference it |
|---|---|---|
| BR-01..BR-24 | 01-business-requirements.md | 02 index map |
| FR01-FR18, FR-019..FR-060 | 02-functional-requirements.md and 02a, 02b, 02c | each FR block |
| SCR-01..SCR-24 | 03-ux.md addendum | 04-ui.md, 05-test-scenarios.md |
| API-<METHOD>-<slug> (43 endpoints) | API-REFERENCE.md | 02a-02c |
| TBL-<schema>.<table> (12 tables) | 07a-er-model.md | 02a-02c, 08 |
| TC-01..TC-40 | 05-test-scenarios.md | each TC names its FR |
| Known gaps SEC-01..SEC-19 | 08-security-performance.md | 01 risks |

## Automated test files per area

| Area | Test file |
|---|---|
| Identifier handling | platform/identity-service/tests/test_identifiers.py |
| Secrets and digests | platform/identity-service/tests/test_secrets.py |
| OTP delivery | platform/identity-service/tests/test_delivery.py |
| Origin guard (return_to, CSRF) | platform/identity-service/tests/test_origin_guard.py |
| Dev tools | platform/identity-service/tests/test_dev_tools.py |
| Live API contract | platform/identity-service/tests/integration/test_contract_live.py |
| Governance with database | platform/identity-service/tests/integration/test_governance_db.py |
| Integrations library | shared/forkhatri-integrations/tests/test_integrations.py, test_places.py |
| Web end to end smoke | platform/forkhatri-web/scripts/e2e-smoke.mjs |
| Language parity | scripts/check_locale_parity.py |

Pass or fail results were not re-run for this documentation pass (unverified).

## Module traceability
Each module keeps its own matrix: MOD01 `modules/MOD01-vyapar/TRACEABILITY.md`, MOD03 `modules/MOD03-mangalya/TRACEABILITY.md`. MOD02 and MOD04: see their `02`/`API-REFERENCE.md` files (no separate matrix at time of writing).

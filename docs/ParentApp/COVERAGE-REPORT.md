# Platform documentation coverage report

**Date:** 2026-11-22. Method: OpenAPI fetched from the running identity service and checked by script against `API-REFERENCE.md`; migrations and tables checked against `07a-er-model.md`; screens, tests and ids counted by grep.

| Item | Inventoried | Documented | Notes |
|---|---|---|---|
| Public API operations (openapi.json) | 39 | 39 | script: zero missing |
| Internal API operations (hidden from OpenAPI, read from internal.py) | 4 | 4 | total 43 |
| Identity migrations | 7 (001-007) | 7 | script: all named in 07a; 000 bootstrap also noted |
| Tables | 12 (identity 4, platform 1, registry 2, governance 5) | 12 | checked against live dev DB by the helper |
| Env and config names | 85 | 85 | identity 46, production example 31, web 8 |
| Screens | 24 | SCR-01..SCR-24 | 7 described from code only (see 03-ux gaps) |
| Test files | 11 | all named in 05 and TRACEABILITY | not re-run |
| Business requirements | 24 | BR-01..BR-24 | |
| Functional requirements | FR01-18, FR-019..060 | all in 02/02a/02b/02c | FR-040..046 reserved for planned features |
| Ports | 11 | 11 | architecture.md |
| Deploy scripts | 9 | 9 | RUNBOOK.md |

## Left out or unverified
- Browser: only the sign-in, dev act-as, hub, account sheet and admin Today/member detail were viewed (owner asked to rely on code). Other screens come from code. Nothing at 1280px.
- Per-role permission lists in `roles.py` and middleware detail in `main.py`: marked unverified in the docs.
- Counsel and Vyapar health paths, database roles and registry availability: unverified.
- Test results: suites not run.
- Mermaid diagrams checked by reading only.


## Update after account deletion (2026-11-22)

Counts changed by the deletion feature. These were derived by adding the new items to the table above; they were not re-measured against the running service (unverified).

| Item | Before | After |
|---|---|---|
| Public API operations | 39 | 45 (4 account delete endpoints, 2 admin) |
| Internal API operations | 4 | 4 in identity (each module also exposes `POST /internal/v1/members/{id}/erase`) |
| Identity migrations | 7 (001-007) | 8 (001-008) |
| Tables | 12 | 14 (`identity.deletion_job`, `identity.deletion_job_module`) |
| Env and config names | 85 | 87 (`ERASE_MODULE_API_URLS`, `DELETION_TOMBSTONE_PEPPER`) |
| Business requirements | 24 | 30 (BR-25 to BR-30) |
| Functional requirements | up to FR-060 | up to FR-070 |
| Test cases | TC-01 to TC-40 | TC-01 to TC-47 |

Not verified: browser rendering of the deletion screens; whether the identity governance test failure is unrelated.

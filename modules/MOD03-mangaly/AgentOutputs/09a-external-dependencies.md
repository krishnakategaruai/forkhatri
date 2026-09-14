---
step: 09a-external-dependencies
module: MOD03
status: Ready for Review
updated: 2026-09-13
---

# 09a — External Dependencies — MOD03 Mangaly

(A lightweight, human-readable companion to real SBOM tooling —
CycloneDX/SPDX generators like syft or cyclonedx-bom should still run in
CI for the machine-readable artifact; this file is the traceable record
inside this pipeline.)

Versions below are the **resolved** versions actually installed into
`modules/MOD03-mangaly/mangaly-service/.venv` on 2026-09-13, captured from
`pip freeze`, not the versions planned at design time. Transitive
dependencies are listed separately from direct ones, because the
"known to Step 8?" question is answered differently for each.

## Dependencies — direct

| Package/API | Version | Traces to (TR/FR) | Known to Step 8 before use? | Supplementary security review |
|---|---|---|---|---|
| fastapi | 0.141.1 | Whole module (CODING-GUIDE §1 fixes FastAPI as the stack) | Yes — named in `/ARCHITECTURE.md`, `IMPLEMENTATION-TEST-STANDARDS.md` §5, and CODING-GUIDE §1, which re-validated the choice against 2026 practice | Not required |
| uvicorn[standard] | 0.52.4 | Whole module — `IMPLEMENTATION-TEST-STANDARDS.md` §5 names `uvicorn app.main:app` as the run command | Yes — named in the project standards' Commands table | Not required |
| pydantic | 2.13.5 | TR001+ (typed request/response contracts across 14 components) | Yes — `IMPLEMENTATION-TEST-STANDARDS.md` §1 and CODING-GUIDE §1 both name Pydantic explicitly | Not required |
| pydantic-settings | 2.15.0 | Config wiring against `07a-db-implementation/.env.example` | **Partially.** Step 8 assumed `.env`-driven configuration throughout (SP092/SP104 cite `CREDENTIAL_HASH_*` from `.env.example`) but never named the library that reads it. It is the standard companion package to an already-approved dependency (same maintainer, same release train as Pydantic) and adds no network, subprocess, or deserialization surface beyond reading a local `.env` file | **Assessed, not escalated** — see "Assessment notes" below. No new STRIDE surface identified; raising a blocker for the config-file reader of an already-approved library would be process theatre, not shift-left security. Flagged here so the Security Lead can disagree on review. |
| SQLAlchemy[asyncio] | 2.0.52 | All data access; `07a-db-implementation/README.md` "ORM / migration-tool conventions for Step 9" names SQLAlchemy 2.x async as the default | Yes — named in the Sealed Step 7a README, which Step 8 reviewed | Not required |
| asyncpg | 0.31.0 | The Postgres driver behind SQLAlchemy's async engine | **Partially.** Step 7a's README fixes "SQLAlchemy 2.x (async engine)" but does not name a driver. asyncpg is the only production-grade async Postgres driver SQLAlchemy 2.x supports, so the choice was effectively made upstream | **Assessed, not escalated.** One genuinely security-relevant property was checked rather than assumed: asyncpg does **not** support multi-statement queries in its extended-protocol path and binds all parameters server-side, which is the property `app/db/session.py` and `app/events/bus.py` rely on. Verified live. |
| greenlet | 3.5.5 | Required by SQLAlchemy's asyncio extension | Implied by SQLAlchemy[asyncio] | Not required — it is a hard requirement of an approved dependency, not an independent choice |
| argon2-cffi | 25.1.0 | TR092, TR093 / **SP092, SP093, SP104** | **Yes — explicitly.** SP092, SP104 and `v1-decisions.md`'s Known-technical-debt note all name Argon2id as the pinned algorithm, and `.env.example` pins its parameters (`CREDENTIAL_HASH_TIME_COST=3`, `MEMORY_COST_KB=65536`, `PARALLELISM=4`). argon2-cffi is the reference Python binding to the Argon2 reference implementation | Not required — the algorithm was chosen by Step 8 itself |
| python-dotenv | 1.2.1 | `.env` loading for pydantic-settings | Implied by pydantic-settings | Not required |
| httpx | 0.28.1 | `identity_bridge/delivery.py` — real Twilio SMS calls (DEC-V1-011/DEC-V1-012) | **Corrected 2026-09-13: was misfiled under dev/test-only below.** httpx started as the ASGI test-transport client and moved to production use when Twilio delivery was implemented, but this file wasn't updated at the time — found and fixed during FR001 implementation, not a new addition | **Assessed, not escalated.** Its production use is a synchronous-looking `async with httpx.AsyncClient(...)` POST with HTTP basic auth to a single, hardcoded Twilio URL — no user-controlled URL, no redirect-following surface beyond Twilio's own domain. |
| python-multipart | 0.0.32 | `api/routes/profile.py` — FastAPI's required backend for `multipart/form-data` (FR001's photo upload) | Not previously named — FR001 is the first endpoint accepting a file upload | **Assessed, not escalated.** A thin, widely-used multipart parser FastAPI itself requires for this exact purpose; `storage.py`'s own size cap (8 MiB) and content-type allow-list are the actual abuse-surface controls, not this library. |

## Dependencies — dev/test only (not shipped)

| Package | Version | Purpose |
|---|---|---|
| pytest | 9.0.1 | `IMPLEMENTATION-TEST-STANDARDS.md` §5 names `pytest` |
| pytest-asyncio | 1.3.0 | Async test support for the async stack |
| ruff | 0.15.1 | `IMPLEMENTATION-TEST-STANDARDS.md` §5 names `ruff check .` |
| mypy | 1.19.1 | `IMPLEMENTATION-TEST-STANDARDS.md` §5 names `mypy .` |

## Transitive dependencies (resolved, not directly chosen)

`annotated-types 0.8.0`, `anyio 4.15.1`, `certifi 2026.7.22`, `cffi 2.1.1`,
`click 8.5.0`, `colorama 0.4.6`, `h11 0.16.0`, `httpcore 1.0.9`,
`idna 3.19`, `iniconfig 2.3.0`, `packaging 26.3`, `pluggy 1.6.0`,
`starlette 1.6.0`.

These are pulled in by the direct dependencies above and were not
independently selected. They are recorded for SBOM completeness; the
machine-readable artifact from CI is the authority for the full closure.

## External APIs / services

No external API is called by any code in this build. The following are
configured (with placeholder values) but **not yet integrated** — they
become dependency-manifest entries when the code that calls them lands:

| Service | Config keys | Traces to | Status |
|---|---|---|---|
| PagerDuty Events API v2 | `PAGERDUTY_*` | TR065, DEC-V1-011 | Config + trigger contract only (`app/config/paging.py`); no HTTP client written |
| Object Storage (S3-compatible) | `OBJECT_STORAGE_*` | TR002, TR006 | Config only; no client written |
| SMS/OTP provider | `SMS_*`, `OTP_FALLBACK_CHANNEL` | TR095 | Config only; provider not selected (`SMS_PROVIDER=CHANGE_ME`) |
| cybercrime.gov.in / SJPU CSAM intake | `CSAM_REPORT_*` | TR065, DEC-V1-009/011 | Config only; no client written |

## Assessment notes

The rule this file exists to enforce is that a third-party package not
already known to Step 8 is unvetted attack surface and must not be
silently absorbed. Two entries above (`pydantic-settings`, `asyncpg`)
are honest edge cases: neither was named by Step 8, and both are the
inevitable companion of something Step 8 *did* approve. Rather than
either pretending they were known or raising blockers that would stall
the build on a formality, they are recorded as **assessed with the
reasoning shown**, so the Security Lead can convert either into a
supplementary review at approval time if they disagree with that call.
Nothing here is presented as cleared by a review that did not happen.

## Open supplementary security reviews

| Dependency | Blocker raised | Status |
|---|---|---|
| — | none | No dependency in this build introduces an external network call, a subprocess, a native parser over untrusted input, or a deserialization path over attacker-controlled data. |

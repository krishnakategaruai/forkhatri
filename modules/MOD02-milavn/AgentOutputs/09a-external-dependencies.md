---
step: 09a-external-dependencies
module: MOD02
status: In Progress
updated: 2026-09-13
---

# 09a — External Dependencies — MOD02 Milavn

(A lightweight, human-readable companion to real SBOM tooling — CycloneDX/SPDX generators should still run in CI for the machine-readable artifact; this file is the traceable record inside this pipeline.)

Step 8 (Security & Performance) has not run for this module yet — the user directed Step 9 to start directly. Every dependency below is therefore marked "No" for *known to Step 8 before use*, and the whole set is one supplementary STRIDE pass for Step 8 to clear when it runs. Versions are the exact resolved ones in `milavn-service/pyproject.toml` / `milavn-web/package-lock.json`, identical to MOD03 Mangaly's already-running baseline wherever the same package is used.

## Dependencies
| Package/API | Version | Traces to (TR/FR) | Known to Step 8 before use? | Supplementary security review |
|---|---|---|---|---|
| fastapi | 0.141.1 | all TRs (API layer) | No — SEC-BLOCKER-01 (bundle) | Pending Step 8 |
| uvicorn[standard] | 0.52.4 | runtime | No | Pending |
| pydantic / pydantic-settings | 2.13.5 / 2.15.0 | TR-CROSSCUT-03 (typed contracts), settings | No | Pending |
| SQLAlchemy[asyncio] / asyncpg / greenlet | 2.0.52 / 0.31.0 / 3.5.5 | data layer, TR16 RLS `SET LOCAL` | No | Pending |
| python-multipart | 0.0.32 | TR01/TR10 photo & cover upload | No | Pending |
| httpx | 0.28.1 | tests / future OpenCage & MapTiler calls (TR03/TR29) | No | Pending |
| python-dotenv | 1.2.1 | config | No | Pending |
| tzdata | 2025.2 | TR05/FR004 IST day boundaries on Windows | No | Pending |
| next / react / react-dom | 16.3.5 / 19.2.8 / 19.2.8 | web client, TR33 SSR public page | No | Pending |
| i18next / react-i18next | ^26.4.2 / ^17.0.13 | FR002 / ADR-010 | No | Pending |
| leaflet (+ @types/leaflet) | ^1.9.4 | TR03 Map mode | No | Pending |
| Google Fonts — Anek Latin / Devanagari / Telugu (via `next/font`, self-hosted at build) | — | 04-ui.md Foundation typography | No | Pending |
| OpenStreetMap tile API (`tile.openstreetmap.org`) — development only; MapTiler placeholder for real use | — | TR03 | No | Pending — swap to a keyed provider before any public deployment (OSM tile policy) |
| Wikimedia Commons API (CC images) / i.pravatar.cc — one-time download of development cover photos and avatars into `public/assets` (not called at runtime) | — | IMP18 seed assets | No | Pending — attribution per image licence, or replace with own imagery before release |
| api.qrserver.com (QR image generation, runtime, development) | — | FR014/FR049 share QR | No | Pending — replace with an in-repo QR generator before release (leaks the share URL to a third party) |

## Open supplementary security reviews
| Dependency | Blocker raised | Status |
|---|---|---|
| Whole set above (Step 8 not yet run) | SEC-BLOCKER-01 | Open — to be cleared by Step 8's scoped STRIDE pass; `api.qrserver.com` and OSM tiles are the two items most likely to need a change, both already noted above. |

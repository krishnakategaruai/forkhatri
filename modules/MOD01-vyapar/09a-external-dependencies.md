---
step: 09a-external-dependencies
module: MOD01
status: In Progress
updated: 2026-09-15
---

# 09a — External Dependencies — MOD01 Vyapar

(A lightweight, human-readable companion to real SBOM tooling — CycloneDX/
SPDX generators like syft or cyclonedx-bom should still run in CI for the
machine-readable artifact; this file is the traceable record inside this
pipeline.)

## Dependencies

| Package/API | Version | Traces to (TR/FR) | Known to Step 8 before use? | Supplementary security review |
|---|---|---|---|---|
| fastapi | 0.141.1 | All TR001-TR055 (the whole API layer) | Yes — `07-tech-reqs.md`'s revision history explicitly names "the existing scaffold (`vyapar-web` Next.js 16 App Router, `vyapar-service` FastAPI/asyncpg)" as the stack Step 7 wrote against; `IMPLEMENTATION-TEST-STANDARDS.md` §"Stack" fixes FastAPI as the project-wide backend choice. | Not needed — pre-vetted stack choice, not a new dependency this session introduced. |
| uvicorn | 0.53.0 | Same as fastapi (its ASGI server) | Yes — implied by the same FastAPI stack decision; `IMPLEMENTATION-TEST-STANDARDS.md` §5 names `uvicorn app.main:app --reload` as this project's own dev-server command. | Not needed. |
| asyncpg | 0.31.0 | TR050 and every TR touching Postgres (all of them) | Yes — `07-tech-reqs.md` names "`vyapar-service` FastAPI/asyncpg" explicitly as the existing scaffold Step 7 wrote against. | Not needed. |
| pydantic-settings | 2.15.0 | TR050, Cross-cutting §1/§2 (config loading) | Yes (by extension) — FastAPI's own request/response validation is Pydantic-based (`IMPLEMENTATION-TEST-STANDARDS.md`'s "typed contract... via Pydantic"); `pydantic-settings` is the standard, first-party-maintained companion for env-file settings loading in that same ecosystem, not a separate untrusted package. | Not needed — same trust boundary as Pydantic itself (no network calls, reads local `.env` only). |
| python-dotenv | 1.0.x (already present before this session) | Cross-cutting config loading | Yes — already installed in the environment before this session started. | Not needed. |
| motion | 13.2.0 (already present in `vyapar-web/package.json` before this session) | Design direction (View Transitions / spring-physics motion) | Yes — already an installed dependency in the pre-existing `vyapar-web` scaffold this session inherited (`package.json` before any edit this session made). This session only *used* `motion/react`'s existing subpath export, verified live against the installed package's own `exports` map before use — did not add or upgrade the package. | Not needed — pre-existing, not newly introduced. |
| next, react, react-dom | 16.3.5 / 19.2.8 / 19.2.8 (already present) | Every frontend page | Yes — pre-existing scaffold. | Not needed. |
| cryptography (pyca) | 50.0.1 | TR008 / SP008 (AES-256-GCM `identifier_enc`, IMP20) | No — SP008 requires encryption of the verification identifier but names no library; raised as SEC-SUPP-01 | Cleared 2026-09-15 — scoped supplementary STRIDE pass below |
| i18next | 26.4.2 | Product-owner i18n rule (IMP15), every UI string | No — added after Step 8 by the owner's multilingual rule; raised as SEC-SUPP-02 | Cleared 2026-09-15 — scoped pass below |
| react-i18next | 17.0.14 | Same as i18next | No — same as above, SEC-SUPP-02 | Cleared 2026-09-15 — scoped pass below |
| Razorpay REST API v1 (Payment Links, Refunds, Webhooks) — external API, called with the Python standard library (`urllib`, `hmac`), no SDK | API v1 | TR051 / FR51 (IMP23) | Yes — SP051 names Razorpay explicitly (X-Razorpay-Signature HMAC-SHA256 over the raw body; dedupe on x-razorpay-event-id) | Not needed — pre-vetted by Step 8. Inert in dev: `PAYMENT_GATEWAY=dev_sandbox` and the keys are `CHANGE_ME` placeholders, which make the real adapter fail closed to "payment service unavailable" |

## Supplementary scoped security reviews (one dependency each — not a Step 8 re-run)

**SEC-SUPP-01 — `cryptography` 50.0.1 (backend)**
- *Spoofing / Tampering:* only `AESGCM` is used, an AEAD, so any tampering with `identifier_enc` fails decryption instead of yielding altered plaintext. A fresh 12-byte random nonce is used per encryption (`os.urandom`), and a nonce is never reused.
- *Information disclosure:* the key comes from `VERIFICATION_IDENTIFIER_ENCRYPTION_KEY` in env (an out-of-band placeholder), never the DB. The API returns only `identifier_masked` (last 4 characters) and has no decrypt route.
- *Supply chain:* pyca/cryptography is the Python Cryptographic Authority's package. It ships wheels built against OpenSSL, and is the de-facto standard that FastAPI ecosystem security libraries themselves depend on. Pinned with `>=50.0` in `requirements.txt`, and the resolved version is recorded here.
- *Denial of service / Elevation:* no network, parsing or deserialisation surface is exposed to request input. Only a short identifier string is encrypted.
- **Result:** cleared, no new controls needed beyond SP008's own.

**SEC-SUPP-02 — `i18next` 26.4.2 + `react-i18next` 17.0.14 (frontend)**
- *Tampering / XSS:* translations are bundled static JSON imported at build time, and no remote backend loader is used. Interpolated values render through React text nodes. `dangerouslySetInnerHTML` and `<Trans>` with HTML are not used, so user-supplied values cannot inject markup.
- *Information disclosure:* no network calls and no analytics. Language preference is stored in localStorage and in the member's own `language` column.
- *Supply chain:* this is the same library pair MOD03 Mangaly already uses (the owner's directive was to mirror that pattern), so it adds no new trust boundary for the product.
- **Result:** cleared.

## Dependencies deliberately NOT added (and why, so a future session doesn't reach for them by habit)

- **httpx** (or any third-party async HTTP client) — TR050's real-path
  Identity & Trust resolve call in `vyapar-service/app/identity.py`
  (`_resolve_real`) is implemented with Python's standard library
  (`urllib.request` wrapped in `asyncio.to_thread`) instead. That code path
  is inert in dev (`DEV_MODE=true` never calls it) and the config value it
  would call (`IDENTITY_SERVICE_INTERNAL_URL`) is still a `CHANGE_ME`
  placeholder — adding a new pip dependency for a path nothing in this
  session's running app exercises would have triggered this file's own
  "new dependency needs a supplementary Step 8 pass" rule for no real
  benefit. If/when a real Identity & Trust integration is built, this is
  the one call site to revisit — either keep stdlib or add `httpx` then,
  with the supplementary review done at that point.

## Open supplementary security reviews

| Dependency | Blocker raised | Status |
|---|---|---|
| cryptography 50.0.1 | SEC-SUPP-01 (2026-09-15) | Cleared 2026-09-15 |
| i18next 26.4.2 / react-i18next 17.0.14 | SEC-SUPP-02 (2026-09-15) | Cleared 2026-09-15 |

No open reviews. (Original 2026-09-14 note, kept:) Every dependency the first session actually added to the running
application (`fastapi`, `uvicorn`, `asyncpg`, `pydantic-settings`) was
already implied/named by the Sealed `07-tech-reqs.md`'s own stated stack
before Step 8 ran its STRIDE pass — none of them is new, unvetted attack
surface Step 8 hadn't already priced in when it wrote SP001-SP055 against
"the existing scaffold... FastAPI/asyncpg."

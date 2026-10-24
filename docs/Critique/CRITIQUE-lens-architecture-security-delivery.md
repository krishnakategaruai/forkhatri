# ForKhatri critique: architecture, security, reliability, cost, delivery

Reviewer lens: technical architect and security reviewer. Date: 2026-10-06. Method: read `deploy/`, `ARCHITECTURE.md`, the ParentApp architecture/tech/security docs and both module architecture files; read and grepped code in identity, Vyapar, Milavn, Mangalya, Counsel and the shared integrations library; ran read-only checks against the local system (signed in as the Asha persona in an isolated browser context, `curl` against local ports, `npm audit`). Nothing was changed, submitted or exploited. External claims carry a URL and date; "unverified" marks what I could not confirm. The web-search budget ran out mid-session, so some research items are secondary-sourced.

**Caveat on measurements.** The running stack is `next dev` (Turbopack) with dev tunnels, so byte counts and timings below are indicative of structure (request counts, duplication), not of production speed. No production build was available to measure (the only one, `.next-build`, dates from 14 Sep).

## 1. Understanding (please correct)

ForKhatri is built as one entrance (Next.js "multi-zones" host) plus a platform Identity and Trust service that issues one opaque `HttpOnly` session cookie. Each module has its own FastAPI service and Next.js web app, and calls identity server-to-server to resolve the cookie. Modules enforce per-member Postgres row-level security through `SET LOCAL`, with SECURITY DEFINER functions as the controlled bypass. Production is planned as one Oracle Always Free Ampere VM (2 OCPU / 12 GB) running Docker Compose: Caddy, `cloudflared` tunnel, one Postgres 18 with several databases, Resend email, nightly dumps to Cloudflare R2, deploy over SSH from a laptop or GitHub Actions. The deploy kit covers identity, entrance, Mangalya and Milavn only. Vyapar, Counsel, Dashboard, Payments and Finance are not in it. The architecture documents describe a modular monolith with shared services (broker, audit, notification, search). The code is five separate web apps and five separate API processes with no shared services. The team is the owner plus AI build agents.

## 2. Critiques, ranked

### Critical

**C1. Development back doors are on by default and one is reachable through the tunnels.** Effort: S.
- Evidence (all observed locally): Vyapar's `DEV_MODE` defaults to `True` (`vyapar-service/app/config.py:25`) and there is no production guard. With it on, headers `X-Dev-Member-Id` and `X-Dev-Admin-Scopes` are trusted. `GET /v1/admin/verification-queue` returned 403 without them and `200 []` with `X-Dev-Member-Id: m_neha_ops` and `X-Dev-Admin-Scopes: vyapar.verify,vyapar.moderate`. So any caller can become any member, or an operator, in any environment where the flag is not turned off.
- The identity service defaults to `ENVIRONMENT=development`, `DEV_EXPOSE_OTP=true` (the sign-in code is returned in the response) and `CHANGE_ME` keys. Its production guard is excellent, but it only runs if `ENVIRONMENT=production` is set. The default fails open.
- `POST /dev/v1/sessions` (identity `dev_tools/router.py`) opens a session for any `member_id` with no credential in browser mode. `GET /dev/v1/personas` returned the owner, the samaj president and the secretary without authentication, through the entrance's `/tunnel-proxy/identity/*` rewrite (`platform/forkhatri-web/next.config.ts`). While a tunnel is up, anyone who learns the URL can reach this. I did not call the POST. Whether it can be exercised from the internet depends on the tunnel's allowed-origins list; I read the code but did not test that.
- Why it matters: testers and other sessions are already using public `trycloudflare.com` URLs. Real member-like data (matrimony profiles) sits behind a passwordless admin impersonation.
- Fix: make every module refuse to start unless `ENVIRONMENT=production` is explicit and its dev switches are off. Invert the defaults (secure unless `ENVIRONMENT=development`). Gate `/dev/v1` behind a static shared dev token even in browser mode. Never rewrite `/dev/*` through the tunnel proxy. Copy the identity `_production_guard` into Vyapar, Counsel, Milavn and Mangalya.

**C2. The deploy kit points at a folder that no longer exists, and ships only 2 of 5 modules.** Effort: S to fix the path, M to add the rest.
- Evidence: `deploy/docker-compose.yml`, `deploy/scripts/deploy.sh`, `deploy/migrate/*` and `.github/workflows/deploy.yml` all reference `modules/MOD03-mangaly/...`. The repository folder is `MOD03-mangalya` (`git ls-files` shows 4,823 files under the new name, 0 under the old). Today the tar upload and Docker builds for Mangalya would fail, and a push that changes only Mangalya would not trigger the workflow (its path filter has the old name).
- The hub shows Vyapar and Counsel as "Open now" while production cannot run them.
- Why it matters: "we can deploy" has not been true since the rename. The first real launch will fail at the worst moment.
- Fix: rename the paths, add a dry-run `docker compose build` and `migrate --status` job on every pull request, and decide whether launch is Mangalya plus Milavn only.

**C3. Single point of failure for sensitive family data, and the stated recovery objectives do not match what is built.** Effort: M.
- Evidence: everything runs on one free VM and one Postgres container (`deploy/README.md`). The Step 8 document promises "RPO ≤5 min, RTO ≤1 h" for identity. The backup is a nightly plain `pg_dump` (`backup.sh`), so the real RPO is up to 24 hours. There is no WAL archiving or point-in-time recovery, no encrypted backups (dumps with horoscopes, family details and photos go to R2 in clear), no object lock or versioning (the same R2 token on the VM can delete the history), no restore drill, and no alert if a backup fails.
- Oracle halved the Always Free allowance from 4 OCPU / 24 GB to 2 OCPU / 12 GB, enforced from 2026-06-15, with instances over the limit shut down (https://infoq.com/news/2026/07/oracle-cloud-free-tier-limits/, 2026-07-03). Idle reclamation applies when CPU, network and memory are all under 20% over 7 days (https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm, fetched 2026-10-06). Unexplained account terminations are reported anecdotally on LowEndSpirit and Reddit (unverified; I could not retrieve specific threads).
- Why it matters: a matrimony module that loses a month of connections or leaks a backup breaks the trust the product sells.
- Fix: for launch, move to a paid VM (about $25-60 per month) with a provider that has a support line. Add WAL-G or pgBackRest to R2 with client-side encryption, R2 object lock, a monthly restore drill, and an external uptime monitor that messages the owner.

### High

**H1. A critical Next.js advisory applies to all five web apps today, and nothing watches for the next one.** Effort: S.
- Evidence: `npm audit --omit=dev` on the entrance and on Mangalya reports `next 16.2.0-16.3.5` critical, GHSA-vcvr-r3jv-pc5j (RCE in the Node `next/og` `ImageResponse`, published 2026-09-22, fixed in 16.3.6; `npm audit` suggests 16.3.8). All five apps pin 16.3.5. I found no use of `ImageResponse` in the apps, so it is likely not exploitable here. Next.js also shipped critical releases on 2026-08-25 (image optimizer RCE via AVIF) and High middleware/SSRF fixes in May and July (https://nextjs.org/blog/august-2026-security-release, https://nextjs.org/blog/july-2026-security-release). React2Shell (CVE-2025-55182, CVSS 10, 2025-12-03) was exploited within hours (https://nextjs.org/blog/CVE-2025-66478).
- Why it matters: five Node processes to patch, with exact-pinned versions and no Dependabot or CI audit.
- Fix: bump to the latest 16.3.x patch, add Dependabot or Renovate plus `npm audit` and `pip-audit` in CI, strip `x-middleware-subrequest` at Caddy, and disable image optimizer features you do not use. Fewer Node apps (see H3) means fewer patch targets.

**H2. Almost no automated tests, and no gate before deploy.** Effort: M to L.
- Evidence: about 184,000 lines of Python and TypeScript. Test files: identity 7, Milavn 8, Mangalya 7, shared library 2, and zero for every web app, for Vyapar's API (about 36,000 lines, only manual `check_*.py` scripts) and for Counsel. The only workflow is `deploy.yml`; it runs no tests, and the deploy pushes the working tree.
- Why it matters: an AI agent changing code daily with no regression net is how a security fix in one module breaks another. This also makes C1 and C2 invisible until launch.
- Fix: a CI job that builds all images, runs the existing tests, boots Postgres, applies migrations from empty, and runs a small Playwright smoke per module using `dev_session.py`. Add an RLS test that runs as the runtime role and checks that member A cannot read member B.

**H3. Architecture documents and reality have diverged, and cross-cutting code is copied four times.** Effort: M (decision), L (consolidation).
- Evidence: `ARCHITECTURE.md` and Milavn's `architecture.md` say Milavn, Vyapar and Dashboard are one FastAPI process on a shared "Core Platform" database, with a message broker, Audit, Notification and Search services. In code, Vyapar and Counsel have their own service, web app and database, and no broker or shared services exist. Rate limiters, idempotency, outbox, i18n loaders, notification queues and media code are re-implemented per module (Milavn's DB-backed limiter is one of at least four).
- External evidence: Segment merged 140+ services back into one because 3 engineers were just keeping them alive (https://www.twilio.com/en-us/blog/developers/best-practices/goodbye-microservices/, 2018). Shopify runs a 2.8M-line modular monolith and extracts only for throughput or isolation (https://shopify.engineering/shopify-monolith, 2020). Amazon Prime Video cut one monitoring tool's cost by about 90% by merging services (via https://world.hey.com/dhh/even-amazon-can-t-make-sense-of-serverless-or-microservices-59625580, 2023). Those are older, narrow cases; I could not run 2024-26 searches.
- Why it matters for a small team: 12 processes, 5 databases, 5 migration folders and 5 sets of secrets multiply every fix.
- Fix: keep isolation only where the law or the risk demands it (Mangalya, and later payments). Move Milavn, Vyapar and Counsel's APIs into one deployable with separate schemas and roles. Extract the shared rate limiter, outbox and idempotency into `shared/`.

**H4. Migrations: two sources of truth, duplicate numbers, and editing applied files.** Effort: S to M.
- Evidence: Milavn has two files numbered `050`; Vyapar has two `026`. The migration runner (`deploy/migrate/migrate.py`) orders by file name and records filename plus SHA-256, so it works, but ordering between duplicates is alphabetical by accident. `schema.sql` says it is "equivalent to applying every file in migrations/" and `init.sh` loads it for dev, but it contains no `locality_lat` (050), no `ticket_type` (052) and no albums (053) (grep returned 0). `052-ticket-types-codes-contact.sql` is committed and also modified in the working tree; the runner only warns "changed after it was applied; not re-run", so production and dev will drift.
- Rollback is forward-only by design (`deploy/README.md`), which is acceptable only if migrations stay additive.
- Fix: never edit an applied migration; add `056`. Renumber duplicates now. Delete `schema.sql` or generate it with `pg_dump` in CI. Test "empty database plus all migrations equals dev database" on every pull request.

**H5. Row-level security is hand-built at scale, with no automated proof.** Effort: M.
- Evidence: distinct SECURITY DEFINER functions: Milavn 184, Mangalya 140, Vyapar 75. I checked every definition: all set `search_path` and the sampled ones `REVOKE ... FROM PUBLIC`, which is what PostgreSQL asks (https://www.postgresql.org/docs/current/sql-createfunction.html). That is strong. But `FORCE ROW LEVEL SECURITY` appears nowhere (0 hits), so a table owner bypasses policies (https://www.postgresql.org/docs/current/ddl-rowsecurity.html). Every definer function is a private authorisation decision that bypasses RLS and needs its own review. Postgres RLS pitfalls include views that skip policies (use `security_invoker`), and a forgotten `SET LOCAL` under pooling (https://www.pgbouncer.org/features.html). Real incidents: 16,326 exposed Supabase databases in UpGuard's study, and CVE-2025-48757 (https://www.upguard.com/blog/everything-everywhere-systemic-data-exposure-in-supabase-apps, 2025-26).
- Fix: FORCE RLS on member-data tables, a CI test that enumerates definer functions without an owner/viewer check, `security_invoker` on views, policies that fail closed on NULL context.

**H6. Admin accounts are as weak as member accounts.** Effort: M.
- Evidence: the samaj president and secretary use the same 30-day cookie, signed in by email code (SMS is off) or password. There is a two-person approval rule (good, `approval_four_eyes`), but no step-up authentication, no idle timeout and no passkey. The admin personas exist in dev data.
- Why it matters: these accounts can approve roles and see the audit trail. Email takeover equals community takeover.
- Fix: passkeys (WebAuthn) or TOTP for every admin and moderator role, 12-hour admin sessions, step-up before approvals. ASVS 5.0 (2025-05-30) asks for session listing and termination at L2 (https://github.com/OWASP/ASVS/tree/v5.0.0/5.0/en).

**H7. Photo handling for a matrimony product.** Effort: S to M.
- Evidence: Mangalya trusts the browser's `Content-Type` (`profile/storage.py`), does not check file signature, re-encode or strip EXIF; no service strips EXIF at all (0 hits). Phone photos carry GPS. Mangalya serves each photo through Python with `Cache-Control: private, no-store` after a per-request authorisation check, which is the right privacy choice but means no CDN can ever help. Vyapar checks extension only, and serves `/uploads` as static files. Counsel's malware scanner defaults to `none`. Milavn is good: it sniffs magic bytes and enforces size while streaming (`media_files.py`).
- OWASP says re-encode images and strip metadata (https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html).
- Fix: one shared image pipeline (Pillow: decode, resize to 2 sizes, re-encode to WebP/JPEG, drop EXIF). Use it in every module.

**H8. Place search breaks the OpenStreetMap policy, and does not scale.** Effort: M.
- Evidence: Milavn's `PlacePicker` sends a debounced request on every typed keystroke to `nominatim.openstreetmap.org` (settings default). The policy: maximum 1 request per second; "Auto-complete search ... you must not implement such a service on the client side"; identifying User-Agent; results must be cached (https://operations.osmfoundation.org/policies/nominatim/, fetched 2026-10-06). The library is careful (1.1 s gap, cache, User-Agent), but a single process-wide 1.1 s queue means 50 people searching at once wait about a minute. The default User-Agent is generic (`ForKhatri-Milavn/1.0`) and the contact email is blank. Modules that reverse-geocode send members' coordinates to a third party.
- Fix: for launch, bundle an India place list or self-host Photon on the VM. Later options: LocationIQ (free 5,000 per day), Google Places (70,000 free events per month in India) or Ola/Mappls (current quotas unverified). Keep the `places` seam so this stays a config change.

### Medium

**M1. No security headers beyond HSTS and nosniff; no CSP or clickjacking protection.** Effort: S. Evidence: no `Content-Security-Policy`, `frame-ancestors` or `X-Frame-Options` anywhere in the repo's apps or Caddyfile (grep found none; API and page responses I captured carried none). A hostile page could frame the sign-in or a connection request. Add a baseline CSP (report-only first) and `frame-ancestors 'self'` at Caddy.

**M2. Observability and incident duty.** Effort: M. Evidence: logs rotate locally (10 MB x 5), there is no error tracker, metrics or alert, and the heartbeat restarts the stack silently. Log masking is good (`hint()` masks phone/email). DPDP Rule 7 expects a detailed breach report to the Board within 72 hours, and CERT-In's 2022 directions ask for 6-hour incident reporting and 180-day logs (https://www.cert-in.org.in/PDF/CERT-In_Directions_70B_28.04.2022.pdf). DPDP core duties commence 2027-05-13 (secondary: https://www.scconline.com/blog/post/2025/12/26/digital-personal-data-protection-rules-2025-key-highlights/); confirm against the Gazette. Add Sentry or GlitchTip, uptime alerts to WhatsApp or email, and an incident runbook.

**M3. Rate limiting is per-feature and database-backed; international numbers are accepted.** Effort: S to M. Evidence: Milavn's limiter writes to Postgres on each limited call (write amplification, hot rows). Most read endpoints, search and LLM-backed endpoints have no per-member budget (OWASP API4, https://api-security.owasp.org/editions/2023/en/0x11-t10). Identity accepts "any `+`-prefixed E.164" number (`07-tech-reqs.md` TR13), so once SMS is funded, SMS pumping to foreign numbers becomes a cost risk. The WAF stays on defaults. Allow only `+91` for SMS, add Cloudflare rate-limit rules on `/api/identity/v1/auth/*`, set a daily SMS spend cap, and cap LLM calls per member per day.

**M4. Sessions: strong design, three residual gaps.** Effort: S. Strengths: opaque 256-bit token stored as a digest, `__Host-` prefix, no `Domain`, enforced in production. Gaps: (1) 30-day absolute lifetime and no idle timeout; (2) revocation reaches modules in up to 30 s by design; (3) only identity, Mangalya and Milavn check `Origin` on state-changing requests. Vyapar and Counsel rely on `SameSite=Lax`, which is enough on one origin but not on sibling subdomains, since SameSite is registrable-domain wide (https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html). One XSS in any module acts as the member in all, because every zone shares one origin. Add the Origin guard to every service and a content-security-policy per zone.

**M5. Mobile performance is untested against real low-end devices.** Effort: M. Evidence (dev build): Mangalya Home made 76 requests and 35 API calls on load, including six `/auth/me`, three identity session checks and three `connections/incoming` calls (React strict mode in dev explains some duplication, not all), 11 photos loaded individually, a 257 KB font file on Milavn, no service worker and no web app manifest on any module. Under Slow 4G with 4x CPU throttling at 360 px, the dev build reached first paint at 2.05 s and the load event at about 8 s. Budgets: India P75 is about 6.2 Mbps and 85 ms; for a 3 s load keep JS under 0.3-0.6 MiB (https://infrequently.org/2025/11/performance-inequality-gap-2026/, 2025-11); Android is 93.9% and Chrome 90.6% of Indian mobile (https://gs.statcounter.com/os-market-share/mobile/india, Sep 2026). Fix: one bootstrap endpoint per module home, image thumbnails, a production Lighthouse run on a Galaxy A24-class profile, and a manifest.

**M6. Cost model and lock-in (rough; unit prices from the research pass, my arithmetic).** Effort: S to plan.

| Members | Compute + DB | R2 | Email (Resend) | SMS OTP (India) |
|---|---|---|---|---|
| 10k | free VM, or about $25-60 paid | under $1 | free tier to $20 | under Rs 500 per month |
| 100k | $25-100 VM, optionally $60-120 managed DB | about $8 | $20-90 | about Rs 3-4k |
| 1M | multiple boxes, replicated DB, CDN: about $500-2,000 | about $75 | about $300-800 | about Rs 30-40k |

Sources: R2 https://developers.cloudflare.com/r2/platform/pricing/; Resend and SMS prices are vendor blogs (secondary, 2026). The mailbox and SMS lines are small; the real cost is people and risk. Lock-in is low where the `shared/forkhatri-integrations` seams exist (payments, SMS, email, places), moderate for Cloudflare (tunnel, R2, DNS) and Oracle. Note Cloudflare Quick Tunnels have no uptime guarantee, 200 in-flight requests, no SSE and are "for testing and development" (https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/, fetched 2026-10-06). That is fine for dev, but the owner is already sharing them with testers.

**M7. Bus factor and delivery hygiene.** Effort: S. Evidence: 36 commits for 6,747 tracked files, with messages like "new", "final", "new puhs"; very large unreviewed commits; all work by AI agents; one owner machine holds the SSH key and `owner-inputs.env`. Screenshots (`.logs/*.png`) are tracked. `deploy.sh` uploads the working tree (it marks releases `-dirty`, which is honest, but the build is not reproducible from git). Fix: small commits, branch protection, deploy only tagged clean commits, keep a sealed copy of secrets in a password manager (the README already says so), and write a one-page "if the owner is unavailable" runbook for a trusted samaj officer.

## 3. New in the world

- Next.js now publishes pre-announced security releases (2026-07-13), so plan a patch day (https://nextjs.org/blog/july-2026-security-release).
- OWASP ASVS 5.0 (2025-05-30) adds session-management and file-handling requirements you can check against (https://github.com/OWASP/ASVS/tree/v5.0.0/5.0/en).
- RFC 10017 (BCP 212, 2026) on browser-based apps endorses the cookie-mediated backend pattern ForKhatri already uses (https://www.rfc-editor.org/rfc/rfc10017).
- Passkeys for admin roles are now cheap to add.
- WhatsApp authentication templates in India cost roughly Rs 0.11-0.13 (secondary, https://baat.ai/blog/whatsapp-api-pricing-india), and many Khatri families use WhatsApp daily; this could replace SMS OTP.
- DPDP Rules 2025 (notified 2025-11-13) phase in over 18 months; the Rule 7 breach report, Section 9 child rules and logging duties will bind you from 2027-05-13 (secondary sources; verify in the Gazette).
- Hetzner raised prices in April and June 2026 and has no India region (https://northflank.com/blog/hetzner-cloud-server-price-increases); a cheap overseas VM is not the easy exit it was.
- Real leaks of personal-photo apps: the Tea app exposed about 72,000 images and 1.1M messages in July 2025 (https://en.wikipedia.org/wiki/Tea_(app)); it shows what an open or misconfigured store does to a trust product. I found no verified India matrimonial leak (unverified).

## 4. Rethink

1. **One database and process per module.** For: matches Mangalya's privacy and legal load; isolates blast radius. Against: on a single VM there is no real isolation (one host failure), and it multiplies migrations, patching and secrets for a tiny team. Best resolution: isolate Mangalya and payments only.
2. **A free VM for family data.** For: zero cost during validation. Against: Oracle changed the allowance in 2026 with little notice and has no support commitment; the cost of one lost month is greater than $40. Pay for a small VM before the first real member.
3. **Build five modules, deploy two.** For: shows the umbrella vision. Against: every unlaunched module adds code, patching and risk (C1 is in unlaunched Vyapar). Consider launching one module, with tests.
4. **Thirty-day sessions for everyone.** For: low friction for non-technical elders and parents. Against: admin and agent accounts carry community-level power. Use different lifetimes by role.
5. **AI agents write and review everything.** For: speed. Against: no human owns the mental model (bus factor), and agents add flags and defaults that are safe locally and dangerous in production. Add a small human-readable "production checklist" test.

## 5. Do not change

- The opaque session design: hashed token, `__Host-` cookie, no `Domain`, and the identity service's production guard that refuses insecure settings.
- Argon2id, HMAC-hashed OTPs, constant-time comparisons, dummy hashing for unknown users, and masked logging.
- Fail-closed integrations: placeholder secrets reject payment signatures (`_common.py`), sandbox gateways refuse to run outside local use.
- `SET search_path` on every SECURITY DEFINER function, `REVOKE ... FROM PUBLIC`, non-owning runtime roles.
- Caddy: internal paths return 404 at the edge, trusted-proxy handling of `CF-Connecting-IP`, `no-new-privileges`, `cap_drop: ALL`, read-only containers, memory limits.
- Milavn's upload checks (magic bytes, streaming size cap) and Mangalya's per-request photo authorisation.
- The AI design: minimal text only, redaction of contacts, closed vocabularies, validated output, and a rules fallback.
- The ledgered migration runner with checksums, release-per-folder deploy with automatic rollback, and the `-dirty` marker.
- Two-person approval for admin decisions, and the "basic identity only" rule for the platform member.
- The shared integrations seam, which keeps vendors replaceable.

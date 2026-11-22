# ForKhatri deployment summary (as built, 2026-11-22)

Document status: AS BUILT on 2026-11-22. A short map; the full owner guide is `deploy/README.md` and the
step-by-step operations are in `docs/RUNBOOK.md`. Nothing has been deployed yet (no Docker on the build
machine; scripts checked with `bash -n` and a native rehearsal, see `09-implementation.md`).

## Design

- One Oracle Cloud Always Free Ampere VM (Ubuntu 24.04 aarch64, 2 OCPU, 12 GB, 100 GB boot volume), no web ports open.
- Cloudflare Tunnel (`cloudflared` container, outbound only) to Caddy on the private Docker network.
- One public origin: `/` entrance; `/mangaly` and `/milavn` Next.js zones with `basePath`; `/api/identity|mangaly|milavn` with the prefix stripped.
- PostgreSQL 18 container; three databases (`forkhatri_identity`, `mangaly`, `forkhatridb`); one-shot `migrate` job.
- Email codes by Resend; SMS not configured (phone sign-in returns `delivery_unavailable`).
- Backups: nightly to the VM (14 days) and optionally to Cloudflare R2 (30 days).
- CI: `.github/workflows/deploy.yml` (push to `main` or manual), SSH to the VM, runs `deploy/scripts/deploy.sh --ci`.

## Cost (from deploy/README.md; verify before relying)

Oracle Always Free and Cloudflare Free are zero cost within limits; domain, Resend free tier and R2 free tier (10 GB) apply.
Oracle may reclaim an idle free instance (CPU p95, network and memory all under 20% for 7 days); the stated guarantee is
converting the account to Pay As You Go, still free within Always Free limits.

## What is deployed vs not

| Item | Status |
|---|---|
| Identity service, entrance, Mangalya, Milavn | in the compose file |
| Vyapar, Counsel | NOT in compose, Caddy or migrate (planned work) |
| MOD05, MOD06, MOD07 | do not exist |
| Docker images, compose run, cloudflared, backup and restore scripts | never run in production |

## Drift to fix before first deploy

`deploy/docker-compose.yml`, `deploy/scripts/deploy.sh`, `deploy/migrate/migrate.py`, `deploy/migrate/Dockerfile` and
`.github/workflows/deploy.yml` reference `modules/MOD03-mangaly/...`; the folder is now `MOD03-mangalya`. Rename the
references (the registry key and the service name `mangaly` stay). Also decide the production plan for Vyapar and Counsel.

## Decisions the owner must make or confirm

- Domain name, DNS and Cloudflare account; Resend sender; SMS or WhatsApp provider (needed for phone sign-in, critique C1).
- Whether to upgrade Oracle to Pay As You Go; whether R2 backups are mandatory (recommended).
- Data fiduciary and privacy notice before real members (DPDP, `docs/Critique/CRITIQUE-platform.md` C3).

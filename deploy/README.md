# ForKhatri production deployment

Everything runs on **one Oracle Cloud Always Free Ampere VM** (Ubuntu 24.04 aarch64,
2 OCPU / 12 GB) behind a **free Cloudflare Tunnel**. The VM opens no web ports:
`cloudflared` makes an outbound connection to Cloudflare, and Caddy is the only
HTTP entry inside Docker.

```
browser ──https──> Cloudflare ──tunnel──> cloudflared ──http──> caddy:80
   /                 -> forkhatri-web      (entrance, default zone)
   /mangaly/*        -> mangaly-web        (Next basePath /mangaly)
   /milavn/*         -> milavn-web         (Next basePath /milavn)
   /api/identity/*   -> identity-service   (prefix stripped)
   /api/mangaly/*    -> mangaly-service    (prefix stripped)
   /api/milavn/*     -> milavn-service     (prefix stripped, chat WebSocket, /media)
   /internal/*, /api/identity/internal*, /api/*/docs  -> 404
postgres:18 (forkhatri_identity, mangaly, forkhatridb) + a one-shot migrate job
```

Contract: `docs/ParentApp/07-tech-reqs.md` (TR12 cookie, TR14 internal API, TR19 delivery, TR22 zones).

## What you supply, and nothing else

All in one git-ignored file, `deploy/secrets/owner-inputs.env` (copy
`deploy/secrets/owner-inputs.env.example`). Never paste these into chat.

| Key | Where it comes from |
|---|---|
| `DOMAIN` | Your domain, e.g. `forkhatri.in` |
| `CLOUDFLARE_TUNNEL_TOKEN` | Step 3 below |
| `RESEND_API_KEY`, `EMAIL_FROM` | Step 4 below |
| `SERVER_IP`, `SERVER_USER` | Step 2 below (`ubuntu`) |
| `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET` | Step 5 below. Optional but **strongly recommended** |

`deploy/scripts/generate-secrets.sh` turns that into `deploy/secrets/.env.production`
with every database password, the OTP pepper and the service keys generated
(64 hex characters each). It never prints a value. Running it again keeps
existing secrets; `--rotate` makes new ones.

---

## 1. Before you start (this Windows machine)

- Git for Windows (Git Bash provides `bash`, `ssh`, `tar`; rsync is not needed).
- The SSH key pair `~/.ssh/forkhatri_oracle` and `~/.ssh/forkhatri_oracle.pub` (already present).

## 2. Oracle Cloud account and VM

1. Sign up at <https://signup.cloud.oracle.com>. Pick a **home region** near your members
   (e.g. India West (Mumbai) or India South (Hyderabad)); it cannot be changed later, and
   Always Free Ampere capacity is only in the home region.
2. Console → **Compute → Instances → Create instance**.
   - Name: `forkhatri-prod`.
   - **Image**: Change image → Canonical **Ubuntu 24.04** (the aarch64 build is selected automatically for Ampere).
   - **Shape**: Change shape → Ampere → **VM.Standard.A1.Flex**, **2 OCPUs, 12 GB memory** (the whole free allowance).
   - **Networking**: create a new VCN with a public subnet; **Assign a public IPv4 address**: yes.
   - **Add SSH keys** → Paste public keys → paste the whole content of `~/.ssh/forkhatri_oracle.pub`
     (in Git Bash: `cat ~/.ssh/forkhatri_oracle.pub`).
   - **Boot volume**: 100 GB (free allowance is 200 GB in total).
3. Create. If you see **"Out of capacity"**, retry later or in another availability domain;
   upgrading the account to Pay As You Go usually unlocks capacity and costs nothing within Always Free limits.
4. Copy the instance's **Public IP address** into `SERVER_IP`. `SERVER_USER=ubuntu`.
5. Leave the VCN security list as created (only port 22 inbound). Nothing else needs to be opened.
6. Check: `ssh -i ~/.ssh/forkhatri_oracle ubuntu@<SERVER_IP> uname -m` prints `aarch64`.

**Idle reclamation.** Oracle may reclaim an Always Free instance when, over 7 days, CPU (95th
percentile), network and memory are *all* below 20%. The running stack keeps memory above that,
and the heartbeat cron checks the site every 5 minutes. The only guarantee is converting the
account to **Pay As You Go** (Billing → Upgrade), which is still free inside Always Free limits.
Do it once the site matters. Either way, **set up R2 backups (step 5)**: a free VM can be lost.

## 3. Cloudflare: domain and tunnel

1. <https://dash.cloudflare.com> → **Add a domain** → enter your domain → Free plan.
   Change the nameservers at your registrar to the two Cloudflare shows; wait until the domain is **Active**.
2. **SSL/TLS → Overview**: *Full*. **SSL/TLS → Edge Certificates**: *Always Use HTTPS* on.
3. **Zero Trust → Networks → Tunnels → Create a tunnel** → *Cloudflared* → name `forkhatri-prod`.
4. On the install screen choose **Docker**; copy only the long token after `--token` into
   `CLOUDFLARE_TUNNEL_TOKEN`. Do not run the command shown; the stack runs cloudflared itself.
5. **Public hostnames → Add a public hostname**: Subdomain empty, Domain = your domain,
   Service **HTTP**, URL **`caddy:80`**. Save.
   (Optional: add `www` the same way.)
6. **Security → WAF** stays on defaults. **Caching**: defaults are fine; the apps send `no-store` on APIs.

## 4. Resend: email delivery of sign-in codes

1. <https://resend.com> → sign up → **Domains → Add domain** → your domain (region closest to India).
2. Resend shows DNS records (SPF `TXT`/`MX` on `send.`, DKIM `TXT` on `resend._domainkey`, optional DMARC).
   In Cloudflare **DNS → Records** add each exactly as shown, **Proxy status: DNS only**.
   (Resend's "Sign in to Cloudflare" button can add them for you.)
3. Wait for **Verified**, then **API Keys → Create API key**: permission *Sending access*,
   domain = yours. Put it in `RESEND_API_KEY`.
4. `EMAIL_FROM=ForKhatri <no-reply@your-domain>`.

**SMS is not configured.** Phone code requests return `delivery_unavailable`; the entrance tells
the member to use their password or email. Members imported from Mangaly keep their passwords.

## 5. Cloudflare R2: off-server backups (strongly recommended)

1. Cloudflare dashboard → **R2 Object Storage** → enable (free tier: 10 GB).
2. **Create bucket** `forkhatri-backups` (private, automatic location).
3. **Manage API tokens → Create API token**: *Object Read & Write*, **Apply to specific bucket** → `forkhatri-backups`.
4. Copy **Access Key ID**, **Secret Access Key**, and the **Account ID** (R2 overview page) into
   `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_ACCOUNT_ID`; `R2_BUCKET=forkhatri-backups`.

Without these, backups exist only on the VM, and losing the VM loses the data.

## 6. First deployment

In Git Bash, from the repository root:

```bash
cp deploy/secrets/owner-inputs.env.example deploy/secrets/owner-inputs.env
notepad deploy/secrets/owner-inputs.env          # fill in the values from steps 2-5
bash deploy/scripts/generate-secrets.sh          # names only are printed
bash deploy/scripts/deploy.sh --bootstrap        # prepares the VM, uploads, builds, migrates, starts
```

`--bootstrap` (once per VM, asks for nothing; `sudo` on Oracle's Ubuntu needs no password):
security updates and unattended upgrades, Docker Engine + compose plugin, a 4 GB swap file,
UFW allowing only SSH, SSH keys only, `/opt/forkhatri`, rclone, and cron for the nightly backup
(21:00 UTC = 02:30 IST) and the 5-minute heartbeat. Then it deploys.

The first build takes roughly 15-25 minutes on 2 Ampere cores (images are built one at a time).
The deploy ends with health checks of every service through Caddy; open `https://<DOMAIN>`.

Development members (`+919800000001` / `+919999900001`, password `ForKhatri-dev-2026`) are **not**
loaded. Only for a private trial:

```bash
bash deploy/scripts/deploy.sh --seed-dev
```

## Everyday operations

| Task | Command (Git Bash, repository root) |
|---|---|
| Deploy the current working tree | `bash deploy/scripts/deploy.sh` |
| Status, releases, memory, disk | `bash deploy/scripts/deploy.sh --status` |
| Follow logs (all / one service) | `bash deploy/scripts/deploy.sh --logs` · `--logs milavn-service` |
| Back up now | `bash deploy/scripts/deploy.sh --backup-now` |
| Roll back to the previous release | `bash deploy/scripts/deploy.sh --rollback` (or `--rollback <release-id>`) |
| Shell on the VM | `bash deploy/scripts/deploy.sh --ssh` |

On the VM, `/opt/forkhatri/current/deploy/scripts/compose.sh` is `docker compose` with the
secrets file, e.g. `compose.sh ps`, `compose.sh logs --tail=100 caddy`,
`compose.sh --profile ops run --rm migrate --status`.

### How a deploy works

`deploy.sh` streams the needed folders to `/opt/forkhatri/releases/<UTC time>-<git sha>`,
uploads `deploy/secrets/.env.production` to `/opt/forkhatri/shared/` (mode 600), then runs
`remote-release.sh`: build images tagged with the release id → start Postgres → run migrations →
`docker compose up -d` → health checks (`/edge-health`, the three `/api/*/health`, `/`, `/mangaly`,
`/milavn`). Healthy: `/opt/forkhatri/current` points at the new release and releases older than
the newest 5 are pruned. Unhealthy: the previous release is started again and the deploy fails.

### Roll back

`deploy.sh --rollback` restarts the previous release's images (no rebuild). **Migrations are
forward-only**: a rollback does not undo schema changes. Migrations in this repository are
additive, so the previous code normally runs on the newer schema; if a release ever ships a
destructive migration, restore the backup taken before it instead.

### Update secrets or inputs

Edit `deploy/secrets/owner-inputs.env`, then `generate-secrets.sh` and `deploy.sh`.
To rotate all generated secrets: `generate-secrets.sh --rotate`, then `deploy.sh` (migrations
re-sync database passwords; members stay signed in; codes requested in the last 5 minutes stop working).

## Backups and restore

Nightly on the VM (`backup.sh`): `pg_dump` of `forkhatri_identity`, `mangaly`, `forkhatridb`
(gzip), role definitions, and both media volumes, with `SHA256SUMS`. Kept **14 days** in
`/opt/forkhatri/backups/`, and, when R2 is configured, copied to `r2:<bucket>/forkhatri/<name>`
(verified, kept 30 days there). Log: `/opt/forkhatri/logs/backup.log`.

Restore on the same VM (SSH in first: `deploy.sh --ssh`):

```bash
/opt/forkhatri/current/deploy/scripts/restore.sh --list
/opt/forkhatri/current/deploy/scripts/restore.sh 20260915T210000Z                 # everything
/opt/forkhatri/current/deploy/scripts/restore.sh 20260915T210000Z --only mangaly  # one database
```

**Restore from R2 onto a new VM** (the VM was reclaimed or destroyed):

1. Create a new VM (step 2), update `SERVER_IP` in `owner-inputs.env`.
2. `bash deploy/scripts/deploy.sh --bootstrap` (same secrets file, so the same passwords and keys).
3. `bash deploy/scripts/deploy.sh --ssh`, then:
   ```bash
   /opt/forkhatri/current/deploy/scripts/restore.sh --list                       # shows R2 backups
   /opt/forkhatri/current/deploy/scripts/restore.sh <name> --from-r2
   ```
   It downloads, verifies checksums, stops the apps, recreates each database with its owner,
   loads the dumps, re-runs migrations (grants and anything newer), restores media and starts the apps.
4. The tunnel token is unchanged, so the site comes back at the same address.

If you lost `deploy/secrets/.env.production` too, restore still works: new secrets are generated,
migrations reset the role passwords, and members only need to sign in again if `OTP_PEPPER` changed
codes in flight. Keep a copy of `owner-inputs.env` and `.env.production` in a password manager.

## Push-to-deploy (optional)

`.github/workflows/deploy.yml` deploys every push to `main` that touches `platform/`, the two
modules or `deploy/`, and can be run by hand (Actions → deploy → Run workflow, with an option to
load development data). It never runs for pull requests or forks. It uploads the pushed commit,
builds on the VM, migrates, restarts with `docker compose up -d`, and fails if any health check fails.

1. Create a key only for GitHub (do not reuse your personal key):
   `ssh-keygen -t ed25519 -f ~/.ssh/forkhatri_github_deploy -N "" -C github-deploy`
2. Authorise it on the VM:
   `cat ~/.ssh/forkhatri_github_deploy.pub | ssh -i ~/.ssh/forkhatri_oracle ubuntu@<SERVER_IP> 'cat >> ~/.ssh/authorized_keys'`
3. GitHub → repository → **Settings → Secrets and variables → Actions → New repository secret**:
   - `SERVER_IP`: the VM address
   - `SERVER_USER`: `ubuntu`
   - `SSH_PRIVATE_KEY`: the full content of `~/.ssh/forkhatri_github_deploy`
   - `SSH_KNOWN_HOSTS` (recommended): output of `ssh-keyscan -t ed25519 <SERVER_IP>`
4. **Settings → Environments → production**: optionally add yourself as a required reviewer.
5. Run one deploy with `deploy.sh` first: the workflow expects `/opt/forkhatri/shared/.env.production`
   to exist already. Application secrets are never stored in GitHub.

## Memory budget (12 GB)

Container limits: Postgres 2048 MB, identity 384 MB, Mangaly API 512 MB, Milavn API 512 MB,
three web zones 384 MB each, Caddy 128 MB, cloudflared 128 MB, migrate job 256 MB
(≈ 5.3 GB). The rest is page cache and headroom for image builds (a Next.js build peaks near
2 GB and runs one at a time), plus the 4 GB swap file. `deploy.sh --status` shows live usage.

## Local rehearsal (a machine with Docker)

```bash
LOCAL_PORT=8080 bash deploy/scripts/generate-secrets.sh --local-test
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.local-test.yml \
  --env-file deploy/secrets/.env.local-test up -d --build
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.local-test.yml \
  --env-file deploy/secrets/.env.local-test --profile ops run --rm migrate --seed-dev --i-understand-this-loads-development-data
# http://localhost:8080 ; tear down: ... down -v
```

`LOCAL_HTTP_TEST=true` (only in `.env.local-test`) lets the identity service use `fk_session`
without `Secure` over plain http; production refuses to start without `__Host-fk_session` + Secure.

## Known limits

- Milavn runs as exactly one process: chat fan-out and its reminder/suggestion jobs are in memory.
- Uploaded media live on Docker volumes on the VM (included in backups), not object storage.
- Phone sign-in codes need an SMS provider; until then phone members use passwords.
- Image tags for Postgres, Caddy and cloudflared are major-version tags; pin exact tags in
  `.env.production` after the first good deploy.

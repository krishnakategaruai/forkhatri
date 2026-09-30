/**
 * ForKhatri tunnel launcher — one command to expose the whole app on the
 * public internet via Cloudflare Quick Tunnels, with every tunnel-sensitive
 * env value rewritten automatically. Companion to scripts/dev.mjs; use one
 * or the other, not both at once — this script starts its own dev servers.
 *
 * `npm run dev:tunnel` from the repo root:
 *   1. starts a cloudflared quick tunnel for every browser-facing port
 *   2. waits for each tunnel's assigned https://*.trycloudflare.com URL
 *   3. rewrites a clearly-marked, auto-managed block in every affected
 *      .env / .env.local file with the fresh tunnel URLs
 *   4. starts every dev server fresh, so each one reads the just-written
 *      tunnel URLs from its very first boot — no manual restart, ever
 *
 * Ctrl+C tears everything down in reverse: dev servers, then cloudflared
 * tunnels, then reverts every managed block back to localhost defaults —
 * so a plain `npm run dev` afterwards behaves exactly as if this script
 * had never run. This replaces the old manual process (hand-editing 8
 * files, copying values into .env.tunnel.bak, restarting servers by hand).
 *
 * Known limitation this script does NOT solve: Cloudflare Quick Tunnels
 * hand out a new random *.trycloudflare.com hostname every run, and each
 * service gets a DIFFERENT hostname — so the cross-module sign-in cookie
 * (fk_session) still will not carry over between modules while tunnelled.
 * Fixing that needs a named tunnel on a real domain you control (so every
 * service can share one parent domain and SESSION_COOKIE_DOMAIN can be
 * set) — a one-time ~15 minute setup, out of scope for this script.
 */

import { spawn } from "node:child_process";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import net from "node:net";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const IS_WINDOWS = process.platform === "win32";
const VENV_PYTHON = IS_WINDOWS ? path.join(".venv", "Scripts", "python.exe") : path.join(".venv", "bin", "python");
const NPM = IS_WINDOWS ? "npm.cmd" : "npm";

// ---------------------------------------------------------------------------
// Every browser-facing port. The horoscope service (8013) is deliberately
// absent — it is called loopback-only by mangalya-api and is never reached
// by a browser, tunnelled or not.
// ---------------------------------------------------------------------------

const SERVICES = [
  { key: "identity", dir: "platform/identity-service", port: 8100, kind: "api", describe: "Identity & Trust Service" },
  { key: "entrance", dir: "platform/forkhatri-web", port: 3100, kind: "web", describe: "ForKhatri entrance and hub" },
  { key: "mangalyaApi", dir: "modules/MOD03-mangalya/mangaly-service", port: 8000, kind: "api", describe: "MOD03 Mangalya API" },
  { key: "mangalyaWeb", dir: "modules/MOD03-mangalya/mangaly-web", port: 3000, kind: "web", describe: "MOD03 Mangalya" },
  { key: "milavnApi", dir: "modules/MOD02-milavn/milavn-service", port: 8001, kind: "api", describe: "MOD02 Milavn API" },
  { key: "milavnWeb", dir: "modules/MOD02-milavn/milavn-web", port: 3001, kind: "web", describe: "MOD02 Milavn" },
  { key: "vyaparApi", dir: "modules/MOD01-vyapar/vyapar-service", port: 8011, kind: "api", describe: "MOD01 Vyapar API" },
  { key: "vyaparWeb", dir: "modules/MOD01-vyapar/vyapar-web", port: 3011, kind: "web", describe: "MOD01 Vyapar" },
];

// Loopback-only services: started with everything else but never tunnelled.
// Mangalya's API calls the horoscope service on localhost; without it every
// horoscope match returns 503 and Mangalya's Home shows "can't be reached".
const INTERNAL_SERVICES = [
  { key: "horoscope", dir: "modules/MOD03-mangalya/horoscope-service", port: 8013, kind: "web", describe: "MOD03 Mangalya horoscope (internal)" },
];

const LOCAL_URLS = Object.fromEntries(SERVICES.map((s) => [s.key, `http://localhost:${s.port}`]));

// ---------------------------------------------------------------------------
// Which files carry tunnel-sensitive values, and how to build the managed
// block's content from a resolved { key: url } map (either LOCAL_URLS or the
// freshly-captured tunnel URLs). One function per file keeps every file's
// exact variable shape (JSON array, JSON object, single URL) explicit and
// easy to audit against that file's own config code.
// ---------------------------------------------------------------------------

function dedupe(arr) {
  return [...new Set(arr)];
}

const MANAGED_FILES = [
  {
    path: "platform/identity-service/.env",
    keys: ["CORS_ALLOWED_ORIGINS", "MODULE_ENTRY_URLS", "MODULE_API_URLS", "ADMIN_MODULE_API_URLS"],
    build: (u) => [
      `CORS_ALLOWED_ORIGINS=${JSON.stringify(dedupe([
        LOCAL_URLS.entrance, "http://127.0.0.1:3100",
        LOCAL_URLS.mangalyaWeb, LOCAL_URLS.milavnWeb, LOCAL_URLS.vyaparWeb,
        u.entrance, u.mangalyaWeb, u.milavnWeb, u.vyaparWeb,
      ]))}`,
      `MODULE_ENTRY_URLS=${JSON.stringify({ mangaly: u.mangalyaWeb, milavn: u.milavnWeb, vyapar: u.vyaparWeb })}`,
      `MODULE_API_URLS=${JSON.stringify({ mangaly: u.mangalyaApi, milavn: u.milavnApi })}`,
      `ADMIN_MODULE_API_URLS=${JSON.stringify({ vyapar: u.vyaparApi })}`,
    ],
  },
  {
    path: "platform/forkhatri-web/.env.local",
    keys: ["NEXT_PUBLIC_IDENTITY_API"],
    build: (u, tunneling) => [`NEXT_PUBLIC_IDENTITY_API=${tunneling ? "/tunnel-proxy/identity" : u.identity}`],
  },
  {
    path: "modules/MOD03-mangalya/mangaly-web/.env.local",
    keys: ["NEXT_PUBLIC_API_BASE", "NEXT_PUBLIC_FORKHATRI_ENTRANCE_URL", "NEXT_PUBLIC_IDENTITY_API"],
    build: (u, tunneling) => [
      `NEXT_PUBLIC_API_BASE=${tunneling ? "/tunnel-proxy/api" : u.mangalyaApi}`,
      `NEXT_PUBLIC_FORKHATRI_ENTRANCE_URL=${u.entrance}`,
      `NEXT_PUBLIC_IDENTITY_API=${tunneling ? "/tunnel-proxy/identity" : u.identity}`,
    ],
  },
  {
    path: "modules/MOD03-mangalya/mangaly-service/.env",
    keys: ["FORKHATRI_ENTRANCE_URL", "CORS_ALLOWED_ORIGINS"],
    build: (u) => [
      `FORKHATRI_ENTRANCE_URL=${u.entrance}`,
      `CORS_ALLOWED_ORIGINS=${JSON.stringify(dedupe([LOCAL_URLS.mangalyaWeb, "http://127.0.0.1:3000", u.mangalyaWeb]))}`,
    ],
  },
  {
    path: "modules/MOD02-milavn/milavn-web/.env.local",
    keys: ["NEXT_PUBLIC_API_BASE", "NEXT_PUBLIC_IDENTITY_API", "NEXT_PUBLIC_FORKHATRI_ENTRANCE_URL"],
    build: (u, tunneling) => [
      `NEXT_PUBLIC_API_BASE=${tunneling ? "/tunnel-proxy/api" : u.milavnApi}`,
      `NEXT_PUBLIC_IDENTITY_API=${tunneling ? "/tunnel-proxy/identity" : u.identity}`,
      `NEXT_PUBLIC_FORKHATRI_ENTRANCE_URL=${u.entrance}`,
    ],
  },
  {
    path: "modules/MOD02-milavn/milavn-service/.env",
    keys: ["FORKHATRI_ENTRANCE_URL", "CORS_ALLOWED_ORIGINS"],
    build: (u) => [
      `FORKHATRI_ENTRANCE_URL=${u.entrance}`,
      `CORS_ALLOWED_ORIGINS=${JSON.stringify(dedupe([LOCAL_URLS.milavnWeb, "http://127.0.0.1:3001", u.milavnWeb]))}`,
    ],
  },
  {
    path: "modules/MOD01-vyapar/vyapar-web/.env.local",
    keys: ["NEXT_PUBLIC_API_URL", "NEXT_PUBLIC_PLATFORM_URL", "NEXT_PUBLIC_HOST_IDENTITY_API"],
    build: (u, tunneling) => [
      `NEXT_PUBLIC_API_URL=${tunneling ? "/tunnel-proxy/api" : u.vyaparApi}`,
      `NEXT_PUBLIC_PLATFORM_URL=${u.entrance}`,
      `NEXT_PUBLIC_HOST_IDENTITY_API=${tunneling ? "/tunnel-proxy/identity" : u.identity}`,
    ],
  },
  {
    path: "modules/MOD01-vyapar/vyapar-service/.env",
    keys: ["WEB_ORIGIN", "FORKHATRI_ENTRANCE_URL"],
    build: (u) => [`WEB_ORIGIN=${u.vyaparWeb}`, `FORKHATRI_ENTRANCE_URL=${u.entrance}`],
  },
];

const MARK_BEGIN = "# >>> forkhatri-tunnel-managed (scripts/tunnel.mjs — do not edit by hand) >>>";
const MARK_END = "# <<< forkhatri-tunnel-managed <<<";

function upsertManagedBlock(relPath, keys, lines) {
  const full = path.join(ROOT, relPath);
  if (!existsSync(full)) {
    note(`  ${paint(31, "skip")} ${relPath} does not exist`);
    return;
  }
  const original = readFileSync(full, "utf8");
  const keyPattern = new RegExp(`^(${keys.join("|")})=`);
  let out = original.split(/\r?\n/).filter((line) => !keyPattern.test(line));

  const beginIdx = out.indexOf(MARK_BEGIN);
  if (beginIdx !== -1) {
    let endIdx = out.indexOf(MARK_END, beginIdx);
    if (endIdx === -1) endIdx = out.length - 1;
    out.splice(beginIdx, endIdx - beginIdx + 1);
  }
  while (out.length && out[out.length - 1].trim() === "") out.pop();

  out.push("", MARK_BEGIN, ...lines, MARK_END, "");
  writeFileSync(full, out.join("\n"));
}

function applyEnvState(urls, label, tunneling) {
  headline(`Writing ${label} values into ${MANAGED_FILES.length} env files...`);
  for (const file of MANAGED_FILES) {
    upsertManagedBlock(file.path, file.keys, file.build(urls, tunneling));
    note(`  ${paint(32, "ok")}   ${file.path}`);
  }
}

// ---------------------------------------------------------------------------
// Small output helpers (mirrors scripts/dev.mjs's style).
// ---------------------------------------------------------------------------

const ESC = String.fromCharCode(27);
const paint = (code, text) => `${ESC}[${code}m${text}${ESC}[0m`;
const dim = (text) => paint(2, text);
function note(line) { process.stdout.write(`${line}\n`); }
function headline(line) { process.stdout.write(`\n${paint(1, line)}\n`); }

// ---------------------------------------------------------------------------
// Port probing (same connect-based check as dev.mjs — a bind test lies on
// Windows because of SO_REUSEADDR).
// ---------------------------------------------------------------------------

function portInUse(port) {
  return new Promise((resolve) => {
    const socket = net.connect({ port, host: "127.0.0.1" });
    const settle = (answer) => { socket.destroy(); resolve(answer); };
    socket.setTimeout(1000);
    socket.once("connect", () => settle(true));
    socket.once("timeout", () => settle(false));
    socket.once("error", () => settle(false));
  });
}

function missingPrerequisite(svc) {
  const dir = path.join(ROOT, svc.dir);
  if (!existsSync(dir)) return `${svc.dir} does not exist`;
  if (svc.kind === "api" && !existsSync(path.join(dir, VENV_PYTHON))) {
    return `no virtualenv at ${svc.dir}/.venv`;
  }
  if (svc.kind === "web" && !existsSync(path.join(dir, "node_modules"))) {
    return `no node_modules in ${svc.dir}`;
  }
  return null;
}

function commandFor(svc) {
  if (svc.kind === "api") {
    return {
      command: path.join(ROOT, svc.dir, VENV_PYTHON),
      args: ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", String(svc.port)],
    };
  }
  if (IS_WINDOWS) {
    return { command: process.env.ComSpec || "cmd.exe", args: ["/d", "/s", "/c", "npm run dev"] };
  }
  return { command: NPM, args: ["run", "dev"] };
}

// ---------------------------------------------------------------------------
// cloudflared quick tunnels. Each tunnel is its own child process; the
// assigned https://*.trycloudflare.com URL appears in its stderr output.
// ---------------------------------------------------------------------------

const TUNNEL_URL_RE = /https:\/\/[a-z0-9-]+\.trycloudflare\.com/i;

function startTunnel(svc) {
  return new Promise((resolve, reject) => {
    const child = spawn("cloudflared", ["tunnel", "--url", `http://localhost:${svc.port}`], {
      stdio: ["ignore", "pipe", "pipe"],
      windowsHide: true,
    });
    let resolved = false;
    const onData = (chunk) => {
      const text = chunk.toString("utf8");
      const match = text.match(TUNNEL_URL_RE);
      if (match && !resolved) {
        resolved = true;
        resolve({ svc, child, url: match[0] });
      }
    };
    child.stdout.on("data", onData);
    child.stderr.on("data", onData);
    child.on("error", (err) => { if (!resolved) reject(err); });
    child.on("exit", (code) => {
      if (!resolved) reject(new Error(`cloudflared for ${svc.key} exited (code ${code}) before printing a URL`));
    });
    setTimeout(() => {
      if (!resolved) { child.kill(); reject(new Error(`cloudflared for ${svc.key} timed out waiting for a URL`)); }
    }, 30_000);
  });
}

// ---------------------------------------------------------------------------
// Dev-server children (same spawn/log pattern as dev.mjs, kept independent
// so this script owns its full process tree and Ctrl+C is always safe).
// ---------------------------------------------------------------------------

const LABEL_WIDTH = Math.max(...SERVICES.map((s) => s.key.length), "cloudflared".length) + 2;

function spawnService(svc, extraEnv = {}) {
  const { command, args } = commandFor(svc);
  const child = spawn(command, args, {
    cwd: path.join(ROOT, svc.dir),
    env: { ...process.env, FORCE_COLOR: "1", PYTHONUNBUFFERED: "1", ...extraEnv },
    stdio: ["ignore", "pipe", "pipe"],
    windowsHide: true,
  });
  const relay = (stream) => {
    let buffer = "";
    stream.setEncoding("utf8");
    stream.on("data", (chunk) => {
      buffer += chunk;
      const lines = buffer.split(/\r?\n/);
      buffer = lines.pop() ?? "";
      for (const line of lines) if (line.trim()) note(`${paint(36, svc.key.padEnd(LABEL_WIDTH))}${dim("|")} ${line}`);
    });
  };
  relay(child.stdout);
  relay(child.stderr);
  child.on("exit", (code, signal) => {
    if (!shuttingDown) note(`${paint(31, svc.key.padEnd(LABEL_WIDTH))}${dim("|")} exited (code ${code ?? "none"}${signal ? `, signal ${signal}` : ""})`);
  });
  return child;
}

let shuttingDown = false;
const serviceChildren = [];
const tunnelChildren = [];

function killTree(child) {
  if (!child || child.exitCode !== null || child.pid === undefined) return;
  if (IS_WINDOWS) {
    spawn("taskkill", ["/pid", String(child.pid), "/t", "/f"], { stdio: "ignore", windowsHide: true });
  } else {
    try { process.kill(-child.pid, "SIGTERM"); } catch { child.kill("SIGTERM"); }
  }
}

async function teardown() {
  if (shuttingDown) return;
  shuttingDown = true;
  headline("Shutting down...");
  for (const c of serviceChildren) killTree(c);
  for (const c of tunnelChildren) killTree(c);
  applyEnvState(LOCAL_URLS, "localhost", false);
  note(dim("Reverted every managed env block to localhost. `npm run dev` is safe to use normally now."));
  setTimeout(() => process.exit(0), 1500);
}

process.on("SIGINT", teardown);
process.on("SIGTERM", teardown);

// ---------------------------------------------------------------------------
// Main sequence
// ---------------------------------------------------------------------------

async function main() {
  headline("ForKhatri — tunnel mode");

  for (const svc of SERVICES) {
    if (await portInUse(svc.port)) {
      note(`${paint(31, "blocked")} :${svc.port} (${svc.describe}) is already in use.`);
      note(dim("  This script needs to control every service's full lifecycle so each one boots with"));
      note(dim("  fresh tunnel URLs. Stop any running `npm run dev` (or other process on this port) first."));
      process.exit(1);
    }
    const problem = missingPrerequisite(svc);
    if (problem) {
      note(`${paint(31, "missing")} ${svc.describe}: ${problem}`);
      process.exit(1);
    }
  }

  headline(`Starting ${SERVICES.length} Cloudflare Quick Tunnels...`);
  const tunnels = await Promise.all(
    SERVICES.map((svc) =>
      startTunnel(svc).then((result) => {
        note(`${paint(32, "up")}     ${svc.key.padEnd(LABEL_WIDTH)} ${dim("->")} ${result.url}`);
        return result;
      })
    )
  );
  for (const t of tunnels) tunnelChildren.push(t.child);
  const tunnelUrls = Object.fromEntries(tunnels.map((t) => [t.svc.key, t.url]));

  applyEnvState(tunnelUrls, "tunnel", true);

  headline(`Starting ${SERVICES.length} dev servers with tunnel-aware env...`);
  for (const svc of SERVICES) {
    // Next.js dev servers reject requests whose Host header isn't localhost
    // unless the origin is explicitly allow-listed (allowedDevOrigins in each
    // app's next.config.ts) — TUNNEL_DEV_ORIGIN carries this run's actual
    // tunnel hostname to that config, since it's random every run.
    const extraEnv =
      svc.kind === "web"
        ? { TUNNEL_DEV_ORIGIN: new URL(tunnelUrls[svc.key]).host, FORKHATRI_IDENTITY_INTERNAL_URL: LOCAL_URLS.identity }
        : {};
    serviceChildren.push(spawnService(svc, extraEnv));
    note(`${paint(32, "start")}  ${svc.key.padEnd(LABEL_WIDTH)} :${svc.port}  ${dim(svc.describe)}`);
  }
  for (const svc of INTERNAL_SERVICES) {
    serviceChildren.push(spawnService(svc));
    note(`${paint(32, "start")}  ${svc.key.padEnd(LABEL_WIDTH)} :${svc.port}  ${dim(svc.describe)}`);
  }

  headline("Open (share these — each is a different public hostname)");
  for (const svc of SERVICES.filter((s) => s.kind === "web")) {
    note(`${paint(1, tunnelUrls[svc.key].padEnd(45))}  ${dim(svc.describe)}`);
  }
  note("");
  note(dim("Sign-in will NOT carry across these hostnames (each is a separate origin) — sign in"));
  note(dim("separately on each module you open. See scripts/tunnel.mjs's header comment for why."));
  note(dim("Ctrl+C stops every server and tunnel, and reverts all env files to localhost."));
  process.stdout.write("\n");
}

main().catch((err) => {
  console.error(err);
  teardown();
});

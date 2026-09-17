/**
 * ForKhatri development launcher — one command for the whole product.
 *
 * `npm run dev` from the repository root starts the platform (identity service +
 * entrance) and every module that has actually been built, each on its own pinned
 * port, in one terminal with prefixed logs.
 *
 * Two rules from CLAUDE.md are enforced here rather than left to discipline:
 *
 *  1. A port that is already in use is LEFT ALONE. Several sessions work on this
 *     repository at the same time, so a listener we did not start may belong to
 *     someone else's workstream. We report it as "already running" and skip it —
 *     we never kill by port or by image name (a broad `python.exe` kill has taken
 *     down three other services before).
 *  2. On shutdown we kill only the child processes this script started, by exact
 *     PID, with their own process trees.
 *
 * Python services run WITHOUT uvicorn's --reload: on Windows the reloader spawns
 * the real server as a multiprocessing child that inherits the listening socket,
 * so killing the reloader leaves an orphan serving stale code.
 */

import { spawn } from "node:child_process";
import net from "node:net";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const IS_WINDOWS = process.platform === "win32";
const NPM = IS_WINDOWS ? "npm.cmd" : "npm";
const VENV_PYTHON = IS_WINDOWS ? path.join(".venv", "Scripts", "python.exe") : path.join(".venv", "bin", "python");

// ---------------------------------------------------------------------------
// The processes that make up a full local ForKhatri.
//
// `group` is what --only filters on. Postgres is a prerequisite, not a child:
// it runs as a service on 5433 and we only check that it is there.
// ---------------------------------------------------------------------------

const POSTGRES_PORT = 5433;

const PROCESSES = [
  {
    group: "platform",
    name: "identity",
    color: 36,
    dir: "platform/identity-service",
    port: 8100,
    kind: "api",
    describe: "Identity & Trust Service — sign-in, sessions, module registry",
  },
  {
    group: "platform",
    name: "entrance",
    color: 96,
    dir: "platform/forkhatri-web",
    port: 3100,
    kind: "web",
    describe: "ForKhatri entrance and hub",
  },
  {
    group: "mangaly",
    name: "mangaly-api",
    color: 35,
    dir: "modules/MOD03-mangaly/mangaly-service",
    port: 8000,
    kind: "api",
    describe: "MOD03 Mangaly API",
  },
  {
    group: "mangaly",
    name: "mangaly-web",
    color: 95,
    dir: "modules/MOD03-mangaly/mangaly-web",
    port: 3000,
    kind: "web",
    describe: "MOD03 Mangaly",
  },
  {
    group: "milavn",
    name: "milavn-api",
    color: 34,
    dir: "modules/MOD02-milavn/milavn-service",
    port: 8001,
    kind: "api",
    describe: "MOD02 Milavn API",
  },
  {
    group: "milavn",
    name: "milavn-web",
    color: 94,
    dir: "modules/MOD02-milavn/milavn-web",
    port: 3001,
    kind: "web",
    describe: "MOD02 Milavn",
  },
  {
    group: "vyapar",
    name: "vyapar-api",
    color: 33,
    dir: "modules/MOD01-vyapar/vyapar-service",
    port: 8011,
    kind: "api",
    describe: "MOD01 Vyapar API",
  },
  {
    group: "vyapar",
    name: "vyapar-web",
    color: 93,
    dir: "modules/MOD01-vyapar/vyapar-web",
    port: 3011,
    kind: "web",
    describe: "MOD01 Vyapar (open directly — the hub still lists it as in development)",
  },
];

// ---------------------------------------------------------------------------
// Small output helpers. One fixed-width prefix per process so interleaved logs
// stay readable in a single terminal.
// ---------------------------------------------------------------------------

const ESC = String.fromCharCode(27);
const LABEL_WIDTH = Math.max(...PROCESSES.map((p) => p.name.length), 8);
const paint = (code, text) => `${ESC}[${code}m${text}${ESC}[0m`;
const dim = (text) => paint(2, text);
const BAR = "|";

function log(proc, line) {
  const label = proc.name.padEnd(LABEL_WIDTH);
  process.stdout.write(`${paint(proc.color, label)} ${dim(BAR)} ${line}\n`);
}

function note(line) {
  process.stdout.write(`${"".padEnd(LABEL_WIDTH)} ${dim(BAR)} ${line}\n`);
}

function headline(line) {
  process.stdout.write(`\n${paint(1, line)}\n`);
}

// ---------------------------------------------------------------------------
// Port probing.
//
// We test by CONNECTING, not by binding. On Windows libuv sets SO_REUSEADDR, so
// a second bind to a port that is already being listened on succeeds — a bind
// test reports a busy port as free and we would start a duplicate server that
// silently steals half the connections. A successful connection is unambiguous.
// ---------------------------------------------------------------------------

function portInUse(port) {
  return new Promise((resolve) => {
    const socket = net.connect({ port, host: "127.0.0.1" });
    const settle = (answer) => {
      socket.destroy();
      resolve(answer);
    };
    socket.setTimeout(1000);
    socket.once("connect", () => settle(true));
    socket.once("timeout", () => settle(false));
    socket.once("error", () => settle(false));
  });
}

async function waitForHttp(port, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      // Any HTTP answer means the server is up; a 404 is as good as a 200 here.
      await fetch(`http://localhost:${port}/`, { signal: AbortSignal.timeout(2000) });
      return true;
    } catch {
      await new Promise((r) => setTimeout(r, 500));
    }
  }
  return false;
}

// ---------------------------------------------------------------------------
// Readiness checks. Each entry is either startable, already-listening, or has a
// missing prerequisite (no virtualenv, no node_modules) that we report plainly
// instead of crashing the whole launch.
// ---------------------------------------------------------------------------

function missingPrerequisite(proc) {
  const dir = path.join(ROOT, proc.dir);
  if (!existsSync(dir)) return `${proc.dir} does not exist`;
  if (proc.kind === "api" && !existsSync(path.join(dir, VENV_PYTHON))) {
    return `no virtualenv at ${proc.dir}/.venv — create it and install requirements`;
  }
  if (proc.kind === "web" && !existsSync(path.join(dir, "node_modules"))) {
    return `no node_modules in ${proc.dir} — run npm install there`;
  }
  return null;
}

function commandFor(proc) {
  if (proc.kind === "api") {
    return {
      command: path.join(ROOT, proc.dir, VENV_PYTHON),
      args: ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", String(proc.port)],
    };
  }
  // Node refuses to spawn a .cmd shim directly (the CVE-2024-27980 fix), so npm
  // on Windows goes through the command interpreter explicitly.
  if (IS_WINDOWS) {
    return { command: process.env.ComSpec || "cmd.exe", args: ["/d", "/s", "/c", "npm run dev"] };
  }
  return { command: NPM, args: ["run", "dev"] };
}

// ---------------------------------------------------------------------------
// Launch
// ---------------------------------------------------------------------------

const args = process.argv.slice(2);
const onlyArg = args.find((a) => a.startsWith("--only="));
const statusOnly = args.includes("--status");
const wanted = onlyArg
  ? onlyArg.slice("--only=".length).split(",").map((s) => s.trim()).filter(Boolean)
  : null;

const selected = PROCESSES.filter((p) => !wanted || wanted.includes(p.group) || wanted.includes(p.name));

if (selected.length === 0) {
  const groups = [...new Set(PROCESSES.map((p) => p.group))].join(", ");
  console.error(`Nothing matched --only=${wanted?.join(",")}. Groups: ${groups}`);
  process.exit(1);
}

const children = [];
let shuttingDown = false;

function start(proc) {
  const { command, args: cmdArgs } = commandFor(proc);
  let child;
  try {
    child = spawn(command, cmdArgs, {
      cwd: path.join(ROOT, proc.dir),
      env: { ...process.env, FORCE_COLOR: "1", PYTHONUNBUFFERED: "1" },
      stdio: ["ignore", "pipe", "pipe"],
      windowsHide: true,
    });
  } catch (err) {
    // One process failing to launch must not take the other seven down with it.
    log(proc, paint(31, `could not start: ${err.message}`));
    return null;
  }

  const relay = (stream) => {
    let buffer = "";
    stream.setEncoding("utf8");
    stream.on("data", (chunk) => {
      buffer += chunk;
      const lines = buffer.split(/\r?\n/);
      buffer = lines.pop() ?? "";
      for (const line of lines) if (line.trim()) log(proc, line);
    });
  };
  relay(child.stdout);
  relay(child.stderr);

  child.on("exit", (code, signal) => {
    if (shuttingDown) return;
    log(proc, paint(31, `exited (code ${code ?? "none"}${signal ? `, signal ${signal}` : ""})`));
  });

  child.on("error", (err) => log(proc, paint(31, `could not start: ${err.message}`)));

  children.push({ proc, child });
  return child;
}

/**
 * Stop only what we started, by exact PID and with the process tree, so a
 * uvicorn or Next.js worker is not left orphaned holding its port.
 */
function stopAll() {
  if (shuttingDown) return;
  shuttingDown = true;
  headline("Stopping the processes this launcher started...");
  for (const { proc, child } of children) {
    if (child.exitCode !== null || child.pid === undefined) continue;
    note(`${proc.name} (pid ${child.pid})`);
    if (IS_WINDOWS) {
      spawn("taskkill", ["/pid", String(child.pid), "/t", "/f"], { stdio: "ignore", windowsHide: true });
    } else {
      try {
        process.kill(-child.pid, "SIGTERM");
      } catch {
        child.kill("SIGTERM");
      }
    }
  }
  setTimeout(() => process.exit(0), 1500);
}

process.on("SIGINT", stopAll);
process.on("SIGTERM", stopAll);

async function main() {
  headline("ForKhatri — development");

  if (await portInUse(POSTGRES_PORT)) {
    note(`${paint(32, "ok")}      Postgres is listening on ${POSTGRES_PORT}`);
  } else {
    note(`${paint(31, "missing")} Postgres is NOT listening on ${POSTGRES_PORT} — every API will fail to serve data.`);
    note(`        Start it, then run this again.`);
  }

  const started = [];
  const alreadyUp = [];
  const skipped = [];

  for (const proc of selected) {
    const problem = missingPrerequisite(proc);
    if (problem) {
      skipped.push({ proc, reason: problem });
      continue;
    }
    if (await portInUse(proc.port)) {
      // Someone else's workstream may own this. Never reclaim it.
      alreadyUp.push(proc);
      continue;
    }
    if (!statusOnly) start(proc);
    started.push(proc);
  }

  headline("Processes");
  for (const proc of started) {
    note(`${paint(32, statusOnly ? "free   " : "start  ")} ${proc.name.padEnd(LABEL_WIDTH)} :${proc.port}  ${dim(proc.describe)}`);
  }
  for (const proc of alreadyUp) {
    note(`${paint(33, "running")} ${proc.name.padEnd(LABEL_WIDTH)} :${proc.port}  ${dim("already listening — left untouched")}`);
  }
  for (const { proc, reason } of skipped) {
    note(`${paint(31, "skipped")} ${proc.name.padEnd(LABEL_WIDTH)} :${proc.port}  ${dim(reason)}`);
  }

  if (statusOnly) return;
  if (started.length === 0) {
    headline("Nothing to start — everything selected is already running or unavailable.");
    return;
  }

  // Report the URLs only once the web apps genuinely answer, so the summary is
  // not a promise the browser will immediately break.
  const webApps = [...started, ...alreadyUp].filter((p) => p.kind === "web");
  await Promise.all(webApps.map((p) => waitForHttp(p.port, 90_000)));

  headline("Open");
  note(`${paint(1, "http://localhost:3100")}  ${dim("ForKhatri entrance — sign in here, then enter a module")}`);
  for (const proc of webApps.filter((p) => p.port !== 3100)) {
    note(`${paint(1, `http://localhost:${proc.port}`.padEnd(21))}  ${dim(proc.describe)}`);
  }
  note("");
  note(dim('Sign in: avatar -> "Act as (development)", or the "Development: act as..." link when signed out.'));
  note(dim("Ctrl+C stops only the processes this launcher started."));
  process.stdout.write("\n");
}

main().catch((err) => {
  console.error(err);
  stopAll();
});

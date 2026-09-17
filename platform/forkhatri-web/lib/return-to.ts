/**
 * TR17 return-to handling: follow `return_to` only when its origin equals the
 * entrance origin or the origin of a registry `entry_url`. Anything else is
 * ignored (open-redirect prevention).
 */
import type { ModuleEntry } from "./api";

const BOUNCE_KEY = "fk.returnTo.bounce";
const BOUNCE_WINDOW_MS = 20_000;

export function readReturnTo(): string | null {
  if (typeof window === "undefined") return null;
  return new URLSearchParams(window.location.search).get("return_to");
}

export function safeReturnTo(raw: string | null, modules: ModuleEntry[]): URL | null {
  if (!raw) return null;
  let target: URL;
  try {
    target = new URL(raw, window.location.origin);
  } catch {
    return null;
  }
  if (target.protocol !== "http:" && target.protocol !== "https:") return null;

  const allowed = new Set<string>([window.location.origin]);
  for (const entry of modules) {
    if (!entry.entry_url) continue;
    try {
      allowed.add(new URL(entry.entry_url).origin);
    } catch {
      // A malformed registry URL simply contributes no origin.
    }
  }
  return allowed.has(target.origin) ? target : null;
}

/** The module a return target belongs to, for "Sign in to continue to Milavn". */
export function moduleForTarget(target: URL, modules: ModuleEntry[]): ModuleEntry | null {
  return (
    modules.find((module) => {
      if (!module.entry_url) return false;
      try {
        return new URL(module.entry_url).origin === target.origin;
      } catch {
        return false;
      }
    }) ?? null
  );
}

/** Removes `return_to` from the address bar once it has been followed or ignored. */
export function clearReturnTo() {
  const url = new URL(window.location.href);
  if (!url.searchParams.has("return_to")) return;
  url.searchParams.delete("return_to");
  window.history.replaceState(window.history.state, "", url.pathname + url.search + url.hash);
}

/**
 * Loop guard for a member who arrives already signed in: if we sent them to the
 * same target moments ago and they came straight back, the module is not
 * accepting the session, so stay on the hub instead of bouncing forever.
 */
export function isBounceLoop(target: URL): boolean {
  try {
    const previous = JSON.parse(sessionStorage.getItem(BOUNCE_KEY) ?? "null") as { href: string; at: number } | null;
    return !!previous && previous.href === target.href && Date.now() - previous.at < BOUNCE_WINDOW_MS;
  } catch {
    return false;
  }
}

export function markBounce(target: URL) {
  try {
    sessionStorage.setItem(BOUNCE_KEY, JSON.stringify({ href: target.href, at: Date.now() }));
  } catch {
    // Storage blocked: the guard just does not apply.
  }
}

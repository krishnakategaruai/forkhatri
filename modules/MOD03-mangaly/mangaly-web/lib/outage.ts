/* One shared "cannot reach Mangaly right now" signal.
 *
 * [ForKhatri TR15/TR16, 2026-09-14] When MangalyService is unreachable, or
 * answers 502/503/504 (503 is also what it returns when the ForKhatri identity
 * service cannot be reached), a screen that is LOADING must not sit on
 * "Loading…" forever — and must never treat it as "signed out", which would
 * bounce a signed-in member through the entrance and straight back in a loop.
 *
 * Reads (GET) report here; `OutageGate` in the root layout then replaces the
 * screen with one calm retry state. Mutations (POST/PATCH/DELETE) do not:
 * they keep their existing inline error so a half-filled form keeps its input.
 *
 * Retry is a full reload of the URL the member was on when the outage was
 * first seen — not of wherever a page's fallback routing may have sent them
 * in the meantime (e.g. a failed profile read routing to /profile/create). */

type Listener = () => void;

let outageHref: string | null = null;
const listeners = new Set<Listener>();

export function reportOutage(): void {
  if (typeof window === 'undefined' || outageHref !== null) return;
  outageHref = window.location.href;
  listeners.forEach((listener) => listener());
}

export function isOutage(): boolean {
  return outageHref !== null;
}

export function subscribeOutage(listener: Listener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function retryAfterOutage(): void {
  if (typeof window === 'undefined') return;
  window.location.assign(outageHref ?? window.location.href);
}

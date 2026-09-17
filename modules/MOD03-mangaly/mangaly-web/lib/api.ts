/* Thin REST/JSON client for MangalyService.
 *
 * ADR-014 fixes REST/JSON as the contract between this web client and the
 * backend, so this stays a plain fetch wrapper — no GraphQL layer, no client
 * -side ORM. Every mutation helper added later must send an idempotency key
 * (TR102), which is why that lives here rather than per call site. */

import { reportOutage } from './outage';
import { redirectToEntrance } from './platform';

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000';

export type BackendHealth = {
  status: string;
  database?: string;
  schemas?: number;
  tables?: number;
  version?: string;
};

export type HealthResult =
  | { state: 'ok'; data: BackendHealth }
  | { state: 'down'; reason: string };

export async function getHealth(signal?: AbortSignal): Promise<HealthResult> {
  try {
    const res = await fetch(`${API_BASE}/health`, {
      signal,
      cache: 'no-store',
    });
    if (!res.ok) {
      return { state: 'down', reason: `HTTP ${res.status}` };
    }
    return { state: 'ok', data: (await res.json()) as BackendHealth };
  } catch (err) {
    // The backend simply not running yet is the expected case during the
    // early build, so this is a normal state to render, not an error to throw.
    return {
      state: 'down',
      reason: err instanceof Error ? err.message : 'unreachable',
    };
  }
}

/**
 * [ForKhatri TR16, 2026-09-14] Every MangalyService call goes through here:
 * `credentials: 'include'` so the HttpOnly ForKhatri session cookie rides
 * along, and a 401 hands the member to the ForKhatri entrance (with
 * `return_to`) instead of leaving a screen silently empty. Only a 401 does
 * that — a 503 means "cannot check right now", not "signed out".
 *
 * A READ that cannot reach the service (network error, 502/503/504) reports an
 * outage, which swaps the screen for the shared retry state (`lib/outage.ts`).
 * Mutations keep their own inline errors. Callers still see the same
 * Response/exception as before.
 */
const OUTAGE_STATUSES = new Set([502, 503, 504]);

export async function apiFetch(input: string, init: RequestInit = {}): Promise<Response> {
  const isRead = (init.method ?? 'GET').toUpperCase() === 'GET';
  let res: Response;
  try {
    res = await fetch(input, { ...init, credentials: 'include' });
  } catch (err) {
    if (isRead && !(err instanceof DOMException && err.name === 'AbortError')) reportOutage();
    throw err;
  }
  if (res.status === 401) redirectToEntrance();
  else if (isRead && OUTAGE_STATUSES.has(res.status)) reportOutage();
  return res;
}

/** Client-generated idempotency key for queueable mutations (TR102/SP102). */
export function newIdempotencyKey(): string {
  return crypto.randomUUID();
}

/**
 * [Bug found live, 2026-09-13] `profile.photo_url` (and any other server-
 * returned media path) is a path relative to the API's own origin
 * (`/media/...`, served by `components/profile/storage.py`'s local-disk
 * stand-in), not the frontend's. Rendered as-is in an `<img src>`, the
 * browser resolved it against `localhost:3000` instead of `localhost:8000`
 * and 404'd — found by checking the actual network tab, not by reading the
 * component. Every render site must go through this rather than use a
 * server-returned media path directly.
 */
export function resolveMediaUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  if (path.startsWith('http://') || path.startsWith('https://')) return path;
  return `${API_BASE}${path}`;
}

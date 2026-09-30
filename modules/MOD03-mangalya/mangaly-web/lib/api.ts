/* Thin REST/JSON client for MangalyService.
 *
 * ADR-014 fixes REST/JSON as the contract between this web client and the
 * backend, so this stays a plain fetch wrapper — no GraphQL layer, no client
 * -side ORM. Every mutation helper added later must send an idempotency key
 * (TR102), which is why that lives here rather than per call site.
 *
 * [2026-09-17 rework] The per-module `getJson`/`sendJson`/`del` copies that
 * every `lib/*.ts` file used to carry now live here once, so a new API client
 * (shortlist, safety, notifications) is a handful of lines. */

import { reportOutage } from './outage';
import { redirectToEntrance } from './platform';
import { getI18n } from './i18n/config';

function resolveApiBase(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000';
  if (typeof window === 'undefined') return configured;
  // Development only: `p1.localhost:3000`, `c2.localhost:3000` … are separate
  // cookie jars inside ONE Chrome window (cookies are kept per host), so a
  // whole family can be signed in side by side as tabs. Each tab must then
  // reach the API on its own host, or every tab would send the same cookie.
  const host = window.location.hostname;
  if (host.endsWith('.localhost')) {
    try {
      const url = new URL(configured);
      if (url.hostname === 'localhost') {
        url.hostname = host;
        return url.toString().replace(/\/$/, '');
      }
    } catch {
      /* a malformed value falls through to the configured one */
    }
  }
  return configured;
}

export const API_BASE = resolveApiBase();

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

/** [ADR-010] Every request tells the server which language to localize
 *  `detail` text in. */
export function currentLanguageHeader(): Record<string, string> {
  try {
    return { 'X-Mangalya-Language': getI18n().language };
  } catch {
    return {};
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

/* [DEC-V1-019] While a parent is filling in a profile they created for their
 * son or daughter, profile and photo calls carry `X-Mangalya-Manage`. The
 * server honours it only on /profile and /media, only for a profile this
 * caller created and the candidate has not taken over — everything else runs
 * as the parent, whatever the header says. */
let managingFor: string | null = null;
export function setManaging(accountId: string | null): void {
  managingFor = accountId;
}
export function currentlyManaging(): string | null {
  return managingFor;
}

export async function apiFetch(input: string, init: RequestInit = {}): Promise<Response> {
  const isRead = (init.method ?? 'GET').toUpperCase() === 'GET';
  let res: Response;
  if (managingFor) {
    const headers = new Headers(init.headers);
    headers.set('X-Mangalya-Manage', managingFor);
    init = { ...init, headers };
  }
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
  // Already resolved once (a same-origin base such as the tunnel's
  // "/tunnel-proxy/api"): prefixing again gave ".../tunnel-proxy/api/tunnel-proxy/api/media/…".
  if (API_BASE && path.startsWith(`${API_BASE}/`)) return path;
  return `${API_BASE}${path}`;
}

/* ---------- Shared JSON helpers ---------- */

export type Outcome<T> = { ok: true; data: T } | { ok: false; status: number; message?: string };

/** GET a JSON body; `null` for any non-2xx or unreachable answer. */
export async function getJson<T>(path: string): Promise<T | null> {
  try {
    const res = await apiFetch(`${API_BASE}${path}`, {
      cache: 'no-store',
      headers: currentLanguageHeader(),
    });
    if (!res.ok) return null;
    const text = await res.text();
    return text ? (JSON.parse(text) as T) : null;
  } catch {
    return null;
  }
}

/** POST/PATCH/DELETE a JSON body; carries the server's localized `detail`. */
export async function sendJson<T>(
  method: 'POST' | 'PATCH' | 'DELETE' | 'PUT',
  path: string,
  body?: unknown
): Promise<Outcome<T>> {
  let res: Response;
  try {
    res = await apiFetch(`${API_BASE}${path}`, {
      method,
      headers: { 'Content-Type': 'application/json', ...currentLanguageHeader() },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    return { ok: false, status: 0 };
  }
  const text = await res.text();
  let parsed: unknown = null;
  try {
    parsed = text ? JSON.parse(text) : null;
  } catch {
    parsed = null;
  }
  if (!res.ok) {
    const detail = (parsed as { detail?: unknown } | null)?.detail;
    // Plain `detail` text, or the `{code, message}` shape several routes use.
    const nested = (detail as { message?: unknown } | null)?.message;
    return {
      ok: false,
      status: res.status,
      message:
        typeof detail === 'string'
          ? detail
          : typeof nested === 'string'
            ? nested
            : undefined,
    };
  }
  return { ok: true, data: parsed as T };
}

export function postJson<T>(path: string, body?: unknown): Promise<Outcome<T>> {
  return sendJson<T>('POST', path, body);
}

export function deleteJson<T = null>(path: string, body?: unknown): Promise<Outcome<T>> {
  return sendJson<T>('DELETE', path, body);
}

/** Builds `?a=1&b=2` from a plain object, skipping empty values; arrays repeat the key. */
export function query(params: Record<string, string | number | boolean | string[] | undefined | null>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === '' || value === false) continue;
    if (Array.isArray(value)) value.forEach((v) => search.append(key, v));
    else search.set(key, String(value));
  }
  const s = search.toString();
  return s ? `?${s}` : '';
}

/* Thin REST/JSON client for the Milavn service (ADR-014).
 *
 * Every call carries the acting member (dev stand-in for the ForKhatri
 * platform session — see lib/identity.tsx) and the resolved UI language.
 * Client-queueable mutations send an Idempotency-Key (TR-CROSSCUT-01). */

import { withBasePath } from './base-path';

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8001';

export class ApiError extends Error {
  status: number;
  detail: unknown;
  constructor(status: number, detail: unknown) {
    super(typeof detail === 'string' ? detail : (detail as { message?: string })?.message ?? `HTTP ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

let language = 'en';
export function setApiLanguage(lang: string) { language = lang; }

/* Fired when the API says the ForKhatri session is gone (401), so the identity
 * provider can drop the member and the shell can send them to the entrance. */
export const UNAUTHORIZED_EVENT = 'milavn:unauthorized';

export function newIdempotencyKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;
}

type Opts = { method?: string; body?: unknown; idempotent?: boolean; form?: FormData; signal?: AbortSignal };

export async function api<T = unknown>(path: string, opts: Opts = {}): Promise<T> {
  const headers: Record<string, string> = { 'X-Milavn-Language': language };
  if (opts.body !== undefined) headers['Content-Type'] = 'application/json';
  if (opts.idempotent) headers['Idempotency-Key'] = newIdempotencyKey();
  const res = await fetch(`${API_BASE}${path}`, {
    method: opts.method ?? (opts.body !== undefined || opts.form ? 'POST' : 'GET'),
    headers,
    body: opts.form ?? (opts.body !== undefined ? JSON.stringify(opts.body) : undefined),
    signal: opts.signal,
    cache: 'no-store',
    // The member is the ForKhatri session cookie (TR16) — never a header this client sets.
    credentials: 'include',
  });
  if (res.status === 204) return undefined as T;
  const text = await res.text();
  let data: { detail?: unknown } | null = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = null; }
  if (res.status === 401 && typeof window !== 'undefined') window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
  if (!res.ok) throw new ApiError(res.status, data?.detail ?? data);
  return data as unknown as T;
}

export function resolveMediaUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  if (path.startsWith('http')) return path;
  if (path.startsWith('/media/')) return `${API_BASE}${path}`;
  return withBasePath(path); // /assets/... served by this web app (under its zone prefix)
}

/* ---------- Types (mirror the API's card contract, FR006) ---------- */
export type Card = {
  id: string; slug: string; title: string; intent_category: string; category_label: string;
  time_start: string; time_end: string | null; location_label: string; distance_label: string | null;
  host_member_id: string; host_name: string; host_avatar: string | null;
  going_count: number; interested_count: number; capacity: number | null; spots_left: number | null;
  trust_level: string; trust_label: string; trust_positive: boolean;
  why_reason: string; why_factor: string; viewer_status: string | null;
  cover_image_url: string | null; visibility_scope: string; circle_id: string | null;
  high_risk: boolean; status: string; is_recurring: boolean; lat: number | null; lng: number | null;
  price_paise?: number | null; // FR102: null = free
  audience_tags?: string[]; food_tags?: string[]; // FR110: who it's for, food and drink
};

export type Profile = {
  member_id: string; locality_city: string; locality_zone: string | null; locality_locality: string | null;
  language_preference: string; interests: string[]; interest_labels: string[]; bio: string | null; photo_url: string | null;
};

export type Identity = { member_id: string; display_name: string; handle: string; avatar: string | null; scopes: string[] };

export type Circle = {
  id: string; name: string; circle_type: string; type_label: string; description: string | null;
  created_by_member_id: string; created_at: string; member_count: number; viewer_role: string | null; is_open: boolean;
  locality_city?: string | null; locality_locality?: string | null; locality_label?: string | null; near_you?: boolean;
};

export type AroundYou = { today: Card[]; tomorrow: Card[]; weekend: Card[]; later: Card[]; circles: { id: string; name: string; circle_type: string; member_count: number }[]; viewer_locality: string };

export const getProfile = () => api<Profile | null>('/profile/me');
export const getAroundYou = () => api<AroundYou>('/discovery/around-you');
export const getIdentity = () => api<Identity>('/identity/me');
export const getDevMembers = () => api<Identity[]>('/identity/dev/members');
export const getUnread = () => api<{ unread: number }>('/notifications/unread-count');

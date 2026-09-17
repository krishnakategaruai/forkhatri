/* Profile calls against MangalyService — FR001.
 *
 * `multipart/form-data`, not JSON: a photo is part of the existence tier
 * (DEC-V1-001), not an optional extra, so the create call always carries a
 * file. `credentials: 'include'` for the same HttpOnly-cookie reason every
 * other authenticated call in this app uses. */

import { API_BASE, apiFetch } from './api';
import { getI18n } from './i18n/config';

export type Profile = {
  id: string;
  name: string;
  date_of_birth: string;
  gender: string;
  city_locality: string;
  photo_url: string | null;
};

export type CreateProfileInput = {
  lookingFor: 'bride' | 'groom';
  name: string;
  dateOfBirth: string; // YYYY-MM-DD
  gender: string;
  cityLocality: string;
  photo: File;
};

export type CreateProfileOutcome =
  | { ok: true; data: Profile }
  | { ok: false; kind: 'missingFields'; fields: string[]; message: string }
  | { ok: false; kind: 'rejected' | 'network'; message?: string };

function currentLanguageHeader(): Record<string, string> {
  try {
    return { 'X-Mangaly-Language': getI18n().language };
  } catch {
    return {};
  }
}

export async function createProfile(input: CreateProfileInput): Promise<CreateProfileOutcome> {
  const form = new FormData();
  form.set('name', input.name);
  form.set('date_of_birth', input.dateOfBirth);
  form.set('gender', input.gender);
  form.set('city_locality', input.cityLocality);
  form.set('looking_for', input.lookingFor);
  form.set('photo', input.photo);

  let res: Response;
  try {
    res = await apiFetch(`${API_BASE}/profile`, {
      method: 'POST',
      credentials: 'include',
      headers: currentLanguageHeader(),
      body: form,
    });
  } catch {
    return { ok: false, kind: 'network' };
  }

  if (res.ok) {
    return { ok: true, data: (await res.json()) as Profile };
  }

  const body = await res.json().catch(() => null);
  if (res.status === 422 && body && Array.isArray(body.detail?.fields)) {
    return { ok: false, kind: 'missingFields', fields: body.detail.fields, message: body.detail.message };
  }
  const message: string | undefined =
    typeof body?.detail === 'string' ? body.detail : undefined;
  return { ok: false, kind: 'rejected', message };
}

/** Whether the signed-in caller has a saved profile yet — null means no. */
export async function getOwnProfile(): Promise<Profile | null> {
  try {
    const res = await apiFetch(`${API_BASE}/profile/me`, {
      credentials: 'include',
      cache: 'no-store',
      headers: currentLanguageHeader(),
    });
    if (!res.ok) return null;
    const text = await res.text();
    return text ? (JSON.parse(text) as Profile) : null;
  } catch {
    return null;
  }
}

export type Photo = { id: string; url: string; is_primary: boolean };
export type PhotoOutcome = { ok: true } | { ok: false; message?: string };

async function photoRequest(path: string, init: RequestInit): Promise<PhotoOutcome> {
  try {
    const res = await apiFetch(`${API_BASE}${path}`, {
      credentials: 'include',
      headers: currentLanguageHeader(),
      ...init,
    });
    if (res.ok) return { ok: true };
    const body = await res.json().catch(() => null);
    return { ok: false, message: typeof body?.detail === 'string' ? body.detail : undefined };
  } catch {
    return { ok: false };
  }
}

/** The caller's own photos, main photo first. */
export async function listPhotos(): Promise<Photo[]> {
  try {
    const res = await apiFetch(`${API_BASE}/profile/photos`, {
      credentials: 'include',
      cache: 'no-store',
      headers: currentLanguageHeader(),
    });
    if (!res.ok) return [];
    return (await res.json()) as Photo[];
  } catch {
    return [];
  }
}

export function uploadPhoto(file: File): Promise<PhotoOutcome> {
  const form = new FormData();
  form.set('photo', file);
  return photoRequest('/profile/photos', { method: 'POST', body: form });
}

export function deletePhoto(id: string): Promise<PhotoOutcome> {
  return photoRequest(`/profile/photos/${id}`, { method: 'DELETE' });
}

export function setPrimaryPhoto(id: string): Promise<PhotoOutcome> {
  return photoRequest(`/profile/photos/${id}/primary`, { method: 'POST' });
}

/** Save a full photo order; the first id becomes the main photo. */
export function reorderPhotos(ids: string[]): Promise<PhotoOutcome> {
  return photoRequest('/profile/photos/order', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', ...currentLanguageHeader() },
    body: JSON.stringify({ ids }),
  });
}

/** [FR021] View ANY account's profile, not just the caller's own — returns
 * `null` both when it doesn't exist and when the caller isn't authorized to
 * see it yet (self, or an accepted-connection grant); the two are
 * deliberately indistinguishable from here (same anti-enumeration shape
 * every other lookup in this app uses). */
export async function viewProfile(accountId: string): Promise<Profile | null> {
  try {
    const res = await apiFetch(`${API_BASE}/profile/view/${accountId}`, {
      credentials: 'include',
      cache: 'no-store',
      headers: currentLanguageHeader(),
    });
    if (!res.ok) return null;
    const text = await res.text();
    return text ? (JSON.parse(text) as Profile) : null;
  } catch {
    return null;
  }
}

export type ProfileView = {
  profile: Profile;
  photos: Photo[];
  attributes: Record<string, Record<string, AttributeValue>>;
  /** Heard only by an accepted connection (migration 029). */
  voice_intro_url?: string | null;
};

/** The spoken introduction on the caller's own profile. One clip: recording
 * again replaces it. */
export async function recordVoiceIntro(
  clip: Blob
): Promise<{ ok: true; data: { voice_intro_url: string | null } } | { ok: false; status: number; message?: string }> {
  const form = new FormData();
  form.set('clip', clip, 'voice-intro.webm');
  try {
    const res = await apiFetch(`${API_BASE}/profile/voice-intro`, {
      method: 'POST',
      credentials: 'include',
      body: form,
      headers: currentLanguageHeader(),
    });
    const text = await res.text();
    const parsed = text ? JSON.parse(text) : null;
    if (!res.ok) {
      return { ok: false, status: res.status, message: typeof parsed?.detail === 'string' ? parsed.detail : undefined };
    }
    return { ok: true, data: parsed as { voice_intro_url: string | null } };
  } catch {
    return { ok: false, status: 0 };
  }
}

export async function getVoiceIntro(): Promise<string | null> {
  try {
    const res = await apiFetch(`${API_BASE}/profile/voice-intro`, {
      credentials: 'include',
      cache: 'no-store',
      headers: currentLanguageHeader(),
    });
    if (!res.ok) return null;
    const text = await res.text();
    return text ? ((JSON.parse(text) as { voice_intro_url: string | null }).voice_intro_url ?? null) : null;
  } catch {
    return null;
  }
}

export async function deleteVoiceIntro(): Promise<{ ok: boolean }> {
  try {
    const res = await apiFetch(`${API_BASE}/profile/voice-intro`, {
      method: 'DELETE',
      credentials: 'include',
      headers: currentLanguageHeader(),
    });
    return { ok: res.ok };
  } catch {
    return { ok: false };
  }
}

/** [DEC-V1-020] A searchable candidate as any signed-in member may see them:
 * the matrimonial facts and the main photo, never the name or contact. */
export type PublicProfile = {
  account_id: string;
  age: number | null;
  locality: string | null;
  photo_url: string | null;
  education_level: string | null;
  profession: string | null;
  attributes: Record<string, Record<string, AttributeValue>>;
};

export async function viewPublicProfile(accountId: string): Promise<PublicProfile | null> {
  try {
    const res = await apiFetch(`${API_BASE}/profile/view/${accountId}/public`, {
      credentials: 'include',
      cache: 'no-store',
      headers: currentLanguageHeader(),
    });
    if (!res.ok) return null;
    const text = await res.text();
    return text ? (JSON.parse(text) as PublicProfile) : null;
  } catch {
    return null;
  }
}

/** [FR020/FR021] Everything an authorized viewer may see in one response;
 * `null` until the two members are connected. */
export async function viewProfileFull(accountId: string): Promise<ProfileView | null> {
  try {
    const res = await apiFetch(`${API_BASE}/profile/view/${accountId}/full`, {
      credentials: 'include',
      cache: 'no-store',
      headers: currentLanguageHeader(),
    });
    if (!res.ok) return null;
    const text = await res.text();
    return text ? (JSON.parse(text) as ProfileView) : null;
  } catch {
    return null;
  }
}

/* FR002/FR003/FR005 — per-category tri-state attributes and the three-tier
 * completeness read. `state` mirrors the backend's `field_state` enum
 * exactly: 'declined' is a first-class fact, never collapsed into 'unset'. */

export type AttributeState = 'unset' | 'declined' | 'value';

export type AttributeValue = string | number | boolean | string[] | Record<string, unknown> | null;

export type CompletenessReport = {
  existence_complete: boolean;
  discoverability_complete: boolean;
  discoverability_missing: string[];
  enhanced_filled_categories: number;
  enhanced_total_categories: number;
};

export async function getCompleteness(): Promise<CompletenessReport | null> {
  try {
    const res = await apiFetch(`${API_BASE}/profile/completeness`, {
      credentials: 'include',
      cache: 'no-store',
      headers: currentLanguageHeader(),
    });
    if (!res.ok) return null;
    return (await res.json()) as CompletenessReport;
  } catch {
    return null;
  }
}

export type UpdateCategoryOutcome = { ok: true } | { ok: false; kind: 'rejected' | 'network' };

/** One PATCH per category (UX02's per-category editing screens) — never one
 * PATCH per field, matching the backend's own transaction boundary. */
export async function updateCategoryAttributes(
  category: string,
  attributes: Record<string, { state: AttributeState; value?: AttributeValue }>
): Promise<UpdateCategoryOutcome> {
  try {
    const res = await apiFetch(`${API_BASE}/profile/${category}`, {
      method: 'PATCH',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', ...currentLanguageHeader() },
      body: JSON.stringify(attributes),
    });
    return res.ok ? { ok: true } : { ok: false, kind: 'rejected' };
  } catch {
    return { ok: false, kind: 'network' };
  }
}

/** Every saved attribute's state, grouped by category — one call for the
 * whole Profile edit hub's category cards rather than one per category. */
export async function getAllAttributes(): Promise<Record<string, Record<string, AttributeState>>> {
  try {
    const res = await apiFetch(`${API_BASE}/profile/attributes`, {
      credentials: 'include',
      cache: 'no-store',
      headers: currentLanguageHeader(),
    });
    if (!res.ok) return {};
    return (await res.json()) as Record<string, Record<string, AttributeState>>;
  } catch {
    return {};
  }
}

export type CategoryAttributes = Record<string, { state: AttributeState; value: AttributeValue }>;

/** Own attributes with values, grouped by category — powers the Profile
 * hub's value badges and its Edit/Preview toggle in one request. */
export async function getAllAttributeValues(): Promise<Record<string, CategoryAttributes>> {
  try {
    const res = await apiFetch(`${API_BASE}/profile/attributes/full`, {
      credentials: 'include',
      cache: 'no-store',
      headers: currentLanguageHeader(),
    });
    if (!res.ok) return {};
    return (await res.json()) as Record<string, CategoryAttributes>;
  } catch {
    return {};
  }
}

/** The caller's own saved attribute states for one category — pre-fills the
 * editor so re-opening a category shows what was actually saved, rather than
 * a blank form that would silently re-prompt an already-answered question. */
export async function getCategoryAttributes(category: string): Promise<CategoryAttributes> {
  try {
    const res = await apiFetch(`${API_BASE}/profile/${category}`, {
      credentials: 'include',
      cache: 'no-store',
      headers: currentLanguageHeader(),
    });
    if (!res.ok) return {};
    return (await res.json()) as CategoryAttributes;
  } catch {
    return {};
  }
}

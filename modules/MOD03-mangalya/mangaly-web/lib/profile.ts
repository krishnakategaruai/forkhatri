/* Profile calls against MangalyService — FR001.
 *
 * `multipart/form-data`, not JSON: a photo is part of the existence tier
 * (DEC-V1-001), not an optional extra, so the create call always carries a
 * file. `credentials: 'include'` for the same HttpOnly-cookie reason every
 * other authenticated call in this app uses. */

import { API_BASE, apiFetch, currentLanguageHeader, getJson, query, sendJson, type Outcome } from './api';

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
  educationLevel?: string;
  occupation?: string;
  maritalStatus?: string;
  relocationWillingness?: string;
};

function setFirstDetails(form: FormData, input: CreateProfileInput) {
  if (input.educationLevel) form.set('education_level', input.educationLevel);
  if (input.occupation?.trim()) form.set('occupation', input.occupation.trim());
  if (input.maritalStatus) form.set('marital_status', input.maritalStatus);
  if (input.relocationWillingness) form.set('relocation_willingness', input.relocationWillingness);
}

export type CreateProfileOutcome =
  | { ok: true; data: Profile }
  | { ok: false; kind: 'missingFields'; fields: string[]; message: string }
  | { ok: false; kind: 'rejected' | 'network'; message?: string };

export async function createProfile(input: CreateProfileInput): Promise<CreateProfileOutcome> {
  const form = new FormData();
  form.set('name', input.name);
  form.set('date_of_birth', input.dateOfBirth);
  form.set('gender', input.gender);
  form.set('city_locality', input.cityLocality);
  form.set('looking_for', input.lookingFor);
  form.set('photo', input.photo);
  setFirstDetails(form, input);

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

/** [DEC-V1-019] A parent creates their son's or daughter's profile. */
export async function createProfileForChild(
  input: CreateProfileInput & { childPhone: string; relation: string },
): Promise<{ ok: true; accountId: string } | { ok: false; kind: 'rejected' | 'network'; message?: string }> {
  const form = new FormData();
  form.set('child_phone', input.childPhone);
  form.set('relation', input.relation);
  form.set('name', input.name);
  form.set('date_of_birth', input.dateOfBirth);
  form.set('gender', input.gender);
  form.set('city_locality', input.cityLocality);
  form.set('looking_for', input.lookingFor);
  form.set('photo', input.photo);
  setFirstDetails(form, input);
  let res: Response;
  try {
    res = await apiFetch(`${API_BASE}/profile/managed`, {
      method: 'POST',
      headers: currentLanguageHeader(),
      body: form,
    });
  } catch {
    return { ok: false, kind: 'network' };
  }
  const body = await res.json().catch(() => null);
  if (res.ok && body?.account_id) return { ok: true, accountId: String(body.account_id) };
  // [DEC-V1-025] The maker gate answers {code: 'verification_required', message}.
  const detail = body?.detail;
  return {
    ok: false,
    kind: 'rejected',
    message:
      typeof detail === 'string'
        ? detail
        : typeof detail?.message === 'string'
          ? detail.message
          : undefined,
  };
}

export type ManagedProfile = {
  account_id: string;
  name: string;
  photo_url: string | null;
  phone_masked: string | null;
};

export async function listManagedProfiles(): Promise<ManagedProfile[]> {
  try {
    const res = await apiFetch(`${API_BASE}/profile/managed`, { cache: 'no-store', headers: currentLanguageHeader() });
    return res.ok ? ((await res.json()) as ManagedProfile[]) : [];
  } catch {
    return [];
  }
}

/** "This isn't me": remove a profile someone else made with my number. */
export async function disownProfile(): Promise<boolean> {
  try {
    const res = await apiFetch(`${API_BASE}/profile/disown`, { method: 'POST', headers: currentLanguageHeader() });
    return res.ok;
  } catch {
    return false;
  }
}

/** The candidate takes over a profile made for them. */
export async function claimProfile(): Promise<boolean> {
  try {
    const res = await apiFetch(`${API_BASE}/profile/claim`, { method: 'POST', headers: currentLanguageHeader() });
    return res.ok;
  } catch {
    return false;
  }
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
  /** [Migration 043] What this person chose to show openly. */
  open_name?: string | null;
  open_photo_urls?: string[];
  /** Full name, for a parent or guardian whose candidate is connected with them. */
  name?: string | null;
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

/* ---------- [2026-09-17 rework, contract §2] The two profile lenses ---------- */

export type Lens = 'story' | 'biodata';

export type BiodataRow = { key: string; label: string; value: string };
export type BiodataSection = { id: string; title?: string | null; rows: BiodataRow[] };

export type StoryBlock =
  | { kind: 'photo'; url: string }
  | { kind: 'prompt'; q: string; a: string }
  | { kind: 'section'; id: string; title?: string | null; rows: BiodataRow[] }
  | { kind: 'voice'; url: string };

/** What the profile screen renders, whichever lens the server answered in.
 * `sections` is always present (biodata order); `blocks` only when the server
 * built the story itself — otherwise the screen interleaves photos, prompts
 * and sections client-side. */
export type LensView = {
  lens: Lens;
  profile_id: string;
  account_id: string;
  /** Null until the disclosure rules allow the name. */
  name: string | null;
  age: number | null;
  locality: string | null;
  gender?: string | null;
  height_cm?: number | null;
  education_level?: string | null;
  profession?: string | null;
  photo_url: string | null;
  photos: string[];
  sections: BiodataSection[];
  blocks: StoryBlock[] | null;
  prompts: { q: string; a: string }[];
  voice_intro_url: string | null;
  /** 'connected' ⇒ name, contact and every photo may be shown. */
  disclosure: 'public' | 'connected';
  connection: { id: string; status: string } | null;
  shortlisted: boolean;
  blocked?: boolean;
  /** The raw attributes, for screens that still read categories directly. */
  attributes: Record<string, Record<string, AttributeValue>>;
  /** True when the server answered nothing at all (blocked, gone, or not permitted). */
  empty?: boolean;
};

/* `photos` is omitted from the `LensView` half before widening it: the
 * intersection would otherwise be `string[] & (Photo | string)[]`, whose
 * element type collapses to `string`, and the object branch below would be
 * unreachable even though the server does send photo objects. */
type ServerLens = Omit<Partial<LensView>, 'photos'> & {
  profile?: Profile | null;
  photos?: (Photo | string)[];
  attributes?: Record<string, Record<string, AttributeValue>>;
  connection_id?: string | null;
  connection_status?: string | null;
};

function ageFromDob(dob: string | undefined | null): number | null {
  if (!dob) return null;
  const birth = new Date(dob);
  if (Number.isNaN(birth.getTime())) return null;
  const now = new Date();
  let age = now.getFullYear() - birth.getFullYear();
  if (now.getMonth() < birth.getMonth() || (now.getMonth() === birth.getMonth() && now.getDate() < birth.getDate())) {
    age -= 1;
  }
  return age;
}

function normalizeLens(raw: ServerLens, lens: Lens, id: string): LensView {
  const photos = (raw.photos ?? []).map((p) => (typeof p === 'string' ? p : p.url)).filter(Boolean);
  const attributes = raw.attributes ?? {};
  const promptRows = attributes['in_my_words'] ?? {};
  const prompts =
    raw.prompts ??
    Object.values(promptRows)
      .filter((v): v is { q: string; a: string } => !!v && typeof v === 'object' && 'q' in v && 'a' in v)
      .map((v) => ({ q: String(v.q), a: String(v.a) }));
  const primary = raw.photo_url ?? raw.profile?.photo_url ?? photos[0] ?? null;
  const connection =
    raw.connection ??
    (raw.connection_id ? { id: raw.connection_id, status: raw.connection_status ?? 'accepted' } : null);
  return {
    lens: raw.lens ?? lens,
    profile_id: raw.profile_id ?? raw.profile?.id ?? id,
    account_id: raw.account_id ?? id,
    name: raw.name ?? raw.profile?.name ?? null,
    age: raw.age ?? ageFromDob(raw.profile?.date_of_birth),
    locality: raw.locality ?? raw.profile?.city_locality ?? null,
    gender: raw.gender ?? raw.profile?.gender ?? null,
    height_cm: raw.height_cm ?? null,
    education_level: raw.education_level ?? null,
    profession: raw.profession ?? null,
    photo_url: primary,
    photos: photos.length ? photos : primary ? [primary] : [],
    sections: raw.sections ?? [],
    blocks: raw.blocks ?? null,
    prompts,
    voice_intro_url: raw.voice_intro_url ?? null,
    disclosure: raw.disclosure ?? (raw.name || raw.profile?.name ? 'connected' : 'public'),
    connection,
    shortlisted: !!raw.shortlisted,
    blocked: raw.blocked,
    attributes,
  };
}

/** `GET /profile/view/{id}?lens=story|biodata&for_candidate=` — one call, both
 * lenses, same disclosure rules. Older servers answer the `/full` (connected)
 * or `/public` (searchable) shapes instead; both normalize to `LensView`. */
export async function viewProfileLens(
  id: string,
  options: { lens: Lens; forCandidate?: string }
): Promise<LensView> {
  const qs = query({ lens: options.lens, for_candidate: options.forCandidate });
  const fresh = await getJson<ServerLens>(`/profile/view/${id}${qs}`);
  if (fresh && (fresh.sections || fresh.blocks || fresh.disclosure || fresh.attributes)) {
    return normalizeLens(fresh, options.lens, id);
  }
  const full = await getJson<ServerLens>(`/profile/view/${id}/full`);
  if (full) return normalizeLens({ ...full, disclosure: 'connected' }, options.lens, id);
  const pub = await getJson<ServerLens>(`/profile/view/${id}/public`);
  if (pub) return normalizeLens({ ...pub, disclosure: 'public' }, options.lens, id);
  return { ...normalizeLens({}, options.lens, id), empty: true };
}

/* [Migration 047 / DEC-V1-027] "My profile" for a parent, sibling or relative:
 * one photo of themselves, a line about them, city and work. Never searchable. */
export type MemberProfile = {
  photo_url: string | null;
  about: string | null;
  city: string | null;
  occupation: string | null;
};

export async function getMemberProfile(): Promise<MemberProfile | null> {
  return getJson<MemberProfile>('/profile/member/me');
}

export async function saveMemberProfile(
  body: Pick<MemberProfile, 'about' | 'city' | 'occupation'>,
): Promise<Outcome<MemberProfile>> {
  return sendJson<MemberProfile>('PATCH', '/profile/member/me', body);
}

export async function uploadMemberPhoto(file: File): Promise<MemberProfile | null> {
  const form = new FormData();
  form.set('photo', file);
  try {
    const res = await apiFetch(`${API_BASE}/profile/member/photo`, {
      method: 'POST',
      body: form,
      credentials: 'include',
      headers: currentLanguageHeader(),
    });
    return res.ok ? ((await res.json()) as MemberProfile) : null;
  } catch {
    return null;
  }
}

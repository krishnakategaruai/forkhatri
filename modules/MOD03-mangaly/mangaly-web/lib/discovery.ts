/* Discovery + Compatibility calls against MangalyService — FR021/FR026/FR030. */

import { API_BASE, apiFetch } from './api';
import { getI18n } from './i18n/config';

/** Matches the backend's own `page_size` default (`discovery.search()`), which is
 * what tells the feed whether another page exists: a full page means there may
 * be more, a short one means this was the last. */
const PAGE_SIZE = 20;

function currentLanguageHeader(): Record<string, string> {
  try {
    return { 'X-Mangaly-Language': getI18n().language };
  } catch {
    return {};
  }
}

async function getJson<T>(path: string): Promise<T | null> {
  try {
    const res = await apiFetch(`${API_BASE}${path}`, {
      credentials: 'include',
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

export type SearchResult = {
  candidate_account_id: string;
  score: number;
  locality: string | null;
  education_level: string | null;
  profession: string | null;
  photo_url?: string | null;
  age?: number | null;
};

export type SearchOutcome = { results: SearchResult[]; lookingForMissing: boolean; hasMore: boolean };

export type DiscoverFilters = {
  nearby?: 'city' | 'state';
  ageMin?: number;
  ageMax?: number;
  maritalStatus?: string[];
  education?: string[];
  diet?: string[];
  openToRelocate?: boolean;
};

export async function search(
  filters: DiscoverFilters,
  forCandidate?: string,
  page: number = 1
): Promise<SearchOutcome> {
  const params = new URLSearchParams();
  if (forCandidate) params.set('for_candidate', forCandidate);
  if (page > 1) params.set('page', String(page));
  if (filters.nearby) params.set('nearby', filters.nearby);
  if (filters.ageMin) params.set('age_min', String(filters.ageMin));
  if (filters.ageMax) params.set('age_max', String(filters.ageMax));
  filters.maritalStatus?.forEach((v) => params.append('marital_status', v));
  filters.education?.forEach((v) => params.append('education', v));
  filters.diet?.forEach((v) => params.append('diet', v));
  if (filters.openToRelocate) params.set('open_to_relocate', 'true');
  const query = params.toString() ? `?${params.toString()}` : '';
  try {
    const res = await apiFetch(`${API_BASE}/discovery/search${query}`, {
      credentials: 'include',
      cache: 'no-store',
      headers: currentLanguageHeader(),
    });
    if (res.status === 409) return { results: [], lookingForMissing: true, hasMore: false };
    if (!res.ok) return { results: [], lookingForMissing: false, hasMore: false };
    const results = (await res.json()) as SearchResult[];
    return { results, lookingForMissing: false, hasMore: results.length >= PAGE_SIZE };
  } catch {
    return { results: [], lookingForMissing: false, hasMore: false };
  }
}

export type Snippet = {
  locality: string | null;
  education_level: string | null;
  profession: string | null;
  photo_url?: string | null;
  age?: number | null;
};

/** [FR021] One candidate's demographic snippet — used to identify a
 * not-yet-connected candidate (e.g. a pending request's sender) somewhere
 * more meaningful than a raw account id, without a new disclosure. */
export async function getSnippet(candidateAccountId: string): Promise<Snippet | null> {
  return await getJson<Snippet>(`/discovery/snippet/${candidateAccountId}`);
}

export type CompatibilityReason = { text: string; source: 'fact' | 'inference' };

export async function whyThisMatch(candidateAccountId: string, forCandidate?: string): Promise<CompatibilityReason[]> {
  const query = forCandidate ? `?for_candidate=${encodeURIComponent(forCandidate)}` : '';
  return (await getJson<CompatibilityReason[]>(`/discovery/compatibility/${candidateAccountId}${query}`)) ?? [];
}

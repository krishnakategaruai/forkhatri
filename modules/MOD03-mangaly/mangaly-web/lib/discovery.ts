/* Discovery + Compatibility calls against MangalyService — FR021/FR026/FR030. */

import { API_BASE } from './api';
import { getI18n } from './i18n/config';

function currentLanguageHeader(): Record<string, string> {
  try {
    return { 'X-Mangaly-Language': getI18n().language };
  } catch {
    return {};
  }
}

async function getJson<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
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
};

export async function search(locality?: string): Promise<SearchResult[]> {
  const query = locality ? `?locality=${encodeURIComponent(locality)}` : '';
  return (await getJson<SearchResult[]>(`/discovery/search${query}`)) ?? [];
}

export type Snippet = { locality: string | null; education_level: string | null; profession: string | null };

/** [FR021] One candidate's demographic snippet — used to identify a
 * not-yet-connected candidate (e.g. a pending request's sender) somewhere
 * more meaningful than a raw account id, without a new disclosure. */
export async function getSnippet(candidateAccountId: string): Promise<Snippet | null> {
  return await getJson<Snippet>(`/discovery/snippet/${candidateAccountId}`);
}

export type CompatibilityReason = { text: string; source: 'fact' | 'inference' };

export async function whyThisMatch(candidateAccountId: string): Promise<CompatibilityReason[]> {
  return (await getJson<CompatibilityReason[]>(`/discovery/compatibility/${candidateAccountId}`)) ?? [];
}

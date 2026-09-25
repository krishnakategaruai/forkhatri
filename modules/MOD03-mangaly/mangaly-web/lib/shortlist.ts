/* Shortlist — contract §3. Context-scoped: a parent's saves for Ananya are
 * Ananya's shortlist, kept apart from the parent's own (if they are also a
 * candidate). Every Discover card, profile and Home panel offers Save. */

import { deleteJson, getJson, postJson, query, type Outcome } from './api';
import type { SearchResult } from './discovery';

export type ShortlistEntry = SearchResult & { saved_at?: string | null; saved_by_name?: string | null };

export async function listShortlist(forCandidate?: string): Promise<ShortlistEntry[]> {
  const rows = await getJson<ShortlistEntry[] | { results: ShortlistEntry[] }>(
    `/shortlist${query({ for_candidate: forCandidate })}`
  );
  const list = Array.isArray(rows) ? rows : rows?.results ?? [];
  return list.map((r) => ({
    ...r,
    profile_id: r.profile_id ?? r.candidate_account_id,
    candidate_account_id: r.candidate_account_id ?? r.profile_id,
  }));
}

export async function save(profileId: string, forCandidate?: string): Promise<Outcome<null>> {
  return postJson(`/shortlist/${profileId}${query({ for_candidate: forCandidate })}`);
}

export async function unsave(profileId: string, forCandidate?: string): Promise<Outcome<null>> {
  return deleteJson(`/shortlist/${profileId}${query({ for_candidate: forCandidate })}`);
}

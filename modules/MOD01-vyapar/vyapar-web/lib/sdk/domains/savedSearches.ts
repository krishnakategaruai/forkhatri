// [FE2 — imp-backend-b §5] Saved Discover searches, optionally with an
// alert when a new post matches (the server's strong-match pass sends it).
import { seg, type VyaparClient } from "../client";
import type { FeedFilterValues } from "../types";

export interface SavedSearch {
  id: string;
  name: string | null;
  query: string;
  filters: FeedFilterValues;
  alert: boolean;
  last_alerted_at: string | null;
  created_at: string;
}

export interface SavedSearchInput {
  query?: string;
  name?: string | null;
  alert?: boolean;
  filters?: FeedFilterValues;
}

export function savedSearchesApi(c: VyaparClient) {
  const base = "/v1/opportunities/saved-searches";
  return {
    /** saveSearch — 429 too_many_saved_searches past 20 */
    create: (body: SavedSearchInput) => c.post<SavedSearch>(base, body),
    /** listSavedSearches */
    list: () => c.get<SavedSearch[]>(base),
    /** deleteSavedSearch */
    remove: (id: string) => c.delete<unknown>(`${base}/${seg(id)}`),
  };
}

export type SavedSearchesApi = ReturnType<typeof savedSearchesApi>;

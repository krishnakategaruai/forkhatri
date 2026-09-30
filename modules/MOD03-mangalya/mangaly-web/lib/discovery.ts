/* Discovery + Compatibility calls against MangalyService — FR021/FR026/FR030.
 *
 * [2026-09-17 rework, contract §3/§6] The search grew the filters a mature
 * matrimony search has (height, gotra, sub-community, profession, income,
 * mother tongue, manglik, keyword), a sort, a `total`, and browse mode: an
 * account with no context passes `looking_for` explicitly. */

import {
  API_BASE,
  apiFetch,
  currentLanguageHeader,
  getJson,
  query,
} from "./api";
import type { LookingFor } from "./auth";

/** Matches the backend's own `page_size` default (`discovery.search()`), which is
 * what tells the feed whether another page exists: a full page means there may
 * be more, a short one means this was the last. */
const PAGE_SIZE = 20;

/* One verified fact about a candidate. A list of these, never a score:
 * Mangalya's baseline (§4.8, §13.1) rules out a trust score, a reputation
 * ranking and any aggregate. `verified_on` and `method` travel with the claim
 * so a reader can weigh how fresh the check is and how it was made (§13.4). */
export type VerifiedLayer = {
  layer: string;
  verified_on: string | null;
  method: string | null;
};

export type SearchResult = {
  /** Contract id for shortlist/safety/profile calls. Falls back to the account id. */
  profile_id: string;
  candidate_account_id: string;
  /** [DEC-V1-031] The engine's word for the pair; its 1–10 number stays on the server. */
  match_label?: 'strong' | 'good' | null;
  name?: string | null;
  locality: string | null;
  education_level: string | null;
  profession: string | null;
  photo_url?: string | null;
  age?: number | null;
  verification?: VerifiedLayer[];
  height_cm?: number | null;
  marital_status?: string | null;
  gotra?: string | null;
  mother_tongue?: string | null;
  income_band?: string | null;
  /** One evidence line the server already chose (FR030); else the card fetches reasons. */
  evidence?: string | null;
  shortlisted?: boolean;
  request_status?: "pending" | "accepted" | "declined" | null;
  /** [Migration 043] Only what this person chose to show openly. */
  open_name?: string | null;
  open_prompt?: { q: string; a: string } | null;
  open_photo_urls?: string[];
};

export type SearchOutcome = {
  results: SearchResult[];
  total: number | null;
  lookingForMissing: boolean;
  hasMore: boolean;
  /** The horoscope filter is on but the person searched for has no kundli yet. */
  horoscopeChartMissing?: boolean;
};

export type SortOrder = "relevance" | "newest" | "recently_active";

export type DiscoverFilters = {
  nearby?: "city" | "state";
  city?: string;
  ageMin?: number;
  ageMax?: number;
  heightMin?: number;
  heightMax?: number;
  maritalStatus?: string[];
  education?: string[];
  profession?: string[];
  incomeBand?: string[];
  gotra?: string[];
  subCommunity?: string[];
  motherTongue?: string[];
  diet?: string[];
  manglik?: "yes" | "no" | "partial";
  openToRelocate?: boolean;
  q?: string;
  sort?: SortOrder;
  /** Horoscope filter: minimum Guna Milan (out of 36) with the person searched for. */
  minGuna?: number;
  /** Horoscope filter: Mangal Dosha the same as the person searched for, or none. */
  mangal?: "match" | "none";
  /** South Indian: at least this many of the 10 poruthams. */
  minPorutham?: number;
  /** South Indian: Rajju and Vedha must agree. */
  poruthamEssentials?: boolean;
};

export const EMPTY_FILTERS: DiscoverFilters = {};

export function countActiveFilters(f: DiscoverFilters): number {
  return [
    f.nearby,
    f.city,
    f.ageMin ?? f.ageMax,
    f.heightMin ?? f.heightMax,
    f.maritalStatus?.length ? true : undefined,
    f.education?.length ? true : undefined,
    f.profession?.length ? true : undefined,
    f.incomeBand?.length ? true : undefined,
    f.gotra?.length ? true : undefined,
    f.subCommunity?.length ? true : undefined,
    f.motherTongue?.length ? true : undefined,
    f.diet?.length ? true : undefined,
    f.manglik,
    f.openToRelocate ? true : undefined,
    f.q?.trim() ? true : undefined,
    f.minGuna,
    f.mangal,
    f.minPorutham,
    f.poruthamEssentials ? true : undefined,
  ].filter((v) => v !== undefined).length;
}

function normalizeResult(
  r: Partial<SearchResult> & {
    candidate_account_id?: string;
    profile_id?: string;
  },
): SearchResult {
  const account = r.candidate_account_id ?? r.profile_id ?? "";
  return {
    ...r,
    profile_id: r.profile_id ?? account,
    candidate_account_id: account,
    locality: r.locality ?? null,
    education_level: r.education_level ?? null,
    profession: r.profession ?? null,
  };
}

export async function search(
  filters: DiscoverFilters,
  options: {
    forCandidate?: string;
    lookingFor?: LookingFor | null;
    page?: number;
  } = {},
): Promise<SearchOutcome> {
  const page = options.page ?? 1;
  const qs = query({
    for_candidate: options.forCandidate,
    looking_for: options.forCandidate
      ? undefined
      : (options.lookingFor ?? undefined),
    page: page > 1 ? page : undefined,
    nearby: filters.nearby,
    city: filters.city,
    age_min: filters.ageMin,
    age_max: filters.ageMax,
    height_min: filters.heightMin,
    height_max: filters.heightMax,
    marital_status: filters.maritalStatus,
    education: filters.education,
    profession: filters.profession,
    income_band: filters.incomeBand,
    gotra: filters.gotra,
    sub_community: filters.subCommunity,
    mother_tongue: filters.motherTongue,
    diet: filters.diet,
    manglik: filters.manglik,
    open_to_relocate: filters.openToRelocate,
    q: filters.q?.trim(),
    min_guna: filters.minGuna,
    mangal: filters.mangal,
    min_porutham: filters.minPorutham,
    porutham_essentials: filters.poruthamEssentials,
    sort:
      filters.sort && filters.sort !== "relevance" ? filters.sort : undefined,
  });
  try {
    const res = await apiFetch(`${API_BASE}/discovery/search${qs}`, {
      cache: "no-store",
      headers: currentLanguageHeader(),
    });
    if (res.status === 409)
      return { results: [], total: 0, lookingForMissing: true, hasMore: false };
    if (res.status === 422 && (filters.minGuna !== undefined || filters.mangal || filters.minPorutham !== undefined || filters.poruthamEssentials))
      return { results: [], total: 0, lookingForMissing: false, hasMore: false, horoscopeChartMissing: true };
    if (!res.ok)
      return {
        results: [],
        total: null,
        lookingForMissing: false,
        hasMore: false,
      };
    const body = (await res.json()) as
      SearchResult[] | { results: SearchResult[]; total?: number };
    const list = Array.isArray(body) ? body : (body.results ?? []);
    const total = Array.isArray(body) ? null : (body.total ?? null);
    const results = list.map(normalizeResult);
    return {
      results,
      total,
      lookingForMissing: false,
      hasMore: results.length >= PAGE_SIZE,
    };
  } catch {
    return {
      results: [],
      total: null,
      lookingForMissing: false,
      hasMore: false,
    };
  }
}

/** [DEC-V1-022] One "For you" row: a fact both people can check, each face
 *  with its one reason. `see_all` reproduces the row on the full wall. */
export type Shelf = {
  key:
    /** [DEC-V1-030] One person from the daily stable-matching pass. */
    | "mostCompatible"
    | "picked"
    | "family"
    | "near"
    | "moving"
    | "roots"
    | "life"
    | "familyView"
    | "words"
    | "new";
  see_all: DiscoverFilters;
  results: (SearchResult & { reason?: string | null })[];
};

export async function getShelves(
  options: { forCandidate?: string; lookingFor?: LookingFor | null } = {},
): Promise<{ shelves: Shelf[]; lookingForMissing: boolean }> {
  const qs = query({
    for_candidate: options.forCandidate,
    looking_for: options.forCandidate
      ? undefined
      : (options.lookingFor ?? undefined),
  });
  try {
    const res = await apiFetch(`${API_BASE}/discovery/shelves${qs}`, {
      cache: "no-store",
      headers: currentLanguageHeader(),
    });
    if (res.status === 409) return { shelves: [], lookingForMissing: true };
    if (!res.ok) return { shelves: [], lookingForMissing: false };
    const body = (await res.json()) as Shelf[];
    return {
      shelves: body.map((s) => ({
        ...s,
        results: s.results.map((r) => ({
          ...normalizeResult(r),
          reason: r.reason ?? null,
        })),
      })),
      lookingForMissing: false,
    };
  } catch {
    return { shelves: [], lookingForMissing: false };
  }
}

/** [Owner, 2026-09-28] "Because of this, these" on Home: people like one
 *  person the family acted on (a request, a suggestion, a save). */
export type BecauseRow = {
  kind: "request" | "suggested" | "saved";
  anchor_account_id: string;
  title: string;
  sub: string;
  results: (SearchResult & { reason?: string | null })[];
};

export async function getBecause(forCandidate?: string): Promise<BecauseRow[]> {
  try {
    const res = await apiFetch(`${API_BASE}/discovery/because${query({ for_candidate: forCandidate })}`, {
      cache: "no-store",
      headers: currentLanguageHeader(),
    });
    if (!res.ok) return [];
    const body = (await res.json()) as BecauseRow[];
    return body.map((row) => ({
      ...row,
      results: row.results.map((r) => ({ ...normalizeResult(r), reason: r.reason ?? null })),
    }));
  } catch {
    return [];
  }
}

export type Snippet = {
  verification?: VerifiedLayer[];
  locality: string | null;
  education_level: string | null;
  profession: string | null;
  photo_url?: string | null;
  age?: number | null;
  name?: string | null;
};

/** [FR021] One candidate's demographic snippet — used to identify a
 * not-yet-connected candidate (e.g. a pending request's sender) somewhere
 * more meaningful than a raw account id, without a new disclosure. */
export async function getSnippet(candidateId: string): Promise<Snippet | null> {
  return await getJson<Snippet>(`/discovery/snippet/${candidateId}`);
}

export type CompatibilityReason = {
  text: string;
  source: "fact" | "inference";
};

export async function whyThisMatch(
  candidateId: string,
  forCandidate?: string,
): Promise<CompatibilityReason[]> {
  return (
    (await getJson<CompatibilityReason[]>(
      `/discovery/compatibility/${candidateId}${query({ for_candidate: forCandidate })}`,
    )) ?? []
  );
}

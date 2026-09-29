// [FE2] Discover filters <-> URL query. The URL is the source of truth so a
// filtered feed can be shared, reloaded, opened from a saved search, from a
// themed row's "See all" and from the Hire / Find work menu.
import type { FeedFilterValues, FeedParams } from "@/lib/sdk";

export type FeedQuery = Partial<
  Record<
    | "skills" | "q" | "type" | "types" | "work_mode" | "radius_km" | "availability" | "sort"
    | "pay_kind" | "pay_min_paise" | "pay_max_paise" | "posted_within" | "shift" | "experience" | "verified_only" | "segment",
    string
  >
>;

const num = (v: string | undefined) => {
  const n = v ? Number(v) : NaN;
  return Number.isFinite(n) ? n : null;
};

export const EMPTY_FILTERS: FeedFilterValues = { skills: [], types: [], sort: "relevance" };

export function filtersFromQuery(q: FeedQuery): FeedFilterValues {
  const types = [...new Set([...(q.types ? q.types.split(",") : []), ...(q.type ? [q.type] : [])].filter(Boolean))];
  return {
    skills: q.skills ? q.skills.split(",").filter(Boolean) : [],
    q: q.q || null,
    types,
    type: null,
    work_mode: q.work_mode || null,
    radius_km: num(q.radius_km),
    availability: q.availability || null,
    sort: q.sort || "relevance",
    pay_kind: q.pay_kind === "monthly" || q.pay_kind === "project" ? q.pay_kind : null,
    pay_min_paise: num(q.pay_min_paise),
    pay_max_paise: num(q.pay_max_paise),
    posted_within: q.posted_within === "today" || q.posted_within === "week" || q.posted_within === "month" ? q.posted_within : null,
    shift: q.shift === "day" || q.shift === "night" || q.shift === "flexible" ? q.shift : null,
    experience: q.experience === "fresher" || q.experience === "1" || q.experience === "3" ? q.experience : null,
    verified_only: q.verified_only === "true",
    segment: q.segment === "community" || q.segment === "public" ? q.segment : null,
  };
}

export function filtersToQuery(f: FeedFilterValues): string {
  const p = new URLSearchParams();
  const types = [...new Set([...(f.types ?? []), ...(f.type ? [String(f.type)] : [])])];
  if (f.q) p.set("q", f.q);
  if (types.length) p.set("types", types.join(","));
  if (f.skills && f.skills.length) p.set("skills", f.skills.join(","));
  if (f.work_mode) p.set("work_mode", String(f.work_mode));
  if (f.radius_km) p.set("radius_km", String(f.radius_km));
  if (f.availability) p.set("availability", String(f.availability));
  if (f.pay_kind) p.set("pay_kind", f.pay_kind);
  if (f.pay_min_paise != null) p.set("pay_min_paise", String(f.pay_min_paise));
  if (f.pay_max_paise != null) p.set("pay_max_paise", String(f.pay_max_paise));
  if (f.posted_within) p.set("posted_within", f.posted_within);
  if (f.shift) p.set("shift", f.shift);
  if (f.experience) p.set("experience", f.experience);
  if (f.verified_only) p.set("verified_only", "true");
  if (f.segment) p.set("segment", f.segment);
  if (f.sort && f.sort !== "relevance") p.set("sort", String(f.sort));
  return p.toString();
}

/** A themed row's "See all" filters (from the API) as a query string. */
export function seeAllQuery(seeAll: Record<string, string | number | boolean>): string {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(seeAll)) p.set(k, String(v));
  return p.toString();
}

export function toFeedParams(f: FeedFilterValues): FeedParams {
  return {
    skills: f.skills ?? [],
    q: f.q ?? null,
    types: [...new Set([...(f.types ?? []), ...(f.type ? [String(f.type)] : [])])],
    work_mode: f.work_mode ?? null,
    radius_km: f.radius_km ?? null,
    availability: f.availability ?? null,
    sort: f.sort ?? null,
    pay_kind: f.pay_kind ?? null,
    pay_min_paise: f.pay_min_paise ?? null,
    pay_max_paise: f.pay_max_paise ?? null,
    posted_within: f.posted_within ?? null,
    shift: f.shift ?? null,
    experience: f.experience ?? null,
    verified_only: !!f.verified_only,
    segment: f.segment ?? null,
  };
}

/** Filters that narrow the list (sort orders it; it is not counted). */
export function activeCount(f: FeedFilterValues): number {
  return (
    (f.q ? 1 : 0) +
    (f.types?.length ?? 0) +
    (f.skills?.length ? 1 : 0) +
    [f.work_mode, f.radius_km, f.availability, f.posted_within, f.shift, f.experience].filter(Boolean).length +
    (f.pay_min_paise != null || f.pay_max_paise != null ? 1 : 0) +
    (f.verified_only ? 1 : 0) +
    (f.segment ? 1 : 0)
  );
}

/** Rows (curated home) only when nothing narrows or re-orders the list. */
export function isCurated(f: FeedFilterValues): boolean {
  return activeCount(f) === 0 && (!f.sort || f.sort === "relevance");
}

/** Posts a filtered feed would show (legacy sectioned feed). */
export function resultCount(sections: { items: { id: string }[]; total_available: number }[]): number {
  const ids = new Set(sections.flatMap((s) => s.items.map((i) => i.id)));
  return Math.max(ids.size, ...sections.map((s) => s.total_available), 0);
}

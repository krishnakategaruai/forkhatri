"use client";

// [TR015/TR017] Businesses & Professionals — standalone search/browse
// surface (FR15 DEC-001: distinct from the Opportunity feed, works with
// zero Opportunities in the system). Zero-result responses render FR17's
// explicit, labelled broadening options — never a silent relaxation.
// [Product-owner i18n rule] `notice` / `broadening_options[].label` /
// `relevance_reason` from the API are i18n KEYS, translated in the view.
//
// [2026-09-30 rebuild — owner: "boring and weak", "i really hate filters
// section"] The route owns search state only:
//   - the text searches as you type (debounced 350ms), no Search button;
//   - the directory shows everyone on arrival (an empty query browses);
//   - filters are structured state sent with every search (Trade, Distance,
//     Available, Verified, More), set from the dropdown bar;
//   - the URL (?q=&category=&skills=&locality=) seeds it, so the Hire menu,
//     Discover's tab and outcome pages still land on a filtered directory.
// The request goes through useListingSearch (SDK); markup is <BusinessesView>.
// Traces to: FR15, FR16, FR17, TR015, TR016, TR017
import { use, useEffect, useRef, useState } from "react";
import type { ListingSearchParams } from "@/lib/sdk";
import { DEFAULT_FILTERS, type Filters } from "@/app/components/FilterSheet";
import Screen from "@/app/components/Screen";
import BusinessesView, { type BizFilters } from "@/app/components/businesses/BusinessesView";
import { useListingSearch } from "@/app/hooks/listings";

type BusinessesQuery = { q?: string; category?: string; locality?: string; skills?: string };

function buildParams(q: string, f: BizFilters, attempt: number, extra: Record<string, string> = {}): ListingSearchParams {
  const params: ListingSearchParams = {};
  if (q.trim()) params.q = q.trim();
  if (f.category) params.category = f.category;
  if (f.locality) params.locality = f.locality;
  if (f.radius_km) params.radius_km = String(f.radius_km);
  if (f.service_mode) params.service_mode = f.service_mode;
  if (f.availability) params.availability = f.availability;
  if (f.verified_only) params.verified_only = "true";
  if (f.skills && f.skills.length > 0) params.skills = f.skills;
  params.sort_by = f.sort_by;
  params.broaden_attempt = attempt;
  Object.entries(extra).forEach(([k, v]) => (params[k] = v));
  return params;
}

function fromQuery(query: BusinessesQuery): BizFilters {
  return {
    ...(DEFAULT_FILTERS as Filters),
    skills: query.skills ? query.skills.split(",").filter(Boolean) : undefined,
    category: query.category ?? null,
    locality: query.locality ?? null,
  };
}

export default function BusinessesPage({ searchParams }: { searchParams: Promise<BusinessesQuery> }) {
  const query = use(searchParams);
  const queryKey = JSON.stringify(query);
  const [q, setQ] = useState(query.q ?? "");
  const [filters, setFilters] = useState<BizFilters>(() => fromQuery(query));
  const [attempt, setAttempt] = useState(0);
  const { response, loading, search } = useListingSearch();

  // A new URL (Hire menu, a link) re-seeds the state.
  const seeded = useRef(queryKey);
  useEffect(() => {
    if (seeded.current === queryKey) return;
    seeded.current = queryKey;
    queueMicrotask(() => {
      setQ(query.q ?? "");
      setFilters(fromQuery(query));
    });
  }, [queryKey, query]);

  // Search as you type (debounced); filters apply at once.
  const lastText = useRef<string | null>(null);
  useEffect(() => {
    const typed = lastText.current !== null && lastText.current !== q;
    lastText.current = q;
    const id = window.setTimeout(
      () => {
        setAttempt(0);
        void search(buildParams(q, filters, 0));
      },
      typed ? 350 : 0,
    );
    return () => window.clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q, filters]);

  function applyBroadening(optionId: string) {
    const next = attempt + 1;
    setAttempt(next);
    if (optionId === "remove_filter") {
      void search(buildParams(q, { ...(DEFAULT_FILTERS as Filters) }, next));
      return;
    }
    const extra: Record<string, string> = {};
    if (optionId.startsWith("radius_")) extra.radius_km = optionId.replace("radius_", "");
    if (optionId === "include_unverified") extra.verified_only = "false";
    void search(buildParams(q, filters, next, extra));
  }

  return (
    <Screen width="wide">
      <BusinessesView
        query={q}
        onQuery={setQ}
        response={response}
        loading={loading}
        filters={filters}
        onFiltersChange={setFilters}
        onBroaden={applyBroadening}
      />
    </Screen>
  );
}

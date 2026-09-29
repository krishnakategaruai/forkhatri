"use client";

// [TR015/TR017] Businesses & Professionals — standalone search/browse
// surface (FR15 DEC-001: distinct from the Opportunity feed, works with
// zero Opportunities in the system). Uses <IntentBar> instead of a
// conventional multi-dropdown filter form per the design direction — fewer
// taps for the common case ("plumber near Ameerpet" is one field, not four
// separate pickers). Zero-result responses render FR17's explicit,
// labelled broadening chips — never a silent filter relaxation.
// [Product-owner i18n rule] `notice`/`broadening_options[].label`/
// `relevance_reason` from the API are now i18n KEYS (discovery.py's own
// i18n conversion) — this page translates them via discover.json/
// ranking.json, never renders them as raw English/key text.
// [IMP38 — Refactor C] Now only the route: search state and the query
// building live here, the request goes through useListingSearch (SDK; the
// last search re-runs on a live language switch), the markup is
// <BusinessesView>.
// Traces to: FR15, FR16, FR17, TR015, TR016, TR017
import { use, useEffect, useRef, useState } from "react";
import type { ListingSearchParams } from "@/lib/sdk";
import type { ParsedIntent } from "@/app/components/IntentBar";
import { DEFAULT_FILTERS, type Filters } from "@/app/components/FilterSheet";
import Screen from "@/app/components/Screen";
import BusinessesView from "@/app/components/businesses/BusinessesView";
import { useListingSearch } from "@/app/hooks/listings";

function buildParams(intent: ParsedIntent, attempt: number, f: Filters, extraParams: Record<string, string> = {}): ListingSearchParams {
  const params: ListingSearchParams = {};
  if (intent.text) params.q = intent.text;
  // [Third critique pass fix] intent.category is now a real taxonomy
  // slug from IntentBar's own suggestion fetch, never a label needing a
  // lossy space-to-underscore guess.
  if (intent.category) params.category = intent.category;
  if (intent.locality) params.locality = intent.locality;
  if (f.radius_km) params.radius_km = String(f.radius_km);
  if (f.service_mode) params.service_mode = f.service_mode;
  if (f.availability) params.availability = f.availability;
  if (f.verified_only) params.verified_only = "true";
  if (f.skills && f.skills.length > 0) params.skills = f.skills;
  params.sort_by = f.sort_by;
  params.broaden_attempt = attempt;
  Object.entries(extraParams).forEach(([k, v]) => (params[k] = v));
  return params;
}

// [FE2] The page now reads its URL (?q=&category=&locality=&skills=) and runs
// that search on arrival — Discover's search box, the desktop Hire menu and
// the outcome pages all link here with a query. Before this, those links
// landed on an empty directory.
type BusinessesQuery = { q?: string; category?: string; locality?: string; skills?: string };

export default function BusinessesPage({ searchParams }: { searchParams: Promise<BusinessesQuery> }) {
  const query = use(searchParams);
  const [lastQuery, setLastQuery] = useState<ParsedIntent | null>(null);
  const [broadenAttempt, setBroadenAttempt] = useState(0);
  // [Real regression fix — FR15/FR17/FR19, coordinator direction] the
  // free-text IntentBar had quietly become the ONLY way to narrow results.
  // `filters` is real, structured state independent of the parsed intent —
  // both are sent together on every search, and the intent bar is now a
  // shortcut INTO these filters (it can set locality/category), never the
  // only path to them.
  const [filters, setFilters] = useState<Filters>(() =>
    query.skills ? { ...DEFAULT_FILTERS, skills: query.skills.split(",").filter(Boolean) } : DEFAULT_FILTERS,
  );
  const { response, loading, search } = useListingSearch();
  const ranFor = useRef<string | null>(null);
  const queryKey = JSON.stringify(query);

  async function runSearch(intent: ParsedIntent, attempt = 0, extraParams: Record<string, string> = {}, f: Filters = filters) {
    setLastQuery(intent);
    setBroadenAttempt(attempt);
    await search(buildParams(intent, attempt, f, extraParams));
  }

  useEffect(() => {
    if (ranFor.current === queryKey) return;
    ranFor.current = queryKey;
    if (!query.q && !query.category && !query.locality && !query.skills) return;
    const f: Filters = query.skills ? { ...DEFAULT_FILTERS, skills: query.skills.split(",").filter(Boolean) } : DEFAULT_FILTERS;
    const intent: ParsedIntent = { text: query.q ?? "", category: query.category, locality: query.locality };
    queueMicrotask(() => {
      setFilters(f);
      void runSearch(intent, 0, {}, f);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [queryKey]);

  function changeFilters(next: Filters) {
    setFilters(next);
    if (lastQuery) runSearch(lastQuery, 0, {}, next);
  }

  function applyBroadening(optionId: string) {
    if (!lastQuery) return;
    const extra: Record<string, string> = {};
    if (optionId.startsWith("radius_")) extra.radius_km = optionId.replace("radius_", "");
    if (optionId === "include_unverified") extra.verified_only = "false";
    if (optionId === "remove_filter") {
      runSearch({ text: lastQuery.text }, broadenAttempt + 1);
      return;
    }
    runSearch(lastQuery, broadenAttempt + 1, extra);
  }

  return (
    // [IMP33] Directory screen — wide measure, and the whole body becomes
    // a sidebar layout at ≥900px. REQUIREMENT (owner, 2026-09-17):
    // "filters should become a persistent left sidebar on desktop instead
    // of a collapsible sheet, with results in a multi-column grid beside
    // them." A toggle-to-reveal filter panel is a phone compromise for
    // scarce vertical space; keeping it on a 1440px screen hides the
    // single most useful control on the screen behind a click. The SAME
    // <FilterSheet> component renders in both places — one filter
    // implementation, two placements, chosen by CSS breakpoint
    // (`vy-desktop-only` / `vy-mobile-only`) so there is no resize
    // listener and no hydration mismatch.
    <Screen width="wide">
      <BusinessesView
        response={response}
        loading={loading}
        filters={filters}
        onFiltersChange={changeFilters}
        onSearch={(intent) => runSearch(intent)}
        onBroaden={applyBroadening}
      />
    </Screen>
  );
}

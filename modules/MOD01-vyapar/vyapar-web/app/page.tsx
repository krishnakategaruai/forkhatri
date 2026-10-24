"use client";

// [TR018] Opportunity Discover — the home screen. [TR044] first-run
// redirect (FR44).
// [IMP38 — Refactor C] Only the route: data here, markup in <DiscoverView>.
// [FE2 — owner review 2026-09-29] Filters live in the URL (?q=&types=&
// radius_km=&pay_min_paise=&posted_within=&sort=…): shareable, reloadable,
// the target of saved searches, row "See all" links and the Hire / Find
// work menu. With nothing narrowing the list the page shows themed rows
// (GET /v1/opportunities/feed/rows); otherwise one ranked list with its
// total and facet counts (GET /v1/opportunities/feed/results).
// [Design language 2026-09-29] the page now also passes a load failure
// (with Try again) to the view; the sidebar is gone, filters live in a
// sheet / drawer that fetches its own preview counts.
// Traces to: FR44, FR18, FR19, FR20
import { use, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import type { FeedFilterValues, ResultsResponse, RowsResponse } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import Screen from "@/app/components/Screen";
import DiscoverView from "@/app/components/discover/DiscoverView";
import { filtersFromQuery, filtersToQuery, isCurated, seeAllQuery, toFeedParams, type FeedQuery } from "@/app/components/discover/feedFilters";
import { useFirstRunState } from "@/app/hooks/opportunities";
import { useResource } from "@/app/hooks/useResource";
import { useRoutes } from "@/app/host/HostProvider";
import { FEED_CHANGED_EVENT } from "@/app/components/reco/feedbackStore";
// [Start flow 2026-10, decision 12] results first: the outcome line and the
// one-question completion card sit on Discover, never on a screen of their own.
import StartOutcomeCard from "@/app/components/start/StartOutcomeCard";
import CompletionCard from "@/app/components/start/CompletionCard";
import { useMyProfile } from "@/app/components/account/useMyProfile";
import "@/app/styles/start-2026.css";

/** The filter the empty state offers to drop: the narrowest-looking one still set. */
function withoutLastFilter(f: FeedFilterValues): FeedFilterValues | null {
  if (f.verified_only) return { ...f, verified_only: false };
  if (f.experience) return { ...f, experience: null };
  if (f.shift) return { ...f, shift: null };
  if (f.posted_within) return { ...f, posted_within: null };
  if (f.pay_min_paise != null || f.pay_max_paise != null) return { ...f, pay_min_paise: null, pay_max_paise: null, pay_kind: null };
  if (f.work_mode) return { ...f, work_mode: null };
  if (f.skills?.length) return { ...f, skills: f.skills.slice(0, -1) };
  if (f.types?.length) return { ...f, types: f.types.slice(0, -1) };
  if (f.segment) return { ...f, segment: null };
  if (f.q) return { ...f, q: null };
  return null;
}

export default function HomePage({ searchParams }: { searchParams: Promise<FeedQuery> }) {
  const query = use(searchParams);
  const router = useRouter();
  const sdk = useSdk();
  const routes = useRoutes();
  const { t } = useTranslation(["explore"]);
  const queryKey = JSON.stringify(query);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const filters = useMemo(() => filtersFromQuery(query), [queryKey]);
  const curated = isCurated(filters);
  const firstRun = useFirstRunState();
  const state = firstRun.data;
  // [Start flow 2026-10, decision 1] a member with a trade or a post is never
  // sent to the start; the server says so through `needs_start`.
  const needsStart = !!state && (state.needs_start ?? !state.done);
  const ready = !!state && !needsStart;
  const welcome = (query as Record<string, string | undefined>).welcome;
  const draftReason = (query as Record<string, string | undefined>).draft ?? null;
  const me = useMyProfile();
  const rows = useResource<RowsResponse>(() => sdk.feed.rows(), [sdk], { enabled: ready && curated });
  const results = useResource<ResultsResponse>(() => sdk.feed.results(toFeedParams(filters)), [queryKey, sdk], { enabled: ready });

  // [Recommendations 2026-09-30] "Not interested" / "More like this" / Undo:
  // re-read the list so similar posts drop and a learned row can appear.
  const refreshRows = rows.refresh;
  const refreshResults = results.refresh;
  useEffect(() => {
    const onChanged = () => void (curated ? refreshRows() : refreshResults());
    window.addEventListener(FEED_CHANGED_EVENT, onChanged);
    return () => window.removeEventListener(FEED_CHANGED_EVENT, onChanged);
  }, [curated, refreshRows, refreshResults]);

  // [TR044 → start flow 2026-10] A member who has not done the 3-question
  // start goes there first — unless the hub sent a search (?q=), which is
  // honoured straight away (decision 1).
  useEffect(() => {
    if (needsStart && !filters.q) router.replace("/first-run");
  }, [needsStart, filters.q, router]);

  function setFilters(next: FeedFilterValues) {
    const qs = filtersToQuery(next);
    router.replace(qs ? `/?${qs}` : "/", { scroll: false });
  }

  const skillLabels = new Map((results.data?.facets.skills ?? []).map((s) => [s.value, s.label ?? s.value]));
  const skillLabel = (slug: string) => skillLabels.get(slug) ?? slug.replace(/_/g, " ");
  const searchName =
    [
      filters.q ? `“${filters.q}”` : null,
      ...(filters.types ?? []).map((x) => t(`explore:type.${x}`)),
      ...(filters.skills ?? []).map(skillLabel),
      filters.radius_km ? t("explore:filters.withinKm", { km: filters.radius_km }) : null,
    ]
      .filter(Boolean)
      .join(" · ") || t("explore:saved.defaultName");
  const resultsFresh = results.data;

  return (
    <Screen width="wide">
      <DiscoverView
        displayName={state ? state.display_name : null}
        filters={filters}
        curated={curated}
        rows={rows.data?.rows ?? null}
        enrichmentPrompt={rows.data?.enrichment_prompt ?? null}
        items={resultsFresh?.items ?? null}
        total={resultsFresh?.total ?? null}
        facets={resultsFresh?.facets ?? null}
        place={resultsFresh?.near_label ?? null}
        defaultRadiusKm={resultsFresh?.radius_km ?? null}
        skillLabel={skillLabel}
        searchName={searchName}
        onFiltersChange={setFilters}
        onSeeAllRow={(row) => {
          const qs = seeAllQuery(row.see_all);
          router.push(qs ? `/?${qs}` : "/", { scroll: true });
        }}
        preview={async (draft) => {
          const r = await sdk.feed.results(toFeedParams(draft), 1);
          return { total: r.total, facets: r.facets };
        }}
        onAddCapabilities={() => router.push(routes.newListing)}
        onPost={() => router.push(routes.post)}
        lastFilterRemoved={withoutLastFilter(filters)}
        hasPersonalRows={rows.data?.has_personal_rows}
        viewerCategories={rows.data?.viewer_categories}
        failed={!!((firstRun.error && !state) || (curated ? rows.error && !rows.data : results.error && !results.data))}
        onRetry={() => void (!state ? firstRun.refresh() : curated ? rows.refresh() : results.refresh())}
        aside={
          ready ? (
            <>
              {(welcome === "work" || welcome === "visible") && (
                <StartOutcomeCard kind={welcome} me={me.data} live={!draftReason} blocked={draftReason} skillLabel={skillLabel} />
              )}
              <CompletionCard />
            </>
          ) : null
        }
      />
    </Screen>
  );
}

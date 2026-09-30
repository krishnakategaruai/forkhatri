"use client";

// [Fix #5 — "See all" affordance] Full, unbounded view of one Discover
// feed section, reached only by tapping "See all N" on the home feed's
// capped preview — keeps the home screen itself short (no scrolling
// burden on primary content) while still making every eligible item
// reachable, not silently dropped past the cap.
// [FE2 — imp-backend-b §5] Carries the home feed's filters (same URL
// query), so "See all" shows the same filtered set, with the applied
// filters as removable chips; cards are the shared OpportunityCard, so
// distance and poster badges show here too.
// Traces to: FR18 (not a separate FR — a UX completion of the same one)
import { use, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import type { OpportunityCard as Card } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import Screen from "@/app/components/Screen";
import { SkeletonGrid, EmptyState } from "@/app/components/States";
import OpportunityCard from "@/app/components/opportunity/OpportunityCard";
import AppliedFilters from "@/app/components/discover/AppliedFilters";
import { filtersFromQuery, filtersToQuery, toFeedParams, type FeedQuery } from "@/app/components/discover/feedFilters";
import { useResource } from "@/app/hooks/useResource";
import { ChevronLeft } from "lucide-react";
import "@/app/styles/deals-2026.css";

const SECTION_LABEL_KEY: Record<string, string> = {
  for_you: "sectionForYou",
  explore: "sectionExplore",
  near_you: "sectionNearYou",
  community: "sectionCommunity",
  public: "sectionPublic",
};

export default function FeedSectionPage({ params, searchParams }: { params: Promise<{ key: string }>; searchParams: Promise<FeedQuery> }) {
  const { key } = use(params);
  const query = use(searchParams);
  const { t } = useTranslation(["discover", "opportunities", "ranking", "explore"]);
  const sdk = useSdk();
  const router = useRouter();
  const queryKey = JSON.stringify(query);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const filters = useMemo(() => filtersFromQuery(query), [queryKey]);
  const items = useResource<Card[]>(() => sdk.feed.section(key, toFeedParams(filters)), [key, queryKey, sdk]);
  const skills = useResource<{ slug: string; label: string }[]>(() => sdk.firstRun.capabilityOptions(), [sdk], { fallback: [] });
  const qs = filtersToQuery(filters);

  return (
    <Screen width="wide">
      <Link href={qs ? `/?${qs}` : "/"} transitionTypes={["vy-back"]} className="vy-dl-back">
        <ChevronLeft size={18} strokeWidth={2} aria-hidden="true" />
        {t("explore:filters.backToDiscover")}
      </Link>
      <div className="vy-dl-head">
        <h1>{t(`discover:home.${SECTION_LABEL_KEY[key] ?? "sectionForYou"}` as "home.sectionForYou")}</h1>
        {items.data && items.data.length > 0 && <p>{t("explore:results.count", { count: items.data.length })}</p>}
      </div>
      <AppliedFilters
        value={filters}
        skillLabel={(slug) => skills.data?.find((s) => s.slug === slug)?.label ?? slug.replace(/_/g, " ")}
        onChange={(next) => {
          const nextQs = filtersToQuery(next);
          router.replace(nextQs ? `?${nextQs}` : "?", { scroll: false });
        }}
      />
      {items.data === null && <SkeletonGrid count={6} />}
      {items.data && items.data.length === 0 && <EmptyState mark="◌" title={t("explore:filters.noResults")} body={t("explore:filters.noResultsBody")} />}
      <div className="vy-grid vy-grid-3">
        {items.data?.map((item, i) => (
          <OpportunityCard key={item.id} item={item} variant="feed" index={i} />
        ))}
      </div>
    </Screen>
  );
}

"use client";

// [IMP38 — Refactor C] Discover (home), presentational half — markup moved
// verbatim out of app/page.tsx (see that file for the FR18 / IMP33
// reasoning). Data in, events out; the only state here is whether the
// phone filter panel is open. IntentBar and FilterSheet are the shared
// search controls and load their own option lists, as before.
import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { FeedResponse } from "@/lib/sdk";
import IntentBar, { type ParsedIntent } from "@/app/components/IntentBar";
import FilterSheet, { activeFilterCount, type Filters } from "@/app/components/FilterSheet";
import { RevealSection } from "@/app/components/Motion";
import { SkeletonGrid, EmptyState } from "@/app/components/States";
import OpportunityCard from "@/app/components/opportunity/OpportunityCard";

export interface DiscoverViewProps {
  /** Member's display name once known; null shows the greeting skeleton. */
  displayName: string | null;
  feed: FeedResponse | null;
  filters: Filters;
  onFiltersChange: (next: Filters) => void;
  onSearch: (intent: ParsedIntent) => void;
  onOpenDirectory: () => void;
  onAddCapabilities: () => void;
  onSeeAll: (sectionKey: string) => void;
  onPost: () => void;
  onNotInterested: (sectionKey: string, opportunityId: string) => void;
}

export default function DiscoverView({
  displayName,
  feed,
  filters,
  onFiltersChange,
  onSearch,
  onOpenDirectory,
  onAddCapabilities,
  onSeeAll,
  onPost,
  onNotInterested,
}: DiscoverViewProps) {
  const { t } = useTranslation(["discover", "opportunities", "ranking"]);
  const [showFilters, setShowFilters] = useState(false);

  return (
    <>
      {/* [IMP33] The greeting moved ABOVE the search bar and became the
          screen's real <h1> at the display scale — no screen should open
          with its chrome louder than its subject. */}
      <div className="vy-page-head">
        {displayName !== null ? (
          <h1>{t("discover:home.greeting", { name: displayName.split(" ")[0] })}</h1>
        ) : (
          <div className="vy-skeleton" style={{ height: 40, width: 260, maxWidth: "70%" }} aria-hidden="true" />
        )}
      </div>

      {/* [Fix #8] Search-first home, WorkIndia/Upwork lens: intent bar +
          one-tap directory entry, both above the feed and above the fold. */}
      <div className="vy-stack">
        <IntentBar onSearch={onSearch} />
        <div className="vy-row" style={{ flexWrap: "wrap" }}>
          <button className="vy-btn vy-btn-secondary" onClick={onOpenDirectory}>
            ▤ {t("discover:home.openDirectory")}
          </button>
          <button className="vy-btn vy-btn-secondary" aria-expanded={showFilters} onClick={() => setShowFilters((v) => !v)}>
            {activeFilterCount(filters) > 0
              ? t("discover:businesses.filtersActive", { count: activeFilterCount(filters) })
              : t("discover:businesses.filters")}
          </button>
        </div>
        {showFilters && <FilterSheet filters={filters} onChange={onFiltersChange} />}
      </div>

      {/* [IMP33] Skeletons that occupy the real grid's shape, so the feed
          resolves in place instead of jumping when it lands. */}
      {feed === null && <SkeletonGrid count={6} />}
      {feed?.enrichment_prompt && (
        <div className="vy-card">
          <p>{t(`discover:enrichment.${feed.enrichment_prompt}` as "enrichment.sparseProfile")}</p>
          <button className="vy-btn vy-btn-secondary" style={{ marginTop: 8 }} onClick={onAddCapabilities}>
            {t("discover:home.addCapabilities")}
          </button>
        </div>
      )}

      {feed?.sponsored?.map((item) => <OpportunityCard key={`sponsored-${item.id}`} item={item} variant="sponsored" />)}

      {feed?.sections.map((section, sectionIndex) => (
        // [IMP33] Each section arrives as one unit (RevealSection), with
        // its own cards staggering inside it. Timing rationale lives in
        // Motion.tsx.
        <RevealSection key={section.key} index={sectionIndex} className="vy-stack">
          <div className="vy-row" style={{ justifyContent: "space-between" }}>
            <h2 className="vy-section-title">{t(`discover:home.section${section.key.replace(/_(.)/g, (_, c) => c.toUpperCase()).replace(/^(.)/, (c) => c.toUpperCase())}` as "home.sectionForYou")}</h2>
            {section.total_available > section.items.length && (
              <button className="vy-btn vy-btn-ghost" style={{ fontSize: 13 }} onClick={() => onSeeAll(section.key)}>
                {t("discover:home.seeAll", { count: section.total_available })}
              </button>
            )}
          </div>
          {/* [IMP33 — F4 "2-column result lists" at ≥600, a third column
              only at ≥1280 where a card is still readable]. */}
          <div className="vy-grid vy-grid-3">
            {section.items.map((item, i) => (
              <OpportunityCard
                key={item.id}
                item={item}
                variant="feed"
                index={i}
                // UX08 per-card Not interested: removes the card from this
                // section immediately (optimistic, handled by the caller).
                onNotInterested={() => onNotInterested(section.key, item.id)}
              />
            ))}
          </div>
        </RevealSection>
      ))}

      {feed && feed.sections.length === 0 && !feed.enrichment_prompt && (
        // [IMP33] A real empty state with a next action, not one muted
        // sentence in a void.
        <EmptyState
          mark="✦"
          title={t("discover:home.noOpportunities")}
          body={t("discover:home.emptyBody")}
          action={
            <button className="vy-btn vy-btn-primary" onClick={onPost}>
              {t("discover:home.emptyAction")}
            </button>
          }
        />
      )}
    </>
  );
}

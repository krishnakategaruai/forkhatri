"use client";

// [IMP38 — Refactor C] Businesses & Professionals directory, presentational
// half — markup moved verbatim out of app/businesses/page.tsx (see that
// file for the FR15/FR17 and IMP33 sidebar reasoning). Data in, events out;
// the only state here is whether the phone filter panel is open.
import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { BroadeningOption, SearchResponse } from "@/lib/sdk";
import IntentBar, { type ParsedIntent } from "@/app/components/IntentBar";
import LivingCard from "@/app/components/LivingCard";
import { useReputationText } from "@/app/components/Reputation";
import FilterSheet, { activeFilterCount, type Filters } from "@/app/components/FilterSheet";
import { SkeletonGrid } from "@/app/components/States";
import { useRoutes } from "@/app/host/HostProvider";
import { signalLabel } from "@/app/components/opportunity/labels";
import { BadgeList } from "@/app/components/trust/Badges";

export interface BusinessesViewProps {
  response: SearchResponse | null;
  loading: boolean;
  filters: Filters;
  onFiltersChange: (next: Filters) => void;
  onSearch: (intent: ParsedIntent) => void;
  onBroaden: (optionId: string) => void;
}

export default function BusinessesView({ response, loading, filters, onFiltersChange, onSearch, onBroaden }: BusinessesViewProps) {
  const { t } = useTranslation(["discover", "common", "ranking"]);
  const [showFilters, setShowFilters] = useState(false);
  const reputationText = useReputationText();
  const routes = useRoutes();

  function broadeningLabel(o: BroadeningOption): string {
    if (o.label === "radius") return t("discover:broaden.radius", { km: o.id.replace("radius_", "") });
    return t(`discover:broaden.${o.label}` as "broaden.remove_filter");
  }

  const relevanceLabel = (key: string) => signalLabel(t, key);
  const resultCount = response?.results.length ?? 0;

  return (
    <>
      <div className="vy-row" style={{ justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
        <div className="vy-page-head">
          <h1>{t("discover:businesses.title")}</h1>
          {response && (
            <p className="vy-muted" role="status" aria-live="polite">
              {t("discover:businesses.resultsCount", { count: resultCount })}
            </p>
          )}
        </div>
        <a className="vy-btn vy-btn-ghost" href={routes.myListings} style={{ fontSize: 13 }}>
          {t("common:action.myListings")}
        </a>
      </div>

      <div className="vy-with-sidebar">
        {/* Desktop: filters always visible beside the results. */}
        <aside className="vy-sidebar vy-desktop-only">
          <h2 className="vy-section-title" style={{ marginBottom: 10 }}>
            {t("discover:businesses.filters")}
          </h2>
          <FilterSheet filters={filters} onChange={onFiltersChange} />
        </aside>

        <div className="vy-stack" style={{ gap: "var(--space-5)", minWidth: 0 }}>
          <IntentBar onSearch={onSearch} />
          {/* Phone: the existing collapsible panel, unchanged. */}
          <div className="vy-mobile-only">
            <div className="vy-row">
              <button className="vy-btn vy-btn-secondary" aria-expanded={showFilters} onClick={() => setShowFilters((v) => !v)}>
                {activeFilterCount(filters) > 0
                  ? t("discover:businesses.filtersActive", { count: activeFilterCount(filters) })
                  : t("discover:businesses.filters")}
              </button>
            </div>
            {showFilters && (
              <div style={{ marginTop: 12 }}>
                <FilterSheet filters={filters} onChange={onFiltersChange} />
              </div>
            )}
          </div>

          {loading && <SkeletonGrid count={6} />}

          {response?.sponsored && response.sponsored.length > 0 && (
            <div className="vy-grid vy-grid-3">
              {response.sponsored.map((r) => (
                <LivingCard
                  key={`sponsored-${r.listing.id}`}
                  href={routes.listing(r.listing.id)}
                  morphName={`listing-${r.listing.id}`}
                  title={r.listing.name}
                  subtitle={`${r.listing.locality} · ${[...r.listing.category_labels, ...r.listing.capability_labels].join(", ") || "—"}`}
                  verified={r.listing.verification_state === "verified"}
                  verificationLabel={t("discover:businesses.verifiedLabel")}
                  sponsored
                  meta={reputationText(r.listing.reputation)}
                />
              ))}
            </div>
          )}

          {response && response.results.length > 0 && (
            <div className="vy-stack" style={{ gap: "var(--space-4)" }}>
              {response.degraded && response.notice && <p className="vy-muted">{t(`discover:notice.${response.notice}` as "notice.degraded")}</p>}
              <div className="vy-grid vy-grid-3">
                {response.results.map((r, i) => (
                  <LivingCard
                    key={r.listing.id}
                    index={i}
                    href={routes.listing(r.listing.id)}
                    morphName={`listing-${r.listing.id}`}
                    title={r.listing.name}
                    subtitle={`${r.listing.locality} · ${[...r.listing.category_labels, ...r.listing.capability_labels].join(", ") || "—"}`}
                    verified={r.listing.verification_state === "verified"}
                    verificationLabel={t("discover:businesses.verifiedLabel")}
                    meta={[
                      reputationText(r.listing.reputation),
                      r.distance_km != null ? t("discover:businesses.distanceAway", { km: r.distance_km }) : null,
                      relevanceLabel(r.relevance_reason),
                    ]
                      .filter(Boolean)
                      .join(" · ")}
                  >
                    <BadgeList badges={r.listing.badges} compact max={3} />
                  </LivingCard>
                ))}
              </div>
            </div>
          )}

          {response && response.results.length === 0 && (
            // [IMP33] The zero-result state keeps FR17's explicit, labelled
            // broadening chips (never a silent relaxation) inside the shared
            // empty-state frame.
            <div className="vy-empty">
              <span className="vy-empty-mark" aria-hidden="true">◌</span>
              <p>{t(`discover:notice.${response.notice ?? "noMatch"}` as "notice.noMatch")}</p>
              <div className="vy-row" style={{ flexWrap: "wrap", justifyContent: "center" }}>
                {response.broadening_options.map((o) => (
                  <button key={o.id} className="vy-chip" style={{ cursor: "pointer" }} onClick={() => onBroaden(o.id)}>
                    {broadeningLabel(o)}
                  </button>
                ))}
              </div>
              {response.fallback && (
                <a className="vy-btn vy-btn-secondary" href={response.fallback.post_link}>
                  {t("discover:businesses.postWhatYouNeed")}
                </a>
              )}
            </div>
          )}

          {!response && !loading && (
            <div className="vy-empty">
              <span className="vy-empty-mark" aria-hidden="true">⌕</span>
              <p>{t("discover:businesses.hint")}</p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

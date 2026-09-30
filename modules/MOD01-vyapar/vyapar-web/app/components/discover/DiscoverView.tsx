"use client";

// [IMP38 — Refactor C] Discover (home), presentational half. Data in,
// events out.
//
// [Design language 2026-09-29 — owner: "this complete design is old
// fashioned"; references/design-language-2026-09-29.md §11] FE2's data
// logic (URL filters, rows vs flat results, facets, preview counts, saved
// searches, widen / drop-last empty state) is kept as it was; the page
// around it is rebuilt:
//   Hero      greeting · Opportunities | Businesses icon tabs · search
//             pill (field, mic, Where on desktop, one brand Search).
//   Trades    tinted icon tiles that filter in place; "All" → every
//             category in a sheet.
//   Chips     sticky: Filters (n) · location (phone) · Near me · Today ·
//             ₹20,000+ a month · Verified · Work from home · Night shift.
//   Curated   ixigo-style themed rows with icons, snap and arrows.
//   Filtered  count heading, Sort, applied chips, Save this search, one
//             flat grid (1 → 2 → 3 → 4 columns).
//   Filters   no permanent sidebar: a bottom sheet on phones, a right
//             drawer on desktop, FE2's sections inside.
//   States    card-shaped skeletons, an empty state that offers to widen,
//             and an error state with Try again.
import { useTranslation } from "react-i18next";
import { Plus, SearchX, Sparkles, UserPlus, WifiOff } from "lucide-react";
import type { FeedFacets, FeedFilterValues, FeedRow, OpportunityCard } from "@/lib/sdk";
import DiscoverHero from "./DiscoverHero";
import TradeRail from "./TradeRail";
import DiscoverFilterBar from "./DiscoverFilterBar";
import FeedRows from "./FeedRows";
import DiscoverCard from "./DiscoverCard";
import ResultsHeader from "./ResultsHeader";

export interface DiscoverViewProps {
  displayName: string | null;
  filters: FeedFilterValues;
  curated: boolean;
  /** Curated mode: themed rows (null while loading). */
  rows: FeedRow[] | null;
  enrichmentPrompt: string | null;
  /** Filtered mode: the ranked list and its total (null while loading). */
  items: OpportunityCard[] | null;
  total: number | null;
  facets: FeedFacets | null;
  place: string | null;
  defaultRadiusKm: number | null;
  skillLabel: (slug: string) => string;
  searchName: string;
  onFiltersChange: (next: FeedFilterValues) => void;
  onSeeAllRow: (row: FeedRow) => void;
  preview: (draft: FeedFilterValues) => Promise<{ total: number; facets: FeedFacets }>;
  onAddCapabilities: () => void;
  onPost: () => void;
  /** The filter to drop for the empty state's "remove the last filter". */
  lastFilterRemoved: FeedFilterValues | null;
  /** The current list failed to load and has nothing to show. */
  failed?: boolean;
  onRetry?: () => void;
  /** [Critique N2] rows API: rows built from the viewer's skills exist (undefined: infer from the rows). */
  hasPersonalRows?: boolean;
  /** [Critique N2] rows API: the viewer's own work categories, strongest first. */
  viewerCategories?: string[];
}

function SkeletonCards({ count, strip }: { count: number; strip?: boolean }) {
  const { t } = useTranslation("common");
  return (
    <div className={strip ? "vy-row2-strip vy-skel-strip" : "vy-dgrid2"} aria-busy="true">
      <span className="vy-visually-hidden" role="status">{t("state.loading", { defaultValue: "Loading" })}</span>
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className={strip ? "vy-row2-cell" : undefined} aria-hidden="true">
          <div className="vy-card vy-ocard vy-ocard-skel">
            <div className="vy-skeleton" style={{ width: 44, height: 44, borderRadius: 14 }} />
            <div className="vy-skeleton" style={{ height: 18, width: "85%" }} />
            <div className="vy-skeleton" style={{ height: 22, width: "55%" }} />
            <div className="vy-skeleton" style={{ height: 14, width: "70%" }} />
          </div>
        </div>
      ))}
    </div>
  );
}

function RowsSkeleton() {
  return (
    <div className="vy-rows2">
      {[0, 1].map((r) => (
        <section key={r} className="vy-row2" aria-hidden={r > 0}>
          <div className="vy-row2-head">
            <div className="vy-skeleton" style={{ height: 24, width: 200 }} />
          </div>
          <SkeletonCards count={4} strip />
        </section>
      ))}
    </div>
  );
}

function StateBlock({ icon, title, body, action }: { icon: React.ReactNode; title: string; body: string; action?: React.ReactNode }) {
  return (
    <div className="vy-empty">
      <span className="vy-empty-mark" aria-hidden="true">{icon}</span>
      <h2 className="vy-card-title">{title}</h2>
      <p>{body}</p>
      {action}
    </div>
  );
}

/** [imp-backend-b L13 — few rows on a sparse home] never a blank gap: say
 *  how to see more (add skills), and offer the other side (post a need).
 *  [2026-09-30, owner: "this too"] one calm card: the icon tile beside the
 *  title, one line under it, both actions inside the card on one row;
 *  nothing can overflow (the actions wrap on a phone). */
function SparseNudge({ skills, onSkills, onPost }: { skills: boolean; onSkills: () => void; onPost: () => void }) {
  const { t } = useTranslation(["discover", "explore"]);
  return (
    <div className="vy-nudge">
      <div className="vy-nudge-head">
        <span className="vy-trade-tile vy-trade-indigo" aria-hidden="true">
          <Sparkles size={22} strokeWidth={1.9} />
        </span>
        <div className="vy-nudge-text">
          <h2 className="vy-card-title">{t("explore:sparse.title")}</h2>
          <p>{t("explore:sparse.body")}</p>
        </div>
      </div>
      <div className="vy-nudge-actions">
        {skills && (
          <button type="button" className="vy-btn vy-btn-soft" onClick={onSkills}>
            <UserPlus size={18} aria-hidden="true" />
            {t("discover:home.addCapabilities")}
          </button>
        )}
        <button type="button" className="vy-btn vy-btn-secondary" onClick={onPost}>
          <Plus size={18} aria-hidden="true" />
          {t("explore:sparse.post")}
        </button>
      </div>
    </div>
  );
}

export default function DiscoverView(p: DiscoverViewProps) {
  const { t } = useTranslation(["discover", "explore"]);
  const f = p.filters;

  const failed = p.failed ? (
    <StateBlock
      icon={<WifiOff size={26} strokeWidth={1.8} />}
      title={t("explore:state.errorTitle")}
      body={t("explore:state.errorBody")}
      action={
        <button type="button" className="vy-btn vy-btn-secondary" onClick={p.onRetry}>
          {t("explore:state.retry")}
        </button>
      }
    />
  ) : null;

  return (
    <div className="vy-discover2">
      <DiscoverHero
        personal={p.hasPersonalRows ?? !!p.rows?.some((r) => r.key === "for_you" || r.key.startsWith("category:"))}
        firstName={p.displayName !== null ? p.displayName.split(" ")[0] : null}
        query={f.q ?? ""}
        onQuery={(q) => p.onFiltersChange({ ...f, q: q || null })}
        place={p.place}
        radiusKm={f.radius_km ?? null}
        defaultRadiusKm={p.defaultRadiusKm}
        onRadius={(km) => p.onFiltersChange({ ...f, radius_km: km })}
      />

      <TradeRail skills={f.skills ?? []} viewerCategories={p.viewerCategories} onSkills={(skills) => p.onFiltersChange({ ...f, skills })} />

      <DiscoverFilterBar filters={f} onChange={p.onFiltersChange} place={p.place} defaultRadiusKm={p.defaultRadiusKm} />


      {p.curated ? (
        failed && p.rows === null ? (
          failed
        ) : p.rows === null ? (
          <RowsSkeleton />
        ) : p.rows.length === 0 ? (
          <SparseNudge skills onSkills={p.onAddCapabilities} onPost={p.onPost} />
        ) : (
          <>
            <FeedRows rows={p.rows} onSeeAll={p.onSeeAllRow} />
            {(p.enrichmentPrompt || p.rows.length <= 3) && <SparseNudge skills={!!p.enrichmentPrompt} onSkills={p.onAddCapabilities} onPost={p.onPost} />}
          </>
        )
      ) : (
        <section className="vy-results2" aria-label={t("explore:filters.applied")}>
          <ResultsHeader total={p.total} place={p.place} filters={f} onChange={p.onFiltersChange} skillLabel={p.skillLabel} searchName={p.searchName} />
          {failed && p.items === null ? (
            failed
          ) : p.items === null ? (
            <SkeletonCards count={8} />
          ) : p.items.length === 0 ? (
            <StateBlock
              icon={<SearchX size={26} strokeWidth={1.8} />}
              title={t("explore:filters.noResults")}
              body={t("explore:filters.noResultsBody")}
              action={
                // [2026-09-30] Zero results offer ways OUT (wider, every
                // trade, fewer filters) — never "Save this search".
                <div className="vy-row" style={{ flexWrap: "wrap", justifyContent: "center", gap: 8 }}>
                  {f.radius_km && f.radius_km < 50 ? (
                    <button className="vy-btn vy-btn-secondary" onClick={() => p.onFiltersChange({ ...f, radius_km: Math.min(50, Math.max(25, f.radius_km! * 2)) })}>
                      {t("explore:fbar.widen", { km: Math.min(50, Math.max(25, f.radius_km * 2)) })}
                    </button>
                  ) : null}
                  {(f.skills?.length ?? 0) > 0 && (
                    <button className="vy-btn vy-btn-secondary" onClick={() => p.onFiltersChange({ ...f, skills: [] })}>
                      {t("explore:fbar.seeAllTrades")}
                    </button>
                  )}
                  {p.lastFilterRemoved && (
                    <button className="vy-btn vy-btn-ghost" onClick={() => p.onFiltersChange(p.lastFilterRemoved!)}>
                      {t("explore:results.dropLast")}
                    </button>
                  )}
                </div>
              }
            />
          ) : (
            <div className="vy-dgrid2">
              {p.items.map((item) => (
                <DiscoverCard key={item.id} item={item} />
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}

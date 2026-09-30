"use client";

// [FE2 — owner review 2026-09-29] The line above the results: how many
// ("24 opportunities near Dilsukhnagar"), the applied-filter chips, Sort on
// the right (a plain select — five options, keyboard and screen-reader
// friendly), and "Save this search" with its alert bell.
// Phone: the sticky bar with "Filters (3)", the Sort select and quick chips
// (Jobs · Near me 5 km · Today · Verified) is <MobileFilterBar>.
import { useTranslation } from "react-i18next";
import type { FeedFilterValues } from "@/lib/sdk";
import Icon from "@/app/components/Icon";
import SaveSearch from "./SaveSearch";

export const SORTS = ["relevance", "distance", "freshness", "salary_high", "verified_first"] as const;

export function SortSelect({ value, onChange, compact = false }: { value: string; onChange: (s: string) => void; compact?: boolean }) {
  const { t } = useTranslation(["explore"]);
  return (
    <label className={compact ? "vy-sort vy-sort-compact" : "vy-sort"}>
      <Icon name="sort" size={15} />
      <span className={compact ? "vy-visually-hidden" : "vy-sort-label"}>{t("explore:filters.sort")}</span>
      <select value={value || "relevance"} onChange={(e) => onChange(e.target.value)} aria-label={t("explore:filters.sort")}>
        {SORTS.map((s) => (
          <option key={s} value={s}>
            {t(`explore:sort.${s}`)}
          </option>
        ))}
      </select>
    </label>
  );
}

export default function ResultsHeader({
  total,
  place,
  filters,
  onChange,
  searchName,
}: {
  total: number | null;
  place: string | null;
  filters: FeedFilterValues;
  onChange: (next: FeedFilterValues) => void;
  /** Kept for callers; applied values now show in the filter buttons. */
  skillLabel?: (slug: string) => string;
  searchName: string;
}) {
  const { t } = useTranslation(["explore"]);
  const heading =
    total === null
      ? t("explore:results.loading")
      : place && (filters.radius_km || filters.sort === "distance")
        ? t("explore:results.countNear", { count: total, place })
        : t("explore:results.count", { count: total });
  return (
    <div className="vy-rhead">
      <div className="vy-rhead-top">
        <h2 className="vy-rhead-title" role="status" aria-live="polite">{heading}</h2>
        <div className="vy-desktop-only">
          <SortSelect value={String(filters.sort ?? "relevance")} onChange={(s) => onChange({ ...filters, sort: s })} />
        </div>
      </div>
      {/* [2026-09-30] Applied values live in the filter buttons, not in a
          second chip row; saving a search only makes sense with results. */}
      {total !== null && total > 0 && <SaveSearch value={filters} name={searchName} />}
    </div>
  );
}

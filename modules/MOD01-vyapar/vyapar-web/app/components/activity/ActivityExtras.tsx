"use client";

// [FE2] Two more things a member comes back to in Activity:
//  - Contracts: how many are running and how many wait on them, one tap to
//    the Contracts screen (the command hub keeps its five destinations);
//  - Saved searches (imp-backend-b §5): each one opens Discover with its
//    filters applied, says whether alerts are on, and can be deleted.
import Link from "next/link";
import { useTranslation } from "react-i18next";
import type { SavedSearch } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import { formatDate } from "@/lib/format";
import Icon from "@/app/components/Icon";
import { useContracts, useSavedSearches } from "@/app/hooks/trade";
import { filtersToQuery } from "@/app/components/discover/feedFilters";
import { summaryNeedsMe } from "@/app/components/contracts/model";

export function useActivityExtras() {
  const contracts = useContracts({ role: "all", limit: 50 });
  const saved = useSavedSearches();
  const items = contracts.data?.items ?? [];
  const live = items.filter((c) => ["draft", "proposed", "active", "disputed"].includes(c.state));
  return {
    contracts: { total: items.length, live: live.length, needsYou: items.filter(summaryNeedsMe).length },
    saved,
    hasAny: items.length > 0 || (saved.data?.length ?? 0) > 0,
  };
}

export default function ActivityExtras({ extras }: { extras: ReturnType<typeof useActivityExtras> }) {
  const { t, i18n } = useTranslation(["explore", "contracts", "common"]);
  const sdk = useSdk();
  const { contracts, saved } = extras;

  async function remove(s: SavedSearch) {
    saved.setData((list) => (list ? list.filter((x) => x.id !== s.id) : list));
    await sdk.savedSearches.remove(s.id).catch(() => saved.refresh());
  }

  function openHref(s: SavedSearch): string {
    const qs = filtersToQuery({ ...s.filters, q: s.query || s.filters.q || null });
    return qs ? `/?${qs}` : "/";
  }

  return (
    <div className="vy-grid">
      {contracts.total > 0 && (
        <Link href="/contracts" className="vy-card vy-row" style={{ textDecoration: "none", justifyContent: "space-between", gap: 12 }}>
          <span className="vy-row" style={{ gap: 12 }}>
            <Icon name="contract" size={20} />
            <span className="vy-stack" style={{ gap: 2 }}>
              <strong>{t("contracts:nav.title")}</strong>
              <span className="vy-muted">{t("explore:activity.contractsLine", { count: contracts.live })}</span>
            </span>
          </span>
          {contracts.needsYou > 0 && (
            <span className="vy-state-chip" data-tone="action">{t("explore:activity.needsYou", { count: contracts.needsYou })}</span>
          )}
        </Link>
      )}
      {saved.data && saved.data.length > 0 && (
        <section id="saved-searches" className="vy-stack" style={{ gap: 8 }} aria-labelledby="saved-title">
          <h2 id="saved-title" className="vy-section-title">{t("explore:saved.title")}</h2>
          {saved.data.map((s) => (
            <div key={s.id} className="vy-card vy-row" style={{ justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
              <Link href={openHref(s)} style={{ textDecoration: "none", minWidth: 0, flex: 1 }} className="vy-stack">
                <strong style={{ color: "var(--text-primary)" }}>{s.name || s.query || t("explore:saved.defaultName")}</strong>
                <span className="vy-muted">
                  {[s.alert ? t("explore:saved.alertOn") : t("explore:saved.alertOff"), t("explore:saved.since", { date: formatDate(s.created_at, i18n.language) })].join(" · ")}
                </span>
              </Link>
              <button type="button" className="vy-btn vy-btn-ghost" style={{ fontSize: 13 }} onClick={() => remove(s)}>
                {t("explore:saved.delete")}
              </button>
            </div>
          ))}
        </section>
      )}
    </div>
  );
}

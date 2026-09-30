"use client";

// [FE2] Two more things a member comes back to in Activity:
//  - Contracts: how many are running and how many wait on them, one tap to
//    the Contracts screen (the command hub keeps its five destinations);
//  - Saved searches (imp-backend-b §5): each one opens Discover with its
//    filters applied, says whether alerts are on, and can be deleted.
// [Design language 2026-09-29] Both drawn as rows of the account list
// (tile, label, hint, count or action) so they match the groups beside them.
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { BellRing, BellOff, ChevronRight, FileText, Search, X } from "lucide-react";
import type { SavedSearch } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import { formatDate } from "@/lib/format";
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
    <>
      {contracts.total > 0 && (
        <div className="vy-card vy-acct-list">
          <Link href="/contracts" className="vy-acct-row" transitionTypes={["vy-forward"]} data-badge={contracts.needsYou > 0 ? "" : undefined}>
            <span className="vy-acct-tile" data-tint="indigo" aria-hidden="true">
              <FileText size={20} strokeWidth={1.9} />
            </span>
            <span className="vy-acct-row-text">
              <span className="vy-acct-row-label">{t("contracts:nav.title")}</span>
              <span className="vy-acct-row-hint">{t("explore:activity.contractsLine", { count: contracts.live })}</span>
            </span>
            <span className="vy-acct-row-end">
              {contracts.needsYou > 0 ? (
                <span className="vy-state-chip" data-tone="action">{t("explore:activity.needsYou", { count: contracts.needsYou })}</span>
              ) : (
                <ChevronRight size={18} strokeWidth={2} aria-hidden="true" />
              )}
            </span>
          </Link>
        </div>
      )}
      {saved.data && saved.data.length > 0 && (
        <section id="saved-searches" className="vy-acct-section" aria-labelledby="saved-title">
          <div className="vy-acct-section-head">
            <h2 id="saved-title" className="vy-section-title">{t("explore:saved.title")}</h2>
            <p>{saved.data.length}</p>
          </div>
          <div className="vy-card vy-acct-list">
            {saved.data.map((s) => (
              <div key={s.id} className="vy-acct-row" data-badge="" style={{ cursor: "default" }}>
                <span className="vy-acct-tile" data-tint="sky" aria-hidden="true">
                  <Search size={20} strokeWidth={1.9} />
                </span>
                <Link href={openHref(s)} className="vy-acct-row-text" style={{ textDecoration: "none", color: "inherit" }}>
                  <span className="vy-acct-row-label">{s.name || s.query || t("explore:saved.defaultName")}</span>
                  <span className="vy-acct-row-hint">
                    {s.alert ? <BellRing size={13} strokeWidth={2} aria-hidden="true" style={{ verticalAlign: "-2px" }} /> : <BellOff size={13} strokeWidth={2} aria-hidden="true" style={{ verticalAlign: "-2px" }} />}{" "}
                    {[s.alert ? t("explore:saved.alertOn") : t("explore:saved.alertOff"), t("explore:saved.since", { date: formatDate(s.created_at, i18n.language) })].join(" · ")}
                  </span>
                </Link>
                <span className="vy-acct-row-end">
                  <button type="button" className="vy-iconbtn" onClick={() => remove(s)} aria-label={`${t("explore:saved.delete")}: ${s.name || s.query || t("explore:saved.defaultName")}`} title={t("explore:saved.delete")}>
                    <X size={18} strokeWidth={2} aria-hidden="true" />
                  </button>
                </span>
              </div>
            ))}
          </div>
        </section>
      )}
    </>
  );
}

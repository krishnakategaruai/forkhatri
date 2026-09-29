"use client";

// [FE2 — imp-backend-d] /contracts — the member's contracts, split by side:
// "I'm paying" (client) and "I'm doing the work" (provider). Phone: a list of
// rows that open /contracts/[id]. ≥1024px: list + detail split pane (the same
// primitive Enquiries uses), so a contract opens beside the list.
import { useState } from "react";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import type { ContractRole, ContractSummary } from "@/lib/sdk";
import { formatDate, formatRupees } from "@/lib/format";
import Screen from "@/app/components/Screen";
import { EmptyState, SkeletonGrid } from "@/app/components/States";
import { useContracts } from "@/app/hooks/trade";
import ContractDetail from "@/app/components/contracts/ContractDetail";
import { stateTone, summaryNeedsMe } from "@/app/components/contracts/model";

type Tab = ContractRole | "all";

function RowBody({ c }: { c: ContractSummary }) {
  const { t, i18n } = useTranslation(["contracts"]);
  const needs = summaryNeedsMe(c);
  const tone = needs ? "action" : stateTone(c.state);
  return (
    <>
      <div className="vy-row" style={{ justifyContent: "space-between", gap: 8, alignItems: "baseline" }}>
        <strong style={{ color: "var(--text-primary)" }}>{c.title}</strong>
        <span className="vy-timeline-amount">{formatRupees(c.total_paise, i18n.language)}</span>
      </div>
      <span className="vy-muted">
        {[c.counterpart_name, t(`contracts:kind.${c.kind}`), t("contracts:list.updated", { date: formatDate(c.updated_at, i18n.language) })]
          .filter(Boolean)
          .join(" · ")}
      </span>
      <span style={{ marginTop: 4 }}>
        <span className="vy-state-chip" data-tone={tone === "action" ? "action" : tone === "done" ? "done" : tone === "warn" ? "warn" : undefined}>
          {needs ? t("contracts:list.needsYou") : t(`contracts:state.${c.state}`)}
        </span>
      </span>
    </>
  );
}

export default function ContractsPage() {
  const { t } = useTranslation(["contracts"]);
  const [tab, setTab] = useState<Tab>("all");
  const [selected, setSelected] = useState<string | null>(null);
  const list = useContracts({ role: tab, limit: 50 });
  const items = list.data?.items ?? null;
  const current = selected ?? items?.[0]?.id ?? null;

  return (
    <Screen width="console">
      <div className="vy-page-head">
        <h1>{t("contracts:list.title")}</h1>
        <p>{t("contracts:list.subtitle")}</p>
      </div>
      <div className="vy-segmented" role="tablist" style={{ alignSelf: "flex-start", display: "inline-flex" }}>
        {(["all", "client", "provider"] as Tab[]).map((k) => (
          <button
            key={k}
            role="tab"
            aria-selected={tab === k}
            onClick={() => {
              setTab(k);
              setSelected(null);
            }}
          >
            {k === "all" ? t("contracts:list.all") : k === "client" ? t("contracts:list.asClient") : t("contracts:list.asProvider")}
          </button>
        ))}
      </div>

      {items === null ? (
        <SkeletonGrid count={3} grid={false} />
      ) : items.length === 0 ? (
        <EmptyState
          mark="◌"
          title={t("contracts:list.emptyTitle")}
          body={t("contracts:list.emptyBody")}
          action={
            <Link className="vy-btn vy-btn-secondary" href="/enquiries/mine" style={{ textDecoration: "none" }}>
              {t("contracts:list.emptyAction")}
            </Link>
          }
        />
      ) : (
        <div className="vy-pane">
          <div className="vy-pane-list vy-stack" style={{ gap: 8 }}>
            {items.map((c) => (
              <div key={c.id}>
                <Link className="vy-card vy-contract-row vy-pane-row-mobile" href={`/contracts/${c.id}`} transitionTypes={["vy-forward"]}>
                  <RowBody c={c} />
                </Link>
                <button
                  type="button"
                  className="vy-card vy-contract-row vy-pane-row-console"
                  aria-current={current === c.id}
                  onClick={() => setSelected(c.id)}
                >
                  <RowBody c={c} />
                </button>
              </div>
            ))}
          </div>
          <div className="vy-pane-detail vy-console-only">
            {current ? (
              <ContractDetail key={current} id={current} embedded onChanged={() => void list.refresh()} />
            ) : (
              <p className="vy-muted">{t("contracts:list.selectHint")}</p>
            )}
          </div>
        </div>
      )}
    </Screen>
  );
}

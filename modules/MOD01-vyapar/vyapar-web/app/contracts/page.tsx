"use client";

// [FE2 — imp-backend-d] /contracts — the member's contracts, split by side:
// "I'm paying" (client) and "I'm doing the work" (professional). Phone: rows
// that open /contracts/[id]. ≥1024px: list + detail split pane (the same
// primitive Requests uses), so a contract opens beside the list.
// [Design language 2026-09-29] Rows read avatar · what the work is · who and
// when · amount, with a quiet state chip; "Needs you" when it is your turn.
import { useState } from "react";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { FileSignature, Inbox } from "lucide-react";
import type { ContractRole, ContractSummary } from "@/lib/sdk";
import { formatDayMonth, formatRupees } from "@/lib/format";
import Screen from "@/app/components/Screen";
import { SkeletonGrid } from "@/app/components/States";
import DealsEmpty from "@/app/components/deals/Empty";
import { useContracts } from "@/app/hooks/trade";
import ContractDetail from "@/app/components/contracts/ContractDetail";
import { stateTone, summaryNeedsMe } from "@/app/components/contracts/model";
import "@/app/styles/deals-2026.css";

type Tab = ContractRole | "all";

function toneOf(c: ContractSummary): "action" | "done" | "warn" | "wait" | undefined {
  if (summaryNeedsMe(c)) return "wait";
  const t = stateTone(c.state);
  return t === "done" ? "done" : t === "warn" ? "warn" : t === "held" ? "action" : undefined;
}

function RowBody({ c }: { c: ContractSummary }) {
  const { t, i18n } = useTranslation(["contracts"]);
  const needs = summaryNeedsMe(c);
  const who = c.counterpart_name ?? "";
  return (
    <>
      <span className="vy-cl-mono" aria-hidden="true">{(who.trim().charAt(0) || "?").toUpperCase()}</span>
      <span className="vy-cl-body">
        <span className="vy-cl-title">{c.title}</span>
        <span className="vy-cl-meta">
          <span className="vy-dot-status" data-tone={toneOf(c)}>{needs ? t("contracts:list.needsYou") : t(`contracts:state.${c.state}`)}</span>
          {who && <span>· {who}</span>}
        </span>
      </span>
      <span className="vy-cl-end">
        <span className="vy-cl-amt vy-num">{formatRupees(c.total_paise, i18n.language)}</span>
        <time className="vy-cl-date vy-num" dateTime={c.updated_at}>{formatDayMonth(c.updated_at, i18n.language)}</time>
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
      <div className="vy-dl-page">
        <div className="vy-dl-head">
          <h1>{t("contracts:list.title")}</h1>
          <p className="vy-dl-hint">{t("contracts:list.subtitle")}</p>
        </div>
        <div className="vy-seg-solid" role="tablist" aria-label={t("contracts:list.title")}>
          {(["all", "client", "provider"] as Tab[]).map((k) => (
            <button
              key={k}
              type="button"
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
          <DealsEmpty
            icon={tab === "all" ? <FileSignature size={24} strokeWidth={1.75} aria-hidden="true" /> : <Inbox size={24} strokeWidth={1.75} aria-hidden="true" />}
            title={t("contracts:list.emptyTitle")}
            body={t("contracts:list.emptyBody")}
            action={
              <Link className="vy-btn vy-btn-secondary" href="/enquiries/mine" style={{ textDecoration: "none" }}>
                {t("contracts:list.emptyAction")}
              </Link>
            }
          />
        ) : (
          <div className="vy-cl-pane">
            <div className="vy-cl-list">
              {items.map((c) => (
                <div key={c.id}>
                  <Link className="vy-cl-row vy-pane-row-mobile" href={`/contracts/${c.id}`} transitionTypes={["vy-forward"]}>
                    <RowBody c={c} />
                  </Link>
                  <button type="button" className="vy-cl-row vy-pane-row-console" aria-current={current === c.id ? "true" : undefined} onClick={() => setSelected(c.id)}>
                    <RowBody c={c} />
                  </button>
                </div>
              ))}
            </div>
            <div className="vy-console-only">
              {current ? (
                <div className="vy-cl-detail vy-dl-embedded">
                  <ContractDetail key={current} id={current} embedded onChanged={() => void list.refresh()} />
                </div>
              ) : (
                <div className="vy-dl-pane-empty">
                  <span className="vy-dl-tile vy-dl-tile-lg" aria-hidden="true">
                    <FileSignature size={24} strokeWidth={1.75} />
                  </span>
                  <p>{t("contracts:list.selectHint")}</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </Screen>
  );
}

"use client";

// [TR035] Campaign detail (FR35, UX21): state, window, package budget and how
// much of it is allocated, every item with its own promotion state,
// pause/resume, and the campaign-level report — one screen, no sub-pages.
// Each item is a real FR30 promotion, so each carries the Sponsored label
// and its own pro-rata credit if it stops being active mid-campaign.
// [Design language 2026-09-29] Items and the report in the main column; a
// sticky receipt card (window, package, allocated, payment reference) in
// the aside with the pause / resume actions.
// Traces to: FR35, FR30, FR31, FR32, TR035, UX21
import { useCallback, useEffect, useState, use as useParamsPromise } from "react";
import { useTranslation } from "react-i18next";
import Link from "next/link";
import { AlertTriangle, ChevronLeft, ChevronRight, Layers, Pause, Play, Receipt } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { formatPaise } from "@/lib/money";
import PerformanceReport from "@/app/components/PerformanceReport";
import Screen from "@/app/components/Screen";
import { SkeletonGrid } from "@/app/components/States";
import DealsEmpty from "@/app/components/deals/Empty";
import { formatDate } from "@/lib/format";
import { promotionTone } from "@/app/promotions/tone";
import "@/app/styles/deals-2026.css";

interface CampaignItem {
  promotion_id: string;
  kind: "listing" | "opportunity";
  target_id: string;
  title: string | null;
  state: string;
  allocated_paise: number;
  credit_paise: number;
}

interface Campaign {
  id: string;
  name: string;
  state: string;
  listing_id: string;
  product_id: string;
  product_version: number;
  budget_paise: number;
  tax_paise: number;
  spent_paise: number;
  starts_at: string;
  ends_at: string;
  payment_state: string | null;
  receipt_ref: string | null;
  items: CampaignItem[];
}

export default function CampaignPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = useParamsPromise(params);
  const { t, i18n } = useTranslation(["workspace", "commercial", "common"]);
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const money = (p: number) => formatPaise(p, i18n.language);
  const fmt = (d: string) => formatDate(d, i18n.language);

  const load = useCallback(async () => {
    try {
      setCampaign(await api.get<Campaign>(`/v1/campaigns/${id}`));
    } catch (e) {
      setError(e instanceof ApiError ? String(e.detail) : t("workspace:campaigns.notFound"));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  useEffect(() => {
    // The initial load runs once per id (the pattern this module's data hooks use).
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  async function itemsState(action: "pause" | "resume") {
    setBusy(true);
    setNotice(null);
    try {
      await api.post(`/v1/campaigns/${id}/items-state`, { action });
      await load();
    } catch (e) {
      setNotice(e instanceof ApiError ? String(e.detail) : t("common:state.actionFailed"));
    } finally {
      setBusy(false);
    }
  }

  if (error)
    return (
      <Screen width="wide">
        <div className="vy-dl-page">
          <DealsEmpty tone="neutral" icon={<AlertTriangle size={24} strokeWidth={1.75} aria-hidden="true" />} title={t("workspace:campaigns.notFound")} body={error} />
        </div>
      </Screen>
    );
  if (!campaign)
    return (
      <Screen width="wide">
        <div className="vy-dl-page">
          <SkeletonGrid count={3} grid={false} />
        </div>
      </Screen>
    );

  const anyActive = campaign.items.some((i) => i.state === "active");
  const anyPaused = campaign.items.some((i) => i.state === "paused");
  const total = campaign.budget_paise + campaign.tax_paise;

  return (
    <Screen width="wide">
      <div className="vy-dl-page">
        <Link href={`/workspace/${campaign.listing_id}`} transitionTypes={["vy-back"]} className="vy-dl-back">
          <ChevronLeft size={18} strokeWidth={2} aria-hidden="true" />
          {t("workspace:title")}
        </Link>
        <div className="vy-ctx">
          <div className="vy-ctx-grid">
            <div className="vy-ctx-main">
              <div className="vy-dl-head">
                <div className="vy-dl-tags">
                  <span className="vy-dl-state" data-tone={promotionTone(campaign.state)}>{t(`commercial:state.${campaign.state}` as "state.active")}</span>
                  <span className="vy-dl-state">{t("workspace:campaigns.itemsCount", { n: campaign.items.length })}</span>
                </div>
                <h1>{campaign.name}</h1>
                <p>{t("commercial:promotion.period", { from: fmt(campaign.starts_at), to: fmt(campaign.ends_at) })}</p>
              </div>
              {notice && (
                <p className="vy-dl-notice" data-tone="bad" role="alert">
                  <AlertTriangle size={18} strokeWidth={1.75} aria-hidden="true" />
                  <span>{notice}</span>
                </p>
              )}
            </div>

            <aside className="vy-ctx-aside">
              <section className="vy-dl-sec" aria-labelledby="camp-receipt">
                <div className="vy-dl-sec-head">
                  <span className="vy-dl-tile vy-dl-tile-green" aria-hidden="true"><Receipt size={20} strokeWidth={1.75} /></span>
                  <h2 id="camp-receipt" className="vy-card-title">{t("workspace:campaigns.package")}</h2>
                  <span className="vy-dl-sec-hint">{t("commercial:promotion.version", { v: campaign.product_version })}</span>
                </div>
                <dl className="vy-dl-receipt">
                  <dt>{t("commercial:disclosure.price")}</dt>
                  <dd>{money(campaign.budget_paise)}</dd>
                  <dt>{t("commercial:disclosure.tax")}</dt>
                  <dd>{money(campaign.tax_paise)}</dd>
                  <dt className="vy-dl-receipt-total">{t("workspace:campaigns.total")}</dt>
                  <dd className="vy-dl-receipt-total"><strong>{money(total)}</strong></dd>
                  <dt>{t("workspace:campaigns.allocatedLabel")}</dt>
                  <dd>{money(campaign.spent_paise)}</dd>
                </dl>
                {campaign.receipt_ref && <p className="vy-dl-fine"><span className="vy-dl-code">{t("commercial:promotion.receiptRef", { ref: campaign.receipt_ref })}</span></p>}
                {(anyActive || anyPaused) && (
                  <div className="vy-dl-actions">
                    {anyActive && (
                      <button className="vy-btn vy-btn-secondary" disabled={busy} onClick={() => itemsState("pause")}>
                        <Pause size={16} strokeWidth={2} aria-hidden="true" /> {t("workspace:campaigns.pause")}
                      </button>
                    )}
                    {anyPaused && (
                      <button className="vy-btn vy-btn-primary" disabled={busy} onClick={() => itemsState("resume")}>
                        <Play size={16} strokeWidth={2} aria-hidden="true" /> {t("workspace:campaigns.resume")}
                      </button>
                    )}
                  </div>
                )}
              </section>
            </aside>

            <div className="vy-ctx-after">
              <section className="vy-dl-sec" aria-labelledby="camp-items">
                <div className="vy-dl-sec-head">
                  <span className="vy-dl-tile vy-dl-tile-brand" aria-hidden="true"><Layers size={20} strokeWidth={1.75} /></span>
                  <h2 id="camp-items" className="vy-card-title">{t("workspace:campaigns.itemsTitle", { n: campaign.items.length })}</h2>
                  <span className="vy-dl-sec-hint">{t("workspace:campaigns.itemsHint")}</span>
                </div>
                <div className="vy-dl-list">
                  {campaign.items.map((item) => (
                    <a key={item.promotion_id} className="vy-dl-row" href={`/${item.kind === "listing" ? "listings" : "opportunities"}/${item.target_id}`}>
                      <span className="vy-dl-row-body" style={{ gridColumn: "1 / span 2" }}>
                        <span className="vy-dl-row-title">{item.title ?? item.target_id}</span>
                        <span className="vy-dl-row-meta">
                          <span>
                            {t("workspace:campaigns.allocation", { amount: money(item.allocated_paise) })}
                            {item.credit_paise > 0 ? ` · ${t("commercial:promotion.creditApplied", { amount: money(item.credit_paise) })}` : ""}
                          </span>
                        </span>
                        <span className="vy-dl-tags" style={{ marginTop: 4 }}>
                          <span className="vy-dl-state" data-tone={promotionTone(item.state)}>{t(`commercial:state.${item.state}` as "state.active")}</span>
                        </span>
                      </span>
                      <span className="vy-dl-row-aside">
                        <ChevronRight size={18} strokeWidth={2} aria-hidden="true" style={{ color: "var(--text-tertiary)" }} />
                      </span>
                    </a>
                  ))}
                </div>
              </section>

              <PerformanceReport targetKind="campaign" targetId={campaign.id} />
            </div>
          </div>
        </div>
      </div>
    </Screen>
  );
}

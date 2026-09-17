"use client";

// [TR035] Campaign detail (FR35, UX21): state, window, package budget and how
// much of it is allocated, every item with its own boost state, pause/resume,
// and the campaign-level report — one screen, no sub-pages.
// Each item is a real FR30 boost, so each carries the Sponsored label and its
// own pro-rata credit if it stops being active mid-campaign.
// Traces to: FR35, FR30, FR31, FR32, TR035, UX21
import { useCallback, useEffect, useState, use as useParamsPromise } from "react";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "@/lib/api";
import { formatPaise } from "@/lib/money";
import PerformanceReport from "@/app/components/PerformanceReport";

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
  const fmt = (d: string) => new Date(d).toLocaleDateString(i18n.language);

  const load = useCallback(async () => {
    try {
      setCampaign(await api.get<Campaign>(`/v1/campaigns/${id}`));
    } catch (e) {
      setError(e instanceof ApiError ? String(e.detail) : t("workspace:campaigns.notFound"));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  useEffect(() => {
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

  if (error) return <main className="vy-shell"><h1>{t("workspace:campaigns.notFound")}</h1><p>{error}</p></main>;
  if (!campaign) return <main className="vy-shell"><p className="vy-muted">{t("common:state.loading")}</p></main>;

  const anyActive = campaign.items.some((i) => i.state === "active");
  const anyPaused = campaign.items.some((i) => i.state === "paused");

  return (
    <main className="vy-shell">
      <div>
        <span className="vy-badge vy-badge-member-provided">{t(`commercial:state.${campaign.state}` as "state.active")}</span>
        <h1 style={{ marginTop: 8 }}>{campaign.name}</h1>
        <a className="vy-muted" href={`/workspace/${campaign.listing_id}`}>{t("workspace:title")} →</a>
      </div>
      {notice && <p className="vy-error">{notice}</p>}

      <div className="vy-card vy-stack" style={{ gap: 6 }}>
        <span>{t("commercial:promotion.period", { from: fmt(campaign.starts_at), to: fmt(campaign.ends_at) })}</span>
        <span>{t("workspace:campaigns.budget", { amount: money(campaign.budget_paise + campaign.tax_paise) })}</span>
        <span className="vy-muted">{t("workspace:campaigns.allocated", { spent: money(campaign.spent_paise), total: money(campaign.budget_paise + campaign.tax_paise) })}</span>
        {campaign.receipt_ref && <span className="vy-muted" style={{ fontSize: 13 }}>{t("commercial:promotion.receiptRef", { ref: campaign.receipt_ref })}</span>}
      </div>

      <section className="vy-stack">
        <h2 style={{ fontSize: 16 }}>{t("workspace:campaigns.itemsTitle", { n: campaign.items.length })}</h2>
        {campaign.items.map((item) => (
          <div key={item.promotion_id} className="vy-card vy-stack" style={{ gap: 4 }}>
            <div className="vy-row" style={{ justifyContent: "space-between", flexWrap: "wrap" }}>
              <a href={`/${item.kind === "listing" ? "listings" : "opportunities"}/${item.target_id}`} style={{ textDecoration: "none" }}>
                <strong>{item.title ?? item.target_id}</strong>
              </a>
              <span className="vy-badge vy-badge-member-provided">{t(`commercial:state.${item.state}` as "state.active")}</span>
            </div>
            <span className="vy-muted" style={{ fontSize: 13 }}>
              {t("workspace:campaigns.allocation", { amount: money(item.allocated_paise) })}
              {item.credit_paise > 0 ? ` · ${t("commercial:promotion.creditApplied", { amount: money(item.credit_paise) })}` : ""}
            </span>
          </div>
        ))}
        <div className="vy-row" style={{ flexWrap: "wrap" }}>
          {anyActive && (
            <button className="vy-btn vy-btn-secondary" disabled={busy} onClick={() => itemsState("pause")}>{t("workspace:campaigns.pause")}</button>
          )}
          {anyPaused && (
            <button className="vy-btn vy-btn-primary" disabled={busy} onClick={() => itemsState("resume")}>{t("workspace:campaigns.resume")}</button>
          )}
        </div>
      </section>

      <PerformanceReport targetKind="campaign" targetId={campaign.id} />
    </main>
  );
}

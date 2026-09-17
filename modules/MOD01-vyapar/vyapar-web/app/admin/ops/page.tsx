"use client";

// [TR046] Marketplace health metrics (FR46). [TR048] Opportunity review /
// stale queue / taxonomy management (FR48). One operator screen with four
// sections, so an operator with both permissions never has to jump between
// pages for a normal day's work.
// Every metric below is exactly what the API returned — a suppressed
// (below-10) metric renders as "not enough data yet" rather than a zero or
// a guess, so an operator never mistakes "too little data" for "no activity".
// Traces to: FR46, FR48, TR046, TR048
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "@/lib/api";

interface Metric {
  level: string;
  value: number | null;
}

interface HealthResponse {
  period_days: number;
  min_group_size: number;
  metrics: Record<string, Metric>;
}

interface QueueOpportunity {
  id: string;
  title: string;
  type: string;
  state: string;
  entry_mode: string;
  flags: string[];
  age_days: number;
}

interface StaleOpportunity {
  id: string;
  title: string;
  state: string;
  age_days: number | null;
}

interface TaxonomyTerm {
  id: number;
  kind: string;
  slug: string;
  name_en: string;
  name_hi: string | null;
  name_te: string | null;
  aliases: string[];
  status: string;
}

const METRIC_KEYS = [
  "opportunity_coverage", "relevant_discovery_rate", "zero_result_rate", "opportunity_action_rate",
  "relevant_opportunity_connections", "successful_connection_rate", "discovery_to_enquiry_rate_listings",
  "freshness", "reports_per_1000_interactions", "notification_opt_out_rate", "promotion_repeat_rate",
  "revenue_paise", "refunds_paise", "time_to_first_relevant_opportunity_hours",
];

export default function AdminOpsPage() {
  const { t } = useTranslation(["adminOps", "common"]);
  const [forbidden, setForbidden] = useState(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [oppQueue, setOppQueue] = useState<QueueOpportunity[]>([]);
  const [staleQueue, setStaleQueue] = useState<StaleOpportunity[]>([]);
  const [selectedStale, setSelectedStale] = useState<string[]>([]);
  const [taxonomy, setTaxonomy] = useState<TaxonomyTerm[]>([]);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const loadAll = useCallback(async () => {
    try {
      const [h, oq, sq, tax] = await Promise.all([
        api.get<HealthResponse>("/v1/admin/marketplace-health"),
        api.get<QueueOpportunity[]>("/v1/admin/opportunities-queue"),
        api.get<StaleOpportunity[]>("/v1/admin/stale-queue"),
        api.get<TaxonomyTerm[]>("/v1/admin/taxonomy"),
      ]);
      setHealth(h);
      setOppQueue(oq);
      setStaleQueue(sq);
      setTaxonomy(tax);
    } catch (e) {
      if (e instanceof ApiError && e.status === 403) setForbidden(true);
    }
  }, []);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  async function decideOpportunity(id: string, action: "approve" | "return" | "remove") {
    setBusy(true);
    setNotice(null);
    try {
      await api.post(`/v1/admin/opportunities-queue/${id}/decide`, { action });
      await loadAll();
    } catch (e) {
      setNotice(e instanceof ApiError ? String(e.detail) : t("common:state.actionFailed"));
    } finally {
      setBusy(false);
    }
  }

  async function bulkStale(action: "remind" | "expire") {
    if (selectedStale.length === 0) return;
    setBusy(true);
    setNotice(null);
    try {
      const res = await api.post<{ changed: number }>("/v1/admin/stale-queue/bulk", {
        action, ids: selectedStale, confirm_count: selectedStale.length,
      });
      setNotice(t("adminOps:stale.done", { n: res.changed }));
      setSelectedStale([]);
      await loadAll();
    } catch (e) {
      setNotice(e instanceof ApiError ? String(e.detail) : t("common:state.actionFailed"));
    } finally {
      setBusy(false);
    }
  }

  if (forbidden) {
    return (
      <main className="vy-shell">
        <h1>{t("adminOps:title")}</h1>
        <p className="vy-muted">{t("adminOps:notOperator")}</p>
      </main>
    );
  }

  return (
    <main className="vy-shell">
      <h1>{t("adminOps:title")}</h1>
      {notice && <p className="vy-error">{notice}</p>}

      <section className="vy-stack">
        <h2 style={{ fontSize: 16 }}>{t("adminOps:health.title")}</h2>
        {health && (
          <>
            <p className="vy-muted" style={{ fontSize: 12 }}>{t("adminOps:health.minGroupNote", { n: health.min_group_size })}</p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 8 }}>
              {METRIC_KEYS.map((key) => {
                const m = health.metrics[key];
                return (
                  <div key={key} style={{ padding: "10px 12px", borderRadius: 12, background: "var(--surface-overlay)" }}>
                    <div className="vy-muted" style={{ fontSize: 12 }}>{t(`adminOps:health.metric.${key}` as "health.metric.freshness")}</div>
                    <div style={{ fontSize: 18, fontWeight: 600 }}>
                      {m.value === null ? t("adminOps:health.notEnoughData") : m.value}
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </section>

      <section className="vy-stack">
        <h2 style={{ fontSize: 16 }}>{t("adminOps:opportunitiesQueue.title")}</h2>
        {oppQueue.length === 0 && <p className="vy-muted">{t("adminOps:opportunitiesQueue.empty")}</p>}
        {oppQueue.map((o) => (
          <div key={o.id} className="vy-card vy-stack" style={{ gap: 6 }}>
            <strong>{o.title}</strong>
            <span className="vy-muted" style={{ fontSize: 13 }}>
              {o.type} · {t("adminOps:opportunitiesQueue.ageDays", { n: o.age_days })}
              {o.flags.length > 0 ? ` · ${o.flags.map((f) => t(`adminOps:opportunitiesQueue.flag.${f}` as "opportunitiesQueue.flag.source_unreachable")).join(", ")}` : ""}
            </span>
            <div className="vy-row">
              <button className="vy-btn vy-btn-primary" style={{ fontSize: 13 }} disabled={busy} onClick={() => decideOpportunity(o.id, "approve")}>{t("adminOps:opportunitiesQueue.approve")}</button>
              <button className="vy-btn vy-btn-secondary" style={{ fontSize: 13 }} disabled={busy} onClick={() => decideOpportunity(o.id, "return")}>{t("adminOps:opportunitiesQueue.return")}</button>
              <button className="vy-btn vy-btn-ghost" style={{ fontSize: 13 }} disabled={busy} onClick={() => decideOpportunity(o.id, "remove")}>{t("adminOps:opportunitiesQueue.remove")}</button>
            </div>
          </div>
        ))}
      </section>

      <section className="vy-stack">
        <h2 style={{ fontSize: 16 }}>{t("adminOps:staleQueue.title")}</h2>
        {staleQueue.length === 0 && <p className="vy-muted">{t("adminOps:staleQueue.empty")}</p>}
        {staleQueue.map((o) => (
          <label key={o.id} className="vy-row" style={{ justifyContent: "space-between" }}>
            <span>{o.title} {o.age_days != null ? `· ${t("adminOps:opportunitiesQueue.ageDays", { n: o.age_days })}` : ""}</span>
            <input type="checkbox" checked={selectedStale.includes(o.id)}
                   onChange={() => setSelectedStale((s) => (s.includes(o.id) ? s.filter((x) => x !== o.id) : [...s, o.id]))} />
          </label>
        ))}
        {staleQueue.length > 0 && (
          <div className="vy-row">
            <button className="vy-btn vy-btn-secondary" disabled={busy || selectedStale.length === 0} onClick={() => bulkStale("remind")}>
              {t("adminOps:staleQueue.remind", { n: selectedStale.length })}
            </button>
            <button className="vy-btn vy-btn-ghost" disabled={busy || selectedStale.length === 0} onClick={() => bulkStale("expire")}>
              {t("adminOps:staleQueue.expire", { n: selectedStale.length })}
            </button>
          </div>
        )}
      </section>

      <section className="vy-stack">
        <h2 style={{ fontSize: 16 }}>{t("adminOps:taxonomy.title")}</h2>
        {taxonomy.map((term) => (
          <div key={term.id} className="vy-row" style={{ justifyContent: "space-between", fontSize: 13 }}>
            <span>{term.name_en} ({term.slug}) — {term.kind}</span>
            <span className="vy-muted">{term.status}</span>
          </div>
        ))}
      </section>
    </main>
  );
}

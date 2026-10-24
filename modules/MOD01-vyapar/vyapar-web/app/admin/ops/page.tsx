"use client";

// [TR046] Marketplace health metrics (FR46). [TR048] Post review / stale
// queue / taxonomy management (FR48). One operator screen with four
// sections, so an operator with both permissions never has to jump between
// pages for a normal day's work. Every metric is exactly what the API
// returned; a suppressed (below-10) metric renders as "not enough data yet"
// rather than a zero or a guess.
// [Design language 2026-09-29, operator console] Health as metric tiles;
// the review queue as rows with one action row; the stale queue and the
// taxonomy as dense tables with selection.
// Traces to: FR46, FR48, TR046, TR048
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { numberLocale } from "@/lib/i18n/languages";
import { Activity, AlertTriangle, CheckCircle2, ClipboardList, Clock, ShieldAlert, Tags } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import Screen from "@/app/components/Screen";
import { SkeletonGrid } from "@/app/components/States";
import DealsEmpty from "@/app/components/deals/Empty";
import "@/app/styles/deals-2026.css";

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
  name_mr?: string | null;
  name_kn?: string | null;
  aliases: string[];
  status: string;
}

const METRIC_KEYS = [
  "opportunity_coverage",
  "relevant_discovery_rate",
  "zero_result_rate",
  "opportunity_action_rate",
  "relevant_opportunity_connections",
  "successful_connection_rate",
  "discovery_to_enquiry_rate_listings",
  "freshness",
  "reports_per_1000_interactions",
  "notification_opt_out_rate",
  "promotion_repeat_rate",
  "revenue_paise",
  "refunds_paise",
  "time_to_first_relevant_opportunity_hours",
];

export default function AdminOpsPage() {
  const { t, i18n } = useTranslation(["adminOps", "opportunities", "common"]);
  const [forbidden, setForbidden] = useState(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [oppQueue, setOppQueue] = useState<QueueOpportunity[] | null>(null);
  const [staleQueue, setStaleQueue] = useState<StaleOpportunity[]>([]);
  const [selectedStale, setSelectedStale] = useState<string[]>([]);
  const [taxonomy, setTaxonomy] = useState<TaxonomyTerm[]>([]);
  const [notice, setNotice] = useState<{ text: string; tone: "good" | "bad" } | null>(null);
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
    // The initial load runs once per id (the pattern this module's data hooks use).
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadAll();
  }, [loadAll]);

  async function decideOpportunity(id: string, action: "approve" | "return" | "remove") {
    setBusy(true);
    setNotice(null);
    try {
      await api.post(`/v1/admin/opportunities-queue/${id}/decide`, { action });
      await loadAll();
    } catch (e) {
      setNotice({ text: e instanceof ApiError ? String(e.detail) : t("common:state.actionFailed"), tone: "bad" });
    } finally {
      setBusy(false);
    }
  }

  async function bulkStale(action: "remind" | "expire") {
    if (selectedStale.length === 0) return;
    setBusy(true);
    setNotice(null);
    try {
      const res = await api.post<{ changed: number }>("/v1/admin/stale-queue/bulk", { action, ids: selectedStale, confirm_count: selectedStale.length });
      setNotice({ text: t("adminOps:stale.done", { n: res.changed }), tone: "good" });
      setSelectedStale([]);
      await loadAll();
    } catch (e) {
      setNotice({ text: e instanceof ApiError ? String(e.detail) : t("common:state.actionFailed"), tone: "bad" });
    } finally {
      setBusy(false);
    }
  }

  if (forbidden) {
    return (
      <Screen width="console">
        <div className="vy-dl-page">
          <div className="vy-dl-head">
            <h1>{t("adminOps:title")}</h1>
          </div>
          <DealsEmpty tone="neutral" icon={<ShieldAlert size={24} strokeWidth={1.75} aria-hidden="true" />} title={t("adminOps:notOperator")} />
        </div>
      </Screen>
    );
  }

  const number = (n: number) => new Intl.NumberFormat(numberLocale(i18n.language), { maximumFractionDigits: 2 }).format(n);
  const allStaleSelected = staleQueue.length > 0 && selectedStale.length === staleQueue.length;

  return (
    <Screen width="console">
      <div className="vy-dl-page">
        <div className="vy-dl-head">
          <h1>{t("adminOps:title")}</h1>
          <p>{t("adminOps:subtitle")}</p>
        </div>
        {notice && (
          <p className="vy-dl-notice" data-tone={notice.tone} role={notice.tone === "bad" ? "alert" : "status"}>
            {notice.tone === "good" ? <CheckCircle2 size={18} strokeWidth={1.75} aria-hidden="true" /> : <AlertTriangle size={18} strokeWidth={1.75} aria-hidden="true" />}
            <span>{notice.text}</span>
          </p>
        )}

        <section className="vy-dl-sec" aria-labelledby="ops-health">
          <div className="vy-dl-sec-head">
            <span className="vy-dl-tile vy-dl-tile-brand" aria-hidden="true"><Activity size={20} strokeWidth={1.75} /></span>
            <h2 id="ops-health" className="vy-card-title">{t("adminOps:health.title")}</h2>
            <span className="vy-dl-sec-hint">{health ? t("adminOps:health.minGroupNote", { n: health.min_group_size }) : ""}</span>
          </div>
          {!health ? (
            <SkeletonGrid count={4} />
          ) : (
            <div className="vy-dl-metrics">
              {METRIC_KEYS.map((key) => {
                const m = health.metrics[key];
                const empty = !m || m.value === null;
                return (
                  <div key={key} className="vy-dl-metric">
                    <span className="vy-dl-metric-label">{t(`adminOps:health.metric.${key}` as "health.metric.freshness")}</span>
                    <span className="vy-dl-metric-value" data-empty={empty ? true : undefined}>{empty ? t("adminOps:health.notEnoughData") : number(m.value as number)}</span>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        <div className="vy-dl-console-2">
          <section className="vy-dl-sec" aria-labelledby="ops-queue">
            <div className="vy-dl-sec-head">
              <span className="vy-dl-tile vy-dl-tile-amber" aria-hidden="true"><ClipboardList size={20} strokeWidth={1.75} /></span>
              <h2 id="ops-queue" className="vy-card-title">
                {t("adminOps:opportunitiesQueue.title")} {oppQueue && <span className="vy-dl-count">{oppQueue.length}</span>}
              </h2>
              <span className="vy-dl-sec-hint">{t("adminOps:opportunitiesQueue.hint")}</span>
            </div>
            {oppQueue === null && <SkeletonGrid count={2} grid={false} />}
            {oppQueue?.length === 0 && <p className="vy-dl-hint">{t("adminOps:opportunitiesQueue.empty")}</p>}
            {oppQueue && oppQueue.length > 0 && (
              <div className="vy-dl-list">
                {oppQueue.map((o) => (
                  <div key={o.id} className="vy-dl-panel">
                    <div className="vy-dl-row-body">
                      <span className="vy-dl-row-title">{o.title}</span>
                      <span className="vy-dl-row-meta">
                        <span>
                          {t(`opportunities:type.${o.type}` as "type.employment", { defaultValue: o.type })} · {t("adminOps:opportunitiesQueue.ageDays", { n: o.age_days })}
                        </span>
                      </span>
                      {o.flags.length > 0 && (
                        <span className="vy-dl-tags" style={{ marginTop: 4 }}>
                          {o.flags.map((f) => (
                            <span key={f} className="vy-dl-state" data-tone="warn">{t(`adminOps:opportunitiesQueue.flag.${f}` as "opportunitiesQueue.flag.source_unreachable")}</span>
                          ))}
                        </span>
                      )}
                    </div>
                    <div className="vy-dl-actions">
                      <button className="vy-btn vy-btn-primary vy-dl-btn-sm" disabled={busy} onClick={() => decideOpportunity(o.id, "approve")}>{t("adminOps:opportunitiesQueue.approve")}</button>
                      <button className="vy-btn vy-btn-secondary vy-dl-btn-sm" disabled={busy} onClick={() => decideOpportunity(o.id, "return")}>{t("adminOps:opportunitiesQueue.return")}</button>
                      <button className="vy-btn vy-btn-ghost vy-dl-btn-sm" disabled={busy} onClick={() => decideOpportunity(o.id, "remove")}>{t("adminOps:opportunitiesQueue.remove")}</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="vy-dl-sec" aria-labelledby="ops-stale">
            <div className="vy-dl-sec-head">
              <span className="vy-dl-tile" aria-hidden="true"><Clock size={20} strokeWidth={1.75} /></span>
              <h2 id="ops-stale" className="vy-card-title">
                {t("adminOps:staleQueue.title")} <span className="vy-dl-count">{staleQueue.length}</span>
              </h2>
              <span className="vy-dl-sec-hint">{t("adminOps:staleQueue.hint")}</span>
            </div>
            {staleQueue.length === 0 && <p className="vy-dl-hint">{t("adminOps:staleQueue.empty")}</p>}
            {staleQueue.length > 0 && (
              <>
                <div className="vy-dl-table-wrap">
                  <table className="vy-dl-table" style={{ minWidth: 0 }}>
                    <thead>
                      <tr>
                        <th style={{ width: 44 }}>
                          <input type="checkbox" aria-label={t("adminOps:staleQueue.selectAll")} checked={allStaleSelected} onChange={() => setSelectedStale(allStaleSelected ? [] : staleQueue.map((o) => o.id))} />
                        </th>
                        <th>{t("adminOps:staleQueue.colPost")}</th>
                        <th className="vy-dl-num">{t("adminOps:staleQueue.colAge")}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {staleQueue.map((o) => (
                        <tr key={o.id}>
                          <td>
                            <input type="checkbox" aria-label={o.title} checked={selectedStale.includes(o.id)} onChange={() => setSelectedStale((s) => (s.includes(o.id) ? s.filter((x) => x !== o.id) : [...s, o.id]))} />
                          </td>
                          <td>{o.title}</td>
                          <td className="vy-dl-num">{o.age_days != null ? t("adminOps:opportunitiesQueue.ageDays", { n: o.age_days }) : "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="vy-dl-actions">
                  <button className="vy-btn vy-btn-secondary" disabled={busy || selectedStale.length === 0} onClick={() => bulkStale("remind")}>
                    {t("adminOps:staleQueue.remind", { n: selectedStale.length })}
                  </button>
                  <button className="vy-btn vy-btn-ghost" disabled={busy || selectedStale.length === 0} onClick={() => bulkStale("expire")}>
                    {t("adminOps:staleQueue.expire", { n: selectedStale.length })}
                  </button>
                </div>
              </>
            )}
          </section>
        </div>

        <section className="vy-dl-sec" aria-labelledby="ops-taxonomy">
          <div className="vy-dl-sec-head">
            <span className="vy-dl-tile vy-dl-tile-teal" aria-hidden="true"><Tags size={20} strokeWidth={1.75} /></span>
            <h2 id="ops-taxonomy" className="vy-card-title">
              {t("adminOps:taxonomy.title")} <span className="vy-dl-count">{taxonomy.length}</span>
            </h2>
            <span className="vy-dl-sec-hint">{t("adminOps:taxonomy.hint")}</span>
          </div>
          <div className="vy-dl-table-wrap">
            <table className="vy-dl-table">
              <thead>
                <tr>
                  <th>{t("adminOps:taxonomy.colName")}</th>
                  <th>{t("adminOps:taxonomy.colSlug")}</th>
                  <th>{t("adminOps:taxonomy.colKind")}</th>
                  <th>{t("adminOps:taxonomy.colStatus")}</th>
                </tr>
              </thead>
              <tbody>
                {taxonomy.map((term) => (
                  <tr key={term.id}>
                    <td>
                      {term.name_en}
                      {(term.name_hi || term.name_te || term.name_mr || term.name_kn) && <div className="vy-dl-fine">{[term.name_hi, term.name_te, term.name_mr, term.name_kn].filter(Boolean).join(" · ")}</div>}
                    </td>
                    <td><span className="vy-dl-code">{term.slug}</span></td>
                    <td>{t(`adminOps:taxonomy.kind.${term.kind}` as "taxonomy.kind.category")}</td>
                    <td>
                      <span className="vy-dl-state" data-tone={term.status === "active" ? "done" : term.status === "merged" ? "muted" : "wait"}>
                        {t(`adminOps:taxonomy.status.${term.status}` as "taxonomy.status.active")}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </Screen>
  );
}

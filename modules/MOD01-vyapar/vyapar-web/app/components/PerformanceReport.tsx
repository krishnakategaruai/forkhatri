"use client";

// [TR032] Provider performance report (FR32) — five separate counts for the
// period (impressions, detail views, saves, enquiries, confirmed outcomes),
// with "Boosted n · Organic n" only when a boost ran AND there are at least
// 10 impressions; otherwise "Too little data to compare". No projections, no
// ROI, no causal wording, no member data — the API has no field for any of
// them. Inline on the owner's listing / opportunity / boost screen rather
// than a separate report screen.
// Traces to: FR32, TR032, SP032, UX20
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "@/lib/api";

interface Count {
  kind: string;
  total: number;
  boosted: number | null;
  organic: number | null;
}

interface Report {
  from: string;
  to: string;
  boost_ran: boolean;
  comparable: boolean;
  too_little_data: boolean;
  counts: Count[];
}

export default function PerformanceReport({
  targetKind,
  targetId,
  promotionId,
}: {
  targetKind: "listing" | "opportunity";
  targetId: string;
  promotionId?: string;
}) {
  const { t, i18n } = useTranslation(["commercial"]);
  const [report, setReport] = useState<Report | null>(null);

  useEffect(() => {
    const query = promotionId ? `?promotion_id=${promotionId}` : "";
    api.get<Report>(`/v1/performance/${targetKind}/${targetId}${query}`).then(setReport).catch(() => setReport(null));
  }, [targetKind, targetId, promotionId]);

  if (!report) return null;
  const fmt = (d: string) => new Date(d).toLocaleDateString(i18n.language);

  return (
    <section className="vy-card vy-stack" aria-labelledby={`perf-${targetId}`}>
      <div className="vy-row" style={{ justifyContent: "space-between", flexWrap: "wrap" }}>
        <h2 id={`perf-${targetId}`} style={{ fontSize: 16 }}>{t("commercial:report.title")}</h2>
        <span className="vy-muted" style={{ fontSize: 13 }}>{t("commercial:report.period", { from: fmt(report.from), to: fmt(report.to) })}</span>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: 8 }}>
        {report.counts.map((c) => (
          <div key={c.kind} style={{ padding: "10px 12px", borderRadius: 12, background: "var(--surface-overlay)" }}>
            <div className="vy-muted" style={{ fontSize: 12 }}>{t(`commercial:report.kind.${c.kind}` as "report.kind.view")}</div>
            <div style={{ fontSize: 22, fontWeight: 600 }}>{c.total}</div>
            {report.comparable && c.boosted !== null && c.organic !== null && (
              <div className="vy-muted" style={{ fontSize: 12 }}>{t("commercial:report.split", { b: c.boosted, o: c.organic })}</div>
            )}
          </div>
        ))}
      </div>
      {report.too_little_data && <p className="vy-muted" style={{ fontSize: 13 }}>{t("commercial:report.tooLittle")}</p>}
      <p className="vy-muted" style={{ fontSize: 12 }}>{t("commercial:report.note")}</p>
    </section>
  );
}

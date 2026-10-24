"use client";

// [TR032] Performance report (FR32): five separate counts for the period
// (impressions, detail views, saves, requests, confirmed outcomes), with
// "Promoted n · Organic n" only when a promotion ran AND there are at least
// 10 impressions; otherwise "Too little data to compare". No projections,
// no ROI, no causal wording, no member data. Inline on the owner's profile /
// post / promotion screen rather than a separate report screen.
// [Design language 2026-09-29] A section card with an icon tile and the
// counts as metric tiles (number as the hero, label above, split below).
// Traces to: FR32, TR032, SP032, UX20
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { numberLocale } from "@/lib/i18n/languages";
import { BarChart3 } from "lucide-react";
import { useSdk } from "@/lib/sdk/react";
import { formatDate } from "@/lib/format";
import "@/app/styles/deals-2026.css";

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

export default function PerformanceReport({ targetKind, targetId, promotionId }: { targetKind: "listing" | "opportunity" | "campaign"; targetId: string; promotionId?: string }) {
  const { t, i18n } = useTranslation(["commercial"]);
  const [report, setReport] = useState<Report | null>(null);
  const sdk = useSdk();

  useEffect(() => {
    sdk.commercial
      .performance<Report>(targetKind, targetId, { promotion_id: promotionId })
      .then(setReport)
      .catch(() => setReport(null));
  }, [targetKind, targetId, promotionId, sdk]);

  if (!report) return null;
  const fmt = (d: string) => formatDate(d, i18n.language);
  const number = (n: number) => new Intl.NumberFormat(numberLocale(i18n.language)).format(n);

  return (
    <section className="vy-dl-sec" aria-labelledby={`perf-${targetId}`}>
      <div className="vy-dl-sec-head">
        <span className="vy-dl-tile vy-dl-tile-brand" aria-hidden="true"><BarChart3 size={20} strokeWidth={1.75} /></span>
        <h2 id={`perf-${targetId}`} className="vy-card-title">{t("commercial:report.title")}</h2>
        <span className="vy-dl-sec-hint">{t("commercial:report.period", { from: fmt(report.from), to: fmt(report.to) })}</span>
      </div>
      <div className="vy-dl-metrics">
        {report.counts.map((c) => (
          <div key={c.kind} className="vy-dl-metric">
            <span className="vy-dl-metric-label">{t(`commercial:report.kind.${c.kind}` as "report.kind.view")}</span>
            <span className="vy-dl-metric-value">{number(c.total)}</span>
            {report.comparable && c.boosted !== null && c.organic !== null && (
              <span className="vy-dl-metric-sub">{t("commercial:report.split", { b: number(c.boosted), o: number(c.organic) })}</span>
            )}
          </div>
        ))}
      </div>
      <p className="vy-dl-fine">
        {report.too_little_data ? `${t("commercial:report.tooLittle")} ` : ""}
        {t("commercial:report.note")}
      </p>
    </section>
  );
}

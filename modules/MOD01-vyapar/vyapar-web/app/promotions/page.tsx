"use client";

// [TR031] Promotion history (FR31): every promotion the member bought, newest
// first, with its state and end date; each row opens the reconstructible
// promotion record. Reached from Profile → My promotions.
// [Design language 2026-09-29] Rows: icon tile · what was promoted · the
// pack · ends on, with a quiet state chip. Glossary: "promotion", not boost.
// Traces to: FR31, TR031, UX20
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { ChevronRight, Megaphone } from "lucide-react";
import { api } from "@/lib/api";
import Screen from "@/app/components/Screen";
import { SkeletonGrid } from "@/app/components/States";
import DealsEmpty from "@/app/components/deals/Empty";
import { formatDate } from "@/lib/format";
import { promotionTone } from "./tone";
import "@/app/styles/deals-2026.css";

interface PromotionRow {
  id: string;
  target_title: string | null;
  state: string;
  product_id: string;
  ends_at: string | null;
}

export default function PromotionsPage() {
  const { t, i18n } = useTranslation(["commercial", "common"]);
  const [rows, setRows] = useState<PromotionRow[] | null>(null);

  useEffect(() => {
    api.get<PromotionRow[]>("/v1/promotions/mine").then(setRows).catch(() => setRows([]));
  }, []);

  return (
    <Screen width="wide">
      <div className="vy-dl-page">
        <div className="vy-dl-head">
          <h1>{t("commercial:list.title")}</h1>
          <p>{t("commercial:list.subtitle")}</p>
        </div>
        {rows === null && <SkeletonGrid count={3} grid={false} />}
        {rows?.length === 0 && <DealsEmpty icon={<Megaphone size={24} strokeWidth={1.75} aria-hidden="true" />} title={t("commercial:list.emptyTitle")} body={t("commercial:list.empty")} />}
        {rows && rows.length > 0 && (
          <div className="vy-dl-list">
            {rows.map((r) => (
              <a key={r.id} className="vy-dl-row" href={`/promotions/${r.id}`}>
                <span className="vy-dl-tile vy-dl-tile-brand" aria-hidden="true"><Megaphone size={18} strokeWidth={1.75} /></span>
                <span className="vy-dl-row-body">
                  <span className="vy-dl-row-title">{r.target_title ?? t("commercial:promotion.target")}</span>
                  <span className="vy-dl-row-meta">
                    <span>
                      {t(`commercial:product.${r.product_id}` as "product.boost_7d", { defaultValue: r.product_id })}
                      {r.ends_at ? ` · ${t("commercial:list.endsOn", { date: formatDate(r.ends_at, i18n.language) })}` : ""}
                    </span>
                  </span>
                  <span className="vy-dl-tags" style={{ marginTop: 4 }}>
                    <span className="vy-dl-state" data-tone={promotionTone(r.state)}>{t(`commercial:state.${r.state}` as "state.active")}</span>
                  </span>
                </span>
                <span className="vy-dl-row-aside">
                  <ChevronRight size={18} strokeWidth={2} aria-hidden="true" style={{ color: "var(--text-tertiary)" }} />
                </span>
              </a>
            ))}
          </div>
        )}
      </div>
    </Screen>
  );
}

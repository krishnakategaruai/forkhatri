"use client";

// [TR031] Promotion history (FR31) — every boost the member bought, newest
// first, with its state and end date; each row opens the reconstructible
// promotion record. Reached from Profile → My boosts.
// Traces to: FR31, TR031, UX20
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "@/lib/api";

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
    <main className="vy-shell">
      <h1>{t("commercial:list.title")}</h1>
      {rows === null && <p className="vy-muted">{t("common:state.loading")}</p>}
      {rows?.length === 0 && <p className="vy-muted">{t("commercial:list.empty")}</p>}
      <div className="vy-stack" style={{ gap: 8 }}>
        {rows?.map((r) => (
          <a key={r.id} className="vy-card" href={`/promotions/${r.id}`} style={{ textDecoration: "none" }}>
            <div className="vy-row" style={{ justifyContent: "space-between", flexWrap: "wrap" }}>
              <strong>{r.target_title ?? t("commercial:promotion.target")}</strong>
              <span className="vy-badge vy-badge-member-provided">{t(`commercial:state.${r.state}` as "state.active")}</span>
            </div>
            <p className="vy-muted" style={{ fontSize: 13 }}>
              {t(`commercial:product.${r.product_id}` as "product.boost_7d", { defaultValue: r.product_id })}
              {r.ends_at ? ` · ${t("commercial:list.endsOn", { date: new Date(r.ends_at).toLocaleDateString(i18n.language) })}` : ""}
            </p>
          </a>
        ))}
      </div>
    </main>
  );
}

"use client";

// [TR047] Verification queue — operator view (FR47). Oldest first, rows
// waiting longer than 3 days flagged. One-tap decisions straight from the
// card (Verify / Reject / Needs clearer copy) — no separate detail screen,
// per the "no unnecessary intermediate screens" standing preference.
// Evidence stays masked (last 4 only); the API never returns the encrypted
// identifier at all. Non-operators get a plain explanation, not a crash.
// Traces to: FR47, FR08, FR09, TR047, SP047
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "@/lib/api";
import { DOC_KEY } from "@/app/components/Verification";

interface QueueItem {
  id: string;
  listing_id: string;
  document_type: string;
  identifier_masked: string | null;
  credential_name: string | null;
  issuer: string | null;
  days_pending: number;
}

export default function VerificationQueuePage() {
  const { t } = useTranslation(["verification", "common"]);
  const [items, setItems] = useState<QueueItem[] | null>(null);
  const [forbidden, setForbidden] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);

  async function load() {
    try {
      setItems(await api.get<QueueItem[]>("/v1/admin/verification-queue"));
    } catch (e) {
      if (e instanceof ApiError && e.status === 403) setForbidden(true);
      setItems([]);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function decide(id: string, action: "verify" | "reject" | "needs-clearer-copy") {
    setBusy(id);
    try {
      await api.post(`/v1/admin/verification-queue/${id}/${action}`, {});
      await load();
    } finally {
      setBusy(null);
    }
  }

  if (forbidden) {
    return (
      <main className="vy-shell">
        <h1>{t("verification:queueTitle")}</h1>
        <p className="vy-muted">{t("verification:notOperator")}</p>
      </main>
    );
  }

  return (
    <main className="vy-shell">
      <h1>{t("verification:queueTitle")}</h1>
      {items === null && <p className="vy-muted">{t("common:state.loading")}</p>}
      {items?.length === 0 && <p className="vy-muted">{t("verification:queueEmpty")}</p>}
      <div className="vy-stack">
        {items?.map((item) => (
          <div key={item.id} className="vy-card vy-stack">
            <div className="vy-row" style={{ justifyContent: "space-between", flexWrap: "wrap" }}>
              <strong>{t(`verification:${DOC_KEY[item.document_type]}` as "typeGst")}</strong>
              <span className={item.days_pending > 3 ? "vy-badge vy-badge-sponsored" : "vy-muted"}>
                {item.days_pending > 3 ? t("verification:overdue") : t("verification:daysPending", { days: item.days_pending })}
              </span>
            </div>
            <p className="vy-muted">
              {item.document_type === "credential" ? `${item.credential_name ?? ""} · ${item.issuer ?? ""}` : item.identifier_masked}
            </p>
            <a className="vy-muted" href={`/listings/${item.listing_id}`}>
              {t("common:action.back")} →
            </a>
            <div className="vy-row" style={{ flexWrap: "wrap" }}>
              <button className="vy-btn vy-btn-primary" disabled={busy === item.id} onClick={() => decide(item.id, "verify")}>
                {t("verification:verify")}
              </button>
              <button className="vy-btn vy-btn-secondary" disabled={busy === item.id} onClick={() => decide(item.id, "reject")}>
                {t("verification:reject")}
              </button>
              <button className="vy-btn vy-btn-ghost" disabled={busy === item.id} onClick={() => decide(item.id, "needs-clearer-copy")}>
                {t("verification:needsClearerCopy")}
              </button>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}

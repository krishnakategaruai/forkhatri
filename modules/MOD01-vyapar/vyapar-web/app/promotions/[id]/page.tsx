"use client";

// [TR031] Promotion record and lifecycle actions (FR31) + [TR032] its
// performance (FR32), on one screen (UX20 "Result" + "Promotion detail" +
// "Performance report" merged — fewer screens). On return from checkout it
// shows the result and, while the payment is still pending, re-reads the
// order every 3 seconds (which also triggers the API's status-poll fallback)
// until the webhook lands. Shows state, product + price version, dates,
// price / GST / credit / amount paid, payment and refund references, credit
// earned, the full state history, and exactly the actions this state allows:
// retry payment or cancel while awaiting payment; stop with the exact
// pro-rata credit amount while active.
// Traces to: FR30, FR31, FR32, FR51, TR031, TR032, UX20
import { useEffect, useState, use as useParamsPromise } from "react";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "@/lib/api";
import { formatPaise } from "@/lib/money";
import PerformanceReport from "@/app/components/PerformanceReport";

interface HistoryRow {
  from_state: string | null;
  to_state: string;
  reason: string | null;
  at: string;
}

interface Promotion {
  id: string;
  target_kind: "listing" | "opportunity";
  target_id: string;
  target_title: string | null;
  state: string;
  product_id: string;
  product_version: number;
  price_paise: number;
  tax_paise: number;
  credit_applied_paise: number;
  charged_paise: number;
  credit_paise: number;
  starts_at: string | null;
  ends_at: string | null;
  reject_reason: string | null;
  payment_order_id: string | null;
  payment_state: string | null;
  receipt_ref: string | null;
  refund_ref: string | null;
  cancel_preview: { kind: "cancel" | "credit"; amount_paise: number } | null;
  history: HistoryRow[];
}

export default function PromotionPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ result?: string }>;
}) {
  const { id } = useParamsPromise(params);
  const { result } = useParamsPromise(searchParams);
  const { t, i18n } = useTranslation(["commercial", "common", "trustSafety"]);
  const [promo, setPromo] = useState<Promotion | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function load(): Promise<Promotion> {
    const p = await api.get<Promotion>(`/v1/promotions/${id}`);
    setPromo(p);
    return p;
  }

  useEffect(() => {
    let cancelled = false;
    let tries = 0;
    async function tick() {
      try {
        const p = await load();
        if (cancelled) return;
        if (result && p.state === "awaiting_payment" && p.payment_state === "pending" && tries < 10) {
          tries += 1;
          if (p.payment_order_id) await api.get(`/v1/payments/orders/${p.payment_order_id}`).catch(() => undefined);
          setTimeout(tick, 3000);
        }
      } catch (e) {
        setError(e instanceof ApiError ? String(e.detail) : t("commercial:promotion.notFound"));
      }
    }
    tick();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, result]);

  if (error) return <main className="vy-shell"><h1>{t("commercial:promotion.notFound")}</h1><p>{error}</p></main>;
  if (!promo) return <main className="vy-shell"><p className="vy-muted">{t("common:state.loading")}</p></main>;

  const money = (p: number) => formatPaise(p, i18n.language);
  const fmt = (d: string) => new Date(d).toLocaleDateString(i18n.language);

  let banner: string | null = null;
  if (result === "unavailable") banner = t("commercial:promotion.resultUnavailable");
  else if (result === "failed") banner = t("commercial:promotion.resultFailed");
  else if (result === "succeeded") banner = promo.state === "active" ? t("commercial:promotion.resultSucceeded") : t("commercial:promotion.resultPending");

  async function retryPayment() {
    setBusy(true);
    setNotice(null);
    try {
      const res = await api.post<{ checkout_url: string | null; notice: string | null }>(`/v1/promotions/${id}/confirm-purchase`, { confirmed: true });
      if (res.checkout_url) {
        window.location.assign(res.checkout_url);
        return;
      }
      setNotice(res.notice ? t("commercial:promotion.resultUnavailable") : null);
      await load();
    } catch (e) {
      setNotice(e instanceof ApiError ? String(e.detail) : t("common:state.actionFailed"));
    } finally {
      setBusy(false);
    }
  }

  async function cancel() {
    setBusy(true);
    setNotice(null);
    try {
      await api.post(`/v1/promotions/${id}/cancel`);
      await load();
    } catch (e) {
      setNotice(e instanceof ApiError ? String(e.detail) : t("common:state.actionFailed"));
    } finally {
      setBusy(false);
    }
  }

  const targetPath = `/${promo.target_kind === "listing" ? "listings" : "opportunities"}/${promo.target_id}`;
  const rejectReason = promo.reject_reason
    ? t(`trustSafety:reasonCode.${promo.reject_reason}` as "trustSafety:reasonCode.spam", { defaultValue: promo.reject_reason })
    : "";

  return (
    <main className="vy-shell">
      {banner && <div className="vy-card" role="status"><p>{banner}</p></div>}

      <div>
        <span className="vy-badge vy-badge-member-provided">{t(`commercial:state.${promo.state}` as "state.active")}</span>
        <h1 style={{ marginTop: 8 }}>
          {t("commercial:promotion.title", { name: promo.target_title ?? t("commercial:promotion.target") })}
        </h1>
        <a className="vy-muted" href={targetPath}>{promo.target_title ?? t("commercial:promotion.target")} →</a>
      </div>

      <div className="vy-card vy-stack" style={{ gap: 6 }}>
        <strong>{t(`commercial:product.${promo.product_id}` as "product.boost_7d", { defaultValue: promo.product_id })}</strong>
        <span className="vy-muted" style={{ fontSize: 13 }}>{t("commercial:promotion.version", { v: promo.product_version })}</span>
        {promo.starts_at && promo.ends_at && <span>{t("commercial:promotion.period", { from: fmt(promo.starts_at), to: fmt(promo.ends_at) })}</span>}
        <span>{t("commercial:promotion.price", { amount: money(promo.price_paise) })}</span>
        <span>{t("commercial:promotion.tax", { amount: money(promo.tax_paise) })}</span>
        {promo.credit_applied_paise > 0 && <span>{t("commercial:promotion.creditApplied", { amount: money(promo.credit_applied_paise) })}</span>}
        {promo.charged_paise > 0 && <span>{t("commercial:promotion.charged", { amount: money(promo.charged_paise) })}</span>}
        {promo.receipt_ref && <span className="vy-muted" style={{ fontSize: 13 }}>{t("commercial:promotion.receiptRef", { ref: promo.receipt_ref })}</span>}
        {promo.refund_ref && <span className="vy-muted" style={{ fontSize: 13 }}>{t("commercial:promotion.refundRef", { ref: promo.refund_ref })}</span>}
        {promo.credit_paise > 0 && <p className="vy-muted">{t("commercial:promotion.creditOnThis", { amount: money(promo.credit_paise) })}</p>}
        {promo.state === "rejected" && <p className="vy-error">{t("commercial:promotion.rejected", { reason: rejectReason })}</p>}
      </div>

      {notice && <p className="vy-error">{notice}</p>}
      <div className="vy-row" style={{ flexWrap: "wrap" }}>
        {promo.state === "awaiting_payment" && (
          <button className="vy-btn vy-btn-primary" disabled={busy} onClick={retryPayment}>{t("commercial:promotion.retryPayment")}</button>
        )}
        {promo.cancel_preview?.kind === "cancel" && (
          <button className="vy-btn vy-btn-ghost" disabled={busy} onClick={cancel}>{t("commercial:promotion.cancelOrder")}</button>
        )}
        {promo.cancel_preview?.kind === "credit" && (
          <button className="vy-btn vy-btn-secondary" disabled={busy} onClick={cancel}>
            {t("commercial:promotion.cancelActive", { amount: money(promo.cancel_preview.amount_paise) })}
          </button>
        )}
      </div>

      {promo.starts_at && <PerformanceReport targetKind={promo.target_kind} targetId={promo.target_id} promotionId={promo.id} />}

      <section className="vy-stack" style={{ gap: 6 }}>
        <h2 style={{ fontSize: 16 }}>{t("commercial:promotion.history")}</h2>
        <ol className="vy-stack" style={{ gap: 4, margin: 0, paddingLeft: 18 }}>
          {promo.history.map((h, i) => (
            <li key={i} className="vy-muted" style={{ fontSize: 13 }}>
              {new Date(h.at).toLocaleString(i18n.language)} · {t(`commercial:state.${h.to_state}` as "state.active")}
              {h.reason ? ` · ${t(`commercial:historyReason.${h.reason.split(":")[0]}` as "historyReason.created", { defaultValue: h.reason })}` : ""}
            </li>
          ))}
        </ol>
      </section>
    </main>
  );
}

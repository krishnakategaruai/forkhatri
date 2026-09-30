"use client";

// [TR031] Promotion record and lifecycle actions (FR31) + [TR032] its
// performance (FR32), on one screen. On return from checkout it shows the
// result and, while the payment is still pending, re-reads the order every
// 3 seconds (which also triggers the API's status-poll fallback) until the
// webhook lands. Shows state, product + price version, dates, price / GST /
// credit / amount paid, payment and refund references, credit earned, the
// full state history, and exactly the actions this state allows.
// [Design language 2026-09-29] The record (result notice, title, report,
// history) in the main column; a sticky receipt card with the actions in
// the aside. Glossary: "promotion", never boost.
// Traces to: FR30, FR31, FR32, FR51, TR031, TR032, UX20
import { useEffect, useState, use as useParamsPromise } from "react";
import { useTranslation } from "react-i18next";
import Link from "next/link";
import { AlertTriangle, CheckCircle2, ChevronLeft, ChevronRight, Clock, History, Receipt } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { formatPaise } from "@/lib/money";
import PerformanceReport from "@/app/components/PerformanceReport";
import Screen from "@/app/components/Screen";
import { SkeletonGrid } from "@/app/components/States";
import DealsEmpty from "@/app/components/deals/Empty";
import { formatDate, formatDateTime } from "@/lib/format";
import { promotionTone } from "../tone";
import "@/app/styles/deals-2026.css";

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

export default function PromotionPage({ params, searchParams }: { params: Promise<{ id: string }>; searchParams: Promise<{ result?: string }> }) {
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

  if (error)
    return (
      <Screen width="wide">
        <div className="vy-dl-page">
          <DealsEmpty tone="neutral" icon={<AlertTriangle size={24} strokeWidth={1.75} aria-hidden="true" />} title={t("commercial:promotion.notFound")} body={error} />
        </div>
      </Screen>
    );
  if (!promo)
    return (
      <Screen width="wide">
        <div className="vy-dl-page">
          <SkeletonGrid count={3} grid={false} />
        </div>
      </Screen>
    );

  const money = (p: number) => formatPaise(p, i18n.language);
  const fmt = (d: string) => formatDate(d, i18n.language);

  let banner: { text: string; tone: "good" | "warn" | "bad" | undefined } | null = null;
  if (result === "unavailable") banner = { text: t("commercial:promotion.resultUnavailable"), tone: "warn" };
  else if (result === "failed") banner = { text: t("commercial:promotion.resultFailed"), tone: "bad" };
  else if (result === "succeeded") banner = promo.state === "active" ? { text: t("commercial:promotion.resultSucceeded"), tone: "good" } : { text: t("commercial:promotion.resultPending"), tone: undefined };

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
  const rejectReason = promo.reject_reason ? t(`trustSafety:reasonCode.${promo.reject_reason}` as "trustSafety:reasonCode.spam", { defaultValue: promo.reject_reason }) : "";
  const productName = t(`commercial:product.${promo.product_id}` as "product.boost_7d", { defaultValue: promo.product_id });

  return (
    <Screen width="wide">
      <div className="vy-dl-page">
        <Link href="/promotions" transitionTypes={["vy-back"]} className="vy-dl-back">
          <ChevronLeft size={18} strokeWidth={2} aria-hidden="true" />
          {t("commercial:list.title")}
        </Link>
        <div className="vy-ctx">
          <div className="vy-ctx-grid">
            <div className="vy-ctx-main">
              {banner && (
                <p className="vy-dl-notice" data-tone={banner.tone} role="status">
                  {banner.tone === "good" ? <CheckCircle2 size={18} strokeWidth={1.75} aria-hidden="true" /> : banner.tone ? <AlertTriangle size={18} strokeWidth={1.75} aria-hidden="true" /> : <Clock size={18} strokeWidth={1.75} aria-hidden="true" />}
                  <span>{banner.text}</span>
                </p>
              )}
              <div className="vy-dl-head">
                <div className="vy-dl-tags">
                  <span className="vy-dl-state" data-tone={promotionTone(promo.state)}>{t(`commercial:state.${promo.state}` as "state.active")}</span>
                  <span className="vy-dl-state">{productName}</span>
                </div>
                <h1>{t("commercial:promotion.title", { name: promo.target_title ?? t("commercial:promotion.target") })}</h1>
                <p className="vy-dl-thread-about">
                  {promo.starts_at && promo.ends_at && <span>{t("commercial:promotion.period", { from: fmt(promo.starts_at), to: fmt(promo.ends_at) })}</span>}
                  {promo.starts_at && promo.ends_at && <span aria-hidden="true">·</span>}
                  <Link href={targetPath} className="vy-dl-inline-icon">
                    {t("commercial:promotion.openTarget")} <ChevronRight size={14} strokeWidth={2} aria-hidden="true" />
                  </Link>
                </p>
                {promo.state === "rejected" && (
                  <p className="vy-dl-notice" data-tone="bad">
                    <AlertTriangle size={18} strokeWidth={1.75} aria-hidden="true" />
                    <span>{t("commercial:promotion.rejected", { reason: rejectReason })}</span>
                  </p>
                )}
              </div>
            </div>

            <aside className="vy-ctx-aside">
              <section className="vy-dl-sec" aria-labelledby="promo-receipt">
                <div className="vy-dl-sec-head">
                  <span className="vy-dl-tile vy-dl-tile-green" aria-hidden="true"><Receipt size={20} strokeWidth={1.75} /></span>
                  <h2 id="promo-receipt" className="vy-card-title">{t("commercial:promotion.receiptTitle")}</h2>
                  <span className="vy-dl-sec-hint">{t("commercial:promotion.version", { v: promo.product_version })}</span>
                </div>
                <dl className="vy-dl-receipt">
                  <dt>{t("commercial:disclosure.price")}</dt>
                  <dd>{money(promo.price_paise)}</dd>
                  <dt>{t("commercial:disclosure.tax")}</dt>
                  <dd>{money(promo.tax_paise)}</dd>
                  {promo.credit_applied_paise > 0 && (
                    <>
                      <dt>{t("commercial:disclosure.credit")}</dt>
                      <dd>− {money(promo.credit_applied_paise)}</dd>
                    </>
                  )}
                  <dt className="vy-dl-receipt-total">{t("commercial:promotion.chargedLabel")}</dt>
                  <dd className="vy-dl-receipt-total"><strong>{money(promo.charged_paise)}</strong></dd>
                </dl>
                {(promo.receipt_ref || promo.refund_ref) && (
                  <p className="vy-dl-fine">
                    {promo.receipt_ref && <span className="vy-dl-code">{t("commercial:promotion.receiptRef", { ref: promo.receipt_ref })}</span>}
                    {promo.receipt_ref && promo.refund_ref && <br />}
                    {promo.refund_ref && <span className="vy-dl-code">{t("commercial:promotion.refundRef", { ref: promo.refund_ref })}</span>}
                  </p>
                )}
                {promo.credit_paise > 0 && <p className="vy-dl-hint">{t("commercial:promotion.creditOnThis", { amount: money(promo.credit_paise) })}</p>}
                {notice && <p className="vy-error" role="alert">{notice}</p>}
                {(promo.state === "awaiting_payment" || promo.cancel_preview) && (
                  <div className="vy-dl-actions">
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
                )}
              </section>
            </aside>

            <div className="vy-ctx-after">
              {promo.starts_at && <PerformanceReport targetKind={promo.target_kind} targetId={promo.target_id} promotionId={promo.id} />}

              <section className="vy-dl-sec" aria-labelledby="promo-history">
                <div className="vy-dl-sec-head">
                  <span className="vy-dl-tile" aria-hidden="true"><History size={20} strokeWidth={1.75} /></span>
                  <h2 id="promo-history" className="vy-card-title">{t("commercial:promotion.history")}</h2>
                  <span className="vy-dl-sec-hint">{t("commercial:promotion.historyHint")}</span>
                </div>
                <ol className="vy-dl-history">
                  {promo.history.map((h, i) => (
                    <li key={i}>
                      <span>
                        {t(`commercial:state.${h.to_state}` as "state.active")}
                        {h.reason ? ` · ${t(`commercial:historyReason.${h.reason.split(":")[0]}` as "historyReason.created", { defaultValue: h.reason })}` : ""}
                      </span>
                      <time dateTime={h.at}>{formatDateTime(h.at, i18n.language)}</time>
                    </li>
                  ))}
                </ol>
              </section>
            </div>
          </div>
        </div>
      </div>
    </Screen>
  );
}

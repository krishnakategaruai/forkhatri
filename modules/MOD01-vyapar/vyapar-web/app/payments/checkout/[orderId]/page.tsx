"use client";

// [TR051 — DEV STAND-IN] Sandbox checkout for the dev payment gateway. In a
// real deployment (PAYMENT_GATEWAY=razorpay) the member is sent to the
// gateway-hosted page instead and never sees this route. It is labelled as a
// sandbox, collects no card or bank data, and its two buttons push a signed,
// gateway-shaped webhook through the API's real verification path
// (POST /v1/payments/orders/{id}/simulate — rejected unless DEV_MODE).
// [FE2 — imp-backend-d] Contract stages and hourly weeks are paid through
// this same checkout. The contract page sends `?return=/contracts/<id>` so
// the person lands back on their contract. Only same-app paths are honoured.
// [Design language 2026-09-29] One centred amount card: the amount as the
// hero, the GST line, one filled button.
// Traces to: FR51, TR051, SP051
import { useEffect, useState, use as useParamsPromise } from "react";
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { AlertTriangle, ChevronRight, FlaskConical, Lock } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { formatPaise } from "@/lib/money";
import Screen from "@/app/components/Screen";
import { SkeletonGrid } from "@/app/components/States";
import "@/app/styles/deals-2026.css";

interface Order {
  id: string;
  kind: string;
  ref_id: string;
  amount_paise: number;
  tax_paise: number;
  state: string;
  sandbox: boolean;
}

function safeReturn(value: string | undefined): string | null {
  return value && value.startsWith("/") && !value.startsWith("//") ? value : null;
}

export default function SandboxCheckoutPage({ params, searchParams }: { params: Promise<{ orderId: string }>; searchParams: Promise<{ return?: string }> }) {
  const { orderId } = useParamsPromise(params);
  const returnTo = safeReturn(useParamsPromise(searchParams).return);
  const { t, i18n } = useTranslation(["commercial", "common", "contracts"]);
  const router = useRouter();
  const [order, setOrder] = useState<Order | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api
      .get<Order>(`/v1/payments/orders/${orderId}`)
      .then(setOrder)
      .catch((e) => setError(e instanceof ApiError ? String(e.detail) : t("common:state.somethingWentWrong")));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orderId]);

  async function simulate(outcome: "succeeded" | "failed") {
    setBusy(true);
    try {
      const res = await api.post<{ redirect: string }>(`/v1/payments/orders/${orderId}/simulate`, { outcome });
      router.push(returnTo ?? res.redirect);
    } catch (e) {
      setError(e instanceof ApiError ? String(e.detail) : t("common:state.somethingWentWrong"));
      setBusy(false);
    }
  }

  const money = (p: number) => formatPaise(p, i18n.language);
  const backHref = returnTo ?? (order ? `/promotions/${order.ref_id}` : "/promotions");
  const backLabel = order?.kind === "contract_milestone" ? t("contracts:checkout.back") : t("commercial:checkout.back");

  return (
    <Screen width="wide">
      <div className="vy-dl-page vy-checkout">
        <div className="vy-checkout-intro vy-dl-page" style={{ gap: "var(--space-3)" }}>
          <div className="vy-dl-tags">
            <span className="vy-dl-state" data-tone="wait">
              <FlaskConical size={13} strokeWidth={2} aria-hidden="true" />
              {t("commercial:checkout.title")}
            </span>
          </div>
          <h1>{t("commercial:checkout.heading")}</h1>
          <p className="vy-dl-hint">{t("commercial:checkout.note")}</p>
          {error && (
            <p className="vy-dl-notice" data-tone="bad" role="alert">
              <AlertTriangle size={18} strokeWidth={1.75} aria-hidden="true" />
              <span>{error}</span>
            </p>
          )}
        </div>
        {!order && !error && <SkeletonGrid count={1} grid={false} />}
        {order && (
          <section className="vy-dl-sec" aria-label={t("commercial:checkout.title")}>
            <div className="vy-dl-page" style={{ gap: 4 }}>
              <span className="vy-dl-fine">{t("commercial:checkout.amountLabel")}</span>
              <span className="vy-dl-money vy-dl-money-lg">{money(order.amount_paise + order.tax_paise)}</span>
            </div>
            <dl className="vy-dl-receipt">
              <dt>{t("commercial:disclosure.price")}</dt>
              <dd>{money(order.amount_paise)}</dd>
              <dt>{t("commercial:disclosure.tax")}</dt>
              <dd>{money(order.tax_paise)}</dd>
            </dl>
            {order.state === "pending" ? (
              <div className="vy-dl-page" style={{ gap: "var(--space-2)" }}>
                <button className="vy-btn vy-btn-primary" disabled={busy} onClick={() => simulate("succeeded")}>
                  {t("commercial:checkout.succeed")}
                </button>
                <button className="vy-btn vy-btn-ghost" disabled={busy} onClick={() => simulate("failed")}>
                  {t("commercial:checkout.fail")}
                </button>
              </div>
            ) : (
              <div className="vy-dl-page" style={{ gap: "var(--space-2)" }}>
                <p className="vy-dl-hint">{t("commercial:checkout.done", { state: t(`commercial:paymentState.${order.state}` as "paymentState.pending") })}</p>
                <a className="vy-btn vy-btn-secondary" href={backHref} style={{ textDecoration: "none" }}>
                  {backLabel} <ChevronRight size={16} strokeWidth={2} aria-hidden="true" />
                </a>
              </div>
            )}
            <p className="vy-dl-safety">
              <Lock size={13} strokeWidth={2} aria-hidden="true" />
              <span>{t("commercial:checkout.safety")}</span>
            </p>
          </section>
        )}
      </div>
    </Screen>
  );
}

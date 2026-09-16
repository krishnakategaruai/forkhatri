"use client";

// [TR051 — DEV STAND-IN] Sandbox checkout for the dev payment gateway. In a
// real deployment (PAYMENT_GATEWAY=razorpay) the member is sent to the
// gateway-hosted page instead and never sees this route. It is labelled as a
// sandbox, collects no card or bank data, and its two buttons push a signed,
// gateway-shaped webhook through the API's real verification path
// (POST /v1/payments/orders/{id}/simulate — rejected unless DEV_MODE).
// Traces to: FR51, TR051, SP051
import { useEffect, useState, use as useParamsPromise } from "react";
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "@/lib/api";
import { formatPaise } from "@/lib/money";

interface Order {
  id: string;
  kind: string;
  ref_id: string;
  amount_paise: number;
  tax_paise: number;
  state: string;
  sandbox: boolean;
}

export default function SandboxCheckoutPage({ params }: { params: Promise<{ orderId: string }> }) {
  const { orderId } = useParamsPromise(params);
  const { t, i18n } = useTranslation(["commercial", "common"]);
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
      router.push(res.redirect);
    } catch (e) {
      setError(e instanceof ApiError ? String(e.detail) : t("common:state.somethingWentWrong"));
      setBusy(false);
    }
  }

  return (
    <main className="vy-shell">
      <span className="vy-badge vy-badge-sponsored" style={{ alignSelf: "flex-start" }}>{t("commercial:checkout.title")}</span>
      <p className="vy-muted">{t("commercial:checkout.note")}</p>
      {error && <p className="vy-error">{error}</p>}
      {order && (
        <div className="vy-card vy-stack">
          <strong style={{ fontSize: 22 }}>{t("commercial:checkout.amount", { amount: formatPaise(order.amount_paise + order.tax_paise, i18n.language) })}</strong>
          {order.state === "pending" ? (
            <>
              <button className="vy-btn vy-btn-primary" disabled={busy} onClick={() => simulate("succeeded")}>
                {t("commercial:checkout.succeed")}
              </button>
              <button className="vy-btn vy-btn-ghost" disabled={busy} onClick={() => simulate("failed")}>
                {t("commercial:checkout.fail")}
              </button>
            </>
          ) : (
            <>
              <p>{t("commercial:checkout.done", { state: t(`commercial:paymentState.${order.state}` as "paymentState.pending") })}</p>
              <a href={`/promotions/${order.ref_id}`}>{t("commercial:checkout.back")} →</a>
            </>
          )}
        </div>
      )}
    </main>
  );
}

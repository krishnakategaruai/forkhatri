"use client";

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import {
  confirmOrder,
  createOrder,
  formatRupees,
  getCatalogue,
  openRazorpayCheckout,
  sandboxPay,
  type Plan,
} from "@/lib/billing";

/* [DEC-V1-033] Buying one of the two agent plans in place — the agent's own
 * membership (AGENT) or a family's Agent Connect — at the price a Mangalya
 * administrator set. Terms side by side, one button; the same order,
 * Razorpay and development-sandbox path as /plans. */

export default function AgentPlanCheckout({
  code,
  onPaid,
  payLabel,
}: {
  code: "AGENT" | "AGENT_CONNECT";
  onPaid: () => void;
  payLabel?: string;
}) {
  const { t } = useTranslation(["agents", "billing", "common"]);
  const [plan, setPlan] = useState<Plan | null | undefined>(undefined);
  const [months, setMonths] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sandbox, setSandbox] = useState(false);

  useEffect(() => {
    let alive = true;
    getCatalogue([code]).then((c) => {
      if (!alive) return;
      const p = c?.plans.find((x) => x.code === code) ?? null;
      setPlan(p);
      if (p?.terms.length) setMonths(p.terms[0].months);
    });
    return () => {
      alive = false;
    };
  }, [code]);

  if (plan === undefined) return <p className="caption">{t("common:state.loading")}</p>;
  if (!plan || plan.terms.length === 0) return null;
  const term = plan.terms.find((x) => x.months === months) ?? plan.terms[0];

  async function pay() {
    setBusy(true);
    setError(null);
    const order = await createOrder(code, term.months);
    if (!order.ok) {
      setBusy(false);
      setError(order.message ?? t("agents:membership.failed"));
      return;
    }
    const checkout = order.data;
    let confirmed;
    if (!checkout.key_id) {
      setSandbox(true);
      confirmed = await sandboxPay(checkout.order.id);
    } else {
      const proof = await openRazorpayCheckout(checkout, {
        name: "Mangalya",
        description: plan?.name ?? "",
        accent: "#cc0106",
      });
      if (!proof) {
        setBusy(false);
        return;
      }
      confirmed = await confirmOrder(checkout.order.id, proof.paymentId, proof.signature);
    }
    setBusy(false);
    if (!confirmed.ok) {
      setError(confirmed.message ?? t("agents:membership.failed"));
      return;
    }
    onPaid();
  }

  return (
    <div className="ag-form">
      <div className="ag-terms" role="group">
        {plan.terms.map((x) => (
          <button
            key={x.months}
            type="button"
            className="ag-term"
            aria-pressed={x.months === term.months}
            onClick={() => setMonths(x.months)}
          >
            <span className="ag-term__months">{t("agents:membership.term", { months: x.months })}</span>
            <span className="ag-term__price">{t("agents:membership.price", { amount: formatRupees(x.amount_paise) })}</span>
          </button>
        ))}
      </div>
      <div className="ag-row">
        <button type="button" className="btn btn--primary" disabled={busy} onClick={pay}>
          {busy
            ? t("agents:membership.paying")
            : payLabel ?? t("agents:membership.pay", { amount: formatRupees(term.total_paise) })}
        </button>
        {sandbox && <span className="caption">{t("agents:membership.sandbox")}</span>}
      </div>
      {error && <p className="ag-error">{error}</p>}
    </div>
  );
}

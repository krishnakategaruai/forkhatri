"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import SacredLoader from "@/components/SacredLoader";
import { useActiveContext } from "@/lib/activeContext";
import { requireSession } from "@/lib/auth";
import {
  createOrder,
  formatRupees,
  getCatalogue,
  getMyPlan,
  openRazorpayCheckout,
  confirmOrder,
  sandboxPay,
  type Catalogue,
  type MyPlan,
  type Plan,
} from "@/lib/billing";
import { useLoaderHold } from "@/lib/useLoaderHold";

import "./plans.css";

/* Plans — DEC-V1-031, linked from the bottom of Home (owner, 2026-09-28).
 *
 * Three plans side by side, the term chosen per plan, and checkout in place:
 * the order total with GST shown as its own line, then Razorpay when its
 * keys are set, or the development sandbox before that. A plan changes what
 * this search can do, never where anyone appears (the values line says so).
 * A parent acting for their child sees and buys the child's plan — the
 * entitlement belongs to the candidate. */

type Step =
  | { kind: "idle" }
  | { kind: "busy"; code: string }
  | { kind: "ready"; code: string; orderId: string; total: number; gst: number; amount: number; sandbox: boolean; checkout: Awaited<ReturnType<typeof createOrder>> }
  | { kind: "paid"; code: string; until: string | null }
  | { kind: "error"; code: string; message: string };

export default function PlansPage() {
  const loaderHold = useLoaderHold();
  const { t, i18n } = useTranslation(["billing", "common"]);
  const router = useRouter();
  const { active, loaded } = useActiveContext();
  const forId = active?.kind === "family" ? active.circle.candidate_account_id : undefined;
  const [catalogue, setCatalogue] = useState<Catalogue | null | "error">(null);
  const [mine, setMine] = useState<MyPlan | null>(null);
  const [terms, setTerms] = useState<Record<string, number>>({});
  const [step, setStep] = useState<Step>({ kind: "idle" });

  useEffect(() => {
    if (!loaded) return;
    let alive = true;
    (async () => {
      const session = await requireSession();
      if (!alive || !session) return;
      const [cat, plan] = await Promise.all([getCatalogue(), getMyPlan(forId)]);
      if (!alive) return;
      setCatalogue(cat ?? "error");
      setMine(plan);
    })();
    return () => {
      alive = false;
    };
  }, [loaded, forId]);

  if (catalogue === null || loaderHold) {
    return (
      <main className="screen screen--centered">
        <SacredLoader />
      </main>
    );
  }

  const date = (iso: string | null) =>
    iso ? new Intl.DateTimeFormat(`${i18n.language}-IN`, { day: "numeric", month: "long", year: "numeric" }).format(new Date(iso)) : "";

  async function choose(plan: Plan, months: number) {
    setStep({ kind: "busy", code: plan.code });
    const outcome = await createOrder(plan.code, months);
    if (!outcome.ok) {
      setStep({ kind: "error", code: plan.code, message: outcome.message ?? t("billing:checkout.failed") });
      return;
    }
    const { order, key_id } = outcome.data;
    setStep({
      kind: "ready",
      code: plan.code,
      orderId: order.id,
      total: order.total_paise,
      gst: order.gst_paise,
      amount: order.amount_paise,
      sandbox: !key_id,
      checkout: outcome,
    });
  }

  async function pay(plan: Plan) {
    if (step.kind !== "ready" || !step.checkout.ok) return;
    const checkout = step.checkout.data;
    setStep({ kind: "busy", code: plan.code });
    let confirmed;
    if (!checkout.key_id) {
      confirmed = await sandboxPay(checkout.order.id);
    } else {
      const proof = await openRazorpayCheckout(checkout, {
        name: "Mangaly",
        description: plan.name,
        accent: "#cc0106",
      });
      if (!proof) {
        setStep({ kind: "error", code: plan.code, message: t("billing:checkout.dismissed") });
        return;
      }
      confirmed = await confirmOrder(checkout.order.id, proof.paymentId, proof.signature);
    }
    if (!confirmed.ok) {
      setStep({ kind: "error", code: plan.code, message: confirmed.message ?? t("billing:checkout.failed") });
      return;
    }
    const plan2 = await getMyPlan(forId);
    setMine(plan2);
    setStep({ kind: "paid", code: plan.code, until: plan2?.ends_at ?? null });
  }

  return (
    <>
      <header className="topbar">
        <button className="icon-btn" onClick={() => router.back()} aria-label={t("common:action.back")}>
          ←
        </button>
        <h1>{t("billing:title")}</h1>
        <span style={{ width: 44 }} aria-hidden="true" />
      </header>

      <main className="screen">
        <div className="plans">
          <div className="plans__lead">
            <p className="plans__eyebrow">{t("billing:eyebrow")}</p>
            <p className="plans__intro">{t("billing:intro")}</p>
            <p className="plans__values">{t("billing:valuesLine")}</p>
            {mine && (
              <p className="plans__status caption">
                {t("billing:me.row")}: {mine.plan_name}
                {mine.ends_at ? ` · ${t("billing:me.until", { date: date(mine.ends_at) })}` : ""}
                {" · "}
                {mine.usage.daily_requests == null
                  ? t("billing:me.requestsUnlimited")
                  : t("billing:me.requestsToday", {
                      used: mine.usage.requests_sent_today,
                      limit: mine.usage.daily_requests,
                    })}
              </p>
            )}
          </div>

          {catalogue === "error" ? (
            <p className="plans__status">{t("billing:unavailable")}</p>
          ) : (
            <div className="plans__grid">
              {catalogue.plans.map((plan) => {
                const current = mine?.plan_code === plan.code;
                const featured = plan.code === "GOLD";
                const months = terms[plan.code] ?? plan.terms[0]?.months;
                const term = plan.terms.find((x) => x.months === months) ?? plan.terms[0];
                const mineStep = step.kind !== "idle" && step.code === plan.code ? step : null;
                const includedPlan = plan.includes ? catalogue.plans.find((p) => p.code === plan.includes) : null;
                const includes = includedPlan?.name ?? null;
                const includedFeatures = includedPlan?.features ?? [];
                return (
                  <section
                    key={plan.code}
                    className={`plan${featured ? " plan--featured" : ""}${current ? " plan--current" : ""}`}
                    aria-labelledby={`plan-${plan.code}`}
                  >
                    {current && <span className="plan__badge chip">{t("billing:action.current")}</span>}
                    <div className="plan__head">
                      <h3 className="plan__name" id={`plan-${plan.code}`}>
                        {plan.name}
                      </h3>
                      <p className="plan__blurb">{plan.blurb}</p>
                    </div>

                    <div className="plan__price">
                      {term ? (
                        <>
                          {/* The price you pay, GST included, in whole rupees. */}
                          <span className="plan__amount">{formatRupees(Math.round(term.total_paise / 100) * 100)}</span>
                          <span className="plan__per">
                            {t("billing:price.forTerm", { term: term.label })} ·{" "}
                            {t("billing:price.perMonth", {
                              amount: formatRupees(Math.round(term.total_paise / term.months / 100) * 100),
                            })}
                          </span>
                          <span className="plan__gst">{t("billing:price.includesGst", { gst: formatRupees(term.gst_paise) })}</span>
                        </>
                      ) : null}
                    </div>

                    {plan.terms.length > 1 && (
                      <div className="plan__terms" role="group" aria-label={t("billing:term.label")}>
                        {plan.terms.map((x) => (
                          <button
                            key={x.months}
                            type="button"
                            className={`plan__term${x.months === months ? " is-active" : ""}`}
                            aria-pressed={x.months === months}
                            onClick={() => setTerms((all) => ({ ...all, [plan.code]: x.months }))}
                          >
                            {x.label}
                          </button>
                        ))}
                      </div>
                    )}

                    <div>
                      <p className="plan__included">{t("billing:included")}</p>
                      {includes && <p className="plan__includes">{t("billing:includesPlan", { plan: includes })}</p>}
                    </div>
                    <ul className="plan__features">
                      {/* Under "Everything in Gold, and": only what this plan adds. */}
                      {plan.features
                        .filter((f) => !includedFeatures.includes(f))
                        .map((f) => (
                        <li key={f} className="plan__feature">
                          <span className="plan__tick" aria-hidden="true">
                            ✓
                          </span>
                          {f}
                        </li>
                      ))}
                    </ul>

                    {term && forId && active?.kind === "family" && (
                      <p className="plan__note">
                        {t("billing:familyNote", { name: active.circle.candidate_name.split(" ")[0] })}
                      </p>
                    )}
                    {term && !forId && (
                      <div className="plan__cta">
                        {mineStep?.kind === "ready" ? (
                          <div className="plan__checkout">
                            <p className="plan__note">
                              {t("billing:checkout.ready", { plan: plan.name, term: term.label })}
                            </p>
                            <div className="plan__checkout-line">
                              <span>{plan.name}</span>
                              <span>{formatRupees(mineStep.amount)}</span>
                            </div>
                            <div className="plan__checkout-line">
                              <span>GST 18%</span>
                              <span>{formatRupees(mineStep.gst)}</span>
                            </div>
                            <div className="plan__checkout-line plan__checkout-line--total">
                              <span>{t("billing:price.total", { total: "" }).trim()}</span>
                              <span>{formatRupees(mineStep.total)}</span>
                            </div>
                            <button type="button" className="btn btn--primary" onClick={() => pay(plan)}>
                              {mineStep.sandbox
                                ? t("billing:action.paySandbox", { total: formatRupees(mineStep.total) })
                                : t("billing:action.pay", { total: formatRupees(mineStep.total) })}
                            </button>
                            {mineStep.sandbox && <p className="plan__note">{t("billing:checkout.sandboxNote")}</p>}
                          </div>
                        ) : mineStep?.kind === "paid" ? (
                          <p className="plan__done" role="status">
                            {t("billing:checkout.paid", { plan: plan.name, date: date(mineStep.until) })}
                          </p>
                        ) : (
                          <button
                            type="button"
                            className={`btn ${featured ? "btn--primary" : "plan__second"}`}
                            disabled={mineStep?.kind === "busy"}
                            onClick={() => choose(plan, term.months)}
                          >
                            {mineStep?.kind === "busy"
                              ? t("billing:checkout.creating")
                              : current
                                ? t("billing:action.renew", { plan: plan.name })
                                : t("billing:action.choose", { plan: plan.name })}
                          </button>
                        )}
                        {mineStep?.kind === "error" && (
                          <p className="plan__error" role="alert">
                            {mineStep.message}
                          </p>
                        )}
                      </div>
                    )}
                  </section>
                );
              })}
            </div>
          )}
          <p className="plans__foot">{t("billing:gstIncludedNote")}</p>
        </div>
      </main>
    </>
  );
}

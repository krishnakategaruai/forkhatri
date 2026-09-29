"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import AccountButton from "@/components/AccountButton";
import {
  LIMIT_NAMES,
  formatDay,
  getLimits,
  listApplications,
  listPrices,
  reviewApplication,
  setLimit,
  setPrice,
  type AdminApplication,
  type AdminPrice,
  type AgentLimits,
} from "@/lib/agents";

import "../agent.css";

/* [DEC-V1-033] Mangaly moderators: check agents before families can choose
 * them, and set what each plan costs — the owner asked that Agent Connect be
 * "a premium tier which admin can decide", so every plan term's price is
 * editable here over the catalogue placeholder. The same applications also
 * appear in the platform console's Mangaly view. */

function PriceRow({ price, onSaved }: { price: AdminPrice; onSaved: () => void }) {
  const { t } = useTranslation(["agents", "billing"]);
  const [rupees, setRupees] = useState(String(price.amount_paise / 100));
  const [active, setActive] = useState(price.active);
  const [state, setState] = useState<"idle" | "saving" | "saved">("idle");

  const save = async () => {
    setState("saving");
    const out = await setPrice({
      plan_code: price.plan_code,
      term_months: price.term_months,
      amount_paise: Math.round(Number(rupees) * 100),
      active,
    });
    setState(out.ok ? "saved" : "idle");
    if (out.ok) onSaved();
  };

  return (
    <tr>
      <td>{t(`billing:plan.${price.plan_code}.name`, { defaultValue: price.plan_code })}</td>
      <td>{t("agents:membership.term", { months: price.term_months })}</td>
      <td>
        <input
          className="input"
          type="number"
          min={1}
          step={1}
          value={rupees}
          onChange={(e) => {
            setRupees(e.target.value);
            setState("idle");
          }}
          aria-label={t("agents:review.prices.price")}
        />
        {price.catalogue_paise != null && price.catalogue_paise !== price.amount_paise && (
          <div className="caption">{t("agents:review.prices.catalogue", { amount: (price.catalogue_paise / 100).toLocaleString("en-IN") })}</div>
        )}
      </td>
      <td>
        <label className="ag-consent">
          <input
            type="checkbox"
            checked={active}
            onChange={(e) => {
              setActive(e.target.checked);
              setState("idle");
            }}
          />
          {t("agents:review.prices.active")}
        </label>
      </td>
      <td>
        {state === "saved" ? (
          <span className="ag-ok">{t("agents:review.prices.saved")}</span>
        ) : (
          <button type="button" className="btn btn--secondary btn--sm" disabled={state === "saving" || !(Number(rupees) > 0)} onClick={save}>
            {t("agents:review.prices.save")}
          </button>
        )}
      </td>
    </tr>
  );
}

/* [DEC-V1-034] The fair-use limits, tuned without a code change. */
function LimitRow({ name, value }: { name: keyof AgentLimits; value: number }) {
  const { t } = useTranslation(["agents"]);
  const [draft, setDraft] = useState(String(value));
  const [state, setState] = useState<"idle" | "saving" | "saved">("idle");
  const save = async () => {
    setState("saving");
    const out = await setLimit(name, Math.round(Number(draft)));
    setState(out.ok ? "saved" : "idle");
  };
  return (
    <tr>
      <td>{t(`agents:limits.names.${name}`)}</td>
      <td>
        <input
          className="input"
          type="number"
          min={0}
          step={1}
          value={draft}
          onChange={(e) => {
            setDraft(e.target.value);
            setState("idle");
          }}
          aria-label={t(`agents:limits.names.${name}`)}
        />
      </td>
      <td>
        {state === "saved" ? (
          <span className="ag-ok">{t("agents:limits.saved")}</span>
        ) : (
          <button type="button" className="btn btn--secondary btn--sm" disabled={state === "saving" || !(Number(draft) >= 0) || draft === ""} onClick={save}>
            {t("agents:limits.save")}
          </button>
        )}
      </td>
    </tr>
  );
}

export default function AgentReviewPage() {
  const { t, i18n } = useTranslation(["agents", "common"]);
  const [apps, setApps] = useState<AdminApplication[] | null | undefined>(undefined);
  const [prices, setPrices] = useState<AdminPrice[] | null>(null);
  const [limits, setLimits] = useState<AgentLimits | null>(null);

  const reload = useCallback(async () => {
    setApps(await listApplications());
    setPrices(await listPrices());
  }, []);

  useEffect(() => {
    let alive = true;
    Promise.all([listApplications(), listPrices(), getLimits()]).then(([a, p, l]) => {
      if (!alive) return;
      setApps(a);
      setPrices(p);
      setLimits(l);
    });
    return () => {
      alive = false;
    };
  }, []);

  const decide = async (a: AdminApplication, status: "verified" | "rejected") => {
    const out = await reviewApplication(a.account_id, status);
    if (out.ok) await reload();
  };

  return (
    <>
      <header className="topbar">
        <Link className="link" href="/agent">
          ‹ {t("agents:workspace.title")}
        </Link>
        <div className="topbar__actions">
          <AccountButton />
        </div>
      </header>
      <main className="screen ag-screen">
        {apps === undefined ? (
          <p className="caption">{t("common:state.loading")}</p>
        ) : apps === null ? (
          <p className="caption">{t("agents:review.notModerator")}</p>
        ) : (
          <>
            <section className="section ag-form">
              <h2 className="ag-title">{t("agents:review.title")}</h2>
              {apps.length === 0 ? (
                <p className="caption">{t("agents:review.empty")}</p>
              ) : (
                <ul className="ag-apps">
                  {apps.map((a) => (
                    <li key={a.account_id} className="ag-app">
                      <div className="ag-bar">
                        <div className="ag-head">
                          <strong>{a.business_name ?? a.display_name}</strong>
                          <span className="caption">
                            {[a.business_name ? a.display_name : null, a.city, a.business_phone].filter(Boolean).join(" · ")}
                          </span>
                        </div>
                        <span className={`ag-pill${a.verification_status === "verified" ? " ag-pill--ok" : a.verification_status === "pending" ? "" : " ag-pill--quiet"}`}>
                          {t(
                            a.verification_status === "verified"
                              ? "agents:status.verified"
                              : a.verification_status === "suspended" || (a.verification_status as string) === "contact_suspended"
                                ? `agents:status.${a.verification_status === "suspended" ? "suspended" : "contactSuspended"}`
                                : `agents:status.${a.verification_status}.title`,
                          )}
                        </span>
                      </div>
                      {a.about && <p className="caption" style={{ margin: 0 }}>{a.about}</p>}
                      <span className="caption">
                        {[
                          a.years_active != null ? t("agents:family.directory.years", { count: a.years_active }) : null,
                          a.communities.join(", ") || null,
                          a.languages.map((l) => t(`agents:join.language.${l}`, { defaultValue: l })).join(", ") || null,
                          a.applied_at ? t("agents:review.applied", { date: formatDay(a.applied_at, i18n.language) }) : null,
                          a.membership_until
                            ? t("agents:review.membership", { date: formatDay(a.membership_until, i18n.language) })
                            : t("agents:review.noMembership"),
                        ]
                          .filter(Boolean)
                          .join(" · ")}
                      </span>
                      <div className="ag-row">
                        {a.verification_status !== "verified" && (
                          <button type="button" className="btn btn--primary btn--sm" onClick={() => decide(a, "verified")}>
                            {t("agents:review.verify")}
                          </button>
                        )}
                        {a.verification_status !== "rejected" && (
                          <button type="button" className="btn btn--ghost btn--sm" onClick={() => decide(a, "rejected")}>
                            {t("agents:review.reject")}
                          </button>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </section>
            {prices && (
              <section className="section ag-form">
                <h2 className="h3" style={{ margin: 0 }}>
                  {t("agents:review.prices.title")}
                </h2>
                <p className="caption" style={{ margin: 0 }}>
                  {t("agents:review.prices.lede")}
                </p>
                <div style={{ overflowX: "auto" }}>
                  <table className="ag-prices">
                    <thead>
                      <tr>
                        <th>{t("agents:review.prices.plan")}</th>
                        <th>{t("agents:review.prices.term")}</th>
                        <th>{t("agents:review.prices.price")}</th>
                        <th />
                        <th />
                      </tr>
                    </thead>
                    <tbody>
                      {prices.map((p) => (
                        <PriceRow key={`${p.plan_code}-${p.term_months}`} price={p} onSaved={() => undefined} />
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            )}
            {limits && (
              <section className="section ag-form">
                <h2 className="h3" style={{ margin: 0 }}>
                  {t("agents:limits.title")}
                </h2>
                <p className="caption" style={{ margin: 0 }}>
                  {t("agents:limits.lede")}
                </p>
                <div style={{ overflowX: "auto" }}>
                  <table className="ag-prices">
                    <tbody>
                      {LIMIT_NAMES.map((n) => (
                        <LimitRow key={n} name={n} value={limits[n]} />
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            )}
          </>
        )}
      </main>
    </>
  );
}

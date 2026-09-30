"use client";

// [FE2 — imp-backend-b §4, research §7] Service packages, the viewer's side.
//
// Up to three tiers (Basic · Standard · Premium). Phone: tabs, one tier at a
// time, the middle tier pre-selected (the research's anchor), with price,
// delivery, revisions and what is included. Desktop: a column per tier and
// a row per attribute, with ✓ / — for each included item across tiers, so
// the tiers can be compared at a glance. "Request this package" opens a
// prefilled message right there and sends it as an ordinary enquiry — no
// separate screen; after sending, the conversation is one tap away.
import { useState } from "react";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import type { ServicePackage } from "@/lib/sdk";
import { formatRupees } from "@/lib/format";
import Icon from "@/app/components/Icon";
import DisabledReason from "@/app/components/DisabledReason";

const TIER_ORDER = ["basic", "standard", "premium"];

export interface PackagesCompareProps {
  packages: ServicePackage[];
  providerName: string;
  /** Sends the request; resolves with the new enquiry id. */
  onRequest: (pkg: ServicePackage, message: string) => Promise<string>;
}

export default function PackagesCompare({ packages, providerName, onRequest }: PackagesCompareProps) {
  const { t, i18n } = useTranslation(["packages", "common"]);
  const tiers = [...packages].sort((a, b) => TIER_ORDER.indexOf(a.tier) - TIER_ORDER.indexOf(b.tier));
  const [tab, setTab] = useState(() => (tiers.find((p) => p.tier === "standard") ?? tiers[0])?.id ?? null);
  const [asking, setAsking] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  if (tiers.length === 0) return null;

  const money = (p: number) => formatRupees(p, i18n.language);
  const allIncludes = [...new Set(tiers.flatMap((p) => p.includes))];
  // [FE1 — critique N12] "Ready in" instead of Fiverr's "Delivery"; revisions
  // are optional and never shown as a lone dash.
  const delivery = (p: ServicePackage) => (p.delivery_days != null ? t("packages:days", { count: p.delivery_days }) : null);
  const revisions = (p: ServicePackage) => (p.revisions != null ? t("packages:revisionsCount", { count: p.revisions }) : null);
  const anyRevisions = tiers.some((p) => p.revisions != null);
  const anyDelivery = tiers.some((p) => p.delivery_days != null);

  function startRequest(p: ServicePackage) {
    setAsking(p.id);
    setError(null);
    setMessage(t("packages:requestPrefill", { name: providerName, tier: p.tier_label, pkg: p.name, price: money(p.price_paise) }));
  }

  async function send(p: ServicePackage) {
    setBusy(true);
    setError(null);
    try {
      const enquiryId = await onRequest(p, message.trim());
      setSent((s) => ({ ...s, [p.id]: enquiryId }));
      setAsking(null);
    } catch (e) {
      setError(e instanceof Error && e.message ? e.message : t("common:state.actionFailed"));
    } finally {
      setBusy(false);
    }
  }

  function requestBlock(p: ServicePackage) {
    if (sent[p.id]) {
      return (
        <p className="vy-muted" role="status">
          ✓ {t("packages:sent")}{" "}
          <Link className="vy-link-btn" href={`/enquiries/${sent[p.id]}`}>{t("packages:openConversation")}</Link>
        </p>
      );
    }
    if (asking === p.id) {
      return (
        <div className="vy-stack" style={{ gap: 8 }}>
          <textarea className="vy-textarea" rows={3} maxLength={2000} value={message} onChange={(e) => setMessage(e.target.value)} aria-label={t("packages:messageLabel")} />
          <div className="vy-row" style={{ flexWrap: "wrap" }}>
            <button className="vy-btn vy-btn-primary" aria-describedby={message.trim().length < 5 ? "why-package-msg" : undefined} disabled={busy || message.trim().length < 5} onClick={() => send(p)}>
              {busy ? t("packages:sending") : t("packages:send")}
            </button>
            <DisabledReason id={"why-package-msg"} show={message.trim().length < 5}>{t("common:disabled.min5")}</DisabledReason>
            <button className="vy-btn vy-btn-ghost" onClick={() => setAsking(null)}>{t("common:action.cancel")}</button>
          </div>
          {error && <p className="vy-error">{error}</p>}
        </div>
      );
    }
    return (
      // secondary: the page's one primary action stays "Enquire now"
      <button className="vy-btn vy-btn-secondary" onClick={() => startRequest(p)}>
        {t("packages:request")}
      </button>
    );
  }

  const current = tiers.find((p) => p.id === tab) ?? tiers[0];

  return (
    <section className="vy-card vy-stack" style={{ gap: 16 }} aria-labelledby="pkg-title">
      <div className="vy-stack" style={{ gap: 4 }}>
        <h2 id="pkg-title" className="vy-card-title">{t("packages:title")}</h2>
        <p className="vy-muted">{t("packages:subtitle")}</p>
      </div>

      {/* phone: tabs */}
      <div className="vy-pkg-mobile vy-stack" style={{ gap: 14 }}>
        {tiers.length > 1 && (
          <div className="vy-pkg-tabs" role="tablist">
            {tiers.map((p) => (
              <button key={p.id} role="tab" aria-selected={p.id === current.id} onClick={() => setTab(p.id)}>
                {p.tier_label}
              </button>
            ))}
          </div>
        )}
        <div className="vy-stack" style={{ gap: 10 }} role="tabpanel">
          <div className="vy-row" style={{ justifyContent: "space-between", alignItems: "baseline", gap: 12 }}>
            <strong>{current.name}</strong>
            <span className="vy-pkg-price">{money(current.price_paise)}</span>
          </div>
          {current.description && <p style={{ fontSize: 14 }}>{current.description}</p>}
          {(delivery(current) || revisions(current)) && <p className="vy-muted">{[delivery(current), revisions(current)].filter(Boolean).join(" · ")}</p>}
          {current.includes.length > 0 && (
            <ul className="vy-pkg-list">
              {current.includes.map((x) => (
                <li key={x}><Icon name="check" size={15} /> {x}</li>
              ))}
            </ul>
          )}
          {requestBlock(current)}
        </div>
      </div>

      {/* desktop: a column per tier */}
      <table className="vy-pkg-table">
        <thead>
          <tr>
            <th scope="col"><span className="vy-visually-hidden">{t("packages:tier")}</span></th>
            {tiers.map((p) => (
              <th key={p.id} scope="col">
                <span className="vy-eyebrow">{p.tier_label}</span>
                <br />
                {p.name}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          <tr>
            <th scope="row">{t("packages:price")}</th>
            {tiers.map((p) => (
              <td key={p.id} data-yes><span className="vy-pkg-price" style={{ fontSize: 22 }}>{money(p.price_paise)}</span></td>
            ))}
          </tr>
          {tiers.some((p) => p.description) && (
            <tr>
              <th scope="row">{t("packages:whatYouGet")}</th>
              {tiers.map((p) => <td key={p.id}>{p.description ?? "—"}</td>)}
            </tr>
          )}
          {anyDelivery && (
            <tr>
              <th scope="row">{t("packages:delivery")}</th>
              {tiers.map((p) => <td key={p.id} data-yes>{delivery(p) ?? "—"}</td>)}
            </tr>
          )}
          {anyRevisions && (
            <tr>
              <th scope="row">{t("packages:revisions")}</th>
              {tiers.map((p) => <td key={p.id} data-yes>{revisions(p) ?? "—"}</td>)}
            </tr>
          )}
          {allIncludes.map((x) => (
            <tr key={x}>
              <th scope="row">{x}</th>
              {tiers.map((p) =>
                p.includes.includes(x) ? (
                  <td key={p.id} data-yes aria-label={t("packages:included")}><Icon name="check" size={16} style={{ color: "var(--trust-verified)" }} /></td>
                ) : (
                  <td key={p.id} aria-label={t("packages:notIncluded")}>—</td>
                ),
              )}
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <td />
            {tiers.map((p) => <td key={p.id}>{requestBlock(p)}</td>)}
          </tr>
        </tfoot>
      </table>
    </section>
  );
}

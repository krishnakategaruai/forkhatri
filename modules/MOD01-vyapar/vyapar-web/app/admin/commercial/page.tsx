"use client";

// [TR049] Commercial administration and audit review (FR49) — operator view.
// Four sections on one screen: products with their versions (a price change
// is a NEW version; there is no edit control because there is no such API
// route), orders by kind and state with a refund form bounded by the order's
// remaining value, ranking diagnostics that explain rather than override,
// and audit search. Deliberately absent, per SP049's separation of powers:
// any control to change a verification state, a ranking weight or a
// moderation decision.
// [Design language 2026-09-29, operator console] Dense tables for products,
// orders and the audit log; the refund and diagnostics forms nested one
// lightness step down.
// Traces to: FR49, FR31, FR32, TR049, SP049
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { AlertTriangle, CheckCircle2, Package, Receipt, ScrollText, Search, ShieldAlert } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { formatPaise } from "@/lib/money";
import Screen from "@/app/components/Screen";
import { SkeletonGrid } from "@/app/components/States";
import DealsEmpty from "@/app/components/deals/Empty";
import { formatDate, formatDateTime } from "@/lib/format";
import { promotionTone } from "@/app/promotions/tone";
import "@/app/styles/deals-2026.css";

interface Product {
  id: string;
  version: number;
  kind: string;
  name: string;
  duration_days: number | null;
  billing: string;
  price_paise: number;
  tax_paise: number;
  active: boolean;
  orders: number;
}

interface Order {
  id: string;
  kind: string;
  owner_id: string;
  state: string;
  product: string;
  created_at: string;
  payment_order_id: string | null;
  payment_state: string | null;
  charged_paise: number | null;
  refunded_paise: number | null;
}

interface Diagnostics {
  target_kind: string;
  target_id: string;
  title: string | null;
  eligible: boolean;
  exclusions: string[];
  score: { total: number; signals: { signal: string; value: number; weight: number; contribution: number }[] } | null;
  note: string | null;
}

interface AuditRow {
  id: number;
  at: string;
  actor_id: string | null;
  action: string;
  object_kind: string;
  object_id: string;
  reason_code: string | null;
  outcome: string;
}

const REFUND_REASONS = ["scam_confirmed", "policy_other", "no_violation", "appeal_evidence_accepted"];

export default function AdminCommercialPage() {
  const { t, i18n } = useTranslation(["adminCommercial", "commercial", "trustSafety", "ranking", "common"]);
  const [forbidden, setForbidden] = useState(false);
  const [products, setProducts] = useState<Product[] | null>(null);
  const [orderKind, setOrderKind] = useState<"promotion" | "entitlement" | "campaign">("promotion");
  const [orders, setOrders] = useState<Order[]>([]);
  const [notice, setNotice] = useState<{ text: string; tone: "good" | "bad" } | null>(null);
  const [busy, setBusy] = useState(false);
  const [refundFor, setRefundFor] = useState<Order | null>(null);
  const [refundAmount, setRefundAmount] = useState("");
  const [refundReason, setRefundReason] = useState(REFUND_REASONS[0]);
  const [newPrice, setNewPrice] = useState<Record<string, string>>({});
  const [diagKind, setDiagKind] = useState<"listing" | "opportunity">("listing");
  const [diagId, setDiagId] = useState("");
  const [diag, setDiag] = useState<Diagnostics | null>(null);
  const [auditRows, setAuditRows] = useState<AuditRow[]>([]);
  const [auditActor, setAuditActor] = useState("");
  const [auditAction, setAuditAction] = useState("");

  const money = (p: number) => formatPaise(p, i18n.language);

  const loadProducts = useCallback(async () => {
    try {
      setProducts(await api.get<Product[]>("/v1/admin/commercial/products"));
    } catch (e) {
      if (e instanceof ApiError && e.status === 403) setForbidden(true);
      setProducts([]);
    }
  }, []);

  const loadOrders = useCallback(async () => {
    try {
      setOrders(await api.get<Order[]>(`/v1/admin/commercial/orders?kind=${orderKind}`));
    } catch {
      setOrders([]);
    }
  }, [orderKind]);

  const loadAudit = useCallback(async () => {
    const params = new URLSearchParams();
    if (auditActor) params.set("actor_id", auditActor);
    if (auditAction) params.set("action", auditAction);
    try {
      setAuditRows(await api.get<AuditRow[]>(`/v1/admin/audit?${params.toString()}`));
    } catch {
      setAuditRows([]);
    }
  }, [auditActor, auditAction]);

  useEffect(() => {
    // The initial load runs once per id (the pattern this module's data hooks use).
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadProducts();
  }, [loadProducts]);
  useEffect(() => {
    // The initial load runs once per id (the pattern this module's data hooks use).
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadOrders();
  }, [loadOrders]);
  useEffect(() => {
    // The initial load runs once per id (the pattern this module's data hooks use).
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadAudit();
  }, [loadAudit]);

  if (forbidden) {
    return (
      <Screen width="console">
        <div className="vy-dl-page">
          <div className="vy-dl-head">
            <h1>{t("adminCommercial:title")}</h1>
          </div>
          <DealsEmpty tone="neutral" icon={<ShieldAlert size={24} strokeWidth={1.75} aria-hidden="true" />} title={t("adminCommercial:notOperator")} />
        </div>
      </Screen>
    );
  }

  async function addVersion(product: Product) {
    const raw = newPrice[product.id];
    if (!raw) return;
    setBusy(true);
    setNotice(null);
    try {
      await api.post("/v1/admin/commercial/products", {
        id: product.id,
        kind: product.kind,
        name: product.name,
        duration_days: product.duration_days,
        billing: product.billing,
        price_paise: Math.round(Number(raw) * 100),
      });
      setNewPrice((p) => ({ ...p, [product.id]: "" }));
      await loadProducts();
      await loadAudit();
    } catch (e) {
      setNotice({ text: e instanceof ApiError ? String(e.detail) : t("common:state.actionFailed"), tone: "bad" });
    } finally {
      setBusy(false);
    }
  }

  async function submitRefund() {
    if (!refundFor?.payment_order_id) return;
    setBusy(true);
    setNotice(null);
    try {
      const res = await api.post<{ refunded: boolean; notice?: string }>("/v1/admin/commercial/refunds", {
        payment_order_id: refundFor.payment_order_id,
        amount_paise: Math.round(Number(refundAmount) * 100),
        reason_code: refundReason,
      });
      setNotice(res.refunded ? { text: t("adminCommercial:refund.done"), tone: "good" } : { text: t("commercial:promotion.resultUnavailable"), tone: "bad" });
      setRefundFor(null);
      setRefundAmount("");
      await loadOrders();
      await loadAudit();
    } catch (e) {
      setNotice({ text: e instanceof ApiError ? String(e.detail) : t("common:state.actionFailed"), tone: "bad" });
    } finally {
      setBusy(false);
    }
  }

  async function runDiagnostics() {
    setNotice(null);
    try {
      setDiag(await api.get<Diagnostics>(`/v1/admin/commercial/diagnostics/${diagKind}/${diagId.trim()}`));
    } catch (e) {
      setDiag(null);
      setNotice({ text: e instanceof ApiError ? String(e.detail) : t("common:state.actionFailed"), tone: "bad" });
    }
  }

  const productName = (p: Product) => t(`commercial:product.${p.id}` as "product.boost_7d", { defaultValue: p.name || p.id });

  return (
    <Screen width="console">
      <div className="vy-dl-page">
        <div className="vy-dl-head">
          <h1>{t("adminCommercial:title")}</h1>
          <p>{t("adminCommercial:scopeNote")}</p>
        </div>
        {notice && (
          <p className="vy-dl-notice" data-tone={notice.tone} role={notice.tone === "bad" ? "alert" : "status"}>
            {notice.tone === "good" ? <CheckCircle2 size={18} strokeWidth={1.75} aria-hidden="true" /> : <AlertTriangle size={18} strokeWidth={1.75} aria-hidden="true" />}
            <span>{notice.text}</span>
          </p>
        )}

        <section className="vy-dl-sec" aria-labelledby="ac-products">
          <div className="vy-dl-sec-head">
            <span className="vy-dl-tile vy-dl-tile-brand" aria-hidden="true"><Package size={20} strokeWidth={1.75} /></span>
            <h2 id="ac-products" className="vy-card-title">{t("adminCommercial:products.title")}</h2>
            <span className="vy-dl-sec-hint">{t("adminCommercial:products.insertOnly")}</span>
          </div>
          {products === null ? (
            <SkeletonGrid count={2} grid={false} />
          ) : (
            <div className="vy-dl-table-wrap">
              <table className="vy-dl-table">
                <thead>
                  <tr>
                    <th>{t("adminCommercial:products.colProduct")}</th>
                    <th>{t("adminCommercial:products.colBilling")}</th>
                    <th className="vy-dl-num">{t("adminCommercial:products.colPrice")}</th>
                    <th className="vy-dl-num">{t("adminCommercial:products.colTax")}</th>
                    <th className="vy-dl-num">{t("adminCommercial:products.colOrders")}</th>
                    <th>{t("adminCommercial:products.colNewVersion")}</th>
                  </tr>
                </thead>
                <tbody>
                  {products.map((p) => (
                    <tr key={`${p.id}-${p.version}`}>
                      <td>
                        <strong>{productName(p)}</strong>
                        <div className="vy-dl-fine"><span className="vy-dl-code">{p.id}</span> · v{p.version}</div>
                      </td>
                      <td>{t(`adminCommercial:products.billing.${p.billing}` as "products.billing.one_time")}</td>
                      <td className="vy-dl-num">{money(p.price_paise)}</td>
                      <td className="vy-dl-num">{money(p.tax_paise)}</td>
                      <td className="vy-dl-num">{p.orders}</td>
                      <td>
                        <div className="vy-dl-cell-actions" style={{ flexWrap: "nowrap" }}>
                          <input className="vy-input" style={{ minHeight: 36, width: 120, padding: "4px 10px" }} inputMode="decimal" aria-label={t("adminCommercial:products.newPricePlaceholder")} placeholder={t("adminCommercial:products.newPricePlaceholder")} value={newPrice[p.id] ?? ""} onChange={(e) => setNewPrice((s) => ({ ...s, [p.id]: e.target.value }))} />
                          <button className="vy-btn vy-btn-secondary vy-dl-btn-sm" disabled={busy || !newPrice[p.id]} onClick={() => addVersion(p)}>
                            {t("adminCommercial:products.addVersion")}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="vy-dl-sec" aria-labelledby="ac-orders">
          <div className="vy-dl-sec-head">
            <span className="vy-dl-tile vy-dl-tile-green" aria-hidden="true"><Receipt size={20} strokeWidth={1.75} /></span>
            <h2 id="ac-orders" className="vy-card-title">{t("adminCommercial:orders.title")}</h2>
            <span className="vy-dl-sec-hint">{t("adminCommercial:orders.hint")}</span>
          </div>
          <div className="vy-segmented vy-dl-tabs" role="tablist" aria-label={t("adminCommercial:orders.title")}>
            {(["promotion", "entitlement", "campaign"] as const).map((k) => (
              <button key={k} type="button" role="tab" aria-selected={orderKind === k} onClick={() => setOrderKind(k)}>
                {t(`adminCommercial:orders.kind.${k}` as "orders.kind.promotion")}
              </button>
            ))}
          </div>
          {orders.length === 0 && <p className="vy-dl-hint">{t("adminCommercial:orders.empty")}</p>}
          {orders.length > 0 && (
            <div className="vy-dl-table-wrap">
              <table className="vy-dl-table">
                <thead>
                  <tr>
                    <th>{t("adminCommercial:orders.colProduct")}</th>
                    <th>{t("adminCommercial:orders.colMember")}</th>
                    <th>{t("adminCommercial:orders.colDate")}</th>
                    <th>{t("adminCommercial:orders.colState")}</th>
                    <th className="vy-dl-num">{t("adminCommercial:orders.colPaid")}</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {orders.map((o) => (
                    <tr key={o.id}>
                      <td>
                        <strong>{t(`commercial:product.${o.product}` as "product.boost_7d", { defaultValue: o.product })}</strong>
                        <div className="vy-dl-fine"><span className="vy-dl-code">{o.id.slice(0, 8)}</span></div>
                      </td>
                      <td><span className="vy-dl-code">{o.owner_id}</span></td>
                      <td>{formatDate(o.created_at, i18n.language)}</td>
                      <td>
                        <span className="vy-dl-state" data-tone={promotionTone(o.state)}>{t(`commercial:state.${o.state}` as "state.active")}</span>
                      </td>
                      <td className="vy-dl-num">
                        {o.charged_paise != null ? money(o.charged_paise) : "—"}
                        {o.refunded_paise ? <div className="vy-dl-fine">{t("adminCommercial:orders.refunded", { amount: money(o.refunded_paise) })}</div> : null}
                      </td>
                      <td>
                        {o.payment_order_id && o.payment_state === "succeeded" && (
                          <button
                            className="vy-btn vy-btn-ghost vy-dl-btn-sm"
                            onClick={() => {
                              setRefundFor(o);
                              setRefundAmount(String(((o.charged_paise ?? 0) - (o.refunded_paise ?? 0)) / 100));
                            }}
                          >
                            {t("adminCommercial:refund.open")}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {refundFor && (
            <div className="vy-dl-panel">
              <span className="vy-label">{t("adminCommercial:refund.title", { product: t(`commercial:product.${refundFor.product}` as "product.boost_7d", { defaultValue: refundFor.product }) })}</span>
              <div className="vy-field-pair">
                <label className="vy-field">
                  <span className="vy-label">{t("adminCommercial:refund.amount")}</span>
                  <input className="vy-input" inputMode="decimal" value={refundAmount} onChange={(e) => setRefundAmount(e.target.value)} />
                </label>
                <label className="vy-field">
                  <span className="vy-label">{t("adminCommercial:refund.reason")}</span>
                  <select className="vy-select" value={refundReason} onChange={(e) => setRefundReason(e.target.value)}>
                    {REFUND_REASONS.map((r) => (
                      <option key={r} value={r}>{t(`trustSafety:reasonCode.${r}` as "reasonCode.spam")}</option>
                    ))}
                  </select>
                </label>
              </div>
              <div className="vy-dl-actions">
                <button className="vy-btn vy-btn-primary" disabled={busy || !refundAmount} onClick={submitRefund}>{t("adminCommercial:refund.submit")}</button>
                <button className="vy-btn vy-btn-ghost" onClick={() => setRefundFor(null)}>{t("common:action.cancel")}</button>
              </div>
            </div>
          )}
        </section>

        <div className="vy-dl-console-2">
          <section className="vy-dl-sec" aria-labelledby="ac-diag">
            <div className="vy-dl-sec-head">
              <span className="vy-dl-tile vy-dl-tile-teal" aria-hidden="true"><Search size={20} strokeWidth={1.75} /></span>
              <h2 id="ac-diag" className="vy-card-title">{t("adminCommercial:diagnostics.title")}</h2>
              <span className="vy-dl-sec-hint">{t("adminCommercial:diagnostics.help")}</span>
            </div>
            <div className="vy-segmented vy-dl-tabs" role="group" aria-label={t("adminCommercial:diagnostics.title")}>
              {(["listing", "opportunity"] as const).map((k) => (
                <button key={k} type="button" aria-pressed={diagKind === k} onClick={() => setDiagKind(k)}>
                  {t(`trustSafety:objectKind.${k}` as "objectKind.listing")}
                </button>
              ))}
            </div>
            <div className="vy-dl-actions">
              <input className="vy-input" style={{ flex: 1, minWidth: 180 }} value={diagId} onChange={(e) => setDiagId(e.target.value)} placeholder={t("adminCommercial:diagnostics.idPlaceholder")} aria-label={t("adminCommercial:diagnostics.idPlaceholder")} />
              <button className="vy-btn vy-btn-secondary" disabled={!diagId.trim()} onClick={runDiagnostics}>{t("adminCommercial:diagnostics.run")}</button>
            </div>
            {diag && (
              <div className="vy-dl-panel">
                <div className="vy-dl-row-body">
                  <strong>{diag.title ?? diag.target_id}</strong>
                  <span className="vy-dl-tags" style={{ marginTop: 4 }}>
                    <span className="vy-dl-state" data-tone={diag.eligible ? "done" : "warn"}>{diag.eligible ? t("adminCommercial:diagnostics.eligible") : t("adminCommercial:diagnostics.excluded")}</span>
                  </span>
                </div>
                {diag.exclusions.length > 0 && (
                  <ul className="vy-dl-history">
                    {diag.exclusions.map((x) => (
                      <li key={x}><span>{t(`adminCommercial:diagnostics.exclusion.${x}` as "diagnostics.exclusion.state_not_active", { defaultValue: x })}</span></li>
                    ))}
                  </ul>
                )}
                {diag.note === "memberRelative" && <p className="vy-dl-hint">{t("adminCommercial:diagnostics.memberRelative")}</p>}
                {diag.score && (
                  <div className="vy-dl-table-wrap">
                    <table className="vy-dl-table" style={{ minWidth: 0 }}>
                      <thead>
                        <tr>
                          <th>{t("adminCommercial:diagnostics.colSignal")}</th>
                          <th className="vy-dl-num">{t("adminCommercial:diagnostics.colValue")}</th>
                          <th className="vy-dl-num">{t("adminCommercial:diagnostics.colWeight")}</th>
                          <th className="vy-dl-num">{t("adminCommercial:diagnostics.colContribution")}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {diag.score.signals.map((s) => (
                          <tr key={s.signal}>
                            <td>{t(`ranking:signal.${s.signal}` as never, { defaultValue: s.signal })}</td>
                            <td className="vy-dl-num">{s.value}</td>
                            <td className="vy-dl-num">{s.weight}</td>
                            <td className="vy-dl-num">{s.contribution}</td>
                          </tr>
                        ))}
                        <tr>
                          <td colSpan={3}><strong>{t("adminCommercial:diagnostics.scoreLabel")}</strong></td>
                          <td className="vy-dl-num"><strong>{diag.score.total}</strong></td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </section>

          <section className="vy-dl-sec" aria-labelledby="ac-audit">
            <div className="vy-dl-sec-head">
              <span className="vy-dl-tile" aria-hidden="true"><ScrollText size={20} strokeWidth={1.75} /></span>
              <h2 id="ac-audit" className="vy-card-title">{t("adminCommercial:audit.title")}</h2>
              <span className="vy-dl-sec-hint">{t("adminCommercial:audit.hint")}</span>
            </div>
            <div className="vy-dl-actions">
              <input className="vy-input" style={{ flex: 1, minWidth: 140 }} value={auditActor} onChange={(e) => setAuditActor(e.target.value)} placeholder={t("adminCommercial:audit.actorPlaceholder")} aria-label={t("adminCommercial:audit.actorPlaceholder")} />
              <input className="vy-input" style={{ flex: 1, minWidth: 140 }} value={auditAction} onChange={(e) => setAuditAction(e.target.value)} placeholder={t("adminCommercial:audit.actionPlaceholder")} aria-label={t("adminCommercial:audit.actionPlaceholder")} />
              <button className="vy-btn vy-btn-secondary" onClick={loadAudit}>{t("adminCommercial:audit.search")}</button>
            </div>
            {auditRows.length === 0 && <p className="vy-dl-hint">{t("adminCommercial:audit.empty")}</p>}
            {auditRows.length > 0 && (
              <div className="vy-dl-table-wrap">
                <table className="vy-dl-table">
                  <thead>
                    <tr>
                      <th>{t("adminCommercial:audit.colWhen")}</th>
                      <th>{t("adminCommercial:audit.colActor")}</th>
                      <th>{t("adminCommercial:audit.colAction")}</th>
                      <th>{t("adminCommercial:audit.colObject")}</th>
                      <th>{t("adminCommercial:audit.colOutcome")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {auditRows.map((r) => (
                      <tr key={r.id}>
                        <td style={{ whiteSpace: "nowrap" }}>{formatDateTime(r.at, i18n.language)}</td>
                        <td><span className="vy-dl-code">{r.actor_id ?? "—"}</span></td>
                        <td><span className="vy-dl-code">{r.action}</span></td>
                        <td><span className="vy-dl-code">{r.object_kind}/{r.object_id.slice(0, 8)}</span></td>
                        <td>
                          <span className="vy-dl-state" data-tone={r.outcome === "ok" ? "done" : "warn"}>{r.outcome}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>
      </div>
    </Screen>
  );
}

"use client";

// [TR049] Commercial administration and audit review (FR49) — operator view.
// Four sections on one screen: products with their versions (a price change is
// a NEW version, and there is no edit control anywhere because there is no
// such API route), orders by kind and state with a refund form bounded by the
// order's remaining value, ranking diagnostics that explain rather than
// override, and audit search.
// Deliberately absent, per SP049's separation of powers: any control to change
// a verification state, a ranking weight, or a moderation decision. Those live
// in their own queues and cannot be reached from here.
// Traces to: FR49, FR31, FR32, TR049, SP049
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "@/lib/api";
import { formatPaise } from "@/lib/money";

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
  const [notice, setNotice] = useState<string | null>(null);
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
    loadProducts();
  }, [loadProducts]);
  useEffect(() => {
    loadOrders();
  }, [loadOrders]);
  useEffect(() => {
    loadAudit();
  }, [loadAudit]);

  if (forbidden) {
    return (
      <main className="vy-shell">
        <h1>{t("adminCommercial:title")}</h1>
        <p className="vy-muted">{t("adminCommercial:notOperator")}</p>
      </main>
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
      setNotice(e instanceof ApiError ? String(e.detail) : t("common:state.actionFailed"));
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
      setNotice(res.refunded ? t("adminCommercial:refund.done") : t("commercial:promotion.resultUnavailable"));
      setRefundFor(null);
      setRefundAmount("");
      await loadOrders();
      await loadAudit();
    } catch (e) {
      setNotice(e instanceof ApiError ? String(e.detail) : t("common:state.actionFailed"));
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
      setNotice(e instanceof ApiError ? String(e.detail) : t("common:state.actionFailed"));
    }
  }

  return (
    <main className="vy-shell">
      <h1>{t("adminCommercial:title")}</h1>
      <p className="vy-muted">{t("adminCommercial:scopeNote")}</p>
      {notice && <p className="vy-error">{notice}</p>}

      <section className="vy-stack">
        <h2 style={{ fontSize: 16 }}>{t("adminCommercial:products.title")}</h2>
        <p className="vy-muted" style={{ fontSize: 13 }}>{t("adminCommercial:products.insertOnly")}</p>
        {products?.map((p) => (
          <div key={`${p.id}-${p.version}`} className="vy-card vy-stack" style={{ gap: 6 }}>
            <div className="vy-row" style={{ justifyContent: "space-between", flexWrap: "wrap" }}>
              <strong>{p.id} · v{p.version}</strong>
              <span>{money(p.price_paise)} + {money(p.tax_paise)}</span>
            </div>
            <span className="vy-muted" style={{ fontSize: 13 }}>
              {p.kind} · {t(`adminCommercial:products.billing.${p.billing}` as "products.billing.one_time")} · {t("adminCommercial:products.orders", { n: p.orders })}
            </span>
            <div className="vy-row">
              <input className="vy-input" inputMode="decimal" placeholder={t("adminCommercial:products.newPricePlaceholder")}
                     value={newPrice[p.id] ?? ""} onChange={(e) => setNewPrice((s) => ({ ...s, [p.id]: e.target.value }))} />
              <button className="vy-btn vy-btn-secondary" disabled={busy || !newPrice[p.id]} onClick={() => addVersion(p)}>
                {t("adminCommercial:products.addVersion")}
              </button>
            </div>
          </div>
        ))}
      </section>

      <section className="vy-stack">
        <h2 style={{ fontSize: 16 }}>{t("adminCommercial:orders.title")}</h2>
        <div className="vy-row" style={{ flexWrap: "wrap" }}>
          {(["promotion", "entitlement", "campaign"] as const).map((k) => (
            <button key={k} className="vy-chip" aria-pressed={orderKind === k}
                    style={{ border: "none", cursor: "pointer", background: orderKind === k ? "var(--accent)" : "var(--surface-overlay)", color: orderKind === k ? "var(--accent-ink)" : "var(--text-primary)" }}
                    onClick={() => setOrderKind(k)}>
              {t(`adminCommercial:orders.kind.${k}` as "orders.kind.promotion")}
            </button>
          ))}
        </div>
        {orders.length === 0 && <p className="vy-muted">{t("adminCommercial:orders.empty")}</p>}
        {orders.map((o) => (
          <div key={o.id} className="vy-card vy-stack" style={{ gap: 4 }}>
            <div className="vy-row" style={{ justifyContent: "space-between", flexWrap: "wrap" }}>
              <strong>{o.product}</strong>
              <span className="vy-badge vy-badge-member-provided">{t(`commercial:state.${o.state}` as "state.active")}</span>
            </div>
            <span className="vy-muted" style={{ fontSize: 13 }}>
              {o.owner_id} · {new Date(o.created_at).toLocaleDateString(i18n.language)}
              {o.charged_paise != null ? ` · ${money(o.charged_paise)}` : ""}
              {o.refunded_paise ? ` · ${t("adminCommercial:orders.refunded", { amount: money(o.refunded_paise) })}` : ""}
            </span>
            {o.payment_order_id && o.payment_state === "succeeded" && (
              <button className="vy-btn vy-btn-ghost" style={{ alignSelf: "flex-start", fontSize: 13 }} onClick={() => { setRefundFor(o); setRefundAmount(String(((o.charged_paise ?? 0) - (o.refunded_paise ?? 0)) / 100)); }}>
                {t("adminCommercial:refund.open")}
              </button>
            )}
            {refundFor?.id === o.id && (
              <div className="vy-stack" style={{ gap: 6 }}>
                <label className="vy-field">
                  <span className="vy-label">{t("adminCommercial:refund.amount")}</span>
                  <input className="vy-input" inputMode="decimal" value={refundAmount} onChange={(e) => setRefundAmount(e.target.value)} />
                </label>
                <select className="vy-select" value={refundReason} onChange={(e) => setRefundReason(e.target.value)}>
                  {REFUND_REASONS.map((r) => (
                    <option key={r} value={r}>{t(`trustSafety:reasonCode.${r}` as "reasonCode.spam")}</option>
                  ))}
                </select>
                <div className="vy-row">
                  <button className="vy-btn vy-btn-primary" disabled={busy || !refundAmount} onClick={submitRefund}>{t("adminCommercial:refund.submit")}</button>
                  <button className="vy-btn vy-btn-ghost" onClick={() => setRefundFor(null)}>{t("common:action.cancel")}</button>
                </div>
              </div>
            )}
          </div>
        ))}
      </section>

      <section className="vy-stack">
        <h2 style={{ fontSize: 16 }}>{t("adminCommercial:diagnostics.title")}</h2>
        <p className="vy-muted" style={{ fontSize: 13 }}>{t("adminCommercial:diagnostics.help")}</p>
        <div className="vy-row" style={{ flexWrap: "wrap" }}>
          {(["listing", "opportunity"] as const).map((k) => (
            <button key={k} className="vy-chip" aria-pressed={diagKind === k}
                    style={{ border: "none", cursor: "pointer", background: diagKind === k ? "var(--accent)" : "var(--surface-overlay)", color: diagKind === k ? "var(--accent-ink)" : "var(--text-primary)" }}
                    onClick={() => setDiagKind(k)}>
              {t(`trustSafety:objectKind.${k}` as "objectKind.listing")}
            </button>
          ))}
        </div>
        <div className="vy-row">
          <input className="vy-input" value={diagId} onChange={(e) => setDiagId(e.target.value)} placeholder={t("adminCommercial:diagnostics.idPlaceholder")} />
          <button className="vy-btn vy-btn-secondary" disabled={!diagId.trim()} onClick={runDiagnostics}>{t("adminCommercial:diagnostics.run")}</button>
        </div>
        {diag && (
          <div className="vy-card vy-stack" style={{ gap: 6 }}>
            <strong>{diag.title ?? diag.target_id}</strong>
            <span className={diag.eligible ? "vy-muted" : "vy-error"}>
              {diag.eligible ? t("adminCommercial:diagnostics.eligible") : t("adminCommercial:diagnostics.excluded")}
            </span>
            {diag.exclusions.map((x) => (
              <span key={x} className="vy-muted" style={{ fontSize: 13 }}>
                · {t(`adminCommercial:diagnostics.exclusion.${x}` as "diagnostics.exclusion.state_not_active", { defaultValue: x })}
              </span>
            ))}
            {diag.note === "memberRelative" && <p className="vy-muted" style={{ fontSize: 13 }}>{t("adminCommercial:diagnostics.memberRelative")}</p>}
            {diag.score && (
              <>
                <span className="vy-label">{t("adminCommercial:diagnostics.score", { total: diag.score.total })}</span>
                {diag.score.signals.map((s) => (
                  <span key={s.signal} className="vy-muted" style={{ fontSize: 13 }}>
                    {t(`ranking:signal.${s.signal}` as never, { defaultValue: s.signal })}: {s.value} × {s.weight} = {s.contribution}
                  </span>
                ))}
              </>
            )}
          </div>
        )}
      </section>

      <section className="vy-stack">
        <h2 style={{ fontSize: 16 }}>{t("adminCommercial:audit.title")}</h2>
        <div className="vy-row" style={{ flexWrap: "wrap" }}>
          <input className="vy-input" value={auditActor} onChange={(e) => setAuditActor(e.target.value)} placeholder={t("adminCommercial:audit.actorPlaceholder")} />
          <input className="vy-input" value={auditAction} onChange={(e) => setAuditAction(e.target.value)} placeholder={t("adminCommercial:audit.actionPlaceholder")} />
          <button className="vy-btn vy-btn-secondary" onClick={loadAudit}>{t("adminCommercial:audit.search")}</button>
        </div>
        {auditRows.length === 0 && <p className="vy-muted">{t("adminCommercial:audit.empty")}</p>}
        <ol className="vy-stack" style={{ gap: 4, margin: 0, paddingLeft: 18 }}>
          {auditRows.map((r) => (
            <li key={r.id} className="vy-muted" style={{ fontSize: 13 }}>
              {new Date(r.at).toLocaleString(i18n.language)} · {r.actor_id ?? "—"} · {r.action} · {r.object_kind}/{r.object_id.slice(0, 8)}
              {r.outcome !== "ok" ? ` · ${r.outcome}` : ""}
            </li>
          ))}
        </ol>
      </section>
    </main>
  );
}

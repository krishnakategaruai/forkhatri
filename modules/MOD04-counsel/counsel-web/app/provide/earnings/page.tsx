"use client";

import Link from "next/link";
import { useTranslation } from "react-i18next";
import { api } from "@/lib/api";
import { dateLong, money } from "@/lib/format";
import { Empty, Skeleton, StatusTag, useAsync, useToast } from "@/components/ui";
import { useState } from "react";
import { ApiError } from "@/lib/api";

type Earn = {
  bookings: { id: string; service_title: string; starts_at: string; status: string; gross_minor: number; platform_fee_minor: number; refund_minor: number; provider_payable_minor: number; payout_status: string; currency: string; seeker_name: string }[];
  payouts: { id: string; amount_minor: number; currency: string; status: string; created_at: string; external_ref: string | null }[];
};

export default function EarningsPage() {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const toast = useToast();
  const { data, loading, reload } = useAsync(() => api<Earn>("/provide/earnings"), []);
  const { data: method, reload: reloadMethod } = useAsync(() => api<{ kind: string; holder_name: string; ifsc: string | null; last4: string } | null>("/provide/payout-method"), []);
  const [editing, setEditing] = useState(false);
  const [pm, setPm] = useState({ kind: "upi", holder_name: "", upi_id: "", account_number: "", ifsc: "" });
  const saveMethod = async () => {
    try {
      await api("/provide/payout-method", { method: "PUT", body: pm.kind === "upi" ? { kind: "upi", holder_name: pm.holder_name, upi_id: pm.upi_id } : { kind: "bank", holder_name: pm.holder_name, account_number: pm.account_number, ifsc: pm.ifsc } });
      toast(t("common.saved")); setEditing(false); setPm({ kind: "upi", holder_name: "", upi_id: "", account_number: "", ifsc: "" }); await reloadMethod();
    } catch (e) { toast(t(`errors.${(e as ApiError).code}`, { defaultValue: (e as Error).message })); }
  };
  if (loading) return <Skeleton h={80} n={3} />;
  if (!data) return <Empty title={t("provide.start_title")} action={<Link href="/provide/profile" className="btn btn-primary">{t("provide.start_cta")}</Link>} />;
  const eligible = data.bookings.filter((b) => b.payout_status === "eligible").reduce((s, b) => s + b.provider_payable_minor - b.refund_minor, 0);
  const cur = data.bookings[0]?.currency ?? "INR";
  const payout = async () => { if (!method) { toast(t("payout_method.required")); setEditing(true); return; } try { const r = await api<{ amount_minor: number }>("/provide/payouts", { method: "POST" }); toast(t("earn.paid_toast", { amount: money(r.amount_minor, cur, lang) })); await reload(); } catch (e) { toast((e as Error).message); } };

  return (
    <div className="stack-lg">
      <div className="card card-pad between">
        <div><div className="eyebrow">{t("earn.ready")}</div><div className="serif" style={{ fontSize: "1.8rem" }}>{money(eligible, cur, lang)}</div><div className="tiny muted">{t("earn.hold_note")}</div></div>
        <button className="btn btn-primary" disabled={eligible <= 0} onClick={() => void payout()}>{t("earn.request_payout")}</button>
      </div>
      <section className="card card-pad stack">
        <div className="between"><span className="eyebrow">{t("payout_method.title")}</span>{method && !editing && <button className="link small" onClick={() => setEditing(true)}>{t("common.edit")}</button>}</div>
        {method && !editing ? (
          <div className="small">{method.kind === "upi" ? t("payout_method.upi_masked", { last4: method.last4 }) : t("payout_method.bank_masked", { last4: method.last4, ifsc: method.ifsc })} · {method.holder_name}</div>
        ) : (
          <>
            <div className="row">{["upi", "bank"].map((k) => <button key={k} className="chip" aria-pressed={pm.kind === k} onClick={() => setPm({ ...pm, kind: k })}>{t(`payout_method.${k}`)}</button>)}</div>
            <div className="grid grid-2">
              <label className="field"><span className="label">{t("payout_method.holder")}</span><input className="input" value={pm.holder_name} onChange={(e) => setPm({ ...pm, holder_name: e.target.value })} /></label>
              {pm.kind === "upi" ? (
                <label className="field"><span className="label">{t("payout_method.upi_id")}</span><input className="input" value={pm.upi_id} onChange={(e) => setPm({ ...pm, upi_id: e.target.value.trim() })} placeholder="name@bank" /></label>
              ) : (<>
                <label className="field"><span className="label">{t("payout_method.account")}</span><input className="input" inputMode="numeric" value={pm.account_number} onChange={(e) => setPm({ ...pm, account_number: e.target.value.replace(/\D/g, "") })} /></label>
                <label className="field"><span className="label">IFSC</span><input className="input" value={pm.ifsc} onChange={(e) => setPm({ ...pm, ifsc: e.target.value.toUpperCase() })} placeholder="SBIN0001234" /></label>
              </>)}
            </div>
            <p className="tiny muted">{t("payout_method.secure")}</p>
            <div className="row">{method && <button className="btn btn-ghost btn-sm" onClick={() => setEditing(false)}>{t("common.cancel")}</button>}<button className="btn btn-primary btn-sm" disabled={!pm.holder_name || (pm.kind === "upi" ? !pm.upi_id : !pm.account_number || !pm.ifsc)} onClick={() => void saveMethod()}>{t("common.save")}</button></div>
          </>
        )}
      </section>

      <section className="stack">
        <h2>{t("earn.transactions")}</h2>
        {!data.bookings.length ? <p className="muted small">{t("earn.none")}</p> : (
          <div className="card list" style={{ padding: "0 18px" }}>
            {data.bookings.map((b) => (
              <Link key={b.id} href={`/bookings/${b.id}`} className="item">
                <div className="grow"><div className="small strong">{b.service_title} · {b.seeker_name}</div><div className="tiny muted">{dateLong(b.starts_at, lang)} · <StatusTag status={b.status} /> · {t(`payout.${b.payout_status}`)}</div></div>
                <div style={{ textAlign: "right" }}>
                  <div className="num">{money(b.provider_payable_minor - b.refund_minor, b.currency, lang)}</div>
                  <div className="tiny muted num">{t("earn.breakdown", { gross: money(b.gross_minor, b.currency, lang), fee: money(b.platform_fee_minor, b.currency, lang) })}{b.refund_minor ? ` · ${t("booking.refunded")} ${money(b.refund_minor, b.currency, lang)}` : ""}</div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
      <section className="stack">
        <h2>{t("earn.payouts")}</h2>
        {!data.payouts.length ? <p className="muted small">{t("earn.no_payouts")}</p> : (
          <div className="card list" style={{ padding: "0 18px" }}>
            {data.payouts.map((p) => <div key={p.id} className="item"><div className="grow small">{dateLong(p.created_at, lang)} <span className="tiny muted mono">{p.external_ref}</span></div><div className="num">{money(p.amount_minor, p.currency, lang)}</div><span className="tag tag-ok">{t(`payout.${p.status}`)}</span></div>)}
          </div>
        )}
      </section>
    </div>
  );
}

"use client";

import Link from "next/link";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "@/lib/api";
import { dateTime, money } from "@/lib/format";
import { Empty, Skeleton, StatusTag, useAsync, useToast } from "@/components/ui";

type Dispute = { id: string; booking_id: string; reason: string; created_at: string; service_title: string; gross_minor: number; refund_minor: number; currency: string; booking_status: string; seeker_name: string; provider_name: string; opened_by_name: string; starts_at: string };

export default function AdminDisputes() {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const toast = useToast();
  const { data, loading, reload } = useAsync(() => api<Dispute[]>("/admin/disputes"), []);
  const [form, setForm] = useState<Record<string, { pct: string; resolution: string }>>({});
  const decide = async (d: Dispute) => {
    const f = form[d.id] ?? { pct: "0", resolution: "" };
    await api(`/admin/disputes/${d.id}/decide`, { body: { refund_percent: Number(f.pct) || 0, resolution: f.resolution } });
    toast(t("common.saved")); await reload();
  };
  if (loading) return <Skeleton h={120} n={2} />;
  if (!data?.length) return <Empty title={t("admin.no_disputes")} />;
  return (
    <div className="stack">
      {data.map((d) => (
        <div key={d.id} className="card card-pad stack">
          <div className="between"><div><Link href={`/bookings/${d.booking_id}`} className="serif" style={{ fontSize: "1.15rem" }}>{d.service_title}</Link><div className="tiny muted">{d.seeker_name} ↔ {d.provider_name} · {dateTime(d.starts_at, lang)} · <StatusTag status={d.booking_status} /></div></div><div className="num">{money(d.gross_minor, d.currency, lang)}{d.refund_minor ? <span className="tiny muted"> ({t("booking.refunded")} {money(d.refund_minor, d.currency, lang)})</span> : null}</div></div>
          <p className="small"><span className="muted">{t("admin.opened_by", { name: d.opened_by_name })}:</span> {d.reason}</p>
          <div className="grid grid-3">
            <label className="field"><span className="label">{t("admin.refund_pct")}</span><input className="input" inputMode="numeric" value={form[d.id]?.pct ?? ""} onChange={(e) => setForm({ ...form, [d.id]: { ...(form[d.id] ?? { resolution: "" }), pct: e.target.value.replace(/\D/g, "") } })} placeholder="0–100" /></label>
            <label className="field" style={{ gridColumn: "span 2" }}><span className="label">{t("admin.resolution")}</span><input className="input" value={form[d.id]?.resolution ?? ""} onChange={(e) => setForm({ ...form, [d.id]: { ...(form[d.id] ?? { pct: "0" }), resolution: e.target.value } })} /></label>
          </div>
          <div><button className="btn btn-primary btn-sm" disabled={!form[d.id]?.resolution} onClick={() => void decide(d)}>{t("admin.resolve")}</button></div>
        </div>
      ))}
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api, type Policy } from "@/lib/api";
import { Skeleton, useToast } from "@/components/ui";

type Settings = { platform_fee_percent: number; cancellation_policy: Policy; payout_hold_hours: number; review_window_days: number; retention_recording_days: number; retention_file_days: number };

export default function AdminSettings() {
  const { t } = useTranslation();
  const toast = useToast();
  const [s, setS] = useState<Settings | null>(null);
  useEffect(() => { void api<Settings>("/admin/settings").then(setS); }, []);
  if (!s) return <Skeleton h={80} n={2} />;
  const save = async (key: keyof Settings, value: unknown) => { await api(`/admin/settings/${key}`, { method: "PUT", body: { value } }); toast(t("common.saved")); };
  const pol = s.cancellation_policy;
  const setTier = (i: number, k: "min_hours_before" | "refund_percent", v: number) => setS({ ...s, cancellation_policy: { ...pol, seeker: pol.seeker.map((tier, j) => (j === i ? { ...tier, [k]: v } : tier)) } });
  return (
    <div className="stack-lg" style={{ maxWidth: 720 }}>
      <section className="card card-pad stack">
        <h3>{t("admin.fee_title")}</h3>
        <p className="tiny muted">{t("admin.fee_hint")}</p>
        <div className="row"><input className="input" style={{ width: 120 }} inputMode="decimal" value={s.platform_fee_percent} onChange={(e) => setS({ ...s, platform_fee_percent: Number(e.target.value) || 0 })} /><span>%</span><button className="btn btn-secondary btn-sm" onClick={() => void save("platform_fee_percent", s.platform_fee_percent)}>{t("common.save")}</button></div>
      </section>
      <section className="card card-pad stack">
        <h3>{t("book.cancellation")}</h3>
        <p className="tiny muted">{t("admin.policy_hint")}</p>
        {pol.seeker.map((tier, i) => (
          <div key={i} className="row small"><span>{t("admin.tier_at_least")}</span><input className="input" style={{ width: 80 }} inputMode="numeric" value={tier.min_hours_before} onChange={(e) => setTier(i, "min_hours_before", Number(e.target.value) || 0)} /><span>{t("admin.hours_before")}</span><input className="input" style={{ width: 80 }} inputMode="numeric" value={tier.refund_percent} onChange={(e) => setTier(i, "refund_percent", Number(e.target.value) || 0)} /><span>% {t("admin.refund")}</span></div>
        ))}
        <div className="row small"><span>{t("policy.provider_cancels_label")}</span><input className="input" style={{ width: 80 }} inputMode="numeric" value={pol.provider_cancel_refund_percent} onChange={(e) => setS({ ...s, cancellation_policy: { ...pol, provider_cancel_refund_percent: Number(e.target.value) || 0 } })} /><span>%</span></div>
        <div className="row small"><span>{t("policy.seeker_no_show_label")}</span><input className="input" style={{ width: 80 }} inputMode="numeric" value={pol.seeker_no_show_refund_percent} onChange={(e) => setS({ ...s, cancellation_policy: { ...pol, seeker_no_show_refund_percent: Number(e.target.value) || 0 } })} /><span>%</span></div>
        <div className="row small"><span>{t("policy.provider_no_show_label")}</span><input className="input" style={{ width: 80 }} inputMode="numeric" value={pol.provider_no_show_refund_percent} onChange={(e) => setS({ ...s, cancellation_policy: { ...pol, provider_no_show_refund_percent: Number(e.target.value) || 0 } })} /><span>%</span></div>
        <div><button className="btn btn-secondary btn-sm" onClick={() => void save("cancellation_policy", pol)}>{t("common.save")}</button></div>
      </section>
      <section className="card card-pad stack">
        <h3>{t("admin.retention")}</h3>
        <p className="tiny muted">{t("admin.retention_hint")}</p>
        <div className="row small"><span>{t("admin.retention_recordings")}</span><input className="input" style={{ width: 90 }} inputMode="numeric" value={s.retention_recording_days} onChange={(e) => setS({ ...s, retention_recording_days: Number(e.target.value) || 1 })} /><span>{t("admin.days")}</span><button className="btn btn-secondary btn-sm" onClick={() => void save("retention_recording_days", s.retention_recording_days)}>{t("common.save")}</button></div>
        <div className="row small"><span>{t("admin.retention_files")}</span><input className="input" style={{ width: 90 }} inputMode="numeric" value={s.retention_file_days} onChange={(e) => setS({ ...s, retention_file_days: Number(e.target.value) || 1 })} /><span>{t("admin.days")}</span><button className="btn btn-secondary btn-sm" onClick={() => void save("retention_file_days", s.retention_file_days)}>{t("common.save")}</button></div>
      </section>
      <section className="card card-pad stack">
        <h3>{t("admin.payout_hold")}</h3>
        <div className="row"><input className="input" style={{ width: 120 }} inputMode="numeric" value={s.payout_hold_hours} onChange={(e) => setS({ ...s, payout_hold_hours: Number(e.target.value) || 0 })} /><span>{t("admin.hours")}</span><button className="btn btn-secondary btn-sm" onClick={() => void save("payout_hold_hours", s.payout_hold_hours)}>{t("common.save")}</button></div>
      </section>
    </div>
  );
}

"use client";

import Link from "next/link";
import { useTranslation } from "react-i18next";
import { api } from "@/lib/api";
import { money } from "@/lib/format";
import { Skeleton, useAsync } from "@/components/ui";

type Overview = { pending_providers: number; approved_providers: number; pending_expertise: number; open_reports: number; open_disputes: number; completed: number; gtv_minor: number; fee_minor: number; refunds_minor: number; cancelled: number; no_shows: number };

export default function AdminHome() {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const { data, loading } = useAsync(() => api<Overview>("/admin/overview"), []);
  if (loading || !data) return <Skeleton h={80} n={3} />;
  const queue = [
    { n: data.pending_providers, k: t("admin.q_providers"), href: "/admin/providers" },
    { n: data.pending_expertise, k: t("admin.q_expertise"), href: "/admin/expertise" },
    { n: data.open_reports, k: t("admin.q_reports"), href: "/admin/reports" },
    { n: data.open_disputes, k: t("admin.q_disputes"), href: "/admin/disputes" },
  ];
  return (
    <div className="stack-lg">
      <section className="stack"><h2>{t("admin.needs_you")}</h2>
        <div className="grid grid-4">{queue.map((q) => <Link key={q.href} href={q.href} className="stat"><div className="v" style={{ color: q.n ? "var(--accent-ink)" : undefined }}>{q.n}</div><div className="k">{q.k}</div></Link>)}</div>
      </section>
      <section className="stack"><h2>{t("admin.marketplace")}</h2>
        <div className="grid grid-4">
          <div className="stat"><div className="v">{data.approved_providers}</div><div className="k">{t("admin.m_providers")}</div></div>
          <div className="stat"><div className="v">{data.completed}</div><div className="k">{t("admin.m_completed")}</div></div>
          <div className="stat"><div className="v">{data.cancelled}</div><div className="k">{t("admin.m_cancelled")}</div></div>
          <div className="stat"><div className="v">{data.no_shows}</div><div className="k">{t("admin.m_no_shows")}</div></div>
        </div>
      </section>
      <section className="stack"><h2>{t("admin.economics")}</h2>
        <div className="grid grid-3">
          <div className="stat"><div className="v">{money(data.gtv_minor, "INR", lang)}</div><div className="k">{t("admin.e_gtv")}</div></div>
          <div className="stat"><div className="v">{money(data.fee_minor, "INR", lang)}</div><div className="k">{t("admin.e_fee")}</div></div>
          <div className="stat"><div className="v">{money(data.refunds_minor, "INR", lang)}</div><div className="k">{t("admin.e_refunds")}</div></div>
        </div>
      </section>
    </div>
  );
}

"use client";

import { useTranslation } from "react-i18next";
import { api } from "@/lib/api";
import { dateTime } from "@/lib/format";
import { Empty, Skeleton, useAsync } from "@/components/ui";

type Report = { id: string; reporter_name: string; target_kind: string; target_id: string; reason: string; detail: string | null; created_at: string };

export default function AdminReports() {
  const { t, i18n } = useTranslation();
  const { data, loading, reload } = useAsync(() => api<Report[]>("/admin/reports"), []);
  const decide = async (id: string, status: string) => { await api(`/admin/reports/${id}/decide`, { body: { status } }); await reload(); };
  if (loading) return <Skeleton h={80} n={2} />;
  if (!data?.length) return <Empty title={t("admin.no_reports")} />;
  return (
    <div className="card list" style={{ padding: "0 18px" }}>
      {data.map((r) => (
        <div key={r.id} className="item" style={{ alignItems: "flex-start" }}>
          <div className="grow"><div className="small strong">{t(`report.reason.${r.reason}`, { defaultValue: r.reason })} · <span className="muted">{r.target_kind}</span></div><div className="tiny mono muted">{r.target_id}</div>{r.detail && <p className="small">{r.detail}</p>}<div className="tiny muted">{r.reporter_name} · {dateTime(r.created_at, i18n.language)}</div></div>
          <button className="btn btn-secondary btn-sm" onClick={() => void decide(r.id, "actioned")}>{t("admin.actioned")}</button>
          <button className="btn btn-ghost btn-sm" onClick={() => void decide(r.id, "dismissed")}>{t("admin.dismiss")}</button>
        </div>
      ))}
    </div>
  );
}

"use client";

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { api, type Expertise } from "@/lib/api";
import { Empty, Skeleton, useAsync, useToast } from "@/components/ui";

type Req = { id: string; name: string; parent_id: string | null; note: string | null; proposed_by_name: string; created_at: string };
// The area's name in each language besides English (English is the proposed name).
const NAME_LANGS = ["hi", "te", "mr", "kn"] as const;
type Edit = { id: string; name_hi: string; name_te: string; name_mr: string; name_kn: string; regulated: boolean };
const BLANK: Edit = { id: "", name_hi: "", name_te: "", name_mr: "", name_kn: "", regulated: false };

export default function AdminExpertise() {
  const { t } = useTranslation();
  const toast = useToast();
  const { data, loading, reload } = useAsync(() => api<Req[]>("/admin/expertise-requests"), []);
  const { data: areas, reload: reloadAreas } = useAsync(() => api<Expertise[]>("/expertise"), []);
  const [edit, setEdit] = useState<Record<string, Edit>>({});
  const change = (rid: string, patch: Partial<Edit>) => setEdit({ ...edit, [rid]: { ...(edit[rid] ?? BLANK), ...patch } });

  const decide = async (r: Req, approve: boolean) => {
    const e = edit[r.id] ?? BLANK;
    await api(`/admin/expertise-requests/${r.id}/decide`, { body: {
      approve, id: e.id || null, name_en: r.name, name_hi: e.name_hi || null, name_te: e.name_te || null,
      name_mr: e.name_mr || null, name_kn: e.name_kn || null, regulated: e.regulated,
    } });
    toast(t("common.saved")); await reload(); await reloadAreas();
  };

  return (
    <div className="stack-lg">
      <section className="stack"><h2>{t("admin.expertise_requests")}</h2>
        {loading ? <Skeleton h={90} n={2} /> : !data?.length ? <Empty title={t("admin.no_requests")} /> : data.map((r) => (
          <div key={r.id} className="card card-pad stack">
            <div><div className="serif" style={{ fontSize: "1.15rem" }}>{r.name}</div><div className="tiny muted">{t("admin.proposed_by", { name: r.proposed_by_name })}{r.parent_id ? ` · ${t("admin.under", { area: areas?.find((a) => a.id === r.parent_id)?.name ?? r.parent_id })}` : ""}</div>{r.note && <p className="small" style={{ marginTop: 4 }}>{r.note}</p>}</div>
            <div className="grid grid-4">
              <label className="field"><span className="label">{t("admin.slug")}</span><input className="input" value={edit[r.id]?.id ?? ""} onChange={(e) => change(r.id, { id: e.target.value })} placeholder={r.name.toLowerCase().replace(/[^a-z0-9]+/g, "-")} /></label>
              {NAME_LANGS.map((l) => (
                <label key={l} className="field"><span className="label">{t(`lang.${l}`)}</span><input className="input" lang={l} value={edit[r.id]?.[`name_${l}`] ?? ""} onChange={(e) => change(r.id, { [`name_${l}`]: e.target.value })} /></label>
              ))}
              <label className="check" style={{ alignSelf: "end", paddingBottom: 12 }}><input type="checkbox" checked={edit[r.id]?.regulated ?? false} onChange={(e) => change(r.id, { regulated: e.target.checked })} /><span className="small">{t("admin.regulated")}</span></label>
            </div>
            <div className="row"><button className="btn btn-primary btn-sm" onClick={() => void decide(r, true)}>{t("admin.approve")}</button><button className="btn btn-ghost btn-sm" onClick={() => void decide(r, false)}>{t("admin.reject")}</button></div>
          </div>
        ))}
      </section>
      <section className="stack"><h2>{t("admin.taxonomy")}</h2>
        <div className="row">{areas?.map((a) => <span key={a.id} className="tag">{a.name} <span className="muted">· {a.providers}</span>{a.regulated ? " ·R" : ""}</span>)}</div>
      </section>
    </div>
  );
}

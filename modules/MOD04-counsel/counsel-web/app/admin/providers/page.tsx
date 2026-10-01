"use client";

import Link from "next/link";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { ArrowRight } from "lucide-react";
import { api, type ExpertiseTag } from "@/lib/api";
import { dateLong } from "@/lib/format";
import { Avatar, Empty, Skeleton, VerifiedTags, useAsync } from "@/components/ui";

type Row = { member_id: string; display_name: string; headline: string; status: string; standing?: string; submitted_at: string | null; country: string; expertise: ExpertiseTag[]; verified: string[] };
const STATUSES = ["pending_review", "approved", "changes_requested", "suspended", "draft"];

export default function AdminProviders() {
  const { t, i18n } = useTranslation();
  const [status, setStatus] = useState("pending_review");
  const { data, loading } = useAsync(() => api<Row[]>(`/admin/providers?status=${status}`), [status]);
  return (
    <div className="stack">
      <div className="row">{STATUSES.map((s) => <button key={s} className="chip" aria-pressed={status === s} onClick={() => setStatus(s)}>{t(`provider.status.${s}`)}</button>)}</div>
      {loading ? <Skeleton h={80} n={3} /> : !data?.length ? <Empty title={t("admin.none_in_status")} /> : (
        <div className="card list" style={{ padding: "0 18px" }}>
          {data.map((r) => (
            <Link key={r.member_id} href={`/admin/providers/${r.member_id}`} className="item">
              <Avatar name={r.display_name} size={44} />
              <div className="grow"><div className="small strong">{r.display_name} <span className="tiny muted">· {r.country}{r.standing ? ` · ${t(`standing.${r.standing}`)}` : ""}</span></div><div className="tiny muted clamp-2">{r.headline}</div>
                <div className="row tiny" style={{ marginTop: 4 }}>{r.expertise.map((e) => <span key={e.id} className="tag">{e.name}</span>)}<VerifiedTags dims={r.verified} /></div></div>
              <div className="tiny muted">{r.submitted_at ? dateLong(r.submitted_at, i18n.language) : ""}</div>
              <ArrowRight size={16} className="muted" />
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

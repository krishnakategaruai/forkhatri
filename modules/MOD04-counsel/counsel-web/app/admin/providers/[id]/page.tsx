"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { ShieldCheck } from "lucide-react";
import { API_BASE, api, type Evidence, type ExpertiseTag, type Reputation } from "@/lib/api";
import { dateTime, money } from "@/lib/format";
import { Avatar, Skeleton, useAsync, useToast } from "@/components/ui";

type Detail = {
  member_id: string; display_name: string; headline: string; intro: string; city: string | null; country: string; status: string; review_note: string | null; links: Record<string, string>;
  expertise: ExpertiseTag[]; verified: string[]; evidence: Evidence[]; services: { id: string; title: string; price_minor: number; duration_min: number; status: string }[];
  reputation: Reputation; required_dimensions: string[]; standing?: string;
  badge_history: { badge_id: string; level: number; awarded_at: string; evidence: Record<string, number> }[]; audit: { action: string; detail: Record<string, unknown>; at: string }[];
};
const DIMS = ["identity", "contact", "experience", "qualification", "certification", "registration", "business", "portfolio"];

export default function AdminProviderDetail() {
  const { id } = useParams<{ id: string }>();
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const toast = useToast();
  const { data: p, loading, reload } = useAsync(() => api<Detail>(`/admin/providers/${id}`), [id]);
  const [note, setNote] = useState("");
  if (loading || !p) return <Skeleton h={100} n={3} />;

  const decide = async (decision: string) => { await api(`/admin/providers/${id}/decide`, { body: { decision, note } }); toast(t("common.saved")); await reload(); };
  const verify = async (dimension: string, verified: boolean) => { await api(`/admin/providers/${id}/verify`, { body: { dimension, verified, note: "" } }); await reload(); };
  const evidence = async (eid: string, status: string) => { await api(`/admin/evidence/${eid}/decide`, { body: { status, note: "" } }); await reload(); };

  return (
    <div className="two-col">
      <div className="stack-lg">
        <header className="row" style={{ gap: 16 }}>
          <Avatar name={p.display_name} size={72} />
          <div><h2>{p.display_name}</h2><p className="muted">{p.headline}</p><div className="row tiny muted"><span>{p.city} · {p.country}</span><span className="tag">{t(`provider.status.${p.status}`)}</span><Link href={`/p/${id}`} className="link">{t("admin.public_view")}</Link></div></div>
        </header>
        <p className="small" style={{ whiteSpace: "pre-wrap", color: "var(--ink-2)" }}>{p.intro}</p>
        <div className="row">{p.expertise.map((e) => <span key={e.id} className="tag">{e.name} · {e.years}y{e.regulated ? " · " + t("admin.regulated") : ""}</span>)}</div>

        <section className="card card-pad stack">
          <h3>{t("admin.evidence")}</h3>
          {p.required_dimensions.length > 0 && <p className="tiny" style={{ color: "var(--warn)" }}>{t("profile.required", { dims: p.required_dimensions.map((d) => t(`verify.${d}`)).join(", ") })}</p>}
          <div className="list">
            {p.evidence.map((e) => (
              <div key={e.id} className="item" style={{ padding: "10px 0" }}>
                <div className="grow"><div className="tiny muted">{t(`evidence.${e.kind}`)}</div><div className="small">{e.title}</div><div className="tiny muted">{[e.issuer, e.year_from, e.reference_no ? `${t("evidence.reference")}: ${e.reference_no}` : null].filter(Boolean).join(" · ")}</div></div>
                {e.has_document ? <a className="link small" href={`${API_BASE}/admin/evidence/${e.id}/document`} target="_blank" rel="noopener noreferrer">{t("admin.view_proof")}</a> : <span className="tiny muted">{t("admin.no_proof")}</span>}
                <span className={`tag ${e.status === "verified" ? "tag-verified" : e.status === "rejected" ? "tag-danger" : ""}`}>{t(`evidence.status.${e.status}`)}</span>
                <button className="btn btn-secondary btn-sm" onClick={() => void evidence(e.id, "verified")} disabled={e.status === "verified"}>{t("admin.mark_verified")}</button>
                <button className="btn btn-ghost btn-sm" onClick={() => void evidence(e.id, "rejected")}>{t("admin.reject")}</button>
              </div>
            ))}
            {!p.evidence.length && <p className="tiny muted">{t("admin.no_evidence")}</p>}
          </div>
        </section>

        <section className="card card-pad stack">
          <h3>{t("admin.verification")}</h3>
          <p className="tiny muted">{t("admin.verification_hint")}</p>
          <div className="row">
            {DIMS.map((d) => { const on = p.verified.includes(d); return <button key={d} className="chip" aria-pressed={on} onClick={() => void verify(d, !on)}>{on && <ShieldCheck size={13} />}{t(`verify.${d}`)}</button>; })}
          </div>
        </section>

        <section className="card card-pad stack">
          <h3>{t("admin.services")}</h3>
          <div className="list">{p.services.map((s) => <div key={s.id} className="item" style={{ padding: "8px 0" }}><div className="grow small">{s.title} <span className="tiny muted">· {t("service.minutes", { n: s.duration_min })}</span></div><span className="num small">{money(s.price_minor, "INR", lang)}</span><span className="tag">{t(`services.status.${s.status}`)}</span></div>)}</div>
        </section>

        <section className="card card-pad stack">
          <div className="between"><h3>{t("badge_section.history")}</h3>{p.standing && <span className="tag tag-verified">{t(`standing.${p.standing}`)}</span>}</div>
          {p.badge_history.length ? (
            <div className="list">
              {p.badge_history.map((b, i) => (
                <div key={i} className="item" style={{ padding: "8px 0" }}>
                  <div className="grow small">{t(`badge.${b.badge_id}`, { n: "" })} · {t("badge_section.level", { n: b.level })}</div>
                  <span className="tiny muted">{dateTime(b.awarded_at, lang)}</span>
                  <span className="tiny muted num">{t("badge_section.at_the_time", { completed: b.evidence.completed ?? 0, clients: b.evidence.clients ?? 0 })}</span>
                </div>
              ))}
            </div>
          ) : <p className="tiny muted">{t("badge_section.none")}</p>}
          <p className="tiny muted">{t("badge_section.admin_note")}</p>
        </section>

        <section className="stack"><h3>{t("admin.audit")}</h3>
          {p.audit.length ? (
            <div className="timeline">{p.audit.map((a, i) => {
              const d = a.detail as { note?: string; dimension?: string; kind?: string };
              return (
                <div key={i} className="t on"><div className="small">
                  {t(`audit.${a.action}`, { defaultValue: a.action, dimension: d.dimension ? t(`verify.${d.dimension}`) : "", kind: d.kind ? t(`evidence.${d.kind}`) : "" })} <span className="tiny muted">{dateTime(a.at, lang)}</span>
                  {d.note && <div className="tiny muted">“{d.note}”</div>}
                </div></div>
              );
            })}</div>
          ) : <p className="tiny muted">{t("admin.no_history")}</p>}
        </section>
      </div>

      <aside className="card card-pad stack">
        <span className="eyebrow">{t("admin.decision")}</span>
        <div className="grid grid-2" style={{ gap: 8 }}>
          <div><div className="serif" style={{ fontSize: "1.3rem" }}>{p.reputation.completed}</div><div className="tiny muted">{t("rep.completed")}</div></div>
          <div><div className="serif" style={{ fontSize: "1.3rem" }}>{p.reputation.rating?.toFixed(1) ?? "—"}</div><div className="tiny muted">{t("rep.rating", { n: p.reputation.review_count })}</div></div>
        </div>
        <textarea className="textarea" value={note} onChange={(e) => setNote(e.target.value)} placeholder={t("admin.note_placeholder")} style={{ minHeight: 80 }} />
        {p.status !== "approved" && <button className="btn btn-primary btn-block" onClick={() => void decide("approve")}>{t("admin.approve")}</button>}
        {p.status === "suspended" ? <button className="btn btn-secondary btn-block" onClick={() => void decide("reinstate")}>{t("admin.reinstate")}</button> : (
          <>
            <button className="btn btn-secondary btn-block" onClick={() => void decide("changes_requested")}>{t("admin.request_changes")}</button>
            <button className="btn btn-danger btn-block" onClick={() => void decide("suspend")}>{t("admin.suspend")}</button>
          </>
        )}
        {p.review_note && <p className="tiny muted">{t("admin.last_note")}: {p.review_note}</p>}
      </aside>
    </div>
  );
}

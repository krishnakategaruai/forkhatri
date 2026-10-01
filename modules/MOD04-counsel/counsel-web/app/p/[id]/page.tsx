"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Bookmark, Clock, ExternalLink, Flag, Languages, MapPin, MessageCircle, ShieldCheck, Video } from "lucide-react";
import { api, type Profile } from "@/lib/api";
import { money, dateLong, timeZoneLabel } from "@/lib/format";
import { Avatar, Dialog, Skeleton, Stars, VerifiedTags, useAsync, useToast } from "@/components/ui";
import { BadgeChip } from "@/components/Badges";
import { replyLabel } from "@/components/ProviderCard";
import { useIdentity } from "@/lib/identity";

// A repeat-client share is shown only once enough different people have booked.
const REPEAT_MIN_CLIENTS = 3;
const DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];

export default function ProviderPage() {
  const { id } = useParams<{ id: string }>();
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const { me } = useIdentity();
  const toast = useToast();
  const { data: p, loading, setData } = useAsync(() => api<Profile>(`/providers/${id}`), [id]);
  const [report, setReport] = useState(false);
  const [reason, setReason] = useState("");

  if (loading || !p) return <div className="wrap page"><Skeleton h={120} n={4} /></div>;
  const primary = p.expertise.find((e) => e.primary) ?? p.expertise[0];
  const groups = ["experience", "qualification", "certification", "registration", "business", "portfolio"].map((k) => ({ k, items: p.evidence.filter((e) => e.kind === k) })).filter((g) => g.items.length);

  const toggleSave = async () => {
    if (!me) { toast(t("auth.signin_to_save")); return; }
    const next = !p.saved;
    setData({ ...p, saved: next });
    try { await api(`/me/saved/${p.id}`, { method: next ? "PUT" : "DELETE" }); } catch { setData({ ...p, saved: !next }); }
  };
  const sendReport = async () => {
    await api("/reports", { body: { target_kind: "provider", target_id: p.id, reason: reason || "other", detail: "" } });
    setReport(false); toast(t("report.sent"));
  };

  return (
    <div className="wrap page two-col">
      <div className="stack-lg">
        {p.status !== "approved" && <div className="tag tag-warn">{t(`provider.status.${p.status}`)}</div>}
        <header className="row" style={{ gap: 20, alignItems: "flex-start" }}>
          <Avatar name={p.name} url={p.photo_url} size={112} />
          <div className="stack" style={{ gap: 6, flex: 1, minWidth: 220 }}>
            {primary && <span className="eyebrow">{primary.name}</span>}
            <h1 style={{ fontSize: "clamp(1.7rem,3.4vw,2.4rem)" }}>{p.name}</h1>
            <p className="lede" style={{ fontSize: "1.05rem" }}>{p.headline}</p>
            <div className="row small muted">
              <Stars value={p.rating} count={p.review_count} />
              {p.city && <span className="row" style={{ gap: 4 }}><MapPin size={14} />{p.city}</span>}
              <span className="row" style={{ gap: 4 }}><Languages size={14} />{p.languages.map((l) => t(`lang.${l}`)).join(", ")}</span>
            </div>
            <div className="row">
              <button className="btn btn-secondary btn-sm" onClick={toggleSave} aria-pressed={p.saved}><Bookmark size={15} fill={p.saved ? "currentColor" : "none"} />{p.saved ? t("card.saved") : t("card.save")}</button>
              {me && <button className="btn btn-ghost btn-sm" onClick={() => setReport(true)}><Flag size={14} />{t("report.report")}</button>}
            </div>
          </div>
        </header>

        <section className="stack">
          <h2>{t("provider.about")}</h2>
          <p style={{ whiteSpace: "pre-wrap", maxWidth: "68ch", color: "var(--ink-2)" }}>{p.intro}</p>
          <div className="row">
            {p.expertise.map((e) => <span key={e.id} className="tag">{e.name}{e.years ? ` · ${t("card.years", { n: e.years })}` : ""}</span>)}
          </div>
        </section>

        <section className="stack">
          <h2>{t("provider.why_trust")}</h2>
          <div className="card card-pad stack">
            <div className="stack" style={{ gap: 6 }}>
              <span className="eyebrow">{t("provider.verified_by")}</span>
              {p.verified.length ? <VerifiedTags dims={p.verified} max={8} /> : <span className="small muted">{t("provider.not_verified")}</span>}
              <p className="tiny muted">{t("provider.verified_note")}</p>
            </div>
            {groups.map((g) => (
              <div key={g.k} className="stack" style={{ gap: 6 }}>
                <span className="eyebrow">{t(`evidence.${g.k}`)}</span>
                <div className="list">
                  {g.items.map((e) => (
                    <div key={e.id} className="item" style={{ padding: "8px 0" }}>
                      <div className="grow">
                        <div>{e.title}</div>
                        <div className="tiny muted">{[e.issuer, e.year_from ? `${e.year_from}${e.year_to ? `–${e.year_to}` : ` – ${t("evidence.present")}`}` : null].filter(Boolean).join(" · ")}</div>
                      </div>
                      {e.status === "verified" && <span className="tag tag-verified"><ShieldCheck size={12} />{t("evidence.checked")}</span>}
                    </div>
                  ))}
                </div>
              </div>
            ))}
            {Object.keys(p.links ?? {}).length > 0 && (
              <div className="stack" style={{ gap: 6 }}>
                <span className="eyebrow">{t("provider.elsewhere")}</span>
                <div className="row">
                  {Object.entries(p.links).filter(([, v]) => v).map(([k, v]) => (
                    <a key={k} className="chip" href={v} target="_blank" rel="noopener noreferrer"><ExternalLink size={13} />{t(`links.${k}`, { defaultValue: k })}</a>
                  ))}
                </div>
                <p className="tiny muted">{t("provider.links_note")}</p>
              </div>
            )}
          </div>
        </section>

        <section className="stack" id="services">
          <h2>{t("provider.services")}</h2>
          <div className="grid">
            {p.services.map((s) => (
              <div key={s.id} className="card card-pad stack" style={{ gap: 10 }}>
                <div className="between" style={{ alignItems: "flex-start" }}>
                  <div>
                    <h3>{s.title}</h3>
                    <div className="tiny muted row" style={{ marginTop: 4 }}>
                      <span className="row" style={{ gap: 4 }}><Clock size={12} />{t("service.minutes", { n: s.duration_min })}</span>
                      <span className="row" style={{ gap: 4 }}><Video size={12} />{s.formats.map((f) => t(`format.${f}`)).join(" · ")}</span>
                    </div>
                  </div>
                  <div className="serif" style={{ fontSize: "1.35rem" }}>{money(s.price_minor, s.currency, lang)}</div>
                </div>
                <p className="small" style={{ color: "var(--ink-2)" }}>{s.description}</p>
                {s.outcomes.length > 0 && (
                  <ul className="small" style={{ margin: 0, paddingLeft: 18, color: "var(--ink-2)" }}>
                    {s.outcomes.map((o) => <li key={o}>{o}</li>)}
                  </ul>
                )}
                <div><Link href={`/book/${s.id}`} className="btn btn-primary">{t("service.book")}</Link></div>
              </div>
            ))}
            {!p.services.length && <p className="muted small">{t("provider.no_services")}</p>}
          </div>
        </section>

        <section className="stack">
          <h2>{t("provider.reviews")}</h2>
          {p.reviews.length ? (
            <div className="list">
              {p.reviews.map((r) => (
                <div key={r.id} className="item" style={{ alignItems: "flex-start" }}>
                  <div className="grow stack" style={{ gap: 4 }}>
                    <div className="row"><Stars value={r.overall} /><span className="tiny muted">{r.reviewer ?? t("review.member")} · {dateLong(r.created_at, lang)}</span></div>
                    {r.body && <p className="small">{r.body}</p>}
                  </div>
                </div>
              ))}
            </div>
          ) : <p className="muted small">{t("provider.no_reviews")}</p>}
        </section>
      </div>

      <aside className="stack">
        <div className="card card-pad stack">
          <span className="eyebrow">{t("provider.at_a_glance")}</span>
          <div className="grid grid-2" style={{ gap: 10 }}>
            <div><div className="serif" style={{ fontSize: "1.4rem" }}>{p.reputation.completed}</div><div className="tiny muted">{t("rep.completed")}</div></div>
            <div><div className="serif" style={{ fontSize: "1.4rem" }}>{p.reputation.repeat_clients}</div><div className="tiny muted">{p.reputation.clients >= REPEAT_MIN_CLIENTS ? t("rep.repeat_share", { n: Math.round((100 * p.reputation.repeat_clients) / p.reputation.clients) }) : t("rep.repeat")}</div></div>
            <div><div className="serif" style={{ fontSize: "1.4rem" }}>{p.reputation.reliability_percent === null ? "—" : `${p.reputation.reliability_percent}%`}</div><div className="tiny muted">{t("rep.reliability")}</div></div>
            <div><div className="serif" style={{ fontSize: "1.4rem" }}>{p.verified.length}</div><div className="tiny muted">{t("rep.verified_dims")}</div></div>
          </div>
          {replyLabel(t, p.reply_hours) && <p className="small row" style={{ gap: 6 }}><MessageCircle size={14} className="muted" />{replyLabel(t, p.reply_hours)}</p>}
          {p.reputation.review_count > 0 && (
            <div className="stack" style={{ gap: 4 }}>
              {(["expertise", "communication", "professionalism", "punctuality"] as const).map((k) => (
                <div key={k} className="between small"><span className="muted">{t(`review.${k}`)}</span><span className="num">{p.reputation.dimensions[k]?.toFixed(1) ?? "—"}</span></div>
              ))}
            </div>
          )}
        </div>
        {p.badges && p.badges.length > 0 && (
          <div className="card card-pad stack" style={{ gap: 10 }}>
            <span className="eyebrow">{t("badge_section.public")}</span>
            <div className="stack" style={{ gap: 8 }}>
              {p.badges.map((b) => (
                <div key={b.id} className="between small">
                  <BadgeChip b={b} />
                  <span className="tiny muted">{t("badge_section.since", { when: dateLong(b.since, lang) })}</span>
                </div>
              ))}
            </div>
            <p className="tiny muted">{t("badge_section.public_note")}</p>
          </div>
        )}
        <div className="card card-pad stack">
          <span className="eyebrow">{t("provider.usually_available")}</span>
          {p.weekly.length ? (
            <div className="stack" style={{ gap: 3 }}>
              {p.weekly.map((w, i) => (
                <div key={i} className="between small"><span>{t(`day.${DAYS[w.weekday]}`)}</span><span className="num muted">{w.kind === "slot" ? w.start_time.slice(0, 5) : `${w.start_time.slice(0, 5)} – ${w.end_time.slice(0, 5)}`}</span></div>
              ))}
              <p className="tiny muted" style={{ marginTop: 6 }}>{t("provider.tz", { tz: timeZoneLabel(lang, p.timezone) })}</p>
            </div>
          ) : <p className="small muted">{t("provider.no_availability")}</p>}
          {p.services[0] && <Link href={`/book/${p.services[0].id}`} className="btn btn-primary btn-block">{t("provider.book_cta")}</Link>}
        </div>
      </aside>

      <Dialog open={report} onClose={() => setReport(false)} title={t("report.title")}>
        <select className="select" value={reason} onChange={(e) => setReason(e.target.value)}>
          <option value="">{t("report.choose")}</option>
          {["misleading", "unqualified", "abuse", "spam", "other"].map((r) => <option key={r} value={r}>{t(`report.reason.${r}`)}</option>)}
        </select>
        <div className="row" style={{ justifyContent: "flex-end" }}>
          <button className="btn btn-ghost" onClick={() => setReport(false)}>{t("common.cancel")}</button>
          <button className="btn btn-primary" disabled={!reason} onClick={() => void sendReport()}>{t("report.send")}</button>
        </div>
      </Dialog>
    </div>
  );
}

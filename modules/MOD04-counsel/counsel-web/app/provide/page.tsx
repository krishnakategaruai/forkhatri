"use client";

import Link from "next/link";
import { useTranslation } from "react-i18next";
import { Check, Circle } from "lucide-react";
import { api, type Booking, type Expertise, type Reputation } from "@/lib/api";
import { BookingCard } from "@/components/BookingCard";
import { replyLabel } from "@/components/ProviderCard";
import { timeShort, money } from "@/lib/format";
import { Empty, Skeleton, VerifiedTags, useAsync, useNow, useToast } from "@/components/ui";
import { TimeRequests } from "@/components/TimeRequests";
import { MyPurchases } from "@/components/Offers";
import { BadgeChip, NextMilestones, type EarnedBadge, type NextMilestone } from "@/components/Badges";

type Dash = {
  available_until: string | null;
  open_questions: { id: string; title: string; body: string; due_at: string; buyer_name: string }[];
  badges: { earned: EarnedBadge[]; next: NextMilestone[]; standing: string };
  status: string; review_note: string | null; reputation: Reputation; currency: string;
  upcoming: { id: string; service_title: string; starts_at: string; status: string; brief: string; seeker_name: string }[];
  earnings: { earned: number; pending_payout: number; paid_out: number; last_30: number };
  verified: string[]; active_services: number; has_availability: boolean;
  found: Found;
};
type Found = {
  visibility: { impressions: number; impressions_prev: number; views: number; views_prev: number; bookings: number; bookings_prev: number; conversion_percent: number | null };
  strength: { percent: number; items: { id: string; done: boolean; href: string }[]; reviews: number; prior_reviews: number };
  rank: { area_id: string; position: number | null; of: number } | null;
  reply_hours: number | null;
};

function FoundSection({ f, approved }: { f: Found; approved: boolean }) {
  const { t } = useTranslation();
  const { data: areas } = useAsync(() => api<Expertise[]>("/expertise"), []);
  const v = f.visibility;
  const missing = f.strength.items.filter((i) => !i.done);
  const areaName = areas?.find((a) => a.id === f.rank?.area_id)?.name ?? "";
  const reply = replyLabel(t, f.reply_hours);
  const stats = [
    { v: v.impressions, prev: v.impressions_prev, k: t("found.impressions") },
    { v: v.views, prev: v.views_prev, k: t("found.views") },
    { v: v.bookings, prev: v.bookings_prev, k: t("found.bookings") },
  ];
  return (
    <section className="stack">
      <div className="section-title"><h2>{t("found.title")}</h2>{approved && <span className="tiny muted">{t("found.window")}</span>}</div>
      {approved && (
        <div className="grid grid-4">
          {stats.map((s) => (
            <div key={s.k} className="stat"><div className="v">{s.v}</div><div className="k">{s.k}</div><div className="tiny muted">{t("found.prev", { n: s.prev })}</div></div>
          ))}
          <div className="stat"><div className="v">{v.conversion_percent === null ? "—" : `${v.conversion_percent}%`}</div><div className="k">{t("found.conversion")}</div><div className="tiny muted">{t("found.conversion_hint")}</div></div>
        </div>
      )}
      <div className="grid grid-2">
        <div className="card card-pad stack" style={{ gap: 10, alignContent: "start" }}>
          <div className="between"><span className="eyebrow">{t("found.strength")}</span><span className="strong">{f.strength.percent}%</span></div>
          <div className="meter light" role="progressbar" aria-valuenow={f.strength.percent} aria-valuemin={0} aria-valuemax={100} aria-label={t("found.strength")}><span style={{ width: `${f.strength.percent}%` }} /></div>
          {missing.length ? (
            <div className="strength-list small">
              {missing.map((i) => <Link key={i.id} href={i.href}><Circle size={14} className="muted" /><span>{t(`strength.${i.id}`)}</span></Link>)}
            </div>
          ) : <p className="small">{t("found.strength_full")}</p>}
          <p className="tiny muted">{t("found.strength_why")}</p>
        </div>
        <div className="card card-pad stack" style={{ gap: 10, alignContent: "start" }}>
          <span className="eyebrow">{t("found.standing")}</span>
          {approved && f.rank ? (
            f.rank.position
              ? <p className="small">{t("found.rank", { n: f.rank.position, of: f.rank.of, area: areaName })}</p>
              : <p className="small">{t("found.rank_none", { area: areaName })}</p>
          ) : <p className="small muted">{t("found.rank_after_approval")}</p>}
          <p className="small">{reply ?? t("found.reply_none")}</p>
          {f.strength.reviews < f.strength.prior_reviews && <p className="small">{t("found.reviews_tip", { n: f.strength.prior_reviews })}</p>}
          <p className="tiny muted">{t("found.how_ranked")}</p>
        </div>
      </div>
    </section>
  );
}

/** The next few consultations as booking cards; the full list is on the Bookings tab. */
function UpcomingPreview() {
  const { t } = useTranslation();
  const now = useNow(15000);
  const { data, loading, reload } = useAsync(() => api<Booking[]>("/bookings?scope=upcoming&role=provider"), []);
  if (loading && !data) return <Skeleton h={120} n={1} />;
  if (!data?.length) return <Empty title={t("provide.no_upcoming")} body={t("provide.no_upcoming_body")} />;
  return <div className="bgrid">{data.slice(0, 3).map((b) => <BookingCard key={b.id} b={b} now={now} onChanged={() => void reload()} />)}</div>;
}

export default function ProvideHome() {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const toast = useToast();
  const now = useNow();
  const { data, loading, error, reload } = useAsync(() => api<Dash>("/provide/dashboard"), []);

  if (loading) return <Skeleton h={100} n={3} />;
  if (error || !data) {
    return (
      <div className="card card-pad stack" style={{ maxWidth: 640 }}>
        <h2>{t("provide.start_title")}</h2>
        <p className="muted">{t("provide.start_body")}</p>
        <ul className="small" style={{ margin: 0, paddingLeft: 18, color: "var(--ink-2)" }}>
          <li>{t("provide.start_1")}</li><li>{t("provide.start_2")}</li><li>{t("provide.start_3")}</li><li>{t("provide.start_4")}</li>
        </ul>
        <div><Link href="/provide/profile" className="btn btn-primary btn-lg">{t("provide.start_cta")}</Link></div>
      </div>
    );
  }
  const d = data;
  const steps = [
    { ok: true, label: t("provide.step_profile"), href: "/provide/profile" },
    { ok: d.status === "approved", label: t(`provide.step_review_${d.status === "approved" ? "done" : d.status}`), href: "/provide/profile" },
    { ok: d.has_availability, label: t("provide.step_availability"), href: "/provide/availability" },
    { ok: d.active_services > 0, label: t("provide.step_service"), href: "/provide/services" },
  ];
  const online = !!d.available_until && new Date(d.available_until).getTime() > now;
  const goOnline = async (minutes: number) => { try { await api("/provide/available-now", { body: { minutes } }); await reload(); } catch (e) { toast((e as Error).message); } };
  const submit = async () => { try { await api("/provide/submit", { method: "POST" }); toast(t("provide.submitted")); await reload(); } catch (e) { toast((e as Error).message); } };

  return (
    <div className="stack-lg">
      {d.status !== "approved" && (
        <div className="card card-pad stack">
          <div className="row"><span className={`tag ${d.status === "pending_review" ? "tag-warn" : d.status === "suspended" ? "tag-danger" : ""}`}>{t(`provider.status.${d.status}`)}</span></div>
          <p className="small muted">{t(`provide.status_body.${d.status}`)}</p>
          {d.review_note && <p className="small" style={{ borderLeft: "2px solid var(--line-strong)", paddingLeft: 10 }}>{d.review_note}</p>}
          {(d.status === "draft" || d.status === "changes_requested") && <div><button className="btn btn-primary" onClick={() => void submit()}>{t("provide.submit")}</button></div>}
        </div>
      )}

      <div className="grid grid-2">
        <div className="card card-pad stack" style={{ gap: 8 }}>
          <span className="eyebrow">{t("provide.checklist")}</span>
          {steps.map((s) => (
            <Link key={s.label} href={s.href} className="row small" style={{ gap: 8 }}>
              {s.ok ? <Check size={16} style={{ color: "var(--ok)" }} /> : <Circle size={16} className="muted" />}<span>{s.label}</span>
            </Link>
          ))}
        </div>
        <div className="card card-pad stack" style={{ gap: 8 }}>
          <span className="eyebrow">{t("provide.trust")}</span>
          {d.verified.length ? <VerifiedTags dims={d.verified} max={8} /> : <p className="small muted">{t("provide.no_verification")}</p>}
          <Link href="/provide/profile#evidence" className="link small">{t("provide.add_evidence")}</Link>
        </div>
      </div>

      {d.status === "approved" && (
        <div className="card card-pad between">
          <div className="stack" style={{ gap: 2 }}>
            <span className="strong row" style={{ gap: 8 }}><span className="presence" data-on={online} />{online ? t("offers.online_until", { when: timeShort(d.available_until!, lang) }) : t("offers.offline")}</span>
            <span className="tiny muted">{t("offers.online_hint")}</span>
          </div>
          <div className="row">
            {online ? <button className="btn btn-secondary btn-sm" onClick={() => void goOnline(0)}>{t("offers.go_offline")}</button> : [30, 60, 120].map((m) => <button key={m} className="btn btn-secondary btn-sm" onClick={() => void goOnline(m)}>{t("offers.online_for", { n: m })}</button>)}
          </div>
        </div>
      )}

      <MyPurchases role="provider" />

      <TimeRequests role="provider" pendingOnly />

      <section className="stack">
        <div className="section-title"><h2>{t("provide.upcoming")}</h2><Link href="/provide/bookings" className="link small">{t("home.see_all")}</Link></div>
        <UpcomingPreview />
      </section>

      <FoundSection f={d.found} approved={d.status === "approved"} />

      <section className="stack">
        <div className="section-title"><h2>{t("badge_section.yours")}</h2><span className="tag tag-verified">{t(`standing.${d.badges.standing}`)}</span></div>
        <div className="grid grid-2">
          <div className="card card-pad stack" style={{ gap: 10, alignContent: "start" }}>
            <span className="eyebrow">{t("badge_section.earned")}</span>
            {d.badges.earned.length ? (
              <div className="row" style={{ gap: 8 }}>{d.badges.earned.map((b) => <BadgeChip key={b.id} b={b} />)}</div>
            ) : <p className="small muted">{t("badge_section.none")}</p>}
            <p className="tiny muted">{t(`standing_why.${d.badges.standing}`)}</p>
          </div>
          <div className="card card-pad stack" style={{ gap: 10, alignContent: "start" }}>
            <span className="eyebrow">{t("badge_section.next")}</span>
            <NextMilestones items={d.badges.next} />
          </div>
        </div>
        <p className="tiny muted">{t("badge_section.how")}</p>
      </section>

      <section className="stack">
        <h2>{t("provide.performance")}</h2>
        <div className="grid grid-4">
          <div className="stat"><div className="v">{d.reputation.completed}</div><div className="k">{t("rep.completed")}</div></div>
          <div className="stat"><div className="v">{d.reputation.rating?.toFixed(1) ?? "—"}</div><div className="k">{t("rep.rating", { n: d.reputation.review_count })}</div></div>
          <div className="stat"><div className="v">{d.reputation.repeat_clients}</div><div className="k">{t("rep.repeat")}</div></div>
          <div className="stat"><div className="v">{d.reputation.reliability_percent === null ? "—" : `${d.reputation.reliability_percent}%`}</div><div className="k">{t("rep.reliability")}</div></div>
        </div>
      </section>

      <section className="stack">
        <div className="section-title"><h2>{t("provide.earnings")}</h2><Link href="/provide/earnings" className="link small">{t("provide.details")}</Link></div>
        <div className="grid grid-3">
          <div className="stat"><div className="v">{money(d.earnings.last_30, d.currency, lang)}</div><div className="k">{t("earn.last_30")}</div></div>
          <div className="stat"><div className="v">{money(d.earnings.pending_payout, d.currency, lang)}</div><div className="k">{t("earn.pending")}</div></div>
          <div className="stat"><div className="v">{money(d.earnings.paid_out, d.currency, lang)}</div><div className="k">{t("earn.paid")}</div></div>
        </div>
      </section>
    </div>
  );
}

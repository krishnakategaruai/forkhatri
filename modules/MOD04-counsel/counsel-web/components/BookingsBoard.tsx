"use client";

import Link from "next/link";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { api, type Booking } from "@/lib/api";
import { needsAction, sameDay } from "@/lib/booking";
import { BookingCard } from "@/components/BookingCard";
import { Empty, Skeleton, useAsync, useNow } from "@/components/ui";

type Who = "any" | "seeker" | "provider";
type PastFilter = "all" | "completed" | "cancelled";

function Group({ title, count, children, tone }: { title: string; count: number; children: React.ReactNode; tone?: "action" }) {
  if (!count) return null;
  return (
    <section className="stack" style={{ gap: 10 }}>
      <h3 className={`bgroup${tone === "action" ? " action" : ""}`}>{title}<span className="bcount">{count}</span></h3>
      <div className="bgrid">{children}</div>
    </section>
  );
}

/**
 * Bookings grouped the way people think about them: what needs doing, today,
 * what's coming, and what's done. `role` = "provider" is the consultant's view;
 * "any" lets someone who both books and consults switch between the two.
 * `extra` renders inside the upcoming tab (time requests, follow-ups, questions).
 */
export function BookingsBoard({ role, extra, emptyAction }: { role: Who; extra?: React.ReactNode; emptyAction?: React.ReactNode }) {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const now = useNow(15000);
  const [tab, setTab] = useState<"upcoming" | "past">("upcoming");
  const [who, setWho] = useState<Who>(role);
  const [pastFilter, setPastFilter] = useState<PastFilter>("all");
  const up = useAsync(() => api<Booking[]>(`/bookings?scope=upcoming&role=${role}`), [role]);
  const past = useAsync(() => api<Booking[]>(`/bookings?scope=past&role=${role}`), [role]);
  const reload = () => { void up.reload(); void past.reload(); };

  if (up.loading && !up.data) return <Skeleton h={140} n={3} />;
  const all = [...(up.data ?? []), ...(past.data ?? [])];
  const both = role === "any" && all.some((b) => b.role === "provider") && all.some((b) => b.role === "seeker");
  const mine = (b: Booking) => who === "any" || b.role === who;
  const upcoming = (up.data ?? []).filter(mine);
  const done = (past.data ?? []).filter(mine);

  const action = [...upcoming, ...done].filter((b) => needsAction(b, now));
  const actionIds = new Set(action.map((b) => b.id));
  const rest = upcoming.filter((b) => !actionIds.has(b.id));
  const today = rest.filter((b) => sameDay(b.starts_at, now));
  const later = rest.filter((b) => !sameDay(b.starts_at, now));
  const weekEnd = now + 7 * 86400000;
  const thisWeek = upcoming.filter((b) => new Date(b.starts_at).getTime() < weekEnd).length;

  const pastShown = done.filter((b) => pastFilter === "all" ? true : pastFilter === "completed" ? b.status === "completed" : b.status !== "completed");
  // Past bookings fall under month headings ("September 2026").
  const months: [string, Booking[]][] = [];
  for (const b of pastShown) {
    const key = new Intl.DateTimeFormat(`${lang}-IN`, { month: "long", year: "numeric" }).format(new Date(b.starts_at));
    const last = months[months.length - 1];
    if (last && last[0] === key) last[1].push(b); else months.push([key, [b]]);
  }
  const card = (b: Booking) => <BookingCard key={b.id} b={b} now={now} onChanged={reload} />;

  return (
    <div className="stack-lg">
      <div className="bsummary" role="list">
        <div role="listitem"><span className="v">{upcoming.filter((b) => sameDay(b.starts_at, now)).length}</span><span className="k">{t("bookings.sum_today")}</span></div>
        <div role="listitem"><span className="v">{thisWeek}</span><span className="k">{t("bookings.sum_week")}</span></div>
        <div role="listitem" data-on={action.length > 0}><span className="v">{action.length}</span><span className="k">{t("bookings.sum_action")}</span></div>
      </div>

      {both && (
        <div className="row" style={{ gap: 8 }} role="group" aria-label={t("bookings.whose")}>
          {(["any", "seeker", "provider"] as const).map((w) => (
            <button key={w} className="chip" aria-pressed={who === w} onClick={() => setWho(w)}>{t(`bookings.who.${w}`)}</button>
          ))}
        </div>
      )}

      <div className="tabs" role="tablist" style={{ marginBottom: 0 }}>
        <button role="tab" aria-selected={tab === "upcoming"} onClick={() => setTab("upcoming")}>{t("bookings.upcoming")} <span className="bcount">{upcoming.length}</span></button>
        <button role="tab" aria-selected={tab === "past"} onClick={() => setTab("past")}>{t("bookings.past")} <span className="bcount">{done.length}</span></button>
      </div>

      {tab === "upcoming" ? (
        <div className="stack-lg">
          <Group title={t("bookings.needs_action")} count={action.length} tone="action">{action.map(card)}</Group>
          {extra}
          <Group title={t("bookings.today")} count={today.length}>{today.map(card)}</Group>
          <Group title={t("bookings.coming_up")} count={later.length}>{later.map(card)}</Group>
          {!upcoming.length && (
            <Empty title={role === "provider" || who === "provider" ? t("provide.no_upcoming") : t("bookings.empty_upcoming")}
              body={role === "provider" || who === "provider" ? t("provide.no_upcoming_body") : t("bookings.empty_body")}
              action={emptyAction ?? <Link href="/discover" className="btn btn-primary">{t("bookings.find")}</Link>} />
          )}
        </div>
      ) : (
        <div className="stack-lg">
          {done.length > 0 && (
            <div className="row" style={{ gap: 8 }} role="group" aria-label={t("bookings.past")}>
              {(["all", "completed", "cancelled"] as const).map((f) => (
                <button key={f} className="chip" aria-pressed={pastFilter === f} onClick={() => setPastFilter(f)}>{t(`bookings.past_filter.${f}`)}</button>
              ))}
            </div>
          )}
          {months.map(([m, list]) => <Group key={m} title={m} count={list.length}>{list.map(card)}</Group>)}
          {!pastShown.length && (
            <Empty title={t("bookings.empty_past")} body={done.length ? undefined : t("bookings.empty_body")}
              action={done.length ? undefined : (emptyAction ?? <Link href="/discover" className="btn btn-primary">{t("bookings.find")}</Link>)} />
          )}
        </div>
      )}
    </div>
  );
}

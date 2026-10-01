"use client";

import Link from "next/link";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { CalendarPlus, Clock, Mic, NotebookText, RotateCcw, Star, Video } from "lucide-react";
import { API_BASE, api, ApiError, type Booking } from "@/lib/api";
import { dateShort, dayParts, money, span, timeRangeZone, timeShort } from "@/lib/format";
import { earningMinor, fullRefundUntil, nextStep } from "@/lib/booking";
import { Avatar, StatusTag, useToast } from "@/components/ui";

/** Calendar-style day badge: month, day number, weekday. */
export function DateBadge({ iso, muted = false }: { iso: string; muted?: boolean }) {
  const { i18n } = useTranslation();
  const p = dayParts(iso, i18n.language);
  return (
    <span className={`daybadge${muted ? " muted-badge" : ""}`} aria-hidden>
      <span className="m">{p.month}</span>
      <span className="d">{p.day}</span>
      <span className="w">{p.weekday}</span>
    </span>
  );
}

/** How the call happens: video, or voice when the service is audio only. */
function FormatLabel({ formats }: { formats: string[] }) {
  const { t } = useTranslation();
  const voice = !formats.includes("video") && formats.includes("audio");
  return <span className="row" style={{ gap: 4 }}>{voice ? <Mic size={14} /> : <Video size={14} />}{t(voice ? "bookings.card.voice" : "bookings.card.video")}</span>;
}

/** One booking, for either side, with the single next step its state calls for. */
export function BookingCard({ b, now, onChanged }: { b: Booking; now: number; onChanged?: () => void }) {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const toast = useToast();
  const [busy, setBusy] = useState(false);
  const other = b.role === "seeker" ? b.provider_name : b.seeker_name;
  const step = nextStep(b, now);
  const ended = b.status.startsWith("cancel") || b.status.startsWith("no_show") || b.status === "expired";
  const hot = step.kind === "join" || step.kind === "pay" || step.kind === "complete";

  const complete = async () => {
    setBusy(true);
    try { await api(`/bookings/${b.id}/complete`, { method: "POST" }); toast(t("booking.completed_toast")); onChanged?.(); }
    catch (e) { toast(t(`errors.${(e as ApiError).code}`, { defaultValue: (e as Error).message })); }
    finally { setBusy(false); }
  };

  // The line under the details: when it starts, how long the hold lasts, or what the refund window is.
  let hint: React.ReactNode = null;
  if (step.kind === "pay") hint = <span className="bhint warn"><Clock size={14} />{t("bookings.card.pay_within", { time: span(new Date(step.until).getTime() - now, lang) })}</span>;
  else if (step.kind === "await_payment") hint = <span className="bhint">{t("bookings.card.awaiting_payment", { name: other })}</span>;
  else if (step.kind === "join") hint = <span className="bhint live"><span className="presence" data-on="true" />{step.startsIn > 0 ? t("bookings.card.starts_in", { time: span(step.startsIn, lang) }) : t("bookings.card.live_now")}</span>;
  else if (step.kind === "complete") hint = <span className="bhint warn">{t("bookings.card.ended_mark")}</span>;
  else if (step.kind === "calendar") {
    const until = b.role === "seeker" && !b.purchase_id ? fullRefundUntil(b, now) : null;
    hint = (
      <span className="bhint-stack">
        <span>{t("bookings.card.starts_in", { time: span(step.startsIn, lang) })}</span>
        {until && <span className="tiny muted">{t("bookings.card.free_cancel_until", { when: `${dateShort(until.toISOString(), lang)}, ${timeShort(until.toISOString(), lang)}` })}</span>}
      </span>
    );
  } else if (step.kind === "review") hint = <span className="bhint">{t("bookings.card.review_hint", { name: other })}</span>;

  let action: React.ReactNode = null;
  switch (step.kind) {
    case "pay": action = <Link href={`/bookings/${b.id}`} className="btn btn-primary btn-sm">{t("bookings.card.pay", { amount: money(b.gross_minor, b.currency, lang) })}</Link>; break;
    case "join": action = <Link href={`/room/${b.id}`} className="btn btn-primary btn-sm"><Video size={15} />{t("bookings.card.join")}</Link>; break;
    case "complete": action = (
      <>
        <Link href={`/room/${b.id}`} className="btn btn-ghost btn-sm">{t("bookings.card.open_room")}</Link>
        <button className="btn btn-primary btn-sm" disabled={busy} onClick={() => void complete()}>{t("booking.mark_complete")}</button>
      </>
    ); break;
    case "calendar": action = <a className="btn btn-secondary btn-sm" href={`${API_BASE}/bookings/${b.id}/calendar.ics`}><CalendarPlus size={15} />{t("bookings.card.add_calendar")}</a>; break;
    case "review": action = <Link href={`/bookings/${b.id}?review=1`} className="btn btn-primary btn-sm"><Star size={15} />{t("bookings.card.review")}</Link>; break;
    case "recap": action = <Link href={`/bookings/${b.id}#recap`} className="btn btn-secondary btn-sm"><NotebookText size={15} />{t("bookings.card.recap")}</Link>; break;
    case "book_again": action = <Link href={`/p/${b.provider_id}`} className="btn btn-secondary btn-sm"><RotateCcw size={15} />{t("booking.book_again")}</Link>; break;
  }

  // Money line: what was paid (seeker) or what the consultant keeps and where it is (consultant).
  const moneyLine = b.role === "provider"
    ? (b.status === "pending_payment" ? null : ended && earningMinor(b) === 0 ? null
      : <span>{t(b.status === "completed" || ended ? "bookings.card.you_earned" : "bookings.card.you_earn", { amount: money(earningMinor(b), b.currency, lang) })}{b.payout_status && b.payout_status !== "none" && <span className="muted"> · {t(`bookings.card.payout_${b.payout_status}`)}</span>}</span>)
    : b.purchase_id ? <span>{t("bookings.card.from_follow_up")}</span>
      : b.status === "pending_payment" ? null
        : <span>{t(ended ? "bookings.card.was_paid" : "bookings.card.paid", { amount: money(b.gross_minor, b.currency, lang) })}</span>;

  return (
    <article className={`bcard fade-in${hot ? " hot" : ""}${ended ? " ended" : ""}`}>
      <DateBadge iso={b.starts_at} muted={ended} />
      <div className="bcard-main">
        <div className="bcard-top">
          <Link href={`/bookings/${b.id}`} className="bcard-title">{b.service_title}</Link>
          <StatusTag status={b.status} role={b.role} />
        </div>
        <div className="bcard-who small">
          <Avatar name={other} url={b.role === "seeker" ? b.provider_photo : null} size={24} />
          <span>{b.role === "seeker" ? t("bookings.with", { name: other }) : t("bookings.booked_by", { name: other })}</span>
        </div>
        <div className="bcard-meta small">
          <span className="row" style={{ gap: 4 }}><Clock size={14} />{timeRangeZone(b.starts_at, b.ends_at, lang)}</span>
          <span>{t("service.minutes", { n: b.duration_min })}</span>
          <FormatLabel formats={b.formats ?? []} />
        </div>
        {b.role === "provider" && b.brief && !ended && <p className="bcard-brief small clamp-2">{b.brief}</p>}
        {(moneyLine || b.refund_minor > 0) && (
          <div className="bcard-money small num">
            {moneyLine}
            {b.refund_minor > 0 && <span className="muted">{t("bookings.card.refunded", { amount: money(b.refund_minor, b.currency, lang) })}</span>}
          </div>
        )}
      </div>
      {(hint || action) && (
        <div className="bcard-foot">
          <div className="bcard-hint">{hint}</div>
          {action && <div className="bcard-actions">{action}</div>}
        </div>
      )}
    </article>
  );
}

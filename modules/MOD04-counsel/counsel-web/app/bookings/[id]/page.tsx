"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { AlertTriangle, CalendarPlus, Check, Clock, Mic, NotebookText, Send, Star, Video } from "lucide-react";
import { API_BASE, api, ApiError, type Booking, type Message, type TimelineEvent } from "@/lib/api";
import { PackageOffer } from "@/components/Offers";
import { useRouter } from "next/navigation";
import { dateLong, timeShort, money, relative, span, timeRangeZone } from "@/lib/format";
import { canJoin as roomOpen, earningMinor, refundPercentNow } from "@/lib/booking";
import { DateBadge } from "@/components/BookingCard";
import { Avatar, Dialog, Skeleton, StarInput, StatusTag, useAsync, useNow, useToast } from "@/components/ui";

function Detail() {
  const { id } = useParams<{ id: string }>();
  const sp = useSearchParams();
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const toast = useToast();
  const router = useRouter();
  const { data: b, loading, reload: reloadBooking } = useAsync(() => api<Booking>(`/bookings/${id}`), [id]);
  const { data: tl, reload: reloadTimeline } = useAsync(() => api<{ events: TimelineEvent[]; currency: string }>(`/bookings/${id}/timeline`), [id]);
  const reload = async () => { await Promise.all([reloadBooking(), reloadTimeline()]); };
  const [msgs, setMsgs] = useState<Message[]>([]);
  const [text, setText] = useState("");
  const [cancel, setCancel] = useState(false);
  const [reason, setReason] = useState("");
  const [review, setReview] = useState(() => sp.get("review") === "1");
  const [dispute, setDispute] = useState(false);
  const [r, setR] = useState({ overall: 5, expertise: 5, communication: 5, professionalism: 5, punctuality: 5, body: "" });
  const [busy, setBusy] = useState(false);
  const bottom = useRef<HTMLDivElement>(null);
  const now = useNow(15000);

  useEffect(() => {
    let alive = true;
    const poll = async () => {
      try { const m = await api<Message[]>(`/bookings/${id}/messages`); if (alive) setMsgs(m); } catch { /* ignore */ }
    };
    void poll();
    const h = window.setInterval(poll, 8000);
    return () => { alive = false; window.clearInterval(h); };
  }, [id]);
  useEffect(() => { bottom.current?.scrollIntoView({ block: "nearest" }); }, [msgs.length]);

  if (loading || !b) return <div className="wrap page"><Skeleton h={120} n={3} /></div>;
  const tiers = b.cancellation_policy?.seeker ?? [];
  const other = b.role === "seeker" ? b.provider_name : b.seeker_name;
  const live = ["confirmed", "in_progress"].includes(b.status);
  const canJoin = roomOpen(b, now);
  const canCancel = ["pending_payment", "confirmed"].includes(b.status);
  const canNoShow = live && now >= new Date(b.starts_at).getTime() + 10 * 60000;
  const canComplete = live && now >= new Date(b.starts_at).getTime();
  const refundPct = refundPercentNow(b, now);
  const refundNow = Math.round(b.gross_minor * refundPct / 100);
  const startsIn = new Date(b.starts_at).getTime() - now;
  const currentTier = b.role === "seeker" ? [...tiers].sort((x, y) => y.min_hours_before - x.min_hours_before).find((tier) => startsIn / 3600000 >= tier.min_hours_before) : undefined;
  const voice = !(b.formats ?? []).includes("video") && (b.formats ?? []).includes("audio");
  const who = (w: "you" | "other" | null) => (w === "other" ? other : "");

  const send = async () => {
    if (!text.trim()) return;
    const body = text.trim(); setText("");
    try { const m = await api<Message>(`/bookings/${id}/messages`, { body: { body } }); setMsgs((s) => [...s, m]); } catch (e) { toast((e as Error).message); }
  };
  const act = async (fn: () => Promise<unknown>, ok: string) => {
    setBusy(true);
    try { await fn(); toast(ok); await reload(); } catch (e) { toast(t(`errors.${(e as ApiError).code}`, { defaultValue: (e as Error).message })); } finally { setBusy(false); }
  };

  return (
    <div className="wrap page two-col">
      <div className="stack-lg">
        {sp.get("new") && <div className="card card-pad row fade-in" style={{ borderColor: "var(--accent)" }}><Check className="muted" /><div><div className="strong">{t("booking.confirmed_title")}</div><div className="small muted">{t("booking.confirmed_body")}</div></div></div>}
        <header className="card bhead">
          <DateBadge iso={b.starts_at} muted={!live && b.status !== "pending_payment"} />
          <div className="stack" style={{ gap: 8, minWidth: 0 }}>
            <div className="row"><StatusTag status={b.status} role={b.role} /><span className="tiny muted">{relative(b.starts_at, lang)}</span>{b.purchase_id && <span className="tag">{t("offers.package_session")}</span>}</div>
            <h1 style={{ fontSize: "clamp(1.45rem,3vw,2.1rem)" }}>{b.service_title}</h1>
            <div className="row small">
              <Avatar name={other} url={b.role === "seeker" ? b.provider_photo : null} size={28} />
              <span>{b.role === "seeker" ? t("bookings.with", { name: other }) : t("bookings.booked_by", { name: other })}</span>
              {b.role === "seeker" && <Link href={`/p/${b.provider_id}`} className="link">{t("booking.view_profile")}</Link>}
            </div>
            <div className="bcard-meta small">
              <span className="row" style={{ gap: 4 }}><Clock size={14} />{dateLong(b.starts_at, lang)} · {timeRangeZone(b.starts_at, b.ends_at, lang)}</span>
              <span>{t("service.minutes", { n: b.duration_min })}</span>
              <span className="row" style={{ gap: 4 }}>{voice ? <Mic size={14} /> : <Video size={14} />}{t(voice ? "bookings.card.voice" : "bookings.card.video")}</span>
            </div>
            {live && !canJoin && startsIn > 0 && <span className="small strong">{t("bookings.card.starts_in", { time: span(startsIn, lang) })}</span>}
          </div>
        </header>

        {b.status === "pending_payment" && b.role === "seeker" && b.pay_by && (
          <div className="card card-pad between" style={{ borderColor: "var(--accent)" }}>
            <div className="stack" style={{ gap: 4 }}>
              <div className="serif" style={{ fontSize: "1.2rem" }}>{t("booking.held_title")}</div>
              <div className="small muted">{t("booking.held_body", { when: `${dateLong(b.pay_by, lang)}, ${timeShort(b.pay_by, lang)}` })}</div>
              <span className="bhint warn"><Clock size={14} />{t("bookings.card.pay_within", { time: span(new Date(b.pay_by).getTime() - now, lang) })}</span>
            </div>
            <button className="btn btn-primary" disabled={busy} onClick={() => void act(() => api(`/bookings/${id}/pay`, { body: { proof: { mock_result: "success" } } }), t("book.confirmed_toast"))}>{t("book.pay_confirm", { amount: money(b.gross_minor, b.currency, lang) })}</button>
          </div>
        )}
        {b.status === "pending_payment" && b.role === "provider" && <div className="card card-pad small muted">{t("bookings.card.awaiting_payment", { name: other })}</div>}
        {canJoin && (
          <Link href={`/room/${b.id}`} className="card card-pad between" style={{ background: "var(--accent-soft)", borderColor: "transparent" }}>
            <div>
              <div className="serif" style={{ fontSize: "1.2rem" }}>{t("booking.room_ready")}</div>
              <div className="small muted">{startsIn > 0 ? t("bookings.card.starts_in", { time: span(startsIn, lang) }) : t("bookings.card.live_now")} · {t("booking.room_hint")}</div>
            </div>
            <span className="btn btn-primary"><Video size={16} />{t("booking.join")}</span>
          </Link>
        )}
        {b.role === "seeker" && b.status === "completed" && !b.reviewed && (
          <div className="card card-pad between">
            <div><div className="serif" style={{ fontSize: "1.2rem" }}>{t("booking.review_ask_title")}</div><div className="small muted">{t("bookings.card.review_hint", { name: other })}</div></div>
            <button className="btn btn-primary" onClick={() => setReview(true)}><Star size={16} />{t("booking.write_review")}</button>
          </div>
        )}
        {b.status === "completed" && <Link href={`/room/${b.id}`} className="link small">{t("booking.open_workspace")}</Link>}

        {b.brief && <section className="stack" style={{ gap: 6 }}><span className="eyebrow">{b.role === "provider" ? t("booking.brief_provider") : t("booking.brief")}</span><p style={{ whiteSpace: "pre-wrap", color: "var(--ink-2)" }}>{b.brief}</p></section>}

        <section className="card" style={{ display: "grid", gridTemplateRows: "auto 1fr auto", maxHeight: 480 }}>
          <div className="card-pad" style={{ paddingBottom: 8 }}><span className="eyebrow">{t("booking.conversation")}</span><p className="tiny muted">{t("booking.conversation_hint")}</p></div>
          <div className="stack" style={{ overflow: "auto", padding: "0 18px", gap: 8 }}>
            {msgs.map((m) => m.kind === "system" ? (
              <div key={m.id} className="bubble sys">{t(`system.${m.body}`, { defaultValue: m.body })}</div>
            ) : (
              <div key={m.id} className={`bubble ${m.sender_id === (b.role === "seeker" ? b.seeker_id : b.provider_id) ? "mine" : ""}`}>
                {m.kind === "file" ? <Link className="link" href={`/room/${b.id}`}>📎 {m.body}</Link> : m.body}
                <div className="tiny muted">{timeShort(m.created_at, lang)}</div>
              </div>
            ))}
            <div ref={bottom} />
          </div>
          <form className="row card-pad" style={{ paddingTop: 10, gap: 8, flexWrap: "nowrap" }} onSubmit={(e) => { e.preventDefault(); void send(); }}>
            <input className="input" value={text} onChange={(e) => setText(e.target.value)} placeholder={t("booking.message_placeholder")} />
            <button className="btn btn-primary" type="submit" aria-label={t("common.send")}><Send size={16} /></button>
          </form>
        </section>

        {b.follow_ups && b.follow_ups.length > 0 && (
          <section className="card card-pad stack" style={{ gap: 10 }}>
            <div className="stack" style={{ gap: 2 }}>
              <span className="serif" style={{ fontSize: "1.15rem" }}>{t("offers.continue_title", { name: b.provider_name })}</span>
              <span className="small muted">{t("offers.continue_body")}</span>
            </div>
            <PackageOffer packages={b.follow_ups} priceMinor={b.service_price_minor ?? b.gross_minor} currency={b.currency} providerName={b.provider_name}
              onBought={(pid) => router.push(`/book/${b.service_id}?package=${pid}`)} hideTitle />
          </section>
        )}
        {b.recap && (
          <section id="recap" className="card card-pad stack" style={{ gap: 8, scrollMarginTop: 90 }}>
            <span className="eyebrow row" style={{ gap: 6 }}><NotebookText size={13} />{t("offers.recap")}</span>
            <div className="recap small">{b.recap.split("\n").map((line, i) => line.startsWith("## ") ? <div key={i} className="strong" style={{ marginTop: 6 }}>{t(`offers.recap_h.${line.slice(3).toLowerCase().replace(/ /g, "_")}`, { defaultValue: line.slice(3) })}</div> : <div key={i}>{line}</div>)}</div>
          </section>
        )}
        {b.review && <section className="card card-pad stack" style={{ gap: 6 }}><span className="eyebrow">{t("booking.your_review")}</span><div className="row"><span className="stars">{"★".repeat(b.review.overall)}</span></div>{b.review.body && <p className="small">{b.review.body}</p>}</section>}
        {b.dispute && <section className="card card-pad stack" style={{ gap: 6 }}><span className="eyebrow">{t("booking.dispute")}</span><div className="row"><span className="tag tag-warn">{t(`dispute.${b.dispute.status}`)}</span></div><p className="small">{b.dispute.reason}</p>{b.dispute.resolution && <p className="small muted">{b.dispute.resolution}</p>}</section>}

        {!!tl?.events.length && (
          <section className="card card-pad stack" style={{ gap: 12 }}>
            <span className="eyebrow">{t("timeline.title")}</span>
            <ol className="btimeline">
              {tl.events.map((e, i) => {
                const kind = e.kind.startsWith("cancelled") ? "cancelled" : e.kind;
                const params = { name: who(e.who), amount: e.params.amount_minor !== undefined ? money(e.params.amount_minor, tl.currency, lang) : "", n: e.params.overall ?? 0, status: e.params.status ? t(`dispute.${e.params.status}`) : "" };
                const label = e.who ? t(`timeline.${kind}_${e.who}`, { ...params, defaultValue: t(`timeline.${kind}`, params) }) : t(`timeline.${kind}`, params);
                return (
                  <li key={`${e.kind}-${i}`}>
                    <span className="small">{label}</span>
                    <span className="tiny muted">{dateLong(e.at, lang)}, {timeShort(e.at, lang)}</span>
                  </li>
                );
              })}
            </ol>
          </section>
        )}
      </div>

      <aside className="stack">
        <div className="card card-pad stack">
          <span className="eyebrow">{t("booking.money")}</span>
          <div className="between small"><span className="muted">{t("book.price")}</span><span className="num">{money(b.gross_minor, b.currency, lang)}</span></div>
          {b.role === "provider" && <div className="between small"><span className="muted">{t("booking.platform_fee")}</span><span className="num">− {money(b.platform_fee_minor, b.currency, lang)}</span></div>}
          {b.role === "provider" && <div className="between small"><span className="muted">{t("booking.you_receive")}</span><span className="num strong">{money(earningMinor(b), b.currency, lang)}</span></div>}
          {b.role === "provider" && b.payout_status && b.payout_status !== "none" && <div className="between small"><span className="muted">{t("booking.payout")}</span><span className="cap">{t(`bookings.card.payout_${b.payout_status}`)}</span></div>}
          {b.refund_minor > 0 && <div className="between small"><span className="muted">{t("booking.refunded")}</span><span className="num">{money(b.refund_minor, b.currency, lang)}</span></div>}
          <div className="divider" />
          <span className="eyebrow">{t("book.cancellation")}</span>
          <ul className="tiny muted" style={{ margin: 0, paddingLeft: 16 }}>
            {tiers.map((tier) => <li key={tier.min_hours_before} className={b.status === "confirmed" && currentTier === tier ? "strong" : undefined} style={b.status === "confirmed" && currentTier === tier ? { color: "var(--ink)" } : undefined}>{tier.min_hours_before > 0 ? t("policy.tier", { h: tier.min_hours_before, pct: tier.refund_percent }) : t("policy.tier_last", { pct: tier.refund_percent })}</li>)}
          </ul>
        </div>
        <div className="card card-pad stack">
          {live && <a className="btn btn-secondary btn-block" href={`${API_BASE}/bookings/${b.id}/calendar.ics`}><CalendarPlus size={16} />{t("offers.add_calendar")}</a>}
          {canComplete && <button className="btn btn-secondary btn-block" disabled={busy} onClick={() => void act(() => api(`/bookings/${id}/complete`, { method: "POST" }), t("booking.completed_toast"))}>{t("booking.mark_complete")}</button>}
          {canNoShow && <button className="btn btn-secondary btn-block" disabled={busy} onClick={() => void act(() => api(`/bookings/${id}/no-show`, { method: "POST" }), t("booking.no_show_toast"))}><AlertTriangle size={15} />{t("booking.report_no_show")}</button>}
          {canCancel && (
            <div className="stack" style={{ gap: 4 }}>
              <button className="btn btn-danger btn-block" onClick={() => setCancel(true)}>{t("booking.cancel")}</button>
              {b.status === "confirmed" && !b.purchase_id && <span className="tiny muted" style={{ textAlign: "center" }}>{refundNow > 0 ? t("booking.cancel_now_refund", { amount: money(refundNow, b.currency, lang), pct: refundPct }) : t("booking.cancel_now_none")}</span>}
            </div>
          )}
          {!b.dispute && ["completed", "no_show_seeker", "no_show_provider", "in_progress"].includes(b.status) && <button className="btn btn-ghost btn-block" onClick={() => setDispute(true)}>{t("booking.open_dispute")}</button>}
          {b.role === "seeker" && b.status === "completed" && <Link href={`/p/${b.provider_id}`} className="btn btn-ghost btn-block">{t("booking.book_again")}</Link>}
        </div>
      </aside>

      <Dialog open={cancel} onClose={() => setCancel(false)} title={t("booking.cancel_title")}>
        <p className="small">{b.status === "confirmed" ? t("booking.cancel_refund", { pct: refundPct, amount: money(Math.round(b.gross_minor * refundPct / 100), b.currency, lang) }) : t("booking.cancel_unpaid")}</p>
        <textarea className="textarea" value={reason} onChange={(e) => setReason(e.target.value)} placeholder={t("booking.cancel_reason")} style={{ minHeight: 80 }} />
        <div className="row" style={{ justifyContent: "flex-end" }}>
          <button className="btn btn-ghost" onClick={() => setCancel(false)}>{t("common.keep")}</button>
          <button className="btn btn-danger" disabled={busy} onClick={() => void act(() => api(`/bookings/${id}/cancel`, { body: { reason } }), t("booking.cancelled_toast")).then(() => setCancel(false))}>{t("booking.cancel_confirm")}</button>
        </div>
      </Dialog>

      <Dialog open={review} onClose={() => setReview(false)} title={t("booking.review_title")}>
        {(["overall", "expertise", "communication", "professionalism", "punctuality"] as const).map((k) => (
          <StarInput key={k} label={t(`review.${k}`)} value={r[k]} onChange={(v) => setR({ ...r, [k]: v })} />
        ))}
        <textarea className="textarea" value={r.body} onChange={(e) => setR({ ...r, body: e.target.value })} placeholder={t("booking.review_placeholder")} />
        <div className="row" style={{ justifyContent: "flex-end" }}>
          <button className="btn btn-ghost" onClick={() => setReview(false)}>{t("common.cancel")}</button>
          <button className="btn btn-primary" disabled={busy} onClick={() => void act(() => api(`/bookings/${id}/review`, { body: r }), t("booking.review_thanks")).then(() => setReview(false))}>{t("booking.review_submit")}</button>
        </div>
      </Dialog>

      <Dialog open={dispute} onClose={() => setDispute(false)} title={t("booking.dispute_title")}>
        <p className="small muted">{t("booking.dispute_body")}</p>
        <textarea className="textarea" value={reason} onChange={(e) => setReason(e.target.value)} placeholder={t("booking.dispute_placeholder")} />
        <div className="row" style={{ justifyContent: "flex-end" }}>
          <button className="btn btn-ghost" onClick={() => setDispute(false)}>{t("common.cancel")}</button>
          <button className="btn btn-primary" disabled={busy || !reason.trim()} onClick={() => void act(() => api(`/bookings/${id}/dispute`, { body: { reason } }), t("booking.dispute_opened")).then(() => setDispute(false))}>{t("booking.dispute_submit")}</button>
        </div>
      </Dialog>
    </div>
  );
}

export default function BookingPage() {
  return <Suspense fallback={<div className="wrap page"><Skeleton h={120} n={3} /></div>}><Detail /></Suspense>;
}

"use client";

import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Check, Clock, Video } from "lucide-react";
import { api, ApiError, type Booking, type ServiceDetail } from "@/lib/api";
import { dateLong, dayKey, localTimeZone, money, timeShort, timeZoneLabel } from "@/lib/format";
import { Avatar, Skeleton, useAsync, useNow, useToast } from "@/components/ui";
import { useIdentity } from "@/lib/identity";
import { AskQuestion, PackageOffer, type Purchase } from "@/components/Offers";
import { entranceSignInUrl } from "@/lib/platform";

export default function BookPageWrap() {
  return <Suspense fallback={<div className="wrap page"><Skeleton h={120} n={3} /></div>}><BookPage /></Suspense>;
}

function BookPage() {
  const { serviceId } = useParams<{ serviceId: string }>();
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const router = useRouter();
  const toast = useToast();
  const { me, ready } = useIdentity();
  const { data: s, loading } = useAsync(() => api<ServiceDetail>(`/services/${serviceId}`), [serviceId]);
  const [slots, setSlots] = useState<string[] | null>(null);
  const [day, setDay] = useState<string | null>(null);
  const [slot, setSlot] = useState<string | null>(null);
  const [brief, setBrief] = useState("");
  const [agree, setAgree] = useState(false);
  const [step, setStep] = useState<1 | 2>(1);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const tz = localTimeZone();
  const now = useNow(15000);
  const [propose, setPropose] = useState(false);
  const [pDate, setPDate] = useState("");
  const [pTime, setPTime] = useState("");
  const [pNote, setPNote] = useState("");
  const [proposed, setProposed] = useState(false);
  const sp = useSearchParams();
  const [usePkg, setUsePkg] = useState<string | null>(sp.get("package"));
  const [mine, setMine] = useState<Purchase[]>([]);
  useEffect(() => { if (me) void api<Purchase[]>("/purchases").then(setMine).catch(() => {}); }, [me, usePkg]);
  const activePkg = mine.find((p) => p.kind === "package" && p.role === "buyer" && p.status === "active" && p.service_id === serviceId && (p.sessions_total ?? 0) > p.sessions_used);
  // Offer the person's own package by default, once; "pay separately" is respected.
  const [pkgChoice, setPkgChoice] = useState<"auto" | "single">("auto");
  const chosenPkg = usePkg ?? (pkgChoice === "auto" ? activePkg?.id ?? null : null);
  const pkg = mine.find((p) => p.id === chosenPkg);

  useEffect(() => { void api<{ slots: string[] }>(`/services/${serviceId}/slots?days=30`).then((r) => setSlots(r.slots)); }, [serviceId]);
  const days = useMemo(() => {
    const m = new Map<string, string[]>();
    for (const iso of slots ?? []) { const k = dayKey(iso); m.set(k, [...(m.get(k) ?? []), iso]); }
    return [...m.entries()];
  }, [slots]);
  useEffect(() => { if (!day && days[0]) setDay(days[0][0]); }, [days, day]);

  if (loading || !s) return <div className="wrap page"><Skeleton h={120} n={3} /></div>;
  const q = s.quote;
  const policy = s.cancellation_policy;

  const sendProposal = async () => {
    setBusy(true); setError(null);
    try {
      const startsAt = new Date(`${pDate}T${pTime}`).toISOString();
      await api(`/services/${s.id}/time-requests`, { body: { starts_at: startsAt, brief, note: pNote, timezone: tz } });
      setProposed(true);
    } catch (e) {
      const err = e as ApiError;
      setError(t(`errors.${err.code}`, { defaultValue: err.message }));
    } finally { setBusy(false); }
  };

  const confirm = async () => {
    if (!slot) return;
    setBusy(true); setError(null);
    try {
      if (chosenPkg) {
        // A package session: already paid for, confirmed straight away.
        const r = await api<{ id: string }>(`/purchases/${chosenPkg}/book`, { body: { starts_at: slot, brief, timezone: tz } });
        toast(t("book.confirmed_toast"));
        router.replace(`/bookings/${r.id}?new=1`);
        return;
      }
      const b = await api<Booking>("/bookings", { body: { service_id: s.id, starts_at: slot, brief, timezone: tz } });
      // Mock checkout: succeeds immediately in development. A real gateway adapter opens its checkout here.
      const paid = await api<Booking>(`/bookings/${b.id}/pay`, { body: { proof: { mock_result: "success" } } });
      toast(t("book.confirmed_toast"));
      router.replace(`/bookings/${paid.id}?new=1`);
    } catch (e) {
      const err = e as ApiError;
      setError(t(`errors.${err.code}`, { defaultValue: err.message }));
      if (err.code === "slot_taken" || err.code === "slot_unavailable") {
        setSlot(null); setStep(1);
        void api<{ slots: string[] }>(`/services/${serviceId}/slots?days=30`).then((r) => setSlots(r.slots));
      }
    } finally { setBusy(false); }
  };

  return (
    <div className="wrap page two-col">
      <div className="stack-lg">
        <div className="stack" style={{ gap: 6 }}>
          <div className="steps"><b>{t("book.step_time")}</b><span>→</span><span className={step === 2 ? "strong" : ""}>{pkg ? t("offers.step_confirm_pkg") : t("book.step_confirm")}</span></div>
          <h1 style={{ fontSize: "clamp(1.6rem,3vw,2.2rem)" }}>{step === 1 ? t("book.pick_time") : t("book.review_confirm")}</h1>
        </div>

        {step === 1 && (
          <section className="stack">
            {!slots ? <Skeleton h={60} n={2} /> : days.length === 0 ? (
              <div className="card card-pad muted">{t("book.no_slots")}</div>
            ) : (
              <>
                <div className="slot-days" role="tablist">
                  {days.map(([k, list]) => {
                    const d = new Date(list[0]);
                    return (
                      <button key={k} role="tab" aria-selected={day === k} className={`slot-day ${day === k ? "on" : ""}`} onClick={() => { setDay(k); setSlot(null); }}>
                        <div className="tiny">{new Intl.DateTimeFormat(lang === "en" ? "en-IN" : `${lang}-IN`, { weekday: "short" }).format(d)}</div>
                        <div className="d">{d.getDate()}</div>
                        <div className="tiny">{new Intl.DateTimeFormat(lang === "en" ? "en-IN" : `${lang}-IN`, { month: "short" }).format(d)}</div>
                      </button>
                    );
                  })}
                </div>
                <p className="tiny muted">{t("book.times_in", { tz: timeZoneLabel(lang) })}</p>
                <div className="slots">
                  {(days.find(([k]) => k === day)?.[1] ?? []).map((iso) => (
                    <button key={iso} className={`slot ${slot === iso ? "on" : ""} ${s.available_now && new Date(iso).getTime() - now < 10 * 60000 ? "slot-now" : ""}`} onClick={() => setSlot(iso)} aria-pressed={slot === iso}>{s.available_now && new Date(iso).getTime() - now < 10 * 60000 ? t("offers.now") : timeShort(iso, lang)}</button>
                  ))}
                </div>
              </>
            )}
            {s.allow_custom_time && (
              <div className="card card-pad stack" style={{ gap: 10 }}>
                {proposed ? (
                  <div className="stack" style={{ gap: 4 }}>
                    <span className="strong">{t("book.proposed_title")}</span>
                    <span className="small muted">{t("book.proposed_body", { name: s.provider_name })}</span>
                    <Link href="/bookings" className="link small">{t("book.see_requests")}</Link>
                  </div>
                ) : !propose ? (
                  <div className="between">
                    <span className="small muted">{t("book.none_work")}</span>
                    <button className="btn btn-secondary btn-sm" onClick={() => setPropose(true)} disabled={ready && !me}>{t("book.propose")}</button>
                  </div>
                ) : (
                  <>
                    <span className="strong small">{t("book.propose_title")}</span>
                    <p className="tiny muted">{t("book.propose_hint", { name: s.provider_name })}</p>
                    <div className="grid grid-2">
                      <label className="field"><span className="label">{t("avail.date")}</span><input type="date" className="input" value={pDate} onChange={(e) => setPDate(e.target.value)} /></label>
                      <label className="field"><span className="label">{t("book.time")}</span><input type="time" className="input" value={pTime} step={900} onChange={(e) => setPTime(e.target.value)} /></label>
                    </div>
                    <input className="input" value={pNote} onChange={(e) => setPNote(e.target.value.slice(0, 500))} placeholder={t("book.propose_note")} />
                    <div className="row">
                      <button className="btn btn-ghost btn-sm" onClick={() => setPropose(false)}>{t("common.cancel")}</button>
                      <button className="btn btn-primary btn-sm" disabled={!pDate || !pTime || busy} onClick={() => void sendProposal()}>{t("book.send_proposal")}</button>
                    </div>
                  </>
                )}
              </div>
            )}
            {error && step === 1 && <p className="error">{error}</p>}
            <label className="field">
              <span className="label">{t("book.brief")}</span>
              <textarea className="textarea" value={brief} onChange={(e) => setBrief(e.target.value.slice(0, 1500))} placeholder={t("book.brief_placeholder")} />
              <span className="hint">{t("book.brief_hint")}</span>
            </label>
            <div>
              {ready && !me ? (
                <a className="btn btn-primary btn-lg" href={entranceSignInUrl()}>{t("book.signin_to_book")}</a>
              ) : (
                <button className="btn btn-primary btn-lg" disabled={!slot} onClick={() => setStep(2)}>{t("book.continue")}</button>
              )}
            </div>
          </section>
        )}

        {step === 2 && slot && (
          <section className="stack">
            <div className="card card-pad stack">
              {[
                [t("book.who"), s.provider_name],
                [t("book.what"), s.title],
                [t("book.when"), `${dateLong(slot, lang)}, ${timeShort(slot, lang)} (${timeZoneLabel(lang)})`],
                [t("book.how_long"), t("service.minutes", { n: s.duration_min })],
                [t("book.how"), s.formats.map((f) => t(`format.${f}`)).join(" · ")],
                [t("book.recording"), s.recording_allowed ? t("book.recording_optional") : t("book.recording_never")],
              ].map(([k, v]) => (
                <div key={k} className="between small"><span className="muted">{k}</span><span style={{ textAlign: "right" }}>{v}</span></div>
              ))}
              <div className="divider" />
              {pkg ? (
                <div className="between"><span className="strong">{t("offers.from_package", { n: pkg.sessions_used + 1, total: pkg.sessions_total })}</span><span className="serif num" style={{ fontSize: "1.3rem" }}>{t("offers.nothing_to_pay")}</span></div>
              ) : (<>
              <div className="between small"><span className="muted">{t("book.price")}</span><span className="num">{money(q.gross_minor, q.currency, lang)}</span></div>
              <div className="between tiny muted"><span>{t("book.fee_note", { pct: q.platform_fee_percent })}</span><span className="num">{money(q.platform_fee_minor, q.currency, lang)}</span></div>
              <div className="between" style={{ fontSize: "1.1rem" }}><span className="strong">{t("book.you_pay")}</span><span className="serif num" style={{ fontSize: "1.4rem" }}>{money(q.gross_minor, q.currency, lang)}</span></div>
              </>)}
            </div>

            <div className="card card-pad stack" style={{ gap: 8 }}>
              <span className="eyebrow">{t("book.cancellation")}</span>
              <ul className="small" style={{ margin: 0, paddingLeft: 18, color: "var(--ink-2)" }}>
                {policy.seeker.map((tier) => (
                  <li key={tier.min_hours_before}>
                    {tier.min_hours_before > 0 ? t("policy.tier", { h: tier.min_hours_before, pct: tier.refund_percent }) : t("policy.tier_last", { pct: tier.refund_percent })}
                  </li>
                ))}
                <li>{t("policy.provider_cancels", { pct: policy.provider_cancel_refund_percent })}</li>
                <li>{t("policy.no_show", { pct: policy.seeker_no_show_refund_percent })}</li>
              </ul>
              {s.disclaimer_key && <p className="tiny" style={{ color: "var(--warn)" }}>{t(s.disclaimer_key)}</p>}
              <p className="tiny muted">{t("book.platform_role")}</p>
              <label className="check"><input type="checkbox" checked={agree} onChange={(e) => setAgree(e.target.checked)} /><span className="small">{t("book.agree")}</span></label>
            </div>

            {error && <p className="error">{error}</p>}
            <div className="row">
              <button className="btn btn-ghost" onClick={() => setStep(1)}>{t("common.back")}</button>
              <button className="btn btn-primary btn-lg" disabled={!agree || busy} onClick={() => void confirm()}>
                <Check size={18} />{busy ? t("book.paying") : pkg ? t("offers.confirm_session") : t("book.pay_confirm", { amount: money(q.gross_minor, q.currency, lang) })}
              </button>
            </div>
            <p className="tiny muted">{t("book.mock_note")}</p>
          </section>
        )}
      </div>

      <aside className="card card-pad stack">
        <div className="row" style={{ gap: 12 }}>
          <Avatar name={s.provider_name} url={s.photo_url} size={56} />
          <div><Link href={`/p/${s.provider_id}`} className="serif" style={{ fontSize: "1.15rem" }}>{s.provider_name}</Link><div className="tiny muted">{s.area_name}</div></div>
        </div>
        <div className="divider" />
        <h3>{s.title}</h3>
        <div className="tiny muted row">
          <span className="row" style={{ gap: 4 }}><Clock size={12} />{t("service.minutes", { n: s.duration_min })}</span>
          <span className="row" style={{ gap: 4 }}><Video size={12} />{s.formats.map((f) => t(`format.${f}`)).join(" · ")}</span>
        </div>
        <p className="small" style={{ color: "var(--ink-2)" }}>{s.description}</p>
        {s.outcomes.length > 0 && (
          <div className="stack" style={{ gap: 4 }}>
            <span className="eyebrow">{t("service.you_leave_with")}</span>
            <ul className="small" style={{ margin: 0, paddingLeft: 18 }}>{s.outcomes.map((o) => <li key={o}>{o}</li>)}</ul>
          </div>
        )}
        <div className="serif" style={{ fontSize: "1.5rem" }}>{money(s.price_minor, s.currency, lang)}</div>
        {s.available_now && <span className="live-tag"><span className="presence" data-on="true" />{t("offers.available_now")}</span>}
        {pkg ? (
          <div className="card card-pad stack" style={{ gap: 6, background: "var(--accent-soft)", borderColor: "transparent" }}>
            <span className="strong small">{t("offers.using_package", { left: (pkg.sessions_total ?? 0) - pkg.sessions_used, total: pkg.sessions_total })}</span>
            <button className="link small" style={{ justifySelf: "start" }} onClick={() => { setUsePkg(null); setPkgChoice("single"); }}>{t("offers.pay_single_instead")}</button>
          </div>
        ) : (
          <>
            {activePkg && <button className="link small" style={{ justifySelf: "start" }} onClick={() => { setUsePkg(activePkg.id); setPkgChoice("auto"); }}>{t("offers.use_my_package")}</button>}
            {s.follow_up_eligible && <PackageOffer packages={s.packages} priceMinor={s.price_minor} currency={s.currency} providerName={s.provider_name} onBought={(id) => setUsePkg(id)} />}
          </>
        )}
        <AskQuestion serviceId={s.id} priceMinor={s.question_price_minor} days={s.question_answer_days} currency={s.currency} providerName={s.provider_name} />
      </aside>
    </div>
  );
}

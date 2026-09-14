'use client';

/* Activity/Event Detail (UX06/UI06) + RSVP toggle (UX08/UI08) + share sheet
 * (FR049) + report (FR061) + block (FR062) + feedback prompt (FR066) +
 * notification priming on first "Going" (FR082) + safety block (FR064) +
 * organizer identity/location once RSVP'd (FR063). Renders from the
 * server-fetched public contract first (FR047), then enriches with the
 * authenticated detail when a member is present. */

import dynamic from 'next/dynamic';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { TrustPill } from '@/components/ActivityCard';
import Moments from '@/components/Moments';
import QrCode from '@/components/QrCode';
import Thread from '@/components/Thread';
import { Modal, Sheet } from '@/components/Sheet';
import { CardSkeleton, ErrorState, Toast } from '@/components/States';
import { api, ApiError, resolveMediaUrl, type Card } from '@/lib/api';
import { formatDateLong, formatRelative } from '@/lib/format';
import { buildIcs, icsDataUrl } from '@/lib/ics';
import { renderPoster } from '@/lib/poster';
import { useIdentity } from '@/lib/identity';

const MiniMap = dynamic(() => import('@/components/MiniMap'), { ssr: false, loading: () => <div className="sk" style={{ height: 150 }} /> });

export type PublicPage = {
  card: Card; description: string | null;
  organizer: { display_name: string; avatar: string | null; trust_label: string; trust_level: string; trust_positive: boolean; reputation: string[]; member_id: string };
  capacity: number | null; spots_left: number | null; safety_guidelines: string[];
  rsvp_cta: { authenticated: boolean; viewer_status: string | null };
  share: { path: string; channels: string[]; text: string };
  seo: { title: string; description: string; image: string | null };
  series: { held: number; upcoming: number; first_at: string | null; upcoming_list?: { id: string; slug: string; time_start: string }[] } | null;
  viewer_role: string | null;
};

type Detail = Card & {
  description: string | null; share_url: string; viewer_role: string;
  organizer: { member_id: string; display_name: string; avatar: string | null; trust_label: string; trust_positive: boolean; reputation: string[]; identity_visible: boolean };
  co_organizers: { member_id: string; display_name: string }[];
  announcements: { id: string; message: string; created_at: string; by: string }[];
  safety_guidelines: string[];
  series: { held: number; upcoming: number; recurrence_rule: Record<string, string> | null; upcoming_list?: { id: string; slug: string; time_start: string }[] } | null;
  cancelled_at: string | null;
  circle_peers?: { member_id: string; display_name: string; avatar: string | null }[];
  thread_access?: boolean;
  was_there?: boolean;
};

const CATEGORY_ICON: Record<string, string> = { play: '🏸', meet: '☕', eat: '🍛', learn: '📚', work: '💼', explore: '🥾', celebrate: '🎉', help: '🤝' };
const NOTIF_KEY = 'milavn.notifPrimed';

export default function DetailClient({ slug, initial }: { slug: string; initial: PublicPage | null }) {
  const { t, i18n } = useTranslation();
  const router = useRouter();
  const { ready, identity } = useIdentity();
  const [pub, setPub] = useState<PublicPage | null>(initial);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [status, setStatus] = useState<string | null>(initial?.rsvp_cta.viewer_status ?? null);
  const [waitPos, setWaitPos] = useState<number | null>(null);
  const [going, setGoing] = useState(initial?.card.going_count ?? 0);
  const [busy, setBusy] = useState(false);
  const [pop, setPop] = useState(false);
  const [error, setError] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [trustOpen, setTrustOpen] = useState(false);
  const [share, setShare] = useState(false);
  const [menu, setMenu] = useState(false);
  const [report, setReport] = useState(false);
  const [reason, setReason] = useState('spam');
  const [reportText, setReportText] = useState('');
  const [blockAsk, setBlockAsk] = useState(false);
  const [notifAsk, setNotifAsk] = useState(false);
  const [feedback, setFeedback] = useState<{ eligible: boolean; already_submitted: boolean } | null>(null);
  const [rating, setRating] = useState<number | null>(null);
  const [fbText, setFbText] = useState('');
  const [icsHref, setIcsHref] = useState<string | null>(null);

  const say = (m: string) => { setToast(m); setTimeout(() => setToast(null), 2200); };

  const loadAuth = useCallback(async () => {
    try {
      const d = await api<Detail>(`/occurrences/by-slug/${encodeURIComponent(slug)}`);
      setDetail(d); setStatus(d.viewer_status); setGoing(d.going_count); setError(false);
      if (['attended', 'checked_in'].includes(d.viewer_status ?? '')) api<{ eligible: boolean; already_submitted: boolean }>(`/feedback/prompt/${d.id}`).then(setFeedback).catch(() => undefined);
    } catch (e) {
      if (!pub) setError(true);
    }
  }, [slug, pub]);

  useEffect(() => { if (ready && identity) void loadAuth(); }, [ready, identity, loadAuth]);

  // [FR018] Scanned the organizer's QR (URL carries ?checkin=<token>): redeem once, then clean the URL.
  useEffect(() => {
    if (!ready || !identity || !detail) return;
    const params = new URLSearchParams(window.location.search);
    const token = params.get('checkin');
    if (!token) return;
    window.history.replaceState(null, '', window.location.pathname);
    api<{ status: string }>(`/occurrences/${detail.id}/checkin`, { body: { token } })
      .then(() => { setStatus('checked_in'); say(`✓ ${t('card.youAre.checked_in')}`); })
      .catch((e) => say(e instanceof ApiError ? e.message : t('state.error')));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, identity, detail?.id]);

  const card: Card | null = detail ?? pub?.card ?? null;
  const organizer = detail?.organizer ?? pub?.organizer ?? null;
  const description = detail?.description ?? pub?.description ?? null;

  useEffect(() => {
    if (!card) return;
    const ics = buildIcs({ uid: card.id, title: card.title, start: card.time_start, location: card.location_label, description: description ?? undefined, url: `${window.location.origin}/a/${card.slug}` });
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setIcsHref(icsDataUrl(ics));
  }, [card?.id, card?.time_start, card?.title, card?.location_label, description]); // eslint-disable-line react-hooks/exhaustive-deps
  const safety = detail?.safety_guidelines ?? pub?.safety_guidelines ?? [];
  const isOrganizer = detail?.viewer_role === 'organizer' || detail?.viewer_role === 'co_organizer';
  const cancelled = card?.status === 'cancelled';
  const rsvpd = !!status && !['cancelled', 'no_show'].includes(status);

  const setRsvp = async (desired: 'interested' | 'going' | 'cancelled') => {
    if (!card || busy) return;
    const prev = status;
    setBusy(true); setStatus(desired === 'cancelled' ? null : desired); setPop(true); setTimeout(() => setPop(false), 350);
    try {
      const r = await api<{ status: string; waitlist_position: number | null; going_count: number; message: string | null }>(`/occurrences/${card.id}/participation`, { body: { status: desired }, idempotent: true });
      setStatus(r.status === 'cancelled' ? null : r.status); setWaitPos(r.waitlist_position); setGoing(r.going_count);
      if (r.message) say(r.message);
      if (desired === 'going' && r.status !== 'cancelled') {
        let primed = false; try { primed = localStorage.getItem(NOTIF_KEY) === '1'; } catch { /* ignore */ }
        if (!primed) setNotifAsk(true);
      }
    } catch (e) {
      setStatus(prev);
      say(e instanceof ApiError ? e.message : t('state.error'));
    } finally { setBusy(false); }
  };

  const primeNotifications = async (yes: boolean) => {
    try { localStorage.setItem(NOTIF_KEY, '1'); } catch { /* ignore */ }
    setNotifAsk(false);
    if (yes && typeof Notification !== 'undefined' && Notification.permission === 'default') {
      try { await Notification.requestPermission(); } catch { /* denial is fine — inbox still works (FR082) */ }
    }
  };

  const sharePoster = async () => {
    if (!card) return;
    const url = `${window.location.origin}/a/${card.slug}`;
    const blob = await renderPoster({ title: card.title, when: formatDateLong(card.time_start, i18n.language), place: card.location_label, host: card.host_name, url, coverUrl: resolveMediaUrl(card.cover_image_url) ?? null, category: card.category_label, trustLabel: card.trust_label });
    if (!blob) { say(t('state.error')); return; }
    const file = new File([blob], `${card.slug}.png`, { type: 'image/png' });
    const nav = navigator as Navigator & { canShare?: (d: { files: File[] }) => boolean };
    if (nav.share && nav.canShare?.({ files: [file] })) { try { await nav.share({ files: [file], title: card.title, url }); return; } catch { /* cancelled */ } }
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = file.name; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 4000);
    say(t('detail.posterSaved'));
  };

  const doShare = async (channel: string) => {
    if (!card) return;
    const url = `${window.location.origin}/a/${card.slug}`;
    const text = pub?.share.text ?? `${card.title} — ${card.location_label}. Join me on Milavn.`;
    if (channel === 'native' && navigator.share) { try { await navigator.share({ title: card.title, text, url }); } catch { /* cancelled */ } return; }
    if (channel === 'copy' || channel === 'instagram') { await navigator.clipboard?.writeText(url); say(t('create.copied')); return; }
    const targets: Record<string, string> = {
      whatsapp: `https://wa.me/?text=${encodeURIComponent(`${text} ${url}`)}`,
      sms: `sms:?&body=${encodeURIComponent(`${text} ${url}`)}`,
      email: `mailto:?subject=${encodeURIComponent(card.title)}&body=${encodeURIComponent(`${text}\n${url}`)}`,
    };
    if (targets[channel]) window.open(targets[channel], '_blank', 'noopener');
  };

  const submitReport = async () => {
    if (!card) return;
    try {
      await api('/safety/reports', { body: { subject_type: 'occurrence', subject_id: card.id, reason_category: reason, description: reportText }, idempotent: true });
      setReport(false); setReportText(''); say(t('safety.submitted'));
    } catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  const doBlock = async () => {
    if (!organizer) return;
    try { await api('/safety/blocks', { body: { member_id: organizer.member_id } }); setBlockAsk(false); say(t('safety.blocked')); router.push('/'); }
    catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  const sendFeedback = async (skip: boolean) => {
    if (!card) return;
    if (skip) { setFeedback(null); return; }
    try { await api('/feedback', { body: { occurrence_id: card.id, rating, comments: fbText }, idempotent: true }); setFeedback(null); say(t('detail.feedbackThanks')); }
    catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  if (!card) {
    return <main className="screen">{error ? <ErrorState onRetry={loadAuth} /> : <CardSkeleton count={1} />}</main>;
  }


  const rsvpControls = identity && !cancelled ? (
    status === 'going' || status === 'waitlisted' || status === 'checked_in' || status === 'attended' ? (
      <button className={`btn btn--primary btn--spring grow${pop ? ' pop' : ''}`} aria-live="polite" onClick={() => setRsvp('cancelled')} disabled={busy}>✓ {status === 'waitlisted' ? t('card.youAre.waitlisted') : t('detail.youreGoing')} · {t('detail.withdraw')}</button>
    ) : (
      <>
        <button className={`btn btn--secondary btn--spring grow${pop && status === 'interested' ? ' pop' : ''}`} aria-pressed={status === 'interested'} onClick={() => setRsvp(status === 'interested' ? 'cancelled' : 'interested')} disabled={busy}>{status === 'interested' ? '✓ ' : ''}{t('detail.interested')}</button>
        <button className={`btn btn--primary btn--glow btn--spring grow${pop && status === 'going' ? ' pop' : ''}`} onClick={() => setRsvp('going')} disabled={busy}>{t('detail.going')}</button>
      </>
    )
  ) : null;

  return (
    <>
      {card.cover_image_url && <div className="backdrop" aria-hidden="true" style={{ backgroundImage: `url(${resolveMediaUrl(card.cover_image_url) ?? ''})` }} />}
      <div className="detail__wrap">
      <div className="hero">
        {card.cover_image_url && <img src={resolveMediaUrl(card.cover_image_url) ?? ''} alt={`${card.category_label}: ${card.title} in ${card.location_label}`} />}
        <div className="hero__top">
          <button className="icon-btn" aria-label={t('common.back')} onClick={() => (history.length > 1 ? router.back() : router.push('/'))}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M15 6l-6 6 6 6" /></svg>
          </button>
          {identity && (
            <button className="icon-btn" aria-label="More" onClick={() => setMenu(true)}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><circle cx="5" cy="12" r="2" /><circle cx="12" cy="12" r="2" /><circle cx="19" cy="12" r="2" /></svg>
            </button>
          )}
        </div>
        <div className="hero__title">
          <span className="pill" style={{ background: 'rgba(255,255,255,0.18)', color: '#fff', backdropFilter: 'blur(4px)' }}>{CATEGORY_ICON[card.intent_category]} {card.category_label}{card.is_recurring ? ` · ${t('card.recurring')}` : ''}</span>
          <h1>{card.title}</h1>
        </div>
      </div>
      </div>

      <div className="detail__grid">
      <main className={`screen${identity ? ' has-footer' : ''}`}>
        {cancelled && <div className="pill pill--danger" style={{ alignSelf: 'flex-start' }}>{t('detail.cancelledBanner')}</div>}
        {rsvpd && !cancelled && (
          <div className="pill pill--trust" style={{ alignSelf: 'flex-start' }}>
            {status === 'going' ? t('detail.youreGoing') : status === 'waitlisted' ? t('detail.waitlisted', { n: waitPos ?? '' }) : status === 'interested' ? t('detail.youreInterested') : t(`card.youAre.${status}`)}
          </div>
        )}

        <div className="stack" style={{ gap: 8 }}>
          <div className="datetile">
            <span className="datetile__day"><small>{new Intl.DateTimeFormat(i18n.language === 'hi' ? 'hi-IN' : i18n.language === 'te' ? 'te-IN' : 'en-IN', { timeZone: 'Asia/Kolkata', month: 'short' }).format(new Date(card.time_start))}</small><b>{new Intl.DateTimeFormat('en-IN', { timeZone: 'Asia/Kolkata', day: 'numeric' }).format(new Date(card.time_start))}</b></span>
            <span><div className="title">{formatDateLong(card.time_start, i18n.language)}</div><div className="caption">{card.category_label}{card.is_recurring ? ` · ${t('card.recurring')}` : ''}</div></span>
          </div>
          <div className="muted">
            {card.location_label}{card.distance_label ? ` · ${card.distance_label}` : ''}
            {rsvpd && status === 'going' && (
              <> · <a className="link" href={`https://www.google.com/maps/search/${encodeURIComponent(`${card.location_label}, ${card.location_label}`)}`} target="_blank" rel="noopener">{t('detail.directions')}</a></>
            )}
          </div>
          <div className="row" style={{ gap: 12 }}>
            {going === 0 && !cancelled ? <strong style={{ color: 'var(--accent-pressed)' }}>{t('detail.beFirst')}</strong> : <strong>{t('card.going', { count: going })}</strong>}
            {card.interested_count > 0 && <span className="muted">{t('card.interested', { count: card.interested_count })}</span>}
            {card.capacity !== null && <span className="pill pill--neutral">{going >= card.capacity ? t('card.full') : t('card.spotsLeft', { count: card.capacity - going })}</span>}
          </div>
          <span className="caption">{t('detail.attendeesPrivate')}</span>
          {card.why_reason && identity && (
            <span className="whyline" style={{ marginTop: 4 }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M12 3l2.5 5.5L20 9.5l-4 4 1 5.5-5-2.7-5 2.7 1-5.5-4-4 5.5-1z" /></svg>
              <span><span className="caption">{t('detail.whyThis')}: </span>{card.why_reason}</span>
            </span>
          )}
        </div>

        {card.lat !== null && card.lng !== null && (
          <section className="stack" style={{ gap: 8 }}>
            <div className="row row--between">
              <span className="label">{t('detail.where')}</span>
              {icsHref && <a className="link caption" href={icsHref} download={`${card.slug}.ics`}>📅 {t('detail.addToCalendar')}</a>}
            </div>
            <a href={`https://www.google.com/maps/search/${encodeURIComponent(card.location_label)}`} target="_blank" rel="noopener" aria-label={t('detail.directions')} style={{ display: 'block' }}>
              <MiniMap lat={card.lat} lng={card.lng} label={card.location_label} />
            </a>
          </section>
        )}

        {detail?.circle_peers && detail.circle_peers.length > 0 && (
          <section className="stack fade-in" style={{ gap: 8 }}>
            <span className="label">{t('detail.circleMates')}</span>
            <div className="row" style={{ gap: 10, flexWrap: 'wrap' }}>
              <span className="avatar-stack">
                {detail.circle_peers.slice(0, 5).map((m) => m.avatar ? <img key={m.member_id} className="avatar avatar--lg" src={resolveMediaUrl(m.avatar) ?? ''} alt="" /> : <span key={m.member_id} className="avatar avatar--lg" />)}
              </span>
              <span className="caption">{detail.circle_peers.map((m, i) => <span key={m.member_id}>{i > 0 ? ', ' : ''}<Link href={`/p/${m.member_id}`} className="link">{m.display_name}</Link></span>)} {t('detail.circleMatesGoing', { count: detail.circle_peers.length })}</span>
            </div>
          </section>
        )}

        {organizer && (
          <section className="card stack" style={{ gap: 10 }}>
            <span className="label">{t('detail.organizer')}</span>
            <div className="row" style={{ gap: 12 }}>
              {organizer.avatar ? <img className="avatar avatar--lg" src={resolveMediaUrl(organizer.avatar) ?? ''} alt="" /> : <span className="avatar avatar--lg" />}
              <div className="grow">
                <Link href={`/p/${organizer.member_id}`} className="title" style={{ display: 'block' }}>{organizer.display_name} <span className="muted" aria-hidden="true">›</span></Link>
                <div className="caption">{organizer.reputation.join(' · ')}</div>
              </div>
            </div>
            <button className="row" style={{ background: 'none', border: 0, padding: 0, gap: 8, textAlign: 'left' }} aria-expanded={trustOpen} aria-controls="trust-panel" onClick={() => setTrustOpen((v) => !v)}>
              <TrustPill level={card.trust_level} label={card.trust_label} positive={card.trust_positive} />
              <span className="caption">{t('detail.trustWhy')} {trustOpen ? '▴' : '▾'}</span>
            </button>
            {trustOpen && <p id="trust-panel" className="caption fade-in" style={{ margin: 0, padding: 12, background: 'var(--surface-sunken)', borderRadius: 12 }}>{t(`detail.trustExplain.${card.trust_level}`)}</p>}
          </section>
        )}

        {description && (
          <section className="stack" style={{ gap: 6 }}>
            <span className="label">{t('detail.about')}</span>
            <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{description}</p>
          </section>
        )}

        {detail?.thread_access && <Thread occurrenceId={card.id} onError={say} />}
        {detail?.thread_access && <Moments occurrenceId={card.id} onError={say} />}

        {detail?.announcements && detail.announcements.length > 0 && (
          <section className="stack" style={{ gap: 8 }}>
            <span className="label">{t('detail.announcements')}</span>
            {detail.announcements.map((a) => (
              <div key={a.id} className="card" style={{ padding: 12 }}>
                <p style={{ margin: 0 }}>{a.message}</p>
                <span className="caption">{a.by} · {formatRelative(a.created_at)}</span>
              </div>
            ))}
          </section>
        )}

        {safety.length > 0 && (
          <section className="card stack" style={{ gap: 8, borderColor: 'var(--accent-primary)' }}>
            <span className="label" style={{ color: 'var(--accent-pressed)' }}>{t('detail.safety')}</span>
            <p style={{ margin: 0 }} className="caption">{t('detail.safetyIntro')}</p>
            <ul style={{ margin: 0, paddingLeft: 18 }}>{safety.map((s) => <li key={s}>{s}</li>)}</ul>
          </section>
        )}

        {(detail?.series ?? pub?.series) && (
          <section className="stack" style={{ gap: 8 }}>
            <span className="label">{t('detail.series')}</span>
            <div className="row">
              <div className="stat"><b>{(detail?.series ?? pub?.series)?.held ?? 0}</b><span>{t('detail.seriesHeld', { held: '' }).trim()}</span></div>
              <div className="stat"><b>{(detail?.series ?? pub?.series)?.upcoming ?? 0}</b><span>{t('detail.seriesUpcoming', { upcoming: '' }).trim()}</span></div>
            </div>
            {detail?.series?.upcoming_list && detail.series.upcoming_list.length > 0 && (
              <div className="chips chips--scroll">
                {detail.series.upcoming_list.map((u) => <Link key={u.id} href={`/a/${u.slug}`} className="chip chip--sm">{formatDateLong(u.time_start, i18n.language)}</Link>)}
              </div>
            )}
          </section>
        )}

        {feedback?.eligible && !feedback.already_submitted && (
          <section className="card stack fade-in" style={{ gap: 10 }}>
            <div className="title">{t('detail.feedbackPrompt')}</div>
            <span className="caption">{t('detail.feedbackBody')}</span>
            <div className="row" role="radiogroup" aria-label={t('detail.feedbackPrompt')}>
              {[1, 2, 3, 4, 5].map((n) => <button key={n} className="chip chip--sm" aria-pressed={rating === n} onClick={() => setRating(n)}>{n}</button>)}
            </div>
            <label className="field"><textarea placeholder="…" value={fbText} onChange={(e) => setFbText(e.target.value)} /></label>
            <div className="row"><button className="btn btn--ghost" onClick={() => sendFeedback(true)}>{t('detail.feedbackSkip')}</button><button className="btn btn--primary grow" onClick={() => sendFeedback(false)}>{t('detail.feedbackSend')}</button></div>
          </section>
        )}

        {isOrganizer && <Link href={`/organizer/${card.id}`} className="btn btn--secondary btn--block">{t('detail.manage')}</Link>}
        {!identity && ready && <Link href="/welcome" className="btn btn--primary btn--block">{t('detail.loginToRsvp')}</Link>}
      </main>

      <aside className="detail__aside">
        <div className="detail__card card glass">
          <div className="stack" style={{ gap: 4 }}>
            <div className="title">{formatDateLong(card.time_start, i18n.language)}</div>
            <div className="muted">{card.location_label}{card.distance_label ? ` · ${card.distance_label}` : ''}</div>
            <div className="row" style={{ gap: 10 }}>
              {going === 0 && !cancelled ? <strong style={{ color: 'var(--accent-pressed)' }}>{t('detail.beFirst')}</strong> : <strong>{t('card.going', { count: going })}</strong>}
              {card.capacity !== null && <span className="pill pill--neutral">{going >= card.capacity ? t('card.full') : t('card.spotsLeft', { count: card.capacity - going })}</span>}
            </div>
          </div>
          {rsvpControls && <div className="row" style={{ gap: 10 }}>{rsvpControls}</div>}
          {cancelled && <div className="pill pill--danger" style={{ alignSelf: 'flex-start' }}>{t('detail.cancelledBanner')}</div>}
          {!identity && ready && <Link href="/welcome" className="btn btn--primary btn--block">{t('detail.loginToRsvp')}</Link>}
          <div className="row" style={{ gap: 8 }}>
            {identity && <button className="btn btn--secondary btn--sm grow" onClick={() => setShare(true)}>{t('detail.share')}</button>}
            {icsHref && <a className="btn btn--secondary btn--sm grow" href={icsHref} download={`${card.slug}.ics`}>📅 {t('detail.addToCalendar')}</a>}
          </div>
          {organizer && (
            <Link href={`/p/${organizer.member_id}`} className="row" style={{ gap: 10 }}>
              {organizer.avatar ? <img className="avatar avatar--lg" src={resolveMediaUrl(organizer.avatar) ?? ''} alt="" /> : <span className="avatar avatar--lg" />}
              <span className="grow"><span className="caption">{t('detail.organizer')}</span><br /><b>{organizer.display_name}</b></span>
            </Link>
          )}
        </div>
      </aside>
      </div>

      {identity && !cancelled && (
        <div className="footer-sticky">
          {rsvpControls}
          <button className="icon-btn" aria-label={t('detail.share')} onClick={() => setShare(true)}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path d="M12 3v12M7 8l5-5 5 5M5 14v5a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-5" /></svg>
          </button>
        </div>
      )}

      <Sheet open={share} onClose={() => setShare(false)} label={t('detail.share')}>
        <div className="stack">
          <h2 className="h2">{t('detail.share')}</h2>
          <div className="grid-2">
            {typeof navigator !== 'undefined' && 'share' in navigator && <button className="btn btn--primary" onClick={() => doShare('native')}>Share…</button>}
            <button className="btn btn--primary" onClick={sharePoster}>🖼️ {t('detail.posterShare')}</button>
            <button className="btn btn--secondary" onClick={() => doShare('whatsapp')}>WhatsApp</button>
            <button className="btn btn--secondary" onClick={() => doShare('sms')}>SMS</button>
            <button className="btn btn--secondary" onClick={() => doShare('email')}>Email</button>
            <button className="btn btn--secondary" onClick={() => doShare('instagram')}>Instagram (copy)</button>
            <button className="btn btn--secondary" onClick={() => doShare('copy')}>{t('common.copy')}</button>
          </div>
          {share && <QrCode value={`${window.location.origin}/a/${card.slug}`} size={180} label="QR code for this activity" />}
        </div>
      </Sheet>

      <Sheet open={menu} onClose={() => setMenu(false)} label="More">
        <div className="stack">
          {isOrganizer && <Link href={`/organizer/${card.id}`} className="btn btn--secondary btn--block" onClick={() => setMenu(false)}>{t('detail.manage')}</Link>}
          <button className="btn btn--secondary btn--block" onClick={() => { setMenu(false); setReport(true); }}>{t('detail.report')}</button>
          {organizer && organizer.member_id !== identity?.member_id && <button className="btn btn--danger-outline btn--block" onClick={() => { setMenu(false); setBlockAsk(true); }}>{t('safety.block', { name: organizer.display_name })}</button>}
        </div>
      </Sheet>

      <Sheet open={report} onClose={() => setReport(false)} label={t('safety.reportTitle')}>
        <div className="stack">
          <h2 className="h2">{t('safety.reportTitle')}</h2>
          <p className="caption" style={{ margin: 0 }}>{t('safety.reportBody')}</p>
          <div className="chips">{['spam', 'unsafe', 'harassment', 'misleading', 'other'].map((r) => <button key={r} className="chip chip--sm" aria-pressed={reason === r} onClick={() => setReason(r)}>{t(`safety.reasons.${r}`)}</button>)}</div>
          <label className="field"><span className="field__label">{t('safety.details')}</span><textarea value={reportText} onChange={(e) => setReportText(e.target.value)} /></label>
          <button className="btn btn--danger btn--block" onClick={submitReport}>{t('safety.submit')}</button>
        </div>
      </Sheet>

      <Modal open={blockAsk} onClose={() => setBlockAsk(false)} label={t('safety.block', { name: organizer?.display_name ?? '' })}>
        <div className="stack">
          <h2 className="h2">{t('safety.block', { name: organizer?.display_name ?? '' })}</h2>
          <p className="muted" style={{ margin: 0 }}>{t('safety.blockBody')}</p>
          <div className="row"><button className="btn btn--ghost grow" onClick={() => setBlockAsk(false)}>{t('common.cancel')}</button><button className="btn btn--danger grow" onClick={doBlock}>{t('safety.blockConfirm')}</button></div>
        </div>
      </Modal>

      {notifAsk && (
        <div className="prime fade-in" role="dialog" aria-label={t('detail.notifyPrompt')}>
          <span className="grow">🔔 {t('detail.notifyPrompt')}</span>
          <button className="btn btn--sm btn--primary" onClick={() => primeNotifications(true)}>{t('detail.notifyYes')}</button>
          <button className="btn btn--sm btn--ghost" onClick={() => primeNotifications(false)}>{t('detail.notifyNo')}</button>
        </div>
      )}
      <Toast text={toast} />
    </>
  );
}

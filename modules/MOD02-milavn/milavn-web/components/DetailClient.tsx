'use client';

/* Activity/Event Detail (UX06/UI06) + RSVP toggle (UX08/UI08) + share sheet
 * (FR049) + report (FR061) + block (FR062) + feedback prompt (FR066) +
 * notification priming on first "Going" (FR082) + safety block (FR064) +
 * organizer identity/location once RSVP'd (FR063). Renders from the
 * server-fetched public contract first (FR047), then enriches with the
 * authenticated detail when a member is present. */

import dynamic from 'next/dynamic';
import Link from 'next/link';

import { entranceSignInUrl } from '@/lib/platform';
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
import { appUrl } from '@/lib/base-path';
import { formatDateLong, formatInr, formatRelative, formatWhen } from '@/lib/format';
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
  series: { held: number; upcoming: number; recurrence_rule: Record<string, string> | null; upcoming_list?: { id: string; slug: string; time_start: string }[]; regular?: boolean; my_recent?: { attended: number; total: number } } | null;
  cancelled_at: string | null;
  circle_peers?: { member_id: string; display_name: string; avatar: string | null }[];
  thread_access?: boolean;
  was_there?: boolean;
  my_plan?: { travel: string | null; company: string | null; confirmed_at: string | null } | null;
  still_coming_due?: boolean;
  max_guests_per_member?: number; // [FR114] what the host allows
  my_guests?: number; // how many I am bringing
  guest_total?: number; // how many guests altogether
  first_time?: boolean;
  thanked?: boolean;
};

// FR107: one-tap thank-you presets (the attendee can also write their own).
const THANKS_PRESETS = ['organizing', 'loved', 'group', 'next'] as const;
const TELANGANA_CITIES = /hyderabad|secunderabad|warangal|karimnagar|nizamabad|khammam/i;

// FR105: one tap each, optional; repeated back in the reminder before it starts.
const TRAVEL = ['walk', 'two_wheeler', 'car', 'cab_auto', 'metro_bus'] as const;
const COMPANY = ['alone', 'friend', 'family'] as const;

// FR102 paid spots: what the member needs to decide and to know where they stand.
type TicketInfo = {
  price_paise: number | null; refund_cutoff_hours: number; refund_deadline: string; refund_if_withdraw_now_paise: number; payments_available: boolean;
  ticket: { kind: string; status: string; amount_paise: number; checkout_url: string | null; hold_active: boolean; hold_expires_at: string | null; refund_amount_paise: number | null } | null;
};

const CATEGORY_ICON: Record<string, string> ={ play: '🏸', meet: '☕', eat: '🍛', learn: '📚', work: '💼', explore: '🥾', celebrate: '🎉', help: '🤝' };
const NOTIF_KEY = 'milavn.notifPrimed';

export default function DetailClient({ slug, initial }: { slug: string; initial: PublicPage | null }) {
  const { t, i18n } = useTranslation();
  const router = useRouter();
  const { ready, identity, profile } = useIdentity();
  const [pub, setPub] = useState<PublicPage | null>(initial);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [status, setStatus] = useState<string | null>(initial?.rsvp_cta.viewer_status ?? null);
  const [waitPos, setWaitPos] = useState<number | null>(null);
  const [going, setGoing] = useState(initial?.card.going_count ?? 0);
  // [FR114] Spots left is counted on the server (guests take spots too) — never re-derived here.
  const [spotsLeft, setSpotsLeft] = useState<number | null>(initial?.card.spots_left ?? null);
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
  const [comeAgain, setComeAgain] = useState<'yes' | 'maybe' | 'no' | null>(null);
  const [thanksSent, setThanksSent] = useState(false);
  const [thanksText, setThanksText] = useState('');
  const [fbText, setFbText] = useState('');
  const [icsHref, setIcsHref] = useState<string | null>(null);
  const [pay, setPay] = useState<TicketInfo | null>(null);
  const [payAsk, setPayAsk] = useState(false);
  const [planEdit, setPlanEdit] = useState(false);
  const [hideAsk, setHideAsk] = useState(false);

  const say = (m: string) => { setToast(m); setTimeout(() => setToast(null), 2200); };

  const loadTicket = useCallback(async (occurrenceId: string) => {
    try { setPay(await api<TicketInfo>(`/occurrences/${occurrenceId}/ticket`)); } catch { /* the price still shows from the card */ }
  }, []);

  const loadAuth = useCallback(async () => {
    try {
      const d = await api<Detail>(`/occurrences/by-slug/${encodeURIComponent(slug)}`);
      setDetail(d); setStatus(d.viewer_status); setGoing(d.going_count); setSpotsLeft(d.spots_left ?? null); setError(false);
      if (d.price_paise != null) void loadTicket(d.id);
      if (['attended', 'checked_in'].includes(d.viewer_status ?? '')) api<{ eligible: boolean; already_submitted: boolean }>(`/feedback/prompt/${d.id}`).then(setFeedback).catch(() => undefined);
    } catch (e) {
      if (!pub) setError(true);
    }
  }, [slug, pub, loadTicket]);

  useEffect(() => { if (ready && identity) void loadAuth(); }, [ready, identity, loadAuth]);

  // [FR102] Back from checkout (?payment=return): confirmation arrives from Payment Services a moment later, so check a few times.
  useEffect(() => {
    if (!ready || !identity || !detail || detail.price_paise == null) return;
    if (new URLSearchParams(window.location.search).get('payment') !== 'return') return;
    window.history.replaceState(null, '', window.location.pathname);
    let tries = 0; let stopped = false;
    const check = async () => {
      if (stopped) return;
      try {
        const r = await api<TicketInfo>(`/occurrences/${detail.id}/ticket`);
        setPay(r);
        if (r.ticket?.status === 'paid') { setStatus('going'); say(t('pay.confirmed')); void loadAuth(); return; }
        if (r.ticket?.status === 'failed') { say(t('pay.failed')); return; }
      } catch { /* try again */ }
      tries += 1;
      if (tries < 6) setTimeout(check, 1500); else say(t('pay.pending'));
    };
    void check();
    return () => { stopped = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, identity, detail?.id]);

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
    const ics = buildIcs({ uid: card.id, title: card.title, start: card.time_start, location: card.location_label, description: description ?? undefined, url: appUrl(`/a/${card.slug}`) });
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
      const r = await api<{ status: string; waitlist_position: number | null; going_count: number; spots_left: number | null; message: string | null }>(`/occurrences/${card.id}/participation`, { body: { status: desired }, idempotent: true });
      setStatus(r.status === 'cancelled' ? null : r.status); setWaitPos(r.waitlist_position); setGoing(r.going_count); setSpotsLeft(r.spots_left ?? null);
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

  // [FR102] Paid activity: hold a spot and go to checkout, or join the waitlist when full.
  const joinPaid = async () => {
    if (!card || busy) return;
    setBusy(true);
    try {
      const r = await api<{ status: string; checkout_url: string | null; waitlist_position: number | null }>(`/occurrences/${card.id}/ticket`, { body: {}, idempotent: true });
      if (r.status === 'awaiting_payment' && r.checkout_url) { window.location.assign(r.checkout_url); return; }
      if (r.status === 'waitlisted') { setStatus('waitlisted'); setWaitPos(r.waitlist_position); say(t('pay.waitlisted')); }
      await loadTicket(card.id);
    } catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
    finally { setBusy(false); }
  };

  const withdrawPaid = async () => {
    if (!card) return;
    setPayAsk(false); setBusy(true);
    try {
      const r = await api<{ refund_paise: number; refund_status: string | null }>(`/occurrences/${card.id}/ticket/withdraw`, { body: {} });
      setStatus(null);
      say(r.refund_paise > 0 ? t('pay.refundStarted', { amount: formatInr(r.refund_paise, i18n.language) }) : t('pay.withdrawn'));
      await loadAuth();
    } catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
    finally { setBusy(false); }
  };

  // [FR105] Plan: how I'm getting there, who with. [FR103] Still coming? — or free the spot for someone waiting.
  const savePlan = async (next: { travel: string | null; company: string | null }) => {
    if (!card) return;
    try {
      const r = await api<{ travel: string | null; company: string | null; confirmed_at: string | null }>(`/occurrences/${card.id}/plan`, { method: 'PUT', body: next });
      setDetail((d) => (d ? { ...d, my_plan: r } : d));
      if (r.travel && r.company) setPlanEdit(false);
    } catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  const stillComing = async () => {
    if (!card) return;
    try {
      const r = await api<{ confirmed_at: string }>(`/occurrences/${card.id}/confirm`, { body: {} });
      setDetail((d) => (d ? { ...d, still_coming_due: false, my_plan: d.my_plan ? { ...d.my_plan, confirmed_at: r.confirmed_at } : d.my_plan } : d));
      say(t('show.thanksComing'));
    } catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  // [FR112] Keep a spot for me each time this series gets a new date (free series only; opt out any time).
  const setRegular = async (keep: boolean) => {
    if (!card) return;
    try {
      const r = await api<{ regular: boolean; kept: number }>(`/occurrences/${card.id}/regular`, { body: { keep } });
      say(keep ? t('regular.kept', { count: r.kept }) : t('regular.stopped'));
      await loadAuth();
    } catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  // [FR111] Not interested, with a reason: this activity (or this host, for 60 days) leaves my discovery.
  const hideThis = async (reason: 'not_my_thing' | 'too_far' | 'bad_time' | 'not_this_host') => {
    if (!card) return;
    try {
      await api('/discovery/hide', { body: { occurrence_id: card.id, reason } });
      setMenu(false); setHideAsk(false); say(t('fit.hidden'));
      setTimeout(() => router.push('/'), 900);
    } catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  // [FR107] A thank-you in the attendee's words; the host hears it once.
  const sendThanks = async (message: string) => {
    if (!card || !message.trim()) return;
    try {
      await api('/feedback/thanks', { body: { occurrence_id: card.id, message: message.trim() } });
      setThanksSent(true); setThanksText('');
      say(t('belong.thanksSent', { name: organizer?.display_name.split(' ')[0] ?? '' }));
    } catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  // [FR106] Would meet again: private picks among people who were there; both are told only when they pick each other.
  const [openedAt] = useState(() => Date.now());
  // [FR118] Conversation cards for the people who are there, around the time it happens.
  const [cards, setCards] = useState<string[] | null>(null);
  const [cardIndex, setCardIndex] = useState(0); // "has it ended?" is judged once per page view, not on every render
  type MeetPerson = { member_id: string; display_name: string; avatar: string | null; picked: boolean };
  const [meet, setMeet] = useState<MeetPerson[] | null>(null);
  const cardId = card?.id;
  const wasThere = ['attended', 'checked_in'].includes(status ?? '') || isOrganizer;
  useEffect(() => {
    if (!cardId || !wasThere) return;
    api<MeetPerson[]>(`/people/meet-again/${cardId}`).then(setMeet).catch(() => setMeet(null));
  }, [cardId, wasThere]);

  useEffect(() => {
    if (!cardId || !['going', 'checked_in', 'attended'].includes(status ?? '')) return;
    api<{ cards: string[]; active: boolean }>(`/occurrences/${cardId}/conversation-cards`)
      .then((r) => setCards(r.active ? r.cards : null))
      .catch(() => setCards(null));
  }, [cardId, status]);
  const toggleMeet = async (p: MeetPerson) => {
    if (!cardId) return;
    const pick = !p.picked;
    const flip = (v: boolean) => setMeet((cur) => (cur ?? []).map((x) => (x.member_id === p.member_id ? { ...x, picked: v } : x)));
    flip(pick);
    try {
      const r = await api<{ picked: boolean; mutual: boolean }>('/people/meet-again', { body: { occurrence_id: cardId, member_id: p.member_id, pick } });
      if (r.mutual) say(t('meet.mutual', { name: p.display_name.split(' ')[0] }));
    } catch (e) { flip(!pick); say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  // [FR114] Bringing someone: one tap, in place, and the spots update straight away.
  const setGuests = async (n: number) => {
    if (!card || !status) return;
    const before = detail?.my_guests ?? 0;
    setDetail((d) => (d ? { ...d, my_guests: n } : d));
    try {
      const r = await api<{ status: string; waitlist_position: number | null; going_count: number; spots_left: number | null; guests: number; message: string | null }>(
        `/occurrences/${card.id}/participation`,
        { body: { status, guests: n }, idempotent: true }
      );
      setStatus(r.status === 'cancelled' ? null : r.status);
      setWaitPos(r.waitlist_position);
      setGoing(r.going_count);
      setSpotsLeft(r.spots_left ?? null);
      setDetail((d) => (d ? { ...d, my_guests: r.guests, guest_total: (d.guest_total ?? 0) - before + r.guests } : d));
      if (r.message) say(r.message);
    } catch (e) {
      setDetail((d) => (d ? { ...d, my_guests: before } : d));
      say(e instanceof ApiError ? e.message : t('state.error'));
    }
  };

  // [FR109] Share my plan with family over WhatsApp: activity, when, locality, host — never a live location.
  const sharePlan = () => {
    if (!card) return;
    const when = formatDateLong(card.time_start, i18n.language);
    const hour = Number(new Intl.DateTimeFormat('en-IN', { timeZone: 'Asia/Kolkata', hour: 'numeric', hourCycle: 'h23' }).format(new Date(card.time_start)));
    const lines = [t('belong.planMessage', { title: card.title, when, place: card.location_label, host: organizer?.display_name.split(' ')[0] ?? '' }), appUrl(`/a/${card.slug}`)];
    if ((hour >= 18 || hour < 6) && TELANGANA_CITIES.test(profile?.locality_city ?? '')) lines.push(t('belong.tsafe'));
    window.open(`https://wa.me/?text=${encodeURIComponent(lines.join('\n'))}`, '_blank', 'noopener');
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
    const url = appUrl(`/a/${card.slug}`);
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
    const url = appUrl(`/a/${card.slug}`);
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
    try { await api('/feedback', { body: { occurrence_id: card.id, come_again: comeAgain, comments: fbText }, idempotent: true }); setFeedback(null); say(t('detail.feedbackThanks')); }
    catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  if (!card) {
    return <main className="screen">{error ? <ErrorState onRetry={loadAuth} /> : <CardSkeleton count={1} />}</main>;
  }


  const paidActivity = card.price_paise != null;
  // An activity has ended at its end time, or three hours after the start when no end was given (same rule as the chat context).
  const ended = openedAt >= (card.time_end ? Date.parse(card.time_end) : Date.parse(card.time_start) + 3 * 3600_000);
  const tk = pay?.ticket ?? null;
  const priceLabel = paidActivity ? formatInr(card.price_paise as number, i18n.language) : '';
  const paidControls = identity && !cancelled && paidActivity ? (
    status === 'checked_in' || status === 'attended' ? (
      <span className="btn btn--secondary grow" aria-live="polite">✓ {t(`card.youAre.${status}`)}</span>
    ) : ended ? (
      <span className="btn btn--ghost grow">{t('detail.ended')}</span>
    ) : tk?.status === 'paid' ? (
      <button className={`btn btn--primary btn--spring grow${pop ? ' pop' : ''}`} aria-live="polite" onClick={() => setPayAsk(true)} disabled={busy}>✓ {t('pay.youPaid', { amount: formatInr(tk.amount_paise, i18n.language) })} · {t('detail.withdraw')}</button>
    ) : tk?.hold_active ? (
      <>
        <button className="btn btn--primary btn--glow grow" onClick={() => (tk.checkout_url ? window.location.assign(tk.checkout_url) : void joinPaid())} disabled={busy}>
          {tk.kind === 'waitlist_offer' ? t('pay.claimSpot', { amount: priceLabel }) : t('pay.completePayment', { amount: priceLabel })}
        </button>
        <button className="btn btn--ghost" onClick={withdrawPaid} disabled={busy}>{t('pay.release')}</button>
      </>
    ) : status === 'waitlisted' ? (
      <button className="btn btn--secondary grow" onClick={withdrawPaid} disabled={busy}>✓ {t('card.youAre.waitlisted')} · {t('detail.withdraw')}</button>
    ) : (
      <button className="btn btn--primary btn--glow btn--spring grow" onClick={joinPaid} disabled={busy || pay?.payments_available === false}>{t('pay.join', { amount: priceLabel })}</button>
    )
  ) : null;

  const rsvpControls = paidActivity ? paidControls : identity && !cancelled ? (
    // You can't withdraw from something you were at, or join something that is over.
    status === 'checked_in' || status === 'attended' ? (
      <span className="btn btn--secondary grow" aria-live="polite">✓ {t(`card.youAre.${status}`)}</span>
    ) : ended ? (
      <span className="btn btn--ghost grow">{t('detail.ended')}</span>
    ) : status === 'going' || status === 'waitlisted' ? (
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

        {detail?.still_coming_due && status === 'going' && !cancelled && (
          <section className="card stack fade-in" style={{ gap: 10, borderColor: 'var(--accent-primary)' }} aria-label={t('show.stillComingTitle')}>
            <b className="title">{t('show.stillComingTitle')}</b>
            <span className="caption">{t('show.stillComingBody')}</span>
            <div className="row" style={{ gap: 8, flexWrap: 'wrap' }}>
              <button className="btn btn--primary grow" onClick={stillComing}>{t('show.stillComing')}</button>
              <button className="btn btn--secondary grow" onClick={() => (paidActivity && tk?.status === 'paid' ? setPayAsk(true) : void setRsvp('cancelled'))}>{t('show.freeSpot')}</button>
            </div>
          </section>
        )}
        {(detail?.max_guests_per_member ?? 0) > 0 && (status === 'going' || status === 'waitlisted') && !cancelled && !ended && (
          <section className="card stack fade-in" style={{ gap: 8 }}>
            <div className="title">{t('guest.bringingTitle')}</div>
            <span className="caption">{t('guest.bringingBody')}</span>
            <div className="chips" role="radiogroup" aria-label={t('guest.bringingTitle')}>
              {Array.from({ length: (detail?.max_guests_per_member ?? 0) + 1 }, (_, n) => (
                <button key={n} type="button" className="chip chip--sm" aria-pressed={(detail?.my_guests ?? 0) === n} onClick={() => setGuests(n)}>
                  {n === 0 ? t('guest.justMe') : t('guest.plusN', { count: n })}
                </button>
              ))}
            </div>
          </section>
        )}

        {detail?.my_plan && (status === 'going' || status === 'waitlisted') && !cancelled && (
          detail.my_plan.travel && detail.my_plan.company && !planEdit ? (
            <div className="caption" style={{ alignSelf: 'flex-start' }}>
              {t('show.yourPlan')}: {t(`show.travel.${detail.my_plan.travel}`)} · {t(`show.company.${detail.my_plan.company}`)} · <button className="link" onClick={() => setPlanEdit(true)}>{t('show.change')}</button>
            </div>
          ) : (
            <section className="card stack fade-in" style={{ gap: 10 }}>
              <b>{t('show.howGetting')}</b>
              <div className="chips">
                {TRAVEL.map((v) => <button key={v} type="button" className="chip chip--sm" aria-pressed={detail.my_plan?.travel === v} onClick={() => savePlan({ travel: detail.my_plan?.travel === v ? null : v, company: detail.my_plan?.company ?? null })}>{t(`show.travel.${v}`)}</button>)}
              </div>
              <b>{t('show.comingWith')}</b>
              <div className="chips">
                {COMPANY.map((v) => <button key={v} type="button" className="chip chip--sm" aria-pressed={detail.my_plan?.company === v} onClick={() => savePlan({ travel: detail.my_plan?.travel ?? null, company: detail.my_plan?.company === v ? null : v })}>{t(`show.company.${v}`)}</button>)}
              </div>
              <span className="caption">{t('show.planPrivacy')}</span>
            </section>
          )
        )}

        {detail?.first_time && status === 'going' && !cancelled && (
          <section className="card stack fade-in" style={{ gap: 6 }}>
            <b>{t('belong.firstTitle')}</b>
            <span className="caption">{t('belong.firstBody', { host: organizer?.display_name.split(' ')[0] ?? '', place: card.location_label })}</span>
          </section>
        )}
        {status === 'going' && !cancelled && (
          <button type="button" className="btn btn--secondary btn--sm" style={{ alignSelf: 'flex-start' }} onClick={sharePlan}>{t('belong.sharePlan')}</button>
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
            {ended ? <strong>{t('detail.wentCount', { count: going })}</strong> : going === 0 && !cancelled ? <strong style={{ color: 'var(--accent-pressed)' }}>{t('detail.beFirst')}</strong> : <strong>{t('card.going', { count: going })}</strong>}
            {(detail?.guest_total ?? 0) > 0 && <span className="muted">{t('guest.total', { count: detail?.guest_total ?? 0 })}</span>}
            {!ended && card.interested_count > 0 && <span className="muted">{t('card.interested', { count: card.interested_count })}</span>}
            {!ended && card.capacity !== null && spotsLeft !== null && <span className="pill pill--neutral">{spotsLeft > 0 ? t('card.spotsLeft', { count: spotsLeft }) : t('card.full')}</span>}
          </div>
          <span className="caption">{t(ended ? 'detail.attendeesPrivatePast' : 'detail.attendeesPrivate')}</span>
          {paidActivity && (
            <div className="paynote">
              <b>{t('pay.pricePerPersonValue', { amount: priceLabel })}</b>
              {pay && <span className="caption">{pay.refund_cutoff_hours === 0 ? t('pay.refundUntilStart') : t('pay.refundUntil', { time: formatDateLong(pay.refund_deadline, i18n.language) })}</span>}
              {tk?.hold_active && tk.hold_expires_at && <span className="caption">{t('pay.heldUntil', { time: formatWhen(tk.hold_expires_at, i18n.language) })}</span>}
              {tk?.status === 'refund_pending' && <span className="pill pill--neutral" style={{ alignSelf: 'flex-start' }}>{t('pay.refundPending', { amount: formatInr(tk.refund_amount_paise ?? tk.amount_paise, i18n.language) })}</span>}
              {tk?.status === 'refunded' && <span className="pill pill--trust" style={{ alignSelf: 'flex-start' }}>{t('pay.refunded', { amount: formatInr(tk.refund_amount_paise ?? tk.amount_paise, i18n.language) })}</span>}
              {pay && !pay.payments_available && <span className="caption">{t('pay.notOpenYet')}</span>}
            </div>
          )}
          {((card.audience_tags?.length ?? 0) > 0 || (card.food_tags?.length ?? 0) > 0) && (
            <div className="chips" aria-label={t('fit.whoFor')}>
              {(card.audience_tags ?? []).map((a) => <span key={a} className="pill pill--trust">{t(`fit.audience.${a}`)}</span>)}
              {(card.food_tags ?? []).map((f) => <span key={f} className="pill pill--neutral">{t(`fit.food.${f}`)}</span>)}
            </div>
          )}
          {card.why_reason && identity && !ended && (
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
              <span className="caption">{detail.circle_peers.map((m, i) => <span key={m.member_id}>{i > 0 ? ', ' : ''}<Link href={`/p/${m.member_id}`} className="link">{m.display_name}</Link></span>)} {t(ended ? 'detail.circleMatesWent' : 'detail.circleMatesGoing', { count: detail.circle_peers.length })}</span>
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
            {detail?.series && identity && !isOrganizer && (
              <div className="stack" style={{ gap: 6 }}>
                {(detail.series.my_recent?.total ?? 0) > 0 && (detail.series.my_recent?.attended ?? 0) > 0 && (
                  <span className="caption">{t('regular.recent', { attended: detail.series.my_recent?.attended, total: detail.series.my_recent?.total })}</span>
                )}
                {detail.series.regular ? (
                  <>
                    <span className="caption">{t('regular.on')}</span>
                    <button className="link" style={{ alignSelf: 'flex-start' }} onClick={() => setRegular(false)}>{t('regular.stop')}</button>
                  </>
                ) : card.price_paise == null && (detail.series.my_recent?.attended ?? 0) >= 1 && (
                  <button className="btn btn--secondary btn--sm" style={{ alignSelf: 'flex-start' }} onClick={() => setRegular(true)}>{t('regular.keep')}</button>
                )}
              </div>
            )}
            {detail?.series?.upcoming_list && detail.series.upcoming_list.length > 0 && (
              <div className="chips chips--scroll">
                {detail.series.upcoming_list.map((u) => <Link key={u.id} href={`/a/${u.slug}`} className="chip chip--sm">{formatDateLong(u.time_start, i18n.language)}</Link>)}
              </div>
            )}
          </section>
        )}

        {['attended', 'checked_in'].includes(status ?? '') && !isOrganizer && detail?.thanked === false && !thanksSent && organizer && (
          <section className="card stack fade-in" style={{ gap: 10 }}>
            <div className="title">{t('belong.thanksTitle', { name: organizer.display_name.split(' ')[0] })}</div>
            <span className="caption">{t('belong.thanksBody')}</span>
            <div className="chips">
              {THANKS_PRESETS.map((p) => <button key={p} type="button" className="chip chip--sm" onClick={() => sendThanks(t(`belong.presets.${p}`))}>{t(`belong.presets.${p}`)}</button>)}
            </div>
            <div className="row" style={{ gap: 8 }}>
              <label className="field grow" style={{ margin: 0 }}><input className="field__input" name="thanks" maxLength={140} value={thanksText} onChange={(e) => setThanksText(e.target.value)} placeholder={t('belong.thanksOwn')} /></label>
              <button className="btn btn--primary btn--sm" disabled={!thanksText.trim()} onClick={() => sendThanks(thanksText)}>{t('belong.thanksSend')}</button>
            </div>
          </section>
        )}

        {cards && cards.length > 0 && (
          <section className="card stack fade-in" style={{ gap: 8 }}>
            <div className="title">{t('cards.title')}</div>
            <p style={{ margin: 0, fontSize: '1.05rem' }}>{cards[cardIndex % cards.length]}</p>
            <button type="button" className="btn btn--secondary btn--sm" style={{ alignSelf: 'flex-start' }} onClick={() => setCardIndex((i) => i + 1)}>
              {t('cards.another')}
            </button>
          </section>
        )}

        {meet && meet.length > 0 && (
          <section className="card stack fade-in" style={{ gap: 10 }}>
            <div className="title">{t('meet.title')}</div>
            <span className="caption">{t('meet.body')}</span>
            <div className="chips">
              {meet.map((p) => <button key={p.member_id} type="button" className="chip chip--sm" aria-pressed={p.picked} onClick={() => toggleMeet(p)}>{p.picked ? '✓ ' : ''}{p.display_name}</button>)}
            </div>
          </section>
        )}

        {feedback?.eligible && !feedback.already_submitted && (
          <section className="card stack fade-in" style={{ gap: 10 }}>
            <div className="title">{t('belong.comeAgainTitle')}</div>
            <span className="caption">{t('belong.privateNote')}</span>
            <div className="row" role="radiogroup" aria-label={t('belong.comeAgainTitle')}>
              {(['yes', 'maybe', 'no'] as const).map((v) => <button key={v} type="button" role="radio" aria-checked={comeAgain === v} className="chip chip--sm" aria-pressed={comeAgain === v} onClick={() => setComeAgain(v)}>{t(`belong.comeAgain.${v}`)}</button>)}
            </div>
            <label className="field"><textarea placeholder={t('belong.betterPlaceholder')} value={fbText} onChange={(e) => setFbText(e.target.value)} maxLength={500} /></label>
            <div className="row"><button className="btn btn--ghost" onClick={() => sendFeedback(true)}>{t('detail.feedbackSkip')}</button><button className="btn btn--primary grow" onClick={() => sendFeedback(false)}>{t('detail.feedbackSend')}</button></div>
          </section>
        )}

        {isOrganizer && <Link href={`/organizer/${card.id}`} className="btn btn--secondary btn--block">{t('detail.manage')}</Link>}
        {!identity && ready && <a href={entranceSignInUrl()} className="btn btn--primary btn--block">{t('detail.loginToRsvp')}</a>}
      </main>

      <aside className="detail__aside">
        <div className="detail__card card glass">
          <div className="stack" style={{ gap: 4 }}>
            <div className="title">{formatDateLong(card.time_start, i18n.language)}</div>
            <div className="muted">{card.location_label}{card.distance_label ? ` · ${card.distance_label}` : ''}</div>
            <div className="row" style={{ gap: 10 }}>
              {going === 0 && !cancelled ? <strong style={{ color: 'var(--accent-pressed)' }}>{t('detail.beFirst')}</strong> : <strong>{t('card.going', { count: going })}</strong>}
              {card.capacity !== null && spotsLeft !== null && <span className="pill pill--neutral">{spotsLeft > 0 ? t('card.spotsLeft', { count: spotsLeft }) : t('card.full')}</span>}
            </div>
          </div>
          {rsvpControls && <div className="row" style={{ gap: 10 }}>{rsvpControls}</div>}
          {cancelled && <div className="pill pill--danger" style={{ alignSelf: 'flex-start' }}>{t('detail.cancelledBanner')}</div>}
          {!identity && ready && <a href={entranceSignInUrl()} className="btn btn--primary btn--block">{t('detail.loginToRsvp')}</a>}
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
          {share && <QrCode value={appUrl(`/a/${card.slug}`)} size={180} label="QR code for this activity" />}
        </div>
      </Sheet>

      <Sheet open={menu} onClose={() => setMenu(false)} label="More">
        <div className="stack">
          {isOrganizer && <Link href={`/organizer/${card.id}`} className="btn btn--secondary btn--block" onClick={() => setMenu(false)}>{t('detail.manage')}</Link>}
          {!isOrganizer && (hideAsk ? (
            <div className="stack" style={{ gap: 8 }}>
              <span className="caption">{t('fit.notInterestedWhy')}</span>
              <div className="chips">
                {(['not_my_thing', 'too_far', 'bad_time', 'not_this_host'] as const).map((r) => <button key={r} type="button" className="chip chip--sm" onClick={() => hideThis(r)}>{t(`fit.reasons.${r}`)}</button>)}
              </div>
            </div>
          ) : (
            <button className="btn btn--secondary btn--block" onClick={() => setHideAsk(true)}>{t('fit.notInterested')}</button>
          ))}
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

      <Modal open={payAsk} onClose={() => setPayAsk(false)} label={t('pay.withdrawTitle')}>
        <div className="stack">
          <h2 className="h2">{t('pay.withdrawTitle')}</h2>
          <p className="muted" style={{ margin: 0 }}>
            {(pay?.refund_if_withdraw_now_paise ?? 0) > 0 ? t('pay.withdrawRefund', { amount: formatInr(pay?.refund_if_withdraw_now_paise ?? 0, i18n.language) }) : t('pay.withdrawNoRefund')}
          </p>
          <div className="row"><button className="btn btn--ghost grow" onClick={() => setPayAsk(false)}>{t('create.keep')}</button><button className="btn btn--danger grow" onClick={withdrawPaid}>{t('pay.withdrawConfirm')}</button></div>
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

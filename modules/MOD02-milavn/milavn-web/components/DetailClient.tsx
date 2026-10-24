'use client';

/* Event page (UX06/UI06 + FR046-FR050 public page), redesigned 2026-10 after
 * AgentOutputs/EVENT-PAGE-LEARNING-2026-10.md (decisions D1-D15).
 *
 * One page, three moments, decided by who is looking and when:
 *   deciding   a visitor from a link or a member who has not joined: title, host, When / Where / Price /
 *              Who's going above the fold, Good to know, About, approximate map, the host's latest update;
 *              the bar carries one action with the price in it ("Join · Free", "Join · ₹250", "Join waitlist")
 *              plus a small Save (the server's 'interested' status) and Share.
 *   going      a confirmed attendee: status strip with a countdown, the host's latest update first, the exact
 *              place with directions (or the meeting link in its window), the one group chat, who's going.
 *   hosting    the organizer: what is still missing, who is coming, her updates (sent from here), one chat;
 *              never Join / Interested on her own event. Check-in and the rest stay under Manage.
 *   recap      after the end: when it happened, photos first, thanks, meet again, the next date.
 *
 * Every endpoint, RSVP rule and server behaviour is unchanged: the exact venue and the join link still arrive
 * only for organizers and confirmed attendees (RLS), tickets / waitlist / co-hosting / teams / agenda keep
 * working. Renders from the server-fetched public contract first (FR047), then enriches when a member is present. */

import dynamic from 'next/dynamic';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { TrustPill } from '@/components/ActivityCard';
import Avatar from '@/components/Avatar';
import CategoryIcon from '@/components/CategoryIcon';
import CohostPanel from '@/components/CohostPanel';
import EventProgram from '@/components/EventProgram';
import Moments from '@/components/Moments';
import QrCode from '@/components/QrCode';
import { Modal, Sheet } from '@/components/Sheet';
import { CardSkeleton, ErrorState, Toast } from '@/components/States';
import { OrganizerContact, TicketPicker, TicketQrCard, type TicketChoice, type Tix } from '@/components/TicketPanel';
import { api, ApiError, resolveMediaUrl, type Card } from '@/lib/api';
import { appUrl } from '@/lib/base-path';
import { daySpan, type Provider } from '@/lib/event-formats';
import { formatDateLong, formatInr, formatRelative, formatTime, formatWhen, intlLocale } from '@/lib/format';
import { buildIcs, icsDataUrl } from '@/lib/ics';
import { useIdentity } from '@/lib/identity';
import { entranceSignInUrl } from '@/lib/platform';
import { renderPoster } from '@/lib/poster';

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

const directionsHref = (query: string) => `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`;
// [054] The exact venue pin: directions straight to the point, not a search on the address text.
const directionsToPoint = (lat: number, lng: number) => `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;

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
  attendance_mode?: 'in_person' | 'online' | 'hybrid';
  venue?: { venue_address: string | null; venue_notes: string | null; join_link: string | null; lat?: number | null; lng?: number | null } | null; // only for organizers and confirmed attendees
  // [054] Online / hybrid: the join link reaches confirmed attendees only from open_minutes before the start until the end.
  online?: { state: 'later' | 'open' | 'ended'; opens_at: string; open_minutes: number; provider: Provider | null } | null;
  event_format?: string | null;
  team_size_max?: number | null;
  my_guests?: number; // how many I am bringing
  guest_total?: number; // how many guests altogether
  first_time?: boolean;
  thanked?: boolean;
};

// The event's group chat in Chats (migration 049), as the server summarises it for people inside it.
type ActivityChat = {
  conversation_id: string | null; last_preview: string | null; last_by: string | null; last_message_at: string | null; unread: number;
  members: { member_id: string; display_name: string; avatar: string | null }[];
};
type Attendee = { member_id: string; display_name: string; avatar: string | null; status: string; waitlist_position: number | null; checked_in_at: string | null; company?: string | null; first_time?: boolean; guests?: number };

// FR107: one-tap thank-you presets (the attendee can also write their own).
const THANKS_PRESETS = ['organizing', 'loved', 'group', 'next'] as const;
const TELANGANA_CITIES = /hyderabad|secunderabad|warangal|karimnagar|nizamabad|khammam/i;

// FR105: one tap each, optional; repeated back in the reminder before it starts.
const TRAVEL = ['walk', 'two_wheeler', 'car', 'cab_auto', 'metro_bus'] as const;
const COMPANY = ['alone', 'friend', 'family'] as const;

// FR102 paid spots: what the member needs to decide and to know where they stand.
type TicketInfo = {
  price_paise: number | null; refund_cutoff_hours: number; refund_deadline: string; refund_if_withdraw_now_paise: number; payments_available: boolean;
  ticket: { kind: string; status: string; amount_paise: number; checkout_url: string | null; hold_active: boolean; hold_expires_at: string | null; refund_amount_paise: number | null; type_name?: string | null; qr_code?: string | null; discount_paise?: number } | null;
};

const NOTIF_KEY = 'milavn.notifPrimed';
const IST = 'Asia/Kolkata';
const CONFIRMED = ['going', 'checked_in', 'attended'];
// A calm colour per category for the hero when there is no cover (D8: never a stock photo of strangers).
const CATEGORY_HUE: Record<string, string> = {
  play: 'linear-gradient(135deg, #1b4a5e, #0f2a3d)', meet: 'linear-gradient(135deg, #5a3d2b, #2e1f17)', eat: 'linear-gradient(135deg, #6b3a1e, #3a1f10)',
  learn: 'linear-gradient(135deg, #2f3e6b, #1a2340)', work: 'linear-gradient(135deg, #2d4a3e, #172a22)', explore: 'linear-gradient(135deg, #3a5a2e, #1f3119)',
  celebrate: 'linear-gradient(135deg, #6b2d4a, #3a1828)', help: 'linear-gradient(135deg, #2e5a56, #17302e)', professional: 'linear-gradient(135deg, #3b3f6b, #1f2140)',
};

const istDay = (iso: string | number) => new Intl.DateTimeFormat('en-CA', { timeZone: IST, year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date(iso));
const dayShort = (iso: string, lang: string) => new Intl.DateTimeFormat(intlLocale(lang), { timeZone: IST, weekday: 'short', day: 'numeric', month: 'short' }).format(new Date(iso));
const weekdayLong = (iso: string, lang: string) => new Intl.DateTimeFormat(intlLocale(lang), { timeZone: IST, weekday: 'long' }).format(new Date(iso));

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
  const [qrOpen, setQrOpen] = useState(false);
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
  const [tix, setTix] = useState<Tix | null>(null); // [052] ticket types, organizer contact, Counsel link
  const [choice, setChoice] = useState<TicketChoice>({ typeId: null, code: '', amount: null });
  const [planEdit, setPlanEdit] = useState(false);
  const [hideAsk, setHideAsk] = useState(false);
  const [allUpdates, setAllUpdates] = useState(false);
  const [updateText, setUpdateText] = useState('');
  const [attendees, setAttendees] = useState<Attendee[] | null>(null); // organizer only (FR056)
  const [now, setNow] = useState(() => Date.now()); // for the countdown; ticks once a minute

  const say = (m: string) => { setToast(m); setTimeout(() => setToast(null), 2200); };

  const loadTicket = useCallback(async (occurrenceId: string) => {
    try { setPay(await api<TicketInfo>(`/occurrences/${occurrenceId}/ticket`)); } catch { /* the price still shows from the card */ }
  }, []);

  const loadAuth = useCallback(async () => {
    try {
      const d = await api<Detail>(`/occurrences/by-slug/${encodeURIComponent(slug)}`);
      setDetail(d); setStatus(d.viewer_status); setGoing(d.going_count); setSpotsLeft(d.spots_left ?? null); setError(false);
      if (d.price_paise != null) void loadTicket(d.id);
      api<Tix>(`/occurrences/${d.id}/ticketing`).then(setTix).catch(() => setTix(null));
      if (['attended', 'checked_in'].includes(d.viewer_status ?? '')) api<{ eligible: boolean; already_submitted: boolean }>(`/feedback/prompt/${d.id}`).then(setFeedback).catch(() => undefined);
      if (d.viewer_role === 'organizer' || d.viewer_role === 'co_organizer') api<Attendee[]>(`/occurrences/${d.id}/attendees`).then(setAttendees).catch(() => setAttendees(null));
    } catch {
      if (!pub) setError(true);
    }
  }, [slug, pub, loadTicket]);

  useEffect(() => { if (ready && identity) void loadAuth(); }, [ready, identity, loadAuth]);
  useEffect(() => { const id = setInterval(() => setNow(Date.now()), 60_000); return () => clearInterval(id); }, []);

  // [049] The one group chat in Messages for the host and everyone going; the server answers null for anyone else.
  const [activityChat, setActivityChat] = useState<ActivityChat | null>(null);
  const detailId = detail?.id;
  useEffect(() => {
    if (!detailId) return;
    api<ActivityChat>(`/chats/activity/${detailId}`).then(setActivityChat).catch(() => setActivityChat(null));
  }, [detailId, status]);

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
    const minutes = card.time_end ? Math.max(15, Math.round((Date.parse(card.time_end) - Date.parse(card.time_start)) / 60_000)) : undefined;
    const ics = buildIcs({ uid: card.id, title: card.title, start: card.time_start, durationMinutes: minutes, location: card.location_label, description: description ?? undefined, url: appUrl(`/a/${card.slug}`) });
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setIcsHref(icsDataUrl(ics));
  }, [card?.id, card?.time_start, card?.time_end, card?.title, card?.location_label, description]); // eslint-disable-line react-hooks/exhaustive-deps
  const safety = detail?.safety_guidelines ?? pub?.safety_guidelines ?? [];
  const isOrganizer = detail?.viewer_role === 'organizer' || detail?.viewer_role === 'co_organizer';
  const cancelled = card?.status === 'cancelled';
  const venue = detail?.venue ?? null;
  const confirmed = CONFIRMED.includes(status ?? '');

  const setRsvp = async (desired: 'interested' | 'going' | 'cancelled', quiet = false) => {
    if (!card || busy) return;
    const prev = status;
    setBusy(true); setStatus(desired === 'cancelled' ? null : desired); setPop(true); setTimeout(() => setPop(false), 350);
    try {
      const r = await api<{ status: string; waitlist_position: number | null; going_count: number; spots_left: number | null; message: string | null }>(`/occurrences/${card.id}/participation`, { body: { status: desired }, idempotent: true });
      setStatus(r.status === 'cancelled' ? null : r.status); setWaitPos(r.waitlist_position); setGoing(r.going_count); setSpotsLeft(r.spots_left ?? null);
      if (r.message) say(r.message);
      else if (!quiet && desired === 'interested') say(t('evp.savedToast'));
      else if (!quiet && desired === 'cancelled' && prev === 'interested') say(t('evp.unsavedToast'));
      if (desired === 'going' && r.status !== 'cancelled') {
        let primed = false; try { primed = localStorage.getItem(NOTIF_KEY) === '1'; } catch { /* ignore */ }
        if (!primed) setNotifAsk(true);
        void loadAuth(); // the venue / join link arrive now that this member is confirmed
      }
    } catch (e) {
      setStatus(prev);
      say(e instanceof ApiError ? e.message : t('state.error'));
    } finally { setBusy(false); }
  };

  // [D12] A visitor tapped "Join · Free", signed in at the ForKhatri entrance and came back with ?join=1: finish the join
  // in one step. Paid events come back to the page with the Join button ready (the checkout is its own step).
  const [autoJoined, setAutoJoined] = useState(false);
  useEffect(() => {
    if (!ready || !identity || !detail || autoJoined) return;
    if (new URLSearchParams(window.location.search).get('join') !== '1') return;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setAutoJoined(true);
    window.history.replaceState(null, '', window.location.pathname);
    const over = Date.now() >= (detail.time_end ? Date.parse(detail.time_end) : Date.parse(detail.time_start) + 3 * 3600_000);
    if (detail.price_paise == null && !detail.viewer_status && detail.viewer_role === 'viewer' && detail.status !== 'cancelled' && !over) void setRsvp('going', true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, identity, detail?.id]);

  // [FR102] Paid activity: hold a spot and go to checkout, or join the waitlist when full.
  const joinPaid = async () => {
    if (!card || busy) return;
    setBusy(true);
    try {
      const r = await api<{ status: string; checkout_url: string | null; waitlist_position: number | null }>(`/occurrences/${card.id}/ticket`, { body: { ticket_type_id: choice.typeId, code: choice.code || null }, idempotent: true });
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

  // [054] Tapping Join opens the organizer's meeting link (a plain link, so the browser never blocks it) and tells the
  // server, which marks a confirmed attendee checked in. Organizers just open it.
  const joinOnline = () => {
    if (!card || isOrganizer) return;
    api<{ status: string }>(`/occurrences/${card.id}/join-online`, { body: {} })
      .then(() => setStatus('checked_in'))
      .catch((e) => say(e instanceof ApiError ? e.message : t('state.error')));
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
    const hour = Number(new Intl.DateTimeFormat('en-IN', { timeZone: IST, hour: 'numeric', hourCycle: 'h23' }).format(new Date(card.time_start)));
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
    const text = pub?.share.text ?? `${card.title} — ${card.location_label}`;
    if (channel === 'native' && navigator.share) { try { await navigator.share({ title: card.title, text, url }); } catch { /* cancelled */ } return; }
    if (channel === 'copy') { await navigator.clipboard?.writeText(url); say(t('create.copied')); return; }
    if (channel === 'whatsapp') window.open(`https://wa.me/?text=${encodeURIComponent(`${text} ${url}`)}`, '_blank', 'noopener');
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

  // [D7] The organizer sends an update from the page itself; everyone going is told (FR057, unchanged endpoint).
  const sendUpdate = async () => {
    if (!card || !updateText.trim() || busy) return;
    setBusy(true);
    try {
      await api(`/occurrences/${card.id}/announcements`, { body: { message: updateText.trim() } });
      setUpdateText(''); say(t('evp.updateSent')); await loadAuth();
    } catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
    finally { setBusy(false); }
  };

  // [D3] "Ask Asha": a private chat with the host. Trust-scoped (milavn-social-decisions): only people who share this
  // event with the host reach here, and the server checks that again.
  const askHost = async () => {
    if (!organizer) return;
    try { const r = await api<{ id: string }>('/chats/direct', { body: { member_id: organizer.member_id } }); router.push(`/chats/${r.id}`); }
    catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  const announcements = useMemo(() => [...(detail?.announcements ?? [])].sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at)), [detail?.announcements]);

  if (!card) {
    return <main className="screen">{error ? <ErrorState onRetry={loadAuth} /> : <CardSkeleton count={1} />}</main>;
  }

  const lang = i18n.language;
  const paidActivity = card.price_paise != null;
  const startMs = Date.parse(card.time_start);
  const endMs = card.time_end ? Date.parse(card.time_end) : startMs + 3 * 3600_000;
  // An activity has ended at its end time, or three hours after the start when no end was given (same rule as the chat context).
  const ended = openedAt >= endMs;
  const live = now >= startMs && now < endMs;
  const tk = pay?.ticket ?? null;
  const priceLabel = paidActivity ? formatInr(card.price_paise as number, lang) : t('evp.free');
  const hostFirst = organizer?.display_name.split(' ')[0] ?? card.host_name.split(' ')[0];
  const mode = detail?.attendance_mode ?? 'in_person';
  const view: 'recap' | 'host' | 'going' | 'deciding' = ended ? 'recap' : isOrganizer ? 'host' : confirmed ? 'going' : 'deciding';
  const coverUrl = resolveMediaUrl(card.cover_image_url);
  const spots = card.capacity !== null && spotsLeft !== null ? (spotsLeft > 0 ? t('evp.spotsOf', { left: spotsLeft, total: card.capacity }) : t('card.full')) : null;

  // "Sat 11 Oct, 6:30–8:30 pm" — one line, the end time included (D9). Multi-day events say until when.
  const sameDay = !card.time_end || daySpan(card.time_start, card.time_end) === 1;
  const whenLine = card.time_end
    ? sameDay ? `${dayShort(card.time_start, lang)}, ${formatTime(card.time_start, lang)} – ${formatTime(card.time_end, lang)}` : `${dayShort(card.time_start, lang)}, ${formatTime(card.time_start, lang)} – ${dayShort(card.time_end, lang)}, ${formatTime(card.time_end, lang)}`
    : `${dayShort(card.time_start, lang)}, ${formatTime(card.time_start, lang)}`;
  // "Today · in 2 hours", "Tomorrow", "in 5 days", "Happening now".
  const untilLabel = (() => {
    if (live) return t('evp.happeningNow');
    if (now >= endMs) return null;
    const mins = Math.round((startMs - now) / 60_000);
    const today = istDay(card.time_start) === istDay(now);
    const tomorrow = istDay(card.time_start) === istDay(now + 86_400_000);
    const rel = mins < 60 ? t('evp.inMinutes', { count: Math.max(1, mins) }) : mins < 24 * 60 ? t('evp.inHours', { count: Math.round(mins / 60) }) : t('evp.inDays', { count: Math.round(mins / (24 * 60)) });
    if (today) return `${t('evp.today')} · ${rel}`;
    if (tomorrow) return `${t('evp.tomorrow')} · ${rel}`;
    return rel;
  })();

  const providerLabel = detail?.online?.provider && detail.online.provider !== 'other' ? t(`evt.provider.${detail.online.provider}`) : null;
  const whereSub = [
    card.distance_label,
    mode === 'online' ? (providerLabel ? t('evp.onlineOn', { provider: providerLabel }) : t('evp.online')) : mode === 'hybrid' ? t('evp.hybrid') : null,
  ].filter(Boolean).join(' · ');
  const hiddenNote = !confirmed && !isOrganizer && !cancelled ? (mode === 'online' ? t('evp.linkAfterJoin') : t('evp.exactAfterJoin')) : null;

  const peers = detail?.circle_peers ?? [];
  const peerNames = peers.slice(0, 3).map((p) => p.display_name.split(' ')[0]);
  // "Vikram and Priya" in the person's own language (Intl.ListFormat; a plain comma list where it is missing).
  const listNames = (names: string[]) => { try { return new Intl.ListFormat(intlLocale(lang), { style: 'long', type: 'conjunction' }).format(names); } catch { return names.join(', '); } };

  /* ---------- the one primary action, with the price in it (D2) ---------- */
  const joinLabel = spotsLeft === 0 ? t('evp.joinWaitlist') : t('pay.join', { amount: choice.amount != null ? formatInr(choice.amount, lang) : priceLabel });
  const primary = (() => {
    if (cancelled) return null;
    if (!identity) {
      // [D12] Sign in at the ForKhatri entrance and come back to this page with the join done.
      return ready ? <a className="btn btn--primary btn--glow grow" href={entranceSignInUrl(appUrl(`/a/${card.slug}?join=1`))}>{t('evp.signInJoin', { price: priceLabel })}</a> : null;
    }
    if (isOrganizer) return null;
    if (status === 'checked_in' || status === 'attended') return <span className="btn btn--secondary grow" aria-live="polite">✓ {t(`card.youAre.${status}`)}</span>;
    if (ended) return null;
    if (paidActivity) {
      if (tk?.status === 'paid') return <button className={`btn btn--primary btn--spring grow${pop ? ' pop' : ''}`} aria-live="polite" onClick={() => setPayAsk(true)} disabled={busy}>✓ {t('pay.youPaid', { amount: formatInr(tk.amount_paise, lang) })} · {t('detail.withdraw')}</button>;
      if (tk?.hold_active) {
        return (
          <>
            <button className="btn btn--primary btn--glow grow" onClick={() => (tk.checkout_url ? window.location.assign(tk.checkout_url) : void joinPaid())} disabled={busy}>
              {tk.kind === 'waitlist_offer' ? t('pay.claimSpot', { amount: formatInr(tk.amount_paise, lang) }) : t('pay.completePayment', { amount: formatInr(tk.amount_paise, lang) })}
            </button>
            <button className="btn btn--ghost" onClick={withdrawPaid} disabled={busy}>{t('pay.release')}</button>
          </>
        );
      }
      if (status === 'waitlisted') return <button className="btn btn--secondary grow" onClick={withdrawPaid} disabled={busy}>✓ {t('card.youAre.waitlisted')} · {t('detail.withdraw')}</button>;
      return <button className="btn btn--primary btn--glow btn--spring grow" onClick={joinPaid} disabled={busy || pay?.payments_available === false || (!!tix?.tiered && !choice.typeId)}>{tix?.tiered && !choice.typeId ? t('tix.pickFirst') : joinLabel}</button>;
    }
    if (status === 'going') {
      // Going: the bar turns into the way there (D4). Can't make it sits under ⋯.
      if (mode !== 'online' && venue?.lat != null && venue.lng != null) return <a className="btn btn--primary grow" href={directionsToPoint(venue.lat, venue.lng)} target="_blank" rel="noopener">{t('detail.directions')}</a>;
      if (mode !== 'online' && venue?.venue_address) return <a className="btn btn--primary grow" href={directionsHref(venue.venue_address)} target="_blank" rel="noopener">{t('detail.directions')}</a>;
      if (venue?.join_link && detail?.online?.state === 'open') return <a className="btn btn--primary grow" href={venue.join_link} target="_blank" rel="noopener noreferrer" onClick={joinOnline}>{providerLabel ? t('evt.online.joinOn', { provider: providerLabel }) : t('detail.venue.join')}</a>;
      return <span className="btn btn--secondary grow" aria-live="polite">✓ {t('detail.youreGoing')}</span>;
    }
    if (status === 'waitlisted') return <button className={`btn btn--secondary grow${pop ? ' pop' : ''}`} aria-live="polite" onClick={() => setRsvp('cancelled')} disabled={busy}>✓ {t('card.youAre.waitlisted')} · {t('detail.withdraw')}</button>;
    return <button className={`btn btn--primary btn--glow btn--spring grow${pop && status === 'going' ? ' pop' : ''}`} onClick={() => setRsvp('going')} disabled={busy}>{joinLabel}</button>;
  })();

  const saveButton = identity && !isOrganizer && !confirmed && !ended && !cancelled && status !== 'waitlisted' && !tk?.hold_active ? (
    <button type="button" className="evp-save" aria-pressed={status === 'interested'} aria-label={status === 'interested' ? t('evp.saved') : t('evp.save')} title={status === 'interested' ? t('evp.saved') : t('evp.save')} onClick={() => setRsvp(status === 'interested' ? 'cancelled' : 'interested')} disabled={busy}>
      <svg width="22" height="22" viewBox="0 0 24 24" fill={status === 'interested' ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z" /></svg>
    </button>
  ) : null;
  const shareButton = (
    <button className="evp-save" aria-label={t('detail.share')} title={t('detail.share')} onClick={() => setShare(true)}>
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path d="M12 3v12M7 8l5-5 5 5M5 14v5a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-5" /></svg>
    </button>
  );
  const chatButton = activityChat?.conversation_id ? (
    <Link className="evp-save" href={`/chats/${activityChat.conversation_id}`} aria-label={t('evp.groupChat')} title={t('evp.groupChat')} style={{ position: 'relative' }}>
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path d="M21 12a8 8 0 0 1-8 8H5l-2 2V12a8 8 0 0 1 8-8h2a8 8 0 0 1 8 8z" /></svg>
      {activityChat.unread > 0 && <span className="evp-dot" style={{ position: 'absolute', top: -4, right: -4 }}>{activityChat.unread > 9 ? '9+' : activityChat.unread}</span>}
    </Link>
  ) : null;
  const moreButton = identity ? (
    <button className="evp-save" aria-label={t('common.more')} title={t('common.more')} onClick={() => setMenu(true)}>
      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><circle cx="5" cy="12" r="2" /><circle cx="12" cy="12" r="2" /><circle cx="19" cy="12" r="2" /></svg>
    </button>
  ) : null;
  const nextDate = (detail?.series ?? pub?.series)?.upcoming_list?.[0] ?? null;

  const bar = cancelled ? null : view === 'host' ? (
    <>
      <a className="btn btn--primary grow" href="#send-update">{t('evp.sendUpdate')}</a>
      <Link href={`/organizer/${card.id}`} className="btn btn--secondary" style={{ minHeight: 50 }}>{t('evp.manage')}</Link>
      {shareButton}
    </>
  ) : view === 'recap' ? (
    <>
      {nextDate ? <Link href={`/a/${nextDate.slug}`} className="btn btn--primary grow">{t('evp.joinNext')}</Link> : <span className="btn btn--ghost grow">{t('detail.ended')}</span>}
      {shareButton}
    </>
  ) : view === 'going' ? (
    <>
      {primary}
      {chatButton}
      {moreButton}
    </>
  ) : (
    <>
      {primary}
      {saveButton}
      {shareButton}
    </>
  );

  /* ---------- blocks shared between the moments ---------- */
  const hostLine = organizer && (
    <div className="evp-host">
      <Link href={`/p/${organizer.member_id}`} aria-label={organizer.display_name}><Avatar src={organizer.avatar} name={organizer.display_name} size="lg" /></Link>
      <div className="grow" style={{ minWidth: 0 }}>
        <Link href={`/p/${organizer.member_id}`} className="evp-host__name">{t('evp.hostedBy', { name: organizer.display_name })} <span className="muted" aria-hidden="true">›</span></Link>
        <div className="row" style={{ gap: 8, flexWrap: 'wrap' }}>
          <button type="button" className="evp-host__badge" aria-expanded={trustOpen} aria-controls="trust-panel" onClick={() => setTrustOpen((v) => !v)}>
            <TrustPill level={card.trust_level} label={card.trust_label} positive={card.trust_positive} />
            <span>{trustOpen ? '▴' : '▾'}</span>
          </button>
          {((detail?.series ?? pub?.series)?.held ?? 0) > 0 && <span className="caption">{t('evp.heldSoFar', { count: (detail?.series ?? pub?.series)?.held ?? 0 })}</span>}
        </div>
      </div>
    </div>
  );
  const trustPanel = trustOpen && <p id="trust-panel" className="caption fade-in" style={{ margin: 0, padding: 12, background: 'var(--surface-sunken)', borderRadius: 12 }}>{t(`detail.trustExplain.${card.trust_level}`)}</p>;

  const kicker = (
    <div className="evp-kicker">
      <CategoryIcon category={card.intent_category} size={16} />
      <span>{card.category_label}{card.event_format ? ` · ${t(`evt.format.${card.event_format}`)}` : ''}{card.is_recurring ? ` · ${t('card.recurring')}` : ''}</span>
      {(card.audience_tags ?? []).map((a) => <span key={a} className="pill pill--trust">{t(`fit.audience.${a}`)}</span>)}
    </div>
  );

  const latestUpdate = announcements.length > 0 && (
    <section className="stack" style={{ gap: 8 }} aria-label={t('evp.latestFrom', { name: hostFirst })}>
      <span className="label">{view === 'host' ? t('evp.yourUpdates') : t('evp.latestFrom', { name: hostFirst })}</span>
      {(allUpdates ? announcements : announcements.slice(0, 1)).map((a) => (
        <div key={a.id} className="card evp-update" style={{ padding: 12 }}>
          <p>{a.message}</p>
          <span className="caption">{view === 'host' ? `${t('evp.sentTo', { count: going })} · ` : ''}{formatRelative(a.created_at)}</span>
        </div>
      ))}
      {!allUpdates && announcements.length > 1 && <button className="link evp-row44" style={{ alignSelf: 'flex-start' }} onClick={() => setAllUpdates(true)}>{t('evp.earlierUpdates', { count: announcements.length - 1 })}</button>}
    </section>
  );

  const goodToKnow = (() => {
    const items: React.ReactNode[] = [];
    (card.food_tags ?? []).forEach((f) => items.push(<li key={f}>{t(`fit.food.${f}`)}</li>));
    if ((detail?.max_guests_per_member ?? 0) > 0 && !isOrganizer) items.push(<li key="guests">{t('evp.bringAllowed', { count: detail?.max_guests_per_member ?? 0 })}</li>);
    if (!sameDay && card.time_end) items.push(<li key="days">{t('evt.multiDay', { count: daySpan(card.time_start, card.time_end), until: formatDateLong(card.time_end, lang) })}</li>);
    if (paidActivity && pay) items.push(<li key="refund">{pay.refund_cutoff_hours === 0 ? t('pay.refundUntilStart') : t('pay.refundUntil', { time: formatDateLong(pay.refund_deadline, lang) })}</li>);
    if (items.length === 0) return null;
    return (
      <section className="stack" style={{ gap: 8 }}>
        <span className="label">{t('evp.goodToKnow')}</span>
        <div className="card" style={{ padding: 14 }}><ul style={{ margin: 0, paddingLeft: 18 }}>{items}</ul></div>
      </section>
    );
  })();

  const about = description && (
    <section className="stack" style={{ gap: 6 }}>
      <span className="label">{t('detail.about')}</span>
      <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{description}</p>
    </section>
  );

  const programme = detail && (
    <EventProgram
      eventId={detail.id} start={card.time_start} end={card.time_end} viewerId={identity?.member_id ?? null}
      confirmed={confirmed} isOrganizer={isOrganizer} ended={ended || cancelled}
      say={say} refreshKey={status}
    />
  );

  const approxMap = card.lat !== null && card.lng !== null && mode !== 'online' && (
    <section className="stack" style={{ gap: 8 }}>
      <span className="label">{t('evp.where')}</span>
      <MiniMap lat={card.lat} lng={card.lng} label={card.location_label} caption={t('evp.approxArea')} />
    </section>
  );

  const safetyBlock = safety.length > 0 && (
    <details className="card" style={{ padding: 14, borderColor: 'var(--accent-primary)' }} open={card.high_risk && view !== 'recap'}>
      <summary className="label evp-row44" style={{ color: 'var(--accent-pressed)', cursor: 'pointer' }}>{t('detail.safety')}</summary>
      <p style={{ margin: '8px 0 0' }} className="caption">{t('detail.safetyIntro')}</p>
      <ul style={{ margin: '6px 0 0', paddingLeft: 18 }}>{safety.map((s) => <li key={s}>{s}</li>)}</ul>
    </details>
  );

  // [D5] One chat: the latest message and the unread count, opening the event's chat in Chats.
  const chatRow = activityChat?.conversation_id && !cancelled && (
    <section className="stack" style={{ gap: 8 }}>
      <span className="label">{t('evp.groupChat')}</span>
      <Link href={`/chats/${activityChat.conversation_id}`} className="card evp-chat card--tap" style={{ padding: '10px 14px' }}>
        <span className="avatar avatar--lg avatar--group" aria-hidden="true">💬</span>
        <span className="grow" style={{ minWidth: 0 }}>
          {activityChat.last_preview ? (
            <><b className="truncate" style={{ display: 'block' }}>{activityChat.last_by ?? ''}</b><span className="caption truncate" style={{ display: 'block' }}>{activityChat.last_preview}</span></>
          ) : (
            <><b style={{ display: 'block' }}>{t('evp.openChat')}</b><span className="caption">{t('evp.chatEmpty')}</span></>
          )}
        </span>
        {activityChat.unread > 0 ? <span className="evp-dot">{activityChat.unread > 9 ? '9+' : activityChat.unread}</span> : <span className="muted" aria-hidden="true">›</span>}
      </Link>
    </section>
  );

  const seriesBlock = (detail?.series ?? pub?.series)?.upcoming_list && ((detail?.series ?? pub?.series)?.upcoming_list?.length ?? 0) > 0 && (
    <section className="stack" style={{ gap: 8 }}>
      <span className="label">{t('evp.nextDate')}</span>
      <div className="chips chips--scroll">
        {(detail?.series ?? pub?.series)?.upcoming_list?.map((u) => <Link key={u.id} href={`/a/${u.slug}`} className="chip">{formatDateLong(u.time_start, lang)}</Link>)}
      </div>
      {detail?.series && identity && !isOrganizer && (
        <div className="stack" style={{ gap: 6 }}>
          {(detail.series.my_recent?.total ?? 0) > 0 && (detail.series.my_recent?.attended ?? 0) > 0 && (
            <span className="caption">{t('regular.recent', { attended: detail.series.my_recent?.attended, total: detail.series.my_recent?.total })}</span>
          )}
          {detail.series.regular ? (
            <>
              <span className="caption">{t('regular.on')}</span>
              <button className="link evp-row44" style={{ alignSelf: 'flex-start' }} onClick={() => setRegular(false)}>{t('regular.stop')}</button>
            </>
          ) : card.price_paise == null && (detail.series.my_recent?.attended ?? 0) >= 1 && (
            <button className="btn btn--secondary btn--sm" style={{ alignSelf: 'flex-start' }} onClick={() => setRegular(true)}>{t('regular.keep')}</button>
          )}
        </div>
      )}
    </section>
  );

  // Who's going, by what the viewer may know (D1): a visitor sees the count; a member also sees faces from their own
  // circles; a confirmed attendee sees everyone in the chat; the host sees the guest list (further down).
  const whosGoing = (() => {
    const count = going === 0 && !cancelled ? <strong style={{ color: 'var(--accent-pressed)' }}>{t('detail.beFirst')}</strong> : <strong>{t('evp.goingCount', { count: going })}</strong>;
    if (view === 'going' && activityChat && activityChat.members.length > 0) {
      const others = activityChat.members.filter((m) => m.member_id !== identity?.member_id);
      return (
        <div className="evp-going">
          <span className="avatar-stack">{activityChat.members.slice(0, 5).map((m) => <Avatar key={m.member_id} src={m.avatar} name={m.display_name} />)}</span>
          <div className="grow" style={{ minWidth: 0 }}>
            <b>{others.length > 0 ? listNames(others.map((m) => m.display_name.split(' ')[0])) : t('evp.youToo')}</b>
            <div className="caption">{t('evp.youToo')}{spots ? ` · ${spots}` : ''}{(detail?.guest_total ?? 0) > 0 ? ` · ${t('guest.total', { count: detail?.guest_total ?? 0 })}` : ''}</div>
          </div>
        </div>
      );
    }
    if (identity && peers.length > 0) {
      return (
        <div className="evp-going">
          <span className="avatar-stack">{peers.slice(0, 4).map((m) => <Avatar key={m.member_id} src={m.avatar} name={m.display_name} />)}</span>
          <div className="grow" style={{ minWidth: 0 }}>
            <b>{t('evp.goingNames', { names: listNames(peerNames), count: peers.length })}</b>
            <div className="caption">{t('evp.fromCircles')} · {t('evp.goingCount', { count: going })}{spots ? ` · ${spots}` : ''}</div>
          </div>
        </div>
      );
    }
    return (
      <div className="evp-going">
        <span className="evp-fact__i" aria-hidden="true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="9" cy="8" r="3.5" /><path d="M2.5 20a6.5 6.5 0 0 1 13 0M16 4.5a3.5 3.5 0 0 1 0 7M21.5 20a6.5 6.5 0 0 0-4-6" /></svg>
        </span>
        <div className="grow">{count}{(detail?.guest_total ?? 0) > 0 && <span className="muted"> · {t('guest.total', { count: detail?.guest_total ?? 0 })}</span>}{spots && <div className="caption">{spots}</div>}</div>
      </div>
    );
  })();

  /* ---------- the facts, each once (D9) ---------- */
  const facts = (
    <div className="evp-facts">
      <div className="evp-fact">
        <span className="evp-fact__i" aria-hidden="true"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><rect x="3" y="5" width="18" height="16" rx="3" /><path d="M3 10h18M8 3v4M16 3v4" /></svg></span>
        <div className="evp-fact__t"><b>{whenLine}</b>{untilLabel && <span className="caption">{untilLabel}</span>}</div>
        {icsHref && !ended && <a className="evp-fact__a" href={icsHref} download={`${card.slug}.ics`}>{t('detail.addToCalendar')}</a>}
      </div>
      <div className="evp-fact">
        <span className="evp-fact__i" aria-hidden="true"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21z" /><circle cx="12" cy="9.5" r="2.5" /></svg></span>
        <div className="evp-fact__t">
          <b>{mode === 'online' ? (providerLabel ? t('evp.onlineOn', { provider: providerLabel }) : t('evp.online')) : card.location_label}</b>
          {mode !== 'online' && whereSub && <span className="caption">{whereSub}</span>}
          {hiddenNote && <span className="caption" style={{ display: 'block' }}>{hiddenNote}</span>}
        </div>
      </div>
      <div className="evp-fact">
        <span className="evp-fact__i" aria-hidden="true">₹</span>
        <div className="evp-fact__t">
          <b>{tix?.tiered ? t('tix.fromPrice', { amount: priceLabel }) : priceLabel}</b>
          {paidActivity && pay && <span className="caption">{pay.refund_cutoff_hours === 0 ? t('pay.refundUntilStart') : t('pay.refundUntil', { time: formatDateLong(pay.refund_deadline, lang) })}</span>}
          {paidActivity && pay && !pay.payments_available && <span className="caption" style={{ display: 'block' }}>{t('pay.notOpenYet')}</span>}
          {tk?.status === 'refund_pending' && <span className="pill pill--neutral">{t('pay.refundPending', { amount: formatInr(tk.refund_amount_paise ?? tk.amount_paise, lang) })}</span>}
          {tk?.status === 'refunded' && <span className="pill pill--trust">{t('pay.refunded', { amount: formatInr(tk.refund_amount_paise ?? tk.amount_paise, lang) })}</span>}
        </div>
      </div>
      <div className="evp-fact" style={{ borderBottom: 0 }}>{whosGoing}</div>
    </div>
  );

  /* ---------- status strips ---------- */
  const strip = (() => {
    if (cancelled) return <div className="evp-strip evp-strip--off">{t('detail.cancelledBanner')}</div>;
    if (view === 'recap') return <div className="evp-strip evp-strip--past"><span>{t('evp.happenedOn', { date: dayShort(card.time_start, lang) })}</span><span aria-hidden="true">·</span><span>{t('detail.wentCount', { count: going })}</span></div>;
    if (view === 'host') return <div className="evp-strip evp-strip--host"><span aria-hidden="true">★</span><span>{t('evp.youreHosting')} · {whenLine}{untilLabel ? ` · ${untilLabel}` : ''}</span></div>;
    if (status === 'going' || status === 'checked_in' || status === 'attended') return <div className="evp-strip"><span aria-hidden="true">✓</span><span>{status === 'going' ? t('detail.youreGoing') : t(`card.youAre.${status}`)} · {whenLine}{untilLabel ? ` · ${untilLabel}` : ''}</span></div>;
    if (status === 'waitlisted') return <div className="evp-strip evp-strip--wait"><span>{t('detail.waitlisted', { n: waitPos ?? '' })}</span></div>;
    return null;
  })();

  /* ---------- "Where to go": organizers and confirmed attendees only (the server sends the venue to nobody else) ---------- */
  const whereToGo = (view === 'going' || view === 'host') && !cancelled && (
    <section className="stack fade-in" style={{ gap: 8 }} aria-label={t('detail.venue.title')}>
      <span className="label">{t('detail.venue.title')}</span>
      <div className="card evp-venue stack" style={{ gap: 8, padding: 14 }}>
        {mode !== 'online' && (venue?.venue_address ? (
          <>
            <b>{venue.venue_address}</b>
            {venue.venue_notes && <span className="caption">{t('evp.arrival')}: {venue.venue_notes}</span>}
            {venue.lat != null && venue.lng != null ? (
              <MiniMap lat={venue.lat} lng={venue.lng} label={venue.venue_address} exact height={120} caption={t('evp.exactPlace')} />
            ) : card.lat !== null && card.lng !== null ? (
              <MiniMap lat={card.lat} lng={card.lng} label={card.location_label} height={120} caption={t('evp.approxArea')} />
            ) : null}
            <div className="row" style={{ gap: 8, flexWrap: 'wrap' }}>
              <a className="btn btn--secondary grow" href={venue.lat != null && venue.lng != null ? directionsToPoint(venue.lat, venue.lng) : directionsHref(venue.venue_address)} target="_blank" rel="noopener">{t('detail.directions')}</a>
              {view === 'going' && <button className="btn btn--secondary grow" onClick={askHost}>{t('evp.askHost', { name: hostFirst })}</button>}
            </div>
          </>
        ) : (
          <>
            <b>{card.location_label}</b>
            {venue?.venue_notes && <span className="caption">{t('evp.arrival')}: {venue.venue_notes}</span>}
            {card.lat !== null && card.lng !== null && <MiniMap lat={card.lat} lng={card.lng} label={card.location_label} height={120} caption={t('evp.approxArea')} />}
            {view === 'going' && (
              <div className="stack" style={{ gap: 8 }}>
                <span className="caption">{t('evp.noExactPlaceYet', { name: hostFirst })}</span>
                <button className="btn btn--secondary" style={{ alignSelf: 'flex-start' }} onClick={askHost}>{t('evp.askHost', { name: hostFirst })}</button>
              </div>
            )}
          </>
        ))}
        {detail?.online && (() => {
          // [054] Which service it is (from the link), when the link appears, and Join that marks attendance.
          const on = detail.online;
          if (venue?.join_link) {
            return (
              <div className="stack" style={{ gap: 4 }}>
                <a className="btn btn--primary" style={{ alignSelf: 'flex-start' }} href={venue.join_link} target="_blank" rel="noopener noreferrer" onClick={joinOnline}>
                  {providerLabel ? t('evt.online.joinOn', { provider: providerLabel }) : t('detail.venue.join')}
                </a>
                {!isOrganizer && <span className="caption">{t('evt.online.joinMarks')}</span>}
                {isOrganizer && on.state === 'later' && <span className="caption">{t('evt.online.organizerWhen', { minutes: on.open_minutes })}</span>}
              </div>
            );
          }
          if (on.state === 'later' && on.provider) return <span className="caption">{t('evt.online.linkLater', { provider: providerLabel ?? '', minutes: on.open_minutes, time: formatWhen(on.opens_at, lang) })}</span>;
          if (on.state === 'ended') return <span className="caption">{t('evt.online.ended')}</span>;
          return null;
        })()}
        {view === 'host' && <span className="caption">{t('detail.venue.organizerNote')}</span>}
      </div>
    </section>
  );

  /* ---------- the organizer's own blocks (D7) ---------- */
  const hostTasks = view === 'host' && !cancelled && (() => {
    const tasks: React.ReactNode[] = [];
    if (mode !== 'online' && !venue?.venue_address) tasks.push(
      <Link key="place" href={`/create?edit=${card.id}`} className="card evp-task card--tap" style={{ padding: 14 }}>
        <span className="grow"><b>{t('evp.taskAddPlace')}</b><div className="caption">{t('evp.taskAddPlaceBody', { area: card.location_label })}</div></span>
        <span className="link">{t('evp.add')}</span>
      </Link>
    );
    if (mode !== 'in_person' && !venue?.join_link) tasks.push(
      <Link key="link" href={`/create?edit=${card.id}`} className="card evp-task card--tap" style={{ padding: 14 }}>
        <span className="grow"><b>{t('evp.taskAddLink')}</b><div className="caption">{t('evp.taskAddLinkBody')}</div></span>
        <span className="link">{t('evp.add')}</span>
      </Link>
    );
    if (tasks.length === 0) return null;
    const today = istDay(card.time_start) === istDay(now);
    return (
      <section className="stack" style={{ gap: 8 }}>
        <span className="label">{today ? t('evp.beforeStart') : t('evp.beforeDay', { day: weekdayLong(card.time_start, lang) })}</span>
        {tasks}
      </section>
    );
  })();

  const guestList = view === 'host' && (() => {
    const rows = (attendees ?? []).filter((a) => CONFIRMED.includes(a.status));
    const waiting = (attendees ?? []).filter((a) => a.status === 'waitlisted').length;
    const saved = (attendees ?? []).filter((a) => a.status === 'interested').length;
    return (
      <section className="stack" style={{ gap: 8 }}>
        <div className="row row--between">
          <span className="label">{card.capacity !== null ? t('evp.comingOf', { count: going, total: card.capacity }) : t('evp.comingCount', { count: going })}</span>
          <Link href={`/organizer/${card.id}`} className="link evp-row44" style={{ fontSize: '0.875rem' }}>{t('evp.checkIn')} ›</Link>
        </div>
        <div className="card stack" style={{ gap: 4, padding: '8px 14px' }}>
          {rows.length === 0 && <span className="caption evp-row44">{t('evp.nobodyYet')}</span>}
          {rows.map((a) => (
            <Link key={a.member_id} href={`/p/${a.member_id}`} className="evp-person">
              <Avatar src={a.avatar} name={a.display_name} size="lg" />
              <span className="grow" style={{ minWidth: 0 }}>
                <b className="truncate" style={{ display: 'block' }}>{a.display_name}</b>
                <span className="caption">
                  {[a.status !== 'going' ? t(`card.youAre.${a.status}`) : null, (a.guests ?? 0) > 0 ? t('guest.plusN', { count: a.guests }) : null, a.first_time ? t('belong.firstTime') : null, a.company === 'alone' ? t('belong.onTheirOwn') : null].filter(Boolean).join(' · ')}
                </span>
              </span>
            </Link>
          ))}
          {(waiting > 0 || saved > 0) && (
            <span className="caption" style={{ padding: '6px 0' }}>{[waiting > 0 ? t('evp.waitlistCount', { count: waiting }) : null, saved > 0 ? t('evp.savedCount', { count: saved }) : null].filter(Boolean).join(' · ')}</span>
          )}
        </div>
      </section>
    );
  })();

  const updateComposer = view === 'host' && !cancelled && (
    <section className="stack" style={{ gap: 8 }} id="send-update">
      {announcements.length === 0 && <><span className="label">{t('evp.yourUpdates')}</span><span className="caption">{t('evp.noUpdates')}</span></>}
      <label className="field" style={{ margin: 0 }}>
        <textarea value={updateText} onChange={(e) => setUpdateText(e.target.value)} placeholder={t('evp.updatePlaceholder')} maxLength={500} rows={2} />
      </label>
      <button className="btn btn--primary" style={{ alignSelf: 'flex-start' }} disabled={!updateText.trim() || busy} onClick={sendUpdate}>{t('evp.sendUpdate')}</button>
    </section>
  );

  /* ---------- the attendee's own blocks once going ---------- */
  const myPlan = view === 'going' && !cancelled && (
    <>
      {detail?.still_coming_due && status === 'going' && (
        <section className="card stack fade-in" style={{ gap: 10, borderColor: 'var(--accent-primary)' }} aria-label={t('show.stillComingTitle')}>
          <b className="title">{t('show.stillComingTitle')}</b>
          <span className="caption">{t('show.stillComingBody')}</span>
          <div className="row" style={{ gap: 8, flexWrap: 'wrap' }}>
            <button className="btn btn--primary grow" onClick={stillComing}>{t('show.stillComing')}</button>
            <button className="btn btn--secondary grow" onClick={() => (paidActivity && tk?.status === 'paid' ? setPayAsk(true) : void setRsvp('cancelled'))}>{t('show.freeSpot')}</button>
          </div>
        </section>
      )}
      {((detail?.max_guests_per_member ?? 0) > 0 || detail?.my_plan) && status === 'going' && (
        <section className="stack" style={{ gap: 8 }}>
          <span className="label">{t('show.yourPlan')}</span>
          <div className="card stack" style={{ gap: 10, padding: 14 }}>
            {(detail?.max_guests_per_member ?? 0) > 0 && (
              <div className="stack" style={{ gap: 6 }}>
                <b>{t('guest.bringingTitle')}</b>
                <div className="chips" role="radiogroup" aria-label={t('guest.bringingTitle')}>
                  {Array.from({ length: (detail?.max_guests_per_member ?? 0) + 1 }, (_, n) => (
                    <button key={n} type="button" className="chip chip--sm" aria-pressed={(detail?.my_guests ?? 0) === n} onClick={() => setGuests(n)}>
                      {n === 0 ? t('guest.justMe') : t('guest.plusN', { count: n })}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {detail?.my_plan && (detail.my_plan.travel && detail.my_plan.company && !planEdit ? (
              <div className="caption evp-row44">
                {t(`show.travel.${detail.my_plan.travel}`)} · {t(`show.company.${detail.my_plan.company}`)} · <button className="link" onClick={() => setPlanEdit(true)}>{t('show.change')}</button>
              </div>
            ) : (
              <div className="stack fade-in" style={{ gap: 8 }}>
                <b>{t('show.howGetting')}</b>
                <div className="chips">
                  {TRAVEL.map((v) => <button key={v} type="button" className="chip chip--sm" aria-pressed={detail.my_plan?.travel === v} onClick={() => savePlan({ travel: detail.my_plan?.travel === v ? null : v, company: detail.my_plan?.company ?? null })}>{t(`show.travel.${v}`)}</button>)}
                </div>
                <b>{t('show.comingWith')}</b>
                <div className="chips">
                  {COMPANY.map((v) => <button key={v} type="button" className="chip chip--sm" aria-pressed={detail.my_plan?.company === v} onClick={() => savePlan({ travel: detail.my_plan?.travel ?? null, company: detail.my_plan?.company === v ? null : v })}>{t(`show.company.${v}`)}</button>)}
                </div>
                <span className="caption">{t('show.planPrivacy')}</span>
              </div>
            ))}
            <button type="button" className="btn btn--secondary btn--sm" style={{ alignSelf: 'flex-start' }} onClick={sharePlan}>{t('belong.sharePlan')}</button>
          </div>
        </section>
      )}
      {detail?.first_time && status === 'going' && (
        <section className="card stack fade-in" style={{ gap: 6 }}>
          <b>{t('belong.firstTitle')}</b>
          <span className="caption">{t('belong.firstBody', { host: hostFirst, place: card.location_label })}</span>
        </section>
      )}
      {tk?.status === 'paid' && tk.qr_code && (
        <TicketQrCard code={tk.qr_code} typeName={tk.type_name ?? null} savedPaise={tk.discount_paise ?? 0} checkedIn={['checked_in', 'attended'].includes(status ?? '')} />
      )}
      {cards && cards.length > 0 && (
        <section className="card stack fade-in" style={{ gap: 8 }}>
          <div className="title">{t('cards.title')}</div>
          <p style={{ margin: 0, fontSize: '1.05rem' }}>{cards[cardIndex % cards.length]}</p>
          <button type="button" className="btn btn--secondary btn--sm" style={{ alignSelf: 'flex-start' }} onClick={() => setCardIndex((i) => i + 1)}>{t('cards.another')}</button>
        </section>
      )}
    </>
  );

  /* ---------- recap (D6) ---------- */
  const recap = view === 'recap' && (
    <>
      {ended && ['attended', 'checked_in'].includes(status ?? '') && !isOrganizer && detail?.thanked === false && !thanksSent && organizer && (
        <section className="card stack fade-in" style={{ gap: 10 }}>
          <div className="title">{t('belong.thanksTitle', { name: hostFirst })}</div>
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
      {organizer && !nextDate && (
        <Link href={`/p/${organizer.member_id}`} className="btn btn--secondary" style={{ alignSelf: 'flex-start' }}>{t('evp.moreFrom', { name: hostFirst })}</Link>
      )}
    </>
  );

  const moments = detail?.thread_access && (view === 'recap' || live) && <Moments occurrenceId={card.id} onError={say} />;

  return (
    <>
      {coverUrl && <div className="backdrop" aria-hidden="true" style={{ backgroundImage: `url(${coverUrl})` }} />}
      <div className={`evp-hero${coverUrl ? '' : ' evp-hero--grad'}${view !== 'deciding' ? ' evp-hero--short' : ''}`} style={coverUrl ? undefined : { background: CATEGORY_HUE[card.intent_category] ?? CATEGORY_HUE.meet }}>
        {coverUrl ? <img src={coverUrl} alt="" /> : <CategoryIcon category={card.intent_category} size={64} strokeWidth={1.25} />}
        <div className="evp-hero__top">
          <button className="icon-btn" aria-label={t('common.back')} onClick={() => (history.length > 1 ? router.back() : router.push('/'))}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M15 6l-6 6 6 6" /></svg>
          </button>
          {identity && view !== 'going' && (
            <button className="icon-btn" aria-label={t('common.more')} onClick={() => setMenu(true)}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><circle cx="5" cy="12" r="2" /><circle cx="12" cy="12" r="2" /><circle cx="19" cy="12" r="2" /></svg>
            </button>
          )}
        </div>
      </div>

      <div className="detail__grid">
      <main className="screen has-footer">
        {strip}
        {kicker}
        <h1 className="evp-title">{card.title}</h1>

        {view === 'deciding' && (
          <>
            {hostLine}{trustPanel}
            {facts}
            {paidActivity && tix && identity && !cancelled && !tk?.hold_active && tk?.status !== 'paid' && status !== 'waitlisted' && (
              <TicketPicker eventId={card.id} tix={tix} basePaise={card.price_paise ?? null} onChange={setChoice} />
            )}
            {goodToKnow}
            {about}
            {programme}
            {approxMap}
            {latestUpdate}
            {identity && !cancelled && <CohostPanel occurrenceId={card.id} ended={ended} />}
            {tix && organizer && <OrganizerContact tix={tix} organizerName={organizer.display_name} />}
            {seriesBlock}
            {safetyBlock}
          </>
        )}

        {view === 'going' && (
          <>
            {icsHref && istDay(card.time_start) !== istDay(now) && <a className="link evp-row44" style={{ alignSelf: 'flex-start' }} href={icsHref} download={`${card.slug}.ics`}>{t('detail.addToCalendar')}</a>}
            {latestUpdate}
            {whereToGo}
            {chatRow}
            <section className="stack" style={{ gap: 8 }}><span className="label">{t('evp.whosGoing')}</span>{whosGoing}</section>
            {myPlan}
            {goodToKnow}
            {about}
            {programme}
            {moments}
            {hostLine}{trustPanel}
            {tix && organizer && <OrganizerContact tix={tix} organizerName={organizer.display_name} />}
            {identity && !cancelled && <CohostPanel occurrenceId={card.id} ended={ended} />}
            {seriesBlock}
            {safetyBlock}
          </>
        )}

        {view === 'host' && (
          <>
            {hostTasks}
            {guestList}
            {latestUpdate}
            {updateComposer}
            {chatRow}
            {whereToGo}
            {moments}
            {goodToKnow}
            {about}
            {programme}
            {identity && !cancelled && <CohostPanel occurrenceId={card.id} ended={ended} />}
            {seriesBlock}
            {safetyBlock}
          </>
        )}

        {view === 'recap' && (
          <>
            {hostLine}{trustPanel}
            {moments}
            {recap}
            {seriesBlock}
            {detail?.thread_access && chatRow}
            {about}
            {programme}
            {identity && !cancelled && <CohostPanel occurrenceId={card.id} ended={ended} />}
          </>
        )}
      </main>

      {/* Desktop: the right card holds only the action, the price and the spots left; the facts appear once, on the left (D9). */}
      <aside className="detail__aside">
        <div className="detail__card card glass">
          <div className="evp-aside__price">
            <b>{tix?.tiered ? t('tix.fromPrice', { amount: priceLabel }) : priceLabel}</b>
            {spots && !ended && <span className="caption">{spots}</span>}
          </div>
          {untilLabel && !ended && <span className="caption">{whenLine} · {untilLabel}</span>}
          {bar && <div className="row" style={{ gap: 10 }}>{bar}</div>}
          {cancelled && <div className="pill pill--danger" style={{ alignSelf: 'flex-start' }}>{t('detail.cancelledBanner')}</div>}
        </div>
      </aside>
      </div>

      {bar && <div className="footer-sticky">{bar}</div>}

      <Sheet open={share} onClose={() => { setShare(false); setQrOpen(false); }} label={t('detail.share')}>
        <div className="stack">
          <h2 className="h2">{t('detail.share')}</h2>
          <div className="grid-2">
            <button className="btn btn--primary" onClick={() => doShare('whatsapp')}>WhatsApp</button>
            <button className="btn btn--secondary" onClick={sharePoster}>{t('detail.posterShare')}</button>
            {typeof navigator !== 'undefined' && 'share' in navigator && <button className="btn btn--secondary" onClick={() => doShare('native')}>{t('evp.shareNative')}</button>}
            <button className="btn btn--secondary" onClick={() => doShare('copy')}>{t('common.copy')}</button>
          </div>
          {share && (qrOpen ? <QrCode value={appUrl(`/a/${card.slug}`)} size={180} label={t('evp.qrLabel')} /> : <button className="link evp-row44" style={{ alignSelf: 'center' }} onClick={() => setQrOpen(true)}>{t('evp.showQr')}</button>)}
        </div>
      </Sheet>

      <Sheet open={menu} onClose={() => { setMenu(false); setHideAsk(false); }} label={t('common.more')}>
        <div className="stack">
          {isOrganizer && <Link href={`/organizer/${card.id}`} className="btn btn--secondary btn--block" onClick={() => setMenu(false)}>{t('evp.manage')}</Link>}
          {view === 'going' && !ended && status === 'going' && (
            <button className="btn btn--secondary btn--block" onClick={() => { setMenu(false); if (paidActivity && tk?.status === 'paid') setPayAsk(true); else void setRsvp('cancelled'); }}>{t('evp.cantMakeIt')}</button>
          )}
          {view === 'going' && <button className="btn btn--secondary btn--block" onClick={() => { setMenu(false); setShare(true); }}>{t('detail.share')}</button>}
          {!isOrganizer && view === 'deciding' && (hideAsk ? (
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
            {(pay?.refund_if_withdraw_now_paise ?? 0) > 0 ? t('pay.withdrawRefund', { amount: formatInr(pay?.refund_if_withdraw_now_paise ?? 0, lang) }) : t('pay.withdrawNoRefund')}
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

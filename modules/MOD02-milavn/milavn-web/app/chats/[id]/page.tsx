'use client';

/* A conversation — FR096 (trust-scoped messaging) + FR097 (expressive avatars).
 *
 * v3, 2026-09-14. The owner looked at v2 and asked, honestly, whether it looked
 * like a 2040 app. It did not: a glass "stage" panel spent a third of the phone
 * on two cartoons, every message carried its own "2 h ago", bubbles had
 * drop-shadowed tails, and seven emoji chips sat permanently above the keyboard.
 * v3 keeps Milavn's navy/saffron and every avatar feature, and fixes structure:
 *
 *  - Presence the Snapchat way ("Friends in Chat"): the other person's avatar
 *    rises above the composer only while they are actually here, mirrors their
 *    live expression and carries the typing dots. Away, the header says how
 *    long ago ("Active 12 min ago") instead of a flat "Not active".
 *  - Why you can talk (FR096): a slim strip names the next activity you share
 *    (else the circle) and links to it.
 *  - Messages read as a conversation, not a log: consecutive messages merge
 *    into one shaped group, day separators replace per-message timestamps, the
 *    time sits once under a group, reactions are a pill on the bubble's corner,
 *    and double-tap is a ❤️.
 *  - Your avatar is the mood button: a tray of *your* avatar in all seven
 *    expressions (tap = show your live mood, tap again = send it as a sticker)
 *    plus the opt-in on-device "Mirror my face" camera. Only a word leaves the
 *    device.
 *  - Quick replies appear only when the last message is theirs and you have
 *    not started typing, worded for the shared activity when there is one.
 */

import { CalendarDays, Camera, ChevronLeft, ImagePlus, Send, Trash2, Users } from 'lucide-react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { Fragment, useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';

import MoodAvatar from '@/components/MoodAvatar';
import { ErrorState, Toast } from '@/components/States';
import { API_BASE, api, ApiError, resolveMediaUrl } from '@/lib/api';
import { EXPRESSIONS, startExpressions, type Expression, type ExpressionSession } from '@/lib/expressions';
import { formatWhen } from '@/lib/format';
import { useIdentity } from '@/lib/identity';

type Person = { member_id: string; display_name: string; avatar: string | null; active: boolean; here?: boolean; expression: string | null; last_seen_at: string | null };
type SharedContext = { kind: 'activity' | 'circle'; title: string; ref: string; starts_at: string | null; locality: string | null };
type Conv = { id: string; kind: string; title: string; members: Person[]; active: boolean; expression: string | null; context: SharedContext | null };
type Msg = { id: string; member_id: string; display_name: string; avatar: string | null; kind: string; body: string | null; media_url: string | null; expression: string | null; created_at: string; mine: boolean; reactions: Record<string, string[]> };
type Ev = { type: string; message?: Msg; message_id?: string; member_id?: string; emoji?: string; present?: boolean; active?: boolean; expression?: string };
// here = this chat is open on their device right now (socket); active = used Milavn in the last two minutes (heartbeat).
type Live = { here: boolean; active: boolean; expression?: string; lastSeen?: string | null };

const IST = 'Asia/Kolkata';
const GROUP_GAP_MS = 10 * 60000; // one person's consecutive messages within this merge into one shaped group
const BREAK_MS = 45 * 60000; // a longer pause opens a new timestamped block; no per-message times (tap a message for its time)
const DOUBLE_TAP_MS = 280;
const QUICK = { activity: ['onMyWay', 'seeYouThere', 'late'], plain: ['soundsGood', 'countMeIn', 'thanks'] } as const;

const intl = (lang: string) => `${lang}-IN`;
const dayKey = (d: Date) => new Intl.DateTimeFormat('en-CA', { timeZone: IST }).format(d);
const clock = (iso: string, lang: string) => new Intl.DateTimeFormat(intl(lang), { timeZone: IST, hour: 'numeric', minute: '2-digit' }).format(new Date(iso));

export default function ChatRoomPage() {
  const { t, i18n } = useTranslation();
  const lang = i18n.language || 'en';
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { identity } = useIdentity();
  const [conv, setConv] = useState<Conv | null>(null);
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [reactions, setReactions] = useState<string[]>([]);
  const [error, setError] = useState(false);
  const [draft, setDraft] = useState('');
  const [typing, setTyping] = useState<string | null>(null);
  const [live, setLive] = useState<Record<string, Live>>({});
  const [menuFor, setMenuFor] = useState<string | null>(null);
  const [burst, setBurst] = useState<string | null>(null);
  const [trayOpen, setTrayOpen] = useState(false);
  const [camOn, setCamOn] = useState(false);
  const [myExpr, setMyExpr] = useState<Expression | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [now, setNow] = useState(() => Date.now()); // ticks every minute so "Active 3 min ago" stays true
  const wsRef = useRef<WebSocket | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const sessionRef = useRef<ExpressionSession | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const tapRef = useRef<{ id: string; at: number; timer: ReturnType<typeof setTimeout> } | null>(null);
  const typingTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const firstScroll = useRef(true);
  const say = (m: string) => { setToast(m); setTimeout(() => setToast(null), 2200); };
  const fail = (e: unknown) => say(e instanceof ApiError ? e.message : t('state.error'));

  const load = useCallback(() => {
    api<{ conversation: Conv; messages: Msg[]; reactions: string[] }>(`/chats/${id}`).then((r) => {
      setConv(r.conversation); setMsgs(r.messages); setReactions(r.reactions); setError(false);
      setLive((cur) => {
        const next: Record<string, Live> = {};
        r.conversation.members.forEach((m) => { next[m.member_id] = { here: !!m.here, active: m.active, expression: m.expression ?? cur[m.member_id]?.expression, lastSeen: m.last_seen_at }; });
        return next;
      });
      api(`/chats/${id}/read`, { body: {} }).catch(() => undefined);
    }).catch(() => setError(true));
  }, [id]);
  useEffect(load, [load]);
  useEffect(() => { const i = setInterval(() => setNow(Date.now()), 60000); return () => clearInterval(i); }, []);

  // Live channel; polling every 5 s covers the case where the socket cannot connect.
  useEffect(() => {
    if (!identity) return;
    let alive = true; let poll: ReturnType<typeof setInterval> | null = null;
    try {
      const ws = new WebSocket(`${API_BASE.replace(/^http/, 'ws')}/ws/chat?conversation=${id}`); wsRef.current = ws;
      ws.onmessage = (e) => {
        if (!alive) return;
        const ev: Ev = JSON.parse(e.data);
        if (ev.type === 'message' && ev.message) {
          const m = ev.message;
          setMsgs((cur) => (cur.some((x) => x.id === m.id) ? cur : [...cur, { ...m, mine: m.member_id === identity.member_id }]));
          if (m.member_id === typing) setTyping(null);
          api(`/chats/${id}/read`, { body: {} }).catch(() => undefined);
        }
        if (ev.type === 'reaction' && ev.message_id && ev.emoji && ev.member_id) {
          const { emoji, member_id: who } = ev;
          setMsgs((cur) => cur.map((m) => (m.id !== ev.message_id ? m : { ...m, reactions: { ...m.reactions, [emoji]: ev.present ? Array.from(new Set([...(m.reactions[emoji] ?? []), who])) : (m.reactions[emoji] ?? []).filter((x) => x !== who) } })));
        }
        if (ev.type === 'retract' && ev.message_id) setMsgs((cur) => cur.filter((m) => m.id !== ev.message_id));
        if (ev.type === 'typing' && ev.member_id && ev.member_id !== identity.member_id) {
          setTyping(ev.member_id);
          if (typingTimer.current) clearTimeout(typingTimer.current);
          typingTimer.current = setTimeout(() => setTyping(null), 3000);
        }
        if (ev.type === 'presence' && ev.member_id) {
          const who = ev.member_id;
          setLive((cur) => {
            const was = cur[who] ?? { here: false, active: false };
            const here = ev.active ?? was.here; // socket presence events are about this chat
            return { ...cur, [who]: { here, active: here, expression: ev.expression ?? was.expression, lastSeen: here ? was.lastSeen : new Date().toISOString() } };
          });
        }
      };
      ws.onerror = () => { if (!poll) poll = setInterval(load, 5000); };
      ws.onclose = () => { if (alive && !poll) poll = setInterval(load, 5000); };
    } catch { poll = setInterval(load, 5000); }
    return () => { alive = false; wsRef.current?.close(); wsRef.current = null; if (poll) clearInterval(poll); };
    // `typing` is read only to clear the dots early; re-subscribing on it would drop the socket.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, identity, load]);

  const others = conv?.members.filter((m) => m.member_id !== identity?.member_id) ?? [];
  const direct = conv?.kind === 'direct';
  const other = direct ? others[0] : undefined;
  const exprOf = (memberId: string) => (live[memberId]?.expression as Expression | undefined) ?? 'neutral';
  const here = others.filter((m) => live[m.member_id]?.here || typing === m.member_id).slice(0, 3);
  const typingName = typing ? conv?.members.find((m) => m.member_id === typing)?.display_name.split(' ')[0] : null;
  const ctx = conv?.context ?? null;
  const last = msgs[msgs.length - 1];
  const quick = last && !last.mine && !draft ? QUICK[ctx?.kind === 'activity' ? 'activity' : 'plain'] : [];

  // The footer is sticky, so "scroll the last bubble into view" would leave it underneath the composer: scroll the page to its end.
  useEffect(() => {
    const id = requestAnimationFrame(() => window.scrollTo({ top: document.documentElement.scrollHeight, behavior: firstScroll.current ? 'auto' : 'smooth' }));
    if (msgs.length) firstScroll.current = false;
    return () => cancelAnimationFrame(id);
  }, [msgs.length, here.length, typing, trayOpen, camOn]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') { setMenuFor(null); setTrayOpen(false); } };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const seenAgo = (iso: string | null | undefined) => {
    if (!iso) return t('chat.offline');
    const mins = Math.floor((now - new Date(iso).getTime()) / 60000);
    if (mins < 1) return t('chat.seenJustNow');
    if (mins < 60) return t('chat.seenMin', { count: mins });
    if (mins < 1440) return t('chat.seenHour', { count: Math.floor(mins / 60) });
    if (mins < 10080) return t('chat.seenDay', { count: Math.floor(mins / 1440) });
    return t('chat.offline');
  };
  const dayLabel = (iso: string) => {
    const k = dayKey(new Date(iso));
    if (k === dayKey(new Date(now))) return t('chat.today');
    if (k === dayKey(new Date(now - 86400000))) return t('chat.yesterday');
    return new Intl.DateTimeFormat(intl(lang), { timeZone: IST, weekday: 'long', day: 'numeric', month: 'long' }).format(new Date(iso));
  };

  const sendText = async (raw: string) => {
    const body = raw.trim(); if (!body) return;
    setDraft(''); if (inputRef.current) inputRef.current.style.height = '';
    try { const m = await api<Msg>(`/chats/${id}/messages`, { body: { kind: 'text', body }, idempotent: true }); setMsgs((cur) => (cur.some((x) => x.id === m.id) ? cur : [...cur, m])); }
    catch (e) { fail(e); setDraft(body); }
  };
  const sendSticker = async (e: Expression) => {
    setTrayOpen(false);
    try { const m = await api<Msg>(`/chats/${id}/messages`, { body: { kind: 'expression', expression: e }, idempotent: true }); setMsgs((cur) => (cur.some((x) => x.id === m.id) ? cur : [...cur, m])); }
    catch (err) { fail(err); }
  };
  const sendPhoto = async (file: File | undefined) => {
    if (!file) return;
    const form = new FormData(); form.append('photo', file);
    try { const m = await api<Msg>(`/chats/${id}/photos`, { form }); setMsgs((cur) => (cur.some((x) => x.id === m.id) ? cur : [...cur, m])); } catch (e) { fail(e); }
    finally { if (fileRef.current) fileRef.current.value = ''; }
  };
  // Optimistic toggle; the server's reaction event then sets the definitive state for everyone.
  const react = async (m: Msg, emoji: string) => {
    setMenuFor(null);
    if (!identity) return;
    const me = identity.member_id;
    setMsgs((cur) => cur.map((x) => {
      if (x.id !== m.id) return x;
      const who = x.reactions[emoji] ?? [];
      return { ...x, reactions: { ...x.reactions, [emoji]: who.includes(me) ? who.filter((w) => w !== me) : [...who, me] } };
    }));
    try { await api(`/chats/${id}/messages/${m.id}/reactions`, { body: { emoji } }); } catch (e) { fail(e); load(); }
  };
  const unsend = async (m: Msg) => {
    setMenuFor(null);
    setMsgs((cur) => cur.filter((x) => x.id !== m.id));
    try { await api(`/chats/${id}/messages/${m.id}`, { method: 'DELETE' }); } catch (e) { fail(e); load(); }
  };
  const onBubbleTap = (m: Msg, at: number) => {
    const prev = tapRef.current;
    if (prev && prev.id === m.id && at - prev.at < DOUBLE_TAP_MS) {
      clearTimeout(prev.timer); tapRef.current = null; setMenuFor(null);
      setBurst(m.id); setTimeout(() => setBurst(null), 750);
      if (identity && !(m.reactions['❤️'] ?? []).includes(identity.member_id)) void react(m, '❤️');
      return;
    }
    const timer = setTimeout(() => { tapRef.current = null; setTrayOpen(false); setMenuFor((cur) => (cur === m.id ? null : m.id)); }, DOUBLE_TAP_MS);
    tapRef.current = { id: m.id, at, timer };
  };
  const onType = (v: string) => {
    setDraft(v);
    const el = inputRef.current; if (el) { el.style.height = 'auto'; el.style.height = `${Math.min(el.scrollHeight, 132)}px`; }
    if (wsRef.current?.readyState === 1) wsRef.current.send(JSON.stringify({ type: 'typing' }));
  };
  const shareExpression = useCallback((e: Expression) => {
    setMyExpr(e);
    if (wsRef.current?.readyState === 1) wsRef.current.send(JSON.stringify({ type: 'expression', value: e }));
    else api('/presence', { body: { expression: e } }).catch(() => undefined);
  }, []);
  const pickMood = (e: Expression) => { if (myExpr === e && !camOn) void sendSticker(e); else shareExpression(e); };
  const toggleCam = async () => {
    if (camOn) { sessionRef.current?.stop(); sessionRef.current = null; setCamOn(false); return; }
    if (!videoRef.current) return;
    const s = await startExpressions(videoRef.current, shareExpression, () => say(t('chat.cameraFailed')));
    // Mirroring shows live in the dock, so the tray gets out of the way of the conversation.
    if (s) { sessionRef.current = s; setMyExpr(null); setCamOn(true); setTrayOpen(false); }
  };
  useEffect(() => () => { sessionRef.current?.stop(); }, []);

  const status = typingName
    ? t('chat.typing', { name: typingName })
    : direct
      ? (other && live[other.member_id]?.here ? t('chat.hereNow') : other && live[other.member_id]?.active ? t('chat.activeNow') : seenAgo(other ? live[other.member_id]?.lastSeen : null))
      : `${t('chat.members', { count: conv?.members.length ?? 0 })}${here.length ? ` · ${t('chat.hereCount', { count: here.length })}` : ''}`;

  const rows = msgs.map((m, i) => {
    const joins = (a?: Msg, b?: Msg) => !!a && !!b && a.member_id === b.member_id && a.kind !== 'expression' && b.kind !== 'expression'
      && dayKey(new Date(a.created_at)) === dayKey(new Date(b.created_at)) && new Date(b.created_at).getTime() - new Date(a.created_at).getTime() < GROUP_GAP_MS;
    const prev = msgs[i - 1];
    const newBlock = !prev || dayKey(new Date(prev.created_at)) !== dayKey(new Date(m.created_at)) || new Date(m.created_at).getTime() - new Date(prev.created_at).getTime() >= BREAK_MS;
    return { m, top: joins(prev, m), bottom: joins(m, msgs[i + 1]), newBlock };
  });

  return (
    <div className="room">
      <header className="room__head">
        <div className="room__bar">
          <button className="icon-btn room__ghost" aria-label={t('common.back')} onClick={() => (history.length > 1 ? router.back() : router.push('/chats'))}><ChevronLeft size={24} strokeWidth={2} aria-hidden="true" /></button>
          {direct && other ? (
            <Link href={`/p/${other.member_id}`} className="room__who">
              <MoodAvatar seed={other.member_id} expression={exprOf(other.member_id)} size={40} active={!!live[other.member_id]?.here} />
              <span className="room__whotext"><b className="truncate">{conv?.title}</b><span className={`room__status${typingName ? ' is-typing' : live[other.member_id]?.here ? ' is-here' : ''}`}>{status}</span></span>
            </Link>
          ) : (
            <div className="room__who">
              <span className="room__group" aria-hidden="true"><Users size={20} /></span>
              <span className="room__whotext"><b className="truncate">{conv?.title ?? ''}</b><span className={`room__status${typingName ? ' is-typing' : ''}`}>{status}</span></span>
            </div>
          )}
          <button className={`icon-btn room__ghost${camOn ? ' room__ghost--live' : ''}`} aria-pressed={camOn} aria-label={camOn ? t('chat.cameraOff') : t('chat.mirror')} title={t('chat.cameraHint')} onClick={toggleCam}><Camera size={20} strokeWidth={1.9} aria-hidden="true" /></button>
        </div>
        {ctx && (
          <Link href={ctx.kind === 'activity' ? `/a/${ctx.ref}` : `/circles/${ctx.ref}`} className="room__ctx">
            <span className="room__ctxicon" aria-hidden="true">{ctx.kind === 'activity' ? <CalendarDays size={15} /> : <Users size={15} />}</span>
            <span className="room__ctxlabel">{ctx.kind === 'activity' ? t('chat.nextTogether') : t('chat.sharedCircle')}</span>
            <b className="truncate">{ctx.title}</b>
            <span className="room__ctxmeta">{ctx.kind === 'activity' && ctx.starts_at ? formatWhen(ctx.starts_at, lang) : ctx.locality}</span>
          </Link>
        )}
      </header>

      <main className="room__thread" onClick={(e) => { if (e.target === e.currentTarget) setMenuFor(null); }}>
        {error && <ErrorState onRetry={load} />}
        {!conv && !error && <div className="room__loading">{[62, 44, 70].map((w, i) => <div key={i} className="sk" style={{ width: `${w}%`, height: 40, borderRadius: 18, alignSelf: i === 1 ? 'flex-end' : 'flex-start' }} />)}</div>}
        {conv && (
          <section className="room__intro">
            {direct && other ? <MoodAvatar seed={other.member_id} expression={exprOf(other.member_id)} size={76} /> :<span className="room__group room__group--lg" aria-hidden="true"><Users size={30} /></span>}
            <b className="room__introname">{conv.title}</b>
            <span className="room__introline">{t('chat.first')}</span>
          </section>
        )}

        {rows.map(({ m, top, bottom, newBlock }) => {
          const rx = Object.entries(m.reactions).filter(([, who]) => who.length > 0);
          return (
            <Fragment key={m.id}>
              {newBlock && <div className="room__day"><span>{dayLabel(m.created_at)} · {clock(m.created_at, lang)}</span></div>}
              <div className={`bub-row${m.mine ? ' bub-row--mine' : ''}${top ? ' bub-row--top' : ''}${bottom ? ' bub-row--bottom' : ''}${rx.length ? ' bub-row--rx' : ''}`}>
                {/* 1:1 needs no avatar beside each bubble (the header and the presence dock carry it); groups need to show who spoke. */}
                {!m.mine && !direct && (bottom
                  ? <span className="bub-row__avatar" aria-hidden="true" />
                  : <Link href={`/p/${m.member_id}`} className="bub-row__avatar" aria-label={m.display_name}><MoodAvatar seed={m.member_id} expression={exprOf(m.member_id)} size={28} idle={false} /></Link>)}
                <div className="bub-row__col">
                  {!m.mine && !top && !direct && <span className="bub-row__name">{m.display_name.split(' ')[0]}</span>}
                  <div className="bub-row__wrap">
                    {m.kind === 'expression' && m.expression ? (
                      <button type="button" className="sticker" onClick={(e) => onBubbleTap(m, e.timeStamp)} aria-haspopup="menu" aria-expanded={menuFor === m.id}>
                        <MoodAvatar seed={m.member_id} expression={m.expression as Expression} size={92} idle={false} label={`${m.display_name} · ${t(`chat.expr.${m.expression}`)}`} />
                      </button>
                    ) : (
                      <button type="button" className={`bub${m.kind === 'photo' ? ' bub--photo' : ''}`} onClick={(e) => onBubbleTap(m, e.timeStamp)} aria-haspopup="menu" aria-expanded={menuFor === m.id}>
                        {m.kind === 'photo' && m.media_url && <img src={resolveMediaUrl(m.media_url) ?? ''} alt={t('chat.photo')} />}
                        {m.kind === 'text' && m.body}
                      </button>
                    )}
                    {burst === m.id && <span className="bub-burst" aria-hidden="true">❤️</span>}
                    {rx.length > 0 && (
                      <span className="bub-rx">
                        {rx.map(([e, who]) => (
                          <button key={e} type="button" className={`bub-rx__item${identity && who.includes(identity.member_id) ? ' is-mine' : ''}`} onClick={() => react(m, e)} aria-label={`${e} ${who.length}`}>
                            {e}{who.length > 1 && <span>{who.length}</span>}
                          </button>
                        ))}
                      </span>
                    )}
                    {menuFor === m.id && (
                      <div className="rbar" role="menu" aria-label={t('chat.react')}>
                        <span className="rbar__time">{clock(m.created_at, lang)}</span>
                        {reactions.map((e) => <button key={e} type="button" role="menuitem" onClick={() => react(m, e)}>{e}</button>)}
                        {m.mine && <><span className="rbar__sep" aria-hidden="true" /><button type="button" role="menuitem" className="rbar__tool" aria-label={t('chat.unsend')} title={t('chat.unsend')} onClick={() => unsend(m)}><Trash2 size={17} aria-hidden="true" /></button></>}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </Fragment>
          );
        })}
        <div ref={bottomRef} />
      </main>

      <footer className="room__foot">
        {/* Presence dock: people here on the left; while you mirror your face, your own live avatar and a small camera preview on the right. */}
        <div className={`dock${here.length > 0 || camOn ? ' dock--on' : ''}`} aria-live="polite">
          <div className="dock__others">
            {here.map((p) => {
              const e = exprOf(p.member_id);
              return (
                <div key={p.member_id} className="dock__person">
                  <MoodAvatar seed={p.member_id} expression={e} size={here.length > 1 ? 46 : 58} label={`${p.display_name} · ${t(`chat.expr.${e}`)}`} />
                  {typing === p.member_id
                    ? <span className="dock__bubble" aria-label={t('chat.typing', { name: p.display_name.split(' ')[0] })}><i /><i /><i /></span>
                    : e !== 'neutral' && <span className="dock__bubble dock__bubble--mood">{t(`chat.expr.${e}`)}</span>}
                </div>
              );
            })}
          </div>
          <div className={`dock__me${camOn ? ' is-on' : ''}`}>
            {camOn && myExpr && <span className="dock__bubble dock__bubble--mood dock__bubble--me">{t(`chat.expr.${myExpr}`)}</span>}
            {camOn && <MoodAvatar seed={identity?.member_id ?? 'me'} expression={myExpr ?? 'neutral'} size={58} label={`${t('chat.you')} · ${t(`chat.expr.${myExpr ?? 'neutral'}`)}`} />}
            <video ref={videoRef} muted playsInline className="dock__cam" aria-hidden="true" />
          </div>
        </div>

        {trayOpen && (
          <div className="tray" role="dialog" aria-label={t('chat.trayTitle')}>
            <div className="tray__head"><b>{t('chat.trayTitle')}</b><span>{t('chat.trayHint')}</span></div>
            <div className="tray__grid">
              {EXPRESSIONS.map((e) => (
                <button key={e} type="button" className={`tray__item${myExpr === e ? ' is-on' : ''}`} aria-pressed={myExpr === e} onClick={() => pickMood(e)}>
                  <MoodAvatar seed={identity?.member_id ?? 'me'} expression={e} size={50} idle={false} />
                  <span>{myExpr === e && !camOn ? t('chat.sendIt') : t(`chat.expr.${e}`)}</span>
                </button>
              ))}
            </div>
            <button type="button" className={`tray__mirror${camOn ? ' is-on' : ''}`} aria-pressed={camOn} onClick={toggleCam}>
              <span className="tray__mirroricon" aria-hidden="true"><Camera size={18} /></span>
              <span><b>{camOn ? t('chat.mirrorOn') : t('chat.mirror')}</b><small>{t('chat.cameraHint')}</small></span>
            </button>
          </div>
        )}

        {quick.length > 0 && !trayOpen && (
          <div className="quick" role="group" aria-label={t('chat.quickLabel')}>
            {quick.map((k) => <button key={k} type="button" onClick={() => sendText(t(`chat.quick.${k}`))}>{t(`chat.quick.${k}`)}</button>)}
          </div>
        )}

        <div className="pill">
          <button type="button" className={`pill__me${myExpr && myExpr !== 'neutral' ? ' is-on' : ''}`} aria-expanded={trayOpen} aria-label={t('chat.mood')} onClick={() => { setMenuFor(null); setTrayOpen((o) => !o); }}>
            <MoodAvatar seed={identity?.member_id ?? 'me'} expression={myExpr ?? 'neutral'} size={36} idle={false} label={t('chat.you')} />
          </button>
          <textarea ref={inputRef} name="message" rows={1} value={draft} onChange={(e) => onType(e.target.value)} onFocus={() => setTrayOpen(false)} placeholder={t('chat.placeholder')} aria-label={t('chat.placeholder')} maxLength={2000} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); void sendText(draft); } }} />
          <input ref={fileRef} type="file" accept="image/*" hidden onChange={(e) => sendPhoto(e.target.files?.[0])} />
          {draft.trim()
            ? <button type="button" className="pill__send" aria-label={t('thread.send')} onClick={() => sendText(draft)}><Send size={18} aria-hidden="true" /></button>
            : <button type="button" className="pill__tool" aria-label={t('chat.photo')} onClick={() => fileRef.current?.click()}><ImagePlus size={21} strokeWidth={1.8} aria-hidden="true" /></button>}
        </div>
      </footer>
      <Toast text={toast} />
    </div>
  );
}

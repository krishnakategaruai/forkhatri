'use client';

/* A conversation: live over WebSocket (messages, reactions, typing, presence
 * and expressions), with polling as the fallback. Reactions replace likes.
 * Expressions come from the front camera analysed on the device (opt-in) or
 * from the manual mood picker; either way only a word is shared. */

import { Camera, CameraOff, ImagePlus, Send } from 'lucide-react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';

import MoodAvatar from '@/components/MoodAvatar';
import { ErrorState, Toast } from '@/components/States';
import { API_BASE, api, ApiError, resolveMediaUrl } from '@/lib/api';
import { EXPRESSION_EMOJI, EXPRESSIONS, startExpressions, type Expression, type ExpressionSession } from '@/lib/expressions';
import { formatRelative } from '@/lib/format';
import { useIdentity } from '@/lib/identity';

type Person = { member_id: string; display_name: string; avatar: string | null; active: boolean; expression: string | null };
type Conv = { id: string; kind: string; title: string; members: Person[]; active: boolean; expression: string | null };
type Msg = { id: string; member_id: string; display_name: string; avatar: string | null; kind: string; body: string | null; media_url: string | null; expression: string | null; created_at: string; mine: boolean; reactions: Record<string, string[]> };
type Ev = { type: string; message?: Msg; message_id?: string; member_id?: string; emoji?: string; present?: boolean; active?: boolean; expression?: string };

export default function ChatRoomPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { identity } = useIdentity();
  const [conv, setConv] = useState<Conv | null>(null);
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [reactions, setReactions] = useState<string[]>([]);
  const [error, setError] = useState(false);
  const [draft, setDraft] = useState('');
  const [typing, setTyping] = useState<string | null>(null);
  const [presence, setPresence] = useState<Record<string, { active: boolean; expression?: string }>>({});
  const [pickFor, setPickFor] = useState<string | null>(null);
  const [camOn, setCamOn] = useState(false);
  const [myExpr, setMyExpr] = useState<Expression | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const sessionRef = useRef<ExpressionSession | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const say = (m: string) => { setToast(m); setTimeout(() => setToast(null), 2200); };

  const load = useCallback(() => {
    api<{ conversation: Conv; messages: Msg[]; reactions: string[] }>(`/chats/${id}`).then((r) => {
      setConv(r.conversation); setMsgs(r.messages); setReactions(r.reactions); setError(false);
      const p: Record<string, { active: boolean; expression?: string }> = {}; r.conversation.members.forEach((m) => { p[m.member_id] = { active: m.active, expression: m.expression ?? undefined }; }); setPresence(p);
      api(`/chats/${id}/read`, { body: {} }).catch(() => undefined);
    }).catch(() => setError(true));
  }, [id]);
  useEffect(load, [load]);
  useEffect(() => { bottomRef.current?.scrollIntoView({ block: 'end' }); }, [msgs.length]);

  // Live channel; polling every 5 s covers the case where the socket cannot connect.
  useEffect(() => {
    if (!identity) return;
    let alive = true; let poll: ReturnType<typeof setInterval> | null = null;
    const url = `${API_BASE.replace(/^http/, 'ws')}/ws/chat?member=${identity.member_id}&conversation=${id}`;
    try {
      const ws = new WebSocket(url); wsRef.current = ws;
      ws.onmessage = (e) => {
        if (!alive) return;
        const ev: Ev = JSON.parse(e.data);
        if (ev.type === 'message' && ev.message) { const m = ev.message; setMsgs((cur) => (cur.some((x) => x.id === m.id) ? cur : [...cur, { ...m, mine: m.member_id === identity.member_id }])); api(`/chats/${id}/read`, { body: {} }).catch(() => undefined); }
        if (ev.type === 'reaction' && ev.message_id && ev.emoji && ev.member_id) setMsgs((cur) => cur.map((m) => m.id !== ev.message_id ? m : { ...m, reactions: { ...m.reactions, [ev.emoji!]: ev.present ? Array.from(new Set([...(m.reactions[ev.emoji!] ?? []), ev.member_id!])) : (m.reactions[ev.emoji!] ?? []).filter((x) => x !== ev.member_id) } }));
        if (ev.type === 'retract' && ev.message_id) setMsgs((cur) => cur.filter((m) => m.id !== ev.message_id));
        if (ev.type === 'typing' && ev.member_id && ev.member_id !== identity.member_id) { setTyping(ev.member_id); setTimeout(() => setTyping(null), 2500); }
        if (ev.type === 'presence' && ev.member_id) setPresence((cur) => ({ ...cur, [ev.member_id!]: { active: ev.active ?? cur[ev.member_id!]?.active ?? false, expression: ev.expression ?? cur[ev.member_id!]?.expression } }));
      };
      ws.onerror = () => { if (!poll) poll = setInterval(load, 5000); };
      ws.onclose = () => { if (alive && !poll) poll = setInterval(load, 5000); };
    } catch { poll = setInterval(load, 5000); }
    return () => { alive = false; wsRef.current?.close(); wsRef.current = null; if (poll) clearInterval(poll); };
  }, [id, identity, load]);

  const send = async () => {
    const body = draft.trim(); if (!body) return;
    setDraft('');
    try { const m = await api<Msg>(`/chats/${id}/messages`, { body: { kind: 'text', body }, idempotent: true }); setMsgs((cur) => (cur.some((x) => x.id === m.id) ? cur : [...cur, m])); }
    catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); setDraft(body); }
  };
  const sendPhoto = async (file: File | undefined) => {
    if (!file) return;
    const form = new FormData(); form.append('photo', file);
    try { const m = await api<Msg>(`/chats/${id}/photos`, { form }); setMsgs((cur) => [...cur, m]); } catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
    finally { if (fileRef.current) fileRef.current.value = ''; }
  };
  const react = async (m: Msg, emoji: string) => {
    setPickFor(null);
    try { await api(`/chats/${id}/messages/${m.id}/reactions`, { body: { emoji } }); if (!wsRef.current || wsRef.current.readyState !== 1) load(); } catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };
  const onType = (v: string) => { setDraft(v); if (wsRef.current?.readyState === 1) wsRef.current.send(JSON.stringify({ type: 'typing' })); };
  const shareExpression = useCallback((e: Expression) => {
    setMyExpr(e);
    if (wsRef.current?.readyState === 1) wsRef.current.send(JSON.stringify({ type: 'expression', value: e }));
    else api('/presence', { body: { expression: e } }).catch(() => undefined);
  }, []);
  const toggleCam = async () => {
    if (camOn) { sessionRef.current?.stop(); sessionRef.current = null; setCamOn(false); return; }
    if (!videoRef.current) return;
    const s = await startExpressions(videoRef.current, shareExpression, () => say(t('chat.cameraFailed')));
    if (s) { sessionRef.current = s; setCamOn(true); }
  };
  useEffect(() => () => { sessionRef.current?.stop(); }, []);

  const others = conv?.members.filter((m) => m.member_id !== identity?.member_id) ?? [];
  const activeOthers = others.filter((m) => presence[m.member_id]?.active);
  const typingName = typing ? conv?.members.find((m) => m.member_id === typing)?.display_name : null;

  return (
    <>
      <header className="topbar">
        <div className="row" style={{ gap: 10, minWidth: 0 }}>
          <button className="icon-btn" aria-label={t('common.back')} onClick={() => (history.length > 1 ? router.back() : router.push('/chats'))}>‹</button>
          {others[0] && conv?.kind === 'direct' ? <MoodAvatar seed={others[0].member_id} expression={(presence[others[0].member_id]?.expression as Expression) ?? 'neutral'} size={44} label={others[0].display_name} /> : <span className="avatar avatar--lg avatar--group">👥</span>}
          <div className="grow" style={{ minWidth: 0 }}>
            <div className="title truncate">{conv?.title ?? ''}</div>
            <div className="caption">
              {typingName ? t('chat.typing', { name: typingName }) : activeOthers.length > 0 ? `${t('chat.activeNow')}${others.length > 1 ? ` · ${activeOthers.length}` : ''}` : t('chat.offline')}
              {others[0] && presence[others[0].member_id]?.expression && <> · {EXPRESSION_EMOJI[presence[others[0].member_id].expression as Expression]}</>}
            </div>
          </div>
        </div>
        <button className={`icon-btn${camOn ? ' icon-btn--on' : ''}`} aria-pressed={camOn} aria-label={camOn ? t('chat.cameraOff') : t('chat.cameraOn')} title={t('chat.cameraHint')} onClick={toggleCam}>{camOn ? <Camera size={18} aria-hidden="true" /> : <CameraOff size={18} aria-hidden="true" />}</button>
      </header>
      <video ref={videoRef} muted playsInline className={`cam-preview${camOn ? ' cam-preview--on' : ''}`} aria-hidden="true" />
      <main className="screen chat" style={{ gap: 8 }}>
        {conv && identity && (
          <div className="stage" aria-label={t('chat.stage')}>
            {[...others, ...conv.members.filter((m) => m.member_id === identity.member_id)].map((m) => {
              const me = m.member_id === identity.member_id;
              const expr = me ? (myExpr ?? 'neutral') : ((presence[m.member_id]?.expression as Expression) ?? 'neutral');
              const active = me ? true : !!presence[m.member_id]?.active;
              return (
                <div key={m.member_id} className={`stage__person${active ? '' : ' stage__person--away'}`}>
                  <MoodAvatar seed={m.member_id} expression={expr} size={others.length > 2 ? 56 : 84} label={m.display_name} />
                  <span className="caption">{me ? t('chat.you') : m.display_name.split(' ')[0]}{active && !me ? ' ·' : ''}{active && !me && <span className="presence-inline" aria-label={t('chat.activeNow')} />}</span>
                </div>
              );
            })}
          </div>
        )}
        {error && <ErrorState onRetry={load} />}
        {conv && msgs.length === 0 && <p className="caption" style={{ textAlign: 'center', margin: '24px 0' }}>{t('chat.first')}</p>}
        {msgs.map((m, i) => {
          const prev = msgs[i - 1]; const grouped = prev && prev.member_id === m.member_id && new Date(m.created_at).getTime() - new Date(prev.created_at).getTime() < 3 * 60000;
          const rx = Object.entries(m.reactions).filter(([, who]) => who.length > 0);
          return (
            <div key={m.id} className={`msg${m.mine ? ' msg--mine' : ''}${grouped ? ' msg--grouped' : ''}`}>
              {!m.mine && !grouped && <Link href={`/p/${m.member_id}`} className="msg__avatar"><MoodAvatar seed={m.member_id} expression={(presence[m.member_id]?.expression as Expression) ?? 'neutral'} size={30} label={m.display_name} /></Link>}
              {!m.mine && grouped && <span className="msg__avatar msg__avatar--spacer" />}
              <div style={{ minWidth: 0 }}>
                {!m.mine && !grouped && conv?.kind === 'group' && <div className="msg__meta" style={{ marginBottom: 2 }}>{m.display_name}</div>}
                <button type="button" className={`msg__bubble${m.kind === 'expression' ? ' msg__bubble--expr' : ''}`} onClick={() => setPickFor(pickFor === m.id ? null : m.id)} aria-label={t('chat.react')}>
                  {m.kind === 'photo' && m.media_url && <img src={resolveMediaUrl(m.media_url) ?? ''} alt="" className="msg__photo" />}
                  {m.kind === 'expression' && <span style={{ fontSize: '2rem' }}>{EXPRESSION_EMOJI[m.expression as Expression] ?? ''}</span>}
                  {m.kind === 'text' && m.body}
                </button>
                {pickFor === m.id && (
                  <div className="react-picker fade-in" role="menu">
                    {reactions.map((e) => <button key={e} type="button" role="menuitem" onClick={() => react(m, e)}>{e}</button>)}
                  </div>
                )}
                {rx.length > 0 && <div className="msg__reactions">{rx.map(([e, who]) => <button key={e} type="button" className={`rx${identity && who.includes(identity.member_id) ? ' rx--mine' : ''}`} onClick={() => react(m, e)}>{e} {who.length}</button>)}</div>}
                {!grouped && <div className="msg__meta">{formatRelative(m.created_at)}</div>}
              </div>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </main>
      <div className="composer composer--chat">
        <div className="chips chips--scroll mood" aria-label={t('chat.mood')}>
          {EXPRESSIONS.map((e) => <button key={e} type="button" className={`chip chip--sm${myExpr === e ? ' chip--on' : ''}`} onClick={() => shareExpression(e)} aria-pressed={myExpr === e} title={t(`chat.expr.${e}`)}>{EXPRESSION_EMOJI[e]}</button>)}
        </div>
        <div className="row" style={{ gap: 8, alignItems: 'flex-end' }}>
          <button type="button" className="icon-btn" aria-label={t('chat.photo')} onClick={() => fileRef.current?.click()}><ImagePlus size={18} aria-hidden="true" /></button>
          <input ref={fileRef} type="file" accept="image/*" hidden onChange={(e) => sendPhoto(e.target.files?.[0])} />
          <textarea rows={1} value={draft} onChange={(e) => onType(e.target.value)} placeholder={t('chat.placeholder')} aria-label={t('chat.placeholder')} maxLength={2000} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); void send(); } }} />
          <button type="button" className="ask__go" aria-label={t('thread.send')} disabled={!draft.trim()} onClick={send}><Send size={18} aria-hidden="true" /></button>
        </div>
      </div>
      <Toast text={toast} />
    </>
  );
}

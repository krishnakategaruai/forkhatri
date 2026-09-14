'use client';

/* Chats — trust-scoped messaging (owner decision 2026-09-14). The list shows
 * 1:1 and group conversations with presence (active now), the other person's
 * live expression, and unread counts. New chats start from people you already
 * share an activity or a circle with. */

import { MessageSquarePlus } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import MoodAvatar from '@/components/MoodAvatar';
import { Sheet } from '@/components/Sheet';
import { EmptyState, ErrorState, Toast } from '@/components/States';
import TopActions from '@/components/TopActions';
import { api, ApiError, resolveMediaUrl } from '@/lib/api';
import { type Expression } from '@/lib/expressions';
import { formatRelative } from '@/lib/format';

type Conv = { id: string; kind: string; title: string; avatar: string | null; active: boolean; expression: string | null; last_message_at: string | null; last_preview: string | null; unread: number; members: { member_id: string; display_name: string; avatar: string | null; active: boolean }[] };
type Person = { member_id: string; display_name: string; avatar: string | null; reason: string };

export default function ChatsPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const [convs, setConvs] = useState<Conv[] | null>(null);
  const [error, setError] = useState(false);
  const [open, setOpen] = useState(false);
  const [people, setPeople] = useState<Person[]>([]);
  const [picked, setPicked] = useState<string[]>([]);
  const [title, setTitle] = useState('');
  const [toast, setToast] = useState<string | null>(null);
  const say = (m: string) => { setToast(m); setTimeout(() => setToast(null), 2200); };

  const load = useCallback(() => { setError(false); api<{ conversations: Conv[] }>('/chats').then((r) => setConvs(r.conversations)).catch(() => setError(true)); }, []);
  useEffect(() => { load(); const id = setInterval(load, 15000); return () => clearInterval(id); }, [load]);

  const startNew = async () => { setOpen(true); setPicked([]); setTitle(''); try { setPeople(await api<Person[]>('/people/suggestions')); } catch { setPeople([]); } };
  const go = async () => {
    try {
      if (picked.length === 1 && !title.trim()) { const r = await api<{ id: string }>('/chats/direct', { body: { member_id: picked[0] } }); router.push(`/chats/${r.id}`); return; }
      const r = await api<{ id: string }>('/chats/group', { body: { title: title.trim() || t('chat.groupDefault'), member_ids: picked } }); router.push(`/chats/${r.id}`);
    } catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  return (
    <>
      <header className="topbar"><h1>{t('chat.title')}</h1><div className="row" style={{ gap: 8 }}><button className="btn btn--primary btn--sm" onClick={startNew}><MessageSquarePlus size={16} aria-hidden="true" /> {t('chat.new')}</button><TopActions /></div></header>
      <main className="screen">
        <p className="caption" style={{ margin: 0 }}>{t('chat.scope')}</p>
        {error && <ErrorState onRetry={load} />}
        {!convs && !error && <div className="stack">{[0, 1, 2].map((i) => <div key={i} className="sk" style={{ height: 72 }} />)}</div>}
        {convs && convs.length === 0 && <EmptyState message={t('chat.empty')} action={t('chat.new')} onAction={startNew} />}
        {convs && convs.length > 0 && (
          <div className="list">
            {convs.map((c) => (
              <Link key={c.id} href={`/chats/${c.id}`} className={`lrow lrow--tap chatrow${c.unread ? ' chatrow--unread' : ''}`}>
                <span className="chatrow__avatar">
                  {c.avatar ? <img className="avatar avatar--lg" src={resolveMediaUrl(c.avatar) ?? ''} alt="" /> : <span className="avatar avatar--lg avatar--group">{c.kind === 'group' ? '👥' : ''}</span>}
                  {c.active && <span className="presence-dot" aria-label={t('chat.activeNow')} />}
                  {c.expression && c.kind === 'direct' && c.members.filter((m) => m.member_id !== '')[0] && <span className="expr-badge" aria-hidden="true"><MoodAvatar seed={c.members.find((m) => m.avatar === c.avatar)?.member_id ?? c.id} expression={c.expression as Expression} size={26} /></span>}
                </span>
                <span className="grow" style={{ minWidth: 0 }}>
                  <span className="row row--between"><b className="truncate">{c.title}</b>{c.last_message_at && <span className="caption">{formatRelative(c.last_message_at)}</span>}</span>
                  <span className="caption truncate" style={{ display: 'block' }}>{c.last_preview ?? (c.active ? t('chat.activeNow') : t('chat.sayHello'))}</span>
                </span>
                {c.unread > 0 && <span className="nav__badge nav__badge--inline">{c.unread > 9 ? '9+' : c.unread}</span>}
              </Link>
            ))}
          </div>
        )}
      </main>
      <Sheet open={open} onClose={() => setOpen(false)} label={t('chat.new')}>
        <div className="stack" style={{ gap: 12 }}>
          <h2 className="h2">{t('chat.new')}</h2>
          <p className="caption" style={{ margin: 0 }}>{t('chat.scope')}</p>
          {people.length === 0 && <p className="caption" style={{ margin: 0 }}>{t('chat.nobodyYet')}</p>}
          <div className="list" style={{ maxHeight: '40vh', overflowY: 'auto' }}>
            {people.map((p) => (
              <button key={p.member_id} className="lrow lrow--tap" style={{ width: '100%', textAlign: 'left' }} aria-pressed={picked.includes(p.member_id)} onClick={() => setPicked((c) => (c.includes(p.member_id) ? c.filter((x) => x !== p.member_id) : [...c, p.member_id]))}>
                {p.avatar ? <img className="avatar avatar--lg" src={resolveMediaUrl(p.avatar) ?? ''} alt="" /> : <span className="avatar avatar--lg" />}
                <span className="grow"><b>{p.display_name}</b><br /><span className="caption">{p.reason}</span></span>
                <span className={`check${picked.includes(p.member_id) ? ' check--on' : ''}`} aria-hidden="true">✓</span>
              </button>
            ))}
          </div>
          {picked.length > 1 && <label className="field"><input className="field__input" placeholder={t('chat.groupName')} value={title} onChange={(e) => setTitle(e.target.value)} maxLength={80} /></label>}
          <button className="btn btn--primary btn--block" disabled={picked.length === 0} onClick={go}>{picked.length > 1 ? t('chat.startGroup', { count: picked.length }) : t('chat.start')}</button>
        </div>
      </Sheet>
      <Toast text={toast} />
    </>
  );
}

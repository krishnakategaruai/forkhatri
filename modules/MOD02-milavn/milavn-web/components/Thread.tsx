'use client';

/* Occurrence thread — simple coordination for the people who are going and
 * the organizer(s) (Meetup's event chat, WhatsApp's coordination habit, kept
 * private to the RSVP list). Not a feed: no likes, no reactions. */

import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { api, ApiError, resolveMediaUrl } from '@/lib/api';
import { formatRelative } from '@/lib/format';

export type ThreadMessage = { id: string; member_id: string; display_name: string; avatar: string | null; body: string; created_at: string; mine: boolean };

export default function Thread({ occurrenceId, onError }: { occurrenceId: string; onError: (m: string) => void }) {
  const { t } = useTranslation();
  const [messages, setMessages] = useState<ThreadMessage[] | null>(null);
  const [draft, setDraft] = useState('');
  const [sending, setSending] = useState(false);

  const load = useCallback(() => {
    api<{ messages: ThreadMessage[] }>(`/occurrences/${occurrenceId}/messages`).then((r) => setMessages(r.messages)).catch(() => setMessages([]));
  }, [occurrenceId]);
  useEffect(() => { load(); const id = setInterval(load, 15000); return () => clearInterval(id); }, [load]);

  const send = async () => {
    const body = draft.trim();
    if (!body || sending) return;
    setSending(true);
    try {
      await api(`/occurrences/${occurrenceId}/messages`, { body: { body }, idempotent: true });
      setDraft(''); load();
    } catch (e) { onError(e instanceof ApiError ? e.message : t('state.error')); }
    finally { setSending(false); }
  };

  const retract = async (m: ThreadMessage) => {
    setMessages((cur) => (cur ?? []).filter((x) => x.id !== m.id));
    await api(`/occurrences/${occurrenceId}/messages/${m.id}`, { method: 'DELETE' }).catch(() => load());
  };

  return (
    <section className="card stack" style={{ gap: 12 }}>
      <div className="row row--between">
        <span className="label">{t('thread.title')}</span>
        <span className="caption">{t('thread.private')}</span>
      </div>
      {messages === null && <div className="stack">{[0, 1].map((i) => <div key={i} className="sk" style={{ height: 44, width: '70%' }} />)}</div>}
      {messages && messages.length === 0 && <p className="caption" style={{ margin: 0 }}>{t('thread.empty')}</p>}
      {messages && messages.length > 0 && (
        <div className="thread">
          {messages.map((m) => (
            <div key={m.id} className={`msg${m.mine ? ' msg--mine' : ''}`}>
              {!m.mine && (
                <Link href={`/p/${m.member_id}`} aria-label={m.display_name}>
                  {m.avatar ? <img className="avatar" src={resolveMediaUrl(m.avatar) ?? ''} alt="" /> : <span className="avatar" />}
                </Link>
              )}
              <div>
                <div className="msg__bubble">{m.body}</div>
                <div className="msg__meta">
                  {!m.mine && <>{m.display_name} · </>}{formatRelative(m.created_at)}
                  {m.mine && <> · <button className="link" style={{ fontSize: '0.75rem' }} onClick={() => retract(m)}>{t('thread.retract')}</button></>}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      <div className="composer">
        <textarea rows={1} value={draft} onChange={(e) => setDraft(e.target.value)} placeholder={t('thread.placeholder')} aria-label={t('thread.placeholder')} maxLength={1000}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); void send(); } }} />
        <button className="btn btn--primary btn--sm btn--spring" disabled={!draft.trim() || sending} onClick={send}>{t('thread.send')}</button>
      </div>
    </section>
  );
}

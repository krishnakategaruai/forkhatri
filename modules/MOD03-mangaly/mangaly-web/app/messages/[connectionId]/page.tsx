'use client';

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Avatar } from '@/components/Avatar';
import { requireSession, type Session } from '@/lib/auth';
import { getConnection } from '@/lib/connections';
import { closeConversation, listMessages, sendMessage, type Message } from '@/lib/messages';
import { viewProfile, type Profile } from '@/lib/profile';

/* FR049/FR050 · UX21 "Conversation thread"
 *
 * [2026-09-17, DEC-V1-021] The thread is a session, not a history: when either
 * person leaves it — closing the tab, switching away, pressing back, or
 * tapping "End chat" — every message the two wrote is deleted for both, and
 * the thread reopens empty. The banner says this plainly, and says the one
 * thing the app cannot do: a browser cannot stop a screenshot or a screen
 * recording, so anything sent here can still be captured by the other person.
 * Saying so is the honest version of UX21's capture-risk disclosure; claiming
 * screenshot protection would be a promise no web app can keep."
 *
 * First-open-per-thread capture-risk disclosure (UX21) is simplified to a
 * persistent header tag for this pass rather than a one-time bottom sheet —
 * the honest-disclosure content is the same, just always-visible instead of
 * dismissible-once (a deliberate, documented scope simplification, not a
 * missing feature: the privacy fact is stated either way). The header
 * identifies the other party by name+photo — safe here specifically because
 * a thread only exists for an ACCEPTED connection, which is exactly what
 * already unlocked their full profile (see `communication` route's own
 * docstring on the backend). */

export default function ThreadPage() {
  const { t } = useTranslation(['common', 'messages']);
  const router = useRouter();
  const params = useParams<{ connectionId: string }>();
  const connectionId = params.connectionId;

  const [session, setSession] = useState<Session | null>(null);
  const [other, setOther] = useState<Profile | null>(null);
  const [otherAccountId, setOtherAccountId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [phase, setPhase] = useState<'checking' | 'ready'>('checking');

  async function refresh() {
    const rows = await listMessages(connectionId);
    setMessages(rows);
  }

  /* Leaving ends the session for both people. `pagehide` covers closing the
     tab and navigating away; `visibilitychange` covers switching apps on a
     phone, which is where a matrimony conversation is actually read. */
  useEffect(() => {
    const end = () => void closeConversation(connectionId);
    const onHidden = () => {
      if (document.visibilityState === 'hidden') end();
    };
    window.addEventListener('pagehide', end);
    document.addEventListener('visibilitychange', onHidden);
    return () => {
      window.removeEventListener('pagehide', end);
      document.removeEventListener('visibilitychange', onHidden);
    };
  }, [connectionId]);

  useEffect(() => {
    let active = true;
    (async () => {
      const s = await requireSession();
      if (!active) return;
      if (!s) {
        // requireSession() has already handed off to the ForKhatri entrance (TR16).
        return;
      }
      setSession(s);

      const conn = await getConnection(connectionId);
      if (active && conn) {
        const otherAccountId = conn.acting_account_id === s.account_id ? conn.target_account_id : conn.acting_account_id;
        const otherProfile = await viewProfile(otherAccountId);
        if (active) {
          setOther(otherProfile);
          setOtherAccountId(otherAccountId);
        }
      }

      await refresh();
      if (!active) return;
      setPhase('ready');
    })();
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [connectionId, router]);

  if (phase === 'checking' || !session) {
    return (
      <main className="screen screen--centered">
        <p className="caption">{t('common:state.loading')}</p>
      </main>
    );
  }

  async function onSend(e: React.FormEvent) {
    e.preventDefault();
    if (!draft.trim()) return;
    setBusy(true);
    setError(null);
    const outcome = await sendMessage(connectionId, draft.trim());
    setBusy(false);
    if (!outcome.ok) {
      setError(
        outcome.message ?? (outcome.status === 0 ? t('messages:error.network') : t('messages:error.rateLimited'))
      );
      return;
    }
    setDraft('');
    await refresh();
  }

  return (
    <>
      <header className="topbar">
        <button className="icon-btn" onClick={() => router.push('/messages')} aria-label={t('common:action.back')}>
          ←
        </button>
        <Link
          href={otherAccountId ? `/profile/${otherAccountId}?connection=${connectionId}` : '#'}
          aria-label={other?.name ?? t('messages:title')}
          style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0, flex: 1, color: 'inherit', textDecoration: 'none' }}
        >
          <Avatar photoUrl={other?.photo_url} name={other?.name} size={36} />
          <span style={{ fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {other?.name ?? t('messages:title')}
          </span>
        </Link>
        <span className="pill pill--live" style={{ flex: 'none' }}>
          {t('messages:thread.privacyTag')}
        </span>
      </header>

      <main className="screen">
        <p className="caption thread-session-note">{t('messages:thread.sessionNote')}</p>

        {messages.length === 0 ? (
          <p className="caption">{t('messages:thread.empty')}</p>
        ) : (
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {messages.map((m) => {
              if (m.kind === 'system') {
                return (
                  <p key={m.id} className="caption thread-system" role="status">
                    {t(`messages:${m.content}`)}
                  </p>
                );
              }
              const mine = m.sender_account_id === session.account_id;
              return (
                <div
                  key={m.id}
                  style={{
                    alignSelf: mine ? 'flex-end' : 'flex-start',
                    background: mine ? 'var(--accent-tint)' : 'var(--surface-sunken)',
                    borderRadius: 12,
                    padding: '8px 12px',
                    maxWidth: '80%',
                  }}
                >
                  <p style={{ margin: 0 }}>{m.content}</p>
                  <span className="caption">{new Date(m.sent_at).toLocaleTimeString()}</span>
                </div>
              );
            })}
          </div>
        )}

        <p className="form__error">{error ?? ''}</p>

        <form className="form__actions" onSubmit={onSend} style={{ flexDirection: 'row', gap: 8 }}>
          <div className="field__box" style={{ flex: 1 }}>
            <input
              className="field__input"
              placeholder={t('messages:thread.placeholder')}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              disabled={busy}
            />
          </div>
          <button className="cta" style={{ width: 'auto', padding: '0 20px' }} disabled={busy || !draft.trim()}>
            {t('messages:thread.send')}
          </button>
        </form>

        <button
          type="button"
          className="quick-pick__chip"
          style={{ alignSelf: 'flex-start' }}
          onClick={async () => {
            await closeConversation(connectionId);
            router.push('/messages');
          }}
        >
          {t('messages:thread.endSession')}
        </button>
      </main>
    </>
  );
}

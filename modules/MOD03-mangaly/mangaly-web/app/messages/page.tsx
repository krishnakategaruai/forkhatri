'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Avatar } from '@/components/Avatar';
import { getSession } from '@/lib/auth';
import { listConversations, type ConversationSummary } from '@/lib/messages';

/* FR049 · UX21 — Conversation list, pure recency order, no seriousness/
 * exclusivity ranking. Available immediately once a connection is
 * accepted — the list itself only ever shows conversations that already
 * have at least one message (the lazy-created conversation row implies
 * that; see `communication.interface`'s own docstring on the backend). */

export default function MessagesPage() {
  const { t } = useTranslation(['common', 'messages']);
  const router = useRouter();
  const [phase, setPhase] = useState<'checking' | 'ready'>('checking');
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);

  useEffect(() => {
    let active = true;
    (async () => {
      const session = await getSession();
      if (!active) return;
      if (!session) {
        router.replace('/login');
        return;
      }
      const rows = await listConversations();
      if (!active) return;
      setConversations(rows);
      setPhase('ready');
    })();
    return () => {
      active = false;
    };
  }, [router]);

  if (phase === 'checking') {
    return (
      <main className="screen screen--centered">
        <p className="caption">{t('common:state.loading')}</p>
      </main>
    );
  }

  return (
    <>
      <header className="topbar">
        <h1>{t('messages:title')}</h1>
      </header>
      <main className="screen">
        {conversations.length === 0 ? (
          <p className="caption">{t('messages:empty')}</p>
        ) : (
          <ul className="category-list">
            {conversations.map((c) => (
              <li key={c.connection_id}>
                <Link href={`/messages/${c.connection_id}`} className="category-card">
                  <Avatar photoUrl={c.other_photo_url} name={c.other_name} size={48} />
                  <span className="category-card__body">
                    <span className="category-card__title">{c.other_name ?? t('messages:title')}</span>
                    <span className="category-card__preview">
                      {c.last_message_at ? new Date(c.last_message_at).toLocaleString() : ''}
                    </span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </main>
    </>
  );
}

'use client';

/* Notification inbox (FR051-FR055, FR086 · UX12 · UI12): four classes with a
 * visibly distinct "always delivered" Important treatment, mark read,
 * swipe/tap dismiss, per-class settings (Important locked). */

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Sheet } from '@/components/Sheet';
import { EmptyState, ErrorState } from '@/components/States';
import { api } from '@/lib/api';
import { formatRelative } from '@/lib/format';

type Entry = { id: string; class: string; title: string; body: string; deep_link: string | null; read_at: string | null; created_at: string };
type Prefs = Record<string, { muted: boolean; frequency: string; locked?: boolean }>;
const ICON: Record<string, string> = { important: '!', useful: '⏰', social: '👋', opportunity: '✨' };

export default function NotificationsPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const [entries, setEntries] = useState<Entry[] | null>(null);
  const [error, setError] = useState(false);
  const [prefs, setPrefs] = useState<Prefs | null>(null);
  const [settings, setSettings] = useState(false);

  const load = useCallback(() => { setError(false); api<{ entries: Entry[] }>('/notifications').then((r) => setEntries(r.entries)).catch(() => setError(true)); }, []);
  useEffect(load, [load]);

  const markAll = async () => { await api('/notifications/read', { body: {} }); load(); };
  const open = async (e: Entry) => { if (!e.read_at) await api(`/notifications/${e.id}/read`, { body: {} }).catch(() => undefined); };
  const dismiss = async (e: Entry) => { setEntries((cur) => (cur ?? []).filter((x) => x.id !== e.id)); await api(`/notifications/${e.id}`, { method: 'DELETE' }).catch(() => undefined); };
  const openSettings = async () => { setSettings(true); setPrefs(await api<Prefs>('/notifications/preferences')); };
  const toggle = async (cls: string) => {
    if (!prefs || prefs[cls].locked) return;
    setPrefs(await api<Prefs>('/notifications/preferences', { method: 'PUT', body: { notification_class: cls, muted: !prefs[cls].muted, frequency: prefs[cls].frequency } }));
  };

  return (
    <>
      <header className="topbar">
        <div className="row" style={{ gap: 10 }}>
          <button className="icon-btn" aria-label={t('common.back')} onClick={() => (history.length > 1 ? router.back() : router.push('/'))}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M15 6l-6 6 6 6" /></svg>
          </button>
          <h1>{t('notifications.title')}</h1>
        </div>
        <div className="row">
          {entries && entries.some((e) => !e.read_at) && <button className="link" onClick={markAll}>{t('notifications.markAll')}</button>}
          <button className="icon-btn" aria-label={t('notifications.settings')} onClick={openSettings}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true"><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z" /></svg>
          </button>
        </div>
      </header>
      <main className="screen">
        {error && <ErrorState onRetry={load} />}
        {!entries && !error && <div className="stack">{[0, 1, 2].map((i) => <div key={i} className="sk" style={{ height: 72 }} />)}</div>}
        {entries && entries.length === 0 && <EmptyState message={t('notifications.empty')} />}
        {entries && entries.map((e) => (
          <div key={e.id} className={`notif fade-in${e.read_at ? '' : ' notif--unread'}`}>
            <span className={`notif__cls cls-${e.class}`} aria-label={t(`notifications.classes.${e.class}`)}>{ICON[e.class]}</span>
            <Link href={e.deep_link ?? '#'} className="grow" onClick={() => open(e)}>
              <div className="title" style={{ fontSize: '0.9375rem' }}>{e.title}</div>
              <div className="caption">{e.body}</div>
              <div className="caption" style={{ marginTop: 4 }}>{e.class === 'important' ? <span className="pill pill--important" style={{ marginRight: 6 }}>{t('notifications.classes.important')}</span> : null}{formatRelative(e.created_at)}</div>
            </Link>
            <button className="icon-btn" style={{ minWidth: 36, minHeight: 36, border: 0 }} aria-label={t('notifications.dismiss')} onClick={() => dismiss(e)}>×</button>
          </div>
        ))}
      </main>
      <Sheet open={settings} onClose={() => setSettings(false)} label={t('notifications.settings')}>
        <div className="stack">
          <h2 className="h2">{t('notifications.settings')}</h2>
          {prefs && ['important', 'useful', 'social', 'opportunity'].map((cls) => (
            <div key={cls} className="row row--between" style={{ minHeight: 48 }}>
              <span>
                <b>{t(`notifications.classes.${cls}`)}</b>
                {cls === 'important' && <><br /><span className="caption">{t('notifications.alwaysOn')}</span></>}
              </span>
              <button className="switch" role="switch" aria-checked={!prefs[cls].muted} disabled={!!prefs[cls].locked} onClick={() => toggle(cls)} aria-label={t(`notifications.classes.${cls}`)} />
            </div>
          ))}
        </div>
      </Sheet>
    </>
  );
}

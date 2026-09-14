'use client';

/* Calendar (FR026-FR029 · UX10 · UI10): Mine (personal), Community, and a
 * per-circle view; grouped by day; the same card component everywhere. */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';

import ActivityCard from '@/components/ActivityCard';
import TopActions from '@/components/TopActions';
import { CardSkeleton, EmptyState, ErrorState } from '@/components/States';
import { api, type Card, type Circle } from '@/lib/api';

type Tab = 'personal' | 'community' | 'circle';

export default function CalendarPage() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<Tab>('personal');
  const [circles, setCircles] = useState<Circle[]>([]);
  const [circleId, setCircleId] = useState<string>('');
  const [cards, setCards] = useState<Card[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => { api<Circle[]>('/circles/mine').then((c) => { setCircles(c); if (c[0]) setCircleId((v) => v || c[0].id); }).catch(() => undefined); }, []);

  const load = useCallback(() => {
    setError(false); setCards(null);
    const path = tab === 'personal' ? '/calendar/personal' : tab === 'community' ? '/calendar/community' : circleId ? `/calendar/circle/${circleId}` : null;
    if (!path) { setCards([]); return; }
    api<Card[]>(path).then(setCards).catch(() => setError(true));
  }, [tab, circleId]);
  useEffect(load, [load]);

  const grouped = useMemo(() => {
    const m = new Map<string, Card[]>();
    (cards ?? []).forEach((c) => {
      const key = new Intl.DateTimeFormat('en-IN', { timeZone: 'Asia/Kolkata', weekday: 'long', day: 'numeric', month: 'long' }).format(new Date(c.time_start));
      m.set(key, [...(m.get(key) ?? []), c]);
    });
    return [...m.entries()];
  }, [cards]);

  return (
    <>
      <header className="topbar"><h1>{t('calendar.title')}</h1><TopActions /></header>
      <main className="screen">
        <div className="toggle" role="tablist">
          {(['personal', 'community', 'circle'] as Tab[]).map((k) => <button key={k} role="tab" aria-pressed={tab === k} aria-selected={tab === k} onClick={() => setTab(k)}>{t(`calendar.${k}`)}</button>)}
        </div>
        {tab === 'circle' && (
          <select className="field__input" value={circleId} onChange={(e) => setCircleId(e.target.value)} aria-label={t('calendar.circle')}>
            {circles.length === 0 && <option value="">{t('circles.emptyMine')}</option>}
            {circles.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        )}
        {error && <ErrorState onRetry={load} />}
        {!cards && !error && <CardSkeleton />}
        {cards && cards.length === 0 && <EmptyState message={tab === 'community' ? t('calendar.emptyCommunity') : t('calendar.empty')} />}
        {grouped.map(([day, list]) => (
          <section key={day} className="stack fade-in" style={{ gap: 10 }}>
            <div className="section__head"><h2 style={{ fontSize: '1.05rem' }}>{day}</h2><span className="count-chip">{list.length}</span></div>
            <div className="rail">{list.map((c) => <ActivityCard key={c.id} card={c} compact />)}</div>
          </section>
        ))}
      </main>
    </>
  );
}

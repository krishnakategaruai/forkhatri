'use client';

/* People discovery (FR042-FR045 · UX14 · UI14): a plain list, every person
 * with a real reason, no swipe/match, activity-framed copy only. Block is
 * reachable from here (FR062). */

import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { EmptyState, ErrorState, Toast } from '@/components/States';
import { api, ApiError, resolveMediaUrl } from '@/lib/api';

type Person = { member_id: string; display_name: string; avatar: string | null; reason: string; reason_kind: string; location_label: string | null; reputation: string[] };

export default function PeoplePage() {
  const { t } = useTranslation();
  const [people, setPeople] = useState<Person[] | null>(null);
  const [error, setError] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const load = useCallback(() => { setError(false); api<Person[]>('/people/suggestions').then(setPeople).catch(() => setError(true)); }, []);
  useEffect(load, [load]);

  const block = async (p: Person) => {
    try { await api('/safety/blocks', { body: { member_id: p.member_id } }); setToast(t('safety.blocked')); setTimeout(() => setToast(null), 2000); load(); }
    catch (e) { setToast(e instanceof ApiError ? e.message : t('state.error')); }
  };

  return (
    <>
      <header className="topbar"><h1>{t('people.title')}</h1></header>
      <main className="screen">
        <p className="caption" style={{ margin: 0 }}>{t('people.body')}</p>
        {error && <ErrorState onRetry={load} />}
        {!people && !error && <div className="stack">{[0, 1, 2].map((i) => <div key={i} className="sk" style={{ height: 72 }} />)}</div>}
        {people && people.length === 0 && <EmptyState message={t('people.empty')} />}
        {people && people.map((p) => (
          <div key={p.member_id} className="lrow fade-in">
            <Link href={`/p/${p.member_id}`} className="row grow" style={{ gap: 12 }}>
              {p.avatar ? <img className="avatar avatar--lg" src={resolveMediaUrl(p.avatar) ?? ''} alt="" /> : <span className="avatar avatar--lg" />}
              <div className="grow">
                <div className="title">{p.display_name}</div>
                <div className="whyline">✦ {p.reason}</div>
                <div className="caption">{[p.location_label, ...p.reputation].filter(Boolean).join(' · ')}</div>
              </div>
            </Link>
            <button className="icon-btn" aria-label={t('safety.block', { name: p.display_name })} onClick={() => block(p)} title={t('safety.blockConfirm')}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M6 6l12 12" /></svg>
            </button>
          </div>
        ))}
      </main>
      <Toast text={toast} />
    </>
  );
}

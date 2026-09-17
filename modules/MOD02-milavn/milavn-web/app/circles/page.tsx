'use client';

/* Circles (FR020-FR025 · UX09 · UI09): my circles, organic suggestions
 * (FR022) with a human accept, discover open circles, create with an
 * enum-enforced type. */

import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Sheet } from '@/components/Sheet';
import TopActions from '@/components/TopActions';
import { EmptyState, ErrorState, Toast } from '@/components/States';
import { api, ApiError, resolveMediaUrl, type Circle } from '@/lib/api';
import { initials } from '@/lib/format';
import { useIdentity } from '@/lib/identity';

type Suggestion = { id: string; name: string; created_at: string; members: { member_id: string; display_name: string; avatar: string | null }[] };
type CircleType = { value: string; label: string; is_open: boolean };

function CircleRow({ c, action }: { c: Circle; action?: React.ReactNode }) {
  const { t } = useTranslation();
  return (
    <div className="lrow">
      <Link href={`/circles/${c.id}`} className="row grow" style={{ gap: 12 }}>
        <span className="strip__ring" style={{ width: 48, height: 48, borderColor: 'transparent', padding: 0 }}><div style={{ fontSize: '0.95rem' }}>{initials(c.name)}</div></span>
        <span className="grow">
          <span className="title truncate" style={{ display: 'block' }}>{c.name}</span>
          <span className="caption">{c.type_label} · {t('circles.members', { count: c.member_count })}{c.locality_label ? ` · ${c.locality_label}` : ''}{!c.is_open ? ` · ${t('circles.inviteOnly')}` : ''}</span>
        </span>
      </Link>
      {action}
    </div>
  );
}

export default function CirclesPage() {
  const { t } = useTranslation();
  const { profile } = useIdentity();
  const [mine, setMine] = useState<Circle[] | null>(null);
  const [nearOnly, setNearOnly] = useState(false);
  const [homeLocality, setHomeLocality] = useState<'home' | 'anywhere'>('home');
  const [found, setFound] = useState<Circle[] | null>(null);
  const [sugs, setSugs] = useState<Suggestion[]>([]);
  const [types, setTypes] = useState<CircleType[]>([]);
  const [q, setQ] = useState('');
  const [error, setError] = useState(false);
  const [create, setCreate] = useState(false);
  // [FR115] A circle can ask a question or two before letting someone in.
  const [askFirst, setAskFirst] = useState(false);
  const [questions, setQuestions] = useState<string[]>(['', '']);
  const [name, setName] = useState('');
  const [type, setType] = useState('public');
  const [desc, setDesc] = useState('');
  const [toast, setToast] = useState<string | null>(null);
  const say = (m: string) => { setToast(m); setTimeout(() => setToast(null), 2000); };

  const load = useCallback(() => {
    setError(false);
    const qs = new URLSearchParams(); if (q) qs.set('q', q); if (nearOnly) qs.set('near', 'true');
    Promise.all([api<Circle[]>('/circles/mine'), api<Circle[]>(`/circles/discover${qs.toString() ? `?${qs}` : ''}`), api<Suggestion[]>('/circles/suggestions'), api<CircleType[]>('/circles/types')])
      .then(([m, d, s, ty]) => { setMine(m); setFound(d); setSugs(s); setTypes(ty); })
      .catch(() => setError(true));
  }, [q, nearOnly]);
  useEffect(() => { const id = setTimeout(load, 200); return () => clearTimeout(id); }, [load]);

  const join = async (c: Circle) => {
    try {
      const r = await api<{ status: string }>(`/circles/${c.id}/join`, { body: {} });
      say(r.status === 'pending' ? t('join.asked') : t('circles.joined'));
      load();
    }
    catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };
  const respond = async (s: Suggestion, accept: boolean) => {
    try { await api(`/circles/suggestions/${s.id}/respond`, { body: { accept } }); load(); }
    catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };
  const submit = async () => {
    const place = homeLocality === 'home' && profile ? { locality_city: profile.locality_city, locality_locality: profile.locality_locality } : {};
    const joinSetup = { join_policy: askFirst ? 'approval' : 'open', join_questions: askFirst ? questions.map((q) => q.trim()).filter(Boolean) : [] };
    try { const c = await api<Circle>('/circles', { body: { name, circle_type: type, description: desc, ...place, ...joinSetup } }); setCreate(false); setName(''); setDesc(''); setAskFirst(false); setQuestions(['', '']); say(`${c.name} ✓`); load(); }
    catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  const mineIds = new Set((mine ?? []).map((c) => c.id));

  return (
    <>
      <header className="topbar"><h1>{t('circles.title')}</h1><div className="row" style={{ gap: 8 }}><button className="btn btn--primary btn--sm" onClick={() => setCreate(true)}>+ {t('circles.create')}</button><TopActions /></div></header>
      <main className="screen">
        {error && <ErrorState onRetry={load} />}
        {sugs.map((s) => (
          <section key={s.id} className="card stack fade-in" style={{ gap: 10, borderColor: 'var(--accent-primary)' }}>
            <span className="label" style={{ color: 'var(--accent-pressed)' }}>{t('circles.suggested')}</span>
            <div className="row" style={{ gap: 10 }}>
              <span className="avatar-stack">{s.members.map((m) => m.avatar ? <img key={m.member_id} className="avatar avatar--lg" src={resolveMediaUrl(m.avatar) ?? ''} alt="" /> : <span key={m.member_id} className="avatar avatar--lg" />)}</span>
              <span className="grow"><b>{s.name}</b><br /><span className="caption">{s.members.map((m) => m.display_name).join(', ')} — {t('circles.suggestedBody')}</span></span>
            </div>
            <div className="row"><button className="btn btn--ghost" onClick={() => respond(s, false)}>{t('circles.notNow')}</button><button className="btn btn--primary grow btn--spring" onClick={() => respond(s, true)}>{t('circles.start')}</button></div>
          </section>
        ))}

        <section className="section">
          <div className="section__head"><h2>{t('circles.mine')}</h2></div>
          {mine === null && !error && <div className="stack">{[0, 1].map((i) => <div key={i} className="sk" style={{ height: 64 }} />)}</div>}
          {mine && mine.length === 0 && <EmptyState message={t('circles.emptyMine')} action={t('circles.create')} onAction={() => setCreate(true)} />}
          {mine && mine.length > 0 && <div className="list fade-in">{mine.map((c) => <CircleRow key={c.id} c={c} />)}</div>}
        </section>

        <section className="section">
          <div className="section__head"><h2>{t('circles.discover')}</h2></div>
          <label className="field"><input className="field__input" type="search" placeholder={t('circles.searchPlaceholder')} value={q} onChange={(e) => setQ(e.target.value)} /></label>
          <div className="chips" aria-label={t('circles.discover')}>
            <button className="chip chip--sm" aria-pressed={nearOnly} onClick={() => setNearOnly(true)}>📍 {t('circles.nearMe')}</button>
            <button className="chip chip--sm" aria-pressed={!nearOnly} onClick={() => setNearOnly(false)}>{t('circles.all')}</button>
          </div>
          {found && found.filter((c) => !mineIds.has(c.id)).length === 0 && <EmptyState message={t('circles.emptyDiscover')} />}
          {found && (() => {
            const rest = found.filter((c) => !mineIds.has(c.id));
            const near = rest.filter((c) => c.near_you);
            const far = rest.filter((c) => !c.near_you);
            const row = (c: Circle) => <CircleRow key={c.id} c={c} action={<button className="btn btn--secondary btn--sm btn--spring" onClick={() => join(c)}>{t('circles.join')}</button>} />;
            return (
              <div className="stack fade-in" style={{ gap: 14 }}>
                {near.length > 0 && <div className="stack" style={{ gap: 8 }}><span className="label">📍 {t('circles.nearYou')}{profile?.locality_locality ? ` · ${profile.locality_locality}` : ''}</span><div className="list">{near.map(row)}</div></div>}
                {far.length > 0 && <div className="stack" style={{ gap: 8 }}>{near.length > 0 && <span className="label">{t('circles.elsewhere')}</span>}<div className="list">{far.map(row)}</div></div>}
              </div>
            );
          })()}
        </section>
      </main>

      <Sheet open={create} onClose={() => setCreate(false)} label={t('circles.create')}>
        <div className="stack">
          <h2 className="h2">{t('circles.create')}</h2>
          <label className="field"><span className="field__label">{t('circles.name')}</span><input className="field__input" value={name} onChange={(e) => setName(e.target.value)} maxLength={80} /></label>
          <div className="stack" style={{ gap: 8 }}>
            <span className="field__label">{t('circles.type')}</span>
            <div className="chips">{types.map((ty) => <button key={ty.value} className="chip chip--sm" aria-pressed={type === ty.value} onClick={() => setType(ty.value)}>{ty.label}{!ty.is_open ? ' 🔒' : ''}</button>)}</div>
          </div>
          <label className="field"><textarea placeholder={t('circles.descriptionPlaceholder')} value={desc} onChange={(e) => setDesc(e.target.value)} /></label>
          <div className="stack" style={{ gap: 8 }}>
            <span className="field__label">{t('circles.home')}</span>
            <div className="chips">
              <button className="chip chip--sm" aria-pressed={homeLocality === 'home'} onClick={() => setHomeLocality('home')}>📍 {profile?.locality_locality ?? profile?.locality_city ?? t('circles.home')}</button>
              <button className="chip chip--sm" aria-pressed={homeLocality === 'anywhere'} onClick={() => setHomeLocality('anywhere')}>{t('circles.anywhere')}</button>
            </div>
          </div>
          <div className="stack" style={{ gap: 8 }}>
            <span className="field__label">{t('join.whoCanJoin')}</span>
            <div className="chips">
              <button type="button" className="chip chip--sm" aria-pressed={!askFirst} onClick={() => setAskFirst(false)}>{t('join.anyone')}</button>
              <button type="button" className="chip chip--sm" aria-pressed={askFirst} onClick={() => setAskFirst(true)}>{t('join.askFirst')}</button>
            </div>
            {askFirst && (
              <>
                <span className="caption">{t('join.questionsHint')}</span>
                {questions.map((q, i) => (
                  <label key={i} className="field">
                    <input
                      className="field__input"
                      name={`join-question-${i}`}
                      maxLength={120}
                      placeholder={t(`join.questionPlaceholder${i}`)}
                      value={q}
                      onChange={(e) => setQuestions((prev) => prev.map((v, j) => (j === i ? e.target.value : v)))}
                    />
                  </label>
                ))}
              </>
            )}
          </div>
          <button className="btn btn--primary btn--block" disabled={!name.trim()} onClick={submit}>{t('circles.create')}</button>
        </div>
      </Sheet>
      <Toast text={toast} />
    </>
  );
}

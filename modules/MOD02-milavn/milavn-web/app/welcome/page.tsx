'use client';

/* Launch / identity handoff (FR076-FR080 are ForKhatri platform flows).
 * Milavn never signs anyone in; while it runs standalone this screen stands
 * in for the platform session handoff by letting you continue as one of the
 * registered development identities. On a wide screen it doubles as the
 * product's landing: what Milavn is, in three lines, next to the picker. */

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { ErrorState } from '@/components/States';
import { getDevMembers, resolveMediaUrl, type Identity } from '@/lib/api';
import { useIdentity } from '@/lib/identity';

export default function WelcomePage() {
  const { t } = useTranslation();
  const { choose } = useIdentity();
  const router = useRouter();
  const [members, setMembers] = useState<Identity[] | null>(null);
  const [error, setError] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);

  const load = () => { setError(false); getDevMembers().then(setMembers).catch(() => setError(true)); };
  useEffect(load, []);

  const pick = async (m: Identity) => {
    setBusy(m.member_id);
    await choose(m.member_id);
    router.replace('/');
  };

  return (
    <main className="screen motif landing" style={{ minHeight: '100vh', justifyContent: 'center' }}>
      <section className="landing__hero">
        <div className="row" style={{ gap: 12, marginBottom: 18 }}>
          <span className="brand-mark brand-mark--glow">M</span>
          <b style={{ fontSize: '1.125rem' }}>{t('app.name')}</b>
        </div>
        <h1><span className="gradient-text">{t('welcome.headline')}</span></h1>
        <p>{t('welcome.lede')}</p>
        <div className="collage" aria-hidden="true">
          <img src="/assets/covers/kw-badminton.jpg" alt="" />
          <img src="/assets/covers/kw-biryani.jpg" alt="" />
          <img src="/assets/covers/kw-trek.jpg" alt="" />
        </div>
        <div className="landing__points">
          <div className="landing__point"><span>📍</span><span>{t('welcome.point1')}</span></div>
          <div className="landing__point"><span>🛡️</span><span>{t('welcome.point2')}</span></div>
          <div className="landing__point"><span>✦</span><span>{t('welcome.point3')}</span></div>
        </div>
      </section>
      <section className="card stack glass" style={{ gap: 12 }}>
        <h2 className="h2">{t('welcome.title')}</h2>
        <p className="caption" style={{ margin: 0 }}>{t('welcome.subtitle')}</p>
        {error && <ErrorState onRetry={load} />}
        {!members && !error && <div className="stack">{[0, 1, 2].map((i) => <div key={i} className="sk" style={{ height: 64 }} />)}</div>}
        {members && (
          <div className="list">
            {members.map((m) => (
              <button key={m.member_id} className="lrow lrow--tap" style={{ textAlign: 'left', width: '100%' }} onClick={() => pick(m)} disabled={busy !== null}>
                {m.avatar ? <img className="avatar avatar--lg" src={resolveMediaUrl(m.avatar) ?? ''} alt="" /> : <span className="avatar avatar--lg" />}
                <span className="grow">
                  <span className="title" style={{ display: 'block' }}>{m.display_name}</span>
                  <span className="caption">@{m.handle}{m.scopes.includes('milavn.moderate') ? ` · ${t('welcome.moderator')}` : ''}</span>
                </span>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M9 6l6 6-6 6" /></svg>
              </button>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}

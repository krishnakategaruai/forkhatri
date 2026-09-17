'use client';

/* Home / Around You (FR004, FR006, FR007, FR008, FR038 · UX04 · UI04):
 * active-circles strip, mode switcher, Today / Tomorrow / This Weekend /
 * Coming up, skeleton -> content cross-fade, specific empty copy per group,
 * "+" Make something happen. */

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import ActivityCard from '@/components/ActivityCard';
import AskBar from '@/components/AskBar';
import TopActions from '@/components/TopActions';
import { ChevronLeft } from 'lucide-react';
import { FORKHATRI_ENTRANCE_URL } from '@/lib/platform';
import ModeSwitcher, { type Mode } from '@/components/ModeSwitcher';
import { CardSkeleton, EmptyState, ErrorState } from '@/components/States';
import { api, type AroundYou } from '@/lib/api';
import { initials } from '@/lib/format';
import { useIdentity } from '@/lib/identity';

export default function HomePage() {
  const { t } = useTranslation();
  const router = useRouter();
  const { identity, profile } = useIdentity();
  const hour = new Date().getHours();
  const greetKey = hour < 12 ? 'home.greetMorning' : hour < 17 ? 'home.greetAfternoon' : 'home.greetEvening';
  const firstName = (identity?.display_name ?? '').split(' ')[0];
  const [data, setData] = useState<AroundYou | null>(null);
  const [error, setError] = useState(false);
  const [compactFab, setCompactFab] = useState(false);
  const [digest, setDigest] = useState<string[] | null>(null);
  // "Here, right now": a one-shot device position that changes what you *see*, not your profile (FR038/FR041). No background tracking.
  const [here, setHere] = useState<{ lat: number; lng: number } | null>(() => { try { const v = sessionStorage.getItem('milavn.here'); return v ? JSON.parse(v) : null; } catch { return null; } });
  const [locating, setLocating] = useState(false);
  const locateHere = () => {
    if (!navigator.geolocation) return;
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => { const h = { lat: pos.coords.latitude, lng: pos.coords.longitude }; try { sessionStorage.setItem('milavn.here', JSON.stringify(h)); } catch { /* ignore */ } setHere(h); setLocating(false); },
      () => setLocating(false), { timeout: 8000 },
    );
  };
  const clearHere = () => { try { sessionStorage.removeItem('milavn.here'); } catch { /* ignore */ } setHere(null); };

  // "Make something happen" (thesis §71) is a principle, so the button says
  // so; it folds to "+" once the person is reading cards.
  useEffect(() => {
    const onScroll = () => setCompactFab(window.scrollY > 160);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const load = useCallback(() => {
    setError(false);
    const qs = here ? `?lat=${here.lat}&lng=${here.lng}` : '';
    api<AroundYou>(`/discovery/around-you${qs}`).then(setData).catch(() => setError(true));
    api<{ lines: string[] }>(`/discovery/digest${qs}`).then((d) => setDigest(d.lines)).catch(() => setDigest(null));
  }, [here]);
  useEffect(() => { if (identity && profile) load(); }, [identity, profile, load]);

  const onMode = (m: Mode) => { if (m !== 'feed') router.push(`/discover?mode=${m}`); };

  const groups: { key: keyof Omit<AroundYou, 'circles' | 'viewer_locality'>; title: string; empty: string }[] = [
    { key: 'today', title: t('home.today'), empty: t('home.emptyToday') },
    { key: 'tomorrow', title: t('home.tomorrow'), empty: t('home.emptyTomorrow') },
    { key: 'weekend', title: t('home.weekend'), empty: t('home.emptyWeekend') },
    { key: 'later', title: t('home.later'), empty: t('home.emptyLater') },
  ];
  const total = data ? groups.reduce((n, g) => n + data[g.key].length, 0) : 0;
  // Real time on the device: whatever is on right now (start ≤ now ≤ end, or start + 2h when no end).
  const [nowMs, setNowMs] = useState(() => Date.now());
  useEffect(() => { const id = setInterval(() => setNowMs(Date.now()), 60000); return () => clearInterval(id); }, []);
  const liveNow = data ? data.today.filter((c) => { const s = new Date(c.time_start).getTime(); const e = c.time_end ? new Date(c.time_end).getTime() : s + 2 * 3600 * 1000; return nowMs >= s && nowMs <= e && c.status !== 'cancelled'; }) : [];

  return (
    <>
      <header className="topbar">
        <div className="row home-brand">
          <span className="brand-mark">M</span>
          <div className="home-brand__text">
            {/* [ParentApp TR16] Milavn sits inside ForKhatri: a breadcrumb-style way back to the hub (phones; the desktop rail has its own). */}
            <a href={`${FORKHATRI_ENTRANCE_URL}/`} className="hub-eyebrow" aria-label={t('platform.backToHub')}>
              <ChevronLeft size={12} strokeWidth={2.4} aria-hidden="true" />{t('platform.hub')}
            </a>
            <h1 className="greeting" style={{ fontSize: '1.15rem' }}>{t('app.name')}</h1>
            {data && (
              <button type="button" className="link caption herechip" onClick={here ? clearHere : locateHere} disabled={locating} aria-live="polite">
                📍 {locating ? t('home.locating') : t('home.near', { locality: data.viewer_locality })}{here ? ` · ${t('home.hereNow')} ×` : ` · ${t('home.useHere')}`}
              </button>
            )}
          </div>
        </div>
        <TopActions people />
      </header>
      <main className="screen">
        <div className="fade-in">
          <h2 className="greeting">{t(greetKey)}{firstName ? <>, <em>{firstName}</em></> : ''}.</h2>
          {data && <p className="greeting__sub">{t('home.greetSub', { locality: data.viewer_locality })}</p>}
        </div>
        <AskBar prompts={[t('ask.prompt1'), t('ask.prompt2'), t('ask.prompt3'), t('ask.prompt4')]} />
        {digest && digest.length > 0 && (
          <div className="digest fade-in" aria-label={t('digest.label')}>
            {digest.map((l) => <div key={l} className="digest__line"><span aria-hidden="true">✦</span><span>{l}</span></div>)}
          </div>
        )}
        {data && data.circles.length > 0 && (
          <section className="stack" style={{ gap: 6 }}>
            <div className="row row--between"><span className="label">{t('home.yourCircles')}</span><Link href="/circles" className="link caption">{t('home.seeAll')} ›</Link></div>
            <div className="strip" aria-label={t('home.yourCircles')}>
              {data.circles.map((c) => (
                <Link key={c.id} href={`/circles/${c.id}`} className="strip__item">
                  <span className="strip__ring strip__ring--fresh"><div>{initials(c.name)}</div></span>
                  <span className="strip__label">{c.name}</span>
                </Link>
              ))}
            </div>
          </section>
        )}
        <ModeSwitcher mode="feed" onChange={onMode} />

        {error && <ErrorState onRetry={load} />}
        {!data && !error && (
          <>
            <div className="strip">{[0, 1, 2].map((i) => <div key={i} className="sk sk--circle" />)}</div>
            <CardSkeleton count={2} />
          </>
        )}
        {data && total === 0 && (
          <EmptyState message={t('home.emptyAll', { locality: data.viewer_locality })} action={t('home.makeSomething')} onAction={() => router.push('/create')} />
        )}
        {data && liveNow.length > 0 && (
          <section className="stack fade-in" style={{ gap: 10 }}>
            <div className="section__head"><h2><span className="live-dot" aria-hidden="true" /> {t('home.happeningNow')}</h2><span className="count-chip">{liveNow.length}</span></div>
            <div className="rail">{liveNow.map((c) => <ActivityCard key={c.id} card={c} compact />)}</div>
          </section>
        )}
        {data && total > 0 && groups.map((g, gi) => {
          const firstNonEmpty = groups.findIndex((x) => data[x.key].length > 0);
          return (
            <section key={g.key} className="stack fade-in" style={{ gap: 10 }}>
              <div className="section__head"><h2>{g.title}</h2>{data[g.key].length > 0 && <span className="count-chip">{data[g.key].length}</span>}</div>
              {data[g.key].length === 0 ? <EmptyState message={g.empty} /> : (
                <div className="rail">
                  {data[g.key].map((c, i) => <ActivityCard key={c.id} card={c} hero={gi === firstNonEmpty && i === 0} />)}
                </div>
              )}
            </section>
          );
        })}
      </main>
      <Link href="/create" className={`fab fab--extended${compactFab ? ' fab--compact' : ''}`} aria-label={t('home.makeSomething')}>
        <span className="fab__plus" aria-hidden="true">+</span>
        <span className="fab__label">{t('home.makeSomething')}</span>
      </Link>
    </>
  );
}

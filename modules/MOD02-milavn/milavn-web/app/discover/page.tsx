'use client';

/* Discovery modes (FR005, FR009, FR033 · UX05 · UI05): Calendar (date strip),
 * Map (pins + preview sheet, list-view alternative), Search (common filter
 * chips by default, advanced filters behind a "More filters" sheet). */

import dynamic from 'next/dynamic';
import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';

import ActivityCard from '@/components/ActivityCard';
import AskBar, { type Understood } from '@/components/AskBar';
import ModeSwitcher, { type Mode } from '@/components/ModeSwitcher';
import { Sheet } from '@/components/Sheet';
import { CardSkeleton, EmptyState, ErrorState } from '@/components/States';
import { api, type Card } from '@/lib/api';
import { formatWhen } from '@/lib/format';

const MapView = dynamic(() => import('@/components/MapView'), { ssr: false, loading: () => <div className="sk map" /> });
const CATEGORIES = ['play', 'meet', 'eat', 'learn', 'work', 'explore', 'celebrate', 'help'];

function DiscoverInner() {
  const { t } = useTranslation();
  const router = useRouter();
  const params = useSearchParams();
  const mode = (params.get('mode') as Mode) || 'calendar';
  const [cards, setCards] = useState<Card[] | null>(null);
  const [error, setError] = useState(false);
  const [day, setDay] = useState(() => { const d = new Date(); d.setHours(0, 0, 0, 0); return d; });
  const [q, setQ] = useState('');
  const [when, setWhen] = useState<string | null>(null);
  const [distance, setDistance] = useState<string | null>(null);
  const [category, setCategory] = useState<string | null>(null);
  const [scope, setScope] = useState<string | null>(null);
  const [safeOnly, setSafeOnly] = useState(false);
  const [more, setMore] = useState(false);
  const [preview, setPreview] = useState<Card | null>(null);
  const [mapList, setMapList] = useState(false);
  const ask = params.get('ask') ?? '';
  const [askChips, setAskChips] = useState<string[]>([]);
  const [widened, setWidened] = useState<string | null>(null);

  const applyUnderstanding = useCallback((u: Understood) => {
    setQ(u.q ?? ''); setWhen(u.when); setDistance(u.distance); setCategory(u.category); setAskChips(u.chips);
  }, []);
  // Arriving from Home's Ask bar: interpret once, then let the chips take over.
  useEffect(() => {
    if (!ask) return;
    api<Understood>(`/discovery/understand?q=${encodeURIComponent(ask)}`).then(applyUnderstanding).catch(() => setQ(ask));
  }, [ask, applyUnderstanding]);

  const days = useMemo(() => Array.from({ length: 21 }, (_, i) => { const d = new Date(); d.setHours(0, 0, 0, 0); d.setDate(d.getDate() + i); return d; }), []);

  const load = useCallback(() => {
    setError(false); setCards(null);
    let p: Promise<Card[]>;
    if (mode === 'calendar') p = api<Card[]>(`/discovery/calendar?date=${encodeURIComponent(day.toISOString())}`);
    else if (mode === 'map') p = api<Card[]>('/discovery/map');
    else {
      const qs = new URLSearchParams();
      if (q) qs.set('q', q); if (when) qs.set('when', when); if (distance) qs.set('distance', distance);
      if (category) qs.set('category', category); if (scope) qs.set('scope', scope); if (safeOnly) qs.set('safe_only', 'true');
      p = api<Card[]>(`/discovery/search?${qs}`);
    }
    p.then(async (list) => {
      setWidened(null);
      if (mode === 'search' && list.length === 0 && (distance || when)) {
        // Nothing matched the exact ask: widen once (drop distance), then twice (drop the date), and say which.
        const retry = async (drop: 'distance' | 'when') => {
          const qs2 = new URLSearchParams();
          if (q) qs2.set('q', q); if (when && drop !== 'when') qs2.set('when', when); if (distance && drop === 'when') qs2.set('distance', distance);
          if (category) qs2.set('category', category); if (scope) qs2.set('scope', scope); if (safeOnly) qs2.set('safe_only', 'true');
          return api<Card[]>(`/discovery/search?${qs2}`);
        };
        if (distance) { const r = await retry('distance'); if (r.length) { setWidened(t('ask.widenedDistance')); setCards(r); return; } }
        if (when) { const r = await retry('when'); if (r.length) { setWidened(t('ask.widenedWhen')); setCards(r); return; } }
      }
      setCards(list);
    }).catch(() => setError(true));
  }, [mode, day, q, when, distance, category, scope, safeOnly, t]);

  useEffect(() => { const id = setTimeout(load, mode === 'search' ? 250 : 0); return () => clearTimeout(id); }, [load, mode]);

  const onMode = (m: Mode) => (m === 'feed' ? router.push('/') : router.replace(`/discover?mode=${m}`));

  return (
    <>
      <header className="topbar"><h1>{t('home.title')}</h1></header>
      <main className="screen">
        <ModeSwitcher mode={mode} onChange={onMode} />

        {mode === 'calendar' && (
          <div className="date-strip" role="tablist" aria-label={t('calendar.title')}>
            {days.map((d) => {
              const on = d.getTime() === day.getTime();
              return (
                <button key={d.toISOString()} role="tab" aria-pressed={on} aria-selected={on} onClick={() => setDay(d)}>
                  <small>{d.toLocaleDateString('en-IN', { weekday: 'short' })}</small><b>{d.getDate()}</b>
                </button>
              );
            })}
          </div>
        )}

        {mode === 'search' && (
          <>
            <AskBar initial={ask} autoNavigate={false} onUnderstood={(u) => applyUnderstanding(u)} />
            {askChips.length > 0 && <div className="ask__understood"><span>{t('ask.filtersFrom')}</span>{askChips.map((c) => <span key={c} className="pill">{c}</span>)}<button className="link" style={{ fontSize: '0.8125rem' }} onClick={() => { setAskChips([]); setQ(''); setWhen(null); setDistance(null); setCategory(null); }}>{t('ask.clear')}</button></div>}
            <label className="field">
              <input className="field__input" type="search" placeholder={t('discover.searchPlaceholder')} value={q} onChange={(e) => setQ(e.target.value)} aria-label={t('discover.searchPlaceholder')} />
            </label>
            <div className="chips chips--scroll" aria-label="Filters">
              <button className="chip chip--sm" aria-pressed={when === 'today'} onClick={() => setWhen(when === 'today' ? null : 'today')}>{t('discover.filters.today')}</button>
              <button className="chip chip--sm" aria-pressed={when === 'weekend'} onClick={() => setWhen(when === 'weekend' ? null : 'weekend')}>{t('discover.filters.weekend')}</button>
              <button className="chip chip--sm" aria-pressed={distance === 'zone'} onClick={() => setDistance(distance === 'zone' ? null : 'zone')}>{t('discover.filters.nearby')}</button>
              <button className="chip chip--sm" aria-pressed={category !== null} onClick={() => setMore(true)}>{category ? t(`create.categories.${category}`) : t('discover.filters.category')}</button>
              <button className="chip chip--sm" aria-pressed={true} disabled title="Everything on Milavn is free right now">{t('discover.filters.free')}</button>
              <button className="chip chip--sm" onClick={() => setMore(true)}>{t('discover.filters.more')} ›</button>
            </div>
          </>
        )}

        {error && <ErrorState onRetry={load} />}
        {!cards && !error && mode !== 'map' && <CardSkeleton />}

        {mode === 'map' && (
          <>
            <div className="row row--between">
              <span className="caption">{cards ? `${cards.length} nearby` : t('state.loading')}</span>
              <button className="link" onClick={() => setMapList((v) => !v)}>{mapList ? t('discover.mapView') : t('discover.listView')}</button>
            </div>
            {!mapList && cards && (cards.length ? <MapView cards={cards} onSelect={setPreview} /> : <EmptyState message={t('discover.emptyMap')} />)}
            {mapList && cards && (cards.length ? <div className="rail">{cards.map((c) => <ActivityCard key={c.id} card={c} />)}</div> : <EmptyState message={t('discover.emptyMap')} />)}
          </>
        )}

        {widened && <div className="ask__understood fade-in"><span className="ask__spark" aria-hidden="true">✦</span><span>{widened}</span></div>}
        {cards && mode !== 'map' && (
          cards.length === 0
            ? <EmptyState message={mode === 'calendar' ? t('discover.emptyDay') : t('discover.emptySearch')} />
            : <div className="rail fade-in">{cards.map((c) => <ActivityCard key={c.id} card={c} />)}</div>
        )}
      </main>

      <Sheet open={preview !== null} onClose={() => setPreview(null)} label={preview?.title ?? ''}>
        {preview && (
          <div className="stack">
            <ActivityCard card={preview} compact />
            <button className="btn btn--primary btn--block" onClick={() => router.push(`/a/${preview.slug}`)}>{t('discover.viewDetails')}</button>
          </div>
        )}
      </Sheet>

      <Sheet open={more} onClose={() => setMore(false)} label={t('discover.filters.more')}>
        <div className="stack" style={{ gap: 18 }}>
          <div className="stack" style={{ gap: 8 }}>
            <span className="label">{t('discover.filters.category')}</span>
            <div className="chips">
              <button className="chip chip--sm" aria-pressed={category === null} onClick={() => setCategory(null)}>{t('discover.filters.any')}</button>
              {CATEGORIES.map((c) => <button key={c} className="chip chip--sm" aria-pressed={category === c} onClick={() => setCategory(c)}>{t(`create.categories.${c}`)}</button>)}
            </div>
          </div>
          <div className="stack" style={{ gap: 8 }}>
            <span className="label">{t('discover.filters.distance')}</span>
            <div className="chips">
              {[['locality', t('discover.filters.locality')], ['zone', t('discover.filters.zone')], ['city', t('discover.filters.city')]].map(([v, l]) => (
                <button key={v} className="chip chip--sm" aria-pressed={distance === v} onClick={() => setDistance(distance === v ? null : v)}>{l}</button>
              ))}
            </div>
          </div>
          <div className="stack" style={{ gap: 8 }}>
            <span className="label">{t('discover.filters.scope')}</span>
            <div className="chips">
              {['public', 'community', 'circle'].map((s) => <button key={s} className="chip chip--sm" aria-pressed={scope === s} onClick={() => setScope(scope === s ? null : s)}>{t(`discover.scopes.${s}`)}</button>)}
            </div>
          </div>
          <div className="row row--between">
            <span>{t('discover.filters.safeOnly')}</span>
            <button className="switch" role="switch" aria-checked={safeOnly} onClick={() => setSafeOnly((v) => !v)} aria-label={t('discover.filters.safeOnly')} />
          </div>
          <button className="btn btn--primary btn--block" onClick={() => setMore(false)}>{t('common.done')}</button>
        </div>
      </Sheet>
    </>
  );
}

export default function DiscoverPage() {
  return <Suspense fallback={<main className="screen"><CardSkeleton /></main>}><DiscoverInner /></Suspense>;
}

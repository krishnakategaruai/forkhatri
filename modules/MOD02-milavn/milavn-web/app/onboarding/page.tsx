'use client';

/* First run (FR001, FR081 · redesigned 2026-10-06, ONBOARDING-REDESIGN-2026-10.md §9 · mockup A/A2).
 *
 * One screen, one answer: where should Milavn look. Before, three forced screens (place → at least
 * one interest → language) stood between the hub and Home, and the language step had English
 * pre-ticked, which silently switched Telugu and Hindi members to English.
 *   - Language is never asked here and never overwritten: Milavn already speaks the member's ForKhatri
 *     language, and that is what the new profile records.
 *   - Interests are optional and asked later, on Home (FR001 relaxed to "place only").
 *   - The place takes one tap: "Use where I am" then "Yes", a big-city chip (city only), or typing straight
 *     into the search on this screen (no sheet). Picking a result saves it; there is no Continue.
 *   - If the location cannot be read, the screen says so and the city chips and search are right there.
 *   - Afterwards the member goes where they were going (`?next=`, e.g. a shared circle link), else Home. */

import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { usePlaceSearch, type PickedPlace } from '@/components/PlacePicker';
import { api, ApiError, type Profile } from '@/lib/api';
import { CITIES, citiesFor, safeNext } from '@/lib/first-run';
import { isSupported } from '@/lib/i18n/config';
import { useIdentity } from '@/lib/identity';

function placeName(p: PickedPlace): string {
  return p.locality_locality || p.locality_city;
}
function placeContext(p: PickedPlace): string {
  return [p.locality_locality ? p.locality_city : null, p.locality_state].filter((v, i, a) => v && a.indexOf(v) === i).join(', ');
}

function FirstRun() {
  const { t, i18n } = useTranslation();
  const router = useRouter();
  const params = useSearchParams();
  const next = safeNext(params.get('next'));
  const { identity, setProfile } = useIdentity();
  const firstName = (identity?.display_name ?? '').split(' ')[0];

  const [q, setQ] = useState('');
  const { hits, busy, failed, needleOk } = usePlaceSearch(q);
  const [found, setFound] = useState<PickedPlace | null>(null); // what "Use where I am" found, waiting for "Yes"
  const [locating, setLocating] = useState(false);
  const [gpsProblem, setGpsProblem] = useState<'denied' | 'notFound' | null>(null);
  const [saving, setSaving] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const save = async (p: PickedPlace, key: string) => {
    if (saving) return;
    setSaving(key); setError(null);
    const lang = i18n.language;
    try {
      const prof = await api<Profile>('/profile', {
        body: {
          locality_city: p.locality_city, locality_zone: p.locality_zone ?? null, locality_locality: p.locality_locality ?? null,
          locality_state: p.locality_state ?? null, locality_lat: p.lat ?? null, locality_lng: p.lon ?? null,
          // The member's ForKhatri language, recorded as it is (never a default English).
          language_preference: isSupported(lang) ? lang : null,
        },
      });
      setProfile(prof);
      router.replace(next ?? '/');
    } catch (e) {
      setError(e instanceof ApiError ? e.message : t('state.error'));
      setSaving(null);
    }
  };

  const useLocation = () => {
    setGpsProblem(null);
    if (!navigator.geolocation) { setGpsProblem('denied'); return; }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          setFound(await api<PickedPlace>(`/profile/places/nearest?lat=${pos.coords.latitude}&lng=${pos.coords.longitude}`));
        } catch { setGpsProblem('notFound'); } finally { setLocating(false); }
      },
      () => { setLocating(false); setGpsProblem('denied'); }, // denied or timed out: say so, the chips and search are right here
      { timeout: 8000 },
    );
  };

  if (found) {
    return (
      <main className="screen firstrun" style={{ minHeight: '100vh' }}>
        <section className="stack fade-in" style={{ gap: 16 }}>
          <h1 className="display firstrun__title">{t('firstRun.nearTitle', { place: placeName(found) })}</h1>
          <p className="muted" style={{ margin: 0 }}>{t('firstRun.keepAreaOnly')}</p>
          <div className="picker" aria-hidden="true">
            <span className="picker__icon">📍</span>
            <span className="grow"><b>{placeName(found)}</b><span className="caption" style={{ display: 'block' }}>{placeContext(found)}</span></span>
          </div>
          {error && <p className="field__error" role="alert" style={{ margin: 0 }}>{error}</p>}
          <button className="btn btn--primary btn--block" disabled={!!saving} onClick={() => save(found, 'gps')}>{saving ? t('firstRun.saving') : t('firstRun.yesThis')}</button>
          <button className="btn btn--ghost btn--block" disabled={!!saving} onClick={() => setFound(null)}>{t('firstRun.chooseAnother')}</button>
        </section>
      </main>
    );
  }

  return (
    <main className="screen firstrun" style={{ minHeight: '100vh' }}>
      <section className="stack fade-in" style={{ gap: 16 }}>
        <div>
          {firstName && <p className="firstrun__hello">{t('firstRun.hello', { name: firstName })}</p>}
          <h1 className="display firstrun__title">{t('firstRun.title')}</h1>
          <p className="muted" style={{ margin: '8px 0 0' }}>{t('firstRun.body')}</p>
        </div>

        <button className="btn btn--primary btn--block" onClick={useLocation} disabled={locating || !!saving}>
          📍 {locating ? t('onboarding.locating') : t('firstRun.useWhereIAm')}
        </button>
        {gpsProblem && <p className="firstrun__note" role="alert">{t(gpsProblem === 'denied' ? 'firstRun.gpsDenied' : 'firstRun.gpsNotFound')}</p>}

        <label className="field" style={{ margin: 0 }}>
          <input
            className="field__input" type="search" value={q} onChange={(e) => setQ(e.target.value)} autoComplete="off"
            placeholder={t('firstRun.searchPlaceholder')} aria-label={t('firstRun.searchPlaceholder')}
          />
        </label>
        {q.trim() !== '' && (
          <div className="stack" style={{ gap: 6 }} aria-live="polite">
            {!needleOk && <p className="caption" style={{ margin: 0 }}>{t('place.hint')}</p>}
            {needleOk && busy && <p className="caption" style={{ margin: 0 }}>{t('place.searching')}</p>}
            {needleOk && !busy && failed && <p className="field__error" role="alert" style={{ margin: 0 }}>{t('place.unavailable')}</p>}
            {needleOk && !busy && !failed && hits.length === 0 && <p className="caption" style={{ margin: 0 }}>{t('place.none')}</p>}
            {hits.map((p, i) => (
              <button key={`${p.label}-${i}`} type="button" className="picker" disabled={!!saving} onClick={() => save(p, `hit-${i}`)}>
                <span className="grow" style={{ textAlign: 'left' }}>
                  <b>{placeName(p)}</b>
                  <span className="caption" style={{ display: 'block' }}>{(p.label ?? '').split(', ').slice(1).join(', ')}</span>
                </span>
                {saving === `hit-${i}` ? <span className="caption">{t('firstRun.saving')}</span> : p.kind && <span className="pill pill--neutral">{t(`place.kind.${p.kind}`)}</span>}
              </button>
            ))}
          </div>
        )}

        <div className="stack" style={{ gap: 8 }}>
          <span className="label">{t('firstRun.orTapCity')}</span>
          <div className="chips">
            {citiesFor(i18n.language).map((key) => (
              <button key={key} type="button" className="chip" disabled={!!saving} aria-busy={saving === key} onClick={() => save(CITIES[key], key)}>
                {saving === key ? t('firstRun.saving') : t(`firstRun.city.${key}`)}
              </button>
            ))}
          </div>
          <p className="caption" style={{ margin: 0 }}>{t('firstRun.cityOnlyNote')}</p>
        </div>
        {error && <p className="field__error" role="alert" style={{ margin: 0 }}>{error}</p>}
      </section>
    </main>
  );
}

export default function OnboardingPage() {
  return <Suspense fallback={<main className="screen" />}><FirstRun /></Suspense>;
}

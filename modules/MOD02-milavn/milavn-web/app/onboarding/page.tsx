'use client';

/* First-run onboarding (FR001, FR002, FR003, FR081 · UX02 · UI02):
 * Locality (soft-ask -> native prompt -> nearest approximate locality, manual
 * picker fallback, denial is a normal path) -> Interests (springy chips,
 * >=1 required) -> Language (native-script options) -> Home. */

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import PlacePicker from '@/components/PlacePicker';
import { api, ApiError, type Profile } from '@/lib/api';
import { applyLanguage } from '@/lib/i18n/provider';
import { LANGUAGE_NATIVE, SUPPORTED_LANGUAGES, type Language } from '@/lib/i18n/config';
import { useIdentity } from '@/lib/identity';

type Taxonomy = { group: string; interests: { tag: string; label: string; intent_category: string }[] }[];

export default function OnboardingPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const { setProfile } = useIdentity();
  const [step, setStep] = useState(1);
  const [taxonomy, setTaxonomy] = useState<Taxonomy>([]);
  const [city, setCity] = useState('');
  const [locality, setLocality] = useState('');
  const [locating, setLocating] = useState(false);
  const [interests, setInterests] = useState<string[]>([]);
  const [lang, setLang] = useState<Language>('en');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [popTag, setPopTag] = useState<string | null>(null);

  useEffect(() => {
    api<Taxonomy>('/profile/interests/taxonomy').then(setTaxonomy).catch(() => undefined);
  }, []);


  const useLocation = () => {
    if (!navigator.geolocation) return;
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          const near = await api<{ city: string; zone: string; locality: string }>(`/profile/localities/nearest?lat=${pos.coords.latitude}&lng=${pos.coords.longitude}`);
          setCity(near.city);
          setLocality(near.locality);
        } finally { setLocating(false); }
      },
      () => setLocating(false), // denial is a normal path: the manual picker is already visible
      { timeout: 8000 },
    );
  };

  const toggle = (tag: string) => {
    setInterests((cur) => (cur.includes(tag) ? cur.filter((x) => x !== tag) : [...cur, tag]));
    setPopTag(tag);
    setTimeout(() => setPopTag(null), 350);
  };

  const finish = async () => {
    setBusy(true); setError(null);
    try {
      const p = await api<Profile>('/profile', { body: { locality_city: city, locality_locality: locality || null, interests, language_preference: lang } });
      applyLanguage(lang);
      setProfile(p);
      router.replace('/');
    } catch (e) {
      setError(e instanceof ApiError ? e.message : t('state.error'));
      setBusy(false);
    }
  };

  return (
    <main className="screen" style={{ minHeight: '100vh' }}>
      <div className="progress" aria-label={t('onboarding.step', { n: step })} role="progressbar" aria-valuenow={step} aria-valuemin={1} aria-valuemax={3}>
        {[1, 2, 3].map((n) => <span key={n} className={n <= step ? 'on' : ''} />)}
      </div>

      {step === 1 && (
        <section className="stack fade-in" style={{ gap: 20 }}>
          <div>
            <h1 className="display">{t('onboarding.whereTitle')}</h1>
            <p className="muted">{t('onboarding.whereBody')}</p>
          </div>
          <div className="motif" style={{ padding: 20, borderRadius: 24 }}>
            <button className="btn btn--primary btn--block" onClick={useLocation} disabled={locating}>
              {locating ? t('onboarding.locating') : t('onboarding.useLocation')}
            </button>
          </div>
          <div className="row" style={{ gap: 12 }}><span className="divider grow" /><span className="caption">{t('onboarding.or')}</span><span className="divider grow" /></div>
          {locating ? (
            <div className="stack"><div className="sk" style={{ height: 48 }} /><div className="sk" style={{ height: 48 }} /></div>
          ) : (
            <PlacePicker city={city} locality={locality} onChange={(c, l) => { setCity(c); setLocality(l); }} label={t('onboarding.whereTitle')} />
          )}
          <button className="btn btn--primary btn--block" disabled={!city} onClick={() => setStep(2)}>{t('onboarding.continue')}</button>
        </section>
      )}

      {step === 2 && (
        <section className="stack fade-in" style={{ gap: 20 }}>
          <div>
            <h1 className="display">{t('onboarding.interestsTitle')}</h1>
            <p className="muted">{t('onboarding.interestsBody')}</p>
          </div>
          {taxonomy.map((g) => (
            <div key={g.group} className="stack" style={{ gap: 8 }}>
              <span className="label">{g.group}</span>
              <div className="chips">
                {g.interests.map((i) => {
                  const on = interests.includes(i.tag);
                  return (
                    <button key={i.tag} type="button" className={`chip${popTag === i.tag ? ' pop' : ''}`} aria-pressed={on} onClick={() => toggle(i.tag)}>
                      {on && <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" aria-hidden="true"><path d="M5 12l5 5L19 7" /></svg>}
                      {i.label}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
          <div className="row">
            <button className="btn btn--ghost" onClick={() => setStep(1)}>{t('common.back')}</button>
            <button className="btn btn--primary grow" disabled={interests.length === 0} onClick={() => setStep(3)}>{t('onboarding.continue')}</button>
          </div>
        </section>
      )}

      {step === 3 && (
        <section className="stack fade-in" style={{ gap: 20 }}>
          <div>
            <h1 className="display">{t('onboarding.languageTitle')}</h1>
            <p className="muted">{t('onboarding.languageBody')}</p>
          </div>
          <div className="stack" role="radiogroup">
            {SUPPORTED_LANGUAGES.map((l) => (
              <button key={l} type="button" role="radio" aria-checked={lang === l} className="radio" onClick={() => { setLang(l); applyLanguage(l); }}>
                <span className="radio__dot" />{LANGUAGE_NATIVE[l]}
              </button>
            ))}
          </div>
          {error && <p className="field__error">{error}</p>}
          <div className="row">
            <button className="btn btn--ghost" onClick={() => setStep(2)}>{t('common.back')}</button>
            <button className="btn btn--primary grow" disabled={busy} onClick={finish}>{t('onboarding.finish')}</button>
          </div>
        </section>
      )}
    </main>
  );
}

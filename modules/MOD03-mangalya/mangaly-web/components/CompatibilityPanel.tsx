'use client';

import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import HoroscopeMatch, { type HoroscopeMatchResponse } from '@/components/HoroscopeMatch';
import HowYouFit, { type Fit } from '@/components/HowYouFit';
import { getJson, query, resolveMediaUrl } from '@/lib/api';
import { formatClockTime } from '@/lib/profileFormat';

import './compatibility-panel.css';

/* [Owner, 2026-09-28] One place on a profile where everything the matching
 * engine knows about this pair is visible — "so they are not just working in
 * the backend, the user can also see them".
 *
 * Shaadi.com splits this into a "You & Her" tab (her preferences with ticks
 * and "You match 5/8") and an "Astro" pop-up (21/36 and eight rings). Mangalya
 * keeps the good part — both faces, one glance, then detail — and goes
 * further on what it can honestly show:
 *   · the summary line carries every signal at once: the engine's word
 *     ("Strong match", never its number), the gunas or poruthams, and how
 *     much the two share;
 *   · "You & them" is the reader's own list with ticks, the topics of THEIR
 *     wishes the reader meets (never their values or a fraction — their
 *     preferences stay private, FR020), and what the two simply share;
 *   · "Horoscope" is the full traditional reading in the family's own system
 *     (Ashtakoota and/or Porutham), rings first, the worked table a tap away.
 * A parent reading for their child sees it all from the child's seat. */

type Tab = 'fit' | 'horoscope';

type Props = {
  candidateId: string;
  forCandidate?: { accountId: string; name: string };
  /** Their birth time and place: always visible, before any connection
   *  (owner, 2026-09-27), so families can check with their own pandit. */
  birth?: { time?: string | null; place?: string | null } | null;
};

export default function CompatibilityPanel({ candidateId, forCandidate, birth }: Props) {
  const { t, i18n } = useTranslation(['discover', 'horoscope']);
  // Results are kept with the pair they belong to, so moving to another
  // profile never shows the previous person's reading for a moment.
  const forId = forCandidate?.accountId;
  const pairKey = `${candidateId}|${forId ?? ''}`;
  const [fitFor, setFit] = useState<{ key: string; value: Fit | null } | null>(null);
  const [horoFor, setHoro] = useState<{ key: string; value: HoroscopeMatchResponse | null } | null>(null);
  const [tab, setTab] = useState<Tab>('fit');
  const fit = fitFor?.key === pairKey ? fitFor.value : undefined;
  const horo = horoFor?.key === pairKey ? horoFor.value : undefined;

  useEffect(() => {
    let active = true;
    const key = `${candidateId}|${forId ?? ''}`;
    getJson<Fit>(`/discovery/fit/${candidateId}${query({ for_candidate: forId })}`).then((f) => {
      if (active) setFit({ key, value: f });
    });
    getJson<HoroscopeMatchResponse>(`/horoscope/match/${candidateId}${query({ for_candidate: forId })}`).then(
      (h) => {
        if (active) setHoro({ key, value: h });
      },
    );
    return () => {
      active = false;
    };
  }, [candidateId, forId]);

  if (fit === undefined && horo === undefined) return null;
  if (!fit && !horo) return null;

  const name = forCandidate?.name.split(' ')[0];
  const seat = name ? 'For' : '';

  // Two people of the same gender have no horoscope match; nothing to offer.
  const horoShown = !!horo && (horo.available || (!!horo.missing && horo.missing !== 'SAME_GENDER'));
  const match = horo?.available ? horo.match : null;
  const porutham = match?.porutham;
  const usePorutham = horo?.preferred_system === 'porutham' && porutham?.status === 'CALCULATED';
  const gunas = match?.ashtakoota.status === 'CALCULATED' ? match.ashtakoota.totalScore : null;
  const fmt = (n: number) => (Number.isInteger(n) ? String(n) : n.toFixed(1));
  const commons = fit?.common?.length ?? 0;

  const face = (url: string | null | undefined, cls: string) => {
    const src = url ? resolveMediaUrl(url) : null;
    return src ? (
      // eslint-disable-next-line @next/next/no-img-element
      <img className={`compat__face ${cls}`} src={src} alt="" />
    ) : (
      <span className={`compat__face compat__face--blank ${cls}`} aria-hidden="true" />
    );
  };

  return (
    <section id="compatibility" className="compat" aria-labelledby={`compat-${candidateId}`}>
      <div className="compat__top">
        <div className="compat__faces" aria-hidden="true">
          {face(fit?.seat_photo_url, 'compat__face--seat')}
          {face(fit?.other_photo_url, 'compat__face--other')}
        </div>
        <div className="compat__heading">
          <h2 id={`compat-${candidateId}`} className="compat__title">
            {t(`discover:fit.title${seat}`, { name })}
          </h2>
          <ul className="compat__summary">
            {fit?.label && (
              <li className="compat__pill compat__pill--word">{t(`discover:match.${fit.label}`)}</li>
            )}
            {usePorutham && porutham?.agreed != null ? (
              <li>
                <button type="button" className="compat__pill" onClick={() => setTab('horoscope')}>
                  {t('discover:compat.poruthams', { n: porutham.agreed, max: porutham.outOf })}
                </button>
              </li>
            ) : gunas != null ? (
              <li>
                <button type="button" className="compat__pill" onClick={() => setTab('horoscope')}>
                  {t('discover:compat.gunas', { n: fmt(gunas), max: match!.ashtakoota.maxScore })}
                </button>
              </li>
            ) : null}
            {commons > 0 && (
              <li>
                <button type="button" className="compat__pill" onClick={() => setTab('fit')}>
                  {t('discover:compat.common', { count: commons })}
                </button>
              </li>
            )}
          </ul>
        </div>
      </div>

      {horoShown && (
        <div className="compat__tabs" role="tablist" aria-label={t(`discover:fit.title${seat}`, { name })}>
          <button
            type="button"
            role="tab"
            id={`compat-tab-fit-${candidateId}`}
            aria-selected={tab === 'fit'}
            aria-controls={`compat-panel-${candidateId}`}
            className={`compat__tab${tab === 'fit' ? ' is-on' : ''}`}
            onClick={() => setTab('fit')}
          >
            {t(`discover:compat.tabFit${seat}`, { name })}
          </button>
          <button
            type="button"
            role="tab"
            id={`compat-tab-horoscope-${candidateId}`}
            aria-selected={tab === 'horoscope'}
            aria-controls={`compat-panel-${candidateId}`}
            className={`compat__tab${tab === 'horoscope' ? ' is-on' : ''}`}
            onClick={() => setTab('horoscope')}
          >
            {t('discover:compat.tabHoroscope')}
          </button>
        </div>
      )}

      <div
        id={`compat-panel-${candidateId}`}
        role={horoShown ? 'tabpanel' : undefined}
        aria-labelledby={horoShown ? `compat-tab-${tab}-${candidateId}` : undefined}
        className="compat__body"
      >
        {tab === 'horoscope' && horoShown ? (
          <>
            {(birth?.time || birth?.place) && (
              <p className="compat__birth">
                <span className="compat__birth-label">{t('discover:compat.birth')}</span>{' '}
                {[birth?.time ? formatClockTime(birth.time, i18n.language) : null, birth?.place]
                  .filter(Boolean)
                  .join(' · ')}
              </p>
            )}
            <HoroscopeMatch result={horo!} forCandidate={forCandidate} bare />
          </>
        ) : fit ? (
          <HowYouFit candidateId={candidateId} forCandidate={forCandidate} data={fit} bare />
        ) : null}
      </div>
    </section>
  );
}

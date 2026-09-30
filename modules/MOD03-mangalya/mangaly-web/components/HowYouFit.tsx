'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { getJson } from '@/lib/api';
import { ITEM_OPTIONS } from '@/lib/matchmaker';

import './how-you-fit.css';

/* [DEC-V1-031] "How you fit each other" on a profile.
 *
 * Shaadi.com shows one side only — her preference list with ticks and a
 * "7/10" count. Mangalya shows both directions, weighted by what matters:
 *   · what YOU are looking for, point by point — met, close, different, or
 *     not shared — with your must-haves marked (your own list, so shown in
 *     full, and editable from here);
 *   · what THEY are looking for, only as the topics you meet. Their values,
 *     their misses and how many wishes they have stay private (FR020), so
 *     nothing here can be read back into their list.
 * No fraction, no percentage (baseline §3): the one summary is a word.
 *
 * [Owner, 2026-09-28] A reader who has not said what they want still gets a
 * rating: the word, and the generic points of match — what the two share
 * (roots, city, food, family values, education) — with a way to say more. */

type Status = 'met' | 'close' | 'differs' | 'unknown';
type Wish = {
  field: string;
  values: string[];
  min: number | null;
  max: number | null;
  must: boolean;
  importance: number;
  status: Status;
};
export type Fit = {
  label: 'strong' | 'good' | null;
  yours: Wish[];
  theirs_met: string[];
  /** What the two share, as sentences in the reader's language. */
  common?: string[];
  seat_photo_url?: string | null;
  other_photo_url?: string | null;
};

const OPTION_KEY: Record<string, string> = {
  relocation: 'relocation_willingness',
  education: 'highest_education_level',
};
const MARK: Record<Status, string> = { met: '✓', close: '≈', differs: '×', unknown: '–' };

type Props = {
  candidateId: string;
  /** A circle member reading for their candidate: the candidate's seat. */
  forCandidate?: { accountId: string; name: string };
  /** Already fetched by the compatibility panel; skips the request. */
  data?: Fit | null;
  /** Inside the compatibility panel: no card, no heading of its own. */
  bare?: boolean;
};

export default function HowYouFit({ candidateId, forCandidate, data, bare }: Props) {
  const { t } = useTranslation(['discover', 'profile']);
  const [fetched, setFit] = useState<Fit | null>(null);
  const fit = data !== undefined ? data : fetched;

  const forId = forCandidate?.accountId;
  useEffect(() => {
    if (data !== undefined) return;
    let active = true;
    const q = forId ? `?for_candidate=${encodeURIComponent(forId)}` : '';
    getJson<Fit>(`/discovery/fit/${candidateId}${q}`).then((f) => {
      if (active) setFit(f);
    });
    return () => {
      active = false;
    };
  }, [candidateId, forId, data]);

  if (!fit) return null;
  const name = forCandidate?.name.split(' ')[0];
  const seat = name ? 'For' : '';

  function wanted(w: Wish): string {
    if (w.field === 'age' || w.field === 'height_cm') {
      const unit = t(`discover:matchmaker.range.${w.field === 'age' ? 'years' : 'cm'}`);
      if (w.min && w.max) return `${w.min}–${w.max} ${unit}`;
      if (w.min) return t('discover:fit.atLeast', { value: `${w.min} ${unit}` });
      if (w.max) return t('discover:fit.upTo', { value: `${w.max} ${unit}` });
      return '';
    }
    if (ITEM_OPTIONS[w.field]) {
      return w.values
        .map((v) => t(`profile:option.${OPTION_KEY[w.field] ?? w.field}.${v}`, { defaultValue: v }))
        .join(', ');
    }
    return w.values.join(', ');
  }

  const field = (f: string) => t(`discover:matchmaker.field.${f}`);

  return (
    <section
      className={`fit${bare ? ' fit--bare' : ''}`}
      aria-labelledby={bare ? undefined : `fit-${candidateId}`}
    >
      {!bare && (
        <div className="fit__head">
          <h2 id={`fit-${candidateId}`} className="fit__title">
            {t(`discover:fit.title${seat}`, { name })}
          </h2>
          {fit.label && <span className="fit__label">{t(`discover:match.${fit.label}`)}</span>}
        </div>
      )}

      <div className="fit__cols">
        <div className="fit__col">
          <h3 className="fit__h">
            {t(fit.yours.length === 0 ? `discover:fit.common${seat}` : `discover:fit.yours${seat}`, { name })}
          </h3>
          {fit.yours.length === 0 ? (
            <>
              {(fit.common ?? []).length > 0 ? (
                <ul className="fit__list">
                  {(fit.common ?? []).map((point) => (
                    <li key={point} className="fit__row fit__row--met">
                      <span className="fit__mark" aria-hidden="true">
                        {MARK.met}
                      </span>
                      <span className="fit__what">
                        <span className="fit__wanted">{point}</span>
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="fit__quiet">{t('discover:fit.commonNone')}</p>
              )}
              {forCandidate ? (
                <p className="fit__quiet">{t('discover:fit.yoursEmptyFor', { name })}</p>
              ) : (
                <Link href="/me/matchmaker" className="fit__cta" prefetch={false}>
                  {t('discover:fit.commonCta')} →
                </Link>
              )}
            </>
          ) : (
            <ul className="fit__list">
              {fit.yours.map((w) => (
                <li key={w.field} className={`fit__row fit__row--${w.status}`}>
                  <span className="fit__mark" aria-hidden="true">
                    {MARK[w.status]}
                  </span>
                  <span className="fit__what">
                    <span className="fit__field">
                      {field(w.field)}
                      {w.must && <span className="fit__must">{t('discover:matchmaker.must')}</span>}
                    </span>
                    <span className="fit__wanted">{wanted(w)}</span>
                  </span>
                  <span className="fit__status">{t(`discover:fit.status.${w.status}`)}</span>
                </li>
              ))}
            </ul>
          )}
          {!forCandidate && fit.yours.length > 0 && (
            <Link href="/me/matchmaker" className="fit__edit" prefetch={false}>
              {t('discover:fit.edit')}
            </Link>
          )}
          {/* Their own list first; what the two simply share comes after. */}
          {fit.yours.length > 0 && (fit.common ?? []).length > 0 && (
            <>
              <h3 className="fit__h fit__h--gap">{t('discover:fit.alsoCommon')}</h3>
              <ul className="fit__chips">
                {(fit.common ?? []).map((point) => (
                  <li key={point} className="fit__chip">
                    <span aria-hidden="true">✓</span> {point}
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>

        <div className="fit__col">
          <h3 className="fit__h">{t(`discover:fit.theirs${seat}`, { name })}</h3>
          {fit.theirs_met.length > 0 ? (
            <>
              <p className="fit__quiet">{t(`discover:fit.theirsMet${seat}`, { name })}</p>
              <ul className="fit__chips">
                {fit.theirs_met.map((f) => (
                  <li key={f} className="fit__chip">
                    <span aria-hidden="true">✓</span> {field(f)}
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <p className="fit__quiet">{t('discover:fit.theirsNone')}</p>
          )}
          <p className="fit__private">{t('discover:fit.private')}</p>
        </div>
      </div>
    </section>
  );
}

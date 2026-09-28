import type { Explanation, KootaName, KootaResult } from './types.ts';
import type { RuleScore } from './ashtakootaRules.ts';

/* Deterministic explanations. Each koota result carries codes and parameters,
 * never generated prose; the UI renders them through translation keys in each
 * language. Wording is neutral: it names the traditional rule, never what a
 * score "means" for a marriage. */

/** What each koota is traditionally derived from. */
export const KOOTA_BASIS: Readonly<Record<KootaName, string>> = {
  VARNA: 'RASHI_VARNA_CLASS',
  VASHYA: 'RASHI_VASHYA_GROUP',
  TARA: 'NAKSHATRA_COUNT_REMAINDER',
  YONI: 'NAKSHATRA_YONI_ANIMAL',
  GRAHA_MAITRI: 'RASHI_LORD_FRIENDSHIP',
  GANA: 'NAKSHATRA_GANA',
  BHAKOOT: 'RASHI_DISTANCE',
  NADI: 'NAKSHATRA_NADI',
};

export function explainKoota(k: RuleScore): KootaResult {
  const params: Explanation['params'] = {
    basis: KOOTA_BASIS[k.koota],
    groomClass: k.groomClass,
    brideClass: k.brideClass,
    score: k.score,
    maxScore: k.maxScore,
    ...(k.notes ?? {}),
  };
  let code = `KOOTA.${k.koota}.${k.score === k.maxScore ? 'FULL' : k.score === 0 ? 'NONE' : 'PARTIAL'}`;
  if (k.exception?.applied) {
    code = `KOOTA.${k.koota}.EXCEPTION_APPLIED`;
    params.exception = k.exception.code;
  }
  return {
    koota: k.koota,
    score: k.score,
    maxScore: k.maxScore,
    groomClass: k.groomClass,
    brideClass: k.brideClass,
    exceptionApplied: k.exception ? k.exception.applied : null,
    exceptionCode: k.exception ? k.exception.code : null,
    explanation: { code, params },
  };
}

/** Notices shown with every horoscope result, whatever the score. */
export const STANDING_NOTICE_CODES = [
  'HOROSCOPE.NOTICE.TRADITIONAL_OPTIONAL_LAYER',
  'HOROSCOPE.NOTICE.NOT_SCIENTIFIC_NOT_A_PREDICTION',
  'HOROSCOPE.NOTICE.SEPARATE_FROM_MANGALY_COMPATIBILITY',
  'HOROSCOPE.NOTICE.MANGAL_NOT_IN_36',
] as const;

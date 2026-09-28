import type { HoroscopeConfiguration, MangalRuleset, MatchingConfiguration } from './types.ts';

/* Every value that changes what a calculation means lives here, in the open.
 * Nothing below is a provider default: the provider is told each of these and
 * refuses to run if it cannot honour them. */

/** Version of Mangaly's own pipeline (normalisation, sampling, canonical model, explanations). */
export const CALCULATION_VERSION = 'mangaly-horoscope/1.0.0';

/** Version of the Ashtakoota / Mangal rule set Mangaly presents. Bump on any rule change. */
// v3 (2026-09-27): Mangaly's own koota tables (domain/ashtakootaRules.ts),
// equal to AstroSage's on every observed pair, replace the provider's.
// v4 (2026-09-27): South Indian 10 poruthams added (domain/poruthamRules.ts).
export const RULES_VERSION = 'mangaly-ashtakoota-rules/4';

export const DEFAULT_HOROSCOPE_CONFIGURATION: Readonly<HoroscopeConfiguration> = Object.freeze({
  zodiacSystem: 'SIDEREAL',
  ayanamsha: 'LAHIRI',
  houseSystem: 'WHOLE_SIGN',
});

/**
 * The Mangal / Kuja Dosha rules the V1 provider implements: Mars counted from
 * the Lagna, the Moon and Venus; houses 1, 2, 4, 7, 8, 12; cancelled when Mars
 * is in Aries, Scorpio (own) or Capricorn (exalted). Other traditions use
 * fewer reference points or houses (many omit the 2nd house and Venus), so this
 * is a named rule set, never an unstated default.
 */
export const MANGAL_RULESET_INCLUSIVE_V1: Readonly<MangalRuleset> = Object.freeze({
  id: 'MANGAL_INCLUSIVE_V1',
  referencePoints: Object.freeze(['LAGNA', 'MOON', 'VENUS'] as const),
  houses: Object.freeze([1, 2, 4, 7, 8, 12]),
  cancellationMarsRashis: Object.freeze([1, 8, 10]),
});

/**
 * The rule set Mangaly shows (rules v3): AstroSage's, as read from its public
 * calculator for 40 synthetic people (test/fixtures/astrosage-mangal.json):
 * Mars in house 1, 4, 7, 8 or 12 counted from the ascendant and from the
 * Moon; HIGH when both, LOW when one; no own-sign cancellation; Venus and
 * the 2nd house not counted.
 */
export const MANGAL_RULESET_ASTROSAGE_V1: Readonly<MangalRuleset> = Object.freeze({
  id: 'MANGAL_ASTROSAGE_V1',
  referencePoints: Object.freeze(['LAGNA', 'MOON'] as const),
  houses: Object.freeze([1, 4, 7, 8, 12]),
  cancellationMarsRashis: Object.freeze([]),
  highFromReferences: 2,
});

export function defaultMatchingConfiguration(groomChart: 'A' | 'B'): MatchingConfiguration {
  return {
    matchingSystem: 'ASHTAKOOTA',
    rulesVersion: RULES_VERSION,
    groomChart,
    mangalRuleset: MANGAL_RULESET_ASTROSAGE_V1 as MangalRuleset,
  };
}

/** Births outside this range are refused: it is the range the engine has been exercised over. */
export const SUPPORTED_DATE_RANGE = Object.freeze({ fromYear: 1900, toYear: 2100 });

/** Samples taken across an uncertain birth-time window to see whether a result is stable. */
export const UNCERTAINTY_SAMPLES = 25;
export const MAX_UNCERTAINTY_MINUTES = 720;

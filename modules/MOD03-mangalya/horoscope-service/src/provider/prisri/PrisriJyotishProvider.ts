/* PrisriJyotishProvider — the only file in Mangaly that knows @prisri/jyotish.
 *
 * It converts Mangaly's inputs into the library's, calls it, and converts the
 * result back into Mangaly's canonical types. Nothing library-shaped (a Kundli
 * object, an English label, the library's "Good Match" verdict) crosses this
 * boundary.
 *
 * Version pin: the adapter was written and validated against exactly
 * PRISRI_VALIDATED_VERSION. It refuses to run against any other installed
 * version (PROVIDER_VERSION_MISMATCH), because the library parses no
 * structured rule data out — exceptions are read from its English
 * descriptions, which can change without notice. */

import { createRequire } from 'node:module';

import { KOOTA_MAX, KOOTA_ORDER } from '../../domain/types.ts';
import type {
  ExactChart,
  ExactPosition,
  GrahaName,
  HoroscopeConfiguration,
  KootaName,
  MangalDoshaResult,
  MangalInput,
  MatchingConfiguration,
  MoonPlacement,
} from '../../domain/types.ts';
import { HoroscopeError } from '../../domain/errors.ts';
import { MANGAL_RULESET_INCLUSIVE_V1 } from '../../domain/config.ts';
import { evaluateMangal } from '../../domain/mangalRules.ts';
import { placementFromLongitude, rashiCentre } from '../../domain/zodiac.ts';
import type {
  ChartRequest,
  HoroscopeProvider,
  ProviderDescriptor,
  ProviderKootaScore,
} from '../HoroscopeProvider.ts';

// ---- the library, loaded behind this adapter only ------------------------

const require = createRequire(import.meta.url);

interface PrisriPlanet {
  longitude: number;
  rashi: number;
  pada: number;
  isRetrograde: boolean;
}
interface PrisriKundli {
  ascendant: { longitude: number; rashi: number; pada: number };
  planets: Record<string, PrisriPlanet>;
}
interface PrisriKoota {
  name: string;
  score: number;
  maxScore: number;
  boy: string;
  girl: string;
  description: string;
}
interface PrisriLib {
  getKundli(date: Date, observer: unknown, config: Record<string, unknown>): PrisriKundli;
  matchKundli(boy: PrisriKundli, girl: PrisriKundli, options?: { lang?: string }): {
    ashtakoot: { totalScore: number; kootas: PrisriKoota[] };
  };
  checkMangalDosha(kundli: PrisriKundli, options?: { lang?: string }): {
    hasDosha: boolean;
    isHigh: boolean;
    description: string;
  };
  Observer: new (latitude: number, longitude: number, heightMeters: number) => unknown;
}

const lib = require('@prisri/jyotish') as PrisriLib;
const installedVersion = (require('@prisri/jyotish/package.json') as { version: string }).version;

export const PRISRI_PROVIDER_NAME = 'prisri-jyotish';
export const PRISRI_VALIDATED_VERSION = '1.1.12';

// ---- mappings -----------------------------------------------------------

const GRAHA_KEYS: Record<GrahaName, string> = {
  SUN: 'Sun',
  MOON: 'Moon',
  MARS: 'Mars',
  MERCURY: 'Mercury',
  JUPITER: 'Jupiter',
  VENUS: 'Venus',
  SATURN: 'Saturn',
  RAHU: 'Rahu',
  KETU: 'Ketu',
};

const KOOTA_BY_PROVIDER_NAME: Record<string, KootaName> = {
  Varna: 'VARNA',
  Vashya: 'VASHYA',
  Tara: 'TARA',
  Yoni: 'YONI',
  'Graha Maitri': 'GRAHA_MAITRI',
  Gana: 'GANA',
  Bhakoot: 'BHAKOOT',
  Nadi: 'NADI',
};

/** "Cat (Marjara)" → "CAT"; "Adi (Start)" → "ADI"; "Good" (Tara) → "FAVOURABLE_COUNT". */
function classCode(koota: KootaName, label: string): string {
  const head = label.split(' (')[0]?.trim() ?? '';
  if (koota === 'TARA') {
    if (head === 'Good') return 'FAVOURABLE_COUNT';
    if (head === 'Bad') return 'UNFAVOURABLE_COUNT';
  }
  if (!/^[A-Za-z]+$/.test(head)) {
    throw new HoroscopeError('PROVIDER_INCOMPLETE_RESULT', `unrecognised ${koota} class from provider`);
  }
  return head.toUpperCase();
}

function exceptionFor(koota: KootaName, description: string): ProviderKootaScore['exception'] {
  if (koota === 'BHAKOOT') {
    return description.includes('(Exception: Same Lord')
      ? { applied: true, code: 'BHAKOOT_SAME_RASHI_LORD' }
      : { applied: false, code: 'BHAKOOT_SAME_RASHI_LORD' };
  }
  if (koota === 'NADI') {
    return description.includes('(Exception: Same Rashi, Diff Nakshatra)')
      ? { applied: true, code: 'NADI_SAME_RASHI_DIFFERENT_NAKSHATRA' }
      : { applied: false, code: 'NADI_SAME_RASHI_DIFFERENT_NAKSHATRA' };
  }
  return null;
}

/** A longitude that lies inside both the given rashi and the given nakshatra. */
function longitudeFor(placement: MoonPlacement): number {
  const rStart = (placement.rashi - 1) * 30;
  const nStart = ((placement.nakshatra - 1) * 360) / 27;
  const lo = Math.max(rStart, nStart);
  const hi = Math.min(rStart + 30, nStart + 360 / 27);
  if (!(hi > lo)) {
    throw new HoroscopeError('INVALID_INPUT', 'Moon nakshatra does not fall in the given rashi', ['moon']);
  }
  return (lo + hi) / 2;
}

/* The library's matching functions take whole Kundli objects but, for these
 * two calls, read only the longitudes below. The adapter hands it minimal
 * objects built from Mangaly's canonical placements, so the result depends on
 * nothing else. */
function syntheticKundli(longitudes: { lagna: number; moon: number; mars: number; venus: number }): PrisriKundli {
  const planet = (longitude: number): PrisriPlanet => ({ longitude, rashi: 0, pada: 0, isRetrograde: false });
  return {
    ascendant: { longitude: longitudes.lagna, rashi: 0, pada: 0 },
    planets: {
      Moon: planet(longitudes.moon),
      Mars: planet(longitudes.mars),
      Venus: planet(longitudes.venus),
    },
  };
}

function exactPosition(p: { longitude: number; isRetrograde?: boolean } | undefined, body: string): ExactPosition {
  if (!p || typeof p.longitude !== 'number' || !Number.isFinite(p.longitude)) {
    throw new HoroscopeError('PROVIDER_INCOMPLETE_RESULT', `provider returned no position for ${body}`);
  }
  if (p.longitude < 0 || p.longitude >= 360) {
    throw new HoroscopeError('PROVIDER_INCONSISTENT', `provider returned an out-of-range longitude for ${body}`);
  }
  return { siderealLongitude: p.longitude, retrograde: p.isRetrograde === true };
}

// ---- the provider -------------------------------------------------------

export class PrisriJyotishProvider implements HoroscopeProvider {
  constructor() {
    if (installedVersion !== PRISRI_VALIDATED_VERSION) {
      throw new HoroscopeError(
        'PROVIDER_VERSION_MISMATCH',
        `installed @prisri/jyotish ${installedVersion} is not the validated ${PRISRI_VALIDATED_VERSION}`,
      );
    }
  }

  describe(): ProviderDescriptor {
    return {
      name: PRISRI_PROVIDER_NAME,
      version: installedVersion,
      license: 'ISC',
      capabilities: {
        ayanamshas: ['LAHIRI'],
        houseSystems: ['WHOLE_SIGN'],
        matchingSystems: ['ASHTAKOOTA'],
        mangalRulesetIds: [MANGAL_RULESET_INCLUSIVE_V1.id],
        exceptionRules: ['BHAKOOT_SAME_RASHI_LORD', 'NADI_SAME_RASHI_DIFFERENT_NAKSHATRA', 'MARS_IN_OWN_OR_EXALTED_SIGN'],
      },
    };
  }

  calculateChart(request: ChartRequest, configuration: HoroscopeConfiguration): ExactChart {
    if (configuration.zodiacSystem !== 'SIDEREAL' || configuration.ayanamsha !== 'LAHIRI' || configuration.houseSystem !== 'WHOLE_SIGN') {
      throw new HoroscopeError('UNSUPPORTED_CONFIGURATION', 'provider supports only sidereal Lahiri with whole-sign houses in this adapter');
    }
    const date = new Date(request.instantUtc);
    if (Number.isNaN(date.getTime())) throw new HoroscopeError('INVALID_INPUT', 'instant is not a valid date');

    let kundli: PrisriKundli;
    try {
      kundli = lib.getKundli(date, new lib.Observer(request.latitude, request.longitude, request.elevationMeters), {
        // Stated explicitly: never the library's defaults.
        ayanamsa: 'lahiri',
        houseSystem: 'whole_sign',
        lang: 'en',
      });
    } catch {
      // The library's own message may echo the input; it is not passed on.
      throw new HoroscopeError('PROVIDER_FAILURE', 'provider failed to calculate the chart');
    }

    const grahas = {} as Record<GrahaName, ExactPosition>;
    for (const [graha, key] of Object.entries(GRAHA_KEYS) as [GrahaName, string][]) {
      grahas[graha] = exactPosition(kundli.planets?.[key], graha);
    }
    const chart: ExactChart = { ascendant: exactPosition(kundli.ascendant, 'ASCENDANT'), grahas };

    // Cross-check: the library's own rashi label must agree with the longitude it reported.
    const check = (label: number | undefined, longitude: number, body: string) => {
      if (typeof label === 'number' && label !== placementFromLongitude(longitude).rashi) {
        throw new HoroscopeError('PROVIDER_INCONSISTENT', `provider rashi label disagrees with its longitude for ${body}`);
      }
    };
    check(kundli.ascendant.rashi, chart.ascendant.siderealLongitude, 'ASCENDANT');
    for (const [graha, key] of Object.entries(GRAHA_KEYS) as [GrahaName, string][]) {
      check(kundli.planets[key]?.rashi, grahas[graha].siderealLongitude, graha);
    }
    return chart;
  }

  calculateAshtakoota(groom: MoonPlacement, bride: MoonPlacement, configuration: MatchingConfiguration): ProviderKootaScore[] {
    if (configuration.matchingSystem !== 'ASHTAKOOTA') {
      throw new HoroscopeError('UNSUPPORTED_CONFIGURATION', 'provider supports only Ashtakoota matching');
    }
    const g = longitudeFor(groom);
    const b = longitudeFor(bride);
    let kootas: PrisriKoota[];
    try {
      // Only the Moon longitude is read for the eight kootas; the rest is filler.
      const result = lib.matchKundli(
        syntheticKundli({ lagna: g, moon: g, mars: g, venus: g }),
        syntheticKundli({ lagna: b, moon: b, mars: b, venus: b }),
        { lang: 'en' },
      );
      kootas = result.ashtakoot.kootas;
    } catch {
      throw new HoroscopeError('PROVIDER_FAILURE', 'provider failed to calculate Ashtakoota');
    }
    // The library's verdict and total are deliberately not read.

    const out: ProviderKootaScore[] = [];
    for (const k of kootas ?? []) {
      const koota = KOOTA_BY_PROVIDER_NAME[k.name];
      if (!koota) throw new HoroscopeError('PROVIDER_INCOMPLETE_RESULT', 'provider returned an unknown koota');
      if (k.maxScore !== KOOTA_MAX[koota] || !(k.score >= 0 && k.score <= k.maxScore)) {
        throw new HoroscopeError('PROVIDER_INCONSISTENT', `provider ${koota} score is out of range`);
      }
      out.push({
        koota,
        score: k.score,
        maxScore: k.maxScore,
        groomClass: classCode(koota, k.boy),
        brideClass: classCode(koota, k.girl),
        exception: exceptionFor(koota, k.description),
      });
    }
    const names = out.map((k) => k.koota).sort().join();
    if (out.length !== 8 || names !== [...KOOTA_ORDER].sort().join()) {
      throw new HoroscopeError('PROVIDER_INCOMPLETE_RESULT', 'provider did not return all eight kootas');
    }
    return KOOTA_ORDER.map((name) => out.find((k) => k.koota === name) as ProviderKootaScore);
  }

  calculateMangalDosha(input: MangalInput, configuration: MatchingConfiguration): MangalDoshaResult {
    if (configuration.mangalRuleset.id !== MANGAL_RULESET_INCLUSIVE_V1.id) {
      throw new HoroscopeError('UNSUPPORTED_CONFIGURATION', 'provider implements only the MANGAL_INCLUSIVE_V1 rule set');
    }
    let raw: { hasDosha: boolean; description: string };
    try {
      raw = lib.checkMangalDosha(
        syntheticKundli({
          lagna: rashiCentre(input.lagnaRashi),
          moon: rashiCentre(input.moonRashi),
          mars: rashiCentre(input.marsRashi),
          venus: rashiCentre(input.venusRashi),
        }),
        { lang: 'en' },
      );
    } catch {
      throw new HoroscopeError('PROVIDER_FAILURE', 'provider failed to calculate Mangal Dosha');
    }
    const providerStatus = raw.hasDosha ? 'PRESENT' : raw.description.startsWith('Cancelled') ? 'CANCELLED' : 'ABSENT';

    /* The library returns a flag and an English sentence. Mangaly's structured
     * rule gives the placements and the exception applied; the two must agree
     * or the result is refused rather than guessed. */
    const structured = evaluateMangal(input, configuration.mangalRuleset);
    if (structured.status !== providerStatus) {
      throw new HoroscopeError('PROVIDER_INCONSISTENT', 'provider Mangal result disagrees with the declared rule set');
    }
    return structured;
  }
}

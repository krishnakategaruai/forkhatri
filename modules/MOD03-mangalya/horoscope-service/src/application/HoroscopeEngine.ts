import {
  CALCULATION_VERSION,
  DEFAULT_HOROSCOPE_CONFIGURATION,
  RULES_VERSION,
  UNCERTAINTY_SAMPLES,
  defaultMatchingConfiguration,
} from '../domain/config.ts';
import { normalizeBirthDetails } from '../domain/birthTime.ts';
import { canonicalJson, canonicalizeSamples, sampleInstants, stableHash } from '../domain/canonical.ts';
import { HoroscopeError } from '../domain/errors.ts';
import { STANDING_NOTICE_CODES, explainKoota } from '../domain/explanations.ts';
import { evaluateMangal, indeterminateMangal } from '../domain/mangalRules.ts';
import { scoreAshtakoota, vashyaNeedsHalf } from '../domain/ashtakootaRules.ts';
import { scorePorutham } from '../domain/poruthamRules.ts';
import { ASHTAKOOTA_MAX_TOTAL } from '../domain/types.ts';
import type {
  AshtakootaResult,
  BirthDetails,
  CalculationWarning,
  CanonicalHoroscope,
  CanonicalPosition,
  HoroscopeConfiguration,
  HoroscopeMatch,
  MangalDoshaResult,
  MangalPairing,
  MatchingConfiguration,
  PoruthamResult,
} from '../domain/types.ts';
import type { HoroscopeProvider } from '../provider/HoroscopeProvider.ts';

/* The stateless calculation pipeline:
 *
 *   BirthDetails → normalised input → provider chart(s) → CanonicalHoroscope
 *   CanonicalHoroscope × 2 → Ashtakoota (8 kootas, /36) + Mangal (separate)
 *
 * It knows the provider only through HoroscopeProvider. Given the same input,
 * configuration, provider version and rules version it always returns the
 * same result, and ids are derived from exactly those things. */

interface CacheEntry {
  value: CanonicalHoroscope;
  expiresAt: number;
}

export interface EngineOptions {
  configuration?: HoroscopeConfiguration;
  /** Individual charts are cached this long (ms), then dropped; birth data is never kept indefinitely in memory. */
  chartCacheTtlMs?: number;
  chartCacheMaxEntries?: number;
  now?: () => number;
}

export class HoroscopeEngine {
  private readonly provider: HoroscopeProvider;
  readonly configuration: HoroscopeConfiguration;
  private readonly cache = new Map<string, CacheEntry>();
  private readonly ttl: number;
  private readonly maxEntries: number;
  private readonly now: () => number;

  constructor(provider: HoroscopeProvider, options: EngineOptions = {}) {
    this.provider = provider;
    this.configuration = Object.freeze({ ...(options.configuration ?? DEFAULT_HOROSCOPE_CONFIGURATION) });
    this.ttl = options.chartCacheTtlMs ?? 10 * 60_000;
    this.maxEntries = options.chartCacheMaxEntries ?? 500;
    this.now = options.now ?? Date.now;

    const d = provider.describe();
    if (!d.capabilities.ayanamshas.includes(this.configuration.ayanamsha) || !d.capabilities.houseSystems.includes(this.configuration.houseSystem)) {
      throw new HoroscopeError('UNSUPPORTED_CONFIGURATION', 'the provider cannot honour the configured ayanamsha or house system');
    }
  }

  providerIdentity(): { name: string; version: string } {
    const d = this.provider.describe();
    return { name: d.name, version: d.version };
  }

  // ------------------------------------------------------------- chart ---

  calculateChart(details: BirthDetails): CanonicalHoroscope {
    const input = normalizeBirthDetails(details);
    const provider = this.providerIdentity();
    const key = stableHash({
      input,
      configuration: this.configuration,
      provider,
      calculationVersion: CALCULATION_VERSION,
      rulesVersion: RULES_VERSION,
    });

    const hit = this.cache.get(key);
    if (hit && hit.expiresAt > this.now()) return structuredClone(hit.value);

    const instants = sampleInstants(input, UNCERTAINTY_SAMPLES);
    const charts = instants.map((instantUtc) =>
      this.provider.calculateChart(
        { instantUtc, latitude: input.latitude, longitude: input.longitude, elevationMeters: input.elevationMeters },
        this.configuration,
      ),
    );
    const { moonSignHalf, ascendant, planetaryPositions, warnings } = canonicalizeSamples(input, charts);
    const byBody = (b: string) => planetaryPositions.find((p) => p.body === b) as CanonicalPosition;
    const moon = byBody('MOON');
    const sun = byBody('SUN');
    const mars = byBody('MARS');
    const venus = byBody('VENUS');

    const mangalInput =
      ascendant.rashi !== null && moon.rashi !== null && mars.rashi !== null && venus.rashi !== null
        ? { lagnaRashi: ascendant.rashi, moonRashi: moon.rashi, marsRashi: mars.rashi, venusRashi: venus.rashi }
        : null;
    const mangalRules = defaultMatchingConfiguration('A').mangalRuleset;
    const horoscope: CanonicalHoroscope = {
      calculationId: `hc_${key.slice(0, 32)}`,
      calculationVersion: CALCULATION_VERSION,
      provider,
      rulesVersion: RULES_VERSION,
      configuration: { ...this.configuration },
      input,
      ascendant,
      moon,
      sun,
      rashi: moon.rashi,
      nakshatra: moon.nakshatra,
      nakshatraPada: moon.pada,
      moonSignHalf,
      planetaryPositions,
      mangalInput,
      mangal: mangalInput ? evaluateMangal(mangalInput, mangalRules) : indeterminateMangal(mangalRules),
      calculationWarnings: warnings,
    };

    this.remember(key, horoscope);
    return structuredClone(horoscope);
  }

  private remember(key: string, value: CanonicalHoroscope): void {
    const now = this.now();
    for (const [k, v] of this.cache) if (v.expiresAt <= now) this.cache.delete(k);
    while (this.cache.size >= this.maxEntries) {
      const oldest = this.cache.keys().next().value;
      if (oldest === undefined) break;
      this.cache.delete(oldest);
    }
    this.cache.set(key, { value: structuredClone(value), expiresAt: now + this.ttl });
  }

  clearCache(): void {
    this.cache.clear();
  }

  // ------------------------------------------------------------- match ---

  /** Refuses charts produced by a different pipeline, provider, rule set or configuration. */
  assertCurrent(chart: CanonicalHoroscope): void {
    const provider = this.providerIdentity();
    if (
      chart.calculationVersion !== CALCULATION_VERSION ||
      chart.rulesVersion !== RULES_VERSION ||
      chart.provider.name !== provider.name ||
      chart.provider.version !== provider.version ||
      canonicalJson(chart.configuration) !== canonicalJson(this.configuration)
    ) {
      throw new HoroscopeError(
        'PROVIDER_VERSION_MISMATCH',
        'chart was calculated by a different engine, rules or configuration version; recalculate it before matching',
      );
    }
  }

  calculateMatch(groom: CanonicalHoroscope, bride: CanonicalHoroscope): HoroscopeMatch {
    this.assertCurrent(groom);
    this.assertCurrent(bride);
    // The configuration always names the groom side; charts are passed already in that order.
    const config: MatchingConfiguration = defaultMatchingConfiguration('A');

    const ashtakoota = this.ashtakoota(groom, bride, config);
    const porutham = this.porutham(groom, bride);
    const mangalGroom = this.mangal(groom, config);
    const mangalBride = this.mangal(bride, config);

    const warnings: CalculationWarning[] = [];
    const seen = new Set<string>();
    for (const w of [...groom.calculationWarnings, ...bride.calculationWarnings]) {
      const k = canonicalJson(w);
      if (!seen.has(k)) {
        seen.add(k);
        warnings.push(w);
      }
    }

    const body = {
      calculationVersion: CALCULATION_VERSION,
      rulesVersion: RULES_VERSION,
      traditionalSystem: 'ASHTAKOOTA' as const,
      groomChartId: groom.calculationId,
      brideChartId: bride.calculationId,
      ashtakoota,
      porutham,
      mangal: { groom: mangalGroom, bride: mangalBride, pairing: pairing(mangalGroom, mangalBride) },
      warnings,
      presentation: {
        layer: 'TRADITIONAL_OPTIONAL' as const,
        headline:
          ashtakoota.status === 'CALCULATED'
            ? { code: 'ASHTAKOOTA_SCORE' as const, score: ashtakoota.totalScore as number, outOf: ASHTAKOOTA_MAX_TOTAL }
            : { code: 'ASHTAKOOTA_NOT_DETERMINABLE' as const },
        noticeCodes: [...STANDING_NOTICE_CODES],
      },
    };
    return { matchId: `hm_${stableHash(body).slice(0, 32)}`, ...body };
  }

  private ashtakoota(groom: CanonicalHoroscope, bride: CanonicalHoroscope, config: MatchingConfiguration): AshtakootaResult {
    const reasons: string[] = [];
    if (groom.rashi === null || groom.nakshatra === null) reasons.push('GROOM_MOON_NOT_DETERMINABLE');
    if (bride.rashi === null || bride.nakshatra === null) reasons.push('BRIDE_MOON_NOT_DETERMINABLE');
    // Vashya splits Sagittarius and Capricorn at 15°; an uncertain time may leave the half unknown.
    if (reasons.length === 0) {
      if (vashyaNeedsHalf(groom.rashi as number) && groom.moonSignHalf === null) reasons.push('GROOM_MOON_SIGN_HALF_NOT_DETERMINABLE');
      if (vashyaNeedsHalf(bride.rashi as number) && bride.moonSignHalf === null) reasons.push('BRIDE_MOON_SIGN_HALF_NOT_DETERMINABLE');
    }
    if (reasons.length > 0) {
      return {
        matchingSystem: 'ASHTAKOOTA',
        rulesVersion: config.rulesVersion,
        status: 'NOT_DETERMINABLE',
        totalScore: null,
        maxScore: ASHTAKOOTA_MAX_TOTAL,
        kootas: [],
        notDeterminableReasons: reasons,
      };
    }
    // Mangaly's own tables (domain/ashtakootaRules.ts); the provider supplies positions only.
    const scores = scoreAshtakoota(
      { rashi: groom.rashi as number, nakshatra: groom.nakshatra as number, signHalf: groom.moonSignHalf },
      { rashi: bride.rashi as number, nakshatra: bride.nakshatra as number, signHalf: bride.moonSignHalf },
    );
    const kootas = scores.map(explainKoota);
    const total = kootas.reduce((sum, k) => sum + k.score, 0);
    // Half-point kootas exist (Tara, Vashya, Graha Maitri); keep the sum exact to the half.
    return {
      matchingSystem: 'ASHTAKOOTA',
      rulesVersion: config.rulesVersion,
      status: 'CALCULATED',
      totalScore: Math.round(total * 2) / 2,
      maxScore: ASHTAKOOTA_MAX_TOTAL,
      kootas,
      notDeterminableReasons: [],
    };
  }

  /** South Indian 10 poruthams, counted from the bride's star to the groom's. */
  private porutham(groom: CanonicalHoroscope, bride: CanonicalHoroscope): PoruthamResult {
    const reasons: string[] = [];
    if (groom.rashi === null || groom.nakshatra === null) reasons.push('GROOM_MOON_NOT_DETERMINABLE');
    if (bride.rashi === null || bride.nakshatra === null) reasons.push('BRIDE_MOON_NOT_DETERMINABLE');
    if (reasons.length > 0) {
      return { matchingSystem: 'PORUTHAM', rulesVersion: RULES_VERSION, status: 'NOT_DETERMINABLE', agreed: null, outOf: 10, essentialsAgree: null, items: [], notDeterminableReasons: reasons };
    }
    const items = scorePorutham(
      { rashi: bride.rashi as number, nakshatra: bride.nakshatra as number },
      { rashi: groom.rashi as number, nakshatra: groom.nakshatra as number },
    );
    return {
      matchingSystem: 'PORUTHAM',
      rulesVersion: RULES_VERSION,
      status: 'CALCULATED',
      agreed: items.filter((i) => i.agrees).length,
      outOf: 10,
      essentialsAgree: items.filter((i) => i.essential).every((i) => i.agrees),
      items,
      notDeterminableReasons: [],
    };
  }

  private mangal(chart: CanonicalHoroscope, config: MatchingConfiguration): MangalDoshaResult {
    if (!chart.mangalInput) return indeterminateMangal(config.mangalRuleset);
    // Mangaly's rule set (AstroSage's), on the provider's positions.
    return evaluateMangal(chart.mangalInput, config.mangalRuleset);
  }
}

function pairing(a: MangalDoshaResult, b: MangalDoshaResult): MangalPairing {
  if (a.status === 'INDETERMINATE' || b.status === 'INDETERMINATE') return 'INDETERMINATE';
  const pa = a.status === 'PRESENT';
  const pb = b.status === 'PRESENT';
  if (pa && pb) return 'BOTH_PRESENT';
  if (pa || pb) return 'ONE_PRESENT';
  return 'NEITHER_PRESENT';
}

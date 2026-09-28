import { createDefaultEngine } from '../../src/index.ts';
import { defaultMatchingConfiguration, MANGAL_RULESET_INCLUSIVE_V1 } from '../../src/domain/config.ts';
import { distanceToBoundary, placementFromLongitude } from '../../src/domain/zodiac.ts';
import { GRAHA_ORDER, KOOTA_ORDER } from '../../src/domain/types.ts';
import type { CanonicalHoroscope, GrahaName, MangalRuleset, MoonPlacement } from '../../src/domain/types.ts';
import { PrisriJyotishProvider } from '../../src/provider/prisri/PrisriJyotishProvider.ts';
import { referenceChart, TOLERANCE_DEG } from '../reference/astronomy.ts';
import type { ReferenceChart } from '../reference/astronomy.ts';
import { scoreAshtakoota } from '../../src/domain/ashtakootaRules.ts';
import { generateCorpus, generatePairs } from './corpus.ts';

/* Differential testing: the provider against independent references.
 *
 * Every mismatch is recorded with its input, the provider's output and the
 * reference output, and given a category:
 *   ASTRONOMICAL | TIMEZONE | AYANAMSHA | RULE_DEFINITION | EXCEPTION |
 *   PROVIDER_BUG | EXPECTED_REGIONAL_VARIATION | UNEXPLAINED
 * Nothing is corrected. A mismatch whose cause is not one of the documented
 * causes is UNEXPLAINED, and the test suite fails on any of those. */

export type Category =
  | 'ASTRONOMICAL'
  | 'TIMEZONE'
  | 'AYANAMSHA'
  | 'RULE_DEFINITION'
  | 'EXCEPTION'
  | 'PROVIDER_BUG'
  | 'EXPECTED_REGIONAL_VARIATION'
  | 'UNEXPLAINED';

export interface Mismatch {
  area: string;
  category: Category;
  cause: string;
  input: unknown;
  provider: unknown;
  reference: unknown;
}

export interface DifferentialReport {
  generatedWith: { provider: { name: string; version: string }; seed: number };
  charts: {
    compared: number;
    bodiesCompared: number;
    maxAbsDiffDeg: Record<string, number>;
    placementComparisons: number;
    placementSkippedNearBoundary: number;
  };
  pairs: { compared: number; totalScoreDiffers: number };
  exhaustivePlacements: { placements: number; pairs: number };
  exhaustiveMangal: { inputs: number; disagreements: number; classicalNarrowDiffers: number };
  mismatchCounts: Record<string, number>;
  mismatches: Mismatch[];
}

const angular = (a: number, b: number) => {
  const d = Math.abs(a - b) % 360;
  return Math.min(d, 360 - d);
};

/** Every (rashi, nakshatra) combination a Moon can have: 36 of them. */
export function allMoonPlacements(): MoonPlacement[] {
  const out: MoonPlacement[] = [];
  for (let n = 1; n <= 27; n++) {
    const s = ((n - 1) * 360) / 27;
    const e = (n * 360) / 27;
    for (let r = 1; r <= 12; r++) {
      const rs = (r - 1) * 30;
      if (Math.min(e, rs + 30) > Math.max(s, rs)) out.push({ rashi: r, nakshatra: n });
    }
  }
  return out;
}

/** Why the provider's koota differs from Mangaly's rules, when the cause is a known rule difference. */
function classifyKoota(
  koota: string,
  provider: { score: number; groomClass: string; brideClass: string; exception?: { applied: boolean } | null },
  groom: { rashi: number; half: 1 | 2 },
  bride: { rashi: number; half: 1 | 2 },
): { category: Category; cause: string } {
  if (koota === 'YONI') {
    return { category: 'RULE_DEFINITION', cause: "YONI_TABLE: provider uses a simplified table (same 4 / sworn enemy 0 / three enemy pairs 1 / else 2); Mangaly uses AstroSage's table" };
  }
  if (koota === 'GANA' && provider.groomClass === 'RAKSHASA' && provider.brideClass === 'DEVA') {
    return { category: 'RULE_DEFINITION', cause: 'GANA_RAKSHASA_GROOM_DEVA_BRIDE: provider 0; Drik Panchang and AstroSage 1' };
  }
  if (koota === 'BHAKOOT' && provider.exception?.applied) {
    return { category: 'EXCEPTION', cause: 'BHAKOOT_SAME_LORD: provider restores 7 points when both signs share a lord; Drik Panchang and AstroSage score 0' };
  }
  if (koota === 'VASHYA') {
    const split = (s: { rashi: number; half: 1 | 2 }) => (s.rashi === 9 || s.rashi === 10) && s.half === 2;
    if (split(groom) || split(bride)) {
      return { category: 'RULE_DEFINITION', cause: 'VASHYA_HALF_SIGN: provider treats Sagittarius and Capricorn as whole signs; AstroSage splits them at 15°' };
    }
    const pair = `${provider.groomClass}-${provider.brideClass}`;
    if (pair === 'CHATUSHPAD-VANCHAR' || pair === 'VANCHAR-CHATUSHPAD') {
      return { category: 'RULE_DEFINITION', cause: 'VASHYA_CHATUSHPADA_VANACHARA: provider 0.5 both ways; AstroSage 0.5 only for a Vanachara groom' };
    }
    if (pair === 'MANAV-KEET') {
      return { category: 'RULE_DEFINITION', cause: 'VASHYA_MANAVA_KEETA: provider 1; AstroSage 0 for a Manava groom with a Keeta bride' };
    }
  }
  if (koota === 'NADI' && provider.exception?.applied) {
    return { category: 'EXCEPTION', cause: 'NADI_SAME_SIGN: provider keeps 8 when the Moon sign is the same and the birth stars differ; AstroSage scores 0' };
  }
  return { category: 'UNEXPLAINED', cause: 'no documented cause' };
}

export function runDifferential(seed = 20260927, chartCount = 200, pairCount = 200): DifferentialReport {
  const engine = createDefaultEngine({ chartCacheTtlMs: 0 });
  const provider = new PrisriJyotishProvider();
  const mismatches: Mismatch[] = [];
  const maxAbs: Record<string, number> = {};
  let bodiesCompared = 0;
  let placementComparisons = 0;
  let placementSkipped = 0;

  // ---- 1. individual charts against the independent astronomy ----------
  const corpus = generateCorpus(seed, chartCount);
  const charts: CanonicalHoroscope[] = [];
  for (const person of corpus) {
    const chart = engine.calculateChart(person.details);
    charts.push(chart);
    const ms = Date.parse(chart.input.instantUtc as string);
    const ref = referenceChart(ms, chart.input.latitude, chart.input.longitude);
    const bodies: [keyof ReferenceChart, number][] = [
      ['ASCENDANT', chart.ascendant.siderealLongitude as number],
      ...GRAHA_ORDER.map((g: GrahaName) => [g, chart.planetaryPositions.find((p) => p.body === g)?.siderealLongitude as number] as [keyof ReferenceChart, number]),
    ];
    for (const [body, lon] of bodies) {
      bodiesCompared++;
      const d = angular(lon, ref[body]);
      maxAbs[body] = Math.max(maxAbs[body] ?? 0, d);
      const tol = TOLERANCE_DEG[body];
      if (d > tol) {
        mismatches.push({
          area: `chart.${body}.longitude`,
          category: 'ASTRONOMICAL',
          cause: `difference ${d.toFixed(4)}° exceeds tolerance ${tol}°`,
          input: { id: person.id, instantUtc: chart.input.instantUtc },
          provider: lon,
          reference: ref[body],
        });
        continue;
      }
      // Rashi / nakshatra / pada are compared only where the reference is decisive.
      if (distanceToBoundary(ref[body]) <= tol) {
        placementSkipped++;
        continue;
      }
      placementComparisons++;
      const a = placementFromLongitude(lon);
      const b = placementFromLongitude(ref[body]);
      if (a.rashi !== b.rashi || a.nakshatra !== b.nakshatra || a.pada !== b.pada) {
        mismatches.push({ area: `chart.${body}.placement`, category: 'UNEXPLAINED', cause: 'placement differs away from a boundary', input: { id: person.id }, provider: a, reference: b });
      }
    }
  }

  // ---- 2. pairs: the provider's kootas against Mangaly's rules, same Moons ----
  const pairs = generatePairs(seed, charts.length, pairCount);
  const cfg = defaultMatchingConfiguration('A');
  let totalDiffers = 0;
  const halfOf = (c: CanonicalHoroscope) => (c.moonSignHalf ?? 1) as 1 | 2;
  for (const [gi, bi] of pairs) {
    const g = charts[gi] as CanonicalHoroscope;
    const b = charts[bi] as CanonicalHoroscope;
    const gm = { rashi: g.rashi as number, nakshatra: g.nakshatra as number, signHalf: halfOf(g) };
    const bm = { rashi: b.rashi as number, nakshatra: b.nakshatra as number, signHalf: halfOf(b) };
    const provided = provider.calculateAshtakoota(gm, bm, cfg);
    const ours = scoreAshtakoota(gm, bm);
    const sum = (xs: { score: number }[]) => xs.reduce((s, k) => s + k.score, 0);
    if (sum(provided) !== sum(ours)) totalDiffers++;
    for (const [i, name] of KOOTA_ORDER.entries()) {
      const p = provided[i];
      const r = ours[i];
      if (!p || !r) throw new Error('missing koota');
      if (p.score !== r.score) {
        const c = classifyKoota(name, p, { rashi: gm.rashi, half: gm.signHalf }, { rashi: bm.rashi, half: bm.signHalf });
        mismatches.push({ area: `pair.${name}.score`, ...c, input: { groom: corpus[gi]?.id, bride: corpus[bi]?.id }, provider: { score: p.score, groomClass: p.groomClass, brideClass: p.brideClass }, reference: { score: r.score } });
      }
    }
  }

  // ---- 3. every possible Moon placement pair (first half of each sign) ----
  const placements = allMoonPlacements();
  for (const g of placements) {
    for (const b of placements) {
      const p = provider.calculateAshtakoota(g, b, cfg);
      const r = scoreAshtakoota({ ...g, signHalf: 1 }, { ...b, signHalf: 1 });
      for (const [i, name] of KOOTA_ORDER.entries()) {
        const pk = p[i];
        const rk = r[i];
        if (!pk || !rk) throw new Error('missing koota');
        if (pk.score !== rk.score) {
          const c = classifyKoota(name, pk, { rashi: g.rashi, half: 1 }, { rashi: b.rashi, half: 1 });
          mismatches.push({ area: `placement.${name}.score`, ...c, input: { groom: g, bride: b }, provider: { score: pk.score, groomClass: pk.groomClass, brideClass: pk.brideClass }, reference: { score: rk.score } });
        }
      }
    }
  }

  // ---- 4. Mangal: every sign combination; the adapter itself refuses any disagreement ----
  let mangalInputs = 0;
  let mangalDisagreements = 0;
  let narrowDiffers = 0;
  const narrow: MangalRuleset = { id: 'CLASSICAL_NARROW', referencePoints: ['LAGNA'], houses: [1, 4, 7, 8, 12], cancellationMarsRashis: [] };
  for (let lagna = 1; lagna <= 12; lagna++)
    for (let moon = 1; moon <= 12; moon++)
      for (let venus = 1; venus <= 12; venus++)
        for (let mars = 1; mars <= 12; mars++) {
          mangalInputs++;
          const input = { lagnaRashi: lagna, moonRashi: moon, venusRashi: venus, marsRashi: mars };
          let status: string;
          try {
            status = provider.calculateMangalDosha(input, { ...cfg, mangalRuleset: MANGAL_RULESET_INCLUSIVE_V1 as MangalRuleset }).status;
          } catch {
            mangalDisagreements++;
            mismatches.push({ area: 'mangal', category: 'UNEXPLAINED', cause: 'provider disagrees with declared rule set', input, provider: 'error', reference: null });
            continue;
          }
          // How often a narrower, lagna-only tradition would say otherwise: regional variation, recorded as a count only.
          const house = ((mars - lagna + 12) % 12) + 1;
          const narrowPresent = narrow.houses.includes(house);
          if (narrowPresent !== (status === 'PRESENT')) narrowDiffers++;
        }

  const counts: Record<string, number> = {};
  for (const m of mismatches) {
    const key = `${m.category}:${m.area.replace(/^(pair|placement)\./, '')}`;
    counts[key] = (counts[key] ?? 0) + 1;
  }

  return {
    generatedWith: { provider: engine.providerIdentity(), seed },
    charts: { compared: charts.length, bodiesCompared, maxAbsDiffDeg: maxAbs, placementComparisons, placementSkippedNearBoundary: placementSkipped },
    pairs: { compared: pairs.length, totalScoreDiffers: totalDiffers },
    exhaustivePlacements: { placements: placements.length, pairs: placements.length ** 2 },
    exhaustiveMangal: { inputs: mangalInputs, disagreements: mangalDisagreements, classicalNarrowDiffers: narrowDiffers },
    mismatchCounts: counts,
    mismatches,
  };
}

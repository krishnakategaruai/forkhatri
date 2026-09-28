import { createDefaultEngine } from '../../src/index.ts';
import type { BirthDetails, CanonicalHoroscope, HoroscopeMatch } from '../../src/domain/types.ts';
import { generateCorpus, generatePairs } from '../differential/corpus.ts';

/* Golden fixtures: version-controlled expected outputs for a fixed synthetic
 * corpus plus hand-picked edge cases. They lock behaviour — any change in the
 * provider, rules or pipeline shows up as a diff — but they are a regression
 * guard, not proof of correctness (that is what the differential harness and
 * independent references are for). */

export const GOLDEN_SEED = 7_2026;
export const GOLDEN_CHARTS = 60;
export const GOLDEN_PAIRS = 60;

/** Edge cases: time-zone history, clock changes, imprecise times, high latitude. */
export const EDGE_CASES: { id: string; note: string; details: BirthDetails }[] = [
  {
    id: 'edge-india-wartime-1943',
    note: 'India used UTC+06:30 war time from 1942-09 to 1945-10; not IST.',
    details: { birthDate: '1943-06-15', birthTime: '10:00', birthTimePrecision: 'EXACT', birthLocation: 'Chennai', latitude: 13.0827, longitude: 80.2707, timezone: 'Asia/Kolkata' },
  },
  {
    id: 'edge-new-york-dst-summer',
    note: 'Daylight saving time (UTC−04:00).',
    details: { birthDate: '1995-07-04', birthTime: '21:15', birthTimePrecision: 'EXACT', birthLocation: 'New York', latitude: 40.7128, longitude: -74.006, timezone: 'America/New_York' },
  },
  {
    id: 'edge-new-york-overlap-second',
    note: 'Wall-clock time repeated at the end of DST; the later (standard-time) occurrence chosen explicitly.',
    details: { birthDate: '2002-10-27', birthTime: '01:30', birthTimePrecision: 'EXACT', birthLocation: 'New York', latitude: 40.7128, longitude: -74.006, timezone: 'America/New_York', utcOffsetSeconds: -18000 },
  },
  {
    id: 'edge-kathmandu-offset',
    note: 'A +05:45 zone.',
    details: { birthDate: '1999-02-11', birthTime: '04:05', birthTimePrecision: 'EXACT', birthLocation: 'Kathmandu', latitude: 27.7172, longitude: 85.324, timezone: 'Asia/Kathmandu' },
  },
  {
    id: 'edge-southern-hemisphere',
    note: 'Southern latitude, DST in January.',
    details: { birthDate: '1988-01-20', birthTime: '23:59', birthTimePrecision: 'EXACT', birthLocation: 'Sydney', latitude: -33.8688, longitude: 151.2093, timezone: 'Australia/Sydney' },
  },
  {
    id: 'edge-high-latitude',
    note: 'High latitude, where the ascendant moves unevenly.',
    details: { birthDate: '1990-12-21', birthTime: '12:00', birthTimePrecision: 'EXACT', birthLocation: 'Tromsø', latitude: 69.6492, longitude: 18.9553, timezone: 'Europe/Oslo' },
  },
  {
    id: 'edge-approximate-30min',
    note: 'Approximate time ±30 minutes: fields that change inside the window are null.',
    details: { birthDate: '1992-03-08', birthTime: '07:40', birthTimePrecision: 'APPROXIMATE', birthTimeUncertaintyMinutes: 30, birthLocation: 'Hyderabad', latitude: 17.385, longitude: 78.4867, timezone: 'Asia/Kolkata' },
  },
  {
    id: 'edge-unknown-time',
    note: 'Unknown time on a day the Moon changes nakshatra: Ashtakoota cannot be settled.',
    details: { birthDate: '1997-09-18', birthTime: null, birthTimePrecision: 'UNKNOWN', birthLocation: 'Vijayawada', latitude: 16.5062, longitude: 80.648, timezone: 'Asia/Kolkata' },
  },
  {
    id: 'edge-unknown-time-moon-steady',
    note: 'Unknown time on a day the Moon stays in one rashi and nakshatra: Ashtakoota is calculated; pada, ascendant and Mangal are not.',
    details: { birthDate: '1997-09-01', birthTime: null, birthTimePrecision: 'UNKNOWN', birthLocation: 'Vijayawada', latitude: 16.5062, longitude: 80.648, timezone: 'Asia/Kolkata' },
  },
  {
    id: 'edge-mars-own-sign',
    note: 'Mars in Scorpio (own sign), 8th from the Moon: the cancellation path. Found by search and kept as a fixture.',
    details: { birthDate: '1984-03-07', birthTime: '06:10', birthTimePrecision: 'EXACT', birthLocation: 'Bengaluru', latitude: 12.9716, longitude: 77.5946, timezone: 'Asia/Kolkata' },
  },
];

export interface GoldenChart {
  id: string;
  input: BirthDetails;
  expected: Pick<
    CanonicalHoroscope,
    | 'calculationId'
    | 'calculationVersion'
    | 'provider'
    | 'rulesVersion'
    | 'configuration'
    | 'input'
    | 'ascendant'
    | 'rashi'
    | 'nakshatra'
    | 'nakshatraPada'
    | 'planetaryPositions'
    | 'mangalInput'
    | 'calculationWarnings'
  >;
}

export interface GoldenPair {
  groom: string;
  bride: string;
  expected: Pick<HoroscopeMatch, 'matchId' | 'calculationVersion' | 'rulesVersion' | 'ashtakoota' | 'mangal' | 'warnings'>;
}

export interface GoldenFile {
  note: string;
  charts: GoldenChart[];
  pairs: GoldenPair[];
}

function pickChart(h: CanonicalHoroscope): GoldenChart['expected'] {
  const { calculationId, calculationVersion, provider, rulesVersion, configuration, input, ascendant, rashi, nakshatra, nakshatraPada, planetaryPositions, mangalInput, calculationWarnings } = h;
  // tzdbVersion identifies the runtime's time-zone database, not the result; it is checked separately.
  return { calculationId, calculationVersion, provider, rulesVersion, configuration, input: { ...input, tzdbVersion: '(runtime)' }, ascendant, rashi, nakshatra, nakshatraPada, planetaryPositions, mangalInput, calculationWarnings };
}

function pickMatch(m: HoroscopeMatch): GoldenPair['expected'] {
  const { matchId, calculationVersion, rulesVersion, ashtakoota, mangal, warnings } = m;
  return { matchId, calculationVersion, rulesVersion, ashtakoota, mangal, warnings };
}

/** Computes the golden set with the engine as it is now. */
export function computeGolden(): GoldenFile {
  const engine = createDefaultEngine({ chartCacheTtlMs: 0 });
  const people = [
    ...generateCorpus(GOLDEN_SEED, GOLDEN_CHARTS).map((p) => ({ id: p.id, details: p.details })),
    ...EDGE_CASES.map((e) => ({ id: e.id, details: e.details })),
  ];
  const computed = people.map((p) => ({ id: p.id, details: p.details, chart: engine.calculateChart(p.details) }));
  const charts: GoldenChart[] = computed.map((c) => ({ id: c.id, input: c.details, expected: pickChart(c.chart) }));

  const pairs: GoldenPair[] = generatePairs(GOLDEN_SEED, GOLDEN_CHARTS, GOLDEN_PAIRS).map(([g, b]) => {
    const groom = computed[g] as (typeof computed)[number];
    const bride = computed[b] as (typeof computed)[number];
    return { groom: groom.id, bride: bride.id, expected: pickMatch(engine.calculateMatch(groom.chart, bride.chart)) };
  });
  // Edge cases paired with a corpus person so imprecise times reach the match path.
  for (const edge of computed.slice(GOLDEN_CHARTS)) {
    const other = computed[0] as (typeof computed)[number];
    pairs.push({ groom: other.id, bride: edge.id, expected: pickMatch(engine.calculateMatch(other.chart, edge.chart)) });
  }
  return {
    note: 'Synthetic birth data only. Regenerate with `npm run golden:update` ONLY when a change in results is intended and reviewed.',
    charts,
    pairs,
  };
}

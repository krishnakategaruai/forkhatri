import { createHash } from 'node:crypto';

import { GRAHA_ORDER } from './types.ts';
import type {
  CalculationWarning,
  CanonicalPosition,
  ExactChart,
  ExactPosition,
  GrahaName,
  NormalizedBirthInput,
} from './types.ts';
import { placementFromLongitude } from './zodiac.ts';

/* Turns one or more exact provider charts into Mangaly's canonical fields.
 *
 * An EXACT birth time gives one chart. APPROXIMATE and UNKNOWN times give a
 * chart at each sampled instant across the window; a field is reported only
 * when every sample agrees on it, and is null otherwise. Nothing is ever
 * filled in from a guessed time. */

export function stableHash(value: unknown): string {
  return createHash('sha256').update(canonicalJson(value)).digest('hex');
}

/** JSON with object keys sorted, so equal values always hash equally. */
export function canonicalJson(value: unknown): string {
  if (value === null || typeof value !== 'object') return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(',')}]`;
  const entries = Object.entries(value as Record<string, unknown>)
    .filter(([, v]) => v !== undefined)
    .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0));
  return `{${entries.map(([k, v]) => `${JSON.stringify(k)}:${canonicalJson(v)}`).join(',')}}`;
}

/** Instants to sample across a birth window: both ends and evenly between. */
export function sampleInstants(input: NormalizedBirthInput, samples: number): string[] {
  if (input.precision === 'EXACT') return [input.instantUtc as string];
  const start = Date.parse(input.windowStartUtc);
  const end = Date.parse(input.windowEndUtc);
  const out: string[] = [];
  for (let i = 0; i < samples; i++) {
    out.push(new Date(Math.round(start + ((end - start) * i) / (samples - 1))).toISOString());
  }
  return out;
}

/** Longitudes are rounded so a floating-point wobble in the last digit cannot change a stored result. */
function round(longitude: number): number {
  return Math.round(longitude * 1e6) / 1e6;
}

function agree(body: GrahaName | 'ASCENDANT', positions: ExactPosition[], exact: boolean): CanonicalPosition {
  const placements = positions.map((p) => placementFromLongitude(p.siderealLongitude));
  const first = placements[0];
  if (!first) throw new Error('no samples');
  const same = <K extends 'rashi' | 'nakshatra' | 'pada'>(key: K) => placements.every((p) => p[key] === first[key]);
  const rashiKnown = same('rashi');
  const nakshatraKnown = same('nakshatra');
  // A pada only means something inside a known nakshatra.
  const padaKnown = nakshatraKnown && same('pada');
  const retro = positions.every((p) => p.retrograde === positions[0]?.retrograde);
  return {
    body,
    siderealLongitude: exact ? round((positions[0] as ExactPosition).siderealLongitude) : null,
    rashi: rashiKnown ? first.rashi : null,
    nakshatra: nakshatraKnown ? first.nakshatra : null,
    pada: padaKnown ? first.pada : null,
    retrograde: retro ? (positions[0] as ExactPosition).retrograde : null,
  };
}

export interface CanonicalFields {
  moonSignHalf: 1 | 2 | null;
  ascendant: CanonicalPosition;
  planetaryPositions: CanonicalPosition[];
  warnings: CalculationWarning[];
}

export function canonicalizeSamples(input: NormalizedBirthInput, charts: ExactChart[]): CanonicalFields {
  const exact = input.precision === 'EXACT';
  const ascendant = agree('ASCENDANT', charts.map((c) => c.ascendant), exact);
  const planetaryPositions = GRAHA_ORDER.map((g) => agree(g, charts.map((c) => c.grahas[g]), exact));

  const warnings: CalculationWarning[] = [];
  if (input.precision === 'APPROXIMATE') {
    warnings.push({ code: 'BIRTH_TIME_APPROXIMATE', params: { uncertaintyMinutes: input.uncertaintyMinutes ?? 0 } });
  }
  if (input.precision === 'UNKNOWN') warnings.push({ code: 'BIRTH_TIME_UNKNOWN' });
  if (ascendant.rashi === null) warnings.push({ code: 'ASCENDANT_NOT_DETERMINABLE' });
  const moon = planetaryPositions[1] as CanonicalPosition;
  if (moon.rashi === null || moon.nakshatra === null) warnings.push({ code: 'MOON_NOT_DETERMINABLE' });
  const halves = charts.map((c) => (c.grahas.MOON.siderealLongitude % 30 < 15 ? 1 : 2));
  const moonSignHalf = moon.rashi !== null && halves.every((h) => h === halves[0]) ? (halves[0] as 1 | 2) : null;
  return { moonSignHalf, ascendant, planetaryPositions, warnings };
}

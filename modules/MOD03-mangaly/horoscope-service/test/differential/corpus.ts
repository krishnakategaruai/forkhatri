import { normalizeBirthDetails } from '../../src/domain/birthTime.ts';
import type { BirthDetails } from '../../src/domain/types.ts';

/* A synthetic birth-data corpus. No real person's data: dates and times come
 * from a seeded generator; places are public city coordinates. The same seed
 * always yields the same corpus, so fixtures and reports are reproducible. */

export function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Public coordinates of cities; weighted towards India, with others for time-zone coverage. */
export const PLACES: readonly { label: string; latitude: number; longitude: number; timezone: string }[] = [
  { label: 'Hyderabad', latitude: 17.385, longitude: 78.4867, timezone: 'Asia/Kolkata' },
  { label: 'Chennai', latitude: 13.0827, longitude: 80.2707, timezone: 'Asia/Kolkata' },
  { label: 'Bengaluru', latitude: 12.9716, longitude: 77.5946, timezone: 'Asia/Kolkata' },
  { label: 'Vijayawada', latitude: 16.5062, longitude: 80.648, timezone: 'Asia/Kolkata' },
  { label: 'Visakhapatnam', latitude: 17.6868, longitude: 83.2185, timezone: 'Asia/Kolkata' },
  { label: 'Mumbai', latitude: 19.076, longitude: 72.8777, timezone: 'Asia/Kolkata' },
  { label: 'Delhi', latitude: 28.6139, longitude: 77.209, timezone: 'Asia/Kolkata' },
  { label: 'Kolkata', latitude: 22.5726, longitude: 88.3639, timezone: 'Asia/Kolkata' },
  { label: 'Srinagar', latitude: 34.0837, longitude: 74.7973, timezone: 'Asia/Kolkata' },
  { label: 'Kathmandu', latitude: 27.7172, longitude: 85.324, timezone: 'Asia/Kathmandu' },
  { label: 'Dubai', latitude: 25.2048, longitude: 55.2708, timezone: 'Asia/Dubai' },
  { label: 'Singapore', latitude: 1.3521, longitude: 103.8198, timezone: 'Asia/Singapore' },
  { label: 'London', latitude: 51.5072, longitude: -0.1276, timezone: 'Europe/London' },
  { label: 'New York', latitude: 40.7128, longitude: -74.006, timezone: 'America/New_York' },
  { label: 'San Jose', latitude: 37.3382, longitude: -121.8863, timezone: 'America/Los_Angeles' },
  { label: 'Sydney', latitude: -33.8688, longitude: 151.2093, timezone: 'Australia/Sydney' },
  { label: 'Nairobi', latitude: -1.2921, longitude: 36.8219, timezone: 'Africa/Nairobi' },
];

export interface CorpusPerson {
  id: string;
  details: BirthDetails;
}

export function generateCorpus(seed: number, count: number, fromYear = 1940, toYear = 2008): CorpusPerson[] {
  const rnd = mulberry32(seed);
  const out: CorpusPerson[] = [];
  const pad = (n: number) => String(n).padStart(2, '0');
  while (out.length < count) {
    const year = fromYear + Math.floor(rnd() * (toYear - fromYear + 1));
    const month = 1 + Math.floor(rnd() * 12);
    const day = 1 + Math.floor(rnd() * new Date(Date.UTC(year, month, 0)).getUTCDate());
    const hour = Math.floor(rnd() * 24);
    const minute = Math.floor(rnd() * 60);
    // Two-thirds of people are born in India, like Mangaly's members.
    const place = (rnd() < 0.66 ? PLACES[Math.floor(rnd() * 9)] : PLACES[9 + Math.floor(rnd() * (PLACES.length - 9))]) as (typeof PLACES)[number];
    const details: BirthDetails = {
      birthDate: `${year}-${pad(month)}-${pad(day)}`,
      birthTime: `${pad(hour)}:${pad(minute)}`,
      birthTimePrecision: 'EXACT',
      birthLocation: place.label,
      latitude: place.latitude,
      longitude: place.longitude,
      timezone: place.timezone,
    };
    try {
      // A wall-clock time skipped or repeated by a clock change is not a usable exact time.
      normalizeBirthDetails(details);
    } catch {
      continue;
    }
    out.push({ id: `synthetic-${seed}-${out.length + 1}`, details });
  }
  return out;
}

/** Pairs drawn from a corpus: index pairs, groom first. */
export function generatePairs(seed: number, size: number, count: number): [number, number][] {
  const rnd = mulberry32(seed ^ 0x9e3779b9);
  const pairs: [number, number][] = [];
  while (pairs.length < count) {
    const a = Math.floor(rnd() * size);
    const b = Math.floor(rnd() * size);
    if (a !== b) pairs.push([a, b]);
  }
  return pairs;
}

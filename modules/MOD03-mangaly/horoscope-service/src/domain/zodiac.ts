import type { ZodiacPlacement } from './types.ts';

/* Pure zodiac arithmetic on sidereal longitudes. Mangaly derives rashi,
 * nakshatra and pada itself from the longitude, so a provider's labels are
 * only ever cross-checked, never trusted. */

export const RASHI_NAMES = [
  'MESHA', 'VRISHABHA', 'MITHUNA', 'KARKA', 'SIMHA', 'KANYA',
  'TULA', 'VRISHCHIKA', 'DHANU', 'MAKARA', 'KUMBHA', 'MEENA',
] as const;

export const NAKSHATRA_NAMES = [
  'ASHWINI', 'BHARANI', 'KRITTIKA', 'ROHINI', 'MRIGASHIRA', 'ARDRA', 'PUNARVASU', 'PUSHYA', 'ASHLESHA',
  'MAGHA', 'PURVA_PHALGUNI', 'UTTARA_PHALGUNI', 'HASTA', 'CHITRA', 'SWATI', 'VISHAKHA', 'ANURADHA', 'JYESHTHA',
  'MULA', 'PURVA_ASHADHA', 'UTTARA_ASHADHA', 'SHRAVANA', 'DHANISHTHA', 'SHATABHISHA',
  'PURVA_BHADRAPADA', 'UTTARA_BHADRAPADA', 'REVATI',
] as const;

export function normalizeLongitude(degrees: number): number {
  const wrapped = degrees % 360;
  return wrapped < 0 ? wrapped + 360 : wrapped;
}

/** Rashi 1..12, nakshatra 1..27, pada 1..4 of a sidereal longitude. */
export function placementFromLongitude(longitude: number): ZodiacPlacement {
  const lon = normalizeLongitude(longitude);
  // 360/27 = 13°20' per nakshatra; a pada is a quarter of that, 3°20' = 360/108.
  const padaIndex = Math.min(107, Math.floor((lon * 108) / 360));
  return {
    rashi: Math.min(11, Math.floor(lon / 30)) + 1,
    nakshatra: Math.floor(padaIndex / 4) + 1,
    pada: (padaIndex % 4) + 1,
  };
}

/** Distance in degrees from a longitude to the nearest rashi, nakshatra or pada boundary. */
export function distanceToBoundary(longitude: number): number {
  const lon = normalizeLongitude(longitude);
  const nearest = (width: number) => {
    const r = lon % width;
    return Math.min(r, width - r);
  };
  return Math.min(nearest(30), nearest(360 / 108));
}

/** Longitude at the middle of a rashi, used only to feed sign-based rules a stable point. */
export function rashiCentre(rashi: number): number {
  return (rashi - 1) * 30 + 15;
}

/** Longitude at the middle of a nakshatra. */
export function nakshatraCentre(nakshatra: number): number {
  return (nakshatra - 1) * (360 / 27) + 360 / 54;
}

/** Whole-sign house (1..12) of `rashi` counted from `fromRashi`. */
export function houseFrom(fromRashi: number, rashi: number): number {
  return ((rashi - fromRashi + 12) % 12) + 1;
}

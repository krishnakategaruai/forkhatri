/* INDEPENDENT REFERENCE — astronomy. Test-only; never used in production.
 *
 * Written from published algorithms, not from any provider's source, so it
 * can act as a differential oracle for the provider's chart positions:
 *   - Moon: Meeus, "Astronomical Algorithms" (2nd ed.) ch. 47, truncated to the
 *     largest longitude terms (expected error of the order of 0.01°).
 *   - Sun: Meeus ch. 25, low-accuracy method (~0.01°).
 *   - Mercury…Saturn: JPL "Keplerian Elements for Approximate Positions of the
 *     Major Planets" (E. M. Standish), table for 1800–2050 (arc-minute level;
 *     Jupiter/Saturn worse).
 *   - Mean lunar node (Rahu): Meeus ch. 47.
 *   - Ascendant: Meeus ch. 12 sidereal time with the standard ascendant formula.
 *
 * Deliberately low-precision: it cannot referee a position within its
 * tolerance of a sign/nakshatra/pada boundary, and the harness does not ask it
 * to. It shares one thing with the provider — the Lahiri ayanamsha anchor at
 * J2000 — which is therefore NOT independently validated here (see
 * docs/PROVIDER-LIMITATIONS.md). */

const DEG = Math.PI / 180;
const sin = (d: number) => Math.sin(d * DEG);
const cos = (d: number) => Math.cos(d * DEG);
const norm = (d: number) => ((d % 360) + 360) % 360;

/** Mean Lahiri ayanamsha anchor at J2000 (23°51'25.532"). Shared with the provider; see header. */
const LAHIRI_J2000_DEG = 23 + 51 / 60 + 25.532 / 3600;

export function julianDayUt(epochMs: number): number {
  return epochMs / 86_400_000 + 2440587.5;
}

/** ΔT = TT − UT in seconds, Espenak & Meeus polynomials (NASA eclipse site). */
export function deltaTSeconds(year: number): number {
  if (year < 1920) {
    const t = year - 1900;
    return -2.79 + 1.494119 * t - 0.0598939 * t ** 2 + 0.0061966 * t ** 3 - 0.000197 * t ** 4;
  }
  if (year < 1941) {
    const t = year - 1920;
    return 21.2 + 0.84493 * t - 0.0761 * t ** 2 + 0.0020936 * t ** 3;
  }
  if (year < 1961) {
    const t = year - 1950;
    return 29.07 + 0.407 * t - t ** 2 / 233 + t ** 3 / 2547;
  }
  if (year < 1986) {
    const t = year - 1975;
    return 45.45 + 1.067 * t - t ** 2 / 260 - t ** 3 / 718;
  }
  if (year < 2005) {
    const t = year - 2000;
    return 63.86 + 0.3345 * t - 0.060374 * t ** 2 + 0.0017275 * t ** 3 + 0.000651814 * t ** 4 + 0.00002373599 * t ** 5;
  }
  if (year < 2050) {
    const t = year - 2000;
    return 62.92 + 0.32217 * t + 0.005589 * t ** 2;
  }
  return -20 + 32 * ((year - 1820) / 100) ** 2 - 0.5628 * (2150 - year);
}

function centuriesTT(epochMs: number): number {
  const year = 1970 + epochMs / (365.25 * 86_400_000);
  const jdTT = julianDayUt(epochMs) + deltaTSeconds(year) / 86_400;
  return (jdTT - 2451545.0) / 36525;
}

/** Mean Lahiri ayanamsha of date: anchor plus IAU 2006 general precession in longitude. */
export function lahiriMean(T: number): number {
  return LAHIRI_J2000_DEG + (5028.796195 * T + 1.1054348 * T * T) / 3600;
}

// ---- Moon (Meeus 47) ------------------------------------------------------

// [D, M, M', F, coefficient in 1e-6 degrees]
const MOON_TERMS: [number, number, number, number, number][] = [
  [0, 0, 1, 0, 6288774], [2, 0, -1, 0, 1274027], [2, 0, 0, 0, 658314], [0, 0, 2, 0, 213618],
  [0, 1, 0, 0, -185116], [0, 0, 0, 2, -114332], [2, 0, -2, 0, 58793], [2, -1, -1, 0, 57066],
  [2, 0, 1, 0, 53322], [2, -1, 0, 0, 45758], [0, 1, -1, 0, -40923], [1, 0, 0, 0, -34720],
  [0, 1, 1, 0, -30383], [2, 0, 0, -2, 15327], [0, 0, 1, 2, -12528], [0, 0, 1, -2, 10980],
  [4, 0, -1, 0, 10675], [0, 0, 3, 0, 10034], [4, 0, -2, 0, 8548], [2, 1, -1, 0, -7888],
  [2, 1, 0, 0, -6766], [1, 0, -1, 0, -5163], [1, 1, 0, 0, 4987], [2, -1, 1, 0, 4036],
  [2, 0, 2, 0, 3994], [4, 0, 0, 0, 3861], [2, 0, -3, 0, 3665], [0, 1, -2, 0, -2689],
  [2, 0, -1, 2, -2602], [2, -1, -2, 0, 2390], [1, 0, 1, 0, -2348], [2, -2, 0, 0, 2236],
];

export function moonTropicalMean(T: number): number {
  const Lp = 218.3164477 + 481267.88123421 * T - 0.0015786 * T * T;
  const D = 297.8501921 + 445267.1114034 * T - 0.0018819 * T * T;
  const M = 357.5291092 + 35999.0502909 * T - 0.0001536 * T * T;
  const Mp = 134.9633964 + 477198.8675055 * T + 0.0087414 * T * T;
  const F = 93.272095 + 483202.0175233 * T - 0.0036539 * T * T;
  const E = 1 - 0.002516 * T - 0.0000074 * T * T;
  const A1 = 119.75 + 131.849 * T;
  const A2 = 53.09 + 479264.29 * T;
  let sum = 0;
  for (const [d, m, mp, f, c] of MOON_TERMS) {
    const e = Math.abs(m) === 1 ? E : Math.abs(m) === 2 ? E * E : 1;
    sum += c * e * sin(d * D + m * M + mp * Mp + f * F);
  }
  sum += 3958 * sin(A1) + 1962 * sin(Lp - F) + 318 * sin(A2);
  return norm(Lp + sum / 1e6);
}

// ---- Sun (Meeus 25, low accuracy) ------------------------------------------

export function sunTropicalMean(T: number): number {
  const L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T;
  const M = 357.52911 + 35999.05029 * T - 0.0001537 * T * T;
  const C =
    (1.914602 - 0.004817 * T - 0.000014 * T * T) * sin(M) +
    (0.019993 - 0.000101 * T) * sin(2 * M) +
    0.000289 * sin(3 * M);
  // Annual aberration (−20.5"), referred to the mean equinox of date.
  return norm(L0 + C - 0.00569);
}

// ---- planets (JPL approximate Keplerian elements, 1800–2050) ---------------

type Elements = [number, number, number, number, number, number];
const PLANETS: Record<string, { el: Elements; rate: Elements }> = {
  MERCURY: { el: [0.38709927, 0.20563593, 7.00497902, 252.2503235, 77.45779628, 48.33076593], rate: [0.00000037, 0.00001906, -0.00594749, 149472.67411175, 0.16047689, -0.12534081] },
  VENUS: { el: [0.72333566, 0.00677672, 3.39467605, 181.9790995, 131.60246718, 76.67984255], rate: [0.0000039, -0.00004107, -0.0007889, 58517.81538729, 0.00268329, -0.27769418] },
  EARTH: { el: [1.00000261, 0.01671123, -0.00001531, 100.46457166, 102.93768193, 0.0], rate: [0.00000562, -0.00004392, -0.01294668, 35999.37244981, 0.32327364, 0.0] },
  MARS: { el: [1.52371034, 0.0933941, 1.84969142, -4.55343205, -23.94362959, 49.55953891], rate: [0.00001847, 0.00007882, -0.00813131, 19140.30268499, 0.44441088, -0.29257343] },
  JUPITER: { el: [5.202887, 0.04838624, 1.30439695, 34.39644051, 14.72847983, 100.47390909], rate: [-0.00011607, -0.00013253, -0.00183714, 3034.74612775, 0.21252668, 0.20469106] },
  SATURN: { el: [9.53667594, 0.05386179, 2.48599187, 49.95424423, 92.59887831, 113.66242448], rate: [-0.0012506, -0.00050991, 0.00193609, 1222.49362201, -0.41897216, -0.28867794] },
};

function helio(name: string, T: number): [number, number, number] {
  const p = PLANETS[name] as { el: Elements; rate: Elements };
  const [a, e, I, L, w, O] = p.el.map((v, i) => v + (p.rate[i] as number) * T) as Elements;
  const argPeri = w - O;
  let M = norm(L - w);
  if (M > 180) M -= 360;
  let E = M + (e / DEG) * Math.sin(M * DEG);
  for (let i = 0; i < 10; i++) {
    const dM = M - (E - (e / DEG) * Math.sin(E * DEG));
    E += dM / (1 - e * Math.cos(E * DEG));
  }
  const xp = a * (Math.cos(E * DEG) - e);
  const yp = a * Math.sqrt(1 - e * e) * Math.sin(E * DEG);
  const cw = cos(argPeri), sw = sin(argPeri), cO = cos(O), sO = sin(O), cI = cos(I), sI = sin(I);
  return [
    (cw * cO - sw * sO * cI) * xp + (-sw * cO - cw * sO * cI) * yp,
    (cw * sO + sw * cO * cI) * xp + (-sw * sO + cw * cO * cI) * yp,
    sw * sI * xp + cw * sI * yp,
  ];
}

/** Geocentric ecliptic longitude referred to the J2000 equinox. */
function planetJ2000(name: string, T: number): number {
  const [x, y] = helio(name, T);
  const [xe, ye] = helio('EARTH', T);
  return norm(Math.atan2(y - ye, x - xe) / DEG);
}

// ---- ascendant ------------------------------------------------------------

function ascendantTropical(epochMs: number, T: number, latitude: number, longitude: number): number {
  const jd = julianDayUt(epochMs);
  const Tu = (jd - 2451545.0) / 36525;
  const gmst = 280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * Tu * Tu - (Tu * Tu * Tu) / 38710000;
  const ramc = norm(gmst + longitude);
  const eps = 23.4392911 - 0.0130042 * T;
  return norm(Math.atan2(cos(ramc), -(sin(ramc) * cos(eps) + Math.tan(latitude * DEG) * sin(eps))) / DEG);
}

// ---- public ----------------------------------------------------------------

export interface ReferenceChart {
  ASCENDANT: number;
  SUN: number;
  MOON: number;
  MERCURY: number;
  VENUS: number;
  MARS: number;
  JUPITER: number;
  SATURN: number;
  RAHU: number;
  KETU: number;
}

/** Sidereal (mean Lahiri) longitudes at an instant. */
export function referenceChart(epochMs: number, latitude: number, longitude: number): ReferenceChart {
  const T = centuriesTT(epochMs);
  const ayan = lahiriMean(T);
  // For bodies referred to J2000, precession to date and the ayanamsha's precession cancel.
  const fromJ2000 = (lon: number) => norm(lon - LAHIRI_J2000_DEG);
  const node = 125.0445479 - 1934.1362891 * T + 0.0020754 * T * T + (T * T * T) / 467441;
  const rahu = norm(node - ayan);
  return {
    ASCENDANT: norm(ascendantTropical(epochMs, T, latitude, longitude) - ayan),
    SUN: norm(sunTropicalMean(T) - ayan),
    MOON: norm(moonTropicalMean(T) - ayan),
    MERCURY: fromJ2000(planetJ2000('MERCURY', T)),
    VENUS: fromJ2000(planetJ2000('VENUS', T)),
    MARS: fromJ2000(planetJ2000('MARS', T)),
    JUPITER: fromJ2000(planetJ2000('JUPITER', T)),
    SATURN: fromJ2000(planetJ2000('SATURN', T)),
    RAHU: rahu,
    KETU: norm(rahu + 180),
  };
}

/** Agreement tolerances (degrees) between the provider and this reference, per body. */
export const TOLERANCE_DEG: Readonly<Record<keyof ReferenceChart, number>> = {
  ASCENDANT: 0.05,
  SUN: 0.02,
  MOON: 0.05,
  MERCURY: 0.1,
  VENUS: 0.1,
  MARS: 0.1,
  JUPITER: 0.3,
  SATURN: 0.3,
  RAHU: 0.02,
  KETU: 0.02,
};

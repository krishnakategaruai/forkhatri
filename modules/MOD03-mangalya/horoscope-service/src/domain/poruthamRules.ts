import { ESSENTIAL_PORUTHAMS } from './types.ts';
import type { PoruthamItem, PoruthamName } from './types.ts';

/* South Indian 10-Porutham matching (Mangaly rules v3).
 *
 * Every porutham depends only on the bride's and the groom's birth star
 * (nakshatra) and Moon sign (rashi). Counts are taken from the bride's star to
 * the groom's, inclusive, as the tradition does.
 *
 * Reference: ProKerala's Nakshatra Porutham calculator, the most-visited site
 * offering South Indian matching, read for every bride × groom star option
 * (54 × 54, stars spanning two signs split by pada) on 2026-09-27. The results
 * are in test/fixtures/prokerala-porutham.json and every one is replayed as a
 * test. Nine poruthams follow ProKerala exactly, including where it differs
 * from a common textbook form (noted below).
 *
 * Rajju is the exception. ProKerala's Rajju output contradicts itself — it
 * labels a star with a different Rajju group depending on the partner, and on
 * its detailed form calls "Nabhi | Nabhi" a Good match although the rule is
 * that the same group does not agree. Rajju is one of the two poruthams
 * families treat as essential, so Mangaly uses the classical definition every
 * Tamil and Kerala text gives: five groups by star; the same group does not
 * agree. The replay test records exactly which pairs differ from ProKerala. */

export interface StarMoon {
  rashi: number; // 1..12
  nakshatra: number; // 1..27
}

const at = <T>(xs: readonly T[], i: number): T => {
  const v = xs[i];
  if (v === undefined) throw new RangeError('table index');
  return v;
};

/** Stars counted from the bride's to the groom's, inclusive (1..27). */
const starCount = (bride: StarMoon, groom: StarMoon) => ((groom.nakshatra - bride.nakshatra + 27) % 27) + 1;

const GANA = ['DEVA', 'MANUSHYA', 'RAKSHASA'] as const;
const GANA_OF = [0, 1, 2, 1, 0, 1, 0, 0, 2, 2, 1, 1, 0, 2, 0, 2, 0, 2, 2, 1, 1, 0, 2, 2, 1, 1, 0];
/** Bride's gana (row) × groom's gana (column): agrees? (ProKerala.) */
const GANA_AGREES = [
  [true, false, false],
  [true, true, true],
  [false, false, true],
];

/* Yoni: ProKerala decides it by whether the bride's star is a "female" or
 * "male" star; the bride's being female agrees. Gender by star, 1-based. */
const YONI_FEMALE = new Set([3, 4, 5, 6, 7, 11, 13, 14, 17, 23, 24, 26, 27]);

// Rajju: the five groups, by star (classical).
const RAJJU = ['PADA', 'KATI', 'NABHI', 'KANTA', 'SIRO'] as const;
const RAJJU_OF = [0, 1, 2, 3, 4, 3, 2, 1, 0, 0, 1, 2, 3, 4, 3, 2, 1, 0, 0, 1, 2, 3, 4, 3, 2, 1, 0];

// Vedha: the twelve obstructing pairs (1-based). ProKerala does not count the
// Mrigashira–Chitra–Dhanishta group some texts add.
const VEDHA_PAIRS: readonly (readonly [number, number])[] = [
  [1, 18], [2, 17], [3, 16], [4, 15], [6, 22], [7, 21], [8, 20], [9, 19], [10, 27], [11, 26], [12, 25], [13, 24],
];

/** Rasi: for each bride sign, the groom signs that agree (ProKerala). */
const RASI_AGREES: Readonly<Record<number, readonly number[]>> = {
  1: [1, 7, 8, 9, 10, 11, 12],
  2: [1, 2, 7, 8, 9, 10, 11, 12],
  3: [1, 2, 3, 9, 10, 11, 12],
  4: [1, 2, 3, 4, 9, 10, 11, 12],
  5: [1, 2, 3, 4, 5, 11, 12],
  6: [1, 2, 3, 4, 5, 6, 11, 12],
  7: [1, 2, 3, 4, 5, 6, 7],
  8: [1, 2, 3, 4, 5, 6, 7, 8],
  9: [3, 4, 5, 6, 7, 8, 9],
  10: [3, 4, 5, 6, 7, 8, 9, 10],
  11: [5, 6, 7, 8, 9, 10, 11],
  12: [5, 6, 7, 8, 9, 10, 11, 12],
};

/** Vasya: for each bride sign, the groom signs that agree (ProKerala). */
const VASYA_AGREES: Readonly<Record<number, readonly number[]>> = {
  1: [5, 8, 10, 11],
  2: [4, 7],
  3: [6],
  4: [2, 8, 9],
  5: [1, 7],
  6: [3, 7, 12],
  7: [2, 5, 6, 10],
  8: [1, 4],
  9: [4, 12],
  10: [1, 7, 11, 12],
  11: [1, 10],
  12: [6, 9, 10],
};

const LORDS = ['MARS', 'VENUS', 'MERCURY', 'MOON', 'SUN', 'MERCURY', 'VENUS', 'MARS', 'JUPITER', 'SATURN', 'SATURN', 'JUPITER'];
/** Rasi Adhipathi: bride's lord → groom's lord pairs that do not agree (ProKerala). */
const LORDS_DISAGREE = new Set([
  'JUPITER>MARS', 'MARS>JUPITER', 'MARS>MOON', 'MARS>SATURN', 'MARS>SUN', 'MERCURY>SUN', 'MOON>MARS', 'MOON>SATURN',
  'MOON>SUN', 'MOON>VENUS', 'SATURN>MARS', 'SATURN>MOON', 'SATURN>SUN', 'SUN>MARS', 'SUN>MERCURY', 'SUN>MOON',
  'SUN>SATURN', 'SUN>VENUS', 'VENUS>MOON', 'VENUS>SUN',
]);

const RASHI_CODES = ['MESHA', 'VRISHABHA', 'MITHUNA', 'KARKA', 'SIMHA', 'KANYA', 'TULA', 'VRISHCHIKA', 'DHANU', 'MAKARA', 'KUMBHA', 'MEENA'];
const star = (n: number) => `STAR_${n}`;

export function scorePorutham(bride: StarMoon, groom: StarMoon): PoruthamItem[] {
  const n = starCount(bride, groom);
  const item = (porutham: PoruthamName, agrees: boolean, brideClass: string, groomClass: string): PoruthamItem => ({
    porutham,
    agrees,
    brideClass,
    groomClass,
    essential: ESSENTIAL_PORUTHAMS.includes(porutham),
    explanation: { code: `PORUTHAM.${porutham}.${agrees ? 'AGREES' : 'DOES_NOT_AGREE'}`, params: { starCount: n } },
  });

  const bg = at(GANA_OF, bride.nakshatra - 1);
  const gg = at(GANA_OF, groom.nakshatra - 1);
  const br = at(RAJJU_OF, bride.nakshatra - 1);
  const gr = at(RAJJU_OF, groom.nakshatra - 1);
  const bl = at(LORDS, bride.rashi - 1);
  const gl = at(LORDS, groom.rashi - 1);
  const gender = (s: number) => (YONI_FEMALE.has(s) ? 'FEMALE' : 'MALE');

  return [
    item('DINA', [0, 1, 2, 4, 6, 8].includes(n % 9), star(bride.nakshatra), star(groom.nakshatra)),
    item('GANA', at(at(GANA_AGREES, bg), gg), at(GANA, bg), at(GANA, gg)),
    item('MAHENDRA', [4, 7, 10, 13, 16, 19, 22, 25].includes(n), star(bride.nakshatra), star(groom.nakshatra)),
    item('STREE_DEERGHA', n >= 10, star(bride.nakshatra), star(groom.nakshatra)),
    item('YONI', YONI_FEMALE.has(bride.nakshatra), gender(bride.nakshatra), gender(groom.nakshatra)),
    item('VEDHA', !VEDHA_PAIRS.some(([a, b]) => (a === bride.nakshatra && b === groom.nakshatra) || (a === groom.nakshatra && b === bride.nakshatra)), star(bride.nakshatra), star(groom.nakshatra)),
    item('RAJJU', br !== gr, at(RAJJU, br), at(RAJJU, gr)),
    item('RASI', !!RASI_AGREES[bride.rashi]?.includes(groom.rashi), at(RASHI_CODES, bride.rashi - 1), at(RASHI_CODES, groom.rashi - 1)),
    item('RASI_ADHIPATHI', !LORDS_DISAGREE.has(`${bl}>${gl}`), bl, gl),
    item('VASYA', !!VASYA_AGREES[bride.rashi]?.includes(groom.rashi), at(RASHI_CODES, bride.rashi - 1), at(RASHI_CODES, groom.rashi - 1)),
  ];
}

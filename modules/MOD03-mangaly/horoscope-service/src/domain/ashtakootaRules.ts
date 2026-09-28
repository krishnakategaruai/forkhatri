import { KOOTA_MAX } from './types.ts';
import type { KootaName } from './types.ts';

/* Mangaly's own Ashtakoota (Guna Milan) rules — rules version 3.

 * Goal (owner, 2026-09-27): every customer gets the correct number, the one
 * they will see when they check. The reference is AstroSage, the kundli
 * service most Indian families use (70M+ app installs; it states that 80% of
 * online kundli matching runs on it). Its tables were read from its public
 * calculator (robots.txt allows automated access) on 2026-09-27: 205 synthetic
 * pairs covering every ordered Yoni animal pairing, every Vashya group pairing, and
 * the Gana, Varna, Maitri, Bhakoot and Nadi cases they touch. Those results
 * are kept in test/fixtures/astrosage-calibration.json and replayed as tests;
 * Mangaly equals AstroSage on every koota of every one.
 *
 * AstroSage's rules, as observed:
 *   - Vashya: Sagittarius 0–15° Manava, 15–30° Chatushpada; Capricorn 0–15°
 *     Chatushpada, 15–30° Jalachara. Manava groom with Keeta bride scores 0;
 *     Vanachara groom with Chatushpada bride 0.5 (both one-directional).
 *   - Gana: groom Rakshasa with bride Deva 1; groom Deva with bride Rakshasa 0;
 *     groom Manushya with bride Deva 5; groom Deva with bride Manushya 6.
 *   - Bhakoot: 2/12, 5/9 and 6/8 score 0 even when both signs share a lord.
 *   - Nadi: the same Nadi scores 0, with no same-sign exception.
 *   - Yoni: AstroSage's own 14×14 table (below), every one of the 196 cells
 *     read in both directions. Six pairs score differently depending on who is
 *     the groom: Rat/Deer, Rat/Lion, Cow/Tiger, Buffalo/Deer, Tiger/Lion,
 *     Deer/Lion.
 * Where Drik Panchang differs (a few Yoni cells, the Nadi same-sign exception,
 * Vanachara–Chatushpada Vashya) the differences are recorded in
 * test/fixtures/reference-site-checks.json and docs/PROVIDER-LIMITATIONS.md.
 *
 * Scores keep their half points; the total is exact, as AstroSage shows it. */

export const ASHTAKOOTA_RULES_ID = 'MANGALY_ASHTAKOOTA_V3_ASTROSAGE';

export interface RulesMoon {
  rashi: number; // 1..12
  nakshatra: number; // 1..27
  /** 1 = first 15° of the sign, 2 = last 15°; null when the birth time cannot settle it. */
  signHalf: 1 | 2 | null;
}

export interface RuleScore {
  koota: KootaName;
  score: number;
  maxScore: number;
  groomClass: string;
  brideClass: string;
  exception: { applied: boolean; code: string } | null;
  notes?: Record<string, string | boolean>;
}

// ---- tables -------------------------------------------------------------

// Varna by rashi: water signs Brahmin (0), fire Kshatriya (1), earth Vaishya (2), air Shudra (3).
const VARNA = [1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0];
const VARNA_NAMES = ['BRAHMIN', 'KSHATRIYA', 'VAISHYA', 'SHUDRA'];

const VASHYA_NAMES = ['CHATUSHPADA', 'MANAVA', 'JALACHARA', 'VANACHARA', 'KEETA'] as const;
// Groom row, bride column.
const VASHYA_TABLE = [
  [2, 1, 1, 0, 1],
  [1, 2, 0.5, 0, 0],
  [1, 0.5, 2, 1, 1],
  [0.5, 0, 1, 2, 0],
  [1, 1, 1, 0, 2],
];

/** Vashya group, or null when a split sign's half is unknown. */
export function vashyaGroup(rashi: number, half: 1 | 2 | null): number | null {
  switch (rashi) {
    case 1: case 2: return 0;
    case 3: case 6: case 7: case 11: return 1;
    case 4: case 12: return 2;
    case 5: return 3;
    case 8: return 4;
    case 9: return half === null ? null : half === 1 ? 1 : 0;
    case 10: return half === null ? null : half === 1 ? 0 : 2;
    default: throw new RangeError('rashi');
  }
}

/** Whether this sign's Vashya depends on which half the Moon is in. */
export function vashyaNeedsHalf(rashi: number): boolean {
  return rashi === 9 || rashi === 10;
}

const YONI_NAMES = [
  'HORSE', 'ELEPHANT', 'SHEEP', 'SERPENT', 'DOG', 'CAT', 'RAT',
  'COW', 'BUFFALO', 'TIGER', 'DEER', 'MONKEY', 'MONGOOSE', 'LION',
] as const;
const YONI_OF_NAKSHATRA = [0, 1, 2, 3, 3, 4, 5, 2, 5, 6, 6, 7, 8, 9, 8, 9, 10, 10, 4, 11, 12, 11, 13, 0, 13, 7, 1];
// Groom row, bride column, as read from AstroSage.
const YONI_TABLE = [
  [4, 2, 3, 2, 2, 3, 3, 3, 0, 1, 3, 2, 2, 1], // Horse
  [2, 4, 3, 2, 2, 3, 3, 3, 3, 1, 3, 2, 2, 0], // Elephant
  [3, 3, 4, 2, 2, 3, 3, 3, 3, 1, 3, 0, 2, 1], // Sheep
  [2, 2, 2, 4, 2, 1, 1, 2, 2, 2, 2, 1, 0, 2], // Serpent
  [2, 2, 2, 2, 4, 1, 2, 2, 2, 2, 0, 2, 2, 2], // Dog
  [3, 3, 3, 1, 1, 4, 0, 3, 3, 2, 3, 2, 2, 2], // Cat
  [3, 3, 3, 1, 2, 0, 4, 3, 3, 2, 2, 2, 1, 2], // Rat
  [3, 3, 3, 2, 2, 3, 3, 4, 3, 1, 3, 2, 2, 1], // Cow
  [0, 3, 3, 2, 2, 3, 3, 3, 4, 1, 3, 2, 2, 1], // Buffalo
  [1, 1, 1, 2, 2, 2, 2, 0, 1, 4, 1, 2, 2, 2], // Tiger
  [3, 3, 3, 2, 0, 3, 3, 3, 1, 1, 4, 2, 2, 1], // Deer
  [2, 2, 0, 1, 2, 2, 2, 2, 2, 2, 2, 4, 2, 2], // Monkey
  [2, 2, 2, 0, 2, 2, 1, 2, 2, 2, 2, 2, 4, 2], // Mongoose
  [1, 0, 1, 2, 2, 2, 1, 1, 1, 1, 3, 2, 2, 4], // Lion
];

const LORDS = ['MARS', 'VENUS', 'MERCURY', 'MOON', 'SUN', 'MERCURY', 'VENUS', 'MARS', 'JUPITER', 'SATURN', 'SATURN', 'JUPITER'];
// Natural friendships (Brihat Parashara Hora Shastra).
const FRIENDS: Record<string, string[]> = {
  SUN: ['MOON', 'MARS', 'JUPITER'], MOON: ['SUN', 'MERCURY'], MARS: ['SUN', 'MOON', 'JUPITER'],
  MERCURY: ['SUN', 'VENUS'], JUPITER: ['SUN', 'MOON', 'MARS'], VENUS: ['MERCURY', 'SATURN'], SATURN: ['MERCURY', 'VENUS'],
};
const ENEMIES: Record<string, string[]> = {
  SUN: ['VENUS', 'SATURN'], MOON: [], MARS: ['MERCURY'], MERCURY: ['MOON'],
  JUPITER: ['MERCURY', 'VENUS'], VENUS: ['SUN', 'MOON'], SATURN: ['SUN', 'MOON', 'MARS'],
};

const GANA_NAMES = ['DEVA', 'MANUSHYA', 'RAKSHASA'];
const GANA_OF_NAKSHATRA = [0, 1, 2, 1, 0, 1, 0, 0, 2, 2, 1, 1, 0, 2, 0, 2, 0, 2, 2, 1, 1, 0, 2, 2, 1, 1, 0];
// Groom row, bride column.
const GANA_TABLE = [
  [6, 6, 0],
  [5, 6, 0],
  [1, 0, 6],
];

const NADI_NAMES = ['ADI', 'MADHYA', 'ANTYA'];
const nadiOf = (nakshatra: number) => [0, 1, 2, 2, 1, 0][(nakshatra - 1) % 6] as number;

// ---- the eight kootas ---------------------------------------------------

function relation(a: string, b: string): 1 | 0 | -1 {
  if (a === b || FRIENDS[a]?.includes(b)) return 1;
  return ENEMIES[a]?.includes(b) ? -1 : 0;
}

const at = <T>(xs: readonly T[], i: number): T => {
  const v = xs[i];
  if (v === undefined) throw new RangeError('table index');
  return v;
};

/** Scores all eight kootas. Throws if a split sign's half is needed and unknown (caller checks first). */
export function scoreAshtakoota(groom: RulesMoon, bride: RulesMoon): RuleScore[] {
  const out: RuleScore[] = [];
  const push = (koota: KootaName, score: number, g: string, b: string, exception: RuleScore['exception'] = null, notes?: RuleScore['notes']) =>
    out.push({ koota, score, maxScore: KOOTA_MAX[koota], groomClass: g, brideClass: b, exception, ...(notes ? { notes } : {}) });

  // Varna: 1 when the groom's varna is the same as or higher than the bride's.
  const gv = at(VARNA, groom.rashi - 1);
  const bv = at(VARNA, bride.rashi - 1);
  push('VARNA', gv <= bv ? 1 : 0, at(VARNA_NAMES, gv), at(VARNA_NAMES, bv));

  // Vashya.
  const gw = vashyaGroup(groom.rashi, groom.signHalf);
  const bw = vashyaGroup(bride.rashi, bride.signHalf);
  if (gw === null || bw === null) throw new RangeError('vashya half unknown');
  push('VASHYA', at(at(VASHYA_TABLE, gw), bw), at(VASHYA_NAMES, gw), at(VASHYA_NAMES, bw));

  // Tara: count each way, inclusive; remainders 3, 5 and 7 (mod 9) are unfavourable.
  const count = (from: number, to: number) => ((to - from + 27) % 27) + 1;
  const good = (c: number) => ![3, 5, 7].includes(c % 9);
  const fromBride = good(count(bride.nakshatra, groom.nakshatra));
  const fromGroom = good(count(groom.nakshatra, bride.nakshatra));
  const cls = (ok: boolean) => (ok ? 'FAVOURABLE_COUNT' : 'UNFAVOURABLE_COUNT');
  push('TARA', fromBride && fromGroom ? 3 : fromBride || fromGroom ? 1.5 : 0, cls(fromBride), cls(fromGroom));

  // Yoni.
  const gy = at(YONI_OF_NAKSHATRA, groom.nakshatra - 1);
  const by = at(YONI_OF_NAKSHATRA, bride.nakshatra - 1);
  push('YONI', at(at(YONI_TABLE, gy), by), at(YONI_NAMES, gy), at(YONI_NAMES, by));

  // Graha Maitri: friendship of the two Moon-sign lords, each way.
  const gl = at(LORDS, groom.rashi - 1);
  const bl = at(LORDS, bride.rashi - 1);
  const pair = [relation(gl, bl), relation(bl, gl)].sort().join(',');
  const MAITRI: Record<string, number> = { '1,1': 5, '0,1': 4, '0,0': 3, '-1,1': 1, '-1,0': 0.5, '-1,-1': 0 };
  push('GRAHA_MAITRI', MAITRI[pair] as number, gl, bl);

  // Gana.
  const gg = at(GANA_OF_NAKSHATRA, groom.nakshatra - 1);
  const bg = at(GANA_OF_NAKSHATRA, bride.nakshatra - 1);
  push('GANA', at(at(GANA_TABLE, gg), bg), at(GANA_NAMES, gg), at(GANA_NAMES, bg));

  // Bhakoot: the bride's sign counted from the groom's.
  const pos = ((bride.rashi - groom.rashi + 12) % 12) + 1;
  const dosha = [2, 12, 5, 9, 6, 8].includes(pos);
  push('BHAKOOT', dosha ? 0 : 7, gl, bl, null, { position: String(pos), sameLord: dosha && gl === bl });

  // Nadi.
  const gn = nadiOf(groom.nakshatra);
  const bn = nadiOf(bride.nakshatra);
  // No same-sign exception is scored (AstroSage); when that situation occurs
  // it is noted, because some traditions (and Drik Panchang) would keep 8.
  const same = gn === bn;
  const sameSignOtherStar = same && groom.rashi === bride.rashi && groom.nakshatra !== bride.nakshatra;
  push('NADI', same ? 0 : 8, at(NADI_NAMES, gn), at(NADI_NAMES, bn), null, { sameSignOtherStar });

  return out;
}

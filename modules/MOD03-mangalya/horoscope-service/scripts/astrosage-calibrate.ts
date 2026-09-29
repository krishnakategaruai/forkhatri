import { existsSync, readFileSync, writeFileSync } from 'node:fs';

import { PrisriJyotishProvider } from '../src/provider/prisri/PrisriJyotishProvider.ts';
import { placementFromLongitude } from '../src/domain/zodiac.ts';
import { astrosage } from './astrosage-check.ts';

/* Calibration run against AstroSage (robots.txt: Allow all). One synthetic
 * Hyderabad birth per Yoni animal (Moon mid-nakshatra), every animal pairing
 * plus some reversed pairs; results appended to a fixture as they arrive so
 * the run can resume. Gentle pace: one pair every ~4 s. */

const OUT = new URL('../test/fixtures/astrosage-calibration.json', import.meta.url);
const YONI_OF_NAKSHATRA = [0, 1, 2, 3, 3, 4, 5, 2, 5, 6, 6, 7, 8, 9, 8, 9, 10, 10, 4, 11, 12, 11, 13, 0, 13, 7, 1];
const ANIMALS = ['HORSE', 'ELEPHANT', 'SHEEP', 'SERPENT', 'DOG', 'CAT', 'RAT', 'COW', 'BUFFALO', 'TIGER', 'DEER', 'MONKEY', 'MONGOOSE', 'LION'];

const p = new PrisriJyotishProvider();
const cfg = { zodiacSystem: 'SIDEREAL', ayanamsha: 'LAHIRI', houseSystem: 'WHOLE_SIGN' } as const;

/** A 1996 Hyderabad birth (IST, whole hour) whose Moon is within 2° of the middle of `nakshatra`. */
function birthFor(nakshatra: number): { date: string; time: string; moon: number } {
  const target = (nakshatra - 1) * (360 / 27) + 360 / 54;
  for (let ms = Date.UTC(1996, 0, 1); ms < Date.UTC(1997, 0, 1); ms += 3_600_000) {
    const lon = p.calculateChart({ instantUtc: new Date(ms).toISOString(), latitude: 17.3842, longitude: 78.4564, elevationMeters: 0 }, cfg).grahas.MOON.siderealLongitude;
    if (Math.abs(lon - target) < 2 && placementFromLongitude(lon).nakshatra === nakshatra) {
      const ist = new Date(ms + 5.5 * 3_600_000).toISOString();
      return { date: ist.slice(0, 10), time: ist.slice(11, 16), moon: +lon.toFixed(3) };
    }
  }
  throw new Error(`no birth for nakshatra ${nakshatra}`);
}

const rep = ANIMALS.map((_, a) => YONI_OF_NAKSHATRA.indexOf(a) + 1);
const births = Object.fromEntries(rep.map((n, a) => [ANIMALS[a]!, { nakshatra: n, ...birthFor(n) }]));

const pairs: [string, string][] = [];
for (let i = 0; i < ANIMALS.length; i++) for (let j = i; j < ANIMALS.length; j++) pairs.push([ANIMALS[i]!, ANIMALS[j]!]);
// Every reversed pairing too: AstroSage's Yoni table is not symmetric everywhere.
for (let i = 0; i < ANIMALS.length; i++) for (let j = 0; j < i; j++) pairs.push([ANIMALS[i]!, ANIMALS[j]!]);

type Row = { groom: string; bride: string; result: Awaited<ReturnType<typeof astrosage>> };
const done: { births: typeof births; rows: Row[] } = existsSync(OUT) ? JSON.parse(readFileSync(OUT, 'utf8')) : { births, rows: [] };
done.births = births;
const have = new Set(done.rows.map((r) => `${r.groom}|${r.bride}`));

for (const [g, b] of pairs) {
  if (have.has(`${g}|${b}`)) continue;
  const G = births[g]!, B = births[b]!;
  let result;
  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      result = await astrosage([G.date, G.time], [B.date, B.time]);
      if (Object.keys(result.kootas).length === 8) break;
    } catch (e) {
      console.error(`${g}×${b} attempt ${attempt}: ${(e as Error).message}`);
    }
    await new Promise((r) => setTimeout(r, 8000));
  }
  if (!result || Object.keys(result.kootas).length !== 8) {
    console.error(`${g}×${b}: no result, skipped`);
    continue;
  }
  done.rows.push({ groom: g, bride: b, result });
  writeFileSync(OUT, `${JSON.stringify(done, null, 1)}\n`);
  console.log(`${done.rows.length}/${pairs.length} ${g}×${b} yoni=${result.kootas.Yoni?.obt} total=${result.total}`);
  await new Promise((r) => setTimeout(r, 4000));
}
console.log('complete');

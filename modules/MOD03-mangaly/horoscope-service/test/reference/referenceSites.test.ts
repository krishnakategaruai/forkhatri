import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { describe, it } from 'node:test';

import { createDefaultEngine } from '../../src/index.ts';
import type { BirthDetails, KootaName } from '../../src/domain/types.ts';

/* Replays Guna Milan results read from the public calculators through the
 * whole engine, from the birth details (Hyderabad, IST, Lahiri).
 *
 *   AstroSage (the reference Mangaly follows): 3 hand checks + 117 calibration
 *   pairs + 5 Vashya checks — every koota of every pair must be equal.
 *
 *   Drik Panchang (11 hand checks): equal except the documented differences
 *   between Drik and AstroSage; the test fails if that set changes. */

const KEY: Record<string, KootaName> = {
  Varna: 'VARNA', Vasya: 'VASHYA', Tara: 'TARA', Yoni: 'YONI', Maitri: 'GRAHA_MAITRI', Gana: 'GANA', Bhakoot: 'BHAKOOT', Nadi: 'NADI',
};

const hand = JSON.parse(readFileSync(new URL('../fixtures/reference-site-checks.json', import.meta.url), 'utf8')) as {
  births: Record<string, { date: string; time: string; moon: { drik: number } }>;
  checks: { site: string; groom: string; bride: string; obt: Record<KootaName, number>; totalShown: number }[];
};
const calib = JSON.parse(readFileSync(new URL('../fixtures/astrosage-calibration.json', import.meta.url), 'utf8')) as {
  births: Record<string, { date: string; time: string }>;
  rows: { groom: string; bride: string; result: { kootas: Record<string, { obt: number }>; total: number } }[];
  extra: { label: string; groom: { date: string; time: string }; bride: { date: string; time: string }; result: { kootas: Record<string, { obt: number }>; total: number } }[];
};

/** Where Drik Panchang's score differs from AstroSage's (and so from Mangaly's). */
const KNOWN_DRIK_DIFFERENCES = [
  'A×B YONI mangaly 2 drik 1',
  'H×D YONI mangaly 3 drik 2',
  'A×F YONI mangaly 3 drik 3',
  'F×G YONI mangaly 3 drik 2',
  'B×A YONI mangaly 2 drik 1',
  'F×A VASHYA mangaly 0.5 drik 0',
  'K×B YONI mangaly 2 drik 1',
  'K×B NADI mangaly 0 drik 8',
].filter((d) => !d.includes('mangaly 3 drik 3'));

const engine = createDefaultEngine({ chartCacheTtlMs: 0 });
const chart = (date: string, time: string) => {
  const details: BirthDetails = {
    birthDate: date,
    birthTime: time,
    birthTimePrecision: 'EXACT',
    birthLocation: 'Hyderabad',
    latitude: 17.3842,
    longitude: 78.4564,
    timezone: 'Asia/Kolkata',
  };
  return engine.calculateChart(details);
};
const scores = (g: { date: string; time: string }, b: { date: string; time: string }) => {
  const m = engine.calculateMatch(chart(g.date, g.time), chart(b.date, b.time));
  assert.equal(m.ashtakoota.status, 'CALCULATED');
  return { kootas: Object.fromEntries(m.ashtakoota.kootas.map((k) => [k.koota, k.score])) as Record<KootaName, number>, total: m.ashtakoota.totalScore };
};

describe('AstroSage: Mangaly equals it on every koota of every pair', () => {
  it('Moon longitudes agree with Drik Panchang within 0.02°', () => {
    for (const [key, b] of Object.entries(hand.births)) {
      const lon = chart(b.date, b.time).moon.siderealLongitude as number;
      assert.ok(Math.abs(lon - b.moon.drik) < 0.02, `${key}: ${lon} vs ${b.moon.drik}`);
    }
  });

  for (const c of hand.checks.filter((x) => x.site === 'astrosage')) {
    it(`hand check ${c.groom}×${c.bride}`, () => {
      const s = scores(hand.births[c.groom]!, hand.births[c.bride]!);
      assert.deepEqual(s.kootas, c.obt);
      assert.equal(s.total, c.totalShown);
    });
  }

  it(`${calib.rows.length} calibration pairs (every Yoni animal pairing)`, () => {
    const wrong: string[] = [];
    for (const r of calib.rows) {
      const s = scores(calib.births[r.groom]!, calib.births[r.bride]!);
      for (const [name, v] of Object.entries(r.result.kootas)) {
        const code = KEY[name] as KootaName;
        if (s.kootas[code] !== v.obt) wrong.push(`${r.groom}×${r.bride} ${code} mangaly ${s.kootas[code]} astrosage ${v.obt}`);
      }
      if (s.total !== r.result.total) wrong.push(`${r.groom}×${r.bride} total ${s.total} vs ${r.result.total}`);
    }
    assert.deepEqual(wrong, []);
  });

  for (const e of calib.extra) {
    it(`Vashya check ${e.label}`, () => {
      const s = scores(e.groom, e.bride);
      for (const [name, v] of Object.entries(e.result.kootas)) assert.equal(s.kootas[KEY[name] as KootaName], v.obt, name);
    });
  }
});

describe('Drik Panchang: differs only where documented', () => {
  it('every Drik check equals Mangaly except the known Drik/AstroSage differences', () => {
    const diffs: string[] = [];
    for (const c of hand.checks.filter((x) => x.site === 'drikpanchang')) {
      const s = scores(hand.births[c.groom]!, hand.births[c.bride]!);
      for (const k of Object.keys(c.obt) as KootaName[]) {
        if (s.kootas[k] !== c.obt[k]) diffs.push(`${c.groom}×${c.bride} ${k} mangaly ${s.kootas[k]} drik ${c.obt[k]}`);
      }
    }
    assert.deepEqual(diffs.sort(), [...KNOWN_DRIK_DIFFERENCES].sort());
  });
});

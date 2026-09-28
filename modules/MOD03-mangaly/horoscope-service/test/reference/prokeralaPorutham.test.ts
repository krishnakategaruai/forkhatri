import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { describe, it } from 'node:test';

import { scorePorutham } from '../../src/domain/poruthamRules.ts';
import type { PoruthamName } from '../../src/domain/types.ts';

/* Replays ProKerala's Nakshatra Porutham result for every bride star × groom
 * star option (54 × 54 = 2,916 pairs; test/fixtures/prokerala-porutham.json).
 *
 * Nine poruthams must equal ProKerala on every pair. Rajju follows the
 * classical definition instead (see domain/poruthamRules.ts), so for Rajju the
 * test checks that every difference is exactly one ProKerala gets wrong by that
 * definition, and that the count of differences does not drift. */

type Row = { girl: string; boy: string; poruthams: { name: string; points: number }[] };
const f = JSON.parse(readFileSync(new URL('../fixtures/prokerala-porutham.json', import.meta.url), 'utf8')) as { rows: Row[] };

const NAME: Record<string, PoruthamName> = {
  'Dina Porutham': 'DINA', 'Gana Porutham': 'GANA', 'Mahendra Porutham': 'MAHENDRA', 'Stree Deergha Porutham': 'STREE_DEERGHA',
  'Yoni Porutham': 'YONI', 'Veda Porutham': 'VEDHA', 'Rajju Porutham': 'RAJJU', 'Rasi Porutham': 'RASI',
  'Rasiyathipathi Porutham': 'RASI_ADHIPATHI', 'Vasya Porutham': 'VASYA',
};

/** ProKerala option "k" or "k-p" (0-based star, 0-based pada) → star and the sign that pada is in. */
const moon = (v: string) => {
  const [k, p] = v.split('-').map(Number) as [number, number | undefined];
  const lon = (k * 360) / 27 + ((p ?? 0) + 0.5) * (360 / 108);
  return { nakshatra: k + 1, rashi: Math.floor(lon / 30) + 1 };
};

describe('Porutham: ProKerala, every bride star × groom star', () => {
  it('covers all 2,916 options', () => {
    assert.equal(new Set(f.rows.map((r) => `${r.girl}|${r.boy}`)).size, 2916);
  });

  it('nine poruthams equal ProKerala on every pair', () => {
    const wrong: string[] = [];
    for (const r of f.rows) {
      const ours = Object.fromEntries(scorePorutham(moon(r.girl), moon(r.boy)).map((i) => [i.porutham, i.agrees]));
      for (const p of r.poruthams) {
        const key = NAME[p.name];
        if (!key || key === 'RAJJU') continue;
        if (ours[key] !== (p.points > 0)) wrong.push(`${r.girl}×${r.boy} ${key}: mangaly ${ours[key]} prokerala ${p.points}`);
      }
    }
    assert.deepEqual(wrong.slice(0, 10), []);
  });

  it('Rajju is classical: the same group never agrees, different groups always do', () => {
    const GROUP = [0, 1, 2, 3, 4, 3, 2, 1, 0, 0, 1, 2, 3, 4, 3, 2, 1, 0, 0, 1, 2, 3, 4, 3, 2, 1, 0];
    let differ = 0;
    for (const r of f.rows) {
      const b = moon(r.girl), g = moon(r.boy);
      const rajju = scorePorutham(b, g).find((i) => i.porutham === 'RAJJU');
      assert.equal(rajju?.agrees, GROUP[b.nakshatra - 1] !== GROUP[g.nakshatra - 1]);
      const pk = (r.poruthams.find((p) => p.name === 'Rajju Porutham')?.points ?? 0) > 0;
      if (pk !== rajju?.agrees) differ++;
    }
    // ProKerala's Rajju (self-contradictory, see the rules file) differs on 792 pairs.
    assert.equal(differ, 792);
  });
});

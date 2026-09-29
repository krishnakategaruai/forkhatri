import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { describe, it } from 'node:test';

import { MANGAL_RULESET_ASTROSAGE_V1 } from '../../src/domain/config.ts';
import { evaluateMangal } from '../../src/domain/mangalRules.ts';
import type { MangalRuleset } from '../../src/domain/types.ts';
import { createDefaultEngine } from '../../src/index.ts';

/* Replays AstroSage's Mangal Dosha level for 40 synthetic people
 * (test/fixtures/astrosage-mangal.json) through the engine, from the birth
 * details: none / low / high must match exactly. */

const f = JSON.parse(readFileSync(new URL('../fixtures/astrosage-mangal.json', import.meta.url), 'utf8')) as {
  rows: { person: { date: string; time: string }; astro: string }[];
};
const engine = createDefaultEngine({ chartCacheTtlMs: 0 });

describe('Mangal Dosha: equal to AstroSage for every observed person', () => {
  it(`${f.rows.length} people`, () => {
    assert.ok(f.rows.length >= 40);
    const wrong: string[] = [];
    for (const r of f.rows) {
      const chart = engine.calculateChart({
        birthDate: r.person.date,
        birthTime: r.person.time,
        birthTimePrecision: 'EXACT',
        birthLocation: 'Hyderabad',
        latitude: 17.3842,
        longitude: 78.4564,
        timezone: 'Asia/Kolkata',
      });
      assert.ok(chart.mangalInput);
      const m = evaluateMangal(chart.mangalInput, MANGAL_RULESET_ASTROSAGE_V1 as MangalRuleset);
      const ours = m.status === 'PRESENT' ? `${m.level === 'HIGH' ? 'High' : 'Low'} Mangal Dosha` : 'No Mangal Dosha';
      if (ours !== r.astro) wrong.push(`${r.person.date} ${r.person.time}: mangaly "${ours}" astrosage "${r.astro}"`);
    }
    assert.deepEqual(wrong, []);
  });
});

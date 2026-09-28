import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { describe, it } from 'node:test';

import { computeGolden } from './golden.ts';
import type { GoldenFile } from './golden.ts';

/* Recomputes every golden chart and pair and compares with the committed
 * fixtures. A difference means results changed — after a library upgrade,
 * rule change or pipeline change — and must be reviewed, never silently
 * accepted. */

const committed = JSON.parse(readFileSync(new URL('./fixtures.json', import.meta.url), 'utf8')) as GoldenFile;
const current = computeGolden();

describe('golden fixtures', () => {
  it('cover at least 50 charts and 50 pairs', () => {
    assert.ok(committed.charts.length >= 50);
    assert.ok(committed.pairs.length >= 50);
  });

  for (const [i, expected] of committed.charts.entries()) {
    it(`chart ${expected.id}`, () => {
      assert.deepEqual(current.charts[i]?.input, expected.input);
      assert.deepEqual(current.charts[i]?.expected, expected.expected);
    });
  }

  for (const [i, expected] of committed.pairs.entries()) {
    it(`pair ${expected.groom} × ${expected.bride}`, () => {
      assert.deepEqual(current.pairs[i], expected);
    });
  }
});

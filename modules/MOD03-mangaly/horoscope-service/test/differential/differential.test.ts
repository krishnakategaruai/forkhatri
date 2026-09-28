import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import { runDifferential } from './harness.ts';

/* Fails on any mismatch without a documented cause, and on any astronomical
 * disagreement beyond the reference's tolerance. Known rule-definition
 * differences are allowed but counted; docs/differential-report.json has
 * every one with its inputs and outputs (npm run differential:report). */

const report = runDifferential();

describe('differential: provider vs independent references', () => {
  it('compares at least 200 charts and 200 pairs, all 1,296 Moon-placement pairs and all 20,736 Mangal inputs', () => {
    assert.ok(report.charts.compared >= 200);
    assert.ok(report.pairs.compared >= 200);
    assert.equal(report.exhaustivePlacements.pairs, 1296);
    assert.equal(report.exhaustiveMangal.inputs, 20736);
  });

  it('positions agree with independent astronomy within tolerance', () => {
    assert.deepEqual(report.mismatches.filter((m) => m.category === 'ASTRONOMICAL'), []);
  });

  it('no unexplained mismatch (placements, kootas, exceptions, Mangal)', () => {
    const unexplained = report.mismatches.filter((m) => m.category === 'UNEXPLAINED');
    assert.deepEqual(unexplained.slice(0, 5), []);
  });

  it('every provider-vs-Mangaly-rules difference has one of the documented causes', () => {
    const causes = new Set(report.mismatches.filter((m) => m.area.includes('.score')).map((m) => m.cause.split(':')[0]));
    for (const c of causes) {
      assert.ok(
        ['YONI_TABLE', 'GANA_RAKSHASA_GROOM_DEVA_BRIDE', 'BHAKOOT_SAME_LORD', 'VASHYA_HALF_SIGN', 'VASHYA_CHATUSHPADA_VANACHARA', 'VASHYA_MANAVA_KEETA', 'NADI_SAME_SIGN'].includes(c as string),
        `undocumented cause ${c}`,
      );
    }
  });

  it('Varna, Tara and Graha Maitri agree with Mangaly rules on every placement pair', () => {
    const areas = new Set(report.mismatches.filter((m) => m.area.startsWith('placement.')).map((m) => m.area.split('.')[1]));
    for (const same of ['VARNA', 'TARA', 'GRAHA_MAITRI']) assert.ok(!areas.has(same), same);
  });
});

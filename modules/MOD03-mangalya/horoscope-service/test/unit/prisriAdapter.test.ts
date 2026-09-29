import assert from 'node:assert/strict';
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { describe, it } from 'node:test';
import { fileURLToPath } from 'node:url';

import { MANGAL_RULESET_INCLUSIVE_V1, defaultMatchingConfiguration } from '../../src/domain/config.ts';
import type { MangalRuleset } from '../../src/domain/types.ts';
import { HoroscopeError } from '../../src/domain/errors.ts';
import { KOOTA_ORDER } from '../../src/domain/types.ts';
import { PrisriJyotishProvider } from '../../src/provider/prisri/PrisriJyotishProvider.ts';

const provider = new PrisriJyotishProvider();
// The library's own Mangal rule is the inclusive one; the adapter cross-checks against it.
const cfg = { ...defaultMatchingConfiguration('A'), mangalRuleset: MANGAL_RULESET_INCLUSIVE_V1 as MangalRuleset };
const config = { zodiacSystem: 'SIDEREAL', ayanamsha: 'LAHIRI', houseSystem: 'WHOLE_SIGN' } as const;

describe('Prisri adapter', () => {
  it('declares itself and its license', () => {
    const d = provider.describe();
    assert.equal(d.name, 'prisri-jyotish');
    assert.equal(d.version, '1.1.12');
    assert.equal(d.license, 'ISC');
  });

  it('returns Mangaly types only: longitudes and flags, no library objects', () => {
    const c = provider.calculateChart({ instantUtc: '2000-01-01T06:30:00.000Z', latitude: 19.076, longitude: 72.8777, elevationMeters: 0 }, config);
    assert.deepEqual(Object.keys(c).sort(), ['ascendant', 'grahas']);
    assert.deepEqual(Object.keys(c.grahas).sort(), ['JUPITER', 'KETU', 'MARS', 'MERCURY', 'MOON', 'RAHU', 'SATURN', 'SUN', 'VENUS']);
    for (const p of [c.ascendant, ...Object.values(c.grahas)]) {
      assert.deepEqual(Object.keys(p).sort(), ['retrograde', 'siderealLongitude']);
      assert.ok(p.siderealLongitude >= 0 && p.siderealLongitude < 360);
    }
    // Rahu and Ketu are opposite.
    const d = Math.abs(c.grahas.RAHU.siderealLongitude - c.grahas.KETU.siderealLongitude);
    assert.ok(Math.abs(d - 180) < 1e-6);
  });

  it('refuses a configuration it has not been told how to honour', () => {
    assert.throws(
      () => provider.calculateChart({ instantUtc: '2000-01-01T00:00:00Z', latitude: 0, longitude: 0, elevationMeters: 0 }, { ...config, houseSystem: 'PLACIDUS' as 'WHOLE_SIGN' }),
      (e: unknown) => e instanceof HoroscopeError && e.code === 'UNSUPPORTED_CONFIGURATION',
    );
  });

  it('returns all eight kootas in order, with class codes and no verdict or total', () => {
    const k = provider.calculateAshtakoota({ rashi: 1, nakshatra: 1 }, { rashi: 8, nakshatra: 17 }, cfg);
    assert.deepEqual(k.map((x) => x.koota), [...KOOTA_ORDER]);
    for (const x of k) {
      assert.match(x.groomClass, /^[A-Z_]+$/);
      assert.match(x.brideClass, /^[A-Z_]+$/);
    }
    assert.ok(!('verdict' in (k as unknown as Record<string, unknown>)));
  });

  it('reads the Bhakoot same-lord exception (Aries–Scorpio, both Mars, 6/8)', () => {
    const k = provider.calculateAshtakoota({ rashi: 1, nakshatra: 1 }, { rashi: 8, nakshatra: 17 }, cfg);
    const bhakoot = k.find((x) => x.koota === 'BHAKOOT');
    assert.deepEqual(bhakoot?.exception, { applied: true, code: 'BHAKOOT_SAME_RASHI_LORD' });
    assert.equal(bhakoot?.score, 7);
  });

  it('reads the Nadi same-rashi, different-nakshatra exception', () => {
    // Krittika (3, Antya) and Ashlesha (9, Antya) are both Antya; Krittika pada 2+ is Vrishabha, Ashlesha is Karka: no exception.
    const none = provider.calculateAshtakoota({ rashi: 2, nakshatra: 3 }, { rashi: 4, nakshatra: 9 }, cfg).find((x) => x.koota === 'NADI');
    assert.equal(none?.score, 0);
    assert.deepEqual(none?.exception, { applied: false, code: 'NADI_SAME_RASHI_DIFFERENT_NAKSHATRA' });
    // Krittika (Antya) and Rohini (Antya) both in Vrishabha: same rashi, different nakshatra → exception.
    const applied = provider.calculateAshtakoota({ rashi: 2, nakshatra: 3 }, { rashi: 2, nakshatra: 4 }, cfg).find((x) => x.koota === 'NADI');
    assert.equal(applied?.score, 8);
    assert.deepEqual(applied?.exception, { applied: true, code: 'NADI_SAME_RASHI_DIFFERENT_NAKSHATRA' });
  });

  it('rejects an impossible Moon placement (nakshatra outside the rashi)', () => {
    assert.throws(() => provider.calculateAshtakoota({ rashi: 1, nakshatra: 20 }, { rashi: 1, nakshatra: 1 }, cfg), (e: unknown) => e instanceof HoroscopeError && e.code === 'INVALID_INPUT');
  });

  it('Mangal from the library must agree with the declared rule set on every sign combination', () => {
    // 12^4 combinations; any disagreement throws PROVIDER_INCONSISTENT.
    let present = 0;
    for (let l = 1; l <= 12; l++)
      for (let m = 1; m <= 12; m++)
        for (let v = 1; v <= 12; v++)
          for (let ma = 1; ma <= 12; ma++)
            if (provider.calculateMangalDosha({ lagnaRashi: l, moonRashi: m, venusRashi: v, marsRashi: ma }, cfg).status === 'PRESENT') present++;
    assert.ok(present > 0);
  });
});

describe('dependency boundary', () => {
  it('only the Prisri adapter imports @prisri/jyotish', () => {
    const root = fileURLToPath(new URL('../../src', import.meta.url));
    const offenders: string[] = [];
    const walk = (dir: string) => {
      for (const name of readdirSync(dir)) {
        const p = join(dir, name);
        if (statSync(p).isDirectory()) walk(p);
        else if (p.endsWith('.ts') && readFileSync(p, 'utf8').includes('@prisri/jyotish') && !p.includes(join('provider', 'prisri'))) offenders.push(p);
      }
    };
    walk(root);
    assert.deepEqual(offenders, []);
  });

  it('domain code does not import the provider implementation', () => {
    const dir = fileURLToPath(new URL('../../src/domain', import.meta.url));
    for (const name of readdirSync(dir)) {
      assert.ok(!readFileSync(join(dir, name), 'utf8').includes('provider/prisri'), name);
    }
  });
});

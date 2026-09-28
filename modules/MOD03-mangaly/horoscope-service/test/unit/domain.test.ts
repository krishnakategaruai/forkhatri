import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import { MANGAL_RULESET_INCLUSIVE_V1 } from '../../src/domain/config.ts';
import { canonicalJson, canonicalizeSamples, sampleInstants } from '../../src/domain/canonical.ts';
import { evaluateMangal } from '../../src/domain/mangalRules.ts';
import { GRAHA_ORDER } from '../../src/domain/types.ts';
import type { ExactChart, GrahaName, MangalRuleset, NormalizedBirthInput } from '../../src/domain/types.ts';
import { distanceToBoundary, houseFrom, placementFromLongitude } from '../../src/domain/zodiac.ts';

const rules = MANGAL_RULESET_INCLUSIVE_V1 as MangalRuleset;

describe('zodiac arithmetic', () => {
  it('0° is Mesha, Ashwini pada 1', () => {
    assert.deepEqual(placementFromLongitude(0), { rashi: 1, nakshatra: 1, pada: 1 });
  });
  it('359.999° is Meena, Revati pada 4', () => {
    assert.deepEqual(placementFromLongitude(359.999), { rashi: 12, nakshatra: 27, pada: 4 });
  });
  it('26°40′ starts Krittika pada 2 in Mesha; 30° is Krittika pada 2 in Vrishabha', () => {
    assert.deepEqual(placementFromLongitude(26 + 40 / 60), { rashi: 1, nakshatra: 3, pada: 1 });
    assert.deepEqual(placementFromLongitude(30), { rashi: 2, nakshatra: 3, pada: 2 });
  });
  it('wraps negative and >360 longitudes', () => {
    assert.deepEqual(placementFromLongitude(-1), placementFromLongitude(359));
    assert.deepEqual(placementFromLongitude(725), placementFromLongitude(5));
  });
  it('every pada is 3°20′', () => {
    for (let i = 0; i < 108; i++) {
      const p = placementFromLongitude(i * (10 / 3) + 0.001);
      assert.equal((p.nakshatra - 1) * 4 + p.pada, i + 1);
    }
  });
  it('whole-sign house counting', () => {
    assert.equal(houseFrom(1, 1), 1);
    assert.equal(houseFrom(1, 12), 12);
    assert.equal(houseFrom(10, 1), 4);
  });
  it('distance to the nearest boundary', () => {
    assert.ok(Math.abs(distanceToBoundary(30.01) - 0.01) < 1e-9);
    assert.ok(Math.abs(distanceToBoundary(1) - 1) < 1e-9);
  });
});

describe('Mangal / Kuja Dosha structure (MANGAL_INCLUSIVE_V1)', () => {
  it('Mars in the 7th from the Lagna, not in its own sign → PRESENT with the placement named', () => {
    const r = evaluateMangal({ lagnaRashi: 1, moonRashi: 3, venusRashi: 3, marsRashi: 7 }, rules);
    assert.equal(r.status, 'PRESENT');
    assert.deepEqual(r.relevantPlacements, [{ reference: 'LAGNA', house: 7, inDoshaHouse: true }]);
    assert.equal(r.cancellationApplied, false);
  });
  it('the 2nd house counts in this rule set', () => {
    assert.equal(evaluateMangal({ lagnaRashi: 1, moonRashi: 6, venusRashi: 6, marsRashi: 2 }, rules).status, 'PRESENT');
  });
  it('Mars in Aries, Scorpio or Capricorn cancels the placement and says so', () => {
    for (const mars of [1, 8, 10]) {
      const r = evaluateMangal({ lagnaRashi: mars, moonRashi: mars, venusRashi: mars, marsRashi: mars }, rules);
      assert.equal(r.status, 'CANCELLED');
      assert.equal(r.cancellationApplied, true);
      assert.equal(r.cancellationCode, 'MARS_IN_OWN_OR_EXALTED_SIGN');
      assert.equal(r.relevantPlacements.length, 3);
    }
  });
  it('no placement → ABSENT, not a bare false', () => {
    const r = evaluateMangal({ lagnaRashi: 1, moonRashi: 1, venusRashi: 1, marsRashi: 3 }, rules);
    assert.equal(r.status, 'ABSENT');
    assert.equal(r.explanationCode, 'MANGAL.NO_MARS_PLACEMENT_IN_RULE_HOUSES');
  });
});

describe('canonical sampling for imprecise times', () => {
  const input = (precision: 'EXACT' | 'APPROXIMATE'): NormalizedBirthInput => ({
    localDate: '2000-01-01',
    localTime: '12:00',
    timezone: 'UTC',
    utcOffsetSeconds: 0,
    instantUtc: '2000-01-01T12:00:00.000Z',
    precision,
    uncertaintyMinutes: precision === 'EXACT' ? null : 60,
    windowStartUtc: precision === 'EXACT' ? '2000-01-01T12:00:00.000Z' : '2000-01-01T11:00:00.000Z',
    windowEndUtc: precision === 'EXACT' ? '2000-01-01T12:00:00.000Z' : '2000-01-01T13:00:00.000Z',
    latitude: 0,
    longitude: 0,
    elevationMeters: 0,
    tzdbVersion: 'x',
  });
  const chart = (moon: number, asc: number): ExactChart => ({
    ascendant: { siderealLongitude: asc, retrograde: false },
    grahas: Object.fromEntries(GRAHA_ORDER.map((g) => [g, { siderealLongitude: g === 'MOON' ? moon : 100, retrograde: false }])) as Record<GrahaName, { siderealLongitude: number; retrograde: boolean }>,
  });

  it('EXACT samples once', () => {
    assert.equal(sampleInstants(input('EXACT'), 25).length, 1);
  });
  it('APPROXIMATE samples both ends of the window', () => {
    const s = sampleInstants(input('APPROXIMATE'), 25);
    assert.equal(s[0], '2000-01-01T11:00:00.000Z');
    assert.equal(s.at(-1), '2000-01-01T13:00:00.000Z');
  });
  it('a field that changes inside the window is null; one that holds is kept; longitude is never reported', () => {
    // Moon crosses 13°20′ (Ashwini → Bharani) but stays in Mesha; ascendant crosses 30° (Mesha → Vrishabha).
    const c = canonicalizeSamples(input('APPROXIMATE'), [chart(13.0, 29.5), chart(13.6, 30.5)]);
    const moon = c.planetaryPositions.find((p) => p.body === 'MOON');
    assert.equal(moon?.rashi, 1);
    assert.equal(moon?.nakshatra, null);
    assert.equal(moon?.pada, null);
    assert.equal(moon?.siderealLongitude, null);
    assert.equal(c.ascendant.rashi, null);
    assert.deepEqual(c.warnings.map((w) => w.code), ['BIRTH_TIME_APPROXIMATE', 'ASCENDANT_NOT_DETERMINABLE', 'MOON_NOT_DETERMINABLE']);
  });
});

describe('canonical JSON', () => {
  it('is independent of key order', () => {
    assert.equal(canonicalJson({ b: 1, a: [2, { d: 1, c: 2 }] }), canonicalJson({ a: [2, { c: 2, d: 1 }], b: 1 }));
  });
});

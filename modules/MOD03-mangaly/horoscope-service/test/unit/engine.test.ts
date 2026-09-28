import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import { HoroscopeEngine } from '../../src/application/HoroscopeEngine.ts';
import { MANGAL_RULESET_INCLUSIVE_V1, RULES_VERSION } from '../../src/domain/config.ts';
import { HoroscopeError } from '../../src/domain/errors.ts';
import { evaluateMangal } from '../../src/domain/mangalRules.ts';
import { GRAHA_ORDER, KOOTA_MAX, KOOTA_ORDER } from '../../src/domain/types.ts';
import type { BirthDetails, ExactChart, GrahaName, MangalRuleset } from '../../src/domain/types.ts';
import { createDefaultEngine } from '../../src/index.ts';
import type { HoroscopeProvider, ProviderDescriptor } from '../../src/provider/HoroscopeProvider.ts';

const hyd: BirthDetails = {
  birthDate: '1993-11-02',
  birthTime: '05:45',
  birthTimePrecision: 'EXACT',
  birthLocation: 'Hyderabad',
  latitude: 17.385,
  longitude: 78.4867,
  timezone: 'Asia/Kolkata',
};
const che: BirthDetails = { ...hyd, birthDate: '1995-04-19', birthTime: '19:10', birthLocation: 'Chennai', latitude: 13.0827, longitude: 80.2707 };

/** A provider that is not Prisri: proves the engine needs only the interface. */
class FixedProvider implements HoroscopeProvider {
  calls = 0;
  private readonly version: string;
  private readonly moon: number;
  constructor(version = '1', moon = 100) {
    this.version = version;
    this.moon = moon;
  }
  describe(): ProviderDescriptor {
    return {
      name: 'fixed-test-provider',
      version: this.version,
      license: 'n/a',
      capabilities: { ayanamshas: ['LAHIRI'], houseSystems: ['WHOLE_SIGN'], matchingSystems: ['ASHTAKOOTA'], mangalRulesetIds: ['MANGAL_INCLUSIVE_V1'], exceptionRules: [] },
    };
  }
  calculateChart(): ExactChart {
    this.calls++;
    return {
      ascendant: { siderealLongitude: 5, retrograde: false },
      grahas: Object.fromEntries(GRAHA_ORDER.map((g) => [g, { siderealLongitude: g === 'MOON' ? this.moon : 200, retrograde: false }])) as Record<GrahaName, { siderealLongitude: number; retrograde: boolean }>,
    };
  }
  calculateAshtakoota() {
    return KOOTA_ORDER.map((k) => ({ koota: k, score: KOOTA_MAX[k], maxScore: KOOTA_MAX[k], groomClass: 'X', brideClass: 'Y', exception: null }));
  }
  calculateMangalDosha(input: Parameters<HoroscopeProvider['calculateMangalDosha']>[0], cfg: Parameters<HoroscopeProvider['calculateMangalDosha']>[1]) {
    return evaluateMangal(input, cfg.mangalRuleset);
  }
}

describe('engine with the Prisri provider', () => {
  const engine = createDefaultEngine();

  it('states its configuration explicitly in every result', () => {
    const c = engine.calculateChart(hyd);
    assert.deepEqual(c.configuration, { zodiacSystem: 'SIDEREAL', ayanamsha: 'LAHIRI', houseSystem: 'WHOLE_SIGN' });
    assert.equal(c.rulesVersion, RULES_VERSION);
    assert.equal(c.provider.name, 'prisri-jyotish');
    assert.match(c.provider.version, /^\d+\.\d+\.\d+$/);
    assert.ok(c.calculationVersion);
  });

  it('gives rashi, nakshatra and pada from the Moon, plus the planetary positions', () => {
    const c = engine.calculateChart(hyd);
    assert.equal(c.rashi, c.moon.rashi);
    assert.equal(c.nakshatra, c.moon.nakshatra);
    assert.equal(c.nakshatraPada, c.moon.pada);
    assert.equal(c.planetaryPositions.length, 9);
    assert.ok(c.ascendant.rashi !== null && c.sun.rashi !== null);
  });

  it('is deterministic: same input → identical chart and match, ids included', () => {
    const fresh = createDefaultEngine({ chartCacheTtlMs: 0 });
    const a1 = fresh.calculateChart(hyd);
    const a2 = fresh.calculateChart({ ...hyd });
    assert.deepEqual(a1, a2);
    const b = fresh.calculateChart(che);
    assert.deepEqual(fresh.calculateMatch(a1, b), fresh.calculateMatch(a2, b));
  });

  it('keeps all eight kootas with their maxima, totalling out of 36', () => {
    const m = engine.calculateMatch(engine.calculateChart(hyd), engine.calculateChart(che));
    assert.equal(m.ashtakoota.status, 'CALCULATED');
    assert.deepEqual(m.ashtakoota.kootas.map((k) => [k.koota, k.maxScore]), KOOTA_ORDER.map((k) => [k, KOOTA_MAX[k]]));
    assert.equal(m.ashtakoota.maxScore, 36);
    assert.equal(m.ashtakoota.totalScore, m.ashtakoota.kootas.reduce((s, k) => s + k.score, 0));
    for (const k of m.ashtakoota.kootas) {
      assert.ok(k.explanation.code.startsWith(`KOOTA.${k.koota}.`));
      assert.ok(typeof k.explanation.params.basis === 'string');
    }
  });

  it('keeps Mangal separate from the 36 and never includes a verdict', () => {
    const m = engine.calculateMatch(engine.calculateChart(hyd), engine.calculateChart(che));
    const kootaTotal = m.ashtakoota.kootas.reduce((s, k) => s + k.score, 0);
    assert.equal(m.ashtakoota.totalScore, kootaTotal);
    assert.ok(['PRESENT', 'ABSENT', 'CANCELLED'].includes(m.mangal.groom.status));
    const text = JSON.stringify(m).toLowerCase();
    for (const banned of ['good match', 'poor match', 'average match', 'recommend', 'proceed', 'verdict', 'compatible', 'best match', 'mismatch']) {
      assert.ok(!text.includes(banned), `result must not contain "${banned}"`);
    }
    assert.equal(m.presentation.layer, 'TRADITIONAL_OPTIONAL');
    assert.ok(m.presentation.noticeCodes.includes('HOROSCOPE.NOTICE.NOT_SCIENTIFIC_NOT_A_PREDICTION'));
  });

  it('the match holds no birth details', () => {
    const m = engine.calculateMatch(engine.calculateChart(hyd), engine.calculateChart(che));
    const text = JSON.stringify(m);
    for (const secret of ['05:45', '19:10', '17.385', '78.4867', '13.0827', 'Hyderabad', 'Chennai', '1993-11-02', 'Asia/Kolkata']) {
      assert.ok(!text.includes(secret), `match must not contain ${secret}`);
    }
  });

  it('an unknown birth time never becomes a guessed chart', () => {
    const c = engine.calculateChart({ ...hyd, birthTime: null, birthTimePrecision: 'UNKNOWN' });
    assert.equal(c.ascendant.rashi, null);
    assert.equal(c.mangalInput, null);
    assert.ok(c.planetaryPositions.every((p) => p.siderealLongitude === null));
    assert.ok(c.calculationWarnings.some((w) => w.code === 'BIRTH_TIME_UNKNOWN'));
  });

  it('an approximate time is flagged and never reported as an exact longitude', () => {
    const c = engine.calculateChart({ ...hyd, birthTimePrecision: 'APPROXIMATE', birthTimeUncertaintyMinutes: 20 });
    assert.ok(c.calculationWarnings.some((w) => w.code === 'BIRTH_TIME_APPROXIMATE'));
    assert.ok(c.planetaryPositions.every((p) => p.siderealLongitude === null));
  });

  it('a wider uncertainty never settles more than a narrower one', () => {
    for (const date of ['1991-02-03', '1994-08-21', '1999-12-12']) {
      const narrow = engine.calculateChart({ ...hyd, birthDate: date, birthTimePrecision: 'APPROXIMATE', birthTimeUncertaintyMinutes: 10 });
      const wide = engine.calculateChart({ ...hyd, birthDate: date, birthTimePrecision: 'APPROXIMATE', birthTimeUncertaintyMinutes: 240 });
      for (const f of ['rashi', 'nakshatra', 'pada'] as const) {
        if (wide.ascendant[f] !== null) assert.equal(wide.ascendant[f], narrow.ascendant[f]);
        if (wide.moon[f] !== null) assert.equal(wide.moon[f], narrow.moon[f]);
      }
    }
  });
});

describe('engine behaviour independent of the provider', () => {
  it('works with any HoroscopeProvider; koota scores come from Mangaly rules, not the provider', () => {
    const e = new HoroscopeEngine(new FixedProvider());
    const m = e.calculateMatch(e.calculateChart(hyd), e.calculateChart(che));
    // Both Moons at 100° (Pushya, Karka): identical placement.
    assert.equal(m.ashtakoota.status, 'CALCULATED');
    assert.equal(m.ashtakoota.kootas.find((k) => k.koota === 'NADI')?.score, 0);
    assert.equal(m.ashtakoota.kootas.find((k) => k.koota === 'YONI')?.score, 4);
    assert.equal(m.ashtakoota.rulesVersion, 'mangaly-ashtakoota-rules/4');
  });

  it('a Moon in the second half of Sagittarius or Capricorn needs its half known for Vashya', () => {
    const e = new HoroscopeEngine(new FixedProvider('1', 262));
    const a = e.calculateChart(hyd);
    assert.equal(a.moonSignHalf, 2);
    const unknownHalf = { ...e.calculateChart(che), moonSignHalf: null };
    const m = e.calculateMatch(unknownHalf, a);
    assert.deepEqual(m.ashtakoota.notDeterminableReasons, ['GROOM_MOON_SIGN_HALF_NOT_DETERMINABLE']);
  });

  it('caches identical charts and expires them', () => {
    let now = 0;
    const p = new FixedProvider();
    const e = new HoroscopeEngine(p, { chartCacheTtlMs: 1000, now: () => now });
    e.calculateChart(hyd);
    e.calculateChart(hyd);
    assert.equal(p.calls, 1);
    now = 1001;
    e.calculateChart(hyd);
    assert.equal(p.calls, 2);
  });

  it('a cached chart cannot be mutated by the caller', () => {
    const e = new HoroscopeEngine(new FixedProvider());
    const a = e.calculateChart(hyd);
    a.rashi = 99;
    assert.notEqual(e.calculateChart(hyd).rashi, 99);
  });

  it('refuses to match charts from another provider version (detectable, never silently mixed)', () => {
    const v1 = new HoroscopeEngine(new FixedProvider('1'));
    const v2 = new HoroscopeEngine(new FixedProvider('2'));
    const old = v1.calculateChart(hyd);
    assert.throws(() => v2.calculateMatch(old, v2.calculateChart(che)), (e: unknown) => e instanceof HoroscopeError && e.code === 'PROVIDER_VERSION_MISMATCH');
  });

  it('a provider version change changes the calculation id', () => {
    assert.notEqual(new HoroscopeEngine(new FixedProvider('1')).calculateChart(hyd).calculationId, new HoroscopeEngine(new FixedProvider('2')).calculateChart(hyd).calculationId);
  });

  it('refuses a provider that cannot honour the configuration', () => {
    class NoLahiri extends FixedProvider {
      override describe(): ProviderDescriptor {
        const d = super.describe();
        return { ...d, capabilities: { ...d.capabilities, ayanamshas: ['RAMAN'] } };
      }
    }
    assert.throws(() => new HoroscopeEngine(new NoLahiri()), (e: unknown) => e instanceof HoroscopeError && e.code === 'UNSUPPORTED_CONFIGURATION');
  });

  it('a Moon that cannot be settled makes Ashtakoota NOT_DETERMINABLE, not a partial score', () => {
    const e = new HoroscopeEngine(new FixedProvider());
    const c = e.calculateChart(hyd);
    const unknown = { ...e.calculateChart(che), rashi: null, nakshatra: null };
    const m = e.calculateMatch(c, unknown);
    assert.equal(m.ashtakoota.status, 'NOT_DETERMINABLE');
    assert.equal(m.ashtakoota.totalScore, null);
    assert.deepEqual(m.ashtakoota.notDeterminableReasons, ['BRIDE_MOON_NOT_DETERMINABLE']);
    assert.deepEqual(m.presentation.headline, { code: 'ASHTAKOOTA_NOT_DETERMINABLE' });
  });

  it('provider failures surface as typed errors', () => {
    class Broken extends FixedProvider {
      override calculateChart(): ExactChart {
        throw new HoroscopeError('PROVIDER_FAILURE', 'provider failed to calculate the chart');
      }
    }
    assert.throws(() => new HoroscopeEngine(new Broken()).calculateChart(hyd), (e: unknown) => e instanceof HoroscopeError && e.code === 'PROVIDER_FAILURE');
  });

  it("uses the named Mangal rule set (AstroSage's)", () => {
    const e = new HoroscopeEngine(new FixedProvider());
    const m = e.calculateMatch(e.calculateChart(hyd), e.calculateChart(che));
    assert.equal(m.mangal.groom.rulesetId, 'MANGAL_ASTROSAGE_V1');
    assert.notEqual(m.mangal.groom.rulesetId, (MANGAL_RULESET_INCLUSIVE_V1 as MangalRuleset).id);
  });
});

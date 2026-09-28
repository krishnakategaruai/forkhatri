import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import { HoroscopeService } from '../../src/application/HoroscopeService.ts';
import { InMemoryHoroscopeStore, MemoryAuditLog, OwnersOnlyAccessPolicy } from '../../src/application/memory.ts';
import { HoroscopeError } from '../../src/domain/errors.ts';
import type { BirthDetails } from '../../src/domain/types.ts';
import { createDefaultEngine } from '../../src/index.ts';

const kavya: BirthDetails = { birthDate: '1996-02-14', birthTime: '08:20', birthTimePrecision: 'EXACT', birthLocation: 'Hyderabad', latitude: 17.385, longitude: 78.4867, timezone: 'Asia/Kolkata' };
const arjun: BirthDetails = { birthDate: '1993-10-03', birthTime: '22:05', birthTimePrecision: 'EXACT', birthLocation: 'Visakhapatnam', latitude: 17.6868, longitude: 83.2185, timezone: 'Asia/Kolkata' };

function setup() {
  const audit = new MemoryAuditLog();
  const store = new InMemoryHoroscopeStore();
  const service = new HoroscopeService({ engine: createDefaultEngine(), store, policy: new OwnersOnlyAccessPolicy(), audit });
  return { service, audit, store };
}

const code = (fn: () => unknown) => {
  try {
    fn();
  } catch (e) {
    assert.ok(e instanceof HoroscopeError);
    return e.code;
  }
  return 'NO_ERROR';
};

describe('HoroscopeService (engine + store + policy + audit)', () => {
  it('only an opted-in owner gets a chart', () => {
    const { service } = setup();
    assert.equal(code(() => service.createChart('kavya', 'kavya', false, kavya)), 'OPT_IN_REQUIRED');
    assert.equal(code(() => service.createChart('arjun', 'kavya', true, kavya)), 'FORBIDDEN');
    assert.ok(service.createChart('kavya', 'kavya', true, kavya).chartId.startsWith('chart_'));
  });

  it('recalculating identical details returns the stored chart', () => {
    const { service } = setup();
    const a = service.createChart('kavya', 'kavya', true, kavya);
    const b = service.createChart('kavya', 'kavya', true, { ...kavya });
    assert.equal(a.chartId, b.chartId);
  });

  it('nobody else can read a chart (it holds birth details)', () => {
    const { service } = setup();
    const c = service.createChart('kavya', 'kavya', true, kavya);
    assert.equal(service.getChart('kavya', c.chartId).horoscope.input.localTime, '08:20');
    assert.equal(code(() => service.getChart('arjun', c.chartId)), 'FORBIDDEN');
  });

  it('a match is created and readable by the two people only, and every access is audited', () => {
    const { service, audit } = setup();
    const k = service.createChart('kavya', 'kavya', true, kavya);
    const a = service.createChart('arjun', 'arjun', true, arjun);
    const { match, created } = service.createMatch('kavya', a.chartId, k.chartId);
    assert.equal(created, true);
    assert.equal(service.createMatch('arjun', a.chartId, k.chartId).created, false);
    assert.equal(service.getMatch('arjun', match.matchId).matchId, match.matchId);
    assert.equal(code(() => service.getMatch('stranger', match.matchId)), 'FORBIDDEN');
    assert.equal(code(() => service.createMatch('stranger', a.chartId, k.chartId)), 'FORBIDDEN');
    const denied = audit.events.filter((e) => e.outcome === 'DENIED');
    assert.equal(denied.length, 2);
    assert.ok(audit.events.every((e) => !JSON.stringify(e).includes('08:20') && !JSON.stringify(e).includes('17.385')));
  });

  it('refuses a match of a person with themself and unknown charts', () => {
    const { service } = setup();
    const k = service.createChart('kavya', 'kavya', true, kavya);
    assert.equal(code(() => service.createMatch('kavya', k.chartId, k.chartId)), 'INVALID_INPUT');
    assert.equal(code(() => service.createMatch('kavya', k.chartId, 'chart_missing')), 'NOT_FOUND');
  });

  it('never overwrites a stored result with a different one', () => {
    const { service, store } = setup();
    const k = service.createChart('kavya', 'kavya', true, kavya);
    const tampered = structuredClone(k);
    tampered.horoscope.rashi = ((tampered.horoscope.rashi ?? 1) % 12) + 1;
    assert.throws(() => store.putChart(tampered), (e: unknown) => e instanceof HoroscopeError && e.code === 'PROVIDER_INCONSISTENT');
  });

  it("the summary shown to the owner's app has no birth inputs", () => {
    const { service } = setup();
    const s = HoroscopeService.summarize(service.createChart('kavya', 'kavya', true, kavya));
    const text = JSON.stringify(s);
    for (const secret of ['08:20', '17.385', 'Hyderabad', '1996-02-14']) assert.ok(!text.includes(secret));
  });
});

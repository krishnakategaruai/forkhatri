import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import type { AddressInfo } from 'node:net';
import { after, before, describe, it } from 'node:test';

import { createHandler } from '../../src/api/http.ts';
import { HoroscopeService } from '../../src/application/HoroscopeService.ts';
import { InMemoryHoroscopeStore, MemoryAuditLog, OwnersOnlyAccessPolicy } from '../../src/application/memory.ts';
import { createDefaultEngine } from '../../src/index.ts';

const TOKEN = 'test-token-0123456789abcdef';
const logs: string[] = [];
let base = '';
const engine = createDefaultEngine();
const server = createServer(
  createHandler(
    new HoroscopeService({ engine, store: new InMemoryHoroscopeStore(), policy: new OwnersOnlyAccessPolicy(), audit: new MemoryAuditLog() }),
    TOKEN,
    (e) => logs.push(JSON.stringify(e)),
    engine,
  ),
);

before(async () => {
  await new Promise<void>((r) => server.listen(0, '127.0.0.1', r));
  base = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
});
after(() => server.close());

async function call(method: string, path: string, viewer: string | null, body?: unknown, token = TOKEN) {
  const headers: Record<string, string> = { 'content-type': 'application/json' };
  if (token) headers.authorization = `Bearer ${token}`;
  if (viewer) headers['x-mangaly-viewer'] = viewer;
  const res = await fetch(base + path, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
  return { status: res.status, json: (await res.json()) as Record<string, any> };
}

const birth = (date: string, time: string) => ({
  birthDate: date,
  birthTime: time,
  birthTimePrecision: 'EXACT',
  birthLocation: 'Secret Street, Hyderabad',
  latitude: 17.4123,
  longitude: 78.4321,
  timezone: 'Asia/Kolkata',
});

describe('HTTP API', () => {
  it('health needs no token; everything else does', async () => {
    assert.equal((await call('GET', '/health', null, undefined, '')).status, 200);
    assert.equal((await call('POST', '/horoscope/chart', 'kavya', {}, '')).status, 403);
    assert.equal((await call('POST', '/horoscope/chart', 'kavya', {}, 'wrong-token-0123456789abcd')).status, 403);
  });

  it('chart → match → read, end to end', async () => {
    const k = await call('POST', '/horoscope/chart', 'kavya', { ownerAccountId: 'kavya', optedIn: true, birthDetails: birth('1996-02-14', '08:20') });
    assert.equal(k.status, 201);
    assert.ok(!JSON.stringify(k.json).includes('08:20'));
    const a = await call('POST', '/horoscope/chart', 'arjun', { ownerAccountId: 'arjun', optedIn: true, birthDetails: birth('1993-10-03', '22:05') });

    const m = await call('POST', '/horoscope/match', 'kavya', { groomChartId: a.json.chartId, brideChartId: k.json.chartId });
    assert.equal(m.status, 201);
    assert.deepEqual(Object.keys(m.json).sort(), ['ashtakoota', 'brideChartId', 'calculationVersion', 'groomChartId', 'mangal', 'matchId', 'porutham', 'presentation', 'rulesVersion', 'traditionalSystem', 'warnings']);
    assert.equal(m.json.ashtakoota.kootas.length, 8);

    const again = await call('GET', `/horoscope/match/${m.json.matchId}`, 'arjun');
    assert.equal(again.status, 200);
    assert.equal((await call('GET', `/horoscope/match/${m.json.matchId}`, 'stranger')).status, 403);
    assert.equal((await call('GET', `/horoscope/chart/${k.json.chartId}`, 'arjun')).status, 403);
    const own = await call('GET', `/horoscope/chart/${k.json.chartId}`, 'kavya');
    assert.equal(own.status, 200);
    assert.equal(own.json.horoscope.input.localTime, '08:20');
  });

  it('bad input answers with a code and field names, never the values', async () => {
    const r = await call('POST', '/horoscope/chart', 'kavya', { ownerAccountId: 'kavya', optedIn: true, birthDetails: { ...birth('1996-02-14', '08:20'), timezone: 'Mars/Olympus' } });
    assert.equal(r.status, 422);
    assert.equal(r.json.error.code, 'INVALID_TIMEZONE');
    assert.ok(!JSON.stringify(r.json).includes('Mars/Olympus'));
    const opt = await call('POST', '/horoscope/chart', 'kavya', { ownerAccountId: 'kavya', optedIn: false, birthDetails: birth('1996-02-14', '08:20') });
    assert.equal(opt.status, 409);
  });

  it('stateless routes for mangaly-service: chart, match, scores', async () => {
    const g = await call('POST', '/horoscope/calculate/chart', 'svc', { birthDetails: birth('1995-01-09', '22:30') });
    const b = await call('POST', '/horoscope/calculate/chart', 'svc', { birthDetails: birth('1995-01-13', '07:30') });
    assert.equal(g.status, 200);
    assert.equal(g.json.rulesVersion, 'mangaly-ashtakoota-rules/4');
    assert.ok(['PRESENT', 'ABSENT'].includes(g.json.mangal.status));
    const m = await call('POST', '/horoscope/calculate/match', 'svc', { groom: g.json, bride: b.json });
    assert.equal(m.status, 200);
    assert.equal(m.json.ashtakoota.totalScore, 23.5); // AstroSage shows 23.5 for this pair
    const stale = await call('POST', '/horoscope/calculate/match', 'svc', { groom: { ...g.json, rulesVersion: 'old' }, bride: b.json });
    assert.equal(stale.status, 409);
    const sc = await call('POST', '/horoscope/calculate/scores', 'svc', {
      pairs: [
        { groom: { rashi: g.json.rashi, nakshatra: g.json.nakshatra, signHalf: g.json.moonSignHalf }, bride: { rashi: b.json.rashi, nakshatra: b.json.nakshatra, signHalf: b.json.moonSignHalf } },
        { groom: { rashi: 9, nakshatra: 20, signHalf: null }, bride: { rashi: 1, nakshatra: 1, signHalf: 1 } },
        { groom: { rashi: 99 }, bride: {} },
      ],
    });
    assert.equal(sc.json.scores[0].status, 'CALCULATED');
    assert.equal(sc.json.scores[0].totalScore, 23.5);
    assert.ok(Number.isInteger(sc.json.scores[0].poruthamAgreed));
    // Sign half unknown: Ashtakoota can't be settled, Porutham still can.
    assert.equal(sc.json.scores[1].status, 'NOT_DETERMINABLE');
    assert.ok(Number.isInteger(sc.json.scores[1].poruthamAgreed));
    assert.deepEqual(sc.json.scores[2], { status: 'NOT_DETERMINABLE', totalScore: null, poruthamAgreed: null, essentialsAgree: null });
  });

  it('logs hold no birth details', () => {
    const all = logs.join('\n');
    for (const secret of ['08:20', '22:05', '17.4123', '78.4321', 'Secret Street', '1996-02-14', 'Asia/Kolkata']) {
      assert.ok(!all.includes(secret), `log leaked ${secret}`);
    }
    assert.ok(logs.length > 0);
  });
});

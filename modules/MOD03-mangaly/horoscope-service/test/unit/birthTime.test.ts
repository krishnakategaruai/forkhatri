import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { describe, it } from 'node:test';

import { normalizeBirthDetails } from '../../src/domain/birthTime.ts';
import { HoroscopeError } from '../../src/domain/errors.ts';
import type { BirthDetails } from '../../src/domain/types.ts';

const base: BirthDetails = {
  birthDate: '1990-05-17',
  birthTime: '14:25',
  birthTimePrecision: 'EXACT',
  birthLocation: 'Hyderabad',
  latitude: 17.385,
  longitude: 78.4867,
  timezone: 'Asia/Kolkata',
};

function code(fn: () => unknown): string {
  try {
    fn();
  } catch (e) {
    assert.ok(e instanceof HoroscopeError);
    return e.code;
  }
  assert.fail('expected an error');
}

describe('birth time → UTC (expected instants computed by hand from the zone rules)', () => {
  it('IST is +05:30', () => {
    const n = normalizeBirthDetails(base);
    assert.equal(n.instantUtc, '1990-05-17T08:55:00.000Z');
    assert.equal(n.utcOffsetSeconds, 19800);
  });

  it('India war time 1942–45 is +06:30, not IST', () => {
    const n = normalizeBirthDetails({ ...base, birthDate: '1944-01-10', birthTime: '06:30' });
    assert.equal(n.utcOffsetSeconds, 23400);
    assert.equal(n.instantUtc, '1944-01-10T00:00:00.000Z');
  });

  it('New York summer uses EDT (−04:00), winter EST (−05:00)', () => {
    const ny = { ...base, latitude: 40.7128, longitude: -74.006, timezone: 'America/New_York' };
    assert.equal(normalizeBirthDetails({ ...ny, birthDate: '1995-07-04', birthTime: '21:15' }).instantUtc, '1995-07-05T01:15:00.000Z');
    assert.equal(normalizeBirthDetails({ ...ny, birthDate: '1995-01-04', birthTime: '21:15' }).instantUtc, '1995-01-05T02:15:00.000Z');
  });

  it('a wall-clock time skipped by a clock change is refused, not shifted', () => {
    const ny = { ...base, latitude: 40.7128, longitude: -74.006, timezone: 'America/New_York' };
    assert.equal(code(() => normalizeBirthDetails({ ...ny, birthDate: '2021-03-14', birthTime: '02:30' })), 'NONEXISTENT_LOCAL_TIME');
  });

  it('a repeated wall-clock time needs the offset stated; either choice is honoured', () => {
    const ny = { ...base, latitude: 40.7128, longitude: -74.006, timezone: 'America/New_York', birthDate: '2021-11-07', birthTime: '01:30' };
    assert.equal(code(() => normalizeBirthDetails(ny)), 'AMBIGUOUS_LOCAL_TIME');
    assert.equal(normalizeBirthDetails({ ...ny, utcOffsetSeconds: -14400 }).instantUtc, '2021-11-07T05:30:00.000Z');
    assert.equal(normalizeBirthDetails({ ...ny, utcOffsetSeconds: -18000 }).instantUtc, '2021-11-07T06:30:00.000Z');
    assert.equal(code(() => normalizeBirthDetails({ ...ny, utcOffsetSeconds: 0 })), 'INVALID_INPUT');
  });

  it('+05:45 Kathmandu crosses the UTC date line backwards', () => {
    const n = normalizeBirthDetails({ ...base, birthDate: '1999-02-11', birthTime: '04:05', timezone: 'Asia/Kathmandu', latitude: 27.7, longitude: 85.3 });
    assert.equal(n.instantUtc, '1999-02-10T22:20:00.000Z');
  });

  it('does not depend on the server time zone', () => {
    const script =
      "import('./src/domain/birthTime.ts').then(m => process.stdout.write(m.normalizeBirthDetails(" +
      JSON.stringify(base) +
      ').instantUtc))';
    for (const tz of ['America/Los_Angeles', 'Pacific/Kiritimati', 'UTC']) {
      const out = execFileSync(process.execPath, ['--input-type=module', '-e', script], {
        env: { ...process.env, TZ: tz },
        cwd: new URL('../..', import.meta.url),
      }).toString();
      assert.equal(out, '1990-05-17T08:55:00.000Z', `server TZ ${tz}`);
    }
  });
});

describe('precision', () => {
  it('EXACT gives a single-instant window', () => {
    const n = normalizeBirthDetails(base);
    assert.equal(n.windowStartUtc, n.windowEndUtc);
  });

  it('APPROXIMATE requires a stated uncertainty and widens the window by it', () => {
    assert.equal(code(() => normalizeBirthDetails({ ...base, birthTimePrecision: 'APPROXIMATE' })), 'INVALID_INPUT');
    const n = normalizeBirthDetails({ ...base, birthTimePrecision: 'APPROXIMATE', birthTimeUncertaintyMinutes: 45 });
    assert.equal(n.precision, 'APPROXIMATE');
    assert.equal(n.windowStartUtc, '1990-05-17T08:10:00.000Z');
    assert.equal(n.windowEndUtc, '1990-05-17T09:40:00.000Z');
  });

  it('UNKNOWN must not carry a time and covers the whole local day', () => {
    assert.equal(code(() => normalizeBirthDetails({ ...base, birthTimePrecision: 'UNKNOWN' })), 'INVALID_INPUT');
    const n = normalizeBirthDetails({ ...base, birthTime: null, birthTimePrecision: 'UNKNOWN' });
    assert.equal(n.instantUtc, null);
    assert.equal(n.localTime, null);
    assert.equal(n.windowStartUtc, '1990-05-16T18:30:00.000Z');
    assert.equal(n.windowEndUtc, '1990-05-17T18:30:00.000Z');
  });

  it('a missing time is an error unless precision says UNKNOWN (never a default time)', () => {
    assert.equal(code(() => normalizeBirthDetails({ ...base, birthTime: null })), 'MISSING_BIRTH_TIME');
  });
});

describe('validation', () => {
  const cases: [string, Record<string, unknown>, string][] = [
    ['bad date format', { birthDate: '17/05/1990' }, 'INVALID_DATE'],
    ['Feb 30', { birthDate: '1990-02-30' }, 'INVALID_DATE'],
    ['29 Feb in a non-leap year', { birthDate: '1990-02-29' }, 'INVALID_DATE'],
    ['hour 24', { birthTime: '24:00' }, 'INVALID_TIME'],
    ['minute 60', { birthTime: '10:60' }, 'INVALID_TIME'],
    ['bad time format', { birthTime: '10.30am' }, 'INVALID_TIME'],
    ['unknown zone', { timezone: 'India/Hyderabad' }, 'INVALID_TIMEZONE'],
    ['empty zone', { timezone: '' }, 'INVALID_TIMEZONE'],
    ['latitude 91', { latitude: 91 }, 'INVALID_COORDINATES'],
    ['longitude NaN', { longitude: Number.NaN }, 'INVALID_COORDINATES'],
    ['elevation absurd', { elevationMeters: 20000 }, 'INVALID_COORDINATES'],
    ['no place label', { birthLocation: '' }, 'INVALID_INPUT'],
    ['before 1900', { birthDate: '1899-12-31' }, 'UNSUPPORTED_DATE_RANGE'],
    ['after 2100', { birthDate: '2101-01-01' }, 'UNSUPPORTED_DATE_RANGE'],
    ['bad precision', { birthTimePrecision: 'ROUGH' }, 'INVALID_INPUT'],
  ];
  for (const [name, patch, expected] of cases) {
    it(name, () => assert.equal(code(() => normalizeBirthDetails({ ...base, ...patch } as BirthDetails)), expected));
  }

  it('29 Feb 2024 (leap day) is valid', () => {
    assert.ok(normalizeBirthDetails({ ...base, birthDate: '2024-02-29' }));
  });

  it('error messages never contain the submitted values', () => {
    try {
      normalizeBirthDetails({ ...base, birthTime: '27:13', latitude: 17.385 });
    } catch (e) {
      const text = `${(e as Error).message} ${JSON.stringify(e)}`;
      assert.ok(!text.includes('27:13'));
      assert.ok(!text.includes('17.385'));
    }
  });
});

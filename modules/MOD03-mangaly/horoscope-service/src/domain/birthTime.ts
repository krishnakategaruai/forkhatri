import { MAX_UNCERTAINTY_MINUTES, SUPPORTED_DATE_RANGE } from './config.ts';
import { HoroscopeError } from './errors.ts';
import type { BirthDetails, NormalizedBirthInput } from './types.ts';

/* Birth-details validation and the wall-clock → UTC conversion.
 *
 * The conversion uses the *birthplace's* IANA zone through the runtime's tz
 * database (which carries historical offsets, wartime time, DST and
 * local-mean-time eras). It never reads the server's own zone and never assumes
 * India Standard Time. Error messages name fields, never values. */

const DATE_RE = /^(\d{4})-(\d{2})-(\d{2})$/;
const TIME_RE = /^(\d{2}):(\d{2})(?::(\d{2}))?$/;

const formatters = new Map<string, Intl.DateTimeFormat>();

function formatterFor(timezone: string): Intl.DateTimeFormat {
  let f = formatters.get(timezone);
  if (!f) {
    f = new Intl.DateTimeFormat('en-US', {
      timeZone: timezone,
      hourCycle: 'h23',
      year: 'numeric',
      month: 'numeric',
      day: 'numeric',
      hour: 'numeric',
      minute: 'numeric',
      second: 'numeric',
    });
    formatters.set(timezone, f);
  }
  return f;
}

/** Offset of the zone from UTC, in seconds east, at an absolute instant. */
export function zoneOffsetSecondsAt(timezone: string, epochMs: number): number {
  const wholeSecondMs = Math.floor(epochMs / 1000) * 1000;
  const parts: Record<string, number> = {};
  for (const p of formatterFor(timezone).formatToParts(new Date(wholeSecondMs))) {
    if (p.type !== 'literal') parts[p.type] = Number(p.value);
  }
  const asIfUtc = Date.UTC(
    parts.year as number,
    (parts.month as number) - 1,
    parts.day as number,
    parts.hour as number,
    parts.minute as number,
    parts.second as number,
  );
  return (asIfUtc - wholeSecondMs) / 1000;
}

export function isValidTimezone(timezone: unknown): timezone is string {
  if (typeof timezone !== 'string' || timezone.length === 0 || timezone.length > 64) return false;
  try {
    new Intl.DateTimeFormat('en-US', { timeZone: timezone });
    return true;
  } catch {
    return false;
  }
}

/** Absolute instants whose wall-clock time in the zone equals `localAsUtcMs`. */
function candidateInstants(timezone: string, localAsUtcMs: number): { epochMs: number; offset: number }[] {
  const seen = new Set<number>();
  for (const probe of [localAsUtcMs - 36 * 3_600_000, localAsUtcMs, localAsUtcMs + 36 * 3_600_000]) {
    seen.add(zoneOffsetSecondsAt(timezone, probe));
  }
  const out: { epochMs: number; offset: number }[] = [];
  for (const offset of seen) {
    const epochMs = localAsUtcMs - offset * 1000;
    if (zoneOffsetSecondsAt(timezone, epochMs) === offset) out.push({ epochMs, offset });
  }
  return out;
}

function assertInt(value: number, lo: number, hi: number, code: 'INVALID_DATE' | 'INVALID_TIME', field: string): void {
  if (!Number.isInteger(value) || value < lo || value > hi) {
    throw new HoroscopeError(code, `${field} is out of range`, [field]);
  }
}

function tzdbVersion(): string {
  const v = (process.versions as Record<string, string | undefined>).tz;
  return v ?? 'unknown';
}

export function normalizeBirthDetails(details: BirthDetails): NormalizedBirthInput {
  if (details === null || typeof details !== 'object') {
    throw new HoroscopeError('INVALID_INPUT', 'birthDetails must be an object', ['birthDetails']);
  }

  // ---- date
  if (typeof details.birthDate !== 'string') {
    throw new HoroscopeError('INVALID_DATE', 'birthDate is required', ['birthDate']);
  }
  const dm = DATE_RE.exec(details.birthDate);
  if (!dm) throw new HoroscopeError('INVALID_DATE', 'birthDate must be YYYY-MM-DD', ['birthDate']);
  const [year, month, day] = [Number(dm[1]), Number(dm[2]), Number(dm[3])] as [number, number, number];
  assertInt(month, 1, 12, 'INVALID_DATE', 'birthDate');
  const daysInMonth = new Date(Date.UTC(year, month, 0)).getUTCDate();
  assertInt(day, 1, daysInMonth, 'INVALID_DATE', 'birthDate');
  if (year < SUPPORTED_DATE_RANGE.fromYear || year > SUPPORTED_DATE_RANGE.toYear) {
    throw new HoroscopeError('UNSUPPORTED_DATE_RANGE', 'birthDate is outside the supported range', ['birthDate']);
  }

  // ---- coordinates
  const { latitude, longitude } = details;
  if (typeof latitude !== 'number' || !Number.isFinite(latitude) || latitude < -90 || latitude > 90) {
    throw new HoroscopeError('INVALID_COORDINATES', 'latitude must be between -90 and 90', ['latitude']);
  }
  if (typeof longitude !== 'number' || !Number.isFinite(longitude) || longitude < -180 || longitude > 180) {
    throw new HoroscopeError('INVALID_COORDINATES', 'longitude must be between -180 and 180', ['longitude']);
  }
  const elevation = details.elevationMeters ?? 0;
  if (typeof elevation !== 'number' || !Number.isFinite(elevation) || elevation < -500 || elevation > 9000) {
    throw new HoroscopeError('INVALID_COORDINATES', 'elevationMeters is out of range', ['elevationMeters']);
  }
  if (typeof details.birthLocation !== 'string' || details.birthLocation.trim() === '' || details.birthLocation.length > 200) {
    throw new HoroscopeError('INVALID_INPUT', 'birthLocation is required', ['birthLocation']);
  }

  // ---- timezone (never defaulted)
  if (!isValidTimezone(details.timezone)) {
    throw new HoroscopeError('INVALID_TIMEZONE', 'timezone must be a valid IANA zone', ['timezone']);
  }
  const timezone = details.timezone;

  // ---- precision and time
  const precision = details.birthTimePrecision;
  if (precision !== 'EXACT' && precision !== 'APPROXIMATE' && precision !== 'UNKNOWN') {
    throw new HoroscopeError('INVALID_INPUT', 'birthTimePrecision must be EXACT, APPROXIMATE or UNKNOWN', ['birthTimePrecision']);
  }

  const localMidnightAsUtc = Date.UTC(year, month - 1, day);
  const base = { localDate: details.birthDate, timezone, latitude, longitude, elevationMeters: elevation, tzdbVersion: tzdbVersion(), precision };

  if (precision === 'UNKNOWN') {
    if (details.birthTime !== null && details.birthTime !== undefined) {
      throw new HoroscopeError('INVALID_INPUT', 'birthTime must be absent when precision is UNKNOWN', ['birthTime']);
    }
    if (details.birthTimeUncertaintyMinutes !== undefined) {
      throw new HoroscopeError('INVALID_INPUT', 'birthTimeUncertaintyMinutes does not apply when precision is UNKNOWN', ['birthTimeUncertaintyMinutes']);
    }
    // The whole local day, widened just enough to stay correct across a clock change.
    const offsets = [
      zoneOffsetSecondsAt(timezone, localMidnightAsUtc - 12 * 3_600_000),
      zoneOffsetSecondsAt(timezone, localMidnightAsUtc + 12 * 3_600_000),
      zoneOffsetSecondsAt(timezone, localMidnightAsUtc + 36 * 3_600_000),
    ];
    const start = localMidnightAsUtc - Math.max(...offsets) * 1000;
    const end = localMidnightAsUtc + 86_400_000 - Math.min(...offsets) * 1000;
    return {
      ...base,
      localTime: null,
      utcOffsetSeconds: null,
      instantUtc: null,
      uncertaintyMinutes: null,
      windowStartUtc: new Date(start).toISOString(),
      windowEndUtc: new Date(end).toISOString(),
    };
  }

  if (details.birthTime === null || details.birthTime === undefined) {
    throw new HoroscopeError('MISSING_BIRTH_TIME', 'birthTime is required unless precision is UNKNOWN', ['birthTime']);
  }
  const tm = typeof details.birthTime === 'string' ? TIME_RE.exec(details.birthTime) : null;
  if (!tm) throw new HoroscopeError('INVALID_TIME', 'birthTime must be HH:MM or HH:MM:SS', ['birthTime']);
  const [hh, mm, ss] = [Number(tm[1]), Number(tm[2]), Number(tm[3] ?? '0')] as [number, number, number];
  assertInt(hh, 0, 23, 'INVALID_TIME', 'birthTime');
  assertInt(mm, 0, 59, 'INVALID_TIME', 'birthTime');
  assertInt(ss, 0, 59, 'INVALID_TIME', 'birthTime');
  const localAsUtc = Date.UTC(year, month - 1, day, hh, mm, ss);

  const candidates = candidateInstants(timezone, localAsUtc);
  if (candidates.length === 0) {
    throw new HoroscopeError('NONEXISTENT_LOCAL_TIME', 'birthTime does not exist in that time zone on that date (clock change)', ['birthTime']);
  }
  let chosen = candidates[0] as { epochMs: number; offset: number };
  if (candidates.length > 1) {
    if (details.utcOffsetSeconds === undefined) {
      throw new HoroscopeError('AMBIGUOUS_LOCAL_TIME', 'birthTime occurred twice in that time zone on that date; supply utcOffsetSeconds', ['birthTime', 'utcOffsetSeconds']);
    }
    const match = candidates.find((c) => c.offset === details.utcOffsetSeconds);
    if (!match) {
      throw new HoroscopeError('INVALID_INPUT', 'utcOffsetSeconds does not match either possible offset', ['utcOffsetSeconds']);
    }
    chosen = match;
  } else if (details.utcOffsetSeconds !== undefined && details.utcOffsetSeconds !== chosen.offset) {
    throw new HoroscopeError('INVALID_INPUT', 'utcOffsetSeconds does not match the time zone on that date', ['utcOffsetSeconds']);
  }

  const instant = chosen.epochMs;
  if (precision === 'EXACT') {
    if (details.birthTimeUncertaintyMinutes !== undefined) {
      throw new HoroscopeError('INVALID_INPUT', 'birthTimeUncertaintyMinutes does not apply when precision is EXACT', ['birthTimeUncertaintyMinutes']);
    }
    return {
      ...base,
      localTime: details.birthTime,
      utcOffsetSeconds: chosen.offset,
      instantUtc: new Date(instant).toISOString(),
      uncertaintyMinutes: null,
      windowStartUtc: new Date(instant).toISOString(),
      windowEndUtc: new Date(instant).toISOString(),
    };
  }

  // APPROXIMATE: never silently treated as exact, and the width of the doubt is stated by the caller.
  const u = details.birthTimeUncertaintyMinutes;
  if (typeof u !== 'number' || !Number.isInteger(u) || u < 1 || u > MAX_UNCERTAINTY_MINUTES) {
    throw new HoroscopeError('INVALID_INPUT', `birthTimeUncertaintyMinutes must be a whole number of minutes from 1 to ${MAX_UNCERTAINTY_MINUTES}`, ['birthTimeUncertaintyMinutes']);
  }
  return {
    ...base,
    localTime: details.birthTime,
    utcOffsetSeconds: chosen.offset,
    instantUtc: new Date(instant).toISOString(),
    uncertaintyMinutes: u,
    windowStartUtc: new Date(instant - u * 60_000).toISOString(),
    windowEndUtc: new Date(instant + u * 60_000).toISOString(),
  };
}

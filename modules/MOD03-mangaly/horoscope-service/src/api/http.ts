import { timingSafeEqual } from 'node:crypto';
import type { IncomingMessage, ServerResponse } from 'node:http';

import { HoroscopeError } from '../domain/errors.ts';
import type { ErrorCode } from '../domain/errors.ts';
import { HoroscopeService } from '../application/HoroscopeService.ts';
import type { HoroscopeEngine } from '../application/HoroscopeEngine.ts';
import { scoreAshtakoota, vashyaNeedsHalf } from '../domain/ashtakootaRules.ts';
import { scorePorutham } from '../domain/poruthamRules.ts';
import type { BirthDetails, CanonicalHoroscope } from '../domain/types.ts';

/* Internal HTTP API. Only mangaly-service calls it (shared service token);
 * browsers never do. The caller states whose request it is in
 * `x-mangaly-viewer`; this service then applies its own AccessPolicy.
 *
 *   POST /horoscope/chart        create (or return) the viewer's chart
 *   GET  /horoscope/chart/{id}   the owner's own chart
 *   POST /horoscope/match        Ashtakoota + Mangal for two charts
 *   GET  /horoscope/match/{id}   a stored match
 *
 * Stateless routes for mangaly-service, which keeps charts in its own
 * database (append-only, versioned) and does its own authorisation:
 *   POST /horoscope/calculate/chart   {birthDetails} → canonical chart
 *   POST /horoscope/calculate/match   {groom, bride} (canonical charts) → match
 *   POST /horoscope/calculate/scores  {pairs:[{groom,bride}]} (Moon placements) → totals, for filtering
 *
 * Responses never contain provider objects, another person's birth inputs,
 * a verdict or a recommendation. Logs carry method, path shape, status and
 * error code only. */

const STATUS: Record<ErrorCode, number> = {
  INVALID_INPUT: 422,
  INVALID_DATE: 422,
  INVALID_TIME: 422,
  MISSING_BIRTH_TIME: 422,
  INVALID_TIMEZONE: 422,
  NONEXISTENT_LOCAL_TIME: 422,
  AMBIGUOUS_LOCAL_TIME: 422,
  INVALID_COORDINATES: 422,
  UNSUPPORTED_DATE_RANGE: 422,
  UNSUPPORTED_CONFIGURATION: 422,
  OPT_IN_REQUIRED: 409,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  PROVIDER_FAILURE: 502,
  PROVIDER_INCOMPLETE_RESULT: 502,
  PROVIDER_INCONSISTENT: 502,
  PROVIDER_VERSION_MISMATCH: 409,
};

const MAX_BODY_BYTES = 16 * 1024;

export type Logger = (entry: Record<string, string | number>) => void;

export function createHandler(service: HoroscopeService, serviceToken: string, log: Logger, engine?: HoroscopeEngine) {
  const expected = Buffer.from(serviceToken);

  return async function handle(req: IncomingMessage, res: ServerResponse): Promise<void> {
    const started = Date.now();
    const path = (req.url ?? '/').split('?')[0] ?? '/';
    const shape = path.replace(/\/(chart|hm|hc)_[A-Za-z0-9-]+$/, '/:id');
    let status = 500;
    let code = '';
    try {
      const result = await route(req, path);
      status = result.status;
      send(res, status, result.body);
    } catch (err) {
      if (err instanceof HoroscopeError) {
        status = STATUS[err.code];
        code = err.code;
        send(res, status, { error: { code: err.code, message: err.message, fields: err.fields } });
      } else {
        status = 500;
        code = 'INTERNAL';
        // The thrown value may contain request data: it is not logged or returned.
        send(res, 500, { error: { code: 'INTERNAL', message: 'internal error', fields: [] } });
      }
    } finally {
      log({ method: req.method ?? '', path: shape, status, code, ms: Date.now() - started });
    }
  };

  async function route(req: IncomingMessage, path: string): Promise<{ status: number; body: unknown }> {
    if (req.method === 'GET' && path === '/health') return { status: 200, body: { status: 'ok' } };

    authenticate(req);
    const viewer = viewerOf(req);

    if (req.method === 'POST' && path === '/horoscope/chart') {
      const body = (await readJson(req)) as { ownerAccountId?: unknown; optedIn?: unknown; birthDetails?: unknown };
      if (typeof body.ownerAccountId !== 'string' || typeof body.optedIn !== 'boolean' || typeof body.birthDetails !== 'object') {
        throw new HoroscopeError('INVALID_INPUT', 'ownerAccountId, optedIn and birthDetails are required', ['ownerAccountId', 'optedIn', 'birthDetails']);
      }
      const record = service.createChart(viewer, body.ownerAccountId, body.optedIn, body.birthDetails as BirthDetails);
      return { status: 201, body: HoroscopeService.summarize(record) };
    }

    const chartMatch = /^\/horoscope\/chart\/(chart_[A-Za-z0-9-]+)$/.exec(path);
    if (req.method === 'GET' && chartMatch) {
      const record = service.getChart(viewer, chartMatch[1] as string);
      // The owner sees their own full chart; a provider object never exists at this level.
      return { status: 200, body: { chartId: record.chartId, horoscope: record.horoscope } };
    }

    if (req.method === 'POST' && path === '/horoscope/match') {
      const body = (await readJson(req)) as { groomChartId?: unknown; brideChartId?: unknown };
      if (typeof body.groomChartId !== 'string' || typeof body.brideChartId !== 'string') {
        throw new HoroscopeError('INVALID_INPUT', 'groomChartId and brideChartId are required', ['groomChartId', 'brideChartId']);
      }
      const { match, created } = service.createMatch(viewer, body.groomChartId, body.brideChartId);
      return { status: created ? 201 : 200, body: match };
    }

    if (engine && req.method === 'POST' && path === '/horoscope/calculate/chart') {
      const body = (await readJson(req)) as { birthDetails?: unknown };
      if (typeof body.birthDetails !== 'object' || body.birthDetails === null) {
        throw new HoroscopeError('INVALID_INPUT', 'birthDetails is required', ['birthDetails']);
      }
      return { status: 200, body: engine.calculateChart(body.birthDetails as BirthDetails) };
    }

    if (engine && req.method === 'POST' && path === '/horoscope/calculate/match') {
      const body = (await readJson(req)) as { groom?: unknown; bride?: unknown };
      const isChart = (c: unknown): c is CanonicalHoroscope =>
        typeof c === 'object' && c !== null && typeof (c as CanonicalHoroscope).calculationId === 'string' && typeof (c as CanonicalHoroscope).rulesVersion === 'string';
      if (!isChart(body.groom) || !isChart(body.bride)) {
        throw new HoroscopeError('INVALID_INPUT', 'groom and bride charts are required', ['groom', 'bride']);
      }
      // Refuses charts from another pipeline, provider, rules or configuration version.
      return { status: 200, body: engine.calculateMatch(body.groom, body.bride) };
    }

    if (req.method === 'POST' && path === '/horoscope/calculate/scores') {
      const body = (await readJson(req)) as { pairs?: unknown };
      if (!Array.isArray(body.pairs) || body.pairs.length > 500) {
        throw new HoroscopeError('INVALID_INPUT', 'pairs must be a list of at most 500', ['pairs']);
      }
      const moon = (m: unknown) => {
        const x = m as { rashi?: unknown; nakshatra?: unknown; signHalf?: unknown } | null;
        if (!x || !Number.isInteger(x.rashi) || !Number.isInteger(x.nakshatra)) return null;
        const r = x.rashi as number, n = x.nakshatra as number;
        if (r < 1 || r > 12 || n < 1 || n > 27) return null;
        const half = x.signHalf === 1 || x.signHalf === 2 ? x.signHalf : null;
        return { rashi: r, nakshatra: n, signHalf: half as 1 | 2 | null };
      };
      const scores = body.pairs.map((p) => {
        const g = moon((p as { groom?: unknown }).groom);
        const b = moon((p as { bride?: unknown }).bride);
        const none = { status: 'NOT_DETERMINABLE' as const, totalScore: null, poruthamAgreed: null, essentialsAgree: null };
        if (!g || !b) return none;
        // Porutham needs only the stars and signs; Ashtakoota may also need the sign half.
        const items = scorePorutham(b, g);
        const porutham = { poruthamAgreed: items.filter((i) => i.agrees).length, essentialsAgree: items.filter((i) => i.essential).every((i) => i.agrees) };
        if ((vashyaNeedsHalf(g.rashi) && g.signHalf === null) || (vashyaNeedsHalf(b.rashi) && b.signHalf === null)) {
          return { ...none, ...porutham };
        }
        try {
          const total = scoreAshtakoota(g, b).reduce((s, k) => s + k.score, 0);
          return { status: 'CALCULATED' as const, totalScore: Math.round(total * 2) / 2, ...porutham };
        } catch {
          return none;
        }
      });
      return { status: 200, body: { scores } };
    }

    const matchMatch = /^\/horoscope\/match\/(hm_[a-f0-9]+)$/.exec(path);
    if (req.method === 'GET' && matchMatch) {
      return { status: 200, body: service.getMatch(viewer, matchMatch[1] as string) };
    }

    throw new HoroscopeError('NOT_FOUND', 'no such route');
  }

  function authenticate(req: IncomingMessage): void {
    const header = req.headers.authorization ?? '';
    const token = Buffer.from(header.startsWith('Bearer ') ? header.slice(7) : '');
    if (token.length !== expected.length || !timingSafeEqual(token, expected)) {
      throw new HoroscopeError('FORBIDDEN', 'service token required');
    }
  }
}

function viewerOf(req: IncomingMessage): string {
  const v = req.headers['x-mangaly-viewer'];
  if (typeof v !== 'string' || !/^[A-Za-z0-9_-]{1,64}$/.test(v)) {
    throw new HoroscopeError('INVALID_INPUT', 'x-mangaly-viewer header is required', ['x-mangaly-viewer']);
  }
  return v;
}

async function readJson(req: IncomingMessage): Promise<unknown> {
  const chunks: Buffer[] = [];
  let size = 0;
  for await (const chunk of req) {
    size += (chunk as Buffer).length;
    if (size > MAX_BODY_BYTES) throw new HoroscopeError('INVALID_INPUT', 'request body too large');
    chunks.push(chunk as Buffer);
  }
  try {
    const parsed: unknown = JSON.parse(Buffer.concat(chunks).toString('utf8'));
    if (parsed === null || typeof parsed !== 'object' || Array.isArray(parsed)) throw new Error('not an object');
    return parsed;
  } catch {
    throw new HoroscopeError('INVALID_INPUT', 'body must be a JSON object');
  }
}

function send(res: ServerResponse, status: number, body: unknown): void {
  const text = JSON.stringify(body);
  res.writeHead(status, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' });
  res.end(text);
}

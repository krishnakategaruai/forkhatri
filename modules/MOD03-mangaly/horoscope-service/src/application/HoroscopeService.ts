import { randomUUID } from 'node:crypto';

import { HoroscopeError } from '../domain/errors.ts';
import type { BirthDetails, CanonicalHoroscope, HoroscopeMatch } from '../domain/types.ts';
import type { HoroscopeEngine } from './HoroscopeEngine.ts';
import type { AccessPolicy, AuditLog, ChartRecord, HoroscopeStore } from './ports.ts';

/* The application service Mangaly calls: calculation plus opt-in,
 * authorization, audit and append-only persistence. Every read of someone
 * else's result goes through the AccessPolicy, and every consequential access
 * is audited. */

/** What anyone other than the owner may ever see of a chart: that it exists. Never birth details. */
export interface ChartSummary {
  chartId: string;
  calculationId: string;
  calculationVersion: string;
  rulesVersion: string;
  configuration: CanonicalHoroscope['configuration'];
  rashi: number | null;
  nakshatra: number | null;
  nakshatraPada: number | null;
  warnings: CanonicalHoroscope['calculationWarnings'];
}

export class HoroscopeService {
  private readonly engine: HoroscopeEngine;
  private readonly store: HoroscopeStore;
  private readonly policy: AccessPolicy;
  private readonly audit: AuditLog;
  private readonly now: () => Date;

  constructor(deps: { engine: HoroscopeEngine; store: HoroscopeStore; policy: AccessPolicy; audit: AuditLog; now?: () => Date }) {
    this.engine = deps.engine;
    this.store = deps.store;
    this.policy = deps.policy;
    this.audit = deps.audit;
    this.now = deps.now ?? (() => new Date());
  }

  createChart(viewerAccountId: string, ownerAccountId: string, optedIn: boolean, details: BirthDetails): ChartRecord {
    this.authorize('chart.create', viewerAccountId, [ownerAccountId], this.policy.canCreateChart(viewerAccountId, ownerAccountId));
    // Horoscope is opt-in only: nothing is calculated for someone who has not chosen it.
    if (optedIn !== true) throw new HoroscopeError('OPT_IN_REQUIRED', 'the owner has not opted in to horoscope matching');

    const horoscope = this.engine.calculateChart(details);
    const existing = this.store.findChart(ownerAccountId, horoscope.calculationId);
    if (existing) return existing;
    const record: ChartRecord = {
      chartId: `chart_${randomUUID()}`,
      ownerAccountId,
      optedIn: true,
      horoscope,
      createdAt: this.now().toISOString(),
    };
    this.store.putChart(record);
    return record;
  }

  /** The owner's full chart, including their own private birth inputs. */
  getChart(viewerAccountId: string, chartId: string): ChartRecord {
    const record = this.store.getChart(chartId);
    if (!record) throw new HoroscopeError('NOT_FOUND', 'chart not found');
    this.authorize('chart.read', viewerAccountId, [chartId], this.policy.canViewChart(viewerAccountId, record.ownerAccountId));
    return record;
  }

  createMatch(viewerAccountId: string, groomChartId: string, brideChartId: string): { match: HoroscopeMatch; created: boolean } {
    const groom = this.store.getChart(groomChartId);
    const bride = this.store.getChart(brideChartId);
    // Not-found and forbidden look the same to a caller who is not allowed to know either chart exists.
    if (!groom || !bride) throw new HoroscopeError('NOT_FOUND', 'chart not found');
    this.authorize(
      'match.create',
      viewerAccountId,
      [groomChartId, brideChartId],
      this.policy.canCreateMatch(viewerAccountId, groom.ownerAccountId, bride.ownerAccountId),
    );
    if (!groom.optedIn || !bride.optedIn) throw new HoroscopeError('OPT_IN_REQUIRED', 'both people must have opted in');
    if (groom.ownerAccountId === bride.ownerAccountId) throw new HoroscopeError('INVALID_INPUT', 'a match needs two different people');

    const match = this.engine.calculateMatch(groom.horoscope, bride.horoscope);
    const created = !this.store.getMatch(match.matchId);
    this.store.putMatch({
      match,
      groomOwnerAccountId: groom.ownerAccountId,
      brideOwnerAccountId: bride.ownerAccountId,
      createdAt: this.now().toISOString(),
    });
    return { match, created };
  }

  getMatch(viewerAccountId: string, matchId: string): HoroscopeMatch {
    const record = this.store.getMatch(matchId);
    if (!record) throw new HoroscopeError('NOT_FOUND', 'match not found');
    this.authorize(
      'match.read',
      viewerAccountId,
      [matchId],
      this.policy.canViewMatch(viewerAccountId, record.groomOwnerAccountId, record.brideOwnerAccountId),
    );
    return record.match;
  }

  static summarize(record: ChartRecord): ChartSummary {
    const h = record.horoscope;
    return {
      chartId: record.chartId,
      calculationId: h.calculationId,
      calculationVersion: h.calculationVersion,
      rulesVersion: h.rulesVersion,
      configuration: h.configuration,
      rashi: h.rashi,
      nakshatra: h.nakshatra,
      nakshatraPada: h.nakshatraPada,
      warnings: h.calculationWarnings,
    };
  }

  private authorize(action: string, viewerAccountId: string, subjectIds: string[], allowed: boolean): void {
    this.audit.record({ action, viewerAccountId, subjectIds, outcome: allowed ? 'ALLOWED' : 'DENIED' });
    if (!allowed) throw new HoroscopeError('FORBIDDEN', 'not permitted');
  }
}

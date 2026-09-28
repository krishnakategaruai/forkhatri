import { canonicalJson } from '../domain/canonical.ts';
import { HoroscopeError } from '../domain/errors.ts';
import type { AccessPolicy, AuditLog, ChartRecord, HoroscopeStore, MatchRecord } from './ports.ts';

/* In-memory implementations for tests and local development. Not durable and
 * not encrypted: production storage belongs in Mangaly's database (see
 * docs/README.md, "Persistence"). */

export class InMemoryHoroscopeStore implements HoroscopeStore {
  private charts = new Map<string, ChartRecord>();
  private matches = new Map<string, MatchRecord>();

  getChart(chartId: string): ChartRecord | undefined {
    return this.charts.get(chartId);
  }

  putChart(record: ChartRecord): void {
    const existing = this.charts.get(record.chartId);
    if (existing) {
      if (canonicalJson(existing.horoscope) !== canonicalJson(record.horoscope)) {
        // Same id, different result: a determinism failure. Never overwrite.
        throw new HoroscopeError('PROVIDER_INCONSISTENT', 'a stored chart would be overwritten with a different result');
      }
      return;
    }
    this.charts.set(record.chartId, record);
  }

  findChart(ownerAccountId: string, calculationId: string): ChartRecord | undefined {
    for (const r of this.charts.values()) {
      if (r.ownerAccountId === ownerAccountId && r.horoscope.calculationId === calculationId) return r;
    }
    return undefined;
  }

  getMatch(matchId: string): MatchRecord | undefined {
    return this.matches.get(matchId);
  }

  putMatch(record: MatchRecord): void {
    const existing = this.matches.get(record.match.matchId);
    if (existing) {
      if (canonicalJson(existing.match) !== canonicalJson(record.match)) {
        throw new HoroscopeError('PROVIDER_INCONSISTENT', 'a stored match would be overwritten with a different result');
      }
      return;
    }
    this.matches.set(record.match.matchId, record);
  }
}

/** The narrowest safe default: a person acts only on their own chart and on matches they are part of. */
export class OwnersOnlyAccessPolicy implements AccessPolicy {
  canCreateChart(viewer: string, owner: string): boolean {
    return viewer === owner;
  }
  canViewChart(viewer: string, owner: string): boolean {
    return viewer === owner;
  }
  canCreateMatch(viewer: string, groom: string, bride: string): boolean {
    return viewer === groom || viewer === bride;
  }
  canViewMatch(viewer: string, groom: string, bride: string): boolean {
    return viewer === groom || viewer === bride;
  }
}

export class MemoryAuditLog implements AuditLog {
  readonly events: Parameters<AuditLog['record']>[0][] = [];
  record(event: Parameters<AuditLog['record']>[0]): void {
    this.events.push(event);
  }
}

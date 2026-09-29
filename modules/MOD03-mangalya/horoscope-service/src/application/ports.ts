import type { CanonicalHoroscope, HoroscopeMatch } from '../domain/types.ts';

/* What the application service needs from the outside world. Mangaly supplies
 * the real implementations (Postgres storage, circle-aware authorization);
 * this package ships in-memory versions for tests and local use. */

export interface ChartRecord {
  chartId: string;
  ownerAccountId: string;
  /** Owner's opt-in at the time of calculation (FR034 / TR034: never used for anyone who has not opted in). */
  optedIn: boolean;
  horoscope: CanonicalHoroscope;
  createdAt: string;
}

export interface MatchRecord {
  match: HoroscopeMatch;
  groomOwnerAccountId: string;
  brideOwnerAccountId: string;
  createdAt: string;
}

/** Append-only: a stored calculation is never overwritten. */
export interface HoroscopeStore {
  getChart(chartId: string): ChartRecord | undefined;
  /** Throws if a different record already exists under the same id. */
  putChart(record: ChartRecord): void;
  /** The current chart an owner has for a calculation key, if any. */
  findChart(ownerAccountId: string, calculationId: string): ChartRecord | undefined;
  getMatch(matchId: string): MatchRecord | undefined;
  putMatch(record: MatchRecord): void;
}

/**
 * Who may do what. Relationship is not permission: being in someone's circle
 * or connected to them does not by itself grant access; Mangaly's policy
 * decides, per request.
 */
export interface AccessPolicy {
  canCreateChart(viewerAccountId: string, ownerAccountId: string): boolean;
  /** Full chart including private birth inputs. */
  canViewChart(viewerAccountId: string, ownerAccountId: string): boolean;
  canCreateMatch(viewerAccountId: string, groomOwner: string, brideOwner: string): boolean;
  canViewMatch(viewerAccountId: string, groomOwner: string, brideOwner: string): boolean;
}

/** Events only: ids and codes, never birth details. */
export interface AuditLog {
  record(event: { action: string; viewerAccountId: string; subjectIds: string[]; outcome: 'ALLOWED' | 'DENIED' }): void;
}

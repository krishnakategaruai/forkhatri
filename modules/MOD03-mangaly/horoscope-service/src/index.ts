/* Public surface of the horoscope package. Mangaly code imports from here and
 * from domain types only; the Prisri adapter is wired in `createDefaultEngine`
 * and nowhere else. */

export * from './domain/types.ts';
export { HoroscopeError } from './domain/errors.ts';
export type { ErrorCode } from './domain/errors.ts';
export { CALCULATION_VERSION, RULES_VERSION, DEFAULT_HOROSCOPE_CONFIGURATION, MANGAL_RULESET_INCLUSIVE_V1, MANGAL_RULESET_ASTROSAGE_V1 } from './domain/config.ts';
export type { HoroscopeProvider, ProviderKootaScore, ProviderDescriptor, ChartRequest } from './provider/HoroscopeProvider.ts';
export { HoroscopeEngine } from './application/HoroscopeEngine.ts';
export { HoroscopeService } from './application/HoroscopeService.ts';
export type { AccessPolicy, AuditLog, HoroscopeStore, ChartRecord, MatchRecord } from './application/ports.ts';
export { InMemoryHoroscopeStore, OwnersOnlyAccessPolicy, MemoryAuditLog } from './application/memory.ts';

import { HoroscopeEngine } from './application/HoroscopeEngine.ts';
import type { EngineOptions } from './application/HoroscopeEngine.ts';
import { PrisriJyotishProvider } from './provider/prisri/PrisriJyotishProvider.ts';

/** The V1 engine: Prisri as the calculation provider. Swap the provider here, nowhere else. */
export function createDefaultEngine(options?: EngineOptions): HoroscopeEngine {
  return new HoroscopeEngine(new PrisriJyotishProvider(), options);
}

import type {
  ExactChart,
  HoroscopeConfiguration,
  KootaName,
  MangalDoshaResult,
  MangalInput,
  MatchingConfiguration,
  MatchingSystem,
  MoonPlacement,
  ProviderIdentity,
} from '../domain/types.ts';

/* The boundary between Mangaly and any astrology engine.
 *
 * The rest of Mangaly depends on this file and on `domain/`, never on a
 * particular library. A provider turns Mangaly's own inputs into Mangaly's own
 * outputs; it may not leak a library type, enum or verdict through here. */

export interface ChartRequest {
  /** An exact instant, ISO 8601 UTC. Uncertain birth times are handled above this boundary. */
  instantUtc: string;
  latitude: number;
  longitude: number;
  elevationMeters: number;
}

/** One koota's raw outcome from a provider, before Mangaly explains it. */
export interface ProviderKootaScore {
  koota: KootaName;
  score: number;
  maxScore: number;
  /** Stable upper-snake codes, e.g. NADI → ADI / MADHYA / ANTYA. */
  groomClass: string;
  brideClass: string;
  /** Null when this provider has no exception rule for the koota. */
  exception: { applied: boolean; code: string } | null;
}

export interface ProviderCapabilities {
  ayanamshas: readonly string[];
  houseSystems: readonly string[];
  matchingSystems: readonly MatchingSystem[];
  mangalRulesetIds: readonly string[];
  /** Exception rules the provider applies inside Ashtakoota, by code. */
  exceptionRules: readonly string[];
}

export interface ProviderDescriptor extends ProviderIdentity {
  license: string;
  capabilities: ProviderCapabilities;
}

export interface HoroscopeProvider {
  describe(): ProviderDescriptor;

  /** Sidereal positions and the ascendant at one exact instant. */
  calculateChart(request: ChartRequest, configuration: HoroscopeConfiguration): ExactChart;

  /**
   * The eight koota scores for a groom-side and a bride-side Moon placement.
   * Returns scores and classes only: no total, no verdict.
   */
  calculateAshtakoota(
    groom: MoonPlacement,
    bride: MoonPlacement,
    configuration: MatchingConfiguration,
  ): ProviderKootaScore[];

  /** Whether the provider's own rule finds a Mangal / Kuja placement present (not cancelled). */
  calculateMangalDosha(input: MangalInput, configuration: MatchingConfiguration): MangalDoshaResult;
}

/* Mangaly's own horoscope vocabulary. Nothing in this file (or anything that
 * imports only from it) knows which astrology library produced a number. */

// ---------------------------------------------------------------- input ----

export type BirthTimePrecision = 'EXACT' | 'APPROXIMATE' | 'UNKNOWN';

export interface BirthDetails {
  /** Local calendar date at the place of birth, YYYY-MM-DD. */
  birthDate: string;
  /** Local wall-clock time, HH:MM or HH:MM:SS. Must be null when precision is UNKNOWN. */
  birthTime: string | null;
  birthTimePrecision: BirthTimePrecision;
  /** Required for APPROXIMATE: how many minutes either side of birthTime the real time may lie. */
  birthTimeUncertaintyMinutes?: number;
  /** Human-readable place label. Never logged, never returned to other users. */
  birthLocation: string;
  latitude: number;
  longitude: number;
  /** IANA zone of the birthplace at the time of birth, e.g. Asia/Kolkata. Never defaulted. */
  timezone: string;
  elevationMeters?: number;
  /**
   * Only needed when the wall-clock time is ambiguous (a clock change repeated
   * it): the offset, in seconds east of UTC, the person was actually on.
   */
  utcOffsetSeconds?: number;
}

/** Birth details after validation: everything needed to reproduce the calculation. */
export interface NormalizedBirthInput {
  localDate: string;
  localTime: string | null;
  timezone: string;
  /** Null when the time is unknown. */
  utcOffsetSeconds: number | null;
  /** ISO instant; the stated time for EXACT/APPROXIMATE, null for UNKNOWN. */
  instantUtc: string | null;
  precision: BirthTimePrecision;
  uncertaintyMinutes: number | null;
  /** The span of instants the birth may have happened in: a single instant for EXACT. */
  windowStartUtc: string;
  windowEndUtc: string;
  latitude: number;
  longitude: number;
  elevationMeters: number;
  /** Version of the IANA time-zone database the offset came from. */
  tzdbVersion: string;
}

// -------------------------------------------------------- configuration ----

export type ZodiacSystem = 'SIDEREAL';
export type Ayanamsha = 'LAHIRI';
export type HouseSystem = 'WHOLE_SIGN';
/** ASHTAKOOTA: North Indian 36-point Guna Milan. PORUTHAM: South Indian 10 poruthams. */
export type MatchingSystem = 'ASHTAKOOTA' | 'PORUTHAM';

export interface HoroscopeConfiguration {
  zodiacSystem: ZodiacSystem;
  ayanamsha: Ayanamsha;
  houseSystem: HouseSystem;
}

export type MangalReference = 'LAGNA' | 'MOON' | 'VENUS';

/** Which Mangal / Kuja Dosha rules apply. Regional traditions differ, so the rule set is explicit. */
export interface MangalRuleset {
  id: string;
  referencePoints: readonly MangalReference[];
  /** Houses counted from each reference point in which Mars counts as a placement. */
  houses: readonly number[];
  /** 1-based rashi numbers in which Mars cancels the placement (Aries, Scorpio, Capricorn). */
  cancellationMarsRashis: readonly number[];
  /** When set, the dosha is HIGH if Mars is in a rule house from at least this many reference points, else LOW. */
  highFromReferences?: number;
}

export interface MatchingConfiguration {
  matchingSystem: MatchingSystem;
  rulesVersion: string;
  /** Ashtakoota is asymmetric (Tara, Yoni, Gana, Varna, Vashya): which chart plays the groom role. */
  groomChart: 'A' | 'B';
  mangalRuleset: MangalRuleset;
}

// ------------------------------------------------------------- zodiac -----

export type GrahaName =
  | 'SUN' | 'MOON' | 'MARS' | 'MERCURY' | 'JUPITER' | 'VENUS' | 'SATURN' | 'RAHU' | 'KETU';

export const GRAHA_ORDER: readonly GrahaName[] = [
  'SUN', 'MOON', 'MARS', 'MERCURY', 'JUPITER', 'VENUS', 'SATURN', 'RAHU', 'KETU',
];

export interface ZodiacPlacement {
  /** 1..12 (Mesha = 1). */
  rashi: number;
  /** 1..27 (Ashwini = 1). */
  nakshatra: number;
  /** 1..4. */
  pada: number;
}

/** A body's position at one exact instant, as a provider reports it. */
export interface ExactPosition {
  /** Sidereal ecliptic longitude in degrees, [0, 360). */
  siderealLongitude: number;
  retrograde: boolean;
}

/** What a provider returns for one exact instant. */
export interface ExactChart {
  ascendant: ExactPosition;
  grahas: Record<GrahaName, ExactPosition>;
}

/** A body's position in a canonical chart; fields are null where the birth time cannot settle them. */
export interface CanonicalPosition {
  body: GrahaName | 'ASCENDANT';
  /** Null unless the birth time is EXACT. */
  siderealLongitude: number | null;
  rashi: number | null;
  nakshatra: number | null;
  pada: number | null;
  retrograde: boolean | null;
}

export interface CalculationWarning {
  code:
    | 'BIRTH_TIME_APPROXIMATE'
    | 'BIRTH_TIME_UNKNOWN'
    | 'ASCENDANT_NOT_DETERMINABLE'
    | 'MOON_NOT_DETERMINABLE'
    | 'PROVIDER_LABEL_BOUNDARY_DISAGREEMENT';
  params?: Record<string, string | number>;
}

export interface ProviderIdentity {
  name: string;
  version: string;
}

export interface CanonicalHoroscope {
  calculationId: string;
  calculationVersion: string;
  provider: ProviderIdentity;
  rulesVersion: string;
  configuration: HoroscopeConfiguration;
  /** Private: exact inputs, kept so the result can be reproduced. Never sent to other users. */
  input: NormalizedBirthInput;
  ascendant: CanonicalPosition;
  moon: CanonicalPosition;
  sun: CanonicalPosition;
  /** Janma rashi / nakshatra / pada: the Moon's, as Ashtakoota uses them. Null when not determinable. */
  rashi: number | null;
  nakshatra: number | null;
  nakshatraPada: number | null;
  /** Which half of its sign the Moon is in (1 = 0–15°, 2 = 15–30°); Vashya splits Sagittarius and Capricorn there. */
  moonSignHalf: 1 | 2 | null;
  planetaryPositions: CanonicalPosition[];
  /** Signs Mangal Dosha is decided on, when the birth time settles them. */
  mangalInput: MangalInput | null;
  /** This person's Mangal Dosha under the rule set Mangaly shows (it depends on one chart only). */
  mangal: MangalDoshaResult;
  calculationWarnings: CalculationWarning[];
}

// ---------------------------------------------------------- ashtakoota ----

export type KootaName =
  | 'VARNA' | 'VASHYA' | 'TARA' | 'YONI' | 'GRAHA_MAITRI' | 'GANA' | 'BHAKOOT' | 'NADI';

export const KOOTA_ORDER: readonly KootaName[] = [
  'VARNA', 'VASHYA', 'TARA', 'YONI', 'GRAHA_MAITRI', 'GANA', 'BHAKOOT', 'NADI',
];

export const KOOTA_MAX: Readonly<Record<KootaName, number>> = {
  VARNA: 1, VASHYA: 2, TARA: 3, YONI: 4, GRAHA_MAITRI: 5, GANA: 6, BHAKOOT: 7, NADI: 8,
};

export const ASHTAKOOTA_MAX_TOTAL = 36;

/** The Moon placement Ashtakoota is defined on. */
export interface MoonPlacement {
  rashi: number;
  nakshatra: number;
}

export interface Explanation {
  code: string;
  params: Record<string, string | number | boolean>;
}

export interface KootaResult {
  koota: KootaName;
  score: number;
  maxScore: number;
  /** The traditional class each side falls in for this koota, as a stable code. */
  groomClass: string;
  brideClass: string;
  /** True/false where the rule set has an exception for this koota; null where it has none. */
  exceptionApplied: boolean | null;
  exceptionCode: string | null;
  explanation: Explanation;
}

export interface AshtakootaResult {
  matchingSystem: MatchingSystem;
  rulesVersion: string;
  /** CALCULATED, or NOT_DETERMINABLE when a Moon placement cannot be settled from the birth time. */
  status: 'CALCULATED' | 'NOT_DETERMINABLE';
  totalScore: number | null;
  maxScore: number;
  kootas: KootaResult[];
  notDeterminableReasons: string[];
}

// -------------------------------------------------------------- mangal ----

/** The signs Mangal Dosha is decided on. */
export interface MangalInput {
  lagnaRashi: number;
  moonRashi: number;
  venusRashi: number;
  marsRashi: number;
}

export interface MangalPlacement {
  reference: MangalReference;
  /** House of Mars counted from the reference point, 1..12. */
  house: number;
  inDoshaHouse: boolean;
}

export interface MangalDoshaResult {
  /** PRESENT; ABSENT (no placement); CANCELLED (placement present, exception applied); INDETERMINATE. */
  status: 'PRESENT' | 'ABSENT' | 'CANCELLED' | 'INDETERMINATE';
  rulesetId: string;
  marsRashi: number | null;
  relevantPlacements: MangalPlacement[];
  cancellationApplied: boolean;
  cancellationCode: string | null;
  /** HIGH / LOW for rule sets that grade the dosha; null otherwise or when not present. */
  level: 'HIGH' | 'LOW' | null;
  explanationCode: string;
}

export type MangalPairing = 'BOTH_PRESENT' | 'ONE_PRESENT' | 'NEITHER_PRESENT' | 'INDETERMINATE';

// --------------------------------------------------------------- match ----

// ------------------------------------------------------------ porutham ----

export type PoruthamName =
  | 'DINA' | 'GANA' | 'MAHENDRA' | 'STREE_DEERGHA' | 'YONI'
  | 'VEDHA' | 'RAJJU' | 'RASI' | 'RASI_ADHIPATHI' | 'VASYA';

export const PORUTHAM_ORDER: readonly PoruthamName[] = [
  'DINA', 'GANA', 'MAHENDRA', 'STREE_DEERGHA', 'YONI', 'VEDHA', 'RAJJU', 'RASI', 'RASI_ADHIPATHI', 'VASYA',
];

/** Rajju and Vedha are traditionally treated as essential: a match is not considered when either fails. */
export const ESSENTIAL_PORUTHAMS: readonly PoruthamName[] = ['RAJJU', 'VEDHA'];

export interface PoruthamItem {
  porutham: PoruthamName;
  /** Agrees (1 point) or not (0). */
  agrees: boolean;
  /** Stable class codes for each side, e.g. RAJJU → KANTA / NABHI…; the star for count-based ones. */
  brideClass: string;
  groomClass: string;
  essential: boolean;
  explanation: Explanation;
}

export interface PoruthamResult {
  matchingSystem: 'PORUTHAM';
  rulesVersion: string;
  status: 'CALCULATED' | 'NOT_DETERMINABLE';
  agreed: number | null;
  outOf: 10;
  /** Whether both essential poruthams (Rajju, Vedha) agree. */
  essentialsAgree: boolean | null;
  items: PoruthamItem[];
  notDeterminableReasons: string[];
}

export interface HoroscopeMatch {
  matchId: string;
  calculationVersion: string;
  rulesVersion: string;
  traditionalSystem: MatchingSystem;
  groomChartId: string;
  brideChartId: string;
  ashtakoota: AshtakootaResult;
  porutham: PoruthamResult;
  mangal: { groom: MangalDoshaResult; bride: MangalDoshaResult; pairing: MangalPairing };
  warnings: CalculationWarning[];
  /** Neutral, structured presentation hints. The UI turns codes into words in each language. */
  presentation: {
    layer: 'TRADITIONAL_OPTIONAL';
    headline:
      | { code: 'ASHTAKOOTA_SCORE'; score: number; outOf: number }
      | { code: 'ASHTAKOOTA_NOT_DETERMINABLE' };
    noticeCodes: string[];
  };
}

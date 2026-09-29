/* Every failure the engine can report. Messages are deliberately generic and
 * never contain birth details: birth data is private and must not reach logs
 * or error responses. `fields` names the offending input by path only. */

export type ErrorCode =
  | 'INVALID_INPUT'
  | 'INVALID_DATE'
  | 'INVALID_TIME'
  | 'MISSING_BIRTH_TIME'
  | 'INVALID_TIMEZONE'
  | 'NONEXISTENT_LOCAL_TIME'
  | 'AMBIGUOUS_LOCAL_TIME'
  | 'INVALID_COORDINATES'
  | 'UNSUPPORTED_DATE_RANGE'
  | 'UNSUPPORTED_CONFIGURATION'
  | 'OPT_IN_REQUIRED'
  | 'FORBIDDEN'
  | 'NOT_FOUND'
  | 'PROVIDER_FAILURE'
  | 'PROVIDER_INCOMPLETE_RESULT'
  | 'PROVIDER_INCONSISTENT'
  | 'PROVIDER_VERSION_MISMATCH';

export class HoroscopeError extends Error {
  readonly code: ErrorCode;
  readonly fields: readonly string[];

  constructor(code: ErrorCode, message: string, fields: readonly string[] = []) {
    super(message);
    this.name = 'HoroscopeError';
    this.code = code;
    this.fields = fields;
  }
}

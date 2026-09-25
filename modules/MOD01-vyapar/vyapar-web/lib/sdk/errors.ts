// [IMP38 — Refactor C] One error type for every Vyapar API failure.
//
// The backend is moving to a single envelope
//   {"error": {"code": "opportunity_not_found", "message": "<localized>", "details": {}}}
// while still sending the legacy `detail` field for this web app. `code` is
// the stable, machine-readable identifier an integration or agent branches
// on; `detail` stays the localized, human-readable text the screens render
// (unchanged from before, so no page has to change how it shows errors).

export interface ErrorEnvelope {
  code?: string;
  message?: string;
  details?: Record<string, unknown>;
}

export class ApiError extends Error {
  /** HTTP status of the failed response. */
  status: number;
  /** Human-readable, localized detail (legacy `detail`, else `error.message`, else the raw body). */
  detail: unknown;
  /** Stable machine-readable code from `error.code`, or null when the server sent none. */
  code: string | null;
  /** Structured details from `error.details`, when present. */
  details: Record<string, unknown> | null;
  /** The full response body, for callers that need something else from it. */
  body: unknown;

  constructor(status: number, detail: unknown, code: string | null = null, body?: unknown, details: Record<string, unknown> | null = null) {
    super(typeof detail === "string" ? detail : JSON.stringify(detail));
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.code = code;
    this.body = body;
    this.details = details;
  }
}

/** Build an ApiError from a failed response body, whichever shape it has. */
export function toApiError(status: number, body: unknown, headerCode?: string | null): ApiError {
  const obj = body && typeof body === "object" ? (body as Record<string, unknown>) : null;
  const envelope = obj && obj.error && typeof obj.error === "object" ? (obj.error as ErrorEnvelope) : null;
  // The backend also sends the code as X-Vyapar-Error-Code, which survives a
  // non-JSON body (a proxy error page, for instance).
  const code = envelope && typeof envelope.code === "string" ? envelope.code : headerCode || null;
  const detail = obj?.detail ?? envelope?.message ?? body;
  const details = envelope?.details && typeof envelope.details === "object" ? envelope.details : null;
  return new ApiError(status, detail, code, body, details);
}

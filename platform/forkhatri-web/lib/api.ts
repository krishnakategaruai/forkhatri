/**
 * Typed client for the public Identity & Trust API
 * (docs/ParentApp/07-tech-reqs.md TR13).
 *
 * - Every call uses `credentials: "include"`; the session is an HttpOnly cookie
 *   this code never sees (TR12). Nothing here reads or writes a token.
 * - Failures surface as `ApiError` (the service answered with a stable
 *   `detail.code`) or `NetworkError` (the service could not be reached), so
 *   screens can tell "you typed a wrong code" apart from "we are offline".
 */

export type Lang = "en" | "hi" | "te" | "mr" | "kn";

/** Every language ForKhatri speaks, in picker order (identity `LANGUAGES`, ADR-010). */
export const LANG_CODES: readonly Lang[] = ["en", "hi", "te", "mr", "kn"];

/** BCP 47 locale for Intl date, number and relative-time formatting and for speech (mr-IN, kn-IN). */
export const INTL_LOCALE: Record<Lang, string> = { en: "en-IN", hi: "hi-IN", te: "te-IN", mr: "mr-IN", kn: "kn-IN" };

export function isLang(value: unknown): value is Lang {
  return typeof value === "string" && (LANG_CODES as readonly string[]).includes(value);
}

/**
 * The platform keeps only basic member information. Every other profile detail
 * (matrimonial profile, activity location, …) lives in the module that needs it.
 */
export type Member = {
  member_id: string;
  display_name: string;
  preferred_language: Lang;
  identity_level: string;
  phone_hint: string | null;
  email_hint: string | null;
};

export type Availability = "available" | "in_development" | "planned";

export type ModuleEntry = {
  key: string;
  name: string;
  tagline: string;
  availability: Availability;
  entry_url: string | null;
  accent: string;
  last_entered_at: string | null;
  /** Present when the service exposes it; order of the array is the fallback. */
  sort_order?: number;
};

export type CodeChallenge = {
  challenge_id: string;
  channel: "sms" | "email";
  destination_hint: string;
  expires_in: number;
  resend_in: number;
  dev_code?: string;
};

/** GET /v1/insights: totals only, never a person. */
export type Insights = {
  generated_at: string;
  totals: {
    members: number;
    joined: number;
    not_yet_joined: number;
    suspended: number;
    new_7d: number;
    new_30d: number;
    active_7d: number;
    active_30d: number;
  };
  growth: { date: string; new: number; total: number }[];
  sign_in: Record<string, number>;
  languages: Record<string, number>;
  modules: { key: string; name: string; members: number }[];
  gender: { candidates: number; counts: Record<string, number> };
  age: {
    bands: { band: string; by_gender: Record<string, number> }[];
    median: number | null;
    youngest: number | null;
    oldest: number | null;
    median_by_gender: Record<string, number | null>;
  };
  candidates: { looking_for: Record<string, number>; marital_status: Record<string, number>; mother_tongue: Record<string, number> };
  location: {
    located: number;
    cities: { name: string; region: string; cc: string; lat: number; lon: number; members: number; by_gender: Record<string, number> }[];
    india_states: { state: string; members: number }[];
    countries: { cc: string; members: number; from_city: number; from_phone: number }[];
    country_unknown: number;
    unresolved: { text: string; members: number }[];
  };
  sources: { module: string; ok: boolean; error?: string | null }[];
};

export type SignedIn = { outcome: "signed_in"; member: Member };
export type VerifyResult = SignedIn | { outcome: "name_required" };

/** Account deletion (docs/ParentApp/ACCOUNT-DELETION.md, kind A). */
export type DeletePreview = {
  modules: { key: string; name: string }[];
  blocked: "admin_role" | null;
  has_password: boolean;
  destination_hint: string | null;
};
export type DeletionModule = {
  module: string;
  name: string;
  status: "pending" | "running" | "done" | "nothing_to_delete" | "partial" | "failed";
  attempts: number;
  deleted: Record<string, number>;
  files_removed: number;
};
export type DeletionStatus = {
  status: "closing" | "done";
  modules: DeletionModule[];
  receipt: null | {
    tombstone: string;
    completed_at: string;
    retained: { scope: string; kind: string; reason: string }[];
  };
};

export const IDENTITY_API = (process.env.NEXT_PUBLIC_IDENTITY_API ?? "http://localhost:8100").replace(/\/+$/, "");

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly retryAfter: number | null,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export class NetworkError extends Error {
  constructor(cause?: unknown) {
    super("identity_unreachable", { cause });
    this.name = "NetworkError";
  }
}

type RequestOptions = {
  method?: "GET" | "POST" | "PATCH";
  body?: unknown;
  lang?: Lang;
  signal?: AbortSignal;
};

async function request<T>(path: string, { method = "GET", body, lang, signal }: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (lang) headers["Accept-Language"] = lang;

  let response: Response;
  try {
    response = await fetch(`${IDENTITY_API}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      credentials: "include",
      cache: "no-store",
      signal,
    });
  } catch (error) {
    if (signal?.aborted) throw error;
    throw new NetworkError(error);
  }

  if (response.status === 204) return undefined as T;

  let payload: unknown = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    const detail = (payload as { detail?: { code?: unknown; message?: unknown } } | null)?.detail;
    const code = typeof detail?.code === "string" ? detail.code : `http_${response.status}`;
    const message = typeof detail?.message === "string" ? detail.message : response.statusText;
    const header = response.headers.get("Retry-After");
    const retryAfter = header && /^\d+$/.test(header.trim()) ? Number(header) : null;
    throw new ApiError(response.status, code, message, retryAfter);
  }
  return payload as T;
}

export const identity = {
  health: (signal?: AbortSignal) => request<{ status: string; service: string }>("/health", { signal }),

  requestCode: (identifier: string) =>
    request<CodeChallenge>("/v1/auth/code", { method: "POST", body: { identifier } }),

  verifyCode: (challenge_id: string, code: string) =>
    request<VerifyResult>("/v1/auth/code/verify", { method: "POST", body: { challenge_id, code } }),

  welcome: (input: { challenge_id: string; code: string; display_name: string; preferred_language: Lang }) =>
    request<SignedIn>("/v1/auth/welcome", { method: "POST", body: input }),

  password: (identifier: string, password: string) =>
    request<SignedIn>("/v1/auth/password", { method: "POST", body: { identifier, password } }),

  signOut: (everywhere: boolean) => request<void>("/v1/auth/sign-out", { method: "POST", body: { everywhere } }),

  /** Resolves to `null` when signed out (`401 not_signed_in`). */
  session: async (signal?: AbortSignal) => {
    try {
      return await request<{ member: Member; expires_at: string }>("/v1/session", { signal });
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) return null;
      throw error;
    }
  },

  updateMe: (patch: Partial<Pick<Member, "display_name" | "preferred_language">>) =>
    request<Member>("/v1/me", { method: "PATCH", body: patch }),

  modules: (lang: Lang, signal?: AbortSignal) => request<ModuleEntry[]>("/v1/modules", { lang, signal }),

  /** Members dashboard: totals only, for every signed-in member. */
  insights: (signal?: AbortSignal) => request<Insights>("/v1/insights", { signal }),

  deletePreview: () => request<DeletePreview>("/v1/account/delete/preview"),
  deleteCode: () => request<CodeChallenge>("/v1/account/delete/code", { method: "POST" }),
  deleteAccount: (body: { confirm: "DELETE"; password?: string; challenge_id?: string; code?: string }) =>
    request<{ job_id: string; status: string }>("/v1/account/delete", { method: "POST", body }),
  deletionStatus: (jobId: string) => request<DeletionStatus>(`/v1/account/deletion/${encodeURIComponent(jobId)}`),

  enter: (key: string) =>
    request<{ entry_url: string }>(`/v1/modules/${encodeURIComponent(key)}/enter`, { method: "POST" }),
  handoff: () => request<{ code: string; expires_in: number }>("/v1/auth/handoff", { method: "POST" }),
};

/** Recently entered first (newest first), then registry order (TR18). */
export function orderModules(modules: ModuleEntry[]): ModuleEntry[] {
  return modules
    .map((module, index) => ({ module, index }))
    .sort((a, b) => {
      const at = a.module.last_entered_at ? Date.parse(a.module.last_entered_at) : NaN;
      const bt = b.module.last_entered_at ? Date.parse(b.module.last_entered_at) : NaN;
      const aRecent = !Number.isNaN(at);
      const bRecent = !Number.isNaN(bt);
      if (aRecent && bRecent) return bt - at;
      if (aRecent !== bRecent) return aRecent ? -1 : 1;
      const ao = a.module.sort_order ?? a.index;
      const bo = b.module.sort_order ?? b.index;
      return ao - bo;
    })
    .map(({ module }) => module);
}

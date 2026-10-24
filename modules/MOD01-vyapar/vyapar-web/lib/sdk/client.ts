// [IMP38 — Refactor C] The transport underneath every SDK domain module.
//
// One small class owns everything a request needs that is NOT business
// logic: the base URL, the auth strategy, the member's language (sent as
// X-Vyapar-Language so every server-side label and error comes back in the
// language on screen), JSON encoding, and turning a failed response into an
// ApiError. Domain modules (opportunities.ts, listings.ts…) only name paths
// and types, so a host swaps any of the above by configuration, never by
// editing a page.
import type { AuthStrategy } from "./auth";
import { toApiError } from "./errors";

export type QueryValue = string | number | boolean | null | undefined | readonly string[];
export type Query = Record<string, QueryValue>;

export interface VyaparClientConfig {
  /** API origin, for example "http://localhost:8011". A function is read on every request. */
  baseUrl: string | (() => string);
  /** Who the caller is. Defaults to no credentials. */
  auth?: AuthStrategy;
  /** Current UI language ("en" | "hi" | "te" | "mr" | "kn"). Read on every request. */
  language?: () => string | null | undefined;
  /** Custom fetch (tests, server runtimes). Defaults to the global fetch. */
  fetch?: typeof fetch;
  /** Extra headers sent with every request. */
  headers?: Record<string, string>;
}

export interface RequestOptions {
  query?: Query;
  body?: unknown;
  headers?: Record<string, string>;
  signal?: AbortSignal;
  /** Sent as Idempotency-Key: a retried POST with the same key returns the first response. */
  idempotencyKey?: string;
  /** Let the request finish even if the page navigates away (fire-and-forget logging). */
  keepalive?: boolean;
}

export type HttpMethod = "GET" | "POST" | "PATCH" | "PUT" | "DELETE";

/** Serialise a query object, skipping empty values; arrays become comma lists. */
export function buildQuery(query?: Query): string {
  if (!query) return "";
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === null || value === "") continue;
    if (Array.isArray(value)) {
      if (value.length > 0) params.set(key, value.join(","));
      continue;
    }
    params.set(key, String(value));
  }
  const s = params.toString();
  return s ? `?${s}` : "";
}

export class VyaparClient {
  private readonly config: VyaparClientConfig;

  constructor(config: VyaparClientConfig) {
    this.config = config;
  }

  get baseUrl(): string {
    const b = this.config.baseUrl;
    return typeof b === "function" ? b() : b;
  }

  get auth(): AuthStrategy | undefined {
    return this.config.auth;
  }

  /** A copy of this client with some settings replaced (for example another auth strategy). */
  with(overrides: Partial<VyaparClientConfig>): VyaparClient {
    return new VyaparClient({ ...this.config, ...overrides });
  }

  private async prepare(extra?: Record<string, string>, json = true): Promise<{ headers: Record<string, string>; init: RequestInit }> {
    const headers: Record<string, string> = { ...(this.config.headers ?? {}) };
    if (json) headers["Content-Type"] = "application/json";
    const init: RequestInit = {};
    if (this.config.auth) await this.config.auth.apply({ headers, init });
    const lang = this.config.language?.();
    if (lang) headers["X-Vyapar-Language"] = lang;
    Object.assign(headers, extra ?? {});
    return { headers, init };
  }

  async request<T>(method: HttpMethod, path: string, options: RequestOptions = {}): Promise<T> {
    const extra = options.idempotencyKey ? { ...(options.headers ?? {}), "Idempotency-Key": options.idempotencyKey } : options.headers;
    const { headers, init } = await this.prepare(extra);
    const doFetch = this.config.fetch ?? fetch;
    const res = await doFetch(`${this.baseUrl}${path}${buildQuery(options.query)}`, {
      ...init,
      method,
      headers,
      // [2026-09-30, owner's phone over the tunnel: cards stayed on
      // skeletons] A read that stalls must fail, so the screen can show its
      // error state with Try again instead of loading forever. Writes are
      // not cut off (they may legitimately take longer and must not be
      // half-sent twice).
      signal:
        options.signal ??
        (method === "GET" && typeof AbortSignal !== "undefined" && "timeout" in AbortSignal ? AbortSignal.timeout(20_000) : undefined),
      keepalive: options.keepalive,
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    });
    const isJson = res.headers.get("content-type")?.includes("application/json");
    const body = isJson ? await res.json() : await res.text();
    if (!res.ok) throw toApiError(res.status, body, res.headers.get("X-Vyapar-Error-Code"));
    return body as T;
  }

  get<T>(path: string, query?: Query, options: Omit<RequestOptions, "query" | "body"> = {}): Promise<T> {
    return this.request<T>("GET", path, { ...options, query });
  }

  post<T>(path: string, body?: unknown, options: Omit<RequestOptions, "body"> = {}): Promise<T> {
    return this.request<T>("POST", path, { ...options, body });
  }

  patch<T>(path: string, body?: unknown, options: Omit<RequestOptions, "body"> = {}): Promise<T> {
    return this.request<T>("PATCH", path, { ...options, body });
  }

  put<T>(path: string, body?: unknown, options: Omit<RequestOptions, "body"> = {}): Promise<T> {
    return this.request<T>("PUT", path, { ...options, body });
  }

  delete<T>(path: string, options: Omit<RequestOptions, "body"> = {}): Promise<T> {
    return this.request<T>("DELETE", path, options);
  }

  /**
   * Multipart upload. Deliberately NOT through request(): multipart bodies
   * must not carry a JSON Content-Type — the browser sets its own with the
   * correct boundary.
   */
  async upload<T = { url: string; size: number }>(path: string, file: File, field = "file"): Promise<T> {
    const form = new FormData();
    form.append(field, file);
    const { headers, init } = await this.prepare(undefined, false);
    const doFetch = this.config.fetch ?? fetch;
    const res = await doFetch(`${this.baseUrl}${path}`, { ...init, method: "POST", headers, body: form });
    const body = await res.json();
    if (!res.ok) throw toApiError(res.status, body, res.headers.get("X-Vyapar-Error-Code"));
    return body as T;
  }

  /** Absolute URL for a server-relative attachment path. */
  resolveUrl(url: string): string {
    return url.startsWith("http") ? url : `${this.baseUrl}${url}`;
  }
}

/** Encode a path segment (ids are UUIDs or slugs, but never trust that). */
export const seg = (value: string | number) => encodeURIComponent(String(value));

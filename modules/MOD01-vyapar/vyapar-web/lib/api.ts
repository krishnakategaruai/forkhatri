// [TR050/FR50 → IMP38 — Refactor C] Compatibility shim over the typed SDK.
//
// This file used to be the fetch wrapper itself: it attached the dev
// identity stub header (X-Dev-Member-Id) and the member's language
// (X-Vyapar-Language) to every request. Both now live in lib/sdk — the
// identity part as a pluggable AuthStrategy (dev header, host session
// cookie or bearer token), the language part as the client's language
// provider — so a host changes them by configuration, not by editing here.
//
// Every export keeps its old name and behaviour so pages not yet moved to
// `useSdk()` / the data hooks keep working unchanged. New code should use
// the SDK directly (`sdk.opportunities.get(id)`), not these helpers.
// Traces to: FR50 (dev-only stand-in), i18n rule, REFACTOR-PLAN.md §C
import { defaultSdk } from "./sdk/default";
import type { HttpMethod } from "./sdk/client";

export { ApiError } from "./sdk/errors";
export { getDevMemberId, setDevMemberId } from "./sdk/auth";

const client = defaultSdk.client;

/** Legacy fetch-style entry point: `init.method`, `init.body` (a JSON string) and extra headers are honoured. */
export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const method = ((init?.method ?? "GET").toUpperCase() as HttpMethod);
  let body: unknown = undefined;
  if (typeof init?.body === "string") {
    try {
      body = JSON.parse(init.body);
    } catch {
      body = init.body;
    }
  }
  const h = init?.headers;
  const headers: Record<string, string> | undefined = !h
    ? undefined
    : h instanceof Headers
      ? Object.fromEntries(h.entries())
      : Array.isArray(h)
        ? Object.fromEntries(h)
        : { ...(h as Record<string, string>) };
  return client.request<T>(method, path, { body, headers, signal: init?.signal ?? undefined });
}

export function uploadFile(file: File): Promise<{ url: string; size: number }> {
  return defaultSdk.uploads.upload(file);
}

export function resolveAttachmentUrl(url: string): string {
  return client.resolveUrl(url);
}

export const api = {
  get: <T>(path: string) => client.request<T>("GET", path),
  post: <T>(path: string, data?: unknown) => client.request<T>("POST", path, { body: data }),
  patch: <T>(path: string, data?: unknown) => client.request<T>("PATCH", path, { body: data }),
  delete: <T>(path: string) => client.request<T>("DELETE", path),
};

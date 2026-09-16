// [TR050/FR50] Thin fetch wrapper that attaches the dev identity stub header
// (X-Dev-Member-Id) to every request. This is the ONLY place the frontend
// asserts "who is calling" — it reads the member id the DevMemberSwitcher
// component wrote to localStorage, never a login form. Once the parent
// ForKhatri platform's real fk_session cookie is wired in, this file is the
// one call site to change (drop the header, rely on the cookie the browser
// already sends), not a rewrite scattered across every page.
// [Product-owner i18n rule] Also attaches X-Vyapar-Language (the same
// localStorage key provider.tsx reads) so every backend error/success
// message (app/i18n's translate()) matches the member's chosen language,
// not just the frontend's own JSX strings.
// Traces to: FR50 (dev-only stand-in), task brief's "dev member switcher", i18n rule
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8011";
const DEV_MEMBER_STORAGE_KEY = "vyapar_dev_member_id";
const LANGUAGE_STORAGE_KEY = "vyapar.language";

function getLanguage(): string {
  if (typeof window === "undefined") return "en";
  return window.localStorage.getItem(LANGUAGE_STORAGE_KEY) ?? "en";
}

export function getDevMemberId(): string {
  if (typeof window === "undefined") return "m_krishna";
  return window.localStorage.getItem(DEV_MEMBER_STORAGE_KEY) ?? "m_krishna";
}

export function setDevMemberId(memberId: string) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(DEV_MEMBER_STORAGE_KEY, memberId);
  window.dispatchEvent(new CustomEvent("vyapar:dev-member-changed", { detail: memberId }));
}

export class ApiError extends Error {
  status: number;
  detail: unknown;
  constructor(status: number, detail: unknown) {
    super(typeof detail === "string" ? detail : JSON.stringify(detail));
    this.status = status;
    this.detail = detail;
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-Dev-Member-Id": getDevMemberId(),
      "X-Vyapar-Language": getLanguage(),
      ...(init?.headers ?? {}),
    },
  });
  const isJson = res.headers.get("content-type")?.includes("application/json");
  const body = isJson ? await res.json() : await res.text();
  if (!res.ok) {
    throw new ApiError(res.status, (body as { detail?: unknown })?.detail ?? body);
  }
  return body as T;
}

export const api = {
  get: <T>(path: string) => apiFetch<T>(path),
  post: <T>(path: string, data?: unknown) =>
    apiFetch<T>(path, { method: "POST", body: data !== undefined ? JSON.stringify(data) : undefined }),
  patch: <T>(path: string, data?: unknown) =>
    apiFetch<T>(path, { method: "PATCH", body: JSON.stringify(data) }),
  delete: <T>(path: string) => apiFetch<T>(path, { method: "DELETE" }),
};

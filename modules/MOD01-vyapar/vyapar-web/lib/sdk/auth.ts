// [IMP38 — Refactor C] Pluggable authentication for the Vyapar SDK.
//
// The SDK never decides who the caller is; an AuthStrategy does. Three are
// provided, matching the backend's identity providers (workstream B):
//   - devHeaderAuth      — the development stand-in: X-Dev-Member-Id read
//                          from localStorage (what the web app has always
//                          sent). Never use in production.
//   - cookieSessionAuth  — a browser session owned by the host platform; the
//                          SDK sends `credentials: "include"` and no header.
//   - bearerTokenAuth    — a personal access token or agent credential,
//                          sent as `Authorization: Bearer <token>`.
// A host can supply its own strategy by implementing the interface.

export interface AuthRequest {
  /** Mutable request headers. */
  headers: Record<string, string>;
  /** Mutable fetch init (for example to set `credentials`). */
  init: RequestInit;
}

export interface AuthStrategy {
  /** Short name, for diagnostics only. */
  readonly kind: string;
  apply(req: AuthRequest): void | Promise<void>;
}

// ---- development member identity -------------------------------------------

export const DEV_MEMBER_STORAGE_KEY = "vyapar_dev_member_id";
export const DEFAULT_DEV_MEMBER_ID = "m_krishna";

export function getDevMemberId(): string {
  if (typeof window === "undefined") return DEFAULT_DEV_MEMBER_ID;
  try {
    return window.localStorage.getItem(DEV_MEMBER_STORAGE_KEY) ?? DEFAULT_DEV_MEMBER_ID;
  } catch {
    return DEFAULT_DEV_MEMBER_ID;
  }
}

export function setDevMemberId(memberId: string): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(DEV_MEMBER_STORAGE_KEY, memberId);
  } catch {
    /* blocked storage: the switch lasts for this page only */
  }
  window.dispatchEvent(new CustomEvent("vyapar:dev-member-changed", { detail: memberId }));
}

export function devHeaderAuth(options: { getMemberId?: () => string } = {}): AuthStrategy {
  const read = options.getMemberId ?? getDevMemberId;
  return {
    kind: "dev-header",
    apply({ headers }) {
      headers["X-Dev-Member-Id"] = read();
    },
  };
}

// ---- host session cookie ----------------------------------------------------

export function cookieSessionAuth(): AuthStrategy {
  return {
    kind: "cookie-session",
    apply({ init }) {
      init.credentials = "include";
    },
  };
}

// ---- bearer token -----------------------------------------------------------

export type TokenSource = string | (() => string | null | undefined | Promise<string | null | undefined>);

export function bearerTokenAuth(token: TokenSource): AuthStrategy {
  return {
    kind: "bearer",
    async apply({ headers }) {
      const value = typeof token === "function" ? await token() : token;
      if (value) headers["Authorization"] = `Bearer ${value}`;
    },
  };
}

/** No credentials at all (public reads only). */
export function anonymousAuth(): AuthStrategy {
  return { kind: "anonymous", apply() {} };
}

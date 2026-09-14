/* Auth calls against MangalyService.
 *
 * Every request sends `credentials: 'include'` because the session token is an
 * HttpOnly cookie (SP090) — page JS cannot read or attach it, so the browser
 * has to. That is the point: a token JS can read is a token an injected script
 * can steal.
 *
 * [ADR-010] Every request also sends `X-Mangaly-Language` so the server can
 * localize `detail`/`message` text itself (see `mangaly-service/app/i18n/`).
 * Because of that, `message` below is already-localized prose straight from
 * the server for any response the server actually returned — this module
 * does not re-translate it. The one case with no server response at all
 * (`kind: 'network'`) is the only one a caller should translate client-side,
 * since there is nothing localized to display otherwise.
 */

import { API_BASE } from './api';
import { getI18n } from './i18n/config';

function currentLanguageHeader(): Record<string, string> {
  try {
    return { 'X-Mangaly-Language': getI18n().language };
  } catch {
    return {};
  }
}

export type AuthOutcome<T> =
  | { ok: true; data: T }
  | { ok: false; kind: 'rejected' | 'rateLimited' | 'network'; message?: string };

async function post<T>(path: string, body: unknown): Promise<AuthOutcome<T>> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...currentLanguageHeader() },
      credentials: 'include',
      body: JSON.stringify(body),
    });
  } catch {
    return { ok: false, kind: 'network' };
  }

  if (res.ok) {
    const text = await res.text();
    return { ok: true, data: (text ? JSON.parse(text) : null) as T };
  }

  // The server already localized `detail` for us (ADR-010) — carry it through
  // verbatim rather than re-deriving a client-side message for the same error.
  const body_ = await res.json().catch(() => null);
  const message: string | undefined = body_?.detail;
  return { ok: false, kind: res.status === 429 ? 'rateLimited' : 'rejected', message };
}

export type Session = { account_id: string; expires_at: string };

/** [FR093/TR093, DEC-V1-012] SECONDARY login path — password, for an account
 *  that has one set. Reached only via the login screen's "use password
 *  instead" link. Failure carries the server's own localized reason. */
export function logIn(identifier: string, credential: string) {
  return post<Session>('/auth/login', { identifier, credential });
}

/** [FR093/DEC-V1-012] PRIMARY login path — request an OTP. Same response
 *  whether or not the identifier is registered (SP092-class). Verify via
 *  `verifyOtp(identifier, code, 'login')`. */
export function requestLoginOtp(identifier: string) {
  return post<{ status: string; message: string }>('/auth/login/otp/request', {
    identifier,
  });
}

/** [FR092/TR092, DEC-V1-012] Sign up — identifier + OTP only, no password.
 *  Always succeeds from the client's point of view — the response is
 *  identical whether or not the identifier already exists (SP092). */
export function signUp(identifier: string) {
  return post<{ status: string; message: string }>('/auth/signup', {
    identifier,
  });
}

export function logOut() {
  return post<null>('/auth/logout', {});
}

/** [FR095/TR095] Verify a one-time code. `outcome` is a machine-readable code
 *  the CALLER localizes via `auth:otp.error.*` — see `OtpVerifyResult`. */
export type OtpPurpose = 'signup' | 'login' | 'password_reset' | 'identifier_change';
export type OtpOutcome = 'verified' | 'invalid' | 'expired' | 'too_many_attempts';
export type OtpVerifyResult = { outcome: OtpOutcome; account_id: string | null };

export function verifyOtp(identifier: string, code: string, purpose: OtpPurpose = 'signup') {
  return post<OtpVerifyResult>('/auth/otp/verify', { identifier, code, purpose });
}

export function resendOtp(identifier: string, purpose: OtpPurpose = 'signup') {
  return post<{ status: string; message: string }>('/auth/otp/resend', {
    identifier,
    purpose,
  });
}

/** [FR094/TR094] Request a password-reset code. Same anti-enumeration shape
 *  as sign-up/login-OTP — identical response whether or not the identifier
 *  has an account. Confirm via `confirmPasswordReset()`. */
export function requestPasswordReset(identifier: string) {
  return post<{ status: string; message: string }>('/auth/reset/request', {
    identifier,
  });
}

export type PasswordResetConfirmResult = { outcome: OtpOutcome; message: string | null };

/** [FR094/TR094] Verify the reset code and set a new password in one step —
 *  there is no separate "verify" call first, since the code is single-use. */
export function confirmPasswordReset(identifier: string, code: string, newCredential: string) {
  return post<PasswordResetConfirmResult>('/auth/reset/confirm', {
    identifier,
    code,
    new_credential: newCredential,
  });
}

/** [FR090/TR090] Resolve the current session, or null when not signed in. */
export async function getSession(): Promise<Session | null> {
  try {
    const res = await fetch(`${API_BASE}/auth/me`, {
      credentials: 'include',
      cache: 'no-store',
      headers: currentLanguageHeader(),
    });
    if (!res.ok) return null;
    return (await res.json()) as Session;
  } catch {
    return null;
  }
}

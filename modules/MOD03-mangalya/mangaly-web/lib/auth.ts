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
 *
 * [2026-09-17 rework, contract §1] `GET /auth/me` is now the ONE identity
 * call: it carries the account's display name, its own candidate profile (if
 * any), every Home Circle membership with its relationship, and the unread
 * counts the navigation shows. Pages never call `/home-circle/contexts` or
 * `/profile/me` just to find out who is signed in any more — `lib/session.tsx`
 * fetches this once and shares it. */

import { API_BASE, currentLanguageHeader } from './api';
import { reportOutage } from './outage';
import { redirectToEntrance, signOutOfForKhatri } from './platform';

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

/* ---------- Contract §1: the identity payload ---------- */

export type LookingFor = 'bride' | 'groom';

/** Relationship vocabulary — per membership, never per account (contract §6). */
export type Relationship = 'parent' | 'sibling' | 'relative' | 'guardian';

export type OwnProfile = {
  profile_id: string;
  name: string;
  looking_for: LookingFor | null;
  primary_photo_url: string | null;
  discoverable: boolean;
  /** [DEC-V1-019] Set when someone else (a parent) created this profile. */
  created_by_name?: string | null;
  created_by_relation?: string | null;
  created_by_role?: string | null;
  claimed?: boolean;
};

export type ManagedProfileRef = { account_id: string; name: string; primary_photo_url: string | null };

export type CircleMembership = {
  /** The candidate's account id — what every people-keyed endpoint takes. */
  candidate_account_id: string;
  candidate_profile_id: string;
  candidate_name: string;
  relationship: Relationship;
  /** [Migration 040] Exact relation (mother, maternal_uncle, …) when stated. */
  relation?: string | null;
  looking_for: LookingFor | null;
  primary_photo_url: string | null;
  member_count: number;
  /** The caller's own membership row, when the server sends it (leave/remove). */
  membership_id?: string;
};

export type Counts = {
  unread_messages: number;
  pending_requests: number;
  unread_notifications: number;
};

export type Session = {
  account_id: string;
  display_name: string;
  preferred_language: string;
  expires_at: string;
  /** Present ⇒ the account is also a candidate. */
  own_profile: OwnProfile | null;
  /** One entry per Home Circle membership, each with its own relationship. */
  circles: CircleMembership[];
  counts: Counts;
  /** [DEC-V1-019] Profiles this person created for a son or daughter, not yet taken over. */
  managed_profiles: ManagedProfileRef[];
};

/** Normalizes whatever `/auth/me` answers into the contract shape, so a field
 *  the server has not started sending yet reads as "none" rather than crashing
 *  the shell. Nothing here invents data. */
function normalizeSession(raw: Record<string, unknown>): Session {
  const own = (raw.own_profile ?? null) as OwnProfile | null;
  const circles = Array.isArray(raw.circles) ? (raw.circles as CircleMembership[]) : [];
  const counts = (raw.counts ?? {}) as Partial<Counts>;
  return {
    account_id: String(raw.account_id ?? ''),
    display_name: typeof raw.display_name === 'string' ? raw.display_name : '',
    preferred_language: typeof raw.preferred_language === 'string' ? raw.preferred_language : 'en',
    expires_at: typeof raw.expires_at === 'string' ? raw.expires_at : '',
    own_profile: own
      ? {
          profile_id: String(own.profile_id ?? ''),
          name: own.name ?? '',
          looking_for: own.looking_for ?? null,
          primary_photo_url: own.primary_photo_url ?? null,
          discoverable: !!own.discoverable,
          created_by_name: own.created_by_name ?? null,
          created_by_relation: own.created_by_relation ?? null,
          created_by_role: own.created_by_role ?? null,
          claimed: own.claimed ?? true,
        }
      : null,
    managed_profiles: Array.isArray(raw.managed_profiles)
      ? (raw.managed_profiles as ManagedProfileRef[])
      : [],
    circles: circles.map((c) => ({
      candidate_account_id: String(
        (c as { candidate_account_id?: string }).candidate_account_id ?? c.candidate_profile_id ?? '',
      ),
      candidate_profile_id: String(c.candidate_profile_id ?? ''),
      candidate_name: c.candidate_name ?? '',
      relationship: (c.relationship ?? 'relative') as Relationship,
      relation: c.relation ?? null,
      looking_for: c.looking_for ?? null,
      primary_photo_url: c.primary_photo_url ?? null,
      member_count: Number(c.member_count ?? 0),
      membership_id: c.membership_id,
    })),
    counts: {
      unread_messages: Number(counts.unread_messages ?? 0),
      pending_requests: Number(counts.pending_requests ?? 0),
      unread_notifications: Number(counts.unread_notifications ?? 0),
    },
  };
}

/** [FR093/TR093, DEC-V1-012] SECONDARY login path — password, for an account
 *  that has one set. Reached only via the login screen's "use password
 *  instead" link. Failure carries the server's own localized reason. */
export function logIn(identifier: string, credential: string) {
  return post<{ account_id: string; expires_at: string }>('/auth/login', { identifier, credential });
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

/** [ForKhatri TR16, 2026-09-14] Log out = sign out of ForKhatri, then the
 *  entrance. Mangaly has no module-only session left to end. */
export async function logOut(): Promise<void> {
  await signOutOfForKhatri();
}

/** Retained interim logout (`mangaly_session`). No rendered screen calls it. */
export function logOutInterim() {
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

/** Mangaly or the ForKhatri identity service cannot answer right now. */
export class SessionUnavailableError extends Error {}

/** [FR090/TR090 → ForKhatri TR15/TR16] The signed-in ForKhatri member as
 *  MangalyService sees them. `null` means signed out (401) and nothing else.
 *  Unreachable/503/403 throw `SessionUnavailableError`: reporting those as
 *  "signed out" would send a signed-in member to the entrance, which would
 *  send them straight back — a redirect loop. */
export async function getSession(): Promise<Session | null> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/auth/me`, {
      credentials: 'include',
      cache: 'no-store',
      headers: currentLanguageHeader(),
    });
  } catch {
    throw new SessionUnavailableError('network');
  }
  if (res.status === 401) return null;
  if (!res.ok) throw new SessionUnavailableError(`HTTP ${res.status}`);
  return normalizeSession((await res.json()) as Record<string, unknown>);
}

/** For signed-in screens outside the shell's provider (the profile wizard).
 *  Returns the session; or starts the hand-off to the ForKhatri entrance and
 *  returns null (signed out); or reports an outage and returns null. */
export async function requireSession(): Promise<Session | null> {
  try {
    const session = await getSession();
    if (!session) redirectToEntrance();
    return session;
  } catch {
    reportOutage();
    return null;
  }
}

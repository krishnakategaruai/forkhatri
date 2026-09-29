/* ForKhatri platform integration for the Mangaly web client.
 *
 * docs/ParentApp/07-tech-reqs.md TR12/TR16/TR17/TR24 (2026-09-14): ForKhatri
 * is one app with one sign-in. Mangaly renders no sign-in, sign-up, OTP or
 * password-reset screen of its own. The browser's only credential is the
 * HttpOnly `fk_session` cookie issued by the ForKhatri Identity & Trust
 * Service; page JS never sees it, it simply rides along on every
 * `credentials: 'include'` request to MangalyService.
 *
 *  - Signed out, or any API call answering 401 → a full-page navigation to the
 *    ForKhatri entrance with `return_to` set to where the member was, so they
 *    land back on the same Mangaly screen after signing in.
 *  - Log out → the platform sign-out endpoint, then the entrance. Signing out
 *    of Mangaly IS signing out of ForKhatri; there is no module-only session.
 *
 * No URL is hardcoded at a call site (TR24): both come from NEXT_PUBLIC_* env
 * values, with the development ports as fallbacks. */

export const FORKHATRI_ENTRANCE_URL = (
  process.env.NEXT_PUBLIC_FORKHATRI_ENTRANCE_URL ?? 'http://localhost:3100'
).replace(/\/+$/, '');

export const IDENTITY_API = (
  process.env.NEXT_PUBLIC_IDENTITY_API ?? 'http://localhost:8100'
).replace(/\/+$/, '');

/** [TR22] Mangaly's zone prefix in production (`/mangaly`); empty in development. */
export const BASE_PATH = (process.env.NEXT_PUBLIC_BASE_PATH ?? '').replace(/\/+$/, '');

/** Absolute URL of a Mangaly page, for places that leave the Next router (return_to). */
export function mangalyUrl(path = '/'): string {
  return `${window.location.origin}${BASE_PATH}${path}`;
}

/** The entrance (hub) URL, optionally asking it to send the member back. */
export function entranceUrl(returnTo?: string): string {
  return returnTo
    ? `${FORKHATRI_ENTRANCE_URL}/?return_to=${encodeURIComponent(returnTo)}`
    : `${FORKHATRI_ENTRANCE_URL}/`;
}

// Several API calls on one screen can all see the same 401; navigate once.
let leaving = false;

/** [TR16] Full-page navigation to the ForKhatri entrance. */
export function redirectToEntrance(returnTo?: string): void {
  if (typeof window === 'undefined' || leaving) return;
  leaving = true;
  window.location.assign(entranceUrl(returnTo ?? window.location.href));
}

/** [TR16] Sign out of ForKhatri (not just Mangaly), then go to the entrance. */
export async function signOutOfForKhatri(): Promise<void> {
  try {
    await fetch(`${IDENTITY_API}/v1/auth/sign-out`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ everywhere: false }),
    });
  } catch {
    // Unreachable identity service: still leave. The entrance shows the real
    // session state, and MangalyService re-checks every request regardless.
  }
  if (typeof window === 'undefined') return;
  leaving = true;
  window.location.assign(entranceUrl());
}

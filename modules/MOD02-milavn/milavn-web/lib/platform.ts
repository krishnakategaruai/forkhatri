/* ForKhatri platform edges for the Milavn web client (docs/ParentApp/07-tech-reqs.md TR12, TR16, TR17).
 *
 * Milavn never signs anyone in. The browser holds one HttpOnly ForKhatri
 * session cookie that Milavn's API resolves; this file only knows where the
 * ForKhatri entrance and the Identity API are, so a signed-out person can be
 * sent to sign in and brought straight back (`return_to`). */

export const IDENTITY_API = process.env.NEXT_PUBLIC_IDENTITY_API ?? 'http://localhost:8100';
export const FORKHATRI_ENTRANCE_URL = process.env.NEXT_PUBLIC_FORKHATRI_ENTRANCE_URL ?? 'http://localhost:3100';

/** Entrance sign-in URL that returns here afterwards (TR16/TR17). */
export function entranceSignInUrl(returnTo?: string): string {
  const target = returnTo ?? (typeof window !== 'undefined' ? window.location.href : undefined);
  return target ? `${FORKHATRI_ENTRANCE_URL}/?return_to=${encodeURIComponent(target)}` : `${FORKHATRI_ENTRANCE_URL}/`;
}

/** Full-page navigation to the ForKhatri entrance (sign in, then come back). */
export function goToEntrance(returnTo?: string): void {
  window.location.assign(entranceSignInUrl(returnTo));
}

/** The ForKhatri account area, where account deletion is orchestrated for every module at once. */
export const FORKHATRI_ACCOUNT_URL = `${FORKHATRI_ENTRANCE_URL}/account`;

/** Revoke the ForKhatri session (every module signs out together), then go to the entrance. */
export async function signOutOfForKhatri(): Promise<void> {
  try {
    await fetch(`${IDENTITY_API}/v1/auth/sign-out`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ everywhere: false }),
    });
  } catch { /* the entrance shows the true session state either way */ }
  window.location.assign(`${FORKHATRI_ENTRANCE_URL}/`);
}

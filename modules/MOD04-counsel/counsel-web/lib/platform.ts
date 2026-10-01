/* ForKhatri platform edges. Counsel never signs anyone in. */
export const IDENTITY_API = process.env.NEXT_PUBLIC_IDENTITY_API ?? "http://localhost:8100";
export const FORKHATRI_ENTRANCE_URL = process.env.NEXT_PUBLIC_FORKHATRI_ENTRANCE_URL ?? "http://localhost:3100";

export function entranceSignInUrl(returnTo?: string): string {
  const target = returnTo ?? (typeof window !== "undefined" ? window.location.href : undefined);
  return target ? `${FORKHATRI_ENTRANCE_URL}/?return_to=${encodeURIComponent(target)}` : `${FORKHATRI_ENTRANCE_URL}/`;
}

export function goToEntrance(returnTo?: string): void {
  window.location.assign(entranceSignInUrl(returnTo));
}

export async function signOutOfForKhatri(): Promise<void> {
  try {
    await fetch(`${IDENTITY_API}/v1/auth/sign-out`, {
      method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ everywhere: false }),
    });
  } catch { /* the entrance shows the true state */ }
  window.location.assign(`${FORKHATRI_ENTRANCE_URL}/`);
}

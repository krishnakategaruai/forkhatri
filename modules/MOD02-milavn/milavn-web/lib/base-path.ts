/* [ForKhatri TR22, deployment kit 2026-09-14] Milavn runs as a Next.js zone under
 * `/milavn` on the one ForKhatri origin in production, and at the root of
 * :3001 in development (NEXT_PUBLIC_BASE_PATH unset).
 *
 * `next/link` and `router.push` add the base path themselves. Everything that
 * leaves the Next router does not, and must go through these helpers:
 * `<img src>` for files in `public/`, share links, QR codes, calendar files,
 * and `return_to` URLs. */

export const BASE_PATH = (process.env.NEXT_PUBLIC_BASE_PATH ?? '').replace(/\/+$/, '');

/** `/assets/x.jpg` → `/milavn/assets/x.jpg` in production. */
export function withBasePath(path: string): string {
  return path.startsWith('/') ? `${BASE_PATH}${path}` : path;
}

/** Absolute URL of a Milavn page on the current origin (browser only). */
export function appUrl(path: string): string {
  return `${window.location.origin}${withBasePath(path)}`;
}

'use client';

import { useSyncExternalStore } from 'react';

/* Breakpoints (contract §5): md ≥768, lg ≥1024. CSS does the layout; this
 * hook exists only for the few decisions markup cannot make on its own
 * (which route a conversation link points at, whether a sheet or a section
 * hosts the settings). The server snapshot is `false`, so the phone layout
 * renders first and the desktop one takes over on hydration. */

export const LG = '(min-width: 1024px)';
export const MD = '(min-width: 768px)';

export function useMediaQuery(queryString: string): boolean {
  return useSyncExternalStore(
    (onChange) => {
      const mql = window.matchMedia(queryString);
      mql.addEventListener('change', onChange);
      return () => mql.removeEventListener('change', onChange);
    },
    () => window.matchMedia(queryString).matches,
    () => false
  );
}

export function useIsDesktop(): boolean {
  return useMediaQuery(LG);
}

/* Appearance preference: light / dark / system.
 *
 * `globals.css` already defines a complete dark palette two ways — a
 * `prefers-color-scheme` media query (the "system" default) and an explicit
 * `:root[data-theme='dark']` override (the same tokens, applied regardless
 * of OS preference) — but nothing in the app ever set `data-theme` or gave
 * the person a way to choose. This is that missing piece: a tiny persisted
 * preference plus the one DOM write CSS is already waiting for.
 */

export type Theme = 'light' | 'dark' | 'system';

const STORAGE_KEY = 'mangaly.theme';

export function getStoredTheme(): Theme {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === 'light' || saved === 'dark' || saved === 'system') return saved;
  } catch {
    // Private mode or blocked storage: fall through to system.
  }
  return 'system';
}

/** Writes `data-theme` on <html> — 'system' removes the attribute entirely
 * so the `prefers-color-scheme` media query in globals.css takes back over,
 * exactly the same tokens either way. */
export function applyTheme(theme: Theme): void {
  const root = document.documentElement;
  if (theme === 'system') root.removeAttribute('data-theme');
  else root.setAttribute('data-theme', theme);
}

export function setPreferredTheme(theme: Theme): void {
  try {
    localStorage.setItem(STORAGE_KEY, theme);
  } catch {
    // Non-fatal: the choice just will not survive a reload.
  }
  applyTheme(theme);
}

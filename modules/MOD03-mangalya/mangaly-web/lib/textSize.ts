/* Text size preference: standard / larger / largest (owner, 2026-09-29).
 *
 * Evidence (docs/PreStartResearch/mangaly-2030-evidence-research.md): users
 * over 65 complete 55% of tasks against 75% for younger users, and Nielsen
 * Norman Group asks for a way to enlarge text. Parents in South India make
 * nearly half the profiles, so Mangalya offers the control to everyone and
 * never switches it on by age. The whole interface is set in rem, so one
 * root size scales every screen. */

export type TextSize = 'standard' | 'larger' | 'largest';

export const TEXT_SIZES: TextSize[] = ['standard', 'larger', 'largest'];

const STORAGE_KEY = 'mangaly.textSize';

export function getStoredTextSize(): TextSize {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === 'larger' || saved === 'largest') return saved;
  } catch {
    // Private mode or blocked storage: standard.
  }
  return 'standard';
}

export function applyTextSize(size: TextSize): void {
  const root = document.documentElement;
  if (size === 'standard') root.removeAttribute('data-text-size');
  else root.setAttribute('data-text-size', size);
}

export function setPreferredTextSize(size: TextSize): void {
  try {
    localStorage.setItem(STORAGE_KEY, size);
  } catch {
    // Non-fatal: the choice just will not survive a reload.
  }
  applyTextSize(size);
}

/* Appearance (UX17): System / Light / Dark.
 *
 * The stylesheet has one dark theme, keyed on `<html data-theme="dark">`, so
 * the attribute always carries the *resolved* theme. "System" is stored as no
 * saved choice and resolved from the device's prefers-color-scheme, including
 * when the device switches while Milavn is open. */

export type ThemeChoice = 'system' | 'light' | 'dark';

const THEME_KEY = 'milavn.theme';
const DARK_QUERY = '(prefers-color-scheme: dark)';

/** Runs inline in <head> before first paint, so no screen flashes the wrong theme. Keep in step with applyTheme. */
export const THEME_BOOT_SCRIPT = `try{var t=localStorage.getItem('${THEME_KEY}');if(t!=='light'&&t!=='dark')t=matchMedia('${DARK_QUERY}').matches?'dark':'light';document.documentElement.dataset.theme=t}catch(e){}`;

export function readThemeChoice(): ThemeChoice {
  try {
    const saved = localStorage.getItem(THEME_KEY);
    return saved === 'light' || saved === 'dark' ? saved : 'system';
  } catch {
    return 'system';
  }
}

function applyTheme(choice: ThemeChoice): void {
  const dark = choice === 'dark' || (choice === 'system' && window.matchMedia(DARK_QUERY).matches);
  document.documentElement.dataset.theme = dark ? 'dark' : 'light';
}

export function setThemeChoice(choice: ThemeChoice): void {
  try {
    if (choice === 'system') localStorage.removeItem(THEME_KEY);
    else localStorage.setItem(THEME_KEY, choice);
  } catch { /* ignore */ }
  applyTheme(choice);
}

/** While the choice is "System", follow the device when it changes (e.g. at sunset). Returns the unsubscribe. */
export function followSystemTheme(): () => void {
  const mq = window.matchMedia(DARK_QUERY);
  const onChange = () => { if (readThemeChoice() === 'system') applyTheme('system'); };
  mq.addEventListener('change', onChange);
  return () => mq.removeEventListener('change', onChange);
}

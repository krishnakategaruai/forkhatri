/**
 * Appearance (System / Light / Dark) is a device preference only: it lives in
 * localStorage and is never sent to the identity service.
 *
 * THEME_BOOT_SCRIPT runs inline in <head> before first paint. It resolves the
 * stored choice, or the OS `prefers-color-scheme` when the choice is "system",
 * into `data-theme` on <html>, so a reload never flashes the wrong theme.
 * CSS tokens: `:root` holds the light values, and `[data-theme="dark"]` overrides them.
 */
export type ThemeChoice = "system" | "light" | "dark";

export const THEME_STORAGE_KEY = "fk.theme";
export const THEME_EVENT = "fk-theme-change";
export const THEME_COLORS = { light: "#fafaf8", dark: "#0c0c0d" } as const;

export const THEME_BOOT_SCRIPT = `(function(){var d=document.documentElement,c="system";try{var s=localStorage.getItem("${THEME_STORAGE_KEY}");if(s==="light"||s==="dark")c=s}catch(e){}var dark=c==="dark"||(c==="system"&&!!window.matchMedia&&window.matchMedia("(prefers-color-scheme: dark)").matches);d.setAttribute("data-theme",dark?"dark":"light");d.setAttribute("data-theme-choice",c)})();`;

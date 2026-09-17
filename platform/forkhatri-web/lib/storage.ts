/**
 * Browser storage for non-sensitive conveniences only (TR12: never a token).
 * - the last good module registry, shown dimmed when the service is unreachable (TR05)
 * - the interface language chosen while signed out
 * Every access is guarded: private windows and blocked storage must not break the page.
 */
import type { Lang, ModuleEntry } from "./api";

const REGISTRY_KEY = "fk.registry.v1";
const LANG_KEY = "fk.lang";

export function loadCachedRegistry(): ModuleEntry[] | null {
  try {
    const parsed = JSON.parse(localStorage.getItem(REGISTRY_KEY) ?? "null") as { modules?: unknown } | null;
    return Array.isArray(parsed?.modules) ? (parsed.modules as ModuleEntry[]) : null;
  } catch {
    return null;
  }
}

export function saveCachedRegistry(modules: ModuleEntry[]) {
  try {
    // Strip per-member data: only the public registry shape is cached.
    const safe = modules.map((module) => ({ ...module, last_entered_at: null }));
    localStorage.setItem(REGISTRY_KEY, JSON.stringify({ modules: safe, saved_at: Date.now() }));
  } catch {
    // Ignore quota / blocked storage.
  }
}

export function loadStoredLang(): Lang | null {
  try {
    const value = localStorage.getItem(LANG_KEY);
    return value === "en" || value === "hi" || value === "te" ? value : null;
  } catch {
    return null;
  }
}

export function saveStoredLang(lang: Lang) {
  try {
    localStorage.setItem(LANG_KEY, lang);
  } catch {
    // Ignore.
  }
}

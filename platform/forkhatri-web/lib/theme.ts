"use client";

/** Client side of the Appearance preference (see lib/theme-script.ts). Device-only, never sent to the server. */
import { useCallback, useEffect, useSyncExternalStore } from "react";
import { THEME_COLORS, THEME_EVENT, THEME_STORAGE_KEY, type ThemeChoice } from "./theme-script";

const DARK_QUERY = "(prefers-color-scheme: dark)";

export function readThemeChoice(): ThemeChoice {
  try {
    const value = localStorage.getItem(THEME_STORAGE_KEY);
    return value === "light" || value === "dark" ? value : "system";
  } catch {
    return "system";
  }
}

function saveThemeChoice(choice: ThemeChoice) {
  try {
    if (choice === "system") localStorage.removeItem(THEME_STORAGE_KEY);
    else localStorage.setItem(THEME_STORAGE_KEY, choice);
  } catch {
    // Storage blocked: the choice still applies for this page view.
  }
}

/** Resolves a choice into `data-theme`, keeps the browser theme-color in step, and notifies listeners. */
export function applyTheme(choice: ThemeChoice) {
  const root = document.documentElement;
  const dark = choice === "dark" || (choice === "system" && window.matchMedia(DARK_QUERY).matches);
  root.setAttribute("data-theme", dark ? "dark" : "light");
  root.setAttribute("data-theme-choice", choice);
  for (const meta of document.querySelectorAll<HTMLMetaElement>('meta[name="theme-color"]')) {
    meta.content = dark ? THEME_COLORS.dark : THEME_COLORS.light;
  }
  window.dispatchEvent(new Event(THEME_EVENT));
}

function subscribe(onChange: () => void) {
  window.addEventListener(THEME_EVENT, onChange);
  return () => window.removeEventListener(THEME_EVENT, onChange);
}

function snapshot(): ThemeChoice {
  const value = document.documentElement.getAttribute("data-theme-choice");
  return value === "light" || value === "dark" ? value : "system";
}

export function useThemeChoice(): [ThemeChoice, (choice: ThemeChoice) => void] {
  const choice = useSyncExternalStore(subscribe, snapshot, () => "system" as ThemeChoice);
  const setChoice = useCallback((next: ThemeChoice) => {
    saveThemeChoice(next);
    applyTheme(next);
  }, []);
  return [choice, setChoice];
}

/** Mounted once: follows OS changes while the choice is "system", and choices made in other tabs. */
export function useThemeSync() {
  useEffect(() => {
    const media = window.matchMedia(DARK_QUERY);
    const sync = () => applyTheme(readThemeChoice());
    const onStorage = (event: StorageEvent) => {
      if (event.key === THEME_STORAGE_KEY) sync();
    };
    sync();
    media.addEventListener("change", sync);
    window.addEventListener("storage", onStorage);
    return () => {
      media.removeEventListener("change", sync);
      window.removeEventListener("storage", onStorage);
    };
  }, []);
}

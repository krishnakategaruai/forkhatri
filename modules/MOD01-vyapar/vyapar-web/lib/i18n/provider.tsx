"use client";

// [Product-owner standing i18n rule] Wraps the app so every component can
// reach `useTranslation()`. Mirrors MOD03 Mangaly's provider.tsx pattern
// (read, not edited) — same resolution order (saved choice, then device
// locale, then English) — plus one addition Vyapar needs that Mangaly's
// snippet didn't show: syncing the choice to the member's own row
// (`vyapar_identity.members.language`, already modeled and already used
// by first-run) so the preference survives across devices, not just this
// browser's localStorage.
import { useEffect, useState } from "react";
import { I18nextProvider } from "react-i18next";
import { DEFAULT_LANGUAGE, type Language, getI18n, isSupported } from "./config";

const STORAGE_KEY = "vyapar.language";

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [i18n] = useState(() => getI18n(DEFAULT_LANGUAGE));

  useEffect(() => {
    let next: Language = DEFAULT_LANGUAGE;
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (isSupported(saved)) {
        next = saved;
      } else {
        const device = navigator.language?.split("-")[0];
        if (isSupported(device)) next = device;
      }
    } catch {
      // Private mode or blocked storage: fall through to English rather
      // than failing to render.
    }
    if (i18n.language !== next) void i18n.changeLanguage(next);
    document.documentElement.lang = next;
  }, [i18n]);

  return <I18nextProvider i18n={i18n}>{children}</I18nextProvider>;
}

export function setPreferredLanguage(lang: Language): void {
  try {
    localStorage.setItem(STORAGE_KEY, lang);
  } catch {
    // Non-fatal: the choice just won't survive a reload on this device.
  }
  document.documentElement.lang = lang;
  // Best-effort sync to the member's own row — the backend is the source
  // of truth for the next device/session; localStorage is the same-device
  // fast path. Failure here must never block the visible language switch.
  import("@/lib/api").then(({ api }) => {
    api.patch("/v1/members/me/language", { language: lang }).catch(() => {});
  });
}

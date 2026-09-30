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
import { DEFAULT_LANGUAGE, LANGUAGE_COOKIE, type Language, getI18n, isSupported } from "./config";

const STORAGE_KEY = "vyapar.language";

/** Optional host platform (ForKhatri) identity service; unset = standalone Vyapar. */
const HOST_IDENTITY_API = (process.env.NEXT_PUBLIC_HOST_IDENTITY_API ?? "").replace(/\/+$/, "");

async function hostLanguage(): Promise<Language | null> {
  try {
    const res = await fetch(`${HOST_IDENTITY_API}/v1/session`, { credentials: "include", cache: "no-store" });
    if (!res.ok) return null;
    const body = (await res.json()) as { member?: { preferred_language?: string } };
    const lang = body.member?.preferred_language;
    return isSupported(lang) ? lang : null;
  } catch {
    return null;
  }
}

function writeLanguageCookie(lang: Language) {
  document.cookie = `${LANGUAGE_COOKIE}=${lang}; path=/; max-age=31536000; samesite=lax`;
}

// [Critique N10] `initialLanguage` comes from the language cookie, read by
// the server layout, so server and first client render agree; the effect
// below only corrects a first visit (no cookie yet) and keeps the cookie
// in step with localStorage and the host account.
export function I18nProvider({ children, initialLanguage = DEFAULT_LANGUAGE }: { children: React.ReactNode; initialLanguage?: Language }) {
  const [i18n] = useState(() => getI18n(initialLanguage));

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
    writeLanguageCookie(next);

    // [Owner, 2026-09-27] Hosted in ForKhatri, the language chosen there is
    // the person's language here too. Vyapar stays host-independent: this runs
    // only when a host identity URL is configured, and reads the host
    // account's language on open and whenever the tab comes back into view.
    if (!HOST_IDENTITY_API) return;
    let alive = true;
    const sync = async () => {
      const lang = await hostLanguage();
      if (!alive || !lang || lang === i18n.language) return;
      void i18n.changeLanguage(lang);
      document.documentElement.lang = lang;
      writeLanguageCookie(lang);
      try {
        localStorage.setItem(STORAGE_KEY, lang);
      } catch {
        // Non-fatal.
      }
    };
    void sync();
    const onVisible = () => {
      if (document.visibilityState === "visible") void sync();
    };
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      alive = false;
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [i18n]);

  return <I18nextProvider i18n={i18n}>{children}</I18nextProvider>;
}

export function setPreferredLanguage(lang: Language): void {
  try {
    localStorage.setItem(STORAGE_KEY, lang);
  } catch {
    // Non-fatal: the choice just won't survive a reload on this device.
  }
  writeLanguageCookie(lang);
  document.documentElement.lang = lang;
  // Best-effort sync to the member's own row — the backend is the source
  // of truth for the next device/session; localStorage is the same-device
  // fast path. Failure here must never block the visible language switch.
  import("@/lib/sdk/default").then(({ defaultSdk }) => {
    defaultSdk.members.setLanguage(lang).catch(() => {});
  });
  // Hosted in ForKhatri: the choice is also the person's ForKhatri language.
  if (HOST_IDENTITY_API) {
    void fetch(`${HOST_IDENTITY_API}/v1/me`, {
      method: "PATCH",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ preferred_language: lang }),
    }).catch(() => {});
  }
}

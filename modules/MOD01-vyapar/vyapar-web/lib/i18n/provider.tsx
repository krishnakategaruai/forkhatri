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
import { DEFAULT_LANGUAGE, LANGUAGE_COOKIE, type Language, createI18n, getI18n, isSupported } from "./config";

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

function readLanguageCookie(): Language | null {
  const m = document.cookie.match(new RegExp(`(?:^|; )${LANGUAGE_COOKIE}=([^;]*)`));
  const v = m ? decodeURIComponent(m[1]) : null;
  return isSupported(v) ? v : null;
}

/** The language the server rendered this page in (<html lang>, set from the cookie by the root layout). */
function serverLanguage(fallback: Language): Language {
  if (typeof document === "undefined") return fallback;
  const lang = document.documentElement.lang;
  return isSupported(lang) ? lang : fallback;
}

// [Critique N10 → 2026-09-30, coordinator: "make the mismatch impossible"]
// The first client render ALWAYS uses the language the server rendered
// (<html lang>, which the layout set from the `vyapar_lang` cookie), never
// localStorage, so hydration can't disagree with the HTML. Only after
// hydration does the effect reconcile:
//   - a cookie exists: it is the truth (the server used it); localStorage is
//     brought in step, nothing on screen changes;
//   - no cookie (a first visit, or a member who chose Hindi or Telugu before
//     the cookie existed): the saved choice, else the device language, is
//     written to the cookie and switched to — an ordinary state change after
//     hydration, not a mismatch. The next load is server-rendered in that
//     language, so it happens once.
// The switch is a NEW i18n instance given to the provider (React state),
// never `changeLanguage` on the instance the page hydrated with: an effect
// can run while a lower Suspense boundary (the composer, for one) is still
// hydrating, and mutating the shared instance made that boundary render the
// new language against the server's HTML. A context change instead makes
// React finish hydrating the boundary with the old value first (selective
// hydration), then re-render it in the new language.
export function I18nProvider({ children, initialLanguage = DEFAULT_LANGUAGE }: { children: React.ReactNode; initialLanguage?: Language }) {
  const [i18n, setI18n] = useState(() => getI18n(serverLanguage(initialLanguage)));

  useEffect(() => {
    const rendered = serverLanguage(initialLanguage);
    let saved: Language | null = null;
    try {
      const v = localStorage.getItem(STORAGE_KEY);
      saved = isSupported(v) ? v : null;
    } catch {
      // Private mode or blocked storage: the server's language stands.
    }
    const cookie = readLanguageCookie();
    let next: Language = rendered;
    if (cookie) {
      next = cookie;
    } else {
      const device = navigator.language?.split("-")[0];
      next = saved ?? (isSupported(device) ? device : rendered);
      writeLanguageCookie(next);
    }
    try {
      if (saved !== next) localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // Non-fatal.
    }
    if (next !== i18n.language) {
      // After hydration only, and as a new instance (see above).
      document.documentElement.lang = next;
      // Deliberately a state change after hydration (never during render).
      queueMicrotask(() => setI18n(createI18n(next)));
      return;
    }

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
    // Runs once, after hydration; the language it reconciles is read inside.
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

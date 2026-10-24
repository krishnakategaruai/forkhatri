// [IMP38 — Refactor C] The web app's own SDK instance, configured from env.
//
//   NEXT_PUBLIC_API_URL       API origin (default http://localhost:8011)
//   NEXT_PUBLIC_VYAPAR_AUTH   "dev" | "cookie"  — how the browser proves who
//                             it is. Unset: the host decides (the ForKhatri
//                             host uses the development header today, a
//                             standalone deployment uses its session cookie).
//
// A bearer token is deliberately NOT configurable through NEXT_PUBLIC_* env:
// that would publish the credential in the JavaScript bundle. Hosts and
// embedders that hold a token build their own instance with
// createVyaparSdk({ auth: bearerTokenAuth(() => token) }).
import { createVyaparSdk, type VyaparSdk } from "./index";
import { cookieSessionAuth, devHeaderAuth, type AuthStrategy } from "./auth";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8011";
export const LANGUAGE_STORAGE_KEY = "vyapar.language";

/** The language on screen, as the i18n provider saved it. */
export function storedLanguage(): string {
  if (typeof window === "undefined") return "en";
  try {
    // The cookie is the language the page was rendered in (and the provider
    // keeps it in step), so API labels match the screen from the first call.
    const cookie = document.cookie.match(/(?:^|; )vyapar_lang=([^;]*)/)?.[1];
    if (cookie === "en" || cookie === "hi" || cookie === "te" || cookie === "mr" || cookie === "kn") return cookie;
    return window.localStorage.getItem(LANGUAGE_STORAGE_KEY) ?? "en";
  } catch {
    return "en";
  }
}

export type AuthMode = "dev" | "cookie";

export function authFromMode(mode: AuthMode): AuthStrategy {
  return mode === "cookie" ? cookieSessionAuth() : devHeaderAuth();
}

function hostDefaultAuthMode(): AuthMode {
  // Mirrors app/host's selection without importing React code into the SDK.
  return process.env.NEXT_PUBLIC_VYAPAR_HOST === "standalone" ? "cookie" : "dev";
}

export function configuredAuthMode(): AuthMode {
  const explicit = process.env.NEXT_PUBLIC_VYAPAR_AUTH;
  if (explicit === "dev" || explicit === "cookie") return explicit;
  return hostDefaultAuthMode();
}

export const defaultSdk: VyaparSdk = createVyaparSdk({
  baseUrl: API_URL,
  auth: authFromMode(configuredAuthMode()),
  language: storedLanguage,
});

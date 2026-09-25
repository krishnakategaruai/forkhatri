"use client";

// [IMP38 — Refactor C] Everything an embedded Vyapar surface needs, in one
// wrapper: the SDK instance to call through, the host config (routes,
// brand, bell source) and Vyapar's own translations (en / hi / te), driven
// by the `language` the embedding app passes. Changing `language` updates
// every label live, and the embedded data hooks re-fetch so server-side
// labels follow too.
import { useEffect, useState } from "react";
import { I18nextProvider } from "react-i18next";
import type { VyaparSdk } from "@/lib/sdk";
import { VyaparSdkProvider } from "@/lib/sdk/react";
import { HostProvider, selectHost } from "@/app/host/HostProvider";
import type { HostConfig } from "@/app/host/types";
import { DEFAULT_LANGUAGE, getI18n, isSupported } from "@/lib/i18n/config";

export interface VyaparEmbedProviderProps {
  sdk: VyaparSdk;
  /** Host config; defaults to the standalone host (neutral brand, no dev tools). */
  host?: HostConfig;
  /** "en" | "hi" | "te". Defaults to English. */
  language?: string;
  children: React.ReactNode;
}

export default function VyaparEmbedProvider({ sdk, host, language = DEFAULT_LANGUAGE, children }: VyaparEmbedProviderProps) {
  const [i18n] = useState(() => getI18n(isSupported(language) ? language : DEFAULT_LANGUAGE));
  useEffect(() => {
    const next = isSupported(language) ? language : DEFAULT_LANGUAGE;
    if (i18n.language !== next) void i18n.changeLanguage(next);
  }, [i18n, language]);

  return (
    <HostProvider host={host ?? selectHost("standalone")}>
      <VyaparSdkProvider sdk={sdk}>
        <I18nextProvider i18n={i18n}>{children}</I18nextProvider>
      </VyaparSdkProvider>
    </HostProvider>
  );
}

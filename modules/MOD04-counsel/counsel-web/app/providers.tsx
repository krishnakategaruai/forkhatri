"use client";

import { I18nProvider } from "@/lib/i18n/provider";
import { IdentityProvider } from "@/lib/identity";
import { ToastProvider } from "@/components/ui";
import { useEffect } from "react";

export function Providers({ children }: { children: React.ReactNode }) {
  // Appearance chosen on the You screen (system / light / dark).
  useEffect(() => {
    try {
      const v = localStorage.getItem("counsel.theme");
      if (v === "light" || v === "dark") document.documentElement.dataset.theme = v;
    } catch { /* ignore */ }
  }, []);
  return (
    <I18nProvider>
      <IdentityProvider>
        <ToastProvider>{children}</ToastProvider>
      </IdentityProvider>
    </I18nProvider>
  );
}

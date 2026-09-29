// [Cross-cutting] Root layout — mounts the design system fonts (Noto Sans/
// Devanagari/Telugu per 04-ui.md's i18n requirement, kept even though the
// visual tokens themselves were overridden by the design direction), the
// floating CommandHub (replaces the bottom tab bar), the dev member
// switcher, and (per the product-owner's standing multilingual rule) the
// i18n provider + language switcher — English/Hindi/Telugu, reachable from
// every screen without a sign-in form. No login/signup UI here or anywhere
// else in this module — FR50.
// Traces to: FR42 (i18n typography), FR44/FR50 (no auth screens), Design
// direction, product-owner i18n rule (2026-09-15, not a numbered FR)
import type { Metadata } from "next";
import { Noto_Sans, Noto_Sans_Devanagari, Noto_Sans_Telugu } from "next/font/google";
import "./globals.css";
// [FE2] contact, packages, filters, contracts, badges, Hire/Find work menu
import "./styles/fe2.css";
// [FE1] composer, response composers, applicants board, voice input, picker
import "./hiring.css";
// [Design language 2026-09-29] the 2026 language on every shared class; loaded last so it wins
import "./styles/language-2026.css";
import "./styles/discover-2026.css";
import CommandHub from "./components/CommandHub";
import AppTopBar from "./components/nav/AppTopBar";
import { I18nProvider } from "@/lib/i18n/provider";
// [IMP38 — Refactor C] The host adapter owns the platform-specific shell
// pieces (account control, bell source, brand, platform link); the layout
// only decides WHERE they go. NEXT_PUBLIC_VYAPAR_HOST selects the host.
import { HostProvider } from "./host/HostProvider";
import { hostMetadata } from "./host/meta";
import { DISPLAY_BOOT_SCRIPT } from "@/lib/display";

const notoSans = Noto_Sans({ subsets: ["latin"], variable: "--font-noto-sans" });
const notoDevanagari = Noto_Sans_Devanagari({ subsets: ["devanagari"], variable: "--font-noto-deva" });
const notoTelugu = Noto_Sans_Telugu({ subsets: ["telugu"], variable: "--font-noto-telugu" });

export const metadata: Metadata = {
  title: hostMetadata.title,
  description: hostMetadata.description,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${notoSans.variable} ${notoDevanagari.variable} ${notoTelugu.variable}`} suppressHydrationWarning>
      <head>
        {/* Text size and high contrast before first paint (lib/display.ts). */}
        <script dangerouslySetInnerHTML={{ __html: DISPLAY_BOOT_SCRIPT }} />
      </head>
      <body>
        <HostProvider>
        <I18nProvider>
          {/* [Design language 2026-09-29] One real header replaces the
              floating language / Hire / alerts / account pills and the
              scrim behind them: wordmark, Hire / Find work, the search
              pill, language & display, bell, avatar (right-most). The
              lesson of the old overlap bug still holds — every control
              lives in ONE flex row, none guesses another's width. */}
          <AppTopBar />
          {children}
          <CommandHub />
        </I18nProvider>
        </HostProvider>
      </body>
    </html>
  );
}

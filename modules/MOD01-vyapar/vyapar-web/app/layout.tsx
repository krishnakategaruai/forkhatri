// [Cross-cutting] Root layout — mounts the design system fonts, the
// floating CommandHub (replaces the bottom tab bar), the dev member
// switcher, and (per the product-owner's standing multilingual rule) the
// i18n provider + language switcher — English/Hindi/Telugu, reachable from
// every screen without a sign-in form. No login/signup UI here or anywhere
// else in this module — FR50.
//
// [Typography 2026-09-29 (premium)] Owner: "see the fonts also… i wanted
// this to be a premium website for vyapar, but this looks ugly." Noto Sans
// (chosen only for script coverage) is replaced by Ek Type's Anek: one
// family whose Latin, Devanagari and Telugu were drawn together (Google
// Design, "Design for Many"), so the Hindi and Telugu screens look as
// designed as the English one instead of falling back. Variable weight
// 100–800 in one file per script; Latin is preloaded, the Indic files are
// declared with unicode-range and fetched only when their script is on
// screen (a budget Android on English pays for one font, not three).
// references/design-language-2026-09-29.md, "Typography 2026-09-29".
// Traces to: FR42 (i18n typography), FR44/FR50 (no auth screens), Design
// direction, product-owner i18n rule (2026-09-15, not a numbered FR)
import type { Metadata } from "next";
import { Anek_Latin, Anek_Devanagari, Anek_Telugu } from "next/font/google";
import "./globals.css";
// [FE2] contact, packages, filters, contracts, badges, Hire/Find work menu
import "./styles/fe2.css";
// [FE1] composer, response composers, applicants board, voice input, picker
import "./hiring.css";
// [Design language 2026-09-29] the 2026 language on every shared class; loaded last so it wins
import "./styles/language-2026.css";
import "./styles/discover-2026.css";
// [2026-09-30] filter dropdown bar + panels (portalled to <body>), cards, Businesses, top-bar host link
import "./styles/filters-2026.css";
import CommandHub from "./components/CommandHub";
import AppTopBar from "./components/nav/AppTopBar";
import { I18nProvider } from "@/lib/i18n/provider";
// [IMP38 — Refactor C] The host adapter owns the platform-specific shell
// pieces (account control, bell source, brand, platform link); the layout
// only decides WHERE they go. NEXT_PUBLIC_VYAPAR_HOST selects the host.
import { HostProvider } from "./host/HostProvider";
import { hostMetadata } from "./host/meta";
import { DISPLAY_BOOT_SCRIPT } from "@/lib/display";

// Weight axis only (no width axis): keeps each file small for the budget
// Android that is our baseline. Display contrast comes from weight and
// tracking (globals.css type tokens), not from a second axis.
const anekLatin = Anek_Latin({ subsets: ["latin"], display: "swap", variable: "--font-anek-latin" });
const anekDevanagari = Anek_Devanagari({ subsets: ["devanagari"], display: "swap", preload: false, variable: "--font-anek-deva" });
const anekTelugu = Anek_Telugu({ subsets: ["telugu"], display: "swap", preload: false, variable: "--font-anek-telugu" });

export const metadata: Metadata = {
  title: hostMetadata.title,
  description: hostMetadata.description,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${anekLatin.variable} ${anekDevanagari.variable} ${anekTelugu.variable}`} suppressHydrationWarning>
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

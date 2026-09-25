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
import CommandHub from "./components/CommandHub";
import LanguageSwitcher from "./components/LanguageSwitcher";
import { I18nProvider } from "@/lib/i18n/provider";
// [IMP38 — Refactor C] The host adapter owns the platform-specific shell
// pieces (account control, bell source, brand, platform link); the layout
// only decides WHERE they go. NEXT_PUBLIC_VYAPAR_HOST selects the host.
import { HostProvider } from "./host/HostProvider";
import HostTopBar from "./host/HostTopBar";
import { hostMetadata } from "./host/meta";

const notoSans = Noto_Sans({ subsets: ["latin"], variable: "--font-noto-sans" });
const notoDevanagari = Noto_Sans_Devanagari({ subsets: ["devanagari"], variable: "--font-noto-deva" });
const notoTelugu = Noto_Sans_Telugu({ subsets: ["telugu"], variable: "--font-noto-telugu" });

export const metadata: Metadata = {
  title: hostMetadata.title,
  description: hostMetadata.description,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${notoSans.variable} ${notoDevanagari.variable} ${notoTelugu.variable}`}>
      <body>
        <HostProvider>
        <I18nProvider>
          <LanguageSwitcher />
          {/* [Real bug found live by the product owner — "Alerts and name
              is being missed up in UI"] NotificationBell and
              DevMemberSwitcher used to be two INDEPENDENT `position: fixed`
              elements, each with a hand-guessed `right` offset that assumed
              the other's exact pixel width — NotificationBell was
              hardcoded at `right: 168` on the assumption DevMemberSwitcher
              is always ~154px wide. Any member with a longer display name
              (or an unread count reaching two digits) breaks that
              assumption and the two elements overlap. Fixed by giving them
              ONE shared fixed-position flex container instead — real
              flexbox layout, gap-based spacing, `min-width: 0` on the name
              pill so it can never force the row wider than the viewport;
              neither child guesses the other's size anymore. */}
          {/* The language / alerts / account pills float over the page; this
              scrim sits behind them so scrolled content fades out under the
              pills instead of showing through between them. */}
          <div className="vy-topbar-scrim" aria-hidden="true" />
          {/* [IMP38] That shared flex row now lives in host/HostTopBar.tsx,
              which renders the bell and the host's account control (the
              development member switcher on ForKhatri) inside it. */}
          <HostTopBar />
          {children}
          <CommandHub />
        </I18nProvider>
        </HostProvider>
      </body>
    </html>
  );
}

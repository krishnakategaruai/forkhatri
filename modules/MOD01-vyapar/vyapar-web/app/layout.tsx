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
import DevMemberSwitcher from "./components/DevMemberSwitcher";
import LanguageSwitcher from "./components/LanguageSwitcher";
import NotificationBell from "./components/NotificationBell";
import { I18nProvider } from "@/lib/i18n/provider";

const notoSans = Noto_Sans({ subsets: ["latin"], variable: "--font-noto-sans" });
const notoDevanagari = Noto_Sans_Devanagari({ subsets: ["devanagari"], variable: "--font-noto-deva" });
const notoTelugu = Noto_Sans_Telugu({ subsets: ["telugu"], variable: "--font-noto-telugu" });

export const metadata: Metadata = {
  title: "Vyapar — ForKhatri",
  description: "Business, professional and opportunity discovery for the Khatri community.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${notoSans.variable} ${notoDevanagari.variable} ${notoTelugu.variable}`}>
      <body>
        <I18nProvider>
          <LanguageSwitcher />
          <NotificationBell />
          <DevMemberSwitcher />
          {children}
          <CommandHub />
        </I18nProvider>
      </body>
    </html>
  );
}

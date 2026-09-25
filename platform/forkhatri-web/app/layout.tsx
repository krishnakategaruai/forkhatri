import type { Metadata, Viewport } from "next";
import { Geist, Noto_Sans_Devanagari, Noto_Sans_Telugu, Sora } from "next/font/google";
import { SPLASH_BOOT_SCRIPT, SPLASH_IMAGE } from "@/lib/splash-script";
import { THEME_BOOT_SCRIPT, THEME_COLORS } from "@/lib/theme-script";
import "./globals.css";
import "./arrival.css";
import "./hub.css";
import "./splash.css";

// Latin UI face + a variable display face, with Noto faces that render
// Devanagari and Telugu properly. The browser picks per glyph from the stack.
const geist = Geist({ subsets: ["latin"], variable: "--font-geist", display: "swap" });
const sora = Sora({ subsets: ["latin"], variable: "--font-sora", display: "swap" });
const devanagari = Noto_Sans_Devanagari({ subsets: ["devanagari"], variable: "--font-deva", display: "swap" });
const telugu = Noto_Sans_Telugu({ subsets: ["telugu"], variable: "--font-telugu", display: "swap" });

export const metadata: Metadata = {
  title: "ForKhatri",
  description: "One trusted ForKhatri account for your community, opportunities, support and growth.",
  applicationName: "ForKhatri",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  colorScheme: "light dark",
  // System default; an explicit Appearance choice rewrites both tags on the client (lib/theme.ts).
  themeColor: [
    { media: "(prefers-color-scheme: dark)", color: THEME_COLORS.dark },
    { media: "(prefers-color-scheme: light)", color: THEME_COLORS.light },
  ],
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    // `lang` is updated on the client once the member's language is known.
    <html lang="en" suppressHydrationWarning className={`${geist.variable} ${sora.variable} ${devanagari.variable} ${telugu.variable}`}>
      <head>
        {/* Sets data-theme before first paint so a reload never flashes the wrong appearance. */}
        <script dangerouslySetInnerHTML={{ __html: THEME_BOOT_SCRIPT }} />
        {/* Hides the first-load splash before paint when this tab has already seen it. */}
        <script dangerouslySetInnerHTML={{ __html: SPLASH_BOOT_SCRIPT }} />
        <link rel="preload" as="image" type="image/webp" href={SPLASH_IMAGE.src} fetchPriority="high" />
      </head>
      <body>{children}</body>
    </html>
  );
}

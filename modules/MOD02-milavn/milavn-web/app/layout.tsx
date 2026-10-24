import type { Metadata, Viewport } from 'next';
import { Anek_Devanagari, Anek_Kannada, Anek_Latin, Anek_Telugu, Fraunces } from 'next/font/google';
import './globals.css';
import AppChrome from '@/components/AppChrome';
import { IdentityProvider } from '@/lib/identity';
import { I18nProvider } from '@/lib/i18n/provider';
import { THEME_BOOT_SCRIPT } from '@/lib/theme';

// 04-ui.md Design System Foundation: Anek is one multiscript system for
// Latin, Devanagari (Hindi and Marathi), Telugu and Kannada — not a Latin face with bolted-on fallbacks.
const anek = Anek_Latin({ subsets: ['latin'], variable: '--font-anek', display: 'swap' });
const anekDev = Anek_Devanagari({ subsets: ['devanagari'], variable: '--font-anek-dev', display: 'swap' });
const anekTe = Anek_Telugu({ subsets: ['telugu'], variable: '--font-anek-te', display: 'swap' });
const anekKn = Anek_Kannada({ subsets: ['kannada'], variable: '--font-anek-kn', display: 'swap' });
// Editorial display face for headlines and poster titles (Latin); Anek carries body and the Indian scripts.
const fraunces = Fraunces({ subsets: ['latin'], variable: '--font-fraunces', display: 'swap', axes: ['opsz', 'SOFT'] });

export const metadata: Metadata = {
  title: 'Milavn',
  description: 'Milavn — what’s happening around you. Real-world activities, circles and people near you. Part of ForKhatri.',
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  viewportFit: 'cover',
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#FBF8F3' },
    { media: '(prefers-color-scheme: dark)', color: '#0B1220' },
  ],
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${anek.variable} ${anekDev.variable} ${anekTe.variable} ${anekKn.variable} ${fraunces.variable}`} suppressHydrationWarning>
      <head>
        {/* Appearance (UX17) is resolved before first paint; set after hydration, the launch screen flashed light, then dark. */}
        <script dangerouslySetInnerHTML={{ __html: THEME_BOOT_SCRIPT }} />
      </head>
      <body>
        <I18nProvider>
          <IdentityProvider>
            <AppChrome>{children}</AppChrome>
          </IdentityProvider>
        </I18nProvider>
      </body>
    </html>
  );
}

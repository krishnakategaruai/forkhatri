import type { Metadata, Viewport } from 'next';
import {
  Instrument_Sans,
  Instrument_Serif,
  Noto_Sans_Devanagari,
  Noto_Sans_Telugu,
  Noto_Serif_Devanagari,
  Noto_Serif_Telugu,
} from 'next/font/google';
import './globals.css';
import './sindoor.css';
import './home.css';
import './royal.css';
import './editorial.css';
import OutageGate from '@/components/OutageGate';
import AppShell from '@/components/AppShell';
import MangalySplash from '@/components/MangalySplash';
import ScreenGuard from '@/components/ScreenGuard';
import { I18nProvider } from '@/lib/i18n/provider';

/* Typography (DEC-V1-030, revised 2026-09-25: the owner found the earlier
 * serif pairing not classy, and asked for "minimalist, modern").
 *
 * Instrument Serif + Instrument Sans are a pair drawn to work together: a
 * slim, high-contrast editorial serif for names and headings — set large and
 * at its single regular weight, the way modern premium brands do — and a
 * clean, contemporary sans for everything that must be read quickly. Hindi
 * and Telugu headings keep a matching serif register (Noto Serif), and their
 * body text a clear Noto Sans. */
const displayLatin = Instrument_Serif({
  subsets: ['latin'],
  weight: ['400'],
  style: ['normal', 'italic'],
  variable: '--font-display',
  display: 'swap',
});
const displayDevanagari = Noto_Serif_Devanagari({
  subsets: ['devanagari'],
  weight: ['500', '600', '700'],
  variable: '--font-display-devanagari',
  display: 'swap',
});
const displayTelugu = Noto_Serif_Telugu({
  subsets: ['telugu'],
  weight: ['500', '600', '700'],
  variable: '--font-display-telugu',
  display: 'swap',
});
const bodyDevanagari = Noto_Sans_Devanagari({
  subsets: ['devanagari'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-body-devanagari',
  display: 'swap',
});
const bodyTelugu = Noto_Sans_Telugu({
  subsets: ['telugu'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-body-telugu',
  display: 'swap',
});
const bodyFont = Instrument_Sans({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-body',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Mangalya',
  description:
    'Mangalya — a family-involved, evidence-based matrimonial search. Part of ForKhatri.',
};

// Mobile-first: lock the layout viewport and respect device safe areas. The
// browser chrome takes the page colour of each theme (turmeric cream by day,
// kumkum night after dark).
export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  viewportFit: 'cover',
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#fff4d2' },
    { media: '(prefers-color-scheme: dark)', color: '#1a0708' },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  // suppressHydrationWarning below is scoped to this element's own
  // attributes only (React does not suppress mismatches in descendants) —
  // needed because the inline script further down intentionally sets
  // `data-theme` on the client before hydration, which the server-rendered
  // markup can never predict (it doesn't know the visitor's saved
  // preference). This is the documented fix for exactly this pattern, not a
  // blanket suppression: https://nextjs.org/docs/messages/react-hydration-error
  return (
    <html
      lang="en"
      className={`${displayLatin.variable} ${displayDevanagari.variable} ${displayTelugu.variable} ${bodyDevanagari.variable} ${bodyTelugu.variable} ${bodyFont.variable}`}
      suppressHydrationWarning
    >
      <body>
        {/* Sets `data-theme` before hydration/paint so a saved Light/Dark
            choice never flashes the wrong theme first — `lib/theme.ts`'s
            `applyTheme()` does the same write later for a live in-session
            change, this is only for the very first paint. 'system' stores
            no attribute, matching `applyTheme()`'s own convention. The same
            script marks a first visit in this tab so the splash can paint
            before hydration instead of flashing the page underneath. */}
        <script
          dangerouslySetInnerHTML={{
            __html:
              "try{var t=localStorage.getItem('mangaly.theme');if(t==='light'||t==='dark'){document.documentElement.setAttribute('data-theme',t);}}catch(e){}try{var z=localStorage.getItem('mangaly.textSize');if(z==='larger'||z==='largest'){document.documentElement.setAttribute('data-text-size',z);}}catch(e){}try{if(!sessionStorage.getItem('mangaly.splash')&&!matchMedia('(prefers-reduced-motion: reduce)').matches){document.documentElement.setAttribute('data-splash','1');}}catch(e){}",
          }}
        />
        <I18nProvider>
          <MangalySplash />
          <ScreenGuard />
          {/* AppShell emits the responsive nav markup: a rail/sidebar at
              desktop widths, a floating bar below. */}
          <AppShell>
            {/* [ForKhatri TR15/TR16] One shared "can't reach Mangalya" retry state. */}
            <OutageGate>{children}</OutageGate>
          </AppShell>
        </I18nProvider>
      </body>
    </html>
  );
}

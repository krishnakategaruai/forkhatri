import type { Metadata, Viewport } from 'next';
import { Plus_Jakarta_Sans, Space_Grotesk } from 'next/font/google';
import './globals.css';
import TabBar from '@/components/TabBar';
import { I18nProvider } from '@/lib/i18n/provider';

/* 2030-refresh: a distinctive geometric display face for headings/brand/
 * numerals (Space Grotesk — the same family of choice behind most current
 * AI-native product shells, e.g. Linear/Perplexity-adjacent work) paired
 * with a warmer, more expressive humanist body face (Plus Jakarta Sans)
 * instead of the generic OS system-font stack. Loaded as CSS variables via
 * next/font so both self-host at build time (no runtime request, no
 * layout-shift) and are scoped through globals.css rather than inlined. */
const displayFont = Space_Grotesk({
  subsets: ['latin'],
  weight: ['500', '600', '700'],
  variable: '--font-display',
  display: 'swap',
});
const bodyFont = Plus_Jakarta_Sans({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700', '800'],
  variable: '--font-body',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Mangaly',
  description:
    'Mangaly — a family-involved, evidence-based matrimonial search. Part of ForKhatri.',
};

// Mobile-first: lock the layout viewport and respect device safe areas.
export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  viewportFit: 'cover',
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#FAF7F1' },
    { media: '(prefers-color-scheme: dark)', color: '#0B1220' },
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
      className={`${displayFont.variable} ${bodyFont.variable}`}
      suppressHydrationWarning
    >
      <body>
        {/* Sets `data-theme` before hydration/paint so a saved Light/Dark
            choice never flashes the wrong theme first — `lib/theme.ts`'s
            `applyTheme()` does the same write later for a live in-session
            change, this is only for the very first paint. 'system' stores
            no attribute, matching `applyTheme()`'s own convention. */}
        <script
          dangerouslySetInnerHTML={{
            __html:
              "try{var t=localStorage.getItem('mangaly.theme');if(t==='light'||t==='dark'){document.documentElement.setAttribute('data-theme',t);}}catch(e){}",
          }}
        />
        <I18nProvider>
          <div className="shell">{children}</div>
          <TabBar />
        </I18nProvider>
      </body>
    </html>
  );
}

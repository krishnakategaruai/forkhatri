import type { Metadata, Viewport } from "next";
import { Anek_Devanagari, Anek_Latin, Anek_Telugu, Fraunces } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { Shell } from "@/components/Shell";

const fraunces = Fraunces({ subsets: ["latin"], variable: "--font-fraunces", axes: ["opsz", "SOFT"] });
const anekLatin = Anek_Latin({ subsets: ["latin"], variable: "--font-anek-latin", weight: ["400", "500", "600", "700"] });
const anekDevanagari = Anek_Devanagari({ subsets: ["devanagari"], variable: "--font-anek-devanagari", weight: ["400", "500", "600"] });
const anekTelugu = Anek_Telugu({ subsets: ["telugu"], variable: "--font-anek-telugu", weight: ["400", "500", "600"] });

export const metadata: Metadata = {
  title: "Counsel · ForKhatri",
  description: "Find someone who knows what you need. Book their time. Have a productive conversation.",
};
export const viewport: Viewport = { themeColor: "#f5f0e8", width: "device-width", initialScale: 1, viewportFit: "cover" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${fraunces.variable} ${anekLatin.variable} ${anekDevanagari.variable} ${anekTelugu.variable}`}>
        <Providers>
          <Shell>{children}</Shell>
        </Providers>
      </body>
    </html>
  );
}

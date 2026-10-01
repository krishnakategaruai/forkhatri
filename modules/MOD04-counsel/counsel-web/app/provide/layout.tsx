"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTranslation } from "react-i18next";

const TABS = [
  ["/provide", "provide.tab.overview"],
  ["/provide/bookings", "provide.tab.bookings"],
  ["/provide/profile", "provide.tab.profile"],
  ["/provide/services", "provide.tab.services"],
  ["/provide/availability", "provide.tab.availability"],
  ["/provide/earnings", "provide.tab.earnings"],
] as const;

export default function ProvideLayout({ children }: { children: React.ReactNode }) {
  const { t } = useTranslation();
  const path = usePathname();
  return (
    <div className="wrap page stack">
      <div className="stack" style={{ gap: 4 }}>
        <span className="eyebrow">{t("provide.eyebrow")}</span>
        <h1 style={{ fontSize: "clamp(1.7rem,3vw,2.3rem)" }}>{t("provide.title")}</h1>
      </div>
      <nav className="tabs" aria-label={t("provide.title")}>
        {TABS.map(([href, key]) => <Link key={href} href={href} aria-current={path === href ? "page" : undefined}>{t(key)}</Link>)}
      </nav>
      {children}
    </div>
  );
}

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTranslation } from "react-i18next";
import { useIdentity } from "@/lib/identity";

const TABS = [
  ["/admin", "admin.tab.overview"],
  ["/admin/providers", "admin.tab.providers"],
  ["/admin/expertise", "admin.tab.expertise"],
  ["/admin/reports", "admin.tab.reports"],
  ["/admin/disputes", "admin.tab.disputes"],
  ["/admin/transactions", "admin.tab.transactions"],
  ["/admin/settings", "admin.tab.settings"],
] as const;

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { t } = useTranslation();
  const path = usePathname();
  const { me, ready } = useIdentity();
  if (ready && me && !me.is_admin) return <div className="wrap page"><div className="empty"><h3>{t("admin.only")}</h3></div></div>;
  return (
    <div className="wrap page stack">
      <div className="stack" style={{ gap: 4 }}><span className="eyebrow">{t("admin.eyebrow")}</span><h1 style={{ fontSize: "clamp(1.7rem,3vw,2.3rem)" }}>{t("admin.title")}</h1></div>
      <nav className="tabs">{TABS.map(([href, key]) => <Link key={href} href={href} aria-current={path === href || (href !== "/admin" && path.startsWith(href)) ? "page" : undefined}>{t(key)}</Link>)}</nav>
      {children}
    </div>
  );
}

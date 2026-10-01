"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTranslation } from "react-i18next";
import { Bell, Bookmark, Briefcase, Calendar, Compass, Home, ShieldCheck } from "lucide-react";
import { useIdentity } from "@/lib/identity";
import { entranceSignInUrl } from "@/lib/platform";
import { Avatar } from "@/components/ui";

const PUBLIC = ["/", "/discover", "/p/", "/book/"];

export function Shell({ children }: { children: React.ReactNode }) {
  const { t } = useTranslation();
  const path = usePathname();
  const { ready, me, unavailable, reload } = useIdentity();
  const isPublic = PUBLIC.some((p) => (p === "/" ? path === "/" : path.startsWith(p)));
  const inRoom = path.startsWith("/room/");

  const nav = [
    { href: "/", label: t("nav.home"), icon: Home, exact: true },
    { href: "/discover", label: t("nav.discover"), icon: Compass },
    { href: "/bookings", label: t("nav.bookings"), icon: Calendar },
    { href: "/provide", label: t("nav.provide"), icon: Briefcase },
    ...(me?.is_admin ? [{ href: "/admin", label: t("nav.admin"), icon: ShieldCheck }] : []),
  ];
  const current = (href: string, exact?: boolean) => (exact ? path === href : path === href || path.startsWith(href + "/"));

  let body: React.ReactNode = children;
  if (ready && !me && !isPublic) {
    body = (
      <div className="wrap page">
        <div className="card card-pad stack" style={{ maxWidth: 480, margin: "40px auto", textAlign: "center" }}>
          <h2>{unavailable ? t("auth.unavailable_title") : t("auth.signin_title")}</h2>
          <p className="muted">{unavailable ? t("auth.unavailable_body") : t("auth.signin_body")}</p>
          {unavailable ? (
            <button className="btn btn-primary" onClick={() => void reload()}>{t("common.retry")}</button>
          ) : (
            <a className="btn btn-primary" href={entranceSignInUrl()}>{t("auth.signin")}</a>
          )}
        </div>
      </div>
    );
  }

  return (
    <>
      <header className="topbar">
        <div className="wrap">
          <Link href="/" className="brand" aria-label="Counsel">Counsel <small>ForKhatri</small></Link>
          {!inRoom && (
            <nav className="topnav" aria-label={t("nav.main")}>
              {nav.map((n) => (
                <Link key={n.href} href={n.href} aria-current={current(n.href, n.exact) ? "page" : undefined}>{n.label}</Link>
              ))}
            </nav>
          )}
          <div className="row" style={{ gap: 4 }}>
            {me && (
              <>
                <Link href="/saved" className="icon-btn" aria-label={t("nav.saved")}><Bookmark size={20} strokeWidth={1.6} /></Link>
                <Link href="/notifications" className="icon-btn" aria-label={t("nav.notifications")}>
                  <Bell size={20} strokeWidth={1.6} />
                  {me.unread > 0 && <span className="dot" />}
                </Link>
                <Link href="/me" aria-label={t("nav.me")} style={{ marginLeft: 4 }}><Avatar name={me.display_name} size={36} /></Link>
              </>
            )}
            {ready && !me && <a className="btn btn-primary btn-sm" href={entranceSignInUrl()}>{t("auth.signin")}</a>}
          </div>
        </div>
      </header>
      <main>{body}</main>
      {!inRoom && (
        <nav className="bottombar" aria-label={t("nav.main")}>
          {nav.slice(0, 4).map((n) => {
            const Icon = n.icon;
            return (
              <Link key={n.href} href={n.href} aria-current={current(n.href, n.exact) ? "page" : undefined}>
                <Icon size={22} strokeWidth={1.6} />
                <span>{n.label}</span>
              </Link>
            );
          })}
        </nav>
      )}
    </>
  );
}

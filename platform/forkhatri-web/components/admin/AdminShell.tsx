"use client";

/**
 * The Admin & Governance Console shell (ARCHITECTURE.md ADR-012): one console for the
 * whole of ForKhatri. Desktop gets a side navigation; phones get a bottom bar with the
 * four daily sections and "More" for the rest. Sections a person's role cannot use are
 * not shown at all (least privilege is also least clutter).
 */
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { ApiError, identity, type Lang } from "@/lib/api";
import { admin, type AdminMe } from "@/lib/admin-api";
import { adminTranslator, type AdminKey } from "@/lib/admin-i18n";
import { langFromNavigator } from "@/lib/i18n";
import { loadStoredLang } from "@/lib/storage";
import { ConsoleContext, Dialog, roleName, scopeName, type Console } from "./kit";

type Phase = { kind: "loading" } | { kind: "signedOut" } | { kind: "notAdmin" } | { kind: "error" } | { kind: "ready"; me: AdminMe };

type NavItem = { href: string; label: AdminKey; icon: ReactNode; show: (can: (p: string) => boolean, me: AdminMe) => boolean };

const I = ({ d }: { d: string }) => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d={d} />
  </svg>
);

const NAV: NavItem[] = [
  { href: "/admin", label: "navToday", icon: <I d="M4 11l8-6 8 6v8a1 1 0 0 1-1 1h-4v-6H9v6H5a1 1 0 0 1-1-1z" />, show: () => true },
  { href: "/admin/queues", label: "navQueues", icon: <I d="M4 6h16M4 12h16M4 18h10" />, show: (_c, me) => me.module_scopes.length > 0 },
  { href: "/admin/members", label: "navMembers", icon: <I d="M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM2 21a7 7 0 0 1 14 0M17 11a3 3 0 1 0 0-6M22 21a6 6 0 0 0-4-5.6" />, show: (c) => c("members.view") },
  {
    href: "/admin/approvals",
    label: "navApprovals",
    icon: <I d="M9 12l2 2 4-4M12 3l7 3v6c0 4.5-3 8-7 9-4-1-7-4.5-7-9V6z" />,
    show: (c) => c("approvals.decide") || c("members.ban") || c("roles.manage"),
  },
  { href: "/admin/team", label: "navTeam", icon: <I d="M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0zM4 21v-1a6 6 0 0 1 6-6h4a6 6 0 0 1 6 6v1" />, show: (c, me) => c("roles.view") || me.managed_chapters.length > 0 },
  { href: "/admin/org", label: "navOrg", icon: <I d="M12 3v4M5 21v-6h14v6M12 11v4M8 7h8v4H8z" />, show: (c) => c("org.view") },
  { href: "/admin/audit", label: "navAudit", icon: <I d="M7 3h8l4 4v14H7zM15 3v4h4M10 12h6M10 16h6" />, show: (c) => c("audit.view") },
  { href: "/admin/modules", label: "navModules", icon: <I d="M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z" />, show: () => true },
];

// Four daily destinations on the phone bar; everything else sits under "More".
const PHONE_PRIMARY = ["/admin", "/admin/queues", "/admin/members", "/admin/approvals"];

export default function AdminShell({ children }: { children: ReactNode }) {
  const [phase, setPhase] = useState<Phase>({ kind: "loading" });
  const [lang, setLang] = useState<Lang>("en");
  const [version, setVersion] = useState(0);
  const [moreOpen, setMoreOpen] = useState(false);
  const pathname = usePathname();
  const t = useMemo(() => adminTranslator(lang), [lang]);

  const load = useCallback(async () => {
    try {
      const session = await identity.session();
      const next = loadStoredLang() ?? session?.member.preferred_language ?? langFromNavigator();
      setLang(next);
      document.documentElement.lang = next;
      if (!session) return setPhase({ kind: "signedOut" });
      const me = await admin.me();
      setPhase(me.is_admin ? { kind: "ready", me } : { kind: "notAdmin" });
    } catch (error) {
      setPhase(error instanceof ApiError && error.status === 401 ? { kind: "signedOut" } : { kind: "error" });
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    // Deferred a tick, as the entrance does, so no state is set synchronously in the effect.
    void Promise.resolve().then(() => {
      if (!cancelled) void load();
    });
    return () => {
      cancelled = true;
    };
  }, [load]);

  const value: Console | null = useMemo(() => {
    if (phase.kind !== "ready") return null;
    const permissions = new Set(phase.me.permissions);
    return { me: phase.me, lang, t, can: (p: string) => permissions.has(p), version, changed: () => setVersion((v) => v + 1) };
  }, [phase, lang, t, version]);

  if (phase.kind !== "ready" || !value) {
    return (
      <div className="adm adm-gate">
        <div className="adm-gate-card">
          <Link href="/" className="adm-brand">
            For<strong>Khatri</strong>
          </Link>
          {phase.kind === "loading" && <p className="adm-muted">{t("loading")}</p>}
          {phase.kind === "signedOut" && (
            <>
              <h1>{t("signedOutTitle")}</h1>
              <Link className="adm-btn primary" href="/?return_to=/admin">
                {t("signIn")}
              </Link>
            </>
          )}
          {phase.kind === "notAdmin" && (
            <>
              <h1>{t("notAdminTitle")}</h1>
              <p className="adm-muted">{t("notAdminBody")}</p>
              <Link className="adm-btn" href="/">
                {t("backToApp")}
              </Link>
            </>
          )}
          {phase.kind === "error" && (
            <>
              <p>{t("loadFailed")}</p>
              <button type="button" className="adm-btn primary" onClick={() => void load()}>
                {t("retry")}
              </button>
            </>
          )}
        </div>
      </div>
    );
  }

  const nav = NAV.filter((item) => item.show(value.can, value.me));
  const isActive = (href: string) => (href === "/admin" ? pathname === "/admin" : pathname?.startsWith(href));
  const primary = nav.filter((item) => PHONE_PRIMARY.includes(item.href));
  const secondary = nav.filter((item) => !PHONE_PRIMARY.includes(item.href));
  const firstRole = value.me.roles[0];

  return (
    <ConsoleContext.Provider value={value}>
      <div className="adm">
        <aside className="adm-side" aria-label={t("consoleName")}>
          <Link href="/" className="adm-brand" title={t("backToApp")}>
            For<strong>Khatri</strong>
          </Link>
          <p className="adm-side-kicker">{t("consoleName")}</p>
          <nav className="adm-nav">
            {nav.map((item) => (
              <Link key={item.href} href={item.href} className={`adm-nav-item${isActive(item.href) ? " is-active" : ""}`} aria-current={isActive(item.href) ? "page" : undefined}>
                {item.icon}
                <span>{t(item.label)}</span>
              </Link>
            ))}
          </nav>
          <div className="adm-side-foot">
            <span className="adm-side-name">{value.me.member.display_name}</span>
            {firstRole && (
              <span className="adm-side-role">
                {roleName(t, firstRole.role)} · {scopeName(t, firstRole.scope_kind, null, firstRole.scope_key)}
              </span>
            )}
            <Link href="/" className="adm-side-back">
              {t("backToApp")}
            </Link>
          </div>
        </aside>

        <header className="adm-topbar">
          <Link href="/" className="adm-brand" aria-label={t("backToApp")}>
            For<strong>Khatri</strong>
          </Link>
          <span className="adm-topbar-title">{t("consoleName")}</span>
        </header>

        <main className="adm-main" id="main">
          {children}
        </main>

        <nav className="adm-tabbar" aria-label={t("consoleName")}>
          {primary.map((item) => (
            <Link key={item.href} href={item.href} className={`adm-tab${isActive(item.href) ? " is-active" : ""}`} aria-current={isActive(item.href) ? "page" : undefined}>
              {item.icon}
              <span>{t(item.label)}</span>
            </Link>
          ))}
          {secondary.length > 0 && (
            <button type="button" className={`adm-tab${secondary.some((i) => isActive(i.href)) ? " is-active" : ""}`} onClick={() => setMoreOpen(true)}>
              <I d="M5 12h.01M12 12h.01M19 12h.01" />
              <span>{t("navMore")}</span>
            </button>
          )}
        </nav>

        <Dialog open={moreOpen} onClose={() => setMoreOpen(false)} title={t("navMore")}>
          <div className="adm-more">
            {secondary.map((item) => (
              <Link key={item.href} href={item.href} className="adm-more-item" onClick={() => setMoreOpen(false)}>
                {item.icon}
                <span>{t(item.label)}</span>
              </Link>
            ))}
            <Link href="/" className="adm-more-item">
              <I d="M15 18l-6-6 6-6" />
              <span>{t("backToApp")}</span>
            </Link>
          </div>
        </Dialog>
      </div>
    </ConsoleContext.Provider>
  );
}

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import ForKhatriHubLink from "@/components/ForKhatriHubLink";
import Icon from "@/components/Icon";
import RequestPrompt from "@/components/RequestPrompt";
import { getSession, type Session } from "@/lib/auth";
import { getMyAgentRecord } from "@/lib/agents";

/* The navigation shell — one component for both form factors, because they
 * are the same navigation and must never drift apart.
 *
 * globals.css §4 already describes the whole thing: below 1024px a sticky
 * `.mtop` top bar plus a fixed five-slot `.bottombar`; at 1024px and above
 * those two hide, `.app` turns into a row, and a fixed `.sidebar` takes
 * over with the same five destinations. That stylesheet landed without a
 * component that emits its markup, so the app was still rendering the old
 * phone-only `.tabbar` (which has no CSS at all) inside a 480px-capped
 * `.shell` — a phone column stranded in the middle of a desktop window.
 * This component emits the markup the stylesheet was written for, so
 * Mangalya is a genuine desktop web app as well as a mobile-first one.
 *
 * Counts come from the session `/auth/me` already returns, so the badges
 * cost no extra request. */

type Dest = {
  href: string;
  labelKey: string;
  count?: (s: Session) => number;
  icon: (active: boolean) => React.ReactNode;
};

/* One icon set (components/Icon): light outline, filled when active. */
const DESTINATIONS: Dest[] = [
  {
    href: "/",
    labelKey: "common:nav.home",
    icon: (active) => <Icon name="home" filled={active} />,
  },
  {
    href: "/discover",
    labelKey: "common:nav.discover",
    icon: (active) => <Icon name="search" filled={active} />,
  },
  {
    href: "/circle",
    labelKey: "common:nav.circle",
    count: (s) => s.counts.pending_requests,
    icon: (active) => <Icon name="family" filled={active} />,
  },
  {
    href: "/messages",
    labelKey: "common:nav.messages",
    count: (s) => s.counts.unread_messages,
    icon: (active) => <Icon name="chat" filled={active} />,
  },
  {
    href: "/me",
    labelKey: "common:nav.me",
    icon: (active) => <Icon name="me" filled={active} />,
  },
];

/* [Owner walkthrough, 2026-09-30] "why i am not seeing agent or agent
 * screen?" — the agent workspace (/agent) and the families' agent page
 * (/agents) were built but linked from nowhere. A verified or applying agent
 * gets their workspace first in the menu; every other member gets "Marriage
 * agents", the way to find and work with one. */
const AGENT_WORKSPACE: Dest = {
  href: "/agent",
  labelKey: "common:nav.agentWorkspace",
  icon: (active) => <Icon name="briefcase" filled={active} />,
};
const FIND_AGENTS: Dest = {
  href: "/agents",
  labelKey: "common:nav.agents",
  icon: (active) => <Icon name="handshake" filled={active} />,
};

/* Routes outside the signed-in shell. Navigation on a sign-in screen would
 * imply places you can go before you can go anywhere. These keep the narrow
 * centred column, which is the right measure for a single form. */
const CHROMELESS = ["/login", "/signup", "/reset", "/otp", "/profile/create"];

function isActive(pathname: string, href: string): boolean {
  return pathname === href || (href !== "/" && pathname.startsWith(`${href}/`));
}

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { t } = useTranslation("common");
  const [session, setSession] = useState<Session | null>(null);
  const [isAgent, setIsAgent] = useState(false);
  useEffect(() => {
    getMyAgentRecord()
      .then((r) => setIsAgent(r?.kind === "agent"))
      .catch(() => undefined);
  }, []);
  const destinations = isAgent
    ? [AGENT_WORKSPACE, ...DESTINATIONS]
    : [...DESTINATIONS.slice(0, 4), FIND_AGENTS, DESTINATIONS[4]];
  /* [DEC-V1-030, owner 2026-09-24] Below desktop width the navigation is a
     left drawer opened from a menu button, not a bottom bar — the page keeps
     its full width for photos. Detail screens (a profile, an open chat)
     carry their own back button, so the menu button steps aside there. */
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerPath, setDrawerPath] = useState(pathname);
  if (drawerPath !== pathname) {
    // Navigating closes the drawer (state adjusted during render, not in an
    // effect, so there is no extra paint with it still open).
    setDrawerPath(pathname);
    setDrawerOpen(false);
  }
  useEffect(() => {
    if (!drawerOpen) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setDrawerOpen(false);
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [drawerOpen]);
  const isDetail =
    pathname.startsWith("/profile/") ||
    /^\/messages\/[^/]+/.test(pathname);

  useEffect(() => {
    let active = true;
    // A failed session read must not take the navigation down with it: the
    // shell still renders, only the badges are missing.
    getSession()
      .then((s) => {
        if (active) setSession(s);
      })
      .catch(() => undefined);
    return () => {
      active = false;
    };
  }, [pathname]);

  if (CHROMELESS.includes(pathname)) {
    return <div className="shell">{children}</div>;
  }

  const countFor = (dest: Dest) =>
    session && dest.count ? dest.count(session) : 0;

  return (
    <div className={`app${drawerOpen ? " app--drawer" : ""}${isDetail ? " app--detail" : ""}`}>
      {!isDetail && (
        <button
          type="button"
          className="menu-btn"
          aria-label={t(drawerOpen ? "common:nav.closeMenu" : "common:nav.menu")}
          aria-expanded={drawerOpen}
          aria-controls="app-drawer"
          onClick={() => setDrawerOpen((o) => !o)}
        >
          <Icon name={drawerOpen ? "close" : "menu"} />
        </button>
      )}
      <div
        className="drawer-scrim"
        aria-hidden="true"
        onClick={() => setDrawerOpen(false)}
      />
      <aside className="sidebar" id="app-drawer">
        <Link className="sidebar__brand" href="/">
          <span className="brand-mark" aria-hidden="true">
            m
          </span>
          {t("common:app.name", { defaultValue: "Mangalya" })}
        </Link>

        <nav className="sidebar__nav" aria-label={t("common:nav.home")}>
          {destinations.map((dest) => {
            const active = isActive(pathname, dest.href);
            const count = countFor(dest);
            return (
              <Link
                key={dest.href}
                href={dest.href}
                className="sidebar__item"
                aria-current={active ? "page" : undefined}
              >
                {dest.icon(active)}
                <span>{t(dest.labelKey)}</span>
                {count > 0 && <span className="sidebar__count">{count}</span>}
              </Link>
            );
          })}
        </nav>

        <div className="sidebar__foot">
          <Link className="sidebar__help" href="/help">
            {t("common:nav.help")}
          </Link>
          <ForKhatriHubLink />
        </div>
      </aside>

      <main className="app__main">
        <div className="app__content">{children}</div>
      </main>

      {/* A request waiting for this person — as the candidate, or as a
          mother, father or guardian in a candidate's circle. */}
      <RequestPrompt />

      <nav className="bottombar" aria-label="Primary">
        {destinations.map((dest) => {
          const active = isActive(pathname, dest.href);
          const count = countFor(dest);
          return (
            <Link
              key={dest.href}
              href={dest.href}
              className="bottombar__item"
              aria-current={active ? "page" : undefined}
            >
              {dest.icon(active)}
              <span>{t(dest.labelKey)}</span>
              {count > 0 && <span className="nav-badge">{count}</span>}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}

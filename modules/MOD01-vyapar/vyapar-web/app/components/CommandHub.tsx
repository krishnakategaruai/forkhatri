"use client";

// [Design language 2026-09-29, §11] Primary navigation, one source of truth
// for two presentations (CSS-swapped at 900px, no hydration mismatch):
//
//  Desktop (≥900): a quiet 232px side rail under the top bar (Linear's
//  "reduce visual noise… increase hierarchy and density"): Post first, as
//  an ink button (the screen's own primary action keeps the one brand
//  fill), then Discover, Businesses, Activity, Profile as 44px rows with
//  icon + word; the current page gets the neutral selected fill and a
//  brand icon.
//
//  Phone: the floating command hub, now always open — a pill in the thumb
//  zone with every destination as icon + word (low-literacy research:
//  icons alone are opaque, hidden menus are missed; the old collapsed ✦
//  orb hid all five). Post is the raised ink circle in the middle. While
//  scrolling DOWN the hub condenses to icons only; scrolling up brings the
//  words back (motion layout spring). Reduced motion: no animation, and
//  it never condenses.
import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, useReducedMotion } from "motion/react";
import { useTranslation } from "react-i18next";
import { Compass, Store, Plus, Activity, CircleUserRound, type LucideIcon } from "lucide-react";
import { useHost } from "@/app/host/HostProvider";

type Dest = { href: string; labelKey: string; icon: LucideIcon };

const DESTINATIONS: Dest[] = [
  { href: "/", labelKey: "nav.discover", icon: Compass },
  { href: "/businesses", labelKey: "nav.businesses", icon: Store },
  { href: "/post", labelKey: "nav.post", icon: Plus },
  { href: "/activity", labelKey: "nav.activity", icon: Activity },
  { href: "/profile", labelKey: "nav.profile", icon: CircleUserRound },
];

function isActive(pathname: string, href: string) {
  return href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(href + "/");
}

export default function CommandHub() {
  const { t } = useTranslation("common");
  const pathname = usePathname();
  const reduce = useReducedMotion();
  const { brand } = useHost();
  const [condensed, setCondensed] = useState(false);

  useEffect(() => {
    if (reduce) return;
    let last = window.scrollY;
    const on = () => {
      const y = window.scrollY;
      if (Math.abs(y - last) < 12) return;
      setCondensed(y > last && y > 120);
      last = y;
    };
    window.addEventListener("scroll", on, { passive: true });
    return () => window.removeEventListener("scroll", on);
  }, [reduce]);

  const post = DESTINATIONS[2];
  const others = DESTINATIONS.filter((d) => d !== post);

  return (
    <>
      <nav className="vy-rail" aria-label={t("nav.primary")}>
        <Link href={post.href} className="vy-rail-post" aria-current={isActive(pathname, post.href) ? "page" : undefined}>
          <Plus size={20} strokeWidth={2.25} aria-hidden="true" />
          {t(post.labelKey)}
        </Link>
        {others.map((d) => {
          const active = isActive(pathname, d.href);
          const I = d.icon;
          return (
            <Link key={d.href} href={d.href} className="vy-rail-link" aria-current={active ? "page" : undefined}>
              <span className="vy-rail-mark" aria-hidden="true">
                <I size={20} strokeWidth={active ? 2.1 : 1.75} />
              </span>
              {t(d.labelKey)}
            </Link>
          );
        })}
        {brand.qualifier && (
          <p className="vy-rail-foot">
            {brand.name} · {brand.qualifier}
          </p>
        )}
      </nav>

      <div className="vy-hub-float">
        <motion.nav
          layout={!reduce}
          transition={{ type: "spring", stiffness: 420, damping: 36 }}
          className="vy-hub"
          data-condensed={condensed ? "" : undefined}
          aria-label={t("nav.primary")}
        >
          {DESTINATIONS.map((d) => {
            const active = isActive(pathname, d.href);
            const I = d.icon;
            const isPost = d === post;
            return (
              <Link
                key={d.href}
                href={d.href}
                className={isPost ? "vy-hub-item vy-hub-post" : "vy-hub-item"}
                aria-current={active ? "page" : undefined}
                aria-label={condensed ? t(d.labelKey) : undefined}
              >
                <span className="vy-hub-icon" aria-hidden="true">
                  <I size={isPost ? 24 : 22} strokeWidth={isPost ? 2.25 : active ? 2.1 : 1.75} />
                </span>
                <span className="vy-hub-label">{t(d.labelKey)}</span>
              </Link>
            );
          })}
        </motion.nav>
      </div>
    </>
  );
}

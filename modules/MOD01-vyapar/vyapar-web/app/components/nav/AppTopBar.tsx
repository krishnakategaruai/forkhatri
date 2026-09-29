"use client";

// [Design language 2026-09-29, §11 — owner: "this complete design is old
// fashioned"] One real header instead of floating pills over the page:
//   wordmark · (desktop) Hire / Find work · floating search pill ·
//   language & display · bell · avatar (always right-most).
// Condensed on scroll: after 8px the bar gains its hairline and raised
// shadow. The search pill yields to Discover's own hero search while that
// is on screen (html[data-hero-search="visible"], set by the hero), then
// slides into the bar once the hero scrolls away — search is never more
// than one tap away, and never shown twice. Phones get a round search
// button that returns to Discover's search.
import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { Search } from "lucide-react";
import { useHost } from "@/app/host/HostProvider";
import HostTopBar from "@/app/host/HostTopBar";
import LanguageSwitcher from "@/app/components/LanguageSwitcher";
import HireMenu from "./HireMenu";

export function BrandMark({ size = 30 }: { size?: number }) {
  // Original mark: a rounded square in the brand colour with a stylised
  // "V" drawn as two strokes meeting at a point — a handshake of two paths.
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true" className="vy-brandmark">
      <rect width="32" height="32" rx="10" fill="var(--brand)" />
      <path d="M9 10.5 15.2 22a1 1 0 0 0 1.6 0L23 10.5" fill="none" stroke="var(--on-brand)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default function AppTopBar() {
  const { t } = useTranslation("common");
  const { brand } = useHost();
  const router = useRouter();
  const pathname = usePathname();
  const [scrolled, setScrolled] = useState(false);
  const [q, setQ] = useState("");

  useEffect(() => {
    const on = () => setScrolled(window.scrollY > 8);
    on();
    window.addEventListener("scroll", on, { passive: true });
    return () => window.removeEventListener("scroll", on);
  }, []);

  function goSearch(text: string) {
    const v = text.trim();
    router.push(v ? `/?q=${encodeURIComponent(v)}` : "/");
    setQ("");
  }

  function focusHero() {
    const el = document.getElementById("vy-hero-search") as HTMLInputElement | null;
    if (pathname === "/" && el) {
      window.scrollTo({ top: 0, behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
      el.focus({ preventScroll: true });
    } else {
      router.push("/#search");
    }
  }

  return (
    <header className="vy-topbar" data-scrolled={scrolled ? "" : undefined}>
      <Link href="/" className="vy-topbar-brand" aria-label={t("shell.home")}>
        <BrandMark />
        <span className="vy-topbar-word">{brand.name}</span>
        {brand.qualifier && <span className="vy-topbar-qual">{brand.qualifier}</span>}
      </Link>

      {/* Upwork order: the two intents right after the wordmark (desktop). */}
      <div className="vy-topbar-menus">
        <HireMenu />
      </div>

      <form
        className="vy-topsearch"
        role="search"
        onSubmit={(e) => {
          e.preventDefault();
          goSearch(q);
        }}
      >
        <Search size={18} strokeWidth={2} aria-hidden="true" className="vy-topsearch-icon" />
        <input
          type="search"
          enterKeyHint="search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={t("shell.searchPlaceholder")}
          aria-label={t("shell.searchLabel")}
        />
        <button type="submit" className="vy-topsearch-go" aria-label={t("shell.openSearch")}>
          <Search size={16} strokeWidth={2.25} aria-hidden="true" />
        </button>
      </form>

      <div className="vy-topbar-end">
        <button type="button" className="vy-iconbtn vy-topsearch-mobile" onClick={focusHero} aria-label={t("shell.openSearch")}>
          <Search size={20} strokeWidth={1.75} aria-hidden="true" />
        </button>
        <LanguageSwitcher />
        <HostTopBar />
      </div>
    </header>
  );
}

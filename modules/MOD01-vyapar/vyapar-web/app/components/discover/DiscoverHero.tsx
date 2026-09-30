"use client";

// [Design language 2026-09-29, §11] The top of Discover (replaces FE2's
// DiscoverTop, keeping its behaviour: the Opportunities | Businesses
// switch, one search with the mic (VoiceInput, FE1) and a clear ×, Enter
// searches, the field follows the URL).
//
//  - Greeting in bold hero type, one quiet line under it (desktop only —
//    critique W1: on a 360×740 phone the first card's title and pay must
//    be visible without scrolling, so the phone hero stays compact).
//  - The switch as icon tabs (Airbnb's Homes / Experiences / Services).
//  - The search pill: icon, field, mic, and ONE round brand Search button
//    (the screen's single brand fill). Desktop widens it Airbnb-style with
//    a "Where" segment (the distance popover, LocationChip).
//  - While the pill is on screen it tells the top bar (html
//    data-hero-search="visible"), so the top-bar pill steps aside and
//    slides in once this one scrolls away. "/#search" focuses it.
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { Search, X, Briefcase, Store } from "lucide-react";
import VoiceInput, { appendSpoken } from "@/app/components/VoiceInput";
import LocationChip from "./LocationChip";

export default function DiscoverHero({
  firstName,
  query,
  onQuery,
  place,
  radiusKm,
  defaultRadiusKm,
  onRadius,
}: {
  firstName: string | null;
  query: string;
  onQuery: (q: string) => void;
  place: string | null;
  radiusKm: number | null;
  defaultRadiusKm: number | null;
  onRadius: (km: number | null) => void;
}) {
  const { t } = useTranslation(["explore", "discover", "common"]);
  const [text, setText] = useState(query);
  const pill = useRef<HTMLFormElement>(null);

  // [Typography 2026-09-29] Phone placeholder is the short one: the long
  // sentence ran under the mic at 360px (owner, device emulation). Same
  // breakpoint as the CSS (599px) so the tab labels and this agree.
  const [narrow, setNarrow] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(max-width: 599px)");
    const on = () => setNarrow(mq.matches);
    on();
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);

  // keep the field in step when the URL changes (a chip removed, "Clear all")
  const [shownQuery, setShownQuery] = useState(query);
  if (shownQuery !== query) {
    setShownQuery(query);
    setText(query);
  }

  useEffect(() => {
    const el = pill.current;
    const html = document.documentElement;
    if (!el || typeof IntersectionObserver === "undefined") return;
    const io = new IntersectionObserver(([e]) => {
      html.dataset.heroSearch = e.isIntersecting ? "visible" : "hidden";
    }, { rootMargin: "-64px 0px 0px 0px" });
    io.observe(el);
    if (window.location.hash === "#search") document.getElementById("vy-hero-search")?.focus();
    return () => {
      io.disconnect();
      delete html.dataset.heroSearch;
    };
  }, []);

  return (
    <section className="vy-hero" aria-labelledby="vy-hero-title">
      <div className="vy-hero-head">
        {firstName !== null ? (
          <h1 id="vy-hero-title" className="vy-hero-title">
            {t("discover:home.greeting", { name: firstName })}
          </h1>
        ) : (
          <div className="vy-skeleton" style={{ height: 36, width: 240, maxWidth: "70%" }} aria-hidden="true" />
        )}
        <p className="vy-hero-sub">{place ? t("explore:hero.subtitleNear", { place }) : t("explore:hero.subtitle")}</p>
      </div>

      <div className="vy-hero-tabs" role="tablist" aria-label={t("explore:top.switchLabel")}>
        <button type="button" role="tab" aria-selected="true" className="vy-hero-tab">
          <Briefcase size={18} strokeWidth={2} aria-hidden="true" />
          {t("explore:top.opportunities")}
        </button>
        {/* Long label on desktop, the short word on phones (CSS picks one),
            so "Businesses & professionals" is never clipped at 360px. */}
        <Link role="tab" aria-selected="false" href="/businesses" className="vy-hero-tab">
          <Store size={18} strokeWidth={2} aria-hidden="true" />
          <span className="vy-hero-tab-long">{t("explore:top.businesses")}</span>
          <span className="vy-hero-tab-short">{t("common:nav.businesses")}</span>
        </Link>
      </div>

      <form
        ref={pill}
        className="vy-hero-search"
        role="search"
        onSubmit={(e) => {
          e.preventDefault();
          onQuery(text.trim());
        }}
      >
        <div className="vy-hero-what">
          <Search size={20} strokeWidth={2} className="vy-hero-search-icon" aria-hidden="true" />
          <VoiceInput
            fieldLabel={t("explore:top.searchLabel")}
            compact
            onConfirm={(spoken) => {
              const next = appendSpoken(text, spoken);
              setText(next);
              onQuery(next.trim());
            }}
          >
            <input
              id="vy-hero-search"
              className="vy-hero-input"
              type="search"
              enterKeyHint="search"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder={t(narrow ? "explore:top.searchPlaceholderShort" : "explore:top.searchPlaceholder")}
              aria-label={t("explore:top.searchLabel")}
            />
          </VoiceInput>
          {text && (
            <button
              type="button"
              className="vy-hero-clear"
              aria-label={t("explore:top.clearSearch")}
              onClick={() => {
                setText("");
                if (query) onQuery("");
              }}
            >
              <X size={16} strokeWidth={2.25} aria-hidden="true" />
            </button>
          )}
        </div>
        <div className="vy-hero-where vy-desktop-only">
          <span className="vy-hero-where-label">{t("explore:hero.where")}</span>
          <LocationChip place={place} radiusKm={radiusKm} defaultRadiusKm={defaultRadiusKm} onRadius={onRadius} bare />
        </div>
        <button type="submit" className="vy-hero-go" aria-label={t("explore:hero.search")}>
          <Search size={20} strokeWidth={2.5} aria-hidden="true" />
          <span className="vy-hero-go-label">{t("explore:hero.search")}</span>
        </button>
      </form>
    </section>
  );
}

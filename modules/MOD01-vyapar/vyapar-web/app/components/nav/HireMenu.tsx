"use client";

// [FE2 — research §5] Desktop "Hire" and "Find work" menus in the top bar.
//
// Opened by click (not hover — it must work on touch laptops and by
// keyboard). Three narrow columns on a floating surface: categories on the
// left (from GET /v1/taxonomy/tree), the chosen category's specialties in
// the middle — each with its one-line description — and, on the right,
// outcomes ("Get my home repaired") for Hire or shortcuts for Find work.
// Hire → specialties open Businesses & Professionals filtered to that skill;
// Find work → they open Discover filtered to it. If the taxonomy can't be
// read, the menus simply don't render (the rail still has everything).
// Escape or a click outside closes; desktop only (≥900px).
import { useState } from "react";
import { usePopoverDismiss } from "@/lib/usePopoverDismiss";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import type { TaxonomyTree } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import { useResource } from "@/app/hooks/useResource";
import { OUTCOMES } from "@/app/components/explore/outcomes";

type Mode = "hire" | "work";

export default function HireMenu() {
  const { t } = useTranslation(["explore"]);
  const sdk = useSdk();
  const tree = useResource<TaxonomyTree | null>(() => sdk.taxonomy.tree(), [sdk], { fallback: null });
  const [open, setOpen] = useState<Mode | null>(null);
  const [cat, setCat] = useState<string | null>(null);
  const ref = usePopoverDismiss(open !== null, () => setOpen(null));

  const categories = tree.data?.categories ?? [];
  if (categories.length === 0) return null;
  const current = categories.find((c) => c.slug === cat) ?? categories[0];

  const specialtyHref = (slug: string) =>
    open === "hire" ? `/businesses?category=${current.slug}&skills=${slug}` : `/?skills=${slug}`;
  const categoryHref = open === "hire" ? `/businesses?category=${current.slug}` : `/?skills=${(current.children ?? []).map((c) => c.slug).join(",")}`;

  function toggle(mode: Mode) {
    setOpen((m) => (m === mode ? null : mode));
  }

  return (
    <div ref={ref} className="vy-desktop-only" style={{ position: "relative" }}>
      <nav className="vy-row" style={{ gap: 2 }} aria-label={t("explore:menu.label")}>
        <button type="button" className="vy-menu-trigger" aria-expanded={open === "hire"} aria-controls="vy-mega" onClick={() => toggle("hire")}>
          {t("explore:menu.hire")} <span aria-hidden="true">▾</span>
        </button>
        <button type="button" className="vy-menu-trigger" aria-expanded={open === "work"} aria-controls="vy-mega" onClick={() => toggle("work")}>
          {t("explore:menu.work")} <span aria-hidden="true">▾</span>
        </button>
      </nav>
      {open && (
        <div id="vy-mega" className="vy-card vy-card-floating vy-mega" role="region" aria-label={open === "hire" ? t("explore:menu.hire") : t("explore:menu.work")}>
          <div className="vy-mega-col" role="tablist" aria-orientation="vertical">
            <span className="vy-eyebrow vy-mega-head">{t("explore:menu.byCategory")}</span>
            {categories.map((c) => (
              <button
                key={c.slug}
                type="button"
                role="tab"
                className="vy-mega-cat"
                aria-selected={c.slug === current.slug}
                onClick={() => setCat(c.slug)}
                onMouseEnter={() => setCat(c.slug)}
              >
                {c.label}
              </button>
            ))}
          </div>
          <div className="vy-mega-col" role="tabpanel">
            <div className="vy-mega-head vy-stack" style={{ gap: 2 }}>
              <strong>{current.label}</strong>
              {current.description && <span className="vy-muted">{current.description}</span>}
            </div>
            <div className="vy-mega-items">
              {(current.children ?? []).map((s) => (
                <Link key={s.slug} href={specialtyHref(s.slug)} className="vy-mega-item" onClick={() => setOpen(null)}>
                  <strong>{s.label}</strong>
                  {s.description && <span>{s.description}</span>}
                </Link>
              ))}
            </div>
            <Link href={categoryHref} className="vy-link-btn" style={{ margin: "10px 10px 0" }} onClick={() => setOpen(null)}>
              {open === "hire" ? t("explore:menu.allIn", { name: current.label }) : t("explore:menu.workIn", { name: current.label })}
            </Link>
          </div>
          <div className="vy-mega-col">
            {open === "hire" ? (
              <>
                <span className="vy-eyebrow vy-mega-head">{t("explore:menu.byOutcome")}</span>
                {OUTCOMES.map((o) => (
                  <Link key={o.slug} href={`/outcomes/${o.slug}`} className="vy-mega-item" onClick={() => setOpen(null)}>
                    <strong>{t(`explore:outcome.${o.slug}.title`)}</strong>
                    <span>{t(`explore:outcome.${o.slug}.short`)}</span>
                  </Link>
                ))}
                <Link href="/post" className="vy-mega-item" onClick={() => setOpen(null)}>
                  <strong>{t("explore:menu.post")}</strong>
                  <span>{t("explore:menu.postDesc")}</span>
                </Link>
              </>
            ) : (
              <>
                <span className="vy-eyebrow vy-mega-head">{t("explore:menu.forYou")}</span>
                <Link href="/" className="vy-mega-item" onClick={() => setOpen(null)}>
                  <strong>{t("explore:menu.matches")}</strong>
                  <span>{t("explore:menu.matchesDesc")}</span>
                </Link>
                <Link href="/?radius_km=10&sort=distance" className="vy-mega-item" onClick={() => setOpen(null)}>
                  <strong>{t("explore:menu.nearby")}</strong>
                  <span>{t("explore:menu.nearbyDesc")}</span>
                </Link>
                <Link href="/?availability=now&type=employment" className="vy-mega-item" onClick={() => setOpen(null)}>
                  <strong>{t("explore:menu.urgentJobs")}</strong>
                  <span>{t("explore:menu.urgentJobsDesc")}</span>
                </Link>
                <Link href="/activity#saved-searches" className="vy-mega-item" onClick={() => setOpen(null)}>
                  <strong>{t("explore:menu.saved")}</strong>
                  <span>{t("explore:menu.savedDesc")}</span>
                </Link>
                <Link href="/listings/new" className="vy-mega-item" onClick={() => setOpen(null)}>
                  <strong>{t("explore:menu.profile")}</strong>
                  <span>{t("explore:menu.profileDesc")}</span>
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

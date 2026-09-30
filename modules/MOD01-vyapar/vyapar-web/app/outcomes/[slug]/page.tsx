"use client";

// [FE2 — research §5] /outcomes/[slug] — "Get my home repaired", "Build my
// website"… One outcome, in plain words: what Vyapar does for it, the
// specialties that do it (with the taxonomy's own one-line descriptions),
// profiles that match right now (the directory search, by the outcome's
// skills), and one primary action, "Post this", which opens the composer
// already set to the right kind of post and skills.
// [Design language 2026-09-29] Specialties as trade tiles with their word
// (§8), profiles as the directory's ProfileCard (§10), the "Post this" card
// sticky on the right; the whole page in the same language as Discover.
import { use } from "react";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { ChevronRight, Send } from "lucide-react";
import type { SearchResponse, TaxonomyTree } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import Screen from "@/app/components/Screen";
import ProfileCard from "@/app/components/businesses/ProfileCard";
import { SkeletonGrid } from "@/app/components/States";
import DealsEmpty from "@/app/components/deals/Empty";
import { useResource } from "@/app/hooks/useResource";
import { OUTCOMES, outcomeBySlug, postHref } from "@/app/components/explore/outcomes";
import { categoryVisual, specialtyVisual } from "@/app/components/discover/trades";
import "@/app/styles/deals-2026.css";

export default function OutcomePage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);
  const { t } = useTranslation(["explore", "discover", "common"]);
  const sdk = useSdk();
  const outcome = outcomeBySlug(slug);
  const tree = useResource<TaxonomyTree | null>(() => sdk.taxonomy.tree(), [sdk], { fallback: null });
  // The viewer's own profiles are never offered back to them as "people who can do it".
  const profiles = useResource<SearchResponse | null>(
    async () => {
      if (!outcome) return null;
      const [res, mine] = await Promise.all([
        sdk.listings.search({ skills: outcome.skills, sort_by: "relevance", limit: 12 }),
        sdk.listings.mine<{ id: string }[]>().catch(() => [] as { id: string }[]),
      ]);
      const own = new Set(mine.map((l) => l.id));
      return { ...res, results: res.results.filter((r) => !own.has(r.listing.id)) };
    },
    [slug, sdk],
    { fallback: null },
  );

  if (!outcome) {
    return (
      <Screen width="wide">
        <div className="vy-dl-page">
          <DealsEmpty
            tone="neutral"
            icon={<Send size={24} strokeWidth={1.75} aria-hidden="true" />}
            title={t("common:state.notFound")}
            action={
              <Link className="vy-btn vy-btn-secondary" href="/" style={{ textDecoration: "none" }}>
                {t("explore:filters.backToDiscover")}
              </Link>
            }
          />
        </div>
      </Screen>
    );
  }

  const specialties = (tree.data?.categories ?? [])
    .flatMap((c) => c.children ?? [])
    .filter((s, i, all) => outcome.skills.includes(s.slug) && all.findIndex((x) => x.slug === s.slug) === i)
    .sort((a, b) => outcome.skills.indexOf(a.slug) - outcome.skills.indexOf(b.slug));
  const results = profiles.data?.results ?? null;
  const others = OUTCOMES.filter((o) => o.slug !== slug);
  const Hero = categoryVisual(outcome.category);
  const HeroIcon = Hero.icon;

  return (
    <Screen width="wide">
      <div className="vy-dl-page">
        <div className="vy-detail">
          <div className="vy-detail-main">
            <div className="vy-dl-head">
              <span className={`vy-trade-tile vy-trade-${Hero.family}`} style={{ width: 56, height: 56, borderRadius: "var(--radius-tile)" }} aria-hidden="true">
                <HeroIcon size={28} strokeWidth={1.75} />
              </span>
              <span className="vy-eyebrow">{t("explore:outcome.eyebrow")}</span>
              <h1>{t(`explore:outcome.${slug}.title`)}</h1>
              <p>{t(`explore:outcome.${slug}.lead`)}</p>
              <p className="vy-dl-fine">{t("explore:outcome.how")}</p>
            </div>

            <section className="vy-dl-page" style={{ gap: "var(--space-3)" }} aria-labelledby="spec-title">
              <h2 id="spec-title" className="vy-section-title">{t("explore:outcome.whoDoesIt")}</h2>
              {tree.data === null && tree.loading ? (
                <SkeletonGrid count={3} />
              ) : (
                <div className="vy-dl-list">
                  {specialties.map((s) => {
                    const v = specialtyVisual(s.slug);
                    const Icon = v.icon;
                    return (
                      <Link key={s.slug} className="vy-dl-row" href={`/businesses?category=${outcome.category}&skills=${s.slug}`}>
                        <span className={`vy-trade-tile vy-trade-${v.family}`} aria-hidden="true">
                          <Icon size={22} strokeWidth={1.9} />
                        </span>
                        <span className="vy-dl-row-body">
                          <span className="vy-dl-row-title">{s.label}</span>
                          {s.description && <span className="vy-dl-row-meta"><span>{s.description}</span></span>}
                        </span>
                        <span className="vy-dl-row-aside">
                          <ChevronRight size={18} strokeWidth={2} aria-hidden="true" style={{ color: "var(--text-tertiary)" }} />
                        </span>
                      </Link>
                    );
                  })}
                </div>
              )}
            </section>
          </div>

          <aside className="vy-detail-aside">
            <div className="vy-dl-sec">
              <div className="vy-dl-sec-head">
                <span className="vy-dl-tile vy-dl-tile-brand" aria-hidden="true"><Send size={20} strokeWidth={1.75} /></span>
                <h2 className="vy-card-title">{t(`explore:outcome.${slug}.postTitle`)}</h2>
                <span className="vy-dl-sec-hint">{t(`explore:outcome.${slug}.postBody`)}</span>
              </div>
              <Link className="vy-btn vy-btn-primary" href={postHref(outcome)} style={{ textDecoration: "none", textAlign: "center" }}>
                {t("explore:outcome.postThis")}
              </Link>
              <p className="vy-dl-fine">{t("explore:outcome.free")}</p>
            </div>
          </aside>
        </div>

        <section className="vy-dl-page" style={{ gap: "var(--space-3)" }} aria-labelledby="profiles-title">
          <div className="vy-dl-head-row">
            <h2 id="profiles-title" className="vy-section-title">{t("explore:outcome.profiles")}</h2>
            <Link className="vy-dl-link vy-dl-inline-icon" href={`/businesses?category=${outcome.category}&skills=${outcome.skills.join(",")}`}>
              {t("explore:outcome.seeAllProfiles")} <ChevronRight size={16} strokeWidth={2} aria-hidden="true" />
            </Link>
          </div>
          {results === null ? (
            profiles.loading ? <SkeletonGrid count={3} /> : null
          ) : results.length === 0 ? (
            <p className="vy-dl-hint">{t("explore:outcome.noProfiles")}</p>
          ) : (
            <div className="vy-grid vy-grid-3">
              {results.slice(0, 6).map((r) => (
                <ProfileCard key={r.listing.id} result={r} />
              ))}
            </div>
          )}
        </section>

        <section className="vy-dl-page" style={{ gap: "var(--space-3)" }} aria-labelledby="more-title">
          <h2 id="more-title" className="vy-section-title">{t("explore:outcome.more")}</h2>
          <div className="vy-dl-tags">
            {others.map((o) => (
              <Link key={o.slug} href={`/outcomes/${o.slug}`} className="vy-chip" style={{ textDecoration: "none" }}>
                {t(`explore:outcome.${o.slug}.title`)}
              </Link>
            ))}
          </div>
        </section>
      </div>
    </Screen>
  );
}

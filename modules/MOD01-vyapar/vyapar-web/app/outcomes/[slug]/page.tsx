"use client";

// [FE2 — research §5] /outcomes/[slug] — "Get my home repaired", "Build my
// website"… One outcome, in plain words: what Vyapar does for it, the
// specialties that do it (with the taxonomy's own one-line descriptions),
// profiles that match right now (the existing directory search, by the
// outcome's skills), and one primary action, "Post this", which opens the
// composer already set to the right kind of post and skills
// (/opportunities/new?type=&skills=). Desktop: copy and specialties on the
// left, the "Post this" card sticky on the right; profiles in a grid below.
import { use } from "react";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import type { SearchResponse, TaxonomyTree } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import Screen from "@/app/components/Screen";
import LivingCard from "@/app/components/LivingCard";
import { EmptyState, SkeletonGrid } from "@/app/components/States";
import { useReputationText } from "@/app/components/Reputation";
import { BadgeList } from "@/app/components/trust/Badges";
import { useResource } from "@/app/hooks/useResource";
import { OUTCOMES, outcomeBySlug, postHref } from "@/app/components/explore/outcomes";

export default function OutcomePage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);
  const { t } = useTranslation(["explore", "discover", "common"]);
  const sdk = useSdk();
  const reputationText = useReputationText();
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
      <Screen>
        <EmptyState mark="◌" title={t("common:state.notFound")} action={<Link className="vy-btn vy-btn-secondary" href="/" style={{ textDecoration: "none" }}>{t("explore:filters.backToDiscover")}</Link>} />
      </Screen>
    );
  }

  const specialties = (tree.data?.categories ?? [])
    .flatMap((c) => c.children ?? [])
    .filter((s, i, all) => outcome.skills.includes(s.slug) && all.findIndex((x) => x.slug === s.slug) === i)
    .sort((a, b) => outcome.skills.indexOf(a.slug) - outcome.skills.indexOf(b.slug));
  const results = profiles.data?.results ?? null;
  const others = OUTCOMES.filter((o) => o.slug !== slug);

  return (
    <Screen width="wide">
      <div className="vy-detail">
        <div className="vy-detail-main">
          <div className="vy-outcome-hero">
            <span className="vy-eyebrow">{t("explore:outcome.eyebrow")}</span>
            <h1>{t(`explore:outcome.${slug}.title`)}</h1>
            <p>{t(`explore:outcome.${slug}.lead`)}</p>
            <p className="vy-muted">{t("explore:outcome.how")}</p>
          </div>

          <section className="vy-stack" style={{ gap: 10 }} aria-labelledby="spec-title">
            <h2 id="spec-title" className="vy-section-title">{t("explore:outcome.whoDoesIt")}</h2>
            {tree.data === null && tree.loading ? (
              <SkeletonGrid count={3} />
            ) : (
              <div className="vy-spec-grid">
                {specialties.map((s) => (
                  <Link key={s.slug} className="vy-card vy-spec" href={`/businesses?category=${outcome.category}&skills=${s.slug}`}>
                    <strong>{s.label}</strong>
                    {s.description && <span className="vy-muted">{s.description}</span>}
                  </Link>
                ))}
              </div>
            )}
          </section>
        </div>

        <aside className="vy-detail-aside">
          <div className="vy-card vy-stack" style={{ gap: 12 }}>
            <strong>{t(`explore:outcome.${slug}.postTitle`)}</strong>
            <p style={{ fontSize: 14 }}>{t(`explore:outcome.${slug}.postBody`)}</p>
            <Link className="vy-btn vy-btn-primary" href={postHref(outcome)} style={{ textDecoration: "none", textAlign: "center" }}>
              {t("explore:outcome.postThis")}
            </Link>
            <p className="vy-muted">{t("explore:outcome.free")}</p>
          </div>
        </aside>
      </div>

      <section className="vy-stack" style={{ gap: 12 }} aria-labelledby="profiles-title">
        <div className="vy-row" style={{ justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
          <h2 id="profiles-title" className="vy-section-title">{t("explore:outcome.profiles")}</h2>
          <Link className="vy-link-btn" href={`/businesses?category=${outcome.category}&skills=${outcome.skills.join(",")}`}>
            {t("explore:outcome.seeAllProfiles")}
          </Link>
        </div>
        {results === null ? (
          profiles.loading ? <SkeletonGrid count={3} /> : null
        ) : results.length === 0 ? (
          <p className="vy-muted">{t("explore:outcome.noProfiles")}</p>
        ) : (
          <div className="vy-grid vy-grid-3">
            {results.slice(0, 6).map((r, i) => (
              <LivingCard
                key={r.listing.id}
                index={i}
                href={`/listings/${r.listing.id}`}
                morphName={`listing-${r.listing.id}`}
                title={r.listing.name}
                subtitle={`${r.listing.locality} · ${[...r.listing.category_labels, ...r.listing.capability_labels].join(", ")}`}
                verified={r.listing.verification_state === "verified"}
                verificationLabel={t("discover:businesses.verifiedLabel")}
                meta={[reputationText(r.listing.reputation), r.distance_km != null ? t("discover:businesses.distanceAway", { km: r.distance_km }) : null].filter(Boolean).join(" · ")}
              >
                <BadgeList badges={r.listing.badges} compact max={3} />
              </LivingCard>
            ))}
          </div>
        )}
      </section>

      <section className="vy-stack" style={{ gap: 10 }} aria-labelledby="more-title">
        <h2 id="more-title" className="vy-section-title">{t("explore:outcome.more")}</h2>
        <div className="vy-row" style={{ flexWrap: "wrap", gap: 8 }}>
          {others.map((o) => (
            <Link key={o.slug} href={`/outcomes/${o.slug}`} className="vy-chip" style={{ textDecoration: "none" }}>
              {t(`explore:outcome.${o.slug}.title`)}
            </Link>
          ))}
        </div>
      </section>
    </Screen>
  );
}

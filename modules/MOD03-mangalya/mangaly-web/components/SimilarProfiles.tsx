"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { Avatar } from "@/components/Avatar";
import { resolveMediaUrl } from "@/lib/api";
import { getSnippet, search, type SearchResult, type Snippet } from "@/lib/discovery";

/* "Similar profiles" at the foot of a profile: after reading one person, the
 * next few worth reading. Drawn from the same Discover search the viewer is
 * already in — so the Looking-for rule and whose search is active apply
 * exactly as on Discover — then ordered by closeness to the profile just
 * read: same city, near in age, same profession, same education, same
 * mother tongue. The person being viewed is never in the row. */

type Props = {
  viewedId: string;
  /** The candidate whose search a family member is acting in, if any. */
  forCandidate?: string;
};

function closeness(basis: Snippet, r: SearchResult): number {
  const city = (s: string | null | undefined) => s?.split(",")[0]?.trim().toLowerCase() || null;
  let score = 0;
  if (city(basis.locality) && city(basis.locality) === city(r.locality)) score += 3;
  if (basis.age && r.age) {
    const gap = Math.abs(basis.age - r.age);
    score += gap <= 2 ? 2 : gap <= 4 ? 1 : 0;
  }
  if (basis.profession && r.profession && basis.profession.toLowerCase() === r.profession.toLowerCase()) score += 2;
  if (basis.education_level && basis.education_level === r.education_level) score += 1;
  return score;
}

/** The strongest shared fact, shown as a small glass chip on the card. */
function reasonOf(basis: Snippet | null, r: SearchResult): "sameCity" | "closeAge" | "sameWork" | "sameEducation" | null {
  if (!basis) return null;
  const city = (s: string | null | undefined) => s?.split(",")[0]?.trim().toLowerCase() || null;
  if (city(basis.locality) && city(basis.locality) === city(r.locality)) return "sameCity";
  if (basis.profession && r.profession && basis.profession.toLowerCase() === r.profession.toLowerCase()) return "sameWork";
  if (basis.age && r.age && Math.abs(basis.age - r.age) <= 2) return "closeAge";
  if (basis.education_level && basis.education_level === r.education_level) return "sameEducation";
  return null;
}

export default function SimilarProfiles({ viewedId, forCandidate }: Props) {
  const { t } = useTranslation(["profile", "home", "discover"]);
  const [people, setPeople] = useState<SearchResult[] | null>(null);
  const [total, setTotal] = useState<number | null>(null);
  const [basis, setBasis] = useState<Snippet | null>(null);

  useEffect(() => {
    let active = true;
    (async () => {
      const [basis, found] = await Promise.all([
        getSnippet(viewedId).catch(() => null),
        search({}, { forCandidate }).catch(() => null),
      ]);
      if (!active) return;
      setBasis(basis);
      const pool = (found?.results ?? []).filter((r) => r.candidate_account_id !== viewedId);
      const ranked = basis
        ? pool
            .map((r, i) => ({ r, s: closeness(basis, r), i }))
            // Closeness first; Discover's own order breaks ties.
            .sort((a, b) => b.s - a.s || a.i - b.i)
            .map((x) => x.r)
        : pool;
      setPeople(ranked.slice(0, 12));
      // Everyone else in this search, for the closing "see more" card.
      setTotal(found?.total != null ? Math.max(0, found.total - 1) : pool.length);
    })();
    return () => {
      active = false;
    };
  }, [viewedId, forCandidate]);

  if (!people || people.length === 0) return null;

  return (
    <section className="hfeed similar" aria-labelledby="similar-title">
      <div className="similar__head">
        <h2 className="similar__title" id="similar-title">
          {t("profile:view.similar")}
        </h2>
        <p className="similar__sub">{t("profile:view.similarWhy")}</p>
      </div>
      <ul className="hrail">
        {people.map((p, i) => {
          const city = p.locality?.split(",")[0]?.trim();
          const name = p.open_name?.trim().split(/\s+/)[0];
          return (
            <li key={p.candidate_account_id} className="hcard" style={{ "--i": Math.min(i, 6) } as React.CSSProperties}>
              <Link
                className="hcard__link"
                href={`/profile/${p.candidate_account_id}`}
                aria-label={[name, p.age, city, p.profession].filter(Boolean).join(", ")}
              >
                {p.photo_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img className="hcard__img" src={resolveMediaUrl(p.photo_url) ?? ""} alt="" loading="lazy" decoding="async" />
                ) : (
                  <span className="hcard__empty">
                    <Avatar anonymized size={72} />
                  </span>
                )}
                {(() => {
                  const why = reasonOf(basis, p);
                  return why ? <span className="similar__why">{t(`profile:view.similarReason.${why}`)}</span> : null;
                })()}
                <span className="hcard__text">
                  <span className="hcard__name">
                    {name ?? t("profile:hub.ageYears", { age: p.age ?? "" })}
                    {name && p.age ? <span className="hcard__age"> {p.age}</span> : null}
                  </span>
                  <span className="hcard__meta">{[p.profession, city].filter(Boolean).join(" · ")}</span>
                </span>
              </Link>
            </li>
          );
        })}
        {/* The row ends in a way onward, as Home's does: the rest of this search on Discover. */}
        <li className="hcard hcard--more">
          <Link className="hcard__link hcard__link--more" href="/discover">
            {/* A count only when Discover holds more than this row already shows. */}
            {total && total > people.length ? <span className="hcard__more-n">{total}</span> : null}
            <span>
              {total && total > people.length ? t("home:matches.seeAllCount", { count: total }) : t("home:matches.seeAll")}
            </span>
          </Link>
        </li>
      </ul>
    </section>
  );
}

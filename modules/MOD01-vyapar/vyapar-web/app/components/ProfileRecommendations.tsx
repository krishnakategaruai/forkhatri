"use client";

// [Profile recommendations — product owner, 2026-09-21: "like similar
// profiles, we will have other profiles for you"] One self-contained block
// for every place Vyapar recommends business/professional profiles. It is
// given only the API path that produces the cards (the backend's shared
// ProfileCard shape from app/profile_cards.py) and a heading; it fetches,
// re-fetches on a live language switch (skill names are translated
// server-side), and renders nothing when there is nothing to recommend, so
// a caller never has to handle an empty state.
//
// Every card says WHY it is shown: the skills that matched come first with
// a check, the profile's other skills follow, so a person never has to
// trust an unexplained list.
// Traces to: FR16, FR19, FR28, UX09
//
// [IMP38 — Refactor C] Split in two: <ProfileRecommendationsView> renders
// cards it is handed (no fetching — embeddable anywhere), and the default
// export stays the self-contained block: it loads through the SDK in scope
// with any loader (`load`, e.g. () => sdk.listings.similar(id)) or, for
// older call sites, a raw API path (`source`).
import { useTranslation } from "react-i18next";
import type { ProfileCardData } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import { useProfileRecommendations } from "@/app/hooks/opportunities";
import { useRoutes } from "@/app/host/HostProvider";
import LivingCard from "@/app/components/LivingCard";
import { useReputationText } from "@/app/components/Reputation";

export type { ProfileCardData };

const MAX_CHIPS = 4;

export function ProfileRecommendationsView({ cards, title, help }: { cards: ProfileCardData[]; title: string; help?: string }) {
  const { t } = useTranslation(["discover"]);
  const reputationText = useReputationText();
  const routes = useRoutes();

  if (cards.length === 0) return null;

  return (
    <section className="vy-stack" style={{ gap: 12 }}>
      <div className="vy-stack" style={{ gap: 4 }}>
        <h2 className="vy-section-title">{title}</h2>
        {help && <p className="vy-muted" style={{ fontSize: 14 }}>{help}</p>}
      </div>
      <div className="vy-grid">
        {cards.map((c, i) => {
          const chips = [...c.matched_labels.map((l) => ({ l, match: true })), ...c.other_labels.map((l) => ({ l, match: false }))].slice(0, MAX_CHIPS);
          const facts = [
            t(`discover:profiles.kind.${c.kind}` as "profiles.kind.business"),
            c.locality,
            c.experience_years ? t("discover:profiles.experience", { count: c.experience_years }) : null,
            c.availability === "now" ? t("discover:profiles.availableNow") : null,
          ].filter(Boolean);
          return (
            <LivingCard
              key={c.id}
              index={i}
              href={routes.listing(c.id)}
              morphName={`listing-${c.id}`}
              title={c.name}
              subtitle={c.headline ?? facts.join(" · ")}
              verified={c.verified}
              verificationLabel={t("discover:businesses.verifiedLabel")}
              meta={[c.headline ? facts.join(" · ") : null, reputationText(c.reputation) || null].filter(Boolean).join(" · ")}
            >
              {chips.length > 0 && (
                <div className="vy-row" style={{ flexWrap: "wrap", gap: 6 }}>
                  {chips.map(({ l, match }) =>
                    match ? (
                      <span key={l} className="vy-chip vy-chip-match">
                        <span aria-hidden="true">✓</span> {l}
                      </span>
                    ) : (
                      <span key={l} className="vy-chip">{l}</span>
                    ),
                  )}
                </div>
              )}
            </LivingCard>
          );
        })}
      </div>
    </section>
  );
}

export default function ProfileRecommendations({
  source,
  load,
  loadKey,
  title,
  help,
}: {
  /** Legacy: a raw API path returning ProfileCard[]. */
  source?: string;
  /** Preferred: any SDK call returning ProfileCard[]. */
  load?: () => Promise<ProfileCardData[]>;
  /** Changes when `load` should run again (defaults to `source`). */
  loadKey?: string;
  title: string;
  help?: string;
}) {
  const sdk = useSdk();
  const key = loadKey ?? source ?? "";
  const { data } = useProfileRecommendations(
    () => (load ? load() : source ? sdk.client.get<ProfileCardData[]>(source) : Promise.resolve([])),
    key,
  );
  return <ProfileRecommendationsView cards={data ?? []} title={title} help={help} />;
}

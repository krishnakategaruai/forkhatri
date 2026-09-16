"use client";

// [TR001] "My listings" — the owner-scoped list every FR01/FR04 create flow
// needs to land somewhere afterwards. Reuses <LivingCard> so this screen
// already looks like the future Businesses & Professionals discovery
// surface (FR15) will, rather than a bespoke admin-looking table.
// [Product-owner i18n rule] Converted to useTranslation().
// Traces to: FR01, FR03, FR04 (list + state visibility)
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "@/lib/api";
import LivingCard from "@/app/components/LivingCard";

interface Listing {
  id: string;
  kind: string;
  name: string;
  locality: string;
  state: string;
  verification_state: string;
  contact_verified: boolean;
}

const STATE_KEY: Record<string, string> = {
  draft: "stateDraft",
  submitted: "stateSubmitted",
  active_unverified: "stateActiveUnverified",
  active_verified: "stateActiveVerified",
  suspended: "stateSuspended",
  archived: "stateArchived",
};

export default function MyListingsPage() {
  const { t } = useTranslation(["listings", "common"]);
  const [listings, setListings] = useState<Listing[] | null>(null);

  useEffect(() => {
    api.get<Listing[]>("/v1/listings/mine").then(setListings);
  }, []);

  return (
    <main className="vy-shell">
      <h1>{t("listings:mine.title")}</h1>
      {listings === null && <p>{t("common:state.loading")}</p>}
      {listings?.length === 0 && (
        <p className="vy-muted">{t("listings:mine.empty")}</p>
      )}
      <div className="vy-stack">
        {listings?.map((l) => (
          <LivingCard
            key={l.id}
            href={`/listings/${l.id}`}
            title={l.name}
            subtitle={`${l.kind === "business" ? t("listings:mine.kindBusiness") : t("listings:mine.kindProfessional")} · ${l.locality}`}
            verified={l.verification_state === "verified"}
            verificationLabel={t("listings:mine.verifiedLabel")}
            memberProvided={l.verification_state !== "verified"}
            meta={`${t(`listings:mine.${STATE_KEY[l.state] ?? "stateDraft"}` as "mine.stateDraft")}${l.contact_verified ? " · " + t("listings:mine.contactVerified") : " · " + t("listings:mine.contactNotVerified")}`}
          />
        ))}
      </div>
    </main>
  );
}

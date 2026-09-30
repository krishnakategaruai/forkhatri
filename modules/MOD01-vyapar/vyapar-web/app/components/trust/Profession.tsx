"use client";

// ======================================================================
// [Trust pack §4, 2026-09-30] Profession-aware profiles.
//
// REQUIREMENT: an advocate (Bar Council of India Rule 36) or an architect
// (Council of Architecture) may not advertise, so their profile shows only
// what the council allows: no reviews, badges, packages, prices, promotion
// or "Sponsored", and a neutral "Contact" instead of "Ask for a price".
// The API already strips those fields for other readers and says which
// rule applies (`ListingOut.profession`); screens only decide what NOT to
// draw, from these helpers, so every card and page asks the same question.
//  - restrictedProfession(): the verdict when a rule restricts the profile.
//  - <ProfessionInfo>: "Information only" and the council's note, once, on
//    the public profile.
//  - <ProfessionOwnerNote>: the owner's view — what others do not see.
//  - <NoPromotionNote>: replaces every promote action for the owner.
// ======================================================================

import { useTranslation } from "react-i18next";
import { EyeOff, Info, Landmark } from "lucide-react";
import type { ProfessionVerdict } from "@/lib/sdk";

/** The verdict when a council rule restricts this profile, else null. */
export function restrictedProfession(p: ProfessionVerdict | null | undefined): ProfessionVerdict | null {
  return p && p.restricted ? p : null;
}

/** Promotion is forbidden for this profile. */
export function promotionBlocked(p: ProfessionVerdict | null | undefined): boolean {
  return !!p && p.restricted && !p.allow_promotion;
}

/** Public reviews, badges and reputation are hidden for this profile. */
export function reviewsBlocked(p: ProfessionVerdict | null | undefined): boolean {
  return !!p && p.restricted && !p.allow_public_reviews;
}

/** Prices and packages are hidden for this profile. */
export function pricesBlocked(p: ProfessionVerdict | null | undefined): boolean {
  return !!p && p.restricted && !p.allow_public_prices;
}

/** "Information only" + the council's note, shown once on the public profile. */
export function ProfessionInfo({ profession }: { profession: ProfessionVerdict }) {
  if (!profession.note) return null;
  return (
    <div className="vy-profession-note" role="note">
      <Landmark size={18} strokeWidth={1.9} aria-hidden="true" />
      {/* the API's note already opens with "Information only." — shown once */}
      <div>
        <span>{profession.note}</span>
      </div>
    </div>
  );
}

const FIELD_KEYS: Record<string, string> = {
  headline: "headline",
  description: "description",
  business_headline: "headline",
  business_description: "description",
  rates: "rates",
  evidence_links: "evidence",
  intent_state: "intent",
  availability: "availability",
};

/** The owner's view: which parts of the profile others do not see, and why. */
export function ProfessionOwnerNote({ profession }: { profession: ProfessionVerdict }) {
  const { t } = useTranslation(["listings"]);
  const parts = [...new Set(profession.hidden_fields.map((f) => FIELD_KEYS[f]).filter(Boolean))].map((k) => t(`listings:profession.field.${k}` as "profession.field.headline"));
  const extras = [
    !profession.allow_public_reviews ? t("listings:profession.field.reviews") : null,
    !profession.allow_public_prices ? t("listings:profession.field.prices") : null,
  ].filter((x): x is string => !!x);
  const all = [...parts, ...extras];
  return (
    <div className="vy-profession-note" role="note">
      <EyeOff size={18} strokeWidth={1.9} aria-hidden="true" />
      <div>
        <strong>{t("listings:profession.ownerTitle", { council: profession.regulator ?? profession.profession_label })}</strong>
        {all.length > 0 && <span>{t("listings:profession.ownerHidden", { fields: all.join(", ") })}</span>}
      </div>
    </div>
  );
}

/** Replaces the promote action: "Promotion isn't available for advocates under Bar Council rules." */
export function NoPromotionNote({ profession }: { profession: ProfessionVerdict }) {
  const { t } = useTranslation(["listings"]);
  const key = profession.profession === "advocate" ? "advocate" : profession.profession === "architect" ? "architect" : "other";
  return (
    <p className="vy-profession-quiet">
      <Info size={16} strokeWidth={2} aria-hidden="true" />
      <span>{t(`listings:profession.noPromotion.${key}` as "profession.noPromotion.other")}</span>
    </p>
  );
}

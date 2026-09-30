"use client";

// [Design language 2026-09-29, §10] A business / professional profile in
// the same card language as a Discover opportunity:
//   ▣ trade tile (the profile's first skill, else its category)   View ›
//   NAME (ink, 2 lines; morphs into the listing page's title)
//   what they do (skills, 2 lines)
//   ⌖ locality · distance
//   reputation, short form on one line ("3 of 3 recommend" / "New on
//   Vyapar"); the full detail stays on the profile page
//   ── ✓ ONE trust signal for the profile KIND (glossary): a business shows
//   "Business verified"; a person's work profile shows the badge the API
//   gives it ("Verified business owner", a credential …)
// No relevance reason on profiles ("posted by someone verified" is an
// opportunity phrase; distance is already on the card). The viewer's own
// profile is labelled "Your profile" (the list puts it last).
// Replaces LivingCard on the directory (LivingCard stays for its other uses).
// [2026-09-30] An <article> with a stretched title link, so the two actions
// can be real buttons: "Ask for a price" when the owner takes enquiries,
// "Call" when the owner shares a number with this viewer. Never on your own.
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { BadgeCheck, ChevronRight, MapPin, MessageSquareText, Phone, Star } from "lucide-react";
import type { SearchResult } from "@/lib/sdk";
import { useRoutes } from "@/app/host/HostProvider";
import { Morph } from "@/app/components/Screen";
import { cardVisual, categoryVisual } from "@/app/components/discover/trades";

const TRUST_ORDER = ["verified_business", "verified_professional", "verified", "id_verified", "top_rated", "rising"];

export default function ProfileCard({ result, sponsored = false }: { result: SearchResult; sponsored?: boolean }) {
  const { t } = useTranslation(["discover", "explore", "reviews"]);
  const routes = useRoutes();
  const l = result.listing;
  const fromSkills = cardVisual(l.capabilities, "");
  const visual = l.capabilities.length ? fromSkills : categoryVisual(l.categories[0]);
  const Icon = visual.icon;
  const what = (l.capability_labels.length ? l.capability_labels : l.category_labels).join(", ");
  const place = [l.locality, result.distance_km != null ? t("discover:businesses.distanceAway", { km: result.distance_km }) : null]
    .filter(Boolean)
    .join(" · ");
  const own = !!l.is_owner;
  const badge = [...(l.badges ?? [])].sort((a, b) => ((TRUST_ORDER.indexOf(a.key) + 99) % 99) - ((TRUST_ORDER.indexOf(b.key) + 99) % 99))[0];
  const trust =
    l.kind === "business" && (l.verification_state === "verified" || badge?.key === "verified_business")
      ? t("discover:businesses.verifiedLabel")
      : (badge?.label ?? null);
  const canAsk = !own && l.enquiry_pref === "enabled";
  const canCall = !own && !!l.primary_phone;
  const rep = l.reputation;
  const reputation = !rep
    ? null
    : rep.new_on_vyapar || rep.interactions === 0
      ? t("reviews:newOnVyapar")
      : t("reviews:recommendShort", { m: rep.recommends, n: rep.interactions });

  return (
    <article className="vy-card vy-ocard vy-pcard">
      <div className="vy-ocard-top">
        <span className={`vy-trade-tile vy-trade-${visual.family}`} aria-hidden="true">
          <Icon size={22} strokeWidth={1.9} />
        </span>
        <span className="vy-ocard-tags">
          {sponsored && <span className="vy-badge vy-badge-sponsored">{t("explore:card.sponsored")}</span>}
          {own && <span className="vy-badge vy-badge-own">{t("explore:biz.yourProfile")}</span>}
          <span className="vy-ocard-action" aria-hidden="true">
            <span>{t("explore:biz.viewProfile")}</span>
            <ChevronRight size={15} strokeWidth={2.25} />
          </span>
        </span>
      </div>

      <Morph name={`listing-${l.id}`}>
        <h3 className="vy-ocard-title">
          <Link href={routes.listing(l.id)} transitionTypes={["vy-forward"]} className="vy-pcard-link">
            {l.name}
          </Link>
        </h3>
      </Morph>
      {what && <p className="vy-pcard-what">{what}</p>}

      {place && (
        <p className="vy-ocard-line">
          <MapPin size={15} strokeWidth={2} aria-hidden="true" />
          <span>{place}</span>
        </p>
      )}
      {reputation && (
        <p className="vy-ocard-line">
          <Star size={15} strokeWidth={2} aria-hidden="true" />
          <span>{reputation}</span>
        </p>
      )}

      {/* The footer only exists when there is a trust signal to show. */}
      {trust && (
        <div className="vy-ocard-foot">
          <span className="vy-ocard-trust">
            <BadgeCheck size={16} strokeWidth={2} aria-hidden="true" />
            {trust}
          </span>
        </div>
      )}

      {(canAsk || canCall) && (
        <div className="vy-pcard-actions">
          {canAsk && (
            <Link href={routes.enquireListing(l.id)} className="vy-btn vy-btn-secondary">
              <MessageSquareText size={18} strokeWidth={2} aria-hidden="true" />
              {t("explore:biz.askPrice")}
            </Link>
          )}
          {canCall && (
            <a href={`tel:${l.primary_phone}`} className="vy-btn vy-btn-ghost">
              <Phone size={18} strokeWidth={2} aria-hidden="true" />
              {t("explore:biz.call")}
            </a>
          )}
        </div>
      )}
    </article>
  );
}

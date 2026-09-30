"use client";

// [Design language 2026-09-29, §10] The member's own profile (a Business
// profile or a Work profile, GLOSSARY.md) in the same card anatomy as a
// Discover or directory card:
//   ▣ tinted tile (shop for a business, person for a work profile)   kind
//   NAME (ink, 2 lines)
//   what they do (headline, else skills), 2 lines
//   skills as quiet chips (up to 4)
//   ⌖ locality
//   ── ONE trust or state line ················· "View or edit ›"
// The whole card is the link. The "add this kind" variant is a dashed card
// with one call to action. Presentational: data in, no fetching.
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { BadgeCheck, ChevronRight, Clock, MapPin, Plus, Store, UserRound } from "lucide-react";

export interface ProfileCardData {
  id: string;
  kind: "business" | "professional" | string;
  name: string;
  headline?: string | null;
  locality: string;
  state: string;
  verification_state: string;
  capability_labels?: string[];
  category_labels?: string[];
  contact_verified?: boolean;
  /** §11b: draft | submitted | active | suspended | archived. Preferred over `state`. */
  profile_status?: string;
  /** §11b: this section's own verification. Preferred over `verification_state`. */
  verified?: boolean;
}

/** profile_status (§11b) → the status label key. */
const STATUS_KEY: Record<string, string> = {
  draft: "stateDraft",
  submitted: "stateSubmitted",
  active: "stateActive",
  suspended: "stateSuspended",
  archived: "stateArchived",
};

export const LISTING_STATE_KEY: Record<string, string> = {
  draft: "stateDraft",
  submitted: "stateSubmitted",
  active_unverified: "stateActiveUnverified",
  active_verified: "stateActiveVerified",
  suspended: "stateSuspended",
  archived: "stateArchived",
};

function KindTile({ kind, size = 44 }: { kind: string; size?: number }) {
  const business = kind === "business";
  const Icon = business ? Store : UserRound;
  return (
    <span className={`vy-acct-tile${size > 40 ? " vy-acct-tile-lg" : ""}`} data-tint={business ? "indigo" : "teal"} aria-hidden="true">
      <Icon size={size > 40 ? 24 : 20} strokeWidth={1.9} />
    </span>
  );
}

export { KindTile };

export default function AccountProfileCard({ profile, href }: { profile: ProfileCardData; href: string }) {
  const { t } = useTranslation(["profile", "listings", "verification"]);
  const business = profile.kind === "business";
  const verified = profile.verified ?? (profile.verification_state === "verified" || profile.verification_state === "expiring");
  const skills = profile.capability_labels ?? [];
  const what = profile.headline || (skills.length === 0 ? (profile.category_labels ?? []).join(", ") : "");
  const status = profile.profile_status;
  const stateKey = (status ? STATUS_KEY[status] : LISTING_STATE_KEY[profile.state]) ?? "stateDraft";
  const tone = (status ?? profile.state) === "suspended" ? "danger" : (status ?? profile.state) === "submitted" ? "warning" : undefined;
  // One line in the footer: the trust signal when earned, otherwise the state.
  const showState = status ? true : !(verified && profile.state === "active_verified");

  return (
    <Link href={href} transitionTypes={["vy-forward"]} className="vy-card vy-acct-pcard" aria-label={profile.name}>
      <div className="vy-acct-pcard-top">
        <KindTile kind={profile.kind} />
        <span className="vy-acct-pcard-kind">{business ? t("profile:profiles.businessTitle") : t("profile:profiles.professionalTitle")}</span>
      </div>
      <h3 className="vy-acct-pcard-title">{profile.name}</h3>
      {what && <p className="vy-acct-pcard-what">{what}</p>}
      {skills.length > 0 && (
        <div className="vy-acct-chips" aria-label={t("profile:profiles.skills")}>
          {skills.slice(0, 4).map((s) => (
            <span key={s} className="vy-acct-chip">
              <span>{s}</span>
            </span>
          ))}
          {skills.length > 4 && (
            <span className="vy-acct-chip">
              <span>+{skills.length - 4}</span>
            </span>
          )}
        </div>
      )}
      {profile.locality && (
        <p className="vy-acct-meta">
          <span>
            <MapPin size={15} strokeWidth={2} aria-hidden="true" />
            {profile.locality}
          </span>
        </p>
      )}
      <div className="vy-acct-pcard-foot">
        {verified ? (
          <span className="vy-acct-trust">
            <BadgeCheck size={16} strokeWidth={2} aria-hidden="true" />
            {business ? t("listings:mine.verifiedLabel") : t("verification:stateVerified")}
          </span>
        ) : showState ? (
          <span className="vy-acct-status" data-tone={tone}>
            <Clock size={14} strokeWidth={2} aria-hidden="true" />
            {t(`listings:mine.${stateKey}` as "mine.stateDraft")}
          </span>
        ) : (
          <span />
        )}
        <span className="vy-acct-action">
          {t("profile:profiles.view")}
          <ChevronRight size={15} strokeWidth={2.25} aria-hidden="true" />
        </span>
      </div>
    </Link>
  );
}

/** The dashed "add this kind of profile" card. */
export function AddProfileCard({ kind, href }: { kind: "business" | "professional"; href: string }) {
  const { t } = useTranslation(["profile"]);
  const business = kind === "business";
  return (
    <Link href={href} transitionTypes={["vy-forward"]} className="vy-card vy-acct-pcard vy-acct-pcard-empty">
      <div className="vy-acct-pcard-top">
        <KindTile kind={kind} />
        <span className="vy-acct-pcard-kind">{business ? t("profile:profiles.businessTitle") : t("profile:profiles.professionalTitle")}</span>
      </div>
      <h3 className="vy-acct-pcard-title">{business ? t("profile:profiles.addBusiness") : t("profile:profiles.addProfessional")}</h3>
      <p className="vy-acct-pcard-what">{business ? t("profile:profiles.businessDesc") : t("profile:profiles.professionalDesc")}</p>
      <div className="vy-acct-pcard-foot">
        <span className="vy-acct-pcard-cta">
          <Plus size={16} strokeWidth={2.25} aria-hidden="true" />
          {t("profile:profiles.start")}
        </span>
      </div>
    </Link>
  );
}

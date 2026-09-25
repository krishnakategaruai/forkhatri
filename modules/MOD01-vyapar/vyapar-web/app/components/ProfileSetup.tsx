"use client";

// [Owner, 2026-09-22: "in my profile we can enhance profile information
// about business / or skill — keep both models, any one can be an option,
// without any nothing can move forward"]
//
// The member's two profile kinds, side by side, always both visible:
//   - Business: a shop, firm or service business.
//   - Professional: the person and their skills.
// Each card either summarises the profile that exists (name, skills, state,
// verification) with a way in to view or edit it, or invites the member to
// add that kind. Neither is mandatory on its own, but at least one is
// needed before posting an opportunity or sending an enquiry; in that
// `required` mode the block is shown IN PLACE of the form it gates, with a
// plain sentence saying why, so the person is never told "no" without the
// way forward on the same screen.
// Traces to: FR01, FR04, FR16, FR55
import { useTranslation } from "react-i18next";
import type { MemberProfiles, ProfileBrief } from "@/lib/sdk";
import Icon from "@/app/components/Icon";

const KINDS: Array<"business" | "professional"> = ["business", "professional"];
const MARK: Record<string, string> = { business: "business", professional: "professional" };
const STATE_KEY: Record<string, string> = {
  draft: "stateDraft",
  submitted: "stateSubmitted",
  active_unverified: "stateActiveUnverified",
  active_verified: "stateActiveVerified",
  suspended: "stateSuspended",
  archived: "stateArchived",
};

function ProfileKindCard({ kind, profile }: { kind: "business" | "professional"; profile: ProfileBrief | null }) {
  const { t } = useTranslation(["profile", "listings"]);
  if (!profile) {
    return (
      <a className="vy-card vy-profile-kind vy-profile-kind-empty" href={`/listings/new?kind=${kind}`}>
        <span className="vy-profile-kind-mark" aria-hidden="true"><Icon name={MARK[kind]} /></span>
        <span className="vy-stack" style={{ gap: 4 }}>
          <strong>{t(`profile:profiles.${kind}Title` as "profiles.businessTitle")}</strong>
          <span className="vy-muted" style={{ fontSize: 13 }}>{t(`profile:profiles.${kind}Desc` as "profiles.businessDesc")}</span>
          <span className="vy-profile-kind-cta">{t(`profile:profiles.add${kind === "business" ? "Business" : "Professional"}` as "profiles.addBusiness")} →</span>
        </span>
      </a>
    );
  }
  const verified = profile.verification_state === "verified" || profile.verification_state === "expiring";
  return (
    <div className="vy-card vy-profile-kind">
      <span className="vy-profile-kind-mark" aria-hidden="true"><Icon name={MARK[kind]} /></span>
      <div className="vy-stack" style={{ gap: 6, minWidth: 0 }}>
        <span className="vy-eyebrow">{t(`profile:profiles.${kind}Title` as "profiles.businessTitle")}</span>
        <strong style={{ fontSize: 17, overflowWrap: "anywhere" }}>{profile.name}</strong>
        {profile.headline && <span className="vy-muted" style={{ fontSize: 14 }}>{profile.headline}</span>}
        {profile.capability_labels.length > 0 && (
          <div className="vy-row" style={{ flexWrap: "wrap", gap: 6 }}>
            {profile.capability_labels.slice(0, 5).map((l) => (
              <span key={l} className="vy-chip">{l}</span>
            ))}
          </div>
        )}
        <span className="vy-row" style={{ gap: 8, flexWrap: "wrap", fontSize: 13, alignItems: "center" }}>
          {verified && <span className="vy-badge vy-badge-verified">✓ {t("listings:mine.verifiedLabel")}</span>}
          <span className="vy-muted">
            {[verified ? null : t(`listings:mine.${STATE_KEY[profile.state] ?? "stateDraft"}` as "mine.stateDraft"), profile.locality].filter(Boolean).join(" · ")}
          </span>
        </span>
        <span className="vy-row" style={{ gap: 12, marginTop: 2 }}>
          <a href={`/listings/${profile.id}`}>{t("profile:profiles.view")} →</a>
        </span>
      </div>
    </div>
  );
}

export default function ProfileSetup({ profiles, required = false }: { profiles: MemberProfiles | null | undefined; required?: boolean }) {
  const { t } = useTranslation(["profile"]);
  if (!profiles) return null;
  return (
    <section className="vy-stack" style={{ gap: 10 }} aria-labelledby="your-profile">
      <div className="vy-stack" style={{ gap: 2 }}>
        <h2 id="your-profile" className={required ? "vy-section-title" : "vy-eyebrow"}>
          {required ? t("profile:profiles.requiredTitle") : t("profile:profiles.title")}
        </h2>
        <p className={required ? "" : "vy-muted"} style={{ fontSize: required ? 15 : 13, margin: 0 }}>
          {required ? t("profile:profiles.requiredHelp") : profiles.complete ? t("profile:profiles.help") : t("profile:profiles.helpNone")}
        </p>
      </div>
      <div className="vy-profile-kinds">
        {KINDS.map((k) => (
          <ProfileKindCard key={k} kind={k} profile={profiles[k]} />
        ))}
      </div>
    </section>
  );
}

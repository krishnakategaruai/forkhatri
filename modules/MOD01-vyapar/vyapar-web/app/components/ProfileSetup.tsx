"use client";

// [Owner, 2026-09-22: "in my profile we can enhance profile information
// about business / or skill — keep both models, any one can be an option,
// without any nothing can move forward"]
//
// The member's two profile kinds, side by side, always both visible:
//   - Business profile: a shop, firm or service business.
//   - Work profile: the person and their skills (GLOSSARY.md).
// Each card either summarises the profile that exists (name, what they do,
// skills, locality, one trust or state line) with the way in, or invites
// the member to add that kind. Neither is mandatory on its own, but at
// least one is needed before posting or sending a request; in that
// `required` mode the block is shown IN PLACE of the form it gates, with a
// plain sentence saying why.
// [Design language 2026-09-29] Cards in the Discover card anatomy
// (AccountProfileCard); this file is only the section frame.
// Traces to: FR01, FR04, FR16, FR55
import { useTranslation } from "react-i18next";
import type { MemberProfiles } from "@/lib/sdk";
import AccountProfileCard, { AddProfileCard } from "@/app/components/account/AccountProfileCard";
import "@/app/styles/account-2026.css";

const KINDS: Array<"business" | "professional"> = ["business", "professional"];

export default function ProfileSetup({ profiles, required = false }: { profiles: MemberProfiles | null | undefined; required?: boolean }) {
  const { t } = useTranslation(["profile"]);
  if (!profiles) return null;
  return (
    <section className="vy-acct-section" aria-labelledby="your-profile">
      <div className="vy-acct-section-head">
        <div className="vy-stack" style={{ gap: 2, minWidth: 0 }}>
          <h2 id="your-profile" className="vy-section-title">
            {required ? t("profile:profiles.requiredTitle") : t("profile:profiles.title")}
          </h2>
          <p>{required ? t("profile:profiles.requiredHelp") : profiles.complete ? t("profile:profiles.help") : t("profile:profiles.helpNone")}</p>
        </div>
      </div>
      <div className="vy-acct-profiles">
        {KINDS.map((k) => {
          const p = profiles[k];
          return p ? <AccountProfileCard key={k} profile={p} href={`/listings/${p.id}`} /> : <AddProfileCard key={k} kind={k} href={`/listings/new?kind=${k}`} />;
        })}
      </div>
    </section>
  );
}

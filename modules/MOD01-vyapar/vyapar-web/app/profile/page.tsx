"use client";
// [Profile hub] No single FR names a standalone Profile screen; this is the
// honest home for the member's own places — listings, enquiries, and their
// moderation outcomes (FR41, where FR53 wants the appeal path reachable) —
// plus operator tools shown ONLY to members holding that permission, so
// ordinary members never see links that would 403. Compact rows, not
// full-size cards, so everything fits on the first phone screen.
// [Product-owner i18n rule] every string is a key in profile.json.
// Traces to: FR41, FR47, FR40 (entry points), FR53
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "@/lib/api";

interface Me {
  display_name: string;
  is_operator: boolean;
  operator_permissions: string[];
}

export default function ProfilePage() {
  const { t } = useTranslation(["profile", "common"]);
  const [me, setMe] = useState<Me | null>(null);

  useEffect(() => {
    api.get<Me>("/v1/members/me").then(setMe).catch(() => setMe(null));
  }, []);

  const memberLinks = [
    { href: "/listings/mine", label: t("profile:myListings") },
    { href: "/enquiries/mine", label: t("profile:enquiries") },
    { href: "/moderation/outcomes", label: t("profile:moderationOutcomes") },
    { href: "/promotions", label: t("profile:myBoosts") },
  ];
  const perms = me?.operator_permissions ?? [];
  const operatorLinks = [
    perms.includes("verification") && { href: "/admin/verification", label: t("profile:verificationQueue") },
    perms.includes("moderation") && { href: "/admin/moderation", label: t("profile:moderationQueue") },
  ].filter(Boolean) as { href: string; label: string }[];

  return (
    <main className="vy-shell">
      <h1>{me?.display_name ?? t("profile:title")}</h1>
      <div className="vy-stack" style={{ gap: 8 }}>
        {memberLinks.map((l) => (
          <a key={l.href} className="vy-card" style={{ textDecoration: "none", padding: "14px 18px" }} href={l.href}>
            {l.label} →
          </a>
        ))}
      </div>
      {operatorLinks.length > 0 && (
        <div className="vy-stack" style={{ gap: 8 }}>
          <h2 style={{ fontSize: 14, color: "var(--text-secondary)" }}>{t("profile:operatorTools")}</h2>
          {operatorLinks.map((l) => (
            <a key={l.href} className="vy-card" style={{ textDecoration: "none", padding: "14px 18px" }} href={l.href}>
              {l.label} →
            </a>
          ))}
        </div>
      )}
      <p className="vy-muted">{t("profile:notBuiltYet")}</p>
    </main>
  );
}

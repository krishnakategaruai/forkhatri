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

// [FR34] a team invitation is an account-level decision, so it waits here
interface Invite {
  id: string;
  listing_id: string;
  listing_name: string | null;
  role: string;
  expires_at: string;
}

interface WorkspaceRow {
  listing_id: string;
  listing_name: string;
  role: string;
}

export default function ProfilePage() {
  const { t, i18n } = useTranslation(["profile", "workspace", "adminCommercial", "privacy", "adminOps", "common"]);
  const [me, setMe] = useState<Me | null>(null);
  const [invites, setInvites] = useState<Invite[]>([]);
  const [workspaces, setWorkspaces] = useState<WorkspaceRow[]>([]);
  const [busy, setBusy] = useState(false);

  async function loadInvites() {
    const [pending, mine] = await Promise.all([
      api.get<Invite[]>("/v1/workspace/invites/mine").catch(() => []),
      api.get<WorkspaceRow[]>("/v1/workspace/mine").catch(() => []),
    ]);
    setInvites(pending);
    setWorkspaces(mine);
  }

  useEffect(() => {
    api.get<Me>("/v1/members/me").then(setMe).catch(() => setMe(null));
    loadInvites();
  }, []);

  async function answerInvite(id: string, accept: boolean) {
    setBusy(true);
    try {
      await api.post(`/v1/workspace/invites/${id}/answer`, { accept });
      await loadInvites();
    } finally {
      setBusy(false);
    }
  }

  const memberLinks = [
    { href: "/listings/mine", label: t("profile:myListings") },
    { href: "/enquiries/mine", label: t("profile:enquiries") },
    { href: "/moderation/outcomes", label: t("profile:moderationOutcomes") },
    { href: "/promotions", label: t("profile:myBoosts") },
    { href: "/privacy", label: t("privacy:title") },
  ];
  const perms = me?.operator_permissions ?? [];
  const operatorLinks = [
    perms.includes("verification") && { href: "/admin/verification", label: t("profile:verificationQueue") },
    perms.includes("moderation") && { href: "/admin/moderation", label: t("profile:moderationQueue") },
    perms.includes("commercial") && { href: "/admin/commercial", label: t("adminCommercial:title") },
    (perms.includes("content") || perms.includes("analytics")) && { href: "/admin/ops", label: t("adminOps:title") },
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
      {invites.length > 0 && (
        <div className="vy-stack" style={{ gap: 8 }}>
          <h2 style={{ fontSize: 14, color: "var(--text-secondary)" }}>{t("profile:pendingInvites")}</h2>
          {invites.map((invite) => (
            <div key={invite.id} className="vy-card vy-stack" style={{ gap: 6 }}>
              <strong>{invite.listing_name ?? invite.listing_id}</strong>
              <span className="vy-muted" style={{ fontSize: 13 }}>
                {t("profile:inviteRole", { role: t(`workspace:role.${invite.role}` as "role.admin") })} · {t("workspace:team.expires", { date: new Date(invite.expires_at).toLocaleDateString(i18n.language) })}
              </span>
              <div className="vy-row">
                <button className="vy-btn vy-btn-primary" disabled={busy} onClick={() => answerInvite(invite.id, true)}>{t("profile:accept")}</button>
                <button className="vy-btn vy-btn-ghost" disabled={busy} onClick={() => answerInvite(invite.id, false)}>{t("profile:decline")}</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {workspaces.length > 0 && (
        <div className="vy-stack" style={{ gap: 8 }}>
          <h2 style={{ fontSize: 14, color: "var(--text-secondary)" }}>{t("profile:workspaces")}</h2>
          {workspaces.map((w) => (
            <a key={w.listing_id} className="vy-card" style={{ textDecoration: "none", padding: "14px 18px" }} href={`/workspace/${w.listing_id}`}>
              {w.listing_name} · {t(`workspace:role.${w.role}` as "role.owner")} →
            </a>
          ))}
        </div>
      )}

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
      <div className="vy-stack" style={{ gap: 8 }}>
        <a className="vy-card" style={{ textDecoration: "none", padding: "14px 18px" }} href="/moderation/outcomes#grievance">
          {t("profile:help")}
        </a>
        {/* [Platform auth rule, FR50] "log out" is the parent platform's action,
            never a Vyapar-owned confirmation flow — this just hands control
            back to the platform entrance that authenticated the member. */}
        <a
          className="vy-card"
          style={{ textDecoration: "none", padding: "14px 18px" }}
          href={process.env.NEXT_PUBLIC_PLATFORM_URL ?? "http://localhost:3100"}
        >
          {t("profile:backToForKhatri")}
        </a>
      </div>
    </main>
  );
}

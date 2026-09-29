"use client";
// [Profile hub] No single FR names a standalone Profile screen; this is the
// honest home for the member's own places — listings, enquiries, and their
// moderation outcomes (FR41, where FR53 wants the appeal path reachable) —
// plus operator tools shown ONLY to members holding that permission, so
// ordinary members never see links that would 403. Compact rows, not
// full-size cards, so everything fits on the first phone screen.
// [Product-owner i18n rule] every string is a key in profile.json.
//
// [IMP39 — desktop layout, owner: "why do I see it as phone only?"] At
// ≥900px the hub is two columns: a sticky identity card (name, the language
// the member uses Vyapar in, and three real counts — listings, open
// enquiries, saved items — each read from an existing endpoint and each a
// link to the place it counts) and, beside it, a grid of described tiles.
// The tiles are the SAME anchors the phone renders: on a phone the glyph and
// description are display:none and the row reads "My listings →" exactly as
// before; on desktop each becomes a tile with a one-line description of
// what is inside. One DOM, two presentations — no second link list to drift.
// Traces to: FR41, FR47, FR40 (entry points), FR53
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import type { EnquirySummary, Me, WorkspaceInvite as Invite, WorkspaceRow } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import Screen from "@/app/components/Screen";
import ProfileSetup from "@/app/components/ProfileSetup";
import Icon from "@/app/components/Icon";
// [IMP38 — Refactor C] The way back to the host platform ("Back to
// ForKhatri" and its URL) comes from the host adapter; standalone has none.
import { useHost, useRoutes } from "@/app/host/HostProvider";
import { formatDate } from "@/lib/format"; // [FE2] Indian date order

// [FR34] a team invitation is an account-level decision, so it waits here

const OPEN_ENQUIRY_STATES = ["open", "awaiting_response", "in_progress"];

interface HubStats {
  listings: number;
  openEnquiries: number;
  saved: number;
}

interface Tile {
  href: string;
  label: string;
  desc: string;
  mark: string;
  /** The phone row showed a trailing arrow for these; Help and Back never had one. */
  arrow: boolean;
}

function HubTile({ tile }: { tile: Tile }) {
  return (
    <a className="vy-card vy-hub-tile" href={tile.href}>
      <span className="vy-hub-tile-mark" aria-hidden="true"><Icon name={tile.mark} size={18} /></span>
      <span className="vy-hub-tile-body">
        <span className="vy-hub-tile-title">
          {tile.label}
          {/* phone: "Label →" inline, exactly as before; desktop: moved to the corner */}
          {tile.arrow && (
            <>
              {" "}
              <span className="vy-hub-tile-arrow" aria-hidden="true">→</span>
            </>
          )}
        </span>
        <span className="vy-hub-tile-desc">{tile.desc}</span>
      </span>
    </a>
  );
}

export default function ProfilePage() {
  const { t, i18n } = useTranslation(["profile", "workspace", "adminCommercial", "privacy", "adminOps", "common", "contracts", "contact"]);
  const [me, setMe] = useState<Me | null>(null);
  const [invites, setInvites] = useState<Invite[]>([]);
  const [workspaces, setWorkspaces] = useState<WorkspaceRow[]>([]);
  const [stats, setStats] = useState<HubStats | null>(null);
  const [busy, setBusy] = useState(false);
  const sdk = useSdk();
  const routes = useRoutes();
  const { platformLink } = useHost();

  async function loadInvites() {
    const [pending, mine] = await Promise.all([
      sdk.workspace.invitesMine().catch((): Invite[] => []),
      sdk.workspace.mine().catch((): WorkspaceRow[] => []),
    ]);
    setInvites(pending);
    setWorkspaces(mine);
  }

  useEffect(() => {
    sdk.members.me().then(setMe).catch(() => setMe(null));
    loadInvites();
    // [IMP39] The identity card's counts. Each comes from an endpoint the
    // app already calls elsewhere; if any one fails the card simply omits
    // the numbers rather than showing a misleading zero.
    Promise.all([
      sdk.listings.mine<unknown[]>(),
      sdk.enquiries.mine("sent"),
      sdk.enquiries.mine("received"),
      sdk.activity.get(),
    ])
      .then(([listings, sent, received, activity]) => {
        const open = (rows: EnquirySummary[]) => rows.filter((e) => OPEN_ENQUIRY_STATES.includes(e.state)).length;
        setStats({ listings: listings.length, openEnquiries: open(sent) + open(received), saved: activity.saved.length });
      })
      .catch(() => setStats(null));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sdk]);

  async function answerInvite(id: string, accept: boolean) {
    setBusy(true);
    try {
      await sdk.workspace.answerInvite(id, accept);
      await loadInvites();
    } finally {
      setBusy(false);
    }
  }

  const memberTiles: Tile[] = [
    { href: routes.myListings, label: t("profile:myListings"), desc: t("profile:hub.desc.myListings"), mark: "listings", arrow: true },
    { href: "/enquiries/mine", label: t("profile:enquiries"), desc: t("profile:hub.desc.enquiries"), mark: "enquiries", arrow: true },
    // [FE2] contracts and calling preferences
    { href: "/contracts", label: t("contracts:nav.title"), desc: t("contracts:nav.desc"), mark: "contract", arrow: true },
    { href: "/profile/contact", label: t("contact:tile.label"), desc: t("contact:tile.desc"), mark: "phone", arrow: true },
    { href: "/moderation/outcomes", label: t("profile:moderationOutcomes"), desc: t("profile:hub.desc.moderationOutcomes"), mark: "moderation", arrow: true },
    { href: "/promotions", label: t("profile:myBoosts"), desc: t("profile:hub.desc.myBoosts"), mark: "boost", arrow: true },
    { href: "/privacy", label: t("privacy:title"), desc: t("profile:hub.desc.privacy"), mark: "privacy", arrow: true },
  ];
  const perms = me?.operator_permissions ?? [];
  const operatorDesc = t("profile:hub.desc.operator");
  const operatorTiles = [
    perms.includes("verification") && { href: "/admin/verification", label: t("profile:verificationQueue") },
    perms.includes("moderation") && { href: "/admin/moderation", label: t("profile:moderationQueue") },
    perms.includes("commercial") && { href: "/admin/commercial", label: t("adminCommercial:title") },
    (perms.includes("content") || perms.includes("analytics")) && { href: "/admin/ops", label: t("adminOps:title") },
  ]
    .filter((x): x is { href: string; label: string } => Boolean(x))
    .map((x): Tile => ({ ...x, desc: operatorDesc, mark: "settings", arrow: true }));
  const supportTiles: Tile[] = [
    { href: "/moderation/outcomes#grievance", label: t("profile:help"), desc: t("profile:hub.desc.help"), mark: "help", arrow: false },
  ];
  // [Platform auth rule, FR50] "log out" is the parent platform's action,
  // never a Vyapar-owned confirmation flow — this just hands control back to
  // the platform entrance that authenticated the member.
  if (platformLink) {
    supportTiles.push({
      href: platformLink.href,
      label: t(platformLink.labelKey as "profile:backToForKhatri"),
      desc: t("profile:hub.desc.back"),
      mark: "back",
      arrow: false,
    });
  }

  const name = me?.display_name ?? t("profile:title");
  const langCode = (me?.language ?? i18n.language ?? "en").slice(0, 2);
  const languageName = t(`common:language.${langCode}` as "common:language.en", { defaultValue: langCode });

  return (
    <Screen width="wide">
      {/* phone: the page title, as before; desktop: the name lives in the identity card */}
      <h1 className="vy-m-only">{name}</h1>
      <div className="vy-hub">
        <aside className="vy-card vy-hub-identity" aria-label={t("profile:title")}>
          <span className="vy-hub-monogram" aria-hidden="true">{name.trim().charAt(0).toUpperCase()}</span>
          <div className="vy-stack" style={{ gap: 4 }}>
            <h1>{name}</h1>
            <p className="vy-muted">{t("profile:hub.languageLine", { language: languageName })}</p>
          </div>
          {stats && (
            <div className="vy-hub-stats">
              <a className="vy-hub-stat" href={routes.myListings}>
                <strong>{stats.listings}</strong>
                <span>{t("profile:hub.statListings")}</span>
              </a>
              <a className="vy-hub-stat" href="/enquiries/mine">
                <strong>{stats.openEnquiries}</strong>
                <span>{t("profile:hub.statOpenEnquiries")}</span>
              </a>
              <a className="vy-hub-stat" href="/activity">
                <strong>{stats.saved}</strong>
                <span>{t("profile:hub.statSaved")}</span>
              </a>
            </div>
          )}
        </aside>

        <div className="vy-hub-main">
          {/* [Owner, 2026-09-22] Business and professional profile, both always
              shown, either optional; the rest of the hub sits below. */}
          <ProfileSetup profiles={me?.profiles} />

          <div className="vy-stack vy-hub-grid" style={{ gap: 8 }}>
            {memberTiles.map((tile) => (
              <HubTile key={tile.href} tile={tile} />
            ))}
          </div>

          {invites.length > 0 && (
            <div className="vy-stack" style={{ gap: 8 }}>
              <h2 className="vy-eyebrow">{t("profile:pendingInvites")}</h2>
              {invites.map((invite) => (
                <div key={invite.id} className="vy-card vy-stack" style={{ gap: 6 }}>
                  <strong>{invite.listing_name ?? invite.listing_id}</strong>
                  <span className="vy-muted" style={{ fontSize: 13 }}>
                    {t("profile:inviteRole", { role: t(`workspace:role.${invite.role}` as "role.admin") })} · {t("workspace:team.expires", { date: formatDate(invite.expires_at, i18n.language) })}
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
              <h2 className="vy-eyebrow">{t("profile:workspaces")}</h2>
              <div className="vy-stack vy-hub-grid" style={{ gap: 8 }}>
                {workspaces.map((w) => (
                  <HubTile
                    key={w.listing_id}
                    tile={{
                      href: routes.workspace(w.listing_id),
                      label: `${w.listing_name} · ${t(`workspace:role.${w.role}` as "role.owner")}`,
                      desc: t("profile:hub.desc.workspace"),
                      mark: "workspace",
                      arrow: true,
                    }}
                  />
                ))}
              </div>
            </div>
          )}

          {operatorTiles.length > 0 && (
            <div className="vy-stack" style={{ gap: 8 }}>
              <h2 className="vy-eyebrow">{t("profile:operatorTools")}</h2>
              <div className="vy-stack vy-hub-grid" style={{ gap: 8 }}>
                {operatorTiles.map((tile) => (
                  <HubTile key={tile.href} tile={tile} />
                ))}
              </div>
            </div>
          )}

          <div className="vy-stack vy-hub-grid" style={{ gap: 8 }}>
            {supportTiles.map((tile) => (
              <HubTile key={tile.href} tile={tile} />
            ))}
          </div>
        </div>
      </div>
    </Screen>
  );
}

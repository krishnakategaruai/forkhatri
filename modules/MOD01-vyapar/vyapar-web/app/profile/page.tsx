"use client";
// [Profile hub] The home for the member's own places — their profile,
// requests, contracts, saved items, promotions, workspaces, settings and
// moderation outcomes (FR41, where FR53 wants the appeal path reachable) —
// plus operator tools shown ONLY to members holding that permission.
// [Product-owner i18n rule] every string is a key in profile.json.
//
// [Owner, 2026-09-29/30] Rebuilt in the 2026 language, around ONE profile
// ("each user will get one profile"):
//   1. identity header — monogram, name, locality and language, all from
//      what ForKhatri and first run already know (never re-asked), with
//      three useful counts: open requests, saved, recommendations;
//   2. "Your work profile" — the one profile (skills, headline, one trust or
//      state line), or one card to set it up;
//   3. "My business" — the optional business section, or a quiet card to
//      add it;
//   4. one list of shortcuts (Your work / Settings / Support), icon + label
//      + one-line hint, 56px rows — not nine big tiles.
// The old hub reused `.vy-hub`, the command hub's own class, so the page was
// drawn as one grey pill, and the desktop tile grid leaked onto phones with
// cards clipped off the right edge. Desktop (≥1024): profile on the left,
// shortcuts in a sticky right column.
// Traces to: FR41, FR47, FR40 (entry points), FR53
import { useEffect, useState } from "react";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { Bookmark, FileText, Globe, Inbox, LayoutGrid, LifeBuoy, Lock, MapPin, Megaphone, Phone, ShieldAlert, ShieldCheck, Undo2, Wrench } from "lucide-react";
import type { EnquirySummary, Listing, WorkspaceInvite as Invite, WorkspaceRow } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import Screen from "@/app/components/Screen";
import ShortcutList, { type Shortcut, type ShortcutGroup } from "@/app/components/account/ShortcutList";
import AccountProfileCard, { AddProfileCard } from "@/app/components/account/AccountProfileCard";
import { useMyProfile } from "@/app/components/account/useMyProfile";
import { NoPromotionNote } from "@/app/components/trust/Profession";
// [IMP38 — Refactor C] The way back to the host platform ("Back to
// ForKhatri" and its URL) comes from the host adapter; standalone has none.
import { useHost, useRoutes } from "@/app/host/HostProvider";
import { formatDate } from "@/lib/format"; // [FE2] Indian date order
import "@/app/styles/account-2026.css";

// [FR34] a team invitation is an account-level decision, so it waits here

const OPEN_ENQUIRY_STATES = ["open", "awaiting_response", "in_progress"];

interface HubStats {
  openEnquiries: number;
  saved: number;
  recommends: number | null;
}

export default function ProfilePage() {
  const { t, i18n } = useTranslation(["profile", "workspace", "adminCommercial", "privacy", "adminOps", "common", "contracts", "contact", "trustSafety", "listings"]);
  const profile = useMyProfile();
  const me = profile.data;
  const [invites, setInvites] = useState<Invite[]>([]);
  const [workspaces, setWorkspaces] = useState<WorkspaceRow[]>([]);
  const [stats, setStats] = useState<HubStats | null>(null);
  const [recommends, setRecommends] = useState<number | null>(null);
  // [Trust pack §3] Settings shows "Restrictions" only while something is restricted.
  const [restricted, setRestricted] = useState(0);
  const [busy, setBusy] = useState(false);
  const sdk = useSdk();
  const routes = useRoutes();
  const { platformLink } = useHost();

  function loadInvites() {
    return Promise.all([
      sdk.workspace.invitesMine().catch((): Invite[] => []),
      sdk.workspace.mine().catch((): WorkspaceRow[] => []),
    ]).then(([pending, mine]) => {
      setInvites(pending);
      setWorkspaces(mine);
    });
  }

  useEffect(() => {
    void loadInvites();
    // Counts from endpoints the app already calls elsewhere; if one fails
    // the numbers are left out rather than shown as a misleading zero.
    Promise.all([sdk.enquiries.mine("sent"), sdk.enquiries.mine("received"), sdk.activity.get()])
      .then(([sent, received, activity]) => {
        const open = (rows: EnquirySummary[]) => rows.filter((e) => OPEN_ENQUIRY_STATES.includes(e.state)).length;
        setStats({ openEnquiries: open(sent) + open(received), saved: activity.saved.length, recommends: null });
      })
      .catch(() => setStats(null));
    sdk.trustPack
      .myRestrictions()
      .then((rows) => setRestricted(rows.length))
      .catch(() => setRestricted(0));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sdk]);

  // Recommendations earned on the profile and the business section.
  const ids = [me?.work?.id, me?.business?.id].filter((x): x is string => !!x).join(",");
  useEffect(() => {
    if (!ids) return;
    Promise.all(ids.split(",").map((id) => sdk.listings.get<Listing>(id).catch(() => null)))
      .then((rows) => setRecommends(rows.reduce((n, l) => n + (l?.reputation?.recommends ?? 0), 0)))
      .catch(() => setRecommends(null));
  }, [ids, sdk]);

  async function answerInvite(id: string, accept: boolean) {
    setBusy(true);
    try {
      await sdk.workspace.answerInvite(id, accept);
      await loadInvites();
    } finally {
      setBusy(false);
    }
  }

  const name = me?.name || t("profile:title");
  const noPromotion = !!me?.profession?.restricted && !me.profession.allow_promotion;
  const langCode = (me?.language ?? i18n.language ?? "en").slice(0, 2);
  const languageName = t(`common:language.${langCode}` as "common:language.en", { defaultValue: langCode });

  const work: Shortcut[] = [
    { href: "/enquiries/mine", label: t("profile:enquiries"), hint: t("profile:hub.desc.enquiries"), icon: Inbox, tint: "brand", count: stats?.openEnquiries },
    { href: "/contracts", label: t("contracts:nav.title"), hint: t("contracts:nav.desc"), icon: FileText, tint: "indigo" },
    { href: "/activity", label: t("profile:hub.saved"), hint: t("profile:hub.desc.saved"), icon: Bookmark, tint: "teal", count: stats?.saved },
    // [Trust pack §4] No promotions for a profession whose council forbids advertising.
    ...(noPromotion ? [] : [{ href: "/promotions", label: t("profile:myBoosts"), hint: t("profile:hub.desc.myBoosts"), icon: Megaphone, tint: "amber" as const }]),
    ...workspaces.map(
      (w): Shortcut => ({
        href: routes.workspace(w.listing_id),
        label: w.listing_name,
        hint: `${t("profile:workspaces")} · ${t(`workspace:role.${w.role}` as "role.owner")}`,
        icon: LayoutGrid,
        tint: "plum",
      }),
    ),
  ];
  const settings: Shortcut[] = [
    { href: "/profile/contact", label: t("contact:tile.label"), hint: t("contact:tile.desc"), icon: Phone, tint: "green" },
    { href: "/privacy", label: t("privacy:title"), hint: t("profile:hub.desc.privacy"), icon: Lock, tint: "sky" },
    ...(restricted > 0
      ? [{ href: "/profile/restrictions", label: t("trustSafety:restrictions.title"), hint: t("trustSafety:restrictions.hubHint"), icon: ShieldAlert, tint: "warning" as const, count: restricted }]
      : []),
    { href: "/moderation/outcomes", label: t("profile:moderationOutcomes"), hint: t("profile:hub.desc.moderationOutcomes"), icon: ShieldCheck },
  ];
  const perms = me?.operatorPermissions ?? [];
  const operator: Shortcut[] = [
    perms.includes("verification") && { href: "/admin/verification", label: t("profile:verificationQueue") },
    perms.includes("moderation") && { href: "/admin/moderation", label: t("profile:moderationQueue") },
    perms.includes("commercial") && { href: "/admin/commercial", label: t("adminCommercial:title") },
    (perms.includes("content") || perms.includes("analytics")) && { href: "/admin/ops", label: t("adminOps:title") },
  ]
    .filter((x): x is { href: string; label: string } => Boolean(x))
    .map((x): Shortcut => ({ ...x, hint: t("profile:hub.desc.operator"), icon: Wrench, tint: "warning" }));
  const support: Shortcut[] = [{ href: "/moderation/outcomes#grievance", label: t("profile:help"), hint: t("profile:hub.desc.help"), icon: LifeBuoy }];
  // [Platform auth rule, FR50] "log out" is the parent platform's action;
  // this just hands control back to the platform entrance.
  if (platformLink) {
    support.push({ href: platformLink.href, label: t(platformLink.labelKey as "profile:backToForKhatri"), hint: t("profile:hub.desc.back"), icon: Undo2 });
  }
  const groups: ShortcutGroup[] = [
    { title: t("profile:hub.sections.work"), items: work },
    { title: t("profile:hub.sections.settings"), items: settings },
    { title: t("profile:operatorTools"), items: operator },
    { title: t("profile:hub.sections.support"), items: support },
  ];

  const statCells = stats
    ? [
        { href: "/enquiries/mine", n: stats.openEnquiries, label: t("profile:hub.statOpenEnquiries") },
        { href: "/activity", n: stats.saved, label: t("profile:hub.statSaved") },
        ...(recommends != null ? [{ href: me?.work ? `/listings/${me.work.id}` : "/profile", n: recommends, label: t("profile:hub.statRecommends") }] : []),
      ]
    : [];

  return (
    <Screen width="wide">
      <div className="vy-acct-two">
        <div className="vy-acct-two-main">
          <section className="vy-card vy-acct-identity" aria-label={t("profile:title")}>
            <span className="vy-acct-monogram" aria-hidden="true">
              {name.trim().charAt(0).toUpperCase()}
            </span>
            <div className="vy-acct-identity-text">
              <h1>{name}</h1>
              <p className="vy-acct-meta">
                {me?.locality && (
                  <span>
                    <MapPin size={14} strokeWidth={2} aria-hidden="true" />
                    {me.locality}
                  </span>
                )}
                <span>
                  <Globe size={14} strokeWidth={2} aria-hidden="true" />
                  {t("profile:hub.languageLine", { language: languageName })}
                </span>
              </p>
            </div>
            {statCells.length > 0 && (
              <div className="vy-acct-stats" style={{ gridTemplateColumns: `repeat(${statCells.length}, minmax(0, 1fr))` }}>
                {statCells.map((s) => (
                  <Link key={s.label} className="vy-acct-stat" href={s.href} transitionTypes={["vy-forward"]}>
                    <strong className="vy-num">{s.n}</strong>
                    <span>{s.label}</span>
                  </Link>
                ))}
              </div>
            )}
          </section>

          {invites.length > 0 && (
            <section className="vy-acct-section" aria-labelledby="invites-title">
              <div className="vy-acct-section-head">
                <h2 id="invites-title" className="vy-section-title">{t("profile:pendingInvites")}</h2>
              </div>
              {invites.map((invite) => (
                <div key={invite.id} className="vy-card vy-acct-invite">
                  <div className="vy-acct-row-text">
                    <span className="vy-acct-row-label">{invite.listing_name ?? invite.listing_id}</span>
                    <span className="vy-acct-hint">
                      {t("profile:inviteRole", { role: t(`workspace:role.${invite.role}` as "role.admin") })} · <span className="vy-num">{t("workspace:team.expires", { date: formatDate(invite.expires_at, i18n.language) })}</span>
                    </span>
                  </div>
                  <div className="vy-row">
                    <button className="vy-btn vy-btn-primary" disabled={busy} onClick={() => answerInvite(invite.id, true)}>{t("profile:accept")}</button>
                    <button className="vy-btn vy-btn-ghost" disabled={busy} onClick={() => answerInvite(invite.id, false)}>{t("profile:decline")}</button>
                  </div>
                </div>
              ))}
            </section>
          )}

          {me && (
            <>
              <section className="vy-acct-section" aria-labelledby="work-title">
                <div className="vy-acct-section-head">
                  <div className="vy-stack" style={{ gap: 2, minWidth: 0 }}>
                    <h2 id="work-title" className="vy-section-title">{t("profile:profiles.workSection")}</h2>
                    <p>{t("profile:profiles.workSectionHint")}</p>
                  </div>
                </div>
                {me.work ? (
                  <>
                    <AccountProfileCard profile={me.work} href={`/listings/${me.work.id}`} />
                    {noPromotion && me.profession && <NoPromotionNote profession={me.profession} />}
                  </>
                ) : (
                  <AddProfileCard kind="professional" href={routes.newListing} />
                )}
              </section>

              <section className="vy-acct-section" aria-labelledby="business-title">
                <div className="vy-acct-section-head">
                  <div className="vy-stack" style={{ gap: 2, minWidth: 0 }}>
                    <h2 id="business-title" className="vy-section-title">{t("profile:profiles.businessSection")}</h2>
                    <p>{t("profile:profiles.businessSectionHint")}</p>
                  </div>
                </div>
                {me.business ? (
                  <AccountProfileCard profile={me.business} href={`/listings/${me.business.id}`} />
                ) : (
                  <AddProfileCard kind="business" href={`${routes.newListing}?kind=business`} />
                )}
              </section>
            </>
          )}
          {!me && !profile.error && <div className="vy-skeleton" style={{ height: 220, borderRadius: "var(--radius-card)" }} aria-hidden="true" />}
        </div>

        <aside className="vy-acct-two-side">
          <ShortcutList groups={groups} ariaLabel={t("profile:hub.shortcuts")} />
        </aside>
      </div>
    </Screen>
  );
}

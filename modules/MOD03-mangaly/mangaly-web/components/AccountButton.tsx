"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { Avatar } from "@/components/Avatar";
import { getSession, type Session } from "@/lib/auth";
import { getMemberProfile } from "@/lib/profile";
import { relationKey } from "@/lib/homeCircle";
import { entranceUrl, signOutOfForKhatri } from "@/lib/platform";

/* Who is signed in, always visible: the right-most item of every top-level
 * header (the owner's standing rule — profile last, top right). The owner
 * could not tell which person a tab was signed in as; a matrimony app where
 * a parent and a candidate may share a phone needs that answer on every
 * screen, not buried in a settings page.
 *
 * The menu names the person and every role they hold — their own candidate
 * profile and each circle they help in, with the relation (roles are per
 * relation, never per account) — then the account actions. */

export default function AccountButton() {
  const { t } = useTranslation(["common", "circle", "profile"]);
  const [session, setSession] = useState<Session | null>(null);
  const [open, setOpen] = useState(false);
  const [memberPhoto, setMemberPhoto] = useState<string | null>(null);
  const root = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let alive = true;
    getSession()
      .then(async (s) => {
        if (!alive) return;
        setSession(s);
        // [DEC-V1-027] Someone who is not a candidate shows their member photo.
        if (s && !s.own_profile) {
          const m = await getMemberProfile().catch(() => null);
          if (alive) setMemberPhoto(m?.photo_url ?? null);
        }
      })
      .catch(() => undefined);
    return () => {
      alive = false;
    };
  }, []);

  // Close on outside click or Escape.
  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (root.current && !root.current.contains(e.target as Node))
        setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  if (!session)
    return <span className="account__placeholder" aria-hidden="true" />;

  const name = session.display_name || session.own_profile?.name || "";
  const photo = session.own_profile?.primary_photo_url ?? memberPhoto;

  return (
    <div className="account" ref={root}>
      <button
        type="button"
        className="account__button"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={t("common:account.menu", { name })}
        title={name}
        onClick={() => setOpen((o) => !o)}
      >
        <Avatar name={name} photoUrl={photo} size={34} />
        {/* First name under the picture, small — whose screen this is, at a glance. */}
        <span className="account__caption">{name.split(" ")[0]}</span>
      </button>

      {open && (
        <div className="account__menu" role="menu">
          <div className="account__who">
            <Avatar name={name} photoUrl={photo} size={48} />
            <span className="account__who-text">
              <span className="account__name">{name}</span>
              <span className="caption">{t("common:account.signedIn")}</span>
            </span>
          </div>

          <div className="account__roles">
            <span className="account__label">{t("common:account.roles")}</span>
            {session.own_profile && (
              <span className="account__role">
                {t("common:account.candidateRole", {
                  lookingFor: session.own_profile.looking_for
                    ? t(
                        `profile:option.looking_for.${session.own_profile.looking_for}`,
                      )
                    : "—",
                })}
              </span>
            )}
            {session.circles.map((c) => (
              <span key={c.candidate_profile_id} className="account__role">
                {t("common:account.helperRole", {
                  relationship: t(relationKey(c.relation, c.relationship)),
                  name: c.candidate_name,
                })}
              </span>
            ))}
            {!session.own_profile && session.circles.length === 0 && (
              <span className="account__role account__role--muted">
                {t("common:account.noRole")}
              </span>
            )}
          </div>

          <nav className="account__links">
            {session.own_profile ? (
              <Link href="/me" role="menuitem" onClick={() => setOpen(false)}>
                {t("common:account.myProfile")}
              </Link>
            ) : (
              <Link
                href="/profile/create"
                role="menuitem"
                onClick={() => setOpen(false)}
              >
                {t("common:account.createProfile")}
              </Link>
            )}
            {session.managed_profiles.map((m) => (
              <Link
                key={m.account_id}
                href={`/me?manage=${m.account_id}`}
                role="menuitem"
                onClick={() => setOpen(false)}
              >
                {t("common:account.fillIn", { name: m.name.split(" ")[0] })}
              </Link>
            ))}
            <Link
              href="/profile/create?for=child"
              role="menuitem"
              onClick={() => setOpen(false)}
            >
              {t("common:account.createForChild")}
            </Link>
            <Link href="/circle" role="menuitem" onClick={() => setOpen(false)}>
              {t("common:account.homeCircle")}
            </Link>
            {/* [DEC-V1-030] The way back to ForKhatri lives here on a phone
                (and in the sidebar on a desktop) instead of taking a slot in
                every page's header. A plain <a>: the hub is another zone.
                Once, at the end of the menu, just above sign-out. */}
            <a href={entranceUrl()} role="menuitem">
              {t("common:platform.backToHub")}
            </a>
            <button
              type="button"
              role="menuitem"
              className="account__signout"
              onClick={() => void signOutOfForKhatri()}
            >
              {t("common:account.signOut")}
            </button>
          </nav>
        </div>
      )}
    </div>
  );
}

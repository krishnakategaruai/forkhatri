"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import AccountButton from "@/components/AccountButton";
import DeleteMyData from "@/components/DeleteMyData";
import { Avatar } from "@/components/Avatar";
import Icon from "@/components/Icon";
import ForKhatriHubLink from "@/components/ForKhatriHubLink";
import PhotoCheckCard from "@/components/PhotoCheckCard";
import PhotoChoice from "@/components/PhotoChoice";
import { resolveMediaUrl } from "@/lib/api";
import { logOut, type Session } from "@/lib/auth";
import { relationKey } from "@/lib/homeCircle";
import {
  getMemberProfile,
  saveMemberProfile,
  uploadMemberPhoto,
  type MemberProfile,
} from "@/lib/profile";

import "@/app/me/me.css";

/* DEC-V1-027 · "My profile" for a parent, sibling or relative.
 *
 * Owner: "basic authentication of login happens in ForKhatri and each module
 * has its own way of my profile." Someone who is not looking for a match
 * still has a Mangalya profile of their own: their photo, a line about them,
 * their city and work, the families they belong to in Mangalya, and the
 * profiles they made for a child. It is never searchable and carries no
 * biodata. Their photo is what the families they talk to see, and what the
 * face check compares against before they may make a profile for a child. */
export default function MemberMe({ session }: { session: Session }) {
  const { t, i18n } = useTranslation(["common", "profile", "circle", "member"]);
  const language = i18n.language || "en";
  const [member, setMember] = useState<MemberProfile | null>(null);
  const [draft, setDraft] = useState({ about: "", city: "", occupation: "" });
  const [saved, setSaved] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [uploading, setUploading] = useState(false);
  const [photoError, setPhotoError] = useState(false);
  const [photoKey, setPhotoKey] = useState(0);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let active = true;
    void getMemberProfile().then((m) => {
      if (!active) return;
      setMember(m);
      setDraft({ about: m?.about ?? "", city: m?.city ?? "", occupation: m?.occupation ?? "" });
    });
    return () => {
      active = false;
    };
  }, []);

  const dirty =
    draft.about !== (member?.about ?? "") ||
    draft.city !== (member?.city ?? "") ||
    draft.occupation !== (member?.occupation ?? "");

  async function save() {
    setSaved("saving");
    const outcome = await saveMemberProfile(draft);
    if (outcome.ok) {
      setMember(outcome.data);
      setSaved("saved");
    } else {
      setSaved("error");
    }
  }

  async function onPhoto(file: File | undefined) {
    if (!file) return;
    setUploading(true);
    setPhotoError(false);
    const m = await uploadMemberPhoto(file);
    setUploading(false);
    setPhotoKey((k) => k + 1);
    if (m) setMember(m);
    else setPhotoError(true);
  }

  const first = (name: string) => name.split(" ")[0];

  return (
    <>
      <header className="topbar me-top">
        <h1>{t("member:title")}</h1>
        <div className="topbar__actions">
          <ForKhatriHubLink />
          {/* The card below already shows you; the account menu opens from
              a small menu icon rather than a second copy of your photo. */}
          <span className="me-account">
            <AccountButton />
          </span>
        </div>
      </header>
      <main className="screen member me-member">
        <div className="member__grid">
          <section className="member__card member__id">
            <button
              type="button"
              className={`member__photo${member?.photo_url ? "" : " member__photo--empty"}`}
              onClick={() => fileRef.current?.click()}
              aria-label={member?.photo_url ? t("member:photo.change") : t("member:photo.add")}
              disabled={uploading}
            >
              {member?.photo_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img key={photoKey} src={resolveMediaUrl(member.photo_url) ?? ""} alt="" />
              ) : (
                <span className="member__photo-empty">
                  <Avatar name={session.display_name} size={112} />
                </span>
              )}
              <span className="member__photo-badge" aria-hidden="true">
                <Icon name="camera" size={16} />
              </span>
            </button>
            <input
              ref={fileRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              hidden
              onChange={(e) => void onPhoto(e.target.files?.[0])}
            />
            <h2 className="member__name">{session.display_name}</h2>
            <p className="caption member__role">{t("member:role")}</p>
            <PhotoChoice disabled={uploading} onFile={(f) => onPhoto(f)} />
            {photoError && <p className="member__nudge" role="alert">{t("member:photo.error")}</p>}
            {!member?.photo_url && <p className="member__nudge">{t("member:photo.whyShort")}</p>}
            <PhotoCheckCard />
          </section>

          <div className="member__main">
            <section className="member__card member__card--primary">
              <h3 className="member__h">{t("member:families.title")}</h3>
              {session.circles.length === 0 ? (
                <p className="caption" style={{ margin: 0 }}>{t("member:families.none")}</p>
              ) : (
                <ul className="member__list">
                  {session.circles.map((c) => (
                    <li key={c.candidate_account_id} className="member__row">
                      <Avatar photoUrl={c.primary_photo_url} name={c.candidate_name} size={48} />
                      <span className="member__row-text">
                        <strong>{c.candidate_name}</strong>
                        <span>
                          {t("member:families.youAre", {
                            relation: t(relationKey(c.relation, c.relationship)).toLocaleLowerCase(language),
                            name: first(c.candidate_name),
                          })}
                        </span>
                      </span>
                      <span className="member__row-actions">
                        <Link className="btn me-tonal" href="/circle">{t("member:families.circle")}</Link>
                        <Link className="btn me-tonal me-tonal--accent" href="/discover">
                          {t("member:families.matches", { name: first(c.candidate_name) })}
                        </Link>
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section className="member__card">
              <h3 className="member__h">{t("member:about.title")}</h3>
              <p className="caption" style={{ margin: 0 }}>{t("member:about.hint")}</p>
              <div className="field">
                <label htmlFor="member-about" className="member__label">{t("member:about.aboutLabel")}</label>
                <textarea
                  id="member-about"
                  className="field__input member__textarea"
                  rows={3}
                  maxLength={500}
                  placeholder={t("member:about.aboutPlaceholder")}
                  value={draft.about}
                  onChange={(e) => {
                    setDraft({ ...draft, about: e.target.value });
                    setSaved("idle");
                  }}
                />
              </div>
              <div className="member__two">
                {(["city", "occupation"] as const).map((key) => (
                  <div className="field" key={key}>
                    {/* A visible label above the field: a placeholder
                        would vanish as soon as someone types. */}
                    <label htmlFor={`member-${key}`} className="member__label">
                      {t(`member:about.${key}`)}
                    </label>
                    <input
                      id={`member-${key}`}
                      className="field__input"
                      maxLength={200}
                      placeholder={t(`member:about.${key}Placeholder`)}
                      value={draft[key]}
                      onChange={(e) => {
                        setDraft({ ...draft, [key]: e.target.value });
                        setSaved("idle");
                      }}
                    />
                  </div>
                ))}
              </div>
              <div className="member__actions">
                <span className="caption" role="status">
                  {saved === "saved" ? t("member:about.saved") : saved === "error" ? t("member:about.error") : ""}
                </span>
                {/* Save appears only once something has changed. */}
                {dirty && (
                  <button
                    type="button"
                    className="btn btn--primary"
                    disabled={saved === "saving"}
                    onClick={save}
                  >
                    {t("member:about.save")}
                  </button>
                )}
              </div>
            </section>

            <section className="member__card">
              <h3 className="member__h">{t("member:made.title")}</h3>
              {session.managed_profiles.length > 0 && (
                <ul className="member__list">
                  {session.managed_profiles.map((m) => (
                    <li key={m.account_id} className="member__row">
                      <Avatar photoUrl={m.primary_photo_url} name={m.name} size={48} />
                      <span className="member__row-text">
                        <strong>{m.name}</strong>
                        <span>{t("member:made.waiting")}</span>
                      </span>
                      <Link className="btn me-tonal" href={`/me?manage=${m.account_id}`}>
                        {t("member:made.edit")}
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
              <p className="caption" style={{ margin: 0 }}>{t("member:made.hint")}</p>
              <Link className="btn btn--primary member__make" href="/profile/create?for=child">
                {t("member:made.cta")}
              </Link>
            </section>

            <button type="button" className="btn member__signout" onClick={() => void logOut()}>
              {t("member:signOut")}
            </button>
            <DeleteMyData />
          </div>
        </div>
      </main>
    </>
  );
}

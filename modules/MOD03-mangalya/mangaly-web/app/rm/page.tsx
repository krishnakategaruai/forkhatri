"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import AccountButton from "@/components/AccountButton";
import { Avatar } from "@/components/Avatar";
import ForKhatriHubLink from "@/components/ForKhatriHubLink";
import { resolveMediaUrl } from "@/lib/api";
import { openDirect, threadHref } from "@/lib/messages";
import { decideSuggestion, formatWhen, getMyRm, type MyRm, type RmSuggestion } from "@/lib/rm";

import "./rm.css";

/* [DEC-V1-032] The family's page for their relationship manager: who they
 * are, what they have put forward (with the note, in the member's language),
 * and every call and meeting they logged. A parent reads the same page for
 * the candidate they help (`?for=<candidate>`). Liking a suggestion sends
 * nothing to anyone; it tells the RM, who may set up a call. */

function RmPage() {
  const { t, i18n } = useTranslation(["rm", "common", "profile"]);
  const router = useRouter();
  const params = useSearchParams();
  const forCandidate = params.get("for") ?? undefined;
  const [mine, setMine] = useState<MyRm | null | undefined>(undefined);
  const [busy, setBusy] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    getMyRm(forCandidate)
      .then((r) => alive && setMine(r))
      .catch(() => alive && setMine(null));
    return () => {
      alive = false;
    };
  }, [forCandidate]);

  const decide = async (s: RmSuggestion, decision: "liked" | "passed") => {
    setBusy(s.id);
    const r = await decideSuggestion(s.id, decision, forCandidate);
    setBusy(null);
    if (r.ok && mine) {
      setMine({ ...mine, suggestions: mine.suggestions.map((x) => (x.id === s.id ? r.data : x)) });
    }
  };

  const message = async () => {
    if (!mine) return;
    const r = await openDirect(mine.rm.account_id);
    if (r.ok) router.push(threadHref(r.data.conversation_id, "direct"));
  };

  return (
    <>
      <header className="topbar">
        <h1 className="topbar__title">{t("rm:page.title")}</h1>
        <div className="topbar__actions">
          <ForKhatriHubLink />
          <AccountButton />
        </div>
      </header>
      <main className="screen rm-page">
        {mine === undefined ? (
          <p className="caption">{t("common:state.loading")}</p>
        ) : mine === null ? (
          <div className="empty rm-empty">
            <h2 className="h3">{t("rm:page.none.title")}</h2>
            <p className="muted">{t("rm:page.none.body")}</p>
          </div>
        ) : (
          <>
            <section className="card rm-card rm-card--page">
              <div className="rm-card__who">
                <Avatar name={mine.rm.display_name} photoUrl={resolveMediaUrl(mine.rm.photo_url)} size={72} />
                <div className="rm-card__text">
                  <span className="rm-card__name">{mine.rm.display_name}</span>
                  <span className="caption">{t("rm:page.role")}</span>
                  <span className="caption">
                    {mine.rm.languages.length > 0 &&
                      t("rm:card.speaks", {
                        languages: mine.rm.languages
                          .map((l) => t(`rm:language.${l.toLowerCase()}`, { defaultValue: l }))
                          .join(", "),
                      })}
                    {mine.rm.region ? ` · ${mine.rm.region}` : ""}
                  </span>
                </div>
              </div>
              <div className="rm-card__actions">
                <button type="button" className="btn btn--primary btn--sm" onClick={message}>
                  {t("rm:card.message")}
                </button>
              </div>
              <p className="caption rm-promise">{t("rm:page.promise")}</p>
            </section>

            <section className="section">
              <div className="section__head">
                <h3 className="h3" style={{ margin: 0 }}>
                  {t("rm:page.suggestions.title")}
                </h3>
                {mine.suggestions.length > 0 && (
                  <span className="caption">{t("rm:page.suggestions.count", { count: mine.suggestions.length })}</span>
                )}
              </div>
              {mine.suggestions.length === 0 ? (
                <p className="caption">{t("rm:page.suggestions.empty")}</p>
              ) : (
                <ul className="rm-wall">
                  {mine.suggestions.map((s) => {
                    const p = s.person;
                    const title = p?.open_name
                      ? [p.open_name, p.age].filter(Boolean).join(", ")
                      : p?.age
                        ? t("profile:hub.ageYears", { age: p.age })
                        : "";
                    const city = p?.locality?.split(",")[0]?.trim();
                    return (
                      <li key={s.id} className={`rm-tile${s.member_decision ? ` rm-tile--${s.member_decision}` : ""}`}>
                        <Link href={`/profile/${s.suggested_account_id}`} className="rm-tile__link" prefetch={false}>
                          <div className="rm-tile__photo">
                            {p?.photo_url ? (
                              // eslint-disable-next-line @next/next/no-img-element
                              <img src={resolveMediaUrl(p.photo_url) ?? ""} alt="" loading="lazy" decoding="async" />
                            ) : (
                              <span className="rm-tile__nophoto">
                                <Avatar anonymized size={64} />
                              </span>
                            )}
                            {s.member_decision && (
                              <span className="rm-tile__state">{t(`rm:decision.${s.member_decision}`)}</span>
                            )}
                          </div>
                          <div className="rm-tile__text">
                            <span className="rm-tile__title">{[title, city].filter(Boolean).join(" · ")}</span>
                            {(p?.profession || p?.education_level) && (
                              <span className="rm-tile__line">
                                {[p?.profession, p?.education_level ? t(`profile:option.highest_education_level.${p.education_level}`, { defaultValue: p.education_level }) : null].filter(Boolean).join(" · ")}
                              </span>
                            )}
                          </div>
                        </Link>
                        {s.note && (
                          <blockquote className="rm-tile__note">
                            <span className="rm-tile__by">{t("rm:page.suggestions.noteBy", { name: mine.rm.display_name })}</span>
                            {s.note}
                          </blockquote>
                        )}
                        {!s.member_decision && (
                          <div className="rm-tile__actions">
                            <button
                              type="button"
                              className="btn btn--primary btn--sm"
                              disabled={busy === s.id}
                              onClick={() => decide(s, "liked")}
                            >
                              {t("rm:decision.like")}
                            </button>
                            <button
                              type="button"
                              className="btn btn--ghost btn--sm"
                              disabled={busy === s.id}
                              onClick={() => decide(s, "passed")}
                            >
                              {t("rm:decision.pass")}
                            </button>
                          </div>
                        )}
                      </li>
                    );
                  })}
                </ul>
              )}
            </section>

            <section className="section">
              <div className="section__head">
                <h3 className="h3" style={{ margin: 0 }}>
                  {t("rm:page.log.title")}
                </h3>
              </div>
              {mine.interactions.length === 0 ? (
                <p className="caption">{t("rm:page.log.empty")}</p>
              ) : (
                <ol className="rm-log">
                  {mine.interactions.map((i) => {
                    const upcoming = !!i.scheduled_at && new Date(i.scheduled_at).getTime() > Date.now();
                    return (
                      <li key={i.id} className={`rm-log__item${upcoming ? " is-upcoming" : ""}`}>
                        <span className="rm-log__kind">{t(`rm:interaction.kind.${i.kind}`)}</span>
                        <span className="rm-log__when">
                          {formatWhen(i.scheduled_at ?? i.created_at, i18n.language)}
                          {upcoming ? ` · ${t("rm:page.log.upcoming")}` : ""}
                        </span>
                        {i.summary && <span className="rm-log__summary">{i.summary}</span>}
                      </li>
                    );
                  })}
                </ol>
              )}
            </section>
          </>
        )}
      </main>
    </>
  );
}

export default function RmPageWithParams() {
  return (
    <Suspense fallback={null}>
      <RmPage />
    </Suspense>
  );
}

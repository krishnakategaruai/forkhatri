"use client";

import Link from "next/link";
import Icon from "@/components/Icon";
import { useLoaderHold } from "@/lib/useLoaderHold";
import SacredLoader from "@/components/SacredLoader";
import MotionTitle from "@/components/MotionTitle";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { resolveMediaUrl } from "@/lib/api";
import AccountButton from "@/components/AccountButton";
import ForKhatriHubLink from "@/components/ForKhatriHubLink";
import { Avatar } from "@/components/Avatar";
import { getSession, type Session } from "@/lib/auth";
import { reportOutage } from "@/lib/outage";
import { redirectToEntrance } from "@/lib/platform";
import { getContexts, listMembers, type Member } from "@/lib/homeCircle";
import {
  getCompleteness,
  getOwnProfile,
  type CompletenessReport,
  type Profile,
} from "@/lib/profile";
import { search, type SearchResult } from "@/lib/discovery";
import { listIncoming, type Connection } from "@/lib/connections";

/* FR090 · TR090 · UX01 · UI01 · SP090
 *
 * Launch routing. Checks the session server-side and shows either the signed-in
 * home or the signed-out entry point. TR090 requires this to fall back to a
 * usable screen rather than hanging — a routine condition for this module's
 * tier-2/3 connectivity audience, not an edge case — so a failed check renders
 * the signed-out state instead of an indefinite spinner.
 *
 * [BR01/FR001] A signed-in account with no saved profile is routed straight
 * into the existence-tier wizard — BR01 calls a saved profile "the floor of
 * the product", so there is nothing useful for a profile-less account to do
 * on Home yet. FR091 (Onboarding) sits between OTP verification and this
 * check in UX03's full flow but is not built in this pass (progressive,
 * buildable slices) — skipping stright to the wizard is a scope reduction,
 * not a UX03 contradiction: onboarding is purely explanatory content with no
 * gating behaviour of its own. */

type State =
  | { phase: "checking" }
  | {
      phase: "in";
      session: Session;
      profile: Profile | null;
      completeness: CompletenessReport | null;
      matches: SearchResult[];
      matchTotal: number;
      incoming: Connection[];
      members: Member[];
    }
  | { phase: "out" };

/* Requests this person may answer: their own, and — as a parent or guardian —
   each candidate's they help (the same set the request popup offers). Home
   used to count only their own, so a father with a request waiting for his
   son read "None waiting right now" beside the popup asking him to answer. */
async function waitingOnThisFamily(
  session: { circles?: { relationship: string; candidate_account_id: string }[] },
  ownProfile: boolean,
): Promise<Connection[]> {
  const jobs: Promise<Connection[]>[] = [];
  if (ownProfile) jobs.push(listIncoming());
  for (const c of session.circles ?? []) {
    if (c.relationship === "parent" || c.relationship === "guardian") {
      jobs.push(listIncoming(c.candidate_account_id));
    }
  }
  const all = (await Promise.all(jobs.map((j) => j.catch(() => [] as Connection[])))).flat();
  return all.filter((r) => r.status === "pending");
}

export default function HomePage() {
  // [owner 2026-09-25] The loader stays at least a second, never a flash.
  const loaderHold = useLoaderHold();
  const { t, i18n } = useTranslation(["common", "auth", "home", "profile", "discover"]);
  const railRef = useRef<HTMLUListElement>(null);
  // One press moves the rail by most of what is visible.
  const railStep = () => Math.round((railRef.current?.clientWidth ?? 600) * 0.8);
  const router = useRouter();
  const [state, setState] = useState<State>({ phase: "checking" });

  useEffect(() => {
    let active = true;
    (async () => {
      let session: Session | null;
      try {
        session = await getSession();
      } catch {
        // [ForKhatri TR15/TR16] Mangaly or ForKhatri sign-in is unreachable:
        // the shared retry state (OutageGate), never "signed out" (a loop).
        if (active) reportOutage();
        return;
      }
      if (!active) return;
      if (!session) {
        // [TR16] Signed out: the ForKhatri entrance signs the member in and
        // returns them here. The old signed-out screen below is retained, unused.
        redirectToEntrance();
        return;
      }
      const profile = await getOwnProfile();
      if (!active) return;
      if (!profile) {
        // No candidate profile of their own and no circle to belong to: the
        // wizard is the only useful next step. A parent or relative who is in
        // someone's circle is a full member and keeps Home.
        const contexts = await getContexts();
        if (!active) return;
        if (!contexts?.circles.length) {
          router.replace("/profile/create");
          return;
        }
      }
      // Home shows people, so it loads people. Each call is optional: a
      // failure leaves that section empty rather than blocking the screen.
      const [completeness, found, incoming, members] = await Promise.all([
        profile ? getCompleteness().catch(() => null) : Promise.resolve(null),
        search({}, { page: 1 }).catch(() => null),
        waitingOnThisFamily(session, !!profile),
        listMembers().catch(() => [] as Member[]),
      ]);
      if (!active) return;
      setState({
        phase: "in",
        session,
        profile,
        completeness,
        matches: found?.results ?? [],
        matchTotal: found?.total ?? 0,
        incoming,
        members,
      });
    })();
    return () => {
      active = false;
    };
  }, [router]);

  if (state.phase === "checking" || loaderHold) {
    return (
      <main className="screen screen--centered">
        <SacredLoader />
      </main>
    );
  }

  if (state.phase === "out") {
    return (
      <main className="screen screen--centered">
        <span className="brand-mark brand-mark--lg" aria-hidden="true">
          m
        </span>
        <div style={{ textAlign: "center" }}>
          <h1
            style={{
              margin: "0 0 6px",
              fontSize: "1.75rem",
              lineHeight: "2.125rem",
            }}
          >
            {t("common:app.name")}
          </h1>
          <p className="muted" style={{ margin: 0 }}>
            {t("common:app.tagline")}
          </p>
        </div>
        <div className="form__actions" style={{ width: "100%" }}>
          <Link className="cta cta--link" href="/signup">
            {t("auth:signup.submit")}
          </Link>
          <p className="form__alt">
            {t("auth:signup.haveAccount")}{" "}
            <Link className="link" href="/login">
              {t("auth:signup.logInLink")}
            </Link>
          </p>
        </div>
      </main>
    );
  }

  const { profile, completeness, matches, matchTotal, incoming, members } =
    state;
  const fullName = profile?.name || state.session.display_name || "";
  const firstName = fullName.trim().split(/\s+/)[0] || fullName;
  /* The same three milestones /me shows, so Home and Me never disagree
     about how far along a profile is. "0 of 8 answered" here beside
     "Basics 2/3" there read as a contradiction, because they counted
     different things. */
  const answered = completeness
    ? {
        done: completeness.enhanced_filled_categories,
        total: completeness.enhanced_total_categories,
      }
    : null;
  const milestonesReached = completeness
    ? 1 +
      (completeness.discoverability_complete ? 1 : 0) +
      (completeness.enhanced_filled_categories >=
      completeness.enhanced_total_categories
        ? 1
        : 0)
    : 0;
  const enhancedShare = completeness
    ? completeness.enhanced_filled_categories /
      Math.max(1, completeness.enhanced_total_categories)
    : 0;
  const milestonePct = Math.round(((milestonesReached + enhancedShare) / 4) * 100);
  const profileIncomplete = !!answered && answered.done < answered.total;
  // The candidate's own Home Circle: the family helping *them*. (Circles the
  // account belongs to for someone else live on the Circle screen.)
  const circleCount = members.length;
  const unread = state.session.counts.unread_messages;
  const waiting = incoming.length;

  return (
    <>
      {/* The greeting is the page title: the date as a quiet eyebrow, the
          name set in motion type. No wordmark (the navigation carries it)
          and no banner — Home leads with people. */}
      <header className="home-head">
        <div className="home-head__text">
          <p className="home-head__date">
            {/* Indian order ("Thursday, 24 September") in every language. */}
            {new Intl.DateTimeFormat(`${i18n.language}-IN`, {
              weekday: "long",
              day: "numeric",
              month: "long",
            }).format(new Date())}
          </p>
          <MotionTitle
            as="h1"
            className="home-head__title"
            text={`${t("home:greetingWord")} ${firstName}`}
            accent={[1]}
          />
        </div>
        <div className="topbar__actions">
          <ForKhatriHubLink />
          <AccountButton />
        </div>
      </header>

      <main className="home">
        {/* Only what is waiting on this person, and only when something is.
            A zero is not news, so nothing renders for it. */}
        {(waiting > 0 || unread > 0) && (
          <div className="home-alerts">
            {waiting > 0 && (
              <Link className="home-alert home-alert--req" href="/discover">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z" />
                </svg>
                <strong>{waiting}</strong>
                <span>{t("home:tiles.requests")}</span>
              </Link>
            )}
            {unread > 0 && (
              <Link className="home-alert" href="/messages">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M4 5h16a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H9l-4.4 3.3A.4.4 0 0 1 4 20z" />
                </svg>
                <strong>{unread}</strong>
                <span>{t("home:tiles.unread", { count: unread })}</span>
              </Link>
            )}
          </div>
        )}

        {/* NEW MATCHES — large immersive portraits, one filling most of a
            phone screen with the next peeking: the face first, the name set
            big on the photo, two or three facts as glass chips. */}
        <section className="hfeed" aria-labelledby="home-matches">
          <div className="hfeed__head">
            <h2 className="hfeed__title" id="home-matches">
              {t("home:matches.title")}
              {matchTotal > 0 && <span className="hfeed__count">{matchTotal}</span>}
            </h2>
            <Link className="hfeed__all" href="/discover">
              {t("home:matches.seeAll")}
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M5 12h14M13 6l6 6-6 6" />
              </svg>
            </Link>
          </div>

          {matches.length === 0 ? (
            <p className="caption">{t("home:matches.empty")}</p>
          ) : (
            <div className="mrail-wrap">
              <button
                type="button"
                className="mrail__nav mrail__nav--prev"
                aria-label={t("home:matches.prev")}
                onClick={() => railRef.current?.scrollBy({ left: -railStep(), behavior: "smooth" })}
              >
                ‹
              </button>
              <ul className="hrail" ref={railRef}>
                {matches.slice(0, 16).map((match, i) => {
                  const city = match.locality?.split(",")[0]?.trim();
                  const name = match.open_name?.trim().split(/\s+/)[0];
                  const photos = match.open_photo_urls?.length ?? 0;
                  // Stored values are keys ("doctorate"); show their translated labels.
                  const chips = [
                    match.education_level
                      ? t(`profile:option.highest_education_level.${match.education_level}`)
                      : null,
                    match.mother_tongue
                      ? t(`profile:option.mother_tongue.${match.mother_tongue}`)
                      : null,
                  ].filter((c): c is string => !!c);
                  return (
                    <li
                      key={match.candidate_account_id}
                      className="hcard"
                      style={{ "--i": Math.min(i, 6) } as React.CSSProperties}
                    >
                      <Link
                        className="hcard__link"
                        href={`/profile/${match.candidate_account_id}`}
                        aria-label={[name, match.age, city, match.profession].filter(Boolean).join(", ")}
                      >
                        {match.photo_url ? (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img
                            className="hcard__img"
                            src={resolveMediaUrl(match.photo_url) ?? ""}
                            alt=""
                            loading={i < 2 ? "eager" : "lazy"}
                            decoding="async"
                          />
                        ) : (
                          <span className="hcard__empty">
                            <Avatar anonymized size={88} />
                          </span>
                        )}
                        <span className="hcard__top">

                          {photos > 1 && (
                            <span className="hcard__chip">
                              {t("discover:tile.photos", { count: photos })}
                            </span>
                          )}
                        </span>
                        <span className="hcard__text">
                          <span className="hcard__name">
                            {name ?? t("profile:hub.ageYears", { age: match.age ?? "" })}
                            {name && match.age ? <span className="hcard__age"> {match.age}</span> : null}
                            {(match.verification?.length ?? 0) > 0 && (
                              <Icon name="verified" size={16} className="seal" label={t("discover:verified.title")} />
                            )}
                          </span>
                          <span className="hcard__meta">
                            {[match.profession, city].filter(Boolean).join(" · ")}
                          </span>
                          {chips.length > 0 && (
                            <span className="hcard__chips">
                              {chips.map((c) => (
                                <span key={c} className="hcard__chip">
                                  {c}
                                </span>
                              ))}
                            </span>
                          )}
                        </span>
                      </Link>
                    </li>
                  );
                })}
                {matchTotal > 0 && (
                  <li className="hcard hcard--more">
                    <Link className="hcard__link hcard__link--more" href="/discover">
                      <span className="hcard__more-n">{matchTotal}</span>
                      <span>{t("home:matches.seeAllCount", { count: matchTotal })}</span>
                    </Link>
                  </li>
                )}
              </ul>
              <button
                type="button"
                className="mrail__nav mrail__nav--next"
                aria-label={t("home:matches.next")}
                onClick={() => railRef.current?.scrollBy({ left: railStep(), behavior: "smooth" })}
              >
                ›
              </button>
            </div>
          )}
        </section>

        {/* Two small tiles, side by side even on a phone: how ready your
            profile is, and who is searching with you. */}
        <div className="home-duo">
          {/* Desktop only: the right column lists what is waiting even when
              it is nothing, so the column is a complete status panel. On a
              phone the alerts above say it only when something waits. */}
          <Link className="duo duo--desk" href="/discover">
            <span className={`duo__icon${waiting > 0 ? " is-live" : ""}`} aria-hidden="true">
              <Icon name="heart" filled={waiting > 0} />
            </span>
            <span className="duo__label">{t("home:tiles.requests")}</span>
            <span className="duo__body">
              {waiting > 0
                ? `${waiting} · ${t("home:tiles.requestsWaiting", { count: waiting })}`
                : t("home:tiles.requestsNone")}
            </span>
          </Link>
          <Link className="duo duo--desk" href="/messages">
            <span className={`duo__icon${unread > 0 ? " is-live" : ""}`} aria-hidden="true">
              <Icon name="chat" filled={unread > 0} />
            </span>
            <span className="duo__label">{t("home:tiles.messages")}</span>
            <span className="duo__body">
              {unread > 0
                ? `${unread} ${t("home:tiles.unread", { count: unread })}`
                : t("home:tiles.allRead")}
            </span>
          </Link>
          {profile && (
            <Link className="duo duo--profile" href="/me">
              <span
                className="duo-ring"
                style={{ "--pct": profileIncomplete ? milestonePct : 100 } as React.CSSProperties}
                aria-hidden="true"
              >
                <span className="duo-ring__n">{profileIncomplete ? milestonePct : 100}%</span>
              </span>
              <span className="duo__label">{t("home:tiles.profile")}</span>
              <span className="duo__body">
                {profileIncomplete
                  ? t(
                      completeness?.discoverability_complete
                        ? "profile:hub.milestone.nextEnhanced"
                        : "profile:hub.milestone.nextDiscoverable",
                    )
                  : t("home:tiles.profileDone")}
              </span>
            </Link>
          )}

          <Link className="duo duo--circle" href="/circle">
            {circleCount > 0 ? (
              <span className="avatar-stack duo__faces">
                {members.slice(0, 4).map((m) => (
                  <Avatar
                    key={m.membership_id}
                    photoUrl={m.member_photo_url}
                    name={m.member_name}
                    size={40}
                  />
                ))}
              </span>
            ) : (
              <span className="duo__plus" aria-hidden="true">
                <Icon name="invite" />
              </span>
            )}
            <span className="duo__label">{t("home:circle.title")}</span>
            <span className="duo__body">
              {circleCount > 0
                ? t("home:circle.helping", { count: circleCount })
                : t("home:circle.invite")}
            </span>
          </Link>

          {/* Kundli matching for any two people (a proposal from outside
              Mangaly, relatives). A profile already shows its own match. */}
          <Link className="duo duo--kundli" href="/horoscope/check">
            <span className="duo__plus" aria-hidden="true">
              <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round">
                <rect x="3.5" y="3.5" width="17" height="17" rx="1.5" />
                <path d="M12 3.5 20.5 12 12 20.5 3.5 12Z" />
                <path d="M3.5 3.5l17 17M20.5 3.5l-17 17" opacity=".45" />
              </svg>
            </span>
            <span className="duo__label">{t("horoscope:check.title")}</span>
            <span className="duo__body">{t("horoscope:check.homeBody")}</span>
          </Link>
        </div>

        {/* The internal build tracker (/status) is not linked from a
            member's Home: a real member has no use for it. */}
      </main>
    </>
  );
}

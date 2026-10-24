"use client";

import Link from "next/link";
import Icon from "@/components/Icon";
import { useLoaderHold } from "@/lib/useLoaderHold";
import SacredLoader from "@/components/SacredLoader";
import MotionTitle from "@/components/MotionTitle";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { getJson, query, resolveMediaUrl } from "@/lib/api";
import ContextChip from "@/components/ContextChip";
import { useActiveContext, contextKey, firstName as firstOf, readBrowseLookingFor } from "@/lib/activeContext";
import { isProvisional, type HoroscopeMatchResponse } from "@/components/HoroscopeMatch";
import HowYouFit, { type Fit } from "@/components/HowYouFit";
import { getBrief, type Brief } from "@/lib/matchmaker";
import { listConversations, type ConversationSummary } from "@/lib/messages";
import AccountButton from "@/components/AccountButton";
import ForKhatriHubLink from "@/components/ForKhatriHubLink";
import { Avatar } from "@/components/Avatar";
import { getSession, type Session } from "@/lib/auth";
import ClaimProfileNote from "@/components/ClaimProfileNote";
import { getMyAgentRecord } from "@/lib/agents";
import { reportOutage } from "@/lib/outage";
import { redirectToEntrance } from "@/lib/platform";
import {
  acceptInvitation,
  declineInvitation,
  invitationText,
  listMembers,
  listPendingInvitations,
  type Member,
  type PendingInvitation,
} from "@/lib/homeCircle";
import {
  getCompleteness,
  getOwnProfile,
  type CompletenessReport,
  type Profile,
} from "@/lib/profile";
import {
  getBecause,
  getShelves,
  getSnippet,
  search,
  type BecauseRow,
  type SearchResult,
  type Snippet,
} from "@/lib/discovery";
import { formatRupees, getCatalogue, getMyPlan, type Catalogue, type MyPlan } from "@/lib/billing";
import { listIncoming, listSent, sendRequest, type Connection } from "@/lib/connections";
import { listSuggestions, suggestProfile, type Suggestion } from "@/lib/homeCircle";

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

/** Where each "Your search" lane's full list lives. */
const LANE_HREF = {
  awaiting: "/circle#sent",
  connected: "/messages",
  suggested: "/circle#suggestions",
} as const;

type State =
  | { phase: "checking" }
  | {
      phase: "in";
      session: Session;
      profile: Profile | null;
      completeness: CompletenessReport | null;
      matches: Picked[];
      matchTotal: number;
      incoming: Connection[];
      /** Home Circle invitations waiting on this person's answer. */
      invitations: PendingInvitation[];
      members: Member[];
      /** [Owner, 2026-09-28] Today's introduction: the daily pick. */
      hero: Hero | null;
      /** Chats with something unread, newest first. */
      unreadChats: ConversationSummary[];
      /** The matchmaker brief (own search only). */
      brief: Brief | null;
      /** [Owner, 2026-09-28] Where this search stands — Home's own job. */
      progress: Progress;
      /** "Because of this, these": people like those the family acted on. */
      because: BecauseRow[];
      /** The seat's plan and the catalogue, for the plans section. */
      plan: MyPlan | null;
      catalogue: Catalogue | null;
    }
  | { phase: "out" };

type Picked = SearchResult & { reason?: string | null };
type Hero = {
  person: Picked;
  /** "Sub" line of the row: why the engine chose them. */
  common: string[];
  gunas: { n: number; max: number; provisional?: boolean } | null;
  /** From the nightly pairing (true), or the engine's top match (false). */
  daily: boolean;
};

/* [Owner, 2026-09-28] "Home has specific functionality other than
   Discovery": browsing people stays on Discover; Home shows where the
   family's search stands — requests out and their answers, connections
   made, and what the family suggested. */
type Face = { id: string; card: Snippet | null };
type Progress = {
  awaiting: Face[];
  awaitingTotal: number;
  connected: Face[];
  connectedTotal: number;
  suggested: (Face & { by: string | null; byYou: boolean })[];
  suggestedTotal: number;
};

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
  const { t, i18n } = useTranslation(["common", "auth", "home", "profile", "discover", "circle"]);
  const [inviteBusy, setInviteBusy] = useState<string | null>(null);
  const [fitOpen, setFitOpen] = useState(false);

  async function onInvitation(id: string, accept: boolean) {
    setInviteBusy(id);
    await (accept ? acceptInvitation(id) : declineInvitation(id));
    // Accepting can add a new circle (a new seat to act in): reload so the
    // contexts and Home read from it. Declining just drops the row.
    if (accept) {
      window.location.reload();
      return;
    }
    setInviteBusy(null);
    setState((s) => (s.phase === "in" ? { ...s, invitations: s.invitations.filter((i) => i.id !== id) } : s));
  }
  const router = useRouter();
  const [state, setState] = useState<State>({ phase: "checking" });
  // The introduction's own action: a request (parents) or a suggestion.
  const [introAction, setIntroAction] = useState<"idle" | "busy" | "done" | "error">("idle");
  // [Owner, 2026-09-28] Home follows whose search you are in. A father in
  // his daughter's Home Circle used to read "No new matches — complete your
  // profile" and "Invite family": Home searched as him (no profile of his
  // own) and counted only his own circle.
  const { contexts, active, choose, loaded } = useActiveContext();
  const forId = active?.kind === "family" ? active.circle.candidate_account_id : undefined;
  const seatKey = active ? contextKey(active) : "none";

  useEffect(() => {
    if (!loaded) return;
    let alive = true;
    (async () => {
      let session: Session | null;
      try {
        session = await getSession();
      } catch {
        // [ForKhatri TR15/TR16] Mangalya or ForKhatri sign-in is unreachable:
        // the shared retry state (OutageGate), never "signed out" (a loop).
        if (alive) reportOutage();
        return;
      }
      if (!alive) return;
      if (!session) {
        // [TR16] Signed out: the ForKhatri entrance signs the member in and
        // returns them here. The old signed-out screen below is retained, unused.
        redirectToEntrance();
        return;
      }
      const [profile, invitations] = await Promise.all([
        getOwnProfile(),
        listPendingInvitations().catch(() => [] as PendingInvitation[]),
      ]);
      if (!alive) return;
      // Someone invited into a circle answers that first, even before they
      // have a profile or a circle of their own.
      // [Owner walkthrough, 2026-09-30] A marriage agent with no search of
      // their own belongs in the agent workspace, not in "create a profile".
      if (!profile && !contexts?.circles.length && invitations.length === 0) {
        const agent = await getMyAgentRecord().catch(() => null);
        if (!alive) return;
        if (agent?.kind === "agent") {
          router.replace("/agent");
          return;
        }
        // No candidate profile of their own and no circle to belong to: the
        // wizard is the only useful next step. A parent or relative who is in
        // someone's circle is a full member and keeps Home.
        // [D1, 2026-10-06] Someone who chose "Just look around first" (and
        // picked brides or grooms) goes on looking; the wizard waits.
        router.replace(readBrowseLookingFor() ? "/discover" : "/profile/create");
        return;
      }
      // Home shows people, so it loads people. Each call is optional: a
      // failure leaves that section empty rather than blocking the screen.
      const [completeness, found, rows, incoming, members, chats, brief] = await Promise.all([
        profile ? getCompleteness().catch(() => null) : Promise.resolve(null),
        search({}, { page: 1, forCandidate: forId }).catch(() => null),
        getShelves({ forCandidate: forId }).catch(() => null),
        waitingOnThisFamily(session, !!profile),
        listMembers(forId).catch(() => [] as Member[]),
        listConversations(forId).catch(() => [] as ConversationSummary[]),
        forId ? Promise.resolve(null) : getBrief().catch(() => null),
      ]);
      const [sent, received, suggestions, because, plan, catalogue] = await Promise.all([
        listSent(forId).catch(() => [] as Connection[]),
        listIncoming(forId).catch(() => [] as Connection[]),
        listSuggestions(forId).catch(() => [] as Suggestion[]),
        getBecause(forId).catch(() => [] as BecauseRow[]),
        getMyPlan(forId).catch(() => null),
        getCatalogue().catch(() => null),
      ]);
      const awaitingIds = sent.filter((c) => c.status === "pending").map((c) => c.target_account_id);
      const connectedIds = [
        ...sent.filter((c) => c.status === "accepted").map((c) => c.target_account_id),
        ...received.filter((c) => c.status === "accepted").map((c) => c.subject_account_id),
      ].filter((v, i, all) => all.indexOf(v) === i);
      const suggestedRows = suggestions.filter(
        (x, i, all) => all.findIndex((y) => y.suggested_profile_id === x.suggested_profile_id) === i,
      );
      // A few faces per lane; the rest is a count.
      const faceIds = [
        ...awaitingIds.slice(0, 4),
        ...connectedIds.slice(0, 4),
        ...suggestedRows.slice(0, 4).map((x) => x.suggested_profile_id),
      ].filter((v, i, all) => all.indexOf(v) === i);
      const cards = new Map(
        await Promise.all(
          faceIds.map(async (id) => [id, await getSnippet(id).catch(() => null)] as const),
        ),
      );
      const face = (id: string): Face => ({ id, card: cards.get(id) ?? null });
      const progress: Progress = {
        awaiting: awaitingIds.slice(0, 4).map(face),
        awaitingTotal: awaitingIds.length,
        connected: connectedIds.slice(0, 4).map(face),
        connectedTotal: connectedIds.length,
        suggested: suggestedRows.slice(0, 4).map((x) => ({
          ...face(x.suggested_profile_id),
          by: x.suggested_by_name ?? null,
          byYou: !!x.suggested_by_is_you,
        })),
        suggestedTotal: suggestedRows.length,
      };
      if (!alive) return;
      const shelves = rows?.shelves ?? [];
      const pairing = shelves.find((sh) => sh.key === "mostCompatible")?.results[0] ?? null;
      const picked = shelves.find((sh) => sh.key === "picked")?.results ?? [];
      // No good pairing today: the engine's top match, said as such.
      // Never introduce someone the family is already talking to or waiting on.
      const inProgress = new Set([
        ...awaitingIds,
        ...connectedIds,
        ...incoming.map((c) => c.subject_account_id),
      ]);
      const daily =
        pairing ?? picked.find((m) => !inProgress.has(m.candidate_account_id)) ?? null;
      // The hero's full story: what the two share, and the gunas.
      let hero: Hero | null = null;
      if (daily) {
        const q = query({ for_candidate: forId });
        const [fit, horo] = await Promise.all([
          getJson<Fit>(`/discovery/fit/${daily.candidate_account_id}${q}`).catch(() => null),
          getJson<HoroscopeMatchResponse>(`/horoscope/match/${daily.candidate_account_id}${q}`).catch(() => null),
        ]);
        const ak = horo?.available ? horo.match?.ashtakoota : null;
        hero = {
          person: { ...daily, match_label: daily.match_label ?? fit?.label ?? null },
          common: (fit?.common ?? []).slice(0, 3),
          // [D16] Unknown birth time on either side: the gunas are provisional.
          gunas: ak && ak.status === "CALCULATED" && ak.totalScore != null ? { n: ak.totalScore, max: ak.maxScore, provisional: isProvisional(horo?.match) } : null,
          daily: !!pairing,
        };
      }
      if (!alive) return;
      setState({
        phase: "in",
        session,
        profile,
        completeness,
        matches: picked.length > 0 ? picked : (found?.results ?? []),
        matchTotal: found?.total ?? 0,
        incoming,
        invitations,
        members,
        hero,
        unreadChats: chats.filter((c) => (c.unread_count ?? 0) > 0),
        brief,
        progress,
        because,
        plan,
        catalogue,
      });
      setIntroAction("idle");
    })();
    return () => {
      alive = false;
    };
    // seatKey stands for `active`; contexts only matter once loaded.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router, loaded, seatKey]);

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

  const { profile, completeness, matches, matchTotal, incoming, invitations, members, hero, unreadChats, brief, progress, because, plan, catalogue } =
    state;
  // [Owner, 2026-09-28] Home reads by role. Someone searching for their child
  // or relative reads the formal view (biodata facts first, larger type);
  // parents and guardians also get the request button — they decide. A
  // candidate reads the photo-and-words view. Nothing else changes by role.
  const familyView = active?.kind === "family";
  const decides =
    active?.kind === "family" && ["parent", "guardian"].includes(active.circle.relationship_type);
  const forName = active?.kind === "family" ? firstOf(active.circle.candidate_name) : null;
  const fmtGunas = (n: number) => (Number.isInteger(n) ? String(n) : n.toFixed(1));
  // What the family told the matchmaker, as a few words for the card.
  const briefPoints = brief
    ? [
        ...Object.entries(brief.priorities ?? {})
          .sort((a, b) => (b[1] ?? 0) - (a[1] ?? 0))
          .map(([theme]) => t(`discover:matchmaker.matters.theme.${theme}.name`)),
        ...brief.items.map((it) => t(`discover:matchmaker.field.${it.field}`)),
      ].filter((v, i, all) => all.indexOf(v) === i)
    : [];
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
  /* [Owner walkthrough, 2026-09-29] "A few more details" named nothing, so a
     new member had no idea what to do next. Name the actual missing fields,
     up to two, the way the field appears when editing (profile:field.*). */
  const missingFieldLabels = (completeness?.discoverability_missing ?? [])
    .filter((k) => k !== "partner_preference.age_range_or_locality")
    .slice(0, 2)
    .map((k) => t(`profile:field.${k}`));
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
          {/* Whose search this is and who is being looked for, right under
              the greeting on every screen size. */}
          {contexts && active && (
            <div className="home-head__context">
              <ContextChip contexts={contexts} active={active} onChoose={choose} />
            </div>
          )}
        </div>
        <div className="topbar__actions">
          <ForKhatriHubLink />
          <AccountButton />
        </div>
      </header>

      <main className={`home${familyView ? " home--family" : ""}`}>
        {/* A profile a parent made for this person: take it over or remove it, first. */}
        <ClaimProfileNote session={state.session} />
        {/* Only what is waiting on this person, and only when something is.
            A zero is not news, so nothing renders for it. */}
        {/* [Owner, 2026-09-28] YOUR TURN — Hinge's "Your turn": the people
            waiting on this family, as faces, only when someone is. */}
        {(waiting > 0 || unreadChats.length > 0) && (
          <section className="home-alerts hturn" aria-labelledby="home-turn">
            <h2 className="hturn__title" id="home-turn">
              {t("home:turn.title")}
            </h2>
            <ul className="hturn__list">
              {incoming.slice(0, 4).map((c) => {
                const who = c.subject?.open_name ?? c.subject_name ?? null;
                return (
                  <li key={c.id}>
                    <Link className="hturn__item" href={`/profile/${c.subject_account_id}`}>
                      <Avatar photoUrl={c.subject?.photo_url ?? null} name={who ?? ""} size={44} anonymized={!who} />
                      <span className="hturn__text">
                        <strong>{who ?? t("profile:hub.ageYears", { age: c.subject?.age ?? "" })}</strong>
                        <span>
                          {c.sent_by_label ??
                            (forName ? t("home:turn.requestFor", { name: forName }) : t("home:turn.request"))}
                        </span>
                      </span>
                    </Link>
                  </li>
                );
              })}
              {unreadChats.slice(0, 3).map((c) => (
                <li key={c.conversation_id ?? c.connection_id}>
                  <Link className="hturn__item" href={`/messages/${c.connection_id}`}>
                    <Avatar photoUrl={c.other_photo_url} name={c.other_name ?? ""} size={44} />
                    <span className="hturn__text">
                      <strong>{c.other_name ?? t("home:turn.someone")}</strong>
                      <span>{t("home:tiles.unread", { count: c.unread_count ?? 1 })}</span>
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* NEW MATCHES — large immersive portraits, one filling most of a
            phone screen with the next peeking: the face first, the name set
            big on the photo, two or three facts as glass chips. */}
        <section className="hfeed" aria-labelledby="home-matches">
          {/* Home Circle invitations: first thing in the page's main column
              on every screen size, answered right here — no detour to Circle. */}
          {invitations.length > 0 && (
            <section className="hinvite" aria-labelledby="home-invite">
              <h2 className="hturn__title" id="home-invite">
                {t("home:turn.invitation", { count: invitations.length })}
              </h2>
              <ul className="hinvite__list">
              {invitations.map((inv) => (
                <li key={inv.id} className="hinvite__row">
                  <span className="hturn__item">
                    <Avatar name={inv.inviter_name ?? ""} anonymized={!inv.inviter_name} size={44} />
                    <span className="hturn__text">
                      <span>{invitationText(t, inv)}</span>
                    </span>
                  </span>
                  <span className="hturn__actions">
                    <button className="cta" type="button" disabled={inviteBusy === inv.id} onClick={() => onInvitation(inv.id, true)}>
                      {t("circle:pendingInvitations.accept")}
                    </button>
                    <button className="icon-btn icon-btn--text" type="button" disabled={inviteBusy === inv.id} onClick={() => onInvitation(inv.id, false)}>
                      {t("circle:pendingInvitations.decline")}
                    </button>
                  </span>
                </li>
              ))}
              </ul>
            </section>
          )}
          {/* [Owner, 2026-09-28] TODAY'S INTRODUCTION — Sitch's
              "Introductions" and Hinge's "Most Compatible": one person the
              nightly pairing chose for this seat, with why, not a feed. */}
          {hero && (
            <article className="hintro" aria-labelledby="home-intro">
              <Link
                className={`hintro__photo${hero.person.photo_url ? "" : " hintro__photo--none"}`}
                href={`/profile/${hero.person.candidate_account_id}`}
                tabIndex={-1}
              >
                {hero.person.photo_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={resolveMediaUrl(hero.person.photo_url) ?? ""} alt="" />
                ) : (
                  <span className="hcard__empty">
                    <Avatar anonymized size={88} />
                  </span>
                )}
                {/* [Owner walkthrough, 2026-09-30] On a phone the photo and the
                    "who is this" text used to be two separate stacked blocks,
                    so a first-time visitor scrolled past a full-screen photo
                    of a stranger with nothing said about them. This overlay —
                    the same scrim-and-name .hcard already uses elsewhere —
                    repeats the eyebrow and name ON the photo, phone widths
                    only (home.css hides it from 640px up, where the name
                    already sits beside the photo). */}
                <span className="hintro__overlay">
                  <span className="hintro__overlay-eyebrow">
                    {hero.daily
                      ? forName
                        ? t("home:intro.eyebrowFor", { name: forName })
                        : t("home:intro.eyebrow")
                      : forName
                        ? t("home:intro.topFor", { name: forName })
                        : t("home:intro.top")}
                  </span>
                  <span className="hintro__overlay-name">
                    {hero.person.open_name?.trim().split(/\s+/)[0] ??
                      (hero.person.profession ||
                        t("profile:hub.ageYears", { age: hero.person.age ?? "" }))}
                    {hero.person.open_name && hero.person.age ? (
                      <span className="hintro__age"> {hero.person.age}</span>
                    ) : null}
                  </span>
                </span>
              </Link>
              <div className="hintro__body">
                <p className="hintro__eyebrow">
                  {hero.daily
                    ? forName
                      ? t("home:intro.eyebrowFor", { name: forName })
                      : t("home:intro.eyebrow")
                    : forName
                      ? t("home:intro.topFor", { name: forName })
                      : t("home:intro.top")}
                </p>
                {/* A hidden name is replaced by who they are (work, city),
                    never by a bare "30 yrs". */}
                <h2 className="hintro__name" id="home-intro">
                  {hero.person.open_name?.trim().split(/\s+/)[0] ??
                    (hero.person.profession ||
                      t("profile:hub.ageYears", { age: hero.person.age ?? "" }))}
                  {hero.person.open_name && hero.person.age ? (
                    <span className="hintro__age"> {hero.person.age}</span>
                  ) : null}
                </h2>
                {familyView ? (
                  <dl className="hintro__facts">
                    {(
                      [
                        ["age", hero.person.age ? t("profile:hub.ageYears", { age: hero.person.age }) : null],
                        ["height", hero.person.height_cm ? `${hero.person.height_cm} cm` : null],
                        [
                          "education",
                          hero.person.education_level
                            ? t(`profile:option.highest_education_level.${hero.person.education_level}`)
                            : null,
                        ],
                        // Work is the heading when the name is hidden.
                        ["work", hero.person.open_name ? hero.person.profession : null],
                        ["city", hero.person.locality?.split(",")[0]?.trim()],
                        [
                          "tongue",
                          hero.person.mother_tongue
                            ? t(`profile:option.mother_tongue.${hero.person.mother_tongue}`)
                            : null,
                        ],
                      ] as const
                    )
                      .filter(([, v]) => !!v)
                      .map(([k, v]) => (
                        <div key={k} className="hintro__fact">
                          <dt>{t(`home:intro.fact.${k}`)}</dt>
                          <dd>{v}</dd>
                        </div>
                      ))}
                  </dl>
                ) : (
                  <>
                    <p className="hintro__meta">
                      {[
                        hero.person.open_name ? hero.person.profession : null,
                        !hero.person.open_name && hero.person.age
                          ? t("profile:hub.ageYears", { age: hero.person.age })
                          : null,
                        hero.person.locality?.split(",")[0]?.trim(),
                      ]
                        .filter(Boolean)
                        .join(" · ")}
                    </p>
                    {/* Their own words, when they published an answer openly. */}
                    {hero.person.open_prompt && (
                      <blockquote className="hintro__words">
                        <span className="hintro__q">{t(`profile:hub.prompts.q.${hero.person.open_prompt.q}`)}</span>
                        <span className="hintro__a">{hero.person.open_prompt.a}</span>
                      </blockquote>
                    )}
                  </>
                )}
                <ul className="hintro__chips">
                  {hero.person.match_label && (
                    <li className="hintro__chip hintro__chip--word">{t(`discover:match.${hero.person.match_label}`)}</li>
                  )}
                  {hero.gunas && (
                    <li className="hintro__chip">
                      {t("discover:compat.gunas", { n: fmtGunas(hero.gunas.n), max: hero.gunas.max })}
                      {hero.gunas.provisional && ` · ${t("horoscope:provisional.short")}`}
                    </li>
                  )}
                </ul>
                {/* [Owner, 2026-09-29] Trust where the family decides: what
                    is verified, and since when (research: 91% of women rate
                    verified profiles highly important). */}
                <ul className="hintro__trust">
                  {(hero.person.verification ?? []).length > 0 ? (
                    (hero.person.verification ?? []).map((v) => (
                      <li key={v.layer}>
                        {v.verified_on
                          ? t("discover:verified.on", {
                              label: t(`discover:verified.layer.${v.layer}`),
                              date: new Intl.DateTimeFormat(`${i18n.language}-IN`, { month: "short", year: "numeric" }).format(
                                new Date(v.verified_on),
                              ),
                            })
                          : t(`discover:verified.layer.${v.layer}`)}
                      </li>
                    ))
                  ) : (
                    <li className="is-none">{t("discover:verified.none")}</li>
                  )}
                </ul>
                {(hero.person.reason || hero.common.length > 0) && (
                  <div className="hintro__why">
                    <p className="hintro__why-title">{t("home:intro.why")}</p>
                    <ul>
                      {[hero.person.reason, ...hero.common]
                        .filter((v, i, all): v is string => !!v && all.indexOf(v) === i)
                        .slice(0, 3)
                        .map((line) => (
                          <li key={line}>{line}</li>
                        ))}
                    </ul>
                  </div>
                )}
                <div className="hintro__actions">
                  <Link className="btn btn--primary" href={`/profile/${hero.person.candidate_account_id}`}>
                    {familyView ? t("home:intro.openBiodata") : t("home:intro.open")}
                  </Link>
                  {familyView && active?.kind === "family" && (
                    <button
                      type="button"
                      className="btn hintro__second"
                      disabled={introAction === "busy" || introAction === "done"}
                      onClick={async () => {
                        setIntroAction("busy");
                        const outcome = decides
                          ? await sendRequest(hero.person.candidate_account_id, active.circle.candidate_account_id)
                          : await suggestProfile(active.circle.membership_id, hero.person.candidate_account_id);
                        setIntroAction(outcome.ok ? "done" : "error");
                      }}
                    >
                      {introAction === "done"
                        ? decides
                          ? t("home:intro.requestSent")
                          : t("home:intro.suggested")
                        : decides
                          ? t("home:intro.requestFor", { name: forName })
                          : t("home:intro.suggestTo", { name: forName })}
                    </button>
                  )}
                  {/* [Owner, 2026-09-30] "why refresh of page is happening, it is
                      just inner component" — opens right here instead of
                      loading the whole profile page. */}
                  <button
                    type="button"
                    className="hintro__link"
                    aria-expanded={fitOpen}
                    onClick={() => setFitOpen((o) => !o)}
                  >
                    {forName ? t("home:intro.fitFor", { name: forName }) : t("home:intro.fit")}
                  </button>
                  {introAction === "error" && (
                    <p className="hintro__error" role="alert">
                      {t("home:intro.actionFailed")}
                    </p>
                  )}
                </div>
                {fitOpen && (
                  <div className="hintro__fit">
                    <HowYouFit
                      candidateId={hero.person.candidate_account_id}
                      forCandidate={forId && forName ? { accountId: forId, name: forName } : undefined}
                      bare
                    />
                  </div>
                )}
              </div>
            </article>
          )}

          {/* [Owner, 2026-09-30] "a card for today's matches, and down a row of
              strong matches, 2 to 3 in a row, then See all → Discover." The
              engine's own word decides "strong"; when nobody is strong yet the
              row says plainly that these are the next best, never a false
              label. */}
          {(() => {
            const pool = matches.filter((m) => m.candidate_account_id !== hero?.person.candidate_account_id);
            const strong = pool.filter((m) => m.match_label === "strong");
            // Strong first, topped up with the next best so the row is full.
            const row = [...strong, ...pool.filter((m) => m.match_label !== "strong")].slice(0, 3);
            if (row.length === 0) return null;
            const allStrong = row.every((m) => m.match_label === "strong");
            return (
              <section className="hstrong" aria-labelledby="home-strong">
                <div className="hstrong__head">
                  <h2 className="hfeed__title" id="home-strong">
                    {t(allStrong ? "home:strong.title" : "home:strong.titleMore")}
                  </h2>
                  <Link className="hfeed__all" href="/discover">
                    {matchTotal > row.length ? t("home:matches.seeAllCount", { count: matchTotal }) : t("home:matches.seeAll")}
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M5 12h14M13 6l6 6-6 6" />
                    </svg>
                  </Link>
                </div>
                <ul className="hstrong__list">
                  {row.map((m) => {
                    const first = m.open_name?.trim().split(/\s+/)[0] ?? null;
                    const city = m.locality?.split(",")[0]?.trim();
                    return (
                      <li key={m.candidate_account_id}>
                        <Link className="hstrong__card" href={`/profile/${m.candidate_account_id}`}>
                          {m.photo_url ? (
                            // eslint-disable-next-line @next/next/no-img-element
                            <img className="hstrong__img" src={resolveMediaUrl(m.photo_url) ?? ""} alt="" loading="lazy" />
                          ) : (
                            <span className="hstrong__img hstrong__img--none">
                              <Avatar anonymized size={48} />
                            </span>
                          )}
                          {m.match_label === "strong" && !allStrong && (
                            <span className="hstrong__tag">{t("home:strong.tag")}</span>
                          )}
                          <span className="hstrong__name">
                            {first ?? t("profile:hub.ageYears", { age: m.age ?? "" })}
                            {first && m.age ? <span className="hstrong__age"> {m.age}</span> : null}
                          </span>
                          <span className="hstrong__meta">{[m.profession, city].filter(Boolean).join(" · ")}</span>
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              </section>
            );
          })()}

          {/* YOUR SEARCH — where things stand, not more people to browse. */}
          <div className="hfeed__head">
            <h2 className="hfeed__title" id="home-matches">
              {forName ? t("home:search.titleFor", { name: forName }) : t("home:search.title")}
            </h2>
            {/* One way to Discover per screen: the top-matches row carries it. */}
          </div>
          {/* [Owner, 2026-09-30] "don't waste unnecessary space": three boxes
              of 0 said nothing to a new member. One line until something
              has happened; the boxes return with the first request. */}
          {progress.awaitingTotal + progress.connectedTotal + progress.suggestedTotal === 0 ? (
            <p className="hsearch__none">
              {forName ? t("home:search.noneYetFor", { name: forName }) : t("home:search.noneYet")}
            </p>
          ) : (
          <div className="hsearch">
            {(
              [
                ["awaiting", progress.awaiting, progress.awaitingTotal],
                ["connected", progress.connected, progress.connectedTotal],
                ["suggested", progress.suggested, progress.suggestedTotal],
              ] as const
            ).map(([lane, faces, total]) => (
              <div key={lane} className={`hsearch__lane${total === 0 ? " is-empty" : ""}`}>
                {/* The number and its words open the full list behind them. */}
                <Link className="hsearch__head" href={LANE_HREF[lane]}>
                  <span className="hsearch__n">{total}</span>
                  <span className="hsearch__label">{t(`home:search.${lane}.label`, { count: total })}</span>
                </Link>
                {total > 0 ? (
                  <ul className="hsearch__faces">
                    {faces.map((f) => {
                      const name = f.card?.name?.trim().split(/\s+/)[0] ?? null;
                      const by =
                        lane === "suggested" && "byYou" in f
                          ? f.byYou
                            ? t("home:search.suggested.byYou")
                            : f.by
                              ? t("home:search.suggested.by", { name: f.by.split(" ")[0] })
                              : null
                          : null;
                      return (
                        <li key={f.id}>
                          <Link
                            className="hsearch__face"
                            href={`/profile/${f.id}`}
                            aria-label={[name, f.card?.age, f.card?.profession, by].filter(Boolean).join(", ")}
                          >
                            <Avatar photoUrl={f.card?.photo_url ?? null} name={name ?? ""} size={48} anonymized={!f.card?.photo_url} />
                            <span className="hsearch__who">
                              {name ?? t("profile:hub.ageYears", { age: f.card?.age ?? "" })}
                            </span>
                            {by && <span className="hsearch__by">{by}</span>}
                          </Link>
                        </li>
                      );
                    })}
                  </ul>
                ) : (
                  <p className="hsearch__empty">
                    {forName
                      ? t(`home:search.${lane}.emptyFor`, { name: forName })
                      : t(`home:search.${lane}.empty`)}
                  </p>
                )}
              </div>
            ))}
          </div>
          )}

          {/* [Owner, 2026-09-28] BECAUSE OF THIS, THESE — rows from what the
              family did (a request, a suggestion, a save), each explaining
              itself. */}
          {because
            .map((row) => ({
              ...row,
              results: row.results.filter((p) => p.candidate_account_id !== hero?.person.candidate_account_id),
            }))
            .filter((row) => row.results.length >= 2)
            .map((row) => (
            <section key={`${row.kind}-${row.anchor_account_id}`} className="hbecause" aria-label={row.title}>
              <div className="hbecause__head">
                <h3 className="hbecause__title">{row.title}</h3>
                <p className="hbecause__sub">{row.sub}</p>
              </div>
              <ul className="hbecause__list">
                {row.results.map((p) => {
                  const name = p.open_name?.trim().split(/\s+/)[0];
                  const facts = familyView
                    ? [
                        p.age ? t("profile:hub.ageYears", { age: p.age }) : null,
                        p.height_cm ? `${p.height_cm} cm` : null,
                        p.profession,
                        p.locality?.split(",")[0]?.trim(),
                      ]
                    : [p.profession, p.locality?.split(",")[0]?.trim()];
                  return (
                    <li key={p.candidate_account_id}>
                      <Link className="bcard" href={`/profile/${p.candidate_account_id}`}>
                        {p.photo_url ? (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img className="bcard__img" src={resolveMediaUrl(p.photo_url) ?? ""} alt="" loading="lazy" />
                        ) : (
                          <span className="bcard__img bcard__img--empty">
                            <Avatar anonymized size={56} />
                          </span>
                        )}
                        <span className="bcard__name">
                          {name ?? t("profile:hub.ageYears", { age: p.age ?? "" })}
                          {name && p.age ? <span className="bcard__age"> {p.age}</span> : null}
                        </span>
                        <span className="bcard__meta">{facts.filter(Boolean).join(" · ")}</span>
                        {p.reason && <span className="bcard__why">{p.reason}</span>}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </section>
          ))}
        </section>

        {/* Two small tiles, side by side even on a phone: how ready your
            profile is, and who is searching with you. */}
        <div className="home-duo">
          {/* [Owner, 2026-09-28] Sitch's "Talk to your matchmaker": what
              this family told the engine, or the ask to tell it. First in the
              column: who you are looking for drives everything else. */}
          {!forId && profile && (
            <Link className="duo duo--mm" href="/me/matchmaker">
              <span className="duo__plus" aria-hidden="true">
                <Icon name="heart" />
              </span>
              <span className="duo__label">{t("home:mm.title")}</span>
              <span className="duo__body">
                {briefPoints.length > 0
                  ? t("home:mm.matters", { list: briefPoints.slice(0, 3).join(", ") })
                  : t("home:mm.ask")}
              </span>
            </Link>
          )}
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
          {profile && !forId && (
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
                  ? completeness?.discoverability_complete
                    ? t("profile:hub.milestone.nextEnhanced")
                    : missingFieldLabels.length > 0
                      ? t("profile:hub.milestone.nextDiscoverableNamed", {
                          fields: missingFieldLabels.join(t("profile:hub.milestone.fieldsJoiner")),
                        })
                      : t("profile:hub.milestone.nextDiscoverable")
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
            <span className="duo__label">
              {forName ? t("home:circle.titleFor", { name: forName }) : t("home:circle.title")}
            </span>
            <span className="duo__body">
              {circleCount > 0
                ? forName
                  ? t("home:circle.helpingFor", { count: circleCount, name: forName })
                  : t("home:circle.helping", { count: circleCount })
                : t("home:circle.invite")}
            </span>
          </Link>

          {/* Kundli matching for any two people (a proposal from outside
              Mangalya, relatives). A profile already shows its own match. */}
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
        {/* [Owner, 2026-09-28] PLANS — last on Home, after everything free:
            the seat's plan, today's requests, and what each plan adds. A plan
            buys capability in one's own search, never a place in anyone's
            results (DEC-V1-031). */}
        {catalogue && plan && (
          <section className="hplans" aria-labelledby="home-plans">
            <div className="hplans__head">
              <h2 className="hfeed__title" id="home-plans">
                {forName ? t("home:plans.titleFor", { name: forName }) : t("home:plans.title")}
              </h2>
              <p className="hplans__now">
                {t("home:plans.current", { plan: plan.plan_name })}
                {plan.usage.daily_requests != null &&
                  ` · ${t("home:plans.usage", { used: plan.usage.requests_sent_today, limit: plan.usage.daily_requests })}`}
              </p>
            </div>
            <ul className="hplans__list">
              {catalogue.plans.map((p) => {
                const cheapest = p.terms.length
                  ? p.terms.reduce((a, b) => (b.total_paise / b.months < a.total_paise / a.months ? b : a))
                  : null;
                const current = p.code === plan.plan_code;
                return (
                  <li key={p.code} className={`hplan${current ? " is-current" : ""}`}>
                    <span className="hplan__name">{p.name}</span>
                    {cheapest && (
                      <span className="hplan__price">
                        {t("home:plans.from", {
                          price: formatRupees(Math.round(cheapest.total_paise / cheapest.months / 100) * 100),
                        })}
                      </span>
                    )}
                    <ul className="hplan__features">
                      {p.features.slice(0, 3).map((f) => (
                        <li key={f}>{f}</li>
                      ))}
                    </ul>
                    {current && <span className="hplan__badge">{t("home:plans.yours")}</span>}
                  </li>
                );
              })}
            </ul>
            <Link className="hplans__all" href="/plans">
              {t("home:plans.compare")}
            </Link>
          </section>
        )}
      </main>
    </>
  );
}

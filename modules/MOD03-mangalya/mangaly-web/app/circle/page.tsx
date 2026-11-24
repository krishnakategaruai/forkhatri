"use client";

import "./circle.css";
import { useLoaderHold } from "@/lib/useLoaderHold";
import MotionTitle from "@/components/MotionTitle";

import Link from "next/link";
import SacredLoader from "@/components/SacredLoader";
import Vignette from "@/components/Vignette";
import CircleInvite from "@/components/CircleInvite";
import RelationChips from "@/components/RelationChips";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { listDrafts, type ProfileDraft } from "@/lib/draft";
import { useTranslation } from "react-i18next";

import { Avatar } from "@/components/Avatar";
import AccountButton from "@/components/AccountButton";
import ForKhatriHubLink from "@/components/ForKhatriHubLink";
import ContextChip from "@/components/ContextChip";
import { useActiveContext } from "@/lib/activeContext";
import { requireSession } from "@/lib/auth";
import { listSent, type Connection } from "@/lib/connections";
import { getSnippet, type Snippet } from "@/lib/discovery";
import {
  acceptInvitation,
  declineInvitation,
  invitationText,
  declineNote,
  listMembers,
  listNoteRequests,
  listPendingInvitations,
  listContactRequests,
  approveContactRequest,
  declineContactRequest,
  type ContactRequest,
  listSentInvitations,
  listSharedNotes,
  listSuggestions,
  type SentInvitation,
  readNote,
  removeMember,
  type Member,
  type NoteReadRequest,
  relationKey,
  setMemberRelation,
  type Relation,
  type PendingInvitation,
  type RelationshipType,
  type SharedNote,
  type Suggestion,
} from "@/lib/homeCircle";

/* FR007/FR008/FR009/FR010/FR014/FR016 · UX12/UI12/UX13 (Home Circle)
 *
 * The candidate's own Home Circle management screen: invitations addressed
 * to them (they can be invited into someone else's circle too — e.g. as a
 * sibling), who has joined their own circle, notes family members asked them
 * to read, and (FR014/UX13) suggestions a family member has forwarded from
 * Discovery. A suggestion never unlocks the suggested profile's name/photo —
 * same pre-connection-safe demographic snippet Discover itself shows, since
 * being suggested is not a consent event (FR021's identity boundary does
 * not move for this feature). "Suggestion — no action has been taken on
 * your behalf" per UX13's own required label: forwarding a suggestion is
 * explicitly NOT a connection request. A family note shows who asks and which
 * match it is about; its words appear only once the candidate chooses to read. */

type State = {
  phase: "checking" | "ready";
  pendingInvitations: PendingInvitation[];
  contactRequests: ContactRequest[];
  members: Member[];
  noteRequests: NoteReadRequest[];
  sharedNotes: SharedNote[];
  suggestions: Suggestion[];
  /* Requests already sent for the candidate this screen is about — so a parent
   * opening Circle sees what has gone out, not just who is in the family. */
  sentForCandidate: Connection[];
  /* Invitations sent that nobody has answered, and profiles still being made
   * on this phone — both belong in the circle, not only the people who joined. */
  sentInvitations: SentInvitation[];
  drafts: { key: string; draft: ProfileDraft }[];
  snippets: Record<string, Snippet | null>;
};

export default function CirclePage() {
  // [owner 2026-09-25] The loader stays at least a second, never a flash.
  const loaderHold = useLoaderHold();
  const { t, i18n } = useTranslation(["common", "circle", "profile"]);
  const { contexts, active, choose, loaded } = useActiveContext();
  const router = useRouter();
  const [state, setState] = useState<State>({
    phase: "checking",
    pendingInvitations: [],
    contactRequests: [],
    members: [],
    noteRequests: [],
    sharedNotes: [],
    suggestions: [],
    sentForCandidate: [],
    sentInvitations: [],
    drafts: [],
    snippets: {},
  });
  const meKey = useRef<string | null>(null);
  // Who "you" are in a list of other people — used to mark your own row in the
  // circle and to say which requests you sent yourself.
  const [meAccountId, setMeAccountId] = useState<string | null>(null);
  const [relBusy, setRelBusy] = useState(false);
  const [ownMode, setOwnMode] = useState<"own" | "join">("own");
  const [decidingNote, setDecidingNote] = useState<string | null>(null);

  /* `circleOf` is whose Home Circle this screen is about: the signed-in
   * member's own, or — when they are acting in a family context — the
   * candidate's. Everything below reads through it, so the parent role shows
   * the candidate's real circle rather than an emptier version of the
   * candidate's screen. */
  const family = active?.kind === "family" ? active.circle : null;
  const circleOf = family?.candidate_account_id;

  async function refresh() {
    const [
      pendingInvitations,
      members,
      noteRequests,
      sharedNotes,
      suggestions,
      contactRequests,
      sent,
    ] = await Promise.all([
      listPendingInvitations(),
      listMembers(circleOf),
      // Notes and contact requests are always addressed to the signed-in
      // member personally, in either role — they are never read "for" someone.
      listNoteRequests(),
      listSharedNotes(),
      listSuggestions(circleOf),
      listContactRequests(),
      listSent(),
    ]);
    const [sentInvitations, drafts] = await Promise.all([
      listSentInvitations(circleOf).catch(() => []),
      circleOf || !meKey.current ? Promise.resolve([]) : listDrafts(meKey.current),
    ]);
    const subject = circleOf;
    // Own context: `/connections/sent` is already scoped to this member's
    // own search, so every row is a request sent for them.
    const sentForCandidate = subject
      ? sent.filter((c) => c.subject_account_id === subject)
      : sent;
    const profileIds = [
      ...new Set([
        ...suggestions.map((s) => s.suggested_profile_id),
        ...noteRequests.map((n) => n.subject_account_id),
        ...sharedNotes.map((n) => n.subject_account_id),
        ...sentForCandidate.map((c) => c.target_account_id),
      ]),
    ];
    const snippetEntries = await Promise.all(
      profileIds.map(async (id) => [id, await getSnippet(id)] as const),
    );
    setState({
      phase: "ready",
      pendingInvitations,
      contactRequests,
      members,
      noteRequests,
      sharedNotes,
      suggestions,
      sentForCandidate,
      sentInvitations,
      drafts,
      snippets: Object.fromEntries(snippetEntries),
    });
  }

  useEffect(() => {
    if (!loaded) return;
    let alive = true;
    (async () => {
      const session = await requireSession();
      if (!alive) return;
      if (!session) {
        // requireSession() has already handed off to the ForKhatri entrance (TR16).
        return;
      }
      setMeAccountId(session.account_id);
      meKey.current = session.account_id || "member";
      await refresh();
    })();
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router, loaded, circleOf]);

  if (state.phase === "checking" || loaderHold) {
    return (
      <main className="screen screen--centered">
        <SacredLoader />
      </main>
    );
  }

  async function onAccept(id: string) {
    await acceptInvitation(id);
    // Accepting can create a new context (you now help someone) — reload the
    // session-level contexts as well as this screen.
    window.location.reload();
  }

  async function onDecline(id: string) {
    await declineInvitation(id);
    await refresh();
  }

  async function onSetRelation(membershipId: string, relation: Relation) {
    setRelBusy(true);
    const outcome = await setMemberRelation(membershipId, relation);
    setRelBusy(false);
    if (outcome.ok) await refresh();
  }

  async function onRemove(membershipId: string) {
    await removeMember(membershipId);
    await refresh();
  }

  async function onNoteDecision(noteId: string, read: boolean) {
    setDecidingNote(noteId);
    const outcome = read ? await readNote(noteId) : await declineNote(noteId);
    setDecidingNote(null);
    if (outcome.ok) await refresh();
  }

  function educationLabel(level: string | null | undefined): string | null {
    if (!level) return null;
    const key = `profile:option.highest_education_level.${level}`;
    const label = t(key);
    return label === key || label === `option.highest_education_level.${level}`
      ? level
      : label;
  }

  function authorLabel(
    name: string | null,
    relationshipType: RelationshipType,
  ): string {
    const relation = t(`circle:invite.relationshipOption.${relationshipType}`);
    return name
      ? t("circle:notes.author", { name, relationship: relation })
      : relation;
  }

  function matchSummary(accountId: string, avatarSize = 48) {
    const snippet = state.snippets[accountId];
    const headline = [
      snippet?.age ? t("profile:hub.ageYears", { age: snippet.age }) : null,
      snippet?.locality,
    ]
      .filter(Boolean)
      .join(" · ");
    const detail = [
      educationLabel(snippet?.education_level),
      snippet?.profession,
    ]
      .filter(Boolean)
      .join(" · ");
    return (
      <Link href={`/profile/${accountId}`} className="req__main note-match">
        <Avatar photoUrl={snippet?.photo_url} anonymized size={avatarSize} />
        <span className="note-match__text">
          <span className="note-match__headline">
            {headline || t("circle:notes.match")}
          </span>
          {detail && <span className="caption">{detail}</span>}
        </span>
      </Link>
    );
  }

  async function onContactDecision(id: string, approve: boolean) {
    const outcome = approve
      ? await approveContactRequest(id)
      : await declineContactRequest(id);
    if (outcome.ok) await refresh();
  }

  const pendingInvitationsCard =
    state.pendingInvitations.length > 0 ? (
      <div className="card">
        <h2 className="h2">{t("circle:pendingInvitations.title")}</h2>
        <ul className="category-list">
          {state.pendingInvitations.map((inv) => (
            <li key={inv.id} className="req req--stacked">
              <div className="req__main">
                <Avatar
                  name={inv.inviter_name ?? undefined}
                  anonymized={!inv.inviter_name}
                  size={40}
                />
                <span className="req__title">{invitationText(t, inv)}</span>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <button
                  className="cta"
                  style={{ minHeight: 40 }}
                  onClick={() => onAccept(inv.id)}
                >
                  {t("circle:pendingInvitations.accept")}
                </button>
                <button
                  className="icon-btn icon-btn--text"
                  onClick={() => onDecline(inv.id)}
                >
                  {t("circle:pendingInvitations.decline")}
                </button>
              </div>
            </li>
          ))}
        </ul>
      </div>
    ) : null;

  const contactRequestsCard =
    state.contactRequests.length > 0 ? (
      <div className="card">
        <h2 className="h2">{t("circle:contactRequests.title")}</h2>
        <ul className="category-list">
          {state.contactRequests.map((r) => (
            <li key={r.id} className="req req--stacked">
              <div className="req__main">
                <span className="req__title">
                  {t("circle:contactRequests.ask", {
                    name:
                      r.candidate_name ?? t("circle:contactRequests.someone"),
                  })}
                </span>
              </div>
              <p className="caption" style={{ margin: 0 }}>
                {t("circle:contactRequests.explain")}
              </p>
              <div style={{ display: "flex", gap: 8 }}>
                <button
                  className="cta"
                  style={{ minHeight: 40 }}
                  onClick={() => onContactDecision(r.id, true)}
                >
                  {t("circle:contactRequests.approve")}
                </button>
                <button
                  className="icon-btn icon-btn--text"
                  onClick={() => onContactDecision(r.id, false)}
                >
                  {t("circle:contactRequests.decline")}
                </button>
              </div>
            </li>
          ))}
        </ul>
      </div>
    ) : null;

  const waitingCard =
    state.sentInvitations.length > 0 ? (
      <div className="card">
        <h2 className="h2">{t("circle:waiting.title")}</h2>
        <ul className="category-list">
          {state.sentInvitations.map((inv) => (
            <li key={inv.id} className="category-card" style={{ width: "100%" }}>
              <Avatar anonymized size={44} />
              <span className="category-card__body">
                <span className="category-card__title">
                  {inv.invitee_hint ?? t(relationKey(inv.relation, inv.relationship_type))}
                </span>
                <span className="category-card__preview">
                  {[
                    t("circle:waiting.invitedAs", {
                      relationship: t(relationKey(inv.relation, inv.relationship_type)).toLowerCase(),
                    }),
                    t("circle:waiting.notAccepted"),
                  ].join(" · ")}
                </span>
              </span>
            </li>
          ))}
        </ul>
      </div>
    ) : null;

  const draftsCard =
    state.drafts.length > 0 ? (
      <div className="card">
        <h2 className="h2">{t("circle:drafts.title")}</h2>
        <ul className="category-list">
          {state.drafts.map(({ key, draft: d }) => (
            <li key={key} className="category-card" style={{ width: "100%" }}>
              <Avatar name={d.name.trim() || undefined} anonymized={!d.name.trim()} size={44} />
              <span className="category-card__body">
                <span className="category-card__title">{d.name.trim() || t("circle:drafts.unnamed")}</span>
                <span className="category-card__preview">{t("circle:drafts.kept")}</span>
              </span>
              <Link className="icon-btn icon-btn--text" href={`/profile/create?draft=${encodeURIComponent(key)}`}>
                {t("circle:drafts.continue")}
              </Link>
            </li>
          ))}
        </ul>
      </div>
    ) : null;

  const header = (
    <>
      <header className="topbar">
        <MotionTitle as="h1" className="royal-title" text={t("circle:title")} />
        <div className="topbar__actions">
          <ForKhatriHubLink />
          <AccountButton />
        </div>
      </header>
      {/* Whose search and who is being looked for, on its own line so a
          phone never cuts it short. */}
      {contexts && active && (
        <div className="page-context">
          <ContextChip contexts={contexts} active={active} onChoose={choose} />
        </div>
      )}
    </>
  );

  /* The "Looking for" answer that governs this circle. Shown on every role's
     Circle screen, and never editable from the family side: it is the
     candidate's own answer, and it is what the server ranks matches by and
     routes a family-sent request under. */
  function lookingForChip(value: "bride" | "groom" | null | undefined) {
    // Answered: the context line under the title already says it.
    if (value) return null;
    return (
      <span className="circle-chip circle-chip--muted">
        {t("circle:lookingFor.unset")}
      </span>
    );
  }

  /* One card, both roles. The candidate can remove a member; a family member
     sees exactly the same people and cannot (FR010 — removal is the
     candidate's own decision). */
  function membersCard(canRemove: boolean, emptyText: string) {
    return (
      <div className="card">
        <h2 className="h2">{t("circle:members.title")}</h2>
        {state.members.length === 0 ? (
          <div className="empty-art">
            <Vignette id="family" className="empty-art__pic" />
            <p className="caption">{emptyText}</p>
          </div>
        ) : (
          <>
            {/* Two groups by relation, one circle and one set of permissions:
                Home is the household (parents, guardian, siblings), Relatives
                is everyone else. The relation stays a label on each person. */}
            {(
              [
                [
                  "home",
                  state.members.filter(
                    (m) => m.relationship_type !== "relative",
                  ),
                ],
                [
                  "relatives",
                  state.members.filter(
                    (m) => m.relationship_type === "relative",
                  ),
                ],
              ] as const
            )
              .filter(([, group]) => group.length > 0)
              .map(([groupKey, group]) => (
                <section key={groupKey} className="member-group">
                  <h3 className="member-group__title">
                    {t(`circle:members.group.${groupKey}`)}
                    <span className="member-group__count">{group.length}</span>
                  </h3>
                  <ul className="category-list">
                    {group.map((m) => {
                      const isYou =
                        !canRemove && m.member_account_id === meAccountId;
                      return (
                        <li
                          key={m.membership_id}
                          className="category-card"
                          style={{ width: "100%" }}
                        >
                          <Avatar
                            name={m.member_name ?? undefined}
                            anonymized={!m.member_name}
                            size={44}
                          />
                          <span className="category-card__body">
                            <span className="category-card__title">
                              {m.member_name ??
                                t(relationKey(m.relation, m.relationship_type))}
                              {isYou && (
                                <span className="circle-chip circle-chip--inline">
                                  {t("circle:members.you")}
                                </span>
                              )}
                            </span>
                            <span className="category-card__preview">
                              {[
                                m.member_name
                                  ? t(
                                      relationKey(
                                        m.relation,
                                        m.relationship_type,
                                      ),
                                    )
                                  : null,
                                t("circle:members.joined", {
                                  date: new Date(
                                    m.joined_at,
                                  ).toLocaleDateString(`${i18n.language}-IN`, {
                                    day: "numeric",
                                    month: "short",
                                    year: "numeric",
                                  }),
                                }),
                              ]
                                .filter(Boolean)
                                .join(" · ")}
                            </span>
                            {/* Rows from before exact relations recorded only a
                                role ("Parent"). The candidate, or the member
                                themselves, answers the one question left —
                                "Mother or father?" — with a single tap. */}
                            {!m.relation && (canRemove || isYou) && (
                              <>
                                <span className="caption member-rel">
                                  {t(`circle:members.which.${m.relationship_type}`)}
                                </span>
                                <RelationChips
                                  value={null}
                                  role={m.relationship_type}
                                  busy={relBusy}
                                  onPick={(r) =>
                                    void onSetRelation(m.membership_id, r)
                                  }
                                />
                              </>
                            )}
                          </span>
                          {canRemove && (
                            <button
                              className="icon-btn icon-btn--text"
                              onClick={() => onRemove(m.membership_id)}
                            >
                              {t("circle:members.remove")}
                            </button>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                </section>
              ))}
          </>
        )}
      </div>
    );
  }

  if (family) {
    const firstName = family.candidate_name.split(" ")[0];
    const relationship = t(
      relationKey(family.relation, family.relationship_type),
    );
    return (
      <>
        {header}
        <main className="screen">
          {/* Who you are helping, what governs their matches, and the one action
              that matters here — finding matches for them. Everything a parent
              needs to start is on this first screen, without scrolling. */}
          <div className="card family-context">
            <div className="req__main">
              <Avatar name={family.candidate_name} size={52} />
              <span className="note-match__text">
                <span className="h2" style={{ margin: 0 }}>
                  {family.candidate_name}
                </span>
                <span className="caption">
                  {t("circle:family.role", { name: firstName, relationship })}
                </span>
              </span>
            </div>
            <div className="circle-chips">
              {lookingForChip(family.looking_for)}
              <span className="circle-chip circle-chip--muted">
                {t("circle:family.memberCount", {
                  count: state.members.length,
                })}
              </span>
            </div>
            <p style={{ margin: "4px 0 0" }}>
              {t("circle:family.about", { name: firstName })}
            </p>
            <div className="form__actions" style={{ marginTop: 12 }}>
              <Link href="/discover" className="cta">
                {t("circle:family.findMatches", { name: firstName })}
              </Link>
            </div>
          </div>

          {pendingInvitationsCard}

          {contactRequestsCard}

          {/* The owner's requirement, plainly: the Circle screen contains the
              Home Circle people, always — in the family role too, not only the
              candidate's own. */}
          {membersCard(
            false,
            t("circle:members.emptyFamily", { name: firstName }),
          )}

          {waitingCard}

          {/* A member can bring another relative in — the circle grows the way
              a real family does, not only through the candidate. */}
          <CircleInvite
            mode="forCandidate"
            candidateAccountId={family.candidate_account_id}
            candidateName={family.candidate_name}
            onSent={() => void refresh()}
          />

          {sentCard(
            t("circle:sent.title", { name: firstName }),
            t("circle:sent.empty", { name: firstName }),
            firstName,
          )}

          {state.suggestions.length > 0 &&
            suggestionsCard(
              t("circle:suggestions.titleFamily", { name: firstName }),
              firstName,
            )}
        </main>
      </>
    );
  }

  const hasOwnProfile = !!contexts?.own_profile;

  const familyNotesCard =
    state.noteRequests.length > 0 || state.sharedNotes.length > 0 ? (
      <div className="card">
        <h2 className="h2">{t("circle:notes.title")}</h2>
        <ul className="category-list">
          {state.noteRequests.map((r) => (
            <li key={r.id} className="req req--stacked">
              {matchSummary(r.subject_account_id)}
              <p style={{ margin: 0 }}>
                {t("circle:notes.request", {
                  name: authorLabel(r.author_name, r.relationship_type),
                })}
              </p>
              <p className="caption" style={{ margin: 0 }}>
                {t("circle:notes.requestExplain")}
              </p>
              <div style={{ display: "flex", gap: 8 }}>
                <button
                  className="cta"
                  style={{ minHeight: 40 }}
                  disabled={decidingNote === r.id}
                  onClick={() => onNoteDecision(r.id, true)}
                >
                  {t("circle:notes.read")}
                </button>
                <button
                  className="icon-btn icon-btn--text"
                  disabled={decidingNote === r.id}
                  onClick={() => onNoteDecision(r.id, false)}
                >
                  {t("circle:notes.notNow")}
                </button>
              </div>
            </li>
          ))}
          {state.sharedNotes.map((n) => (
            <li key={n.id} className="req req--stacked">
              {matchSummary(n.subject_account_id)}
              <p className="note-text">{n.content}</p>
              <p className="caption" style={{ margin: 0 }}>
                {t("circle:notes.from", {
                  name: authorLabel(n.author_name, n.relationship_type),
                  date: new Date(n.forwarded_at).toLocaleDateString(
                    `${i18n.language}-IN`,
                    { day: "numeric", month: "short", year: "numeric" },
                  ),
                })}
              </p>
            </li>
          ))}
        </ul>
      </div>
    ) : null;

  return (
    <>
      {header}

      <main className="screen">
        <p className="caption" style={{ margin: 0 }}>
          {t("circle:blurb")}
        </p>
        {/* The same always-on "Looking for" the family role sees, so both roles
            read the one answer the engine actually matches on. */}
        {hasOwnProfile && (
          <div className="circle-chips">
            {lookingForChip(contexts?.own_profile?.looking_for)}
          </div>
        )}

        {pendingInvitationsCard}

        {contactRequestsCard}

        {familyNotesCard}

        {draftsCard}

        {waitingCard}

        {/* People first, then the way to add more — the order WhatsApp's
            group info and Google Family both use. */}
        {/* [DEC-V1-030] Desktop: members beside the way to add more. An
            empty members card is not rendered — the invite's own heading
            already says there is nobody yet. */}
        <div className="circle-grid">
          {hasOwnProfile &&
            state.members.length > 0 &&
            membersCard(true, t("circle:members.empty"))}

          {/* A candidate adds family to their own circle, or joins someone
              else's (a candidate can also be a sibling) — the rarer path is a
              quiet link under the form, not half of a switch. Someone with no
              profile of their own — typically a parent — starts by asking
              their child to let them in. */}
          {(hasOwnProfile || state.pendingInvitations.length === 0) && (
            <div className="circle-invite-wrap">
              <CircleInvite
                key={hasOwnProfile ? ownMode : "join"}
                mode={hasOwnProfile ? ownMode : "join"}
                onSent={() => void refresh()}
              />
              {hasOwnProfile && (
                <button
                  type="button"
                  className="link link--button circle-switch"
                  onClick={() => setOwnMode(ownMode === "own" ? "join" : "own")}
                >
                  {ownMode === "own"
                    ? t("circle:invite.switchJoin")
                    : t("circle:invite.switchOwn")}
                </button>
              )}
            </div>
          )}
        </div>

        {state.sentForCandidate.length > 0 &&
          sentCard(t("circle:sent.titleOwn"), "", t("circle:sent.you"))}

        {state.suggestions.length > 0 &&
          suggestionsCard(t("circle:suggestions.title"))}
      </main>
    </>
  );

  /* Shared by both roles: the candidate reads it as "suggestions from your
     circle", a family member as "what your circle has suggested to <name>" —
     same rows, same pre-connection-safe snippet, only the heading differs. */
  /* Requests that went out for this search, with who sent them and where
     each stands. Shared by both roles. */
  function sentCard(title: string, empty: string, candidateFirst: string) {
    return (
      <div className="card" id="sent">
            <h2 className="h2">
              {title}
            </h2>
            {state.sentForCandidate.length === 0 ? (
              <p className="caption">
                {empty}
              </p>
            ) : (
              <ul className="category-list">
                {state.sentForCandidate.map((c) => (
                  <li key={c.id} className="req sent-row">
                    {matchSummary(c.target_account_id, 36)}
                    <span className="sent-row__side">
                      <span className={`sent-row__status sent-row__status--${c.status}`}>
                        {t(`circle:sent.status.${c.status}`)}
                      </span>
                      <span className="caption">
                        {[
                          c.acting_account_id === meAccountId
                            ? t("circle:sent.byYou")
                            : c.sent_by_family
                              ? t("circle:sent.byFamily")
                              : t("circle:sent.byCandidate", { name: candidateFirst }),
                          new Date(c.requested_at).toLocaleDateString(
                            `${i18n.language}-IN`,
                            { day: "numeric", month: "short" },
                          ),
                        ].join(" · ")}
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
    );
  }

  function suggestionsCard(title: string, candidateFirst?: string) {
    return (
      <div className="card" id="suggestions">
        <h2 className="h2">{title}</h2>
        <ul className="category-list">
          {state.suggestions.map((s) => {
            const snippet = state.snippets[s.suggested_profile_id];
            // Who they are first (open first name, age), then what they do.
            const who = [
              snippet?.name,
              snippet?.age ? t("profile:hub.ageYears", { age: snippet.age }) : null,
            ].filter(Boolean);
            const work = [
              educationLabel(snippet?.education_level),
              snippet?.profession,
            ].filter(Boolean);
            const relationship = t(
              `profile:view.share.relationship.${s.suggested_by_relationship_type}`,
            );
            return (
              <li key={s.id} className="req req--stacked">
                <div className="req__main">
                  <Avatar photoUrl={snippet?.photo_url} anonymized size={56} />
                  <span
                    className="req__title"
                    style={{ flexDirection: "column", display: "flex" }}
                  >
                    <span style={{ fontWeight: 600 }}>
                      {(who.length ? who : work).join(" · ") ||
                        t("circle:suggestions.unknownProfile")}
                    </span>
                    <span className="caption">
                      {[...(who.length ? work : []), snippet?.locality]
                        .filter(Boolean)
                        .join(" · ")}
                    </span>
                  </span>
                </div>
                <p className="caption" style={{ margin: 0 }}>
                  {/* Worded from the reader's seat: the member who suggested
                      it, another member of the circle, or the candidate. */}
                  {s.suggested_by_is_you
                    ? candidateFirst
                      ? t("circle:suggestions.fromYou", { name: candidateFirst })
                      : t("circle:suggestions.fromYouSelf")
                    : candidateFirst
                      ? t("circle:suggestions.fromFamily", {
                          name: candidateFirst,
                          relationship,
                        })
                      : t("circle:suggestions.from", { relationship })}
                </p>
                {s.note && (
                  <p
                    className="caption"
                    style={{ margin: 0, fontStyle: "italic" }}
                  >
                    “{s.note}”
                  </p>
                )}
                <p className="caption" style={{ margin: 0, opacity: 0.75 }}>
                  {candidateFirst
                    ? t("circle:suggestions.noActionTakenFamily", {
                        name: candidateFirst,
                      })
                    : t("circle:suggestions.noActionTaken")}
                </p>
              </li>
            );
          })}
        </ul>
      </div>
    );
  }
}

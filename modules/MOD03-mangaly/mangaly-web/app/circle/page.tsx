'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Avatar } from '@/components/Avatar';
import ForKhatriHubLink from '@/components/ForKhatriHubLink';
import ContextChip from '@/components/ContextChip';
import { useActiveContext } from '@/lib/activeContext';
import { requireSession } from '@/lib/auth';
import { listSent, type Connection } from '@/lib/connections';
import { getSnippet, type Snippet } from '@/lib/discovery';
import {
  acceptInvitation,
  declineInvitation,
  declineNote,
  invite,
  listMembers,
  listNoteRequests,
  listPendingInvitations,
  listContactRequests,
  approveContactRequest,
  declineContactRequest,
  type ContactRequest,
  listSharedNotes,
  listSuggestions,
  readNote,
  removeMember,
  type Member,
  type NoteReadRequest,
  type PendingInvitation,
  type RelationshipType,
  type SharedNote,
  type Suggestion,
} from '@/lib/homeCircle';

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
  phase: 'checking' | 'ready';
  pendingInvitations: PendingInvitation[];
  contactRequests: ContactRequest[];
  members: Member[];
  noteRequests: NoteReadRequest[];
  sharedNotes: SharedNote[];
  suggestions: Suggestion[];
  /* Requests already sent for the candidate this screen is about — so a parent
   * opening Circle sees what has gone out, not just who is in the family. */
  sentForCandidate: Connection[];
  snippets: Record<string, Snippet | null>;
};

const RELATIONSHIPS: RelationshipType[] = ['parent', 'sibling', 'relative'];

export default function CirclePage() {
  const { t, i18n } = useTranslation(['common', 'circle', 'profile']);
  const { contexts, active, choose, loaded } = useActiveContext();
  const router = useRouter();
  const [state, setState] = useState<State>({
    phase: 'checking',
    pendingInvitations: [],
    contactRequests: [],
    members: [],
    noteRequests: [],
    sharedNotes: [],
    suggestions: [],
    sentForCandidate: [],
    snippets: {},
  });
  // Who "you" are in a list of other people — used to mark your own row in the
  // circle and to say which requests you sent yourself.
  const [meAccountId, setMeAccountId] = useState<string | null>(null);
  const [identifier, setIdentifier] = useState('');
  const [relationship, setRelationship] = useState<RelationshipType>('relative');
  const [inviting, setInviting] = useState(false);
  const [inviteError, setInviteError] = useState<string | null>(null);
  const [inviteSuccess, setInviteSuccess] = useState(false);
  const [decidingNote, setDecidingNote] = useState<string | null>(null);

  /* `circleOf` is whose Home Circle this screen is about: the signed-in
   * member's own, or — when they are acting in a family context — the
   * candidate's. Everything below reads through it, so the parent role shows
   * the candidate's real circle rather than an emptier version of the
   * candidate's screen. */
  const family = active?.kind === 'family' ? active.circle : null;
  const circleOf = family?.candidate_account_id;

  async function refresh() {
    const [pendingInvitations, members, noteRequests, sharedNotes, suggestions, contactRequests, sent] =
      await Promise.all([
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
    const subject = circleOf;
    const sentForCandidate = subject ? sent.filter((c) => c.subject_account_id === subject) : [];
    const profileIds = [
      ...new Set([
        ...suggestions.map((s) => s.suggested_profile_id),
        ...noteRequests.map((n) => n.subject_account_id),
        ...sharedNotes.map((n) => n.subject_account_id),
        ...sentForCandidate.map((c) => c.target_account_id),
      ]),
    ];
    const snippetEntries = await Promise.all(profileIds.map(async (id) => [id, await getSnippet(id)] as const));
    setState({
      phase: 'ready',
      pendingInvitations,
      contactRequests,
      members,
      noteRequests,
      sharedNotes,
      suggestions,
      sentForCandidate,
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
      await refresh();
    })();
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router, loaded, circleOf]);

  if (state.phase === 'checking') {
    return (
      <main className="screen screen--centered">
        <p className="caption">{t('common:state.loading')}</p>
      </main>
    );
  }

  async function onInvite() {
    if (!identifier.trim()) return;
    setInviting(true);
    setInviteError(null);
    setInviteSuccess(false);
    const outcome = await invite(identifier.trim(), relationship);
    setInviting(false);
    if (!outcome.ok) {
      setInviteError(
        outcome.message ??
          (outcome.status === 0 ? t('circle:error.network') : t('circle:error.alreadyInvited'))
      );
      return;
    }
    setIdentifier('');
    setInviteSuccess(true);
    await refresh();
  }

  async function onAccept(id: string) {
    await acceptInvitation(id);
    await refresh();
  }

  async function onDecline(id: string) {
    await declineInvitation(id);
    await refresh();
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
    return label === key || label === `option.highest_education_level.${level}` ? level : label;
  }

  function authorLabel(name: string | null, relationshipType: RelationshipType): string {
    const relation = t(`circle:invite.relationshipOption.${relationshipType}`);
    return name ? t('circle:notes.author', { name, relationship: relation }) : relation;
  }

  function matchSummary(accountId: string) {
    const snippet = state.snippets[accountId];
    const headline = [
      snippet?.age ? t('profile:hub.ageYears', { age: snippet.age }) : null,
      snippet?.locality,
    ]
      .filter(Boolean)
      .join(' · ');
    const detail = [educationLabel(snippet?.education_level), snippet?.profession].filter(Boolean).join(' · ');
    return (
      <Link href={`/profile/${accountId}`} className="req__main note-match">
        <Avatar photoUrl={snippet?.photo_url} anonymized size={48} />
        <span className="note-match__text">
          <span className="note-match__headline">{headline || t('circle:notes.match')}</span>
          {detail && <span className="caption">{detail}</span>}
        </span>
      </Link>
    );
  }

  async function onContactDecision(id: string, approve: boolean) {
    const outcome = approve ? await approveContactRequest(id) : await declineContactRequest(id);
    if (outcome.ok) await refresh();
  }

  const pendingInvitationsCard =
    state.pendingInvitations.length > 0 ? (

          <div className="card">
            <h2 className="h2">{t('circle:pendingInvitations.title')}</h2>
            <ul className="category-list">
              {state.pendingInvitations.map((inv) => (
                <li key={inv.id} className="req req--stacked">
                  <div className="req__main">
                    <Avatar anonymized size={40} />
                    <span className="req__title">
                      {t('circle:pendingInvitations.from', {
                        relationship: t(`circle:invite.relationshipOption.${inv.relationship_type}`),
                      })}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button className="cta" style={{ minHeight: 40 }} onClick={() => onAccept(inv.id)}>
                      {t('circle:pendingInvitations.accept')}
                    </button>
                    <button
                      className="icon-btn icon-btn--text"
                      onClick={() => onDecline(inv.id)}
                    >
                      {t('circle:pendingInvitations.decline')}
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
            <h2 className="h2">{t('circle:contactRequests.title')}</h2>
            <ul className="category-list">
              {state.contactRequests.map((r) => (
                <li key={r.id} className="req req--stacked">
                  <div className="req__main">
                    <span className="req__title">
                      {t('circle:contactRequests.ask', { name: r.candidate_name ?? t('circle:contactRequests.someone') })}
                    </span>
                  </div>
                  <p className="caption" style={{ margin: 0 }}>
                    {t('circle:contactRequests.explain')}
                  </p>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button className="cta" style={{ minHeight: 40 }} onClick={() => onContactDecision(r.id, true)}>
                      {t('circle:contactRequests.approve')}
                    </button>
                    <button className="icon-btn icon-btn--text" onClick={() => onContactDecision(r.id, false)}>
                      {t('circle:contactRequests.decline')}
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          </div>
    ) : null;

  const header = (
    <header className="topbar">
      <h1>{t('circle:title')}</h1>
      <div className="topbar__actions">
        {contexts && active && <ContextChip contexts={contexts} active={active} onChoose={choose} />}
        <ForKhatriHubLink />
      </div>
    </header>
  );

  /* The "Looking for" answer that governs this circle. Shown on every role's
     Circle screen, and never editable from the family side: it is the
     candidate's own answer, and it is what the server ranks matches by and
     routes a family-sent request under. */
  function lookingForChip(value: 'bride' | 'groom' | null | undefined) {
    return (
      <span className={`circle-chip${value ? '' : ' circle-chip--muted'}`}>
        {value
          ? t('circle:lookingFor.chip', { value: t(`profile:option.looking_for.${value}`) })
          : t('circle:lookingFor.unset')}
      </span>
    );
  }

  /* One card, both roles. The candidate can remove a member; a family member
     sees exactly the same people and cannot (FR010 — removal is the
     candidate's own decision). */
  function membersCard(canRemove: boolean, emptyText: string) {
    return (
      <div className="card">
        <h2 className="h2">{t('circle:members.title')}</h2>
        {state.members.length === 0 ? (
          <p className="caption">{emptyText}</p>
        ) : (
          <ul className="category-list">
            {state.members.map((m) => {
              const isYou = !canRemove && m.member_account_id === meAccountId;
              return (
                <li key={m.membership_id} className="category-card" style={{ width: '100%' }}>
                  <Avatar name={m.member_name ?? undefined} anonymized={!m.member_name} size={44} />
                  <span className="category-card__body">
                    <span className="category-card__title">
                      {m.member_name ?? t(`circle:invite.relationshipOption.${m.relationship_type}`)}
                      {isYou && <span className="circle-chip circle-chip--inline">{t('circle:members.you')}</span>}
                    </span>
                    <span className="category-card__preview">
                      {[
                        m.member_name ? t(`circle:invite.relationshipOption.${m.relationship_type}`) : null,
                        t('circle:members.joined', {
                          date: new Date(m.joined_at).toLocaleDateString(i18n.language),
                        }),
                      ]
                        .filter(Boolean)
                        .join(' · ')}
                    </span>
                  </span>
                  {canRemove && (
                    <button className="icon-btn icon-btn--text" onClick={() => onRemove(m.membership_id)}>
                      {t('circle:members.remove')}
                    </button>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </div>
    );
  }

  if (family) {
    const firstName = family.candidate_name.split(' ')[0];
    const relationship = t(`circle:invite.relationshipOption.${family.relationship_type}`);
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
                <span className="h2" style={{ margin: 0 }}>{family.candidate_name}</span>
                <span className="caption">{t('circle:family.role', { name: firstName, relationship })}</span>
              </span>
            </div>
            <div className="circle-chips">
              {lookingForChip(family.looking_for)}
              <span className="circle-chip circle-chip--muted">
                {t('circle:family.memberCount', { count: state.members.length })}
              </span>
            </div>
            <p style={{ margin: '4px 0 0' }}>{t('circle:family.about', { name: firstName })}</p>
            <div className="form__actions" style={{ marginTop: 12 }}>
              <Link href="/discover" className="cta">
                {t('circle:family.findMatches', { name: firstName })}
              </Link>
            </div>
          </div>

          {pendingInvitationsCard}

          {contactRequestsCard}

          {/* The owner's requirement, plainly: the Circle screen contains the
              Home Circle people, always — in the family role too, not only the
              candidate's own. */}
          {membersCard(false, t('circle:members.emptyFamily', { name: firstName }))}

          <div className="card">
            <h2 className="h2">{t('circle:sent.title', { name: firstName })}</h2>
            {state.sentForCandidate.length === 0 ? (
              <p className="caption">{t('circle:sent.empty', { name: firstName })}</p>
            ) : (
              <ul className="category-list">
                {state.sentForCandidate.map((c) => (
                  <li key={c.id} className="req req--stacked">
                    {matchSummary(c.target_account_id)}
                    <p className="caption" style={{ margin: 0 }}>
                      {[
                        t(`circle:sent.status.${c.status}`),
                        c.acting_account_id === meAccountId
                          ? t('circle:sent.byYou')
                          : c.sent_by_family
                            ? t('circle:sent.byFamily')
                            : t('circle:sent.byCandidate', { name: firstName }),
                        new Date(c.requested_at).toLocaleDateString(i18n.language),
                      ].join(' · ')}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {state.suggestions.length > 0 && suggestionsCard(t('circle:suggestions.titleFamily', { name: firstName }))}
        </main>
      </>
    );
  }

  const familyNotesCard =
    state.noteRequests.length > 0 || state.sharedNotes.length > 0 ? (
      <div className="card">
        <h2 className="h2">{t('circle:notes.title')}</h2>
        <ul className="category-list">
          {state.noteRequests.map((r) => (
            <li key={r.id} className="req req--stacked">
              {matchSummary(r.subject_account_id)}
              <p style={{ margin: 0 }}>{t('circle:notes.request', { name: authorLabel(r.author_name, r.relationship_type) })}</p>
              <p className="caption" style={{ margin: 0 }}>
                {t('circle:notes.requestExplain')}
              </p>
              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  className="cta"
                  style={{ minHeight: 40 }}
                  disabled={decidingNote === r.id}
                  onClick={() => onNoteDecision(r.id, true)}
                >
                  {t('circle:notes.read')}
                </button>
                <button
                  className="icon-btn icon-btn--text"
                  disabled={decidingNote === r.id}
                  onClick={() => onNoteDecision(r.id, false)}
                >
                  {t('circle:notes.notNow')}
                </button>
              </div>
            </li>
          ))}
          {state.sharedNotes.map((n) => (
            <li key={n.id} className="req req--stacked">
              {matchSummary(n.subject_account_id)}
              <p className="note-text">{n.content}</p>
              <p className="caption" style={{ margin: 0 }}>
                {t('circle:notes.from', {
                  name: authorLabel(n.author_name, n.relationship_type),
                  date: new Date(n.forwarded_at).toLocaleDateString(i18n.language),
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
          {t('circle:blurb')}
        </p>
        {/* The same always-on "Looking for" the family role sees, so both roles
            read the one answer the engine actually matches on. */}
        <div className="circle-chips">{lookingForChip(contexts?.own_profile?.looking_for)}</div>

        {pendingInvitationsCard}

        {contactRequestsCard}

        {familyNotesCard}

        <div className="card">
          <h2 className="h2">{t('circle:invite.title')}</h2>
          <div className="field__box">
            <input
              className="field__input"
              placeholder=" "
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
            />
            <label className="field__label">{t('circle:invite.identifier')}</label>
          </div>
          <div className="label" style={{ marginTop: 12 }}>
            {t('circle:invite.relationship')}
          </div>
          <div className="segmented segmented--3" role="radiogroup">
            {RELATIONSHIPS.map((r) => (
              <button
                key={r}
                type="button"
                className={`segmented__opt${relationship === r ? ' is-active' : ''}`}
                aria-pressed={relationship === r}
                onClick={() => setRelationship(r)}
              >
                {t(`circle:invite.relationshipOption.${r}`)}
              </button>
            ))}
          </div>
          <p className="form__error">{inviteError ?? ''}</p>
          {inviteSuccess && <p className="caption">{t('circle:invite.success')}</p>}
          <div className="form__actions" style={{ marginTop: 12 }}>
            <button className="cta" disabled={inviting || !identifier.trim()} onClick={onInvite}>
              <span className={inviting ? 'cta__label--hidden' : undefined}>
                {t('circle:invite.submit')}
              </span>
              {inviting && <span className="cta__spinner" aria-hidden="true" />}
            </button>
          </div>
        </div>

        {membersCard(true, t('circle:members.empty'))}

        {state.suggestions.length > 0 && suggestionsCard(t('circle:suggestions.title'))}
      </main>
    </>
  );

  /* Shared by both roles: the candidate reads it as "suggestions from your
     circle", a family member as "what your circle has suggested to <name>" —
     same rows, same pre-connection-safe snippet, only the heading differs. */
  function suggestionsCard(title: string) {
    return (
      <div className="card">
        <h2 className="h2">{title}</h2>
        <ul className="category-list">
          {state.suggestions.map((s) => {
            const snippet = state.snippets[s.suggested_profile_id];
            return (
              <li key={s.id} className="req req--stacked">
                <div className="req__main">
                  <Avatar photoUrl={snippet?.photo_url} anonymized size={56} />
                  <span className="req__title" style={{ flexDirection: 'column', display: 'flex' }}>
                    <span style={{ fontWeight: 600 }}>
                      {[educationLabel(snippet?.education_level), snippet?.profession].filter(Boolean).join(' · ') ||
                        t('circle:suggestions.unknownProfile')}
                    </span>
                    <span className="caption">{snippet?.locality ?? ''}</span>
                  </span>
                </div>
                <p className="caption" style={{ margin: 0 }}>
                  {t('circle:suggestions.from', {
                    relationship: t(`profile:view.share.relationship.${s.suggested_by_relationship_type}`),
                  })}
                </p>
                {s.note && (
                  <p className="caption" style={{ margin: 0, fontStyle: 'italic' }}>
                    “{s.note}”
                  </p>
                )}
                <p className="caption" style={{ margin: 0, opacity: 0.75 }}>
                  {t('circle:suggestions.noActionTaken')}
                </p>
              </li>
            );
          })}
        </ul>
      </div>
    );
  }
}

'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Avatar } from '@/components/Avatar';
import { getSession } from '@/lib/auth';
import { getSnippet, type Snippet } from '@/lib/discovery';
import {
  acceptInvitation,
  declineInvitation,
  forwardNote,
  invite,
  listMembers,
  listNotes,
  listPendingInvitations,
  listPendingNotes,
  listSuggestions,
  removeMember,
  type Member,
  type Note,
  type PendingInvitation,
  type PendingNote,
  type RelationshipType,
  type Suggestion,
} from '@/lib/homeCircle';

/* FR007/FR008/FR009/FR010/FR014/FR016 · UX12/UI12/UX13 (Home Circle)
 *
 * The candidate's own Home Circle management screen: invitations addressed
 * to them (they can be invited into someone else's circle too — e.g. as a
 * sibling), who has joined their own circle, family-notes approval, and
 * (FR014/UX13) suggestions a family member has forwarded from Discovery.
 * A suggestion never unlocks the suggested profile's name/photo — same
 * pre-connection-safe demographic snippet Discover itself shows, since
 * being suggested is not a consent event (FR021's identity boundary does
 * not move for this feature). "Suggestion — no action has been taken on
 * your behalf" per UX13's own required label: forwarding a suggestion is
 * explicitly NOT a connection request. */

type State = {
  phase: 'checking' | 'ready';
  pendingInvitations: PendingInvitation[];
  members: Member[];
  pendingNotes: PendingNote[];
  notes: Note[];
  suggestions: Suggestion[];
  suggestionSnippets: Record<string, Snippet | null>;
};

const RELATIONSHIPS: RelationshipType[] = ['parent', 'sibling', 'relative'];

export default function CirclePage() {
  const { t } = useTranslation(['common', 'circle']);
  const router = useRouter();
  const [state, setState] = useState<State>({
    phase: 'checking',
    pendingInvitations: [],
    members: [],
    pendingNotes: [],
    notes: [],
    suggestions: [],
    suggestionSnippets: {},
  });
  const [identifier, setIdentifier] = useState('');
  const [relationship, setRelationship] = useState<RelationshipType>('relative');
  const [inviting, setInviting] = useState(false);
  const [inviteError, setInviteError] = useState<string | null>(null);
  const [inviteSuccess, setInviteSuccess] = useState(false);

  async function refresh() {
    const [pendingInvitations, members, pendingNotes, notes, suggestions] = await Promise.all([
      listPendingInvitations(),
      listMembers(),
      listPendingNotes(),
      listNotes(),
      listSuggestions(),
    ]);
    const snippetEntries = await Promise.all(
      suggestions.map(async (s) => [s.suggested_profile_id, await getSnippet(s.suggested_profile_id)] as const)
    );
    setState({
      phase: 'ready',
      pendingInvitations,
      members,
      pendingNotes,
      notes,
      suggestions,
      suggestionSnippets: Object.fromEntries(snippetEntries),
    });
  }

  useEffect(() => {
    let active = true;
    (async () => {
      const session = await getSession();
      if (!active) return;
      if (!session) {
        router.replace('/login');
        return;
      }
      await refresh();
    })();
    return () => {
      active = false;
    };
  }, [router]);

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

  async function onApproveNote(noteId: string) {
    await forwardNote(noteId);
    await refresh();
  }

  const forwardedNotes = state.notes.filter((n) => n.forwarded_at);

  return (
    <>
      <header className="topbar">
        <h1>{t('circle:title')}</h1>
      </header>

      <main className="screen">
        <p className="caption" style={{ margin: 0 }}>
          {t('circle:blurb')}
        </p>

        {state.pendingInvitations.length > 0 && (
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
        )}

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

        <div className="card">
          <h2 className="h2">{t('circle:members.title')}</h2>
          {state.members.length === 0 ? (
            <p className="caption">{t('circle:members.empty')}</p>
          ) : (
            <ul className="category-list">
              {state.members.map((m) => (
                <li key={m.membership_id} className="category-card" style={{ width: '100%' }}>
                  <Avatar anonymized size={44} />
                  <span className="category-card__body">
                    <span className="category-card__title">
                      {t(`circle:invite.relationshipOption.${m.relationship_type}`)}
                    </span>
                    <span className="category-card__preview">
                      {new Date(m.joined_at).toLocaleDateString()}
                    </span>
                  </span>
                  <button
                    className="icon-btn icon-btn--text"
                    onClick={() => onRemove(m.membership_id)}
                  >
                    {t('circle:members.remove')}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {state.suggestions.length > 0 && (
          <div className="card">
            <h2 className="h2">{t('circle:suggestions.title')}</h2>
            <ul className="category-list">
              {state.suggestions.map((s) => {
                const snippet = state.suggestionSnippets[s.suggested_profile_id];
                return (
                  <li key={s.id} className="req req--stacked">
                    <div className="req__main">
                      <Avatar anonymized size={40} />
                      <span className="req__title" style={{ flexDirection: 'column', display: 'flex' }}>
                        <span style={{ fontWeight: 600 }}>
                          {[snippet?.education_level, snippet?.profession].filter(Boolean).join(' · ') ||
                            t('circle:suggestions.unknownProfile')}
                        </span>
                        <span className="caption">{snippet?.locality ?? ''}</span>
                      </span>
                    </div>
                    <p className="caption" style={{ margin: 0 }}>
                      {t('circle:suggestions.from', {
                        relationship: t(`circle:invite.relationshipOption.${s.suggested_by_relationship_type}`),
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
        )}

        <div className="card">
          <h2 className="h2">{t('circle:notes.title')}</h2>
          {state.pendingNotes.length > 0 && (
            <p className="caption">
              {t('circle:notes.pendingCount', { count: state.pendingNotes.length })}
            </p>
          )}
          {state.pendingNotes.map((n) => (
            <div key={n.id} className="attr-field">
              <div className="attr-field__head">
                <span className="attr-field__label">
                  {new Date(n.created_at).toLocaleDateString()}
                </span>
                <button
                  type="button"
                  className="attr-field__decline"
                  onClick={() => onApproveNote(n.id)}
                >
                  {t('circle:notes.approve')}
                </button>
              </div>
            </div>
          ))}
          {forwardedNotes.length === 0 && state.pendingNotes.length === 0 ? (
            <p className="caption">{t('circle:notes.empty')}</p>
          ) : (
            forwardedNotes.map((n) => (
              <div className="attr-field" key={n.id}>
                <p className="body-lg" style={{ margin: 0 }}>
                  {n.content}
                </p>
                <span className="caption">{new Date(n.created_at).toLocaleDateString()}</span>
              </div>
            ))
          )}
        </div>
      </main>
    </>
  );
}

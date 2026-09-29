'use client';

import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import VoiceInput from '@/components/VoiceInput';
import {
  addNote,
  askToReadNote,
  deleteNote,
  editNote,
  listMyNotes,
  type FamilyNote,
  type Outcome,
} from '@/lib/homeCircle';

/* FR016 · UX13 — a Home Circle member's private notes about one match.
 *
 * Only the author can read these. A note reaches the candidate only when the
 * author asks, after seeing exactly the words the candidate would read, and
 * the candidate agrees. Everything happens in place on the profile: writing,
 * editing, deleting and asking, with no sheet or sub-screen in between.
 * Editing a note that was asked about makes it private again, so the
 * candidate is only ever asked about the words they would actually read. */

const MAX_LENGTH = 1000;

type Props = {
  membershipId: string;
  subjectAccountId: string;
  candidateName: string;
};

export default function FamilyNotes({ membershipId, subjectAccountId, candidateName }: Props) {
  const { t, i18n } = useTranslation(['profile']);
  const [notes, setNotes] = useState<FamilyNote[] | null>(null);
  const [draft, setDraft] = useState('');
  const [editing, setEditing] = useState<{ id: string; text: string } | null>(null);
  const [asking, setAsking] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const name = candidateName.split(' ')[0];

  useEffect(() => {
    let active = true;
    void listMyNotes(membershipId, subjectAccountId).then((rows) => {
      if (active) setNotes(rows);
    });
    return () => {
      active = false;
    };
  }, [membershipId, subjectAccountId]);

  async function run<T>(action: () => Promise<Outcome<T>>, onDone: (data: T) => void) {
    setBusy(true);
    setError(null);
    const outcome = await action();
    setBusy(false);
    if (!outcome.ok) {
      setError(outcome.message ?? t('profile:notes.error'));
      return;
    }
    onDone(outcome.data);
  }

  function replace(note: FamilyNote) {
    setNotes((prev) => (prev ?? []).map((n) => (n.id === note.id ? note : n)));
  }

  function formatDate(iso: string): string {
    return new Date(iso).toLocaleDateString(i18n.language, { day: 'numeric', month: 'short' });
  }

  return (
    <section className="card family-notes" aria-label={t('profile:notes.title')}>
      <div className="label">{t('profile:notes.title')}</div>
      <p className="caption" style={{ margin: 0 }}>
        {t('profile:notes.intro', { name })}
      </p>

      <div className="sheet__field">
        <label className="sr-only" htmlFor="family-note-draft">
          {t('profile:notes.placeholder')}
        </label>
        <textarea
          id="family-note-draft"
          className="field__input prompt-textarea"
          maxLength={MAX_LENGTH}
          placeholder={t('profile:notes.placeholder')}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
        />
        <div className="family-notes__row">
          <span className="caption">{t('profile:notes.guard')}</span>
          <VoiceInput onText={(said) => setDraft((d) => (d ? `${d} ${said}` : said))} />
          <button
            type="button"
            className="quick-pick__chip quick-pick__chip--active"
            disabled={busy || !draft.trim()}
            onClick={() =>
              void run(
                () => addNote(membershipId, subjectAccountId, draft.trim()),
                (note) => {
                  setNotes((prev) => [note, ...(prev ?? [])]);
                  setDraft('');
                }
              )
            }
          >
            {t('profile:notes.save')}
          </button>
        </div>
      </div>

      {error && (
        <p className="form__error" role="alert">
          {error}
        </p>
      )}

      {notes && notes.length > 0 && (
        <ul className="family-notes__list">
          {notes.map((note) => (
            <li key={note.id} className="family-note">
              {editing?.id === note.id ? (
                <>
                  <textarea
                    className="field__input prompt-textarea"
                    maxLength={MAX_LENGTH}
                    aria-label={t('profile:notes.edit')}
                    value={editing.text}
                    onChange={(e) => setEditing({ id: note.id, text: e.target.value })}
                  />
                  <div className="family-notes__row family-notes__row--end">
                    <button type="button" className="quick-pick__chip" onClick={() => setEditing(null)}>
                      {t('profile:notes.cancel')}
                    </button>
                    <button
                      type="button"
                      className="quick-pick__chip quick-pick__chip--active"
                      disabled={busy || !editing.text.trim()}
                      onClick={() =>
                        void run(
                          () => editNote(note.id, editing.text.trim()),
                          (updated) => {
                            replace(updated);
                            setEditing(null);
                          }
                        )
                      }
                    >
                      {t('profile:notes.saveEdit')}
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <p className="note-text">{note.content}</p>
                  <span className={`family-note__status family-note__status--${note.status}`}>
                    {t(`profile:notes.status.${note.status}`, { name })} · {formatDate(note.updated_at)}
                  </span>
                  {asking === note.id ? (
                    <div className="share-row__confirm">
                      <p style={{ margin: 0 }}>{t('profile:notes.askConfirm', { name })}</p>
                      <blockquote className="family-note__preview">{note.content}</blockquote>
                      <div className="family-notes__row family-notes__row--end">
                        <button type="button" className="quick-pick__chip" onClick={() => setAsking(null)}>
                          {t('profile:notes.cancel')}
                        </button>
                        <button
                          type="button"
                          className="cta"
                          disabled={busy}
                          onClick={() =>
                            void run(
                              () => askToReadNote(note.id),
                              (updated) => {
                                replace(updated);
                                setAsking(null);
                              }
                            )
                          }
                        >
                          {t('profile:notes.askSend')}
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="family-notes__row family-notes__row--end">
                      {note.status !== 'shared' && (
                        <button
                          type="button"
                          className="quick-pick__chip"
                          disabled={busy}
                          onClick={() => setEditing({ id: note.id, text: note.content })}
                        >
                          {t('profile:notes.edit')}
                        </button>
                      )}
                      <button
                        type="button"
                        className="quick-pick__chip"
                        disabled={busy}
                        onClick={() =>
                          void run(
                            () => deleteNote(note.id),
                            () => setNotes((prev) => (prev ?? []).filter((n) => n.id !== note.id))
                          )
                        }
                      >
                        {t('profile:notes.delete')}
                      </button>
                      {note.status === 'private' && (
                        <button
                          type="button"
                          className="quick-pick__chip quick-pick__chip--active"
                          disabled={busy}
                          onClick={() => setAsking(note.id)}
                        >
                          {t('profile:notes.ask', { name })}
                        </button>
                      )}
                    </div>
                  )}
                </>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

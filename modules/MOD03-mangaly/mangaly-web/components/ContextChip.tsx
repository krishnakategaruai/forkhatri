'use client';

import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import type { ActiveContext } from '@/lib/activeContext';
import type { Contexts } from '@/lib/homeCircle';

/* FR097 · UX06 — always says in words whose search is active, and lets a
 * member with more than one search switch between them. Violet is reserved
 * for "acting for someone else" across the app. */

type Props = {
  contexts: Contexts;
  active: ActiveContext;
  onChoose: (next: ActiveContext) => void;
};

function firstName(name: string): string {
  return name.split(' ')[0] || name;
}

export default function ContextChip({ contexts, active, onChoose }: Props) {
  const { t } = useTranslation(['common', 'circle']);
  const [open, setOpen] = useState(false);
  const [announcement, setAnnouncement] = useState('');

  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false);
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open]);

  const total = (contexts.own_profile ? 1 : 0) + contexts.circles.length;
  if (active.kind === 'self' && contexts.circles.length === 0) return null;

  const family = active.kind === 'family';
  const label = family
    ? t('common:context.viewing', { name: firstName(active.circle.candidate_name) })
    : t('common:context.yourSearch');
  const switchable = total > 1;

  function select(next: ActiveContext) {
    onChoose(next);
    setOpen(false);
    setAnnouncement(
      next.kind === 'family'
        ? t('common:context.nowViewing', { name: firstName(next.circle.candidate_name) })
        : t('common:context.nowViewingSelf')
    );
  }

  return (
    <>
      <button
        type="button"
        className={`context-chip${family ? ' context-chip--family' : ''}`}
        onClick={() => switchable && setOpen(true)}
        aria-haspopup={switchable ? 'dialog' : undefined}
        aria-disabled={!switchable}
      >
        <span className="context-chip__dot" aria-hidden="true" />
        <span>{label}</span>
        {switchable && (
          <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true">
            <path fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" d="m7 10 5 5 5-5" />
          </svg>
        )}
      </button>
      <span className="sr-only" aria-live="polite">
        {announcement}
      </span>

      {open && (
        <div className="sheet-backdrop" onClick={() => setOpen(false)}>
          <div
            className="sheet"
            role="dialog"
            aria-modal="true"
            aria-label={t('common:context.switchTitle')}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="sheet__handle" aria-hidden="true" />
            <div className="sheet__head">
              <h2 className="sheet__title">{t('common:context.switchTitle')}</h2>
            </div>
            <ul className="context-list">
              {contexts.own_profile && (
                <li>
                  <button
                    type="button"
                    className="context-row"
                    aria-current={active.kind === 'self' ? 'true' : undefined}
                    onClick={() => select({ kind: 'self' })}
                  >
                    <span className="context-row__name">{t('common:context.you')}</span>
                    <span className="caption">{t('common:context.yourProfile')}</span>
                  </button>
                </li>
              )}
              {contexts.circles.map((circle) => (
                <li key={circle.candidate_account_id}>
                  <button
                    type="button"
                    className="context-row context-row--family"
                    aria-current={
                      active.kind === 'family' && active.circle.candidate_account_id === circle.candidate_account_id
                        ? 'true'
                        : undefined
                    }
                    onClick={() => select({ kind: 'family', circle })}
                  >
                    <span className="context-row__name">{circle.candidate_name}</span>
                    <span className="caption">
                      {t('common:context.role', {
                        relationship: t(`circle:invite.relationshipOption.${circle.relationship_type}`),
                      })}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </>
  );
}

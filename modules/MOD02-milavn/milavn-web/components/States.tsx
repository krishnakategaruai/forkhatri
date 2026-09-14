'use client';

/* Generic system states (FR084/UX18/UI18): on-brand single-colour line art,
 * specific copy supplied by the calling screen, fade in over the region only. */

import { useTranslation } from 'react-i18next';

const Illustration = ({ kind }: { kind: 'empty' | 'error' }) => (
  <svg viewBox="0 0 64 64" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" aria-hidden="true">
    {kind === 'empty' ? (
      <>
        <circle cx="32" cy="30" r="16" />
        <path d="M24 34c2.5 3 5.5 4.5 8 4.5s5.5-1.5 8-4.5M26 26h.01M38 26h.01M16 52h32" />
        <circle cx="12" cy="14" r="1.2" /><circle cx="52" cy="12" r="1.2" /><circle cx="54" cy="46" r="1.2" />
      </>
    ) : (
      <>
        <rect x="14" y="16" width="36" height="28" rx="6" />
        <path d="M22 26l8 8m0-8l-8 8M36 24h8M36 30h8M36 36h6M24 52h16" />
      </>
    )}
  </svg>
);

export function EmptyState({ message, action, onAction }: { message: string; action?: string; onAction?: () => void }) {
  return (
    <div className="state state--inline" role="status">
      <Illustration kind="empty" />
      <p>{message}</p>
      {action && onAction && <button className="btn btn--secondary btn--sm" onClick={onAction}>{action}</button>}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message?: string; onRetry?: () => void }) {
  const { t } = useTranslation();
  return (
    <div className="state state--inline" role="alert">
      <Illustration kind="error" />
      <p>{message ?? t('state.error')}</p>
      {onRetry && <button className="btn btn--secondary btn--sm" onClick={onRetry}>{t('state.retry')}</button>}
    </div>
  );
}

export function CardSkeleton({ count = 2 }: { count?: number }) {
  return (
    <div className="stack" aria-busy="true" aria-label="Loading">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="card card--flush">
          <div className="sk sk--card" />
          <div className="stack" style={{ padding: 14 }}>
            <div className="sk sk--line" style={{ width: '70%' }} />
            <div className="sk sk--line" style={{ width: '45%' }} />
          </div>
        </div>
      ))}
    </div>
  );
}

export function Toast({ text }: { text: string | null }) {
  if (!text) return null;
  return <div className="toast" role="status">{text}</div>;
}

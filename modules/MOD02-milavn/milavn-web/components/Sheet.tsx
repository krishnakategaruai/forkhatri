'use client';

/* Bottom sheet for lightweight actions (UX05 research: sheets for light,
 * non-disruptive actions; modals for high-stakes, irreversible ones). */

import { useEffect } from 'react';

export function Sheet({ open, onClose, children, label }: { open: boolean; onClose: () => void; children: React.ReactNode; label: string }) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);
  if (!open) return null;
  return (
    <>
      <div className="scrim-layer" onClick={onClose} aria-hidden="true" />
      <div className="sheet" role="dialog" aria-modal="true" aria-label={label}>
        <div className="sheet__grab" />
        {children}
      </div>
    </>
  );
}

export function Modal({ open, onClose, children, label }: { open: boolean; onClose: () => void; children: React.ReactNode; label: string }) {
  if (!open) return null;
  return (
    <>
      <div className="scrim-layer" onClick={onClose} aria-hidden="true" />
      <div className="modal" role="alertdialog" aria-modal="true" aria-label={label}>{children}</div>
    </>
  );
}

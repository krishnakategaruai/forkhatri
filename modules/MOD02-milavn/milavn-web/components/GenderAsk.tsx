'use client';

/* Asked once, only where a women-only group needs it (migration 050). The answer is the
 * member's own, private to them, and used for nothing else. */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';

import { api, ApiError } from '@/lib/api';

export default function GenderAsk({ onAnswered }: { onAnswered: (gender: 'woman' | 'man') => void }) {
  const { t } = useTranslation();
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState<string | null>(null);

  const answer = async (gender: 'woman' | 'man') => {
    if (busy) return;
    setBusy(true); setFailed(null);
    try { await api('/circles/gender/me', { method: 'PUT', body: { gender } }); onAnswered(gender); }
    catch (e) { setFailed(e instanceof ApiError ? e.message : t('state.error')); }
    finally { setBusy(false); }
  };

  return (
    <div className="stack" style={{ gap: 10 }}>
      <span className="cx-strong">{t('group.askTitle')}</span>
      <span className="cx-caption">{t('group.askBody')}</span>
      <div className="cx-chips cx-chips--wrap">
        <button type="button" className="cx-chip" disabled={busy} onClick={() => answer('woman')}>{t('group.iAmWoman')}</button>
        <button type="button" className="cx-chip" disabled={busy} onClick={() => answer('man')}>{t('group.iAmMan')}</button>
      </div>
      {failed && <span className="cx-caption" role="alert">{failed}</span>}
    </div>
  );
}

'use client';

/* Adding people to a circle (owner, 2026-09-29: "a big missing piece"). Consent-based, the
 * Facebook-group / WhatsApp-invite model: you pick people, they get an invitation they accept
 * or decline — nobody is dropped into a circle silently. People you already know from Milavn
 * (shared circles, activities, connections, chats) come first; anyone else on Milavn can be
 * found by name. A share link covers people who aren't on Milavn yet. */

import { Check, Link2, Search } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Sheet } from '@/components/Sheet';
import { api, ApiError, resolveMediaUrl } from '@/lib/api';
import { initials } from '@/lib/format';

type Person = {
  member_id: string; display_name: string; avatar: string | null; locality_label: string | null;
  known_via: 'circle' | 'activity' | 'connection' | 'chat' | null; already_member: boolean; invited: boolean;
};

export default function InvitePeopleSheet({
  open, onClose, circleId, circleName, canShareLink, onDone,
}: {
  open: boolean; onClose: () => void; circleId: string; circleName: string; canShareLink: boolean; onDone: (message: string) => void;
}) {
  const { t } = useTranslation();
  const [q, setQ] = useState('');
  const [people, setPeople] = useState<Person[] | null>(null);
  const [picked, setPicked] = useState<Set<string>>(new Set());
  const [sending, setSending] = useState(false);
  const [link, setLink] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Suggestions with no query; search as the person types (debounced).
  useEffect(() => {
    if (!open) return;
    const term = q.trim();
    if (term.length === 1) return;
    const handle = setTimeout(() => {
      const qs = new URLSearchParams({ circle_id: circleId });
      if (term) qs.set('q', term);
      api<Person[]>(`/people/search?${qs}`).then(setPeople).catch(() => setPeople([]));
    }, term ? 250 : 0);
    return () => clearTimeout(handle);
  }, [open, q, circleId]);

  useEffect(() => { if (!open) { setPicked(new Set()); setQ(''); setLink(null); setCopied(false); setError(null); } }, [open]);

  const toggle = (id: string) => setPicked((prev) => { const next = new Set(prev); if (next.has(id)) next.delete(id); else next.add(id); return next; });

  const send = async () => {
    if (picked.size === 0 || sending) return;
    setSending(true);
    try {
      await api(`/circles/${circleId}/invites`, { body: { member_ids: [...picked] }, idempotent: true });
      onDone(t('invite.sent', { count: picked.size }));
      onClose();
    } catch (e) { setError(e instanceof ApiError ? e.message : t('state.error')); }
    finally { setSending(false); }
  };

  const makeLink = async () => {
    try {
      const r = await api<{ url_path: string }>(`/circles/${circleId}/invite-link`, { body: {} });
      const url = `${window.location.origin}${r.url_path}`;
      setLink(url);
      try { await navigator.clipboard.writeText(url); setCopied(true); } catch { setCopied(false); }
    } catch (e) { setError(e instanceof ApiError ? e.message : t('state.error')); }
  };

  const knownText = (p: Person) => (p.known_via ? t(`invite.knownVia.${p.known_via}`) : p.locality_label);

  return (
    <Sheet open={open} onClose={onClose} label={t('circles.invite')}>
      <div className="stack cx" style={{ gap: 14 }}>
        <h2 className="cx-h2">{t('circles.inviteTitle', { name: circleName })}</h2>

        {canShareLink && (
          <div className="cx-hairrow">
            <Link2 size={18} strokeWidth={1.75} aria-hidden="true" />
            <span className="grow" style={{ minWidth: 0 }}>
              <span className="cx-strong" style={{ display: 'block' }}>{t('invite.linkTitle')}</span>
              <span className="cx-caption truncate" style={{ display: 'block' }}>{link ?? t('invite.linkHint')}</span>
            </span>
            <button className="cx-btn cx-btn--quiet" onClick={makeLink}>{copied ? t('invite.copied') : link ? t('invite.copyAgain') : t('invite.copyLink')}</button>
          </div>
        )}

        <label className="cx-search">
          <Search size={18} strokeWidth={1.75} aria-hidden="true" />
          <input type="search" placeholder={t('invite.searchPlaceholder')} value={q} onChange={(e) => setQ(e.target.value)} aria-label={t('invite.searchPlaceholder')} autoFocus />
        </label>
        <span className="cx-label">{q.trim() ? t('invite.results') : t('invite.peopleYouKnow')}</span>

        {people === null && <div className="stack" style={{ gap: 8 }}>{[0, 1, 2].map((i) => <div key={i} className="sk" style={{ height: 52, borderRadius: 12 }} />)}</div>}
        {people !== null && people.length === 0 && <p className="cx-caption" style={{ margin: 0 }}>{q.trim() ? t('invite.noMatch') : t('invite.nobodyYet')}</p>}
        <div className="cx-list" role="listbox" aria-multiselectable="true">
          {[...(people ?? [])].sort((a, b) => Number(a.already_member) - Number(b.already_member)).map((p) => {
            const disabled = p.already_member || p.invited;
            const on = picked.has(p.member_id);
            return (
              <button
                key={p.member_id}
                type="button"
                role="option"
                aria-selected={on}
                className={`cx-row cx-plain cx-pick${on ? ' is-on' : ''}`}
                disabled={disabled}
                onClick={() => toggle(p.member_id)}
              >
                {p.avatar ? <img className="cx-av cx-av--md" src={resolveMediaUrl(p.avatar) ?? ''} alt="" /> : <span className="cx-av cx-av--md">{initials(p.display_name)}</span>}
                <span className="grow" style={{ minWidth: 0 }}>
                  <span className="cx-strong truncate" style={{ display: 'block' }}>{p.display_name}</span>
                  <span className="cx-caption">{p.already_member ? t('invite.alreadyIn') : p.invited ? t('invite.alreadyInvited') : knownText(p)}</span>
                </span>
                {!disabled && <span className="cx-pick__box" aria-hidden="true">{on && <Check size={16} strokeWidth={2.5} />}</span>}
              </button>
            );
          })}
        </div>

        <div className="cx-sheetfoot">
          {error && <p className="cx-caption" style={{ margin: '0 0 8px', color: 'var(--danger)' }}>{error}</p>}
          <button className="cx-btn cx-btn--primary cx-btn--lg" style={{ width: '100%' }} disabled={picked.size === 0 || sending} onClick={send}>
            {picked.size === 0 ? t('invite.pickPeople') : t('invite.sendCount', { count: picked.size })}
          </button>
        </div>
      </div>
    </Sheet>
  );
}

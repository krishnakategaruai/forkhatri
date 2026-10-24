'use client';

/* Large events with tickets (Step 3): what a member sees on the activity page.
 *   TicketPicker   choose a ticket type, apply a discount code, see the price they will pay
 *   TicketQrCard   after booking: the QR ticket shown at the entrance
 *   OrganizerContact  the organizer's phone / email (when the organizer lets this member see it) and the Counsel link
 * The server decides every price, seat count and who may see contact details; nothing here recomputes them. */

import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';

import QrCode from '@/components/QrCode';
import { api, ApiError } from '@/lib/api';
import { formatInr } from '@/lib/format';

export type Tix = {
  tiered: boolean;
  types: { id: string; name: string; price_paise: number; left: number; sold_out: boolean }[];
  has_codes?: boolean; // the host made at least one usable discount code (event page D11: the code field shows only then)
  contact: { phone: string | null; email: string | null } | null;
  contact_after_booking: boolean;
  counsel_url: string | null;
};

export type TicketChoice = { typeId: string | null; code: string; amount: number | null };

type Quote = { list_price_paise: number; discount_paise: number; amount_paise: number };

export function TicketPicker({ eventId, tix, basePaise, onChange }: { eventId: string; tix: Tix; basePaise: number | null; onChange: (c: TicketChoice) => void }) {
  const { t, i18n } = useTranslation();
  const [typeId, setTypeId] = useState<string | null>(null);
  const [codeOpen, setCodeOpen] = useState(false);
  const [codeText, setCodeText] = useState('');
  const [applied, setApplied] = useState<{ code: string; quote: Quote } | null>(null);
  const [codeError, setCodeError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const onChangeRef = useRef(onChange);
  useEffect(() => { onChangeRef.current = onChange; });

  // Start on the first ticket type that still has seats.
  useEffect(() => {
    if (!tix.tiered) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setTypeId((cur) => (cur && tix.types.some((x) => x.id === cur && !x.sold_out) ? cur : tix.types.find((x) => !x.sold_out)?.id ?? null));
  }, [tix]);

  const selected = tix.types.find((x) => x.id === typeId) ?? null;
  const listPrice = tix.tiered ? selected?.price_paise ?? null : basePaise;
  const amount = applied ? applied.quote.amount_paise : listPrice;

  useEffect(() => { onChangeRef.current({ typeId: tix.tiered ? typeId : null, code: applied?.code ?? '', amount }); }, [typeId, applied, amount, tix.tiered]);

  const check = async (code: string, forType: string | null) => {
    setBusy(true); setCodeError(null);
    try {
      const q = await api<Quote>(`/occurrences/${eventId}/ticket/quote`, { body: { ticket_type_id: tix.tiered ? forType : null, code } });
      setApplied({ code, quote: q });
    } catch (e) {
      setApplied(null);
      setCodeError(e instanceof ApiError ? e.message : t('state.error'));
    } finally { setBusy(false); }
  };

  // Choosing another ticket type re-prices an applied code against it.
  const pick = (id: string) => {
    setTypeId(id);
    if (applied) void check(applied.code, id);
  };

  if (!tix.tiered && !tix.has_codes) return null;
  return (
    <section className="stack fade-in" style={{ gap: 10 }} aria-label={t('tix.title')}>
      {tix.tiered && (
        <>
          <span className="label">{t('tix.chooseType')}</span>
          <div className="stack" style={{ gap: 8 }} role="radiogroup" aria-label={t('tix.chooseType')}>
            {tix.types.map((x) => (
              <button
                key={x.id}
                type="button"
                role="radio"
                aria-checked={typeId === x.id}
                disabled={x.sold_out}
                onClick={() => pick(x.id)}
                className={`card tix-type${typeId === x.id ? ' tix-type--on' : ''}`}
              >
                <span className="grow" style={{ textAlign: 'left' }}>
                  <b>{x.name}</b>
                  <br />
                  <span className="caption">{x.sold_out ? t('tix.soldOut') : t('tix.left', { count: x.left })}</span>
                </span>
                <b>{formatInr(x.price_paise, i18n.language)}</b>
              </button>
            ))}
          </div>
        </>
      )}
      {!codeOpen && !applied ? (
        // Only when the host actually created codes; otherwise the line is noise on a court-sharing game.
        tix.has_codes ? <button type="button" className="link" style={{ alignSelf: 'flex-start', minHeight: 44 }} onClick={() => setCodeOpen(true)}>{t('tix.haveCode')}</button> : null
      ) : (
        <div className="stack" style={{ gap: 6 }}>
          <div className="row" style={{ gap: 8 }}>
            <label className="field grow" style={{ margin: 0 }}>
              <input
                className="field__input"
                value={applied ? applied.code : codeText}
                onChange={(e) => setCodeText(e.target.value.toUpperCase())}
                placeholder={t('tix.codePlaceholder')}
                aria-label={t('tix.codeLabel')}
                maxLength={24}
                autoCapitalize="characters"
                autoComplete="off"
                disabled={!!applied}
              />
            </label>
            {applied ? (
              <button type="button" className="btn btn--ghost" onClick={() => { setApplied(null); setCodeText(''); setCodeError(null); }}>{t('tix.remove')}</button>
            ) : (
              <button type="button" className="btn btn--secondary" disabled={busy || !codeText.trim() || (tix.tiered && !typeId)} onClick={() => check(codeText.trim(), typeId)}>{t('tix.apply')}</button>
            )}
          </div>
          {codeError && <span className="caption" role="alert" style={{ color: 'var(--danger, #c0392b)' }}>{codeError}</span>}
          {applied && <span className="caption" aria-live="polite">✓ {t('tix.codeApplied', { amount: formatInr(applied.quote.discount_paise, i18n.language) })}</span>}
        </div>
      )}
      {amount != null && (applied || tix.tiered) && <b aria-live="polite">{t('tix.youPay', { amount: formatInr(amount, i18n.language) })}</b>}
    </section>
  );
}

const groups = (code: string) => code.toUpperCase().replace(/(.{4})/g, '$1 ').trim();

export function TicketQrCard({ code, typeName, savedPaise, checkedIn }: { code: string; typeName: string | null; savedPaise: number; checkedIn: boolean }) {
  const { t, i18n } = useTranslation();
  return (
    <section className="card stack fade-in" style={{ gap: 8, alignItems: 'center', textAlign: 'center' }} aria-label={t('tix.yourTicket')}>
      <span className="label">{t('tix.yourTicket')}{typeName ? ` · ${typeName}` : ''}</span>
      {checkedIn ? (
        <b style={{ fontSize: '1.1rem' }}>✓ {t('tix.checkedIn')}</b>
      ) : (
        <>
          {/* The QR carries only the ticket code (no web address), so a stranger's phone camera learns nothing from it. */}
          <QrCode value={`FKT:${code}`} size={200} label={t('tix.yourTicket')} />
          <span className="caption">{t('tix.showAtEntry')}</span>
        </>
      )}
      <span className="caption">{t('tix.ticketCodeLabel')}</span>
      <b style={{ letterSpacing: '0.12em', fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace' }}>{groups(code)}</b>
      {savedPaise > 0 && <span className="caption">{t('tix.savedWithCode', { amount: formatInr(savedPaise, i18n.language) })}</span>}
    </section>
  );
}

export function OrganizerContact({ tix, organizerName }: { tix: Tix; organizerName: string }) {
  const { t } = useTranslation();
  const c = tix.contact;
  if (!c && !tix.contact_after_booking && !tix.counsel_url) return null;
  return (
    <section className="stack" style={{ gap: 8 }} aria-label={t('tix.contactTitle')}>
      {(c || tix.contact_after_booking) && <span className="label">{t('tix.contactTitle')}</span>}
      {c ? (
        <div className="row" style={{ gap: 8, flexWrap: 'wrap' }}>
          {c.phone && <a className="btn btn--secondary btn--sm" href={`tel:${c.phone.replace(/[^+\d]/g, '')}`}>{t('tix.call')} · {c.phone}</a>}
          {c.email && <a className="btn btn--secondary btn--sm" href={`mailto:${c.email}`}>{t('tix.email')} · {c.email}</a>}
        </div>
      ) : tix.contact_after_booking ? (
        <span className="caption">{t('tix.contactAfter')}</span>
      ) : null}
      {tix.counsel_url && (
        <a className="btn btn--primary btn--sm" style={{ alignSelf: 'flex-start' }} href={tix.counsel_url} target="_blank" rel="noopener noreferrer" aria-label={`${t('tix.counsel')} (${organizerName})`}>{t('tix.counsel')}</a>
      )}
    </section>
  );
}

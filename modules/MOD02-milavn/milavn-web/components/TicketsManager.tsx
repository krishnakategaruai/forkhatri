'use client';

/* Large events with tickets (Step 3): the organizer's side, on the Manage page.
 *   ticket types (own price and seats each), discount codes, contact details for attendees, and the ticket scanner.
 * Every rule (price lock once booked, seats never below what is taken, one code per name, who may write) is enforced by the
 * server; this screen shows the server's own message when it says no. Totals only: never who bought. */

import { useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Sheet } from '@/components/Sheet';
import { api, ApiError } from '@/lib/api';
import { formatInr } from '@/lib/format';

type TypeRow = { id: string; name: string; price_paise: number; quota: number; active: boolean; sold: number; held: number; checked_in: number; revenue_paise: number };
type CodeRow = { id: string; code: string; kind: 'percent' | 'fixed'; value: number; max_uses: number | null; expires_at: string | null; active: boolean; uses: number };
type Admin = { types: TypeRow[]; codes: CodeRow[]; contact: { phone: string | null; email: string | null; visibility: 'confirmed' | 'public'; offer_counsel: boolean } };

const rupeesToPaise = (v: string) => Math.round(Number(v) * 100);

export default function TicketsManager({ eventId, onChanged, say }: { eventId: string; onChanged: () => void; say: (m: string) => void }) {
  const { t, i18n } = useTranslation();
  const [admin, setAdmin] = useState<Admin | null>(null);
  const [scan, setScan] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [name, setName] = useState('');
  const [price, setPrice] = useState('');
  const [seats, setSeats] = useState('');
  const [codeText, setCodeText] = useState('');
  const [kind, setKind] = useState<'percent' | 'fixed'>('percent');
  const [value, setValue] = useState('');
  const [limit, setLimit] = useState('');
  const [expires, setExpires] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [visibility, setVisibility] = useState<'confirmed' | 'public'>('confirmed');
  const [counsel, setCounsel] = useState(false);

  const load = useCallback(async () => {
    try {
      const a = await api<Admin>(`/occurrences/${eventId}/ticket-admin`);
      setAdmin(a);
      setPhone(a.contact.phone ?? ''); setEmail(a.contact.email ?? ''); setVisibility(a.contact.visibility); setCounsel(a.contact.offer_counsel);
    } catch { setAdmin(null); }
  }, [eventId]);
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { void load(); }, [load]);

  const run = async (fn: () => Promise<unknown>, ok?: string) => {
    try { await fn(); if (ok) say(ok); await load(); onChanged(); }
    catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  const resetTypeForm = () => { setEditId(null); setName(''); setPrice(''); setSeats(''); };
  const typeOk = name.trim().length > 0 && rupeesToPaise(price) >= 100 && rupeesToPaise(price) <= 10_000_000 && Number(seats) >= 1 && Number.isInteger(Number(seats));
  const saveType = () => run(
    () => api(editId ? `/occurrences/${eventId}/ticket-types/${editId}` : `/occurrences/${eventId}/ticket-types`, {
      method: editId ? 'PATCH' : 'POST', body: { name: name.trim(), price_paise: rupeesToPaise(price), quota: Number(seats) },
    }).then(resetTypeForm),
    t('tix.manage.saved'),
  );
  const editType = (x: TypeRow) => { setEditId(x.id); setName(x.name); setPrice(String(x.price_paise / 100)); setSeats(String(x.quota)); };
  const setActive = (x: TypeRow, active: boolean) => run(() => api(`/occurrences/${eventId}/ticket-types/${x.id}`, { method: 'PATCH', body: { name: x.name, price_paise: x.price_paise, quota: x.quota, active } }));
  const removeType = (x: TypeRow) => run(() => api(`/occurrences/${eventId}/ticket-types/${x.id}`, { method: 'DELETE' }));

  const codeOk = /^[A-Za-z0-9_-]{3,24}$/.test(codeText) && (kind === 'percent' ? Number(value) >= 1 && Number(value) <= 90 : rupeesToPaise(value) >= 100);
  const addCode = () => run(
    () => api(`/occurrences/${eventId}/discount-codes`, {
      body: {
        code: codeText.trim(), kind, value: kind === 'percent' ? Math.round(Number(value)) : rupeesToPaise(value),
        max_uses: limit ? Number(limit) : null, expires_at: expires ? new Date(`${expires}T23:59:59`).toISOString() : null,
      },
    }).then(() => { setCodeText(''); setValue(''); setLimit(''); setExpires(''); }),
    t('tix.manage.saved'),
  );
  const toggleCode = (c: CodeRow) => run(() => api(`/occurrences/${eventId}/discount-codes/${c.id}`, { method: 'PATCH', body: { active: !c.active } }));
  const saveContact = () => run(() => api(`/occurrences/${eventId}/contact`, { method: 'PUT', body: { phone: phone.trim() || null, email: email.trim() || null, visibility, offer_counsel: counsel } }), t('tix.manage.saved'));

  if (!admin) return null;
  const now = Date.now();

  return (
    <>
      <section className="card stack" style={{ gap: 12 }} aria-label={t('tix.manage.title')}>
        <div className="row row--between">
          <span className="label">{t('tix.manage.title')}</span>
          <button className="btn btn--secondary btn--sm" onClick={() => setScan(true)}>{t('tix.scan.open')}</button>
        </div>

        <div className="stack" style={{ gap: 8 }}>
          <b>{t('tix.manage.types')}</b>
          <span className="caption">{t('tix.manage.typesHint')}</span>
          {admin.types.length === 0 && <span className="caption">{t('tix.manage.noTypes')}</span>}
          {admin.types.map((x) => (
            <div key={x.id} className="card" style={{ padding: 10, gap: 4, opacity: x.active ? 1 : 0.7 }}>
              <div className="row row--between">
                <b>{x.name}{!x.active && <span className="pill pill--neutral" style={{ marginLeft: 6 }}>{t('tix.manage.off')}</span>}</b>
                <b>{formatInr(x.price_paise, i18n.language)}</b>
              </div>
              <span className="caption">{t('tix.manage.sold', { sold: x.sold, quota: x.quota })}{x.held > 0 ? ` · ${t('pay.organizer.holds', { count: x.held })}` : ''} · {t('tix.manage.checkedInCount', { count: x.checked_in })}</span>
              <div className="row" style={{ gap: 6, flexWrap: 'wrap' }}>
                <button className="btn btn--ghost btn--sm" onClick={() => editType(x)}>{t('create.edit')}</button>
                <button className="btn btn--ghost btn--sm" onClick={() => setActive(x, !x.active)}>{x.active ? t('tix.manage.turnOff') : t('tix.manage.turnOn')}</button>
                <button className="btn btn--ghost btn--sm" onClick={() => removeType(x)}>{t('tix.manage.delete')}</button>
              </div>
            </div>
          ))}
          <div className="paybox">
            <b>{editId ? t('create.edit') : t('tix.manage.addType')}</b>
            <label className="field"><span className="field__label">{t('tix.manage.name')}</span>
              <input className="field__input" value={name} maxLength={60} placeholder={t('tix.manage.namePh')} onChange={(e) => setName(e.target.value)} /></label>
            <div className="grid-2">
              <label className="field"><span className="field__label">{t('tix.manage.price')}</span>
                <input className="field__input" type="number" inputMode="decimal" min={1} step="1" value={price} onChange={(e) => setPrice(e.target.value)} /></label>
              <label className="field"><span className="field__label">{t('tix.manage.seats')}</span>
                <input className="field__input" type="number" inputMode="numeric" min={1} step="1" value={seats} onChange={(e) => setSeats(e.target.value)} /></label>
            </div>
            {editId && admin.types.find((x) => x.id === editId && x.sold + x.held > 0) && <span className="caption">{t('tix.manage.priceLocked')}</span>}
            <div className="row" style={{ gap: 8 }}>
              <button className="btn btn--primary grow" disabled={!typeOk} onClick={saveType}>{t('tix.manage.save')}</button>
              {editId && <button className="btn btn--ghost" onClick={resetTypeForm}>{t('create.keep')}</button>}
            </div>
          </div>
        </div>

        <div className="stack" style={{ gap: 8 }}>
          <b>{t('tix.manage.codes')}</b>
          <span className="caption">{t('tix.manage.codesHint')}</span>
          {admin.codes.map((c) => {
            const expired = !!c.expires_at && new Date(c.expires_at).getTime() <= now;
            return (
              <div key={c.id} className="card" style={{ padding: 10, gap: 4, opacity: c.active && !expired ? 1 : 0.7 }}>
                <div className="row row--between">
                  <b style={{ letterSpacing: '0.06em' }}>{c.code}</b>
                  <b>{c.kind === 'percent' ? `${c.value}%` : formatInr(c.value, i18n.language)}</b>
                </div>
                <span className="caption">
                  {c.max_uses ? t('tix.manage.usedOf', { count: c.uses, max: c.max_uses }) : t('tix.manage.used', { count: c.uses })}
                  {c.expires_at ? ` · ${expired ? t('tix.manage.expired') : new Date(c.expires_at).toLocaleDateString(i18n.language)}` : ''}
                  {!c.active ? ` · ${t('tix.manage.off')}` : ''}
                </span>
                <button className="btn btn--ghost btn--sm" style={{ alignSelf: 'flex-start' }} onClick={() => toggleCode(c)}>{c.active ? t('tix.manage.turnOff') : t('tix.manage.turnOn')}</button>
              </div>
            );
          })}
          <div className="paybox">
            <b>{t('tix.manage.addCode')}</b>
            <label className="field"><span className="field__label">{t('tix.manage.code')}</span>
              <input className="field__input" value={codeText} maxLength={24} autoCapitalize="characters" placeholder={t('tix.manage.codePh')} onChange={(e) => setCodeText(e.target.value.toUpperCase())} /></label>
            <div className="chips" role="radiogroup" aria-label={t('tix.manage.kind')}>
              <button type="button" role="radio" aria-checked={kind === 'percent'} className="chip chip--sm" aria-pressed={kind === 'percent'} onClick={() => setKind('percent')}>{t('tix.manage.percent')}</button>
              <button type="button" role="radio" aria-checked={kind === 'fixed'} className="chip chip--sm" aria-pressed={kind === 'fixed'} onClick={() => setKind('fixed')}>{t('tix.manage.fixed')}</button>
            </div>
            <div className="grid-2">
              <label className="field"><span className="field__label">{t('tix.manage.value')}</span>
                <input className="field__input" type="number" inputMode="decimal" min={1} step="1" value={value} onChange={(e) => setValue(e.target.value)} /></label>
              <label className="field"><span className="field__label">{t('tix.manage.limit')}</span>
                <input className="field__input" type="number" inputMode="numeric" min={1} step="1" value={limit} onChange={(e) => setLimit(e.target.value)} /></label>
            </div>
            <label className="field"><span className="field__label">{t('tix.manage.expires')}</span>
              <input className="field__input" type="date" value={expires} onChange={(e) => setExpires(e.target.value)} /></label>
            <button className="btn btn--primary" disabled={!codeOk} onClick={addCode}>{t('tix.manage.addCode')}</button>
          </div>
        </div>

        <div className="stack" style={{ gap: 8 }}>
          <b>{t('tix.manage.contact')}</b>
          <div className="grid-2">
            <label className="field"><span className="field__label">{t('tix.manage.phone')}</span>
              <input className="field__input" type="tel" inputMode="tel" maxLength={20} value={phone} onChange={(e) => setPhone(e.target.value)} /></label>
            <label className="field"><span className="field__label">{t('tix.manage.emailField')}</span>
              <input className="field__input" type="email" inputMode="email" maxLength={120} value={email} onChange={(e) => setEmail(e.target.value)} /></label>
          </div>
          <span className="field__label">{t('tix.manage.showTo')}</span>
          <div className="chips" role="radiogroup" aria-label={t('tix.manage.showTo')}>
            <button type="button" role="radio" aria-checked={visibility === 'confirmed'} className="chip chip--sm" aria-pressed={visibility === 'confirmed'} onClick={() => setVisibility('confirmed')}>{t('tix.manage.showConfirmed')}</button>
            <button type="button" role="radio" aria-checked={visibility === 'public'} className="chip chip--sm" aria-pressed={visibility === 'public'} onClick={() => setVisibility('public')}>{t('tix.manage.showAll')}</button>
          </div>
          <label className="row" style={{ gap: 8 }}>
            <input type="checkbox" checked={counsel} onChange={(e) => setCounsel(e.target.checked)} style={{ width: 22, height: 22 }} />
            <span>{t('tix.manage.counselOffer')}</span>
          </label>
          <button className="btn btn--secondary" onClick={saveContact}>{t('tix.manage.save')}</button>
        </div>
      </section>
      <Scanner eventId={eventId} open={scan} onClose={() => setScan(false)} onDone={() => { void load(); onChanged(); }} />
    </>
  );
}

/* Scan an attendee's ticket QR with the camera where the browser can read QR codes, or type the code printed under it. */
type Detector = { detect: (src: HTMLVideoElement) => Promise<{ rawValue: string }[]> };

function Scanner({ eventId, open, onClose, onDone }: { eventId: string; open: boolean; onClose: () => void; onDone: () => void }) {
  const { t } = useTranslation();
  const [code, setCode] = useState('');
  const [result, setResult] = useState<{ ok: boolean; text: string } | null>(null);
  const [cam, setCam] = useState(false);
  const [noCam, setNoCam] = useState(false);
  const video = useRef<HTMLVideoElement | null>(null);
  const busy = useRef(false);

  const submit = useCallback(async (raw: string) => {
    if (busy.current || !raw.trim()) return;
    busy.current = true;
    try {
      const r = await api<{ result: 'checked_in' | 'already'; name: string; type_name: string | null }>(`/occurrences/${eventId}/checkin/ticket`, { body: { code: raw } });
      const text = r.result === 'already' ? t('tix.scan.already', { name: r.name }) : r.type_name ? t('tix.scan.ok', { name: r.name, type: r.type_name }) : t('tix.scan.okNoType', { name: r.name });
      setResult({ ok: r.result === 'checked_in', text }); setCode('');
      onDone();
    } catch (e) {
      setResult({ ok: false, text: e instanceof ApiError ? e.message : t('state.error') });
    } finally { setTimeout(() => { busy.current = false; }, 1200); }
  }, [eventId, onDone, t]);

  useEffect(() => {
    if (!open || !cam) return;
    const Ctor = (window as unknown as { BarcodeDetector?: new (o: { formats: string[] }) => Detector }).BarcodeDetector;
    if (!Ctor || !navigator.mediaDevices?.getUserMedia) { setNoCam(true); setCam(false); return; }
    const detector = new Ctor({ formats: ['qr_code'] });
    let stream: MediaStream | null = null; let stop = false;
    navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } }).then((s) => {
      if (stop) { s.getTracks().forEach((x) => x.stop()); return; }
      stream = s;
      const v = video.current; if (!v) return;
      v.srcObject = s; void v.play();
      const tick = async () => {
        if (stop) return;
        try { const found = await detector.detect(v); if (found[0]?.rawValue) await submit(found[0].rawValue); } catch { /* keep looking */ }
        setTimeout(tick, 400);
      };
      void tick();
    }).catch(() => { setNoCam(true); setCam(false); });
    return () => { stop = true; stream?.getTracks().forEach((x) => x.stop()); };
  }, [open, cam, submit]);

  const close = () => { setCam(false); setResult(null); setCode(''); onClose(); };
  return (
    <Sheet open={open} onClose={close} label={t('tix.scan.title')}>
      <div className="stack" style={{ gap: 10, padding: '4px 4px 12px' }}>
        <h2 className="h2" style={{ margin: 0 }}>{t('tix.scan.title')}</h2>
        <span className="caption">{t('tix.scan.hint')}</span>
        {result && <div className="card" role="status" aria-live="polite" style={{ padding: 12, borderColor: result.ok ? 'var(--accent-primary)' : undefined }}><b>{result.ok ? '✓ ' : ''}{result.text}</b></div>}
        {cam && <video ref={video} playsInline muted style={{ width: '100%', borderRadius: 12, background: '#000', maxHeight: 260, objectFit: 'cover' }} />}
        <div className="row" style={{ gap: 8 }}>
          <button className="btn btn--secondary btn--sm" onClick={() => { setNoCam(false); setCam((v) => !v); }}>{cam ? t('tix.scan.stop') : t('tix.scan.camera')}</button>
        </div>
        {noCam && <span className="caption">{t('tix.scan.noCamera')}</span>}
        <form className="stack" style={{ gap: 8 }} onSubmit={(e) => { e.preventDefault(); void submit(code); }}>
          <label className="field"><span className="field__label">{t('tix.scan.manual')}</span>
            <input className="field__input" value={code} onChange={(e) => setCode(e.target.value)} autoCapitalize="characters" autoComplete="off" autoCorrect="off" spellCheck={false} inputMode="text" maxLength={40} /></label>
          <button className="btn btn--primary" type="submit" disabled={!code.trim()}>{t('tix.scan.submit')}</button>
        </form>
      </div>
    </Sheet>
  );
}

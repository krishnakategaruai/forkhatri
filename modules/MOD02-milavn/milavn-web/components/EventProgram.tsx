'use client';

/* Event programme (Phase 2, Step 5): what a member sees on the event page, and the organizer's editor on Manage.
 *   EventProgram         agenda by day with speakers, speaker cards, expo stalls, tournament teams, recording / notes
 *   EventProgramManager  the organizer adds and removes speakers, sessions and stalls, and the recording / notes links
 * The server decides everything (who may write, who sees team members and the recording, sessions inside the event,
 * team sizes); these screens show its own message when it says no. */

import Link from 'next/link';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { api, ApiError, resolveMediaUrl } from '@/lib/api';
import { daySpan, dayNumber, type Provider } from '@/lib/event-formats';

type Speaker = { id: string; name: string; bio: string | null; member_id: string | null; avatar: string | null };
type Session = { id: string; starts_at: string; ends_at: string | null; title: string; details: string | null; speaker_ids: string[] };
type Stall = { id: string; stall_number: string | null; name: string; description: string | null };
type Team = { id: string; name: string; size: number; full: boolean; captain_member_id: string | null; members: { member_id: string; display_name: string }[] | null };
export type Program = {
  event_format: string | null;
  speakers: Speaker[]; sessions: Session[]; stalls: Stall[];
  teams: { team_size_max: number; my_team_id: string | null; list: Team[] } | null;
  followup: { recording_url: string | null; recording_provider: Provider | null; notes_url: string | null } | null;
};

const LOCALE: Record<string, string> = { en: 'en-IN', hi: 'hi-IN', te: 'te-IN' };
const IST = 'Asia/Kolkata';
const time = (iso: string, lang: string) => new Intl.DateTimeFormat(LOCALE[lang] ?? 'en-IN', { timeZone: IST, hour: 'numeric', minute: '2-digit' }).format(new Date(iso));
const dayLabel = (iso: string, lang: string) => new Intl.DateTimeFormat(LOCALE[lang] ?? 'en-IN', { timeZone: IST, weekday: 'short', day: 'numeric', month: 'short' }).format(new Date(iso));

export function useProgram(eventId: string | undefined, refreshKey: unknown) {
  const [program, setProgram] = useState<Program | null>(null);
  const load = useCallback(async () => {
    if (!eventId) return;
    try { setProgram(await api<Program>(`/occurrences/${eventId}/program`)); } catch { setProgram(null); }
  }, [eventId]);
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { void load(); }, [load, refreshKey]);
  return { program, reload: load };
}

/* ------------------------------------------------------------------------------------------------------------------ */

export default function EventProgram({ eventId, start, end, viewerId, confirmed, isOrganizer, ended, say, refreshKey }: {
  eventId: string; start: string; end: string | null; viewerId: string | null; confirmed: boolean; isOrganizer: boolean; ended: boolean;
  say: (m: string) => void; refreshKey: unknown;
}) {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const { program, reload } = useProgram(eventId, refreshKey);
  const [allStalls, setAllStalls] = useState(false);
  const [stallQuery, setStallQuery] = useState('');
  const [teamName, setTeamName] = useState('');
  const [busy, setBusy] = useState(false);

  const days = daySpan(start, end);
  const byDay = useMemo(() => {
    const groups = new Map<number, Session[]>();
    for (const s of program?.sessions ?? []) {
      const n = dayNumber(start, s.starts_at);
      groups.set(n, [...(groups.get(n) ?? []), s]);
    }
    return [...groups.entries()].sort((a, b) => a[0] - b[0]);
  }, [program, start]);

  if (!program) return null;
  const speakerById = new Map(program.speakers.map((s) => [s.id, s]));
  const teams = program.teams;

  const run = async (fn: () => Promise<unknown>, ok?: string) => {
    if (busy) return;
    setBusy(true);
    try { await fn(); if (ok) say(ok); await reload(); }
    catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
    finally { setBusy(false); }
  };

  const q = stallQuery.trim().toLowerCase();
  const stalls = program.stalls.filter((s) => !q || `${s.stall_number ?? ''} ${s.name} ${s.description ?? ''}`.toLowerCase().includes(q));
  const shownStalls = allStalls || q ? stalls : stalls.slice(0, 8);

  return (
    <>
      {program.followup && (confirmed || isOrganizer) && (
        <section className="card stack fade-in" style={{ gap: 8 }} aria-label={t('evt.followup.title')}>
          <span className="label">{t('evt.followup.title')}</span>
          <div className="row" style={{ gap: 8, flexWrap: 'wrap' }}>
            {program.followup.recording_url && (
              <a className="btn btn--primary btn--sm" href={program.followup.recording_url} target="_blank" rel="noopener noreferrer">
                {program.followup.recording_provider && program.followup.recording_provider !== 'other'
                  ? t('evt.followup.watchOn', { provider: t(`evt.provider.${program.followup.recording_provider}`) })
                  : t('evt.followup.watch')}
              </a>
            )}
            {program.followup.notes_url && <a className="btn btn--secondary btn--sm" href={program.followup.notes_url} target="_blank" rel="noopener noreferrer">{t('evt.followup.notes')}</a>}
          </div>
        </section>
      )}

      {program.sessions.length > 0 && (
        <section className="stack" style={{ gap: 10 }} aria-label={t('evt.agenda.title')}>
          <span className="label">{t('evt.agenda.title')}</span>
          {byDay.map(([n, list]) => (
            <div key={n} className="stack" style={{ gap: 8 }}>
              {days > 1 && <b>{t('evt.agenda.day', { n })} · {dayLabel(list[0].starts_at, lang)}</b>}
              <ol className="agenda">
                {list.map((s) => (
                  <li key={s.id} className="agenda__item">
                    <span className="agenda__time">{time(s.starts_at, lang)}{s.ends_at ? `–${time(s.ends_at, lang)}` : ''}</span>
                    <span className="stack" style={{ gap: 2, minWidth: 0 }}>
                      <b>{s.title}</b>
                      {s.speaker_ids.length > 0 && (
                        <span className="caption">
                          {s.speaker_ids.map((id, i) => {
                            const sp = speakerById.get(id);
                            if (!sp) return null;
                            return <span key={id}>{i > 0 ? ', ' : ''}{sp.member_id ? <Link className="link" href={`/p/${sp.member_id}`}>{sp.name}</Link> : sp.name}</span>;
                          })}
                        </span>
                      )}
                      {s.details && <span className="caption" style={{ whiteSpace: 'pre-line' }}>{s.details}</span>}
                    </span>
                  </li>
                ))}
              </ol>
            </div>
          ))}
        </section>
      )}

      {program.speakers.length > 0 && (
        <section className="stack" style={{ gap: 8 }} aria-label={t('evt.speakers.title')}>
          <span className="label">{t('evt.speakers.title')}</span>
          <div className="speakers">
            {program.speakers.map((s) => (
              <div key={s.id} className="card speaker">
                {s.avatar ? <img className="avatar avatar--lg" src={resolveMediaUrl(s.avatar) ?? ''} alt="" /> : <span className="avatar avatar--lg speaker__initial" aria-hidden="true">{s.name.slice(0, 1).toUpperCase()}</span>}
                <span className="stack" style={{ gap: 2, minWidth: 0 }}>
                  <b>{s.name}</b>
                  {s.bio && <span className="caption">{s.bio}</span>}
                  {s.member_id && <Link className="link caption" href={`/p/${s.member_id}`}>{t('evt.speakers.profile')} ›</Link>}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {program.stalls.length > 0 && (
        <section className="stack" style={{ gap: 8 }} aria-label={t('evt.stalls.title')}>
          <div className="row row--between"><span className="label">{t('evt.stalls.title')}</span><span className="caption">{t('evt.stalls.count', { count: program.stalls.length })}</span></div>
          {program.stalls.length > 8 && (
            <label className="field"><input className="field__input" type="search" value={stallQuery} onChange={(e) => setStallQuery(e.target.value)} placeholder={t('evt.stalls.search')} aria-label={t('evt.stalls.search')} /></label>
          )}
          <div className="list">
            {shownStalls.map((s) => (
              <div key={s.id} className="lrow" style={{ minHeight: 52, alignItems: 'flex-start' }}>
                {s.stall_number && <span className="pill pill--accent" aria-label={t('evt.stalls.number', { n: s.stall_number })}>{s.stall_number}</span>}
                <span className="stack grow" style={{ gap: 2, minWidth: 0 }}><b>{s.name}</b>{s.description && <span className="caption">{s.description}</span>}</span>
              </div>
            ))}
            {q && stalls.length === 0 && <span className="caption">{t('evt.stalls.none')}</span>}
          </div>
          {!allStalls && !q && stalls.length > 8 && <button className="link" style={{ alignSelf: 'flex-start' }} onClick={() => setAllStalls(true)}>{t('evt.stalls.all', { count: stalls.length })}</button>}
        </section>
      )}

      {teams && (
        <section className="card stack" style={{ gap: 10 }} aria-label={t('evt.teams.title')}>
          <div className="row row--between"><span className="label">{t('evt.teams.title')}</span><span className="caption">{t('evt.teams.upTo', { count: teams.team_size_max })}</span></div>
          {teams.list.length === 0 && <span className="caption">{t('evt.teams.none')}</span>}
          {teams.list.map((tm) => {
            const mine = teams.my_team_id === tm.id;
            const captain = tm.captain_member_id === viewerId;
            return (
              <div key={tm.id} className="card" style={{ padding: 10, gap: 6, borderColor: mine ? 'var(--accent-primary)' : undefined }}>
                <div className="row row--between" style={{ gap: 8 }}>
                  <b>{tm.name}{mine && <span className="pill pill--trust" style={{ marginLeft: 6 }}>{t('evt.teams.yours')}</span>}</b>
                  <span className="caption">{t('evt.teams.size', { size: tm.size, max: teams.team_size_max })}</span>
                </div>
                {tm.members && (
                  <div className="chips">
                    {tm.members.map((m) => (
                      <span key={m.member_id} className="pill pill--neutral">
                        {m.display_name}{m.member_id === tm.captain_member_id ? ` · ${t('evt.teams.captain')}` : ''}
                        {!ended && (captain || isOrganizer) && m.member_id !== viewerId && (
                          <button type="button" className="link" aria-label={t('evt.teams.remove', { name: m.display_name })} onClick={() => run(() => api(`/occurrences/${eventId}/teams/${tm.id}/members/${m.member_id}`, { method: 'DELETE' }))}>×</button>
                        )}
                      </span>
                    ))}
                  </div>
                )}
                {!ended && confirmed && !teams.my_team_id && !tm.full && (
                  <button className="btn btn--secondary btn--sm" style={{ alignSelf: 'flex-start' }} disabled={busy} onClick={() => run(() => api(`/occurrences/${eventId}/teams/${tm.id}/join`, { body: {} }), t('evt.teams.joined', { name: tm.name }))}>{t('evt.teams.join')}</button>
                )}
                {!ended && mine && viewerId && (
                  <button className="link" style={{ alignSelf: 'flex-start' }} disabled={busy} onClick={() => run(() => api(`/occurrences/${eventId}/teams/${tm.id}/members/${viewerId}`, { method: 'DELETE' }), t('evt.teams.left'))}>{t('evt.teams.leave')}</button>
                )}
              </div>
            );
          })}
          {!ended && confirmed && !teams.my_team_id && (
            <form className="row" style={{ gap: 8 }} onSubmit={(e) => { e.preventDefault(); void run(() => api(`/occurrences/${eventId}/teams`, { body: { name: teamName.trim() } }).then(() => setTeamName('')), t('evt.teams.registered')); }}>
              <label className="field grow" style={{ margin: 0 }}><input className="field__input" value={teamName} maxLength={60} onChange={(e) => setTeamName(e.target.value)} placeholder={t('evt.teams.namePh')} aria-label={t('evt.teams.name')} /></label>
              <button className="btn btn--primary btn--sm" type="submit" disabled={busy || teamName.trim().length < 2}>{t('evt.teams.register')}</button>
            </form>
          )}
          {!ended && !confirmed && !isOrganizer && <span className="caption">{t('evt.teams.bookFirst')}</span>}
        </section>
      )}
    </>
  );
}

/* ------------------------------------------------------------------------------------------------------------------ */

type Person = { member_id: string; display_name: string; avatar: string | null };

export function EventProgramManager({ eventId, start, end, say }: { eventId: string; start: string; end: string | null; say: (m: string) => void }) {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const { program, reload } = useProgram(eventId, null);
  // speaker form
  const [spName, setSpName] = useState('');
  const [spBio, setSpBio] = useState('');
  const [spMember, setSpMember] = useState<Person | null>(null);
  const [spQuery, setSpQuery] = useState('');
  const [people, setPeople] = useState<Person[]>([]);
  // session form
  const days = daySpan(start, end);
  const [sDay, setSDay] = useState(1);
  const [sFrom, setSFrom] = useState('');
  const [sTo, setSTo] = useState('');
  const [sTitle, setSTitle] = useState('');
  const [sDetails, setSDetails] = useState('');
  const [sSpeakers, setSSpeakers] = useState<string[]>([]);
  // stall form
  const [stNo, setStNo] = useState('');
  const [stName, setStName] = useState('');
  const [stDesc, setStDesc] = useState('');
  // follow-up
  const [rec, setRec] = useState('');
  const [notes, setNotes] = useState('');
  const [openedAt] = useState(() => Date.now()); // judged once per page view
  const started = Date.parse(start) <= openedAt;

  useEffect(() => {
    if (!program?.followup) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setRec(program.followup.recording_url ?? ''); setNotes(program.followup.notes_url ?? '');
  }, [program?.followup]);

  useEffect(() => {
    if (spQuery.trim().length < 2) { setPeople([]); return; }
    const id = setTimeout(() => { api<Person[]>(`/people/search?q=${encodeURIComponent(spQuery.trim())}`).then(setPeople).catch(() => setPeople([])); }, 250);
    return () => clearTimeout(id);
  }, [spQuery]);

  const run = async (fn: () => Promise<unknown>, ok?: string) => {
    try { await fn(); if (ok) say(ok); await reload(); }
    catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  // A session's time is the event's own day (India time) plus the clock time the organizer typed.
  const at = (dayIndex: number, hhmm: string) => {
    const d = new Date(Date.parse(start) + (dayIndex - 1) * 86_400_000);
    const ymd = new Intl.DateTimeFormat('en-CA', { timeZone: IST, year: 'numeric', month: '2-digit', day: '2-digit' }).format(d);
    return `${ymd}T${hhmm}:00+05:30`;
  };
  const sOk = sTitle.trim().length > 0 && /^\d{2}:\d{2}$/.test(sFrom) && (!sTo || sTo > sFrom);

  if (!program) return null;
  const speakerById = new Map(program.speakers.map((s) => [s.id, s]));
  const isExpo = program.event_format === 'expo' || program.stalls.length > 0;

  return (
    <section className="card stack" style={{ gap: 14 }} aria-label={t('evt.manage.title')}>
      <span className="label">{t('evt.manage.title')}</span>
      <span className="caption">{t('evt.manage.hint')}</span>

      {/* Speakers */}
      <div className="stack" style={{ gap: 8 }}>
        <b>{t('evt.speakers.title')}</b>
        {program.speakers.map((s) => (
          <div key={s.id} className="row row--between" style={{ gap: 8 }}>
            <span className="grow" style={{ minWidth: 0 }}>{s.name}{s.member_id && <span className="pill pill--trust" style={{ marginLeft: 6 }}>{t('evt.speakers.linked')}</span>}</span>
            <button className="btn btn--ghost btn--sm" onClick={() => run(() => api(`/occurrences/${eventId}/speakers/${s.id}`, { method: 'DELETE' }))}>{t('evt.manage.remove')}</button>
          </div>
        ))}
        <div className="paybox">
          <label className="field"><span className="field__label">{t('evt.speakers.name')}</span>
            <input className="field__input" value={spName} maxLength={80} onChange={(e) => setSpName(e.target.value)} /></label>
          <label className="field"><span className="field__label">{t('evt.speakers.bio')}</span>
            <textarea className="field__input" rows={2} maxLength={300} value={spBio} onChange={(e) => setSpBio(e.target.value)} placeholder={t('evt.speakers.bioPh')} /></label>
          {spMember ? (
            <div className="row row--between"><span className="caption">{t('evt.speakers.linkedTo', { name: spMember.display_name })}</span><button className="link" onClick={() => setSpMember(null)}>{t('evt.manage.remove')}</button></div>
          ) : (
            <label className="field"><span className="field__label">{t('evt.speakers.linkMember')}</span>
              <input className="field__input" type="search" value={spQuery} onChange={(e) => setSpQuery(e.target.value)} placeholder={t('evt.speakers.searchPh')} /></label>
          )}
          {!spMember && people.length > 0 && (
            <div className="list">
              {people.slice(0, 5).map((p) => (
                <button key={p.member_id} type="button" className="lrow lrow--tap" style={{ width: '100%', textAlign: 'left', minHeight: 48 }} onClick={() => { setSpMember(p); setSpQuery(''); setPeople([]); if (!spName.trim()) setSpName(p.display_name); }}>
                  {p.avatar ? <img className="avatar" src={resolveMediaUrl(p.avatar) ?? ''} alt="" /> : <span className="avatar" />}
                  <span className="grow">{p.display_name}</span>
                </button>
              ))}
            </div>
          )}
          <button className="btn btn--primary" disabled={!spName.trim()} onClick={() => run(() => api(`/occurrences/${eventId}/speakers`, { body: { name: spName.trim(), bio: spBio.trim() || null, member_id: spMember?.member_id ?? null } }).then(() => { setSpName(''); setSpBio(''); setSpMember(null); }), t('tix.manage.saved'))}>{t('evt.speakers.add')}</button>
        </div>
      </div>

      {/* Agenda */}
      <div className="stack" style={{ gap: 8 }}>
        <b>{t('evt.agenda.title')}</b>
        {program.sessions.map((s) => (
          <div key={s.id} className="row row--between" style={{ gap: 8 }}>
            <span className="grow" style={{ minWidth: 0 }}>
              <span className="caption">{days > 1 ? `${t('evt.agenda.day', { n: dayNumber(start, s.starts_at) })} · ` : ''}{time(s.starts_at, lang)}{s.ends_at ? `–${time(s.ends_at, lang)}` : ''}</span><br />
              <b>{s.title}</b>{s.speaker_ids.length > 0 && <span className="caption"> · {s.speaker_ids.map((id) => speakerById.get(id)?.name).filter(Boolean).join(', ')}</span>}
            </span>
            <button className="btn btn--ghost btn--sm" onClick={() => run(() => api(`/occurrences/${eventId}/sessions/${s.id}`, { method: 'DELETE' }))}>{t('evt.manage.remove')}</button>
          </div>
        ))}
        <div className="paybox">
          {days > 1 && (
            <label className="field"><span className="field__label">{t('evt.agenda.whichDay')}</span>
              <select className="field__input" value={sDay} onChange={(e) => setSDay(Number(e.target.value))}>
                {Array.from({ length: days }, (_, i) => <option key={i + 1} value={i + 1}>{t('evt.agenda.day', { n: i + 1 })} · {dayLabel(new Date(Date.parse(start) + i * 86_400_000).toISOString(), lang)}</option>)}
              </select></label>
          )}
          <div className="grid-2">
            <label className="field"><span className="field__label">{t('evt.agenda.from')}</span><input className="field__input" type="time" value={sFrom} onChange={(e) => setSFrom(e.target.value)} /></label>
            <label className="field"><span className="field__label">{t('evt.agenda.to')}</span><input className="field__input" type="time" value={sTo} onChange={(e) => setSTo(e.target.value)} /></label>
          </div>
          <label className="field"><span className="field__label">{t('evt.agenda.sessionTitle')}</span>
            <input className="field__input" value={sTitle} maxLength={140} onChange={(e) => setSTitle(e.target.value)} /></label>
          <label className="field"><span className="field__label">{t('evt.agenda.details')}</span>
            <input className="field__input" value={sDetails} maxLength={400} onChange={(e) => setSDetails(e.target.value)} /></label>
          {program.speakers.length > 0 && (
            <>
              <span className="field__label">{t('evt.agenda.speakers')}</span>
              <div className="chips">
                {program.speakers.map((s) => <button key={s.id} type="button" className="chip chip--sm" aria-pressed={sSpeakers.includes(s.id)} onClick={() => setSSpeakers((cur) => (cur.includes(s.id) ? cur.filter((x) => x !== s.id) : [...cur, s.id]))}>{s.name}</button>)}
              </div>
            </>
          )}
          <button className="btn btn--primary" disabled={!sOk} onClick={() => run(() => api(`/occurrences/${eventId}/sessions`, {
            body: { starts_at: at(sDay, sFrom), ends_at: sTo ? at(sDay, sTo) : null, title: sTitle.trim(), details: sDetails.trim() || null, speaker_ids: sSpeakers },
          }).then(() => { setSTitle(''); setSDetails(''); setSFrom(sTo || ''); setSTo(''); setSSpeakers([]); }), t('tix.manage.saved'))}>{t('evt.agenda.add')}</button>
        </div>
      </div>

      {/* Expo stalls */}
      {isExpo && (
        <div className="stack" style={{ gap: 8 }}>
          <b>{t('evt.stalls.title')}</b>
          {program.stalls.map((s) => (
            <div key={s.id} className="row row--between" style={{ gap: 8 }}>
              <span className="grow" style={{ minWidth: 0 }}>{s.stall_number && <span className="pill pill--accent" style={{ marginRight: 6 }}>{s.stall_number}</span>}{s.name}</span>
              <button className="btn btn--ghost btn--sm" onClick={() => run(() => api(`/occurrences/${eventId}/stalls/${s.id}`, { method: 'DELETE' }))}>{t('evt.manage.remove')}</button>
            </div>
          ))}
          <div className="paybox">
            <div className="grid-2">
              <label className="field"><span className="field__label">{t('evt.stalls.numberField')}</span><input className="field__input" value={stNo} maxLength={20} onChange={(e) => setStNo(e.target.value)} placeholder="A-12" /></label>
              <label className="field"><span className="field__label">{t('evt.stalls.name')}</span><input className="field__input" value={stName} maxLength={80} onChange={(e) => setStName(e.target.value)} /></label>
            </div>
            <label className="field"><span className="field__label">{t('evt.stalls.description')}</span><input className="field__input" value={stDesc} maxLength={300} onChange={(e) => setStDesc(e.target.value)} /></label>
            <button className="btn btn--primary" disabled={!stName.trim()} onClick={() => run(() => api(`/occurrences/${eventId}/stalls`, { body: { name: stName.trim(), stall_number: stNo.trim() || null, description: stDesc.trim() || null } }).then(() => { setStNo(''); setStName(''); setStDesc(''); }), t('tix.manage.saved'))}>{t('evt.stalls.add')}</button>
          </div>
        </div>
      )}

      {/* Recording / notes after the event */}
      <div className="stack" style={{ gap: 8 }}>
        <b>{t('evt.followup.title')}</b>
        {!started ? <span className="caption">{t('evt.followup.afterStart')}</span> : (
          <>
            <span className="caption">{t('evt.followup.hint')}</span>
            <label className="field"><span className="field__label">{t('evt.followup.recording')}</span><input className="field__input" type="url" inputMode="url" maxLength={500} value={rec} onChange={(e) => setRec(e.target.value)} placeholder="https://" /></label>
            <label className="field"><span className="field__label">{t('evt.followup.notesField')}</span><input className="field__input" type="url" inputMode="url" maxLength={500} value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="https://" /></label>
            <button className="btn btn--secondary" disabled={[rec, notes].some((v) => v.trim() && !/^https:\/\/\S+$/i.test(v.trim()))} onClick={() => run(() => api(`/occurrences/${eventId}/followup`, { method: 'PUT', body: { recording_url: rec.trim() || null, notes_url: notes.trim() || null } }), t('tix.manage.saved'))}>{t('tix.manage.save')}</button>
          </>
        )}
      </div>
    </section>
  );
}

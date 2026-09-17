'use client';

/* Circle detail (FR020, FR024, FR025, FR027 · UX09/UI09): stats pills
 * (community memory, members-only for non-open circles), member list,
 * upcoming activities, join/leave, "new activity in this circle". */

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import ActivityCard from '@/components/ActivityCard';
import { CardSkeleton, EmptyState, ErrorState, Toast } from '@/components/States';
import { api, ApiError, resolveMediaUrl, type Card, type Circle } from '@/lib/api';
import { formatDateLong, formatRelative, initials } from '@/lib/format';

type Post = { id: string; member_id: string; display_name: string; avatar: string | null; body: string; created_at: string; mine: boolean };

type Chapter = { circle_id: string; name: string; locality: string | null; member_count: number; join_policy: string };
type Fundraiser = {
  id: string; title: string; purpose: string | null; target_paise: number | null; closes_on: string | null; closed: boolean; mine: boolean;
  promised_paise: number; people: number; paid_paise: number; my_pledge: { amount_paise: number; note: string | null; paid: boolean } | null;
};

type PollOption = { id: string; label: string; option_time: string | null; occurrence_id: string | null; voters: string[]; voted: boolean };
type Poll = { id: string; question: string; kind: 'date' | 'activity'; asked_by: string; mine: boolean; created_at: string; closed: boolean; options: PollOption[] };

type JoinRequest = { request_id: string; member_id: string; display_name: string; avatar: string | null; answers: string[]; created_at: string };

type Detail = Circle & {
  members: { member_id: string; display_name: string; avatar: string | null; role: string }[];
  join_policy?: 'open' | 'approval'; // [FR115]
  join_questions?: string[];
  my_request_status?: string | null;
  join_requests?: JoinRequest[];
  group?: { id: string; name: string } | null; // [FR123] the umbrella this circle sits under
  memory: { member_count: number; activities_held: number; upcoming_count: number; first_activity_at: string | null } | null;
  upcoming: Card[];
};

export default function CircleDetailPage() {
  const { t, i18n } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [d, setD] = useState<Detail | null>(null);
  const [error, setError] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [posts, setPosts] = useState<Post[] | null>(null);
  const [draft, setDraft] = useState('');
  // [FR115] Answering happens in place on this page — no separate application screen.
  const [answering, setAnswering] = useState(false);
  // [FR120] The circle's open questions: which day, or which one shall we go to.
  const [polls, setPolls] = useState<Poll[]>([]);
  const [asking, setAsking] = useState(false);
  const [question, setQuestion] = useState('');
  const [times, setTimes] = useState<string[]>(['', '']);
  // [FR123/FR124] Sister chapters, and drives for something the community needs.
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [drives, setDrives] = useState<Fundraiser[]>([]);
  const [pledging, setPledging] = useState<string | null>(null);
  const [pledgeAmount, setPledgeAmount] = useState('');
  const [answers, setAnswers] = useState<string[]>([]);
  const say = (m: string) => { setToast(m); setTimeout(() => setToast(null), 2000); };

  const loadPosts = useCallback(() => { api<{ posts: Post[] }>(`/circles/${id}/posts`).then((r) => setPosts(r.posts)).catch(() => setPosts([])); }, [id]);
  const loadPolls = useCallback(() => { api<Poll[]>(`/circles/${id}/polls`).then(setPolls).catch(() => setPolls([])); }, [id]);
  const loadDrives = useCallback(() => { api<Fundraiser[]>(`/circles/${id}/fundraisers`).then(setDrives).catch(() => setDrives([])); }, [id]);
  const load = useCallback(() => { setError(false); api<Detail>(`/circles/${id}`).then(setD).catch(() => setError(true)); loadPosts(); loadPolls(); loadDrives(); }, [id, loadPosts, loadPolls, loadDrives]);
  useEffect(load, [load]);

  const post = async () => {
    const body = draft.trim(); if (!body) return;
    try { await api(`/circles/${id}/posts`, { body: { body }, idempotent: true }); setDraft(''); loadPosts(); }
    catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  const join = async () => {
    // A circle that asks first shows its questions here, then sends the answers with the request.
    if (d?.join_policy === 'approval' && (d.join_questions?.length ?? 0) > 0 && !answering) {
      setAnswers((d.join_questions ?? []).map(() => ''));
      setAnswering(true);
      return;
    }
    try {
      const r = await api<{ status: string }>(`/circles/${id}/join`, { body: { answers } });
      setAnswering(false);
      say(r.status === 'pending' ? t('join.asked') : t('circles.joined'));
      load();
    } catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  const askCircle = async () => {
    const options = times.filter((t) => t).map((t) => ({ label: new Date(t).toLocaleString(), option_time: new Date(t).toISOString() }));
    if (!question.trim() || options.length < 2) { say(t('poll.needTwo')); return; }
    try {
      await api(`/circles/${id}/polls`, { body: { question: question.trim(), kind: 'date', options } });
      setAsking(false); setQuestion(''); setTimes(['', '']); loadPolls();
    } catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  const votePoll = async (poll: Poll, option: PollOption) => {
    setPolls((prev) => prev.map((p) => (p.id !== poll.id ? p : { ...p, options: p.options.map((o) => (o.id === option.id ? { ...o, voted: !o.voted } : o)) })));
    try { await api(`/circles/${id}/polls/${poll.id}/vote`, { body: { option_id: option.id, picked: !option.voted } }); loadPolls(); }
    catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); loadPolls(); }
  };

  const closePoll = async (poll: Poll) => {
    try { await api(`/circles/${id}/polls/${poll.id}/close`, { body: {} }); loadPolls(); }
    catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  useEffect(() => {
    if (!d?.group) { setChapters([]); return; }
    api<Chapter[]>(`/circles/groups/${d.group.id}/chapters`).then(setChapters).catch(() => setChapters([]));
  }, [d?.group]);

  const pledge = async (f: Fundraiser, rupees: string | null) => {
    try {
      const amount_paise = rupees === null ? null : Math.round(Number(rupees) * 100);
      await api(`/circles/${id}/fundraisers/${f.id}/pledge`, { body: { amount_paise } });
      setPledging(null); setPledgeAmount(''); loadDrives();
    } catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  const setRole = async (memberId: string, role: string) => {
    try { await api(`/circles/${id}/roles`, { body: { member_id: memberId, role } }); say(role === 'assistant' ? t('role.nowAssistant') : t('role.nowMember')); load(); }
    catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  const decide = async (r: JoinRequest, approve: boolean) => {
    try {
      await api(`/circles/${id}/requests/${r.request_id}/decide`, { body: { approve } });
      say(approve ? t('join.letIn', { name: r.display_name.split(' ')[0] }) : t('join.declined'));
      load();
    } catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };
  const leave = async () => { try { await api(`/circles/${id}/leave`, { body: {} }); load(); } catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); } };

  return (
    <>
      <header className="topbar">
        <button className="icon-btn" aria-label={t('common.back')} onClick={() => router.back()}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M15 6l-6 6 6 6" /></svg>
        </button>
        <h1 style={{ fontSize: '1.25rem' }} className="truncate">{d?.name ?? ''}</h1>
        <span style={{ width: 44 }} />
      </header>
      <main className="screen">
        {error && <ErrorState onRetry={load} />}
        {!d && !error && <CardSkeleton count={1} />}
        {d && (
          <>
            <div className="row" style={{ gap: 14 }}>
              <span className="strip__ring" style={{ width: 64, height: 64, borderColor: 'transparent', padding: 0 }}><div style={{ fontSize: '1.25rem' }}>{initials(d.name)}</div></span>
              <div className="grow">
                <div className="row" style={{ gap: 8 }}><span className="pill pill--neutral">{d.type_label}</span>{!d.is_open && <span className="pill pill--neutral">{t('circles.inviteOnly')}</span>}</div>
                {d.description && <p className="muted" style={{ margin: '6px 0 0' }}>{d.description}</p>}
              </div>
            </div>
            <div className="row">
              {d.viewer_role ? (
                <>
                  <Link href={`/create?circle=${d.id}`} className="btn btn--primary grow">{t('circles.newActivity')}</Link>
                  {d.viewer_role !== 'organizer' && <button className="btn btn--ghost" onClick={leave}>{t('circles.leave')}</button>}
                </>
              ) : d.is_open ? (
                d.my_request_status === 'pending' ? (
                  <span className="pill pill--neutral" style={{ alignSelf: 'flex-start' }}>{t('join.waiting')}</span>
                ) : answering ? (
                  <div className="stack" style={{ gap: 8 }}>
                    <span className="caption">{t('join.answerHint')}</span>
                    {(d.join_questions ?? []).map((q, i) => (
                      <label key={i} className="field">
                        <span className="field__label">{q}</span>
                        <input
                          className="field__input"
                          name={`join-answer-${i}`}
                          maxLength={200}
                          value={answers[i] ?? ''}
                          onChange={(e) => setAnswers((prev) => prev.map((v, j) => (j === i ? e.target.value : v)))}
                        />
                      </label>
                    ))}
                    <div className="row" style={{ gap: 8 }}>
                      <button className="btn btn--ghost grow" onClick={() => setAnswering(false)}>{t('common.cancel')}</button>
                      <button className="btn btn--primary grow btn--spring" onClick={join}>{t('join.send')}</button>
                    </div>
                  </div>
                ) : (
                  <button className="btn btn--primary btn--block btn--spring" onClick={join}>
                    {d.join_policy === 'approval' ? t('join.ask') : t('circles.join')}
                  </button>
                )
              ) : null}
            </div>

            {d.memory && (
              <section className="stack" style={{ gap: 8 }}>
                <span className="label">{t('circles.memory')}</span>
                <div className="row">
                  <div className="stat"><b>{d.memory.member_count}</b><span>{t('circles.members', { count: d.memory.member_count }).replace(/^\d+\s*/, '')}</span></div>
                  <div className="stat"><b>{d.memory.activities_held}</b><span>{t('circles.held')}</span></div>
                  <div className="stat"><b>{d.memory.upcoming_count}</b><span>{t('circles.upcoming')}</span></div>
                  {d.memory.first_activity_at && <div className="stat"><b>{new Date(d.memory.first_activity_at).getFullYear()}</b><span>{t('circles.since')}</span></div>}
                </div>
              </section>
            )}

            {d.group && (
              <section className="card stack fade-in" style={{ gap: 8 }}>
                <b>{t('chapter.partOf', { name: d.group.name })}</b>
                {chapters.filter((c) => c.circle_id !== d.id).length === 0 ? (
                  <span className="caption">{t('chapter.onlyOne')}</span>
                ) : (
                  chapters.filter((c) => c.circle_id !== d.id).map((c) => (
                    <Link key={c.circle_id} href={`/circles/${c.circle_id}`} className="lrow lrow--tap">
                      <span className="grow">{c.name}<br /><span className="caption">{[c.locality, t('chapter.members', { count: c.member_count })].filter(Boolean).join(' · ')}</span></span>
                      <span className="muted">›</span>
                    </Link>
                  ))
                )}
              </section>
            )}

            {d.viewer_role && drives.length > 0 && (
              <section className="card stack fade-in" style={{ gap: 10 }}>
                <b>{t('drive.title')}</b>
                {drives.map((f) => {
                  const promised = f.promised_paise / 100;
                  const target = f.target_paise ? f.target_paise / 100 : null;
                  return (
                    <div key={f.id} className="stack" style={{ gap: 6 }}>
                      <b>{f.title}</b>
                      {f.purpose && <span className="caption">{f.purpose}</span>}
                      <span className="caption">
                        {target
                          ? `${t('drive.progress', { promised: promised.toLocaleString('en-IN'), target: target.toLocaleString('en-IN') })} · ${t('drive.people', { count: f.people })}`
                          : `${t('drive.promisedOnly', { promised: promised.toLocaleString('en-IN') })} · ${t('drive.people', { count: f.people })}`}
                      </span>
                      <span className="caption" style={{ color: 'var(--accent-pressed)' }}>{t('drive.noPaymentsYet')}</span>
                      {f.my_pledge ? (
                        <div className="row" style={{ gap: 8 }}>
                          <span className="pill pill--trust">{t('drive.youPromised', { amount: (f.my_pledge.amount_paise / 100).toLocaleString('en-IN') })}</span>
                          <button className="link" onClick={() => pledge(f, null)}>{t('drive.takeBack')}</button>
                        </div>
                      ) : pledging === f.id ? (
                        <div className="row" style={{ gap: 8 }}>
                          <label className="field grow" style={{ margin: 0 }}>
                            <input className="field__input" name="pledge-amount" inputMode="numeric" placeholder="₹" value={pledgeAmount} onChange={(e) => setPledgeAmount(e.target.value)} />
                          </label>
                          <button className="btn btn--primary btn--sm" disabled={!pledgeAmount.trim()} onClick={() => pledge(f, pledgeAmount)}>{t('drive.promise')}</button>
                        </div>
                      ) : (
                        !f.closed && <button className="btn btn--secondary btn--sm" style={{ alignSelf: 'flex-start' }} onClick={() => setPledging(f.id)}>{t('drive.iWillGive')}</button>
                      )}
                    </div>
                  );
                })}
              </section>
            )}

            {d.viewer_role && (
              <section className="card stack fade-in" style={{ gap: 10 }}>
                <div className="row row--between">
                  <b>{t('poll.title')}</b>
                  {!asking && <button className="btn btn--secondary btn--sm" onClick={() => setAsking(true)}>{t('poll.ask')}</button>}
                </div>
                {asking && (
                  <div className="stack" style={{ gap: 8 }}>
                    <label className="field">
                      <input className="field__input" name="poll-question" maxLength={160} placeholder={t('poll.questionPlaceholder')} value={question} onChange={(e) => setQuestion(e.target.value)} />
                    </label>
                    {times.map((v, i) => (
                      <label key={i} className="field">
                        <input className="field__input" type="datetime-local" name={`poll-time-${i}`} value={v} onChange={(e) => setTimes((prev) => prev.map((x, j) => (j === i ? e.target.value : x)))} />
                      </label>
                    ))}
                    {times.length < 4 && <button className="link" style={{ alignSelf: 'flex-start' }} onClick={() => setTimes((prev) => [...prev, ''])}>{t('poll.addOption')}</button>}
                    <div className="row" style={{ gap: 8 }}>
                      <button className="btn btn--ghost grow" onClick={() => setAsking(false)}>{t('common.cancel')}</button>
                      <button className="btn btn--primary grow" onClick={askCircle}>{t('poll.send')}</button>
                    </div>
                  </div>
                )}
                {polls.length === 0 && !asking && <span className="caption">{t('poll.none')}</span>}
                {polls.map((poll) => (
                  <div key={poll.id} className="stack" style={{ gap: 6 }}>
                    <b>{poll.question}</b>
                    <span className="caption">{t('poll.askedBy', { name: poll.asked_by })}{poll.closed ? ` · ${t('poll.closed')}` : ''}</span>
                    {poll.options.map((o) => (
                      <button
                        key={o.id}
                        type="button"
                        className="lrow lrow--tap"
                        aria-pressed={o.voted}
                        disabled={poll.closed}
                        onClick={() => votePoll(poll, o)}
                        style={{ textAlign: 'left', borderColor: o.voted ? 'var(--accent-primary)' : undefined }}
                      >
                        <span className="grow">
                          {o.voted ? '✓ ' : ''}{o.option_time ? formatDateLong(o.option_time, i18n.language) : o.label}
                          <br />
                          <span className="caption">{o.voters.length === 0 ? t('poll.noneYet') : o.voters.join(', ')}</span>
                        </span>
                        <span className="pill pill--neutral">{o.voters.length}</span>
                      </button>
                    ))}
                    {poll.mine && !poll.closed && <button className="link" style={{ alignSelf: 'flex-start' }} onClick={() => closePoll(poll)}>{t('poll.settle')}</button>}
                    {poll.closed && poll.kind === 'date' && poll.options.length > 0 && (
                      <Link
                        className="btn btn--secondary btn--sm"
                        style={{ alignSelf: 'flex-start' }}
                        href={`/create?circle=${d.id}&when=${encodeURIComponent([...poll.options].sort((a, b) => b.voters.length - a.voters.length)[0].option_time ?? '')}`}
                      >
                        {t('poll.createActivity')}
                      </Link>
                    )}
                  </div>
                ))}
              </section>
            )}

            {(d.join_requests?.length ?? 0) > 0 && (
              <section className="card stack fade-in" style={{ gap: 10, borderColor: 'var(--accent-primary)' }}>
                <div className="title">{t('join.waitingTitle', { count: d.join_requests?.length ?? 0 })}</div>
                {(d.join_requests ?? []).map((r) => (
                  <div key={r.request_id} className="stack" style={{ gap: 6 }}>
                    <div className="row" style={{ gap: 10 }}>
                      {r.avatar ? <img className="avatar avatar--lg" src={resolveMediaUrl(r.avatar) ?? ''} alt="" /> : <span className="avatar avatar--lg">{initials(r.display_name)}</span>}
                      <span className="grow"><b>{r.display_name}</b><br /><span className="caption">{formatRelative(r.created_at)}</span></span>
                    </div>
                    {(d.join_questions ?? []).map((q, i) => (
                      r.answers[i] ? <span key={i} className="caption">{q} — <b>{r.answers[i]}</b></span> : null
                    ))}
                    <div className="row" style={{ gap: 8 }}>
                      <button className="btn btn--ghost grow" onClick={() => decide(r, false)}>{t('join.notNow')}</button>
                      <button className="btn btn--primary grow" onClick={() => decide(r, true)}>{t('join.letThemIn')}</button>
                    </div>
                  </div>
                ))}
              </section>
            )}

            {d.viewer_role && (
              <section className="card stack" style={{ gap: 12 }}>
                <div className="row row--between"><span className="label">{t('circles.board')}</span><span className="caption">{t('circles.boardPrivate')}</span></div>
                <div className="composer">
                  <textarea rows={1} value={draft} onChange={(e) => setDraft(e.target.value)} placeholder={t('circles.boardPlaceholder')} aria-label={t('circles.boardPlaceholder')} maxLength={1000} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); void post(); } }} />
                  <button className="btn btn--primary btn--sm btn--spring" disabled={!draft.trim()} onClick={post}>{t('thread.send')}</button>
                </div>
                {posts && posts.length === 0 && <p className="caption" style={{ margin: 0 }}>{t('circles.boardEmpty')}</p>}
                {posts && posts.map((p) => (
                  <div key={p.id} className="row" style={{ gap: 10, alignItems: 'flex-start' }}>
                    <Link href={`/p/${p.member_id}`}>{p.avatar ? <img className="avatar avatar--lg" src={resolveMediaUrl(p.avatar) ?? ''} alt="" /> : <span className="avatar avatar--lg" />}</Link>
                    <div className="grow">
                      <div className="row" style={{ gap: 6 }}><b>{p.display_name}</b><span className="caption">· {formatRelative(p.created_at)}</span></div>
                      <p style={{ margin: '2px 0 0', whiteSpace: 'pre-wrap' }}>{p.body}</p>
                    </div>
                  </div>
                ))}
              </section>
            )}

            <section className="section">
              <div className="section__head"><h2>{t('circles.upcomingIn')}</h2></div>
              {d.upcoming.length === 0 ? <EmptyState message={t('circles.emptyUpcoming')} action={d.viewer_role ? t('circles.newActivity') : undefined} onAction={d.viewer_role ? () => router.push(`/create?circle=${d.id}`) : undefined} /> : <div className="rail">{d.upcoming.map((c) => <ActivityCard key={c.id} card={c} compact />)}</div>}
            </section>

            <section className="section">
              <div className="section__head"><h2>{t('circles.members', { count: d.members.length })}</h2></div>
              <div className="list">
                {d.members.map((m) => (
                  <div key={m.member_id} className="lrow" style={{ minHeight: 56 }}>
                    <Link href={`/p/${m.member_id}`} className="row grow" style={{ gap: 10 }}>
                      {m.avatar ? <img className="avatar avatar--lg" src={resolveMediaUrl(m.avatar) ?? ''} alt="" /> : <span className="avatar avatar--lg" />}
                      <span className="grow">{m.display_name}</span>
                    </Link>
                    {m.role === 'organizer' && <span className="pill pill--accent">{t('detail.organizer')}</span>}
                    {m.role === 'assistant' && <span className="pill pill--trust">{t('role.assistant')}</span>}
                    {/* [FR121] The organizer shares the work: one tap to ask someone to help, or to step them back. */}
                    {d.viewer_role === 'organizer' && m.role !== 'organizer' && (
                      <button className="link" onClick={() => setRole(m.member_id, m.role === 'assistant' ? 'member' : 'assistant')}>
                        {m.role === 'assistant' ? t('role.stepDown') : t('role.makeAssistant')}
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </section>
          </>
        )}
      </main>
      <Toast text={toast} />
    </>
  );
}

'use client';

/* Circle detail (FR020, FR024, FR025, FR027 · UX09/UI09). A circle is a community
 * page, never a chat (owner, 2026-09-28). Design brief from the critique agent the
 * same day — photo-led, editorial, near-monochrome, one accent:
 *   hero   full-bleed cover (Luma: no text on the photo), floating back/more, the
 *          top bar fades in only once the hero scrolls away (Apple 2025);
 *   head   caption, the name in the display serif, faces + count, description;
 *   action ONE saffron primary; invite/manage are quiet icon buttons;
 *   tabs   Posts · Events · Photos · Members with a sliding indicator;
 *   feed   hairline-separated posts (Threads/Strava clubs), polls with bars,
 *          documents as rows. Organizer-only circles keep posting to organizers. */

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';

import ActivityCard from '@/components/ActivityCard';
import { ArrowLeft, BarChart3, Ellipsis, FileText, Image as ImageIcon, Megaphone, MessageCircle, Paperclip, Pin, Settings2, SmilePlus, UserPlus, X } from 'lucide-react';

import CircleCover from '@/components/CircleCover';
import InvitePeopleSheet from '@/components/InvitePeopleSheet';
import { Sheet } from '@/components/Sheet';
import { CardSkeleton, ErrorState, Toast } from '@/components/States';
import { api, ApiError, resolveMediaUrl, type Card, type Circle } from '@/lib/api';
import { formatDateLong, formatRelative, formatWhen, initials } from '@/lib/format';
import { useIdentity } from '@/lib/identity';

type Post = {
  id: string; member_id: string; display_name: string; avatar: string | null; body: string; created_at: string; mine: boolean;
  photo_url: string | null; doc_url: string | null; doc_name: string | null;
  // [049] Announcements (organizers' voice, react-only), pins, reactions and one level of comments.
  is_announcement?: boolean; pinned?: boolean; reactions?: Record<string, string[]>; comments?: PostComment[];
};
type PostComment = { id: string; member_id: string; display_name: string; avatar: string | null; body: string; created_at: string; mine: boolean };

type Tab = 'posts' | 'events' | 'photos' | 'members';

type Chapter = { circle_id: string; name: string; locality: string | null; member_count: number; join_policy: string };
type Fundraiser = {
  id: string; title: string; purpose: string | null; target_paise: number | null; closes_on: string | null; closed: boolean; mine: boolean;
  promised_paise: number; people: number; paid_paise: number; my_pledge: { amount_paise: number; note: string | null; paid: boolean } | null;
};

type PollOption = { id: string; label: string; option_time: string | null; occurrence_id: string | null; voters: string[]; voted: boolean };
type Poll = { id: string; question: string; kind: 'date' | 'activity' | 'question'; asked_by: string; mine: boolean; created_at: string; closed: boolean; options: PollOption[] };

type JoinRequest = { request_id: string; member_id: string; display_name: string; avatar: string | null; answers: string[]; created_at: string };


type Detail = Circle & {
  // [FR125] Season circles (temple, travel) carry dates and a computed "concluded".
  starts_on: string | null; ends_on: string | null; is_concluded: boolean;
  posting_policy: 'members' | 'organizers';
  members: { member_id: string; display_name: string; avatar: string | null; role: string }[];
  join_policy?: 'open' | 'approval'; // [FR115]
  join_questions?: string[];
  my_request_status?: string | null;
  join_requests?: JoinRequest[];
  group?: { id: string; name: string } | null; // [FR123] the umbrella this circle sits under
  memory: { member_count: number; activities_held: number; upcoming_count: number; first_activity_at: string | null } | null;
  upcoming: Card[];
};

type FeedItem = { at: string } & ({ kind: 'post'; post: Post } | { kind: 'poll'; poll: Poll });

const MEMBER_PREVIEW = 8;
const MAX_JOIN_QUESTIONS = 3;
const FEED_PREVIEW = 20;

export default function CircleDetailPage() {
  const { t, i18n } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { identity, profile } = useIdentity();
  const [d, setD] = useState<Detail | null>(null);
  const [error, setError] = useState(false);
  const [toast, setToast] = useState<{ text: string; actionLabel?: string; onAction?: () => void; ms: number } | null>(null);
  // Each toast clears itself; a newer toast replaces it and restarts the clock.
  useEffect(() => {
    if (!toast) return;
    const handle = setTimeout(() => setToast(null), toast.ms);
    return () => clearTimeout(handle);
  }, [toast]);
  const [posts, setPosts] = useState<Post[] | null>(null);
  const [reactionSet, setReactionSet] = useState<string[]>([]);
  const [maxPins, setMaxPins] = useState(3);
  const [announce, setAnnounce] = useState(false);
  const [reactFor, setReactFor] = useState<string | null>(null);
  const [openComments, setOpenComments] = useState<Record<string, boolean>>({});
  const [commentDraft, setCommentDraft] = useState<Record<string, string>>({});
  const [mQuestions, setMQuestions] = useState<string[]>([]);
  const [polls, setPolls] = useState<Poll[]>([]);
  // Composer: one place to write a post, attach a photo, or ask a question (a poll IS a post).
  const [draft, setDraft] = useState('');
  const [composing, setComposing] = useState(false);
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [docFile, setDocFile] = useState<File | null>(null);
  const [tab, setTab] = useState<Tab>('posts');
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [pollMode, setPollMode] = useState(false);
  const [pollOptions, setPollOptions] = useState<string[]>(['', '']);
  const [posting, setPosting] = useState(false);
  // [FR115] Answering happens in place on this page — no separate application screen.
  const [answering, setAnswering] = useState(false);
  const [answers, setAnswers] = useState<string[]>([]);
  // [FR123/FR124] Sister chapters, and drives for something the community needs.
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [drives, setDrives] = useState<Fundraiser[]>([]);
  const [pledging, setPledging] = useState<string | null>(null);
  const [pledgeAmount, setPledgeAmount] = useState('');
  const [menu, setMenu] = useState(false);
  // [FR121] Invite: the organizer's people from Milavn itself, added in place.
  const [inviting, setInviting] = useState(false);
  const [allMembers, setAllMembers] = useState(false);
  const [allFeed, setAllFeed] = useState(false);
  // The organizer manages the circle in place (owner: the admin gets every option).
  const [managing, setManaging] = useState(false);
  const [mName, setMName] = useState('');
  const [mDesc, setMDesc] = useState('');
  const [mJoin, setMJoin] = useState<'open' | 'approval'>('open');
  const [mPost, setMPost] = useState<'members' | 'organizers'>('members');
  const [saving, setSaving] = useState(false);
  const fileInput = useRef<HTMLInputElement | null>(null);
  const docInput = useRef<HTMLInputElement | null>(null);
  const coverInput = useRef<HTMLInputElement | null>(null);
  const [coverBusy, setCoverBusy] = useState(false);
  const [descOpen, setDescOpen] = useState(false);
  const [lightbox, setLightbox] = useState<string | null>(null);
  const [postMenu, setPostMenu] = useState<Post | null>(null);
  // The top bar stays out of the way until the hero has scrolled past.
  const [pastHero, setPastHero] = useState(false);
  const heroRef = useRef<HTMLDivElement | null>(null);
  const tabRefs = useRef<Record<string, HTMLButtonElement | null>>({});
  const [indicator, setIndicator] = useState<{ left: number; width: number } | null>(null);

  const say = (text: string, action?: { label: string; run: () => void }, ms = 2000) => {
    setToast({ text, ms, actionLabel: action?.label, onAction: action ? () => { setToast(null); action.run(); } : undefined });
  };

  const loadPosts = useCallback(() => {
    api<{ posts: Post[]; reactions?: string[]; max_pins?: number }>(`/circles/${id}/posts`)
      .then((r) => { setPosts(r.posts); setReactionSet(r.reactions ?? []); setMaxPins(r.max_pins ?? 3); })
      .catch(() => setPosts([]));
  }, [id]);
  const loadPolls = useCallback(() => { api<Poll[]>(`/circles/${id}/polls`).then(setPolls).catch(() => setPolls([])); }, [id]);
  const loadDrives = useCallback(() => { api<Fundraiser[]>(`/circles/${id}/fundraisers`).then(setDrives).catch(() => setDrives([])); }, [id]);
  const load = useCallback(() => { setError(false); api<Detail>(`/circles/${id}`).then(setD).catch(() => setError(true)); loadPosts(); loadPolls(); loadDrives(); }, [id, loadPosts, loadPolls, loadDrives]);
  useEffect(load, [load]);
  // A non-member can't read posts, so their first tab is Events.
  const [tabChosen, setTabChosen] = useState(false);
  useEffect(() => { if (d && !d.viewer_role && !tabChosen) setTab('events'); }, [d, tabChosen]);

  const startComposer = (mode: 'text' | 'photo' | 'doc' | 'poll') => {
    setComposing(true);
    setPollMode(mode === 'poll');
    if (mode === 'photo') setTimeout(() => fileInput.current?.click(), 0);
    if (mode === 'doc') setTimeout(() => docInput.current?.click(), 0);
  };

  const resetComposer = () => { setDraft(''); setPhotoFile(null); setDocFile(null); setPollMode(false); setPollOptions(['', '']); setAnnounce(false); setComposing(false); };

  const submitPost = async () => {
    if (posting) return;
    setPosting(true);
    try {
      if (pollMode) {
        const options = pollOptions.map((o) => o.trim()).filter(Boolean).map((label) => ({ label }));
        if (!draft.trim() || options.length < 2) { say(t('poll.needTwo')); return; }
        await api(`/circles/${id}/polls`, { body: { question: draft.trim(), kind: 'question', options } });
        loadPolls();
      } else if (photoFile || docFile) {
        const form = new FormData();
        if (photoFile) form.append('photo', photoFile);
        if (docFile) form.append('document', docFile);
        form.append('body', draft.trim());
        if (announce) form.append('announcement', 'true');
        await api(`/circles/${id}/posts/media`, { form });
        loadPosts();
      } else {
        const body = draft.trim();
        if (!body) return;
        await api(`/circles/${id}/posts`, { body: { body, announcement: announce }, idempotent: true });
        loadPosts();
      }
      resetComposer();
    } catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
    finally { setPosting(false); }
  };

  const togglePin = async (p: Post) => {
    setPostMenu(null);
    try {
      await api(`/circles/${id}/posts/${p.id}/pin`, { body: { pinned: !p.pinned } });
      say(p.pinned ? t('posts.unpinned') : t('posts.pinnedDone'));
      loadPosts();
    } catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  const react = async (p: Post, emoji: string) => {
    setReactFor(null);
    const me = identity?.member_id ?? '';
    // Optimistic: the pill changes at once; the reload settles it.
    setPosts((cur) => (cur ?? []).map((x) => {
      if (x.id !== p.id) return x;
      const who = x.reactions?.[emoji] ?? [];
      const next = who.includes(me) ? who.filter((m) => m !== me) : [...who, me];
      return { ...x, reactions: { ...(x.reactions ?? {}), [emoji]: next } };
    }));
    try { await api(`/circles/${id}/posts/${p.id}/reactions`, { body: { emoji } }); }
    catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
    loadPosts();
  };

  const sendComment = async (p: Post) => {
    const body = (commentDraft[p.id] ?? '').trim();
    if (!body) return;
    try {
      await api(`/circles/${id}/posts/${p.id}/comments`, { body: { body } });
      setCommentDraft((cur) => ({ ...cur, [p.id]: '' }));
      loadPosts();
    } catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  const removeComment = async (p: Post, c: PostComment) => {
    try { await api(`/circles/${id}/posts/${p.id}/comments/${c.id}`, { method: 'DELETE' }); say(t('posts.commentDeleted')); loadPosts(); }
    catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  const removePost = async (p: Post) => {
    setPostMenu(null);
    try { await api(`/circles/${id}/posts/${p.id}`, { method: 'DELETE' }); say(t('circles.postDeleted')); loadPosts(); }
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

  // Removing someone is a second, deliberate tap on the same button (no extra dialog).
  const [confirmRemove, setConfirmRemove] = useState<string | null>(null);
  const removeMember = async (memberId: string, name: string) => {
    if (confirmRemove !== memberId) { setConfirmRemove(memberId); return; }
    setConfirmRemove(null);
    try { await api(`/circles/${id}/members/${memberId}`, { method: 'DELETE' }); say(t('circles.removed', { name: name.split(' ')[0] })); load(); }
    catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
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

  // Leaving is one tap in the ⋯ menu, so the toast carries the way back: an open
  // circle rejoins instantly; one that screens sends a fresh request instead.
  const leave = async () => {
    if (!d) return;
    setMenu(false);
    try {
      await api(`/circles/${id}/leave`, { body: {} });
      say(t('circles.left', { name: d.name }), {
        label: t('common.undo'),
        run: () => {
          api<{ status: string }>(`/circles/${id}/join`, { body: {} })
            .then((r) => { say(r.status === 'pending' ? t('circles.askedRejoin') : t('circles.rejoined')); load(); })
            .catch((e) => say(e instanceof ApiError ? e.message : t('state.error')));
        },
      }, 6000);
      load();
    } catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  const openInvite = () => setInviting(true);

  // Invitations still waiting for an answer — the organizer can see and withdraw them.
  type PendingInvite = { invite_id: string; member_id: string; display_name: string; avatar: string | null; invited_by: { member_id: string; display_name: string }; created_at: string };
  const [pendingInvites, setPendingInvites] = useState<PendingInvite[]>([]);
  const loadPendingInvites = () => { api<PendingInvite[]>(`/circles/${id}/invites`).then(setPendingInvites).catch(() => setPendingInvites([])); };
  const cancelInvite = async (inv: PendingInvite) => {
    try { await api(`/circles/${id}/invites/${inv.invite_id}`, { method: 'DELETE' }); setPendingInvites((prev) => prev.filter((x) => x.invite_id !== inv.invite_id)); say(t('invite.withdrawn')); }
    catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
  };

  const openManage = () => {
    loadPendingInvites();
    if (!d) return;
    setMName(d.name); setMDesc(d.description ?? ''); setMJoin(d.join_policy ?? 'open'); setMPost(d.posting_policy); setConfirmDelete(false);
    setMQuestions(d.join_questions?.length ? [...d.join_questions] : ['']);
    setManaging(true);
  };

  // The cover photo applies the moment it's picked — no extra save step.
  const setCover = async (file: File | null) => {
    if (coverBusy) return;
    setCoverBusy(true);
    try {
      if (file) {
        const form = new FormData();
        form.append('photo', file);
        await api(`/circles/${id}/cover`, { form });
      } else {
        await api(`/circles/${id}/cover`, { method: 'DELETE' });
      }
      load();
    } catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
    finally { setCoverBusy(false); }
  };

  // Deleting is for everyone and permanent, so it takes a second, deliberate tap in place.
  const deleteCircle = async () => {
    if (!confirmDelete) { setConfirmDelete(true); return; }
    try {
      await api(`/circles/${id}`, { method: 'DELETE' });
      setManaging(false);
      say(t('manage.deleted'));
      router.replace('/circles');
    } catch (e) { setConfirmDelete(false); say(e instanceof ApiError ? e.message : t('state.error'), undefined, 4000); }
  };

  const saveManage = async () => {
    if (saving) return;
    setSaving(true);
    try {
      await api(`/circles/${id}`, { method: 'PATCH', body: {
        name: mName, description: mDesc, join_policy: mJoin, posting_policy: mPost,
        ...(mJoin === 'approval' ? { join_questions: mQuestions.map((q) => q.trim()).filter(Boolean).slice(0, MAX_JOIN_QUESTIONS) } : {}),
      } });
      setManaging(false);
      say(t('manage.saved'));
      load();
    } catch (e) { say(e instanceof ApiError ? e.message : t('state.error')); }
    finally { setSaving(false); }
  };

  const canManage = d?.viewer_role === 'organizer' || d?.viewer_role === 'assistant';
  const mayPost = Boolean(d?.viewer_role && (d.posting_policy !== 'organizers' || canManage));
  const startYear = d ? new Date(d.memory?.first_activity_at ?? d.created_at).getFullYear() : null;
  const sinceYear = startYear !== null && startYear < new Date().getFullYear() ? startYear : null;
  const shownMembers = d ? (allMembers ? d.members : d.members.slice(0, MEMBER_PREVIEW)) : [];
  const roleOf = new Map((d?.members ?? []).map((m) => [m.member_id, m.role]));
  const myAvatar = resolveMediaUrl(profile?.photo_url ?? identity?.avatar ?? null);

  // One feed, newest first: written posts and polls belong together (FB/WhatsApp model).
  // [049] Pinned posts (announcements take a pin) stay on top, in the server's order.
  const pinnedFeed: FeedItem[] = (posts ?? []).filter((p) => p.pinned).map((post) => ({ kind: 'post', at: post.created_at, post }));
  const feed: FeedItem[] = [
    ...pinnedFeed,
    ...[
      ...(posts ?? []).filter((p) => !p.pinned).map((post): FeedItem => ({ kind: 'post', at: post.created_at, post })),
      ...polls.map((poll): FeedItem => ({ kind: 'poll', at: poll.created_at, poll })),
    ].sort((a, b) => b.at.localeCompare(a.at)),
  ];
  const pinnedCount = pinnedFeed.length;
  const shownFeed = allFeed ? feed : feed.slice(0, FEED_PREVIEW);

  // Events tab: what's ahead (soonest first), then what the circle has already done.
  const nowIso = new Date().toISOString();
  const upcomingEvents = (d?.upcoming ?? []).filter((c) => c.time_start >= nowIso && c.status !== 'cancelled').sort((a, b) => a.time_start.localeCompare(b.time_start));
  const pastEvents = (d?.upcoming ?? []).filter((c) => c.time_start < nowIso).sort((a, b) => b.time_start.localeCompare(a.time_start));
  const photoPosts = (posts ?? []).filter((p) => p.photo_url);
  const TABS: { key: Tab; label: string }[] = [
    { key: 'posts', label: t('posts.tabPosts') },
    { key: 'events', label: t('posts.tabEvents') },
    { key: 'photos', label: t('posts.tabPhotos') },
    { key: 'members', label: t('posts.tabMembers') },
  ];

  useEffect(() => {
    const el = heroRef.current;
    if (!el) return;
    const io = new IntersectionObserver(([entry]) => setPastHero(!entry.isIntersecting), { rootMargin: '-56px 0px 0px 0px' });
    io.observe(el);
    return () => io.disconnect();
  }, [d?.id, d?.cover_url]);

  // Sliding tab indicator: measured, so it fits equal tabs on a phone and auto-width tabs on desktop.
  useLayoutEffect(() => {
    const measure = () => {
      const el = tabRefs.current[tab];
      if (el) setIndicator({ left: el.offsetLeft, width: el.offsetWidth });
    };
    measure();
    window.addEventListener('resize', measure);
    return () => window.removeEventListener('resize', measure);
  }, [tab, d?.id]);

  const roleText = (memberId: string) => {
    const role = roleOf.get(memberId);
    if (role === 'organizer') return t('detail.organizer');
    if (role === 'assistant') return t('role.assistant');
    return null;
  };
  const face = (avatar: string | null, name: string, size: 'sm' | 'md' | 'lg') => (
    avatar ? <img className={`cx-av cx-av--${size}`} src={resolveMediaUrl(avatar) ?? ''} alt="" /> : <span className={`cx-av cx-av--${size}`}>{initials(name)}</span>
  );

  const hasHero = Boolean(d?.cover_url);
  const typeText = d ? (d.circle_type === 'public' ? t('circles.openToAll') : d.type_label) : '';
  const caption = d ? [typeText, d.locality_label, !d.is_open ? t('circles.inviteOnly') : null, d.is_concluded ? t('circles.concluded') : null].filter(Boolean).join(' · ') : '';

  const membersList = d && d.members.length > 0 && (
    <div className="cx-list">
      {shownMembers.map((m) => (
        <div key={m.member_id} className="cx-row">
          <Link href={`/p/${m.member_id}`} className="row grow" style={{ gap: 12, minWidth: 0 }}>
            {face(m.avatar, m.display_name, 'md')}
            <span className="grow" style={{ minWidth: 0 }}>
              <span className="cx-strong truncate" style={{ display: 'block' }}>{m.display_name}</span>
              {roleText(m.member_id) && <span className="cx-caption">{roleText(m.member_id)}</span>}
            </span>
          </Link>
          {/* [FR121] The organizer shares the work: one tap to ask someone to help, or to step them back. */}
          {d.viewer_role === 'organizer' && m.role !== 'organizer' && (
            <button className="cx-textbtn" onClick={() => setRole(m.member_id, m.role === 'assistant' ? 'member' : 'assistant')}>
              {m.role === 'assistant' ? t('role.stepDown') : t('role.makeAssistant')}
            </button>
          )}
          {((d.viewer_role === 'organizer' && m.role !== 'organizer') || (d.viewer_role === 'assistant' && m.role === 'member')) && (
            <button className="cx-textbtn" style={{ color: confirmRemove === m.member_id ? 'var(--danger)' : 'var(--cx-muted)' }} onClick={() => removeMember(m.member_id, m.display_name)}>
              {confirmRemove === m.member_id ? t('circles.removeConfirm') : t('circles.remove')}
            </button>
          )}
        </div>
      ))}
      {d.members.length > MEMBER_PREVIEW && (
        <button className="cx-textbtn" style={{ alignSelf: 'flex-start', marginTop: 8 }} onClick={() => setAllMembers((v) => !v)}>
          {allMembers ? t('circles.showFewer') : t('circles.seeAll', { count: d.members.length })}
        </button>
      )}
    </div>
  );

  const chaptersSection = d?.group && (
    <section className="cx-aside-block">
      <span className="cx-label">{t('chapter.partOf', { name: d.group.name })}</span>
      {chapters.filter((c) => c.circle_id !== d.id).length === 0 ? (
        <span className="cx-caption">{t('chapter.onlyOne')}</span>
      ) : (
        chapters.filter((c) => c.circle_id !== d.id).map((c) => (
          <Link key={c.circle_id} href={`/circles/${c.circle_id}`} className="cx-row">
            <span className="grow"><span className="cx-strong">{c.name}</span><br /><span className="cx-caption">{[c.locality, t('chapter.members', { count: c.member_count })].filter(Boolean).join(' · ')}</span></span>
          </Link>
        ))
      )}
    </section>
  );

  const drivesSection = d?.viewer_role && drives.length > 0 && (
    <section className="cx-block">
      <span className="cx-label">{t('drive.title')}</span>
      {drives.map((f) => {
        const promised = f.promised_paise / 100;
        const target = f.target_paise ? f.target_paise / 100 : null;
        return (
          <div key={f.id} className="stack" style={{ gap: 6 }}>
            <span className="cx-strong">{f.title}</span>
            {f.purpose && <span className="cx-caption">{f.purpose}</span>}
            {target && <div className="cx-bar"><span style={{ width: `${Math.min(100, (promised / target) * 100)}%` }} /></div>}
            <span className="cx-caption">
              {target
                ? `${t('drive.progress', { promised: promised.toLocaleString('en-IN'), target: target.toLocaleString('en-IN') })} · ${t('drive.people', { count: f.people })}`
                : `${t('drive.promisedOnly', { promised: promised.toLocaleString('en-IN') })} · ${t('drive.people', { count: f.people })}`}
            </span>
            <span className="cx-caption">{t('drive.noPaymentsYet')}</span>
            {f.my_pledge ? (
              <div className="row" style={{ gap: 12 }}>
                <span className="cx-caption">{t('drive.youPromised', { amount: (f.my_pledge.amount_paise / 100).toLocaleString('en-IN') })}</span>
                <button className="cx-textbtn" onClick={() => pledge(f, null)}>{t('drive.takeBack')}</button>
              </div>
            ) : pledging === f.id ? (
              <div className="row" style={{ gap: 8 }}>
                <input className="cx-input grow" name="pledge-amount" inputMode="numeric" placeholder={t('drive.amountPlaceholder')} value={pledgeAmount} onChange={(e) => setPledgeAmount(e.target.value)} />
                <button className="cx-btn cx-btn--primary" disabled={!pledgeAmount.trim()} onClick={() => pledge(f, pledgeAmount)}>{t('drive.promise')}</button>
              </div>
            ) : (
              !f.closed && <button className="cx-btn cx-btn--quiet" style={{ alignSelf: 'flex-start' }} onClick={() => setPledging(f.id)}>{t('drive.iWillGive')}</button>
            )}
          </div>
        );
      })}
    </section>
  );

  const actionsBlock = d && (
    <div className="cx-actions">
      {d.viewer_role ? (
        <>
          <Link href={`/create?circle=${d.id}`} className={`cx-btn ${d.viewer_role === 'organizer' ? 'cx-btn--primary' : 'cx-btn--quiet'} cx-btn--lg grow`}>{t('circles.newActivity')}</Link>
          {(d.is_open || canManage) && <button className="cx-iconbtn" aria-label={t('circles.invite')} onClick={openInvite}><UserPlus size={20} strokeWidth={1.75} /></button>}
          {d.viewer_role === 'organizer' && <button className="cx-iconbtn" aria-label={t('manage.button')} onClick={openManage}><Settings2 size={20} strokeWidth={1.75} /></button>}
                  </>
      ) : d.is_open ? (
        d.my_request_status === 'pending' ? (
          <button className="cx-btn cx-btn--quiet cx-btn--lg grow" disabled>{t('join.waiting')}</button>
        ) : answering ? (
          <div className="stack grow" style={{ gap: 10 }}>
            <span className="cx-caption">{t('join.answerHint')}</span>
            {(d.join_questions ?? []).map((q, i) => (
              <label key={i} className="stack" style={{ gap: 6 }}>
                <span className="cx-strong">{q}</span>
                <input className="cx-input" name={`join-answer-${i}`} maxLength={200} value={answers[i] ?? ''} onChange={(e) => setAnswers((prev) => prev.map((v, j) => (j === i ? e.target.value : v)))} />
              </label>
            ))}
            <div className="row" style={{ gap: 8 }}>
              <button className="cx-btn cx-btn--ghost" onClick={() => setAnswering(false)}>{t('common.cancel')}</button>
              <button className="cx-btn cx-btn--primary grow" onClick={join}>{t('join.send')}</button>
            </div>
          </div>
        ) : (
          <button className="cx-btn cx-btn--primary cx-btn--lg grow" onClick={join}>{d.join_policy === 'approval' ? t('join.ask') : t('circles.join')}</button>
        )
      ) : null}
    </div>
  );


  return (
    <div className={`cx cx-page${d && !hasHero ? ' cx-page--nohero' : ''}`}>
      {/* The bar is empty over the photo; the name arrives once the hero is gone. */}
      <header className={`topbar cx-topbar${pastHero || (d && !hasHero) ? ' is-solid' : ''}${pastHero ? ' show-title' : ''}`}>
        <button className="icon-btn" aria-label={t('common.back')} onClick={() => (history.length > 1 ? router.back() : router.push('/circles'))}><ArrowLeft size={20} strokeWidth={1.75} /></button>
        <h1 className="truncate cx-topbar__title">{d?.name ?? ''}</h1>
        {d?.viewer_role && d.viewer_role !== 'organizer' ? (
          <button className="icon-btn" aria-label={t('common.more')} onClick={() => setMenu(true)}><Ellipsis size={20} strokeWidth={1.75} /></button>
        ) : <span style={{ width: 44 }} />}
      </header>

      {error && <main className="screen"><ErrorState onRetry={load} /></main>}
      {!d && !error && <main className="screen"><CardSkeleton count={1} /></main>}
      {d && (
        <>
          {hasHero && (
            <div className="cx-hero" ref={heroRef}>
              <CircleCover variant="hero" name={d.name} coverUrl={d.cover_url} faces={d.viewer_role ? d.members : undefined} caption={caption} />
            </div>
          )}

          <div className="cx-layout">
            <main className="cx-main">
              <div className="cx-head" ref={hasHero ? undefined : heroRef}>
                <span className="cx-label">{caption}</span>
                <h1 className="cx-title">{d.name}</h1>
                <div className="row" style={{ gap: 10 }}>
                  {d.members.length > 1 && <span className="cx-stack">{d.members.slice(0, 5).map((m) => <span key={m.member_id}>{face(m.avatar, m.display_name, hasHero ? 'sm' : 'md')}</span>)}</span>}
                  <span className="cx-caption">{[t('circles.members', { count: d.member_count }), sinceYear ? t('circles.sinceYear', { year: sinceYear }) : null].filter(Boolean).join(' · ')}</span>
                </div>
                {d.description && (
                  <p className={`cx-desc${descOpen ? ' is-open' : ''}`}>
                    {d.description}
                  </p>
                )}
                {d.description && d.description.length > 160 && !descOpen && <button className="cx-textbtn" style={{ alignSelf: 'flex-start' }} onClick={() => setDescOpen(true)}>{t('circles.readMore')}</button>}
              </div>

              {/* One action block: under the head on a phone, first in the aside on desktop (Luma's action card). */}
              <div className="cx-only-narrow">{actionsBlock}</div>

              {/* Meetup encourages organizers to add their own images — a quiet nudge until there is one. */}
              {d.viewer_role === 'organizer' && !d.cover_url && (
                <div className="cx-hairrow">
                  <span className="grow cx-caption">{t('manage.coverHint')}</span>
                  <button className="cx-btn cx-btn--quiet" onClick={() => coverInput.current?.click()} disabled={coverBusy}>{t('manage.coverAdd')}</button>
                </div>
              )}
              <input ref={coverInput} type="file" accept="image/jpeg,image/png,image/webp" hidden onChange={(e) => { const f = e.target.files?.[0]; if (f) void setCover(f); e.target.value = ''; }} />

              {(d.join_requests?.length ?? 0) > 0 && (
                <section className="cx-block">
                  <span className="cx-label">{t('join.waitingTitle', { count: d.join_requests?.length ?? 0 })}</span>
                  {(d.join_requests ?? []).map((r) => (
                    <div key={r.request_id} className="stack" style={{ gap: 8 }}>
                      <div className="cx-row" style={{ borderBottom: 0 }}>
                        {face(r.avatar, r.display_name, 'md')}
                        <span className="grow"><span className="cx-strong">{r.display_name}</span><br /><span className="cx-caption">{formatRelative(r.created_at)}</span></span>
                        <button className="cx-btn cx-btn--ghost" onClick={() => decide(r, false)}>{t('join.notNow')}</button>
                        <button className="cx-btn cx-btn--primary" onClick={() => decide(r, true)}>{t('join.letThemIn')}</button>
                      </div>
                      {(d.join_questions ?? []).map((q, i) => (r.answers[i] ? <span key={i} className="cx-caption">{q} — <b>{r.answers[i]}</b></span> : null))}
                    </div>
                  ))}
                </section>
              )}

              {upcomingEvents.length > 0 && (
                <section className="stack cx-only-narrow" style={{ gap: 12 }}>
                  <span className="cx-label">{t('circles.nextUp')}</span>
                  <ActivityCard card={upcomingEvents[0]} />
                </section>
              )}

              <nav className="cx-tabs" role="tablist" aria-label={d.name}>
                {TABS.map((x) => (
                  <button
                    key={x.key}
                    ref={(el) => { tabRefs.current[x.key] = el; }}
                    role="tab"
                    className="cx-tab"
                    aria-selected={tab === x.key}
                    onClick={() => { setTab(x.key); setTabChosen(true); if (x.key === 'members' && canManage) loadPendingInvites(); }}
                  >
                    {x.label}
                    {x.key === 'events' && upcomingEvents.length > 0 && <span className="cx-tab__count">{upcomingEvents.length}</span>}
                  </button>
                ))}
                {indicator && <span className="cx-tabs__ind" style={{ transform: `translateX(${indicator.left}px)`, width: indicator.width }} />}
              </nav>

              {tab === 'posts' && !d.viewer_role && <p className="cx-caption cx-empty">{t('posts.membersOnly')}</p>}
              {tab === 'posts' && d.viewer_role && (
                <section className="stack" style={{ gap: 0 }}>
                  {drivesSection}
                  {d.posting_policy === 'organizers' && <p className="cx-caption" style={{ margin: '12px 0 0' }}>{t('posts.adminOnly')}</p>}

                  {mayPost && (
                    <div className={`cx-composer${composing ? ' is-open' : ''}`}>
                      <div className="row" style={{ gap: 10 }}>
                        {myAvatar ? <img className="cx-av cx-av--sm" src={myAvatar} alt="" /> : <span className="cx-av cx-av--sm">{initials(identity?.display_name ?? '')}</span>}
                        {composing ? (
                          <textarea
                            className="cx-input grow"
                            rows={pollMode ? 2 : 3}
                            autoFocus
                            maxLength={pollMode ? 160 : 1000}
                            value={draft}
                            onChange={(e) => setDraft(e.target.value)}
                            placeholder={pollMode ? t('posts.questionPlaceholder') : t('posts.share')}
                            aria-label={t('posts.share')}
                          />
                        ) : (
                          <button className="cx-input cx-composer__prompt grow" onClick={() => startComposer('text')}>{t('posts.share')}</button>
                        )}
                        {!composing && (
                          <>
                            <button className="cx-iconbtn cx-iconbtn--sm" aria-label={t('posts.addPhoto')} onClick={() => startComposer('photo')}><ImageIcon size={18} strokeWidth={1.75} /></button>
                          </>
                        )}
                      </div>
                      {composing && (
                        <div className="stack" style={{ gap: 8, paddingLeft: 42 }}>
                          {pollMode && pollOptions.map((v, i) => (
                            <input key={i} className="cx-input" name={`poll-option-${i}`} maxLength={120} placeholder={t('posts.option', { n: i + 1 })} value={v} onChange={(e) => setPollOptions((prev) => prev.map((x, j) => (j === i ? e.target.value : x)))} />
                          ))}
                          {pollMode && pollOptions.length < 4 && <button className="cx-textbtn" style={{ alignSelf: 'flex-start' }} onClick={() => setPollOptions((prev) => [...prev, ''])}>{t('posts.addOption')}</button>}
                          {photoFile && !pollMode && <span className="cx-attach"><ImageIcon size={16} strokeWidth={1.75} /> <span className="grow truncate">{photoFile.name}</span><button className="cx-plain" aria-label={t('common.close')} onClick={() => setPhotoFile(null)}><X size={16} /></button></span>}
                          {docFile && !pollMode && <span className="cx-attach"><Paperclip size={16} strokeWidth={1.75} /> <span className="grow truncate">{docFile.name}</span><button className="cx-plain" aria-label={t('common.close')} onClick={() => setDocFile(null)}><X size={16} /></button></span>}
                          <div className="row" style={{ gap: 6 }}>
                            {!pollMode && <button className="cx-iconbtn cx-iconbtn--sm" aria-label={t('posts.addPhoto')} onClick={() => fileInput.current?.click()}><ImageIcon size={18} strokeWidth={1.75} /></button>}
                            {!pollMode && <button className="cx-iconbtn cx-iconbtn--sm" aria-label={t('posts.addDocument')} onClick={() => docInput.current?.click()}><Paperclip size={18} strokeWidth={1.75} /></button>}
                            <button className="cx-iconbtn cx-iconbtn--sm" aria-pressed={pollMode} aria-label={t('posts.askQuestion')} onClick={() => { setPollMode((v) => !v); setAnnounce(false); setPhotoFile(null); setDocFile(null); }}><BarChart3 size={18} strokeWidth={1.75} /></button>
                            {canManage && !pollMode && (
                              <button className="cx-chip" aria-pressed={announce} title={t('posts.announceHint')} onClick={() => setAnnounce((v) => !v)}><Megaphone size={16} strokeWidth={1.75} aria-hidden="true" />{t('posts.announcement')}</button>
                            )}
                            <span className="grow" />
                            <button className="cx-btn cx-btn--ghost" onClick={resetComposer}>{t('common.cancel')}</button>
                            <button className="cx-btn cx-btn--primary" disabled={posting || (!draft.trim() && !photoFile && !docFile)} onClick={submitPost}>{t('posts.post')}</button>
                          </div>
                        </div>
                      )}
                      <input ref={fileInput} type="file" accept="image/jpeg,image/png,image/webp" hidden onChange={(e) => { setPhotoFile(e.target.files?.[0] ?? null); e.target.value = ''; }} />
                      <input ref={docInput} type="file" accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt" hidden onChange={(e) => { setDocFile(e.target.files?.[0] ?? null); e.target.value = ''; }} />
                    </div>
                  )}

                  {posts !== null && feed.length === 0 && <p className="cx-caption cx-empty">{t('posts.empty')}</p>}

                  <div className="cx-feed">
                    {shownFeed.map((item) => item.kind === 'post' ? (
                      <article key={`p-${item.post.id}`} className={`cx-post${item.post.is_announcement ? ' cx-post--announce' : ''}${item.post.pinned ? ' cx-post--pinned' : ''}`}>
                        <Link href={`/p/${item.post.member_id}`} className="cx-post__av">{face(item.post.avatar, item.post.display_name, 'md')}</Link>
                        <div className="cx-post__main">
                          {(item.post.is_announcement || item.post.pinned) && (
                            <div className="cx-post__flags">
                              {item.post.is_announcement && <span className="cx-post__flag cx-post__flag--announce"><Megaphone size={14} strokeWidth={1.75} aria-hidden="true" />{t('posts.announcement')}</span>}
                              {item.post.pinned && <span className="cx-post__flag"><Pin size={14} strokeWidth={1.75} aria-hidden="true" />{t('posts.pinned')}</span>}
                            </div>
                          )}
                          <div className="cx-post__meta">
                            <span className="cx-strong">{item.post.mine ? t('circles.boardYou') : item.post.display_name}</span>
                            {roleText(item.post.member_id) && <span className="cx-caption">· {roleText(item.post.member_id)}</span>}
                            <span className="cx-caption">· {formatWhen(item.post.created_at, i18n.language)}</span>
                            <span className="grow" />
                            {(item.post.mine || canManage) && <button className="cx-plain cx-post__more" aria-label={t('common.more')} onClick={() => setPostMenu(item.post)}><Ellipsis size={18} strokeWidth={1.75} /></button>}
                          </div>
                          {item.post.body && <p className="cx-post__body">{item.post.body}</p>}
                          {item.post.photo_url && (
                            <button className="cx-plain cx-post__photo" onClick={() => setLightbox(item.post.photo_url)}>
                              <img src={resolveMediaUrl(item.post.photo_url) ?? ''} alt="" loading="lazy" />
                            </button>
                          )}
                          {item.post.doc_url && (
                            <a className="cx-doc" href={resolveMediaUrl(item.post.doc_url) ?? ''} target="_blank" rel="noopener noreferrer">
                              <FileText size={20} strokeWidth={1.75} aria-hidden="true" />
                              <span className="grow truncate">{item.post.doc_name}</span>
                              <span className="cx-textbtn">{t('posts.openDoc')}</span>
                            </a>
                          )}
                          {(() => {
                            const p = item.post;
                            const me = identity?.member_id ?? '';
                            const used = Object.entries(p.reactions ?? {}).filter(([, who]) => who.length > 0);
                            const comments = p.comments ?? [];
                            const showComments = openComments[p.id] || comments.length > 0;
                            return (
                              <>
                                <div className="cx-post__actions">
                                  {used.map(([emoji, who]) => (
                                    <button key={emoji} className="cx-react" aria-pressed={who.includes(me)} aria-label={t('posts.reactWith', { emoji, count: who.length })} onClick={() => react(p, emoji)}>
                                      <span aria-hidden="true">{emoji}</span><span>{who.length}</span>
                                    </button>
                                  ))}
                                  <button className="cx-plain cx-post__act" aria-expanded={reactFor === p.id} aria-label={t('posts.react')} onClick={() => setReactFor((v) => (v === p.id ? null : p.id))}><SmilePlus size={18} strokeWidth={1.75} /></button>
                                  {!p.is_announcement && (
                                    <button className="cx-plain cx-post__act" aria-label={t('posts.comment')} onClick={() => setOpenComments((cur) => ({ ...cur, [p.id]: !cur[p.id] }))}>
                                      <MessageCircle size={18} strokeWidth={1.75} />{comments.length > 0 && <span className="cx-caption">{comments.length}</span>}
                                    </button>
                                  )}
                                </div>
                                {reactFor === p.id && (
                                  <div className="cx-reactpick" role="group" aria-label={t('posts.react')}>
                                    {reactionSet.map((emoji) => (
                                      <button key={emoji} className="cx-plain" aria-pressed={(p.reactions?.[emoji] ?? []).includes(me)} onClick={() => react(p, emoji)}>{emoji}</button>
                                    ))}
                                  </div>
                                )}
                                {!p.is_announcement && showComments && (
                                  <div className="cx-comments">
                                    {comments.map((c) => (
                                      <div key={c.id} className="cx-comment">
                                        <Link href={`/p/${c.member_id}`} className="cx-post__av">{face(c.avatar, c.display_name, 'sm')}</Link>
                                        <div className="cx-comment__main">
                                          <span className="cx-strong">{c.mine ? t('circles.boardYou') : c.display_name}</span>
                                          <span className="cx-caption"> · {formatWhen(c.created_at, i18n.language)}</span>
                                          <p className="cx-comment__body">{c.body}</p>
                                        </div>
                                        {(c.mine || canManage) && <button className="cx-plain cx-post__act" aria-label={t('posts.deleteComment')} onClick={() => removeComment(p, c)}><X size={14} /></button>}
                                      </div>
                                    ))}
                                    {openComments[p.id] && (
                                      <div className="row" style={{ gap: 8 }}>
                                        <input
                                          className="cx-input grow" name={`comment-${p.id}`} maxLength={500} placeholder={t('posts.commentPlaceholder')} aria-label={t('posts.commentPlaceholder')}
                                          value={commentDraft[p.id] ?? ''}
                                          onChange={(e) => setCommentDraft((cur) => ({ ...cur, [p.id]: e.target.value }))}
                                          onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); void sendComment(p); } }}
                                        />
                                        <button className="cx-btn cx-btn--primary" disabled={!(commentDraft[p.id] ?? '').trim()} onClick={() => sendComment(p)}>{t('posts.reply')}</button>
                                      </div>
                                    )}
                                    {!openComments[p.id] && <button className="cx-textbtn" style={{ alignSelf: 'flex-start' }} onClick={() => setOpenComments((cur) => ({ ...cur, [p.id]: true }))}>{t('posts.addComment')}</button>}
                                  </div>
                                )}
                              </>
                            );
                          })()}
                        </div>
                      </article>
                    ) : (() => {
                      const poll = item.poll;
                      const total = poll.options.reduce((n, o) => n + o.voters.length, 0);
                      return (
                        <article key={`q-${poll.id}`} className="cx-post">
                          <span className="cx-post__av"><span className="cx-av cx-av--md cx-av--icon"><BarChart3 size={18} strokeWidth={1.75} /></span></span>
                          <div className="cx-post__main">
                            <div className="cx-post__meta">
                              <span className="cx-strong">{poll.asked_by}</span>
                              <span className="cx-caption">· {formatWhen(poll.created_at, i18n.language)}{poll.closed ? ` · ${t('poll.closed')}` : ''}</span>
                            </div>
                            <p className="cx-post__body cx-strong" style={{ fontSize: '1rem' }}>{poll.question}</p>
                            <div className="stack" style={{ gap: 6 }}>
                              {poll.options.map((o) => (
                                <button key={o.id} type="button" className={`cx-opt${o.voted ? ' is-mine' : ''}`} aria-pressed={o.voted} disabled={poll.closed} onClick={() => votePoll(poll, o)}>
                                  <span className="cx-opt__bar" style={{ width: `${total ? (o.voters.length / total) * 100 : 0}%` }} />
                                  <span className="cx-opt__label">{o.option_time ? formatDateLong(o.option_time, i18n.language) : o.label}</span>
                                  <span className="cx-opt__count">{o.voters.length}</span>
                                </button>
                              ))}
                            </div>
                            <div className="row" style={{ gap: 12 }}>
                              {poll.mine && !poll.closed && <button className="cx-textbtn" onClick={() => closePoll(poll)}>{t('poll.settle')}</button>}
                              {poll.closed && poll.kind === 'date' && poll.options.length > 0 && (
                                <Link className="cx-textbtn" href={`/create?circle=${d.id}&when=${encodeURIComponent([...poll.options].sort((a, b) => b.voters.length - a.voters.length)[0].option_time ?? '')}`}>{t('poll.createActivity')}</Link>
                              )}
                            </div>
                          </div>
                        </article>
                      );
                    })())}
                  </div>
                  {feed.length > FEED_PREVIEW && !allFeed && <button className="cx-textbtn" style={{ alignSelf: 'center', marginTop: 12 }} onClick={() => setAllFeed(true)}>{t('circles.showEarlier')}</button>}
                </section>
              )}

              {tab === 'events' && (
                <section className="stack" style={{ gap: 14, paddingTop: 16 }}>
                  <div className="cx-sechead">
                    <span className="cx-label">{t('posts.upcomingEvents')}</span>
                    {d.viewer_role && <Link href={`/create?circle=${d.id}`} className="cx-btn cx-btn--quiet">{t('circles.newActivity')}</Link>}
                  </div>
                  {upcomingEvents.length === 0 && pastEvents.length === 0 && <p className="cx-caption" style={{ margin: 0 }}>{t('posts.noEventsAtAll')}</p>}
                  {upcomingEvents.length > 0 && <div className="cx-evgrid">{upcomingEvents.map((c) => <ActivityCard key={c.id} card={c} compact />)}</div>}
                  {pastEvents.length > 0 && <span className="cx-label" style={{ marginTop: 8 }}>{t('posts.pastEvents')}</span>}
                  {pastEvents.length > 0 && <div className="cx-evgrid">{pastEvents.map((c) => <ActivityCard key={c.id} card={c} compact />)}</div>}
                </section>
              )}

              {tab === 'photos' && (
                !d.viewer_role ? <p className="cx-caption cx-empty">{t('posts.membersOnly')}</p>
                : photoPosts.length === 0 ? <p className="cx-caption cx-empty">{t('posts.noPhotos')}</p>
                : (
                  <div className="cx-photos">
                    {photoPosts.map((p) => (
                      <button key={p.id} className="cx-plain" onClick={() => setLightbox(p.photo_url)}>
                        <img src={resolveMediaUrl(p.photo_url) ?? ''} alt={p.body || p.display_name} loading="lazy" />
                      </button>
                    ))}
                  </div>
                )
              )}

              {tab === 'members' && (
                <section className="stack" style={{ gap: 12, paddingTop: 8 }}>
                  {!d.viewer_role && d.members.length === 0 && <p className="cx-caption cx-empty">{t('circles.membersHidden')}</p>}
                  {membersList}
                  {canManage && pendingInvites.length > 0 && (
                    <div className="stack" style={{ gap: 4 }}>
                      <span className="cx-label">{t('invite.pendingTitle', { count: pendingInvites.length })}</span>
                      <div className="cx-list">
                        {pendingInvites.map((inv) => (
                          <div key={inv.invite_id} className="cx-row">
                            {face(inv.avatar, inv.display_name, 'md')}
                            <span className="grow" style={{ minWidth: 0 }}>
                              <span className="cx-strong truncate" style={{ display: 'block' }}>{inv.display_name}</span>
                              <span className="cx-caption">{t('invite.invitedBy', { name: inv.invited_by.display_name.split(' ')[0] })}</span>
                            </span>
                            <button className="cx-textbtn" onClick={() => cancelInvite(inv)}>{t('invite.withdraw')}</button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  <div className="m-only">{chaptersSection}</div>
                </section>
              )}
            </main>

            <aside className="cx-aside">
              <section className="cx-aside-block">{actionsBlock}</section>
              {upcomingEvents.length > 0 && (
                <section className="cx-aside-block">
                  <span className="cx-label">{t('circles.nextUp')}</span>
                  <ActivityCard card={upcomingEvents[0]} compact />
                </section>
              )}
              {upcomingEvents.length > 1 && (
                <section className="cx-aside-block">
                  <span className="cx-label">{t('posts.upcomingEvents')}</span>
                  {upcomingEvents.slice(1, 4).map((c) => (
                    <Link key={c.id} href={`/a/${c.slug}`} className="cx-row">
                      <span className="grow"><span className="cx-strong">{c.title}</span><br /><span className="cx-caption">{formatWhen(c.time_start, i18n.language)}</span></span>
                    </Link>
                  ))}
                </section>
              )}
              {chaptersSection}
            </aside>
          </div>
        </>
      )}

      {/* Quiet actions: leave for members; the same place holds the organizer's rarer actions. */}
      <Sheet open={menu} onClose={() => setMenu(false)} label={t('common.more')}>
        <div className="stack">
          {d?.viewer_role === 'organizer' ? (
            <button className="cx-btn cx-btn--ghost cx-btn--lg" onClick={() => { setMenu(false); openManage(); }}>{t('manage.title')}</button>
          ) : (
            <button className="cx-btn cx-btn--ghost cx-btn--lg" onClick={leave}>{t('circles.leave')}</button>
          )}
          <button className="cx-btn cx-btn--quiet cx-btn--lg" onClick={() => setMenu(false)}>{t('common.cancel')}</button>
        </div>
      </Sheet>

      <Sheet open={postMenu !== null} onClose={() => setPostMenu(null)} label={t('common.more')}>
        <div className="stack">
          {canManage && postMenu && (
            <button className="cx-btn cx-btn--ghost cx-btn--lg" disabled={!postMenu.pinned && pinnedCount >= maxPins} onClick={() => togglePin(postMenu)}>
              {postMenu.pinned ? t('posts.unpin') : pinnedCount >= maxPins ? t('posts.pinFull', { count: maxPins }) : t('posts.pin')}
            </button>
          )}
          {postMenu && (postMenu.mine || canManage) && <button className="cx-btn cx-btn--danger cx-btn--lg" onClick={() => removePost(postMenu)}>{t('common.delete')}</button>}
          <button className="cx-btn cx-btn--quiet cx-btn--lg" onClick={() => setPostMenu(null)}>{t('common.cancel')}</button>
        </div>
      </Sheet>

      {d && (
        <InvitePeopleSheet
          open={inviting}
          onClose={() => setInviting(false)}
          circleId={d.id}
          circleName={d.name}
          canShareLink={canManage || (d.is_open && d.join_policy !== 'approval')}
          onDone={(m) => { say(m); load(); }}
        />
      )}

      {/* [Owner 2026-09-28] The organizer gets every option of their circle, in one place. */}
      <Sheet open={managing} onClose={() => setManaging(false)} label={t('manage.title')}>
        <div className="stack cx" style={{ gap: 16 }}>
          <h2 className="cx-h2">{t('manage.title')}</h2>
          <div className="stack" style={{ gap: 8 }}>
            <span className="cx-label">{t('manage.cover')}</span>
            {d?.cover_url ? (
              <div className="mcover">
                <img src={resolveMediaUrl(d.cover_url) ?? ''} alt="" />
                <div className="row" style={{ gap: 8 }}>
                  <button className="cx-btn cx-btn--quiet" disabled={coverBusy} onClick={() => coverInput.current?.click()}>{t('manage.coverChange')}</button>
                  <button className="cx-btn cx-btn--ghost" disabled={coverBusy} onClick={() => setCover(null)}>{t('manage.coverRemove')}</button>
                </div>
              </div>
            ) : (
              <button className="mcover mcover--empty" disabled={coverBusy} onClick={() => coverInput.current?.click()}>
                <span className="cx-strong">{t('manage.coverAdd')}</span>
                <span className="cx-caption">{t('manage.coverHint')}</span>
              </button>
            )}
          </div>
          <label className="stack" style={{ gap: 6 }}>
            <span className="cx-label">{t('manage.name')}</span>
            <input className="cx-input" name="circle-name" maxLength={80} value={mName} onChange={(e) => setMName(e.target.value)} />
          </label>
          <label className="stack" style={{ gap: 6 }}>
            <span className="cx-label">{t('manage.description')}</span>
            <textarea className="cx-input" name="circle-description" rows={3} maxLength={500} value={mDesc} onChange={(e) => setMDesc(e.target.value)} />
          </label>
          <div className="stack" style={{ gap: 8 }}>
            <span className="cx-label">{t('manage.whoJoins')}</span>
            <div className="cx-chips">
              <button className="cx-chip" aria-pressed={mJoin === 'open'} onClick={() => setMJoin('open')}>{t('join.anyone')}</button>
              <button className="cx-chip" aria-pressed={mJoin === 'approval'} onClick={() => setMJoin('approval')}>{t('join.askFirst')}</button>
            </div>
          </div>
          {mJoin === 'approval' && (
            <div className="stack" style={{ gap: 8 }}>
              <span className="cx-label">{t('manage.joinQuestions')}</span>
              <span className="cx-caption">{t('manage.joinQuestionsHint', { count: MAX_JOIN_QUESTIONS })}</span>
              {mQuestions.map((q, i) => (
                <div key={i} className="row" style={{ gap: 8 }}>
                  <input
                    className="cx-input grow" name={`join-question-${i}`} maxLength={200} value={q}
                    placeholder={t(i === 0 ? 'join.questionPlaceholder0' : 'join.questionPlaceholder1')}
                    aria-label={t('manage.joinQuestionN', { n: i + 1 })}
                    onChange={(e) => setMQuestions((prev) => prev.map((v, j) => (j === i ? e.target.value : v)))}
                  />
                  <button className="cx-iconbtn cx-iconbtn--sm" aria-label={t('manage.removeQuestion')} onClick={() => setMQuestions((prev) => prev.filter((_, j) => j !== i))}><X size={16} /></button>
                </div>
              ))}
              {mQuestions.length < MAX_JOIN_QUESTIONS && (
                <button className="cx-textbtn" style={{ alignSelf: 'flex-start' }} onClick={() => setMQuestions((prev) => [...prev, ''])}>{t('manage.addQuestion')}</button>
              )}
            </div>
          )}
          <div className="stack" style={{ gap: 8 }}>
            <span className="cx-label">{t('manage.whoPosts')}</span>
            <div className="cx-chips">
              <button className="cx-chip" aria-pressed={mPost === 'members'} onClick={() => setMPost('members')}>{t('manage.postMembers')}</button>
              <button className="cx-chip" aria-pressed={mPost === 'organizers'} onClick={() => setMPost('organizers')}>{t('manage.postOrganizers')}</button>
            </div>
          </div>
          <div className="row cx-sheetfoot" style={{ gap: 8 }}>
            <button className="cx-btn cx-btn--ghost grow" onClick={() => setManaging(false)}>{t('common.cancel')}</button>
            <button className="cx-btn cx-btn--primary grow" disabled={saving || !mName.trim()} onClick={saveManage}>{t('common.save')}</button>
          </div>
          <button className={`cx-btn cx-btn--lg ${confirmDelete ? 'cx-btn--danger' : 'cx-btn--danger-text'}`} onClick={deleteCircle}>
            {confirmDelete ? t('manage.deleteConfirm') : t('manage.delete')}
          </button>
        </div>
      </Sheet>

      {lightbox && (
        <div className="cx-lightbox" role="dialog" aria-modal="true" onClick={() => setLightbox(null)}>
          <button className="cx-iconbtn cx-lightbox__close" aria-label={t('common.close')} onClick={() => setLightbox(null)}><X size={20} /></button>
          <img src={resolveMediaUrl(lightbox) ?? ''} alt="" />
        </div>
      )}

      <Toast text={toast?.text ?? null} actionLabel={toast?.actionLabel} onAction={toast?.onAction} />
    </div>
  );
}

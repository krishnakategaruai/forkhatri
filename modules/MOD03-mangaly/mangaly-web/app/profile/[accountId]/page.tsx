'use client';

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import FamilyNotes from '@/components/FamilyNotes';
import VoiceIntroPlayer from '@/components/VoiceIntroPlayer';
import { useActiveContext } from '@/lib/activeContext';
import { resolveMediaUrl } from '@/lib/api';
import { requireSession } from '@/lib/auth';
import {
  getSharing,
  requestFamilyContact,
  setShare,
  withdrawFamilyContact,
  type ShareCategory,
  type SharingOverview,
} from '@/lib/connections';
import { listMembers, type Member } from '@/lib/homeCircle';
import { getSnippet, type Snippet } from '@/lib/discovery';
import { viewProfileFull, viewPublicProfile, type ProfileView, type PublicProfile } from '@/lib/profile';
import { findCategory, type CategoryDef } from '@/lib/profileCategoryConfig';
import { formatFieldValue } from '@/lib/profileFormat';
import {
  PROFILE_SECTIONS,
  PROMPT_CATEGORY,
  isPromptValue,
  type PromptSlot,
  type SectionId,
} from '@/lib/profileSections';

/* FR020/FR021 · A connection's profile, laid out the way Hinge reads: photos
 * interleaved with prompts and biodata, everything permitted shown at once
 * with no second unlock step. Partner preferences never reach this screen.
 * FR016 · A Home Circle member acting for a candidate also keeps private
 * notes about this match here. */

type Block =
  | { kind: 'photo'; index: number }
  | { kind: 'identity' }
  | { kind: 'prompt'; slot: PromptSlot }
  | { kind: 'section'; id: SectionId };

const LAYOUT: Block[] = [
  { kind: 'photo', index: 0 },
  { kind: 'identity' },
  { kind: 'prompt', slot: 'prompt_1' },
  { kind: 'photo', index: 1 },
  { kind: 'section', id: 'basics' },
  { kind: 'section', id: 'lifestyle' },
  { kind: 'prompt', slot: 'prompt_2' },
  { kind: 'photo', index: 2 },
  { kind: 'section', id: 'family' },
  { kind: 'section', id: 'future' },
  { kind: 'prompt', slot: 'prompt_3' },
  { kind: 'photo', index: 3 },
  { kind: 'photo', index: 4 },
  { kind: 'photo', index: 5 },
];

function ageFromDob(dob: string): number {
  const birth = new Date(dob);
  const now = new Date();
  let age = now.getFullYear() - birth.getFullYear();
  if (now.getMonth() < birth.getMonth() || (now.getMonth() === birth.getMonth() && now.getDate() < birth.getDate())) {
    age -= 1;
  }
  return age;
}

export default function MemberProfilePage() {
  const { t, i18n } = useTranslation(['common', 'profile']);
  const router = useRouter();
  const { accountId } = useParams<{ accountId: string }>();
  const [view, setView] = useState<ProfileView | null | undefined>(undefined);
  const [connectionId, setConnectionId] = useState<string | null>(null);
  const [sharing, setSharing] = useState<SharingOverview | null>(null);
  const [confirming, setConfirming] = useState<ShareCategory | null>(null);
  const [busy, setBusy] = useState<ShareCategory | null>(null);
  const [shareError, setShareError] = useState<string | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [snippet, setSnippet] = useState<Snippet | null>(null);
  const [publicProfile, setPublicProfile] = useState<PublicProfile | null>(null);
  const { active } = useActiveContext();
  const family = active?.kind === 'family' ? active.circle : null;

  useEffect(() => {
    let active = true;
    (async () => {
      const session = await requireSession();
      if (!active || !session) return;
      const result = await viewProfileFull(accountId);
      if (!active) return;
      const connection = new URLSearchParams(window.location.search).get('connection');
      const [overview, circle]: [SharingOverview | null, Member[]] =
        connection && result ? await Promise.all([getSharing(connection), listMembers()]) : [null, []];
      if (!active) return;
      setConnectionId(connection);
      setSharing(overview);
      setMembers(circle);
      // Not connected: the matrimonial facts this candidate has published
      // (DEC-V1-020) — a family member evaluating a match needs the biodata,
      // not four fields. Identity still waits for acceptance.
      if (!result) {
        const [publicView, fallback] = await Promise.all([
          viewPublicProfile(accountId),
          getSnippet(accountId),
        ]);
        setPublicProfile(publicView);
        setSnippet(fallback);
      }
      if (!active) return;
      setView(result);
    })();
    return () => {
      active = false;
    };
  }, [accountId]);

  const header = (title: string) => (
    <header className="topbar">
      <button type="button" className="icon-btn" onClick={() => router.back()} aria-label={t('common:action.back')}>
        ←
      </button>
      <h1>{title}</h1>
      {connectionId && view ? (
        <Link href={`/messages/${connectionId}`} className="icon-btn" aria-label={t('profile:view.message')}>
          <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
            <path
              fill="none"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M4 5h16v11H9l-5 4z"
            />
          </svg>
        </Link>
      ) : (
        <span style={{ width: 44 }} aria-hidden="true" />
      )}
    </header>
  );

  const familyNotes =
    family && family.candidate_account_id !== accountId ? (
      <FamilyNotes
        membershipId={family.membership_id}
        subjectAccountId={accountId}
        candidateName={family.candidate_name}
      />
    ) : null;

  if (view === undefined) {
    return (
      <main className="screen screen--centered">
        <p className="caption">{t('common:state.loading')}</p>
      </main>
    );
  }

  if (view === null) {
    /* Not connected yet. Shaadi.com shows a registered member another member's
       full biodata and gates only identity and contact; Mangaly does the same
       (DEC-V1-020) — the facts are here, the name and contact are not. A family
       member evaluating a match reads them as a biodata sheet, the way every
       matrimony service presents them; a candidate reads the same facts the
       Hinge way, led by the photo and the person's own words. */
    const facts = publicProfile?.attributes ?? {};
    const educationRaw = publicProfile?.education_level ?? snippet?.education_level ?? null;
    const educationKey = `profile:option.highest_education_level.${educationRaw}`;
    const education = educationRaw && t(educationKey) !== educationKey ? t(educationKey) : educationRaw;
    const age = publicProfile?.age ?? snippet?.age ?? null;
    const locality = publicProfile?.locality ?? snippet?.locality ?? null;
    const profession = publicProfile?.profession ?? snippet?.profession ?? null;
    const photoUrl = publicProfile?.photo_url ?? snippet?.photo_url ?? null;
    const headline = [age ? t('profile:hub.ageYears', { age }) : null, locality].filter(Boolean).join(' · ');
    const subline = [education, profession].filter(Boolean).join(' · ');

    const sections = PROFILE_SECTIONS.map((section) => ({
      id: section.id,
      rows: section.categories.flatMap((category) => {
        const def = findCategory(category);
        if (!def) return [];
        return def.fields
          .map((f) => ({
            key: `${category}.${f.key}`,
            label: t(`profile:field.${category}.${f.key}`),
            text: formatFieldValue(t, f, facts[category]?.[f.key]),
          }))
          .filter((row): row is { key: string; label: string; text: string } => !!row.text);
      }),
    })).filter((section) => section.rows.length > 0);

    const prompts = (['prompt_1', 'prompt_2', 'prompt_3'] as PromptSlot[])
      .map((slot) => facts[PROMPT_CATEGORY]?.[slot])
      .filter(isPromptValue);

    const hero = (
      <>
        {photoUrl && (
          <div className="preview-photo">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={resolveMediaUrl(photoUrl) ?? ''} alt="" />
          </div>
        )}
        <div className="preview-identity">
          <span className="profile-hero__name">{headline}</span>
          {subline && <span className="caption">{subline}</span>}
          <span className="caption">
            🔒{' '}
            {family
              ? t('profile:view.familyHint', { name: family.candidate_name.split(' ')[0] })
              : t('profile:view.publicHint')}
          </span>
        </div>
      </>
    );

    if (!publicProfile && !snippet) {
      return (
        <>
          {header(t('profile:view.title'))}
          <main className="screen">
            <div className="card">
              <h2 className="h2">{t('profile:view.locked')}</h2>
              <p className="caption">{t('profile:view.lockedHint')}</p>
            </div>
            {familyNotes}
          </main>
        </>
      );
    }

    if (family) {
      return (
        <>
          {header(t('profile:view.title'))}
          <main className="screen preview-card">
            {hero}
            {sections.length > 0 && (
              <div className="card">
                <div className="label">{t('profile:view.biodata')}</div>
                <dl className="biodata">
                  {sections.flatMap((section) =>
                    section.rows.map((row) => (
                      <div key={row.key} className="biodata__row">
                        <dt>{row.label}</dt>
                        <dd>{row.text}</dd>
                      </div>
                    ))
                  )}
                </dl>
              </div>
            )}
            {familyNotes}
          </main>
        </>
      );
    }

    return (
      <>
        {header(t('profile:view.title'))}
        <main className="screen preview-card">
          {hero}
          {prompts.map((value, i) => (
            <div key={i} className="prompt-card prompt-card--elevated">
              <span className="prompt-card__q">{t(`profile:hub.prompts.q.${value.q}`)}</span>
              <span className="prompt-card__a">{value.a}</span>
            </div>
          ))}
          {sections.map((section) => (
            <div key={section.id} className="card preview-section">
              <div className="label">{t(`profile:hub.section.${section.id}`)}</div>
              <dl className="biodata">
                {section.rows.map((row) => (
                  <div key={row.key} className="biodata__row">
                    <dt>{row.label}</dt>
                    <dd>{row.text}</dd>
                  </div>
                ))}
              </dl>
            </div>
          ))}
        </main>
      </>
    );
  }

  const { profile, photos, attributes } = view;

  function formatDate(iso: string): string {
    return new Date(iso).toLocaleDateString(i18n.language, { day: 'numeric', month: 'short', year: 'numeric' });
  }

  async function changeShare(category: ShareCategory, shared: boolean) {
    if (!connectionId) return;
    setBusy(category);
    setShareError(null);
    const outcome =
      category === 'family_contact' && !shared
        ? await withdrawFamilyContact(connectionId)
        : await setShare(connectionId, category, shared);
    setBusy(null);
    if (!outcome.ok) {
      setShareError(t('profile:view.share.error'));
      return;
    }
    setConfirming(null);
    setSharing((prev) =>
      prev ? { ...prev, mine: prev.mine.map((m) => (m.category === category ? outcome.data : m)) } : prev
    );
  }

  async function askFamily(membershipId: string) {
    if (!connectionId) return;
    setBusy('family_contact');
    setShareError(null);
    const outcome = await requestFamilyContact(connectionId, membershipId);
    setBusy(null);
    if (!outcome.ok) {
      setShareError(t('profile:view.share.error'));
      return;
    }
    setConfirming(null);
    setSharing((prev) =>
      prev ? { ...prev, mine: prev.mine.map((m) => (m.category === 'family_contact' ? outcome.data : m)) } : prev
    );
  }

  function relationshipLabel(value: string | null | undefined): string {
    return value ? t(`profile:view.share.relationship.${value}`) : '';
  }

  function renderBlock(block: Block, index: number) {
    if (block.kind === 'photo') {
      const photo = photos[block.index];
      if (!photo) return null;
      return (
        <div key={`photo-${index}`} className="preview-photo">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={resolveMediaUrl(photo.url) ?? ''} alt={t('profile:view.photoAlt', { name: profile.name })} />
        </div>
      );
    }
    if (block.kind === 'identity') {
      return (
        <div key="identity" className="preview-identity">
          <span className="profile-hero__name">{profile.name}</span>
          <span className="caption">
            {[t('profile:hub.ageYears', { age: ageFromDob(profile.date_of_birth) }), profile.city_locality]
              .filter(Boolean)
              .join(' · ')}
          </span>
        </div>
      );
    }
    if (block.kind === 'prompt') {
      const value = attributes[PROMPT_CATEGORY]?.[block.slot];
      if (!isPromptValue(value)) return null;
      return (
        <div key={block.slot} className="prompt-card prompt-card--elevated">
          <span className="prompt-card__q">{t(`profile:hub.prompts.q.${value.q}`)}</span>
          <span className="prompt-card__a">{value.a}</span>
        </div>
      );
    }
    const section = PROFILE_SECTIONS.find((s) => s.id === block.id);
    const rows = (section?.categories ?? [])
      .map((c) => findCategory(c))
      .filter((d): d is CategoryDef => !!d)
      .map((d) => ({
        def: d,
        text: d.fields
          .map((f) => formatFieldValue(t, f, attributes[d.category]?.[f.key]))
          .filter((v): v is string => !!v)
          .join(' · '),
      }))
      .filter((r) => r.text);
    if (rows.length === 0) return null;
    return (
      <div key={block.id} className="card preview-section">
        <div className="label">{t(`profile:hub.section.${block.id}`)}</div>
        <dl className="biodata">
          {rows.map((r) => (
            <div key={r.def.category} className="biodata__row">
              <dt>{t(`profile:hub.category.${r.def.category}`)}</dt>
              <dd>{r.text}</dd>
            </div>
          ))}
        </dl>
      </div>
    );
  }

  return (
    <>
      {header(profile.name)}
      <main className="screen preview-card">
        {LAYOUT.map(renderBlock)}
        <VoiceIntroPlayer url={view.voice_intro_url ?? null} name={profile.name} />
        {familyNotes}
        {sharing && (
          <section className="card share-card" aria-label={t('profile:view.share.title', { name: profile.name })}>
            <div className="label">{t('profile:view.share.title', { name: profile.name })}</div>
            <p className="caption">{t('profile:view.share.intro')}</p>
            <ul className="share-list">
              {sharing.mine.map((s) => (
                <li key={s.category} className="share-row">
                  {confirming === s.category ? (
                    <div className="share-row__confirm">
                      <p>{t(`profile:view.share.confirm.${s.category}`, { name: profile.name, value: s.value })}</p>
                      {s.category === 'family_contact' && (
                        <div className="quick-pick__chips">
                          {members
                            .filter((m) => m.member_account_id !== accountId)
                            .map((m) => (
                            <button
                              key={m.membership_id}
                              type="button"
                              className="quick-pick__chip quick-pick__chip--active"
                              disabled={busy === 'family_contact'}
                              onClick={() => void askFamily(m.membership_id)}
                            >
                              {t('profile:view.share.askMember', { relationship: relationshipLabel(m.relationship_type) })}
                            </button>
                          ))}
                        </div>
                      )}
                      <div className="sheet__row">
                        <button type="button" className="quick-pick__chip" onClick={() => setConfirming(null)}>
                          {t('profile:view.share.cancel')}
                        </button>
                        {s.category !== 'family_contact' && (
                          <button
                            type="button"
                            className="cta"
                            disabled={busy === s.category}
                            onClick={() => void changeShare(s.category, true)}
                          >
                            {t('profile:view.share.confirmCta')}
                          </button>
                        )}
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="share-row__text">
                        <span className="share-row__name">{t(`profile:view.share.category.${s.category}`)}</span>
                        <span className="caption">
                          {s.shared_at
                            ? t('profile:view.share.sharedOn', { date: formatDate(s.shared_at) })
                            : s.pending
                              ? t('profile:view.share.waiting', { relationship: relationshipLabel(s.pending) })
                              : s.available
                              ? t('profile:view.share.notShared')
                              : t(`profile:view.share.unavailable.${s.category}`)}
                        </span>
                      </div>
                      {s.shared_at ? (
                        <button
                          type="button"
                          className="quick-pick__chip"
                          disabled={busy === s.category}
                          onClick={() => void changeShare(s.category, false)}
                        >
                          {t('profile:view.share.stop')}
                        </button>
                      ) : s.available && !s.pending ? (
                        <button
                          type="button"
                          className="quick-pick__chip quick-pick__chip--active"
                          disabled={busy === s.category}
                          onClick={() => setConfirming(s.category)}
                        >
                          {t('profile:view.share.share')}
                        </button>
                      ) : null}
                    </>
                  )}
                </li>
              ))}
            </ul>
            {shareError && (
              <p className="form__error" role="alert">
                {shareError}
              </p>
            )}
            <div className="label">{t('profile:view.share.theirsTitle', { name: profile.name })}</div>
            {sharing.theirs.length === 0 ? (
              <p className="caption">{t('profile:view.share.theirsEmpty')}</p>
            ) : (
              <ul className="share-list">
                {sharing.theirs.map((s) => (
                  <li key={s.category} className="share-row">
                    <div className="share-row__text">
                      <span className="share-row__name">{t(`profile:view.share.category.${s.category}`)}</span>
                      <span className="caption">
                        {s.shared_at ? t('profile:view.share.sharedOn', { date: formatDate(s.shared_at) }) : ''}
                      </span>
                    </div>
                    {s.category === 'phone' && s.value && (
                      <a className="quick-pick__chip" href={`tel:${s.value}`}>
                        {s.value}
                      </a>
                    )}
                    {s.category === 'email' && s.value && (
                      <a className="quick-pick__chip" href={`mailto:${s.value}`}>
                        {s.value}
                      </a>
                    )}
                    {s.category === 'additional_photos' && (
                      <span className="caption">{t('profile:view.share.photosShared')}</span>
                    )}
                    {s.category === 'family_contact' &&
                      s.value &&
                      (() => {
                        const contact = JSON.parse(s.value) as { name: string | null; relationship: string; phone: string };
                        return (
                          <a className="quick-pick__chip" href={`tel:${contact.phone}`}>
                            {`${contact.name ?? relationshipLabel(contact.relationship)} · ${contact.phone}`}
                          </a>
                        );
                      })()}
                  </li>
                ))}
              </ul>
            )}
          </section>
        )}
      </main>
    </>
  );
}

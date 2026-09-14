'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Avatar } from '@/components/Avatar';
import { resolveMediaUrl } from '@/lib/api';
import { getSession, logOut, type Session } from '@/lib/auth';
import { SUPPORTED_LANGUAGES, type Language } from '@/lib/i18n/config';
import { setPreferredLanguage } from '@/lib/i18n/provider';
import { findCategory, type CategoryDef, type FieldDef } from '@/lib/profileCategoryConfig';
import {
  deletePhoto,
  getAllAttributeValues,
  getOwnProfile,
  listPhotos,
  reorderPhotos,
  setPrimaryPhoto,
  updateCategoryAttributes,
  uploadPhoto,
  type AttributeState,
  type AttributeValue,
  type CategoryAttributes,
  type Photo,
  type Profile,
} from '@/lib/profile';
import {
  PROFILE_SECTIONS,
  PROMPT_CATEGORY,
  PROMPT_QUESTIONS,
  PROMPT_SLOTS,
  isPromptValue,
  type PromptSlot,
  type PromptValue,
  type SectionId,
} from '@/lib/profileSections';
import { getStoredTheme, setPreferredTheme, type Theme } from '@/lib/theme';

/* FR001/FR002/FR003/FR005 · UX11 "Profile edit hub" — v3, built from
 * researched reference patterns rather than invented ones:
 *
 *   • Photo grid, up to six, main photo large — Hinge and Bumble both open
 *     their profile editor on a six-slot photo grid.
 *   • Prompts placed between photos and sections, not in one block — the
 *     way Hinge interleaves them through a profile, so a person can add one
 *     wherever it fits.
 *   • Edit / Preview toggle — Hinge's editor has exactly this. Mangaly's
 *     twist: two Preview lenses, "Before you connect" (the anonymized
 *     snippet a stranger actually sees) and "After you connect" (photos,
 *     prompts and full biodata), so the privacy promise is visible.
 *   • Value badges showing the real answer — Bumble's "My basics", Hinge's
 *     vitals — instead of filled/empty ticks.
 *   • Biodata section order familiar from Shaadi.com and Jeevansathi.
 *   • A "Next up" card (Bumble's "Complete my profile") and every edit in a
 *     bottom sheet: single-choice saves on tap, text/range fields on Save.
 */

const THEME_OPTIONS: Theme[] = ['light', 'dark', 'system'];

// Partner age range bounds for the slider (Baymard: pair a range slider with
// exact number fields; the slider sets an approximate range fast, the fields
// allow precision).
const AGE_MIN = 18;
const AGE_MAX = 70;

// Autocomplete suggestions for occupation — typing is faster than a long
// dropdown on mobile, and suggestions keep common answers consistent so
// matching isn't split across spellings. Free text still accepted.
const OCCUPATION_SUGGESTIONS = [
  'Software Engineer',
  'Doctor',
  'Teacher',
  'Professor',
  'Chartered Accountant',
  'Lawyer',
  'Civil Engineer',
  'Architect',
  'Banker',
  'Business Owner',
  'Entrepreneur',
  'Government Employee',
  'Civil Services (IAS/IPS)',
  'Defence Services',
  'Nurse',
  'Pharmacist',
  'Product Manager',
  'Data Scientist',
  'Designer',
  'Consultant',
];

// Interest badges instead of a blank hobbies box (Bumble: pick up to five from
// a catalogue). Custom entries are still allowed.
const INTEREST_TAGS = [
  'cooking',
  'street_food',
  'trekking',
  'road_trips',
  'pilgrimages',
  'beaches',
  'cricket',
  'badminton',
  'yoga',
  'fitness',
  'music',
  'classical_dance',
  'movies',
  'reading',
  'photography',
  'gardening',
  'volunteering',
  'spirituality',
  'board_games',
  'art',
];
const MAX_TAGS = 5;

function toTagKey(raw: string): string {
  const trimmed = raw.trim();
  const key = trimmed.toLowerCase().replace(/[\s&-]+/g, '_');
  return INTEREST_TAGS.includes(key) ? key : trimmed;
}

// Also accepts older comma-separated text answers.
function parseTags(value: unknown): string[] {
  const parts: unknown[] = Array.isArray(value) ? value : typeof value === 'string' ? value.split(',') : [];
  const tags = parts.filter((p): p is string => typeof p === 'string' && p.trim() !== '').map(toTagKey);
  return [...new Set(tags)];
}

type Values = Record<string, CategoryAttributes>;
type Status = 'answered' | 'hidden' | 'empty';
type Draft = Record<string, { state: AttributeState; value: unknown }>;
type Sheet =
  | { kind: 'category'; category: string }
  | { kind: 'prompt'; slot: PromptSlot }
  | { kind: 'photo'; id: string }
  | { kind: 'settings' }
  | null;
type PageState =
  | { phase: 'checking' }
  | { phase: 'ready'; profile: Profile; values: Values; photos: Photo[] };

type EditBlock = { kind: 'photos' } | { kind: 'prompt'; slot: PromptSlot } | { kind: 'section'; id: SectionId };
const EDIT_LAYOUT: EditBlock[] = [
  { kind: 'photos' },
  { kind: 'prompt', slot: 'prompt_1' },
  { kind: 'section', id: 'basics' },
  { kind: 'section', id: 'lifestyle' },
  { kind: 'prompt', slot: 'prompt_2' },
  { kind: 'section', id: 'family' },
  { kind: 'section', id: 'future' },
  { kind: 'prompt', slot: 'prompt_3' },
  { kind: 'section', id: 'partner' },
];

type PreviewBlock =
  | { kind: 'photo'; index: number }
  | { kind: 'identity' }
  | { kind: 'prompt'; slot: PromptSlot }
  | { kind: 'section'; id: SectionId };
const PREVIEW_LAYOUT: PreviewBlock[] = [
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
  { kind: 'section', id: 'partner' },
];

const ICON: Record<SectionId | 'photos', string> = {
  photos: 'M4 7h3l2-2h6l2 2h3v12H4z M12 10a3 3 0 1 0 0 6a3 3 0 1 0 0-6z',
  basics: 'M4 6h16v12H4z M8 10h4 M8 14h8',
  lifestyle: 'M12 3v2 M12 19v2 M3 12h2 M19 12h2 M12 8a4 4 0 1 0 0 8a4 4 0 1 0 0-8z',
  family:
    'M9 4.8a3.2 3.2 0 1 0 0 6.4a3.2 3.2 0 1 0 0-6.4z M3.5 19.5a5.5 5.5 0 0 1 11 0 M16 6.2a3 3 0 0 1 0 5.6 M17.5 19.5a5.4 5.4 0 0 0-2-4.2',
  future: 'M5 19L19 5 M9 5h10v10',
  partner: 'M12 20s-7-4.5-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.5-7 10-7 10z',
};

const ALL_CATEGORIES_IN_ORDER = PROFILE_SECTIONS.flatMap((s) => s.categories);

function ageFromDob(dob: string): number {
  const birth = new Date(dob);
  const now = new Date();
  let age = now.getFullYear() - birth.getFullYear();
  const hadBirthday =
    now.getMonth() > birth.getMonth() ||
    (now.getMonth() === birth.getMonth() && now.getDate() >= birth.getDate());
  if (!hadBirthday) age -= 1;
  return age;
}

function statusOf(values: Values, category: string): Status {
  const attrs = Object.values(values[category] ?? {});
  if (attrs.some((a) => a.state === 'value')) return 'answered';
  if (attrs.some((a) => a.state === 'declined')) return 'hidden';
  return 'empty';
}

function emptyValue(f: FieldDef): unknown {
  if (f.kind === 'ageRange') return { min: '', max: '' };
  return f.kind === 'tags' ? [] : '';
}

function buildDraft(def: CategoryDef, saved: CategoryAttributes): Draft {
  const next: Draft = {};
  for (const f of def.fields) {
    const row = saved[f.key];
    if (!row) next[f.key] = { state: 'unset', value: emptyValue(f) };
    else if (row.state !== 'value') next[f.key] = { state: row.state, value: emptyValue(f) };
    else next[f.key] = { state: 'value', value: f.kind === 'tags' ? parseTags(row.value) : row.value };
  }
  return next;
}

function promptAt(values: Values, slot: PromptSlot): PromptValue | null {
  const row = values[PROMPT_CATEGORY]?.[slot];
  return row && row.state === 'value' && isPromptValue(row.value) ? row.value : null;
}

function Icon({ d }: { d: string }) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d={d} fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default function ProfileHubPage() {
  const { t, i18n } = useTranslation(['common', 'profile', 'discover']);
  const router = useRouter();
  const [state, setState] = useState<PageState>({ phase: 'checking' });
  const [mode, setMode] = useState<'edit' | 'preview'>('edit');
  const [lens, setLens] = useState<'before' | 'after'>('after');
  // 'system' on first render so server and client markup agree; corrected
  // from localStorage after mount.
  const [theme, setTheme] = useState<Theme>('system');
  const [confirmLogout, setConfirmLogout] = useState(false);
  const [sheet, setSheet] = useState<Sheet>(null);
  const [draft, setDraft] = useState<Draft>({});
  const [promptDraft, setPromptDraft] = useState<PromptValue>({ q: '', a: '' });
  const [saving, setSaving] = useState(false);
  const [sheetError, setSheetError] = useState<string | null>(null);
  const [tagInput, setTagInput] = useState('');
  const [uploading, setUploading] = useState(false);
  const [photoError, setPhotoError] = useState<string | null>(null);
  const [fileInputKey, setFileInputKey] = useState(0);
  const fileRef = useRef<HTMLInputElement>(null);
  const [dragId, setDragId] = useState<string | null>(null);
  const [dropIndex, setDropIndex] = useState<number | null>(null);
  const pressTimer = useRef<number | null>(null);
  const pressStart = useRef<{ x: number; y: number } | null>(null);
  const suppressClick = useRef(false);

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    setTheme(getStoredTheme());
  }, []);
  /* eslint-enable react-hooks/set-state-in-effect */

  useEffect(() => {
    let active = true;
    (async () => {
      const session: Session | null = await getSession();
      if (!active) return;
      if (!session) {
        router.replace('/login');
        return;
      }
      const profile = await getOwnProfile();
      if (!active) return;
      if (!profile) {
        router.replace('/profile/create');
        return;
      }
      const [values, photos] = await Promise.all([getAllAttributeValues(), listPhotos()]);
      if (!active) return;
      setState({ phase: 'ready', profile, values, photos });
      // Deep link from the completeness screen: /me?edit=<category> opens that sheet.
      const editDef = findCategory(new URLSearchParams(window.location.search).get('edit') ?? '');
      if (editDef) {
        setDraft(buildDraft(editDef, values[editDef.category] ?? {}));
        setSheet({ kind: 'category', category: editDef.category });
        window.history.replaceState(null, '', '/me');
      }
    })();
    return () => {
      active = false;
    };
  }, [router]);

  useEffect(() => {
    if (!sheet) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setSheet(null);
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [sheet]);

  if (state.phase === 'checking') {
    return (
      <main className="screen screen--centered">
        <span className="brand-mark brand-mark--lg" aria-hidden="true">
          m
        </span>
        <p className="caption">{t('common:state.loading')}</p>
      </main>
    );
  }

  const { profile, values, photos } = state;

  function tagLabel(tag: string): string {
    return INTEREST_TAGS.includes(tag) ? t(`profile:tag.${tag}`) : tag;
  }

  function formatField(field: FieldDef, value: AttributeValue): string | null {
    if (value === null || value === undefined || value === '') return null;
    if (field.kind === 'select') return t(`profile:option.${field.key}.${String(value)}`);
    if (field.kind === 'tags') {
      const tags = parseTags(value);
      return tags.length ? tags.map(tagLabel).join(', ') : null;
    }
    if (field.kind === 'ageRange' && typeof value === 'object') {
      const { min, max } = value as { min?: number | null; max?: number | null };
      if (!min && !max) return null;
      return t('profile:hub.ageRange', { min: min ?? '–', max: max ?? '–' });
    }
    return String(value);
  }

  function summaryOf(def: CategoryDef): string | null {
    const attrs = values[def.category] ?? {};
    const parts = def.fields
      .map((f) => (attrs[f.key]?.state === 'value' ? formatField(f, attrs[f.key].value) : null))
      .filter((p): p is string => !!p);
    return parts.length ? parts.join(' · ') : null;
  }

  function applyLocal(category: string, payload: Record<string, { state: AttributeState; value?: AttributeValue }>) {
    setState((prev) => {
      if (prev.phase !== 'ready') return prev;
      const merged: CategoryAttributes = { ...(prev.values[category] ?? {}) };
      for (const [key, entry] of Object.entries(payload)) {
        merged[key] = { state: entry.state, value: entry.state === 'value' ? (entry.value ?? null) : null };
      }
      return { ...prev, values: { ...prev.values, [category]: merged } };
    });
  }

  async function persist(category: string, payload: Record<string, { state: AttributeState; value?: AttributeValue }>) {
    setSaving(true);
    setSheetError(null);
    const outcome = await updateCategoryAttributes(category, payload);
    setSaving(false);
    if (!outcome.ok) {
      setSheetError(t(outcome.kind === 'network' ? 'profile:error.network' : 'profile:editor.saveError'));
      return;
    }
    applyLocal(category, payload);
    setSheet(null);
  }

  async function refreshPhotos() {
    const next = await listPhotos();
    setState((prev) =>
      prev.phase !== 'ready'
        ? prev
        : {
            ...prev,
            photos: next,
            profile: { ...prev.profile, photo_url: next.find((p) => p.is_primary)?.url ?? prev.profile.photo_url },
          }
    );
  }

  async function onFileChosen(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    setFileInputKey((k) => k + 1);
    if (!file) return;
    setUploading(true);
    setPhotoError(null);
    const outcome = await uploadPhoto(file);
    setUploading(false);
    if (!outcome.ok) {
      setPhotoError(outcome.message ?? t('profile:error.network'));
      return;
    }
    await refreshPhotos();
  }

  async function onPhotoAction(action: 'main' | 'remove', id: string) {
    setSaving(true);
    setSheetError(null);
    const outcome = action === 'main' ? await setPrimaryPhoto(id) : await deletePhoto(id);
    setSaving(false);
    if (!outcome.ok) {
      setSheetError(outcome.message ?? t('profile:editor.saveError'));
      return;
    }
    await refreshPhotos();
    setSheet(null);
  }

  async function commitOrder(next: Photo[]) {
    setState((prev) =>
      prev.phase !== 'ready'
        ? prev
        : {
            ...prev,
            photos: next.map((p, i) => ({ ...p, is_primary: i === 0 })),
            profile: { ...prev.profile, photo_url: next[0]?.url ?? prev.profile.photo_url },
          }
    );
    const outcome = await reorderPhotos(next.map((p) => p.id));
    if (!outcome.ok) {
      setPhotoError(outcome.message ?? t('profile:editor.saveError'));
      await refreshPhotos();
    }
  }

  function movePhoto(from: number, to: number) {
    if (from < 0 || to < 0 || to >= photos.length || from === to) return;
    const next = [...photos];
    const [moved] = next.splice(from, 1);
    next.splice(to, 0, moved);
    void commitOrder(next);
  }

  // Long-press (350 ms) then drag to reorder — Bumble's pattern. Moving more
  // than 8 px before the press completes is treated as a scroll and cancels
  // it; the photo sheet's Move buttons are the non-drag alternative.
  function clearPress() {
    if (pressTimer.current !== null) window.clearTimeout(pressTimer.current);
    pressTimer.current = null;
    pressStart.current = null;
  }

  function onPhotoPointerDown(e: React.PointerEvent<HTMLButtonElement>, id: string) {
    // A finished drag never produces a click, so the suppression flag from
    // the previous gesture must be cleared here — otherwise the first real
    // tap after any reorder is silently swallowed (found live).
    suppressClick.current = false;
    pressStart.current = { x: e.clientX, y: e.clientY };
    const target = e.currentTarget;
    const pointerId = e.pointerId;
    pressTimer.current = window.setTimeout(() => {
      suppressClick.current = true;
      setDragId(id);
      setDropIndex(photos.findIndex((p) => p.id === id));
      try {
        target.setPointerCapture(pointerId);
      } catch {
        // The pointer may already be released or cancelled; the drag still
        // tracks pointermove events delivered to the slot itself.
      }
    }, 350);
  }

  function onPhotoPointerMove(e: React.PointerEvent<HTMLButtonElement>) {
    if (!dragId) {
      const start = pressStart.current;
      if (start && Math.hypot(e.clientX - start.x, e.clientY - start.y) > 8) clearPress();
      return;
    }
    const over = document.elementFromPoint(e.clientX, e.clientY)?.closest<HTMLElement>('[data-photo-index]');
    if (over) setDropIndex(Math.min(Number(over.dataset.photoIndex), photos.length - 1));
  }

  function onPhotoPointerUp() {
    clearPress();
    if (dragId !== null && dropIndex !== null) {
      movePhoto(photos.findIndex((p) => p.id === dragId), dropIndex);
    }
    setDragId(null);
    setDropIndex(null);
  }

  function openCategory(category: string) {
    const def = findCategory(category);
    if (!def) return;
    setDraft(buildDraft(def, values[category] ?? {}));
    setTagInput('');
    setSheetError(null);
    setSheet({ kind: 'category', category });
  }

  function openPrompt(slot: PromptSlot) {
    setPromptDraft(promptAt(values, slot) ?? { q: '', a: '' });
    setSheetError(null);
    setSheet({ kind: 'prompt', slot });
  }

  function saveDraft(def: CategoryDef) {
    const payload: Record<string, { state: AttributeState; value?: AttributeValue }> = {};
    for (const f of def.fields) {
      const entry = draft[f.key];
      if (!entry || entry.state !== 'value') continue;
      if (f.kind === 'ageRange') {
        const v = (entry.value ?? {}) as { min?: unknown; max?: unknown };
        const min = Number(v.min) || null;
        const max = Number(v.max) || null;
        if (min || max) payload[f.key] = { state: 'value', value: { min, max } };
      } else if (f.kind === 'tags') {
        const tags = parseTags(entry.value);
        if (tags.length) payload[f.key] = { state: 'value', value: tags };
      } else if (typeof entry.value === 'string' && entry.value.trim()) {
        payload[f.key] = { state: 'value', value: entry.value.trim() };
      }
    }
    if (Object.keys(payload).length === 0) {
      setSheet(null);
      return;
    }
    void persist(def.category, payload);
  }

  function hideCategory(def: CategoryDef) {
    void persist(
      def.category,
      Object.fromEntries(def.fields.map((f) => [f.key, { state: 'declined' as const, value: null }]))
    );
  }

  const answeredCount = ALL_CATEGORIES_IN_ORDER.filter((c) => statusOf(values, c) !== 'empty').length;
  const total = ALL_CATEGORIES_IN_ORDER.length;
  const pct = Math.round((answeredCount / total) * 100);
  const nextEmpty = ALL_CATEGORIES_IN_ORDER.find((c) => statusOf(values, c) === 'empty');
  const meta = [t('profile:hub.ageYears', { age: ageFromDob(profile.date_of_birth) }), profile.city_locality]
    .filter(Boolean)
    .join(' · ');

  const sheetDef = sheet?.kind === 'category' ? findCategory(sheet.category) : undefined;
  const singleSelect = !!sheetDef && sheetDef.fields.length === 1 && sheetDef.fields[0].kind === 'select';
  const usedQuestions = PROMPT_SLOTS.filter((s) => sheet?.kind !== 'prompt' || s !== sheet.slot)
    .map((s) => promptAt(values, s)?.q)
    .filter(Boolean);
  const sheetPhoto = sheet?.kind === 'photo' ? photos.find((p) => p.id === sheet.id) : undefined;

  function renderPhotos() {
    return (
      <section key="photos" className="card section-card" aria-label={t('profile:hub.photos.title')}>
        <div className="section-card__head">
          <span className="section-card__icon">
            <Icon d={ICON.photos} />
          </span>
          <h2 className="h2 section-card__title">{t('profile:hub.photos.title')}</h2>
          <span className="section-card__count">{photos.length}/6</span>
        </div>
        <div className="photo-grid">
          {Array.from({ length: 6 }, (_, i) => {
            const photo = photos[i];
            if (photo) {
              return (
                <button
                  key={photo.id}
                  type="button"
                  data-photo-index={i}
                  className={`photo-slot${i === 0 ? ' photo-slot--main' : ''}${dragId === photo.id ? ' is-dragging' : ''}${dragId && dropIndex === i && dragId !== photo.id ? ' is-drop-target' : ''}`}
                  aria-label={`${t('profile:hub.photos.title')} ${i + 1}${photo.is_primary ? ` · ${t('profile:hub.photos.main')}` : ''}`}
                  onPointerDown={(e) => onPhotoPointerDown(e, photo.id)}
                  onPointerMove={onPhotoPointerMove}
                  onPointerUp={onPhotoPointerUp}
                  onPointerCancel={onPhotoPointerUp}
                  onContextMenu={(e) => e.preventDefault()}
                  onClick={() => {
                    if (suppressClick.current) {
                      suppressClick.current = false;
                      return;
                    }
                    setSheetError(null);
                    setSheet({ kind: 'photo', id: photo.id });
                  }}
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={resolveMediaUrl(photo.url) ?? ''} alt="" />
                  {photo.is_primary && <span className="photo-slot__badge">{t('profile:hub.photos.main')}</span>}
                </button>
              );
            }
            const isNext = i === photos.length;
            return (
              <button
                key={`empty-${i}`}
                type="button"
                className={`photo-slot photo-slot--empty${i === 0 ? ' photo-slot--main' : ''}`}
                aria-label={t('profile:hub.photos.add')}
                disabled={!isNext || uploading}
                onClick={() => fileRef.current?.click()}
              >
                {isNext && uploading ? (
                  <span className="caption">{t('profile:hub.photos.uploading')}</span>
                ) : (
                  <span aria-hidden="true">+</span>
                )}
              </button>
            );
          })}
        </div>
        <p className="caption">
          {t('profile:hub.photos.hint')}
          {photos.length > 1 ? ` ${t('profile:hub.photosReorderHint')}` : ''}
        </p>
        {photoError && (
          <p className="form__error" role="status">
            {photoError}
          </p>
        )}
        <input
          key={fileInputKey}
          ref={fileRef}
          type="file"
          name="photo"
          accept="image/jpeg,image/png,image/webp"
          hidden
          onChange={onFileChosen}
        />
      </section>
    );
  }

  function renderPromptEdit(slot: PromptSlot) {
    const p = promptAt(values, slot);
    return p ? (
      <button key={slot} type="button" className="prompt-card prompt-card--elevated" onClick={() => openPrompt(slot)}>
        <span className="prompt-card__q">{t(`profile:hub.prompts.q.${p.q}`)}</span>
        <span className="prompt-card__a">{p.a}</span>
      </button>
    ) : (
      <button key={slot} type="button" className="prompt-add" onClick={() => openPrompt(slot)}>
        <span className="prompt-add__title">+ {t('profile:hub.prompts.add')}</span>
        <span className="caption">{t('profile:hub.prompts.emptyHint')}</span>
      </button>
    );
  }

  function renderSectionEdit(id: SectionId) {
    const section = PROFILE_SECTIONS.find((s) => s.id === id);
    if (!section) return null;
    const done = section.categories.filter((c) => statusOf(values, c) !== 'empty').length;
    return (
      <section key={id} className="card section-card" aria-label={t(`profile:hub.section.${id}`)}>
        <div className="section-card__head">
          <span className="section-card__icon">
            <Icon d={ICON[id]} />
          </span>
          <h2 className="h2 section-card__title">{t(`profile:hub.section.${id}`)}</h2>
          <span className={`section-card__count${done === section.categories.length ? ' is-done' : ''}`}>
            {done}/{section.categories.length}
          </span>
        </div>
        <div className="vitals">
          {section.categories.map((category, i) => {
            const def = findCategory(category);
            if (!def) return null;
            const status = statusOf(values, category);
            const wide = section.categories.length % 2 === 1 && i === section.categories.length - 1;
            return (
              <button
                key={category}
                type="button"
                className={`vital vital--${status}${wide ? ' vital--wide' : ''}`}
                onClick={() => openCategory(category)}
              >
                <span className="vital__label">{t(`profile:hub.category.${category}`)}</span>
                <span className="vital__value">
                  {status === 'answered'
                    ? summaryOf(def)
                    : status === 'hidden'
                      ? t('profile:hub.hidden')
                      : `+ ${t('profile:hub.add')}`}
                </span>
              </button>
            );
          })}
        </div>
        {id === 'partner' && <p className="caption">🔒 {t('profile:hub.partnerPrivate')}</p>}
      </section>
    );
  }

  function renderPreviewBlock(block: PreviewBlock, index: number) {
    if (block.kind === 'photo') {
      const photo = photos[block.index];
      if (!photo) return null;
      return (
        <div key={`photo-${index}`} className="preview-photo">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={resolveMediaUrl(photo.url) ?? ''} alt="" />
        </div>
      );
    }
    if (block.kind === 'identity') {
      return (
        <div key="identity" className="preview-identity">
          <span className="profile-hero__name">{profile.name}</span>
          <span className="caption">{meta}</span>
        </div>
      );
    }
    if (block.kind === 'prompt') {
      const p = promptAt(values, block.slot);
      if (!p) return null;
      return (
        <div key={block.slot} className="prompt-card prompt-card--elevated">
          <span className="prompt-card__q">{t(`profile:hub.prompts.q.${p.q}`)}</span>
          <span className="prompt-card__a">{p.a}</span>
        </div>
      );
    }
    // Partner preferences are private matching filters, never shown to
    // anyone else — Hinge treats preferences the same way.
    if (block.id === 'partner') return null;
    const section = PROFILE_SECTIONS.find((s) => s.id === block.id);
    const rows = (section?.categories ?? [])
      .map((c) => findCategory(c))
      .filter((d): d is CategoryDef => !!d && statusOf(values, d.category) === 'answered');
    if (rows.length === 0) return null;
    return (
      <div key={block.id} className="card preview-section">
        <div className="label">{t(`profile:hub.section.${block.id}`)}</div>
        <dl className="biodata">
          {rows.map((d) => (
            <div key={d.category} className="biodata__row">
              <dt>{t(`profile:hub.category.${d.category}`)}</dt>
              <dd>{summaryOf(d)}</dd>
            </div>
          ))}
        </dl>
      </div>
    );
  }

  return (
    <>
      <header className="topbar">
        <h1>{t('profile:hub.title')}</h1>
        <div style={{ display: 'flex', gap: 4 }}>
          <button
            type="button"
            className="icon-btn"
            aria-label={t('common:settings.title')}
            aria-haspopup="dialog"
            onClick={() => {
              setConfirmLogout(false);
              setSheet({ kind: 'settings' });
            }}
          >
            <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
              <path
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z M19.4 13.5a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V19.4a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-1.08-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H4.6a2 2 0 1 1 0-4h.09a1.65 1.65 0 0 0 1.51-1.08 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H10.5a1.65 1.65 0 0 0 1-1.51V4.6a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V10.5a1.65 1.65 0 0 0 1.51 1H19.4a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1Z"
              />
            </svg>
          </button>
        </div>
      </header>

      <main className="screen">
        <div className="segmented" role="tablist" aria-label={t('profile:hub.title')}>
          {(['edit', 'preview'] as const).map((m) => (
            <button
              key={m}
              type="button"
              role="tab"
              aria-selected={mode === m}
              className={`segmented__opt${mode === m ? ' is-active' : ''}`}
              onClick={() => setMode(m)}
            >
              {t(m === 'edit' ? 'profile:hub.tabEdit' : 'profile:hub.tabPreview')}
            </button>
          ))}
        </div>

        {mode === 'edit' ? (
          <>
            <div className="card profile-hero">
              <Link
                href="/me/completeness"
                className="hero-ring"
                aria-label={t('profile:hub.completenessCta')}
                style={{ background: `conic-gradient(var(--saffron-500) ${pct}%, var(--surface-sunken) 0)` }}
              >
                <Avatar photoUrl={profile.photo_url} name={profile.name} size={80} />
              </Link>
              <div className="profile-hero__body">
                <span className="profile-hero__name">{profile.name}</span>
                <span className="caption">{meta}</span>
                <span className="profile-hero__answered">
                  {t('profile:hub.answered', { done: answeredCount, total })}
                </span>
              </div>
            </div>

            {nextEmpty && (
              <button type="button" className="next-step" onClick={() => openCategory(nextEmpty)}>
                <span className="next-step__dot" aria-hidden="true">
                  +
                </span>
                <span className="next-step__body">
                  <span className="caption">{t('profile:hub.nextUp')}</span>
                  <span className="next-step__title">{t(`profile:hub.category.${nextEmpty}`)}</span>
                </span>
                <span className="caption">{t('profile:hub.nextHint')}</span>
              </button>
            )}

            {EDIT_LAYOUT.map((block) =>
              block.kind === 'photos'
                ? renderPhotos()
                : block.kind === 'prompt'
                  ? renderPromptEdit(block.slot)
                  : renderSectionEdit(block.id)
            )}
          </>
        ) : (
          <>
            <div className="segmented" role="tablist" aria-label={t('profile:hub.tabPreview')}>
              {(['before', 'after'] as const).map((l) => (
                <button
                  key={l}
                  type="button"
                  role="tab"
                  aria-selected={lens === l}
                  className={`segmented__opt${lens === l ? ' is-active' : ''}`}
                  onClick={() => setLens(l)}
                >
                  {t(`profile:hub.preview.${l}`)}
                </button>
              ))}
            </div>

            {lens === 'before' ? (
              <>
                <div className="card preview-card">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <Avatar anonymized size={56} />
                    <div style={{ minWidth: 0 }}>
                      <span className="body-lg" style={{ fontWeight: 600 }}>
                        {[findCategory('education'), findCategory('profession')]
                          .map((d) => (d ? summaryOf(d) : null))
                          .filter(Boolean)
                          .join(' · ') || t('profile:hub.preview.noBasics')}
                      </span>
                      <p className="caption" style={{ margin: '2px 0 0' }}>
                        {profile.city_locality}
                      </p>
                      <p className="caption" style={{ margin: '2px 0 0' }}>
                        🔒 {t('discover:identityProtected')}
                      </p>
                    </div>
                  </div>
                </div>
                <p className="caption">{t('profile:hub.preview.beforeNote')}</p>
              </>
            ) : (
              <>
                {PREVIEW_LAYOUT.map((block, i) => renderPreviewBlock(block, i))}
                <p className="caption">{t('profile:hub.preview.afterNote')}</p>
              </>
            )}
          </>
        )}
      </main>

      {sheet && (
        <div className="sheet-backdrop" onClick={() => setSheet(null)}>
          <div
            className="sheet"
            role="dialog"
            aria-modal="true"
            aria-labelledby="sheet-title"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="sheet__handle" aria-hidden="true" />
            <div className="sheet__head">
              <h2 id="sheet-title" className="h2">
                {sheet.kind === 'category'
                  ? t(`profile:hub.category.${sheet.category}`)
                  : sheet.kind === 'photo'
                    ? t('profile:hub.photos.title')
                    : sheet.kind === 'settings'
                      ? t('common:settings.title')
                      : t('profile:hub.section.prompts')}
              </h2>
              <button
                type="button"
                className="icon-btn"
                aria-label={t('common:action.cancel')}
                onClick={() => setSheet(null)}
              >
                ✕
              </button>
            </div>

            {sheet.kind === 'settings' && (
              <>
                <div className="label">{t('common:settings.language')}</div>
                <div className="segmented segmented--3" role="radiogroup">
                  {SUPPORTED_LANGUAGES.map((lang) => (
                    <button
                      key={lang}
                      type="button"
                      className={`segmented__opt${i18n.language === lang ? ' is-active' : ''}`}
                      aria-pressed={i18n.language === lang}
                      onClick={() => {
                        void i18n.changeLanguage(lang as Language);
                        setPreferredLanguage(lang as Language);
                      }}
                    >
                      {t(`common:language.${lang}`)}
                    </button>
                  ))}
                </div>
                <div className="label" style={{ marginTop: 16 }}>
                  {t('common:settings.theme')}
                </div>
                <div className="segmented segmented--3" role="radiogroup">
                  {THEME_OPTIONS.map((opt) => (
                    <button
                      key={opt}
                      type="button"
                      className={`segmented__opt${theme === opt ? ' is-active' : ''}`}
                      aria-pressed={theme === opt}
                      onClick={() => {
                        setTheme(opt);
                        setPreferredTheme(opt);
                      }}
                    >
                      {t(`common:settings.themeOption.${opt}`)}
                    </button>
                  ))}
                </div>
                <div className="sheet__stack" style={{ marginTop: 24 }}>
                  {confirmLogout ? (
                    <>
                      <p className="caption" style={{ margin: 0 }}>
                        {t('common:settings.logOutConfirm')}
                      </p>
                      <button
                        type="button"
                        className="sheet__danger"
                        onClick={() => void logOut().then(() => router.replace('/login'))}
                      >
                        {t('common:action.logOut')}
                      </button>
                      <button type="button" className="quick-pick__chip" onClick={() => setConfirmLogout(false)}>
                        {t('common:action.cancel')}
                      </button>
                    </>
                  ) : (
                    <button type="button" className="sheet__danger" onClick={() => setConfirmLogout(true)}>
                      {t('common:action.logOut')}
                    </button>
                  )}
                </div>
              </>
            )}

            {sheet.kind === 'photo' && sheetPhoto && (
              <>
                <div className="sheet__photo">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={resolveMediaUrl(sheetPhoto.url) ?? ''} alt="" />
                </div>
                <div className="sheet__stack">
                  <div className="sheet__row">
                    <button
                      type="button"
                      className="quick-pick__chip"
                      disabled={saving || photos.indexOf(sheetPhoto) === 0}
                      onClick={() => movePhoto(photos.indexOf(sheetPhoto), photos.indexOf(sheetPhoto) - 1)}
                    >
                      ← {t('profile:hub.photos.moveEarlier')}
                    </button>
                    <button
                      type="button"
                      className="quick-pick__chip"
                      disabled={saving || photos.indexOf(sheetPhoto) === photos.length - 1}
                      onClick={() => movePhoto(photos.indexOf(sheetPhoto), photos.indexOf(sheetPhoto) + 1)}
                    >
                      {t('profile:hub.photos.moveLater')} →
                    </button>
                  </div>
                  {!sheetPhoto.is_primary && (
                    <button
                      type="button"
                      className="cta"
                      disabled={saving}
                      onClick={() => void onPhotoAction('main', sheetPhoto.id)}
                    >
                      {t('profile:hub.photos.makeMain')}
                    </button>
                  )}
                  <button
                    type="button"
                    className="sheet__danger"
                    disabled={saving}
                    onClick={() => void onPhotoAction('remove', sheetPhoto.id)}
                  >
                    {t('profile:hub.photos.remove')}
                  </button>
                </div>
              </>
            )}

            {sheet.kind === 'category' && sheetDef && (
              <>
                {sheetDef.fields.map((f) => {
                  const entry = draft[f.key];
                  return (
                    <div key={f.key} className="sheet__field">
                      {sheetDef.fields.length > 1 && <div className="label">{t(`profile:${f.labelKey}`)}</div>}
                      {f.kind === 'select' ? (
                        <div className="quick-pick__chips">
                          {(f.options ?? []).map((opt) => {
                            const active = entry?.state === 'value' && entry.value === opt;
                            return (
                              <button
                                key={opt}
                                type="button"
                                className={`quick-pick__chip${active ? ' quick-pick__chip--active' : ''}`}
                                disabled={saving}
                                onClick={() =>
                                  singleSelect
                                    ? void persist(sheetDef.category, { [f.key]: { state: 'value', value: opt } })
                                    : setDraft((d) => ({ ...d, [f.key]: { state: 'value', value: opt } }))
                                }
                              >
                                {t(`profile:option.${f.key}.${opt}`)}
                              </button>
                            );
                          })}
                        </div>
                      ) : f.kind === 'tags' ? (
                        (() => {
                          const chosen = parseTags(entry?.value);
                          const full = chosen.length >= MAX_TAGS;
                          const setTags = (next: string[]) =>
                            setDraft((d) => ({ ...d, [f.key]: { state: 'value', value: next } }));
                          const toggle = (tag: string) =>
                            setTags(chosen.includes(tag) ? chosen.filter((c) => c !== tag) : full ? chosen : [...chosen, tag]);
                          const addCustom = () => {
                            const tag = toTagKey(tagInput);
                            if (tag && !chosen.includes(tag) && !full) setTags([...chosen, tag]);
                            setTagInput('');
                          };
                          return (
                            <>
                              <div className="label">{t('profile:hub.tags.pick', { max: MAX_TAGS, count: chosen.length })}</div>
                              <div className="quick-pick__chips">
                                {[...INTEREST_TAGS, ...chosen.filter((c) => !INTEREST_TAGS.includes(c))].map((tag) => {
                                  const active = chosen.includes(tag);
                                  return (
                                    <button
                                      key={tag}
                                      type="button"
                                      aria-pressed={active}
                                      className={`quick-pick__chip${active ? ' quick-pick__chip--active' : ''}`}
                                      disabled={saving || (!active && full)}
                                      onClick={() => toggle(tag)}
                                    >
                                      {tagLabel(tag)}
                                    </button>
                                  );
                                })}
                              </div>
                              <div className="sheet__row sheet__row--add">
                                <input
                                  className="field__input"
                                  type="text"
                                  name="custom-interest"
                                  maxLength={30}
                                  autoComplete="off"
                                  aria-label={t('profile:hub.tags.custom')}
                                  placeholder={t('profile:hub.tags.custom')}
                                  value={tagInput}
                                  disabled={full}
                                  onChange={(e) => setTagInput(e.target.value)}
                                  onKeyDown={(e) => {
                                    if (e.key === 'Enter') {
                                      e.preventDefault();
                                      addCustom();
                                    }
                                  }}
                                />
                                <button
                                  type="button"
                                  className="quick-pick__chip"
                                  disabled={full || !tagInput.trim()}
                                  onClick={addCustom}
                                >
                                  {t('profile:hub.tags.addCustom')}
                                </button>
                              </div>
                            </>
                          );
                        })()
                      ) : f.kind === 'ageRange' ? (
                        <>
                          {(() => {
                            const rv = (entry?.value as Record<string, unknown> | undefined) ?? {};
                            const lo = Number(rv.min) || AGE_MIN;
                            const hi = Number(rv.max) || AGE_MAX;
                            const pct = (n: number) => ((n - AGE_MIN) / (AGE_MAX - AGE_MIN)) * 100;
                            return (
                              <div className="range-dual">
                                <div
                                  className="range-dual__track"
                                  style={{
                                    background: `linear-gradient(to right, var(--surface-sunken) ${pct(lo)}%, var(--saffron-500) ${pct(lo)}%, var(--saffron-500) ${pct(hi)}%, var(--surface-sunken) ${pct(hi)}%)`,
                                  }}
                                />
                                {(['min', 'max'] as const).map((bound) => (
                                  <input
                                    key={bound}
                                    type="range"
                                    min={AGE_MIN}
                                    max={AGE_MAX}
                                    step={1}
                                    name={`${f.key}-${bound}-slider`}
                                    aria-label={t(bound === 'min' ? 'profile:editor.ageRangeFrom' : 'profile:editor.ageRangeTo')}
                                    value={bound === 'min' ? lo : hi}
                                    onChange={(e) => {
                                      const next = Number(e.target.value);
                                      setDraft((d) => {
                                        const prev = (d[f.key]?.value as Record<string, unknown>) ?? {};
                                        const otherKey = bound === 'min' ? 'max' : 'min';
                                        const other = Number(prev[otherKey]) || (bound === 'min' ? AGE_MAX : AGE_MIN);
                                        const clamped = bound === 'min' ? Math.min(next, other) : Math.max(next, other);
                                        return {
                                          ...d,
                                          [f.key]: { state: 'value', value: { ...prev, [otherKey]: other, [bound]: clamped } },
                                        };
                                      });
                                    }}
                                  />
                                ))}
                              </div>
                            );
                          })()}
                        <div className="age-range">
                          {(['min', 'max'] as const).map((bound, i) => (
                            <span key={bound} style={{ display: 'contents' }}>
                              {i === 1 && <span aria-hidden="true">–</span>}
                              <input
                                className="field__input"
                                type="number"
                                inputMode="numeric"
                                name={`${f.key}-${bound}`}
                                aria-label={t(bound === 'min' ? 'profile:editor.ageRangeFrom' : 'profile:editor.ageRangeTo')}
                                placeholder={t(bound === 'min' ? 'profile:editor.ageRangeFrom' : 'profile:editor.ageRangeTo')}
                                value={String((entry?.value as Record<string, unknown> | undefined)?.[bound] ?? '')}
                                onChange={(e) =>
                                  setDraft((d) => ({
                                    ...d,
                                    [f.key]: {
                                      state: 'value',
                                      value: {
                                        ...((d[f.key]?.value as Record<string, unknown>) ?? {}),
                                        [bound]: e.target.value,
                                      },
                                    },
                                  }))
                                }
                              />
                            </span>
                          ))}
                        </div>
                        </>
                      ) : (
                        <input
                          className="field__input"
                          type="text"
                          name={f.key}
                          list={f.key === 'occupation' ? 'occupation-suggestions' : undefined}
                          autoComplete="off"
                          aria-label={t(`profile:${f.labelKey}`)}
                          placeholder={t(`profile:${f.labelKey}`)}
                          value={typeof entry?.value === 'string' ? entry.value : ''}
                          onChange={(e) =>
                            setDraft((d) => ({ ...d, [f.key]: { state: 'value', value: e.target.value } }))
                          }
                        />
                      )}
                    </div>
                  );
                })}
                <datalist id="occupation-suggestions">
                  {OCCUPATION_SUGGESTIONS.map((o) => (
                    <option key={o} value={o} />
                  ))}
                </datalist>
                <div className="sheet__actions">
                  <button
                    type="button"
                    className="quick-pick__chip quick-pick__chip--decline"
                    disabled={saving}
                    onClick={() => hideCategory(sheetDef)}
                  >
                    {t('profile:editor.decline')}
                  </button>
                  {!singleSelect && (
                    <button
                      type="button"
                      className="cta sheet__save"
                      disabled={saving}
                      onClick={() => saveDraft(sheetDef)}
                    >
                      {saving ? t('profile:editor.saving') : t('profile:editor.save')}
                    </button>
                  )}
                </div>
              </>
            )}

            {sheet.kind === 'prompt' && (
              <>
                <div className="label">{t('profile:hub.prompts.pick')}</div>
                <div className="quick-pick__chips">
                  {PROMPT_QUESTIONS.map((q) => (
                    <button
                      key={q}
                      type="button"
                      className={`quick-pick__chip${promptDraft.q === q ? ' quick-pick__chip--active' : ''}`}
                      disabled={usedQuestions.includes(q)}
                      onClick={() => setPromptDraft((p) => ({ ...p, q }))}
                    >
                      {t(`profile:hub.prompts.q.${q}`)}
                    </button>
                  ))}
                </div>
                {promptDraft.q && (
                  <div className="sheet__field">
                    <label className="label" htmlFor="prompt-answer">
                      {t('profile:hub.prompts.answer')}
                    </label>
                    <textarea
                      id="prompt-answer"
                      className="field__input prompt-textarea"
                      maxLength={150}
                      value={promptDraft.a}
                      onChange={(e) => setPromptDraft((p) => ({ ...p, a: e.target.value }))}
                    />
                    <span className="caption">{promptDraft.a.length}/150</span>
                  </div>
                )}
                <div className="sheet__actions">
                  {promptAt(values, sheet.slot) ? (
                    <button
                      type="button"
                      className="quick-pick__chip quick-pick__chip--decline"
                      disabled={saving}
                      onClick={() => void persist(PROMPT_CATEGORY, { [sheet.slot]: { state: 'declined', value: null } })}
                    >
                      {t('profile:hub.prompts.remove')}
                    </button>
                  ) : (
                    <span />
                  )}
                  <button
                    type="button"
                    className="cta sheet__save"
                    disabled={saving || !promptDraft.q || !promptDraft.a.trim()}
                    onClick={() =>
                      void persist(PROMPT_CATEGORY, {
                        [sheet.slot]: { state: 'value', value: { q: promptDraft.q, a: promptDraft.a.trim() } },
                      })
                    }
                  >
                    {saving ? t('profile:editor.saving') : t('profile:editor.save')}
                  </button>
                </div>
              </>
            )}

            {sheetError && (
              <p className="form__error" role="status">
                {sheetError}
              </p>
            )}
          </div>
        </div>
      )}
    </>
  );
}

import type { FieldDef } from '@/lib/profileCategoryConfig';

type Translate = (key: string, options?: Record<string, unknown>) => string;

// Interest badges instead of a blank hobbies box (Bumble: pick up to five from
// a catalogue). Custom entries are still allowed.
export const INTEREST_TAGS = [
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
export const MAX_TAGS = 5;

export function toTagKey(raw: string): string {
  const trimmed = raw.trim();
  const key = trimmed.toLowerCase().replace(/[\s&-]+/g, '_');
  return INTEREST_TAGS.includes(key) ? key : trimmed;
}

// Also accepts older comma-separated text answers.
export function parseTags(value: unknown): string[] {
  const parts: unknown[] = Array.isArray(value) ? value : typeof value === 'string' ? value.split(',') : [];
  const tags = parts.filter((p): p is string => typeof p === 'string' && p.trim() !== '').map(toTagKey);
  return [...new Set(tags)];
}

export function tagLabel(t: Translate, tag: string): string {
  return INTEREST_TAGS.includes(tag) ? t(`profile:tag.${tag}`) : tag;
}

export function formatFieldValue(t: Translate, field: FieldDef, value: unknown): string | null {
  if (value === null || value === undefined || value === '') return null;
  if (field.kind === 'select') return t(`profile:option.${field.key}.${String(value)}`);
  if (field.kind === 'tags') {
    const tags = parseTags(value);
    return tags.length ? tags.map((tag) => tagLabel(t, tag)).join(', ') : null;
  }
  if (field.kind === 'ageRange' && typeof value === 'object') {
    const { min, max } = value as { min?: number | null; max?: number | null };
    if (!min && !max) return null;
    return t('profile:hub.ageRange', { min: min ?? '–', max: max ?? '–' });
  }
  return String(value);
}

/* Interests (FR001/FR003, redesigned 2026-10-06): optional, asked later, editable any time.
 * The API stores taxonomy tags and the member's own words as "other:<words>"; labels are shown in the
 * member's language from `interest.tag.<tag>` / `interest.group.<key>`, falling back to the API's English. */

import type { TFunction } from 'i18next';

export type TaxonomyGroup = { key?: string; group: string; interests: { tag: string; label: string; intent_category?: string }[] };
export type Taxonomy = TaxonomyGroup[];

export const OTHER_PREFIX = 'other:';
export const OTHER_MAX_CHARS = 40;
export const OTHER_MAX_COUNT = 5;

/** One emoji per broad group, so the picker reads at a glance (mockup C). */
export const GROUP_ICONS: Record<string, string> = {
  spiritual: '🙏', sports: '🏸', outdoors: '🥾', culture: '🎶', food: '🍛', learning: '📚', work: '💼', family: '👨‍👩‍👧', volunteering: '🤝',
};

export function isOwnInterest(tag: string): boolean {
  return tag.startsWith(OTHER_PREFIX);
}

/** A tag in the member's language: their own words as written, a taxonomy tag translated. */
export function interestLabel(t: TFunction, tag: string, fallback?: string): string {
  if (isOwnInterest(tag)) return tag.slice(OTHER_PREFIX.length);
  return t(`interest.tag.${tag}`, { defaultValue: fallback ?? tag });
}

export function groupLabel(t: TFunction, g: TaxonomyGroup): string {
  return g.key ? t(`interest.group.${g.key}`, { defaultValue: g.group }) : g.group;
}

/* [DEC-V1-031] The AI matchmaker: the family's own words about the partner
 * they want, what the engine understood from them (each point with an
 * importance 1–10, where 10 means it must be met), and the six 1–10 scales —
 * how the candidate rates themselves and what they want in a partner.
 *
 * Everything here is private: it only ever feeds the matching engine. The
 * engine's own 1–10 score for a pair never reaches the browser; Discover
 * shows a word ("Strong match") and the factual reasons instead. */

import { getJson, sendJson, type Outcome } from './api';

export const SCALES = ['faith', 'tradition', 'family_closeness', 'career', 'social', 'active'] as const;
export type Scale = (typeof SCALES)[number];

export type UnderstoodItem = {
  field: string;
  importance: number;
  values?: string[];
  min?: number | null;
  max?: number | null;
  /** The few words the point came from, so the family sees why. */
  quote?: string;
};

export type ScaleWish = { want: number; importance: number };

export type Brief = {
  text: string;
  items: UnderstoodItem[];
  partner_scales: Partial<Record<Scale, ScaleWish>>;
  self_scales: Partial<Record<Scale, number>> | null;
  /** False while a parent edits a profile they made: only the candidate rates themselves. */
  can_rate_self: boolean;
  ai_available: boolean;
  /** How much each theme matters, 1–10; unset themes are absent. */
  priorities: Partial<Record<Theme, number>>;
  /** Nothing said yet: starting points read from the profile itself. */
  suggested: UnderstoodItem[];
  /** The candidate's own values each theme compares with. */
  theme_facts: Partial<Record<Theme, string[]>>;
};

/** [Owner, 2026-09-28] "What matters to you" — each theme becomes a
 *  "like us" wish built from the candidate's own profile, so nothing is
 *  asked twice. Horoscope orders Discover's rows. */
export const THEMES = ['horoscope', 'roots', 'near', 'life', 'family_view', 'education'] as const;
export type Theme = (typeof THEMES)[number];

export type Understanding = {
  items: UnderstoodItem[];
  scales: Partial<Record<Scale, ScaleWish>>;
  source: 'ai' | 'basic';
};

/** Fields with a fixed set of answers, and those answers, in display order. */
export const ITEM_OPTIONS: Record<string, string[]> = {
  relocation: ['yes', 'open_to_discussion', 'no'],
  diet: ['vegetarian', 'eggetarian', 'vegan', 'non_vegetarian'],
  smoking: ['never', 'occasionally', 'regularly'],
  drinking: ['never', 'occasionally', 'regularly'],
  education: ['high_school', 'bachelors', 'masters', 'doctorate'],
  income_band: ['under_5', '5_10', '10_20', '20_40', '40_plus'],
  mother_tongue: ['telugu', 'tamil', 'kannada', 'hindi', 'punjabi', 'marathi', 'gujarati', 'english', 'other'],
  sub_community: ['khatri', 'arora', 'sood', 'bhatia', 'other'],
  family_type: ['joint', 'nuclear', 'extended'],
  family_values: ['traditional', 'moderate', 'liberal'],
  manglik: ['yes', 'no', 'partial'],
};

/** Every point a family can add by hand, in the order a biodata is read. */
export const ITEM_FIELDS = [
  'age',
  'height_cm',
  'locality',
  'relocation',
  'mother_tongue',
  'sub_community',
  'education',
  'income_band',
  'diet',
  'smoking',
  'drinking',
  'family_type',
  'family_values',
  'manglik',
  'hobbies',
] as const;

export function getBrief(): Promise<Brief | null> {
  return getJson<Brief>('/profile/matchmaker/brief');
}

export function understand(text: string): Promise<Outcome<Understanding>> {
  return sendJson<Understanding>('POST', '/profile/matchmaker/understand', { text });
}

export function saveBrief(brief: {
  text: string;
  items: UnderstoodItem[];
  partner_scales: Partial<Record<Scale, ScaleWish>>;
  self_scales?: Partial<Record<Scale, number>> | null;
  priorities?: Partial<Record<Theme, number>>;
}): Promise<Outcome<null>> {
  return sendJson<null>('PATCH', '/profile/matchmaker/brief', brief);
}

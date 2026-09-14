/* Profile hub layout — how the 13 attribute categories are grouped on
 * screen, plus the "In my words" prompt library.
 *
 * Grouping follows the biodata order Indian matrimony sites already use
 * (Shaadi.com's "About Myself" → lifestyle → family → partner preference;
 * Jeevansathi's About / Education & Career / Family / Desired Partner), so a
 * parent filling this in recognises the structure. Prompts follow Hinge and
 * Bumble (up to three short answers that give someone something real to
 * reply to). Stored as category `in_my_words`, keys prompt_1..3 — the
 * backend's PATCH /profile/{category} accepts any category, and prompts are
 * deliberately NOT in the enhanced-matching tier, so they never affect
 * discoverability or completeness. */

export type SectionId = 'basics' | 'lifestyle' | 'family' | 'future' | 'partner';

export const PROFILE_SECTIONS: { id: SectionId; categories: string[] }[] = [
  { id: 'basics', categories: ['education', 'profession', 'marital_history', 'relocation'] },
  { id: 'lifestyle', categories: ['lifestyle', 'food_travel_hobbies', 'pets', 'communication_style'] },
  { id: 'family', categories: ['family_involvement_expectations', 'independence'] },
  { id: 'future', categories: ['career_children_living_financial', 'horoscope'] },
  { id: 'partner', categories: ['partner_preference'] },
];

export const PROMPT_CATEGORY = 'in_my_words';
export const PROMPT_SLOTS = ['prompt_1', 'prompt_2', 'prompt_3'] as const;
export type PromptSlot = (typeof PROMPT_SLOTS)[number];

export const PROMPT_QUESTIONS = [
  'ideal_weekend',
  'family_means',
  'looking_for',
  'non_negotiable',
  'simple_pleasures',
  'together_we',
] as const;

export type PromptValue = { q: string; a: string };

export function isPromptValue(v: unknown): v is PromptValue {
  return !!v && typeof v === 'object' && typeof (v as PromptValue).q === 'string' && typeof (v as PromptValue).a === 'string';
}

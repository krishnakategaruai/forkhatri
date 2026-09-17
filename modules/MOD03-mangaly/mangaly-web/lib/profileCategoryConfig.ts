/* FR002/FR003 — the one place that maps (category, attribute_key) pairs to
 * field shape and tier membership, mirroring the backend's
 * `app/config/profile_tiers.py` exactly. Two lists, not one, would risk the
 * TR003/TR027 non-divergence contract drifting; this file is deliberately
 * the frontend's single copy of the same tuples the backend already treats
 * as its one source of truth. */

export type FieldKind = 'select' | 'text' | 'ageRange' | 'tags';

export type FieldDef = {
  category: string;
  key: string;
  kind: FieldKind;
  labelKey: string; // profile:field.<category>.<key>
  options?: string[]; // for 'select' — i18n keys are profile:option.<key>.<option>
};

export type CategoryDef = {
  category: string;
  titleKey: string; // profile:category.<category>
  tier: 'discoverability' | 'enhanced';
  fields: FieldDef[];
};

/* Discoverability tier — DEC-V1-001's four required attributes, plus the
 * any-of partner-preference pair, exactly matching
 * `DISCOVERABILITY_TIER_ATTRIBUTES` / `..._PARTNER_PREFERENCE_ANY_OF`. */
export const DISCOVERABILITY_CATEGORIES: CategoryDef[] = [
  {
    category: 'education',
    titleKey: 'category.education',
    tier: 'discoverability',
    fields: [
      {
        category: 'education',
        key: 'highest_education_level',
        kind: 'select',
        labelKey: 'field.education.highest_education_level',
        options: ['high_school', 'bachelors', 'masters', 'doctorate', 'other'],
      },
    ],
  },
  {
    category: 'profession',
    titleKey: 'category.profession',
    tier: 'discoverability',
    fields: [
      { category: 'profession', key: 'occupation', kind: 'text', labelKey: 'field.profession.occupation' },
    ],
  },
  {
    category: 'marital_history',
    titleKey: 'category.marital_history',
    tier: 'discoverability',
    fields: [
      {
        category: 'marital_history',
        key: 'marital_status',
        kind: 'select',
        labelKey: 'field.marital_history.marital_status',
        options: ['never_married', 'divorced', 'widowed', 'awaiting_divorce'],
      },
    ],
  },
  {
    category: 'relocation',
    titleKey: 'category.relocation',
    tier: 'discoverability',
    fields: [
      {
        category: 'relocation',
        key: 'relocation_willingness',
        kind: 'select',
        labelKey: 'field.relocation.relocation_willingness',
        options: ['yes', 'no', 'open_to_discussion'],
      },
    ],
  },
  {
    category: 'partner_preference',
    titleKey: 'category.partner_preference',
    tier: 'discoverability',
    fields: [
      {
        category: 'partner_preference',
        key: 'looking_for',
        kind: 'select',
        labelKey: 'field.partner_preference.looking_for',
        options: ['bride', 'groom'],
      },
      {
        category: 'partner_preference',
        key: 'age_range',
        kind: 'ageRange',
        labelKey: 'field.partner_preference.age_range',
      },
      {
        category: 'partner_preference',
        key: 'locality',
        kind: 'text',
        labelKey: 'field.partner_preference.locality',
      },
    ],
  },
];

/* Enhanced-matching tier — DEC-V1-001 defines this as "everything else," so
 * the exhaustive field list per category is this app's own implementation
 * choice (FR002's Assumptions note the exact schema is implementation-
 * stage), kept to one representative field per category to stay simple. */
export const ENHANCED_CATEGORIES: CategoryDef[] = [
  {
    category: 'lifestyle',
    titleKey: 'category.lifestyle',
    tier: 'enhanced',
    fields: [
      {
        category: 'lifestyle',
        key: 'diet',
        kind: 'select',
        labelKey: 'field.lifestyle.diet',
        options: ['vegetarian', 'non_vegetarian', 'eggetarian', 'vegan'],
      },
    ],
  },
  {
    category: 'food_travel_hobbies',
    titleKey: 'category.food_travel_hobbies',
    tier: 'enhanced',
    fields: [
      {
        category: 'food_travel_hobbies',
        key: 'hobbies',
        kind: 'tags',
        labelKey: 'field.food_travel_hobbies.hobbies',
      },
    ],
  },
  {
    category: 'communication_style',
    titleKey: 'category.communication_style',
    tier: 'enhanced',
    fields: [
      {
        category: 'communication_style',
        key: 'style',
        kind: 'select',
        labelKey: 'field.communication_style.style',
        options: ['direct', 'thoughtful', 'playful'],
      },
    ],
  },
  {
    category: 'independence',
    titleKey: 'category.independence',
    tier: 'enhanced',
    fields: [
      {
        category: 'independence',
        key: 'preference',
        kind: 'select',
        labelKey: 'field.independence.preference',
        options: ['high', 'balanced', 'family_led'],
      },
    ],
  },
  {
    category: 'family_involvement_expectations',
    titleKey: 'category.family_involvement_expectations',
    tier: 'enhanced',
    fields: [
      {
        category: 'family_involvement_expectations',
        key: 'level',
        kind: 'select',
        labelKey: 'field.family_involvement_expectations.level',
        options: ['close_knit', 'moderate', 'independent'],
      },
    ],
  },
  {
    category: 'career_children_living_financial',
    titleKey: 'category.career_children_living_financial',
    tier: 'enhanced',
    fields: [
      {
        category: 'career_children_living_financial',
        key: 'wants_children',
        kind: 'select',
        labelKey: 'field.career_children_living_financial.wants_children',
        options: ['yes', 'no', 'undecided'],
      },
    ],
  },
  {
    category: 'pets',
    titleKey: 'category.pets',
    tier: 'enhanced',
    fields: [
      {
        category: 'pets',
        key: 'preference',
        kind: 'select',
        labelKey: 'field.pets.preference',
        options: ['love_pets', 'neutral', 'prefer_none'],
      },
    ],
  },
  {
    category: 'horoscope',
    titleKey: 'category.horoscope',
    tier: 'enhanced',
    fields: [
      {
        category: 'horoscope',
        key: 'matching_required',
        kind: 'select',
        labelKey: 'field.horoscope.matching_required',
        options: ['yes', 'no', 'open'],
      },
    ],
  },
];

export const ALL_CATEGORIES: CategoryDef[] = [...DISCOVERABILITY_CATEGORIES, ...ENHANCED_CATEGORIES];

export function findCategory(category: string): CategoryDef | undefined {
  return ALL_CATEGORIES.find((c) => c.category === category);
}

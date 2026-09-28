/* FR002/FR003 — the one place that maps (category, attribute_key) pairs to
 * field shape and tier membership, mirroring the backend's
 * `app/config/profile_tiers.py` exactly. Two lists, not one, would risk the
 * TR003/TR027 non-divergence contract drifting; this file is deliberately
 * the frontend's single copy of the same tuples the backend already treats
 * as its one source of truth.
 *
 * [2026-09-17 rework, contract §3] New categories a mature matrimony biodata
 * carries: `basics` (height, mother tongue, children), `community` (gotra,
 * sub-community, native place), `education_career` (income, employer,
 * college), `family` (family type/values, parents' occupations, siblings),
 * and the horoscope extras (manglik, rashi, nakshatra, birth time/place). */

/** `time` is a 24-hour HH:MM picker; `place` searches the place-of-birth list. */
export type FieldKind = 'select' | 'text' | 'number' | 'textarea' | 'ageRange' | 'tags' | 'time' | 'place';

export type FieldDef = {
  category: string;
  key: string;
  kind: FieldKind;
  labelKey: string; // profile:field.<category>.<key>
  options?: string[]; // for 'select' — i18n keys are profile:option.<key>.<option>
  /** Unit suffix shown after a number (e.g. cm). */
  unit?: string;
  min?: number;
  max?: number;
};

export type CategoryDef = {
  category: string;
  titleKey: string; // profile:category.<category>
  tier: 'discoverability' | 'enhanced';
  fields: FieldDef[];
};

export const MOTHER_TONGUES = ['telugu', 'tamil', 'kannada', 'hindi', 'punjabi', 'marathi', 'gujarati', 'english', 'other'];
export const SUB_COMMUNITIES = ['khatri', 'arora', 'sood', 'bhatia', 'other'];
export const INCOME_BANDS = ['under_5', '5_10', '10_20', '20_40', '40_plus', 'prefer_not'];
export const FAMILY_TYPES = ['joint', 'nuclear', 'extended'];
export const FAMILY_VALUES = ['traditional', 'moderate', 'liberal'];
export const MANGLIK = ['yes', 'no', 'partial', 'dont_know'];
/* The 27 nakshatras in order, as stored keys (profile:option.nakshatra.*). */
export const NAKSHATRAS = [
  'ashwini', 'bharani', 'krittika', 'rohini', 'mrigashira', 'ardra', 'punarvasu', 'pushya', 'ashlesha',
  'magha', 'purva_phalguni', 'uttara_phalguni', 'hasta', 'chitra', 'swati', 'vishakha', 'anuradha', 'jyeshtha',
  'mula', 'purva_ashadha', 'uttara_ashadha', 'shravana', 'dhanishta', 'shatabhisha',
  'purva_bhadrapada', 'uttara_bhadrapada', 'revati',
];
/* How sure the family is of the birth time (± minutes); "unknown" means no time. */
export const BIRTH_TIME_ACCURACY = ['exact', 'about_15', 'about_30', 'about_60', 'about_120', 'unknown'];
export const RASHIS = [
  'mesh',
  'vrishabh',
  'mithun',
  'kark',
  'simha',
  'kanya',
  'tula',
  'vrishchik',
  'dhanu',
  'makar',
  'kumbh',
  'meen',
];

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

/* Enhanced-matching tier — DEC-V1-001 defines this as "everything else." */
export const ENHANCED_CATEGORIES: CategoryDef[] = [
  {
    category: 'basics',
    titleKey: 'category.basics',
    tier: 'enhanced',
    fields: [
      // The formal introduction a biodata opens with — written by the candidate
      // or, on a profile a parent created, by the parent (DEC-V1-019).
      { category: 'basics', key: 'about', kind: 'textarea', labelKey: 'field.basics.about' },
      { category: 'basics', key: 'height_cm', kind: 'number', labelKey: 'field.basics.height_cm', unit: 'cm', min: 120, max: 220 },
      {
        category: 'basics',
        key: 'mother_tongue',
        kind: 'select',
        labelKey: 'field.basics.mother_tongue',
        options: MOTHER_TONGUES,
      },
      {
        category: 'basics',
        key: 'have_children',
        kind: 'select',
        labelKey: 'field.basics.have_children',
        options: ['no', 'yes_living_with_me', 'yes_not_living_with_me'],
      },
    ],
  },
  {
    category: 'community',
    titleKey: 'category.community',
    tier: 'enhanced',
    fields: [
      { category: 'community', key: 'gotra', kind: 'text', labelKey: 'field.community.gotra' },
      {
        category: 'community',
        key: 'sub_community',
        kind: 'select',
        labelKey: 'field.community.sub_community',
        options: SUB_COMMUNITIES,
      },
      { category: 'community', key: 'native_place', kind: 'text', labelKey: 'field.community.native_place' },
    ],
  },
  {
    category: 'education_career',
    titleKey: 'category.education_career',
    tier: 'enhanced',
    fields: [
      {
        category: 'education_career',
        key: 'income_band',
        kind: 'select',
        labelKey: 'field.education_career.income_band',
        options: INCOME_BANDS,
      },
      { category: 'education_career', key: 'employer', kind: 'text', labelKey: 'field.education_career.employer' },
      { category: 'education_career', key: 'college', kind: 'text', labelKey: 'field.education_career.college' },
    ],
  },
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
      // [DEC-V1-031] Standard biodata facts the matchmaker checks against a
      // family's "doesn't drink" / "no smoking".
      {
        category: 'lifestyle',
        key: 'smoking',
        kind: 'select',
        labelKey: 'field.lifestyle.smoking',
        options: ['never', 'occasionally', 'regularly'],
      },
      {
        category: 'lifestyle',
        key: 'drinking',
        kind: 'select',
        labelKey: 'field.lifestyle.drinking',
        options: ['never', 'occasionally', 'regularly'],
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
    category: 'family',
    titleKey: 'category.family',
    tier: 'enhanced',
    fields: [
      { category: 'family', key: 'family_type', kind: 'select', labelKey: 'field.family.family_type', options: FAMILY_TYPES },
      {
        category: 'family',
        key: 'family_values',
        kind: 'select',
        labelKey: 'field.family.family_values',
        options: FAMILY_VALUES,
      },
      { category: 'family', key: 'father_occupation', kind: 'text', labelKey: 'field.family.father_occupation' },
      { category: 'family', key: 'mother_occupation', kind: 'text', labelKey: 'field.family.mother_occupation' },
      { category: 'family', key: 'brothers', kind: 'number', labelKey: 'field.family.brothers', min: 0, max: 12 },
      { category: 'family', key: 'sisters', kind: 'number', labelKey: 'field.family.sisters', min: 0, max: 12 },
      {
        category: 'family',
        key: 'lives_with_parents',
        kind: 'select',
        labelKey: 'field.family.lives_with_parents',
        options: ['yes', 'no'],
      },
      { category: 'family', key: 'about_family', kind: 'textarea', labelKey: 'field.family.about_family' },
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
      // Which traditional matching the family follows; unset means "by mother tongue".
      {
        category: 'horoscope',
        key: 'matching_system',
        kind: 'select',
        labelKey: 'field.horoscope.matching_system',
        options: ['ashtakoota', 'porutham', 'both'],
      },
      // [2026-09-27] What the kundli is calculated from: exact local time, how
      // sure it is, and a place picked from the list (coordinates and time
      // zone come with it). Visible to other members, by the owner's decision.
      { category: 'horoscope', key: 'birth_time', kind: 'time', labelKey: 'field.horoscope.birth_time' },
      {
        category: 'horoscope',
        key: 'birth_time_accuracy',
        kind: 'select',
        labelKey: 'field.horoscope.birth_time_accuracy',
        options: BIRTH_TIME_ACCURACY,
      },
      { category: 'horoscope', key: 'birth_place', kind: 'place', labelKey: 'field.horoscope.birth_place' },
      // What the family's own horoscope says, if they know it.
      { category: 'horoscope', key: 'rashi', kind: 'select', labelKey: 'field.horoscope.rashi', options: RASHIS },
      { category: 'horoscope', key: 'nakshatra', kind: 'select', labelKey: 'field.horoscope.nakshatra', options: NAKSHATRAS },
      { category: 'horoscope', key: 'manglik', kind: 'select', labelKey: 'field.horoscope.manglik', options: MANGLIK },
    ],
  },
];

export const ALL_CATEGORIES: CategoryDef[] = [...DISCOVERABILITY_CATEGORIES, ...ENHANCED_CATEGORIES];

export function findCategory(category: string): CategoryDef | undefined {
  return ALL_CATEGORIES.find((c) => c.category === category);
}

export function findField(category: string, key: string): FieldDef | undefined {
  return findCategory(category)?.fields.find((f) => f.key === key);
}
